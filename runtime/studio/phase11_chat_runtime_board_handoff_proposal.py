"""Phase 11 Studio Chat runtime board handoff proposal surface.

This surface lets Studio Chat package the selected thread or draft into a
digest-bound approval request for a future Hermes/OpenClaw/Codex runtime board
item. It may queue only the approval artifact after an exact digest match. It
does not write a runtime board item, write an Agent Bus task, dispatch a
runtime, call Discord, call providers, mutate schedules, or persist messages.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import load_native_chat_state, safe_state_id
from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_runtime_board_handoff_proposal.v1"
SURFACE_ID = "phase11_chat_runtime_board_handoff_proposal"
PASS_ID = "studio-runtime-chat-runtime-board-handoff-proposal"
STATUS_PREVIEW = "READY / APPROVAL-QUEUE-WRITE-PREVIEW / RUNTIME BOARD WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / RUNTIME BOARD WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-proposal-consumption"
AUDIT_ROOT = "runtime/studio/approvals/chat-runtime-board-handoffs"
METADATA_BLOCK_KEY = "phase11_chat_runtime_board_handoff_execution_blocked"

DEFAULT_THREAD_ID = "runtime-ops-openclaw-chat"
DEFAULT_BOARD_LANE = "triage"
BOARD_LANES = {"triage", "backlog", "in_progress", "review", "done"}
SECRET_TOKEN = "[REDACTED_SECRET]"
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_style_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    ("github_style_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE)),
    ("slack_style_token", re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b", re.IGNORECASE)),
    ("bearer_token", re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})")),
    (
        "secret_assignment",
        re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential|password|passwd|pwd)\s*[:=]\s*)([^\s,;]{8,})"),
    ),
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _slug(value: str | None, fallback: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip().lower()).strip("-")
    return (text or fallback)[:96].strip("-") or fallback


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


def _redact(value: str) -> dict[str, Any]:
    redacted = value
    categories: list[str] = []
    count = 0
    for category, pattern in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}{SECRET_TOKEN}"
            return SECRET_TOKEN

        redacted, local_count = pattern.subn(repl, redacted)
        if local_count:
            categories.append(category)
    return {
        "contains_secret": bool(count),
        "redacted_text": redacted,
        "redaction_count": count,
        "indicator_categories": list(dict.fromkeys(categories)),
    }


def _foundation_threads(foundation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(thread.get("thread_id") or ""): thread
        for thread in foundation.get("threads") or []
        if thread.get("thread_id")
    }


def _select_thread(
    foundation: dict[str, Any],
    native_state: dict[str, Any],
    *,
    selected_thread_id: str | None,
    runtime_id: str | None,
) -> tuple[dict[str, Any], bool, list[str]]:
    blockers: list[str] = []
    threads = _foundation_threads(foundation)
    requested_thread_id = safe_state_id(selected_thread_id, "") if selected_thread_id else ""
    route_thread_id = str((native_state.get("route_state") or {}).get("thread_id") or "")
    requested_runtime = _norm(runtime_id)

    thread_id = requested_thread_id or route_thread_id
    route_state_used = bool(not requested_thread_id and route_thread_id)
    if not thread_id and requested_runtime:
        for candidate in threads.values():
            if str(candidate.get("runtime_id") or "").lower() == requested_runtime.lower():
                thread_id = str(candidate.get("thread_id") or "")
                break
    thread_id = thread_id or DEFAULT_THREAD_ID
    thread = threads.get(thread_id)
    if not thread:
        blockers.append("selected_thread_not_found")
        return {}, route_state_used, blockers

    thread_runtime = str(thread.get("runtime_id") or "")
    if requested_runtime and thread_runtime and requested_runtime.lower() != thread_runtime.lower():
        blockers.append("selected_thread_runtime_mismatch")
    if not thread_runtime:
        blockers.append("selected_thread_has_no_runtime_lane")
    return thread, route_state_used, blockers


def _workspace_for_thread(foundation: dict[str, Any], thread: dict[str, Any]) -> dict[str, Any]:
    workspace_id = str(thread.get("workspace_id") or "")
    for workspace in foundation.get("workspaces") or []:
        if str(workspace.get("workspace_id") or "") == workspace_id:
            return workspace
    return {}


def _latest_draft(native_state: dict[str, Any], thread_id: str, draft_id: str | None) -> dict[str, Any]:
    drafts = [
        draft
        for draft in native_state.get("drafts") or []
        if str(draft.get("thread_id") or "") == thread_id
    ]
    requested = safe_state_id(draft_id, "") if draft_id else ""
    if requested:
        for draft in drafts:
            if str(draft.get("draft_id") or "") == requested:
                return draft
    return drafts[-1] if drafts else {}


def _board_target(thread: dict[str, Any], workspace: dict[str, Any], requested: str | None) -> str:
    if _norm(requested):
        return _slug(requested, "runtime-board")
    targets = [
        str(item)
        for item in list(thread.get("proposal_targets") or []) + list(workspace.get("board_targets") or [])
        if str(item).strip() and "agent_bus" not in str(item).lower()
    ]
    return _slug(targets[0] if targets else f"{thread.get('runtime_id') or 'runtime'}-board", "runtime-board")


def _board_lane(requested: str | None) -> str:
    lane = _slug(requested, DEFAULT_BOARD_LANE).replace("-", "_")
    return lane if lane in BOARD_LANES else DEFAULT_BOARD_LANE


def _handoff_title(thread: dict[str, Any], title: str | None, summary: str) -> str:
    requested = _norm(title)
    if requested:
        return requested[:120]
    base = str(thread.get("title") or "Runtime Board Handoff")
    if summary:
        return " ".join(summary.split()[:9]).strip(" .,:;")[:120] or base
    return base[:120]


def _handoff_summary(
    *,
    handoff_summary: str | None,
    message: str | None,
    latest_draft: dict[str, Any],
) -> tuple[str, str, str]:
    explicit = _norm(handoff_summary)
    if explicit:
        return explicit, "explicit_handoff_summary", ""
    msg = _norm(message)
    if msg:
        return msg, "chat_message", ""
    draft_text = str(latest_draft.get("draft_text") or "")
    if draft_text.strip():
        return _norm(draft_text), "message_draft", str(latest_draft.get("draft_id") or "")
    return "Review this Studio Chat thread and prepare a runtime board item.", "default_thread_review", ""


def _board_packet(
    *,
    foundation: dict[str, Any],
    thread: dict[str, Any],
    workspace: dict[str, Any],
    board_target_id: str,
    board_lane: str,
    title: str,
    summary_text: str,
    source_text_kind: str,
    source_draft_id: str,
    operator_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    runtime_id = str(thread.get("runtime_id") or "runtime")
    runtime_slug = _slug(runtime_id, "runtime")
    action_spec = {
        "handoff_kind": "studio_chat_to_runtime_board",
        "runtime_id": runtime_id,
        "workspace_id": str(thread.get("workspace_id") or ""),
        "folder_id": str(thread.get("folder_id") or ""),
        "thread_id": str(thread.get("thread_id") or ""),
        "thread_title": str(thread.get("title") or ""),
        "thread_kind": str(thread.get("thread_kind") or ""),
        "board_target_id": board_target_id,
        "board_lane": board_lane,
        "title": title,
        "source_text_kind": source_text_kind,
        "source_draft_id": source_draft_id,
        "source_text_sha256": _sha256_text(summary_text),
        "context_paths": list(thread.get("context_paths") or [])[:8],
        "workspace_context_paths": [
            item.get("path")
            for item in workspace.get("context_paths") or []
            if item.get("path")
        ][:8],
        "submitted_by": operator_id or "studio-operator",
    }
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "foundation_model_version": foundation.get("model_version"),
        "action_spec": action_spec,
    }
    handoff_digest = _sha256_text(_canonical_json(digest_material))
    handoff_id = f"runtime-board-handoff-{runtime_slug}-{handoff_digest[:16]}"
    target_path = f"runtime/boards/{runtime_slug}/{board_target_id}/{handoff_id}.json"
    packet = {
        "schema_version": "phase11_chat_runtime_board_handoff.v1",
        "handoff_id": handoff_id,
        "handoff_kind": action_spec["handoff_kind"],
        "status": "pending_approval_preview",
        "runtime_id": runtime_id,
        "workspace_id": action_spec["workspace_id"],
        "folder_id": action_spec["folder_id"],
        "thread_id": action_spec["thread_id"],
        "thread_title": action_spec["thread_title"],
        "thread_kind": action_spec["thread_kind"],
        "board_target_id": board_target_id,
        "board_lane": board_lane,
        "title": title,
        "handoff_summary": summary_text,
        "source_text_kind": source_text_kind,
        "source_draft_id": source_draft_id,
        "source_text_sha256": action_spec["source_text_sha256"],
        "context_paths": action_spec["context_paths"],
        "workspace_context_paths": action_spec["workspace_context_paths"],
        "approval_required_before_effect": True,
        "approval_queue_request_only": True,
        "runtime_board_item_created": False,
        "runtime_board_written": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "chat_message_sent": False,
        "conversation_log_written": False,
        "discord_api_called": False,
        "discord_thread_created": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_allowed": False,
        "handoff_digest": handoff_digest,
        "target_path": target_path,
    }
    return packet, digest_material


def _find_existing(vault: Path, handoff_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active_statuses = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_chat_runtime_board_handoff_digest") != handoff_digest:
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


def _approval_spec(
    *,
    handoff_packet: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    content = json.dumps(handoff_packet, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    handoff_digest = str(handoff_packet.get("handoff_digest") or "")
    return ActionSpec(
        action_type="create_file",
        target_path=str(handoff_packet.get("target_path") or ""),
        content=content,
        metadata={
            "pass": PASS_ID,
            "source_surface": SURFACE_ID,
            "phase11_chat_runtime_board_handoff_proposal": True,
            METADATA_BLOCK_KEY: True,
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": "future_runtime_board_handoff_executor",
            "phase11_chat_runtime_board_handoff_digest": handoff_digest,
            "phase11_chat_runtime_board_handoff_digest_material_sha256": _sha256_text(
                _canonical_json(digest_material)
            ),
            "runtime_id": handoff_packet.get("runtime_id"),
            "workspace_id": handoff_packet.get("workspace_id"),
            "folder_id": handoff_packet.get("folder_id"),
            "thread_id": handoff_packet.get("thread_id"),
            "board_target_id": handoff_packet.get("board_target_id"),
            "board_lane": handoff_packet.get("board_lane"),
            "operator_confirmation": operator_id or "studio-operator",
            "runtime_board_item_created": False,
            "runtime_board_written": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_allowed": False,
        },
        submitted_by="studio-chat",
        note="Phase 11 Chat runtime board handoff approval request; board/runtime effects deferred.",
    )


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    handoff_packet: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> str:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    handoff_digest = str(handoff_packet.get("handoff_digest") or "")
    path = root / f"{handoff_digest}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "handoff_digest": handoff_digest,
        "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        "handoff_id": handoff_packet.get("handoff_id"),
        "runtime_id": handoff_packet.get("runtime_id"),
        "thread_id": handoff_packet.get("thread_id"),
        "board_target_id": handoff_packet.get("board_target_id"),
        "board_lane": handoff_packet.get("board_lane"),
        "target_path": handoff_packet.get("target_path"),
        "operator_id": operator_id or "studio-operator",
        "approval_request_created": True,
        "target_file_written": False,
        "runtime_board_item_created": False,
        "runtime_board_written": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "chat_message_sent": False,
        "discord_api_called": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_allowed": False,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return _rel(vault, path)


def build_phase11_chat_runtime_board_handoff_proposal(
    vault_root: str | Path,
    *,
    selected_thread_id: str | None = None,
    runtime_id: str | None = None,
    board_target_id: str | None = None,
    board_lane: str | None = None,
    title: str | None = None,
    message: str | None = None,
    handoff_summary: str | None = None,
    draft_id: str | None = None,
    expected_handoff_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Preview or queue one approval request for a future runtime board handoff."""

    vault = Path(vault_root).resolve()
    foundation = build_phase11_chat_workspaces_foundation(vault)
    native_state = load_native_chat_state(vault)
    thread, route_state_used, selection_blockers = _select_thread(
        foundation,
        native_state,
        selected_thread_id=selected_thread_id,
        runtime_id=runtime_id,
    )
    workspace = _workspace_for_thread(foundation, thread) if thread else {}
    latest_draft = _latest_draft(native_state, str(thread.get("thread_id") or ""), draft_id) if thread else {}
    raw_summary_text, source_text_kind, source_draft_id = _handoff_summary(
        handoff_summary=handoff_summary,
        message=message,
        latest_draft=latest_draft,
    )
    raw_title = _handoff_title(thread, title, raw_summary_text) if thread else _norm(title) or "Runtime Board Handoff"
    summary_redaction = _redact(raw_summary_text)
    title_redaction = _redact(raw_title)
    contains_secret = bool(summary_redaction["contains_secret"] or title_redaction["contains_secret"])
    safe_summary_text = str(summary_redaction["redacted_text"])
    safe_title = str(title_redaction["redacted_text"])
    target = _board_target(thread, workspace, board_target_id) if thread else _slug(board_target_id, "runtime-board")
    lane = _board_lane(board_lane)
    packet, digest_material = _board_packet(
        foundation=foundation,
        thread=thread or {},
        workspace=workspace or {},
        board_target_id=target,
        board_lane=lane,
        title=safe_title,
        summary_text=safe_summary_text,
        source_text_kind=source_text_kind,
        source_draft_id=source_draft_id,
        operator_id=operator_id,
    )
    handoff_digest = str(packet.get("handoff_digest") or "")
    expected = str(expected_handoff_digest or "").strip()
    target_path = str(packet.get("target_path") or "")
    target_abs = vault / target_path

    blockers = list(selection_blockers)
    if contains_secret:
        blockers.append("secret_or_credential_indicator_present")
    if target_abs.exists():
        blockers.append("runtime_board_target_collision")
    if write_approval and not expected:
        blockers.append("expected_handoff_digest_required_for_queue_write")
    if write_approval and expected and expected != handoff_digest:
        blockers.append("expected_handoff_digest_mismatch")

    spec = _approval_spec(
        handoff_packet=packet,
        digest_material=digest_material,
        operator_id=operator_id,
    )
    validation = StudioService(vault).validate_action(spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")

    hard_blockers = list(dict.fromkeys(blockers))
    duplicate = _find_existing(vault, handoff_digest) if write_approval else None
    warnings: list[str] = []
    if duplicate:
        warnings.append("duplicate_active_runtime_board_handoff_request_present")

    created = False
    approval_id = None
    approval_path = None
    audit_path = None
    queue_writer_called = False
    status = STATUS_PREVIEW
    if write_approval and not hard_blockers and duplicate:
        approval_id = str(duplicate.get("approval_id") or "")
        approval_path = str(duplicate.get("path") or "")
        status = "COMPLETE / DUPLICATE-BLOCKED / EXISTING APPROVAL RETURNED / RUNTIME BOARD WRITES BLOCKED"
    elif write_approval and not hard_blockers:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_path = _write_audit(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            handoff_packet=packet,
            digest_material=digest_material,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    ok = not any(
        item in hard_blockers
        for item in {
            "selected_thread_not_found",
            "selected_thread_runtime_mismatch",
            "selected_thread_has_no_runtime_lane",
            "secret_or_credential_indicator_present",
            "runtime_board_target_collision",
            "expected_handoff_digest_required_for_queue_write",
            "expected_handoff_digest_mismatch",
            "studio_service_validation_gate_blocked",
        }
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not bool(created),
        "approval_gated": True,
        "summary": {
            "runtime_board_handoff_preview_ready": ok,
            "handoff_id": packet.get("handoff_id"),
            "runtime_id": packet.get("runtime_id"),
            "workspace_id": packet.get("workspace_id"),
            "folder_id": packet.get("folder_id"),
            "thread_id": packet.get("thread_id"),
            "board_target_id": packet.get("board_target_id"),
            "board_lane": packet.get("board_lane"),
            "title": packet.get("title"),
            "source_text_kind": source_text_kind,
            "source_draft_id": source_draft_id,
            "route_state_used": route_state_used,
            "target_path_preview": target_path,
            "write_approval_requested": bool(write_approval),
            "approval_request_created": created,
            "duplicate_active_request_present": bool(duplicate),
            "duplicate_returned_existing_request": bool(write_approval and duplicate and not created and not hard_blockers),
            "approval_id": approval_id,
            "approval_artifact_path": approval_path,
            "queue_write_preview_ready": not hard_blockers,
            "target_file_written": False,
            "runtime_board_item_created": False,
            "runtime_board_written": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_allowed": False,
            "blocker_count": len(hard_blockers),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "digest_proof": {
            "handoff_digest": handoff_digest,
            "expected_handoff_digest": expected or None,
            "expected_digest_matched": bool(expected and expected == handoff_digest),
            "digest_required_for_write": True,
            "digest_material": digest_material,
        },
        "source_preview": {
            "source_text_kind": source_text_kind,
            "source_draft_id": source_draft_id,
            "thread_id": packet.get("thread_id"),
            "request_summary_preview": safe_summary_text[:320],
            "source_text_sha256": packet.get("source_text_sha256"),
            "route_state_used": route_state_used,
            "draft_found": bool(latest_draft),
        },
        "secret_redaction": {
            "source_contains_secret": contains_secret,
            "source_redacted": contains_secret,
            "redaction_count": int(summary_redaction["redaction_count"]) + int(title_redaction["redaction_count"]),
            "indicator_categories": list(
                dict.fromkeys(
                    list(summary_redaction["indicator_categories"])
                    + list(title_redaction["indicator_categories"])
                )
            ),
        },
        "future_board_item_preview": packet,
        "approval_queue_write": {
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "approval_status_now": "pending" if created else (duplicate or {}).get("status"),
            "approval_artifact_path": approval_path,
            "duplicate": duplicate,
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
        },
        "target_write_proof": {
            "target_path": target_path,
            "target_file_exists_after": target_abs.exists(),
            "target_file_written": False,
            "runtime_board_item_created": False,
            "runtime_board_written": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "conversation_log_written": False,
            "discord_api_called": False,
            "discord_thread_created": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_allowed": False,
        },
        "service_validation": {
            "valid": validation.valid,
            "gate_blocked": validation.gate_blocked,
            "approval_required": True,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        },
        "authority": {
            "approval_queue_write_allowed_with_digest": True,
            "approval_queue_write_performed": created,
            "approval_execution_allowed": False,
            "runtime_board_write_allowed": False,
            "runtime_board_item_create_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "chat_message_send_allowed": False,
            "conversation_log_write_allowed": False,
            "discord_api_calls_allowed": False,
            "discord_thread_create_allowed": False,
            "schedule_mutation_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_execution",
            "runtime_board_write",
            "runtime_board_item_create",
            "agent_bus_task_write",
            "runtime_dispatch",
            "workflow_dispatch",
            "chat_message_send",
            "conversation_log_write",
            "discord_api_call",
            "discord_thread_create",
            "schedule_mutation",
            "provider_api_call",
            "credential_value_display",
            "canonical_writeback",
        ],
        "readiness": {
            "phase11_chat_runtime_board_handoff_proposal_ready": True,
            "runtime_board_handoff_preview_ready": ok,
            "runtime_board_handoff_requires_digest": True,
            "runtime_board_handoff_approval_queue_write_gated": True,
            "generic_studio_service_execution_blocked": True,
            "runtime_board_write_blocked": True,
            "agent_bus_task_write_blocked": True,
            "runtime_dispatch_blocked": True,
            "discord_api_call_blocked": True,
            "schedule_mutation_blocked": True,
            "provider_call_blocked": True,
            "credential_values_hidden": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "blocked_reasons": hard_blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_chat_runtime_board_handoff_proposal(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    queue = payload.get("approval_queue_write") or {}
    return "\n".join(
        [
            "Phase 11 Chat Runtime Board Handoff Proposal",
            f"  status: {payload.get('status')}",
            f"  handoff_id: {summary.get('handoff_id')}",
            f"  runtime_id: {summary.get('runtime_id')}",
            f"  thread_id: {summary.get('thread_id')}",
            f"  board_target_id: {summary.get('board_target_id')}",
            f"  board_lane: {summary.get('board_lane')}",
            f"  handoff_digest: {digest.get('handoff_digest')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  approval_id: {summary.get('approval_id') or 'none'}",
            f"  approval_artifact_path: {queue.get('approval_artifact_path') or 'none'}",
            f"  target_path: {summary.get('target_path_preview')}",
            f"  target_file_written: {summary.get('target_file_written')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: approval queue artifact only after exact digest; no runtime board write, Agent Bus task, runtime dispatch, Discord call, provider call, or canonical writeback.",
        ]
    )
