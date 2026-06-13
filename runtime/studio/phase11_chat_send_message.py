"""Phase 11 Chat — send to any runtime via Agent Bus.

The recipient is determined by the caller's selected runtime adapter (runtime_id).
No approval workflow is required for sending a chat message.

Architecture:
  Studio Chat sends message with selected runtime_id
    → _resolve_recipient(runtime_id) → Agent Bus recipient name
    → create_task(recipient=..., task_type hint="chat")
    → Runtime watch loop claims and dispatches _dispatch_chat
    → Runtime posts result_attached event on Agent Bus
    → Studio polls poll_chat_result and shows result card

The Studio surface does NOT call any LLM provider directly on this path.
Each runtime uses whatever model/provider it is configured with in its own environment.
OPENAI_API_KEY is only needed for the direct-provider fallback path
(Studio → provider directly, bypassing all runtimes).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import list_tasks, list_events
from runtime.studio.agent_bus_client import (
    DEFAULT_RUNTIME_ID_TO_RECIPIENT,
    StudioAgentBusClient,
    load_recipient_map,
    resolve_recipient,
)
from runtime.studio.phase11_chat_thread_conversations import (
    append_chat_thread_message,
    contains_secret_indicator,
    default_thread_id_for_runtime,
    normalize_attachments,
    resolve_thread_id,
    runtime_id_for_recipient,
)


MODEL_VERSION = "studio.phase11_chat_send_message.v2"
SURFACE_ID = "phase11_chat_send_message"

# Studio Chat runs within the Codex (Claude Code) runtime context.
_SENDER = "Codex"
_TASK_INTENT = "TASK"
_TASK_PRIORITY = "normal"

# Default routing map: companion_id → Agent Bus recipient name.
# Routing lives in runtime.studio.agent_bus_client so Chat and future Studio
# runtime-bound surfaces share one passive Agent Bus client seam.
_DEFAULT_RUNTIME_ID_TO_RECIPIENT = DEFAULT_RUNTIME_ID_TO_RECIPIENT
_load_recipient_map = load_recipient_map


def _resolve_recipient(runtime_id: str, vault: Path) -> str:
    """Backward-compatible wrapper for tests/importers."""
    return resolve_recipient(vault, runtime_id)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _make_session_id() -> str:
    return f"chat-{str(uuid.uuid4())[:16]}"


def send_chat_message(
    vault_root: str | Path,
    message: str,
    *,
    session_id: str | None = None,
    context_hint: str | None = None,
    runtime_id: str = "hermes",
    thread_id: str | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    folder_label: str | None = None,
    title: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Send a chat message to a runtime via Agent Bus. Returns task metadata.

    Args:
        vault_root: Vault root directory.
        message: The user's chat message text.
        session_id: Optional session ID for grouping related messages.
        context_hint: Optional hint for the runtime about the context.
        runtime_id: Companion/runtime ID to route to (hermes, openclaw, claude-code).
        thread_id: Native Studio Chat thread to persist the local transcript under.
        workspace_id: Optional local Studio Chat workspace metadata.
        folder_id: Optional local Studio Chat folder metadata.
        folder_label: Optional local Studio Chat folder label metadata.
        title: Optional local Studio Chat thread title.
        attachments: Optional attachment metadata. File bytes are not copied or uploaded.

    Returns:
        Dict with ok, task_id, session_id, status, and surface fields.
        ok=False if the task could not be created (bus error).
    """
    vault = Path(vault_root).resolve()
    sid = session_id or _make_session_id()
    message = (message or "").strip()
    runtime_id = str(runtime_id or "hermes").strip().lower()
    resolved_thread_id = resolve_thread_id(thread_id, runtime_id)
    normalized_attachments = normalize_attachments(attachments or [])

    # N-4: enforce message size cap to prevent resource abuse
    _MAX_MESSAGE_BYTES = 16_000  # ~4k tokens; well within context but stops runaway payloads
    if not message:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "session_id": sid,
            "task_id": None,
            "status": "BLOCKED / EMPTY MESSAGE",
            "blocked_reason": "message_required",
        }
    if len(message.encode("utf-8")) > _MAX_MESSAGE_BYTES:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "session_id": sid,
            "task_id": None,
            "status": f"BLOCKED / MESSAGE TOO LARGE (max {_MAX_MESSAGE_BYTES} bytes)",
            "blocked_reason": "message_too_large",
        }
    if contains_secret_indicator(message):
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "session_id": sid,
            "thread_id": resolved_thread_id,
            "task_id": None,
            "status": "BLOCKED / SECRET-LIKE TEXT",
            "blocked_reason": "secret_or_credential_indicator_present",
        }

    recipient = _resolve_recipient(runtime_id, vault)

    notes_lines = [
        "task_type: chat",
        f"session_id: {sid}",
        f"thread_id: {resolved_thread_id}",
        "source_surface: studio_chat",
    ]
    if normalized_attachments:
        notes_lines.append(f"attachment_count: {len(normalized_attachments)}")
    if context_hint:
        notes_lines.append(f"context_hint: {context_hint}")
    notes = "\n".join(notes_lines)

    try:
        client = StudioAgentBusClient(vault, sender=_SENDER)
        result_packet = client.create_task(
            runtime_id=runtime_id,
            request=message,
            expected_output="chat-response",
            notes=notes,
            intent=_TASK_INTENT,
            priority=_TASK_PRIORITY,
        )
        result = result_packet["agent_bus_result"]
    except Exception as exc:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "session_id": sid,
            "task_id": None,
            "status": "FAILED / BUS ERROR",
            "blocked_reason": f"bus_create_failed:{str(exc)[:120]}",
        }

    if not result.get("created"):
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "session_id": sid,
            "task_id": None,
            "status": "BLOCKED / TASK NOT CREATED",
            "blocked_reason": result.get("reason", "unknown"),
        }

    conversation_result = append_chat_thread_message(
        vault,
        thread_id=resolved_thread_id,
        role="user",
        content=message,
        runtime_id=runtime_id,
        workspace_id=workspace_id,
        folder_id=folder_id,
        folder_label=folder_label,
        title=title,
        session_id=sid,
        task_id=result["task_id"],
        attachments=normalized_attachments,
        status="queued",
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "session_id": sid,
        "thread_id": resolved_thread_id,
        "workspace_id": workspace_id or "",
        "folder_id": folder_id or "",
        "task_id": result["task_id"],
        "status": f"SENT / AWAITING {recipient.upper()}",
        "generated_at_utc": _now_utc(),
        "recipient": recipient,
        "priority": _TASK_PRIORITY,
        "message_preview": message[:200],
        "attachment_count": len(normalized_attachments),
        "conversation_persisted": bool(conversation_result.get("ok")),
        "conversation_path": conversation_result.get("state_record_path"),
        "conversation_message_id": conversation_result.get("message_id"),
        "authority": {
            "selected_runtime_id": runtime_id,
            "provider_call_performed": False,
            "runtime_dispatch_via_agent_bus": True,
            "runtime_owns_llm_credentials": True,
            "local_conversation_state_written": bool(conversation_result.get("ok")),
            "canonical_mutation_performed": False,
        },
    }


