"""Phase 11 Chat runtime result display.

Polls the Agent Bus for tasks associated with Chat-originated runs and renders
them as governed result cards. Completed Hermes/OpenClaw task results become
visible in the Chat page without requiring the operator to inspect raw bus files.

Read-only: does not claim tasks, start runtimes, write Agent Bus tasks, or
promote outputs to canonical memory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import list_tasks


MODEL_VERSION = "studio.phase11_chat_runtime_result_display.v1"
SURFACE_ID = "phase11_chat_runtime_result_display"
PASS_ID = "phase11-chat-runtime-result-display"
STATUS = "COMPLETE / READ-ONLY / RESULT CARDS AVAILABLE"
NEXT_RECOMMENDED_PASS = "phase11-chat-manual-ui-verification"

_RUNTIME_DISPLAY_ORDER = ["Hermes", "OpenClaw", "Archon", "Codex"]

_LANE_LABELS: dict[str, str] = {
    "Hermes": "Hermes / Main Runtime",
    "OpenClaw": "OpenClaw (Discord + Schedule)",
    "Archon": "Archon (Engineering)",
    "Codex": "Codex (Planning)",
}

_STATUS_SEVERITY: dict[str, int] = {
    "done": 0,
    "completed": 0,
    "result_attached": 0,
    "in_progress": 1,
    "started": 1,
    "claimed": 2,
    "created": 3,
    "open": 3,
    "blocked": 4,
    "escalated": 4,
    "failed": 5,
    "error": 5,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _severity(status: str | None) -> int:
    return _STATUS_SEVERITY.get(str(status or "").lower(), 3)


def _result_summary(task: dict[str, Any]) -> str:
    """Extract a safe result summary from a task dict."""
    for key in ("result", "response", "summary", "notes"):
        val = task.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()[:400]
        if isinstance(val, dict):
            for subkey in ("text", "summary", "output", "message"):
                subval = val.get(subkey)
                if subval and isinstance(subval, str) and subval.strip():
                    return subval.strip()[:400]
    return ""


def _task_card(task: dict[str, Any], runtime_id: str) -> dict[str, Any]:
    status = str(task.get("status") or "unknown")
    task_type = str(task.get("task_type") or "")
    created = str(task.get("created_at") or "")
    updated = str(task.get("updated_at") or task.get("created_at") or "")
    task_id = str(task.get("task_id") or "")
    sender = str(task.get("sender") or "")
    intent_raw = task.get("intent")
    intent = str(
        (intent_raw.get("action") if isinstance(intent_raw, dict) else None)
        or intent_raw
        or ""
    )
    result = _result_summary(task)
    blocked_reason = str(task.get("blocked_reason") or task.get("error") or "")
    evidence = str(task.get("evidence_path") or task.get("result_path") or "")
    return {
        "task_id": task_id,
        "runtime": runtime_id,
        "runtime_label": _LANE_LABELS.get(runtime_id, runtime_id),
        "task_type": task_type,
        "status": status,
        "severity": _severity(status),
        "sender": sender,
        "intent": intent,
        "result_summary": result,
        "result_available": bool(result),
        "blocked_reason": blocked_reason,
        "evidence_path": evidence,
        "created_at": created,
        "updated_at": updated,
        "is_complete": status.lower() in {"done", "completed", "result_attached"},
        "is_blocked": status.lower() in {"blocked", "escalated"},
        "is_failed": status.lower() in {"failed", "error"},
        "is_active": status.lower() in {"created", "open", "claimed", "started", "in_progress"},
        "promote_to_canonical_auto": False,
        "runtime_result_display_only": True,
    }


def _runtime_lane(
    vault: Path,
    runtime_id: str,
    *,
    limit: int,
    task_type_filter: str | None,
    status_filter: str | None,
) -> dict[str, Any]:
    try:
        tasks_raw = list_tasks(vault, recipient=runtime_id)
    except Exception as exc:
        return {
            "runtime": runtime_id,
            "runtime_label": _LANE_LABELS.get(runtime_id, runtime_id),
            "ok": False,
            "error": str(exc)[:200],
            "task_count": 0,
            "cards": [],
        }

    cards = []
    for t in (tasks_raw or []):
        if not isinstance(t, dict):
            continue
        if task_type_filter and t.get("task_type") != task_type_filter:
            continue
        if status_filter and t.get("status") != status_filter:
            continue
        cards.append(_task_card(t, runtime_id))

    cards.sort(key=lambda c: c["severity"])
    cards = cards[:limit]
    complete_count = sum(1 for c in cards if c["is_complete"])
    blocked_count = sum(1 for c in cards if c["is_blocked"])
    active_count = sum(1 for c in cards if c["is_active"])
    failed_count = sum(1 for c in cards if c["is_failed"])

    return {
        "runtime": runtime_id,
        "runtime_label": _LANE_LABELS.get(runtime_id, runtime_id),
        "ok": True,
        "task_count": len(cards),
        "complete_count": complete_count,
        "blocked_count": blocked_count,
        "active_count": active_count,
        "failed_count": failed_count,
        "cards": cards,
    }


def build_chat_runtime_result_display(
    vault_root: str | Path,
    *,
    runtimes: list[str] | None = None,
    limit_per_runtime: int = 20,
    task_type_filter: str | None = None,
    status_filter: str | None = None,
    session_task_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build a runtime result display payload for the Chat page.

    Args:
        vault_root: Vault root directory.
        runtimes: Which runtimes to poll. Defaults to Hermes + OpenClaw.
        limit_per_runtime: Max cards per runtime lane (default 20).
        task_type_filter: Optional task type filter applied to every lane.
        status_filter: Optional status filter applied to every lane.
        session_task_ids: If provided, only return cards matching these task IDs.
    """

    vault = Path(vault_root).resolve()
    target_runtimes = runtimes or ["Hermes", "OpenClaw"]

    lanes: list[dict[str, Any]] = []
    total_tasks = 0
    total_complete = 0
    total_blocked = 0
    total_active = 0
    total_failed = 0

    for runtime_id in target_runtimes:
        lane = _runtime_lane(
            vault,
            runtime_id,
            limit=limit_per_runtime,
            task_type_filter=task_type_filter,
            status_filter=status_filter,
        )
        if session_task_ids:
            lane["cards"] = [
                c for c in lane.get("cards", [])
                if c.get("task_id") in session_task_ids
            ]
            lane["task_count"] = len(lane["cards"])
        total_tasks += lane.get("task_count", 0)
        total_complete += lane.get("complete_count", 0)
        total_blocked += lane.get("blocked_count", 0)
        total_active += lane.get("active_count", 0)
        total_failed += lane.get("failed_count", 0)
        lanes.append(lane)

    all_cards = [c for lane in lanes for c in lane.get("cards", [])]
    has_results = any(c["result_available"] for c in all_cards)
    has_blocked = total_blocked > 0
    has_active = total_active > 0

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "runtimes_polled": target_runtimes,
            "total_tasks": total_tasks,
            "complete_count": total_complete,
            "blocked_count": total_blocked,
            "active_count": total_active,
            "failed_count": total_failed,
            "has_results": has_results,
            "has_blocked": has_blocked,
            "has_active": has_active,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "lanes": lanes,
        "authority": {
            "read_only": True,
            "task_claim_allowed": False,
            "task_write_allowed": False,
            "result_promote_to_canonical_auto": False,
            "runtime_dispatch_allowed": False,
            "workflow_execution_allowed": False,
        },
    }


def get_task_result_card(
    vault_root: str | Path,
    task_id: str,
    runtime_id: str = "Hermes",
) -> dict[str, Any] | None:
    """Return a single task result card by task ID, or None if not found."""
    payload = build_chat_runtime_result_display(
        vault_root,
        runtimes=[runtime_id],
        session_task_ids=[task_id],
    )
    for lane in payload.get("lanes", []):
        for card in lane.get("cards", []):
            if card.get("task_id") == task_id:
                return card
    return None
