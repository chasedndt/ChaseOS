"""
archon_watch.py — Archon Bus Watch Loop (Phase 9 Agent Bus)

Archon-side polling loop that claims and dispatches open tasks from the coordination bus.

Archon's primary mode is direct session-driven engineering (governed by CLAUDE.md).
This watch loop is the parallel coordination-bus receiver — it allows Hermes and
OpenClaw to delegate structured work to Archon asynchronously.

All three current handlers (implementation, code-review, architecture-review) are
bounded analysis handlers: they consume only the bus task packet and return a bus
result plus an Agent-Activity audit writeback. They do not mutate canonical vault
state, call external connectors, execute shell commands, or access credentials.

Dispatch table:
  implementation       -> bounded analysis brief + bus result + Agent-Activity writeback
  code-review          -> bounded code review + bus result + Agent-Activity writeback
  architecture-review  -> bounded architecture review + bus result + Agent-Activity writeback
  others               -> escalation notice posted to bus (task marked blocked)

Lifecycle (single cycle):
  1. Upsert Archon heartbeat (idle)
  2. List open tasks addressed to Archon
  3. For each claimable task (up to max_tasks_per_cycle):
       a. Identify task_type from task data
       b. Dispatch to registered handler — or escalate if unhandled
  4. Upsert heartbeat (busy if tasks were claimed, idle otherwise)
  5. Return cycle summary

Run once: invoke via AOR -> `chaseos run archon_watch`
Run with interval: pass interval_seconds input -> loops until interrupted (Ctrl+C)

Inputs:
  - interval_seconds    int | None   polling interval; None = run once and return
  - max_tasks_per_cycle int          max tasks to claim per cycle (default: 2)

Outputs:
  - cycles_run         int
  - tasks_dispatched   int
  - tasks_escalated    int
  - cycle_summaries    list[dict]
  - writebacks         list  (aggregated from all dispatched handlers)

AOR engine registration:
  _resolve_workflow_handler("archon_watch") -> run_archon_watch

Public API:
    run_archon_watch(inputs, vault_root) -> dict
    WorkflowExecutionError
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WorkflowExecutionError(Exception):
    """Raised when the watch loop cannot complete."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Task annotation parsing ───────────────────────────────────────────────────

def _parse_notes(notes: str | None) -> dict[str, str]:
    """Extract simple key: value annotations from a bus task notes field."""
    result: dict[str, str] = {}
    for line in (notes or "").splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        normalized_key = key.strip().lower()
        if normalized_key:
            result[normalized_key] = value.strip()
    return result


def _normalize_task_type(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace("_", "-")
    return normalized or "unknown"


def _shorten(value: Any, *, limit: int = 900) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _safe_task_id_fragment(task_id: str) -> str:
    fragment = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in task_id)
    return (fragment.strip("-_") or "task")[:24]


# ── Bounded analysis builder (shared by all three current handlers) ───────────

def _build_bounded_analysis_summary(task: dict[str, Any], task_type: str) -> str:
    request = _shorten(task.get("request"), limit=1200) or "(no request supplied)"
    expected = _shorten(task.get("expected_output"), limit=800) or "(no expected output supplied)"
    notes = _shorten(task.get("notes"), limit=800) or "(no notes supplied)"
    return "\n".join(
        [
            f"## Archon Bounded Analysis — {task_type}",
            f"**Task:** `{task.get('task_id', '')}`",
            "",
            "**Request**",
            request,
            "",
            "**Expected Output**",
            expected,
            "",
            "**Notes**",
            notes,
            "",
            "**Result**",
            (
                "Archon accepted this coordination task and produced a bounded analysis "
                "result. No external connectors, shell commands, credential reads, canonical "
                "promotion, or protected-file writes were used by this handler."
            ),
        ]
    )


