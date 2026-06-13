"""
openclaw_post_review_task.py — OpenClaw Review Task Dispatch (Phase 9 Agent Bus Pass 1)

OpenClaw-side workflow for posting a structured review task onto the coordination bus.
Consults the router for the recommended runtime, creates the task, writes an audit entry.

This workflow does NOT perform the review. It dispatches the task and records the
dispatch event. Hermes (or the recommended runtime) executes the review via
hermes_review_execute.

Inputs:
  - artifact_path   str  vault-relative path to the artifact to review
  - request         str  what the reviewer should do (default: "Review artifact")
  - expected_output str  what the review should return (default: structured review summary)
  - priority        str  "low" | "normal" | "high" (default: "normal"; never "critical")
  - notes           str  optional context for the reviewer

Outputs (in returned dict):
  - task_id           coordination bus task ID (str)
  - recipient         runtime the task was addressed to (str)
  - route_recommended recommended runtime from router (str | None)
  - route_reason      router reason string (str)
  - artifact_path     resolved artifact_path (str)
  - writebacks        list of vault writeback entries for AOR Stage 7

AOR engine registration:
  _handlers["openclaw_post_review_task"] = run_openclaw_post_review_task

Public API:
    run_openclaw_post_review_task(inputs, vault_root) -> dict
    WorkflowExecutionError
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WorkflowExecutionError(Exception):
    """Raised when the review dispatch workflow cannot complete."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _build_audit_content(
    *,
    task_id: str,
    artifact_path: str,
    recipient: str,
    route_recommended: str | None,
    route_reason: str,
    request: str,
    priority: str,
    run_iso: str,
) -> str:
    rec_note = route_recommended if route_recommended else "none (all stale or no capacity)"
    return f"""---
type: agent-activity
workflow: openclaw_post_review_task
task_id: {task_id}
runtime: OpenClaw
date: {run_iso}
---

# Review Task Dispatch — {task_id}

**Artifact:** `{artifact_path}`
**Recipient:** {recipient}
**Priority:** {priority}
**Request:** {request}

## Router Decision

- Recommended: {rec_note}
- Reason: {route_reason}

## Result

Task `{task_id}` created on coordination bus. Status: open.
Hermes should claim via `chaseos agent-bus task claim {task_id} --runtime Hermes`
or by running `chaseos run hermes_review_execute`.
"""


def run_openclaw_post_review_task(inputs: dict[str, Any], vault_root: Path | str) -> dict[str, Any]:
    """
    Create a review task on the coordination bus for Hermes (or recommended runtime).

    Raises WorkflowExecutionError if task creation fails.
    Returns dict with task_id, route result, and writebacks for AOR Stage 7.
    """
    from runtime.agent_bus.bus import create_task
    from runtime.agent_bus.router import route_task_type

    root = Path(vault_root)
    run_iso = _now_iso()
    today = _now_date()

    artifact_path = str(inputs.get("artifact_path", "")).strip()
    request = str(inputs.get("request", "")).strip() or f"Review artifact: {artifact_path}"
    expected_output = str(inputs.get("expected_output", "")).strip() or (
        "Structured review with: section checklist, endorsements, flags, and overall verdict."
    )
    priority = str(inputs.get("priority", "normal")).strip()
    notes_extra = inputs.get("notes")

    if not artifact_path:
        raise WorkflowExecutionError("Input 'artifact_path' is required.")

    # Validate priority won't exceed Hermes ceiling (high); block critical at dispatch
    if priority == "critical":
        raise WorkflowExecutionError(
            "Priority 'critical' is not allowed from openclaw_post_review_task. "
            "Use 'high' or lower, or route through operator escalation."
        )

    # Consult the router — informational; task is created regardless of route result
    try:
        route = route_task_type("review", root)
        route_recommended = route.recommended
        route_reason = route.reason
    except Exception as exc:
        route_recommended = None
        route_reason = f"Router unavailable: {exc}"

    # Recipient: use router recommendation if available, else default to Hermes
    recipient = route_recommended or "Hermes"

    notes_parts = [f"artifact_path: {artifact_path}"]
    if notes_extra:
        notes_parts.append(str(notes_extra))
    notes_str = "\n".join(notes_parts)

    result = create_task(
        root,
        sender="OpenClaw",
        recipient=recipient,
        intent="REVIEW",
        priority=priority,
        request=request,
        expected_output=expected_output,
        notes=notes_str,
    )

    if not result.get("created"):
        raise WorkflowExecutionError(
            f"Failed to create review task on coordination bus: {result.get('reason', 'unknown')}"
        )

    task_id: str = result["task_id"]

    # Build audit entry
    audit_filename = f"{today}-openclaw-review-dispatch-{task_id[:12]}.md"
    audit_path = f"07_LOGS/Agent-Activity/{audit_filename}"
    audit_content = _build_audit_content(
        task_id=task_id,
        artifact_path=artifact_path,
        recipient=recipient,
        route_recommended=route_recommended,
        route_reason=route_reason,
        request=request,
        priority=priority,
        run_iso=run_iso,
    )

    return {
        "task_id": task_id,
        "recipient": recipient,
        "route_recommended": route_recommended,
        "route_reason": route_reason,
        "artifact_path": artifact_path,
        "writebacks": [
            {"path": audit_path, "content": audit_content},
        ],
    }
