"""
openclaw_watch.py — OpenClaw Bus Watch Loop (Phase 9 Agent Bus)

OpenClaw-side polling loop that claims and dispatches open tasks from the coordination bus.

This workflow is the receiver side of OpenClaw. OpenClaw is primarily a sender (it posts
tasks to Hermes and other runtimes), but it also declares receiver capability for several
task types in runtime/openclaw/capabilities.yaml. This loop handles the cases where another
runtime or the system dispatches work to OpenClaw via the bus.

Dispatch table:
  operator-briefing   → operator_today (default) or operator_close_day (if workflow: close_day in notes)
  graph-hygiene       → graph_hygiene
  vault-maintenance   → graduate_ideas
  scheduled-briefing  → sbp_strikezone_digest
  source-pack-builder → source_pack_builder from a declared JSON input envelope
  others              → escalation notice posted to bus (task marked blocked)

Task type is inferred from:
  1. intent == "REVIEW"         → review  (OpenClaw is secondary reviewer — escalated to Hermes)
  2. notes field "task_type: X" → use X
  3. notes field "workflow: X"  → derive task_type from workflow name
  4. fallback                   → "unknown" (escalated)

Lifecycle (single cycle):
  1. Upsert OpenClaw heartbeat (idle)
  2. List open tasks addressed to OpenClaw
  3. For each claimable task (up to max_tasks_per_cycle):
       a. Infer task_type from task data
       b. Dispatch to registered handler — or escalate if unhandled
  4. Upsert heartbeat (busy if tasks were claimed, idle otherwise)
  5. Return cycle summary

Run once:     chaseos run openclaw_watch
Run looping:  chaseos run openclaw_watch --input interval_seconds=60

Inputs:
  - interval_seconds    int | None   polling interval; None = run once and return
  - max_tasks_per_cycle int          max tasks to claim per cycle (default: 3 — matches capability)
  - dry_run             bool         log tasks without claiming them (default: False)

Outputs:
  - cycles_run         int
  - tasks_dispatched   int
  - tasks_escalated    int
  - cycle_summaries    list[dict]
  - writebacks         list  (aggregated from all dispatched handlers)

AOR engine registration:
  _handlers["openclaw_watch"] = run_openclaw_watch

Public API:
    run_openclaw_watch(inputs, vault_root) -> dict
    WorkflowExecutionError
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class WorkflowExecutionError(Exception):
    """Raised when the watch loop cannot complete."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Task annotation parsing ───────────────────────────────────────────────────

def _parse_notes(notes: str) -> dict[str, str]:
    """Extract key: value annotations from task notes field."""
    result: dict[str, str] = {}
    for line in (notes or "").splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().lower()] = val.strip()
    return result


def _infer_task_type(task: dict) -> str:
    """
    Infer task_type from bus task data.

    Priority order:
      1. intent == REVIEW → "review"
      2. notes "task_type:" annotation
      3. notes "workflow:" annotation → mapped to task_type
      4. fallback → "unknown"
    """
    intent = (task.get("intent") or "").upper()
    if intent == "REVIEW":
        return "review"

    notes = _parse_notes(task.get("notes") or "")

    if "task_type" in notes:
        return notes["task_type"]

    workflow_map = {
        "operator_today": "operator-briefing",
        "operator_close_day": "operator-briefing",
        "graph_hygiene": "graph-hygiene",
        "graduate_ideas": "vault-maintenance",
        "sbp_strikezone_digest": "scheduled-briefing",
    }
    if "workflow" in notes:
        return workflow_map.get(notes["workflow"], "unknown")

    return "unknown"


def _infer_workflow(task: dict, task_type: str) -> str:
    """
    For task types with multiple possible workflows, pick the right one.
    Reads 'workflow: X' from notes; falls back to sensible defaults.
    """
    notes = _parse_notes(task.get("notes") or "")
    explicit = notes.get("workflow", "")

    if task_type == "operator-briefing":
        if explicit == "operator_close_day":
            return "operator_close_day"
        return "operator_today"

    defaults = {
        "graph-hygiene": "graph_hygiene",
        "vault-maintenance": "graduate_ideas",
        "scheduled-briefing": "sbp_strikezone_digest",
        "source-pack-builder": "source_pack_builder",
    }
    return explicit or defaults.get(task_type, "")


# ── Per-task-type dispatch functions ──────────────────────────────────────────