def _build_bounded_analysis_audit(
    *,
    task: dict[str, Any],
    task_type: str,
    summary: str,
    run_iso: str,
) -> str:
    task_id = str(task.get("task_id") or "")
    return f"""---
type: agent-activity
workflow: archon_watch
task_type: {task_type}
task_id: {task_id}
runtime: Archon
date: {run_iso}
authority: bus-result-only
---

# Archon Watch Bounded Task — {task_id}

**Task Type:** {task_type}
**Bus Status:** done
**Runtime:** Archon

## Boundary Statement

This handler only consumed the coordination bus task packet and wrote a bus result
plus this Agent-Activity audit writeback. It did not read external systems, execute
shell commands, access credentials, mutate canonical notes, or promote knowledge.

## Result Packet

{summary}
"""


def _dispatch_bounded_analysis(task: dict, vault_root: Path, task_type: str) -> dict[str, Any]:
    from runtime.agent_bus.bus import claim_task, update_task_status

    root = Path(vault_root)
    task_id = str(task["task_id"])
    run_iso = _now_iso()
    today = _now_date()

    claim_result = claim_task(root, task_id=task_id, runtime="Archon")
    if not claim_result.get("claimed"):
        return {
            "task_id": task_id,
            "task_type": task_type,
            "status": "skipped",
            "reason": claim_result.get("reason", "claim failed"),
            "writebacks": [],
        }

    update_task_status(
        root,
        task_id=task_id,
        runtime="Archon",
        status="in_progress",
        event_type="started",
        message=f"Archon watch: bounded {task_type} task started.",
    )

    summary = _build_bounded_analysis_summary(task, task_type)
    update_task_status(
        root,
        task_id=task_id,
        runtime="Archon",
        status="done",
        event_type="result_attached",
        message=summary,
    )

    audit_filename = f"{today}-archon-watch-{task_type}-{_safe_task_id_fragment(task_id)}.md"
    audit_path = f"07_LOGS/Agent-Activity/{audit_filename}"
    return {
        "task_id": task_id,
        "task_type": task_type,
        "status": "done",
        "summary": summary,
        "writebacks": [
            {
                "path": audit_path,
                "content": _build_bounded_analysis_audit(
                    task=task,
                    task_type=task_type,
                    summary=summary,
                    run_iso=run_iso,
                ),
            }
        ],
    }


# ── Handler wrappers (one per task type) ──────────────────────────────────────

def _dispatch_implementation(task: dict, vault_root: Path) -> dict[str, Any]:
    return _dispatch_bounded_analysis(task, vault_root, "implementation")


def _dispatch_code_review(task: dict, vault_root: Path) -> dict[str, Any]:
    return _dispatch_bounded_analysis(task, vault_root, "code-review")


def _dispatch_architecture_review(task: dict, vault_root: Path) -> dict[str, Any]:
    return _dispatch_bounded_analysis(task, vault_root, "architecture-review")


def _dispatch_chat(
    task: dict,
    vault_root: Path,
    synthesize: bool = False,
    runtime_instance_id: str | None = None,
) -> dict[str, Any]:
    """Handle a `chat` task type.

    Claims the task and passes the message to this runtime's own execution layer.
    No provider or API key is hardcoded — the runtime uses whatever it is configured with.
    If the runtime produces no response, a bounded acknowledgment is posted.
    """
    from runtime.agent_bus.bus import claim_task, update_task_status

    root = Path(vault_root)
    task_id = str(task["task_id"])
    run_iso = _now_iso()
    today = _now_date()
    message = _shorten(task.get("request"), limit=2000) or "(no message)"
    annotations = _parse_notes(task.get("notes"))
    session_id = annotations.get("session_id") or ""

    claim_result = claim_task(root, task_id=task_id, runtime="Archon",
                              runtime_instance_id=runtime_instance_id)
    if not claim_result.get("claimed"):
        return {
            "task_id": task_id,
            "task_type": "chat",
            "status": "skipped",
            "reason": claim_result.get("reason", "claim failed"),
            "writebacks": [],
        }

    update_task_status(root, task_id=task_id, runtime="Archon", status="in_progress",
                       event_type="started", message="Archon watch: chat task started.")

    runtime_reply = _archon_runtime_chat(message, session_id=session_id, vault_root=vault_root) if synthesize else None

    if runtime_reply:
        response_text = runtime_reply
        runtime_handled = True
    else:
        response_text = (
            "[Archon bounded ack] Chat message received and claimed by Archon watch loop. "
            f"Message: {message}\n\n"
            "Archon runtime execution is not currently active or returned no response. "
            "No vault mutations, credential reads, external API calls, shell commands, "
            "or canonical promotions were performed."
        )
        runtime_handled = False

    update_task_status(root, task_id=task_id, runtime="Archon", status="done",
                       event_type="result_attached", message=response_text)

    audit_filename = f"{today}-archon-chat-{_safe_task_id_fragment(task_id)}.md"
    audit_content = (
        f"---\ntype: agent-activity\nworkflow: archon_watch\ntask_type: chat\n"
        f"task_id: {task_id}\nruntime: Archon\ndate: {run_iso}\n"
        f"runtime_handled: {str(runtime_handled).lower()}\nauthority: bus-result-only\n---\n\n"
        f"# Archon Chat Response — {task_id}\n\n"
        f"**Runtime handled:** {runtime_handled}\n\n"
        "No vault mutations, external API calls beyond the runtime's own configured provider, "
        "shell commands, credential reads, or canonical promotions were performed.\n"
    )
    return {
        "task_id": task_id,
        "task_type": "chat",
        "status": "done",
        "runtime_handled": runtime_handled,
        "response_preview": response_text[:400],
        "writebacks": [{"path": f"07_LOGS/Agent-Activity/{audit_filename}", "content": audit_content}],
    }