def _note_value(notes: str | None, key: str) -> str | None:
    prefix = f"{key}:"
    for line in str(notes or "").splitlines():
        if line.strip().lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def poll_chat_result(
    vault_root: str | Path,
    task_id: str,
    *,
    recipient: str | None = None,
    include_events: bool = False,
) -> dict[str, Any]:
    """Poll the Agent Bus for a chat task result.

    Args:
        vault_root: Vault root directory.
        task_id: The task ID returned by send_chat_message.
        recipient: Optional recipient name to narrow the search (speeds up lookup).
        include_events: Whether to include raw task data in response.

    Returns:
        Dict with ok, task_id, status, is_complete, result_text, and surface fields.
    """
    vault = Path(vault_root).resolve()
    search_recipient = recipient or None  # None = search all recipients

    try:
        if search_recipient:
            tasks = list_tasks(vault, recipient=search_recipient)
        else:
            # Search across all known recipients
            tasks = []
            for r in _DEFAULT_RUNTIME_ID_TO_RECIPIENT.values():
                try:
                    found = list_tasks(vault, recipient=r) or []
                    tasks.extend(found)
                except Exception:
                    pass
    except Exception as exc:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "task_id": task_id,
            "status": "ERROR",
            "error": f"bus_list_failed:{str(exc)[:120]}",
            "is_complete": False,
            "result_text": None,
        }

    task = next((t for t in (tasks or []) if t.get("task_id") == task_id), None)
    if task is None:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "task_id": task_id,
            "status": "NOT_FOUND",
            "is_complete": False,
            "result_text": None,
        }

    status = str(task.get("status") or "unknown")
    is_complete = status.lower() in {"done", "completed", "result_attached"}
    is_blocked = status.lower() in {"blocked", "escalated", "failed", "error"}

    result_text: str | None = None
    # Prefer the result_attached event message (written by the runtime watch loop)
    if is_complete or is_blocked:
        try:
            events = list_events(vault, task_id) or []
            for ev in reversed(events):
                if str(ev.get("event_type", "")).lower() == "result_attached":
                    msg = ev.get("message", "")
                    if msg and isinstance(msg, str) and msg.strip():
                        result_text = msg.strip()
                        break
        except Exception:
            pass
    # Fall back to task-level fields if no event found
    if not result_text:
        for key in ("result", "response"):
            val = task.get(key)
            if val and isinstance(val, str) and val.strip():
                result_text = val.strip()
                break

    out: dict[str, Any] = {
        "ok": True,
        "surface": SURFACE_ID,
        "task_id": task_id,
        "status": status,
        "is_complete": is_complete,
        "is_blocked": is_blocked,
        "result_text": result_text,
        "recipient": task.get("recipient"),
        "sender": task.get("sender"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
    }
    if (is_complete or is_blocked) and result_text:
        runtime_id = runtime_id_for_recipient(task.get("recipient"))
        thread_id = _note_value(task.get("notes"), "thread_id") or default_thread_id_for_runtime(runtime_id)
        session_id = _note_value(task.get("notes"), "session_id") or ""
        saved = append_chat_thread_message(
            vault,
            thread_id=thread_id,
            role="runtime",
            content=result_text,
            runtime_id=runtime_id,
            session_id=session_id,
            task_id=task_id,
            message_id=f"runtime-{task_id}",
            status=status,
        )
        out["thread_id"] = thread_id
        out["session_id"] = session_id
        out["conversation_persisted"] = bool(saved.get("ok"))
        out["conversation_path"] = saved.get("state_record_path")
        out["conversation_message_id"] = saved.get("message_id")
    if include_events:
        out["raw_task"] = task
    return out


def get_hermes_bus_status(vault_root: str | Path) -> dict[str, Any]:
    """Check whether Hermes is reachable via Agent Bus without launching it."""
    status = StudioAgentBusClient(vault_root).runtime_status("hermes")
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "hermes_heartbeat_found": status["heartbeat_found"],
        "hermes_heartbeat_status": status["heartbeat_status"],
        "hermes_last_seen_utc": status["last_seen_utc"],
        "recent_task_count": status["recent_task_count"],
        "wsl_vault_path": status["paths"].get("wsl_vault_path"),
        "windows_vault_path": status["paths"].get("windows_vault_path"),
        "startup_guide": status["startup_guide"],
        "launch_policy": status["launch_policy"],
        "agent_bus_client_surface": status["surface"],
        "warnings": status.get("warnings", []),
    }
