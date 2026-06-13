from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .approvals import (
    find_pending_approvals,
    list_approval_responses,
    read_approval_response,
)


TERMINAL_WAIT_STATUSES = {"denied", "resumed", "not_found"}


def _response_command_hint(approval_id: str) -> str:
    return f"chaseos osril respond {approval_id} --decision approve"


def _resume_command_hint(workflow_id: str, approval_id: str) -> str:
    return f"chaseos run {workflow_id} --input operator_approval_ref={approval_id}"


def _pending_item(item: dict[str, Any]) -> dict[str, Any]:
    approval_id = str(item.get("approval_id") or "")
    return {
        "approval_id": approval_id,
        "wait_status": "waiting_response",
        "terminal": False,
        "actionable": True,
        "next_action": "record_approval_response",
        "response_command_hint": _response_command_hint(approval_id),
        "resume_command_hint": None,
        "session_id": item.get("session_id"),
        "run_id": item.get("run_id"),
        "runtime_id": item.get("runtime_id"),
        "workflow_id": item.get("workflow_id"),
        "requested_at": item.get("requested_at"),
        "responded_at": None,
        "resumed_at": None,
        "decision": None,
        "source": "approval_required",
        "payload": item.get("payload") or {},
    }


def _response_item(item: dict[str, Any]) -> dict[str, Any]:
    approval_id = str(item.get("approval_id") or "")
    workflow_id = str(item.get("workflow_id") or "")
    decision = str(item.get("decision") or "").upper()
    resume_executed = bool(item.get("resume_executed"))
    applied = bool(item.get("applied_to_execution"))

    if decision == "DENY":
        wait_status = "denied"
        next_action = None
        actionable = False
        resume_hint = None
    elif resume_executed:
        wait_status = "resumed"
        next_action = None
        actionable = False
        resume_hint = None
    elif decision == "APPROVE" and applied:
        wait_status = "ready_to_resume"
        next_action = "resume_workflow"
        actionable = True
        resume_hint = _resume_command_hint(workflow_id, approval_id)
    else:
        wait_status = "response_unapplied"
        next_action = "apply_approval_response"
        actionable = True
        resume_hint = None

    return {
        "approval_id": approval_id,
        "wait_status": wait_status,
        "terminal": wait_status in TERMINAL_WAIT_STATUSES,
        "actionable": actionable,
        "next_action": next_action,
        "response_command_hint": None,
        "resume_command_hint": resume_hint,
        "session_id": item.get("session_id"),
        "run_id": item.get("run_id"),
        "runtime_id": item.get("runtime_id"),
        "workflow_id": item.get("workflow_id"),
        "requested_at": item.get("source_event_timestamp"),
        "responded_at": item.get("responded_at"),
        "resumed_at": item.get("resumed_at"),
        "decision": decision,
        "source": "approval_response",
        "response_id": item.get("response_id"),
        "application_id": item.get("application_id"),
        "resume_id": item.get("resume_id"),
        "response_path": item.get("response_path"),
        "application_path": item.get("application_path"),
        "resume_path": item.get("resume_path"),
    }


def _not_found_item(approval_id: str) -> dict[str, Any]:
    return {
        "approval_id": approval_id,
        "wait_status": "not_found",
        "terminal": True,
        "actionable": False,
        "next_action": None,
        "response_command_hint": None,
        "resume_command_hint": None,
        "session_id": None,
        "run_id": None,
        "runtime_id": None,
        "workflow_id": None,
        "requested_at": None,
        "responded_at": None,
        "resumed_at": None,
        "decision": None,
        "source": "none",
    }


def _sort_key(item: dict[str, Any]) -> str:
    return str(
        item.get("resumed_at")
        or item.get("responded_at")
        or item.get("requested_at")
        or ""
    )


def _summarize(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "waiting_count": sum(1 for item in items if item.get("wait_status") == "waiting_response"),
        "ready_count": sum(1 for item in items if item.get("wait_status") == "ready_to_resume"),
        "denied_count": sum(1 for item in items if item.get("wait_status") == "denied"),
        "resumed_count": sum(1 for item in items if item.get("wait_status") == "resumed"),
        "unapplied_count": sum(1 for item in items if item.get("wait_status") == "response_unapplied"),
        "not_found_count": sum(1 for item in items if item.get("wait_status") == "not_found"),
    }


