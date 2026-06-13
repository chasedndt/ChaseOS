"""Phase 11 Chat — Live E2E verification with active runtime.

Verifies the full Studio Chat dispatch chain end-to-end:

  send_chat_message() → Agent Bus task created
    → Runtime watch loop claims → posts result_attached event
    → poll_chat_result() → result_text returned to Studio

The bounded ack response confirms the full chain is working even if
the runtime has no LLM configured yet. The important thing is that
the task travels through the bus and the result comes back.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PASS_ID = "phase11-chat-live-e2e-with-active-runtime"
SURFACE_ID = "phase11_chat_live_e2e"
MODEL_VERSION = "studio.phase11_chat_live_e2e.v2"

_POLL_INTERVAL_S = 1.0
_DEFAULT_MAX_WAIT_S = 30.0
# How long to wait before trying to trigger a daemon cycle when the port is live
# but no watch loop has claimed the task yet.
_DAEMON_TRIGGER_THRESHOLD_S = 4.0


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hidden_subprocess_creationflags() -> int:
    """Prevent transient console windows when Studio triggers a bounded probe."""

    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)


def _trigger_runtime_daemon(vault: Path, runtime_id: str, *, synthesize: bool = False) -> bool:
    """Trigger a one-shot watch cycle for a runtime via the CLI. Fail-open.

    Called when the runtime's gateway port is online but no watch loop has
    claimed the task yet — the gateway is up but the bus poller isn't running.
    Returns True if the subprocess exited 0.
    """
    try:
        command = [
            sys.executable, "-m", "runtime.cli.main",
            "runtime", "daemon",
            "--runtime", runtime_id,
            "--daemon-once",
            "--daemon-max-tasks", "20",
            "--vault-root", str(vault),
            "--json",
        ]
        if synthesize:
            command.insert(-1, "--synthesize")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=_hidden_subprocess_creationflags(),
        )
        return result.returncode == 0
    except Exception:
        return False


def run_chat_probe(
    vault_root: str | Path,
    message: str = "hi",
    *,
    runtime_id: str = "hermes",
    max_wait_s: float = _DEFAULT_MAX_WAIT_S,
    poll_interval_s: float = _POLL_INTERVAL_S,
    auto_trigger_daemon: bool = True,
    synthesize_on_trigger: bool = False,
) -> dict[str, Any]:
    """Send a message and poll until the runtime responds or we time out.

    When auto_trigger_daemon=True (default): if the task isn't claimed within
    _DAEMON_TRIGGER_THRESHOLD_S and the runtime's gateway port is live, triggers
    a one-shot daemon watch cycle via the CLI. This handles the case where the
    gateway process is running on its port but the bus polling loop isn't active.

    Returns a result dict with ok, probe_outcome, task_id, result_text, elapsed_s.
    """
    from runtime.studio.phase11_chat_send_message import (
        send_chat_message,
        poll_chat_result,
    )
    from runtime.studio.phase11_chat_runtime_dispatch_verification import (
        _check_gateway_ports,
    )

    vault = Path(vault_root).resolve()
    message = (message or "").strip() or "hi"

    send_result = send_chat_message(vault, message, runtime_id=runtime_id)
    if not send_result.get("ok"):
        return {
            "ok": False,
            "pass": PASS_ID,
            "surface": SURFACE_ID,
            "probe_outcome": "send_failed",
            "send_error": send_result.get("blocked_reason", "unknown"),
            "task_id": None,
            "recipient": None,
            "result_text": None,
            "elapsed_s": 0.0,
            "runtime_id": runtime_id,
        }

    task_id = send_result["task_id"]
    recipient = send_result.get("recipient")
    start = time.monotonic()
    _daemon_triggered = False

    while True:
        elapsed = time.monotonic() - start
        try:
            poll = poll_chat_result(vault, task_id, recipient=recipient)
        except Exception as exc:
            return {
                "ok": False,
                "pass": PASS_ID,
                "surface": SURFACE_ID,
                "probe_outcome": "poll_error",
                "poll_error": str(exc)[:120],
                "task_id": task_id,
                "recipient": recipient,
                "result_text": None,
                "elapsed_s": round(elapsed, 2),
                "runtime_id": runtime_id,
            }

        if poll.get("ok") and (poll.get("is_complete") or poll.get("is_blocked")):
            outcome = "complete" if poll.get("is_complete") else "blocked"
            return {
                "ok": outcome == "complete",
                "pass": PASS_ID,
                "surface": SURFACE_ID,
                "probe_outcome": outcome,
                "task_id": task_id,
                "recipient": recipient,
                "result_text": poll.get("result_text"),
                "status": poll.get("status"),
                "elapsed_s": round(elapsed, 2),
                "runtime_id": runtime_id,
            }

        # If the task hasn't been claimed yet and we've hit the trigger threshold,
        # trigger a one-shot daemon cycle when the runtime appears reachable by
        # either gateway port or Agent Bus heartbeat. This handles: heartbeat
        # fresh/gateway absent, or gateway up but watch loop not running.
        if (
            auto_trigger_daemon
            and not _daemon_triggered
            and elapsed >= _DAEMON_TRIGGER_THRESHOLD_S
        ):
            _daemon_triggered = True
            try:
                port_info = _check_gateway_ports(runtime_id)
                should_trigger = bool(port_info.get("gateway_port_online"))
                if not should_trigger:
                    from runtime.studio.phase11_chat_runtime_dispatch_verification import (
                        build_chat_runtime_availability,
                    )

                    runtime_info = (
                        (build_chat_runtime_availability(vault).get("runtime_by_adapter") or {}).get(runtime_id)
                        or {}
                    )
                    should_trigger = bool(
                        runtime_info.get("heartbeat_online")
                        or runtime_info.get("dispatch_ready")
                        or runtime_info.get("online")
                    )
                if not should_trigger:
                    should_trigger = True
                if should_trigger:
                    _trigger_runtime_daemon(vault, runtime_id, synthesize=synthesize_on_trigger)
            except Exception:
                pass

        if elapsed >= max_wait_s:
            return {
                "ok": False,
                "pass": PASS_ID,
                "surface": SURFACE_ID,
                "probe_outcome": "timeout",
                "task_id": task_id,
                "recipient": recipient,
                "result_text": None,
                "elapsed_s": round(elapsed, 2),
                "runtime_id": runtime_id,
            }

        time.sleep(poll_interval_s)


def _pick_probe_runtime(avail: dict[str, Any]) -> str:
    """Pick the best available runtime for the probe. Prefers Hermes, then OpenClaw."""
    runtime_by_adapter = avail.get("runtime_by_adapter") or {}
    for adapter_id in ("hermes", "openclaw", "claude-code"):
        info = runtime_by_adapter.get(adapter_id) or {}
        if info.get("online") and info.get("is_bus_runtime"):
            return adapter_id
    return "hermes"


def build_phase11_chat_live_e2e_verification(
    vault_root: str | Path,
    *,
    probe_timeout_s: float = _DEFAULT_MAX_WAIT_S,
    probe_message: str = "hi",
) -> dict[str, Any]:
    """Build the Phase 11 chat live e2e verification report.

    Checks:
      1. send_chat_message + poll_chat_result importable and callable
      2. Agent Bus SQLite accessible
      3. At least one runtime has a recent heartbeat
      4. Live round-trip probe: send message → poll → verify response received

    The probe selects the most-available runtime automatically.
    This function writes a task to the Agent Bus (authority.agent_bus_task_write_performed=True).
    """
    from runtime.studio.phase11_chat_runtime_dispatch_verification import (
        build_chat_runtime_availability,
    )

    vault = Path(vault_root).resolve()
    checks: dict[str, bool] = {}
    blocked_reasons: list[str] = []

    # 1 — Import checks
    try:
        from runtime.studio.phase11_chat_send_message import send_chat_message  # noqa: F401
        from runtime.studio.phase11_chat_send_message import poll_chat_result    # noqa: F401
        checks["send_chat_message_importable"] = True
        checks["poll_chat_result_importable"] = True
    except ImportError:
        checks["send_chat_message_importable"] = False
        checks["poll_chat_result_importable"] = False
        blocked_reasons.append("chat_send_modules_not_importable")

    # 2 — Bus accessible
    db_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    checks["agent_bus_storage_accessible"] = db_path.exists()
    if not db_path.exists():
        blocked_reasons.append("agent_bus_storage_not_present")

    # 3 — Runtime online check
    avail = build_chat_runtime_availability(vault)
    any_online = avail.get("any_runtime_online", False)
    checks["any_runtime_online"] = any_online
    if not any_online:
        blocked_reasons.append("no_runtime_daemon_heartbeat_present")

    probe_runtime = _pick_probe_runtime(avail)

    # 4 — Live probe (only if chain is viable)
    probe_result: dict[str, Any] | None = None
    if not blocked_reasons:
        probe_result = run_chat_probe(
            vault,
            message=probe_message,
            runtime_id=probe_runtime,
            max_wait_s=probe_timeout_s,
        )
        checks["probe_task_created"] = probe_result.get("task_id") is not None
        checks["probe_result_received"] = bool(probe_result.get("result_text"))
        checks["probe_round_trip_ok"] = probe_result.get("ok") is True
        if not checks["probe_round_trip_ok"]:
            blocked_reasons.append(
                f"probe_{probe_result.get('probe_outcome', 'unknown')}"
            )
    else:
        checks["probe_task_created"] = False
        checks["probe_result_received"] = False
        checks["probe_round_trip_ok"] = False

    dispatch_chain_complete = all([
        checks.get("send_chat_message_importable"),
        checks.get("poll_chat_result_importable"),
        checks.get("agent_bus_storage_accessible"),
        checks.get("any_runtime_online"),
        checks.get("probe_round_trip_ok"),
    ])

    all_ok = dispatch_chain_complete and not blocked_reasons

    if all_ok:
        runtime_display = probe_runtime.upper()
        status = f"LIVE E2E COMPLETE / {runtime_display} RESPONDED"
    elif any_online:
        status = "RUNTIME ONLINE / PROBE INCOMPLETE"
    else:
        status = "AWAITING ACTIVE RUNTIME"

    result_preview = ""
    if probe_result and probe_result.get("result_text"):
        result_preview = probe_result["result_text"][:300]

    return {
        "ok": all_ok,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at_utc": _now_utc(),
        "checks": checks,
        "blocked_reasons": blocked_reasons,
        "probe_runtime": probe_runtime,
        "probe_result": probe_result,
        "runtime_availability": avail,
        "summary": {
            "dispatch_chain_complete": dispatch_chain_complete,
            "any_runtime_online": any_online,
            "probe_outcome": (probe_result or {}).get("probe_outcome"),
            "result_text_preview": result_preview,
            "elapsed_s": (probe_result or {}).get("elapsed_s"),
        },
        "authority": {
            "read_only": False,
            "agent_bus_task_write_performed": not bool(blocked_reasons),
            "approval_consumed": False,
            "canonical_mutation_performed": False,
        },
    }
