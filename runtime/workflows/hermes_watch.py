"""
hermes_watch.py — Hermes Bus Watch Loop (Phase 9 Agent Bus)

Hermes-side polling loop that claims and dispatches open tasks from the coordination bus.

This workflow makes Hermes autonomous: instead of waiting to be invoked manually per task,
it polls the bus, claims open tasks addressed to it, and dispatches to the appropriate
handler based on task_type.

Dispatch table (extensible):
  review                   -> run_hermes_review_execute
  planning                 -> bounded bus-analysis result
  shadow-audit             -> bounded bus-analysis result
  developer-co-development -> bounded bus-analysis result
  others                   -> escalation notice posted to bus (task marked blocked)

Lifecycle (single cycle):
  1. Upsert Hermes heartbeat (idle)
  2. List open tasks addressed to Hermes
  3. For each claimable task (up to max_tasks_per_cycle):
       a. Identify task_type from task data
       b. Dispatch to registered handler — or escalate if unhandled
  4. Upsert heartbeat (busy if tasks were claimed, idle otherwise)
  5. Return cycle summary

Run once: invoke via AOR → `chaseos run hermes_watch`
Run with interval: pass interval_seconds input → loops until interrupted (Ctrl+C)
Run via bus.run_watch_loop: use bus.py directly for bare heartbeat-only polling

Inputs:
  - interval_seconds   int | None   polling interval; None = run once and return
  - max_tasks_per_cycle int         max tasks to claim per cycle (default: 2)
  - synthesize         bool         pass to hermes_review_execute (default: False — opt-in only)

Outputs:
  - cycles_run         int
  - tasks_dispatched   int
  - tasks_escalated    int
  - cycle_summaries    list[dict]
  - writebacks         list  (aggregated from all dispatched handlers)

AOR engine registration:
  _handlers["hermes_watch"] = run_hermes_watch

Public API:
    run_hermes_watch(inputs, vault_root) -> dict
    WorkflowExecutionError
"""
from __future__ import annotations

import inspect
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.hermes.chat_bridge import call_hermes_chat_bridge

# M-2 security fix: only allow simple alphanumeric slugs as workflow_id in schedule commands
_WORKFLOW_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


