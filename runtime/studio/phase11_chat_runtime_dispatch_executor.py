"""Phase 11 Chat runtime-dispatch executor.

This governed executor turns a digest-bound Chat runtime-dispatch preview into
one open Agent Bus task. It is deliberately narrower than a live runtime daemon:
it does not claim the task, run a workflow, call a provider/model, control a
browser, mutate target vault content, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import create_task, init_db, list_tasks
from runtime.studio.phase11_chat_runtime_dispatch_readiness import (
    APPROVAL_CLASS,
    build_phase11_chat_runtime_dispatch_readiness,
)
from runtime.studio.service import ActionSpec, ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_runtime_dispatch_executor.v1"
SURFACE_ID = "phase11_chat_runtime_dispatch_executor"
PASS_ID = "phase11-chat-runtime-dispatch-executor"
STATUS = "COMPLETE / APPROVAL-CONSUMED / VERIFIED / AGENT BUS TASK ENQUEUED"
NEXT_RECOMMENDED_PASS = "operator-select-next-governed-executor-lane"
MARKER_DIR = Path("runtime/studio/approvals/_runtime_dispatch_markers")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"
APPROVAL_ACTION_TYPE = "chat_runtime_dispatch"
APPROVAL_TARGET_PATH = "runtime/agent_bus/agent_bus.sqlite"

_EXECUTOR_REMOVABLE_READINESS_BLOCKERS = {
    "operator_runtime_dispatch_approval_missing",
    "chat_runtime_dispatch_executor_not_invoked_by_readonly_contract",
    "agent_bus_task_write_blocked_by_readonly_contract",
    "workflow_dispatch_blocked_by_readonly_contract",
    "agent_bus_storage_not_present",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or ""))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # Executor uses Studio's durable queue writer.


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _authority() -> dict[str, bool]:
    return {
        "approval_queue_write_allowed": True,
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "runtime_dispatch_allowed": True,
        "runtime_dispatch_enqueue_allowed": True,
        "agent_bus_task_write_allowed": True,
        "runtime_task_claim_allowed": False,
        "runtime_execution_allowed": False,
        "workflow_execution_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "browser_control_allowed": False,
        "target_vault_write_allowed": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _summary(
    *,
    readiness: dict[str, Any],
    approval_id: str = "",
    expected_dispatch_digest: str = "",
    approval_recorded_from_current_statement: bool = False,
    approval_status: str | None = None,
    approval_consumed: bool = False,
    approval_status_mutated: bool = False,
    exact_once_marker_written: bool = False,
    agent_bus_task_written: bool = False,
    duplicate_blocked_before_task_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    source = readiness.get("summary") or {}
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "approval_recorded_from_current_statement": approval_recorded_from_current_statement,
        "expected_dispatch_digest_provided": bool(expected_dispatch_digest),
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_status_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "agent_bus_task_written": agent_bus_task_written,
        "agent_bus_task_created": agent_bus_task_written,
        "duplicate_blocked_before_task_write": duplicate_blocked_before_task_write,
        "runtime_dispatch_enqueued": agent_bus_task_written,
        "runtime_task_claimed": False,
        "runtime_process_started": False,
        "workflow_dispatched": False,
        "provider_call_performed": False,
        "model_call_performed": False,
        "browser_control_performed": False,
        "target_write_performed": False,
        "canonical_mutation_performed": False,
        "selected_runtime_id": source.get("selected_runtime_id"),
        "selected_task_type": source.get("selected_task_type"),
        "agent_bus_mode": source.get("agent_bus_mode"),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    readiness: dict[str, Any],
    approval_id: str,
    expected_dispatch_digest: str,
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    digest = readiness.get("request_digest_proof") or {}
    duplicate = "exact_once_marker_already_present" in unique or "active_agent_bus_task_already_present" in unique
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / RUNTIME-DISPATCH / NO AGENT BUS TASK WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            readiness=readiness,
            approval_id=approval_id,
            expected_dispatch_digest=expected_dispatch_digest,
            duplicate_blocked_before_task_write=duplicate,
            blocker_count=len(unique),
        ),
        "readiness_contract": readiness,
        "digest_proof": {
            "expected_dispatch_digest": expected_dispatch_digest or None,
            "dispatch_digest": digest.get("request_digest"),
            "dispatch_digest_matched": False,
        },
        "approval_record": {
            "approval_id": approval_id or None,
            "approval_path": None,
            "approval_status": None,
            "approval_written": False,
        },
        "exact_once_marker": {
            "marker_path": None,
            "marker_written": False,
            "duplicate_blocked_before_task_write": duplicate,
        },
        "agent_bus_task": {
            "task_id": None,
            "task_written": False,
            "task_claimed": False,
            "workflow_dispatched": False,
            "stored_task": {},
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
    }


def _approval_content(
    *,
    normalized_message: str,
    readiness: dict[str, Any],
    dispatch_digest: str,
    task_id: str,
) -> str:
    summary = readiness.get("summary") or {}
    preview = readiness.get("future_dispatch_packet_preview") or {}
    return json.dumps(
        {
            "schema_version": "phase11_chat_runtime_dispatch_approval.v1",
            "surface": SURFACE_ID,
            "pass": PASS_ID,
            "approval_class": APPROVAL_CLASS,
            "dispatch_digest": dispatch_digest,
            "message_sha256": _sha256_text(normalized_message),
            "selected_runtime_id": summary.get("selected_runtime_id"),
            "selected_task_type": summary.get("selected_task_type"),
            "task_id": task_id,
            "task_packet_preview": preview.get("task_packet_preview") or {},
            "runtime_task_claim_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "browser_control_allowed": False,
            "target_vault_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def _new_approval_request(
    *,
    service: StudioService,
    normalized_message: str,
    readiness: dict[str, Any],
    dispatch_digest: str,
    task_id: str,
    operator_id: str,
) -> ApprovalRequest:
    summary = readiness.get("summary") or {}
    spec = ActionSpec(
        action_type=APPROVAL_ACTION_TYPE,
        target_path=APPROVAL_TARGET_PATH,
        content=_approval_content(
            normalized_message=normalized_message,
            readiness=readiness,
            dispatch_digest=dispatch_digest,
            task_id=task_id,
        ),
        metadata={
            "pass": PASS_ID,
            "phase": "Phase 11",
            "source_surface": SURFACE_ID,
            "approval_class": APPROVAL_CLASS,
            "phase11_chat_runtime_dispatch_executor": True,
            "phase11_chat_runtime_dispatch_digest": dispatch_digest,
            "phase11_chat_runtime_dispatch_task_id": task_id,
            "selected_runtime_id": summary.get("selected_runtime_id"),
            "selected_task_type": summary.get("selected_task_type"),
            "source_message_sha256": _sha256_text(normalized_message),
            "operator_confirmation": operator_id,
            "approval_execution_requires_governed_executor": PASS_ID,
            "agent_bus_task_write_performed": False,
            "runtime_task_claimed": False,
            "workflow_dispatched": False,
            "provider_call_performed": False,
            "browser_control_performed": False,
            "target_vault_write_performed": False,
            "canonical_mutation_performed": False,
        },
        submitted_by="studio-chat",
        note="Phase 11 Chat runtime-dispatch approval; Agent Bus enqueue requires governed executor.",
    )
    return service.queue_for_approval(spec)


def _load_content_payload(req: ApprovalRequest) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(str(req.action_spec.content or "{}"))
    except json.JSONDecodeError as exc:
        return None, f"approval_content_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "approval_content_json_not_object"
    return payload, None


def _find_existing_digest_approval(vault: Path, dispatch_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_chat_runtime_dispatch_digest") != dispatch_digest:
            continue
        if str(payload.get("status") or "") not in active:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
        }
    return None


def _existing_active_task(vault: Path, *, task_id: str, recipient: str, work_fingerprint: str) -> dict[str, Any] | None:
    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    if not sqlite_path.exists():
        return None
    try:
        for task in list_tasks(vault, recipient=recipient):
            if task.get("task_id") == task_id:
                return task
            if (
                str(task.get("work_fingerprint") or "") == work_fingerprint
                and str(task.get("status") or "") in {"open", "claimed", "in_progress", "blocked", "review"}
            ):
                return task
    except Exception:
        return None
    return None


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    dispatch_digest: str,
    task_id: str,
    operator_id: str,
    agent_bus_task_written: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_runtime_dispatch_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "dispatch_digest": dispatch_digest,
        "task_id": task_id,
        "operator_id": operator_id,
        "agent_bus_task_written": agent_bus_task_written,
        "runtime_task_claimed": False,
        "workflow_dispatched": False,
        "provider_call_performed": False,
        "browser_control_performed": False,
        "target_write_performed": False,
        "canonical_mutation_performed": False,
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _next_audit_path(vault: Path, dispatch_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{dispatch_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{dispatch_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate runtime-dispatch audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    dispatch_digest: str,
    task_id: str,
    selected_runtime_id: str | None,
    selected_task_type: str | None,
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, dispatch_digest)
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
            "# Phase 11 Chat Runtime Dispatch Executor",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"dispatch_digest: {dispatch_digest}",
            f"task_id: {task_id}",
            f"selected_runtime_id: {selected_runtime_id or 'missing'}",
            f"selected_task_type: {selected_task_type or 'missing'}",
            "approval_consumed: true",
            "approval_status_mutated: true",
            "exact_once_marker_written: true",
            "agent_bus_task_written: true",
            "runtime_task_claimed: false",
            "workflow_dispatched: false",
            "provider_call_performed: false",
            "browser_control_performed: false",
            "target_write_performed: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_runtime_dispatch(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    message: str | None = None,
    explicit_intent: str | None = "runtime-task",
    requested_runtime_id: str | None = None,
    requested_action: str | None = None,
    expected_dispatch_digest: str | None = None,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
    priority: str = "normal",
) -> dict[str, Any]:
    """Consume approval and enqueue one bounded Agent Bus task."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    expected = str(expected_dispatch_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = _norm(operator_approval_statement)
    requested_approval_id = str(approval_id or "").strip()
    readiness = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or "runtime-task",
        requested_runtime_id=requested_runtime_id,
        requested_action=requested_action,
    )
    digest = readiness.get("request_digest_proof") or {}
    dispatch_digest = str(digest.get("request_digest") or "")
    summary = readiness.get("summary") or {}
    selected_runtime_id = str(summary.get("selected_runtime_id") or "")
    selected_task_type = str(summary.get("selected_task_type") or "")
    preview = readiness.get("future_dispatch_packet_preview") or {}
    task_id = str(preview.get("dispatch_packet_id_preview") or f"chat-runtime-dispatch-{dispatch_digest[:20]}")
    work_fingerprint = f"phase11-chat-runtime-dispatch:{dispatch_digest}"

    blockers = [
        str(item)
        for item in (readiness.get("blocked_reasons") or [])
        if str(item) not in _EXECUTOR_REMOVABLE_READINESS_BLOCKERS
    ]
    if not expected:
        blockers.append("expected_dispatch_digest_required")
    elif expected != dispatch_digest:
        blockers.append("dispatch_digest_mismatch")
    if not approval_statement and not requested_approval_id:
        blockers.append("operator_approval_statement_required_for_runtime_dispatch")
    if priority not in {"low", "normal", "high", "critical"}:
        blockers.append("invalid_agent_bus_priority")

    marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id) or 'pending'}.json"
    service = StudioService(vault)
    req: ApprovalRequest | None = None
    approval_recorded_from_statement = False

    if blockers:
        return _blocked_payload(
            vault=vault,
            readiness=readiness,
            approval_id=requested_approval_id,
            expected_dispatch_digest=expected,
            blockers=blockers,
        )

    if requested_approval_id:
        req = service.get_approval(requested_approval_id)
        if req is None:
            blockers.append("approval_request_not_loadable")
    else:
        duplicate_approval = _find_existing_digest_approval(vault, dispatch_digest)
        if duplicate_approval:
            blockers.append("approval_queue_request_already_exists_for_dispatch_digest")
            requested_approval_id = str(duplicate_approval.get("approval_id") or "")
        else:
            req = _new_approval_request(
                service=service,
                normalized_message=normalized_message,
                readiness=readiness,
                dispatch_digest=dispatch_digest,
                task_id=task_id,
                operator_id=operator,
            )
            requested_approval_id = req.approval_id
            marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json"

    if req is not None:
        metadata = dict(req.action_spec.metadata or {})
        if req.action_spec.action_type != APPROVAL_ACTION_TYPE:
            blockers.append("approval_action_type_not_runtime_dispatch")
        if metadata.get("phase11_chat_runtime_dispatch_digest") != dispatch_digest:
            blockers.append("approval_dispatch_digest_mismatch")
        if metadata.get("phase11_chat_runtime_dispatch_task_id") != task_id:
            blockers.append("approval_task_id_mismatch")
        content_payload, content_error = _load_content_payload(req)
        if content_error:
            blockers.append(content_error)
        else:
            if str((content_payload or {}).get("dispatch_digest") or "") != dispatch_digest:
                blockers.append("approval_content_dispatch_digest_mismatch")
            if str((content_payload or {}).get("selected_runtime_id") or "") != selected_runtime_id:
                blockers.append("approval_content_runtime_mismatch")
            if str((content_payload or {}).get("selected_task_type") or "") != selected_task_type:
                blockers.append("approval_content_task_type_mismatch")

        if req.status == "pending" and not approval_statement:
            blockers.append("operator_approval_statement_required_for_pending_approval")
        elif req.status not in {"pending", "approved"}:
            blockers.append("approval_status_not_approved_or_pending_with_statement")

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    existing_task = _existing_active_task(
        vault,
        task_id=task_id,
        recipient=selected_runtime_id,
        work_fingerprint=work_fingerprint,
    )
    if existing_task is not None:
        blockers.append("active_agent_bus_task_already_present")

    if blockers:
        return _blocked_payload(
            vault=vault,
            readiness=readiness,
            approval_id=requested_approval_id,
            expected_dispatch_digest=expected,
            blockers=blockers,
        )

    assert req is not None
    execution_id = f"runtime-dispatch-{dispatch_digest[:20]}"
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
                    dispatch_digest=dispatch_digest,
                    task_id=task_id,
                    operator_id=operator,
                    agent_bus_task_written=False,
                ),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        init_db(vault)
        notes = _canonical_json(
            {
                "surface": SURFACE_ID,
                "pass": PASS_ID,
                "approval_id": requested_approval_id,
                "approval_class": APPROVAL_CLASS,
                "dispatch_digest": dispatch_digest,
                "source_surface": "StudioChat",
                "runtime_task_claimed_by_executor": False,
                "workflow_dispatched_by_executor": False,
            }
        )
        created = create_task(
            vault,
            task_id=task_id,
            sender="Operator",
            recipient=selected_runtime_id,
            intent="TASK",
            priority=priority,
            request=normalized_message[:1200],
            expected_output="Reviewable ChaseOS runtime result artifact, not canonical mutation.",
            notes=notes,
            ingress_context={
                "source_platform": "phase11-chat",
                "source_channel_class": "phase11_chat",
                "conversation_key": "phase11-chat:runtime-dispatch",
                "origin_message_id": requested_approval_id,
                "control_plane_route": "phase11-chat-runtime-dispatch",
            },
            work_fingerprint=work_fingerprint,
            execution_constraints={
                "write_policy": "none",
                "allowed_write_paths": [],
                "allow_shell_commands": False,
                "allow_live_subprocess": False,
            },
            allow_external_sender=True,
        )
        if not created.get("created"):
            raise RuntimeError(f"agent_bus_task_create_failed:{created.get('reason')}")

        persisted = [
            task for task in list_tasks(vault, recipient=selected_runtime_id)
            if task.get("task_id") == task_id
        ]
        stored_task = persisted[0] if persisted else {}

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    dispatch_digest=dispatch_digest,
                    task_id=task_id,
                    operator_id=operator,
                    agent_bus_task_written=True,
                ),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        req.status = "executed"
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = task_id
        req.execution_error = ""
        req.updated_at = req.execution_finished_at
        metadata = dict(req.action_spec.metadata or {})
        metadata.update(
            {
                "phase11_chat_runtime_dispatch_executor": True,
                "phase11_chat_runtime_dispatch_digest": dispatch_digest,
                "phase11_chat_runtime_dispatch_task_id": task_id,
                "agent_bus_task_write_performed": True,
                "runtime_task_claimed": False,
                "workflow_dispatched": False,
                "provider_call_performed": False,
                "browser_control_performed": False,
                "target_vault_write_performed": False,
                "canonical_mutation_performed": False,
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            dispatch_digest=dispatch_digest,
            task_id=task_id,
            selected_runtime_id=selected_runtime_id,
            selected_task_type=selected_task_type,
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
                        dispatch_digest=dispatch_digest,
                        task_id=task_id,
                        operator_id=operator,
                        agent_bus_task_written=False,
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            req.status = "execution_failed"
            req.execution_finished_at = _now_utc()
            req.execution_status = "error"
            req.result_action_id = task_id
            req.execution_error = error
            req.updated_at = req.execution_finished_at
            _write_approval(service, req)
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            readiness=readiness,
            approval_id=requested_approval_id,
            expected_dispatch_digest=expected,
            blockers=[f"runtime_dispatch_execution_failed:{error}"],
        )
        failed["status"] = "FAILED / RUNTIME-DISPATCH / PARTIAL EXECUTION CHECK REQUIRED"
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
            readiness=readiness,
            approval_id=requested_approval_id,
            expected_dispatch_digest=expected,
            approval_recorded_from_current_statement=approval_recorded_from_statement,
            approval_status="executed",
            approval_consumed=True,
            approval_status_mutated=True,
            exact_once_marker_written=True,
            agent_bus_task_written=True,
            blocker_count=0,
        ),
        "readiness_contract": readiness,
        "digest_proof": {
            "expected_dispatch_digest": expected,
            "dispatch_digest": dispatch_digest,
            "dispatch_digest_matched": True,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "dispatch_digest": dispatch_digest,
                        "task_id": task_id,
                    }
                )
            ),
        },
        "approval_record": {
            "approval_id": requested_approval_id,
            "approval_path": f"{StudioService.APPROVAL_DIR}/{requested_approval_id}.json",
            "approval_status": "executed",
            "approval_written": True,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_task_write": True,
        },
        "agent_bus_task": {
            "task_id": task_id,
            "task_written": True,
            "task_claimed": False,
            "workflow_dispatched": False,
            "stored_task": stored_task,
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


def format_phase11_chat_runtime_dispatch_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    task = payload.get("agent_bus_task") or {}
    marker = payload.get("exact_once_marker") or {}
    lines = [
        "Phase 11 Chat Runtime Dispatch Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Dispatch digest: {digest.get('dispatch_digest') or 'missing'}",
        f"Marker written: {summary.get('exact_once_marker_written')}",
        f"Agent Bus task written: {summary.get('agent_bus_task_written')}",
        f"Task id: {task.get('task_id') or 'none'}",
        f"Selected runtime: {summary.get('selected_runtime_id') or 'missing'}",
        f"Selected task type: {summary.get('selected_task_type') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: approval-gated Agent Bus enqueue only; no task claim, workflow "
        "dispatch, provider/model call, browser control, target vault write, or "
        "canonical writeback."
    )
    if marker.get("marker_path"):
        lines.append(f"Marker path: {marker.get('marker_path')}")
    return "\n".join(lines)