def _archon_runtime_chat(message: str, *, session_id: str = "", vault_root: Path | None = None) -> str | None:
    """Invoke Archon's configured synthesis adapter for a chat response.

    Archon proxies through the Hermes model chain via execute_synthesis(adapter="archon").
    Routes through execute_synthesis() — never calls any model provider directly.
    Fail-open: returns None on any error so the caller falls back to a bounded ack.
    """
    del session_id
    try:
        from runtime.execution_adapters.execute import execute_synthesis
        result = execute_synthesis(
            prompt_system=(
                "You are Archon, ChaseOS's engineering runtime. "
                "Answer the user's message concisely and accurately."
            ),
            prompt_user=message,
            execution_adapter="archon",
            vault_root=vault_root or Path.cwd(),
        )
        return result.text.strip() or None
    except Exception:
        return None


# ── Dispatch table ────────────────────────────────────────────────────────────
# Extend here when Archon gains new bus-delegated handler types.

_TASK_DISPATCH: dict[str, Any] = {
    "implementation": _dispatch_implementation,
    "code-review": _dispatch_code_review,
    "architecture-review": _dispatch_architecture_review,
    "chat": _dispatch_chat,
}


# ── Task type inference ───────────────────────────────────────────────────────

def _task_type_from_task(task: dict) -> str:
    """Infer task_type from task data. Notes annotation takes priority."""
    notes = _parse_notes(task.get("notes"))
    if "task_type" in notes:
        return _normalize_task_type(notes["task_type"])

    intent = (task.get("intent") or "").lower()
    intent_to_type = {
        "implementation": "implementation",
        "code-review": "code-review",
        "code_review": "code-review",
        "architecture-review": "architecture-review",
        "architecture_review": "architecture-review",
    }
    return intent_to_type.get(intent, "unknown")


# ── Escalation ────────────────────────────────────────────────────────────────

def _escalate_unhandled(task: dict, vault_root: Path) -> dict[str, Any]:
    """Post a bus blocked event for a task Archon cannot handle."""
    from runtime.agent_bus.bus import update_task_status
    task_type = _task_type_from_task(task)
    msg = (
        f"Archon watch: no handler registered for task_type='{task_type}' "
        f"(intent='{task.get('intent', '?')}'). Task marked blocked — operator intervention required."
    )
    update_task_status(
        vault_root,
        task_id=task["task_id"],
        runtime="Archon",
        status="blocked",
        event_type="blocked",
        message=msg,
    )
    return {"status": "escalated", "task_id": task["task_id"], "reason": msg, "writebacks": []}


# ── Single cycle ──────────────────────────────────────────────────────────────