class WorkflowExecutionError(Exception):
    """Raised when the watch loop cannot complete."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Cron evaluation (Option C: Hermes self-contained schedule polling) ─────────

def _cron_field_matches(field: str, value: int) -> bool:
    """Match a single cron field string against a numeric value. Supports *, a-b ranges, a,b,c lists."""
    field = field.strip()
    if field == "*":
        return True
    if "," in field:
        return any(_cron_field_matches(part, value) for part in field.split(","))
    if "-" in field:
        try:
            lo, hi = field.split("-", 1)
            return int(lo) <= value <= int(hi)
        except ValueError:
            return False
    try:
        return int(field) == value
    except ValueError:
        return False


def _cron_matches(cron_expression: str, dt: datetime) -> bool:
    """
    Return True if dt matches the 5-field cron expression (minute hour dom month dow).
    dow convention: 0=Sunday, 1=Monday, ..., 6=Saturday.
    """
    fields = cron_expression.strip().split()
    if len(fields) != 5:
        return False
    minute_f, hour_f, dom_f, month_f, dow_f = fields
    # Python weekday() Mon=0..Sun=6 → cron Sun=0, Mon=1..Sat=6
    cron_dow = (dt.weekday() + 1) % 7
    return (
        _cron_field_matches(minute_f, dt.minute)
        and _cron_field_matches(hour_f, dt.hour)
        and _cron_field_matches(dom_f, dt.day)
        and _cron_field_matches(month_f, dt.month)
        and _cron_field_matches(dow_f, cron_dow)
    )


# ── Schedule state (dedup: one fire per minute per schedule) ───────────────────

_SCHEDULE_STATE_FILENAME = "hermes_schedule_state.json"


def _get_schedule_state_path(vault_root: Path) -> Path:
    return vault_root / ".chaseos" / _SCHEDULE_STATE_FILENAME


def _load_schedule_state(vault_root: Path) -> dict:
    """Load schedule firing state. Returns empty dict on missing or corrupt file."""
    try:
        return json.loads(_get_schedule_state_path(vault_root).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_schedule_state(vault_root: Path, state: dict) -> None:
    """Persist schedule firing state. Suppresses all IO errors (fail-open)."""
    try:
        path = _get_schedule_state_path(vault_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass


# ── Due schedule detection and execution ───────────────────────────────────────

def _check_due_schedules(vault_root: Path, now_dt: datetime) -> list[dict]:
    """
    Evaluate all Hermes-targeted enabled cron schedules and fire those that are due.

    Fail-open on schedule loader import errors, subprocess failures, and timezone errors.
    Skips hermes_watch itself to prevent recursion.
    Respects shadow_mode: records intent but does not execute.
    Deduplicates within the same minute using .chaseos/hermes_schedule_state.json.

    Returns one result dict per evaluated schedule.
    """
    import subprocess

    results: list[dict] = []

    try:
        from runtime.schedules.loader import export_schedules_for_adapter
        schedules = export_schedules_for_adapter("hermes", vault_root, enabled_only=True)
    except Exception:
        return results

    if not schedules:
        return results

    state = _load_schedule_state(vault_root)
    last_fired: dict[str, str] = state.get("last_fired") or {}
    changed = False
    # Minute-floor prefix in UTC for dedup comparison
    now_minute_prefix = now_dt.strftime("%Y-%m-%dT%H:%M")

    for entry in schedules:
        schedule_id: str = entry.get("schedule_id", "")
        workflow_id: str = entry.get("workflow_id") or ""
        cadence_type = entry.get("cadence_type")
        cron_expression = entry.get("cron_expression")
        tz_name: str = entry.get("timezone") or "UTC"
        command: str = entry.get("command") or ""
        shadow_mode: bool = bool(entry.get("shadow_mode", False))
        is_fallback: bool = bool(entry.get("is_fallback", False))

        if is_fallback:
            continue
        if cadence_type != "cron" or not cron_expression:
            continue
        if workflow_id == "hermes_watch":
            continue

        try:
            from zoneinfo import ZoneInfo
            now_local = now_dt.astimezone(ZoneInfo(tz_name))
        except Exception:
            now_local = now_dt

        if not _cron_matches(cron_expression, now_local):
            results.append({"schedule_id": schedule_id, "fired": False, "reason": "not_due"})
            continue

        prev_fired = last_fired.get(schedule_id, "")
        if prev_fired.startswith(now_minute_prefix):
            results.append({"schedule_id": schedule_id, "fired": False, "reason": "already_fired_this_minute"})
            continue

        if shadow_mode:
            last_fired[schedule_id] = now_dt.isoformat()
            changed = True
            results.append({"schedule_id": schedule_id, "fired": False, "reason": "shadow_mode", "command": command})
            continue

        # M-2 security fix: validate workflow_id is a safe slug before splitting command
        if not _WORKFLOW_ID_RE.match(workflow_id):
            results.append({
                "schedule_id": schedule_id,
                "fired": False,
                "reason": f"invalid_workflow_id_slug: {workflow_id!r}",
            })
            continue

        fired = True
        fire_reason = "fired"
        try:
            subprocess.run(command.split(), check=False, timeout=30)
        except Exception as exc:
            fired = False
            fire_reason = f"subprocess_error: {exc}"

        last_fired[schedule_id] = now_dt.isoformat()
        changed = True
        results.append({
            "schedule_id": schedule_id,
            "workflow_id": workflow_id,
            "fired": fired,
            "reason": fire_reason,
            "command": command,
        })

    if changed:
        _save_schedule_state(vault_root, {"last_fired": last_fired})

    return results


# ── Task type → handler dispatch ──────────────────────────────────────────────
# Add entries here only for handlers that stay inside Hermes' declared bus scope.

_BOUNDED_ANALYSIS_TYPES = {
    "planning",
    "shadow-audit",
    "developer-co-development",
}

def _dispatch_review(
    task: dict,
    vault_root: Path,
    synthesize: bool,
    runtime_instance_id: str | None = None,
) -> dict[str, Any]:
    from runtime.workflows.hermes_review_execute import run_hermes_review_execute
    return run_hermes_review_execute(
        {
            "task_id": task["task_id"],
            "synthesize": synthesize,
            "runtime_instance_id": runtime_instance_id,
        },
        vault_root,
    )


def _dispatch_research_synthesis(
    task: dict,
    vault_root: Path,
    synthesize: bool,
    runtime_instance_id: str | None = None,
) -> dict[str, Any]:
    from runtime.workflows.hermes_research_synthesis import run_hermes_research_synthesis
    annotations = _parse_notes(task.get("notes"))
    workspace_id = annotations.get("workspace_id") or task.get("request", "").strip()
    return run_hermes_research_synthesis(
        {"workspace_id": workspace_id, "synthesize": synthesize},
        vault_root,
    )


def _dispatch_skill_review(
    task: dict,
    vault_root: Path,
    synthesize: bool,
    runtime_instance_id: str | None = None,
) -> dict[str, Any]:
    from runtime.workflows.hermes_skill_review import run_hermes_skill_review
    annotations = _parse_notes(task.get("notes"))
    max_scan = int(annotations.get("max_scan") or 50)
    filter_class = annotations.get("filter_class") or ""
    return run_hermes_skill_review(
        {"max_scan": max_scan, "filter_class": filter_class},
        vault_root,
    )


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


def _build_bounded_analysis_summary(task: dict[str, Any], task_type: str) -> str:
    request = _shorten(task.get("request"), limit=1200) or "(no request supplied)"
    expected = _shorten(task.get("expected_output"), limit=800) or "(no expected output supplied)"
    notes = _shorten(task.get("notes"), limit=800) or "(no notes supplied)"
    return "\n".join(
        [
            f"## Hermes Bounded Bus Analysis - {task_type}",
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
                "Hermes accepted this coordination task and produced a bounded bus-analysis "
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
workflow: hermes_watch
task_type: {task_type}
task_id: {task_id}
runtime: Hermes
date: {run_iso}
authority: bus-result-only
---

# Hermes Watch Bounded Task - {task_id}

**Task Type:** {task_type}
**Bus Status:** done
**Runtime:** Hermes

## Boundary Statement

This handler only consumed the coordination bus task packet and wrote a bus result
plus this Agent-Activity audit writeback. It did not read external systems, execute
shell commands, access credentials, mutate canonical notes, or promote knowledge.

## Result Packet

{summary}
"""


