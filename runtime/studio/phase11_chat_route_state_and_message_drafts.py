"""Phase 11 Studio Chat route state and message draft surface.

This module persists only local Studio Chat UI state: the selected
workspace/folder/thread/tab route and one or more message drafts. It does not
send messages, persist transcripts, write Agent Bus tasks, mutate runtime
boards, mutate schedules, call providers, call Discord, read credentials, or
write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import (
    DRAFT_STATE_DIR,
    ROUTE_STATE_DIR,
    draft_state_path,
    load_native_chat_state,
    route_state_path,
    safe_state_id,
)
from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation


MODEL_VERSION = "studio.phase11_chat_route_state_and_message_drafts.v1"
SURFACE_ID = "phase11_chat_route_state_and_message_drafts"
PASS_ID = "studio-runtime-chat-route-state-and-message-draft-surface"
STATUS = "COMPLETE / LOCAL UI STATE / VERIFIED / NO MESSAGE SEND"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-proposal-consumption"
SECRET_REDACTION_TOKEN = "[REDACTED_SECRET]"

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_style_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    ("github_style_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE)),
    ("slack_style_token", re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b", re.IGNORECASE)),
    ("bearer_token", re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})")),
    ("secret_assignment", re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential|password|passwd|pwd)\s*[:=]\s*)([^\s,;]{8,})")),
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _redact_secret_bearing_input(value: str) -> dict[str, Any]:
    redacted = value
    categories: list[str] = []
    redaction_count = 0
    for category, pattern in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            nonlocal redaction_count
            redaction_count += 1
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}{SECRET_REDACTION_TOKEN}"
            return SECRET_REDACTION_TOKEN

        redacted, count = pattern.subn(repl, redacted)
        if count:
            categories.append(category)
    return {
        "contains_secret": bool(redaction_count),
        "redacted_text": redacted,
        "redaction_count": redaction_count,
        "indicator_categories": list(dict.fromkeys(categories)),
    }


def _blocked_effects() -> dict[str, bool]:
    return {
        "chat_message_sent": False,
        "chat_transcript_written": False,
        "conversation_log_written": False,
        "discord_api_called": False,
        "discord_thread_created": False,
        "webhook_call_performed": False,
        "agent_bus_task_written": False,
        "runtime_board_written": False,
        "runtime_dispatched": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
    }


def _authority() -> dict[str, bool]:
    return {
        "local_chat_route_state_write_allowed": True,
        "local_chat_message_draft_write_allowed": True,
        "message_intent_state_write_allowed": True,
        "chat_message_send_allowed": False,
        "chat_transcript_write_allowed": False,
        "conversation_log_write_allowed": False,
        "discord_api_calls_allowed": False,
        "discord_thread_create_allowed": False,
        "webhook_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_board_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "schedule_mutation_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _index_foundation(foundation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    workspaces = {str(item.get("workspace_id") or ""): item for item in foundation.get("workspaces") or []}
    folders = {
        f"{folder.get('workspace_id')}:{folder.get('folder_id')}": folder
        for folder in foundation.get("folders") or []
    }
    threads = {str(item.get("thread_id") or ""): item for item in foundation.get("threads") or []}
    tabs: dict[str, dict[str, Any]] = {}
    for tab in foundation.get("tabs") or []:
        tab_id = str(tab.get("tab_id") or "")
        tabs[tab_id] = tab
        workspace_id = str(tab.get("workspace_id") or "")
        if workspace_id and tab_id.startswith(f"{workspace_id}-"):
            tab_slug = tab_id.removeprefix(f"{workspace_id}-")
            tabs[f"{workspace_id}:{tab_slug}"] = tab
    return {
        "workspaces": {key: value for key, value in workspaces.items() if key},
        "folders": {key: value for key, value in folders.items() if not key.endswith(":")},
        "threads": {key: value for key, value in threads.items() if key},
        "tabs": tabs,
    }


def _resolve_selection(
    foundation: dict[str, Any],
    *,
    selected_workspace_id: str | None,
    selected_folder_id: str | None,
    selected_thread_id: str | None,
    selected_tab_id: str | None,
    require_thread: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    index = _index_foundation(foundation)
    blockers: list[str] = []
    workspace_id = safe_state_id(selected_workspace_id, "") if selected_workspace_id else ""
    folder_id = safe_state_id(selected_folder_id, "") if selected_folder_id else ""
    thread_id = safe_state_id(selected_thread_id, "") if selected_thread_id else ""

    thread = index["threads"].get(thread_id) if thread_id else None
    if thread_id and not thread:
        blockers.append("selected_thread_not_found")
    if thread:
        thread_workspace_id = str(thread.get("workspace_id") or "")
        thread_folder_id = str(thread.get("folder_id") or "")
        if workspace_id and workspace_id != thread_workspace_id:
            blockers.append("selected_thread_workspace_mismatch")
        workspace_id = workspace_id or thread_workspace_id
        folder_id = folder_id or thread_folder_id
    if require_thread and not thread_id:
        blockers.append("selected_thread_id_required_for_message_draft")
    if not workspace_id:
        blockers.append("selected_workspace_or_thread_required")
    workspace = index["workspaces"].get(workspace_id)
    if workspace_id and not workspace:
        blockers.append("selected_workspace_not_found")
    if folder_id and f"{workspace_id}:{folder_id}" not in index["folders"]:
        blockers.append("selected_folder_not_found")

    tab_slug = safe_state_id(selected_tab_id, "") if selected_tab_id else ""
    if tab_slug.startswith(f"{workspace_id}-"):
        tab_key = tab_slug
        tab_slug = tab_slug.removeprefix(f"{workspace_id}-")
    else:
        tab_slug = tab_slug or ("threads" if thread_id else "chat")
        tab_key = f"{workspace_id}:{tab_slug}"
    tab = index["tabs"].get(tab_key) or index["tabs"].get(f"{workspace_id}-{tab_slug}")
    if workspace_id and not tab:
        blockers.append("selected_tab_not_found")

    route_preview = f"#chat/{workspace_id}"
    if thread_id:
        route_preview = f"#chat/{workspace_id}/threads/{thread_id}"
    elif tab_slug and tab_slug != "chat":
        route_preview = f"#chat/{workspace_id}/{tab_slug}"

    runtime_id = str((thread or {}).get("runtime_id") or "")
    return {
        "workspace_id": workspace_id,
        "folder_id": folder_id,
        "thread_id": thread_id,
        "tab_id": tab_slug,
        "route_preview": route_preview,
        "workspace_label": (workspace or {}).get("label"),
        "thread_title": (thread or {}).get("title"),
        "runtime_id": runtime_id,
        "thread_kind": (thread or {}).get("thread_kind"),
    }, blockers


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _route_record(selection: dict[str, Any], *, operator_id: str) -> dict[str, Any]:
    now = _now_utc()
    return {
        "schema_version": "phase11_chat_route_state.v1",
        "record_type": "route_state",
        "route_state_id": "current",
        "source_surface": SURFACE_ID,
        "updated_at_utc": now,
        "updated_by": operator_id,
        "workspace_id": selection.get("workspace_id") or "",
        "folder_id": selection.get("folder_id") or "",
        "thread_id": selection.get("thread_id") or "",
        "tab_id": selection.get("tab_id") or "chat",
        "route_preview": selection.get("route_preview") or "",
        "workspace_label": selection.get("workspace_label") or "",
        "thread_title": selection.get("thread_title") or "",
        "runtime_id": selection.get("runtime_id") or "",
        "native_route_state_persisted": True,
        **_blocked_effects(),
    }


def _draft_record(
    selection: dict[str, Any],
    *,
    draft_id: str,
    draft_text: str,
    message_intent: str,
    title: str,
    operator_id: str,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _now_utc()
    created_at = str((existing or {}).get("created_at_utc") or now)
    return {
        "schema_version": "phase11_chat_message_draft.v1",
        "record_type": "message_draft",
        "draft_id": draft_id,
        "source_surface": SURFACE_ID,
        "status": "draft_saved_local_only",
        "created_at_utc": created_at,
        "updated_at_utc": now,
        "updated_by": operator_id,
        "title": title or (selection.get("thread_title") or "Message Draft"),
        "workspace_id": selection.get("workspace_id") or "",
        "folder_id": selection.get("folder_id") or "",
        "thread_id": selection.get("thread_id") or "",
        "thread_title": selection.get("thread_title") or "",
        "runtime_id": selection.get("runtime_id") or "",
        "thread_kind": selection.get("thread_kind") or "",
        "message_intent": message_intent or "draft_message",
        "draft_text": draft_text,
        "draft_text_sha256": _sha256_text(draft_text),
        "draft_char_count": len(draft_text),
        "secret_indicator_present": False,
        "secret_indicator_categories": [],
        "future_send_requires_approval": True,
        "future_runtime_handoff_requires_proposal": True,
        "native_draft_state_persisted": True,
        **_blocked_effects(),
    }


def build_phase11_chat_route_state_and_message_drafts(
    vault_root: str | Path,
    *,
    selected_workspace_id: str | None = None,
    selected_folder_id: str | None = None,
    selected_thread_id: str | None = None,
    selected_tab_id: str | None = None,
    draft_id: str | None = None,
    draft_text: str | None = None,
    message_intent: str | None = None,
    title: str | None = None,
    operator_id: str = "studio-operator",
    write_route_state: bool = False,
    write_draft: bool = False,
) -> dict[str, Any]:
    """Preview or persist local route/draft state without runtime side effects."""

    vault = Path(vault_root).resolve()
    foundation = build_phase11_chat_workspaces_foundation(vault)
    selection, selection_blockers = _resolve_selection(
        foundation,
        selected_workspace_id=selected_workspace_id,
        selected_folder_id=selected_folder_id,
        selected_thread_id=selected_thread_id,
        selected_tab_id=selected_tab_id,
        require_thread=write_draft,
    )
    normalized_draft = str(draft_text or "")
    normalized_title = _norm(title) if title is not None else ""
    secret_report = _redact_secret_bearing_input(normalized_draft)
    title_secret_report = _redact_secret_bearing_input(normalized_title)
    draft_secret = bool(secret_report["contains_secret"] or title_secret_report["contains_secret"])
    blocked_reasons = list(selection_blockers)
    if write_draft and not normalized_draft.strip():
        blocked_reasons.append("draft_text_required")
    if write_draft and draft_secret:
        blocked_reasons.append("secret_or_credential_indicator_present")
    if not write_route_state and not write_draft:
        blocked_reasons = []

    route_path = route_state_path(vault)
    current_route_state = _read_json(route_path) if route_path.exists() else {}
    native_state_before = load_native_chat_state(vault)
    drafts_before = list(native_state_before.get("drafts") or [])
    selected_draft_id = safe_state_id(draft_id, "") if draft_id else ""
    if write_draft and not selected_draft_id:
        selected_draft_id = safe_state_id(f"{selection.get('thread_id') or 'thread'}__current", "draft")
    draft_path = draft_state_path(vault, selected_draft_id) if selected_draft_id else None

    route_state_written = False
    draft_written = False
    written_paths: list[str] = []
    if (write_route_state or write_draft) and blocked_reasons:
        ok = False
        status = "BLOCKED / LOCAL CHAT UI STATE / NO WRITE"
    else:
        ok = True
        status = STATUS
        if write_route_state:
            route_payload = _route_record(selection, operator_id=operator_id)
            _write_json(route_path, route_payload)
            current_route_state = route_payload | {"state_record_path": _rel(vault, route_path)}
            route_state_written = True
            written_paths.append(_rel(vault, route_path))
        if write_draft and draft_path is not None:
            existing = _read_json(draft_path) if draft_path.exists() else {}
            draft_payload = _draft_record(
                selection,
                draft_id=selected_draft_id,
                draft_text=normalized_draft,
                message_intent=_norm(message_intent) or "draft_message",
                title=normalized_title,
                operator_id=operator_id,
                existing=existing,
            )
            _write_json(draft_path, draft_payload)
            draft_written = True
            written_paths.append(_rel(vault, draft_path))

    native_state_after = load_native_chat_state(vault)
    current_route_state = native_state_after.get("route_state") or current_route_state
    drafts_after = list(native_state_after.get("drafts") or drafts_before)
    draft_preview = {}
    if selected_draft_id:
        draft_preview = next((item for item in drafts_after if item.get("draft_id") == selected_draft_id), {})

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "local_ui_state_only": True,
        "summary": {
            "route_state_persistence_built": True,
            "message_draft_state_persistence_built": True,
            "message_intent_state_persistence_built": True,
            "route_state_written": route_state_written,
            "draft_written": draft_written,
            "current_route_state_persisted": bool(native_state_after.get("route_state_persisted")),
            "draft_count": native_state_after.get("draft_count"),
            "selected_workspace_id": selection.get("workspace_id") or "",
            "selected_folder_id": selection.get("folder_id") or "",
            "selected_thread_id": selection.get("thread_id") or "",
            "selected_tab_id": selection.get("tab_id") or "",
            "route_preview": selection.get("route_preview") or "",
            "draft_id": selected_draft_id or "",
            "message_intent": _norm(message_intent) or "draft_message",
            "secret_indicator_present": draft_secret,
            "blocker_count": len(list(dict.fromkeys(blocked_reasons))),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            **_blocked_effects(),
        },
        "current_route_state": current_route_state or {},
        "draft_preview": draft_preview or {},
        "drafts": drafts_after,
        "state_writes": {
            "route_state_written": route_state_written,
            "draft_written": draft_written,
            "written_paths": written_paths,
            "route_state_path": _rel(vault, route_path),
            "draft_state_path": _rel(vault, draft_path) if draft_path else None,
        },
        "secret_report": {
            "contains_secret": draft_secret,
            "redaction_count": int(secret_report["redaction_count"]) + int(title_secret_report["redaction_count"]),
            "indicator_categories": list(
                dict.fromkeys(
                    list(secret_report["indicator_categories"])
                    + list(title_secret_report["indicator_categories"])
                )
            ),
            "redacted_preview": str(secret_report["redacted_text"])[:240],
        },
        "authority": _authority(),
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "denied_by_this_surface": [
            "chat_message_send",
            "chat_transcript_write",
            "conversation_log_write",
            "discord_api_call",
            "discord_thread_create",
            "webhook_call",
            "agent_bus_task_write",
            "runtime_board_write",
            "runtime_dispatch",
            "schedule_mutation",
            "provider_api_call",
            "credential_value_display",
            "canonical_writeback",
        ],
        "readiness": {
            "phase11_chat_route_state_and_message_drafts_ready": True,
            "route_state_persistence_built": True,
            "message_draft_state_persistence_built": True,
            "message_intent_state_persistence_built": True,
            "route_state_root": ROUTE_STATE_DIR.as_posix(),
            "draft_state_root": DRAFT_STATE_DIR.as_posix(),
            "local_ui_state_write_allowed": True,
            "message_send_blocked": True,
            "chat_transcript_write_blocked": True,
            "conversation_log_write_blocked": True,
            "discord_api_call_blocked": True,
            "agent_bus_task_write_blocked": True,
            "runtime_board_write_blocked": True,
            "schedule_mutation_blocked": True,
            "provider_call_blocked": True,
            "credential_values_hidden": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }
