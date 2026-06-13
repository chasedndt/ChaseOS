"""Phase 11 Chat companion selection queue-write readiness contract.

This surface previews the future approval-queue write for a companion-selection
change. It validates the approval-preview digest and builds stable queue packet
metadata only; it does not write approval artifacts, selection state, runtime
identity/profile/role-card files, dispatch runtimes, or call providers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_companion_selection_preview import (
    APPROVAL_CLASS,
    MODEL_VERSION as PREVIEW_MODEL_VERSION,
    SELECTION_TARGET_PATH,
    SURFACE_ID as PREVIEW_SURFACE_ID,
    build_phase11_chat_companion_selection_preview,
)
from runtime.studio.service import StudioService


MODEL_VERSION = "studio.phase11_chat_companion_selection_queue_write_readiness.v1"
SURFACE_ID = "phase11_chat_companion_selection_queue_write_readiness"
PASS_ID = "phase11-chat-companion-selection-queue-write-readiness"
STATUS = "COMPLETE / QUEUE-WRITE-READINESS / VERIFIED / QUEUE WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-companion-selection-queue-write-execution-proof"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split()).lower()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _queue_digest_material(*, selection_preview: dict[str, Any], requested_runtime: str, current_runtime: str) -> dict[str, Any]:
    preview_digest = selection_preview.get("digest_proof") or {}
    packet = selection_preview.get("future_approval_packet_preview") or {}
    action_spec = packet.get("action_spec_preview") or {}
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "source_surface": PREVIEW_SURFACE_ID,
        "source_model_version": PREVIEW_MODEL_VERSION,
        "requested_runtime_id": requested_runtime,
        "current_runtime_id": current_runtime,
        "selection_digest": preview_digest.get("selection_digest"),
        "target_path": action_spec.get("target_path") or SELECTION_TARGET_PATH,
        "action_type": action_spec.get("action_type") or "chat_companion_selection_change",
        "required_approval_class": packet.get("required_approval_class") or APPROVAL_CLASS,
        "content_sha256": action_spec.get("content_sha256"),
    }


def build_phase11_chat_companion_selection_queue_write_readiness(
    vault_root: str | Path,
    *,
    requested_runtime: str | None = None,
    current_runtime: str | None = None,
    message: str | None = None,
    expected_selection_digest: str | None = None,
) -> dict[str, Any]:
    """Build read-only readiness metadata for a future companion-selection queue write."""

    vault = Path(vault_root).resolve()
    requested = _norm(requested_runtime)
    current = _norm(current_runtime) or "openclaw"
    normalized_message = " ".join(str(message or "").strip().split())
    selection_preview = build_phase11_chat_companion_selection_preview(
        vault,
        requested_runtime=requested,
        current_runtime=current,
        message=normalized_message,
    )
    preview_summary = selection_preview.get("summary") or {}
    preview_digest = selection_preview.get("digest_proof") or {}
    selection_digest = str(preview_digest.get("selection_digest") or "")
    blockers = list(selection_preview.get("blocked_reasons") or [])

    expected = str(expected_selection_digest or "").strip()
    expected_matched = False
    if expected:
        expected_matched = expected == selection_digest
        if not expected_matched:
            blockers.append("expected_selection_digest_mismatch")

    queue_digest_material = _queue_digest_material(
        selection_preview=selection_preview,
        requested_runtime=requested,
        current_runtime=current,
    )
    queue_write_digest = _sha256_text(_canonical_json(queue_digest_material))
    ready = bool(selection_preview.get("ok") is True and not blockers)
    approval_id_preview = f"chat-companion-selection-queue-{queue_write_digest[:16]}"
    approval_queue_path_preview = f"{StudioService.APPROVAL_DIR}/{approval_id_preview}.json"

    preview_packet = selection_preview.get("future_approval_packet_preview") or {}
    action_spec_preview = dict(preview_packet.get("action_spec_preview") or {})
    metadata = dict(action_spec_preview.get("metadata") or {})
    metadata.update(
        {
            "pass": PASS_ID,
            "phase": "Phase 11",
            "source_surface": SURFACE_ID,
            "source_contract": PREVIEW_SURFACE_ID,
            "phase11_companion_selection_queue_write_readiness": True,
            "phase11_companion_selection_digest": selection_digest,
            "phase11_companion_selection_queue_write_digest": queue_write_digest,
            "approval_queue_write_only": True,
            "target_selection_write_performed": False,
            "runtime_control_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_write_performed": False,
        }
    )
    action_spec_preview.update(
        {
            "action_type": action_spec_preview.get("action_type") or "chat_companion_selection_change",
            "target_path": action_spec_preview.get("target_path") or SELECTION_TARGET_PATH,
            "metadata": metadata,
            "submitted_by": "studio-chat",
            "note": "Phase 11 Chat companion selection queue-write readiness preview; no approval artifact written.",
        }
    )

    blocked_unique = list(dict.fromkeys(blockers))
    return {
        "ok": ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ready else "BLOCKED / QUEUE-WRITE-READINESS / NO APPROVAL ARTIFACT WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": True,
        "summary": {
            "requested_runtime_id": requested,
            "current_runtime_id": current,
            "selection_change_requested": bool(preview_summary.get("selection_change_requested")),
            "queue_write_readiness_ready": ready,
            "expected_selection_digest_provided": bool(expected),
            "expected_selection_digest_matched": expected_matched if expected else None,
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "companion_selection_written": False,
            "companion_selection_write_allowed_now": False,
            "target_write_performed": False,
            "identity_ledger_mutated": False,
            "profile_writes_performed": False,
            "role_card_writes_performed": False,
            "runtime_control_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_written": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(blocked_unique),
        },
        "digest_proof": {
            "selection_digest": selection_digest,
            "queue_write_digest": queue_write_digest,
            "queue_digest_material": queue_digest_material,
            "queue_digest_material_sha256": _sha256_text(_canonical_json(queue_digest_material)),
            "digest_required_for_future_queue_write": True,
        },
        "future_queue_write_packet_preview": {
            "visible": True,
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "approval_id_preview": approval_id_preview,
            "approval_queue_path_preview": approval_queue_path_preview,
            "required_approval_class": APPROVAL_CLASS,
            "future_status_if_written": "pending",
            "expected_selection_digest_required": True,
            "queue_write_digest": queue_write_digest,
            "action_spec_preview": action_spec_preview,
        },
        "selection_preview_contract": selection_preview,
        "authority": {
            "read_only": True,
            "approval_queue_write_readiness_allowed": True,
            "approval_queue_write_allowed": False,
            "approval_execution_allowed": False,
            "companion_selection_write_allowed": False,
            "runtime_control_allowed": False,
            "runtime_dispatch_allowed": False,
            "identity_ledger_mutation_allowed": False,
            "role_card_mutation_allowed": False,
            "profile_write_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_queue_write",
            "approval_execution",
            "companion_selection_write",
            "runtime_control",
            "runtime_dispatch",
            "identity_ledger_mutation",
            "role_card_mutation",
            "profile_write",
            "provider_api_call",
            "agent_bus_task_write",
            "canonical_writeback",
        ],
        "blocked_reasons": blocked_unique,
        "readiness": {
            "companion_selection_queue_write_readiness_ready": ready,
            "companion_selection_queue_write_blocked": True,
            "companion_selection_writes_blocked": True,
            "identity_mutation_blocked": True,
            "profile_writes_blocked": True,
            "role_card_writes_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def format_phase11_chat_companion_selection_queue_write_readiness(payload: dict[str, Any]) -> str:
    """Render a compact text summary for operator CLI use."""

    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    packet = payload.get("future_queue_write_packet_preview") or {}
    lines = [
        "Phase 11 Chat Companion Selection Queue-Write Readiness",
        f"Status: {payload.get('status')}",
        f"Requested runtime: {summary.get('requested_runtime_id') or 'missing'}",
        f"Current runtime: {summary.get('current_runtime_id') or 'missing'}",
        f"Queue-write readiness ready: {summary.get('queue_write_readiness_ready')}",
        f"Selection digest: {digest.get('selection_digest') or 'missing'}",
        f"Queue-write digest: {digest.get('queue_write_digest') or 'missing'}",
        f"Future approval id: {packet.get('approval_id_preview') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
