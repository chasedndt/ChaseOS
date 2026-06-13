"""Exact-once local activation gate for VentureOps Mission Mode."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.ventureops.mission_runtime_claim_result_gate import (
    load_mission_runtime_claim_result_state,
)


ACTIVATION_APPROVAL_FILENAME = "mission-activation-execution-approved.json"
ACTIVATION_MARKER_FILENAME = "mission-activation-execution-consumption.json"
ACTIVATION_APPROVAL_TYPE = "ventureops-mission-activation-execution-approval"
ACTIVATION_MARKER_TYPE = "ventureops-mission-activation-execution-marker"
SURFACE_ID = "ventureops_mission_activation_gate"
APPROVED_NEXT_STEP = "move_local_mission_state_to_active"

FORBIDDEN_TRUE_AUTHORIZATION_FIELDS = (
    "provider_calls_authorized",
    "browser_actions_authorized",
    "browser_skill_activation_authorized",
    "external_side_effects_authorized",
    "crm_or_payment_mutation_authorized",
    "live_trading_authorized",
    "protected_file_edit_authorized",
    "canonical_promotion_authorized",
    "credential_or_secret_read_authorized",
    "workflow_evolution_apply_authorized",
    "followup_agent_bus_task_authorized",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_id(value: Any) -> str:
    normalized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in str(value or "").strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed[:96] or "mission"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return path.resolve().relative_to(vault_root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _resolve_workspace(vault_root: Path, mission_workspace: str | Path | None) -> Path:
    if mission_workspace is None:
        from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness

        readiness = build_mission_activation_readiness(vault_root)
        path = readiness.get("mission_workspace_path")
        if path:
            return (vault_root / str(path)).resolve()
        return (
            vault_root
            / "07_LOGS"
            / "VentureOps-Missions"
            / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
        ).resolve()
    raw = Path(mission_workspace)
    return raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()


def _resolve_target(vault_root: Path, path: str | Path) -> tuple[Path | None, str | None]:
    raw = Path(path)
    target = raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()
    try:
        target.relative_to(vault_root.resolve())
    except ValueError:
        return None, f"path escapes vault root: {path}"
    return target, None


def default_activation_approval_path(workspace: str | Path) -> Path:
    return Path(workspace) / ACTIVATION_APPROVAL_FILENAME


def default_activation_marker_path(workspace: str | Path) -> Path:
    return Path(workspace) / ACTIVATION_MARKER_FILENAME


def build_mission_activation_gate_approval(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    activation_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Build a local mission activation approval artifact without writing it."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    result_state = load_mission_runtime_claim_result_state(root, mission_workspace=workspace)
    manifest = _load_json(workspace / "mission-manifest.json") if (workspace / "mission-manifest.json").exists() else {}
    mission_id = str(manifest.get("mission_id") or result_state.get("mission_id") or "")
    activation_id = _safe_id(
        activation_id
        or f"{mission_id or 'mission'}-activation-execution-{datetime.now(timezone.utc).date().isoformat()}"
    )
    statement = " ".join(str(operator_approval_statement or "").strip().split())
    errors: list[str] = []
    if not statement:
        errors.append("operator_approval_statement is required")
    if manifest.get("status") == "active":
        errors.append("mission_manifest_already_active")
    if result_state.get("claim_result_consumed") is not True:
        errors.append("runtime_claim_result_gate_must_be_consumed_before_activation")
    if result_state.get("mission_result_ingested") is not True:
        errors.append("mission_runtime_result_must_be_ingested_before_activation")
    if result_state.get("agent_bus_task_closed") is not True:
        errors.append("agent_bus_task_must_be_closed_before_activation")

    approval = {
        "schema_version": "0.1",
        "type": ACTIVATION_APPROVAL_TYPE,
        "activation_id": activation_id,
        "approval_decision": "approved" if not errors else "pending",
        "approval_status": "approved" if not errors else "blocked",
        "approved_by": str(approved_by or "operator").strip() or "operator",
        "approved_at": _now_utc(),
        "operator_approval_statement": statement,
        "mission_id": mission_id,
        "mission_workspace_path": _vault_relative(workspace, root),
        "approved_next_step": APPROVED_NEXT_STEP,
        "runtime_claim_result_marker_path": result_state.get("claim_result_marker_path"),
        "mission_runtime_result_path": result_state.get("mission_runtime_result_path"),
        "agent_bus_task_id": result_state.get("agent_bus_task_id"),
        "approved_scope": [
            "move the local mission manifest status from draft to active",
            "move the mission state ledger into active local mission state",
            "record activation artifacts in workspace indexes",
            "preserve external delivery, provider, browser, credential, protected-file, workflow-evolution, and canonical-promotion blocks",
        ],
        "required_acknowledgements": [
            "This activation is local mission state only, not external execution",
            "Runtime claim/result ingestion and task closeout must already be complete",
            "Workflow evolution remains pending_review/unapplied",
            "Real client scope and external delivery remain separate future approvals",
        ],
        "consumption_policy": "exact_once",
        "consumable": not errors,
        "mission_activation_execution_authorized": not errors,
        "provider_calls_authorized": False,
        "browser_actions_authorized": False,
        "browser_skill_activation_authorized": False,
        "external_side_effects_authorized": False,
        "crm_or_payment_mutation_authorized": False,
        "live_trading_authorized": False,
        "protected_file_edit_authorized": False,
        "canonical_promotion_authorized": False,
        "credential_or_secret_read_authorized": False,
        "workflow_evolution_apply_authorized": False,
        "followup_agent_bus_task_authorized": False,
        "context_errors": list(dict.fromkeys(errors)),
    }
    approval["activation_digest"] = _sha256({key: value for key, value in approval.items() if key != "activation_digest"})
    return approval


def validate_mission_activation_gate_approval(
    approval: dict[str, Any],
    *,
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    errors: list[str] = []
    manifest = _load_json(workspace / "mission-manifest.json") if (workspace / "mission-manifest.json").exists() else {}
    mission_id = str(manifest.get("mission_id") or "")
    required = {
        "schema_version",
        "type",
        "activation_id",
        "approval_decision",
        "approval_status",
        "approved_by",
        "approved_at",
        "operator_approval_statement",
        "mission_id",
        "mission_workspace_path",
        "approved_next_step",
        "runtime_claim_result_marker_path",
        "mission_runtime_result_path",
        "consumption_policy",
        "consumable",
        "mission_activation_execution_authorized",
    }
    errors.extend(f"approval missing required field: {field}" for field in sorted(required - set(approval)))
    if approval.get("type") != ACTIVATION_APPROVAL_TYPE:
        errors.append("approval type is not ventureops-mission-activation-execution-approval")
    if approval.get("approval_decision") != "approved":
        errors.append("approval_decision must be approved")
    if approval.get("approval_status") != "approved":
        errors.append("approval_status must be approved")
    if approval.get("mission_id") != mission_id:
        errors.append("approval mission_id does not match mission workspace")
    if approval.get("approved_next_step") != APPROVED_NEXT_STEP:
        errors.append(f"approved_next_step must be {APPROVED_NEXT_STEP}")
    if approval.get("consumption_policy") != "exact_once":
        errors.append("consumption_policy must be exact_once")
    if approval.get("consumable") is not True:
        errors.append("consumable must be true")
    if approval.get("mission_activation_execution_authorized") is not True:
        errors.append("mission_activation_execution_authorized must be true")
    for field in FORBIDDEN_TRUE_AUTHORIZATION_FIELDS:
        if approval.get(field) is not False:
            errors.append(f"{field} must be false")
    if not str(approval.get("operator_approval_statement") or "").strip():
        errors.append("operator_approval_statement is required")
    workspace_value = str(approval.get("mission_workspace_path") or "")
    if workspace_value:
        resolved = (root / workspace_value).resolve() if not Path(workspace_value).is_absolute() else Path(workspace_value).resolve()
        if resolved != workspace.resolve():
            errors.append("approval mission_workspace_path does not match requested mission workspace")
    else:
        errors.append("mission_workspace_path is required")
    expected_digest = _sha256({key: value for key, value in approval.items() if key != "activation_digest"})
    if approval.get("activation_digest") != expected_digest:
        errors.append("activation_digest mismatch")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors))}


def _append_unique(values: list[Any], new_values: list[Any]) -> list[Any]:
    result = list(values)
    for value in new_values:
        if value and value not in result:
            result.append(value)
    return result


def _remove_values(values: list[Any], remove: set[str]) -> list[Any]:
    return [value for value in values if str(value) not in remove]


def _activation_marker(
    *,
    approval: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    result_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "type": ACTIVATION_MARKER_TYPE,
        "status": "executed",
        "surface": SURFACE_ID,
        "activation_id": approval.get("activation_id"),
        "approval_path": str(approval_path).replace("\\", "/"),
        "approval_digest": approval.get("activation_digest"),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": approval.get("mission_workspace_path"),
        "runtime_claim_result_marker_path": result_state.get("claim_result_marker_path"),
        "mission_runtime_result_path": result_state.get("mission_runtime_result_path"),
        "agent_bus_task_id": result_state.get("agent_bus_task_id"),
        "consumed_at": _now_utc(),
        "mission_activation_performed": True,
        "mission_manifest_status_after": "active",
        "mission_state_status_after": "active",
        "runtime_task_claimed": result_state.get("runtime_task_claimed") is True,
        "aor_dispatch_performed": result_state.get("aor_dispatch_performed") is True,
        "mission_result_ingested": result_state.get("mission_result_ingested") is True,
        "agent_bus_task_closed": result_state.get("agent_bus_task_closed") is True,
        "workflow_evolution_applied": False,
        "provider_call_performed": False,
        "browser_action_performed": False,
        "browser_skill_activated": False,
        "external_send_performed": False,
        "crm_or_payment_mutation_performed": False,
        "live_trading_performed": False,
        "protected_file_edit_performed": False,
        "credential_or_secret_read_performed": False,
        "canonical_promotion_performed": False,
        "marker_path": str(marker_path).replace("\\", "/"),
    }


def validate_mission_activation_gate_marker(
    marker: dict[str, Any],
    *,
    approval: dict[str, Any],
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    approval_validation = validate_mission_activation_gate_approval(
        approval,
        vault_root=vault_root,
        mission_workspace=mission_workspace,
    )
    errors.extend(str(error) for error in approval_validation.get("errors") or [])
    if marker.get("type") != ACTIVATION_MARKER_TYPE:
        errors.append("marker type is not ventureops-mission-activation-execution-marker")
    if marker.get("status") != "executed":
        errors.append("marker status must be executed")
    if marker.get("activation_id") != approval.get("activation_id"):
        errors.append("marker activation_id does not match approval")
    if marker.get("approval_digest") != approval.get("activation_digest"):
        errors.append("marker approval_digest does not match approval")
    if marker.get("mission_id") != approval.get("mission_id"):
        errors.append("marker mission_id does not match approval")
    for field in (
        "mission_activation_performed",
        "runtime_task_claimed",
        "aor_dispatch_performed",
        "mission_result_ingested",
        "agent_bus_task_closed",
    ):
        if marker.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "workflow_evolution_applied",
        "provider_call_performed",
        "browser_action_performed",
        "browser_skill_activated",
        "external_send_performed",
        "crm_or_payment_mutation_performed",
        "live_trading_performed",
        "protected_file_edit_performed",
        "credential_or_secret_read_performed",
        "canonical_promotion_performed",
    ):
        if marker.get(field) is not False:
            errors.append(f"{field} must be false")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors))}


def _activate_workspace(
    *,
    root: Path,
    workspace: Path,
    approval: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    result_state: dict[str, Any],
) -> dict[str, Any]:
    approval_rel = _vault_relative(approval_path, root)
    marker_rel = _vault_relative(marker_path, root)
    result_rel = str(result_state.get("mission_runtime_result_path") or "")
    claim_marker_rel = str(result_state.get("claim_result_marker_path") or "")

    manifest_path = workspace / "mission-manifest.json"
    manifest = _load_json(manifest_path)
    manifest["status"] = "active"
    manifest["updated"] = _today_utc()
    manifest["version"] = "0.1-active-local"
    constraints = list(manifest.get("capital_or_resource_constraints") or [])
    manifest["capital_or_resource_constraints"] = _append_unique(
        constraints,
        [
            "local active mission state only",
            "no external delivery, browser action, provider call, credential access, payment/CRM mutation, live trading, protected edit, or canonical promotion without separate approval",
        ],
    )
    manifest["activation_state"] = {
        "status": "active_local",
        "activation_id": approval.get("activation_id"),
        "activated_at": _now_utc(),
        "activation_marker_path": marker_rel,
        "runtime_result_path": result_rel,
        "external_effects_authorized": False,
    }
    manifest["notes"] = (
        "Local Mission Mode activation consumed exactly once after runtime claim/result ingestion. "
        "This is not external delivery or canonical promotion."
    )
    _write_json(manifest_path, manifest)

    state_path = workspace / "mission-state-ledger.json"
    state = _load_json(state_path)
    state["current_status"] = "active"
    state["current_phase"] = "mission_active_local"
    state["last_run_id"] = str(approval.get("activation_id"))
    state["last_review_date"] = _today_utc()
    state["progress_summary"] = (
        "Mission Mode is active in local state after exact-once activation gate consumption. "
        "The runtime claim/result gate is complete, AOR dry-review proof is ingested, and the "
        "Agent Bus task is closed. External/client delivery remains blocked until separate evidence "
        "and approvals exist."
    )
    for item in state.get("active_workflow_versions") or []:
        if isinstance(item, dict):
            if item.get("workflow_id") == "mission_chase_ai_runtime_governance_kit":
                item["status"] = "active_local_dry_review_bridge_verified"
            else:
                item["status"] = "available_for_active_local_mission_reference"
    state["active_blockers"] = _append_unique(
        _remove_values(
            list(state.get("active_blockers") or []),
            {"mission_activation_execution_gate_not_consumed"},
        ),
        ["real_client_scope_not_supplied_for_external_delivery"],
    )
    state["pending_approvals"] = _append_unique(
        _remove_values(list(state.get("pending_approvals") or []), {"mission_activation_execution_gate"}),
        ["human_approval_before_external_delivery", "workflow_evolution_application_if_future_changes_are_requested"],
    )
    state["next_recommended_pass"] = "operator-approved-external-client-evidence-gate-if-needed"
    state["evidence_links"] = _append_unique(list(state.get("evidence_links") or []), [approval_rel, marker_rel, result_rel, claim_marker_rel])
    _write_json(state_path, state)

    boundary_path = workspace / "run-boundary.json"
    boundary = _load_json(boundary_path)
    boundary.update(
        {
            "mission_activation_performed": True,
            "mission_activation_gate_consumed": True,
            "mission_activation_approval_id": approval.get("activation_id"),
            "mission_activation_marker_path": marker_path.name,
            "agent_bus_task_claimed": True,
            "runtime_result_ingested": True,
            "aor_dispatch_performed": True,
            "workflow_mutation_performed": False,
            "workflow_evolution_applied": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "browser_skill_activated": False,
            "external_send_performed": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "protected_file_edit_performed": False,
            "credential_or_secret_read_performed": False,
            "canonical_promotion_performed": False,
            "notes": (
                "Mission activation gate consumed exactly once. Local mission state is active; "
                "all external/provider/browser/credential/workflow-evolution/canonical effects remain blocked."
            ),
        }
    )
    _write_json(boundary_path, boundary)

    review_path = workspace / "mission-review.json"
    review = _load_json(review_path)
    review["what_worked"] = _append_unique(
        list(review.get("what_worked") or []),
        ["Mission activation gate moved the local mission state to active exactly once after runtime result ingestion."],
    )
    review["what_failed"] = _remove_values(
        list(review.get("what_failed") or []),
        ["Mission activation remains intentionally unperformed until the separate activation gate is consumed."],
    )
    review["approvals_needed"] = _append_unique(
        _remove_values(list(review.get("approvals_needed") or []), {"mission_activation_execution_gate"}),
        ["human_approval_before_external_delivery"],
    )
    review["next_pass"] = "operator-approved-external-client-evidence-gate-if-needed"
    _write_json(review_path, review)

    artifact_path = workspace / "artifact-index.json"
    index = _load_json(artifact_path)
    index["status"] = "local_mission_active"
    index["mission_activation_status"] = "active_local"
    artifacts = index.setdefault("artifacts", {})
    artifacts["mission_activation_execution_approval"] = approval_path.name
    artifacts["mission_activation_execution_marker"] = marker_path.name
    linked = index.setdefault("linked_notes", {})
    linked["mission_activation_execution_approval"] = approval_rel
    linked["mission_activation_execution_marker"] = marker_rel
    authority = index.setdefault("authority_boundary", {})
    authority.update(
        {
            "mission_activation_performed": True,
            "agent_bus_task_claimed": True,
            "aor_dispatch_performed": True,
            "mission_result_ingested": True,
            "agent_bus_task_closed": True,
            "external_send_performed": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "browser_skill_activated": False,
            "workflow_mutation_performed": False,
            "workflow_evolution_applied": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "protected_file_edit_performed": False,
            "credential_or_secret_read_performed": False,
            "canonical_promotion_performed": False,
        }
    )
    _write_json(artifact_path, index)

    readme_path = workspace / "README.md"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8", errors="replace")
        if "## Mission Activation Gate" not in text:
            text = text.rstrip() + (
                "\n\n## Mission Activation Gate\n\n"
                "- Status: COMPLETE / LOCAL MISSION ACTIVE.\n"
                f"- Activation approval: `{approval_rel}`.\n"
                f"- Exact-once marker: `{marker_rel}`.\n"
                "- Boundary: local active mission state only; no external delivery, provider call, browser action, credential read, workflow mutation, protected edit, payment/CRM mutation, live trading, or canonical promotion.\n"
            )
            readme_path.write_text(text + "\n", encoding="utf-8")

    return {
        "manifest_path": _vault_relative(manifest_path, root),
        "state_path": _vault_relative(state_path, root),
        "boundary_path": _vault_relative(boundary_path, root),
        "review_path": _vault_relative(review_path, root),
        "artifact_index_path": _vault_relative(artifact_path, root),
        "activation_marker_path": marker_rel,
    }


def consume_mission_activation_gate(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
    activation_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    write_approval: bool = False,
    consume: bool = False,
    activate: bool = False,
) -> dict[str, Any]:
    """Consume the Mission Activation Gate exactly once."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    approval_target = Path(approval_path) if approval_path is not None else default_activation_approval_path(workspace)
    marker_target = Path(marker_path) if marker_path is not None else default_activation_marker_path(workspace)
    if not approval_target.is_absolute():
        approval_target = (root / approval_target).resolve()
    if not marker_target.is_absolute():
        marker_target = (root / marker_target).resolve()
    for target in (approval_target, marker_target):
        resolved, error = _resolve_target(root, target)
        if error or resolved is None:
            approval = build_mission_activation_gate_approval(
                root,
                mission_workspace=workspace,
                activation_id=activation_id,
                approved_by=approved_by,
                operator_approval_statement=operator_approval_statement,
            )
            return _base_response(
                vault_root=root,
                workspace=workspace,
                approval_path=approval_target,
                marker_path=marker_target,
                approval=approval,
                blockers=[error or "target_resolution_failed"],
            )

    approval = build_mission_activation_gate_approval(
        root,
        mission_workspace=workspace,
        activation_id=activation_id,
        approved_by=approved_by,
        operator_approval_statement=operator_approval_statement,
    )
    blockers = list(approval.get("context_errors") or [])
    preview_only = not write_approval and not consume and not activate
    if preview_only:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=blockers,
            preview_only=True,
        )

    if write_approval:
        if approval_target.exists():
            blockers.append("mission_activation_execution_approval_already_present")
        elif not blockers:
            _write_json(approval_target, approval)
    elif approval_target.exists():
        approval = _load_json(approval_target)
        validation = validate_mission_activation_gate_approval(
            approval,
            vault_root=root,
            mission_workspace=workspace,
        )
        blockers.extend(str(error) for error in validation.get("errors") or [])
    else:
        blockers.append("write_approval_required_or_existing_approval_missing")

    approval_written = write_approval and approval_target.exists() and not blockers
    if not consume and not activate:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
        )
    if not consume:
        blockers.append("activate_requires_consume")
    if not activate:
        blockers.append("consume_requires_activate")
    if marker_target.exists():
        blockers.append("exact_once_marker_already_present")
    if blockers:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=list(dict.fromkeys(blockers)),
            approval_artifact_written=approval_written,
            duplicate_blocked="exact_once_marker_already_present" in blockers,
        )

    result_state = load_mission_runtime_claim_result_state(root, mission_workspace=workspace)
    marker = _activation_marker(
        approval=approval,
        approval_path=approval_target,
        marker_path=marker_target,
        result_state=result_state,
    )
    marker_validation = validate_mission_activation_gate_marker(
        marker,
        approval=approval,
        vault_root=root,
        mission_workspace=workspace,
    )
    if not marker_validation.get("ok"):
        blockers.extend(f"activation_marker_invalid:{error}" for error in marker_validation.get("errors") or [])
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
        )
    _write_json(marker_target, marker)
    activation_updates = _activate_workspace(
        root=root,
        workspace=workspace,
        approval=approval,
        approval_path=approval_target,
        marker_path=marker_target,
        result_state=result_state,
    )
    return _base_response(
        vault_root=root,
        workspace=workspace,
        approval_path=approval_target,
        marker_path=marker_target,
        approval=approval,
        blockers=[],
        approval_artifact_written=approval_written,
        activation_consumed=True,
        exact_once_marker_written=True,
        mission_activation_performed=True,
        activation_updates=activation_updates,
        result_state=result_state,
    )


