"""Local Studio Chat thread conversation state.

This module stores the native Studio Chat transcript that backs the product UI.
It is local Studio state only: no provider calls, no canonical memory mutation,
no Discord calls, and no runtime board writes happen here.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import STATE_ROOT, route_state_path, safe_state_id


SURFACE_ID = "phase11_chat_thread_conversations"
MODEL_VERSION = "studio.phase11_chat_thread_conversations.v1"
CONVERSATION_STATE_DIR = STATE_ROOT / "conversations"
CONVERSATION_FOLDER_STATE_DIR = STATE_ROOT / "conversation-folders"
CONVERSATION_ARCHIVE_DIR = STATE_ROOT / "conversations-archive"

DEFAULT_THREAD_BY_RUNTIME: dict[str, str] = {
    "hermes": "runtime-ops-hermes-chat",
    "openclaw": "runtime-ops-openclaw-chat",
    "claude-code": "runtime-ops-codex-patches",
    "codex": "runtime-ops-codex-patches",
}

RUNTIME_BY_RECIPIENT: dict[str, str] = {
    "hermes": "hermes",
    "openclaw": "openclaw",
    "archon": "claude-code",
    "codex": "codex",
}

SECRET_PATTERNS = [
    re.compile(r"\b[A-Z0-9_]*(?:API|TOKEN|SECRET|KEY|PASSWORD)[A-Z0-9_]*\s*=", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:seed phrase|private key|wallet key)\b", re.IGNORECASE),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_thread_id_for_runtime(runtime_id: str | None) -> str:
    runtime_key = str(runtime_id or "hermes").strip().lower()
    return DEFAULT_THREAD_BY_RUNTIME.get(runtime_key, DEFAULT_THREAD_BY_RUNTIME["hermes"])


def runtime_id_for_recipient(recipient: str | None) -> str:
    return RUNTIME_BY_RECIPIENT.get(str(recipient or "").strip().lower(), "hermes")


def conversation_state_path(vault: Path, thread_id: str) -> Path:
    safe_id = safe_state_id(thread_id, "thread")
    return vault / CONVERSATION_STATE_DIR / f"{safe_id}.json"


def conversation_folder_state_path(vault: Path, workspace_id: str, folder_id: str) -> Path:
    key = f"{safe_state_id(workspace_id, 'workspace')}__{safe_state_id(folder_id, 'folder')}"
    return vault / CONVERSATION_FOLDER_STATE_DIR / f"{key}.json"


def resolve_thread_id(thread_id: str | None, runtime_id: str | None = None) -> str:
    candidate = str(thread_id or "").strip()
    return candidate or default_thread_id_for_runtime(runtime_id)


def contains_secret_indicator(text: str | None) -> bool:
    value = str(text or "")
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def normalize_attachments(attachments: Any) -> list[dict[str, Any]]:
    if not isinstance(attachments, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(attachments[:12]):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("file_name") or f"attachment-{index + 1}").strip()
        kind = str(item.get("kind") or item.get("attachment_kind") or "file").strip().lower()
        mime = str(item.get("type") or item.get("mime_type") or "").strip()
        size = item.get("size") if isinstance(item.get("size"), int) else item.get("bytes")
        normalized.append(
            {
                "attachment_id": safe_state_id(item.get("attachment_id") or f"{kind}-{index + 1}", "attachment"),
                "name": name[:160] or f"attachment-{index + 1}",
                "kind": kind if kind in {"file", "image"} else "file",
                "mime_type": mime[:120],
                "size_bytes": int(size) if isinstance(size, int) and size >= 0 else None,
                "content_stored": False,
                "source_path_visible": False,
            }
        )
    return normalized


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _title_from_text(value: str | None, fallback: str = "New chat") -> str:
    text = " ".join(str(value or "").strip().split())
    return (text[:80] or fallback).strip()


def _slug(value: str | None, fallback: str) -> str:
    return safe_state_id(str(value or "").lower(), fallback)


def _runtime_display_id(runtime_id: str | None) -> str:
    runtime = str(runtime_id or "hermes").strip().lower()
    if runtime == "openclaw":
        return "OpenClaw"
    if runtime in {"claude-code", "codex"}:
        return "Codex"
    return "Hermes"


def _default_workspace_folder(runtime_id: str | None) -> tuple[str, str, str]:
    runtime = str(runtime_id or "hermes").strip().lower()
    if runtime == "openclaw":
        return "runtime-ops", "runtime-control", "Runtime Control"
    if runtime in {"claude-code", "codex"}:
        return "runtime-ops", "boards", "Boards"
    return "runtime-ops", "runtime-control", "Runtime Control"


def _relative(vault: Path, path: Path) -> str:
    return path.resolve().relative_to(vault.resolve()).as_posix()


def _iter_conversation_paths(vault: Path) -> list[Path]:
    root = vault / CONVERSATION_STATE_DIR
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def _folder_label_from_record(
    vault: Path,
    workspace_id: str,
    folder_id: str,
    fallback: str | None = None,
) -> str:
    path = conversation_folder_state_path(vault, workspace_id, folder_id)
    payload = _safe_json(path) if path.exists() else None
    if payload and payload.get("label"):
        return _title_from_text(payload.get("label"), fallback or folder_id.replace("-", " ").title())
    if folder_id == "runtime-control":
        return "Runtime Control"
    return _title_from_text(fallback or folder_id.replace("-", " ").title(), "Chats")


def _load_conversation(
    vault: Path,
    thread_id: str,
    *,
    runtime_id: str | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    folder_label: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    path = conversation_state_path(vault, thread_id)
    payload = _safe_json(path) or {}
    default_workspace, default_folder, default_folder_label = _default_workspace_folder(runtime_id)
    if not payload:
        payload = {
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "thread_id": thread_id,
            "created_at_utc": now_utc(),
            "messages": [],
        }
    payload.setdefault("thread_id", thread_id)
    payload.setdefault("messages", [])
    payload.setdefault("title", _title_from_text(title, thread_id.replace("-", " ").title()))
    payload.setdefault("workspace_id", safe_state_id(workspace_id, default_workspace))
    payload.setdefault("folder_id", safe_state_id(folder_id, default_folder))
    payload.setdefault("folder_label", _title_from_text(folder_label, default_folder_label))
    payload.setdefault("runtime_id", str(runtime_id or payload.get("runtime_id") or "hermes").strip().lower())
    payload.setdefault("runtime_label", _runtime_display_id(payload.get("runtime_id")))
    return payload


def _decorate_conversation(vault: Path, payload: dict[str, Any]) -> dict[str, Any]:
    thread_id = str(payload.get("thread_id") or "thread")
    messages = [item for item in payload.get("messages") or [] if isinstance(item, dict)]
    latest = messages[-1] if messages else {}
    out = dict(payload)
    out["messages"] = messages
    out["title"] = _title_from_text(out.get("title"), thread_id.replace("-", " ").title())
    out["workspace_id"] = safe_state_id(out.get("workspace_id"), "runtime-ops")
    out["folder_id"] = safe_state_id(out.get("folder_id"), "runtime-control")
    out["folder_label"] = _title_from_text(out.get("folder_label"), out["folder_id"].replace("-", " ").title())
    out["runtime_id"] = str(out.get("runtime_id") or "hermes").strip().lower()
    out["runtime_label"] = out.get("runtime_label") or _runtime_display_id(out["runtime_id"])
    out["message_count"] = len(messages)
    out["latest_message"] = latest
    out["latest_message_preview"] = str(latest.get("content") or "")[:180]
    out["last_message_at_utc"] = latest.get("created_at_utc") or payload.get("updated_at_utc")
    path = conversation_state_path(vault, thread_id)
    out["state_record_path"] = _relative(vault, path)
    out["native_state_persisted"] = path.exists()
    return out


def get_thread_conversation(vault_root: str | Path, thread_id: str) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    thread_id = resolve_thread_id(thread_id)
    payload = _load_conversation(vault, thread_id)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "conversation": _decorate_conversation(vault, payload),
    }


def _load_local_chat_folders(vault: Path) -> list[dict[str, Any]]:
    root = vault / CONVERSATION_FOLDER_STATE_DIR
    folders: list[dict[str, Any]] = []
    if not root.exists():
        return folders
    for path in sorted(root.glob("*.json")):
        payload = _safe_json(path)
        if not payload:
            continue
        workspace_id = safe_state_id(payload.get("workspace_id"), "runtime-ops")
        folder_id = safe_state_id(payload.get("folder_id"), "folder")
        folders.append(
            {
                **payload,
                "workspace_id": workspace_id,
                "folder_id": folder_id,
                "label": _title_from_text(payload.get("label"), folder_id.replace("-", " ").title()),
                "state_record_path": _relative(vault, path),
                "native_state_persisted": True,
                "local_conversation_folder": True,
                "local_state_only": True,
            }
        )
    return folders


def load_chat_thread_conversations(vault_root: str | Path) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    root = vault / CONVERSATION_STATE_DIR
    conversations: list[dict[str, Any]] = []
    if root.exists():
        for path in sorted(root.glob("*.json")):
            payload = _safe_json(path)
            if not payload:
                continue
            conversations.append(_decorate_conversation(vault, payload))
    conversations.sort(
        key=lambda item: str(item.get("last_message_at_utc") or item.get("updated_at_utc") or ""),
        reverse=True,
    )

    route_state = _safe_json(route_state_path(vault)) or {}
    folders_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for folder in _load_local_chat_folders(vault):
        folders_by_key[(str(folder.get("workspace_id") or ""), str(folder.get("folder_id") or ""))] = folder
    for conversation in conversations:
        workspace_id = safe_state_id(conversation.get("workspace_id"), "runtime-ops")
        folder_id = safe_state_id(conversation.get("folder_id"), "runtime-control")
        key = (workspace_id, folder_id)
        if key not in folders_by_key:
            folders_by_key[key] = {
                "surface": SURFACE_ID,
                "model_version": MODEL_VERSION,
                "workspace_id": workspace_id,
                "folder_id": folder_id,
                "label": _title_from_text(conversation.get("folder_label"), folder_id.replace("-", " ").title()),
                "local_conversation_folder": True,
                "local_state_only": True,
                "native_state_persisted": bool(conversation.get("native_state_persisted")),
                "state_record_path": conversation.get("state_record_path"),
            }
    message_count = sum(int(item.get("message_count") or 0) for item in conversations)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "state_root": CONVERSATION_STATE_DIR.as_posix(),
        "summary": {
            "conversation_count": len(conversations),
            "message_count": message_count,
            "selected_thread_id": route_state.get("thread_id") or "",
            "folder_count": len(folders_by_key),
            "local_conversation_store_ready": True,
            "canonical_memory_written": False,
            "provider_call_performed": False,
        },
        "folders": list(folders_by_key.values()),
        "conversations": conversations,
        "conversations_by_thread_id": {
            str(item.get("thread_id") or ""): item for item in conversations if item.get("thread_id")
        },
    }


def create_chat_folder(
    vault_root: str | Path,
    *,
    workspace_id: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    workspace_id = safe_state_id(workspace_id, "runtime-ops")
    clean_label = _title_from_text(label, "New folder")
    folder_id = _slug(clean_label, "folder")
    path = conversation_folder_state_path(vault, workspace_id, folder_id)
    if path.exists():
        suffix = 2
        while conversation_folder_state_path(vault, workspace_id, f"{folder_id}-{suffix}").exists():
            suffix += 1
        folder_id = f"{folder_id}-{suffix}"
        path = conversation_folder_state_path(vault, workspace_id, folder_id)
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "record_type": "local_chat_folder",
        "workspace_id": workspace_id,
        "folder_id": folder_id,
        "label": clean_label,
        "created_at_utc": now_utc(),
        "updated_at_utc": now_utc(),
        "local_state_only": True,
        "canonical_memory_written": False,
        "provider_call_performed": False,
    }
    _write_json(path, payload)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "folder": {
            **payload,
            "state_record_path": _relative(vault, path),
            "native_state_persisted": True,
        },
    }


def create_chat_thread_conversation(
    vault_root: str | Path,
    *,
    title: str | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    folder_label: str | None = None,
    runtime_id: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    runtime_id = str(runtime_id or "hermes").strip().lower()
    default_workspace, default_folder, default_folder_label = _default_workspace_folder(runtime_id)
    workspace_id = safe_state_id(workspace_id, default_workspace)
    folder_id = safe_state_id(folder_id, default_folder)
    clean_title = _title_from_text(title, "New chat")
    clean_folder_label = _title_from_text(folder_label, default_folder_label)
    thread_base = safe_state_id(f"{workspace_id}-{folder_id}-{clean_title}".lower(), "chat-thread")
    thread_id = thread_base
    path = conversation_state_path(vault, thread_id)
    if path.exists():
        suffix = 2
        while conversation_state_path(vault, f"{thread_base}-{suffix}").exists():
            suffix += 1
        thread_id = f"{thread_base}-{suffix}"
        path = conversation_state_path(vault, thread_id)
    payload = _load_conversation(
        vault,
        thread_id,
        runtime_id=runtime_id,
        workspace_id=workspace_id,
        folder_id=folder_id,
        folder_label=clean_folder_label,
        title=clean_title,
    )
    payload["created_at_utc"] = payload.get("created_at_utc") or now_utc()
    payload["updated_at_utc"] = now_utc()
    payload["local_state_only"] = True
    payload["canonical_memory_written"] = False
    payload["provider_call_performed"] = False
    _write_json(path, payload)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "thread_id": thread_id,
        "conversation": _decorate_conversation(vault, payload),
    }


def rename_chat_folder(
    vault_root: str | Path,
    *,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    workspace_id = safe_state_id(workspace_id, "runtime-ops")
    folder_id = safe_state_id(folder_id, "runtime-control")
    clean_label = _title_from_text(label, "")
    if not clean_label:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "blocked_reason": "folder_label_required",
            "workspace_id": workspace_id,
            "folder_id": folder_id,
        }

    path = conversation_folder_state_path(vault, workspace_id, folder_id)
    now = now_utc()
    payload = _safe_json(path) if path.exists() else None
    if not payload:
        payload = {
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "record_type": "local_chat_folder",
            "workspace_id": workspace_id,
            "folder_id": folder_id,
            "created_at_utc": now,
            "local_state_only": True,
            "canonical_memory_written": False,
            "provider_call_performed": False,
        }
    payload.update(
        {
            "workspace_id": workspace_id,
            "folder_id": folder_id,
            "label": clean_label,
            "updated_at_utc": now,
            "local_state_only": True,
            "canonical_memory_written": False,
            "provider_call_performed": False,
        }
    )
    _write_json(path, payload)

    updated_threads = 0
    for conversation_path in _iter_conversation_paths(vault):
        conversation = _safe_json(conversation_path)
        if not conversation:
            continue
        if str(conversation.get("workspace_id") or "") != workspace_id:
            continue
        if str(conversation.get("folder_id") or "") != folder_id:
            continue
        conversation["folder_label"] = clean_label
        conversation["updated_at_utc"] = now
        _write_json(conversation_path, conversation)
        updated_threads += 1

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "updated_thread_count": updated_threads,
        "folder": {
            **payload,
            "state_record_path": _relative(vault, path),
            "native_state_persisted": True,
        },
    }


def delete_chat_folder(
    vault_root: str | Path,
    *,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    move_threads_to_folder_id: str | None = None,
    move_threads_to_folder_label: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    workspace_id = safe_state_id(workspace_id, "runtime-ops")
    folder_id = safe_state_id(folder_id, "runtime-control")
    if folder_id == "runtime-control":
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "blocked_reason": "default_chat_folder_protected",
            "workspace_id": workspace_id,
            "folder_id": folder_id,
        }

    target_folder_id = safe_state_id(move_threads_to_folder_id, "runtime-control")
    target_folder_label = _folder_label_from_record(
        vault,
        workspace_id,
        target_folder_id,
        move_threads_to_folder_label,
    )
    now = now_utc()
    moved_threads = 0
    for conversation_path in _iter_conversation_paths(vault):
        conversation = _safe_json(conversation_path)
        if not conversation:
            continue
        if str(conversation.get("workspace_id") or "") != workspace_id:
            continue
        if str(conversation.get("folder_id") or "") != folder_id:
            continue
        conversation["folder_id"] = target_folder_id
        conversation["folder_label"] = target_folder_label
        conversation["updated_at_utc"] = now
        conversation["local_state_only"] = True
        _write_json(conversation_path, conversation)
        moved_threads += 1

    path = conversation_folder_state_path(vault, workspace_id, folder_id)
    folder_deleted = False
    if path.exists():
        path.unlink()
        folder_deleted = True

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "workspace_id": workspace_id,
        "folder_id": folder_id,
        "folder_deleted": folder_deleted,
        "moved_thread_count": moved_threads,
        "moved_to_folder_id": target_folder_id,
        "moved_to_folder_label": target_folder_label,
        "canonical_memory_written": False,
        "provider_call_performed": False,
    }


def move_chat_thread(
    vault_root: str | Path,
    *,
    thread_id: str | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    folder_label: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    resolved_thread_id = resolve_thread_id(thread_id, None)
    path = conversation_state_path(vault, resolved_thread_id)
    payload = _safe_json(path) if path.exists() else None
    if not payload:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "blocked_reason": "thread_not_found",
            "thread_id": resolved_thread_id,
        }
    target_workspace_id = safe_state_id(workspace_id or payload.get("workspace_id"), "runtime-ops")
    target_folder_id = safe_state_id(folder_id, "runtime-control")
    target_folder_label = _title_from_text(
        folder_label or _folder_label_from_record(vault, target_workspace_id, target_folder_id),
        target_folder_id.replace("-", " ").title(),
    )
    payload["workspace_id"] = target_workspace_id
    payload["folder_id"] = target_folder_id
    payload["folder_label"] = target_folder_label
    payload["updated_at_utc"] = now_utc()
    payload["local_state_only"] = True
    payload["canonical_memory_written"] = False
    payload["provider_call_performed"] = False
    _write_json(path, payload)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "thread_id": resolved_thread_id,
        "conversation": _decorate_conversation(vault, payload),
    }


def delete_chat_thread(
    vault_root: str | Path,
    *,
    thread_id: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    resolved_thread_id = resolve_thread_id(thread_id, None)
    path = conversation_state_path(vault, resolved_thread_id)
    payload = _safe_json(path) if path.exists() else None
    if not payload:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "blocked_reason": "thread_not_found",
            "thread_id": resolved_thread_id,
        }
    archived_at = now_utc()
    archive_stamp = archived_at.replace(":", "").replace("-", "")
    payload["archived_at_utc"] = archived_at
    payload["archive_reason"] = "studio_chat_delete"
    payload["local_state_only"] = True
    payload["canonical_memory_written"] = False
    payload["provider_call_performed"] = False
    archive_dir = vault / CONVERSATION_ARCHIVE_DIR
    archive_path = archive_dir / f"{resolved_thread_id}-{archive_stamp}.json"
    suffix = 2
    while archive_path.exists():
        archive_path = archive_dir / f"{resolved_thread_id}-{archive_stamp}-{suffix}.json"
        suffix += 1
    _write_json(archive_path, payload)
    path.unlink()
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "thread_id": resolved_thread_id,
        "active_record_deleted": True,
        "archived_record_path": _relative(vault, archive_path),
        "canonical_memory_written": False,
        "provider_call_performed": False,
    }


def append_chat_thread_message(
    vault_root: str | Path,
    *,
    thread_id: str | None,
    role: str,
    content: str,
    runtime_id: str | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    folder_label: str | None = None,
    title: str | None = None,
    session_id: str | None = None,
    task_id: str | None = None,
    message_id: str | None = None,
    attachments: Any = None,
    status: str = "saved",
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    resolved_thread_id = resolve_thread_id(thread_id, runtime_id)
    content = str(content or "").strip()
    if not content:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "blocked_reason": "message_required",
            "thread_id": resolved_thread_id,
        }
    if contains_secret_indicator(content):
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "blocked_reason": "secret_or_credential_indicator_present",
            "thread_id": resolved_thread_id,
        }

    path = conversation_state_path(vault, resolved_thread_id)
    payload = _load_conversation(
        vault,
        resolved_thread_id,
        runtime_id=runtime_id,
        workspace_id=workspace_id,
        folder_id=folder_id,
        folder_label=folder_label,
        title=title,
    )
    messages = [item for item in payload.get("messages") or [] if isinstance(item, dict)]
    effective_message_id = message_id or f"msg-{uuid.uuid4().hex[:16]}"
    existing = next((item for item in messages if item.get("message_id") == effective_message_id), None)
    if existing:
        existing.update(
            {
                "content": content,
                "status": status,
                "updated_at_utc": now_utc(),
            }
        )
        message_created = False
    else:
        messages.append(
            {
                "message_id": effective_message_id,
                "role": str(role or "message").strip().lower() or "message",
                "content": content,
                "runtime_id": str(runtime_id or "").strip().lower(),
                "session_id": session_id or payload.get("session_id") or "",
                "task_id": task_id or "",
                "status": status,
                "created_at_utc": now_utc(),
                "attachments": normalize_attachments(attachments),
            }
        )
        message_created = True

    payload["messages"] = messages
    payload["session_id"] = session_id or payload.get("session_id") or ""
    payload["runtime_id"] = str(runtime_id or payload.get("runtime_id") or "").strip().lower()
    payload["runtime_label"] = _runtime_display_id(payload.get("runtime_id"))
    payload["workspace_id"] = safe_state_id(workspace_id or payload.get("workspace_id"), "runtime-ops")
    payload["folder_id"] = safe_state_id(folder_id or payload.get("folder_id"), "runtime-control")
    payload["folder_label"] = _title_from_text(folder_label or payload.get("folder_label"), payload["folder_id"].replace("-", " ").title())
    if title:
        payload["title"] = _title_from_text(title, payload.get("title") or "New chat")
    elif not payload.get("title") and messages:
        payload["title"] = _title_from_text(messages[0].get("content"), "New chat")
    payload["updated_at_utc"] = now_utc()
    payload["last_task_id"] = task_id or payload.get("last_task_id") or ""
    payload["local_state_only"] = True
    payload["canonical_memory_written"] = False
    payload["provider_call_performed"] = False

    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, payload)

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "thread_id": resolved_thread_id,
        "message_id": effective_message_id,
        "message_created": message_created,
        "state_record_path": _relative(vault, path),
        "conversation": _decorate_conversation(vault, payload),
    }
