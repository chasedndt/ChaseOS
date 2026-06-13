"""Phase 11 companion-selection approval-consumption readiness.

This contract inspects companion-selection approval artifacts created by the
queue-write execution proof and previews the future exact-once consumption
envelope. It does not approve, consume, execute, reserve markers, write the
selection target, control runtimes, call providers, write Agent Bus tasks, or
mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_companion_selection_preview import (
    APPROVAL_CLASS,
    SELECTION_TARGET_PATH,
)
from runtime.studio.phase11_chat_companion_selection_queue_write_readiness import (
    build_phase11_chat_companion_selection_queue_write_readiness,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_companion_selection_approval_consumption_readiness.v1"
SURFACE_ID = "phase11_chat_companion_selection_approval_consumption_readiness"
PASS_ID = "phase11-chat-companion-selection-approval-consumption-readiness"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / SELECTION WRITE BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-companion-selection-approval-consumption-executor"
MARKER_DIR = Path("runtime") / "studio" / "approvals" / "_companion_selection_consumption_markers"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or ""))


def _approval_root(vault: Path) -> Path:
    return vault / StudioService.APPROVAL_DIR


def _approval_path(vault: Path, approval_id: str) -> Path:
    return _approval_root(vault) / f"{_safe_id(approval_id)}.json"


def _safe_payload(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"approval_artifact_read_failed:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"approval_artifact_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "approval_artifact_json_not_object"
    return payload, None


def _action_spec(payload: dict[str, Any] | None) -> dict[str, Any]:
    spec = (payload or {}).get("action_spec")
    return spec if isinstance(spec, dict) else {}


def _metadata(payload: dict[str, Any] | None) -> dict[str, Any]:
    metadata = _action_spec(payload).get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _content_payload(spec: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(str(spec.get("content") or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _artifact_sha256(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


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


def _is_companion_selection_approval(payload: dict[str, Any] | None) -> bool:
    spec = _action_spec(payload)
    metadata = _metadata(payload)
    return bool(
        spec.get("action_type") == "chat_companion_selection_change"
        and spec.get("target_path") == SELECTION_TARGET_PATH
        and (
            metadata.get("phase11_companion_selection_queue_write_execution_proof") is True
            or metadata.get("phase11_companion_selection_queue_write_readiness") is True
            or metadata.get("required_approval_class") == APPROVAL_CLASS
        )
    )


def _list_companion_approvals(vault: Path) -> list[dict[str, Any]]:
    root = _approval_root(vault)
    if not root.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload, error = _safe_payload(path)
        if error or not _is_companion_selection_approval(payload):
            continue
        items.append(
            {
                "approval_id": str((payload or {}).get("approval_id") or path.stem),
                "path": path,
                "payload": payload,
                "status": str((payload or {}).get("status") or "unknown"),
            }
        )
    return items


def _select_approval(vault: Path, approval_id: str | None) -> dict[str, Any]:
    requested = _norm(approval_id)
    if requested:
        path = _approval_path(vault, requested)
        if not path.is_file():
            return {
                "requested_approval_id": requested,
                "selected": None,
                "error": "approval_artifact_not_found",
                "available_companion_approval_ids": [item["approval_id"] for item in _list_companion_approvals(vault)[:10]],
            }
        payload, error = _safe_payload(path)
        return {
            "requested_approval_id": requested,
            "selected": {
                "approval_id": str((payload or {}).get("approval_id") or requested),
                "path": path,
                "payload": payload,
                "status": str((payload or {}).get("status") or "unknown"),
                "parse_error": error,
            },
            "error": error,
            "available_companion_approval_ids": [item["approval_id"] for item in _list_companion_approvals(vault)[:10]],
        }

    approvals = _list_companion_approvals(vault)
    return {
        "requested_approval_id": "",
        "selected": approvals[0] if approvals else None,
        "error": None if approvals else "no_companion_selection_approval_artifacts_found",
        "available_companion_approval_ids": [item["approval_id"] for item in approvals[:10]],
    }


def _target_path_state(vault: Path, spec: dict[str, Any]) -> dict[str, Any]:
    target_path = str(spec.get("target_path") or "")
    if not target_path:
        return {
            "target_path": "",
            "target_path_present": False,
            "target_path_under_vault": False,
            "target_file_exists": False,
            "target_file_written": False,
            "target_collision": False,
            "validation": None,
        }
    service = StudioService(vault)
    validation_payload: dict[str, Any] | None = None
    under_vault = False
    target_exists = False
    try:
        resolved = service._resolve_path(target_path)  # read-only validation.
        under_vault = True
        target_exists = resolved.exists()
    except Exception:
        resolved = vault / target_path
    try:
        action = ActionSpec(
            action_type="write_file",
            target_path=target_path,
            content=str(spec.get("content") or ""),
            metadata=dict(spec.get("metadata") or {}),
            submitted_by=str(spec.get("submitted_by") or "studio-chat"),
            note=str(spec.get("note") or ""),
        )
        validation = service.validate_action(action)
        validation_payload = {
            "valid": validation.valid,
            "approval_required": validation.approval_required,
            "gate_blocked": validation.gate_blocked,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        }
    except Exception as exc:
        validation_payload = {
            "valid": False,
            "approval_required": True,
            "gate_blocked": True,
            "errors": [f"studio_service_validation_failed:{exc}"],
            "warnings": [],
        }
    return {
        "target_path": target_path,
        "target_path_present": True,
        "target_path_under_vault": under_vault,
        "target_file_exists": target_exists,
        "target_file_written": False,
        "target_collision": target_exists,
        "resolved_path_preview": _rel(vault, resolved),
        "validation": validation_payload,
    }


def _selected_summary(vault: Path, path: Path | None, payload: dict[str, Any] | None) -> dict[str, Any]:
    spec = _action_spec(payload)
    metadata = _metadata(payload)
    content = _content_payload(spec)
    return {
        "approval_id": str((payload or {}).get("approval_id") or (path.stem if path else "")),
        "status": str((payload or {}).get("status") or "unknown"),
        "path": _rel(vault, path) if path else "",
        "action_type": spec.get("action_type"),
        "target_path": spec.get("target_path"),
        "submitted_by": spec.get("submitted_by"),
        "reviewed_by": (payload or {}).get("reviewed_by"),
        "submitted_at": (payload or {}).get("submitted_at"),
        "updated_at": (payload or {}).get("updated_at"),
        "content_sha256": _sha256_text(str(spec.get("content") or "")),
        "content_included": False,
        "content_summary": {
            "selected_runtime_id": content.get("selected_runtime_id"),
            "previous_runtime_id": content.get("previous_runtime_id"),
            "selection_digest_present": bool(content.get("selection_digest")),
            "queue_write_digest_present": bool(content.get("queue_write_digest")),
        },
        "metadata": {
            "pass": metadata.get("pass"),
            "source_surface": metadata.get("source_surface"),
            "source_contract": metadata.get("source_contract"),
            "phase11_companion_selection_queue_write_execution_proof": metadata.get(
                "phase11_companion_selection_queue_write_execution_proof"
            )
            is True,
            "phase11_companion_selection_queue_write_digest": metadata.get(
                "phase11_companion_selection_queue_write_digest"
            ),
            "phase11_companion_selection_digest": metadata.get("phase11_companion_selection_digest"),
            "target_selection_write_performed": metadata.get("target_selection_write_performed") is True,
        },
    }


def build_phase11_chat_companion_selection_approval_consumption_readiness(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Build a read-only readiness packet for future companion-selection consumption."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    selection = _select_approval(vault, approval_id)
    selected = selection.get("selected")
    payload = (selected or {}).get("payload") if isinstance(selected, dict) else None
    path = (selected or {}).get("path") if isinstance(selected, dict) else None
    path = path if isinstance(path, Path) else None
    spec = _action_spec(payload)
    metadata = _metadata(payload)
    content = _content_payload(spec)
    approval_id_value = str((payload or {}).get("approval_id") or (path.stem if path else ""))
    status = str((payload or {}).get("status") or "unknown")
    marker_path = vault / MARKER_DIR / f"{_safe_id(approval_id_value) or 'unknown'}.json"
    target_state = _target_path_state(vault, spec) if payload else _target_path_state(vault, {})
    artifact_sha = _artifact_sha256(path)
    injection = _prompt_injection_indicators(normalized_message)

    selected_runtime = str(content.get("selected_runtime_id") or "")
    previous_runtime = str(content.get("previous_runtime_id") or "")
    stored_queue_digest = str(
        metadata.get("phase11_companion_selection_queue_write_digest") or content.get("queue_write_digest") or ""
    )
    stored_selection_digest = str(
        metadata.get("phase11_companion_selection_digest") or content.get("selection_digest") or ""
    )

    replay_readiness: dict[str, Any] | None = None
    replay_digest_matches: bool | None = None
    if payload and normalized_message:
        replay_readiness = build_phase11_chat_companion_selection_queue_write_readiness(
            vault,
            requested_runtime=selected_runtime or None,
            current_runtime=previous_runtime or None,
            message=normalized_message,
        )
        replay_queue_digest = str((replay_readiness.get("digest_proof") or {}).get("queue_write_digest") or "")
        replay_digest_matches = bool(stored_queue_digest and replay_queue_digest == stored_queue_digest)

    blockers: list[str] = []
    warnings: list[str] = []
    selection_error = selection.get("error")
    if selection_error:
        blockers.append(str(selection_error))
    parse_error = (selected or {}).get("parse_error") if isinstance(selected, dict) else None
    if parse_error:
        blockers.append(str(parse_error))
    if payload and not _is_companion_selection_approval(payload):
        blockers.append("approval_not_companion_selection")
    if payload and status not in {"pending", "approved"}:
        blockers.append("approval_status_not_pending_or_approved")
    if payload and status != "approved":
        blockers.append("operator_decision_not_approved")
    if payload and not stored_selection_digest:
        blockers.append("phase11_companion_selection_digest_missing")
    if payload and not stored_queue_digest:
        blockers.append("phase11_companion_selection_queue_write_digest_missing")
    if injection:
        blockers.append("prompt_injection_indicator_present")
    if replay_digest_matches is False:
        blockers.append("queue_write_digest_mismatch")
    if payload and target_state.get("target_collision"):
        blockers.append("future_companion_selection_target_collision")
    validation = target_state.get("validation") or {}
    if payload and validation.get("gate_blocked"):
        blockers.append("studio_service_validation_gate_blocked")
    if marker_path.exists():
        blockers.append("future_exact_once_marker_already_present")

    consumption_material = {
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "approval_id": approval_id_value,
        "approval_status": status,
        "approval_artifact_sha256": artifact_sha,
        "selection_digest": stored_selection_digest,
        "queue_write_digest": stored_queue_digest,
        "selected_runtime_id": selected_runtime,
        "previous_runtime_id": previous_runtime,
        "target_path": spec.get("target_path"),
        "marker_path_preview": _rel(vault, marker_path),
    }
    consumption_digest = _sha256_text(_canonical_json(consumption_material))

    hard_blockers = {
        "approval_artifact_not_found",
        "approval_artifact_json_not_object",
        "no_companion_selection_approval_artifacts_found",
        "prompt_injection_indicator_present",
        "approval_not_companion_selection",
        "approval_status_not_pending_or_approved",
        "phase11_companion_selection_digest_missing",
        "phase11_companion_selection_queue_write_digest_missing",
        "queue_write_digest_mismatch",
        "future_companion_selection_target_collision",
        "studio_service_validation_gate_blocked",
        "future_exact_once_marker_already_present",
    }
    ok = not any(item in hard_blockers or item.startswith("approval_artifact_json_malformed") for item in blockers)

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ok else "BLOCKED / READ-ONLY / NO SELECTION WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": True,
        "summary": {
            "approval_id_requested": selection.get("requested_approval_id") or "",
            "selected_approval_id": approval_id_value or None,
            "approval_artifact_known": bool(payload),
            "companion_selection_approval": bool(payload and _is_companion_selection_approval(payload)),
            "approval_status": status if payload else "missing",
            "operator_approved": status == "approved",
            "consumption_preview_ready": bool(payload) and ok,
            "consumption_preconditions_met": False,
            "approval_status_mutated": False,
            "approval_execution_called": False,
            "exact_once_marker_written": False,
            "companion_selection_written": False,
            "target_write_performed": False,
            "runtime_control_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_written": False,
            "identity_ledger_mutated": False,
            "profile_writes_performed": False,
            "role_card_writes_performed": False,
            "selected_runtime_id": selected_runtime or None,
            "previous_runtime_id": previous_runtime or None,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "source_selection": {
            "requested_approval_id": selection.get("requested_approval_id") or "",
            "selected_latest_companion_approval": bool(not selection.get("requested_approval_id") and payload),
            "available_companion_approval_count": len(selection.get("available_companion_approval_ids") or []),
            "available_companion_approval_ids": selection.get("available_companion_approval_ids") or [],
            "selection_error": selection_error,
        },
        "selected_approval": _selected_summary(vault, path, payload) if payload else None,
        "target_write_preflight": target_state,
        "preflight_checks": {
            "approval_artifact_exists": bool(path and path.exists()),
            "approval_artifact_json_valid": bool(payload),
            "approval_id_matches_request": bool(
                not selection.get("requested_approval_id")
                or str(selection.get("requested_approval_id")) == approval_id_value
            ),
            "companion_selection_metadata_present": bool(payload and _is_companion_selection_approval(payload)),
            "operator_decision_approved": status == "approved",
            "approval_status_pending_or_approved": status in {"pending", "approved"},
            "selection_digest_present": bool(stored_selection_digest),
            "queue_write_digest_present": bool(stored_queue_digest),
            "source_message_replay_supplied": bool(normalized_message),
            "queue_write_digest_matches_replayed_message_when_supplied": replay_digest_matches,
            "target_path_under_vault": bool(target_state.get("target_path_under_vault")),
            "target_path_collision_absent": not bool(target_state.get("target_collision")),
            "studio_service_validation_gate_clear": not bool(validation.get("gate_blocked")),
            "future_exact_once_marker_absent": not marker_path.exists(),
            "approval_record_update_allowed_now": False,
            "studio_service_execute_approved_called": False,
            "target_write_allowed_now": False,
        },
        "digest_proof": {
            "approval_artifact_sha256": artifact_sha,
            "selection_digest": stored_selection_digest or None,
            "queue_write_digest": stored_queue_digest or None,
            "replayed_queue_write_digest_matched": replay_digest_matches,
            "consumption_digest": consumption_digest,
            "digest_material": consumption_material,
            "digest_required_for_future_consumption": True,
        },
        "exact_once_marker_preview": {
            "marker_path_preview": _rel(vault, marker_path),
            "marker_exists_now": marker_path.exists(),
            "marker_reserved_now": False,
            "marker_written_now": False,
            "duplicate_consumption_blocks_before_writes": True,
        },
        "future_consumption_packet_preview": {
            "visible": True,
            "consumption_packet_id_preview": f"companion-selection-consumption-{consumption_digest[:20]}",
            "approval_class": APPROVAL_CLASS,
            "approval_id": approval_id_value or None,
            "approval_status_required": "approved",
            "approval_status_now": status if payload else "missing",
            "future_status_transition_preview": "approved -> executing -> executed",
            "approval_status_mutated": False,
            "approval_execution_called": False,
            "exact_once_marker_written": False,
            "target_path": spec.get("target_path"),
            "companion_selection_written": False,
            "target_file_written": False,
            "selected_runtime_id": selected_runtime or None,
            "previous_runtime_id": previous_runtime or None,
            "execution_audit_path_preview": f"07_LOGS/Agent-Activity/companion-selection-consumption-{consumption_digest[:20]}.md",
        },
        "replay_queue_write_readiness_contract": replay_readiness,
        "authority": {
            "read_only": True,
            "approval_gated": True,
            "approval_consumption_preview_allowed": True,
            "approval_status_mutation_allowed": False,
            "approval_grant_or_reject_allowed": False,
            "approval_execution_allowed": False,
            "target_vault_write_allowed": False,
            "companion_selection_write_allowed": False,
            "exact_once_marker_write_allowed": False,
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
            "approval_grant_or_reject",
            "approval_status_mutation",
            "studio_service_execute_approved",
            "exact_once_marker_write",
            "companion_selection_target_write",
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
        "warnings": warnings,
    }


def format_phase11_chat_companion_selection_approval_consumption_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    marker = payload.get("exact_once_marker_preview") or {}
    target = payload.get("target_write_preflight") or {}
    lines = [
        "Phase 11 Chat Companion Selection Approval Consumption Readiness",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('selected_approval_id') or 'none'}",
        f"Approval status: {summary.get('approval_status')}",
        f"Consumption preview ready: {summary.get('consumption_preview_ready')}",
        f"Consumption preconditions met: {summary.get('consumption_preconditions_met')}",
        f"Consumption digest: {digest.get('consumption_digest') or 'none'}",
        f"Marker path preview: {marker.get('marker_path_preview') or 'none'}",
        f"Target path: {target.get('target_path') or 'none'}",
        f"Companion selection written: {summary.get('companion_selection_written')}",
        f"Approval execution called: {summary.get('approval_execution_called')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: read-only consumption readiness only; no approval status mutation, "
        "no execute_approved call, no exact-once marker write, no companion selection "
        "target write, no runtime/provider/Agent Bus/canonical mutation."
    )
    return "\n".join(lines)
