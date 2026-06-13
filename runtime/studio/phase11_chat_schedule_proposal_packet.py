"""Phase 11 Studio Chat schedule proposal packet surface.

This surface lets Studio Chat package a future ChaseOS schedule intent into a
digest-bound approval request. It may queue only the approval artifact after an
exact digest match. It does not write runtime/schedules YAML, regenerate the
schedule index, change OpenClaw/Hermes cron, dispatch workflows, call Discord,
call providers, read credentials, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import load_native_chat_state, safe_state_id
from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation
from runtime.studio.service import ActionSpec, StudioService

try:
    from runtime.schedules.loader import (
        SCHEDULABLE_TASK_TYPES,
        VALID_APPROVAL_POLICIES,
        VALID_CADENCE_TYPES,
        VALID_DELIVERY_TARGETS,
        VALID_FAILURE_BEHAVIORS,
        VALID_RUNTIME_ADAPTERS,
        VALID_SCHEDULE_COMMANDS,
        VALID_SCHEDULE_KINDS,
    )
except Exception:  # pragma: no cover - fallback keeps Studio import fail-closed.
    SCHEDULABLE_TASK_TYPES = {"operator-briefing", "graph-hygiene", "scheduled-briefing", "coordination"}
    VALID_APPROVAL_POLICIES = {"none", "pre-execution", "pre-delivery"}
    VALID_CADENCE_TYPES = {"cron", "event", "manual", "webhook"}
    VALID_DELIVERY_TARGETS = {"vault-local", "discord", "email", "whop", "slack"}
    VALID_FAILURE_BEHAVIORS = {"escalate", "retry-once-then-escalate", "silent-fail-log"}
    VALID_RUNTIME_ADAPTERS = {"openclaw", "hermes", "claude", "archon", "n8n", "local", "manual"}
    VALID_SCHEDULE_COMMANDS = {"events.watch": "chaseos events watch --once --execute"}
    VALID_SCHEDULE_KINDS = {"workflow", "command"}


MODEL_VERSION = "studio.phase11_chat_schedule_proposal_packet.v1"
SURFACE_ID = "phase11_chat_schedule_proposal_packet"
PASS_ID = "studio-chat-schedule-proposal-packets"
STATUS_PREVIEW = "READY / APPROVAL-QUEUE-WRITE-PREVIEW / SCHEDULE WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / SCHEDULE WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-proposal-consumption"
AUDIT_ROOT = "runtime/studio/approvals/chat-schedule-proposals"
METADATA_BLOCK_KEY = "phase11_chat_schedule_proposal_execution_blocked"

DEFAULT_THREAD_ID = "runtime-ops-schedules"
DEFAULT_WORKFLOW_ID = "operator_today"
DEFAULT_WORKFLOW_TASK_TYPE = "operator-briefing"
DEFAULT_CRON_EXPRESSION = "0 7 * * 1-5"
DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_RUNTIME_ADAPTER = "openclaw"
KNOWN_WORKFLOW_TASK_TYPES: dict[str, str] = {
    "operator_today": "operator-briefing",
    "operator_close_day": "operator-briefing",
    "graph_hygiene": "graph-hygiene",
    "os_hygiene_graph": "os-graph-maintenance",
    "graduate_ideas": "idea-graduation",
    "sbp_strikezone_digest": "scheduled-briefing",
    "source_pack_builder": "source-pack-builder",
    "strikezone_acquisition": "source-pack-builder",
    "hermes_watch": "coordination",
    "openclaw_watch": "coordination",
    "archon_watch": "coordination",
}
SECRET_TOKEN = "[REDACTED_SECRET]"
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_style_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    ("github_style_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE)),
    ("slack_style_token", re.compile(r"\bxox(?:b|p|a|r|s)-[A-Za-z0-9-]{20,}\b", re.IGNORECASE)),
    ("bearer_token", re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})")),
    (
        "secret_assignment",
        re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential|password|passwd|pwd)\s*[:=]\s*)([^\s,;]{8,})"),
    ),
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _slug(value: str | None, fallback: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip().lower()).strip("-")
    return (text or fallback)[:96].strip("-") or fallback


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _redact(value: str) -> dict[str, Any]:
    redacted = value
    categories: list[str] = []
    count = 0
    for category, pattern in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}{SECRET_TOKEN}"
            return SECRET_TOKEN

        redacted, local_count = pattern.subn(repl, redacted)
        if local_count:
            categories.append(category)
    return {
        "contains_secret": bool(count),
        "redacted_text": redacted,
        "redaction_count": count,
        "indicator_categories": list(dict.fromkeys(categories)),
    }


def _foundation_threads(foundation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(thread.get("thread_id") or ""): thread
        for thread in foundation.get("threads") or []
        if thread.get("thread_id")
    }


def _select_thread(
    foundation: dict[str, Any],
    native_state: dict[str, Any],
    *,
    selected_thread_id: str | None,
) -> tuple[dict[str, Any], bool, list[str]]:
    threads = _foundation_threads(foundation)
    requested_thread_id = safe_state_id(selected_thread_id, "") if selected_thread_id else ""
    route_thread_id = str((native_state.get("route_state") or {}).get("thread_id") or "")
    thread_id = requested_thread_id or route_thread_id or DEFAULT_THREAD_ID
    route_state_used = bool(not requested_thread_id and route_thread_id)
    thread = threads.get(thread_id)
    if not thread:
        return {}, route_state_used, ["selected_thread_not_found"]
    return thread, route_state_used, []


def _latest_draft(native_state: dict[str, Any], thread_id: str, draft_id: str | None) -> dict[str, Any]:
    drafts = [
        draft
        for draft in native_state.get("drafts") or []
        if str(draft.get("thread_id") or "") == thread_id
    ]
    requested = safe_state_id(draft_id, "") if draft_id else ""
    if requested:
        for draft in drafts:
            if str(draft.get("draft_id") or "") == requested:
                return draft
    return drafts[-1] if drafts else {}


def _source_summary(
    *,
    schedule_summary: str | None,
    message: str | None,
    latest_draft: dict[str, Any],
) -> tuple[str, str, str]:
    explicit = _norm(schedule_summary)
    if explicit:
        return explicit, "explicit_schedule_summary", ""
    msg = _norm(message)
    if msg:
        return msg, "chat_message", ""
    draft_text = str(latest_draft.get("draft_text") or "")
    if draft_text.strip():
        return _norm(draft_text), "message_draft", str(latest_draft.get("draft_id") or "")
    return "Prepare a governed ChaseOS schedule intent proposal from this Studio Chat thread.", "default_thread_review", ""


def _schedule_kind(requested: str | None, workflow_id: str | None, command_id: str | None, source_text: str) -> str:
    kind = _slug(requested, "") if requested else ""
    if kind in VALID_SCHEDULE_KINDS:
        return kind
    if command_id or "events.watch" in source_text.lower() or "event watch" in source_text.lower():
        return "command"
    return "workflow"


def _infer_workflow_id(source_text: str, requested: str | None) -> str:
    requested_norm = _slug(requested, "") if requested else ""
    if requested_norm:
        return requested_norm.replace("-", "_")
    lowered = source_text.lower()
    if "close day" in lowered or "operator_close_day" in lowered:
        return "operator_close_day"
    if "graph" in lowered and "hygiene" in lowered:
        return "graph_hygiene"
    if "strikezone" in lowered or "digest" in lowered or "sbp" in lowered:
        return "sbp_strikezone_digest"
    if "source pack" in lowered:
        return "source_pack_builder"
    if "watch" in lowered and "hermes" in lowered:
        return "hermes_watch"
    if "watch" in lowered and "openclaw" in lowered:
        return "openclaw_watch"
    return DEFAULT_WORKFLOW_ID


def _infer_command_id(source_text: str, requested: str | None) -> str:
    requested_norm = _norm(requested)
    if requested_norm:
        return requested_norm
    if "events.watch" in source_text.lower() or "event watch" in source_text.lower():
        return "events.watch"
    return "events.watch"


def _infer_cron(source_text: str, workflow_id: str, requested: str | None) -> str:
    requested_norm = _norm(requested)
    if requested_norm:
        return requested_norm
    lowered = source_text.lower()
    if "every minute" in lowered:
        return "* * * * *"
    if workflow_id == "operator_close_day" or "evening" in lowered:
        return "0 19 * * 1-5"
    if workflow_id in {"graph_hygiene", "os_hygiene_graph"}:
        return "0 3 * * *"
    if workflow_id == "sbp_strikezone_digest":
        return "0 6 * * 1-5"
    return DEFAULT_CRON_EXPRESSION


def _runtime_adapter(requested: str | None, source_text: str) -> str:
    requested_norm = _slug(requested, "") if requested else ""
    if requested_norm:
        return requested_norm
    lowered = source_text.lower()
    if "hermes" in lowered:
        return "hermes"
    if "manual" in lowered:
        return "manual"
    if "local" in lowered:
        return "local"
    return DEFAULT_RUNTIME_ADAPTER


def _delivery_targets(workflow_id: str, primary_target: str) -> list[str]:
    if workflow_id == "sbp_strikezone_digest":
        return ["07_LOGS/SBP-Runs/"]
    if workflow_id in {"graph_hygiene", "os_hygiene_graph"}:
        return ["07_LOGS/Graph-Hygiene/"]
    if primary_target != "vault-local":
        return ["07_LOGS/Operator-Briefs/"]
    return ["07_LOGS/Operator-Briefs/"]


def _workflow_task_type(vault: Path, workflow_id: str, requested: str | None) -> tuple[str, bool]:
    requested_norm = _norm(requested)
    if requested_norm:
        return requested_norm, True
    path = vault / "runtime" / "workflows" / "registry" / f"{workflow_id}.yaml"
    if workflow_id in KNOWN_WORKFLOW_TASK_TYPES:
        return KNOWN_WORKFLOW_TASK_TYPES[workflow_id], True
    if not path.exists():
        return DEFAULT_WORKFLOW_TASK_TYPE, False
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("task_type:"):
                return stripped.split(":", 1)[1].strip().strip('"').strip("'"), True
    except OSError:
        return DEFAULT_WORKFLOW_TASK_TYPE, False
    return DEFAULT_WORKFLOW_TASK_TYPE, False


def _cron_shape_valid(cron_expression: str) -> bool:
    return len([part for part in cron_expression.split(" ") if part]) == 5


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


def _schedule_yaml(intent: dict[str, Any]) -> str:
    delivery = intent["delivery"]
    provenance = intent["provenance"]
    lines = [
        f"# runtime/schedules/{intent['schedule_id']}.yaml",
        "# ChaseOS Scheduling Intent - proposed by Studio Chat.",
        "# Approval packet only until consumed by a governed schedule proposal executor.",
        f"schedule_id: {intent['schedule_id']}",
        f"schedule_kind: {intent['schedule_kind']}",
    ]
    if intent["schedule_kind"] == "workflow":
        lines.append(f"workflow_id: {intent['workflow_id']}")
    else:
        lines.extend(
            [
                f"command_id: {_yaml_scalar(intent['command_id'])}",
                f"command: {_yaml_scalar(intent['command'])}",
            ]
        )
    lines.extend(
        [
            f"owner: {_yaml_scalar(intent['owner'])}",
            "cadence:",
            f"  type: {_yaml_scalar(intent['cadence']['type'])}",
            f"  cron_expression: {_yaml_scalar(intent['cadence']['cron_expression'])}",
            f"  timezone: {_yaml_scalar(intent['cadence']['timezone'])}",
            "  event_type: null",
            "  event_source: null",
            f"trigger_source: {_yaml_scalar(intent['trigger_source'])}",
            f"runtime_adapter_target: {_yaml_scalar(intent['runtime_adapter_target'])}",
            "delivery:",
            f"  primary_target: {_yaml_scalar(delivery['primary_target'])}",
            "  vault_writeback_targets:",
        ]
    )
    for target in delivery["vault_writeback_targets"]:
        lines.append(f"    - {_yaml_scalar(target)}")
    lines.extend(
        [
            f"  external_delivery_declared: {_yaml_scalar(delivery['external_delivery_declared'])}",
            f"  vault_local_only: {_yaml_scalar(delivery['vault_local_only'])}",
            f"approval_policy: {_yaml_scalar(intent['approval_policy'])}",
            f"enabled: {_yaml_scalar(intent['enabled'])}",
            f"shadow_mode: {_yaml_scalar(intent['shadow_mode'])}",
            f"failure_behavior: {_yaml_scalar(intent['failure_behavior'])}",
            "audit_requirements:",
            "  - workflow_id",
            "  - schedule_id",
            "  - trigger_time",
            "  - status",
            "  - files_written",
            "  - run_duration_seconds",
        ]
    )
    if intent["schedule_kind"] == "workflow":
        lines.append("allowed_workflow_task_types:")
        for task_type in intent["allowed_workflow_task_types"]:
            lines.append(f"  - {_yaml_scalar(task_type)}")
    else:
        lines.append("allowed_command_ids:")
        for command_id in intent["allowed_command_ids"]:
            lines.append(f"  - {_yaml_scalar(command_id)}")
    lines.extend(
        [
            "provenance:",
            f"  created_by: {_yaml_scalar(provenance['created_by'])}",
            f"  created_at: {_yaml_scalar(provenance['created_at'])}",
            f"  rationale: {_yaml_scalar(provenance['rationale'])}",
            f"notes: {_yaml_scalar(intent['notes'])}",
        ]
    )
    return "\n".join(lines) + "\n"


def _schedule_packet(
    *,
    vault: Path,
    foundation: dict[str, Any],
    thread: dict[str, Any],
    source_summary: str,
    source_text_kind: str,
    source_draft_id: str,
    schedule_kind: str,
    workflow_id: str,
    command_id: str,
    workflow_task_type: str,
    workflow_found: bool,
    cron_expression: str,
    timezone_name: str,
    runtime_adapter_target: str,
    trigger_source: str,
    owner: str,
    delivery_primary_target: str,
    approval_policy: str,
    failure_behavior: str,
    enabled: bool,
    shadow_mode: bool,
    title: str,
    requested_schedule_id: str | None,
    operator_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    core_action = {
        "schedule_kind": schedule_kind,
        "workflow_id": workflow_id if schedule_kind == "workflow" else "",
        "command_id": command_id if schedule_kind == "command" else "",
        "workflow_task_type": workflow_task_type if schedule_kind == "workflow" else "",
        "cron_expression": cron_expression,
        "timezone": timezone_name,
        "runtime_adapter_target": runtime_adapter_target,
        "trigger_source": trigger_source,
        "owner": owner,
        "delivery_primary_target": delivery_primary_target,
        "approval_policy": approval_policy,
        "failure_behavior": failure_behavior,
        "enabled": enabled,
        "shadow_mode": shadow_mode,
        "title": title,
        "source_text_sha256": _sha256_text(source_summary),
        "source_text_kind": source_text_kind,
        "source_draft_id": source_draft_id,
        "source_thread_id": str(thread.get("thread_id") or ""),
        "source_workspace_id": str(thread.get("workspace_id") or ""),
        "submitted_by": operator_id or "studio-operator",
    }
    preliminary_digest = _sha256_text(
        _canonical_json(
            {
                "surface": SURFACE_ID,
                "model_version": MODEL_VERSION,
                "foundation_model_version": foundation.get("model_version"),
                "action_spec": core_action,
            }
        )
    )
    base_slug = (workflow_id if schedule_kind == "workflow" else command_id.replace(".", "-")).replace("_", "-")
    schedule_id = _slug(requested_schedule_id, "") if requested_schedule_id else (
        f"sch-studio-chat-{_slug(base_slug, 'schedule')}-{preliminary_digest[:12]}"
    )
    if not schedule_id.startswith("sch-"):
        schedule_id = f"sch-{schedule_id}"
    schedule_id = schedule_id[:96].strip("-")
    target_path = f"runtime/schedules/{schedule_id}.yaml"
    delivery_targets = _delivery_targets(workflow_id, delivery_primary_target)
    intent = {
        "schedule_id": schedule_id,
        "schedule_kind": schedule_kind,
        "workflow_id": workflow_id if schedule_kind == "workflow" else None,
        "command_id": command_id if schedule_kind == "command" else None,
        "command": VALID_SCHEDULE_COMMANDS.get(command_id) if schedule_kind == "command" else None,
        "owner": owner,
        "cadence": {
            "type": "cron",
            "cron_expression": cron_expression,
            "timezone": timezone_name,
            "event_type": None,
            "event_source": None,
        },
        "trigger_source": trigger_source,
        "runtime_adapter_target": runtime_adapter_target,
        "delivery": {
            "primary_target": delivery_primary_target,
            "vault_writeback_targets": delivery_targets,
            "external_delivery_declared": delivery_primary_target != "vault-local",
            "vault_local_only": delivery_primary_target == "vault-local",
        },
        "approval_policy": approval_policy,
        "enabled": enabled,
        "shadow_mode": shadow_mode,
        "failure_behavior": failure_behavior,
        "audit_requirements": [
            "workflow_id",
            "schedule_id",
            "trigger_time",
            "status",
            "files_written",
            "run_duration_seconds",
        ],
        "allowed_workflow_task_types": [workflow_task_type] if schedule_kind == "workflow" else [],
        "allowed_command_ids": [command_id] if schedule_kind == "command" else [],
        "provenance": {
            "created_by": operator_id or "studio-operator",
            "created_at": "pending-approval",
            "rationale": source_summary,
        },
        "notes": "Proposed from Studio Chat; must be consumed by a governed schedule proposal executor before schedule intent state changes.",
    }
    action_spec = {
        **core_action,
        "schedule_id": schedule_id,
        "target_path": target_path,
        "schedule_yaml_sha256": _sha256_text(_schedule_yaml(intent)),
        "workflow_found_in_registry": workflow_found,
    }
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "foundation_model_version": foundation.get("model_version"),
        "action_spec": action_spec,
    }
    schedule_digest = _sha256_text(_canonical_json(digest_material))
    packet = {
        "schema_version": "phase11_chat_schedule_proposal_packet.v1",
        "schedule_proposal_id": f"chat-schedule-prop-{schedule_digest[:16]}",
        "status": "pending_approval_preview",
        "schedule_digest": schedule_digest,
        "schedule_id": schedule_id,
        "schedule_kind": schedule_kind,
        "workflow_id": workflow_id if schedule_kind == "workflow" else None,
        "command_id": command_id if schedule_kind == "command" else None,
        "workflow_task_type": workflow_task_type if schedule_kind == "workflow" else None,
        "workflow_found_in_registry": workflow_found,
        "cron_expression": cron_expression,
        "timezone": timezone_name,
        "runtime_adapter_target": runtime_adapter_target,
        "trigger_source": trigger_source,
        "owner": owner,
        "delivery_primary_target": delivery_primary_target,
        "approval_policy": approval_policy,
        "enabled": enabled,
        "shadow_mode": shadow_mode,
        "failure_behavior": failure_behavior,
        "title": title,
        "source_text_kind": source_text_kind,
        "source_draft_id": source_draft_id,
        "source_thread_id": str(thread.get("thread_id") or ""),
        "source_text_sha256": _sha256_text(source_summary),
        "target_path": target_path,
        "future_schedule_intent": intent,
        "future_schedule_yaml": _schedule_yaml(intent),
        "approval_required_before_effect": True,
        "approval_queue_request_only": True,
        "schedule_intent_written": False,
        "schedule_index_regenerated": False,
        "schedule_enabled": False,
        "external_scheduler_changed": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "discord_api_called": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_allowed": False,
    }
    return packet, digest_material


def _find_existing(vault: Path, schedule_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active_statuses = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_chat_schedule_proposal_digest") != schedule_digest:
            continue
        if str(payload.get("status") or "") not in active_statuses:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
            "target_path": spec.get("target_path"),
        }
    return None


def _approval_spec(
    *,
    schedule_packet: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    schedule_digest = str(schedule_packet.get("schedule_digest") or "")
    schedule_yaml = str(schedule_packet.get("future_schedule_yaml") or "")
    return ActionSpec(
        action_type="create_file",
        target_path=str(schedule_packet.get("target_path") or ""),
        content=schedule_yaml,
        metadata={
            "pass": PASS_ID,
            "source_surface": SURFACE_ID,
            "phase11_chat_schedule_proposal_packet": True,
            METADATA_BLOCK_KEY: True,
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "phase11_chat_schedule_proposal_digest": schedule_digest,
            "phase11_chat_schedule_digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
            "phase11_chat_schedule_yaml_sha256": _sha256_text(schedule_yaml),
            "phase11_chat_schedule_intent_sha256": _sha256_text(
                _canonical_json(schedule_packet.get("future_schedule_intent") or {})
            ),
            "schedule_id": schedule_packet.get("schedule_id"),
            "schedule_kind": schedule_packet.get("schedule_kind"),
            "workflow_id": schedule_packet.get("workflow_id"),
            "command_id": schedule_packet.get("command_id"),
            "cron_expression": schedule_packet.get("cron_expression"),
            "timezone": schedule_packet.get("timezone"),
            "runtime_adapter_target": schedule_packet.get("runtime_adapter_target"),
            "operator_confirmation": operator_id or "studio-operator",
            "schedule_intent_written": False,
            "schedule_index_regenerated": False,
            "schedule_enabled": False,
            "external_scheduler_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_allowed": False,
        },
        submitted_by="studio-chat",
        note="Phase 11 Chat schedule proposal approval request; schedule effects deferred.",
    )


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    schedule_packet: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> str:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    schedule_digest = str(schedule_packet.get("schedule_digest") or "")
    path = root / f"{schedule_digest}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "schedule_digest": schedule_digest,
        "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        "schedule_proposal_id": schedule_packet.get("schedule_proposal_id"),
        "schedule_id": schedule_packet.get("schedule_id"),
        "schedule_kind": schedule_packet.get("schedule_kind"),
        "workflow_id": schedule_packet.get("workflow_id"),
        "command_id": schedule_packet.get("command_id"),
        "target_path": schedule_packet.get("target_path"),
        "operator_id": operator_id or "studio-operator",
        "approval_request_created": True,
        "target_file_written": False,
        "schedule_intent_written": False,
        "schedule_index_regenerated": False,
        "schedule_enabled": False,
        "external_scheduler_changed": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "discord_api_called": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_allowed": False,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return _rel(vault, path)


def build_phase11_chat_schedule_proposal_packet(
    vault_root: str | Path,
    *,
    selected_thread_id: str | None = None,
    workflow_id: str | None = None,
    workflow_task_type: str | None = None,
    command_id: str | None = None,
    schedule_kind: str | None = None,
    schedule_id: str | None = None,
    cron_expression: str | None = None,
    timezone_name: str | None = None,
    runtime_adapter_target: str | None = None,
    trigger_source: str | None = None,
    owner: str = "operator",
    delivery_primary_target: str = "vault-local",
    approval_policy: str = "pre-execution",
    failure_behavior: str = "escalate",
    enabled: bool = False,
    shadow_mode: bool = True,
    title: str | None = None,
    message: str | None = None,
    schedule_summary: str | None = None,
    draft_id: str | None = None,
    expected_schedule_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Preview or queue one approval request for a future schedule intent."""

    vault = Path(vault_root).resolve()
    foundation = build_phase11_chat_workspaces_foundation(vault)
    native_state = load_native_chat_state(vault)
    thread, route_state_used, selection_blockers = _select_thread(
        foundation,
        native_state,
        selected_thread_id=selected_thread_id,
    )
    latest_draft = _latest_draft(native_state, str(thread.get("thread_id") or ""), draft_id) if thread else {}
    raw_summary_text, source_text_kind, source_draft_id = _source_summary(
        schedule_summary=schedule_summary,
        message=message,
        latest_draft=latest_draft,
    )
    raw_title = _norm(title) or " ".join(raw_summary_text.split()[:9]).strip(" .,:;") or "Studio Chat Schedule Proposal"
    summary_redaction = _redact(raw_summary_text)
    title_redaction = _redact(raw_title)
    contains_secret = bool(summary_redaction["contains_secret"] or title_redaction["contains_secret"])
    safe_summary_text = str(summary_redaction["redacted_text"])
    safe_title = str(title_redaction["redacted_text"])[:120]
    kind = _schedule_kind(schedule_kind, workflow_id, command_id, safe_summary_text)
    wf_id = _infer_workflow_id(safe_summary_text, workflow_id)
    cmd_id = _infer_command_id(safe_summary_text, command_id)
    task_type, workflow_found = _workflow_task_type(vault, wf_id, workflow_task_type)
    cron = _infer_cron(safe_summary_text, wf_id, cron_expression)
    tz_name = _norm(timezone_name) or DEFAULT_TIMEZONE
    adapter = _runtime_adapter(runtime_adapter_target, safe_summary_text)
    trigger = _slug(trigger_source, adapter or DEFAULT_RUNTIME_ADAPTER)
    delivery_target = _slug(delivery_primary_target, "vault-local")
    approval = _slug(approval_policy, "pre-execution")
    failure = _slug(failure_behavior, "escalate")

    packet, digest_material = _schedule_packet(
        vault=vault,
        foundation=foundation,
        thread=thread or {},
        source_summary=safe_summary_text,
        source_text_kind=source_text_kind,
        source_draft_id=source_draft_id,
        schedule_kind=kind,
        workflow_id=wf_id,
        command_id=cmd_id,
        workflow_task_type=task_type,
        workflow_found=workflow_found,
        cron_expression=cron,
        timezone_name=tz_name,
        runtime_adapter_target=adapter,
        trigger_source=trigger,
        owner=_norm(owner) or "operator",
        delivery_primary_target=delivery_target,
        approval_policy=approval,
        failure_behavior=failure,
        enabled=bool(enabled),
        shadow_mode=bool(shadow_mode),
        title=safe_title,
        requested_schedule_id=schedule_id,
        operator_id=operator_id,
    )
    schedule_digest = str(packet.get("schedule_digest") or "")
    expected = str(expected_schedule_digest or "").strip()
    target_path = str(packet.get("target_path") or "")
    target_abs = vault / target_path

    blockers = list(selection_blockers)
    if contains_secret:
        blockers.append("secret_or_credential_indicator_present")
    if kind not in VALID_SCHEDULE_KINDS:
        blockers.append("unsupported_schedule_kind")
    if kind == "workflow":
        if not wf_id:
            blockers.append("workflow_id_required_for_schedule_proposal")
        if not workflow_found:
            blockers.append("workflow_id_not_found_in_registry")
        if task_type not in SCHEDULABLE_TASK_TYPES:
            blockers.append("workflow_task_type_not_schedulable")
    if kind == "command":
        if cmd_id not in VALID_SCHEDULE_COMMANDS:
            blockers.append("command_id_not_schedulable")
    if "cron" not in VALID_CADENCE_TYPES:
        blockers.append("cron_cadence_not_supported_by_schedule_layer")
    if not _cron_shape_valid(cron):
        blockers.append("cron_expression_must_have_five_fields")
    if adapter not in VALID_RUNTIME_ADAPTERS:
        blockers.append("runtime_adapter_target_not_supported")
    if delivery_target not in VALID_DELIVERY_TARGETS:
        blockers.append("delivery_primary_target_not_supported")
    if approval not in VALID_APPROVAL_POLICIES:
        blockers.append("approval_policy_not_supported")
    if failure not in VALID_FAILURE_BEHAVIORS:
        blockers.append("failure_behavior_not_supported")
    if target_abs.exists():
        blockers.append("schedule_target_collision")
    if write_approval and not expected:
        blockers.append("expected_schedule_digest_required_for_queue_write")
    if write_approval and expected and expected != schedule_digest:
        blockers.append("expected_schedule_digest_mismatch")

    spec = _approval_spec(
        schedule_packet=packet,
        digest_material=digest_material,
        operator_id=operator_id,
    )
    validation = StudioService(vault).validate_action(spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")

    hard_blockers = list(dict.fromkeys(blockers))
    duplicate = _find_existing(vault, schedule_digest) if write_approval else None
    warnings: list[str] = []
    if duplicate:
        warnings.append("duplicate_active_schedule_proposal_request_present")

    created = False
    approval_id = None
    approval_path = None
    audit_path = None
    queue_writer_called = False
    status = STATUS_PREVIEW
    if write_approval and not hard_blockers and duplicate:
        approval_id = str(duplicate.get("approval_id") or "")
        approval_path = str(duplicate.get("path") or "")
        status = "COMPLETE / DUPLICATE-BLOCKED / EXISTING APPROVAL RETURNED / SCHEDULE WRITES BLOCKED"
    elif write_approval and not hard_blockers:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_path = _write_audit(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            schedule_packet=packet,
            digest_material=digest_material,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    ok = not any(
        item in hard_blockers
        for item in {
            "selected_thread_not_found",
            "secret_or_credential_indicator_present",
            "unsupported_schedule_kind",
            "workflow_id_required_for_schedule_proposal",
            "workflow_id_not_found_in_registry",
            "workflow_task_type_not_schedulable",
            "command_id_not_schedulable",
            "cron_cadence_not_supported_by_schedule_layer",
            "cron_expression_must_have_five_fields",
            "runtime_adapter_target_not_supported",
            "delivery_primary_target_not_supported",
            "approval_policy_not_supported",
            "failure_behavior_not_supported",
            "schedule_target_collision",
            "expected_schedule_digest_required_for_queue_write",
            "expected_schedule_digest_mismatch",
            "studio_service_validation_gate_blocked",
        }
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not bool(created),
        "approval_gated": True,
        "summary": {
            "schedule_proposal_preview_ready": ok,
            "schedule_proposal_id": packet.get("schedule_proposal_id"),
            "schedule_id": packet.get("schedule_id"),
            "schedule_kind": packet.get("schedule_kind"),
            "workflow_id": packet.get("workflow_id"),
            "command_id": packet.get("command_id"),
            "workflow_task_type": packet.get("workflow_task_type"),
            "cron_expression": packet.get("cron_expression"),
            "timezone": packet.get("timezone"),
            "runtime_adapter_target": packet.get("runtime_adapter_target"),
            "trigger_source": packet.get("trigger_source"),
            "enabled_after_future_execution": packet.get("enabled"),
            "shadow_mode_after_future_execution": packet.get("shadow_mode"),
            "source_text_kind": source_text_kind,
            "source_draft_id": source_draft_id,
            "route_state_used": route_state_used,
            "target_path_preview": target_path,
            "write_approval_requested": bool(write_approval),
            "approval_request_created": created,
            "duplicate_active_request_present": bool(duplicate),
            "duplicate_returned_existing_request": bool(write_approval and duplicate and not created and not hard_blockers),
            "approval_id": approval_id,
            "approval_artifact_path": approval_path,
            "queue_write_preview_ready": not hard_blockers,
            "target_file_written": False,
            "schedule_intent_written": False,
            "schedule_index_regenerated": False,
            "schedule_enabled": False,
            "external_scheduler_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_allowed": False,
            "blocker_count": len(hard_blockers),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "digest_proof": {
            "schedule_digest": schedule_digest,
            "expected_schedule_digest": expected or None,
            "expected_digest_matched": bool(expected and expected == schedule_digest),
            "digest_required_for_write": True,
            "digest_material": digest_material,
        },
        "source_preview": {
            "source_text_kind": source_text_kind,
            "source_draft_id": source_draft_id,
            "thread_id": packet.get("source_thread_id"),
            "request_summary_preview": safe_summary_text[:320],
            "source_text_sha256": packet.get("source_text_sha256"),
            "route_state_used": route_state_used,
            "draft_found": bool(latest_draft),
        },
        "secret_redaction": {
            "source_contains_secret": contains_secret,
            "source_redacted": contains_secret,
            "redaction_count": int(summary_redaction["redaction_count"]) + int(title_redaction["redaction_count"]),
            "indicator_categories": list(
                dict.fromkeys(
                    list(summary_redaction["indicator_categories"])
                    + list(title_redaction["indicator_categories"])
                )
            ),
        },
        "future_schedule_proposal_packet": packet,
        "future_schedule_intent_preview": packet.get("future_schedule_intent"),
        "future_schedule_yaml_preview": packet.get("future_schedule_yaml"),
        "approval_queue_write": {
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "approval_status_now": "pending" if created else (duplicate or {}).get("status"),
            "approval_artifact_path": approval_path,
            "duplicate": duplicate,
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
        },
        "target_write_proof": {
            "target_path": target_path,
            "target_file_exists_after": target_abs.exists(),
            "target_file_written": False,
            "schedule_intent_written": False,
            "schedule_index_regenerated": False,
            "schedule_enabled": False,
            "external_scheduler_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_allowed": False,
        },
        "service_validation": {
            "valid": validation.valid,
            "gate_blocked": validation.gate_blocked,
            "approval_required": True,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        },
        "authority": {
            "approval_queue_write_allowed_with_digest": True,
            "approval_queue_write_performed": created,
            "approval_execution_allowed": False,
            "schedule_intent_write_allowed": False,
            "schedule_index_regeneration_allowed": False,
            "schedule_enable_allowed": False,
            "external_scheduler_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "chat_message_send_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_execution",
            "schedule_intent_write",
            "schedule_index_regeneration",
            "schedule_enable",
            "external_scheduler_mutation",
            "agent_bus_task_write",
            "runtime_dispatch",
            "workflow_dispatch",
            "chat_message_send",
            "discord_api_call",
            "provider_api_call",
            "credential_value_display",
            "canonical_writeback",
        ],
        "readiness": {
            "phase11_chat_schedule_proposal_packet_ready": True,
            "schedule_proposal_preview_ready": ok,
            "schedule_proposal_requires_digest": True,
            "schedule_proposal_approval_queue_write_gated": True,
            "generic_studio_service_execution_blocked": True,
            "schedule_intent_write_blocked": True,
            "schedule_index_regeneration_blocked": True,
            "external_scheduler_mutation_blocked": True,
            "agent_bus_task_write_blocked": True,
            "runtime_dispatch_blocked": True,
            "discord_api_call_blocked": True,
            "provider_call_blocked": True,
            "credential_values_hidden": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "blocked_reasons": hard_blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_chat_schedule_proposal_packet(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    queue = payload.get("approval_queue_write") or {}
    return "\n".join(
        [
            "Phase 11 Chat Schedule Proposal Packet",
            f"  status: {payload.get('status')}",
            f"  schedule_proposal_id: {summary.get('schedule_proposal_id')}",
            f"  schedule_id: {summary.get('schedule_id')}",
            f"  schedule_kind: {summary.get('schedule_kind')}",
            f"  workflow_id: {summary.get('workflow_id') or 'none'}",
            f"  command_id: {summary.get('command_id') or 'none'}",
            f"  cron_expression: {summary.get('cron_expression')}",
            f"  schedule_digest: {digest.get('schedule_digest')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  approval_id: {summary.get('approval_id') or 'none'}",
            f"  approval_artifact_path: {queue.get('approval_artifact_path') or 'none'}",
            f"  target_path: {summary.get('target_path_preview')}",
            f"  target_file_written: {summary.get('target_file_written')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: approval queue artifact only after exact digest; no schedule YAML write, schedule index regeneration, external scheduler mutation, runtime dispatch, Discord call, provider call, or canonical writeback.",
        ]
    )
