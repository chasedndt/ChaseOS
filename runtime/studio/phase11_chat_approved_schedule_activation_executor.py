"""Phase 11 Chat approved schedule activation executor.

This governed executor consumes one digest-bound Studio Chat schedule activation
approval exactly once. It enables the matching ChaseOS schedule intent and
regenerates runtime/schedules/index.yaml through the native schedule loader.

It does not mutate OpenClaw/Hermes cron state, write external scheduler files,
dispatch runtimes/workflows, create Agent Bus tasks, call Discord/providers, or
read credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.schedules.loader import (
    _parse_yaml_mapping,
    _validate_schedule,
    enable_schedule,
    export_schedules_for_adapter,
    load_schedule,
)
from runtime.studio.phase11_chat_schedule_intent_activation_readiness import (
    METADATA_BLOCK_KEY as READINESS_METADATA_BLOCK_KEY,
    SURFACE_ID as READINESS_SURFACE_ID,
    _current_enabled_duplicate_blockers,
    _future_enabled_yaml,
)
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_approved_schedule_activation_executor.v1"
SURFACE_ID = "phase11_chat_approved_schedule_activation_executor"
PASS_ID = "studio-chat-approved-schedule-activation-executor"
STATUS = "COMPLETE / APPROVED-SCHEDULE ACTIVATED / VERIFIED / INDEX REGENERATED"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-adapter-export-readiness"
MARKER_DIR = Path("runtime/studio/approvals/_chat_schedule_activation_markers")
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


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "schedule_enable_allowed": True,
        "schedule_index_regeneration_allowed": True,
        "adapter_export_read_model_allowed": True,
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


def _effect_flags(*, enabled: bool = False) -> dict[str, bool]:
    return {
        "target_schedule_yaml_written": enabled,
        "schedule_enabled": enabled,
        "schedule_index_regenerated": enabled,
        "adapter_export_read_model_refreshed": enabled,
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


def _approval_target_blockers(
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
    schedules_root = (vault / "runtime" / "schedules").resolve()
    try:
        target_abs.relative_to(vault.resolve())
    except ValueError:
        blockers.append("approval_target_path_escapes_vault")
    try:
        target_abs.relative_to(schedules_root)
    except ValueError:
        blockers.append("approval_target_path_escapes_runtime_schedules")
    return target_abs, blockers


def _approval_content_blockers(
    *,
    req: ApprovalRequest,
    expected_activation_digest: str,
    current_yaml: str,
    future_yaml: str,
    target_abs: Path | None,
    vault: Path,
) -> list[str]:
    blockers: list[str] = []
    metadata = req.action_spec.metadata or {}
    content = str(req.action_spec.content or "")
    digest_material = metadata.get("activation_digest_material")
    if not isinstance(digest_material, dict):
        digest_material = {}

    if req.action_spec.action_type != "write_file":
        blockers.append("approval_action_type_not_schedule_activation_write_file")
    if metadata.get("phase11_chat_schedule_activation_readiness") is not True:
        blockers.append("approval_not_schedule_activation_readiness_artifact")
    if metadata.get(READINESS_METADATA_BLOCK_KEY) is not True:
        blockers.append("approval_missing_schedule_activation_execution_block")
    if metadata.get("source_surface") != READINESS_SURFACE_ID:
        blockers.append("approval_source_surface_not_schedule_activation_readiness")
    if not expected_activation_digest:
        blockers.append("expected_activation_digest_required")
    elif metadata.get("activation_digest") != expected_activation_digest:
        blockers.append("activation_digest_mismatch")
    if digest_material.get("schedule_yaml_sha256") != _sha256_text(current_yaml):
        blockers.append("current_schedule_yaml_sha_mismatch")
    if digest_material.get("future_enabled_yaml_sha256") != _sha256_text(future_yaml):
        blockers.append("future_enabled_yaml_sha_mismatch")
    if content != future_yaml:
        blockers.append("approval_content_future_enabled_yaml_mismatch")
    if content:
        try:
            parsed = _parse_yaml_mapping(content)
            if parsed.get("enabled") is not True:
                blockers.append("approval_content_not_enabled_true")
            if target_abs is not None:
                _validate_schedule(parsed, target_abs, vault, check_registry=True)
        except Exception as exc:
            blockers.append(f"approval_content_schedule_invalid:{exc}")
    else:
        blockers.append("approval_content_missing")

    for key in (
        "schedule_enabled",
        "schedule_index_regenerated",
        "external_scheduler_changed",
        "openclaw_cron_changed",
        "hermes_cron_changed",
        "agent_bus_task_written",
        "runtime_dispatched",
        "workflow_dispatched",
        "discord_api_called",
        "provider_call_performed",
        "credential_value_read",
    ):
        if key in metadata and bool(metadata.get(key)) is not False:
            blockers.append(f"approval_metadata_effect_flag_not_false:{key}")
    return blockers


def _activation_digest_material(
    *,
    approval_id: str,
    activation_digest: str,
    schedule_id: str,
    target_path: str,
    current_schedule_yaml_sha256: str,
    future_enabled_yaml_sha256: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": approval_id,
        "activation_digest": activation_digest,
        "schedule_id": schedule_id,
        "target_path": target_path,
        "current_schedule_yaml_sha256": current_schedule_yaml_sha256,
        "future_enabled_yaml_sha256": future_enabled_yaml_sha256,
    }


def _summary(
    *,
    approval_id: str,
    schedule_id: str | None,
    activation_digest: str,
    approval_status: str | None = None,
    operator_approval_recorded: bool = False,
    approval_consumed: bool = False,
    exact_once_marker_written: bool = False,
    enabled: bool = False,
    duplicate_blocked_before_target_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "expected_activation_digest_provided": bool(activation_digest),
        "activation_digest": activation_digest or None,
        "schedule_id": schedule_id,
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "duplicate_blocked_before_target_write": duplicate_blocked_before_target_write,
        **_effect_flags(enabled=enabled),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_activation_digest: str,
    schedule_id: str | None,
    target_path: str,
    marker_path: Path | None,
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVED-SCHEDULE ACTIVATION / NO SCHEDULE ENABLEMENT",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            schedule_id=schedule_id,
            activation_digest=expected_activation_digest,
            duplicate_blocked_before_target_write="exact_once_marker_already_present" in unique,
            blocker_count=len(unique),
        ),
        "digest_proof": {
            "expected_activation_digest": expected_activation_digest or None,
            "activation_digest": None,
            "activation_digest_matched": False,
            "executor_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path) if marker_path else None,
            "marker_written": False,
            "duplicate_blocked_before_target_write": "exact_once_marker_already_present" in unique,
        },
        "target_write": {
            "target_path": target_path or None,
            "target_file_written": False,
            "index_path": "runtime/schedules/index.yaml",
            **_effect_flags(enabled=False),
        },
        "adapter_export_read_model": {
            "adapter_export_refreshed": False,
            "enabled_schedule_ids": [],
            "external_scheduler_changed": False,
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
    }


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    schedule_id: str,
    activation_digest: str,
    executor_digest: str,
    target_path: str,
    operator_id: str,
    enabled: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_approved_schedule_activation_executor_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "schedule_id": schedule_id,
        "activation_digest": activation_digest,
        "executor_digest": executor_digest,
        "target_path": target_path,
        "operator_id": operator_id,
        **_effect_flags(enabled=enabled),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _next_audit_path(vault: Path, executor_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{executor_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{executor_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate schedule activation executor audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    schedule_id: str,
    activation_digest: str,
    executor_digest: str,
    target_path: str,
    runtime_adapter_target: str,
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, executor_digest)
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
            "# Phase 11 Chat Approved Schedule Activation Executor",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"schedule_id: {schedule_id}",
            f"activation_digest: {activation_digest}",
            f"executor_digest: {executor_digest}",
            f"target_schedule_path: {target_path}",
            f"runtime_adapter_target: {runtime_adapter_target}",
            "approval_consumed: true",
            "approval_status_mutated: true",
            "exact_once_marker_written: true",
            "target_schedule_yaml_written: true",
            "schedule_enabled: true",
            "schedule_index_regenerated: true",
            "adapter_export_read_model_refreshed: true",
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


def execute_phase11_chat_approved_schedule_activation(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    expected_activation_digest: str | None = None,
    operator_id: str = "operator",
    operator_activation_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one approved activation packet and enable its schedule."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_activation_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    statement = " ".join(str(operator_activation_statement or "").strip().split())
    service = StudioService(vault)
    blockers: list[str] = []
    target_path = ""
    schedule_id: str | None = None
    runtime_adapter_target = ""
    marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json"

    if not requested_approval_id:
        blockers.append("approval_id_required_for_schedule_activation")
    if not expected:
        blockers.append("expected_activation_digest_required")
    if not statement:
        blockers.append("operator_activation_statement_required")

    req = service.get_approval(requested_approval_id) if requested_approval_id else None
    if req is None:
        blockers.append("approval_request_not_loadable")
    else:
        metadata = req.action_spec.metadata or {}
        digest_material = metadata.get("activation_digest_material")
        if not isinstance(digest_material, dict):
            digest_material = {}
        schedule_id = str(digest_material.get("schedule_id") or "").strip() or None
        runtime_adapter_target = str(digest_material.get("runtime_adapter_target") or "").strip()
        target_path = str(req.action_spec.target_path or "").replace("\\", "/")
        if req.status == "pending" and not statement:
            blockers.append("operator_decision_not_approved")
        elif req.status not in {"pending", "approved"}:
            blockers.append("approval_status_not_approved_or_pending_with_statement")

    target_abs, target_blockers = _approval_target_blockers(
        vault=vault,
        target_path=target_path,
        schedule_id=schedule_id or "",
    )
    blockers.extend(target_blockers)
    current_yaml = ""
    future_yaml = ""
    current_intent = None
    if target_abs is not None and target_abs.exists():
        try:
            current_yaml = target_abs.read_text(encoding="utf-8")
            future_yaml, future_blockers = _future_enabled_yaml(current_yaml)
            blockers.extend(future_blockers)
            current_intent = load_schedule(schedule_id or "", vault, check_registry=True)
            if current_intent is None:
                blockers.append("current_schedule_intent_not_loadable")
            elif current_intent.enabled is not False:
                blockers.append("current_schedule_not_disabled")
            else:
                blockers.extend(
                    _current_enabled_duplicate_blockers(
                        vault=vault,
                        schedule_id=current_intent.schedule_id,
                        schedule_kind=current_intent.schedule_kind,
                        workflow_id=current_intent.workflow_id,
                        command_id=current_intent.command_id,
                        adapter=current_intent.runtime_adapter_target,
                    )
                )
        except Exception as exc:
            blockers.append(f"current_schedule_intent_invalid:{exc}")
    elif target_abs is not None:
        blockers.append("current_schedule_intent_file_missing")

    if req is not None:
        blockers.extend(
            _approval_content_blockers(
                req=req,
                expected_activation_digest=expected,
                current_yaml=current_yaml,
                future_yaml=future_yaml,
                target_abs=target_abs,
                vault=vault,
            )
        )
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    if blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_activation_digest=expected,
            schedule_id=schedule_id,
            target_path=target_path,
            marker_path=marker_path,
            blockers=blockers,
        )

    assert req is not None
    assert target_abs is not None
    assert schedule_id is not None
    assert current_intent is not None

    executor_material = _activation_digest_material(
        approval_id=requested_approval_id,
        activation_digest=expected,
        schedule_id=schedule_id,
        target_path=target_path,
        current_schedule_yaml_sha256=_sha256_text(current_yaml),
        future_enabled_yaml_sha256=_sha256_text(future_yaml),
    )
    executor_digest = _sha256_text(_canonical_json(executor_material))
    execution_id = f"chat-approved-schedule-activation-{executor_digest[:20]}"
    approval_recorded_from_statement = False

    try:
        if req.status == "pending":
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = statement
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
                    schedule_id=schedule_id,
                    activation_digest=expected,
                    executor_digest=executor_digest,
                    target_path=target_path,
                    operator_id=operator,
                    enabled=False,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        changed = enable_schedule(schedule_id, vault)
        if changed is not True:
            raise RuntimeError("schedule_enable_returned_no_change")
        enabled_intent = load_schedule(schedule_id, vault, check_registry=True)
        if enabled_intent is None or enabled_intent.enabled is not True:
            raise RuntimeError("schedule_enable_postcheck_failed")
        enabled_yaml = target_abs.read_text(encoding="utf-8")
        if _sha256_text(enabled_yaml) != _sha256_text(future_yaml):
            raise RuntimeError("enabled_schedule_yaml_sha_mismatch")

        adapter_export = export_schedules_for_adapter(enabled_intent.runtime_adapter_target, vault, enabled_only=True)
        enabled_schedule_ids = [item.get("schedule_id") for item in adapter_export]

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    schedule_id=schedule_id,
                    activation_digest=expected,
                    executor_digest=executor_digest,
                    target_path=target_path,
                    operator_id=operator,
                    enabled=True,
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
                "phase11_chat_approved_schedule_activation_executor": True,
                "phase11_chat_approved_schedule_activation_executor_digest": executor_digest,
                "approval_consumed": True,
                "target_schedule_content_sha256": _sha256_text(enabled_yaml),
                "schedule_index_path": "runtime/schedules/index.yaml",
                "next_required_pass": NEXT_RECOMMENDED_PASS,
                **_effect_flags(enabled=True),
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            schedule_id=schedule_id,
            activation_digest=expected,
            executor_digest=executor_digest,
            target_path=target_path,
            runtime_adapter_target=enabled_intent.runtime_adapter_target,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            marker_path.write_text(
                json.dumps(
                    _marker_payload(
                        status="execution_failed",
                        approval_id=requested_approval_id,
                        execution_id=execution_id,
                        schedule_id=schedule_id,
                        activation_digest=expected,
                        executor_digest=executor_digest,
                        target_path=target_path,
                        operator_id=operator,
                        enabled=False,
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
            expected_activation_digest=expected,
            schedule_id=schedule_id,
            target_path=target_path,
            marker_path=marker_path,
            blockers=[f"schedule_activation_execution_failed:{error}"],
        )
        failed["status"] = "FAILED / APPROVED-SCHEDULE ACTIVATION / PARTIAL EXECUTION CHECK REQUIRED"
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
            schedule_id=schedule_id,
            activation_digest=expected,
            approval_status="executed",
            operator_approval_recorded=approval_recorded_from_statement,
            approval_consumed=True,
            exact_once_marker_written=True,
            enabled=True,
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_activation_digest": expected,
            "activation_digest": expected,
            "activation_digest_matched": True,
            "current_schedule_yaml_sha256": _sha256_text(current_yaml),
            "future_enabled_yaml_sha256": _sha256_text(future_yaml),
            "executor_digest": executor_digest,
            "executor_digest_material": executor_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "schedule_id": schedule_id,
                        "target_path": target_path,
                        "target_content_sha256": _sha256_text(enabled_yaml),
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
            "target_file_written": True,
            "target_content_sha256": _sha256_text(enabled_yaml),
            "index_path": "runtime/schedules/index.yaml",
            "schedule_id": schedule_id,
            "schedule_kind": enabled_intent.schedule_kind,
            "workflow_id": enabled_intent.workflow_id,
            "command_id": enabled_intent.command_id,
            **_effect_flags(enabled=True),
        },
        "adapter_export_read_model": {
            "adapter_export_refreshed": True,
            "runtime_adapter_target": enabled_intent.runtime_adapter_target,
            "enabled_schedule_ids": enabled_schedule_ids,
            "enabled_schedule_count": len(enabled_schedule_ids),
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
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


def format_phase11_chat_approved_schedule_activation_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    target = payload.get("target_write") or {}
    lines = [
        "Phase 11 Chat Approved Schedule Activation Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Schedule id: {summary.get('schedule_id') or target.get('schedule_id') or 'missing'}",
        f"Activation digest: {digest.get('activation_digest') or 'missing'}",
        f"Executor digest: {digest.get('executor_digest') or 'missing'}",
        f"Schedule enabled: {target.get('schedule_enabled')}",
        f"Schedule index regenerated: {target.get('schedule_index_regenerated')}",
        f"External scheduler changed: {target.get('external_scheduler_changed')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: approved schedule enablement and schedule index regeneration only; "
        "no external scheduler mutation, OpenClaw/Hermes cron change, Agent Bus task "
        "write, runtime/workflow dispatch, Discord/API provider call, credential read, "
        "or broader canonical writeback."
    )
    return "\n".join(lines)
