"""Phase 11 Chat approval queue write execution proof.

This pass converts a supported Chat proposal preview into one durable
``StudioService`` approval request, but it does not approve, execute, or write
the proposal target. Writes are limited to the Studio approval queue and require
an exact action digest from a prior preview.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_approval_handoff_queue_contract import (
    build_phase11_chat_approval_handoff_queue_contract,
)
from runtime.studio.phase11_chat_conversation_persistence_contract import (
    build_phase11_chat_conversation_persistence_contract,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_approval_queue_write.v1"
SURFACE_ID = "phase11_chat_approval_queue_write_execution_proof"
PASS_ID = "phase11-chat-approval-queue-write-execution-proof"
STATUS_PREVIEW = "READY / APPROVAL-QUEUE-WRITE-PREVIEW / TARGET WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / EXECUTION BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-browser-dispatch-readiness-contract"
DEFERRED_EXECUTION_METADATA_KEY = "phase11_chat_queue_write_execution_blocked"
CHAT_HANDOFF_AUDIT_DIR = "runtime/studio/approvals/chat-handoffs"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _approval_root(vault: Path) -> Path:
    return vault / StudioService.APPROVAL_DIR


def _find_existing_digest_approval(
    vault: Path,
    action_digest: str,
    *,
    source_digest: str | None = None,
) -> dict[str, Any] | None:
    root = _approval_root(vault)
    if not root.exists():
        return None
    active_statuses = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_chat_action_digest") != action_digest:
            continue
        if str(payload.get("status") or "") not in active_statuses:
            continue
        approval_id = str(payload.get("approval_id") or path.stem)
        approval_artifact_path = _rel(vault, path)
        audit_path = vault / CHAT_HANDOFF_AUDIT_DIR / f"{action_digest}.json"
        audit_payload = _safe_json(audit_path) if audit_path.exists() else None
        metadata_source_digest = metadata.get("phase11_chat_source_digest")
        audit_approval_id_matches = bool(
            audit_payload
            and str(audit_payload.get("approval_id") or "") == approval_id
        )
        audit_artifact_path = str((audit_payload or {}).get("approval_artifact_path") or "")
        audit_artifact_path_matches = bool(
            audit_payload
            and (
                not audit_artifact_path
                or audit_artifact_path == approval_artifact_path
            )
        )
        audit_matches_digest = bool(
            audit_payload
            and audit_payload.get("action_digest") == action_digest
            and (source_digest is None or audit_payload.get("source_digest") == source_digest)
            and audit_approval_id_matches
            and audit_artifact_path_matches
        )
        source_digest_matches = bool(
            metadata_source_digest
            and (source_digest is None or metadata_source_digest == source_digest)
        )
        legacy_blockers: list[str] = []
        if not source_digest_matches:
            legacy_blockers.append("phase11_chat_source_digest_missing_or_mismatched")
        if not audit_matches_digest:
            legacy_blockers.append("chat_handoff_audit_missing_or_mismatched")
        return {
            "approval_id": approval_id,
            "status": payload.get("status") or "unknown",
            "path": approval_artifact_path,
            "target_path": spec.get("target_path"),
            "source_digest_recorded": metadata_source_digest,
            "source_digest_matches": source_digest_matches,
            "handoff_audit_path": f"{CHAT_HANDOFF_AUDIT_DIR}/{action_digest}.json",
            "handoff_audit_present": bool(audit_payload),
            "handoff_audit_matches": audit_matches_digest,
            "handoff_audit_approval_id_matches": audit_approval_id_matches,
            "handoff_audit_artifact_path_matches": audit_artifact_path_matches,
            "legacy_blockers": legacy_blockers,
            "valid_chat_handoff_duplicate": not legacy_blockers,
        }
    return None


def _action_digest_material(
    *,
    message: str,
    handoff_contract: dict[str, Any],
    conversation_contract: dict[str, Any],
) -> dict[str, Any]:
    action_preview = handoff_contract.get("future_action_spec_preview") or {}
    conversation_preview = conversation_contract.get("conversation_log_preview") or {}
    conversation_descriptor = conversation_contract.get("conversation_descriptor") or {}
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "source_contract": handoff_contract.get("model_version"),
        "conversation_contract": conversation_contract.get("model_version"),
        "message_sha256": _sha256_text(message),
        "intent_class": (handoff_contract.get("summary") or {}).get("intent_class"),
        "action_type": action_preview.get("action_type"),
        "target_path": action_preview.get("target_path"),
        "content_sha256": action_preview.get("content_sha256"),
        "conversation_target_path_preview": conversation_descriptor.get("target_path_preview"),
        "conversation_content_sha256": conversation_preview.get("content_sha256"),
        "submitted_by": action_preview.get("submitted_by"),
    }


def _source_digest_material(
    *,
    raw_message: str,
    normalized_message: str,
    explicit_intent: str | None,
    handoff_contract: dict[str, Any],
    action_preview: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_surface": "phase11_chat_panel",
        "source_contract": handoff_contract.get("model_version"),
        "source_message_sha256": _sha256_text(raw_message),
        "normalized_message_sha256": _sha256_text(normalized_message),
        "explicit_intent": explicit_intent,
        "resolved_intent_class": (handoff_contract.get("summary") or {}).get("intent_class"),
        "proposal_action_type": action_preview.get("action_type"),
        "proposal_target_path": action_preview.get("target_path"),
        "proposal_content_sha256": action_preview.get("content_sha256"),
    }


def _write_chat_handoff_audit_record(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    action_digest: str,
    source_digest: str,
    source_digest_material: dict[str, Any],
    digest_material: dict[str, Any],
    target_path: str,
    operator_id: str,
) -> str:
    audit_root = vault / CHAT_HANDOFF_AUDIT_DIR
    audit_root.mkdir(parents=True, exist_ok=True)
    audit_path = audit_root / f"{action_digest}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "action_digest": action_digest,
        "source_digest": source_digest,
        "source_digest_material_sha256": _sha256_text(_canonical_json(source_digest_material)),
        "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        "target_path": target_path or None,
        "operator_id": operator_id or "operator",
        "chat_originated_handoff": True,
        "target_file_written": False,
        "approval_execution_allowed": False,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_allowed": False,
    }
    audit_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return f"{CHAT_HANDOFF_AUDIT_DIR}/{audit_path.name}"


def _approval_spec(
    *,
    message: str,
    action_preview: dict[str, Any],
    action_digest: str,
    source_digest: str,
    source_digest_material: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    metadata = dict(action_preview.get("metadata") or {})
    metadata.update(
        {
            "pass": PASS_ID,
            "phase": "Phase 11",
            "source_surface": "phase11_chat_panel",
            "source_contract": SURFACE_ID,
            "phase11_chat_queue_write_proof": True,
            DEFERRED_EXECUTION_METADATA_KEY: True,
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": "future_phase11_approval_consumption_pass",
            "target_vault_write_performed": False,
            "conversation_log_write_performed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_write_performed": False,
            "phase11_chat_action_digest": action_digest,
            "phase11_chat_source_digest": source_digest,
            "phase11_chat_source_digest_material_sha256": _sha256_text(_canonical_json(source_digest_material)),
            "phase11_chat_digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
            "source_message_sha256": _sha256_text(message),
            "operator_confirmation": operator_id,
        }
    )
    return ActionSpec(
        action_type=str(action_preview.get("action_type") or "create_file"),
        target_path=str(action_preview.get("target_path") or ""),
        content=str(action_preview.get("content_preview") or ""),
        metadata=metadata,
        submitted_by="studio-chat",
        note=f"Phase 11 Chat approval queue write proof queued by {operator_id}; execution deferred.",
    )


def build_phase11_chat_approval_queue_write_execution_proof(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    expected_action_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Preview or write one Chat-originated approval queue request."""

    vault = Path(vault_root).resolve()
    raw_message = str(message or "")
    normalized_message = _norm(message)
    handoff = build_phase11_chat_approval_handoff_queue_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    conversation = build_phase11_chat_conversation_persistence_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    action_preview = handoff.get("future_action_spec_preview") or {}
    digest_material = _action_digest_material(
        message=normalized_message,
        handoff_contract=handoff,
        conversation_contract=conversation,
    )
    action_digest = _sha256_text(_canonical_json(digest_material))
    source_digest_material = _source_digest_material(
        raw_message=raw_message,
        normalized_message=normalized_message,
        explicit_intent=explicit_intent,
        handoff_contract=handoff,
        action_preview=action_preview,
    )
    source_digest = _sha256_text(_canonical_json(source_digest_material))
    target_path = str(action_preview.get("target_path") or "")
    target_abs = (vault / target_path).resolve() if target_path else vault
    approval_root = _approval_root(vault)

    blockers: list[str] = []
    warnings: list[str] = []
    if not normalized_message:
        blockers.append("message_required_for_chat_approval_queue_write")
    if not action_preview:
        blockers.append("queueable_chat_action_spec_preview_missing")
    if "prompt_injection_indicator_present" in (handoff.get("blocked_reasons") or []):
        blockers.append("prompt_injection_indicator_present")
    if target_path and not target_path.endswith(".md"):
        blockers.append("target_path_must_be_markdown")
    if target_path and target_abs.exists():
        blockers.append("future_target_path_collision")
    if write_approval and not expected_action_digest:
        blockers.append("expected_action_digest_required_for_queue_write")
    if write_approval and expected_action_digest and expected_action_digest != action_digest:
        blockers.append("expected_action_digest_mismatch")

    duplicate = (
        _find_existing_digest_approval(vault, action_digest, source_digest=source_digest)
        if write_approval
        else None
    )
    if duplicate:
        warnings.append("duplicate_active_chat_approval_queue_request_present")
        if not duplicate.get("valid_chat_handoff_duplicate"):
            blockers.append("legacy_duplicate_missing_source_digest_or_audit")

    validation_payload: dict[str, Any] | None = None
    spec: ActionSpec | None = None
    if action_preview and not any(
        item in blockers
        for item in {
            "target_path_must_be_markdown",
            "queueable_chat_action_spec_preview_missing",
        }
    ):
        spec = _approval_spec(
            message=normalized_message,
            action_preview=action_preview,
            action_digest=action_digest,
            source_digest=source_digest,
            source_digest_material=source_digest_material,
            digest_material=digest_material,
            operator_id=operator_id or "operator",
        )
        validation = StudioService(vault).validate_action(spec)
        validation_payload = {
            "valid": validation.valid,
            "gate_blocked": validation.gate_blocked,
            "approval_required": True,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        }
        if validation.gate_blocked:
            blockers.append("studio_service_validation_gate_blocked")

    created = False
    approval_id: str | None = None
    approval_path: str | None = None
    audit_record_path: str | None = None
    queue_writer_called = False
    status = STATUS_PREVIEW

    hard_blockers = list(dict.fromkeys(blockers))
    if write_approval and not hard_blockers and duplicate:
        approval_id = str(duplicate.get("approval_id") or "")
        approval_path = str(duplicate.get("path") or "")
        status = "COMPLETE / DUPLICATE-BLOCKED / EXISTING APPROVAL RETURNED / EXECUTION BLOCKED"
    elif write_approval and not hard_blockers and spec is not None:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_record_path = _write_chat_handoff_audit_record(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            action_digest=action_digest,
            source_digest=source_digest,
            source_digest_material=source_digest_material,
            digest_material=digest_material,
            target_path=target_path,
            operator_id=operator_id or "operator",
        )
        status = STATUS_WRITTEN

    target_exists_after = bool(target_path and target_abs.exists())
    approval_count = len(list(approval_root.glob("*.json"))) if approval_root.exists() else 0

    return {
        "ok": not any(item in hard_blockers for item in {
            "message_required_for_chat_approval_queue_write",
            "queueable_chat_action_spec_preview_missing",
            "prompt_injection_indicator_present",
            "target_path_must_be_markdown",
            "future_target_path_collision",
            "expected_action_digest_required_for_queue_write",
            "expected_action_digest_mismatch",
            "studio_service_validation_gate_blocked",
            "legacy_duplicate_missing_source_digest_or_audit",
        }),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not bool(write_approval and created),
        "approval_gated": True,
        "summary": {
            "message_present": bool(normalized_message),
            "intent_class": (handoff.get("summary") or {}).get("intent_class"),
            "queue_write_preview_ready": bool(action_preview) and not any(
                item in hard_blockers
                for item in {
                    "prompt_injection_indicator_present",
                    "target_path_must_be_markdown",
                    "future_target_path_collision",
                    "studio_service_validation_gate_blocked",
                }
            ),
            "write_approval_requested": bool(write_approval),
            "approval_request_created": created,
            "duplicate_active_request_present": bool(duplicate),
            "duplicate_returned_existing_request": bool(write_approval and duplicate and not created and not hard_blockers),
            "approval_id": approval_id,
            "approval_artifact_path": approval_path,
            "target_path_preview": target_path or None,
            "target_path_exists_after": target_exists_after,
            "approval_execution_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(hard_blockers),
        },
        "digest_proof": {
            "action_digest": action_digest,
            "expected_action_digest": expected_action_digest,
            "expected_digest_matched": bool(expected_action_digest and expected_action_digest == action_digest),
            "digest_required_for_write": True,
            "digest_material": digest_material,
        },
        "source_proof": {
            "source_digest": source_digest,
            "source_digest_material": source_digest_material,
            "source_digest_material_sha256": _sha256_text(_canonical_json(source_digest_material)),
            "exact_source_digest_recorded": True,
        },
        "audit_record": {
            "audit_record_written": bool(audit_record_path),
            "audit_record_path": audit_record_path,
            "audit_record_required_for_successful_handoff": True,
        },
        "queue_write": {
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "future_status_if_written": "pending",
            "approval_status_now": "pending" if created else (duplicate or {}).get("status"),
            "approval_artifact_path": approval_path,
            "approval_artifact_count": approval_count,
            "duplicate": duplicate,
        },
        "target_write_proof": {
            "target_path": target_path or None,
            "target_file_exists_after": target_exists_after,
            "target_file_written": False,
            "conversation_log_written": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_written": False,
        },
        "approval_center_visibility": {
            "source_group": "studio-service",
            "visible_after_write": bool(created or duplicate),
            "approval_center_reads_runtime_studio_approvals": True,
        },
        "service_validation": validation_payload,
        "source_contracts": {
            "approval_handoff_queue_contract": handoff,
            "conversation_persistence_contract": conversation,
        },
        "authority": {
            "approval_gated": True,
            "approval_queue_write_allowed_with_digest": True,
            "approval_queue_write_performed": created,
            "approval_grant_or_reject_allowed": False,
            "approval_execution_allowed": False,
            "target_vault_write_allowed": False,
            "conversation_persistence_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "workflow_execution_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_grant_or_reject",
            "approval_execution",
            "target_vault_file_write",
            "conversation_log_write",
            "provider_api_call",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "gate_mutation",
            "git_mutation",
            "workflow_execution",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": hard_blockers,
        "warnings": warnings,
    }


def format_phase11_chat_approval_queue_write_execution_proof(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    source = payload.get("source_proof") or {}
    audit = payload.get("audit_record") or {}
    queue = payload.get("queue_write") or {}
    target = payload.get("target_write_proof") or {}
    return "\n".join(
        [
            "Phase 11 Chat Approval Queue Write Execution Proof",
            f"  status: {payload.get('status')}",
            f"  intent: {summary.get('intent_class')}",
            f"  action_digest: {digest.get('action_digest')}",
            f"  source_digest: {source.get('source_digest')}",
            f"  write_approval_requested: {summary.get('write_approval_requested')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  approval_id: {summary.get('approval_id') or 'none'}",
            f"  approval_artifact_path: {queue.get('approval_artifact_path') or 'none'}",
            f"  audit_record_path: {audit.get('audit_record_path') or 'none'}",
            f"  target_path: {target.get('target_path') or 'none'}",
            f"  target_file_written: {target.get('target_file_written')}",
            f"  approval_execution_allowed: {summary.get('approval_execution_allowed')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: approval queue artifact write only after exact digest confirmation; no approval execution, target vault write, conversation write, provider call, runtime dispatch, Agent Bus task write, or canonical mutation.",
        ]
    )
