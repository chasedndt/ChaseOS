"""Phase 11 Chat companion selection approval-preview contract.

This surface previews a future governed companion-selection change. It creates
stable digest/approval-preview metadata only; it never writes selection state,
mutates runtime identity/profile/role-card files, dispatches runtimes, or calls
providers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.policy import INITIAL_COMPANION_IDS
from runtime.companion.policy import SELECTION_TARGET_PATH as CORE_SELECTION_TARGET_PATH
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status


MODEL_VERSION = "studio.phase11_chat_companion_selection_preview.v1"
SURFACE_ID = "phase11_chat_companion_selection_approval_preview"
PASS_ID = "phase11-chat-companion-selection-approval-preview"
STATUS = "COMPLETE / APPROVAL-PREVIEW ONLY / VERIFIED / SELECTION WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-companion-selection-queue-write-readiness"
APPROVAL_CLASS = "studio_chat_companion_selection_future"
REGISTERED_COMPANION_IDS = set(INITIAL_COMPANION_IDS)
SELECTION_TARGET_PATH = CORE_SELECTION_TARGET_PATH.as_posix()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split()).lower()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _prompt_injection_indicators(message: str) -> list[str]:
    lowered = message.lower()
    indicators = [
        "ignore previous instructions",
        "without approval",
        "bypass approval",
        "override governance",
        "disable safeguards",
    ]
    return [item for item in indicators if item in lowered]


def _digest_material(
    *,
    requested_runtime: str,
    current_runtime: str,
    message: str,
    companion_status: dict[str, Any],
) -> dict[str, Any]:
    selected = companion_status.get("selected_companion") or {}
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "requested_runtime_id": requested_runtime,
        "current_runtime_id": current_runtime,
        "message_sha256": _sha256_text(message),
        "target_path": SELECTION_TARGET_PATH,
        "required_approval_class": APPROVAL_CLASS,
        "selected_companion_digest": selected.get("card_digest"),
        "selected_runtime_profile_path": selected.get("runtime_profile_path"),
        "selected_role_card_paths": selected.get("connected_role_card_paths") or [],
    }


def build_phase11_chat_companion_selection_preview(
    vault_root: str | Path,
    *,
    requested_runtime: str | None = None,
    current_runtime: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Build approval-preview-only metadata for a companion selection request."""

    vault = Path(vault_root).resolve()
    requested = _norm(requested_runtime)
    current = _norm(current_runtime) or "openclaw"
    normalized_message = " ".join(str(message or "").strip().split())
    blockers: list[str] = []

    if not requested:
        blockers.append("requested_companion_runtime_missing")
    if requested and requested not in REGISTERED_COMPANION_IDS:
        blockers.append("requested_companion_runtime_not_registered")
    if requested and requested == current:
        blockers.append("requested_companion_already_selected")
    injection = _prompt_injection_indicators(normalized_message)
    if injection:
        blockers.append("prompt_injection_indicator_present")

    companion_status = build_phase11_chat_companion_status(vault, requested_runtime=requested) if requested else build_phase11_chat_companion_status(vault)
    if companion_status.get("ok") is False and "requested_companion_runtime_not_registered" not in blockers:
        blockers.extend(str(item) for item in companion_status.get("blocked_reasons") or [])

    digest_material = _digest_material(
        requested_runtime=requested,
        current_runtime=current,
        message=normalized_message,
        companion_status=companion_status,
    )
    selection_digest = _sha256_text(_canonical_json(digest_material))
    approval_preview_ready = not blockers
    selection_change_requested = bool(requested and requested != current and requested in REGISTERED_COMPANION_IDS)

    action_spec_preview = {
        "action_type": "chat_companion_selection_change",
        "target_path": SELECTION_TARGET_PATH,
        "target_runtime_id": requested or None,
        "current_runtime_id": current or None,
        "content_sha256": selection_digest,
        "metadata": {
            "phase11_companion_selection_digest": selection_digest,
            "source_surface": SURFACE_ID,
            "source_model_version": MODEL_VERSION,
            "required_approval_class": APPROVAL_CLASS,
        },
    }

    return {
        "ok": approval_preview_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if approval_preview_ready else "BLOCKED / APPROVAL-PREVIEW ONLY / NO SELECTION WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": True,
        "summary": {
            "requested_runtime_id": requested,
            "current_runtime_id": current,
            "selection_change_requested": selection_change_requested,
            "core_companion_package_used": True,
            "registered_companion_ids": sorted(REGISTERED_COMPANION_IDS),
            "approval_preview_ready": approval_preview_ready,
            "companion_selection_written": False,
            "companion_selection_write_allowed_now": False,
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "identity_ledger_mutated": False,
            "profile_writes_performed": False,
            "role_card_writes_performed": False,
            "runtime_control_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "digest_proof": {
            "selection_digest": selection_digest,
            "digest_material": digest_material,
            "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        },
        "future_approval_packet_preview": {
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "approval_id_preview": f"chat-companion-selection-appr-{selection_digest[:16]}",
            "required_approval_class": APPROVAL_CLASS,
            "future_status_if_written": "pending",
            "action_spec_preview": action_spec_preview,
        },
        "companion_status_contract": companion_status,
        "prompt_injection": {
            "input_treated_as_untrusted": True,
            "prompt_injection_suspected": bool(injection),
            "indicators": injection,
        },
        "authority": {
            "read_only": True,
            "approval_preview_allowed": True,
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
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "readiness": {
            "companion_selection_approval_preview_ready": approval_preview_ready,
            "runtime_companion_core_adapter_synced": True,
            "companion_selection_writes_blocked": True,
            "identity_mutation_blocked": True,
            "profile_writes_blocked": True,
            "role_card_writes_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def format_phase11_chat_companion_selection_preview(payload: dict[str, Any]) -> str:
    """Render a compact text summary for operator CLI use."""

    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    preview = payload.get("future_approval_packet_preview") or {}
    lines = [
        "Phase 11 Chat Companion Selection Approval Preview",
        f"Status: {payload.get('status')}",
        f"Requested runtime: {summary.get('requested_runtime_id') or 'missing'}",
        f"Current runtime: {summary.get('current_runtime_id') or 'missing'}",
        f"Approval preview ready: {summary.get('approval_preview_ready')}",
        f"Selection digest: {digest.get('selection_digest') or 'missing'}",
        f"Future approval id: {preview.get('approval_id_preview') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
