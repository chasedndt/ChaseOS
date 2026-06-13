"""
runtime.chaser.sessions

Local JSON session store for ChaserAgent sessions.

Session records are evidence/operator state. Metadata lifecycle writes are
bounded to pin/unpin, rename, and archive-first removal from the active session
store. These writes do not promote session content to canonical ChaseOS truth.

Sessions live under:

    <vault_root>/07_LOGS/Chaser-Sessions/<session_id>.json

This is operator/evidence state, not canonical vault truth.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from runtime.chaser.models import SessionRecord

SESSION_STORE_REL = Path("07_LOGS") / "Chaser-Sessions"
SESSION_AUDIT_SUBDIR = "_audit"
SESSION_ARCHIVE_SUBDIR = "_archive"
MAX_SESSION_TITLE_LEN = 160


class SessionNotFoundError(LookupError):
    """Raised when a requested session_id has no stored record."""


class SessionStoreError(RuntimeError):
    """Raised when a session record exists but cannot be read/parsed."""


def _safe_session_id(session_id: str) -> str:
    """Reject path-traversal / separator characters in a session id."""
    sid = (session_id or "").strip()
    if not sid:
        raise SessionStoreError("session_id is empty")
    if any(ch in sid for ch in ("/", "\\", "..")) or Path(sid).name != sid:
        raise SessionStoreError(f"unsafe session_id: {session_id!r}")
    return sid


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalize_title(title: str) -> str:
    normalized = (title or "").strip()
    if not normalized:
        raise SessionStoreError("session title is empty")
    if len(normalized) > MAX_SESSION_TITLE_LEN:
        raise SessionStoreError(f"session title exceeds {MAX_SESSION_TITLE_LEN} characters")
    if any(ord(ch) < 32 for ch in normalized):
        raise SessionStoreError("session title contains control characters")
    return normalized


def _read_session_payload(vault_root: str | Path, session_id: str) -> tuple[Path, dict, SessionRecord]:
    safe_id = _safe_session_id(session_id)
    path = session_store_dir(vault_root) / f"{safe_id}.json"
    if not path.exists():
        raise SessionNotFoundError(f"no session record for id {session_id!r} at {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionStoreError(f"unable to read session {session_id!r}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SessionStoreError(f"invalid session record {session_id!r}: session record must be a JSON object")
    try:
        record = SessionRecord.from_dict(raw)
    except ValueError as exc:
        raise SessionStoreError(f"invalid session record {session_id!r}: {exc}") from exc
    if record.session_id != safe_id:
        raise SessionStoreError(
            f"invalid session record {session_id!r}: payload session_id {record.session_id!r} does not match path id"
        )
    return path, raw, record


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _audit_dir(vault_root: str | Path) -> Path:
    return session_store_dir(vault_root) / SESSION_AUDIT_SUBDIR


def _archive_dir(vault_root: str | Path) -> Path:
    return session_store_dir(vault_root) / SESSION_ARCHIVE_SUBDIR


def _metadata(record: SessionRecord) -> dict:
    return {
        "session_id": record.session_id,
        "title": record.title,
        "runtime": record.runtime,
        "pinned": record.pinned,
        "updated_at": record.updated_at,
        "message_count": len(record.messages),
        "tool_run_count": len(record.tool_runs),
        "terminal_run_count": len(record.terminal_runs),
        "artifact_count": len(record.artifacts),
    }


def _write_lifecycle_audit(
    vault_root: str | Path,
    *,
    action: str,
    actor: str,
    before: SessionRecord,
    after: SessionRecord | None,
    active_path: Path,
    archive_path: Path | None = None,
    emit_audit: Callable[[dict], None] | None = None,
) -> Path:
    audit_dir = _audit_dir(vault_root)
    stamp = _stamp()
    audit_path = audit_dir / f"{stamp}-{before.session_id}-{action}.json"
    counter = 1
    while audit_path.exists():
        audit_path = audit_dir / f"{stamp}-{before.session_id}-{action}-{counter}.json"
        counter += 1
    audit_record = {
        "event": "session_lifecycle",
        "action": action,
        "actor": actor,
        "session_id": before.session_id,
        "timestamp": _now_iso(),
        "active_path": str(active_path),
        "archive_path": str(archive_path) if archive_path else "",
        "before": _metadata(before),
        "after": _metadata(after) if after else None,
        "hard_delete_performed": False,
        "canonical_writeback_performed": False,
        "external_upload_performed": False,
        "authority": {
            "metadata_write": True,
            "session_content_mutated": False,
            "canonical_truth_mutated": False,
            "provider_calls": False,
            "terminal_execution": False,
        },
    }
    _write_json_atomic(audit_path, audit_record)
    if emit_audit is not None:
        emit_audit(audit_record)
    return audit_path


def session_store_dir(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve() / SESSION_STORE_REL


def session_path(vault_root: str | Path, session_id: str) -> Path:
    return session_store_dir(vault_root) / f"{_safe_session_id(session_id)}.json"


def load_session(vault_root: str | Path, session_id: str) -> SessionRecord:
    """Load a single session record.

    Raises:
        SessionNotFoundError: no record file for this id.
        SessionStoreError: record exists but is unreadable/invalid.
    """
    return _read_session_payload(vault_root, session_id)[2]


def list_sessions(vault_root: str | Path) -> list[dict]:
    """Return lightweight metadata for every stored session (fail-open).

    Unreadable individual records are skipped, not fatal.
    """
    store = session_store_dir(vault_root)
    if not store.exists():
        return []
    summaries: list[dict] = []
    for path in sorted(store.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            record = SessionRecord.from_dict(raw)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        summaries.append(
            {
                "session_id": record.session_id,
                "title": record.title,
                "runtime": record.runtime,
                "pinned": record.pinned,
                "updated_at": record.updated_at,
                "message_count": len(record.messages),
            }
        )
    return summaries


def set_session_pinned(
    vault_root: str | Path,
    session_id: str,
    pinned: bool,
    *,
    actor: str = "operator",
    emit_audit: Callable[[dict], None] | None = None,
) -> dict:
    """Set a session's pinned metadata flag and write lifecycle audit."""
    path, raw, before = _read_session_payload(vault_root, session_id)
    raw["pinned"] = bool(pinned)
    raw["updated_at"] = _now_iso()
    after = SessionRecord.from_dict(raw)
    _write_json_atomic(path, raw)
    audit_path = _write_lifecycle_audit(
        vault_root,
        action="pin" if pinned else "unpin",
        actor=actor,
        before=before,
        after=after,
        active_path=path,
        emit_audit=emit_audit,
    )
    return {
        "ok": True,
        "action": "pin" if pinned else "unpin",
        "session_id": after.session_id,
        "pinned": after.pinned,
        "active_path": str(path),
        "audit_path": str(audit_path),
        "hard_delete_performed": False,
        "canonical_writeback_performed": False,
        "external_upload_performed": False,
    }