def _dispatch_bounded_analysis(
    task: dict,
    vault_root: Path,
    synthesize: bool,
    runtime_instance_id: str | None = None,
) -> dict[str, Any]:
    del synthesize
    from runtime.agent_bus.bus import claim_task, update_task_status

    root = Path(vault_root)
    task_id = str(task["task_id"])
    task_type = _task_type_from_task(task)
    run_iso = _now_iso()
    today = _now_date()

    claim_result = claim_task(
        root,
        task_id=task_id,
        runtime="Hermes",
        runtime_instance_id=runtime_instance_id,
    )
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
        runtime="Hermes",
        status="in_progress",
        event_type="started",
        message=f"Hermes watch: bounded {task_type} task started.",
    )

    summary = _build_bounded_analysis_summary(task, task_type)
    update_task_status(
        root,
        task_id=task_id,
        runtime="Hermes",
        status="done",
        event_type="result_attached",
        message=summary,
    )

    audit_filename = f"{today}-hermes-watch-{task_type}-{_safe_task_id_fragment(task_id)}.md"
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


def _dispatch_chat(
    task: dict,
    vault_root: Path,
    synthesize: bool,
    runtime_instance_id: str | None = None,
) -> dict[str, Any]:
    """Handle a `chat` task type.

    Claims the task and returns either a Hermes-owned bridge response or a
    bounded acknowledgment. This workflow does not call model providers, read
    provider credentials, or mount Hermes backend configuration itself.
    """
    from runtime.agent_bus.bus import claim_task, update_task_status

    root = Path(vault_root)
    task_id = str(task["task_id"])
    run_iso = _now_iso()
    today = _now_date()
    message = _shorten(task.get("request"), limit=2000) or "(no message)"
    annotations = _parse_notes(task.get("notes"))
    session_id = annotations.get("session_id") or ""

    claim_result = claim_task(root, task_id=task_id, runtime="Hermes",
                              runtime_instance_id=runtime_instance_id)
    if not claim_result.get("claimed"):
        return {
            "task_id": task_id,
            "task_type": "chat",
            "status": "skipped",
            "reason": claim_result.get("reason", "claim failed"),
            "writebacks": [],
        }

    update_task_status(root, task_id=task_id, runtime="Hermes", status="in_progress",
                       event_type="started", message="Hermes: chat task claimed, dispatching to runtime.")

    # Delegate to Hermes' own configured execution layer.
    # It returns a response string, or a safe blocker when runtime config is missing.
    runtime_reply = None
    runtime_blocker = ""
    if synthesize:
        runtime_reply, runtime_blocker = _hermes_runtime_chat_result(
            message,
            session_id=session_id,
            vault_root=vault_root,
        )

    if runtime_reply:
        response_text = runtime_reply
        runtime_handled = True
    else:
        response_text = (
            f"[Hermes bounded ack] Chat message received and claimed.\n\n"
            f"Message: {message}\n\n"
            "Hermes live model text is not currently available from the runtime adapter. "
            + (f"Runtime blocker: {runtime_blocker}. " if runtime_blocker else "")
            + "No vault mutations, provider/model calls, credential reads, shell commands, "
            "approval consumption, or canonical promotions were performed."
        )
        runtime_handled = False

    update_task_status(root, task_id=task_id, runtime="Hermes", status="done",
                       event_type="result_attached", message=response_text)

    audit_filename = f"{today}-hermes-chat-{_safe_task_id_fragment(task_id)}.md"
    audit_content = (
        f"---\ntype: agent-activity\nworkflow: hermes_watch\ntask_type: chat\n"
        f"task_id: {task_id}\nruntime: Hermes\ndate: {run_iso}\n"
        f"runtime_handled: {str(runtime_handled).lower()}\nauthority: bus-result-only\n---\n\n"
        f"# Hermes Chat Response — {task_id}\n\n"
        f"**Runtime handled:** {runtime_handled}\n\n"
        "No vault mutations, provider/model calls, shell commands, credential reads, "
        "approval consumption, or canonical promotions were performed.\n"
    )
    return {
        "task_id": task_id,
        "task_type": "chat",
        "status": "done",
        "runtime_handled": runtime_handled,
        "runtime_blocker": runtime_blocker,
        "response_preview": response_text[:400],
        "writebacks": [{"path": f"07_LOGS/Agent-Activity/{audit_filename}", "content": audit_content}],
    }


