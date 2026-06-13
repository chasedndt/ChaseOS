"""Native Studio Chat state helpers.

This module owns the small file-backed state model used by Phase 11 Chat target
execution. It is local Studio state only. It is not Discord transport state,
Agent Bus state, runtime board state, schedule state, provider state, or
canonical memory.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


STATE_ROOT = Path("runtime/studio/chat/native-state")
WORKSPACE_STATE_DIR = STATE_ROOT / "workspaces"
FOLDER_STATE_DIR = STATE_ROOT / "folders"
THREAD_STATE_DIR = STATE_ROOT / "threads"
ROUTE_STATE_DIR = STATE_ROOT / "route-state"
DRAFT_STATE_DIR = STATE_ROOT / "drafts"
CURRENT_ROUTE_STATE_FILE = ROUTE_STATE_DIR / "current.json"


def safe_state_id(value: str | None, fallback: str = "state") -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip()).strip("-")
    return (text or fallback)[:96] or fallback


def workspace_state_path(vault: Path, workspace_id: str) -> Path:
    return vault / WORKSPACE_STATE_DIR / f"{safe_state_id(workspace_id, 'workspace')}.json"


def folder_state_path(vault: Path, workspace_id: str, folder_id: str) -> Path:
    key = f"{safe_state_id(workspace_id, 'workspace')}__{safe_state_id(folder_id, 'folder')}"
    return vault / FOLDER_STATE_DIR / f"{key}.json"


def thread_state_path(vault: Path, thread_id: str) -> Path:
    return vault / THREAD_STATE_DIR / f"{safe_state_id(thread_id, 'thread')}.json"


def route_state_path(vault: Path) -> Path:
    return vault / CURRENT_ROUTE_STATE_FILE


def draft_state_path(vault: Path, draft_id: str) -> Path:
    return vault / DRAFT_STATE_DIR / f"{safe_state_id(draft_id, 'draft')}.json"


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_records(vault: Path, rel_dir: Path) -> list[dict[str, Any]]:
    root = vault / rel_dir
    if not root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        payload = _safe_json(path)
        if not payload:
            continue
        payload = dict(payload)
        payload["state_record_path"] = path.resolve().relative_to(vault.resolve()).as_posix()
        payload["native_state_persisted"] = True
        records.append(payload)
    return records


def load_native_chat_state(vault_root: str | Path) -> dict[str, Any]:
    """Read native Studio Chat state records without side effects."""

    vault = Path(vault_root).resolve()
    workspaces = _load_records(vault, WORKSPACE_STATE_DIR)
    folders = _load_records(vault, FOLDER_STATE_DIR)
    threads = _load_records(vault, THREAD_STATE_DIR)
    route_state = _safe_json(route_state_path(vault))
    if route_state:
        route_state = dict(route_state)
        route_state["state_record_path"] = route_state_path(vault).resolve().relative_to(vault.resolve()).as_posix()
        route_state["native_state_persisted"] = True
    drafts = _load_records(vault, DRAFT_STATE_DIR)
    return {
        "state_root": STATE_ROOT.as_posix(),
        "workspaces": workspaces,
        "folders": folders,
        "threads": threads,
        "route_state": route_state or {},
        "drafts": drafts,
        "workspace_count": len(workspaces),
        "folder_count": len(folders),
        "thread_count": len(threads),
        "route_state_persisted": bool(route_state),
        "draft_count": len(drafts),
        "record_count": len(workspaces) + len(folders) + len(threads),
        "local_ui_state_count": (1 if route_state else 0) + len(drafts),
    }