def _dispatch_operator_briefing(task: dict, vault_root: Path) -> dict[str, Any]:
    workflow = _infer_workflow(task, "operator-briefing")
    if workflow == "operator_close_day":
        from runtime.workflows.operator_close_day import run_operator_close_day
        return run_operator_close_day({}, vault_root)
    from runtime.workflows.operator_today import run_operator_today
    return run_operator_today({}, vault_root)


def _dispatch_graph_hygiene(task: dict, vault_root: Path) -> dict[str, Any]:
    from runtime.workflows.graph_hygiene import run_graph_hygiene
    return run_graph_hygiene({}, vault_root)


def _dispatch_graduate_ideas(task: dict, vault_root: Path) -> dict[str, Any]:
    from runtime.workflows.graduate_ideas import run_graduate_ideas
    return run_graduate_ideas({}, vault_root)


def _load_workflow_manifest(vault_root: Path, workflow_id: str) -> dict[str, Any]:
    """Load a workflow registry manifest for bus-dispatched workflow handlers."""
    manifest_path = vault_root / "runtime" / "workflows" / "registry" / f"{workflow_id}.yaml"
    if not manifest_path.exists():
        raise WorkflowExecutionError(f"workflow manifest not found: {manifest_path}")
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise WorkflowExecutionError("PyYAML is required to load workflow registry manifests") from exc
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WorkflowExecutionError(f"failed to parse workflow manifest {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise WorkflowExecutionError(f"workflow manifest must be a mapping: {manifest_path}")
    return manifest


def _dispatch_sbp(task: dict, vault_root: Path) -> dict[str, Any]:
    from runtime.workflows.sbp_strikezone_digest import run_sbp_strikezone_digest
    workflow = _infer_workflow(task, "scheduled-briefing") or "sbp_strikezone_digest"
    manifest = _load_workflow_manifest(vault_root, workflow)
    return run_sbp_strikezone_digest({}, vault_root, manifest=manifest)


def _safe_relative_json_path(vault_root: Path, raw_path: str) -> Path:
    """Resolve a declared source-pack input packet path under the vault root."""
    rel = Path(str(raw_path or "").strip())
    if not str(raw_path or "").strip():
        raise WorkflowExecutionError("source-pack-builder requires source_pack_inputs_path or source_pack_inputs_json.")
    if rel.is_absolute() or ".." in rel.parts:
        raise WorkflowExecutionError("source-pack-builder input packet path must be vault-relative and may not traverse upward.")
    resolved = (vault_root / rel).resolve()
    root_resolved = vault_root.resolve()
    if root_resolved not in (resolved, *resolved.parents):
        raise WorkflowExecutionError("source-pack-builder input packet path escaped the vault root.")
    return resolved


def _source_pack_inputs_from_task(task: dict, vault_root: Path) -> dict[str, Any]:
    """Load the bounded source-pack-builder input envelope declared by a bus task."""
    notes = _parse_notes(task.get("notes") or "")
    raw_json = notes.get("source_pack_inputs_json")
    raw_path = notes.get("source_pack_inputs_path")

    if raw_json:
        try:
            inputs = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise WorkflowExecutionError(f"source-pack-builder input JSON is invalid: {exc}") from exc
    elif raw_path:
        packet_path = _safe_relative_json_path(vault_root, raw_path)
        if not packet_path.exists():
            raise WorkflowExecutionError(f"source-pack-builder input packet not found: {raw_path}")
        try:
            inputs = json.loads(packet_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WorkflowExecutionError(f"source-pack-builder input packet is invalid JSON: {exc}") from exc
    else:
        raise WorkflowExecutionError("source-pack-builder requires source_pack_inputs_path or source_pack_inputs_json.")

    if not isinstance(inputs, dict):
        raise WorkflowExecutionError("source-pack-builder input envelope must be a JSON object.")

    normalized = dict(inputs)
    normalized.setdefault("acquirer_identity", "OpenClaw")
    normalized.setdefault("acquirer_trust_tier_ceiling", 2)
    normalized.setdefault("adapter_id", "openclaw")
    normalized.setdefault("trigger", "bus")
    return normalized


def _dispatch_source_pack_builder(task: dict, vault_root: Path) -> dict[str, Any]:
    from runtime.acquisition.source_pack_builder import run_source_pack_builder
    return run_source_pack_builder(_source_pack_inputs_from_task(task, vault_root), vault_root)


def _dispatch_chat(task: dict, vault_root: Path) -> dict[str, Any]:
    """Handle a `chat` task type.

    The cycle has already claimed and marked the task in_progress before calling this.
    This handler generates the response and returns it for _post_result to write back.
    No provider or API key is hardcoded — the runtime uses whatever it is configured with.
    """
    run_iso = _now_iso()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    task_id = str(task["task_id"])
    message = (task.get("request") or "")[:2000].strip() or "(no message)"
    annotations = _parse_notes(task.get("notes"))
    session_id = annotations.get("session_id") or ""

    runtime_reply = _openclaw_runtime_chat(message, session_id=session_id, vault_root=vault_root)

    if runtime_reply:
        response_text = runtime_reply
        runtime_handled = True
    else:
        response_text = (
            "[OpenClaw bounded ack] Chat message received and claimed by OpenClaw watch loop. "
            f"Message: {message}\n\n"
            "OpenClaw runtime execution is not currently active or returned no response. "
            "No vault mutations, credential reads, external API calls, shell commands, "
            "or canonical promotions were performed."
        )
        runtime_handled = False

    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in task_id)
    safe_id = (safe_id.strip("-_") or "task")[:24]
    audit_filename = f"{today}-openclaw-chat-{safe_id}.md"
    audit_content = (
        f"---\ntype: agent-activity\nworkflow: openclaw_watch\ntask_type: chat\n"
        f"task_id: {task_id}\nruntime: OpenClaw\ndate: {run_iso}\n"
        f"runtime_handled: {str(runtime_handled).lower()}\nauthority: bus-result-only\n---\n\n"
        f"# OpenClaw Chat Response — {task_id}\n\n"
        f"**Runtime handled:** {runtime_handled}\n\n"
        "No vault mutations, external API calls beyond the runtime's own configured provider, "
        "shell commands, credential reads, or canonical promotions were performed.\n"
    )
    return {
        "task_id": task_id,
        "task_type": "chat",
        "status": "done",
        "summary": response_text[:500],
        "runtime_handled": runtime_handled,
        "response_preview": response_text[:400],
        "writebacks": [{"path": f"07_LOGS/Agent-Activity/{audit_filename}", "content": audit_content}],
    }


def _openclaw_runtime_chat(message: str, *, session_id: str = "", vault_root: Path | None = None) -> str | None:
    """OpenClaw chat stub — bus-dispatch-only runtime.

    OpenClaw must not own provider fallback logic. Chat synthesis for OpenClaw
    routes via the Agent Bus to Hermes. Until bus-based chat coordination is
    built, this returns None so the caller falls back to a bounded ack.
    """
    del message, session_id, vault_root
    return None


# Extensible dispatch table — add new OpenClaw handlers here as they are built.
# "review" is intentionally absent: OpenClaw is secondary reviewer;
# review tasks go to Hermes. If Hermes is stale, bus.mark_stale_tasks()
# reclaims them and they can be re-routed. Secondary review dispatch is Phase 10.
_TASK_DISPATCH: dict[str, Any] = {
    "operator-briefing": _dispatch_operator_briefing,
    "graph-hygiene": _dispatch_graph_hygiene,
    "vault-maintenance": _dispatch_graduate_ideas,
    "scheduled-briefing": _dispatch_sbp,
    "source-pack-builder": _dispatch_source_pack_builder,
    "chat": _dispatch_chat,
}


def _claim_and_mark_inprogress(task: dict, vault_root: Path, runtime_instance_id: str | None = None) -> bool:
    """Claim the task as OpenClaw and mark in_progress. Returns True if claimed."""
    from runtime.agent_bus.bus import claim_task, update_task_status
    result = claim_task(
        vault_root,
        task_id=task["task_id"],
        runtime="OpenClaw",
        runtime_instance_id=runtime_instance_id,
    )
    if not result.get("claimed"):
        return False
    update_task_status(
        vault_root,
        task_id=task["task_id"],
        runtime="OpenClaw",
        status="in_progress",
        event_type="started",
        message="OpenClaw watch: dispatching task.",
    )
    return True


def _post_result(task: dict, vault_root: Path, handler_result: dict) -> None:
    """Post done + summary back to bus after successful dispatch."""
    from runtime.agent_bus.bus import update_task_status
    summary = str(handler_result.get("summary", handler_result.get("status", "completed")))[:500]
    update_task_status(
        vault_root,
        task_id=task["task_id"],
        runtime="OpenClaw",
        status="done",
        event_type="result_attached",
        message=f"OpenClaw watch: handler completed. {summary}",
    )


def _escalate_unhandled(task: dict, vault_root: Path, reason: str) -> None:
    """Mark task blocked with escalation notice."""
    from runtime.agent_bus.bus import update_task_status
    update_task_status(
        vault_root,
        task_id=task["task_id"],
        runtime="OpenClaw",
        status="blocked",
        event_type="blocked",
        message=f"OpenClaw watch: {reason}",
    )


# ── Cycle execution ───────────────────────────────────────────────────────────

def _run_one_cycle(
    vault_root: Path,
    *,
    max_tasks_per_cycle: int,
    dry_run: bool,
    now_iso: str,
    runtime_instance_id: str | None = None,
    control_surface: str | None = None,
    control_surface_key: str | None = None,
) -> dict[str, Any]:
    from runtime.agent_bus.bus import list_tasks, upsert_heartbeat

    heartbeat_kwargs = {
        "runtime_instance_id": runtime_instance_id,
        "heartbeat_scope": "instance" if runtime_instance_id else "runtime",
        "control_surface": control_surface,
        "control_surface_key": control_surface_key,
    }

    upsert_heartbeat(
        vault_root,
        runtime="OpenClaw",
        status="idle",
        health="ok",
        summary="openclaw_watch: polling for open tasks",
        now_iso=now_iso,
        **heartbeat_kwargs,
    )

    open_tasks = list_tasks(vault_root, recipient="OpenClaw", status="open")
    to_process = open_tasks[:max_tasks_per_cycle]

    dispatched: list[dict] = []
    escalated: list[dict] = []
    all_writebacks: list[dict] = []

    for task in to_process:
        task_type = _infer_task_type(task)
        handler = _TASK_DISPATCH.get(task_type)

        if dry_run:
            dispatched.append({
                "task_id": task["task_id"],
                "task_type": task_type,
                "status": "dry_run",
                "handler": handler.__name__ if handler else None,
            })
            continue

        if handler is None:
            reason = (
                f"no handler registered for task_type='{task_type}' "
                f"(intent='{task.get('intent', '?')}'). Operator intervention required."
            )
            claimed = _claim_and_mark_inprogress(task, vault_root, runtime_instance_id)
            if claimed:
                _escalate_unhandled(task, vault_root, reason)
            escalated.append({"task_id": task["task_id"], "task_type": task_type, "reason": reason})
            continue

        try:
            if not _claim_and_mark_inprogress(task, vault_root, runtime_instance_id):
                continue  # Already claimed by another runner — skip silently
            result = handler(task, vault_root)
            _post_result(task, vault_root, result)
            dispatched.append({"task_id": task["task_id"], "task_type": task_type, "status": "done"})
            all_writebacks.extend(result.get("writebacks") or [])
        except Exception as exc:
            # Capture per-task failures — do not abort the cycle
            try:
                _escalate_unhandled(task, vault_root, f"handler raised: {exc}")
            except Exception:
                pass
            escalated.append({"task_id": task["task_id"], "task_type": task_type, "error": str(exc)})

    upsert_heartbeat(
        vault_root,
        runtime="OpenClaw",
        status="busy" if dispatched else "idle",
        health="ok",
        summary=(
            f"openclaw_watch: dispatched={len(dispatched)} "
            f"escalated={len(escalated)} "
            f"open_remaining={len(open_tasks) - len(to_process)}"
        ),
        now_iso=_now_iso(),
        **heartbeat_kwargs,
    )

    return {
        "open_count": len(open_tasks),
        "processed_count": len(to_process),
        "dispatched": dispatched,
        "escalated": escalated,
        "writebacks": all_writebacks,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def run_openclaw_watch(inputs: dict[str, Any], vault_root: Path | str) -> dict[str, Any]:
    """
    OpenClaw bus watch loop — claim and dispatch open tasks addressed to OpenClaw.

    If interval_seconds is provided, loops indefinitely until interrupted.
    If omitted (or None), runs a single cycle and returns.

    Raises WorkflowExecutionError on unrecoverable setup errors.
    Individual dispatch failures are captured per-task and do not abort the loop.
    """
    root = Path(vault_root)

    interval_seconds: int | None = inputs.get("interval_seconds")
    max_tasks_per_cycle: int = int(inputs.get("max_tasks_per_cycle", 3))
    dry_run: bool = bool(inputs.get("dry_run", False))
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
                dry_run=dry_run,
                now_iso=now,
                runtime_instance_id=runtime_instance_id,
                control_surface=control_surface,
                control_surface_key=control_surface_key,
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
                "dry_run": dry_run,
            })

            if interval_seconds is None:
                break
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        pass

    return {
        "cycles_run": cycles_run,
        "tasks_dispatched": tasks_dispatched,
        "tasks_escalated": tasks_escalated,
        "cycle_summaries": cycle_summaries,
        "writebacks": all_writebacks,
    }
