"""Phase 11 Chat runtime-dispatch readiness contract.

This pass lets the Chat panel inspect whether a runtime-bound request could be
prepared for a future Agent Bus/AOR handoff. It does not create tasks, dispatch
workflows, mutate runtime lifecycle state, consume approvals, or write files.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from runtime.agent_bus.capabilities import CapabilityError, load_all_capabilities
from runtime.studio.phase11_chat_router_contract import build_phase11_chat_router_contract
from runtime.studio.runtime_cockpit_action_readiness import build_runtime_cockpit_action_readiness


MODEL_VERSION = "studio.phase11_chat_runtime_dispatch_readiness.v1"
SURFACE_ID = "phase11_chat_runtime_dispatch_readiness_contract"
PASS_ID = "phase11-chat-runtime-dispatch-readiness-contract"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / RUNTIME DISPATCH BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-browser-dispatch-readiness-contract"
APPROVAL_CLASS = "studio_chat_runtime_dispatch_approval_future"

RUNTIME_BOUND_INTENTS = {"runtime-task", "handoff", "scheduled-workflow"}
RUNTIME_NAME_HINTS = {
    "archon": "Archon",
    "codex": "Codex",
    "hermes": "Hermes",
    "openclaw": "OpenClaw",
}

POLICY_DOCS_CHECKED = [
    "06_AGENTS/ChaseOS-Deny-Default-Runtime-Policy.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Agent-Security-Model.md",
    "06_AGENTS/Browser-Operator-Policy.md",
    "06_AGENTS/Trust-Tiers.md",
    "runtime/policy/gateway_allowlists.json",
    "runtime/policy/protected_files.yaml",
]

_DENIED_ACTION_TO_DEPENDENCY_KEY = {
    "vault_write": "protected_file_write",
    "lifecycle_execution": "lifecycle_execution",
    "runtime_dispatch": "runtime_dispatch",
    "browser_or_shell_or_connector_authority": "browser_shell_connector_authority",
    "approval_consumption": "approval_consumption_execution",
    "protected_file_write": "protected_file_write",
    "hidden_memory_write": "canonical_knowledge_promotion",
    "credential_or_config_mutation": "credential_config_mutation",
    "source_pack_promotion": "source_pack_creation_promotion",
    "graph_mutation": "graph_canonical_mutation",
    "canonical_knowledge_promotion": "canonical_knowledge_promotion",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        data: dict[str, Any] = {}
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            if key and value.strip():
                data[key.strip()] = value.strip().strip('"')
        return data


def _bus_mode(vault: Path) -> dict[str, Any]:
    config_path = vault / "runtime" / "agent_bus" / "bus_config.yaml"
    config = _read_yaml_mapping(config_path)
    mode = str(config.get("mode") or "local").strip() or "local"
    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    return {
        "mode": mode,
        "config_path": "runtime/agent_bus/bus_config.yaml",
        "config_present": config_path.exists(),
        "sqlite_path": "runtime/agent_bus/agent_bus.sqlite",
        "sqlite_present": sqlite_path.exists(),
        "storage_initialized_by_this_contract": False,
    }


_SAFE_SQL_TABLES = frozenset({"tasks", "heartbeats", "events", "messages"})


def _safe_sql_count(sqlite_path: Path, table: str) -> int | None:
    # H-2 security fix: allowlist table names to prevent f-string SQL injection
    if table not in _SAFE_SQL_TABLES:
        return None
    if not sqlite_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")  # nosec — table in allowlist
            value = cur.fetchone()
            return int(value[0]) if value else 0
        finally:
            conn.close()
    except Exception:
        return None


def _agent_bus_snapshot(vault: Path) -> dict[str, Any]:
    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    mode = _bus_mode(vault)
    task_count = _safe_sql_count(sqlite_path, "tasks")
    heartbeat_count = _safe_sql_count(sqlite_path, "heartbeats")
    event_count = _safe_sql_count(sqlite_path, "events")
    blockers: list[str] = []
    if mode["mode"] != "local":
        blockers.append("agent_bus_non_local_backend_not_readable_by_static_contract")
    if not mode["sqlite_present"]:
        blockers.append("agent_bus_storage_not_present")
    return {
        **mode,
        "known_storage_readable": bool(mode["sqlite_present"]) and task_count is not None,
        "task_count": task_count,
        "heartbeat_count": heartbeat_count,
        "event_count": event_count,
        "task_write_allowed_now": False,
        "task_created": False,
        "task_claimed": False,
        "event_written": False,
        "blocked_reasons": blockers,
    }


def _capability_snapshot(vault: Path) -> dict[str, Any]:
    try:
        caps = load_all_capabilities(vault)
    except CapabilityError as exc:
        return {
            "ok": False,
            "runtime_count": 0,
            "runtimes": [],
            "blocked_reasons": [f"runtime_capability_manifest_error:{exc}"],
        }
    runtimes = []
    for runtime_name, cap in sorted(caps.items(), key=lambda item: item[0].lower()):
        runtimes.append(
            {
                "runtime_name": runtime_name,
                "bus_name": cap.bus_name,
                "display_name": cap.display_name,
                "heartbeat_stale_seconds": cap.heartbeat_stale_seconds,
                "max_concurrent_tasks": cap.max_concurrent_tasks,
                "priority_ceiling": cap.priority_ceiling,
                "handles": [
                    {
                        "task_type": handle.task_type,
                        "priority": handle.priority,
                        "notes": handle.notes,
                    }
                    for handle in cap.handles
                ],
            }
        )
    return {
        "ok": True,
        "runtime_count": len(runtimes),
        "runtimes": runtimes,
        "blocked_reasons": [] if runtimes else ["no_runtime_capability_manifests_found"],
    }


def _workflow_snapshot(vault: Path) -> dict[str, Any]:
    registry = vault / "runtime" / "workflows" / "registry"
    workflows: list[dict[str, Any]] = []
    if registry.is_dir():
        for path in sorted(registry.glob("*.yaml")):
            if path.name.startswith("_"):
                continue
            data = _read_yaml_mapping(path)
            workflows.append(
                {
                    "id": data.get("id") or path.stem,
                    "name": data.get("name") or path.stem,
                    "status": data.get("status") or "",
                    "task_type": data.get("task_type") or "",
                    "role_card": data.get("role_card") or "",
                    "trigger_type": data.get("trigger_type") or "",
                    "runtime_adapter": data.get("runtime_adapter") or "",
                    "filename": path.name,
                }
            )
    active = [item for item in workflows if item.get("status") == "active"]
    return {
        "registry_present": registry.is_dir(),
        "workflow_count": len(workflows),
        "active_workflow_count": len(active),
        "active_workflow_ids": [str(item.get("id")) for item in active[:25]],
        "workflow_dispatch_allowed_now": False,
        "workflow_dispatched": False,
    }


def _requested_runtime(message: str, requested_runtime_id: str | None, caps: dict[str, Any]) -> dict[str, Any]:
    runtimes = caps.get("runtimes") or []
    by_lower = {str(item.get("bus_name") or item.get("runtime_name") or "").lower(): item for item in runtimes}
    requested = str(requested_runtime_id or "").strip()
    if requested:
        key = requested.lower()
        matched = by_lower.get(key)
        return {
            "requested_runtime_id": requested,
            "selected_runtime_id": (matched or {}).get("bus_name") or requested,
            "selection_reason": "operator_requested_runtime",
            "runtime_known": bool(matched),
            "selected_runtime": matched,
        }
    lowered = message.lower()
    for hint, bus_name in RUNTIME_NAME_HINTS.items():
        if hint in lowered and bus_name.lower() in by_lower:
            return {
                "requested_runtime_id": "",
                "selected_runtime_id": bus_name,
                "selection_reason": f"message_mentions_{hint}",
                "runtime_known": True,
                "selected_runtime": by_lower[bus_name.lower()],
            }
    default = by_lower.get("codex") or (runtimes[0] if runtimes else None)
    return {
        "requested_runtime_id": "",
        "selected_runtime_id": (default or {}).get("bus_name") or "",
        "selection_reason": "default_runtime_preview",
        "runtime_known": bool(default),
        "selected_runtime": default,
    }


def _requested_action(message: str, requested_action: str | None, selected_runtime: dict[str, Any] | None) -> dict[str, Any]:
    requested = str(requested_action or "").strip()
    handles = list((selected_runtime or {}).get("handles") or [])
    task_types = [str(item.get("task_type") or "") for item in handles]
    if requested:
        return {
            "requested_action": requested,
            "selected_task_type": requested,
            "selection_reason": "operator_requested_action",
            "task_type_supported_by_runtime": requested in task_types,
        }
    lowered = message.lower()
    wanted = "test.run" if "test" in lowered else "code.patch" if "patch" in lowered or "fix" in lowered else "repo.inspect"
    selected = wanted if wanted in task_types else (task_types[0] if task_types else "runtime.handoff")
    return {
        "requested_action": "",
        "selected_task_type": selected,
        "selection_reason": "message_inferred_task_type" if selected == wanted else "first_declared_runtime_capability",
        "task_type_supported_by_runtime": selected in task_types,
    }


def _runtime_cockpit_summary(vault: Path) -> dict[str, Any]:
    """Return a no-write cockpit posture summary without initializing Studio cockpit.

    The full runtime cockpit model fans out through dashboard, Pulse, lifecycle,
    port-probing, and Agent Bus readers. That is useful for the Studio cockpit,
    but Phase 11 Chat runtime-dispatch readiness only needs proof that cockpit
    authority is not consumed here. Calling the full cockpit made the static QA
    entrypoint slow and could touch lower-phase runtime state, so this summary is
    intentionally bounded and read-only regardless of whether Agent Bus storage
    already exists.
    """

    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    return {
        "ok": True,
        "surface": "studio_runtime_cockpit_action_readiness",
        "not_invoked_to_preserve_no_write_static_preview": True,
        "agent_bus_storage_present": sqlite_path.exists(),
        "action_count": 0,
        "requestable_action_count": 0,
        "blocked_action_count": 0,
        "runtime_execution_allowed": False,
        "agent_bus_task_writes_allowed": False,
        "readiness": {
            "runtime_cockpit_action_readiness_ready": False,
            "no_direct_runtime_execution": True,
            "no_agent_bus_task_write": True,
        },
    }


def _policy_gate_report(router: dict[str, Any], *, surface: str) -> dict[str, Any]:
    input_posture = router.get("input_posture") or {}
    action_spec = router.get("action_spec") or {}
    ambiguity = action_spec.get("ambiguity") or {}
    denied_actions = list(input_posture.get("requested_denied_actions") or [])
    dependencies = list(router.get("backend_dependencies") or [])
    by_dependency_key = {str(item.get("dependency_key") or ""): item for item in dependencies}
    missing_by_action: dict[str, str] = {}
    blocked_action_reasons: list[dict[str, Any]] = []
    for action in denied_actions:
        dependency = by_dependency_key.get(_DENIED_ACTION_TO_DEPENDENCY_KEY.get(action, ""), {})
        reason = str(dependency.get("blocked_action_reason") or "missing_or_insufficient_lower_phase_authority")
        missing = str(dependency.get("missing_contract") or "missing backend contract")
        missing_by_action[action] = f"{missing}: {reason}"
        blocked_action_reasons.append(
            {
                "action_class": action,
                "denied": True,
                "missing_or_insufficient_authority": missing,
                "blocked_action_reason": reason,
            }
        )
    if ambiguity.get("requires_operator_clarification"):
        blocked_action_reasons.append(
            {
                "action_class": "ambiguous_command",
                "denied": True,
                "missing_or_insufficient_authority": "operator clarification required before routing",
                "blocked_action_reason": "ambiguous Phase 11 Chat command cannot be dispatched or written",
            }
        )
    fail_closed = bool(denied_actions) or bool(ambiguity.get("requires_operator_clarification"))
    return {
        "surface": surface,
        "deny_default_runtime_policy_applied": True,
        "policy_docs_checked": POLICY_DOCS_CHECKED,
        "phase10_11_surface_only": True,
        "not_canonical_truth_engine": True,
        "fail_closed": fail_closed,
        "side_effects_performed": False,
        "execution_allowed": False,
        "denied_action_classes": denied_actions,
        "ambiguous_command": ambiguity,
        "backend_dependency_reports": dependencies,
        "missing_or_insufficient_authority_by_action": missing_by_action,
        "blocked_action_reasons": blocked_action_reasons,
    }


def build_phase11_chat_runtime_dispatch_readiness(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    requested_runtime_id: str | None = None,
    requested_action: str | None = None,
) -> dict[str, Any]:
    """Build a read-only readiness preview for future Chat runtime dispatch."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    router = build_phase11_chat_router_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or "runtime-task",
    )
    intent = str((router.get("intent_result") or {}).get("intent_class") or "runtime-task")
    input_posture = router.get("input_posture") or {}
    action_spec = router.get("action_spec") or {}
    ambiguity = action_spec.get("ambiguity") or {}
    policy_gate = _policy_gate_report(router, surface=SURFACE_ID)
    caps = _capability_snapshot(vault)
    bus = _agent_bus_snapshot(vault)
    workflows = _workflow_snapshot(vault)
    cockpit = _runtime_cockpit_summary(vault)
    runtime_selection = _requested_runtime(normalized_message, requested_runtime_id, caps)
    action_selection = _requested_action(
        normalized_message,
        requested_action,
        runtime_selection.get("selected_runtime"),
    )

    blockers: list[str] = []
    if not normalized_message:
        blockers.append("message_required_for_runtime_dispatch_readiness")
    if intent not in RUNTIME_BOUND_INTENTS:
        blockers.append("intent_not_runtime_bound_for_dispatch")
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if input_posture.get("denied_side_effect_prompt_present"):
        blockers.append("denied_side_effect_prompt_present")
        blockers.append("policy_gate_denied_side_effect_request")
    if ambiguity.get("requires_operator_clarification"):
        blockers.append("ambiguous_command_requires_operator_clarification")
        blockers.append("policy_gate_ambiguous_command")
    if not caps.get("ok"):
        blockers.extend(caps.get("blocked_reasons") or [])
    if not runtime_selection.get("runtime_known"):
        blockers.append("requested_or_selected_runtime_not_registered")
    if not action_selection.get("task_type_supported_by_runtime"):
        blockers.append("selected_runtime_does_not_advertise_task_type")
    if not bus.get("known_storage_readable"):
        blockers.extend(bus.get("blocked_reasons") or [])
    blockers.extend(
        [
            "operator_runtime_dispatch_approval_missing",
            "chat_runtime_dispatch_executor_not_invoked_by_readonly_contract",
            "agent_bus_task_write_blocked_by_readonly_contract",
            "workflow_dispatch_blocked_by_readonly_contract",
        ]
    )

    dispatch_material = {
        "pass": PASS_ID,
        "message_sha256": _sha256_text(normalized_message),
        "intent_class": intent,
        "selected_runtime_id": runtime_selection.get("selected_runtime_id"),
        "selected_task_type": action_selection.get("selected_task_type"),
        "approval_class": APPROVAL_CLASS,
        "agent_bus_mode": bus.get("mode"),
        "router_model_version": router.get("model_version"),
    }
    digest = _sha256_text(_canonical_json(dispatch_material))
    packet_id = f"chat-runtime-dispatch-{digest[:20]}"
    preview_ready = (
        bool(normalized_message)
        and intent in RUNTIME_BOUND_INTENTS
        and not input_posture.get("prompt_injection_suspected")
        and not input_posture.get("denied_side_effect_prompt_present")
        and not ambiguity.get("requires_operator_clarification")
        and bool(runtime_selection.get("selected_runtime_id"))
    )
    dispatch_preconditions_met = preview_ready and not blockers

    return {
        "ok": not any(
            blocker
            in {
                "message_required_for_runtime_dispatch_readiness",
                "intent_not_runtime_bound_for_dispatch",
                "prompt_injection_indicator_present",
                "denied_side_effect_prompt_present",
                "policy_gate_denied_side_effect_request",
                "ambiguous_command_requires_operator_clarification",
                "policy_gate_ambiguous_command",
                "requested_or_selected_runtime_not_registered",
            }
            for blocker in blockers
        ),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": True,
        "summary": {
            "message_present": bool(normalized_message),
            "intent_class": intent,
            "runtime_bound_intent": intent in RUNTIME_BOUND_INTENTS,
            "dispatch_preview_ready": preview_ready,
            "dispatch_preconditions_met": dispatch_preconditions_met,
            "selected_runtime_id": runtime_selection.get("selected_runtime_id"),
            "selected_task_type": action_selection.get("selected_task_type"),
            "agent_bus_mode": bus.get("mode"),
            "runtime_count": caps.get("runtime_count"),
            "workflow_count": workflows.get("workflow_count"),
            "approval_request_created": False,
            "agent_bus_task_created": False,
            "workflow_dispatched": False,
            "runtime_lifecycle_mutated": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "router_contract": router,
        "policy_gate_report": policy_gate,
        "runtime_selection": runtime_selection,
        "action_selection": action_selection,
        "runtime_capability_readiness": caps,
        "agent_bus_readiness": bus,
        "aor_workflow_readiness": workflows,
        "runtime_cockpit_action_readiness": cockpit,
        "request_digest_proof": {
            "request_digest": digest,
            "prompt_message_sha256": _sha256_text(normalized_message),
            "digest_material": dispatch_material,
            "digest_required_for_future_dispatch_approval": True,
        },
        "future_dispatch_packet_preview": {
            "visible": True,
            "dispatch_packet_id_preview": packet_id,
            "approval_id_preview": f"chat-runtime-dispatch-appr-{digest[:20]}",
            "approval_artifact_path_preview": f"runtime/studio/approvals/chat-runtime-dispatch-appr-{digest[:20]}.json",
            "agent_bus_task_path_preview": f"runtime/agent_bus/tasks/{packet_id}.json",
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "agent_bus_task_created": False,
            "agent_bus_create_task_called": False,
            "workflow_dispatch_called": False,
            "required_approval_class": APPROVAL_CLASS,
            "future_status_if_written": "pending",
            "approval_consumption_allowed_now": False,
            "dispatch_allowed_after_preview": False,
            "task_packet_preview": {
                "sender": "StudioChat",
                "recipient": runtime_selection.get("selected_runtime_id"),
                "intent": "TASK",
                "priority": "normal",
                "task_type": action_selection.get("selected_task_type"),
                "request": normalized_message[:1200],
                "expected_output": "Reviewable ChaseOS runtime result artifact, not canonical mutation.",
                "execution_constraints": {
                    "write_policy": "none",
                    "allowed_write_paths": [],
                    "allow_shell_commands": False,
                    "allow_live_subprocess": False,
                },
            },
        },
        "preflight_checks": {
            "message_present": bool(normalized_message),
            "intent_is_runtime_bound": intent in RUNTIME_BOUND_INTENTS,
            "prompt_injection_absent": not bool(input_posture.get("prompt_injection_suspected")),
            "runtime_capabilities_loaded": bool(caps.get("ok")),
            "selected_runtime_registered": bool(runtime_selection.get("runtime_known")),
            "selected_task_type_supported": bool(action_selection.get("task_type_supported_by_runtime")),
            "agent_bus_storage_readable_without_initialization": bool(bus.get("known_storage_readable")),
            "runtime_cockpit_readiness_consumed": bool(cockpit.get("ok")),
            "approval_packet_written": False,
            "agent_bus_task_written": False,
            "workflow_dispatched": False,
        },
        "authority": {
            "read_only": True,
            "approval_gated": True,
            "dispatch_preview_allowed": True,
            "approval_queue_write_allowed": False,
            "approval_execution_allowed": False,
            "runtime_dispatch_allowed": False,
            "runtime_lifecycle_mutation_allowed": False,
            "workflow_execution_allowed": False,
            "agent_bus_task_write_allowed": False,
            "provider_calls_allowed": False,
            "browser_control_allowed": False,
            "conversation_persistence_allowed": False,
            "target_vault_write_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_artifact_write",
            "approval_grant_or_reject",
            "approval_execution",
            "runtime_dispatch",
            "runtime_start_stop_restart",
            "workflow_execution",
            "agent_bus_task_write",
            "agent_bus_task_claim",
            "provider_api_call",
            "browser_control",
            "conversation_log_write",
            "target_vault_file_write",
            "gate_mutation",
            "git_mutation",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def _operator_blocker_text(code: str) -> str:
    mapping = {
        "message_required_for_runtime_dispatch_readiness": "Chat needs an operator request before it can explain runtime readiness.",
        "intent_not_runtime_bound_for_dispatch": "This message is not classified as a runtime-bound workflow request, so Chat cannot preview runtime dispatch.",
        "prompt_injection_indicator_present": "The request contains prompt-injection language; Chat fails closed and will not dispatch or write anything.",
        "denied_side_effect_prompt_present": "The request asks for side effects that Phase 11 Chat is not authorized to perform.",
        "policy_gate_denied_side_effect_request": "Deny-default runtime policy blocked the requested side effect.",
        "ambiguous_command_requires_operator_clarification": "The command is too ambiguous to route safely; operator clarification is required.",
        "policy_gate_ambiguous_command": "Policy gate blocked the ambiguous command before any runtime handoff.",
        "requested_or_selected_runtime_not_registered": "The requested runtime is not registered in the current capability manifests.",
        "selected_runtime_does_not_advertise_task_type": "The selected runtime does not advertise the requested task type.",
        "agent_bus_storage_not_present": "Agent Bus storage is not present, so Chat can only explain the missing bus evidence.",
        "operator_runtime_dispatch_approval_missing": "A runtime-dispatch approval is required and has not been consumed or created by this read-only surface.",
        "chat_runtime_dispatch_executor_not_invoked_by_readonly_contract": "The governed runtime-dispatch executor is separate from this read-only Chat contract.",
        "agent_bus_task_write_blocked_by_readonly_contract": "Creating Agent Bus tasks is blocked by this read-only Chat contract.",
        "workflow_dispatch_blocked_by_readonly_contract": "Workflow dispatch is blocked by this read-only Chat contract.",
    }
    return mapping.get(code, code.replace("_", " "))


def _state_operator_text(status: dict[str, Any]) -> str:
    mode = str(status.get("mode") or "OBSERVE")
    active = int(status.get("active_task_count") or 0)
    pending = int(status.get("pending_approval_count") or 0)
    failed = int(status.get("failed_task_count") or 0)
    heartbeats = int(status.get("heartbeat_count") or 0)
    if mode == "AWAIT_APPROVAL":
        return f"Runtime surface is waiting on {pending} pending approval(s); no approval is consumed from Chat."
    if mode == "ACT":
        return f"Runtime surface reports {active} active task(s) and {heartbeats} heartbeat record(s)."
    if mode == "RECOVER":
        return f"Runtime surface reports {failed} failed task(s), so operator recovery/review is needed."
    return f"Runtime surface is observing: {active} active task(s), {pending} pending approval(s), {heartbeats} heartbeat record(s)."


def _read_pending_approval_summaries(vault: Path) -> list[dict[str, Any]]:
    approval_dir = vault / "runtime" / "studio" / "approvals"
    if not approval_dir.exists():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(approval_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("status") == "pending":
            results.append(
                {
                    "approval_id": data.get("approval_id", path.stem),
                    "action_type": data.get("action_type", "unknown"),
                }
            )
    return results


def _safe_sql_rows(sqlite_path: Path, sql: str) -> list[dict[str, Any]]:
    if not sqlite_path.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(row) for row in conn.execute(sql).fetchall()]
        finally:
            conn.close()
    except Exception:
        return []


def _runtime_status_summary_read_only(vault: Path) -> dict[str, Any]:
    """Small read-only status-pill-shaped summary that never initializes bus storage."""

    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    active_rows = _safe_sql_rows(
        sqlite_path,
        "SELECT id AS task_id, task_type, status, owner FROM tasks WHERE lower(status) IN ('in_progress','claimed','started') LIMIT 5",
    )
    failed_rows = _safe_sql_rows(
        sqlite_path,
        "SELECT id AS task_id, task_type, status FROM tasks WHERE lower(status) = 'failed' LIMIT 5",
    )
    heartbeat_rows = _safe_sql_rows(
        sqlite_path,
        "SELECT runtime, runtime_instance_id, heartbeat_scope, control_surface, control_surface_key, last_seen FROM heartbeats ORDER BY last_seen DESC LIMIT 10",
    )
    pending_approvals = _read_pending_approval_summaries(vault)
    mode = _derive_status_mode(
        active_count=len(active_rows),
        pending_approval_count=len(pending_approvals),
        failed_count=len(failed_rows),
    )
    return {
        "surface": "studio_runtime_status_pill",
        "mode": mode,
        "label": mode.replace("_", " "),
        "color": "amber" if mode == "AWAIT_APPROVAL" else "green" if mode == "ACT" else "orange" if mode == "RECOVER" else "gray",
        "pulse": mode in {"ACT", "RECOVER"},
        "active_task_count": len(active_rows),
        "pending_approval_count": len(pending_approvals),
        "failed_task_count": len(failed_rows),
        "heartbeat_count": len(heartbeat_rows),
        "bus_available": sqlite_path.exists(),
        "active_tasks": active_rows,
        "pending_approvals": pending_approvals[:5],
        "heartbeats": heartbeat_rows,
        "readiness": {
            "read_only": True,
            "writes_vault": False,
            "provider_calls": False,
            "connector_calls": False,
            "storage_initialized_by_this_explanation": False,
        },
    }


def _derive_status_mode(*, active_count: int, pending_approval_count: int, failed_count: int) -> str:
    if pending_approval_count > 0:
        return "AWAIT_APPROVAL"
    if active_count > 0:
        return "ACT"
    if failed_count > 0:
        return "RECOVER"
    return "OBSERVE"


def build_phase11_chat_runtime_status_explanation(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    requested_runtime_id: str | None = None,
    requested_action: str | None = None,
) -> dict[str, Any]:
    """Explain current runtime status for Phase 11 Chat without dispatching or writing.

    This is an operator-facing wrapper over existing Studio/readiness surfaces. It
    intentionally reuses runtime status pill, runtime-dispatch readiness, Agent
    Bus, capability, and cockpit-readiness data instead of creating a new source
    of truth.
    """

    vault = Path(vault_root).resolve()
    readiness = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=message,
        explicit_intent=explicit_intent,
        requested_runtime_id=requested_runtime_id,
        requested_action=requested_action,
    )
    status = _runtime_status_summary_read_only(vault)
    summary = readiness.get("summary") or {}
    preview = readiness.get("future_dispatch_packet_preview") or {}
    bus = readiness.get("agent_bus_readiness") or {}
    blockers = list(readiness.get("blocked_reasons") or [])
    pending_approvals = list(status.get("pending_approvals") or [])
    active_tasks = list(status.get("active_tasks") or [])
    heartbeats = list(status.get("heartbeats") or [])

    blocker_items = [
        {"code": str(code), "operator_text": _operator_blocker_text(str(code))}
        for code in blockers
    ]
    missing_approval = "operator_runtime_dispatch_approval_missing" in blockers
    selected_runtime = summary.get("selected_runtime_id") or "the selected runtime"
    selected_task_type = summary.get("selected_task_type") or "the requested task type"
    blocked_text = (
        "Runtime action is blocked: " + "; ".join(item["operator_text"] for item in blocker_items[:5])
        if blocker_items
        else "No blocking reason was found in the readiness preview, but Chat remains read-only."
    )

    runtime_cockpit_alignment = {
        "source_surface": "studio_runtime_cockpit_contract",
        "aligned_view_ids": [
            "runtime_health",
            "coordination_watch",
            "approval_readiness",
            "proof_status",
            "logs_and_audit",
        ],
        "shares_runtime_cockpit_wording": True,
        "operator_role": "explanation-layer",
        "chat_is_executor": False,
        "runtime_cockpit_is_control_surface": False,
        "wording": "Chat explains the same Runtime Cockpit posture in natural language; lower-phase surfaces keep lifecycle control, dispatch, and approval consumption.",
    }

    return {
        "ok": True,
        "surface": "phase11_chat_runtime_status_explanation",
        "model_version": f"{MODEL_VERSION}.status_explanation.v1",
        "generated_at_utc": readiness.get("generated_at_utc"),
        "vault_root": str(vault),
        "read_only": True,
        "phase10_11_surface_only": True,
        "not_canonical_truth_engine": True,
        "state_explanation": {
            "mode": status.get("mode"),
            "label": status.get("label"),
            "color": status.get("color"),
            "pulse": status.get("pulse"),
            "operator_text": _state_operator_text(status),
        },
        "blocked_reason_explanation": {
            "blocked": bool(blocker_items),
            "operator_text": blocked_text,
            "reasons": blocker_items,
        },
        "missing_approval_explanation": {
            "missing_approval": missing_approval,
            "required_approval_class": preview.get("required_approval_class"),
            "pending_approval_count": status.get("pending_approval_count"),
            "pending_approvals": pending_approvals,
            "operator_text": (
                f"A {preview.get('required_approval_class')} approval is required before {selected_runtime} can receive {selected_task_type}; Chat did not create or consume approval records."
                if missing_approval
                else "No missing runtime-dispatch approval was reported by the readiness preview."
            ),
        },
        "current_activity_explanation": {
            "active_task_count": status.get("active_task_count"),
            "failed_task_count": status.get("failed_task_count"),
            "heartbeat_count": status.get("heartbeat_count"),
            "active_tasks": active_tasks,
            "heartbeats": heartbeats,
            "operator_text": (
                f"Current runtime activity: {status.get('active_task_count')} active task(s), {status.get('failed_task_count')} failed task(s), {status.get('heartbeat_count')} heartbeat record(s)."
            ),
        },
        "runtime_cockpit_alignment": runtime_cockpit_alignment,
        "evidence_links": {
            "runtime_status_surface": status.get("surface"),
            "runtime_dispatch_readiness_surface": readiness.get("surface"),
            "agent_bus_config_path": bus.get("config_path"),
            "agent_bus_sqlite_path": bus.get("sqlite_path"),
            "approval_artifact_path_preview": preview.get("approval_artifact_path_preview"),
            "agent_bus_task_path_preview": preview.get("agent_bus_task_path_preview"),
            "dispatch_packet_id_preview": preview.get("dispatch_packet_id_preview"),
            "request_digest": (readiness.get("request_digest_proof") or {}).get("request_digest"),
        },
        "no_dispatch_proof": {
            "approval_request_created": summary.get("approval_request_created") is True,
            "agent_bus_task_created": summary.get("agent_bus_task_created") is True,
            "workflow_dispatched": summary.get("workflow_dispatched") is True,
            "runtime_lifecycle_mutated": summary.get("runtime_lifecycle_mutated") is True,
            "agent_bus_create_task_called": preview.get("agent_bus_create_task_called") is True,
            "workflow_dispatch_called": preview.get("workflow_dispatch_called") is True,
            "approval_queue_writer_called": preview.get("approval_queue_writer_called") is True,
            "side_effects_performed": (readiness.get("policy_gate_report") or {}).get("side_effects_performed") is True,
        },
        "authority": readiness.get("authority") or {},
        "readiness_summary": summary,
        "runtime_status": status,
    }


def format_phase11_chat_runtime_status_explanation(payload: dict[str, Any]) -> str:
    state = payload.get("state_explanation") or {}
    blocked = payload.get("blocked_reason_explanation") or {}
    approval = payload.get("missing_approval_explanation") or {}
    activity = payload.get("current_activity_explanation") or {}
    evidence = payload.get("evidence_links") or {}
    no_dispatch = payload.get("no_dispatch_proof") or {}
    summary = payload.get("readiness_summary") or {}
    return "\n".join(
        [
            "Phase 11 Chat Runtime Status Explanation",
            f"  selected_runtime: {summary.get('selected_runtime_id')}",
            f"  selected_task_type: {summary.get('selected_task_type')}",
            f"  state: {state.get('operator_text')}",
            f"  blocked: {blocked.get('operator_text')}",
            f"  missing_approval: {approval.get('operator_text')}",
            f"  current_activity: {activity.get('operator_text')}",
            f"  evidence.approval_preview: {evidence.get('approval_artifact_path_preview')}",
            f"  evidence.agent_bus_task_preview: {evidence.get('agent_bus_task_path_preview')}",
            f"  no_dispatch: approval_request_created={no_dispatch.get('approval_request_created')}, agent_bus_task_created={no_dispatch.get('agent_bus_task_created')}, workflow_dispatched={no_dispatch.get('workflow_dispatched')}",
            "  Boundary: explanation only; no approval consumption, Agent Bus task write, workflow dispatch, runtime lifecycle mutation, provider call, browser control, or canonical mutation.",
        ]
    )


def format_phase11_chat_runtime_dispatch_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("request_digest_proof") or {}
    preview = payload.get("future_dispatch_packet_preview") or {}
    return "\n".join(
        [
            "Phase 11 Chat Runtime Dispatch Readiness Contract",
            f"  status: {payload.get('status')}",
            f"  intent: {summary.get('intent_class')}",
            f"  selected_runtime: {summary.get('selected_runtime_id')}",
            f"  selected_task_type: {summary.get('selected_task_type')}",
            f"  agent_bus_mode: {summary.get('agent_bus_mode')}",
            f"  request_digest: {digest.get('request_digest')}",
            f"  dispatch_packet_id_preview: {preview.get('dispatch_packet_id_preview')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  agent_bus_task_created: {summary.get('agent_bus_task_created')}",
            f"  workflow_dispatched: {summary.get('workflow_dispatched')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: read-only readiness only; no approval artifact, Agent Bus task, workflow dispatch, runtime lifecycle mutation, provider call, browser control, or canonical mutation.",
        ]
    )
