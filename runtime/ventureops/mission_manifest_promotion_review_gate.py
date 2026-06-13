"""Exact-once review gate for Mission Mode manifest promotion readiness."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.ventureops.mission_activation_approval_consumption import (
    load_mission_activation_approval_consumption_state,
)
from runtime.ventureops.mission_dry_runs import validate_mission_dry_run_workspace


REVIEW_ARTIFACT_FILENAME = "mission-manifest-promotion-workflow-evolution-review-approved.json"
REVIEW_MARKER_FILENAME = "mission-manifest-promotion-workflow-evolution-review-consumption.json"
ACTIVATION_MARKER_FILENAME = "mission-activation-execution-consumption.json"
REVIEW_TYPE = "ventureops-mission-manifest-promotion-workflow-evolution-review"
MARKER_TYPE = "ventureops-mission-manifest-promotion-workflow-evolution-review-marker"
APPROVED_NEXT_STEP = "activation_readiness_gate_only"
MANIFEST_PROMOTION_DECISION = "approved_for_activation_readiness_only"
WORKFLOW_EVOLUTION_REVIEW_DECISION = "reviewed_deferred_no_apply"
SURFACE_ID = "ventureops_mission_manifest_promotion_workflow_evolution_review_gate"

FORBIDDEN_TRUE_AUTHORIZATION_FIELDS = (
    "mission_manifest_file_mutation_authorized",
    "mission_activation_execution_authorized",
    "aor_dispatch_authorized",
    "agent_bus_task_write_authorized",
    "workflow_evolution_apply_authorized",
    "provider_calls_authorized",
    "browser_actions_authorized",
    "browser_skill_activation_authorized",
    "external_side_effects_authorized",
    "crm_or_payment_mutation_authorized",
    "live_trading_authorized",
    "protected_file_edit_authorized",
    "canonical_promotion_authorized",
    "credential_or_secret_read_authorized",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    normalized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value.strip())
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


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return path.resolve().relative_to(vault_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_workspace(vault_root: Path, mission_workspace: str | Path | None) -> Path:
    if mission_workspace is None:
        return (
            vault_root
            / "07_LOGS"
            / "VentureOps-Missions"
            / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
        ).resolve()
    raw = Path(mission_workspace)
    return raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()


def _resolve_under_vault(vault_root: Path, path: str | Path) -> tuple[Path | None, str | None, str | None]:
    raw = Path(path)
    resolved = raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()
    try:
        relative = resolved.relative_to(vault_root.resolve())
    except ValueError:
        return None, None, f"path escapes vault root: {path}"
    return resolved, relative.as_posix(), None


def _workspace_context(
    vault_root: Path,
    mission_workspace: str | Path | None,
) -> tuple[Path, dict[str, Any] | None, dict[str, Any] | None, str, list[str]]:
    workspace = _resolve_workspace(vault_root, mission_workspace)
    errors: list[str] = []
    if not workspace.exists():
        return workspace, None, None, "", ["mission_dry_run_workspace_missing"]

    validation = validate_mission_dry_run_workspace(workspace)
    if not validation.get("ok"):
        errors.append("mission_dry_run_artifact_validation_failed")
        errors.extend(str(error) for error in validation.get("errors") or [])

    manifest_path = workspace / "mission-manifest.json"
    proposal_path = workspace / "workflow-evolution-proposal.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else None
    proposal = _load_json(proposal_path) if proposal_path.exists() else None
    mission_id = str((manifest or {}).get("mission_id") or validation.get("mission_id") or "")
    if not mission_id:
        errors.append("mission_id_missing")
    return workspace, manifest, proposal, mission_id, errors


def default_review_artifact_path(workspace: str | Path) -> Path:
    return Path(workspace) / REVIEW_ARTIFACT_FILENAME


def default_review_marker_path(workspace: str | Path) -> Path:
    return Path(workspace) / REVIEW_MARKER_FILENAME


def _local_activation_marker_valid(workspace: Path, mission_id: str) -> bool:
    marker_path = workspace / ACTIVATION_MARKER_FILENAME
    if not marker_path.exists():
        return False
    try:
        marker = _load_json(marker_path)
    except Exception:
        return False
    return (
        marker.get("type") == "ventureops-mission-activation-execution-marker"
        and marker.get("status") == "executed"
        and marker.get("mission_id") == mission_id
        and marker.get("mission_activation_performed") is True
    )


def build_mission_manifest_promotion_review_artifact(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    review_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    """Build the manifest-promotion/workflow-evolution review artifact without writing it."""

    root = Path(vault_root).resolve()
    workspace, manifest, proposal, mission_id, context_errors = _workspace_context(root, mission_workspace)
    activation_state = load_mission_activation_approval_consumption_state(root, mission_workspace=workspace)
    activation_errors = [str(error) for error in activation_state.get("errors") or []]
    errors = list(context_errors)
    errors.extend(f"activation_approval_consumption:{error}" for error in activation_errors)

    manifest_status = str((manifest or {}).get("status") or "")
    proposal_status = str((proposal or {}).get("status") or "")
    auto_apply_allowed = (proposal or {}).get("auto_apply_allowed") is True
    if activation_state.get("approval_consumed") is not True:
        errors.append("activation_approval_must_be_consumed_before_manifest_promotion_review")
    if manifest_status != "draft":
        errors.append(f"mission_manifest_status_must_be_draft_for_this_gate:{manifest_status or 'missing'}")
    if proposal_status != "pending_review":
        errors.append(f"workflow_evolution_status_must_be_pending_review:{proposal_status or 'missing'}")
    if auto_apply_allowed:
        errors.append("workflow_evolution_auto_apply_not_allowed")

    statement = " ".join(str(operator_approval_statement or "").strip().split())
    if not statement:
        errors.append("operator_approval_statement is required")

    review_id = _safe_id(
        review_id
        or f"{mission_id or 'mission'}-manifest-promotion-workflow-evolution-review-{datetime.now(timezone.utc).date().isoformat()}"
    )
    approved_by = str(approved_by or "operator").strip() or "operator"
    workspace_rel = _vault_relative(workspace, root)
    review_ready = not errors

    artifact = {
        "schema_version": "0.1",
        "type": REVIEW_TYPE,
        "review_id": review_id,
        "approval_decision": "approved" if review_ready else "pending",
        "approval_status": "approved" if review_ready else "blocked",
        "approved_by": approved_by,
        "reviewed_at": reviewed_at or _now_utc(),
        "operator_approval_statement": statement,
        "mission_id": mission_id,
        "mission_workspace_path": workspace_rel,
        "activation_approval_consumed": activation_state.get("approval_consumed") is True,
        "activation_approval_artifact_path": activation_state.get("approval_artifact_path"),
        "activation_approval_consumption_marker_path": activation_state.get("consumption_marker_path"),
        "approved_next_step": APPROVED_NEXT_STEP,
        "manifest_status_at_review": manifest_status,
        "manifest_promotion_decision": MANIFEST_PROMOTION_DECISION,
        "effective_mission_manifest_status": "approved" if review_ready else manifest_status,
        "workflow_evolution_status_at_review": proposal_status,
        "workflow_evolution_review_decision": WORKFLOW_EVOLUTION_REVIEW_DECISION,
        "effective_workflow_evolution_status": WORKFLOW_EVOLUTION_REVIEW_DECISION if review_ready else proposal_status,
        "approved_scope": [
            "clear the mission_manifest_is_draft readiness blocker through an exact-once review marker",
            "clear the workflow_evolution_proposal_pending_review readiness blocker through review-only evidence",
            "leave mission-manifest.json and workflow-evolution-proposal.json unmutated in the dry-run workspace",
            "permit only a future separately approved local AOR mission dry-review or dispatch gate",
        ],
        "required_acknowledgements": [
            "activation approval must already be consumed exactly once",
            "manifest promotion is readiness evidence only and does not mutate mission-manifest.json",
            "workflow evolution is reviewed and deferred, not applied",
            "AOR dispatch and live Agent Bus task writes remain separate approvals",
            "provider calls, browser actions, external sends, CRM/payment mutation, live trading, protected-file edits, credential reads, and canonical promotion remain forbidden",
        ],
        "consumption_policy": "exact_once",
        "consumable": review_ready,
        "review_consumed": False,
        "manifest_promotion_authority_granted": review_ready,
        "workflow_evolution_review_authority_granted": review_ready,
        "mission_manifest_file_mutation_authorized": False,
        "mission_activation_execution_authorized": False,
        "aor_dispatch_authorized": False,
        "agent_bus_task_write_authorized": False,
        "workflow_evolution_apply_authorized": False,
        "provider_calls_authorized": False,
        "browser_actions_authorized": False,
        "browser_skill_activation_authorized": False,
        "external_side_effects_authorized": False,
        "crm_or_payment_mutation_authorized": False,
        "live_trading_authorized": False,
        "protected_file_edit_authorized": False,
        "canonical_promotion_authorized": False,
        "credential_or_secret_read_authorized": False,
        "context_errors": errors,
    }
    artifact["review_digest"] = _sha256({key: value for key, value in artifact.items() if key != "review_digest"})
    return artifact


def validate_mission_manifest_promotion_review_artifact(
    review: dict[str, Any],
    *,
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a manifest-promotion/workflow-evolution review artifact."""

    root = Path(vault_root).resolve()
    workspace, manifest, proposal, mission_id, context_errors = _workspace_context(root, mission_workspace)
    activation_state = load_mission_activation_approval_consumption_state(root, mission_workspace=workspace)
    errors = list(context_errors)
    errors.extend(f"activation_approval_consumption:{error}" for error in activation_state.get("errors") or [])

    required = {
        "schema_version",
        "type",
        "review_id",
        "approval_decision",
        "approval_status",
        "approved_by",
        "reviewed_at",
        "operator_approval_statement",
        "mission_id",
        "mission_workspace_path",
        "activation_approval_consumed",
        "approved_next_step",
        "manifest_status_at_review",
        "manifest_promotion_decision",
        "effective_mission_manifest_status",
        "workflow_evolution_status_at_review",
        "workflow_evolution_review_decision",
        "effective_workflow_evolution_status",
        "approved_scope",
        "required_acknowledgements",
        "consumption_policy",
        "consumable",
        "manifest_promotion_authority_granted",
        "workflow_evolution_review_authority_granted",
    }
    missing = sorted(field for field in required if field not in review)
    errors.extend(f"review missing required field: {field}" for field in missing)

    if review.get("type") != REVIEW_TYPE:
        errors.append("review type is not ventureops-mission-manifest-promotion-workflow-evolution-review")
    if review.get("approval_decision") != "approved":
        errors.append("approval_decision must be approved")
    if review.get("approval_status") != "approved":
        errors.append("approval_status must be approved")
    if not str(review.get("operator_approval_statement") or "").strip():
        errors.append("operator_approval_statement is required")
    if review.get("mission_id") != mission_id:
        errors.append("review mission_id does not match mission workspace")

    reviewed_workspace = str(review.get("mission_workspace_path") or "")
    if reviewed_workspace:
        reviewed_workspace_path = Path(reviewed_workspace)
        resolved_reviewed = (
            reviewed_workspace_path.resolve()
            if reviewed_workspace_path.is_absolute()
            else (root / reviewed_workspace_path).resolve()
        )
        if resolved_reviewed != workspace.resolve():
            errors.append("review mission_workspace_path does not match requested mission workspace")
    else:
        errors.append("review mission_workspace_path is required")

    manifest_status = str((manifest or {}).get("status") or "")
    proposal_status = str((proposal or {}).get("status") or "")
    if activation_state.get("approval_consumed") is not True:
        errors.append("activation approval must be consumed before manifest promotion review")
    if review.get("activation_approval_consumed") is not True:
        errors.append("activation_approval_consumed must be true")
    if review.get("approved_next_step") != APPROVED_NEXT_STEP:
        errors.append(f"approved_next_step must be {APPROVED_NEXT_STEP}")
    post_activation_manifest = manifest_status == "active" and _local_activation_marker_valid(workspace, mission_id)
    if review.get("manifest_status_at_review") != "draft" or (
        manifest_status != "draft" and not post_activation_manifest
    ):
        errors.append("mission manifest must remain draft at this review gate")
    if review.get("manifest_promotion_decision") != MANIFEST_PROMOTION_DECISION:
        errors.append(f"manifest_promotion_decision must be {MANIFEST_PROMOTION_DECISION}")
    if review.get("effective_mission_manifest_status") != "approved":
        errors.append("effective_mission_manifest_status must be approved")
    if review.get("workflow_evolution_status_at_review") != "pending_review" or proposal_status != "pending_review":
        errors.append("workflow evolution proposal must remain pending_review at this review gate")
    if review.get("workflow_evolution_review_decision") != WORKFLOW_EVOLUTION_REVIEW_DECISION:
        errors.append(f"workflow_evolution_review_decision must be {WORKFLOW_EVOLUTION_REVIEW_DECISION}")
    if review.get("effective_workflow_evolution_status") != WORKFLOW_EVOLUTION_REVIEW_DECISION:
        errors.append(f"effective_workflow_evolution_status must be {WORKFLOW_EVOLUTION_REVIEW_DECISION}")
    if (proposal or {}).get("auto_apply_allowed") is not False:
        errors.append("workflow evolution auto_apply_allowed must remain false")
    if review.get("consumption_policy") != "exact_once":
        errors.append("consumption_policy must be exact_once")
    if review.get("consumable") is not True:
        errors.append("review must be consumable")
    if review.get("manifest_promotion_authority_granted") is not True:
        errors.append("manifest_promotion_authority_granted must be true")
    if review.get("workflow_evolution_review_authority_granted") is not True:
        errors.append("workflow_evolution_review_authority_granted must be true")
    for field in FORBIDDEN_TRUE_AUTHORIZATION_FIELDS:
        if review.get(field) is not False:
            errors.append(f"{field} must be false")

    expected_digest = review.get("review_digest")
    if expected_digest:
        actual_digest = _sha256({key: value for key, value in review.items() if key != "review_digest"})
        if actual_digest != expected_digest:
            errors.append("review_digest mismatch")

    return {
        "ok": not errors,
        "errors": list(dict.fromkeys(errors)),
        "review_id": review.get("review_id"),
        "mission_id": mission_id,
        "mission_workspace_path": _vault_relative(workspace, root),
    }