def _hermes_runtime_chat(message: str, *, session_id: str = "", vault_root: Path | None = None) -> str | None:
    """Return a Hermes-owned synthesis reply for Agent Bus chat tasks.

    Studio never calls providers directly. It writes a Chat task to Agent Bus;
    this Hermes watch daemon claims the task and invokes the runtime-owned
    execution adapter with ``execution_adapter='hermes'``. Adapter failures fail
    open to ``None`` so the bus result can carry a bounded blocker instead of
    crashing the watch loop.
    """

    try:
        bridge_result = call_hermes_chat_bridge(
            message,
            session_id=session_id,
            vault_root=vault_root,
            timeout_seconds=90,
        )
    except Exception:  # noqa: BLE001 - fall through to shared adapter blocker path
        bridge_result = {"ok": False, "error": "bridge_exception"}
    if bridge_result.get("ok") and str(bridge_result.get("text") or "").strip():
        return str(bridge_result["text"]).strip()

    try:
        from runtime.execution_adapters import execute as execution_execute

        result = execution_execute.execute_synthesis(
            vault_root=vault_root,
            prompt_system=(
                "You are Hermes replying to a ChaseOS Studio Chat task after the task was "
                "claimed by the Hermes runtime daemon. Reply concisely. Do not claim file "
                "writes, shell commands, approval consumption, or canonical promotion."
            ),
            prompt_user=message,
            execution_adapter="hermes",
        )
    except Exception:  # noqa: BLE001 - chat task result path records bounded blocker upstream
        return None
    text = str(getattr(result, "text", "") or "").strip()
    return text or None


def _safe_runtime_blocker(exc: BaseException) -> str:
    text = str(exc).replace("\n", " ").strip()
    if not text:
        return type(exc).__name__
    return text[:260]


