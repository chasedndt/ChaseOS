"""Governed exact-once executor for Chat-originated Studio approvals.

This lower-phase backend contract consumes an already approved Chat-originated
StudioService approval request, writes an exact-once marker with create-new-only
semantics, executes only the approved StudioService target action, and records
Agent-Activity audit evidence. It deliberately avoids provider calls, browser
control, runtime dispatch, Agent Bus writes, Gate mutation, and canonical
promotion.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import uuid

from runtime.studio.phase11_chat_approval_consumption_readiness import (
    MARKER_DIR,
    PASS_ID as READINESS_PASS_ID,
    SURFACE_ID as READINESS_SURFACE_ID,
    _action_spec,
    _canonical_json,
    _is_chat_originated,
    _rel,
    _sha256_text,
    build_phase11_chat_approval_consumption_readiness,
)
from runtime.studio.service import ActionResult, ApprovalRequest, StudioService

MODEL_VERSION = "studio.phase11_chat_approval_consumption_executor.v1"
SURFACE_ID = "phase11_chat_approval_consumption_executor"
PASS_ID = "phase11-chat-approval-consumption-executor"
STATUS_BLOCKED = "BLOCKED / NO CONSUMPTION / NO TARGET WRITE"
STATUS_EXECUTED = "COMPLETE / APPROVAL CONSUMED / EXACT-ONCE TARGET WRITE EXECUTED"
AUDIT_PREFIX = "2026-05-11-hermes-optimus-chat-approval-consumption"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or ""))


def _marker_path(vault: Path, approval_id: str) -> Path:
    return vault / MARKER_DIR / f"{_safe_id(approval_id) or 'unknown'}.json"


def _approval_path(vault: Path, approval_id: str) -> Path:
    return vault / StudioService.APPROVAL_DIR / f"{_safe_id(approval_id)}.json"


def _load_approval_payload(vault: Path, approval_id: str) -> dict[str, Any] | None:
    path = _approval_path(vault, approval_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_approval_payload(vault: Path, approval_id: str, payload: dict[str, Any]) -> None:
    path = _approval_path(vault, approval_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _result_payload(result: ActionResult | None) -> dict[str, Any] | None:
    return result.to_dict() if result is not None else None


def _write_json_create_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _replace_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _audit_content(*, payload: dict[str, Any], marker_rel: str, target_path: str | None) -> str:
    summary = payload.get("summary") or {}
    result = payload.get("studio_service_result") or {}
    blocked = payload.get("blocked_reasons") or []
    return f"""---
title: Chat Approval Consumption Executor Audit
created: {_now_utc()}
runtime: hermes-optimus
surface: {SURFACE_ID}
status: {payload.get('status')}
approval_id: {summary.get('approval_id') or 'none'}
consumption_digest: {summary.get('consumption_digest') or 'none'}
target_path: {target_path or 'none'}
target_write_performed: {str(summary.get('target_write_performed', False)).lower()}
provider_call_performed: false
runtime_dispatch_performed: false
browser_dispatch_performed: false
agent_bus_task_written: false
related:
  - "[[Hermes-Runtime-Profile]]"
  - "[[HERMES]]"
  - "[[Agent-Activity-Index]]"
---

# Chat Approval Consumption Executor Audit

Runtime lane: Hermes/Optimus.

ChaseOS OS alignment: this is a lower-phase governed executor contract consumed by Phase 10/11 Studio and Chat surfaces. Chat/Studio still do not grant authority; they present approvals and readiness while this backend verifies exact approved material, consumes once, and records audit evidence.

## Result

- approval_id: `{summary.get('approval_id') or 'none'}`
- status: `{payload.get('status')}`
- ok: `{payload.get('ok')}`
- target_path: `{target_path or 'none'}`
- target_write_performed: `{summary.get('target_write_performed', False)}`
- exact_once_marker: `{marker_rel}`
- approval_consumed: `{summary.get('approval_consumed', False)}`
- studio_action_status: `{result.get('status') or 'none'}`

## Blocked reasons

{chr(10).join(f'- `{item}`' for item in blocked) if blocked else '- (none)'}

## Side-effect denial proof

- provider_call_performed: false
- runtime_dispatch_performed: false
- browser_dispatch_performed: false
- agent_bus_task_written: false
- gate_mutation_performed: false
- canonical_writeback_performed: false

## Target writes

