"""Agent-bus command handlers for the canonical ChaseOS CLI.

Parser registration remains in ``runtime.cli.main``. This module only owns the
implementation for the agent-bus command family so the canonical entrypoint can
stay authoritative without keeping every handler in one giant file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runtime.capture.capture import _detect_vault_root
from runtime.agent_bus.bus import (
    list_tasks as agent_bus_list_tasks,
    list_heartbeats as agent_bus_list_heartbeats,
    get_bus_mode as agent_bus_get_bus_mode,
    claim_task as agent_bus_claim_task,
    update_task_status as agent_bus_update_task_status,
    upsert_heartbeat as agent_bus_upsert_heartbeat,
    mark_stale_tasks as agent_bus_mark_stale_tasks,
    watch_once as agent_bus_watch_once,
    run_watch_loop as agent_bus_run_watch_loop,
    init_db as agent_bus_init_db,
    create_task as agent_bus_create_task,
    cleanup_tasks as agent_bus_cleanup_tasks,
    translate_discord_control_plane_request as agent_bus_translate_discord_control_plane_request,
    reclaim_task as agent_bus_reclaim_task,
)
from runtime.agent_bus.backend_loader import get_backend
from runtime.agent_bus.capabilities import load_all_capabilities, CapabilityError, resolve_runtime_identity
from runtime.agent_bus.router import route_task_type, get_stale_runtimes, get_runtime_liveness, RouterError
from runtime.adapters.codex.daemon import (
    MockCodexExecutor,
    SubprocessCodexExecutor,
    get_codex_daemon_readiness,
    run_codex_daemon_loop,
    run_codex_daemon_once,
)
from runtime.agents.agent_harness_readiness import build_agent_harness_readiness
from runtime.chaseos_gate import check_runtime_operation


def _resolve_vault(vault_root_arg: str | None) -> Path:
    if vault_root_arg:
        return Path(vault_root_arg)
    return _detect_vault_root()


def _runtime_lifecycle_summary(runtime_name: str, caps_bus_name: str) -> dict[str, object]:
    """Return declared lifecycle facts without treating offline state as unknown identity."""
    try:
        from runtime.lifecycle.health_cli import load_lifecycle_record

        record = load_lifecycle_record(runtime_name)
    except Exception:
        return {
            "identity_registered": True,
            "lifecycle_record_present": False,
            "lifecycle_mode": None,
            "coordination_watch_enabled": None,
            "declared_bus_name": caps_bus_name,
        }

    coordination_watch = record.get("coordination_watch") or {}
    return {
        "identity_registered": True,
        "lifecycle_record_present": True,
        "lifecycle_mode": record.get("lifecycle_mode"),
        "coordination_watch_enabled": coordination_watch.get("enabled"),
        "declared_bus_name": coordination_watch.get("runtime_name") or caps_bus_name,
    }


def _block_runtime_operation(args: argparse.Namespace, operation: str, reason: str) -> int:
    if getattr(args, "output_json", False):
        print(json.dumps({"allowed": False, "operation": operation, "reason": reason}, indent=2))
    else:
        print(f"ERROR: runtime policy denied {operation}: {reason}", file=sys.stderr)
    return 1


def _block_bus_validation_error(args: argparse.Namespace, operation: str, exc: Exception) -> int:
    """Return a structured CLI failure for bus runtime/capability validation errors.

    Agent Bus APIs intentionally fail closed on unknown runtime identities or
    malformed capability registries. Canonical CLI handlers should surface that
    as a normal command failure, not leak a traceback before JSON-envelope
    wrapping can occur.
    """
    reason = str(exc)
    if getattr(args, "output_json", False):
        print(json.dumps({"ok": False, "operation": operation, "reason": reason}, indent=2))
    else:
        print(f"ERROR: {reason}", file=sys.stderr)
    return 1


class _RuntimePolicyResolutionError(RuntimeError):
    """Raised when runtime identity cannot be trusted for a Gate policy check."""


def _canonical_policy_runtime(args: argparse.Namespace, runtime_name: str | None) -> str | None:
    """Return the canonical bus runtime name for Gate policy checks when possible.

    CLI parser surfaces intentionally accept capability-declared runtime aliases
    such as ``Axiom-Codex``. Gate policy manifests are keyed by canonical adapter
    identities, so normalize aliases before policy lookup while preserving the
    original runtime string for the Agent Bus API call itself.
    """
    if not runtime_name:
        return runtime_name
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
        return resolve_runtime_identity(vault_root, runtime_name).bus_name
    except CapabilityError as exc:
        raise _RuntimePolicyResolutionError(
            f"Runtime capability resolution failed for '{runtime_name}': {exc}"
        ) from exc
    except (ValueError, RuntimeError):
        return runtime_name


def _check_runtime_operation_or_block(
    args: argparse.Namespace,
    operation: str,
    *,
    actor_adapter_id: str | None = None,
    target_runtime: str | None = None,
    coordination_sensitive: bool | None = None,
    via_bus: bool | None = None,
) -> int | None:
    try:
        policy_actor_adapter_id = _canonical_policy_runtime(args, actor_adapter_id)
        policy_target_runtime = _canonical_policy_runtime(args, target_runtime)
    except _RuntimePolicyResolutionError as exc:
        return _block_runtime_operation(args, operation, str(exc))

    allowed, reason = check_runtime_operation(
        operation,
        actor_adapter_id=policy_actor_adapter_id,
        target_runtime=policy_target_runtime,
        coordination_sensitive=coordination_sensitive,
        via_bus=via_bus,
    )
    if allowed:
        return None
    return _block_runtime_operation(args, operation, reason)


def cmd_agent_bus_status(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    agent_bus_init_db(vault_root)
    tasks = agent_bus_list_tasks(vault_root)
    summary = {
        "task_count": len(tasks),
        "open_count": sum(1 for t in tasks if t["status"] == "open"),
        "claimed_count": sum(1 for t in tasks if t["status"] == "claimed"),
        "in_progress_count": sum(1 for t in tasks if t["status"] == "in_progress"),
        "blocked_count": sum(1 for t in tasks if t["status"] == "blocked"),
        "review_count": sum(1 for t in tasks if t["status"] == "review"),
        "done_count": sum(1 for t in tasks if t["status"] == "done"),
        "expired_count": sum(1 for t in tasks if t["status"] == "expired"),
    }

    if getattr(args, "output_json", False):
        print(json.dumps(summary, indent=2))
        return 0

    print("ChaseOS Agent Bus")
    print()
    print(f"  Tasks:      {summary['task_count']}")
    print(f"  Open:       {summary['open_count']}")
    print(f"  Claimed:    {summary['claimed_count']}")
    print(f"  In progress:{summary['in_progress_count']}")
    print(f"  Blocked:    {summary['blocked_count']}")
    print(f"  Review:     {summary['review_count']}")
    print(f"  Done:       {summary['done_count']}")
    print(f"  Expired:    {summary['expired_count']}")
    return 0


def cmd_agent_bus_task_list(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        tasks = agent_bus_list_tasks(
            vault_root,
            recipient=getattr(args, "recipient", None),
            status=getattr(args, "status", None),
            owner=getattr(args, "owner", None),
        )
    except (ValueError, CapabilityError) as exc:
        return _block_bus_validation_error(args, "agent_bus.task.list", exc)
    matched_count = len(tasks)
    limit = getattr(args, "limit", None)
    if limit is not None:
        tasks = tasks[: max(0, int(limit))]

    if getattr(args, "output_json", False):
        print(json.dumps({"tasks": tasks, "count": len(tasks), "matched_count": matched_count}, indent=2))
        return 0

    if not tasks:
        print("No matching agent-bus tasks.")
        return 0

    for task in tasks:
        owner = task.get("owner") or "-"
        print(f"[{task['status']}] {task['task_id']}  {task.get('sender', task.get('from', '?'))} -> {task.get('recipient', task.get('to', '?'))}  owner={owner}")
        print(f"  request: {task['request']}")
        print(f"  expected: {task['expected_output']}")
        print(f"  updated: {task['updated_at']}")
        print()
    return 0


def cmd_agent_bus_task_claim(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.task.claim",
        actor_adapter_id=args.runtime,
    )
    if blocked is not None:
        return blocked

    try:
        result = agent_bus_claim_task(
            vault_root,
            task_id=args.task_id,
            runtime=args.runtime,
            runtime_instance_id=getattr(args, "runtime_instance_id", None),
        )
    except (ValueError, CapabilityError) as exc:
        return _block_bus_validation_error(args, "agent_bus.task.claim", exc)
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
        return 0 if result.get("claimed") else 1

    if result.get("claimed"):
        owner_instance = result.get("owner_instance")
        suffix = f" [{owner_instance}]" if owner_instance else ""
        print(f"Claimed task: {args.task_id} as {args.runtime}{suffix}")
        return 0

    print(f"ERROR: {result.get('reason', 'claim failed')}", file=sys.stderr)
    return 1


def cmd_agent_bus_task_update(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.task.update",
        actor_adapter_id=args.runtime,
    )
    if blocked is not None:
        return blocked

    event_type_map = {
        "in_progress": "started",
        "blocked": "blocked",
        "review": "review_requested",
        "done": "completed",
        "cancelled": "cancelled",
        "claimed": "claimed",
        "open": "notice",
        "expired": "expired",
    }
    artifacts = getattr(args, "artifact", None) or []
    explicit_event_type = getattr(args, "event_type", None)
    try:
        result = agent_bus_update_task_status(
            vault_root,
            task_id=args.task_id,
            runtime=args.runtime,
            status=args.status,
            event_type=explicit_event_type or event_type_map[args.status],
            message=args.message,
            artifacts=artifacts,
        )
    except (ValueError, CapabilityError) as exc:
        return _block_bus_validation_error(args, "agent_bus.task.update", exc)
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
        return 0 if result.get("updated") else 1

    if result.get("updated"):
        print(f"Updated task: {args.task_id} -> {args.status}")
        return 0

    print(f"ERROR: {result.get('reason', 'update failed')}", file=sys.stderr)
    return 1


def cmd_agent_bus_task_cleanup(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.task.cleanup",
        actor_adapter_id=args.runtime,
    )
    if blocked is not None:
        return blocked

    try:
        result = agent_bus_cleanup_tasks(
            vault_root,
            runtime=args.runtime,
            recipient=getattr(args, "recipient", None),
            sender=getattr(args, "sender", None),
            owner=getattr(args, "owner", None),
            status=getattr(args, "status", None),
            request_exact=getattr(args, "request_exact", None),
            request_contains=getattr(args, "request_contains", None),
            updated_before=getattr(args, "updated_before", None),
            work_fingerprint=getattr(args, "work_fingerprint", None),
            conversation_key=getattr(args, "conversation_key", None),
            origin_message_id=getattr(args, "origin_message_id", None),
            limit=getattr(args, "limit", None),
            reason=getattr(args, "reason", "Queue hygiene cleanup"),
            apply=getattr(args, "apply", False),
        )
    except (ValueError, CapabilityError) as exc:
        return _block_bus_validation_error(args, "agent_bus.task.cleanup", exc)
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok", True) else 1

    print(
        f"Task cleanup preview={not result.get('apply', False)} matched={result.get('matched_count', 0)} "
        f"selected={result.get('selected_count', 0)} updated={result.get('updated_count', 0)}"
    )
    for task_id in result.get("updated_task_ids", []):
        print(f"  - {task_id}")
    return 0 if result.get("ok", True) else 1


def cmd_agent_bus_heartbeat(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.heartbeat",
        actor_adapter_id=args.runtime,
    )
    if blocked is not None:
        return blocked

    try:
        result = agent_bus_upsert_heartbeat(
            vault_root,
            runtime=args.runtime,
            status=args.status,
            health=args.health,
            current_task_id=getattr(args, "current_task_id", None),
            summary=getattr(args, "summary", None),
            runtime_instance_id=getattr(args, "runtime_instance_id", None),
            heartbeat_scope=getattr(args, "heartbeat_scope", "runtime"),
            control_surface=getattr(args, "control_surface", None),
            control_surface_key=getattr(args, "control_surface_key", None),
        )
    except (ValueError, CapabilityError) as exc:
        return _block_bus_validation_error(args, "agent_bus.heartbeat", exc)
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"Heartbeat updated: {args.runtime} [{args.status}/{args.health}]")
    return 0


def cmd_agent_bus_expire_stale(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(args, "agent_bus.expire_stale")
    if blocked is not None:
        return blocked

    result = agent_bus_mark_stale_tasks(vault_root, max_age_seconds=args.max_age_seconds)
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"Expired tasks: {result['expired_count']}")
        if result["task_ids"]:
            for task_id in result["task_ids"]:
                print(f"  - {task_id}")
    return 0


def cmd_agent_bus_watch(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.watch",
        actor_adapter_id=args.runtime,
    )
    if blocked is not None:
        return blocked

    once = getattr(args, "once", False)
    interval = getattr(args, "interval", None)
    claim_next = getattr(args, "claim_next", False)
    stale_after = getattr(args, "stale_after_seconds", None)
    output_json = getattr(args, "output_json", False)

    if not once and interval is None:
        print("ERROR: specify --once or --interval N", file=sys.stderr)
        return 1

    if once:
        try:
            result = agent_bus_watch_once(
                vault_root,
                runtime=args.runtime,
                claim_next=claim_next,
                stale_after_seconds=stale_after,
                runtime_instance_id=getattr(args, "runtime_instance_id", None),
                control_surface=getattr(args, "control_surface", None),
                control_surface_key=getattr(args, "control_surface_key", None),
            )
        except (ValueError, CapabilityError) as exc:
            return _block_bus_validation_error(args, "agent_bus.watch", exc)
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Agent-bus watch: {args.runtime}")
            print(f"  Open tasks:        {result['open_task_count']}")
            print(f"  Claimed by runtime:{result['claimed_task_count']}")
            print(f"  Expired this pass: {result['expired_count']}")
            if result.get("claimed_task_id"):
                print(f"  Claimed next task: {result['claimed_task_id']}")
        return 0

    try:
        if not output_json:
            print(f"Agent-bus watch loop started for {args.runtime}. Ctrl+C to stop.")
        try:
            agent_bus_run_watch_loop(
                vault_root,
                runtime=args.runtime,
                interval_seconds=interval,
                claim_next=claim_next,
                stale_after_seconds=stale_after,
                runtime_instance_id=getattr(args, "runtime_instance_id", None),
                control_surface=getattr(args, "control_surface", None),
                control_surface_key=getattr(args, "control_surface_key", None),
            )
        except (ValueError, CapabilityError) as exc:
            return _block_bus_validation_error(args, "agent_bus.watch", exc)
    except KeyboardInterrupt:
        if not output_json:
            print()
            print("Agent-bus watch loop stopped.")
        return 0
    return 0


def cmd_agent_bus_codex_daemon(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    executor_name = getattr(args, "executor", "codex")
    executor = MockCodexExecutor() if executor_name == "mock" else SubprocessCodexExecutor(
        codex_binary=getattr(args, "codex_binary", "codex"),
        timeout_seconds=getattr(args, "timeout_seconds", 900),
    )
    task_type = getattr(args, "task_type", "code.patch")
    allow_shell_commands = not bool(getattr(args, "no_shell_commands", False))
    stale_after = getattr(args, "stale_after_seconds", None)
    output_json = getattr(args, "output_json", False)

    if getattr(args, "readiness", False):
        result = get_codex_daemon_readiness(
            vault_root,
            codex_binary=getattr(args, "codex_binary", "codex"),
        )
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print("Codex bus daemon readiness")
            print(f"  Ready:        {result['ok']}")
            print(f"  Bus mode:     {result['bus_mode']}")
            print(f"  Codex binary: {result.get('codex_binary_path') or '(not found)'}")
            print(f"  Capabilities: {', '.join(result.get('capability_task_types', [])) or '(none)'}")
            print(f"  Open tasks:   {result['open_task_count']}")
            print(f"  Live command: {result['live_command']}")
        return 0 if result.get("ok") else 1

    if getattr(args, "once", False):
        result = run_codex_daemon_once(
            vault_root,
            executor=executor,
            task_type=task_type,
            allow_shell_commands=allow_shell_commands,
            stale_after_seconds=stale_after,
        )
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print("Codex bus daemon: one cycle")
            print(f"  Claimed task: {result.get('claimed_task_id') or '-'}")
            if result.get("claimed_task_id"):
                print(f"  Adapter event: {result.get('adapter_event_type')}")
                print(f"  Bus status:    {result.get('bus_status')}")
                print(f"  Run dir:       {result.get('run_dir')}")
        return 0 if result.get("ok") else 1

    interval = getattr(args, "interval", None)
    if interval is None:
        print("ERROR: specify --once or --interval N", file=sys.stderr)
        return 1

    try:
        if not output_json:
            print("Codex bus daemon loop started. Ctrl+C to stop.")
        run_codex_daemon_loop(
            vault_root,
            interval_seconds=interval,
            executor=executor,
            task_type=task_type,
            allow_shell_commands=allow_shell_commands,
            stale_after_seconds=stale_after,
        )
    except KeyboardInterrupt:
        if not output_json:
            print()
            print("Codex bus daemon loop stopped.")
        return 0
    return 0


def cmd_agent_bus_route(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    task_type = args.task_type
    try:
        result = route_task_type(task_type, vault_root)
    except RouterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps({
            "task_type": result.task_type,
            "recommended": result.recommended,
            "eligible_runtimes": result.eligible_runtimes,
            "live_runtimes": result.live_runtimes,
            "stale_runtimes": result.stale_runtimes,
            "all_registered": result.all_registered,
            "reason": result.reason,
        }, indent=2))
        return 0 if result.recommended else 1

    print(f"Route: {task_type}")
    print(f"  Recommended:  {result.recommended or '(none — no live eligible runtime)'}")
    print(f"  Eligible:     {', '.join(result.eligible_runtimes) or '(none)'}")
    print(f"  Live:         {', '.join(result.live_runtimes) or '(none)'}")
    if result.stale_runtimes:
        print(f"  Stale:        {', '.join(result.stale_runtimes)}")
    print(f"  Reason:       {result.reason}")
    return 0 if result.recommended else 1


def cmd_agent_bus_harness_readiness(args: argparse.Namespace) -> int:
    """Show read-only readiness for a runtime harness/tool-calling worker."""
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = build_agent_harness_readiness(
        vault_root,
        runtime=getattr(args, "runtime", None) or "hermes",
    )
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"Agent harness readiness: {payload['runtime_id']} — {payload['harness_status']}")
        print("  authority: read-only; no tool call, provider call, terminal execution, Agent Bus mutation, or canonical writeback")
        for reason in payload.get("blocked_reasons") or []:
            print(f"  blocked: {reason}")
        for action in payload.get("next_actions") or []:
            print(f"  next: {action}")
    return 0 if payload.get("harness_status") == "ready_for_operator_gated_activation" else 2


def cmd_agent_bus_runtimes(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        all_caps = load_all_capabilities(vault_root)
    except CapabilityError as exc:
        print(f"ERROR loading capabilities: {exc}", file=sys.stderr)
        return 1

    liveness = get_runtime_liveness(vault_root)
    stale = get_stale_runtimes(vault_root)
    heartbeat_rows = get_backend(vault_root).list_heartbeats()

    if getattr(args, "output_json", False):
        out = []
        for runtime_name, caps in sorted(all_caps.items()):
            live = liveness.get(caps.bus_name)
            runtime_heartbeats = [
                row for row in heartbeat_rows if row.get("runtime") == caps.bus_name
            ]
            lifecycle = _runtime_lifecycle_summary(runtime_name, caps.bus_name)
            out.append({
                "runtime_name": runtime_name,
                "bus_name": caps.bus_name,
                "display_name": caps.display_name,
                "description": caps.description,
                "identity_registered": lifecycle["identity_registered"],
                "lifecycle_record_present": lifecycle["lifecycle_record_present"],
                "lifecycle_mode": lifecycle["lifecycle_mode"],
                "coordination_watch_enabled": lifecycle["coordination_watch_enabled"],
                "declared_bus_name": lifecycle["declared_bus_name"],
                "reachability_state": "stale" if caps.bus_name in stale else "reachable",
                "handles": [
                    {"task_type": c.task_type, "priority": c.priority}
                    for c in caps.handles
                ],
                "max_concurrent_tasks": caps.max_concurrent_tasks,
                "heartbeat_stale_seconds": caps.heartbeat_stale_seconds,
                "is_stale": caps.bus_name in stale,
                "last_seen": live.last_seen if live else None,
                "status": live.status if live else None,
                "health": live.health if live else None,
                "heartbeat_instances": runtime_heartbeats,
                "heartbeat_instance_count": len(runtime_heartbeats),
            })
        print(json.dumps(out, indent=2))
        return 0

    if not all_caps:
        print("No runtimes registered (no capabilities.yaml files found).")
        return 0

    for runtime_name, caps in sorted(all_caps.items()):
        live = liveness.get(caps.bus_name)
        lifecycle = _runtime_lifecycle_summary(runtime_name, caps.bus_name)
        stale_flag = " [STALE]" if caps.bus_name in stale else ""
        age_str = ""
        if live and live.age_seconds is not None:
            age_str = f"  last seen {int(live.age_seconds)}s ago"
        print(f"{caps.display_name} ({caps.bus_name}){stale_flag}{age_str}")
        print(f"  {caps.description}")
        print(
            "  identity: registered; "
            f"lifecycle: {lifecycle.get('lifecycle_mode') or 'undeclared'}; "
            f"reachability: {'stale/offline' if caps.bus_name in stale else 'reachable'}"
        )
        for cap in caps.handles:
            print(f"  - {cap.task_type} [{cap.priority}]")
        print()
    return 0


def cmd_agent_bus_task_create(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.task.create",
        actor_adapter_id=args.sender,
        target_runtime=args.recipient,
        coordination_sensitive=True,
        via_bus=True,
    )
    if blocked is not None:
        return blocked

    ingress_context = {
        key: value
        for key, value in {
            "source_platform": getattr(args, "source_platform", None),
            "source_channel_id": getattr(args, "source_channel_id", None),
            "source_thread_id": getattr(args, "source_thread_id", None),
            "source_channel_class": getattr(args, "source_channel_class", None),
            "conversation_key": getattr(args, "conversation_key", None),
            "origin_message_id": getattr(args, "origin_message_id", None),
            "control_plane_route": getattr(args, "control_plane_route", None),
        }.items()
        if value is not None
    }
    execution_constraints = {
        key: value
        for key, value in {
            "allow_shell_commands": False if getattr(args, "no_shell_commands", False) else None,
            "allow_live_subprocess": False if getattr(args, "no_live_subprocess", False) else None,
            "write_policy": getattr(args, "write_policy", None),
            "allowed_write_paths": getattr(args, "allowed_write_path", None),
        }.items()
        if value is not None
    }

    result = agent_bus_create_task(
        vault_root,
        sender=args.sender,
        recipient=args.recipient,
        intent=getattr(args, "intent", "TASK"),
        priority=getattr(args, "priority", "normal"),
        request=args.request,
        expected_output=args.expected_output,
        notes=getattr(args, "notes", None),
        expires_at=getattr(args, "expires_at", None),
        ingress_context=ingress_context or None,
        work_fingerprint=getattr(args, "work_fingerprint", None),
        execution_constraints=execution_constraints or None,
    )
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
        return 0 if result.get("created") else 1
    if result.get("created"):
        print(f"Created task {result['task_id']} for {args.recipient}")
        return 0
    print(f"ERROR: {result.get('reason', 'create failed')}", file=sys.stderr)
    return 1


def cmd_agent_bus_ingress_discord(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.ingress.discord",
        target_runtime=args.recipient,
        coordination_sensitive=True,
        via_bus=True,
    )
    if blocked is not None:
        return blocked

    result = agent_bus_translate_discord_control_plane_request(
        vault_root,
        recipient=args.recipient,
        intent=getattr(args, "intent", "TASK"),
        priority=getattr(args, "priority", "normal"),
        request=args.request,
        expected_output=args.expected_output,
        notes=getattr(args, "notes", None),
        source_channel_id=args.source_channel_id,
        source_thread_id=getattr(args, "source_thread_id", None),
        source_channel_class=getattr(args, "source_channel_class", None),
        origin_message_id=getattr(args, "origin_message_id", None),
        control_plane_route=getattr(args, "control_plane_route", None),
        work_fingerprint=getattr(args, "work_fingerprint", None),
        coordination_sensitive=getattr(args, "coordination_sensitive", False),
    )
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
        return 0 if result.get("translated") or result.get("classification") == "advisory_only" else 1
    if result.get("translated"):
        print(f"Translated Discord ingress into task {result.get('task_id')} for {args.recipient}")
        return 0
    if result.get("classification") == "advisory_only":
        print(result.get("reason", "Discord ingress remains advisory."))
        return 0
    print(f"ERROR: {result.get('reason', 'Discord ingress translation failed')}", file=sys.stderr)
    return 1


def cmd_agent_bus_mode(args: argparse.Namespace) -> int:
    """Show the current agent bus backend mode (local or server)."""
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    mode = agent_bus_get_bus_mode(vault_root)
    config_path = vault_root / "runtime" / "agent_bus" / "bus_config.yaml"

    if getattr(args, "output_json", False):
        print(json.dumps({"mode": mode, "config_path": str(config_path)}, indent=2))
        return 0

    print(f"Agent bus mode: {mode}")
    print(f"Config:         {config_path}")
    if mode == "local":
        db_path = vault_root / "runtime" / "agent_bus" / "agent_bus.sqlite"
        print(f"Storage:        {db_path}")
    elif mode == "server":
        print("Storage:        server (HTTP/WebSocket — Phase 10)")
    return 0


def cmd_agent_bus_heartbeats(args: argparse.Namespace) -> int:
    """List current runtime heartbeat records."""
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    runtime_filter = getattr(args, "runtime", None)
    try:
        rows = agent_bus_list_heartbeats(vault_root, runtime=runtime_filter)
    except (ValueError, CapabilityError) as exc:
        return _block_bus_validation_error(args, "agent_bus.heartbeats", exc)

    if getattr(args, "output_json", False):
        print(json.dumps({"heartbeats": rows, "count": len(rows)}, indent=2))
        return 0

    if not rows:
        print("No heartbeat records found.")
        return 0

    for row in rows:
        runtime = row.get("runtime", "?")
        status = row.get("status", "?")
        health = row.get("health", "?")
        updated = row.get("updated_at", row.get("last_seen", "?"))
        summary = row.get("summary") or ""
        scope = row.get("heartbeat_scope", "runtime")
        stale_marker = ""
        print(f"{runtime} [{status}/{health}] scope={scope}  updated={updated}{stale_marker}")
        if summary:
            print(f"  {summary}")
    return 0


def cmd_agent_bus_reclaim(args: argparse.Namespace) -> int:
    try:
        vault_root = _resolve_vault(getattr(args, "vault_root", None))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    blocked = _check_runtime_operation_or_block(
        args,
        "agent_bus.task.reclaim",
        actor_adapter_id=args.runtime,
    )
    if blocked is not None:
        return blocked

    result = agent_bus_reclaim_task(
        vault_root,
        task_id=args.task_id,
        new_runtime=args.runtime,
        reason=getattr(args, "reason", "Operator-initiated reclaim.") or "Operator-initiated reclaim.",
    )
    if getattr(args, "output_json", False):
        print(json.dumps(result, indent=2))
        return 0 if result.get("reclaimed") else 1

    if result.get("reclaimed"):
        print(f"Reclaimed task {args.task_id} → {args.runtime} (was: {result.get('previous_owner', 'none')})")
        return 0
    print(f"ERROR: {result.get('reason', 'reclaim failed')}", file=sys.stderr)
    return 1