def _marker_payload(
    *,
    vault_root: Path,
    review: dict[str, Any],
    review_path: Path,
    marker_path: Path,
    consumed_by: str,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "type": MARKER_TYPE,
        "status": "consumed",
        "review_id": review.get("review_id"),
        "review_artifact_path": _vault_relative(review_path, vault_root),
        "review_marker_path": _vault_relative(marker_path, vault_root),
        "mission_id": review.get("mission_id"),
        "mission_workspace_path": review.get("mission_workspace_path"),
        "approved_next_step": review.get("approved_next_step"),
        "manifest_promotion_decision": review.get("manifest_promotion_decision"),
        "workflow_evolution_review_decision": review.get("workflow_evolution_review_decision"),
        "consumption_policy": "exact_once",
        "review_digest": review.get("review_digest") or _sha256(review),
        "consumed_by": consumed_by,
        "consumed_at": _now_utc(),
        "review_consumed": True,
        "manifest_promotion_gate_consumed": True,
        "workflow_evolution_review_gate_consumed": True,
        "mission_manifest_promoted_for_activation_readiness": True,
        "workflow_evolution_reviewed_for_activation_readiness": True,
        "mission_manifest_file_mutation_performed": False,
        "mission_activation_performed": False,
        "aor_dispatch_performed": False,
        "agent_bus_task_written": False,
        "workflow_evolution_applied": False,
        "provider_call_performed": False,
        "browser_action_performed": False,
        "browser_skill_activated": False,
        "external_send_performed": False,
        "crm_or_payment_mutation_performed": False,
        "live_trading_performed": False,
        "protected_file_edit_performed": False,
        "canonical_promotion_performed": False,
        "credential_or_secret_read_performed": False,
    }


