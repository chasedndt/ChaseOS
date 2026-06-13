"""Phase 11 companion memory approval preview and queue-write proof.

This surface turns a validated companion-memory candidate into a deterministic
approval preview. With an exact expected digest and explicit write flag, it may
write one pending Studio approval artifact. It never creates companion memory
folders, writes memory ledgers, consumes approvals, calls providers, dispatches
runtimes, or mutates canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.memory import (
    MEMORY_POLICY_VERSION,
    companion_memory_namespace,
    validate_companion_memory_candidate,
)
from runtime.studio.phase11_companion_memory_boundary_contract import (
    build_phase11_companion_memory_boundary_contract,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_companion_memory_approval_preview.v1"
SURFACE_ID = "phase11_companion_memory_approval_preview"
PASS_ID = "phase11-companion-memory-approval-preview"
STATUS_PREVIEW = "READY / APPROVAL-PREVIEW / MEMORY WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / MEMORY WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-approved-execution-proof"
APPROVAL_CLASS = "studio_companion_memory_write_future"
AUDIT_DIR = "07_LOGS/Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _normalize_candidate(
    candidate: dict[str, Any] | None = None,
    *,
    companion_id: str | None = None,
    memory_class: str | None = None,
    content: str | None = None,
    source_surface: str | None = None,
    source_event_id: str | None = None,
) -> dict[str, Any]:
    source = dict(candidate or {})
    if companion_id is not None:
        source["companion_id"] = companion_id
    if memory_class is not None:
        source["memory_class"] = memory_class
    if content is not None:
        source["content"] = content
    if source_surface is not None:
        source["source_surface"] = source_surface
    if source_event_id is not None:
        source["source_event_id"] = source_event_id
    return {
        "companion_id": " ".join(str(source.get("companion_id") or "").strip().split()).lower(),
        "memory_class": " ".join(str(source.get("memory_class") or "").strip().split()).lower(),
        "content": str(source.get("content") or "").strip(),
        "source_surface": " ".join(str(source.get("source_surface") or "phase11-chat").strip().split()),
        "source_event_id": " ".join(str(source.get("source_event_id") or "").strip().split()),
        "target_path": str(source.get("target_path") or "").strip(),
        "protected_file_path": source.get("protected_file_path"),
        "canonical_target_path": source.get("canonical_target_path"),
        "canonical_mutation": source.get("canonical_mutation"),
        "permission_change": source.get("permission_change"),
        "runtime_permission": source.get("runtime_permission"),
        "provider_config": source.get("provider_config"),
        "connector_config": source.get("connector_config"),
        "agent_bus_task": source.get("agent_bus_task"),
    }


def _approval_root(vault: Path) -> Path:
    return vault / StudioService.APPROVAL_DIR


def _existing_digest_approval(vault: Path, memory_approval_digest: str) -> dict[str, Any] | None:
    root = _approval_root(vault)
    if not root.exists():
        return None
    active = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_companion_memory_approval_digest") != memory_approval_digest:
            continue
        if str(payload.get("status") or "") not in active:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
            "target_path": spec.get("target_path"),
        }
    return None


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / "07_LOGS" / "Companion-Memory"
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def _digest_material(
    *,
    boundary: dict[str, Any],
    validation: dict[str, Any],
    candidate: dict[str, Any],
    target_path: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "memory_policy_version": MEMORY_POLICY_VERSION,
        "boundary_digest": ((boundary.get("digest_proof") or {}).get("memory_boundary_contract_digest")),
        "candidate_validation_digest": validation.get("candidate_digest"),
        "companion_id": candidate.get("companion_id"),
        "memory_class": candidate.get("memory_class"),
        "content_sha256": _sha256_text(str(candidate.get("content") or "")),
        "source_surface": candidate.get("source_surface"),
        "source_event_id": candidate.get("source_event_id"),
        "target_path": target_path,
        "required_approval_class": APPROVAL_CLASS,
    }


def _build_record_preview(candidate: dict[str, Any], memory_approval_digest: str, target_path: str) -> dict[str, Any]:
    content = str(candidate.get("content") or "")
    return {
        "memory_id": f"companion-memory-{memory_approval_digest[:16]}",
        "companion_id": candidate.get("companion_id"),
        "memory_class": candidate.get("memory_class"),
        "content_preview": content[:280],
        "content_sha256": _sha256_text(content),
        "source_surface": candidate.get("source_surface"),
        "source_event_id": candidate.get("source_event_id") or None,
        "target_path": target_path,
        "trust_state": "raw",
        "authoritative": False,
        "canonical": False,
        "created_by_executor": False,
        "memory_file_written": False,
    }


def _build_action_spec(
    *,
    candidate: dict[str, Any],
    target_path: str,
    memory_approval_digest: str,
    digest_material: dict[str, Any],
    record_preview: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    content = json.dumps(record_preview, indent=2, sort_keys=True) + "\n"
    return ActionSpec(
        action_type="companion_memory_write",
        target_path=target_path,
        content=content,
        metadata={
            "pass": PASS_ID,
            "phase": "Phase 11",
            "source_surface": SURFACE_ID,
            "source_policy_version": MEMORY_POLICY_VERSION,
            "required_approval_class": APPROVAL_CLASS,
            "phase11_companion_memory_approval_preview": True,
            "phase11_companion_memory_approval_digest": memory_approval_digest,
            "phase11_companion_memory_digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
            "companion_id": candidate.get("companion_id"),
            "memory_class": candidate.get("memory_class"),
            "source_event_id": candidate.get("source_event_id") or None,
            "operator_confirmation": operator_id or "operator",
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "companion_memory_file_written": False,
            "memory_write_executed": False,
            "approval_consumed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_write_performed": False,
            "canonical_mutation_allowed": False,
        },
        submitted_by="studio-chat",
        note="Phase 11 companion-memory approval request; memory write deferred.",
    )


def _write_audit_record(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    memory_approval_digest: str,
    digest_material: dict[str, Any],
    candidate: dict[str, Any],
    target_path: str,
    operator_id: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    audit_path = root / f"{PASS_ID}-{memory_approval_digest[:16]}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "memory_approval_digest": memory_approval_digest,
        "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        "companion_id": candidate.get("companion_id"),
        "memory_class": candidate.get("memory_class"),
        "target_path": target_path,
        "operator_id": operator_id or "operator",
        "approval_request_created": True,
        "approval_execution_allowed": False,
        "approval_consumed": False,
        "memory_file_written": False,
        "memory_write_executed": False,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_allowed": False,
    }
    audit_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _rel(vault, audit_path)


def build_phase11_companion_memory_approval_preview(
    vault_root: str | Path,
    *,
    candidate: dict[str, Any] | None = None,
    companion_id: str | None = None,
    memory_class: str | None = None,
    content: str | None = None,
    source_surface: str | None = None,
    source_event_id: str | None = None,
    expected_memory_approval_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Preview or write one digest-bound companion-memory approval artifact."""

    vault = Path(vault_root).resolve()
    normalized = _normalize_candidate(
        candidate,
        companion_id=companion_id,
        memory_class=memory_class,
        content=content,
        source_surface=source_surface,
        source_event_id=source_event_id,
    )
    before_memory = _memory_snapshot(vault)
    boundary = build_phase11_companion_memory_boundary_contract(vault)
    validation = validate_companion_memory_candidate(normalized, vault_root=vault)
    blockers: list[str] = []
    warnings: list[str] = list(validation.get("warnings") or [])

    target_path = ""
    namespace: dict[str, Any] = {}
    if normalized.get("companion_id"):
        try:
            namespace = companion_memory_namespace(vault, str(normalized.get("companion_id")))
            target_path = str(namespace.get("ledger_path") or "")
            normalized["target_path"] = target_path
        except ValueError:
            blockers.append("invalid_companion_id")

    if boundary.get("ok") is not True:
        blockers.append("companion_memory_boundary_contract_not_ready")
    if validation.get("candidate_valid") is not True:
        blockers.append("candidate_validation_failed")
    if not target_path:
        blockers.append("companion_memory_target_path_unavailable")

    digest_material = _digest_material(
        boundary=boundary,
        validation=validation,
        candidate=normalized,
        target_path=target_path,
    )
    memory_approval_digest = _sha256_text(_canonical_json(digest_material))
    record_preview = _build_record_preview(normalized, memory_approval_digest, target_path)
    approval_id_preview = f"companion-memory-appr-{memory_approval_digest[:16]}"
    approval_path_preview = f"{StudioService.APPROVAL_DIR}/{approval_id_preview}.json"
    expected = str(expected_memory_approval_digest or "").strip()

    if write_approval and not expected:
        blockers.append("expected_memory_approval_digest_required")
    elif write_approval and expected != memory_approval_digest:
        blockers.append("expected_memory_approval_digest_mismatch")

    duplicate = _existing_digest_approval(vault, memory_approval_digest) if write_approval else None
    if duplicate:
        blockers.append("approval_queue_request_already_exists_for_digest")

    action_spec = _build_action_spec(
        candidate=normalized,
        target_path=target_path,
        memory_approval_digest=memory_approval_digest,
        digest_material=digest_material,
        record_preview=record_preview,
        operator_id=operator_id,
    )
    validation_payload: dict[str, Any] | None = None
    service_validation = StudioService(vault).validate_action(action_spec) if target_path else None
    if service_validation is not None:
        validation_payload = {
            "valid": service_validation.valid,
            "gate_blocked": service_validation.gate_blocked,
            "approval_required": True,
            "errors": list(service_validation.errors),
            "warnings": list(service_validation.warnings),
        }
        if service_validation.gate_blocked:
            blockers.append("studio_service_validation_gate_blocked")

    blocked_unique = list(dict.fromkeys(blockers))
    created = False
    queue_writer_called = False
    approval_id: str | None = None
    approval_path: str | None = None
    audit_path: str | None = None
    status = STATUS_PREVIEW if not blocked_unique else "BLOCKED / APPROVAL-PREVIEW / NO APPROVAL ARTIFACT WRITE"

    if write_approval and not blocked_unique:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(action_spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_path = _write_audit_record(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            memory_approval_digest=memory_approval_digest,
            digest_material=digest_material,
            candidate=normalized,
            target_path=target_path,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    after_memory = _memory_snapshot(vault)
    approval_preview_ready = not blocked_unique or (
        blocked_unique == ["expected_memory_approval_digest_required"]
        and bool(write_approval)
    )
    ok = not blocked_unique
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not created,
        "approval_gated": True,
        "summary": {
            "companion_id": normalized.get("companion_id"),
            "memory_class": normalized.get("memory_class"),
            "content_present": bool(normalized.get("content")),
            "approval_preview_ready": bool(approval_preview_ready and validation.get("candidate_valid") is True and boundary.get("ok") is True),
            "write_approval_requested": bool(write_approval),
            "expected_memory_approval_digest_provided": bool(expected),
            "expected_memory_approval_digest_matched": expected == memory_approval_digest if expected else None,
            "approval_request_created": created,
            "approval_queue_writer_called": queue_writer_called,
            "approval_status": "pending" if created else None,
            "duplicate_active_request_present": bool(duplicate),
            "memory_file_written": False,
            "memory_write_executed": False,
            "memory_root_created": False,
            "approval_consumed": False,
            "approval_execution_called": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(blocked_unique),
        },
        "candidate": {
            "companion_id": normalized.get("companion_id"),
            "memory_class": normalized.get("memory_class"),
            "source_surface": normalized.get("source_surface"),
            "source_event_id": normalized.get("source_event_id") or None,
            "content_sha256": _sha256_text(str(normalized.get("content") or "")),
            "content_chars": len(str(normalized.get("content") or "")),
        },
        "candidate_validation": validation,
        "boundary_contract": boundary,
        "namespace_preview": namespace,
        "record_preview": record_preview,
        "digest_proof": {
            "memory_approval_digest": memory_approval_digest,
            "expected_memory_approval_digest": expected or None,
            "expected_digest_matched": expected == memory_approval_digest if expected else None,
            "digest_required_for_write": True,
            "digest_material": digest_material,
            "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        },
        "future_approval_packet_preview": {
            "approval_request_created": created,
            "approval_queue_writer_called": queue_writer_called,
            "approval_id_preview": approval_id_preview,
            "approval_queue_path_preview": approval_path_preview,
            "required_approval_class": APPROVAL_CLASS,
            "future_status_if_written": "pending",
            "expected_memory_approval_digest_required": True,
            "memory_approval_digest": memory_approval_digest,
            "action_spec_preview": {
                "action_type": action_spec.action_type,
                "target_path": action_spec.target_path,
                "submitted_by": action_spec.submitted_by,
                "content_sha256": _sha256_text(action_spec.content or ""),
                "metadata": dict(action_spec.metadata),
            },
        },
        "approval_record": {
            "approval_id": approval_id,
            "approval_path": approval_path,
            "approval_status": "pending" if created else None,
            "duplicate": duplicate,
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
        },
        "memory_snapshot_proof": {
            "root_path": "07_LOGS/Companion-Memory",
            "files_before": before_memory,
            "files_after": after_memory,
            "unchanged": before_memory == after_memory,
            "memory_root_created_by_this_surface": False,
        },
        "service_validation": validation_payload,
        "approval_center_visibility": {
            "source_group": "studio-service",
            "visible_after_write": created,
            "approval_center_reads_runtime_studio_approvals": True,
        },
        "authority": {
            "approval_gated": True,
            "approval_preview_allowed": True,
            "approval_queue_write_allowed_with_digest": True,
            "approval_queue_write_performed": created,
            "approval_grant_or_reject_allowed": False,
            "approval_consumption_allowed": False,
            "approval_execution_allowed": False,
            "memory_write_allowed": False,
            "memory_write_performed": False,
            "memory_root_create_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "workflow_execution_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_grant_or_reject",
            "approval_consumption",
            "approval_execution",
            "companion_memory_file_write",
            "companion_memory_directory_create",
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
        "readiness": {
            "companion_memory_approval_preview_ready": bool(
                not blocked_unique and validation.get("candidate_valid") is True and boundary.get("ok") is True
            ),
            "companion_memory_approval_queue_write_gated": True,
            "companion_memory_approval_digest_required": True,
            "companion_memory_candidate_validation_ready": True,
            "companion_memory_writes_blocked": True,
            "companion_memory_approved_execution_required": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "blocked_reasons": blocked_unique,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_companion_memory_approval_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    approval = payload.get("approval_record") or {}
    preview = payload.get("future_approval_packet_preview") or {}
    lines = [
        "Phase 11 Companion Memory Approval Preview",
        f"Status: {payload.get('status')}",
        f"Companion: {summary.get('companion_id') or 'missing'}",
        f"Memory class: {summary.get('memory_class') or 'missing'}",
        f"Preview ready: {summary.get('approval_preview_ready')}",
        f"Write approval requested: {summary.get('write_approval_requested')}",
        f"Approval request created: {summary.get('approval_request_created')}",
        f"Approval id: {approval.get('approval_id') or preview.get('approval_id_preview') or 'none'}",
        f"Memory approval digest: {digest.get('memory_approval_digest') or 'missing'}",
        f"Memory write performed: {summary.get('memory_file_written')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
