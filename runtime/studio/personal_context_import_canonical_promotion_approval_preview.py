"""Canonical-promotion approval preview for personal context import.

This surface prepares a digest-bound approval packet for a future canonical
promotion executor. It does not write canonical nodes or indexes. The approval
artifact records exact target paths and blocked effects so the next executor can
be reviewed before touching Dashboard, Personal Operator, project, knowledge, or
OS files.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.personal_context_import_runtime_consumption_readiness import (
    build_personal_context_import_runtime_consumption_readiness,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.personal_context_import_canonical_promotion_approval_preview.v1"
SURFACE_ID = "studio_personal_context_import_canonical_promotion_approval_preview"
PASS_ID = "personal-context-import-canonical-promotion-approval-preview"
STATUS_PREVIEW = "READY / CANONICAL PROMOTION APPROVAL PREVIEW / CANONICAL WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / CANONICAL PROMOTION APPROVAL QUEUED / CANONICAL WRITES BLOCKED"
BLOCKED_STATUS = "BLOCKED / CANONICAL PROMOTION APPROVAL PREVIEW"
NEXT_RECOMMENDED_PASS = "personal-context-import-personal-map-apply-readiness"
APPROVAL_CLASS = "personal_context_import_canonical_promotion_future"
PREVIEW_ROOT = "runtime/studio/context-import/canonical-promotion-previews"
AUDIT_ROOT = "runtime/studio/approvals/personal-context-import/canonical-promotion"

CANONICAL_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "target_id": "dashboard",
        "path": "00_HOME/Dashboard.md",
        "target_class": "home_navigation_index",
        "protected": False,
        "future_operation": "append_or_update_personal_context_routes",
    },
    {
        "target_id": "personal_operator_index",
        "path": "00_HOME/Personal-Operator-Index.md",
        "target_class": "personal_context_hub",
        "protected": False,
        "future_operation": "append_or_update_personal_context_routes",
    },
    {
        "target_id": "operating_system",
        "path": "00_HOME/Operating-System.md",
        "target_class": "protected_os_domain_map",
        "protected": True,
        "future_operation": "minimal_operator_reviewed_domain_route_patch",
    },
    {
        "target_id": "projects_hub",
        "path": "01_PROJECTS/Projects-Hub.md",
        "target_class": "project_navigation_index",
        "protected": False,
        "future_operation": "append_or_update_project_context_routes",
    },
    {
        "target_id": "knowledge_index_master",
        "path": "02_KNOWLEDGE/Knowledge-Index.md",
        "target_class": "canonical_knowledge_taxonomy",
        "protected": False,
        "future_operation": "append_or_update_domain_knowledge_routes",
    },
    {
        "target_id": "personal_domains_index",
        "path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "target_class": "personal_domain_navigation_index",
        "protected": False,
        "future_operation": "append_or_update_life_domain_routes",
    },
    {
        "target_id": "personal_context_intake_index",
        "path": "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md",
        "target_class": "raw_to_review_intake_index",
        "protected": False,
        "future_operation": "append_or_update_review_artifact_routes",
    },
)


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


def _target_plan(vault: Path, runtime_packet: dict[str, Any]) -> list[dict[str, Any]]:
    refs = (runtime_packet.get("runtime_reference_packet_preview") or {}).get("context_refs") or []
    group_ids = sorted({str(item.get("group_id") or "") for item in refs if item.get("group_id")})
    return [
        {
            **target,
            "exists": (vault / str(target["path"])).exists(),
            "content_included": False,
            "future_write_requires_operator_approval": True,
            "future_write_requires_exact_digest": True,
            "runtime_refs_available_for_target": len(refs),
            "reference_group_ids": group_ids,
            "write_performed_now": False,
        }
        for target in CANONICAL_TARGETS
    ]


def _build_packet(vault: Path, *, operator_id: str) -> dict[str, Any]:
    generated_at = _now_utc()
    runtime_packet = build_personal_context_import_runtime_consumption_readiness(vault)
    targets = _target_plan(vault, runtime_packet)
    digest_basis = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "runtime_reference_packet_digest": (runtime_packet.get("digest_proof") or {}).get(
            "runtime_reference_packet_digest"
        ),
        "target_paths": [item["path"] for item in targets],
    }
    digest = _sha256_text(_canonical_json(digest_basis))
    preview_id = f"personal-context-canonical-promotion-{digest[:16]}"
    return {
        "preview_id": preview_id,
        "schema_version": MODEL_VERSION,
        "status": "pending_canonical_promotion_approval_preview",
        "generated_at_utc": generated_at,
        "runtime_reference_packet_ready": bool(
            (runtime_packet.get("summary") or {}).get("runtime_reference_packet_ready")
        ),
        "runtime_reference_packet_digest": (runtime_packet.get("digest_proof") or {}).get(
            "runtime_reference_packet_digest"
        ),
        "runtime_reference_packet_refs_only": True,
        "source_text_included": False,
        "raw_full_memory_injection_allowed": False,
        "canonical_target_plan": targets,
        "canonical_target_count": len(targets),
        "protected_target_count": sum(1 for item in targets if item.get("protected")),
        "canonical_promotion_digest": digest,
        "digest_basis_sha256": _sha256_text(_canonical_json(digest_basis)),
        "target_path": f"{PREVIEW_ROOT}/{preview_id}.json",
        "future_executor_required": True,
        "canonical_writes_performed": False,
        "personal_map_apply_performed": False,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
    }


def _find_existing(vault: Path, digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active_statuses = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("personal_context_import_canonical_promotion_digest") != digest:
            continue
        if str(payload.get("status") or "") not in active_statuses:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
            "target_path": spec.get("target_path"),
        }
    return None


def _approval_spec(*, packet: dict[str, Any], operator_id: str) -> ActionSpec:
    content_packet = {
        "record_type": "personal_context_import_canonical_promotion_preview_packet",
        "schema_version": MODEL_VERSION,
        "canonical_promotion_packet": packet,
        "source_text_included": False,
        "raw_full_memory_injection_allowed": False,
        "future_executor_requires_matching_digest": True,
    }
    content = json.dumps(content_packet, indent=2, sort_keys=True) + "\n"
    return ActionSpec(
        action_type="create_file",
        target_path=str(packet.get("target_path") or ""),
        content=content,
        metadata={
            "pass": PASS_ID,
            "source_surface": SURFACE_ID,
            "personal_context_import_canonical_promotion_approval_preview": True,
            "personal_context_import_canonical_promotion_execution_blocked": True,
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "required_approval_class": APPROVAL_CLASS,
            "personal_context_import_canonical_promotion_digest": packet.get("canonical_promotion_digest"),
            "runtime_reference_packet_digest": packet.get("runtime_reference_packet_digest"),
            "canonical_target_count": packet.get("canonical_target_count"),
            "protected_target_count": packet.get("protected_target_count"),
            "source_text_included": False,
            "raw_full_memory_injection_allowed": False,
            "canonical_writes_performed": False,
            "personal_map_apply_performed": False,
            "runtime_memory_mutation_performed": False,
            "agent_bus_task_written": False,
            "provider_call_performed": False,
            "credential_read_performed": False,
        },
        submitted_by=operator_id or "studio-operator",
        note="Personal context canonical-promotion approval preview; canonical effects deferred.",
    )


def _write_audit_record(*, vault: Path, approval_id: str, approval_path: str, packet: dict[str, Any], operator_id: str) -> str:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    digest = str(packet.get("canonical_promotion_digest") or "missing")
    path = root / f"{digest[:16]}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "preview_id": packet.get("preview_id"),
        "canonical_promotion_digest": digest,
        "runtime_reference_packet_digest": packet.get("runtime_reference_packet_digest"),
        "canonical_target_count": packet.get("canonical_target_count"),
        "protected_target_count": packet.get("protected_target_count"),
        "operator_id": operator_id or "studio-operator",
        "source_text_included": False,
        "canonical_writes_performed": False,
        "personal_map_apply_performed": False,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _rel(vault, path)


def build_personal_context_import_canonical_promotion_approval_preview(
    vault_root: str | Path,
    *,
    expected_canonical_promotion_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Preview or queue a future canonical-promotion approval request."""

    vault = Path(vault_root).resolve()
    packet = _build_packet(vault, operator_id=operator_id)
    digest = str(packet.get("canonical_promotion_digest") or "")
    expected = str(expected_canonical_promotion_digest or "").strip()
    runtime_ready = bool(packet.get("runtime_reference_packet_ready"))
    blockers: list[str] = []
    warnings: list[str] = []
    if not runtime_ready:
        blockers.append("runtime_reference_packet_not_ready")
    if write_approval and not expected:
        blockers.append("expected_canonical_promotion_digest_required")
    elif write_approval and expected != digest:
        blockers.append("expected_canonical_promotion_digest_mismatch")
    duplicate = _find_existing(vault, digest) if digest else None
    if write_approval and duplicate:
        blockers.append("approval_queue_request_already_exists_for_digest")

    action_spec = _approval_spec(packet=packet, operator_id=operator_id)
    validation = StudioService(vault).validate_action(action_spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")
        warnings.extend(str(item) for item in validation.errors)
    warnings.extend(str(item) for item in validation.warnings)

    created = False
    queue_writer_called = False
    approval_id: str | None = None
    approval_path: str | None = None
    audit_path: str | None = None
    blocked_unique = list(dict.fromkeys(blockers))
    status = STATUS_PREVIEW if not blocked_unique else BLOCKED_STATUS

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
            packet=packet,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    return {
        "ok": not blocked_unique,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "summary": {
            "canonical_promotion_approval_preview_ready": not blocked_unique,
            "canonical_promotion_approval_request_created": created,
            "canonical_target_count": packet.get("canonical_target_count"),
            "protected_target_count": packet.get("protected_target_count"),
            "runtime_reference_packet_ready": runtime_ready,
            "source_text_included": False,
            "raw_full_memory_injection_allowed": False,
            "canonical_writes_performed": False,
            "personal_map_apply_performed": False,
            "runtime_memory_mutation_performed": False,
            "agent_bus_task_written": False,
            "provider_call_performed": False,
            "credential_read_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "canonical_promotion_packet_preview": packet,
        "approval_queue_write": {
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "approval_status_now": "pending" if created else None,
            "approval_artifact_path": approval_path,
            "duplicate": duplicate,
        },
        "approval_record": {
            "approval_id": approval_id,
            "approval_path": approval_path,
            "audit_path": audit_path,
        },
        "readiness": {
            "personal_context_import_canonical_promotion_approval_preview_ready": not blocked_unique,
            "personal_context_import_canonical_promotion_approval_queue_write_ready": True,
            "personal_context_import_canonical_promotion_exact_digest_required": True,
            "personal_context_import_canonical_promotion_executor_built": True,
            "personal_context_import_canonical_writes_blocked": True,
            "personal_context_import_personal_map_apply_blocked": True,
            "personal_context_import_runtime_memory_mutation_blocked": True,
            "personal_context_import_agent_bus_dispatch_blocked": True,
            "personal_context_import_provider_calls_blocked": True,
            "personal_context_import_credential_reads_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "authority": {
            "approval_queue_write_allowed_with_digest": True,
            "approval_queue_write_performed": created,
            "approval_execution_allowed": False,
            "canonical_writes_allowed": False,
            "personal_map_apply_allowed": False,
            "runtime_memory_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "provider_calls_allowed": False,
            "credential_reads_allowed": False,
            "source_text_included": False,
            "canonical_mutation_allowed": False,
        },
        "digest_proof": {
            "canonical_promotion_digest": digest,
            "expected_digest_matched": bool(expected and expected == digest),
        },
        "denied_by_this_surface": [
            "canonical_markdown_node_write",
            "dashboard_index_write",
            "personal_operator_index_write",
            "operating_system_write",
            "projects_hub_write",
            "knowledge_index_write",
            "personal_map_apply",
            "runtime_memory_mutation",
            "agent_bus_task_write",
            "provider_api_call",
            "credential_read",
            "secret_read",
            "raw_full_memory_injection",
        ],
        "blocked_reasons": blocked_unique,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_personal_context_import_canonical_promotion_approval_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "Personal Context Import Canonical Promotion Approval Preview",
        f"Status: {payload.get('status')}",
        f"Approval request created: {summary.get('canonical_promotion_approval_request_created')}",
        f"Canonical targets: {summary.get('canonical_target_count')}",
        f"Protected targets: {summary.get('protected_target_count')}",
        f"Canonical writes performed: {summary.get('canonical_writes_performed')}",
        f"Personal Map apply performed: {summary.get('personal_map_apply_performed')}",
        f"Runtime memory mutation performed: {summary.get('runtime_memory_mutation_performed')}",
        f"Agent Bus task written: {summary.get('agent_bus_task_written')}",
        f"Provider call performed: {summary.get('provider_call_performed')}",
        f"Credential read performed: {summary.get('credential_read_performed')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers[:10])
    return "\n".join(lines)