def _hermes_chat_backend_dependency_report() -> dict[str, str]:
    return {
        "missing_contract": "hermes_native_chat_backend_bridge",
        "affected_phase10_or_phase11_surface": "Studio Chat / Hermes saved conversation reply",
        "lower_phase_owner_or_surface": "Hermes backend configuration and Phase 9 runtime-dispatch authority",
        "minimum_proof_needed": (
            "Hermes-owned chat bridge, gateway, ACP, or daemon endpoint returns one bounded "
            "reply using Hermes backend auth/config without ChaseOS Studio reading provider credentials."
        ),
        "blocked_action_reason": (
            "Hermes Agent Bus Chat is bus-result-only in ChaseOS; provider/model execution "
            "is not mounted from hermes_watch. Configure the Hermes backend and expose a "
            "governed Hermes-native chat bridge before live replies can be claimed."
        ),
    }


def _hermes_runtime_chat_result(
    message: str,
    *,
    session_id: str = "",
    vault_root: Path | None = None,
) -> tuple[str | None, str]:
    """Return Hermes' live Chat response or a bounded backend blocker.

    `hermes_watch` is the runtime-daemon side of Studio Chat. Studio creates an
    Agent Bus task and Hermes claims it here. Model/provider execution must come
    from a Hermes-owned backend bridge, not from this ChaseOS workflow.
    """
    reply = _hermes_runtime_chat(message, session_id=session_id, vault_root=vault_root)
    if reply:
        return reply, ""
    report = _hermes_chat_backend_dependency_report()
    return None, report["blocked_action_reason"]


_TASK_DISPATCH: dict[str, Any] = {
    "review": _dispatch_review,
    "research-synthesis": _dispatch_research_synthesis,
    "idea-graduation": _dispatch_skill_review,
    "chat": _dispatch_chat,
    "planning": _dispatch_bounded_analysis,
    "shadow-audit": _dispatch_bounded_analysis,
    "developer-co-development": _dispatch_bounded_analysis,
}


def _task_type_from_task(task: dict) -> str:
    """Infer task_type from task intent or notes. Falls back to 'unknown'."""
    intent = (task.get("intent") or "").lower()
    if intent == "review":
        return "review"

    notes = _parse_notes(task.get("notes"))
    if "task_type" in notes:
        return _normalize_task_type(notes["task_type"])

    intent_to_type = {
        "review": "review",
        "task": "task",
        "result": "result",
        "blocker": "blocker",
        "question": "question",
        "notice": "notice",
    }
    return intent_to_type.get(intent, "unknown")


