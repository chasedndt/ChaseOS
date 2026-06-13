"""Exact-once runtime claim/result gate for VentureOps Mission Mode."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import (
    claim_task,
    evaluate_task_claimability,
    list_tasks,
    update_task_status,
)
from runtime.agent_bus.mission_tasks import MISSION_TASK_TYPE, vault_relative_path
from runtime.ventureops.mission_agent_bus_enqueue_gate import (
    DEFAULT_RECIPIENT,
    load_mission_agent_bus_enqueue_state,
)


CLAIM_RESULT_APPROVAL_FILENAME = "mission-runtime-claim-result-approval-approved.json"
CLAIM_RESULT_MARKER_FILENAME = "mission-runtime-claim-result-consumption.json"
MISSION_RUNTIME_RESULT_FILENAME = "mission-runtime-result.json"
CLAIM_RESULT_APPROVAL_TYPE = "ventureops-mission-runtime-claim-result-approval"
CLAIM_RESULT_MARKER_TYPE = "ventureops-mission-runtime-claim-result-marker"
MISSION_RUNTIME_RESULT_TYPE = "ventureops-mission-runtime-result"
SURFACE_ID = "ventureops_mission_runtime_claim_result_gate"
APPROVED_NEXT_STEP = "claim_dispatch_ingest_close_mission_dry_review_task"
MISSION_AOR_WORKFLOW_ID = "mission_chase_ai_runtime_governance_kit"
DEFAULT_RUNTIME = "Codex"
DEFAULT_RUNTIME_INSTANCE_ID = "Axiom-Codex"
DEFAULT_STALE_AFTER_SECONDS = 86_400

FORBIDDEN_TRUE_AUTHORIZATION_FIELDS = (
    "mission_activation_execution_authorized",
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
    "followup_agent_bus_task_authorized",
)

RESULT_REQUIRED_FIELDS = {
    "schema_version",
    "type",
    "result_id",
    "status",
    "result_shape",
    "mission_id",
    "mission_workspace_path",
    "task_type",
    "agent_bus_task_id",
    "runtime",
    "runtime_instance_id",
    "aor_workflow_id",
    "aor_status",
    "aor_audit_id",
    "aor_writeback_files",
    "result_payload",
    "authority_boundary",
}


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


def default_claim_result_approval_path(workspace: str | Path) -> Path:
    return Path(workspace) / CLAIM_RESULT_APPROVAL_FILENAME


def default_claim_result_marker_path(workspace: str | Path) -> Path:
    return Path(workspace) / CLAIM_RESULT_MARKER_FILENAME


def default_mission_runtime_result_path(workspace: str | Path) -> Path:
    return Path(workspace) / MISSION_RUNTIME_RESULT_FILENAME


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _task_age_seconds(task: dict[str, Any]) -> int | None:
    updated = _parse_timestamp(task.get("updated_at") or task.get("created_at"))
    if updated is None:
        return None
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - updated).total_seconds())


def _mission_task_from_bus(
    vault_root: Path,
    *,
    task_id: str,
    runtime: str,
) -> dict[str, Any] | None:
    for task in list_tasks(vault_root, recipient=runtime):
        if task.get("task_id") == task_id:
            return task
    return None


def _authority_boundary(*, result_ingested: bool, task_closed: bool) -> dict[str, Any]:
    return {
        "runtime_task_claimed": True,
        "runtime_process_started": False,
        "workflow_dispatched": True,
        "aor_dispatch_performed": True,
        "mission_result_ingested": result_ingested,
        "agent_bus_task_closed": task_closed,
        "mission_activation_performed": False,
        "agent_bus_followup_task_written": False,
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
    }


def _result_id(approval_id: str) -> str:
    return f"mission-runtime-result-{_safe_id(approval_id)}"


def build_mission_runtime_claim_result_approval(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    runtime: str = DEFAULT_RUNTIME,
    runtime_instance_id: str | None = DEFAULT_RUNTIME_INSTANCE_ID,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    """Build a claim/result approval artifact without writing it."""

    from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    readiness = build_mission_activation_readiness(root, mission_workspace=workspace)
    enqueue_state = load_mission_agent_bus_enqueue_state(root, mission_workspace=workspace)
    manifest: dict[str, Any] = {}
    if (workspace / "mission-manifest.json").exists():
        manifest = _load_json(workspace / "mission-manifest.json")
    mission_id = str(readiness.get("mission_id") or manifest.get("mission_id") or "")
    approval_id = _safe_id(
        approval_id
        or f"{mission_id or 'mission'}-runtime-claim-result-{datetime.now(timezone.utc).date().isoformat()}"
    )
    statement = " ".join(str(operator_approval_statement or "").strip().split())
    runtime = str(runtime or DEFAULT_RUNTIME).strip() or DEFAULT_RUNTIME
    runtime_instance_id = str(runtime_instance_id or DEFAULT_RUNTIME_INSTANCE_ID).strip() or DEFAULT_RUNTIME_INSTANCE_ID
    errors: list[str] = []
    warnings: list[str] = []

    if not statement:
        errors.append("operator_approval_statement is required")
    if runtime != str(enqueue_state.get("recipient") or DEFAULT_RECIPIENT):
        errors.append("runtime must match enqueued mission task recipient")
    if readiness.get("ready_for_activation") is not True:
        errors.append("mission_activation_readiness_must_be_ready_before_runtime_claim_result")
    if enqueue_state.get("enqueue_consumed") is not True:
        errors.append("mission_agent_bus_enqueue_must_be_consumed_before_runtime_claim_result")
    if enqueue_state.get("agent_bus_task_written") is not True:
        errors.append("agent_bus_mission_task_must_be_written_before_runtime_claim_result")

    task_id = str(enqueue_state.get("agent_bus_task_id") or "")
    task = _mission_task_from_bus(root, task_id=task_id, runtime=runtime) if task_id else None
    claimability: dict[str, Any] = {}
    if not task_id:
        errors.append("agent_bus_task_id_missing")
    elif task is None:
        errors.append("agent_bus_task_missing")
    else:
        if task.get("status") != "open" or task.get("owner") is not None:
            age = _task_age_seconds(task)
            if task.get("owner") and age is not None and age >= int(stale_after_seconds):
                errors.append("stale_owned_task_requires_separate_reclaim_gate")
            else:
                errors.append(f"agent_bus_task_not_open_unclaimed:{task.get('status')}:{task.get('owner')}")
        notes = str(task.get("notes") or "")
        if MISSION_TASK_TYPE not in notes and str(task.get("task_type") or "") != MISSION_TASK_TYPE:
            errors.append("agent_bus_task_missing_mission_run_dry_review_type")
        age = _task_age_seconds(task)
        if age is not None and task.get("status") == "open" and age >= int(stale_after_seconds):
            errors.append("open_agent_bus_task_is_stale_requires_operator_review")
        claimability = evaluate_task_claimability(root, task_id=task_id, runtime=runtime)
        if not claimability.get("claimable"):
            errors.append(f"agent_bus_task_not_claimable:{claimability.get('reason')}")

    approval = {
        "schema_version": "0.1",
        "type": CLAIM_RESULT_APPROVAL_TYPE,
        "approval_id": approval_id,
        "approval_decision": "approved" if not errors else "pending",
        "approval_status": "approved" if not errors else "blocked",
        "approved_by": str(approved_by or "operator").strip() or "operator",
        "approved_at": _now_utc(),
        "operator_approval_statement": statement,
        "mission_id": mission_id,
        "mission_workspace_path": _vault_relative(workspace, root),
        "readiness_status_at_approval": readiness.get("readiness_status"),
        "agent_bus_enqueue_id": enqueue_state.get("enqueue_id"),
        "agent_bus_task_id": task_id,
        "work_fingerprint": enqueue_state.get("work_fingerprint"),
        "runtime": runtime,
        "runtime_instance_id": runtime_instance_id,
        "stale_after_seconds": int(stale_after_seconds),
        "task_claimability": claimability,
        "task_snapshot_at_approval": task or {},
        "approved_next_step": APPROVED_NEXT_STEP,
        "approved_scope": [
            "claim the already-enqueued local mission.run_dry_review Agent Bus task",
            "dispatch only the existing local AOR mission dry-review handler",
            "ingest local proof/review/audit result references into the mission workspace",
            "close the Agent Bus task after successful local result ingestion",
        ],
        "required_acknowledgements": [
            "Duplicate result processing is blocked by an exact-once marker and task status checks",
            "Owned stale tasks require a separate reclaim gate rather than duplicate execution",
            "The AOR dispatch bridge remains local dry-review only and has no external effects",
            "Mission activation remains a separate exact-once gate after result ingestion",
        ],
        "result_schema": {
            "type": MISSION_RUNTIME_RESULT_TYPE,
            "required_fields": sorted(RESULT_REQUIRED_FIELDS),
            "allowed_result_shapes": ["complete", "blocked", "risk"],
            "must_confirm_false": [
                "mission_activation_performed",
                "agent_bus_followup_task_written",
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
            ],
        },
        "consumption_policy": "exact_once",
        "consumable": not errors,
        "runtime_task_claim_authorized": not errors,
        "aor_dry_review_dispatch_authorized": not errors,
        "mission_result_ingestion_authorized": not errors,
        "agent_bus_task_close_authorized": not errors,
        "mission_activation_execution_authorized": False,
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
        "followup_agent_bus_task_authorized": False,
        "context_errors": list(dict.fromkeys(errors)),
        "warnings": warnings,
    }
    approval["approval_digest"] = _sha256({key: value for key, value in approval.items() if key != "approval_digest"})
    return approval


def validate_mission_runtime_claim_result_approval(
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
        "approval_id",
        "approval_decision",
        "approval_status",
        "approved_by",
        "approved_at",
        "operator_approval_statement",
        "mission_id",
        "mission_workspace_path",
        "agent_bus_task_id",
        "runtime",
        "runtime_instance_id",
        "approved_next_step",
        "result_schema",
        "consumption_policy",
        "consumable",
        "runtime_task_claim_authorized",
        "aor_dry_review_dispatch_authorized",
        "mission_result_ingestion_authorized",
        "agent_bus_task_close_authorized",
    }
    errors.extend(f"approval missing required field: {field}" for field in sorted(required - set(approval)))
    if approval.get("type") != CLAIM_RESULT_APPROVAL_TYPE:
        errors.append("approval type is not ventureops-mission-runtime-claim-result-approval")
    if approval.get("approval_decision") != "approved":
        errors.append("approval_decision must be approved")
    if approval.get("approval_status") != "approved":
        errors.append("approval_status must be approved")
    if approval.get("mission_id") != mission_id:
        errors.append("approval mission_id does not match mission workspace")
    if approval.get("approved_next_step") != APPROVED_NEXT_STEP:
        errors.append(f"approved_next_step must be {APPROVED_NEXT_STEP}")
    if approval.get("runtime") != DEFAULT_RUNTIME:
        errors.append("runtime must be Codex for the current enqueued mission task")
    if approval.get("consumption_policy") != "exact_once":
        errors.append("consumption_policy must be exact_once")
    if approval.get("consumable") is not True:
        errors.append("consumable must be true")
    for field in (
        "runtime_task_claim_authorized",
        "aor_dry_review_dispatch_authorized",
        "mission_result_ingestion_authorized",
        "agent_bus_task_close_authorized",
    ):
        if approval.get(field) is not True:
            errors.append(f"{field} must be true")
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
    expected_digest = _sha256({key: value for key, value in approval.items() if key != "approval_digest"})
    if approval.get("approval_digest") != expected_digest:
        errors.append("approval_digest mismatch")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors))}


def validate_mission_runtime_result(result: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    errors.extend(f"result missing required field: {field}" for field in sorted(RESULT_REQUIRED_FIELDS - set(result)))
    if result.get("type") != MISSION_RUNTIME_RESULT_TYPE:
        errors.append("result type is not ventureops-mission-runtime-result")
    if result.get("status") != "complete":
        errors.append("result status must be complete")
    if result.get("result_shape") not in {"complete", "blocked", "risk"}:
        errors.append("result_shape must be one of complete, blocked, risk")
    if result.get("task_type") != MISSION_TASK_TYPE:
        errors.append(f"task_type must be {MISSION_TASK_TYPE}")
    if result.get("aor_workflow_id") != MISSION_AOR_WORKFLOW_ID:
        errors.append(f"aor_workflow_id must be {MISSION_AOR_WORKFLOW_ID}")
    if result.get("aor_status") != "success":
        errors.append("aor_status must be success")
    writebacks = result.get("aor_writeback_files")
    if not isinstance(writebacks, list) or not writebacks:
        errors.append("aor_writeback_files must be a non-empty list")
    else:
        allowed = (
            "07_LOGS/VentureOps-Missions/",
            "07_LOGS/Mission-Reviews/",
            "07_LOGS/Workflow-Proofs/",
            "07_LOGS/Runtime-Audits/",
        )
        for path in writebacks:
            if not isinstance(path, str) or not path.startswith(allowed):
                errors.append(f"aor_writeback_file outside allowed roots: {path}")
    boundary = result.get("authority_boundary")
    if not isinstance(boundary, dict):
        errors.append("authority_boundary must be an object")
    else:
        for field in ("runtime_task_claimed", "workflow_dispatched", "aor_dispatch_performed"):
            if boundary.get(field) is not True:
                errors.append(f"authority_boundary.{field} must be true")
        for field in (
            "mission_activation_performed",
            "agent_bus_followup_task_written",
            "workflow_mutation_performed",
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
            if boundary.get(field) is not False:
                errors.append(f"authority_boundary.{field} must be false")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors))}


def _marker_payload(
    *,
    status: str,
    approval: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    result_path: Path,
    result: dict[str, Any] | None,
    task_closed: bool,
    error: str = "",
) -> dict[str, Any]:
    result_digest = _sha256(result) if result else ""
    return {
        "schema_version": "0.1",
        "type": CLAIM_RESULT_MARKER_TYPE,
        "status": status,
        "surface": SURFACE_ID,
        "approval_id": approval.get("approval_id"),
        "approval_path": str(approval_path).replace("\\", "/"),
        "approval_digest": approval.get("approval_digest"),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": approval.get("mission_workspace_path"),
        "agent_bus_task_id": approval.get("agent_bus_task_id"),
        "work_fingerprint": approval.get("work_fingerprint"),
        "runtime": approval.get("runtime"),
        "runtime_instance_id": approval.get("runtime_instance_id"),
        "result_path": str(result_path).replace("\\", "/"),
        "result_digest": result_digest,
        "consumed_at": _now_utc(),
        "runtime_task_claimed": True,
        "workflow_dispatched": result is not None,
        "aor_dispatch_performed": result is not None,
        "mission_result_ingested": bool(result and (result.get("authority_boundary") or {}).get("mission_result_ingested") is True),
        "agent_bus_task_closed": task_closed,
        "mission_activation_performed": False,
        "agent_bus_followup_task_written": False,
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
        "aor_writeback_files": list((result or {}).get("aor_writeback_files") or []),
        "error": error,
        "marker_path": str(marker_path).replace("\\", "/"),
    }


def validate_mission_runtime_claim_result_marker(
    marker: dict[str, Any],
    *,
    approval: dict[str, Any],
    result: dict[str, Any],
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    approval_validation = validate_mission_runtime_claim_result_approval(
        approval,
        vault_root=vault_root,
        mission_workspace=mission_workspace,
    )
    result_validation = validate_mission_runtime_result(result)
    errors.extend(str(error) for error in approval_validation.get("errors") or [])
    errors.extend(str(error) for error in result_validation.get("errors") or [])
    if marker.get("type") != CLAIM_RESULT_MARKER_TYPE:
        errors.append("marker type is not ventureops-mission-runtime-claim-result-marker")
    if marker.get("status") != "executed":
        errors.append("marker status must be executed")
    if marker.get("approval_id") != approval.get("approval_id"):
        errors.append("marker approval_id does not match approval")
    if marker.get("approval_digest") != approval.get("approval_digest"):
        errors.append("marker approval_digest does not match approval")
    if marker.get("mission_id") != approval.get("mission_id"):
        errors.append("marker mission_id does not match approval")
    if marker.get("agent_bus_task_id") != approval.get("agent_bus_task_id"):
        errors.append("marker agent_bus_task_id does not match approval")
    if marker.get("result_digest") != _sha256(result):
        errors.append("marker result_digest does not match result")
    for field in ("runtime_task_claimed", "workflow_dispatched", "aor_dispatch_performed", "mission_result_ingested", "agent_bus_task_closed"):
        if marker.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "mission_activation_performed",
        "agent_bus_followup_task_written",
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


def _run_aor_dry_review(
    *,
    root: Path,
    workspace: Path,
    approval: dict[str, Any],
) -> Any:
    from runtime.aor.engine import run_workflow

    workspace_rel = _vault_relative(workspace, root)
    approval_packet_path = workspace / "activation-approval-approved.json"
    return run_workflow(
        MISSION_AOR_WORKFLOW_ID,
        inputs={
            "execution_mode": "dry_review",
            "mission_workspace_path": workspace_rel,
            "activation_approval_packet_path": _vault_relative(approval_packet_path, root),
            "run_id": f"{_safe_id(approval.get('approval_id'))}-aor-dry-review",
            "date": _today_utc(),
        },
        vault_root=root,
        dry_run=False,
        runtime_id="codex",
    )


def _append_unique(values: list[Any], new_values: list[Any]) -> list[Any]:
    result = list(values)
    for value in new_values:
        if value and value not in result:
            result.append(value)
    return result


def _remove_values(values: list[Any], remove: set[str]) -> list[Any]:
    return [value for value in values if str(value) not in remove]


def _ingest_result_into_workspace(
    *,
    root: Path,
    workspace: Path,
    approval: dict[str, Any],
    result: dict[str, Any],
    result_path: Path,
    marker_path: Path,
    approval_path: Path,
) -> dict[str, Any]:
    workspace_rel = _vault_relative(workspace, root)
    result_rel = _vault_relative(result_path, root)
    marker_rel = _vault_relative(marker_path, root)
    approval_rel = _vault_relative(approval_path, root)
    aor_files = list(result.get("aor_writeback_files") or [])

    boundary_path = workspace / "run-boundary.json"
    boundary = _load_json(boundary_path)
    boundary.update(
        {
            "agent_bus_task_claimed": True,
            "agent_bus_task_claim_result_gate_consumed": True,
            "agent_bus_task_claim_result_approval_id": approval.get("approval_id"),
            "agent_bus_task_claim_result_marker_path": marker_path.name,
            "agent_bus_task_status": "done",
            "runtime_result_ingested": True,
            "runtime_result_path": result_path.name,
            "aor_dispatch_performed": True,
            "aor_workflow_dispatched_from_claim_result": True,
            "mission_activation_performed": False,
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
                "Runtime claim/result gate consumed exactly once. The local Codex mission task "
                "was claimed, dispatched through the existing local AOR dry-review handler, "
                "ingested back into the mission workspace, and closed. Mission activation and "
                "all external/provider/browser/credential/canonical effects remain separate."
            ),
        }
    )
    _write_json(boundary_path, boundary)

    state_path = workspace / "mission-state-ledger.json"
    state = _load_json(state_path)
    state["current_status"] = "blocked"
    state["current_phase"] = "runtime_result_ingested_pending_activation_gate"
    state["last_run_id"] = str(result.get("result_id") or approval.get("approval_id"))
    state["last_review_date"] = _today_utc()
    state["progress_summary"] = (
        "The enqueued local Codex mission dry-review task has been claimed, dispatched "
        "through the existing local AOR dry-review handler, ingested into the mission "
        "workspace, and closed. The mission is ready for a separate exact-once local "
        "activation gate; external delivery and client scope remain blocked."
    )
    state["active_blockers"] = _append_unique(
        _remove_values(
            list(state.get("active_blockers") or []),
            {"agent_bus_mission_task_open_unclaimed", "runtime_claim_or_result_review_not_completed"},
        ),
        ["mission_activation_execution_gate_not_consumed", "real_client_scope_not_supplied"],
    )
    state["pending_approvals"] = _append_unique(
        _remove_values(
            list(state.get("pending_approvals") or []),
            {"runtime_claim_or_result_review_before_processing_open_task"},
        ),
        ["mission_activation_execution_gate", "human_approval_before_external_delivery"],
    )
    state["next_recommended_pass"] = "ventureops-mission-activation-gate"
    state["evidence_links"] = _append_unique(list(state.get("evidence_links") or []), [approval_rel, result_rel, marker_rel, *aor_files])
    state["proof_cards"] = _append_unique(
        list(state.get("proof_cards") or []),
        [path for path in aor_files if path.startswith("07_LOGS/Workflow-Proofs/")],
    )
    state["audit_links"] = _append_unique(
        list(state.get("audit_links") or []),
        [path for path in aor_files if path.startswith("07_LOGS/Runtime-Audits/")],
    )
    _write_json(state_path, state)

    review_path = workspace / "mission-review.json"
    review = _load_json(review_path)
    review["runs_reviewed"] = _append_unique(list(review.get("runs_reviewed") or []), [str(result.get("result_id"))])
    review["proof_cards"] = _append_unique(
        list(review.get("proof_cards") or []),
        [path for path in aor_files if path.startswith("07_LOGS/Workflow-Proofs/")],
    )
    review["what_worked"] = _append_unique(
        list(review.get("what_worked") or []),
        [
            "Runtime claim/result gate claimed the open Codex mission dry-review task exactly once.",
            "Agent Bus to AOR dispatch bridge invoked the existing local dry-review handler with no external effects.",
            "Mission result ingestion updated workspace state, proof, review, and audit references before task closeout.",
        ],
    )
    review["what_failed"] = _append_unique(
        _remove_values(
            list(review.get("what_failed") or []),
            {
                "No runtime has claimed or completed the open Agent Bus mission dry-review task.",
                "No AOR dispatch has been performed from the enqueued task.",
            },
        ),
        ["Mission activation remains intentionally unperformed until the separate activation gate is consumed."],
    )
    review["proposed_changes"] = _append_unique(
        _remove_values(
            list(review.get("proposed_changes") or []),
            {"Require runtime claim/result review before treating the open Agent Bus mission dry-review task as processed."},
        ),
        ["Consume a separate exact-once activation gate before moving the local mission to active state."],
    )
    review["approvals_needed"] = _append_unique(
        _remove_values(list(review.get("approvals_needed") or []), {"runtime_claim_or_result_review_gate"}),
        ["mission_activation_execution_gate"],
    )
    review["next_pass"] = "ventureops-mission-activation-gate"
    _write_json(review_path, review)

    artifact_path = workspace / "artifact-index.json"
    index = _load_json(artifact_path)
    index["status"] = "local_dry_run_complete_runtime_result_ingested"
    index["mission_activation_status"] = "not_activated"
    artifacts = index.setdefault("artifacts", {})
    artifacts["runtime_claim_result_approval_artifact"] = approval_path.name
    artifacts["mission_runtime_result"] = result_path.name
    artifacts["runtime_claim_result_marker"] = marker_path.name
    linked = index.setdefault("linked_notes", {})
    linked["runtime_claim_result_approval_artifact"] = approval_rel
    linked["mission_runtime_result"] = result_rel
    linked["runtime_claim_result_marker"] = marker_rel
    for idx, path in enumerate(aor_files, start=1):
        linked[f"runtime_result_aor_writeback_{idx}"] = path
    authority = index.setdefault("authority_boundary", {})
    authority.update(
        {
            "agent_bus_task_claimed": True,
            "aor_dispatch_performed": True,
            "mission_result_ingested": True,
            "agent_bus_task_closed": True,
            "mission_activation_performed": False,
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
        if "## Runtime Claim / Result Gate" not in text:
            text = text.rstrip() + (
                "\n\n## Runtime Claim / Result Gate\n\n"
                "- Status: COMPLETE / LOCAL RESULT INGESTED / TASK CLOSED.\n"
                f"- Result artifact: `{result_rel}`.\n"
                f"- Exact-once marker: `{marker_rel}`.\n"
                "- Boundary: local AOR dry-review only; no mission activation, provider call, browser action, external send, credential read, workflow mutation, or canonical promotion.\n"
            )
            readme_path.write_text(text + "\n", encoding="utf-8")

    return {
        "workspace_path": workspace_rel,
        "result_path": result_rel,
        "marker_path": marker_rel,
        "approval_path": approval_rel,
        "aor_writeback_files": aor_files,
        "state_path": _vault_relative(state_path, root),
        "review_path": _vault_relative(review_path, root),
        "artifact_index_path": _vault_relative(artifact_path, root),
    }


def consume_mission_runtime_claim_result_gate(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
    result_path: str | Path | None = None,
    approval_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    runtime: str = DEFAULT_RUNTIME,
    runtime_instance_id: str | None = DEFAULT_RUNTIME_INSTANCE_ID,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
    write_approval: bool = False,
    consume: bool = False,
    claim_task_flag: bool = False,
    dispatch_aor: bool = False,
    ingest_result: bool = False,
    close_task: bool = False,
) -> dict[str, Any]:
    """Consume the runtime claim/result gate exactly once."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    approval_target = Path(approval_path) if approval_path is not None else default_claim_result_approval_path(workspace)
    marker_target = Path(marker_path) if marker_path is not None else default_claim_result_marker_path(workspace)
    result_target = Path(result_path) if result_path is not None else default_mission_runtime_result_path(workspace)
    if not approval_target.is_absolute():
        approval_target = (root / approval_target).resolve()
    if not marker_target.is_absolute():
        marker_target = (root / marker_target).resolve()
    if not result_target.is_absolute():
        result_target = (root / result_target).resolve()
    for target in (approval_target, marker_target, result_target):
        resolved, error = _resolve_target(root, target)
        if error or resolved is None:
            approval = build_mission_runtime_claim_result_approval(
                root,
                mission_workspace=workspace,
                approval_id=approval_id,
                approved_by=approved_by,
                operator_approval_statement=operator_approval_statement,
                runtime=runtime,
                runtime_instance_id=runtime_instance_id,
                stale_after_seconds=stale_after_seconds,
            )
            return _base_response(
                vault_root=root,
                workspace=workspace,
                approval_path=approval_target,
                marker_path=marker_target,
                result_path=result_target,
                approval=approval,
                blockers=[error or "target_resolution_failed"],
            )

    approval = build_mission_runtime_claim_result_approval(
        root,
        mission_workspace=workspace,
        approval_id=approval_id,
        approved_by=approved_by,
        operator_approval_statement=operator_approval_statement,
        runtime=runtime,
        runtime_instance_id=runtime_instance_id,
        stale_after_seconds=stale_after_seconds,
    )
    blockers = list(approval.get("context_errors") or [])
    preview_only = not write_approval and not consume
    if preview_only:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=blockers,
            preview_only=True,
        )

    if write_approval:
        if approval_target.exists():
            blockers.append("claim_result_approval_artifact_already_present")
        elif not blockers:
            _write_json(approval_target, approval)
    elif approval_target.exists():
        approval = _load_json(approval_target)
        validation = validate_mission_runtime_claim_result_approval(
            approval,
            vault_root=root,
            mission_workspace=workspace,
        )
        blockers.extend(str(error) for error in validation.get("errors") or [])
    else:
        blockers.append("write_approval_required_or_existing_approval_missing")

    approval_written = write_approval and approval_target.exists() and not blockers
    if not consume:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
        )

    if marker_target.exists():
        blockers.append("exact_once_marker_already_present")
    if result_target.exists():
        blockers.append("mission_runtime_result_already_present")
    if not claim_task_flag:
        blockers.append("consume_requires_claim_task")
    if not dispatch_aor:
        blockers.append("consume_requires_dispatch_aor")
    if not ingest_result:
        blockers.append("consume_requires_ingest_result")
    if not close_task:
        blockers.append("consume_requires_close_task")
    if blockers:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=list(dict.fromkeys(blockers)),
            approval_artifact_written=approval_written,
            duplicate_blocked="exact_once_marker_already_present" in blockers,
        )

    task_id = str(approval.get("agent_bus_task_id") or "")
    claim = claim_task(
        root,
        task_id=task_id,
        runtime=str(approval.get("runtime") or DEFAULT_RUNTIME),
        runtime_instance_id=str(approval.get("runtime_instance_id") or DEFAULT_RUNTIME_INSTANCE_ID),
    )
    if not claim.get("claimed"):
        blockers.append(f"agent_bus_claim_failed:{claim.get('reason')}")
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
            claim_result=claim,
        )

    update_task_status(
        root,
        task_id=task_id,
        runtime=str(approval.get("runtime") or DEFAULT_RUNTIME),
        status="in_progress",
        event_type="started",
        message="Mission runtime claim/result gate started local AOR dry-review dispatch.",
        artifacts=[_vault_relative(approval_target, root)],
    )

    aor_result = _run_aor_dry_review(root=root, workspace=workspace, approval=approval)
    if getattr(aor_result, "status", None) != "success":
        update_task_status(
            root,
            task_id=task_id,
            runtime=str(approval.get("runtime") or DEFAULT_RUNTIME),
            status="blocked",
            event_type="blocked",
            message=f"Mission AOR dry-review dispatch failed: {getattr(aor_result, 'status', None)}",
            artifacts=[_vault_relative(marker_target, root)],
        )
        failed_marker = _marker_payload(
            status="failed",
            approval=approval,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            result=None,
            task_closed=False,
            error=str(getattr(aor_result, "error", None) or getattr(aor_result, "escalation_reason", None) or "aor_dispatch_failed"),
        )
        _write_json(marker_target, failed_marker)
        blockers.append(f"aor_dispatch_failed:{getattr(aor_result, 'status', None)}")
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
            runtime_task_claimed=True,
            aor_result_status=getattr(aor_result, "status", None),
        )

    writeback = dict((getattr(aor_result, "outputs", {}) or {}).get("writeback") or {})
    aor_files = list(writeback.get("files_written") or [])
    result = {
        "schema_version": "0.1",
        "type": MISSION_RUNTIME_RESULT_TYPE,
        "result_id": _result_id(str(approval.get("approval_id"))),
        "status": "complete",
        "result_shape": "complete",
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": _vault_relative(workspace, root),
        "task_type": MISSION_TASK_TYPE,
        "agent_bus_task_id": task_id,
        "work_fingerprint": approval.get("work_fingerprint"),
        "runtime": approval.get("runtime"),
        "runtime_instance_id": approval.get("runtime_instance_id"),
        "claimed_at": claim.get("claimed_at") or _now_utc(),
        "completed_at": _now_utc(),
        "aor_workflow_id": MISSION_AOR_WORKFLOW_ID,
        "aor_status": getattr(aor_result, "status", None),
        "aor_audit_id": getattr(aor_result, "audit_id", None),
        "aor_stage_reached": getattr(aor_result, "stage_reached", None),
        "aor_writeback_files": aor_files,
        "result_payload": {
            "local_dry_review_completed": True,
            "artifact_validation_ok": True,
            "task_closed_after_ingestion": False,
            "next_recommended_gate": "ventureops-mission-activation-gate",
        },
        "authority_boundary": _authority_boundary(result_ingested=False, task_closed=False),
    }
    validation = validate_mission_runtime_result(result)
    if not validation.get("ok"):
        blockers.extend(f"mission_runtime_result_invalid:{error}" for error in validation.get("errors") or [])
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
            runtime_task_claimed=True,
            aor_result_status=getattr(aor_result, "status", None),
        )

    _write_json(result_target, result)
    ingestion = _ingest_result_into_workspace(
        root=root,
        workspace=workspace,
        approval=approval,
        result=result,
        result_path=result_target,
        marker_path=marker_target,
        approval_path=approval_target,
    )
    result["result_payload"]["task_closed_after_ingestion"] = True
    result["result_payload"]["ingestion"] = ingestion
    result["authority_boundary"] = _authority_boundary(result_ingested=True, task_closed=True)
    _write_json(result_target, result)
    close_result = update_task_status(
        root,
        task_id=task_id,
        runtime=str(approval.get("runtime") or DEFAULT_RUNTIME),
        status="done",
        event_type="completed",
        message="Mission runtime result ingested and Agent Bus task closed.",
        artifacts=[_vault_relative(result_target, root), _vault_relative(marker_target, root), *aor_files],
    )
    marker = _marker_payload(
        status="executed",
        approval=approval,
        approval_path=approval_target,
        marker_path=marker_target,
        result_path=result_target,
        result=result,
        task_closed=bool(close_result.get("updated")),
    )
    marker_validation = validate_mission_runtime_claim_result_marker(
        marker,
        approval=approval,
        result=result,
        vault_root=root,
        mission_workspace=workspace,
    )
    if not marker_validation.get("ok"):
        blockers.extend(f"claim_result_marker_invalid:{error}" for error in marker_validation.get("errors") or [])
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            result_path=result_target,
            approval=approval,
            blockers=blockers,
            approval_artifact_written=approval_written,
            runtime_task_claimed=True,
            aor_result_status=getattr(aor_result, "status", None),
            result_artifact_written=True,
        )
    _write_json(marker_target, marker)
    return _base_response(
        vault_root=root,
        workspace=workspace,
        approval_path=approval_target,
        marker_path=marker_target,
        result_path=result_target,
        approval=approval,
        blockers=[],
        approval_artifact_written=approval_written,
        claim_result_consumed=True,
        exact_once_marker_written=True,
        runtime_task_claimed=True,
        aor_dispatch_performed=True,
        result_artifact_written=True,
        result_ingested=True,
        task_closed=bool(close_result.get("updated")),
        claim_result=claim,
        mission_runtime_result=result,
        ingestion=ingestion,
        aor_result_status=getattr(aor_result, "status", None),
        aor_audit_id=getattr(aor_result, "audit_id", None),
        aor_writeback_files=aor_files,
    )


