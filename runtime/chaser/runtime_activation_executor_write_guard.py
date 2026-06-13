"""N24 ChaserAgent runtime activation executor write guard.

This scoped writer follows N23 and writes only the exact-once runtime activation
marker, activation state record, and append-only activation executor audit event.
It does not activate a live ChaserAgent runtime, bind terminal tools, execute a
terminal command, mutate Agent Bus state, call providers, or write canonical
ChaseOS memory/state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_executor_design import (
    build_chaser_runtime_activation_executor_design,
)


SURFACE = "chaser_runtime_activation_executor_write_guard"
SCHEMA_VERSION = "chaser_runtime_activation_executor_write_guard.v1"
MARKER_SCHEMA_VERSION = "chaser_runtime_activation_marker.v1"
STATE_SCHEMA_VERSION = "chaser_runtime_activation_state.v1"
AUDIT_SCHEMA_VERSION = "chaser_runtime_activation_executor_audit.v1"
NEXT_PASS = "terminal-n25-chaser-runtime-activation-state-readiness"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority(
    *,
    marker_write: bool = False,
    state_write: bool = False,
    audit_write: bool = False,
) -> dict[str, bool]:
    return {
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_toolset_binding_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": False,
        "approval_decision_write_now": False,
        "approval_consumption_now": False,
        "exact_once_marker_write_now": marker_write,
        "activation_state_write_now": state_write,
        "activation_audit_write_now": audit_write,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _blocked_actions() -> list[str]:
    return [
        "mutate approval request status",
        "activate live ChaserAgent runtime",
        "activate Chaser profile as executable authority",
        "activate Chaser toolset as executable authority",
        "bind terminal tools to ChaserAgent",
        "execute terminal command",
        "expose Studio terminal execution",
        "write or claim Agent Bus tasks",
        "call provider or model APIs",
        "write canonical ChaseOS memory/state",
        "mutate host startup/autostart/service state",
    ]


def _scoped_path(root: Path, rel_path: str, label: str) -> Path:
    if not rel_path:
        raise ValueError(f"{label}_path_missing")
    path = (root / rel_path).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label}_path_escapes_vault") from exc
    return path


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _base_result(
    *,
    root: Path,
    approval_id: str,
    actor: str,
    design: dict[str, Any],
    status: str,
    ok: bool,
    blockers: list[str],
    write_activation_state_requested: bool,
    confirm_runtime_activation_record: bool,
    authority: dict[str, bool] | None = None,
) -> dict[str, Any]:
    marker = design.get("future_activation_marker_preview")
    if not isinstance(marker, dict):
        marker = {}
    state = design.get("future_activation_state_preview")
    if not isinstance(state, dict):
        state = {}
    audit = design.get("future_activation_audit_preview")
    if not isinstance(audit, dict):
        audit = {}
    return {
        "ok": ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": design.get("activation_approval_id") or approval_id,
        "activation_approval_preview_id": design.get("activation_approval_preview_id"),
        "approval_path": design.get("approval_path"),
        "approval_status": design.get("approval_status"),
        "approval_status_after": design.get("approval_status"),
        "profile_id": design.get("profile_id"),
        "toolset_id": design.get("toolset_id"),
        "actor": actor,
        "write_guard_status": status,
        "blockers": blockers,
        "write_activation_state_requested": write_activation_state_requested,
        "confirm_runtime_activation_record": confirm_runtime_activation_record,
        "ready_for_activation_executor_write_now": (
            design.get("ready_for_activation_executor_write_guard_next_pass") is True
        ),
        "activation_executor_write_guard_available": True,
        "activation_executor_available": True,
        "activation_executor_scope": (
            "exact_once_activation_marker_state_and_audit_only"
        ),
        "design": {
            "surface": design.get("surface"),
            "ok": design.get("ok"),
            "activation_executor_design_status": design.get(
                "activation_executor_design_status"
            ),
            "ready_for_activation_executor_write_guard_next_pass": design.get(
                "ready_for_activation_executor_write_guard_next_pass"
            ),
            "approval_status": design.get("approval_status"),
        },
        "runtime_activation_marker": {
            "path": marker.get("path") or "",
            "exists_before": bool(marker.get("exists")),
            "marker_written": False,
            "create_new_only": True,
            "exact_once": True,
        },
        "runtime_activation_state": {
            "path": state.get("path") or "",
            "exists_before": bool(state.get("exists")),
            "state_written": False,
            "create_new_only": True,
        },
        "runtime_activation_audit": {
            "path": audit.get("path") or "",
            "event_type": "chaser_runtime_activation_executor",
            "audit_written": False,
            "append_only": True,
        },
        "approval_decision_written": False,
        "approval_status_mutated": False,
        "approval_consumed": False,
        "activation_marker_written": False,
        "activation_state_written": False,
        "activation_audit_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "live_runtime_activated": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "terminal_binding_performed": False,
        "terminal_execution_performed": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": _blocked_actions(),
        "denied_effects": _blocked_actions(),
        "authority": authority or _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "activation_executor_write_guard_stops_before_live_runtime_activation",
            "no_live_chaser_runtime_activation",
            "no_profile_or_toolset_executable_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": NEXT_PASS,
        "boundary": (
            "activation executor write guard only; writes at most the "
            "exact-once runtime activation marker, activation state record, "
            "and append-only activation executor audit event. It performs no "
            "live runtime activation, terminal binding, terminal execution, "
            "Agent Bus mutation, provider call, host mutation, or canonical "
            "writeback."
        ),
    }


def build_chaser_runtime_activation_executor_write_guard(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    actor: str = "operator",
    write_activation_state: bool = False,
    confirm_runtime_activation_record: bool = False,
    request_agent_bus_mutation: bool = False,
    request_provider_dispatch: bool = False,
) -> dict[str, Any]:
    """Preview or write the N24 activation marker/state/audit record."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    actor_value = actor or "operator"
    design = build_chaser_runtime_activation_executor_design(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        actor=actor_value,
        request_agent_bus_mutation=request_agent_bus_mutation,
        request_provider_dispatch=request_provider_dispatch,
    )
    marker = design.get("future_activation_marker_preview")
    if not isinstance(marker, dict):
        marker = {}
    state = design.get("future_activation_state_preview")
    if not isinstance(state, dict):
        state = {}
    audit = design.get("future_activation_audit_preview")
    if not isinstance(audit, dict):
        audit = {}

    blockers: list[str] = []
    if design.get("ok") is not True:
        blockers.append("activation_executor_design_unavailable")
        blockers.extend(str(item) for item in design.get("blockers") or [])
    if design.get("ready_for_activation_executor_write_guard_next_pass") is not True:
        blockers.append(
            str(
                design.get("activation_executor_design_status")
                or "activation_executor_design_not_ready"
            )
        )
    if marker.get("exists") is True:
        blockers.append("runtime_activation_marker_already_present")
    if state.get("exists") is True:
        blockers.append("runtime_activation_state_already_present")

    if not write_activation_state:
        status = (
            "activation_executor_write_guard_ready_no_write"
            if not blockers
            else "blocked_activation_executor_write_guard_preview"
        )
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status=status,
            ok=design.get("ok") is True,
            blockers=blockers,
            write_activation_state_requested=False,
            confirm_runtime_activation_record=confirm_runtime_activation_record,
        )

    if not confirm_runtime_activation_record:
        blockers.append("explicit_runtime_activation_record_confirmation_required")

    if blockers:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="blocked_activation_executor_write_guard",
            ok=False,
            blockers=blockers,
            write_activation_state_requested=True,
            confirm_runtime_activation_record=confirm_runtime_activation_record,
        )

    try:
        marker_path = _scoped_path(root, str(marker.get("path") or ""), "marker")
        state_path = _scoped_path(root, str(state.get("path") or ""), "state")
        audit_path = _scoped_path(root, str(audit.get("path") or ""), "audit")
    except ValueError as exc:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="blocked_activation_executor_write_guard",
            ok=False,
            blockers=[str(exc)],
            write_activation_state_requested=True,
            confirm_runtime_activation_record=True,
        )

    activated_at = _now_iso()
    activation_approval_id = str(design.get("activation_approval_id") or requested_id)
    preview_id = design.get("activation_approval_preview_id")
    marker_payload = {
        "schema_version": MARKER_SCHEMA_VERSION,
        "record_type": "chaser_runtime_activation_marker",
        "status": "activation_marker_written_live_runtime_still_blocked",
        "runtime_id": "chaser",
        "profile_id": design.get("profile_id"),
        "toolset_id": design.get("toolset_id"),
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id,
        "approval_status": design.get("approval_status"),
        "approval_path": design.get("approval_path"),
        "activation_state_path": state_path.relative_to(root).as_posix(),
        "activation_recorded_at": activated_at,
        "activation_recorded_by": actor_value,
        "write_guard_surface": SURFACE,
        "live_runtime_activated": False,
        "runtime_activation_performed": False,
        "profile_activation_performed": False,
        "toolset_activation_performed": False,
        "terminal_binding_performed": False,
        "terminal_execution_performed": False,
        "studio_execution_performed": False,
        "agent_bus_mutation_performed": False,
        "provider_call_performed": False,
        "canonical_writeback_performed": False,
        "external_network_performed": False,
        "host_mutation_performed": False,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
    }
    state_payload = dict(design.get("future_activation_record_schema") or {})
    state_payload.update(
        {
            "schema_version": STATE_SCHEMA_VERSION,
            "record_type": "chaser_runtime_activation_state",
            "status": "activation_state_written_live_runtime_still_blocked",
            "runtime_id": "chaser",
            "profile_id": design.get("profile_id"),
            "toolset_id": design.get("toolset_id"),
            "activation_approval_id": activation_approval_id,
            "activation_approval_preview_id": preview_id,
            "approval_status": design.get("approval_status"),
            "approval_path": design.get("approval_path"),
            "activation_marker_path": marker_path.relative_to(root).as_posix(),
            "activation_audit_path": audit_path.relative_to(root).as_posix(),
            "activation_recorded_at": activated_at,
            "activation_recorded_by": actor_value,
            "write_guard_surface": SURFACE,
            "live_runtime_activated": False,
            "runtime_activation_performed": False,
            "profile_activation_performed": False,
            "toolset_activation_performed": False,
            "terminal_binding_performed": False,
            "terminal_execution_performed": False,
            "studio_execution_performed": False,
            "agent_bus_mutation_performed": False,
            "provider_call_performed": False,
            "canonical_writeback_performed": False,
            "external_network_performed": False,
            "host_mutation_performed": False,
            "terminal_output_trusted": False,
            "trust_tier": "Tier 4",
        }
    )
    try:
        _write_json_exclusive(marker_path, marker_payload)
        _write_json_exclusive(state_path, state_payload)
    except FileExistsError:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="duplicate_blocked_runtime_activation_record_present",
            ok=False,
            blockers=["runtime_activation_record_already_present"],
            write_activation_state_requested=True,
            confirm_runtime_activation_record=True,
        )

    audit_event = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_type": "chaser_runtime_activation_executor",
        "surface": SURFACE,
        "generated_at": activated_at,
        "actor": actor_value,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id,
        "approval_status": design.get("approval_status"),
        "approval_path": design.get("approval_path"),
        "marker_path": marker_path.relative_to(root).as_posix(),
        "state_path": state_path.relative_to(root).as_posix(),
        "live_runtime_activated": False,
        "runtime_activation_performed": False,
        "profile_activation_performed": False,
        "toolset_activation_performed": False,
        "terminal_binding_performed": False,
        "terminal_execution_performed": False,
        "studio_execution_performed": False,
        "agent_bus_mutation_performed": False,
        "provider_call_performed": False,
        "canonical_writeback_performed": False,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
    }
    _append_jsonl(audit_path, audit_event)

    result = _base_result(
        root=root,
        approval_id=requested_id,
        actor=actor_value,
        design=design,
        status="runtime_activation_marker_state_and_audit_written_live_runtime_blocked",
        ok=True,
        blockers=[],
        write_activation_state_requested=True,
        confirm_runtime_activation_record=True,
        authority=_authority(marker_write=True, state_write=True, audit_write=True),
    )
    result["activation_marker_written"] = True
    result["activation_state_written"] = True
    result["activation_audit_written"] = True
    result["writes_performed"] = True
    result["files_modified"] = True
    result["runtime_activation_marker"].update(
        {
            "exists_after": marker_path.exists(),
            "marker_written": True,
        }
    )
    result["runtime_activation_state"].update(
        {
            "exists_after": state_path.exists(),
            "state_written": True,
        }
    )
    result["runtime_activation_audit"].update(
        {
            "audit_written": True,
            "last_event_type": audit_event["event_type"],
        }
    )
    return result
