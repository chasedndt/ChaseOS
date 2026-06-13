"""Phase 11 Chat schedule proposal consumption executor.

This governed executor consumes one digest-bound Studio Chat schedule proposal
approval and records the approved proposal exactly once in Studio-owned staging
state. It does not write runtime/schedules YAML, regenerate the schedule index,
change OpenClaw/Hermes cron state, dispatch workflows, create Agent Bus tasks,
call Discord, call providers, read credentials, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.schedules.loader import _parse_yaml_mapping, _validate_schedule
from runtime.studio.phase11_chat_schedule_proposal_packet import (
    METADATA_BLOCK_KEY,
    SURFACE_ID as PACKET_SURFACE_ID,
)
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_schedule_proposal_consumption_executor.v1"
SURFACE_ID = "phase11_chat_schedule_proposal_consumption_executor"
PASS_ID = "studio-chat-schedule-proposal-consumption"
STATUS = "COMPLETE / APPROVAL-CONSUMED / VERIFIED / SCHEDULE PROPOSAL RECORDED"
NEXT_RECOMMENDED_PASS = "studio-chat-approved-schedule-intent-writer"
SCHEDULE_PROPOSAL_ROOT = "runtime/studio/chat/schedule-proposals"
MARKER_DIR = Path("runtime/studio/approvals/_chat_schedule_proposal_consumption_markers")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "staged_schedule_proposal_write_allowed": True,
        "schedule_intent_yaml_write_allowed": False,
        "schedule_index_regeneration_allowed": False,
        "schedule_enable_allowed": False,
        "external_scheduler_mutation_allowed": False,
        "openclaw_cron_mutation_allowed": False,
        "hermes_cron_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_dispatch_allowed": False,
        "discord_api_calls_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _effect_flags() -> dict[str, bool]:
    return {
        "target_schedule_yaml_written": False,
        "schedule_intent_written": False,
        "schedule_index_regenerated": False,
        "schedule_enabled": False,
        "external_scheduler_changed": False,
        "openclaw_cron_changed": False,
        "hermes_cron_changed": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "discord_api_called": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
    }


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # Reuse Studio's durable queue writer.


def _load_schedule_intent(req: ApprovalRequest) -> tuple[dict[str, Any] | None, str | None]:
    text = str(req.action_spec.content or "")
    if not text.strip():
        return None, "approval_content_schedule_yaml_missing"
    try:
        parsed = _parse_yaml_mapping(text)
    except Exception as exc:
        return None, f"approval_content_schedule_yaml_malformed:{exc}"
    if not isinstance(parsed, dict):
        return None, "approval_content_schedule_yaml_not_mapping"
    return parsed, None


def _target_path_blockers(
    *,
    vault: Path,
    target_path: str,
    schedule_id: str,
) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    normalized = str(target_path or "").replace("\\", "/").strip()
    if not normalized:
        blockers.append("approval_target_path_required")
        return None, blockers
    if not schedule_id:
        blockers.append("schedule_id_required")
    if schedule_id and not re.fullmatch(r"[A-Za-z0-9_-]+", schedule_id):
        blockers.append("schedule_id_not_path_safe")
    expected = f"runtime/schedules/{schedule_id}.yaml" if schedule_id else ""
    if expected and normalized != expected:
        blockers.append("approval_target_path_content_mismatch")
    if not normalized.startswith("runtime/schedules/"):
        blockers.append("approval_target_path_not_runtime_schedules")
    if normalized == "runtime/schedules/index.yaml":
        blockers.append("approval_target_path_is_schedule_index")
    if not normalized.endswith(".yaml"):
        blockers.append("approval_target_path_not_yaml")
    target_abs = (vault / normalized).resolve()
    schedule_root_abs = (vault / "runtime" / "schedules").resolve()
    try:
        target_abs.relative_to(vault.resolve())
    except ValueError:
        blockers.append("approval_target_path_escapes_vault")
    try:
        target_abs.relative_to(schedule_root_abs)
    except ValueError:
        blockers.append("approval_target_path_escapes_runtime_schedules")
    return target_abs, blockers


def _staged_target_path(
    *,
    vault: Path,
    schedule_id: str,
) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    if not schedule_id:
        blockers.append("schedule_id_required_for_staged_record")
        return None, blockers
    if _safe_id(schedule_id) != schedule_id:
        blockers.append("schedule_id_not_safe_for_staged_record")
    staged_abs = (vault / SCHEDULE_PROPOSAL_ROOT / f"{_safe_id(schedule_id)}.json").resolve()
    staging_root_abs = (vault / SCHEDULE_PROPOSAL_ROOT).resolve()
    try:
        staged_abs.relative_to(vault.resolve())
    except ValueError:
        blockers.append("staged_schedule_proposal_target_escapes_vault")
    try:
        staged_abs.relative_to(staging_root_abs)
    except ValueError:
        blockers.append("staged_schedule_proposal_target_escapes_root")
    return staged_abs, blockers


def _validate_schedule_preview(
    *,
    vault: Path,
    schedule_intent: dict[str, Any] | None,
    target_abs: Path | None,
) -> list[str]:
    if schedule_intent is None or target_abs is None:
        return []
    try:
        _validate_schedule(schedule_intent, target_abs, vault, check_registry=False)
    except Exception as exc:
        return [f"schedule_intent_preview_invalid:{exc}"]
    return []


def _content_blockers(
    *,
    req: ApprovalRequest,
    schedule_intent: dict[str, Any] | None,
    expected_schedule_digest: str,
) -> list[str]:
    blockers: list[str] = []
    metadata = req.action_spec.metadata or {}
    intent = schedule_intent or {}
    schedule_yaml = str(req.action_spec.content or "")
    metadata_digest = str(metadata.get("phase11_chat_schedule_proposal_digest") or "")
    metadata_yaml_sha = str(metadata.get("phase11_chat_schedule_yaml_sha256") or "")
    schedule_id = str(intent.get("schedule_id") or "")
    schedule_kind = str(intent.get("schedule_kind") or "")
    cadence = intent.get("cadence") if isinstance(intent.get("cadence"), dict) else {}

    if req.action_spec.action_type != "create_file":
        blockers.append("approval_action_type_not_schedule_proposal_create_file")
    if metadata.get("phase11_chat_schedule_proposal_packet") is not True:
        blockers.append("approval_not_schedule_proposal_packet_artifact")
    if metadata.get(METADATA_BLOCK_KEY) is not True:
        blockers.append("approval_missing_schedule_proposal_execution_block")
    if metadata.get("source_surface") != PACKET_SURFACE_ID:
        blockers.append("approval_source_surface_not_schedule_proposal_packet")
    if metadata.get("approval_queue_write_only") is not True:
        blockers.append("approval_not_queue_write_only")
    if not metadata_digest:
        blockers.append("approval_metadata_schedule_digest_missing")
    if expected_schedule_digest and metadata_digest and expected_schedule_digest != metadata_digest:
        blockers.append("schedule_digest_mismatch")
    if not metadata_yaml_sha:
        blockers.append("approval_metadata_schedule_yaml_sha_missing")
    elif metadata_yaml_sha != _sha256_text(schedule_yaml):
        blockers.append("approval_content_schedule_yaml_sha_mismatch")
    if metadata.get("schedule_id") != schedule_id:
        blockers.append("approval_metadata_schedule_id_mismatch")
    if metadata.get("schedule_kind") != schedule_kind:
        blockers.append("approval_metadata_schedule_kind_mismatch")
    if schedule_kind == "workflow" and metadata.get("workflow_id") != intent.get("workflow_id"):
        blockers.append("approval_metadata_workflow_id_mismatch")
    if schedule_kind == "command" and metadata.get("command_id") != intent.get("command_id"):
        blockers.append("approval_metadata_command_id_mismatch")
    if metadata.get("cron_expression") != cadence.get("cron_expression"):
        blockers.append("approval_metadata_cron_expression_mismatch")
    if metadata.get("timezone") != cadence.get("timezone"):
        blockers.append("approval_metadata_timezone_mismatch")
    if metadata.get("runtime_adapter_target") != intent.get("runtime_adapter_target"):
        blockers.append("approval_metadata_runtime_adapter_target_mismatch")
    if intent.get("enabled") is True:
        blockers.append("schedule_intent_enabled_true_not_allowed_by_consumer")

    for key in (
        "schedule_intent_written",
        "schedule_index_regenerated",
        "schedule_enabled",
        "external_scheduler_changed",
        "agent_bus_task_written",
        "runtime_dispatched",
        "workflow_dispatched",
        "discord_api_called",
        "provider_call_performed",
        "credential_value_read",
        "canonical_mutation_allowed",
    ):
        if key in metadata and bool(metadata.get(key)) is not False:
            blockers.append(f"approval_metadata_effect_flag_not_false:{key}")
    return blockers


def _consumption_digest_material(
    *,
    approval_id: str,
    schedule_digest: str,
    target_path: str,
    staged_target_path: str,
    approved_content_sha256: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": approval_id,
        "schedule_digest": schedule_digest,
        "target_path": target_path,
        "staged_target_path": staged_target_path,
        "approved_content_sha256": approved_content_sha256,
    }


def _summary(
    *,
    approval_id: str,
    schedule_intent: dict[str, Any] | None = None,
    expected_schedule_digest: str = "",
    schedule_digest: str = "",
    approval_status: str | None = None,
    operator_approval_recorded: bool = False,
    approval_consumed: bool = False,
    approval_status_mutated: bool = False,
    exact_once_marker_written: bool = False,
    staged_schedule_proposal_written: bool = False,
    duplicate_blocked_before_target_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    intent = schedule_intent or {}
    cadence = intent.get("cadence") if isinstance(intent.get("cadence"), dict) else {}
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "expected_schedule_digest_provided": bool(expected_schedule_digest),
        "schedule_digest": schedule_digest or None,
        "schedule_id": intent.get("schedule_id"),
        "schedule_kind": intent.get("schedule_kind"),
        "workflow_id": intent.get("workflow_id"),
        "command_id": intent.get("command_id"),
        "cron_expression": cadence.get("cron_expression"),
        "timezone": cadence.get("timezone"),
        "runtime_adapter_target": intent.get("runtime_adapter_target"),
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_status_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "staged_schedule_proposal_written": staged_schedule_proposal_written,
        "duplicate_blocked_before_target_write": duplicate_blocked_before_target_write,
        **_effect_flags(),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_schedule_digest: str,
    schedule_intent: dict[str, Any] | None,
    schedule_digest: str,
    target_path: str,
    staged_target: Path | None,
    marker_path: Path | None,
    blockers: list[str],
) -> dict[str, Any]:
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVAL-CONSUMPTION / NO SCHEDULE PROPOSAL RECORD",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            schedule_intent=schedule_intent,
            expected_schedule_digest=expected_schedule_digest,
            schedule_digest=schedule_digest,
            staged_schedule_proposal_written=False,
            duplicate_blocked_before_target_write="exact_once_marker_already_present" in unique_blockers,
            blocker_count=len(unique_blockers),
        ),
        "digest_proof": {
            "expected_schedule_digest": expected_schedule_digest or None,
            "schedule_digest": schedule_digest or None,
            "schedule_digest_matched": False,
            "consumption_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path) if marker_path else None,
            "marker_written": False,
            "duplicate_blocked_before_target_write": "exact_once_marker_already_present" in unique_blockers,
        },
        "target_write": {
            "target_path": target_path or None,
            "staged_schedule_proposal_path": _rel(vault, staged_target) if staged_target else None,
            "target_file_written": False,
            "staged_schedule_proposal_written": False,
            **_effect_flags(),
        },
        "execution_record": {
            "execution_id": None,
            "execution_status": None,
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique_blockers,
    }


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    schedule_digest: str,
    consumption_digest: str,
    target_path: str,
    staged_target_path: str,
    operator_id: str,
    staged_schedule_proposal_written: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_schedule_proposal_consumption_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "schedule_digest": schedule_digest,
        "consumption_digest": consumption_digest,
        "target_path": target_path,
        "staged_target_path": staged_target_path,
        "operator_id": operator_id,
        "staged_schedule_proposal_written": staged_schedule_proposal_written,
        **_effect_flags(),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _target_payload(
    *,
    schedule_intent: dict[str, Any],
    future_schedule_yaml: str,
    approval_id: str,
    execution_id: str,
    schedule_digest: str,
    consumption_digest: str,
    operator_id: str,
    target_path: str,
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_approved_schedule_proposal_record.v1",
        "status": "approved_schedule_proposal_recorded",
        "approval_id": approval_id,
        "approval_consumed": True,
        "approval_consumed_by": SURFACE_ID,
        "approval_consumption_execution_id": execution_id,
        "approval_consumption_digest": consumption_digest,
        "approved_by": operator_id,
        "approved_at_utc": _now_utc(),
        "schedule_digest": schedule_digest,
        "target_schedule_path": target_path,
        "future_schedule_intent": schedule_intent,
        "future_schedule_yaml": future_schedule_yaml,
        "schedule_intent_writer_required": True,
        "next_required_pass": NEXT_RECOMMENDED_PASS,
        "approval_required_before_effect": True,
        **_effect_flags(),
    }


def _next_audit_path(vault: Path, consumption_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{consumption_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{consumption_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate schedule proposal consumption audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    schedule_digest: str,
    consumption_digest: str,
    target_path: str,
    staged_target_path: str,
    schedule_intent: dict[str, Any],
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, consumption_digest)
    cadence = schedule_intent.get("cadence") if isinstance(schedule_intent.get("cadence"), dict) else {}
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Chat Schedule Proposal Consumption Executor",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"schedule_digest: {schedule_digest}",
            f"consumption_digest: {consumption_digest}",
            f"schedule_id: {schedule_intent.get('schedule_id') or 'missing'}",
            f"schedule_kind: {schedule_intent.get('schedule_kind') or 'missing'}",
            f"workflow_id: {schedule_intent.get('workflow_id') or 'none'}",
            f"command_id: {schedule_intent.get('command_id') or 'none'}",
            f"cron_expression: {cadence.get('cron_expression') or 'missing'}",
            f"timezone: {cadence.get('timezone') or 'missing'}",
            f"runtime_adapter_target: {schedule_intent.get('runtime_adapter_target') or 'missing'}",
            f"target_schedule_path: {target_path}",
            f"staged_schedule_proposal_path: {staged_target_path}",
            "approval_consumed: true",
            "approval_status_mutated: true",
            "exact_once_marker_written: true",
            "staged_schedule_proposal_written: true",
            "target_schedule_yaml_written: false",
            "schedule_intent_written: false",
            "schedule_index_regenerated: false",
            "schedule_enabled: false",
            "external_scheduler_changed: false",
            "openclaw_cron_changed: false",
            "hermes_cron_changed: false",
            "agent_bus_task_written: false",
            "runtime_dispatched: false",
            "workflow_dispatched: false",
            "discord_api_called: false",
            "provider_call_performed: false",
            "credential_value_read: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_schedule_proposal_consumption(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    expected_schedule_digest: str | None = None,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one approved schedule proposal artifact into Studio staging."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_schedule_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = " ".join(str(operator_approval_statement or "").strip().split())
    service = StudioService(vault)
    blockers: list[str] = []
    schedule_intent: dict[str, Any] | None = None
    schedule_digest = ""
    target_path = ""

    if not requested_approval_id:
        blockers.append("approval_id_required_for_schedule_proposal_consumption")
    if not expected:
        blockers.append("expected_schedule_digest_required")

    req = service.get_approval(requested_approval_id) if requested_approval_id else None
    if req is None:
        blockers.append("approval_request_not_loadable")
    else:
        target_path = str(req.action_spec.target_path or "").replace("\\", "/")
        if req.status == "pending" and not approval_statement:
            blockers.append("operator_decision_not_approved")
        elif req.status not in {"pending", "approved"}:
            blockers.append("approval_status_not_approved_or_pending_with_statement")
        schedule_intent, content_error = _load_schedule_intent(req)
        if content_error:
            blockers.append(content_error)
        else:
            metadata = req.action_spec.metadata or {}
            schedule_digest = str(metadata.get("phase11_chat_schedule_proposal_digest") or "")
            blockers.extend(
                _content_blockers(
                    req=req,
                    schedule_intent=schedule_intent,
                    expected_schedule_digest=expected,
                )
            )

    schedule_id = str((schedule_intent or {}).get("schedule_id") or "")
    target_abs, target_blockers = _target_path_blockers(
        vault=vault,
        target_path=target_path,
        schedule_id=schedule_id,
    )
    blockers.extend(target_blockers)
    blockers.extend(_validate_schedule_preview(vault=vault, schedule_intent=schedule_intent, target_abs=target_abs))
    staged_abs, staged_blockers = _staged_target_path(vault=vault, schedule_id=schedule_id)
    blockers.extend(staged_blockers)
    marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json"

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    if staged_abs is not None and staged_abs.exists():
        blockers.append("staged_schedule_proposal_target_collision")
    if target_abs is not None and target_abs.exists():
        blockers.append("schedule_intent_target_collision")

    if blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_schedule_digest=expected,
            schedule_intent=schedule_intent,
            schedule_digest=schedule_digest,
            target_path=target_path,
            staged_target=staged_abs,
            marker_path=marker_path,
            blockers=blockers,
        )

    assert req is not None
    assert schedule_intent is not None
    assert target_abs is not None
    assert staged_abs is not None

    approved_content = str(req.action_spec.content or "")
    approved_content_sha256 = _sha256_text(approved_content)
    staged_rel = _rel(vault, staged_abs)
    consumption_material = _consumption_digest_material(
        approval_id=requested_approval_id,
        schedule_digest=schedule_digest,
        target_path=target_path,
        staged_target_path=staged_rel,
        approved_content_sha256=approved_content_sha256,
    )
    consumption_digest = _sha256_text(_canonical_json(consumption_material))
    execution_id = f"chat-schedule-proposal-consumption-{consumption_digest[:20]}"
    approval_recorded_from_statement = False

    try:
        if req.status == "pending" and approval_statement:
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = approval_statement
            req.updated_at = _now_utc()
            _write_approval(service, req)
            approval_recorded_from_statement = True

        req.status = "executing"
        req.execution_id = execution_id
        req.execution_started_at = _now_utc()
        req.execution_finished_at = None
        req.execution_status = None
        req.result_action_id = None
        req.execution_error = ""
        req.updated_at = req.execution_started_at
        _write_approval(service, req)

        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executing",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    schedule_digest=schedule_digest,
                    consumption_digest=consumption_digest,
                    target_path=target_path,
                    staged_target_path=staged_rel,
                    operator_id=operator,
                    staged_schedule_proposal_written=False,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        written_payload = _target_payload(
            schedule_intent=schedule_intent,
            future_schedule_yaml=approved_content,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            schedule_digest=schedule_digest,
            consumption_digest=consumption_digest,
            operator_id=operator,
            target_path=target_path,
        )
        target_content = json.dumps(written_payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        staged_abs.parent.mkdir(parents=True, exist_ok=True)
        staged_abs.write_text(target_content, encoding="utf-8")

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    schedule_digest=schedule_digest,
                    consumption_digest=consumption_digest,
                    target_path=target_path,
                    staged_target_path=staged_rel,
                    operator_id=operator,
                    staged_schedule_proposal_written=True,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        req.status = "executed"
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = execution_id
        req.execution_error = ""
        req.updated_at = req.execution_finished_at
        metadata = dict(req.action_spec.metadata or {})
        metadata.update(
            {
                "phase11_chat_schedule_proposal_consumption_executor": True,
                "phase11_chat_schedule_proposal_consumption_digest": consumption_digest,
                "staged_schedule_proposal_write_performed": True,
                "approval_consumed": True,
                **_effect_flags(),
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            schedule_digest=schedule_digest,
            consumption_digest=consumption_digest,
            target_path=target_path,
            staged_target_path=staged_rel,
            schedule_intent=schedule_intent,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_text(
                json.dumps(
                    _marker_payload(
                        status="execution_failed",
                        approval_id=requested_approval_id,
                        execution_id=execution_id,
                        schedule_digest=schedule_digest,
                        consumption_digest=consumption_digest,
                        target_path=target_path,
                        staged_target_path=staged_rel,
                        operator_id=operator,
                        staged_schedule_proposal_written=staged_abs.exists(),
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            req.status = "execution_failed"
            req.execution_finished_at = _now_utc()
            req.execution_status = "error"
            req.result_action_id = execution_id
            req.execution_error = error
            req.updated_at = req.execution_finished_at
            _write_approval(service, req)
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_schedule_digest=expected,
            schedule_intent=schedule_intent,
            schedule_digest=schedule_digest,
            target_path=target_path,
            staged_target=staged_abs,
            marker_path=marker_path,
            blockers=[f"schedule_proposal_consumption_execution_failed:{error}"],
        )
        failed["status"] = "FAILED / APPROVAL-CONSUMPTION / PARTIAL EXECUTION CHECK REQUIRED"
        return failed

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=requested_approval_id,
            schedule_intent=schedule_intent,
            expected_schedule_digest=expected,
            schedule_digest=schedule_digest,
            approval_status="executed",
            operator_approval_recorded=approval_recorded_from_statement,
            approval_consumed=True,
            approval_status_mutated=True,
            exact_once_marker_written=True,
            staged_schedule_proposal_written=True,
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_schedule_digest": expected,
            "schedule_digest": schedule_digest,
            "schedule_digest_matched": expected == schedule_digest,
            "approved_content_sha256": approved_content_sha256,
            "consumption_digest": consumption_digest,
            "consumption_digest_material": consumption_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "schedule_digest": schedule_digest,
                        "staged_target_path": staged_rel,
                        "target_content_sha256": _sha256_text(target_content),
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_target_write": True,
        },
        "target_write": {
            "target_path": target_path,
            "staged_schedule_proposal_path": staged_rel,
            "target_file_written": False,
            "staged_schedule_proposal_written": True,
            "staged_target_content_sha256": _sha256_text(target_content),
            "schedule_id": schedule_intent.get("schedule_id"),
            "schedule_kind": schedule_intent.get("schedule_kind"),
            "workflow_id": schedule_intent.get("workflow_id"),
            "command_id": schedule_intent.get("command_id"),
            **_effect_flags(),
        },
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
            "approval_status": "executed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
    }


def format_phase11_chat_schedule_proposal_consumption_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    marker = payload.get("exact_once_marker") or {}
    target = payload.get("target_write") or {}
    lines = [
        "Phase 11 Chat Schedule Proposal Consumption Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Schedule digest: {digest.get('schedule_digest') or 'missing'}",
        f"Consumption digest: {digest.get('consumption_digest') or 'missing'}",
        f"Marker written: {summary.get('exact_once_marker_written')}",
        f"Staged proposal path: {target.get('staged_schedule_proposal_path') or 'missing'}",
        f"Target schedule path: {target.get('target_path') or summary.get('target_path') or 'missing'}",
        f"Staged schedule proposal written: {summary.get('staged_schedule_proposal_written')}",
        f"Schedule id: {target.get('schedule_id') or summary.get('schedule_id') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: schedule-proposal approval consumption only; no runtime/schedules "
        "YAML write, schedule index regeneration, external scheduler mutation, "
        "OpenClaw/Hermes cron change, Agent Bus task write, runtime/workflow "
        "dispatch, Discord/API provider call, credential read, or canonical writeback."
    )
    if marker.get("marker_path"):
        lines.append(f"Marker path: {marker.get('marker_path')}")
    return "\n".join(lines)
