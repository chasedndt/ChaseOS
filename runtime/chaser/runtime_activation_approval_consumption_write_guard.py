"""N21 ChaserAgent runtime activation approval consumption write guard.

This is the scoped approval-consumption marker/audit writer after N20. It can
write the exact-once consumption marker and append the activation-consumption
audit event only when the N20 design is ready and explicit confirmation is
present. It stops before ChaserAgent runtime/profile/toolset activation,
terminal binding, terminal execution, Agent Bus mutation, provider calls, and
canonical writeback.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_approval_consumption_design import (
    build_chaser_runtime_activation_approval_consumption_design,
)
from runtime.studio.service import StudioService


SURFACE = "chaser_runtime_activation_approval_consumption_write_guard"
SCHEMA_VERSION = "chaser_runtime_activation_approval_consumption_write_guard.v1"
MARKER_SCHEMA_VERSION = "chaser_runtime_activation_approval_consumption_marker.v1"
AUDIT_SCHEMA_VERSION = "chaser_runtime_activation_approval_consumption_audit.v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority(
    *,
    approval_consumption: bool = False,
    marker_write: bool = False,
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
        "approval_consumption_now": approval_consumption,
        "exact_once_marker_write_now": marker_write,
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
        "activate ChaserAgent runtime",
        "activate Chaser profile",
        "activate Chaser toolset",
        "bind terminal tools to ChaserAgent",
        "execute terminal command",
        "expose Studio terminal execution",
        "write or claim Agent Bus tasks",
        "call provider or model APIs",
        "write canonical ChaseOS memory/state",
        "mutate host startup/autostart/service state",
    ]


def _base_result(
    *,
    root: Path,
    approval_id: str,
    actor: str,
    design: dict[str, Any],
    status: str,
    ok: bool,
    blockers: list[str],
    write_consumption_marker_requested: bool,
    confirm_activation_approval_consumption: bool,
    authority: dict[str, bool] | None = None,
) -> dict[str, Any]:
    marker = design.get("consumer_marker_preview")
    if not isinstance(marker, dict):
        marker = {}
    audit = design.get("audit_event_preview")
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
        "write_consumption_marker_requested": write_consumption_marker_requested,
        "confirm_activation_approval_consumption": confirm_activation_approval_consumption,
        "ready_for_activation_consumption_write_now": (
            design.get("ready_for_activation_consumption_write_guard_next_pass") is True
        ),
        "activation_approval_consumption_write_guard_available": True,
        "activation_approval_consumption_executor_available": False,
        "activation_approval_consumption_available": True,
        "activation_consumer_implemented": True,
        "design": {
            "surface": design.get("surface"),
            "ok": design.get("ok"),
            "consumption_design_status": design.get("consumption_design_status"),
            "ready_for_activation_consumption_write_guard_next_pass": design.get(
                "ready_for_activation_consumption_write_guard_next_pass"
            ),
            "decision_preflight_status": design.get("decision_preflight_status"),
            "approval_status": design.get("approval_status"),
        },
        "exact_once_marker": {
            "path": marker.get("path") or "",
            "exists_before": bool(marker.get("exists")),
            "marker_written": False,
            "create_new_only": True,
            "exact_once": True,
        },
        "activation_audit": {
            "path": audit.get("path") or "",
            "event_type": "chaser_runtime_activation_approval_consumption",
            "audit_written": False,
            "append_only": True,
        },
        "approval_decision_written": False,
        "approval_status_mutated": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "activation_audit_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": _blocked_actions(),
        "denied_effects": _blocked_actions(),
        "authority": authority or _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "activation_consumption_write_guard_stops_before_runtime_activation",
            "no_chaser_runtime_activation",
            "no_profile_or_toolset_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n22-chaser-runtime-activation-post-consumption-readiness"
        ),
        "boundary": (
            "activation approval consumption write guard only; writes at most "
            "the exact-once consumption marker and append-only audit event after "
            "approved preflight. It performs no approval status mutation, runtime "
            "activation, profile/toolset activation, terminal binding, terminal "
            "execution, Agent Bus mutation, provider call, host mutation, or "
            "canonical writeback."
        ),
    }


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


def build_chaser_runtime_activation_approval_consumption_write_guard(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    actor: str = "operator",
    write_consumption_marker: bool = False,
    confirm_activation_approval_consumption: bool = False,
) -> dict[str, Any]:
    """Preview or write the N21 activation approval consumption marker/audit."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    actor_value = actor or "operator"
    design = build_chaser_runtime_activation_approval_consumption_design(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        actor=actor_value,
    )
    design_ready = (
        design.get("ready_for_activation_consumption_write_guard_next_pass") is True
    )
    marker = design.get("consumer_marker_preview")
    if not isinstance(marker, dict):
        marker = {}
    audit = design.get("audit_event_preview")
    if not isinstance(audit, dict):
        audit = {}

    blockers: list[str] = []
    if design.get("ok") is not True:
        blockers.append("activation_consumption_design_unavailable")
    if not design_ready:
        blockers.append(
            str(design.get("consumption_design_status") or "activation_consumption_design_not_ready")
        )
    if marker.get("exists") is True:
        blockers.append("exact_once_marker_already_present")

    if not write_consumption_marker:
        status = (
            "activation_approval_consumption_write_guard_ready_no_write"
            if not blockers and design_ready
            else "blocked_activation_approval_consumption_write_guard_preview"
        )
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status=status,
            ok=design.get("ok") is True,
            blockers=blockers,
            write_consumption_marker_requested=False,
            confirm_activation_approval_consumption=confirm_activation_approval_consumption,
        )

    if not confirm_activation_approval_consumption:
        blockers.append("explicit_activation_approval_consumption_confirmation_required")

    if blockers:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="blocked_activation_approval_consumption_write_guard",
            ok=False,
            blockers=blockers,
            write_consumption_marker_requested=True,
            confirm_activation_approval_consumption=confirm_activation_approval_consumption,
        )

    try:
        marker_path = _scoped_path(root, str(marker.get("path") or ""), "marker")
        audit_path = _scoped_path(root, str(audit.get("path") or ""), "audit")
    except ValueError as exc:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="blocked_activation_approval_consumption_write_guard",
            ok=False,
            blockers=[str(exc)],
            write_consumption_marker_requested=True,
            confirm_activation_approval_consumption=True,
        )

    consumed_at = _now_iso()
    marker_payload = dict(design.get("consumer_record_schema") or {})
    marker_payload.update(
        {
            "schema_version": MARKER_SCHEMA_VERSION,
            "status": "consumed_marker_written_activation_still_blocked",
            "activation_approval_id": design.get("activation_approval_id") or requested_id,
            "activation_approval_preview_id": design.get("activation_approval_preview_id"),
            "approval_status": design.get("approval_status"),
            "approval_path": design.get("approval_path"),
            "approval_consumed_at": consumed_at,
            "approval_consumed_by": actor_value,
            "write_guard_surface": SURFACE,
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
    except FileExistsError:
        return _base_result(
            root=root,
            approval_id=requested_id,
            actor=actor_value,
            design=design,
            status="duplicate_blocked_activation_approval_consumption_marker_present",
            ok=False,
            blockers=["exact_once_marker_already_present"],
            write_consumption_marker_requested=True,
            confirm_activation_approval_consumption=True,
        )

    audit_event = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_type": "chaser_runtime_activation_approval_consumption",
        "surface": SURFACE,
        "generated_at": consumed_at,
        "actor": actor_value,
        "activation_approval_id": design.get("activation_approval_id") or requested_id,
        "activation_approval_preview_id": design.get("activation_approval_preview_id"),
        "approval_status": design.get("approval_status"),
        "approval_path": design.get("approval_path"),
        "marker_path": marker_path.relative_to(root).as_posix(),
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

    approval_after = StudioService(root).get_approval(requested_id)
    approval_status_after = approval_after.status if approval_after is not None else ""
    result = _base_result(
        root=root,
        approval_id=requested_id,
        actor=actor_value,
        design=design,
        status="activation_approval_consumption_marker_and_audit_written_activation_blocked",
        ok=True,
        blockers=[],
        write_consumption_marker_requested=True,
        confirm_activation_approval_consumption=True,
        authority=_authority(
            approval_consumption=True,
            marker_write=True,
            audit_write=True,
        ),
    )
    result["approval_status_after"] = approval_status_after
    result["approval_consumed"] = True
    result["activation_consumption_marker_written"] = True
    result["activation_audit_written"] = True
    result["writes_performed"] = True
    result["files_modified"] = True
    result["exact_once_marker"].update(
        {
            "exists_after": marker_path.exists(),
            "marker_written": True,
            "sha256_recorded": False,
        }
    )
    result["activation_audit"].update(
        {
            "audit_written": True,
            "last_event_type": audit_event["event_type"],
        }
    )
    return result
