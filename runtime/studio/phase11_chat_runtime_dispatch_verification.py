"""Phase 11 Chat - Runtime Dispatch Verification.

Read-only verification that the full chat dispatch chain is wired:
  1. Agent Bus storage is accessible
  2. send_chat_message() and poll_chat_result() are importable and callable
  3. Heartbeat/gateway-based runtime availability for registered chat adapters

No tasks are created, no approvals consumed, no vault mutations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.runtime_live_status import (
    build_runtime_live_status,
    heartbeat_freshness,
    probe_gateway_ports,
    seconds_since,
)


MODEL_VERSION = "studio.phase11_chat_runtime_dispatch_verification.v3"
SURFACE_ID = "phase11_chat_runtime_dispatch_verification"
PASS_ID = "phase11-chat-runtime-dispatch-verification"
NEXT_RECOMMENDED_PASS = "agent-bus-or-canonical-writeback-readiness"

_ADAPTER_RUNTIME_MAP: dict[str, tuple[str | None, int]] = {
    "hermes": ("Hermes", 120),
    "openclaw": ("OpenClaw", 120),
    "claude-code": ("Archon", 300),
    "direct-provider": (None, 0),
}

_FRESH_THRESHOLD_S = 120
_RECENT_THRESHOLD_S = 900
_ACTIVE_GATEWAY_PROBE_VAULT: Path | None = None


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _seconds_since(iso_ts: str | None) -> float | None:
    return seconds_since(iso_ts)


def _heartbeat_freshness(elapsed_seconds: float | None) -> str:
    return heartbeat_freshness(elapsed_seconds, recent_threshold_seconds=_RECENT_THRESHOLD_S)


def _read_runtime_heartbeat(vault: Path, runtime_name: str) -> dict[str, Any]:
    """Read the most-recent heartbeat row for a given runtime. Never writes."""
    adapter_by_runtime = {
        "Hermes": "hermes",
        "OpenClaw": "openclaw",
        "Archon": "claude-code",
    }
    status = build_runtime_live_status(
        vault,
        adapter_by_runtime.get(runtime_name, runtime_name.lower()),
        probe_wsl_processes=False,
    )
    heartbeat = status.get("heartbeat") or {}
    return {
        "runtime": runtime_name,
        "found": bool(heartbeat.get("found")),
        "last_seen": heartbeat.get("last_seen"),
        "elapsed_seconds": heartbeat.get("elapsed_seconds"),
        "status": heartbeat.get("status"),
    }


def _check_gateway_ports(adapter_id: str) -> dict[str, Any]:
    """TCP-probe declared gateway ports for adapter_id. Fail-open and read-only.

    Tests monkeypatch this one-argument function, so build_chat_runtime_availability
    temporarily supplies the active vault through a module global.
    """
    vault = _ACTIVE_GATEWAY_PROBE_VAULT or Path.cwd()
    return probe_gateway_ports(vault, adapter_id)


def build_chat_runtime_availability(
    vault_root: str | Path,
    *,
    probe_wsl_processes: bool = False,
) -> dict[str, Any]:
    """Return availability for all registered chat runtimes.

    Uses passive liveness signals by default:
      1. Agent Bus heartbeat freshness
      2. TCP probe of declared runtime gateway ports
      3. Studio PID-file process evidence, where present

    The Studio Chat page calls this surface on page load and while polling
    availability.  It must therefore not spawn Windows/WSL process probes by
    default: invoking ``wsl.exe`` from the Windows pywebview process can flash
    transient terminal/conhost windows when the user opens Chat.  Manual
    diagnostics may opt into ``probe_wsl_processes=True`` explicitly.

    `online` may be true when a WSL/runtime gateway is listening even if the
    heartbeat is stale. `dispatch_ready` stays stricter and requires heartbeat
    freshness, because Agent Bus dispatch should not be overclaimed.
    """
    vault = Path(vault_root).resolve()
    runtimes: list[dict[str, Any]] = []

    global _ACTIVE_GATEWAY_PROBE_VAULT
    previous_probe_vault = _ACTIVE_GATEWAY_PROBE_VAULT
    _ACTIVE_GATEWAY_PROBE_VAULT = vault
    try:
        for adapter_id, (bus_name, _stale_sec) in _ADAPTER_RUNTIME_MAP.items():
            if bus_name is None:
                runtimes.append({
                    "adapter_id": adapter_id,
                    "bus_name": None,
                    "freshness": "n/a",
                    "pip_class": "pip--na",
                    "last_seen": None,
                    "elapsed_seconds": None,
                    "is_bus_runtime": False,
                    "online": None,
                    "dispatch_ready": False,
                })
                continue

            live_status = build_runtime_live_status(
                vault,
                adapter_id,
                probe_wsl_processes=probe_wsl_processes,
            )
            heartbeat = live_status.get("heartbeat") or {}
            elapsed = heartbeat.get("elapsed_seconds")
            freshness = live_status.get("heartbeat_freshness") or _heartbeat_freshness(elapsed)
            heartbeat_online = bool(live_status.get("heartbeat_online"))

            port_info = _check_gateway_ports(adapter_id)
            gateway_port_online = bool(port_info.get("gateway_port_online"))
            online = heartbeat_online or gateway_port_online or bool(live_status.get("pid_alive"))

            if online:
                if heartbeat_online:
                    pip_class = "pip--live" if freshness == "fresh" else "pip--recent"
                else:
                    pip_class = "pip--port-live"
            else:
                pip_class = "pip--stale" if freshness == "stale" else "pip--offline"

            runtimes.append({
                "adapter_id": adapter_id,
                "bus_name": bus_name,
                "freshness": freshness,
                "pip_class": pip_class,
                "last_seen": heartbeat.get("last_seen"),
                "elapsed_seconds": elapsed,
                "is_bus_runtime": True,
                "online": online,
                "heartbeat_online": heartbeat_online,
                "gateway_port_online": gateway_port_online,
                "gateway_port_listening": port_info.get("gateway_port_listening"),
                "gateway_host_listening": port_info.get("gateway_host_listening"),
                "gateway_ports_checked": port_info.get("gateway_ports_checked") or [],
                "status_source": live_status.get("status_source"),
                "coordination_state": live_status.get("coordination_state"),
                "coordination_watch_state_stale": bool(live_status.get("coordination_watch_state_stale")),
                "coordination_watch_running": bool(live_status.get("coordination_watch_running")),
                "dispatch_ready": bool(live_status.get("dispatch_ready")),
                "runtime_can_receive_chat": bool(live_status.get("runtime_can_receive_chat")),
                "pid_alive": bool(live_status.get("pid_alive")),
                "wsl_process_probe_enabled": bool(live_status.get("wsl_process_probe_enabled")),
                "wsl_process_alive": bool(live_status.get("wsl_process_alive")),
                "wsl_process": live_status.get("wsl_process") or {},
                "blocked_reasons": live_status.get("blocked_reasons") or [],
            })
    finally:
        _ACTIVE_GATEWAY_PROBE_VAULT = previous_probe_vault

    any_online = any(r.get("online") for r in runtimes if r.get("is_bus_runtime"))
    runtime_by_adapter = {r["adapter_id"]: r for r in runtimes}

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "any_runtime_online": any_online,
        "runtimes": runtimes,
        "runtime_by_adapter": runtime_by_adapter,
    }


def build_phase11_chat_runtime_dispatch_verification(vault_root: str | Path) -> dict[str, Any]:
    """Verify the full chat dispatch chain is wired. Return a verification report."""
    vault = Path(vault_root).resolve()
    checks: dict[str, Any] = {}

    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    checks["agent_bus_storage_accessible"] = sqlite_path.exists()

    try:
        from runtime.studio.phase11_chat_send_message import (  # type: ignore[import]
            poll_chat_result as _poll,
            send_chat_message as _send,
        )
        checks["send_chat_message_importable"] = True
        checks["poll_chat_result_importable"] = True
        checks["send_chat_message_callable"] = callable(_send)
        checks["poll_chat_result_callable"] = callable(_poll)
    except ImportError as exc:
        checks["send_chat_message_importable"] = False
        checks["poll_chat_result_importable"] = False
        checks["send_chat_message_callable"] = False
        checks["poll_chat_result_callable"] = False
        checks["import_error"] = str(exc)

    availability = build_chat_runtime_availability(vault)

    send_wired = bool(checks.get("send_chat_message_callable"))
    poll_wired = bool(checks.get("poll_chat_result_callable"))
    bus_ready = bool(checks.get("agent_bus_storage_accessible"))
    dispatch_chain_wired = send_wired and poll_wired
    any_online = bool(availability.get("any_runtime_online", False))
    any_dispatch_ready = any(
        bool(item.get("dispatch_ready"))
        for item in availability.get("runtimes") or []
        if item.get("is_bus_runtime")
    )

    blockers: list[str] = []
    if not send_wired:
        blockers.append("send_chat_message_not_callable")
    if not poll_wired:
        blockers.append("poll_chat_result_not_callable")
    if not bus_ready:
        blockers.append("agent_bus_storage_not_present")
    if not any_online:
        blockers.append("no_runtime_daemon_heartbeat_present")
    elif not any_dispatch_ready:
        blockers.append("runtime_gateway_live_but_agent_bus_heartbeat_not_fresh")

    return {
        "ok": dispatch_chain_wired,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": (
            "VERIFIED / DISPATCH CHAIN WIRED / AWAITING ACTIVE RUNTIME"
            if dispatch_chain_wired and not any_online
            else "VERIFIED / DISPATCH CHAIN WIRED / GATEWAY ONLINE / HEARTBEAT REQUIRED"
            if dispatch_chain_wired and any_online and not any_dispatch_ready
            else "VERIFIED / DISPATCH CHAIN WIRED / RUNTIME ONLINE"
            if dispatch_chain_wired and any_dispatch_ready
            else "PARTIAL / DISPATCH CHAIN IMPORT ERROR"
        ),
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "dispatch_chain_wired": dispatch_chain_wired,
            "send_message_wired": send_wired,
            "poll_result_wired": poll_wired,
            "agent_bus_storage_accessible": bus_ready,
            "any_runtime_online": any_online,
            "any_runtime_dispatch_ready": any_dispatch_ready,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "next_step": (
                "start a runtime daemon or gateway to enable live chat dispatch"
                if dispatch_chain_wired and not any_online
                else "restore runtime Agent Bus heartbeat before dispatch"
                if dispatch_chain_wired and any_online and not any_dispatch_ready
                else "dispatch chain ready - runtime heartbeat online - send a chat message"
                if dispatch_chain_wired and any_dispatch_ready
                else "fix import error before proceeding"
            ),
        },
        "dispatch_checks": checks,
        "runtime_availability": availability,
        "blocked_reasons": blockers,
        "authority": {
            "read_only": True,
            "provider_call_performed": False,
            "agent_bus_task_write_performed": False,
            "approval_consumed": False,
            "canonical_mutation_performed": False,
        },
    }