def rename_session(
    vault_root: str | Path,
    session_id: str,
    title: str,
    *,
    actor: str = "operator",
    emit_audit: Callable[[dict], None] | None = None,
) -> dict:
    """Rename a session title as metadata and write lifecycle audit."""
    path, raw, before = _read_session_payload(vault_root, session_id)
    raw["title"] = _normalize_title(title)
    raw["updated_at"] = _now_iso()
    after = SessionRecord.from_dict(raw)
    _write_json_atomic(path, raw)
    audit_path = _write_lifecycle_audit(
        vault_root,
        action="rename",
        actor=actor,
        before=before,
        after=after,
        active_path=path,
        emit_audit=emit_audit,
    )
    return {
        "ok": True,
        "action": "rename",
        "session_id": after.session_id,
        "title": after.title,
        "active_path": str(path),
        "audit_path": str(audit_path),
        "hard_delete_performed": False,
        "canonical_writeback_performed": False,
        "external_upload_performed": False,
    }


def archive_session(
    vault_root: str | Path,
    session_id: str,
    *,
    actor: str = "operator",
    reason: str = "",
    emit_audit: Callable[[dict], None] | None = None,
) -> dict:
    """Archive a session out of the active store without hard-deleting it.

    This is the N3 archive-first delete lifecycle. The active session JSON is
    moved into `_archive/<YYYY-MM-DD>/`; no file is unlinked and no canonical
    ChaseOS truth is mutated.
    """
    path, raw, before = _read_session_payload(vault_root, session_id)
    archived_at = _now_iso()
    raw["archived_at"] = archived_at
    raw["archive_reason"] = (reason or "").strip()
    raw["updated_at"] = archived_at
    archive_root = _archive_dir(vault_root) / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_path = archive_root / f"{before.session_id}-{_stamp()}.json"
    counter = 1
    while archive_path.exists():
        archive_path = archive_root / f"{before.session_id}-{_stamp()}-{counter}.json"
        counter += 1
    _write_json_atomic(path, raw)
    shutil.move(str(path), str(archive_path))
    audit_path = _write_lifecycle_audit(
        vault_root,
        action="archive",
        actor=actor,
        before=before,
        after=None,
        active_path=path,
        archive_path=archive_path,
        emit_audit=emit_audit,
    )
    return {
        "ok": True,
        "action": "archive",
        "session_id": before.session_id,
        "active_path": str(path),
        "archive_path": str(archive_path),
        "audit_path": str(audit_path),
        "hard_delete_performed": False,
        "canonical_writeback_performed": False,
        "external_upload_performed": False,
    }