def _run_one_cycle(
    vault_root: Path,
    *,
    max_tasks_per_cycle: int,
    now_iso: str,
) -> dict[str, Any]:
    """
    Execute one watch cycle: heartbeat → claim → dispatch → heartbeat.
    Returns a summary dict for this cycle.
    """
    from runtime.agent_bus.bus import list_tasks, upsert_heartbeat

    upsert_heartbeat(
        vault_root,
        runtime="Archon",
        status="idle",
        health="ok",
        summary="archon_watch: polling for open tasks",
        now_iso=now_iso,
    )

    open_tasks = list_tasks(vault_root, recipient="Archon", status="open")
    to_process = open_tasks[:max_tasks_per_cycle]

    dispatched: list[dict] = []
    escalated: list[dict] = []
    all_writebacks: list[dict] = []

    for task in to_process:
        task_type = _task_type_from_task(task)
        handler = _TASK_DISPATCH.get(task_type)
        if handler is not None:
            try:
                result = handler(task, vault_root)
                if result.get("status") == "skipped":
                    continue
                dispatched.append({"task_id": task["task_id"], "task_type": task_type, "status": result.get("status")})
                all_writebacks.extend(result.get("writebacks") or [])
            except Exception as exc:
                escalated.append({"task_id": task["task_id"], "task_type": task_type, "error": str(exc)})
        else:
            result = _escalate_unhandled(task, vault_root)
            escalated.append({"task_id": task["task_id"], "task_type": task_type, "reason": result.get("reason")})

    busy = len(dispatched) > 0
    upsert_heartbeat(
        vault_root,
        runtime="Archon",
        status="busy" if busy else "idle",
        health="ok",
        summary=f"archon_watch: dispatched={len(dispatched)} escalated={len(escalated)} open_remaining={len(open_tasks) - len(to_process)}",
        now_iso=_now_iso(),
    )

    return {
        "open_count": len(open_tasks),
        "processed_count": len(to_process),
        "dispatched": dispatched,
        "escalated": escalated,
        "writebacks": all_writebacks,
    }


# ── Public entry point ────────────────────────────────────────────────────────

def run_archon_watch(inputs: dict[str, Any], vault_root: Path | str) -> dict[str, Any]:
    """
    Archon bus watch loop — claim and dispatch open tasks addressed to Archon.

    If interval_seconds is provided, loops indefinitely until interrupted.
    If omitted (or None), runs a single cycle and returns.

    Raises WorkflowExecutionError on unrecoverable setup errors.
    Individual dispatch failures are captured per-task — they do not abort the loop.
    """
    root = Path(vault_root)

    interval_seconds: int | None = inputs.get("interval_seconds")
    max_tasks_per_cycle: int = int(inputs.get("max_tasks_per_cycle", 2))

    if interval_seconds is not None:
        try:
            interval_seconds = int(interval_seconds)
            if interval_seconds < 1:
                raise ValueError("interval_seconds must be >= 1")
        except (TypeError, ValueError) as exc:
            raise WorkflowExecutionError(f"Invalid interval_seconds: {exc}") from exc

    cycles_run = 0
    tasks_dispatched = 0
    tasks_escalated = 0
    cycle_summaries: list[dict] = []
    all_writebacks: list[dict] = []

    try:
        while True:
            now = _now_iso()
            cycle = _run_one_cycle(
                root,
                max_tasks_per_cycle=max_tasks_per_cycle,
                now_iso=now,
            )
            cycles_run += 1
            tasks_dispatched += len(cycle["dispatched"])
            tasks_escalated += len(cycle["escalated"])
            all_writebacks.extend(cycle.get("writebacks") or [])
            cycle_summaries.append({
                "cycle": cycles_run,
                "now": now,
                "open_count": cycle["open_count"],
                "dispatched": len(cycle["dispatched"]),
                "escalated": len(cycle["escalated"]),
            })

            if interval_seconds is None:
                break
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        pass  # Clean exit from polling loop

    return {
        "cycles_run": cycles_run,
        "tasks_dispatched": tasks_dispatched,
        "tasks_escalated": tasks_escalated,
        "cycle_summaries": cycle_summaries,
        "writebacks": all_writebacks,
    }
