"""Exact-once approval consumption for VentureOps Mission Mode activation gates."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.ventureops.mission_dry_runs import validate_mission_dry_run_workspace


APPROVAL_ARTIFACT_FILENAME = "activation-approval-approved.json"
CONSUMPTION_MARKER_FILENAME = "activation-approval-consumption.json"
APPROVAL_TYPE = "ventureops-mission-activation-approval"
MARKER_TYPE = "ventureops-mission-activation-approval-consumption-marker"
APPROVED_NEXT_STEP = "mission_activation_gate_only"
SURFACE_ID = "ventureops_mission_activation_approval_consumption"
FORBIDDEN_TRUE_AUTHORIZATION_FIELDS = (
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
) -> tuple[Path, dict[str, Any] | None, str, list[str]]:
    workspace = _resolve_workspace(vault_root, mission_workspace)
    errors: list[str] = []
    if not workspace.exists():
        return workspace, None, "", ["mission_dry_run_workspace_missing"]
    validation = validate_mission_dry_run_workspace(workspace)
    if not validation.get("ok"):
        errors.append("mission_dry_run_artifact_validation_failed")
        errors.extend(str(error) for error in validation.get("errors") or [])
    manifest_path = workspace / "mission-manifest.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else None
    mission_id = str((manifest or {}).get("mission_id") or validation.get("mission_id") or "")
    if not mission_id:
        errors.append("mission_id_missing")
    return workspace, manifest, mission_id, errors


def default_approval_artifact_path(workspace: str | Path) -> Path:
    return Path(workspace) / APPROVAL_ARTIFACT_FILENAME


def default_consumption_marker_path(workspace: str | Path) -> Path:
    return Path(workspace) / CONSUMPTION_MARKER_FILENAME


def build_mission_activation_approval_artifact(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    approved_at: str | None = None,
) -> dict[str, Any]:
    """Build a consumable approval artifact without writing it."""

    root = Path(vault_root).resolve()
    workspace, _manifest, mission_id, context_errors = _workspace_context(root, mission_workspace)
    statement = " ".join(str(operator_approval_statement or "").strip().split())
    approval_id = _safe_id(approval_id or f"{mission_id or 'mission'}-activation-approval-{datetime.now(timezone.utc).date().isoformat()}")
    approved_by = str(approved_by or "operator").strip() or "operator"
    workspace_rel = _vault_relative(workspace, root)
    ready_for_approval = not context_errors and bool(statement)

    artifact = {
        "schema_version": "0.1",
        "type": APPROVAL_TYPE,
        "approval_id": approval_id,
        "approval_decision": "approved" if ready_for_approval else "pending",
        "approval_status": "approved" if ready_for_approval else "blocked_missing_operator_statement",
        "approved_by": approved_by,
        "approved_at": approved_at or _now_utc(),
        "operator_approval_statement": statement,
        "mission_id": mission_id,
        "mission_workspace_path": workspace_rel,
        "approved_next_step": APPROVED_NEXT_STEP,
        "approved_scope": [
            "consume one local Mission Mode activation approval gate",
            "clear only the mission_activation_approval_missing readiness blocker when the exact-once marker validates",
            "leave mission manifest promotion, AOR dispatch, Agent Bus enqueue, and workflow evolution application for separate approvals",
        ],
        "required_acknowledgements": [
            "this approval consumption is exact-once and create-only",
            "mission activation execution is not authorized by this artifact",
            "AOR dispatch and live Agent Bus task writes remain unauthorized",
            "workflow evolution remains pending review and must not auto-apply",
            "provider calls, browser actions, external sends, CRM/payment mutation, live trading, protected-file edits, credential reads, and canonical promotion remain forbidden",
        ],
        "consumption_policy": "exact_once",
        "consumable": ready_for_approval,
        "approval_consumed": False,
        "activation_authority_granted": ready_for_approval,
        "activation_authority_scope": "approval_gate_only_no_execution",
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
        "context_errors": context_errors,
    }
    artifact["approval_digest"] = _sha256({key: value for key, value in artifact.items() if key != "approval_digest"})
    return artifact


def validate_mission_activation_approval_artifact(
    approval: dict[str, Any],
    *,
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a mission activation approval artifact against the current workspace."""

    root = Path(vault_root).resolve()
    workspace, _manifest, mission_id, context_errors = _workspace_context(root, mission_workspace)
    errors = list(context_errors)
    required = {
        "schema_version",
        "type",
        "approval_id",
        "approval_decision",
        "approval_status",
        "approved_by",
        "approved_at",
        "operator_approval_statement",
        "mission_id",
        "mission_workspace_path",
        "approved_next_step",
        "approved_scope",
        "required_acknowledgements",
        "consumption_policy",
        "consumable",
        "activation_authority_granted",
    }
    missing = sorted(field for field in required if field not in approval)
    errors.extend(f"approval missing required field: {field}" for field in missing)
    if approval.get("type") != APPROVAL_TYPE:
        errors.append("approval type is not ventureops-mission-activation-approval")
    if approval.get("approval_decision") != "approved":
        errors.append("approval_decision must be approved")
    if approval.get("approval_status") != "approved":
        errors.append("approval_status must be approved")
    if not str(approval.get("operator_approval_statement") or "").strip():
        errors.append("operator_approval_statement is required")
    if approval.get("mission_id") != mission_id:
        errors.append("approval mission_id does not match mission workspace")

    approved_workspace = str(approval.get("mission_workspace_path") or "")
    if approved_workspace:
        approved_workspace_path = Path(approved_workspace)
        resolved_approved = (
            approved_workspace_path.resolve()
            if approved_workspace_path.is_absolute()
            else (root / approved_workspace_path).resolve()
        )
        if resolved_approved != workspace.resolve():
            errors.append("approval mission_workspace_path does not match requested mission workspace")
    else:
        errors.append("approval mission_workspace_path is required")

    if approval.get("approved_next_step") != APPROVED_NEXT_STEP:
        errors.append(f"approved_next_step must be {APPROVED_NEXT_STEP}")
    if approval.get("consumption_policy") != "exact_once":
        errors.append("consumption_policy must be exact_once")
    if approval.get("consumable") is not True:
        errors.append("approval must be consumable")
    if approval.get("activation_authority_granted") is not True:
        errors.append("activation_authority_granted must be true for the gate approval")
    for field in FORBIDDEN_TRUE_AUTHORIZATION_FIELDS:
        if approval.get(field) is not False:
            errors.append(f"{field} must be false")

    expected_digest = approval.get("approval_digest")
    if expected_digest:
        actual_digest = _sha256({key: value for key, value in approval.items() if key != "approval_digest"})
        if actual_digest != expected_digest:
            errors.append("approval_digest mismatch")

    return {
        "ok": not errors,
        "errors": errors,
        "approval_id": approval.get("approval_id"),
        "mission_id": mission_id,
        "mission_workspace_path": _vault_relative(workspace, root),
    }