def _base_response(
    *,
    vault_root: Path,
    workspace: Path,
    approval_path: Path,
    marker_path: Path,
    result_path: Path,
    approval: dict[str, Any],
    blockers: list[str],
    approval_artifact_written: bool = False,
    claim_result_consumed: bool = False,
    exact_once_marker_written: bool = False,
    runtime_task_claimed: bool = False,
    aor_dispatch_performed: bool = False,
    result_artifact_written: bool = False,
    result_ingested: bool = False,
    task_closed: bool = False,
    duplicate_blocked: bool = False,
    preview_only: bool = False,
    claim_result: dict[str, Any] | None = None,
    mission_runtime_result: dict[str, Any] | None = None,
    ingestion: dict[str, Any] | None = None,
    aor_result_status: str | None = None,
    aor_audit_id: str | None = None,
    aor_writeback_files: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": not blockers and (preview_only or claim_result_consumed or approval_artifact_written),
        "schema_version": "0.1",
        "surface": SURFACE_ID,
        "status": (
            "preview_ready"
            if preview_only and not blockers
            else "mission_runtime_claim_result_consumed"
            if claim_result_consumed
            else "claim_result_approval_artifact_written"
            if approval_artifact_written and not blockers
            else "blocked"
        ),
        "generated_at": _now_utc(),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": _vault_relative(workspace, vault_root),
        "approval_id": approval.get("approval_id"),
        "runtime": approval.get("runtime"),
        "runtime_instance_id": approval.get("runtime_instance_id"),
        "agent_bus_task_id": approval.get("agent_bus_task_id"),
        "work_fingerprint": approval.get("work_fingerprint"),
        "approval_artifact_path": _vault_relative(approval_path, vault_root),
        "result_path": _vault_relative(result_path, vault_root),
        "claim_result_marker_path": _vault_relative(marker_path, vault_root),
        "approval_artifact_written": approval_artifact_written,
        "claim_result_consumed": claim_result_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "runtime_task_claimed": runtime_task_claimed,
        "aor_dispatch_performed": aor_dispatch_performed,
        "mission_result_ingested": result_ingested,
        "agent_bus_task_closed": task_closed,
        "result_artifact_written": result_artifact_written,
        "mission_activation_performed": False,
        "workflow_evolution_applied": False,
        "provider_call_performed": False,
        "browser_action_performed": False,
        "external_send_performed": False,
        "duplicate_blocked_before_claim_or_dispatch": duplicate_blocked,
        "preview_only": preview_only,
        "blockers": list(dict.fromkeys(str(blocker) for blocker in blockers)),
        "warnings": list(approval.get("warnings") or []),
        "claim_result": claim_result or {},
        "mission_runtime_result": mission_runtime_result or {},
        "ingestion": ingestion or {},
        "aor_result_status": aor_result_status,
        "aor_audit_id": aor_audit_id,
        "aor_writeback_files": aor_writeback_files or [],
        "authority_boundary": {
            "runtime_task_claimed": runtime_task_claimed,
            "aor_dispatch_performed": aor_dispatch_performed,
            "mission_result_ingested": result_ingested,
            "agent_bus_task_closed": task_closed,
            "mission_activation_performed": False,
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


def load_mission_runtime_claim_result_state(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
    result_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate Mission runtime claim/result state."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    approval_target = Path(approval_path) if approval_path is not None else default_claim_result_approval_path(workspace)
    marker_target = Path(marker_path) if marker_path is not None else default_claim_result_marker_path(workspace)
    result_target = Path(result_path) if result_path is not None else default_mission_runtime_result_path(workspace)
    if not approval_target.is_absolute():
        approval_target = (root / approval_target).resolve()
    if not marker_target.is_absolute():
        marker_target = (root / marker_target).resolve()
    if not result_target.is_absolute():
        result_target = (root / result_target).resolve()

    errors: list[str] = []
    approval_present = approval_target.exists()
    marker_present = marker_target.exists()
    result_present = result_target.exists()
    approval: dict[str, Any] | None = None
    marker: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    approval_valid = False
    marker_valid = False
    result_valid = False
    stored_task: dict[str, Any] | None = None

    if approval_present:
        try:
            approval = _load_json(approval_target)
            validation = validate_mission_runtime_claim_result_approval(
                approval,
                vault_root=root,
                mission_workspace=workspace,
            )
            approval_valid = bool(validation.get("ok"))
            errors.extend(str(error) for error in validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"claim_result_approval_invalid:{exc}")
    if result_present:
        try:
            result = _load_json(result_target)
            validation = validate_mission_runtime_result(result)
            result_valid = bool(validation.get("ok"))
            errors.extend(str(error) for error in validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"mission_runtime_result_invalid:{exc}")
    if marker_present:
        try:
            marker = _load_json(marker_target)
            if approval is None:
                errors.append("claim_result_marker_present_without_approval_artifact")
            if result is None:
                errors.append("claim_result_marker_present_without_result_artifact")
            if approval is not None and result is not None:
                validation = validate_mission_runtime_claim_result_marker(
                    marker,
                    approval=approval,
                    result=result,
                    vault_root=root,
                    mission_workspace=workspace,
                )
                marker_valid = bool(validation.get("ok"))
                errors.extend(str(error) for error in validation.get("errors") or [])
                stored_task = _mission_task_from_bus(
                    root,
                    task_id=str(marker.get("agent_bus_task_id") or ""),
                    runtime=str(marker.get("runtime") or DEFAULT_RUNTIME),
                )
                if marker_valid:
                    if stored_task is None:
                        errors.append("claim_result_marker_task_missing_from_agent_bus")
                    elif stored_task.get("status") != "done":
                        errors.append(f"claim_result_marker_task_not_closed:{stored_task.get('status')}")
                    elif stored_task.get("owner") != marker.get("runtime"):
                        errors.append("claim_result_marker_task_owner_mismatch")
        except Exception as exc:
            errors.append(f"claim_result_marker_invalid:{exc}")

    consumed = approval_valid and result_valid and marker_valid
    return {
        "ok": not errors,
        "claim_result_approval_artifact_present": approval_present,
        "claim_result_approval_artifact_valid": approval_valid,
        "claim_result_approval_artifact_path": _vault_relative(approval_target, root),
        "mission_runtime_result_present": result_present,
        "mission_runtime_result_valid": result_valid,
        "mission_runtime_result_path": _vault_relative(result_target, root),
        "claim_result_marker_present": marker_present,
        "claim_result_marker_valid": marker_valid,
        "claim_result_marker_path": _vault_relative(marker_target, root),
        "claim_result_consumed": consumed,
        "runtime_task_claimed": consumed and (marker or {}).get("runtime_task_claimed") is True,
        "workflow_dispatched": consumed and (marker or {}).get("workflow_dispatched") is True,
        "aor_dispatch_performed": consumed and (marker or {}).get("aor_dispatch_performed") is True,
        "mission_result_ingested": consumed and (marker or {}).get("mission_result_ingested") is True,
        "agent_bus_task_closed": consumed and (marker or {}).get("agent_bus_task_closed") is True,
        "agent_bus_task_id": (marker or approval or {}).get("agent_bus_task_id"),
        "runtime": (marker or approval or {}).get("runtime"),
        "runtime_instance_id": (marker or approval or {}).get("runtime_instance_id"),
        "result_id": (result or {}).get("result_id"),
        "aor_audit_id": (result or {}).get("aor_audit_id"),
        "aor_writeback_files": list((result or {}).get("aor_writeback_files") or []),
        "stored_task_present": stored_task is not None,
        "stored_task_status": (stored_task or {}).get("status"),
        "stored_task": stored_task or {},
        "mission_id": (approval or result or {}).get("mission_id"),
        "approval_id": (approval or {}).get("approval_id"),
        "errors": list(dict.fromkeys(errors)),
    }