def validate_mission_manifest_promotion_review_marker(
    marker: dict[str, Any],
    *,
    review: dict[str, Any],
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a manifest-promotion/workflow-evolution review marker."""

    root = Path(vault_root).resolve()
    review_validation = validate_mission_manifest_promotion_review_artifact(
        review,
        vault_root=root,
        mission_workspace=mission_workspace,
    )
    errors = [str(error) for error in review_validation.get("errors") or []]
    required = {
        "schema_version",
        "type",
        "status",
        "review_id",
        "review_artifact_path",
        "review_marker_path",
        "mission_id",
        "mission_workspace_path",
        "approved_next_step",
        "manifest_promotion_decision",
        "workflow_evolution_review_decision",
        "consumption_policy",
        "review_digest",
        "consumed_by",
        "consumed_at",
        "review_consumed",
        "manifest_promotion_gate_consumed",
        "workflow_evolution_review_gate_consumed",
    }
    missing = sorted(field for field in required if field not in marker)
    errors.extend(f"marker missing required field: {field}" for field in missing)

    if marker.get("type") != MARKER_TYPE:
        errors.append("marker type is not ventureops-mission-manifest-promotion-workflow-evolution-review-marker")
    if marker.get("status") != "consumed":
        errors.append("marker status must be consumed")
    for field in (
        "review_id",
        "mission_id",
        "mission_workspace_path",
        "approved_next_step",
        "manifest_promotion_decision",
        "workflow_evolution_review_decision",
    ):
        if marker.get(field) != review.get(field):
            errors.append(f"marker {field} does not match review artifact")
    if marker.get("consumption_policy") != "exact_once":
        errors.append("marker consumption_policy must be exact_once")
    if marker.get("review_digest") != (review.get("review_digest") or _sha256(review)):
        errors.append("marker review_digest does not match review artifact")

    required_true = (
        "review_consumed",
        "manifest_promotion_gate_consumed",
        "workflow_evolution_review_gate_consumed",
        "mission_manifest_promoted_for_activation_readiness",
        "workflow_evolution_reviewed_for_activation_readiness",
    )
    for field in required_true:
        if marker.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "mission_manifest_file_mutation_performed",
        "mission_activation_performed",
        "aor_dispatch_performed",
        "agent_bus_task_written",
        "workflow_evolution_applied",
        "provider_call_performed",
        "browser_action_performed",
        "browser_skill_activated",
        "external_send_performed",
        "crm_or_payment_mutation_performed",
        "live_trading_performed",
        "protected_file_edit_performed",
        "canonical_promotion_performed",
        "credential_or_secret_read_performed",
    ):
        if marker.get(field) is not False:
            errors.append(f"{field} must be false")

    return {
        "ok": not errors,
        "errors": list(dict.fromkeys(errors)),
        "review_id": review.get("review_id"),
        "mission_id": review_validation.get("mission_id"),
    }


def load_mission_manifest_promotion_review_state(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    review_path: str | Path | None = None,
    marker_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the exact-once review gate state."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    review_target = Path(review_path) if review_path is not None else default_review_artifact_path(workspace)
    marker_target = Path(marker_path) if marker_path is not None else default_review_marker_path(workspace)
    if not review_target.is_absolute():
        review_target = (root / review_target).resolve()
    if not marker_target.is_absolute():
        marker_target = (root / marker_target).resolve()

    errors: list[str] = []
    review_present = review_target.exists()
    marker_present = marker_target.exists()
    review: dict[str, Any] | None = None
    marker: dict[str, Any] | None = None
    review_valid = False
    marker_valid = False

    if review_present:
        try:
            review = _load_json(review_target)
            review_validation = validate_mission_manifest_promotion_review_artifact(
                review,
                vault_root=root,
                mission_workspace=workspace,
            )
            review_valid = bool(review_validation.get("ok"))
            errors.extend(str(error) for error in review_validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"manifest_promotion_review_artifact_invalid:{exc}")
    if marker_present:
        try:
            marker = _load_json(marker_target)
            if review is None:
                errors.append("manifest_promotion_review_marker_present_without_review_artifact")
            else:
                marker_validation = validate_mission_manifest_promotion_review_marker(
                    marker,
                    review=review,
                    vault_root=root,
                    mission_workspace=workspace,
                )
                marker_valid = bool(marker_validation.get("ok"))
                errors.extend(str(error) for error in marker_validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"manifest_promotion_review_marker_invalid:{exc}")

    gate_consumed = review_valid and marker_valid
    return {
        "ok": not errors,
        "review_artifact_present": review_present,
        "review_artifact_valid": review_valid,
        "review_artifact_path": _vault_relative(review_target, root),
        "review_marker_present": marker_present,
        "review_marker_valid": marker_valid,
        "review_marker_path": _vault_relative(marker_target, root),
        "review_consumed": gate_consumed,
        "manifest_promotion_gate_consumed": gate_consumed,
        "workflow_evolution_review_gate_consumed": gate_consumed,
        "mission_manifest_promoted_for_activation": gate_consumed,
        "workflow_evolution_reviewed_for_activation": gate_consumed,
        "effective_mission_manifest_status": "approved" if gate_consumed else None,
        "effective_workflow_evolution_status": WORKFLOW_EVOLUTION_REVIEW_DECISION if gate_consumed else None,
        "review_id": (review or {}).get("review_id"),
        "mission_id": (review or {}).get("mission_id"),
        "errors": list(dict.fromkeys(errors)),
    }


def _base_response(
    *,
    vault_root: Path,
    workspace: Path,
    review_path: Path,
    marker_path: Path,
    review: dict[str, Any],
    blockers: list[str],
    review_artifact_written: bool = False,
    review_consumed: bool = False,
    exact_once_marker_written: bool = False,
    duplicate_blocked: bool = False,
    preview_only: bool = False,
    readiness_after_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": not blockers and (preview_only or review_consumed or review_artifact_written),
        "schema_version": "0.1",
        "surface": SURFACE_ID,
        "status": (
            "preview_ready"
            if preview_only and not blockers
            else "review_consumed"
            if review_consumed
            else "review_artifact_written"
            if review_artifact_written and not blockers
            else "blocked"
        ),
        "generated_at": _now_utc(),
        "mission_id": review.get("mission_id"),
        "mission_workspace_path": _vault_relative(workspace, vault_root),
        "review_id": review.get("review_id"),
        "review_artifact_path": _vault_relative(review_path, vault_root),
        "review_marker_path": _vault_relative(marker_path, vault_root),
        "review_artifact_written": review_artifact_written,
        "review_consumed": review_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "duplicate_blocked_before_activation": duplicate_blocked,
        "preview_only": preview_only,
        "readiness_after_review": readiness_after_review,
        "blockers": list(dict.fromkeys(blockers)),
        "review_artifact": review if preview_only else None,
        "authority_boundary": {
            "manifest_promotion_review_allowed": True,
            "exact_once_marker_write_allowed": True,
            "mission_manifest_file_mutation_performed": False,
            "mission_activation_performed": False,
            "aor_dispatch_performed": False,
            "agent_bus_task_written": False,
            "workflow_evolution_applied": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "browser_skill_activated": False,
            "external_send_performed": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "protected_file_edit_performed": False,
            "canonical_promotion_performed": False,
            "credential_or_secret_read_performed": False,
        },
    }


def consume_mission_manifest_promotion_review_gate(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    review_path: str | Path | None = None,
    marker_path: str | Path | None = None,
    review_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    write_review: bool = False,
    consume: bool = False,
) -> dict[str, Any]:
    """Write and/or consume the manifest-promotion/workflow-evolution review gate exactly once."""

    root = Path(vault_root).resolve()
    workspace, _manifest, _proposal, _mission_id, context_errors = _workspace_context(root, mission_workspace)
    raw_review = review_path or default_review_artifact_path(workspace)
    raw_marker = marker_path or default_review_marker_path(workspace)
    review_target, _review_rel, review_error = _resolve_under_vault(root, raw_review)
    marker_target, _marker_rel, marker_error = _resolve_under_vault(root, raw_marker)
    blockers = list(context_errors)
    if review_error:
        blockers.append(review_error.replace("path", "review_path"))
    if marker_error:
        blockers.append(marker_error.replace("path", "marker_path"))
    if review_target is None:
        review_target = root / "blocked-review-path.json"
    if marker_target is None:
        marker_target = root / "blocked-marker-path.json"

    if consume and marker_target.exists():
        review = (
            _load_json(review_target)
            if review_target.exists()
            else build_mission_manifest_promotion_review_artifact(
                root,
                mission_workspace=workspace,
                review_id=review_id,
                approved_by=approved_by,
                operator_approval_statement=operator_approval_statement,
            )
        )
        return _base_response(
            vault_root=root,
            workspace=workspace,
            review_path=review_target,
            marker_path=marker_target,
            review=review,
            blockers=[*blockers, "exact_once_marker_already_present"],
            duplicate_blocked=True,
        )

    review = build_mission_manifest_promotion_review_artifact(
        root,
        mission_workspace=workspace,
        review_id=review_id,
        approved_by=approved_by,
        operator_approval_statement=operator_approval_statement,
    )
    review_validation = validate_mission_manifest_promotion_review_artifact(
        review,
        vault_root=root,
        mission_workspace=workspace,
    )
    blockers.extend(str(error) for error in review_validation.get("errors") or [])

    if not write_review and not consume:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            review_path=review_target,
            marker_path=marker_target,
            review=review,
            blockers=blockers,
            preview_only=True,
        )

    review_artifact_written = False
    if write_review:
        if review_target.exists():
            blockers.append("review_artifact_already_exists")
        if not blockers:
            review_target.parent.mkdir(parents=True, exist_ok=True)
            with review_target.open("x", encoding="utf-8") as handle:
                json.dump(review, handle, indent=2, sort_keys=True)
                handle.write("\n")
            review_artifact_written = True
    else:
        if not review_target.exists():
            blockers.append("review_artifact_missing")
        else:
            review = _load_json(review_target)
            stored_validation = validate_mission_manifest_promotion_review_artifact(
                review,
                vault_root=root,
                mission_workspace=workspace,
            )
            blockers.extend(str(error) for error in stored_validation.get("errors") or [])

    exact_once_marker_written = False
    readiness_after: dict[str, Any] | None = None
    review_consumed = False
    if consume and not blockers:
        marker_target.parent.mkdir(parents=True, exist_ok=True)
        marker = _marker_payload(
            vault_root=root,
            review=review,
            review_path=review_target,
            marker_path=marker_target,
            consumed_by=str(approved_by or "operator").strip() or "operator",
        )
        with marker_target.open("x", encoding="utf-8") as handle:
            json.dump(marker, handle, indent=2, sort_keys=True)
            handle.write("\n")
        exact_once_marker_written = True
        review_consumed = True
        from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness

        readiness_after = build_mission_activation_readiness(root, mission_workspace=workspace)

    return _base_response(
        vault_root=root,
        workspace=workspace,
        review_path=review_target,
        marker_path=marker_target,
        review=review,
        blockers=blockers,
        review_artifact_written=review_artifact_written,
        review_consumed=review_consumed,
        exact_once_marker_written=exact_once_marker_written,
        readiness_after_review=readiness_after,
    )