def _base_response(
    *,
    vault_root: Path,
    workspace: Path,
    approval_path: Path,
    marker_path: Path,
    approval: dict[str, Any],
    blockers: list[str],
    approval_artifact_written: bool = False,
    activation_consumed: bool = False,
    exact_once_marker_written: bool = False,
    mission_activation_performed: bool = False,
    duplicate_blocked: bool = False,
    preview_only: bool = False,
    activation_updates: dict[str, Any] | None = None,
    result_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": not blockers and (preview_only or activation_consumed or approval_artifact_written),
        "schema_version": "0.1",
        "surface": SURFACE_ID,
        "status": (
            "preview_ready"
            if preview_only and not blockers
            else "mission_activation_gate_consumed"
            if activation_consumed
            else "mission_activation_approval_artifact_written"
            if approval_artifact_written and not blockers
            else "blocked"
        ),
        "generated_at": _now_utc(),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": _vault_relative(workspace, vault_root),
        "activation_id": approval.get("activation_id"),
        "approval_artifact_path": _vault_relative(approval_path, vault_root),
        "activation_marker_path": _vault_relative(marker_path, vault_root),
        "runtime_claim_result_marker_path": approval.get("runtime_claim_result_marker_path"),
        "mission_runtime_result_path": approval.get("mission_runtime_result_path"),
        "approval_artifact_written": approval_artifact_written,
        "activation_consumed": activation_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "mission_activation_performed": mission_activation_performed,
        "duplicate_blocked_before_activation": duplicate_blocked,
        "preview_only": preview_only,
        "blockers": list(dict.fromkeys(str(blocker) for blocker in blockers)),
        "activation_updates": activation_updates or {},
        "runtime_claim_result_state": result_state or {},
        "authority_boundary": {
            "mission_activation_performed": mission_activation_performed,
            "runtime_task_claimed": bool((result_state or {}).get("runtime_task_claimed")),
            "aor_dispatch_performed": bool((result_state or {}).get("aor_dispatch_performed")),
            "mission_result_ingested": bool((result_state or {}).get("mission_result_ingested")),
            "agent_bus_task_closed": bool((result_state or {}).get("agent_bus_task_closed")),
            "workflow_evolution_applied": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "external_send_performed": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "protected_file_edit_performed": False,
            "credential_or_secret_read_performed": False,
            "canonical_promotion_performed": False,
        },
    }


