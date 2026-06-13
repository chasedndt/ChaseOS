"""N27 ChaserAgent profile/toolset activation write guard.

This scoped writer follows N26 and writes only the exact-once profile/toolset
activation marker, profile state record, toolset state record, and append-only
audit event. It does not activate a live ChaserAgent runtime, bind terminal
tools, execute a terminal command, mutate Agent Bus state, call providers, or
write canonical ChaseOS memory/state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_profile_toolset_activation_design import (
    build_chaser_runtime_profile_toolset_activation_design,
)


SURFACE = "chaser_runtime_profile_toolset_activation_write_guard"
SCHEMA_VERSION = "chaser_runtime_profile_toolset_activation_write_guard.v1"
MARKER_SCHEMA_VERSION = "chaser_profile_toolset_activation_marker.v1"
PROFILE_STATE_SCHEMA_VERSION = "chaser_profile_activation_state.v1"
TOOLSET_STATE_SCHEMA_VERSION = "chaser_toolset_activation_state.v1"
AUDIT_SCHEMA_VERSION = "chaser_profile_toolset_activation_audit.v1"
NEXT_PASS = "terminal-n28-chaser-runtime-profile-toolset-activation-readiness"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority(
    *,
    marker_write: bool = False,
    profile_state_write: bool = False,
    toolset_state_write: bool = False,
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
        "profile_activation_state_write_now": profile_state_write,
        "toolset_activation_state_write_now": toolset_state_write,
        "profile_toolset_activation_audit_write_now": audit_write,
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
        "consume approvals",
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


def _artifact(design: dict[str, Any], key: str) -> dict[str, Any]:
    artifacts = design.get("future_profile_toolset_activation_artifacts")
    if not isinstance(artifacts, dict):
        return {}
    value = artifacts.get(key)
    return value if isinstance(value, dict) else {}


def _base_result(
    *,
    root: Path,
    approval_id: str,
    actor: str,
    design: dict[str, Any],
    status: str,
    ok: bool,
    blockers: list[str],
    write_profile_toolset_activation_requested: bool,
    confirm_profile_toolset_activation_record: bool,
    authority: dict[str, bool] | None = None,
) -> dict[str, Any]:
    marker = _artifact(design, "profile_toolset_activation_marker")
    profile_state = _artifact(design, "profile_activation_state")
    toolset_state = _artifact(design, "toolset_activation_state")
    audit = _artifact(design, "profile_toolset_activation_audit")
    return {
        "ok": ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": design.get("activation_approval_id") or approval_id,
        "activation_approval_preview_id": design.get("activation_approval_preview_id"),
        "approval_status": design.get("approval_status"),
        "approval_status_after": design.get("approval_status"),
        "profile_id": design.get("profile_id"),
        "toolset_id": design.get("toolset_id"),
        "actor": actor,
        "write_guard_status": status,
        "blockers": blockers,
        "write_profile_toolset_activation_requested": (
            write_profile_toolset_activation_requested
        ),
        "confirm_profile_toolset_activation_record": (
            confirm_profile_toolset_activation_record
        ),
        "ready_for_profile_toolset_activation_write_now": (
            design.get("ready_for_profile_toolset_activation_write_guard_next_pass")
            is True
        ),
        "profile_toolset_activation_design_available": True,
        "profile_toolset_activation_write_guard_available": True,
        "profile_toolset_activation_write_guard_scope": (
            "exact_once_marker_profile_state_toolset_state_and_append_only_audit_only"
        ),
        "design": {
            "surface": design.get("surface"),
            "ok": design.get("ok"),
            "profile_toolset_activation_design_status": design.get(
                "profile_toolset_activation_design_status"
            ),
            "ready_for_profile_toolset_activation_write_guard_next_pass": design.get(
                "ready_for_profile_toolset_activation_write_guard_next_pass"
            ),
            "approval_status": design.get("approval_status"),
        },
        "profile_toolset_activation_marker": {
            "path": marker.get("path") or "",
            "exists_before": bool(marker.get("exists")),
            "marker_written": False,
            "create_new_only": True,
            "exact_once": True,
        },
        "profile_activation_state": {
            "path": profile_state.get("path") or "",
            "exists_before": bool(profile_state.get("exists")),
            "state_written": False,
            "create_new_only": True,
        },
        "toolset_activation_state": {
            "path": toolset_state.get("path") or "",
            "exists_before": bool(toolset_state.get("exists")),
            "state_written": False,
            "create_new_only": True,
        },
        "profile_toolset_activation_audit": {
            "path": audit.get("path") or "",
            "event_type": "chaser_profile_toolset_activation_write_guard",
            "audit_written": False,
            "append_only": True,
        },
        "approval_decision_written": False,
        "approval_status_mutated": False,
        "approval_consumed": False,
        "profile_toolset_activation_marker_written": False,
        "profile_activation_state_written": False,
        "toolset_activation_state_written": False,
        "profile_toolset_activation_audit_written": False,
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
            "profile_toolset_activation_write_guard_stops_before_live_activation",
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
            "profile/toolset activation write guard only; writes at most the "
            "exact-once profile/toolset marker, profile state record, toolset "
            "state record, and append-only audit event. It performs no live "
            "runtime activation, executable profile/toolset activation, "
            "terminal binding, terminal execution, Agent Bus mutation, "
            "provider call, host mutation, or canonical writeback."
        ),
    }


def build_chaser_runtime_profile_toolset_activation_write_guard(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    expected_profile_id: str = "",
    expected_toolset_id: str = "",
    actor: str = "operator",
    write_profile_toolset_activation: bool = False,
    confirm_profile_toolset_activation_record: bool = False,
) -> dict[str, Any]:
    """Preview or write the N27 profile/toolset activation marker/state/audit."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    actor_value = actor or "operator"
    design = build_chaser_runtime_profile_toolset_activation_design(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        expected_profile_id=expected_profile_id,
        expected_toolset_id=expected_toolset_id,
        actor=actor_value,
    )

    marker = _artifact(design, "profile_toolset_activation_marker")
    profile_state = _artifact(design, "profile_activation_state")
    toolset_state = _artifact(design, "toolset_activation_state")
    audit = _artifact(design, "profile_toolset_activation_audit")

    blockers: list[str] = []
    if design.get("ok") is not True:
        blockers.append("profile_toolset_activation_design_unavailable")
        blockers.extend(str(item) for item in design.get("blockers") or [])
    if design.get("ready_for_profile_toolset_activation_write_guard_next_pass") is not True:
        blockers.append(
            str(
                design.get("profile_toolset_activation_design_status")
                or "profile_toolset_activation_design_not_ready"
            )
        )
    if marker.get("exists") is True:
        blockers.append("profile_toolset_activation_marker_already_present")
    if profile_state.get("exists") is True:
        blockers.append("profile_activation_state_already_present")
    if toolset_state.get("exists") is True:
        blockers.append("toolset_activation_state_already_present")

    if not write_profile_toolset_activation:
        status = (
            "profile_toolset_activation_write_guard_ready_no_write"
            if not blockers
            else "blocked_profile_toolset_activation_write_guard_preview"
        )
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status=status,
            ok=design.get("ok") is True,
            blockers=blockers,
            write_profile_toolset_activation_requested=False,
            confirm_profile_toolset_activation_record=(
                confirm_profile_toolset_activation_record
            ),
        )

    if not confirm_profile_toolset_activation_record:
        blockers.append("explicit_profile_toolset_activation_record_confirmation_required")

    if blockers:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="blocked_profile_toolset_activation_write_guard",
            ok=False,
            blockers=blockers,
            write_profile_toolset_activation_requested=True,
            confirm_profile_toolset_activation_record=(
                confirm_profile_toolset_activation_record
            ),
        )

    try:
        marker_path = _scoped_path(root, str(marker.get("path") or ""), "marker")
        profile_state_path = _scoped_path(
            root, str(profile_state.get("path") or ""), "profile_state"
        )
        toolset_state_path = _scoped_path(
            root, str(toolset_state.get("path") or ""), "toolset_state"
        )
        audit_path = _scoped_path(root, str(audit.get("path") or ""), "audit")
    except ValueError as exc:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="blocked_profile_toolset_activation_write_guard",
            ok=False,
            blockers=[str(exc)],
            write_profile_toolset_activation_requested=True,
            confirm_profile_toolset_activation_record=True,
        )

    recorded_at = _now_iso()
    activation_approval_id = str(design.get("activation_approval_id") or requested_id)
    preview_id = design.get("activation_approval_preview_id")
    profile_id = design.get("profile_id")
    toolset_id = design.get("toolset_id")
    activation_state = design.get("activation_state_readiness")
    if not isinstance(activation_state, dict):
        activation_state = {}

    shared_effects = {
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
    marker_payload = {
        "schema_version": MARKER_SCHEMA_VERSION,
        "record_type": "chaser_profile_toolset_activation_marker",
        "status": "profile_toolset_activation_marker_written_live_runtime_still_blocked",
        "runtime_id": "chaser",
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id,
        "approval_status": design.get("approval_status"),
        "profile_activation_state_path": profile_state_path.relative_to(root).as_posix(),
        "toolset_activation_state_path": toolset_state_path.relative_to(root).as_posix(),
        "profile_toolset_activation_audit_path": audit_path.relative_to(root).as_posix(),
        "runtime_activation_marker_path": (
            (activation_state.get("runtime_activation_marker") or {}).get("path")
            if isinstance(activation_state.get("runtime_activation_marker"), dict)
            else ""
        ),
        "runtime_activation_state_path": (
            (activation_state.get("runtime_activation_state") or {}).get("path")
            if isinstance(activation_state.get("runtime_activation_state"), dict)
            else ""
        ),
        "activation_recorded_at": recorded_at,
        "activation_recorded_by": actor_value,
        "write_guard_surface": SURFACE,
        **shared_effects,
    }
    profile_state_payload = {
        "schema_version": PROFILE_STATE_SCHEMA_VERSION,
        "record_type": "chaser_profile_activation_state",
        "status": "profile_activation_state_written_executable_activation_still_blocked",
        "runtime_id": "chaser",
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id,
        "approval_status": design.get("approval_status"),
        "profile_view": design.get("profile_view") or {},
        "profile_validation": design.get("profile_validation") or {},
        "profile_toolset_activation_marker_path": marker_path.relative_to(root).as_posix(),
        "toolset_activation_state_path": toolset_state_path.relative_to(root).as_posix(),
        "profile_toolset_activation_audit_path": audit_path.relative_to(root).as_posix(),
        "activation_recorded_at": recorded_at,
        "activation_recorded_by": actor_value,
        "write_guard_surface": SURFACE,
        **shared_effects,
    }
    toolset_state_payload = {
        "schema_version": TOOLSET_STATE_SCHEMA_VERSION,
        "record_type": "chaser_toolset_activation_state",
        "status": "toolset_activation_state_written_executable_activation_still_blocked",
        "runtime_id": "chaser",
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id,
        "approval_status": design.get("approval_status"),
        "toolset_view": design.get("toolset_view") or {},
        "toolset_validation": design.get("toolset_validation") or {},
        "profile_toolset_activation_marker_path": marker_path.relative_to(root).as_posix(),
        "profile_activation_state_path": profile_state_path.relative_to(root).as_posix(),
        "profile_toolset_activation_audit_path": audit_path.relative_to(root).as_posix(),
        "activation_recorded_at": recorded_at,
        "activation_recorded_by": actor_value,
        "write_guard_surface": SURFACE,
        **shared_effects,
    }

    try:
        _write_json_exclusive(marker_path, marker_payload)
        _write_json_exclusive(profile_state_path, profile_state_payload)
        _write_json_exclusive(toolset_state_path, toolset_state_payload)
    except FileExistsError:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="duplicate_blocked_profile_toolset_activation_record_present",
            ok=False,
            blockers=["profile_toolset_activation_record_already_present"],
            write_profile_toolset_activation_requested=True,
            confirm_profile_toolset_activation_record=True,
        )

    audit_event = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_type": "chaser_profile_toolset_activation_write_guard",
        "surface": SURFACE,
        "generated_at": recorded_at,
        "actor": actor_value,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id,
        "approval_status": design.get("approval_status"),
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "marker_path": marker_path.relative_to(root).as_posix(),
        "profile_state_path": profile_state_path.relative_to(root).as_posix(),
        "toolset_state_path": toolset_state_path.relative_to(root).as_posix(),
        **shared_effects,
    }
    _append_jsonl(audit_path, audit_event)

    result = _base_result(
        root=root,
        approval_id=requested_id,
        actor=actor_value,
        design=design,
        status=(
            "profile_toolset_activation_marker_state_and_audit_written_"
            "live_runtime_blocked"
        ),
        ok=True,
        blockers=[],
        write_profile_toolset_activation_requested=True,
        confirm_profile_toolset_activation_record=True,
        authority=_authority(
            marker_write=True,
            profile_state_write=True,
            toolset_state_write=True,
            audit_write=True,
        ),
    )
    result["profile_toolset_activation_marker_written"] = True
    result["profile_activation_state_written"] = True
    result["toolset_activation_state_written"] = True
    result["profile_toolset_activation_audit_written"] = True
    result["writes_performed"] = True
    result["files_modified"] = True
    result["profile_toolset_activation_marker"].update(
        {
            "exists_after": marker_path.exists(),
            "marker_written": True,
        }
    )
    result["profile_activation_state"].update(
        {
            "exists_after": profile_state_path.exists(),
            "state_written": True,
        }
    )
    result["toolset_activation_state"].update(
        {
            "exists_after": toolset_state_path.exists(),
            "state_written": True,
        }
    )
    result["profile_toolset_activation_audit"].update(
        {
            "audit_written": True,
            "last_event_type": audit_event["event_type"],
        }
    )
    return result
