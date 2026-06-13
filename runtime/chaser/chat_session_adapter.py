"""
runtime.chaser.chat_session_adapter

Adapter from Studio Chat native-state conversations to Chaser SessionRecord.

This is the N4 bridge: it reads existing Studio chat state, attaches selected
terminal audit records by safe run id, and can call the governed session export
backend. It performs no provider calls, no command execution, no Agent Bus
writes, and no canonical memory mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from runtime.chaser.exports import export_session
from runtime.chaser.models import SessionMessage, SessionRecord, TerminalRun, UNTRUSTED_TIER
from runtime.operator_surface import terminal_runs


CHAT_CONVERSATIONS_REL = Path("runtime") / "studio" / "chat" / "native-state" / "conversations"


class ChatSessionAdapterError(RuntimeError):
    """Raised when a Studio chat cannot be converted safely."""


def _safe_id(value: str, label: str) -> str:
    safe = (value or "").strip()
    if not safe:
        raise ChatSessionAdapterError(f"{label} is empty")
    if any(ch in safe for ch in ("/", "\\", "..")) or Path(safe).name != safe:
        raise ChatSessionAdapterError(f"unsafe {label}: {value!r}")
    return safe


def _conversation_path(vault_root: str | Path, thread_id: str) -> Path:
    safe_thread = _safe_id(thread_id, "thread_id")
    return Path(vault_root).resolve() / CHAT_CONVERSATIONS_REL / f"{safe_thread}.json"


def _load_conversation(vault_root: str | Path, thread_id: str) -> dict:
    path = _conversation_path(vault_root, thread_id)
    if not path.exists():
        raise ChatSessionAdapterError(f"no Studio chat conversation for thread_id {thread_id!r}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChatSessionAdapterError(f"unable to read Studio chat conversation {thread_id!r}: {exc}") from exc
    if not isinstance(data, dict):
        raise ChatSessionAdapterError("Studio chat conversation must be a JSON object")
    payload_thread = str(data.get("thread_id") or thread_id).strip()
    if payload_thread != _safe_id(thread_id, "thread_id"):
        raise ChatSessionAdapterError(
            f"Studio chat payload thread_id {payload_thread!r} does not match requested thread_id"
        )
    return data


def _message_from_chat(item: dict) -> SessionMessage:
    return SessionMessage(
        role=str(item.get("role") or "unknown"),
        content=str(item.get("content") or ""),
        timestamp=str(item.get("created_at_utc") or item.get("timestamp") or ""),
    )


def _terminal_from_audit(record: dict) -> TerminalRun:
    run_id = _safe_id(str(record.get("run_id") or ""), "run_id")
    audit_paths = record.get("audit_paths") if isinstance(record.get("audit_paths"), dict) else {}
    exit_code = record.get("exit_code")
    return TerminalRun(
        run_id=run_id,
        command=str(record.get("command") or ""),
        cwd=str(record.get("cwd") or ""),
        classification=str(record.get("classification") or ""),
        blocked=not bool(record.get("allowed", False)),
        returncode=int(exit_code) if isinstance(exit_code, (int, float)) else None,
        stdout_excerpt=str(record.get("stdout_excerpt") or ""),
        stderr_excerpt=str(record.get("stderr_excerpt") or ""),
        trust_tier=str(record.get("trust_state") or UNTRUSTED_TIER),
        audit_id=str(audit_paths.get("json") or record.get("audit_id") or run_id),
    )


def _load_terminal_runs(vault_root: str | Path, run_ids: Iterable[str]) -> tuple[TerminalRun, ...]:
    attached: list[TerminalRun] = []
    for run_id in run_ids:
        detail = terminal_runs.load_terminal_run_detail(vault_root, run_id)
        if not detail.get("ok"):
            err = detail.get("error") or {}
            raise ChatSessionAdapterError(
                f"terminal run {run_id!r} could not be attached: {err.get('code') or 'unknown'}"
            )
        attached.append(_terminal_from_audit(detail["record"]))
    return tuple(attached)


def build_session_record_from_studio_chat(
    vault_root: str | Path,
    thread_id: str,
    *,
    terminal_run_ids: Iterable[str] = (),
) -> SessionRecord:
    """Build a Chaser SessionRecord from an existing Studio chat thread."""

    conversation = _load_conversation(vault_root, thread_id)
    safe_thread = _safe_id(thread_id, "thread_id")
    raw_session_id = str(conversation.get("session_id") or f"chat-session-{safe_thread}").strip()
    session_id = _safe_id(raw_session_id, "session_id")
    messages = tuple(
        _message_from_chat(item)
        for item in (conversation.get("messages") or [])
        if isinstance(item, dict)
    )
    return SessionRecord(
        session_id=session_id,
        title=str(conversation.get("title") or safe_thread),
        runtime=str(conversation.get("runtime_id") or ""),
        profile="studio-chat",
        model="",
        provider="",
        created_at=str(conversation.get("created_at_utc") or ""),
        updated_at=str(conversation.get("updated_at_utc") or ""),
        pinned=False,
        messages=messages,
        terminal_runs=_load_terminal_runs(vault_root, terminal_run_ids),
    )


def export_studio_chat_session(
    vault_root: str | Path,
    thread_id: str,
    *,
    fmt: str = "markdown",
    actor: str = "operator",
    terminal_run_ids: Iterable[str] = (),
) -> dict:
    """Export an existing Studio chat thread through the Chaser export backend."""

    try:
        record = build_session_record_from_studio_chat(
            vault_root,
            thread_id,
            terminal_run_ids=terminal_run_ids,
        )
        result = export_session(vault_root, record.session_id, fmt=fmt, actor=actor, session=record)
    except (ChatSessionAdapterError, RuntimeError, ValueError, OSError) as exc:
        return {
            "ok": False,
            "thread_id": thread_id,
            "error": {"code": "chat_session_adapter_failed", "message": str(exc)},
            "authority": authority_flags(),
        }
    result.update({
        "thread_id": thread_id,
        "terminal_run_ids": list(terminal_run_ids),
        "terminal_run_count": len(record.terminal_runs),
        "message_count": len(record.messages),
        "authority": authority_flags(),
    })
    return result


def authority_flags() -> dict:
    return {
        "provider_calls": False,
        "terminal_execution": False,
        "studio_execution": False,
        "agent_bus_writes": False,
        "approval_consumption": False,
        "canonical_memory_write": False,
        "external_upload": False,
    }
