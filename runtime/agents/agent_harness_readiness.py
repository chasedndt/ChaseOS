"""Read-only Agent Harness readiness contract for ChaseOS V1.

This module answers whether a declared runtime harness is ready to become a
bounded tool-calling worker on the Agent Bus.  It intentionally does not call
providers, spawn harnesses, execute terminal commands, mutate the Agent Bus, or
write canonical knowledge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.capabilities import CapabilityError, RuntimeCapabilities, load_all_capabilities
from runtime.agent_bus.router import get_runtime_liveness
from runtime.adapters.codex.daemon import get_codex_daemon_readiness

SURFACE_ID = "agent_harness_readiness"
MODEL_VERSION = "agent_harness_readiness.v1"

REQUIRED_EVIDENCE = [
    "agent_bus_capability_manifest",
    "fresh_runtime_heartbeat",
    "declared_task_capabilities",
    "runtime_identity_resolution",
    "adapter_specific_readiness_when_available",
    "operator_gate_before_live_tool_calls",
]

AUTHORITY = {
    "read_only": True,
    "tools_callable_now": False,
    "agent_bus_mutation_allowed": False,
    "provider_calls_allowed": False,
    "terminal_execution_allowed": False,
    "route_execution_allowed": False,
    "credential_values_visible": False,
    "canonical_mutation_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normal_runtime(value: str) -> str:
    return str(value or "").strip().lower()


def _capability_payload(caps: RuntimeCapabilities | None) -> dict[str, Any] | None:
    if caps is None:
        return None
    return {
        "runtime_name": caps.runtime_name,
        "bus_name": caps.bus_name,
        "display_name": caps.display_name,
        "description": caps.description,
        "personal_runtime_name": caps.personal_runtime_name,
        "retained_runtime_name": caps.retained_runtime_name,
        "legacy_personal_runtime_names": caps.legacy_personal_runtime_names,
        "handles": [
            {"task_type": cap.task_type, "priority": cap.priority, "notes": cap.notes}
            for cap in caps.handles
        ],
        "max_concurrent_tasks": caps.max_concurrent_tasks,
        "heartbeat_stale_seconds": caps.heartbeat_stale_seconds,
        "priority_ceiling": caps.priority_ceiling,
    }


def _find_capabilities(vault_root: Path, runtime: str) -> tuple[RuntimeCapabilities | None, list[str]]:
    warnings: list[str] = []
    try:
        all_caps = load_all_capabilities(vault_root)
    except CapabilityError as exc:
        return None, [f"capability_load_error:{exc}"]

    wanted = _normal_runtime(runtime)
    for runtime_name, caps in all_caps.items():
        aliases = {
            _normal_runtime(runtime_name),
            _normal_runtime(caps.bus_name),
            _normal_runtime(caps.personal_runtime_name),
            _normal_runtime(caps.retained_runtime_name),
            *{_normal_runtime(item) for item in caps.legacy_personal_runtime_names},
        }
        aliases.discard("")
        if wanted in aliases:
            return caps, warnings
    return None, warnings


def _liveness_payload(vault_root: Path, caps: RuntimeCapabilities | None) -> dict[str, Any]:
    if caps is None:
        return {
            "registered": False,
            "is_stale": True,
            "last_seen": None,
            "status": None,
            "health": None,
            "age_seconds": None,
        }
    try:
        live = get_runtime_liveness(vault_root).get(caps.bus_name)
    except Exception as exc:  # pragma: no cover - defensive fail-closed path
        return {
            "registered": True,
            "is_stale": True,
            "last_seen": None,
            "status": None,
            "health": None,
            "age_seconds": None,
            "error": f"liveness_read_error:{exc}",
        }
    if live is None:
        return {
            "registered": True,
            "is_stale": True,
            "last_seen": None,
            "status": None,
            "health": None,
            "age_seconds": None,
        }
    return {
        "registered": True,
        "is_stale": live.is_stale,
        "last_seen": live.last_seen,
        "status": live.status,
        "health": live.health,
        "age_seconds": live.age_seconds,
        "stale_threshold_seconds": live.stale_threshold_seconds,
    }


def _adapter_readiness(vault_root: Path, runtime: str, caps: RuntimeCapabilities | None) -> dict[str, Any] | None:
    runtime_key = _normal_runtime(runtime)
    cap_key = _normal_runtime(caps.runtime_name if caps else "")
    bus_key = _normal_runtime(caps.bus_name if caps else "")
    if "codex" not in {runtime_key, cap_key, bus_key}:
        return None

    readiness = get_codex_daemon_readiness(vault_root)
    return {
        "adapter": "codex",
        "ok": bool(readiness.get("ok")),
        "runtime_instance_id": readiness.get("runtime_instance_id"),
        "blocking_reasons": list(readiness.get("blocking_reasons") or []),
        "capability_task_types": list(readiness.get("capability_task_types") or []),
        "smoke_command": readiness.get("smoke_command"),
        "live_command": readiness.get("live_command"),
    }


def build_agent_harness_readiness(
    vault_root: str | Path,
    *,
    runtime: str = "hermes",
) -> dict[str, Any]:
    """Build a fail-closed, read-only readiness contract for one harness runtime."""

    root = Path(vault_root).resolve()
    caps, warnings = _find_capabilities(root, runtime)
    liveness = _liveness_payload(root, caps)
    adapter = _adapter_readiness(root, runtime, caps)

    blocked_reasons: list[str] = []
    if caps is None:
        blocked_reasons.append("runtime_capability_manifest_missing")
    if caps is not None and not caps.handles:
        blocked_reasons.append("runtime_declares_no_task_capabilities")
    if liveness.get("is_stale"):
        blocked_reasons.append("runtime_heartbeat_missing_or_stale")
    if adapter is not None and not adapter.get("ok"):
        blocked_reasons.append("adapter_not_ready")

    harness_status = "ready_for_operator_gated_activation" if not blocked_reasons else "blocked"

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(root),
        "read_only": True,
        "runtime_id": runtime,
        "runtime_bus_name": caps.bus_name if caps else None,
        "harness_status": harness_status,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": warnings,
        "required_evidence": REQUIRED_EVIDENCE,
        "capability_manifest": _capability_payload(caps),
        "liveness": liveness,
        "adapter_readiness": adapter,
        "tool_calling": {
            "tool_calling_posture": "inspect_only_until_gated_execution",
            "tools_callable_now": False,
            "requires_operator_gate": True,
            "requires_fresh_agent_bus_heartbeat": True,
            "requires_runtime_capability_manifest": True,
            "requires_adapter_specific_readiness": adapter is not None,
        },
        "next_actions": _next_actions(caps, liveness, adapter, blocked_reasons),
        "authority": dict(AUTHORITY),
    }


def _next_actions(
    caps: RuntimeCapabilities | None,
    liveness: dict[str, Any],
    adapter: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> list[str]:
    actions: list[str] = []
    if caps is None:
        actions.append("Add runtime/<runtime>/capabilities.yaml before exposing this harness as a ChaseOS worker.")
    if "runtime_heartbeat_missing_or_stale" in blocked_reasons:
        runtime = caps.bus_name if caps else "<runtime>"
        actions.append(
            f"Start or refresh the harness heartbeat: python -m chaseos agent-bus heartbeat --runtime {runtime} --status idle --health ok --json"
        )
    if adapter is not None and not adapter.get("ok"):
        actions.append("Resolve adapter readiness blockers before enabling live harness subprocess/tool calls.")
        if adapter.get("smoke_command"):
            actions.append(f"Run adapter smoke without live tool calls: {adapter['smoke_command']}")
    if not actions:
        actions.append("Ready for the next pass: add an operator-gated activation/launch contract; do not auto-execute tools from this read-only surface.")
    return actions