def _marker_payload(
    *,
    vault_root: Path,
    approval: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    consumed_by: str,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "type": MARKER_TYPE,
        "status": "consumed",
        "approval_id": approval.get("approval_id"),
        "approval_artifact_path": _vault_relative(approval_path, vault_root),
        "consumption_marker_path": _vault_relative(marker_path, vault_root),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": approval.get("mission_workspace_path"),
        "approved_next_step": approval.get("approved_next_step"),
        "consumption_policy": "exact_once",
        "approval_digest": approval.get("approval_digest") or _sha256(approval),
        "consumed_by": consumed_by,
        "consumed_at": _now_utc(),
        "approval_consumed": True,
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


def validate_mission_activation_approval_consumption_marker(
    marker: dict[str, Any],
    *,
    approval: dict[str, Any],
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Validate an exact-once consumption marker against its approval artifact."""

    root = Path(vault_root).resolve()
    approval_validation = validate_mission_activation_approval_artifact(
        approval,
        vault_root=root,
        mission_workspace=mission_workspace,
    )
    errors = list(approval_validation.get("errors") or [])
    if marker.get("type") != MARKER_TYPE:
        errors.append("marker type is not ventureops mission activation consumption marker")
    if marker.get("status") != "consumed":
        errors.append("marker status must be consumed")
    if marker.get("approval_id") != approval.get("approval_id"):
        errors.append("marker approval_id does not match approval artifact")
    if marker.get("mission_id") != approval.get("mission_id"):
        errors.append("marker mission_id does not match approval artifact")
    if marker.get("mission_workspace_path") != approval.get("mission_workspace_path"):
        errors.append("marker mission_workspace_path does not match approval artifact")
    if marker.get("approved_next_step") != APPROVED_NEXT_STEP:
        errors.append(f"marker approved_next_step must be {APPROVED_NEXT_STEP}")
    if marker.get("consumption_policy") != "exact_once":
        errors.append("marker consumption_policy must be exact_once")
    if marker.get("approval_consumed") is not True:
        errors.append("marker approval_consumed must be true")
    approval_digest = approval.get("approval_digest") or _sha256(approval)
    if marker.get("approval_digest") != approval_digest:
        errors.append("marker approval_digest does not match approval artifact")
    for flag in (
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
        if marker.get(flag) is not False:
            errors.append(f"marker {flag} must be false")
    return {"ok": not errors, "errors": errors}


def load_mission_activation_approval_consumption_state(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the approval artifact/marker state, if present."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    approval_target = (
        Path(approval_path)
        if approval_path is not None
        else default_approval_artifact_path(workspace)
    )
    marker_target = (
        Path(marker_path)
        if marker_path is not None
        else default_consumption_marker_path(workspace)
    )
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
            approval_validation = validate_mission_activation_approval_artifact(
                approval,
                vault_root=root,
                mission_workspace=workspace,
            )
            approval_valid = bool(approval_validation.get("ok"))
            errors.extend(str(error) for error in approval_validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"approval_artifact_invalid:{exc}")
    if marker_present:
        try:
            marker = _load_json(marker_target)
            if approval is None:
                errors.append("activation_approval_marker_present_without_approval_artifact")
            else:
                marker_validation = validate_mission_activation_approval_consumption_marker(
                    marker,
                    approval=approval,
                    vault_root=root,
                    mission_workspace=workspace,
                )
                marker_valid = bool(marker_validation.get("ok"))
                errors.extend(str(error) for error in marker_validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"activation_approval_consumption_marker_invalid:{exc}")

    approval_consumed = approval_valid and marker_valid
    return {
        "ok": not errors,
        "approval_artifact_present": approval_present,
        "approval_artifact_valid": approval_valid,
        "approval_artifact_path": _vault_relative(approval_target, root),
        "consumption_marker_present": marker_present,
        "consumption_marker_valid": marker_valid,
        "consumption_marker_path": _vault_relative(marker_target, root),
        "approval_consumed": approval_consumed,
        "approved_for_activation": approval_consumed,
        "approval_id": (approval or {}).get("approval_id"),
        "mission_id": (approval or {}).get("mission_id"),
        "errors": list(dict.fromkeys(errors)),
    }


def _base_response(
    *,
    vault_root: Path,
    workspace: Path,
    approval_path: Path,
    marker_path: Path,
    approval: dict[str, Any],
    blockers: list[str],
    approval_artifact_written: bool = False,
    approval_consumed: bool = False,
    exact_once_marker_written: bool = False,
    duplicate_blocked: bool = False,
    preview_only: bool = False,
    readiness_after_consumption: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": not blockers and (preview_only or approval_consumed or approval_artifact_written),
        "schema_version": "0.1",
        "surface": SURFACE_ID,
        "status": (
            "preview_ready"
            if preview_only and not blockers
            else "approval_consumed"
            if approval_consumed
            else "approval_artifact_written"
            if approval_artifact_written and not blockers
            else "blocked"
        ),
        "generated_at": _now_utc(),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": _vault_relative(workspace, vault_root),
        "approval_id": approval.get("approval_id"),
        "approval_artifact_path": _vault_relative(approval_path, vault_root),
        "consumption_marker_path": _vault_relative(marker_path, vault_root),
        "approval_artifact_written": approval_artifact_written,
        "approval_consumed": approval_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "duplicate_blocked_before_activation": duplicate_blocked,
        "preview_only": preview_only,
        "readiness_after_consumption": readiness_after_consumption,
        "blockers": list(dict.fromkeys(blockers)),
        "approval_artifact": approval if preview_only else None,
        "authority_boundary": {
            "approval_consumption_allowed": True,
            "exact_once_marker_write_allowed": True,
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


def consume_mission_activation_approval(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
    approval_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    write_approval: bool = False,
    consume: bool = False,
) -> dict[str, Any]:
    """Write an approval artifact and/or consume it exactly once."""

    root = Path(vault_root).resolve()
    workspace, _manifest, _mission_id, context_errors = _workspace_context(root, mission_workspace)
    raw_approval = approval_path or default_approval_artifact_path(workspace)
    raw_marker = marker_path or default_consumption_marker_path(workspace)
    approval_target, _approval_rel, approval_error = _resolve_under_vault(root, raw_approval)
    marker_target, _marker_rel, marker_error = _resolve_under_vault(root, raw_marker)
    blockers = list(context_errors)
    if approval_error:
        blockers.append(approval_error.replace("path", "approval_path"))
    if marker_error:
        blockers.append(marker_error.replace("path", "marker_path"))
    if approval_target is None:
        approval_target = root / "blocked-approval-path.json"
    if marker_target is None:
        marker_target = root / "blocked-marker-path.json"

    if consume and marker_target.exists():
        approval = (
            _load_json(approval_target)
            if approval_target.exists()
            else build_mission_activation_approval_artifact(
                root,
                mission_workspace=workspace,
                approval_id=approval_id,
                approved_by=approved_by,
                operator_approval_statement=operator_approval_statement,
            )
        )
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=[*blockers, "exact_once_marker_already_present"],
            duplicate_blocked=True,
        )

    approval = build_mission_activation_approval_artifact(
        root,
        mission_workspace=workspace,
        approval_id=approval_id,
        approved_by=approved_by,
        operator_approval_statement=operator_approval_statement,
    )
    approval_validation = validate_mission_activation_approval_artifact(
        approval,
        vault_root=root,
        mission_workspace=workspace,
    )
    blockers.extend(str(error) for error in approval_validation.get("errors") or [])

    if not write_approval and not consume:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=blockers,
            preview_only=True,
        )

    approval_artifact_written = False
    if write_approval:
        if approval_target.exists():
            blockers.append("approval_artifact_already_exists")
        if not blockers:
            approval_target.parent.mkdir(parents=True, exist_ok=True)
            with approval_target.open("x", encoding="utf-8") as handle:
                json.dump(approval, handle, indent=2, sort_keys=True)
                handle.write("\n")
            approval_artifact_written = True
    else:
        if not approval_target.exists():
            blockers.append("approval_artifact_missing")
        else:
            approval = _load_json(approval_target)
            stored_validation = validate_mission_activation_approval_artifact(
                approval,
                vault_root=root,
                mission_workspace=workspace,
            )
            blockers.extend(str(error) for error in stored_validation.get("errors") or [])

    exact_once_marker_written = False
    readiness_after: dict[str, Any] | None = None
    approval_consumed = False
    if consume and not blockers:
        marker_target.parent.mkdir(parents=True, exist_ok=True)
        marker = _marker_payload(
            vault_root=root,
            approval=approval,
            approval_path=approval_target,
            marker_path=marker_target,
            consumed_by=str(approved_by or "operator").strip() or "operator",
        )
        with marker_target.open("x", encoding="utf-8") as handle:
            json.dump(marker, handle, indent=2, sort_keys=True)
            handle.write("\n")
        exact_once_marker_written = True
        approval_consumed = True
        from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness

        readiness_after = build_mission_activation_readiness(root, mission_workspace=workspace)

    return _base_response(
        vault_root=root,
        workspace=workspace,
        approval_path=approval_target,
        marker_path=marker_target,
        approval=approval,
        blockers=blockers,
        approval_artifact_written=approval_artifact_written,
        approval_consumed=approval_consumed,
        exact_once_marker_written=exact_once_marker_written,
        readiness_after_consumption=readiness_after,
    )