{chr(10).join(f'- `{item}`' for item in (result.get('writes') or [])) if result.get('writes') else '- (none)'}
"""


def _write_audit(vault: Path, payload: dict[str, Any], marker_rel: str, target_path: str | None) -> str:
    digest = str((payload.get("summary") or {}).get("consumption_digest") or "no-digest")[:20]
    audit_root = vault / StudioService.AUDIT_DIR
    audit_root.mkdir(parents=True, exist_ok=True)
    audit_path = audit_root / f"{AUDIT_PREFIX}-{digest}.md"
    audit_path.write_text(_audit_content(payload=payload, marker_rel=marker_rel, target_path=target_path), encoding="utf-8")
    return _rel(vault, audit_path)


def _base_response(
    *,
    vault: Path,
    approval_id: str,
    expected_consumption_digest: str,
    readiness: dict[str, Any],
    blocked_reasons: list[str],
    marker_path: Path,
    result: ActionResult | None = None,
    marker_written: bool = False,
    audit_path: str | None = None,
) -> dict[str, Any]:
    digest = str((readiness.get("digest_proof") or {}).get("consumption_digest") or "")
    target = readiness.get("target_write_preflight") or {}
    wrote = bool(result and result.status in {"completed", "dry_run"} and result.writes)
    return {
        "ok": not blocked_reasons and bool(wrote),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS_EXECUTED if not blocked_reasons and wrote else STATUS_BLOCKED,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": {
            "approval_id": approval_id or None,
            "approval_status_before": (readiness.get("summary") or {}).get("approval_status"),
            "approval_consumed": not blocked_reasons and bool(wrote),
            "expected_consumption_digest": expected_consumption_digest,
            "consumption_digest": digest,
            "expected_consumption_digest_matched": bool(expected_consumption_digest and expected_consumption_digest == digest),
            "exact_once_marker_written": marker_written,
            "target_write_performed": wrote,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_dispatch_performed": False,
            "agent_bus_task_written": False,
            "gate_mutation_performed": False,
            "canonical_writeback_performed": False,
            "blocker_count": len(blocked_reasons),
        },
        "readiness_contract": {
            "surface": readiness.get("surface"),
            "model_version": readiness.get("model_version"),
            "readiness_ok": readiness.get("ok"),
            "blocked_reasons": readiness.get("blocked_reasons") or [],
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": marker_written,
            "create_new_only": True,
            "duplicate_consumption_blocks_before_target_write": True,
        },
        "target_execution": {
            "executor": "runtime.studio.service.StudioService._execute",
            "target_path": target.get("target_path"),
            "target_write_performed": wrote,
            "writes": list(result.writes) if result else [],
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
            "agent_activity_audit_required": True,
        },
        "studio_service_result": _result_payload(result),
        "authority": {
            "approval_consumption_allowed": True,
            "target_vault_write_limited_to_approved_action": True,
            "protected_file_write_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "gate_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
    }


def execute_phase11_chat_approval_consumption(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_consumption_digest: str,
    message: str | None = None,
    explicit_intent: str | None = None,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Consume and execute one approved Chat-originated Studio approval exactly once."""

    vault = Path(vault_root).resolve()
    approval_id = str(approval_id or "")
    marker_path = _marker_path(vault, approval_id)
    readiness = build_phase11_chat_approval_consumption_readiness(
        vault,
        approval_id=approval_id,
        message=message,
        explicit_intent=explicit_intent or "approval-action",
    )
    digest = str((readiness.get("digest_proof") or {}).get("consumption_digest") or "")
    selected = readiness.get("selected_approval") or {}
    blocked: list[str] = []

    if not approval_id:
        blocked.append("approval_id_required")
    if not expected_consumption_digest:
        blocked.append("expected_consumption_digest_required")
    elif expected_consumption_digest != digest:
        blocked.append("expected_consumption_digest_mismatch")

    payload = _load_approval_payload(vault, approval_id) if approval_id else None
    if payload is None:
        blocked.append("approval_artifact_not_found")
    elif not _is_chat_originated(payload):
        blocked.append("approval_not_chat_originated")

    status = str((payload or {}).get("status") or selected.get("status") or "unknown")
    if status != "approved":
        blocked.append("approval_status_not_approved" if status in {"pending", "rejected", "expired", "unknown"} else "approval_already_consumed_or_not_approved")

    if marker_path.exists():
        blocked.append("exact_once_marker_already_present")

    readiness_blockers = set(readiness.get("blocked_reasons") or [])
    for item in (
        "approval_artifact_not_found",
        "approval_artifact_json_malformed",
        "approval_artifact_json_not_object",
        "prompt_injection_indicator_present",
        "approval_not_chat_originated",
        "source_message_digest_mismatch",
        "future_target_path_collision",
        "canonical_or_high_authority_target_blocked",
        "studio_service_validation_gate_blocked",
        "future_exact_once_marker_already_present",
        "phase11_chat_action_digest_missing",
    ):
        if item in readiness_blockers or any(str(reason).startswith(item) for reason in readiness_blockers):
            blocked.append(item)

    service = StudioService(vault)
    req = service.get_approval(approval_id) if not blocked else None
    validation = service.validate_action(req.action_spec) if req else None
    if validation and validation.gate_blocked:
        blocked.append("studio_service_validation_gate_blocked")

    if blocked or req is None:
        response = _base_response(
            vault=vault,
            approval_id=approval_id,
            expected_consumption_digest=expected_consumption_digest,
            readiness=readiness,
            blocked_reasons=list(dict.fromkeys(blocked)),
            marker_path=marker_path,
        )
        return response

    now = _now_utc()
    execution_id = f"chat-consumption-{uuid.uuid4()}"
    marker_payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "record_type": "phase11_chat_approval_consumption_exact_once_marker",
        "approval_id": approval_id,
        "consumption_digest": digest,
        "expected_consumption_digest": expected_consumption_digest,
        "approval_status_before": status,
        "target_path": req.action_spec.target_path,
        "operator_id": operator_id or "operator",
        "execution_id": execution_id,
        "created_at_utc": now,
        "updated_at_utc": now,
        "state": "reserved",
        "target_write_performed": False,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "browser_dispatch_performed": False,
        "agent_bus_task_written": False,
        "source_readiness": {
            "surface": READINESS_SURFACE_ID,
            "pass": READINESS_PASS_ID,
            "consumption_digest": digest,
        },
    }
    try:
        _write_json_create_new(marker_path, marker_payload)
    except FileExistsError:
        blocked.append("exact_once_marker_already_present")
        return _base_response(
            vault=vault,
            approval_id=approval_id,
            expected_consumption_digest=expected_consumption_digest,
            readiness=readiness,
            blocked_reasons=blocked,
            marker_path=marker_path,
        )

    approval_payload = payload or req.to_dict()
    approval_payload.update(
        {
            "status": "executing",
            "execution_id": execution_id,
            "execution_started_at": now,
            "execution_finished_at": None,
            "execution_status": None,
            "result_action_id": None,
            "execution_error": "",
            "updated_at": now,
            "consumption_marker_path": _rel(vault, marker_path),
            "consumption_digest": digest,
            "consumed_by": operator_id or "operator",
        }
    )
    _write_approval_payload(vault, approval_id, approval_payload)

    result = service._execute(req.action_spec, approval_id=approval_id)  # governed target writer only; no bus dispatch.
    finished = _now_utc()
    final_status = "executed" if result.status in {"completed", "dry_run"} else "execution_failed"
    approval_payload.update(
        {
            "status": final_status,
            "execution_finished_at": finished,
            "execution_status": result.status,
            "result_action_id": result.action_id,
            "execution_error": "; ".join(result.errors),
            "updated_at": finished,
            "approval_consumed": result.status in {"completed", "dry_run"},
        }
    )
    _write_approval_payload(vault, approval_id, approval_payload)

    marker_payload.update(
        {
            "updated_at_utc": finished,
            "state": final_status,
            "target_write_performed": bool(result.status in {"completed", "dry_run"} and result.writes),
            "target_writes": list(result.writes),
            "studio_service_result": result.to_dict(),
        }
    )
    _replace_json(marker_path, marker_payload)

    response = _base_response(
        vault=vault,
        approval_id=approval_id,
        expected_consumption_digest=expected_consumption_digest,
        readiness=readiness,
        blocked_reasons=[] if result.status in {"completed", "dry_run"} else ["target_write_execution_failed"],
        marker_path=marker_path,
        result=result,
        marker_written=True,
    )
    audit_path = _write_audit(vault, response, _rel(vault, marker_path), req.action_spec.target_path)
    response["audit_record"] = {
        "audit_record_written": True,
        "audit_record_path": audit_path,
        "agent_activity_audit_required": True,
    }
    return response


def format_phase11_chat_approval_consumption_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    marker = payload.get("exact_once_marker") or {}
    audit = payload.get("audit_record") or {}
    return "\n".join(
        [
            "Phase 11 Chat Approval Consumption Executor",
            f"  status: {payload.get('status')}",
            f"  approval_id: {summary.get('approval_id') or 'none'}",
            f"  consumption_digest: {summary.get('consumption_digest') or 'none'}",
            f"  digest_matched: {summary.get('expected_consumption_digest_matched')}",
            f"  marker_written: {marker.get('marker_written')}",
            f"  target_write_performed: {summary.get('target_write_performed')}",
            f"  audit_record_path: {audit.get('audit_record_path') or 'none'}",
            "  Boundary: exact approved target action only; no provider call, runtime dispatch, browser control, Agent Bus task write, Gate mutation, or canonical writeback.",
        ]
    )