def load_mission_activation_gate_state(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate local mission activation gate state."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    approval_target = Path(approval_path) if approval_path is not None else default_activation_approval_path(workspace)
    marker_target = Path(marker_path) if marker_path is not None else default_activation_marker_path(workspace)
    if not approval_target.is_absolute():
        approval_target = (root / approval_target).resolve()
    if not marker_target.is_absolute():
        marker_target = (root / marker_target).resolve()

    errors: list[str] = []
    approval_present = approval_target.exists()
    marker_present = marker_target.exists()
    approval: dict[str, Any] | None = None
    marker: dict[str, Any] | None = None
    approval_valid = False
    marker_valid = False
    if approval_present:
        try:
            approval = _load_json(approval_target)
            validation = validate_mission_activation_gate_approval(
                approval,
                vault_root=root,
                mission_workspace=workspace,
            )
            approval_valid = bool(validation.get("ok"))
            errors.extend(str(error) for error in validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"activation_approval_invalid:{exc}")
    if marker_present:
        try:
            marker = _load_json(marker_target)
            if approval is None:
                errors.append("activation_marker_present_without_approval_artifact")
            else:
                validation = validate_mission_activation_gate_marker(
                    marker,
                    approval=approval,
                    vault_root=root,
                    mission_workspace=workspace,
                )
                marker_valid = bool(validation.get("ok"))
                errors.extend(str(error) for error in validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"activation_marker_invalid:{exc}")
    consumed = approval_valid and marker_valid
    return {
        "ok": not errors,
        "activation_approval_artifact_present": approval_present,
        "activation_approval_artifact_valid": approval_valid,
        "activation_approval_artifact_path": _vault_relative(approval_target, root),
        "activation_marker_present": marker_present,
        "activation_marker_valid": marker_valid,
        "activation_marker_path": _vault_relative(marker_target, root),
        "activation_consumed": consumed,
        "mission_activation_performed": consumed and (marker or {}).get("mission_activation_performed") is True,
        "mission_manifest_status_after": (marker or {}).get("mission_manifest_status_after"),
        "mission_state_status_after": (marker or {}).get("mission_state_status_after"),
        "runtime_task_claimed": (marker or {}).get("runtime_task_claimed") is True,
        "aor_dispatch_performed": (marker or {}).get("aor_dispatch_performed") is True,
        "mission_result_ingested": (marker or {}).get("mission_result_ingested") is True,
        "agent_bus_task_closed": (marker or {}).get("agent_bus_task_closed") is True,
        "activation_id": (approval or {}).get("activation_id"),
        "mission_id": (approval or {}).get("mission_id"),
        "errors": list(dict.fromkeys(errors)),
    }