def _call_dispatch_handler(
    handler: Any,
    task: dict,
    vault_root: Path,
    synthesize: bool,
    runtime_instance_id: str | None,
) -> dict[str, Any]:
    """Call watch dispatch handlers while preserving older 3-arg test adapters."""
    signature = inspect.signature(handler)
    params = list(signature.parameters.values())
    accepts_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
    positional_count = len(
        [
            p
            for p in params
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
    )
    if accepts_varargs or positional_count >= 4 or "runtime_instance_id" in signature.parameters:
        return handler(task, vault_root, synthesize, runtime_instance_id)
    return handler(task, vault_root, synthesize)


def _escalate_unhandled(task: dict, vault_root: Path) -> dict[str, Any]:
    """Post a bus blocked event for a task Hermes cannot handle."""
    from runtime.agent_bus.bus import update_task_status
    task_type = _task_type_from_task(task)
    msg = (
        f"Hermes watch: no handler registered for task_type='{task_type}' "
        f"(intent='{task.get('intent', '?')}'). Task marked blocked — operator intervention required."
    )
    update_task_status(
        vault_root,
        task_id=task["task_id"],
        runtime="Hermes",
        status="blocked",
        event_type="blocked",
        message=msg,
    )
    return {"status": "escalated", "task_id": task["task_id"], "reason": msg, "writebacks": []}


def _run_one_cycle(
    vault_root: Path,
    *,
    max_tasks_per_cycle: int,
    synthesize: bool,
    now_iso: str,
    runtime_instance_id: str | None = None,
    control_surface: str | None = None,
    control_surface_key: str | None = None,
    check_schedules: bool = True,
) -> dict[str, Any]:
    """
    Execute one watch cycle: heartbeat → claim → dispatch → heartbeat.
    Returns a summary dict for this cycle.
    """
    from runtime.agent_bus.bus import list_tasks, upsert_heartbeat

    heartbeat_kwargs = {
        "runtime_instance_id": runtime_instance_id,
        "heartbeat_scope": "instance" if runtime_instance_id else "runtime",
        "control_surface": control_surface,
        "control_surface_key": control_surface_key,
    }

    # Heartbeat: announce Hermes is alive and watching
    upsert_heartbeat(
        vault_root,
        runtime="Hermes",
        status="idle",
        health="ok",
        summary="hermes_watch: polling for open tasks",
        now_iso=now_iso,
        **heartbeat_kwargs,
    )

    # Cron schedule polling — fire any due Hermes-targeted schedules
    schedule_results: list[dict] = []
    if check_schedules:
        schedule_results = _check_due_schedules(vault_root, datetime.now(timezone.utc))

    open_tasks = list_tasks(vault_root, recipient="Hermes", status="open")
    to_process = open_tasks[:max_tasks_per_cycle]

    dispatched: list[dict] = []
    escalated: list[dict] = []
    all_writebacks: list[dict] = []

    for task in to_process:
        task_type = _task_type_from_task(task)
        handler = _TASK_DISPATCH.get(task_type)
        if handler is not None:
            try:
                result = _call_dispatch_handler(handler, task, vault_root, synthesize, runtime_instance_id)
                if result.get("status") == "skipped":
                    continue
                dispatched.append({"task_id": task["task_id"], "task_type": task_type, "status": result.get("status")})
                all_writebacks.extend(result.get("writebacks") or [])
            except Exception as exc:
                escalated.append({"task_id": task["task_id"], "task_type": task_type, "error": str(exc)})
        else:
            result = _escalate_unhandled(task, vault_root)
            escalated.append({"task_id": task["task_id"], "task_type": task_type, "reason": result.get("reason")})

    # Update heartbeat with post-cycle state
    busy = len(dispatched) > 0
    claimed = list_tasks(vault_root, recipient="Hermes", owner="Hermes")
    upsert_heartbeat(
        vault_root,
        runtime="Hermes",
        status="busy" if busy else "idle",
        health="ok",
        summary=f"hermes_watch: dispatched={len(dispatched)} escalated={len(escalated)} open_remaining={len(open_tasks) - len(to_process)}",
        now_iso=_now_iso(),
        **heartbeat_kwargs,
    )

    return {
        "open_count": len(open_tasks),
        "processed_count": len(to_process),
        "dispatched": dispatched,
        "escalated": escalated,
        "writebacks": all_writebacks,
        "schedules_fired": [r for r in schedule_results if r.get("fired")],
    }


def run_hermes_watch(inputs: dict[str, Any], vault_root: Path | str) -> dict[str, Any]:
    """
    Hermes bus watch loop — claim and dispatch open tasks addressed to Hermes.

    If interval_seconds is provided, loops indefinitely until interrupted.
    If omitted (or None), runs a single cycle and returns.

    Raises WorkflowExecutionError on unrecoverable setup errors.
    Individual dispatch failures are captured per-task — they do not abort the loop.
    """
    root = Path(vault_root)

    interval_seconds: int | None = inputs.get("interval_seconds")
    max_tasks_per_cycle: int = int(inputs.get("max_tasks_per_cycle", 2))
    synthesize: bool = bool(inputs.get("synthesize", False))  # opt-in only — never default to paid API calls
    check_schedules: bool = bool(inputs.get("check_schedules", True))
    runtime_instance_id = inputs.get("runtime_instance_id") or None
    control_surface = inputs.get("control_surface") or None
    control_surface_key = inputs.get("control_surface_key") or None

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
                synthesize=synthesize,
                now_iso=now,
                runtime_instance_id=runtime_instance_id,
                control_surface=control_surface,
                control_surface_key=control_surface_key,
                check_schedules=check_schedules,
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
                "schedules_fired": len(cycle.get("schedules_fired") or []),
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
