"""Phase 11 — Live Daemon Integration Test.

Checks whether the full operator dispatch chain is live and functional:
  1. Hermes daemon live (PID file OR fresh bus heartbeat)
  2. OpenClaw daemon live (PID file OR fresh bus heartbeat)
  3. Agent Bus storage accessible
  4. send/poll chain importable

When `operator_approved=True`, writes a single integration-test probe task
to the Agent Bus (sender=Studio, recipient=Hermes) and polls for 2 cycles
to confirm the task was accepted. This write is explicit-opt-in only.

Default mode is read-only (dry_run=True / operator_approved=False).

Read-only default: no tasks created, no approvals consumed, no vault mutations.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.phase11_live_daemon_integration_test.v1"
SURFACE_ID = "phase11_live_daemon_integration_test"
PASS_ID = "phase11-live-daemon-integration-test"
NEXT_RECOMMENDED_PASS = "ventureops-operator-readiness-gate"

_PROBE_SENDER = "Studio"
_PROBE_INTENT = "[INTEGRATION TEST] daemon connectivity probe — Studio live dispatch verification"
_POLL_CYCLES = 2
_POLL_INTERVAL_S = 2.0


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Reuse daemon checks from production dispatch readiness ───────────────────

def _daemon_live(vault: Path, runtime_name: str) -> dict[str, Any]:
    """PID probe + heartbeat freshness for one runtime. Returns is_live and detail."""
    from runtime.studio.phase11_production_operator_dispatch_readiness import (
        _check_daemon_pid,
        _check_bus_heartbeat,
    )
    pid = _check_daemon_pid(vault, runtime_name)
    hb = _check_bus_heartbeat(vault, runtime_name)
    is_live = (pid["status"] == "running") or hb.get("fresh", False)
    return {
        "runtime": runtime_name,
        "daemon_process_status": pid["status"],
        "pid": pid.get("pid"),
        "heartbeat_freshness": hb.get("freshness", "unavailable"),
        "heartbeat_age_seconds": hb.get("age_seconds"),
        "is_live": is_live,
    }


def _bus_accessible(vault: Path) -> bool:
    db = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    return db.exists()


def _send_poll_importable() -> bool:
    try:
        from runtime.studio.phase11_chat_send_message import (  # noqa: F401
            send_chat_message as _s,
            poll_chat_result as _p,
        )
        return callable(_s) and callable(_p)
    except ImportError:
        return False


# ── Optional live probe ───────────────────────────────────────────────────────

def _run_live_probe(vault: Path) -> dict[str, Any]:
    """Write a test task to Agent Bus and poll 2 cycles. Requires bus accessible."""
    try:
        from runtime.studio.phase11_chat_send_message import (
            send_chat_message,
            poll_chat_result,
        )
        send_result = send_chat_message(
            vault,
            _PROBE_INTENT,
            runtime_id="hermes",
            session_id="studio-integration-probe",
        )
        task_id = send_result.get("task_id") or send_result.get("data", {}).get("task_id")
        if not task_id:
            return {
                "probe_attempted": True,
                "probe_ok": False,
                "error": "no task_id returned from send_chat_message",
                "send_result": send_result,
            }
        polls: list[dict] = []
        for _ in range(_POLL_CYCLES):
            time.sleep(_POLL_INTERVAL_S)
            poll = poll_chat_result(vault, task_id)
            polls.append(poll)
            if poll.get("status") in ("done", "result_attached", "error", "blocked"):
                break
        final = polls[-1] if polls else {}
        return {
            "probe_attempted": True,
            "probe_ok": True,
            "task_id": task_id,
            "polls_run": len(polls),
            "final_status": final.get("status", "unknown"),
            "task_accepted": final.get("status") != "not_found",
        }
    except Exception as exc:
        return {
            "probe_attempted": True,
            "probe_ok": False,
            "error": str(exc)[:120],
        }


# ── Build function ───────────────────────────────────────────────────────────

def build_phase11_live_daemon_integration_test(
    vault_root: str | Path,
    *,
    operator_approved: bool = False,
    message: str | None = None,
) -> dict[str, Any]:
    """Check live daemon integration readiness and optionally run a bus probe.

    operator_approved=True enables a single Agent Bus write (probe task).
    Default is read-only: no tasks created, no vault mutations.
    """
    vault = Path(vault_root).resolve()
    del message  # accepted for API parity

    hermes = _daemon_live(vault, "hermes")
    openclaw = _daemon_live(vault, "openclaw")
    bus_ok = _bus_accessible(vault)
    chain_ok = _send_poll_importable()

    checks: dict[str, bool] = {
        "hermes_pid_or_heartbeat_live": hermes["is_live"],
        "openclaw_pid_or_heartbeat_live": openclaw["is_live"],
        "bus_storage_accessible": bus_ok,
        "send_poll_chain_importable": chain_ok,
    }

    integration_ready = all(checks.values())

    blocked_reasons: list[str] = []
    if not hermes["is_live"]:
        blocked_reasons.append("hermes_not_live")
    if not openclaw["is_live"]:
        blocked_reasons.append("openclaw_not_live")
    if not bus_ok:
        blocked_reasons.append("bus_storage_not_accessible")
    if not chain_ok:
        blocked_reasons.append("send_poll_chain_not_importable")

    operator_actions: list[str] = []
    if not hermes["is_live"]:
        operator_actions.append(
            "Start Hermes daemon: chaseos runtime daemon --runtime hermes --synthesize"
        )
    if not openclaw["is_live"]:
        operator_actions.append(
            "Start OpenClaw daemon: chaseos runtime daemon --runtime openclaw"
        )
    if not bus_ok:
        operator_actions.append(
            "Initialise Agent Bus: chaseos agent-bus init  OR  start any chaseos watch loop"
        )

    if integration_ready:
        status = "INTEGRATION READY — all daemons live and bus accessible"
    elif not hermes["is_live"] and not openclaw["is_live"]:
        status = "AWAITING DAEMONS — start Hermes and OpenClaw to enable live dispatch"
    elif not hermes["is_live"]:
        status = "AWAITING HERMES — OpenClaw live but Hermes not running"
    elif not openclaw["is_live"]:
        status = "AWAITING OPENCLAW — Hermes live but OpenClaw not running"
    else:
        status = "NOT READY — see blocked_reasons"

    # Optional live probe
    live_probe: dict[str, Any] = {"probe_attempted": False, "operator_approved": operator_approved}
    if operator_approved and bus_ok and chain_ok:
        live_probe = _run_live_probe(vault)
        live_probe["operator_approved"] = True
    elif operator_approved and not (bus_ok and chain_ok):
        live_probe = {
            "probe_attempted": False,
            "operator_approved": True,
            "skipped_reason": "bus or send/poll chain not ready — probe skipped to avoid write errors",
        }

    return {
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "ok": True,
        "integration_ready": integration_ready,
        "status": status,
        "checks": checks,
        "daemon_runtimes": {
            "hermes": hermes,
            "openclaw": openclaw,
        },
        "blocked_reasons": blocked_reasons,
        "operator_actions": operator_actions,
        "live_probe": live_probe,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "authority": {
            "read_only": not operator_approved,
            "tasks_created": live_probe.get("probe_ok", False) and operator_approved,
            "approvals_consumed": False,
            "vault_mutations": False,
            "daemon_started": False,
            "operator_approved_probe": operator_approved,
        },
    }