def _matches_filters(
    item: dict[str, Any],
    *,
    runtime_id: str | None,
    workflow_id: str | None,
    session_id: str | None,
    decision: str | None,
    wait_status: str | None,
) -> bool:
    if runtime_id and item.get("runtime_id") != runtime_id:
        return False
    if workflow_id and item.get("workflow_id") != workflow_id:
        return False
    if session_id and item.get("session_id") != session_id:
        return False
    if decision and str(item.get("decision") or "").upper() != decision.upper():
        return False
    if wait_status and item.get("wait_status") != wait_status:
        return False
    return True


def build_wait_resume_state(
    vault_root: Path,
    *,
    approval_id: str | None = None,
    runtime_id: str | None = None,
    workflow_id: str | None = None,
    session_id: str | None = None,
    decision: str | None = None,
    wait_status: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if approval_id:
        response = read_approval_response(vault_root, approval_id)
        if response is not None:
            items.append(_response_item(response))
        else:
            pending = [
                item
                for item in find_pending_approvals(
                    vault_root,
                    runtime_id=runtime_id,
                    workflow_id=workflow_id,
                    session_id=session_id,
                    limit=None,
                )
                if item.get("approval_id") == approval_id
            ]
            items.append(_pending_item(pending[0]) if pending else _not_found_item(approval_id))
    else:
        items.extend(
            _pending_item(item)
            for item in find_pending_approvals(
                vault_root,
                runtime_id=runtime_id,
                workflow_id=workflow_id,
                session_id=session_id,
                limit=None,
            )
        )
        items.extend(
            _response_item(item)
            for item in list_approval_responses(
                vault_root,
                runtime_id=runtime_id,
                workflow_id=workflow_id,
                session_id=session_id,
                decision=decision,
                limit=None,
            )
        )

    items = [
        item
        for item in items
        if _matches_filters(
            item,
            runtime_id=runtime_id,
            workflow_id=workflow_id,
            session_id=session_id,
            decision=decision,
            wait_status=wait_status,
        )
    ]
    items.sort(key=_sort_key, reverse=True)
    if limit is not None:
        items = items[: max(0, int(limit))]

    summary = _summarize(items)
    return {
        "mode": "single" if approval_id else "list",
        "approval_id": approval_id,
        "count": len(items),
        "items": items,
        "item": items[0] if approval_id and items else None,
        **summary,
        "filters": {
            "approval_id": approval_id,
            "runtime_id": runtime_id,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "decision": decision,
            "wait_status": wait_status,
            "limit": limit,
        },
    }


def _with_wait_status_filter(state: dict[str, Any], wait_status: str | None) -> dict[str, Any]:
    if not wait_status:
        return state
    item = state.get("item") or {}
    state["filters"]["wait_status"] = wait_status
    if item.get("wait_status") == wait_status:
        return state
    state["items"] = []
    state["item"] = None
    state["count"] = 0
    summary = _summarize([])
    for key, value in summary.items():
        state[key] = value
    return state


def wait_for_resume_state(
    vault_root: Path,
    *,
    approval_id: str,
    runtime_id: str | None = None,
    workflow_id: str | None = None,
    session_id: str | None = None,
    decision: str | None = None,
    wait_status: str | None = None,
    timeout_seconds: float = 0,
    poll_interval_seconds: float = 2,
) -> dict[str, Any]:
    timeout = max(0.0, float(timeout_seconds or 0))
    deadline = time.monotonic() + timeout
    interval = max(0.1, float(poll_interval_seconds or 2))

    while True:
        state = build_wait_resume_state(
            vault_root,
            approval_id=approval_id,
            runtime_id=runtime_id,
            workflow_id=workflow_id,
            session_id=session_id,
            decision=decision,
        )
        item = state.get("item") or {}
        current_status = item.get("wait_status")
        if wait_status and current_status == wait_status:
            state = _with_wait_status_filter(state, wait_status)
            state["timed_out"] = False
            return state
        if current_status != "waiting_response":
            state = _with_wait_status_filter(state, wait_status)
            state["timed_out"] = False
            return state
        if timeout <= 0 or time.monotonic() >= deadline:
            state = _with_wait_status_filter(state, wait_status)
            state["timed_out"] = timeout > 0
            return state
        time.sleep(interval)
