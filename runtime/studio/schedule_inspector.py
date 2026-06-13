"""
studio/schedule_inspector.py — Studio Schedule Inspector

Read-only surface for inspecting the ChaseOS schedule layer:
  - list all schedule intents with status, cadence, and runtime target
  - inspect a single schedule with full provenance and recent state-change history
  - aggregate summary: enabled/disabled counts, by runtime, by cadence type

Governance:
  - Read-only: no enable/disable mutations (use `chaseos schedule enable/disable`)
  - Reads runtime/schedules/*.yaml and 07_LOGS/Schedule-State/schedule_state_log.jsonl only
  - Does not trigger, execute, or modify any schedule or workflow
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "read_only": True,
    "reads_schedule_files": True,
    "reads_state_log": True,
    "writes_schedule_files": False,
    "enables_or_disables_schedules": False,
    "cron_mutation_allowed": False,
    "external_scheduler_mutation_allowed": False,
    "agent_bus_task_write_allowed": False,
    "runtime_dispatch_allowed": False,
    "workflow_execution": False,
    "approval_consumption_allowed": False,
    "provider_calls_allowed": False,
    "triggers_execution": False,
    "canonical_mutation_allowed": False,
}

_STATE_LOG_PATH = "07_LOGS/Schedule-State/schedule_state_log.jsonl"


def _load_schedule_state_log(vault_root: Path, schedule_id: Optional[str] = None) -> list[dict]:
    """Read state-change entries from the schedule state log, optionally filtered by schedule_id."""
    log_path = vault_root / _STATE_LOG_PATH
    if not log_path.exists():
        return []
    entries: list[dict] = []
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if schedule_id is None or entry.get("schedule_id") == schedule_id:
                entries.append(entry)
    except Exception:
        pass
    return entries


def _schedule_intent_to_summary(intent: Any) -> dict[str, Any]:
    """Convert a ScheduleIntent dataclass to a Studio-ready summary dict."""
    cadence = intent.cadence
    enabled = bool(intent.enabled)
    return {
        "schedule_id": intent.schedule_id,
        "schedule_kind": intent.schedule_kind,
        "workflow_id": intent.workflow_id,
        "command_id": intent.command_id,
        "enabled": enabled,
        "status_label": "enabled intent" if enabled else "disabled intent",
        "execution_posture": "runtime-governed intent" if enabled else "inactive intent",
        "schedule_boundary": (
            "Read-only schedule intent. Execution, cron mutation, Agent Bus writes, "
            "approval consumption, and external delivery are not available from Studio."
        ),
        "shadow_mode": intent.shadow_mode,
        "owner": intent.owner,
        "runtime_adapter_target": intent.runtime_adapter_target,
        "trigger_source": intent.trigger_source,
        "cadence_type": cadence.type if cadence else None,
        "cron_expression": cadence.cron_expression if cadence else None,
        "timezone": cadence.timezone if cadence else None,
        "approval_policy": intent.approval_policy,
        "failure_behavior": intent.failure_behavior,
        "allowed_workflow_task_types": intent.allowed_workflow_task_types,
        "delivery_primary_target": intent.delivery.primary_target if intent.delivery else None,
        "vault_local_only": intent.delivery.vault_local_only if intent.delivery else None,
        "vault_writeback_targets": intent.delivery.vault_writeback_targets if intent.delivery else [],
        "created_at": intent.provenance.created_at if intent.provenance else None,
        "created_by": intent.provenance.created_by if intent.provenance else None,
    }


def _schedule_intent_to_detail(intent: Any) -> dict[str, Any]:
    """Extend the summary with rationale and notes."""
    summary = _schedule_intent_to_summary(intent)
    summary["rationale"] = intent.provenance.rationale if intent.provenance else None
    summary["notes"] = intent.notes
    return summary


def _schedule_operating_context(
    *,
    total: int,
    enabled: int,
    disabled: int,
    by_runtime: dict[str, int],
    last_change: str | None,
) -> dict[str, Any]:
    """Product-facing schedule desk context without adding execution authority."""
    runtime_count = len(by_runtime)
    return {
        "title": "Schedule Operating Context",
        "description": (
            "Local-first view of schedule intents, cadence, runtime targets, "
            "and governed activation posture."
        ),
        "source": (
            "runtime/schedules/*.yaml, runtime/schedules/index.yaml, and "
            "07_LOGS/Schedule-State/schedule_state_log.jsonl"
        ),
        "safe_action": (
            "Inspect schedule intent and readiness only. Enabling, disabling, "
            "cron mutation, workflow dispatch, and external delivery stay governed."
        ),
        "cards": [
            {
                "label": "Schedule intents",
                "value": total,
                "note": f"{enabled} enabled; {disabled} disabled",
                "status": "read-only",
            },
            {
                "label": "Enabled intents",
                "value": enabled,
                "note": "runtime adapter target is visible; no launch from Studio",
                "status": "governed",
            },
            {
                "label": "Runtime targets",
                "value": runtime_count,
                "note": ", ".join(sorted(by_runtime)) if by_runtime else "none declared",
                "status": "readback",
            },
            {
                "label": "Last state change",
                "value": last_change or "none",
                "note": "schedule state log readback only",
                "status": "audit",
            },
        ],
    }


def _schedule_readiness(last_change: str | None) -> dict[str, Any]:
    """Return conservative readiness rows for the schedule product surface."""
    return {
        "summary": (
            "Schedule intent readback is mounted. Activation, cron mutation, "
            "Agent Bus task writes, runtime dispatch, and external delivery remain "
            "approval-gated or blocked from this page."
        ),
        "rows": [
            {
                "label": "Intent readback",
                "status": "ready",
                "note": "Studio can list local schedule YAML intents without writing files.",
            },
            {
                "label": "State-change audit",
                "status": "ready" if last_change else "empty",
                "note": (
                    f"Latest state entry: {last_change}."
                    if last_change
                    else "No schedule state changes were found in the local log."
                ),
            },
            {
                "label": "Enable / disable",
                "status": "approval-gated",
                "note": "Toggle requests route through approval preview and are not direct mutations.",
            },
            {
                "label": "Cron / runtime dispatch",
                "status": "blocked",
                "note": "This page does not mutate cron, start adapters, or execute workflows.",
            },
            {
                "label": "Agent Bus / provider / delivery writes",
                "status": "blocked",
                "note": "No Agent Bus task write, provider call, approval consumption, or external delivery is mounted.",
            },
        ],
    }


def _schedule_feature_family_coverage() -> list[dict[str, str]]:
    """Canonical capability coverage represented by the Studio Schedules page."""
    return [
        {
            "family": "Scheduled Briefing Pipelines",
            "capability": "Trigger schedule intent readback",
            "product_surface": "Runtime / Schedules",
            "status": "PARTIAL LIVE / READ-ONLY",
            "evidence": "runtime.studio.schedule_inspector.list_schedules and runtime/schedules/*.yaml",
            "boundary": "No workflow execution, cron mutation, or external delivery from Studio.",
        },
        {
            "family": "Scheduling Intent Architecture",
            "capability": "Native schedule intent store",
            "product_surface": "Runtime / Schedules",
            "status": "LIVE READBACK",
            "evidence": "runtime/schedules/index.yaml and schedule loader contract",
            "boundary": "Studio reads schedule files only; enable/disable remains approval-gated.",
        },
        {
            "family": "Operator Runtime / AOR",
            "capability": "Scheduled workflow execution substrate",
            "product_surface": "Tasks & Runs and Schedules",
            "status": "PARTIAL / GOVERNED",
            "evidence": "workflow_id, runtime_adapter_target, allowed_workflow_task_types",
            "boundary": "No workflow dispatch, retry, or Agent Bus task write from this page.",
        },
        {
            "family": "Phase 11 Chat Control",
            "capability": "Schedule proposal and activation lanes",
            "product_surface": "Chat, Review Queue, and Schedules",
            "status": "APPROVAL-GATED / PARTIAL",
            "evidence": "toggle_schedule approval request path and schedule preview lanes",
            "boundary": "No ambient schedule write or approval consumption from Schedules.",
        },
        {
            "family": "Governance",
            "capability": "Schedule state audit readback",
            "product_surface": "Logs / Audit and Schedules",
            "status": "READ-ONLY",
            "evidence": "07_LOGS/Schedule-State/schedule_state_log.jsonl",
            "boundary": "Audit readback only; canonical mutations are unavailable here.",
        },
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def list_schedules(
    vault_root: str | Path,
    *,
    runtime_filter: Optional[str] = None,
    enabled_only: bool = False,
    cadence_filter: Optional[str] = None,
) -> dict[str, Any]:
    """
    List all schedule intents in the vault.

    Parameters
    ----------
    runtime_filter : str, optional
        Filter by runtime_adapter_target (e.g. "openclaw").
    enabled_only : bool
        If True, only return enabled schedules.
    cadence_filter : str, optional
        Filter by cadence type (e.g. "cron", "manual").
    """
    vault = Path(vault_root).resolve()
    try:
        from runtime.schedules.loader import list_schedules as _list_schedules
        intents = _list_schedules(vault_root=vault, check_registry=False)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to load schedules: {exc}",
            "surface": "studio_schedule_inspector",
            "schedules": [],
            "schedule_count": 0,
            "boundary": _BOUNDARY,
            "authority": _BOUNDARY,
        }

    summaries = []
    for intent in intents:
        if enabled_only and not intent.enabled:
            continue
        if runtime_filter and intent.runtime_adapter_target != runtime_filter:
            continue
        if cadence_filter and (intent.cadence is None or intent.cadence.type != cadence_filter):
            continue
        summaries.append(_schedule_intent_to_summary(intent))

    # Sort: enabled first, then by schedule_id
    summaries.sort(key=lambda s: (not s["enabled"], s["schedule_id"]))

    return {
        "ok": True,
        "surface": "studio_schedule_inspector",
        "schedules": summaries,
        "schedule_count": len(summaries),
        "runtime_filter": runtime_filter,
        "enabled_only": enabled_only,
        "cadence_filter": cadence_filter,
        "boundary": _BOUNDARY,
        "authority": _BOUNDARY,
    }


def inspect_schedule(
    vault_root: str | Path,
    schedule_id: str,
    *,
    state_log_limit: int = 10,
) -> dict[str, Any]:
    """
    Return full detail for a single schedule intent plus recent state-change history.

    Parameters
    ----------
    schedule_id : str
        The schedule_id to inspect (e.g. "sch-operator-today-0700").
    state_log_limit : int
        Number of most-recent state-change log entries to include.
    """
    vault = Path(vault_root).resolve()
    try:
        from runtime.schedules.loader import load_schedule as _load_schedule
        intent = _load_schedule(schedule_id, vault_root=vault)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to load schedule '{schedule_id}': {exc}",
            "surface": "studio_schedule_inspector",
            "schedule_id": schedule_id,
            "boundary": _BOUNDARY,
            "authority": _BOUNDARY,
        }

    if intent is None:
        return {
            "ok": False,
            "error": f"Schedule '{schedule_id}' not found.",
            "surface": "studio_schedule_inspector",
            "schedule_id": schedule_id,
            "boundary": _BOUNDARY,
            "authority": _BOUNDARY,
        }

    detail = _schedule_intent_to_detail(intent)

    # Attach recent state-change history (newest first)
    all_entries = _load_schedule_state_log(vault, schedule_id=schedule_id)
    recent_changes = list(reversed(all_entries))[:state_log_limit]

    return {
        "ok": True,
        "surface": "studio_schedule_inspector",
        "schedule": detail,
        "recent_state_changes": recent_changes,
        "state_changes_shown": len(recent_changes),
        "boundary": _BOUNDARY,
        "authority": _BOUNDARY,
    }


def get_schedule_summary(
    vault_root: str | Path,
) -> dict[str, Any]:
    """
    Aggregate counts across all schedules.

    Returns enabled/disabled totals, breakdown by runtime_adapter_target,
    and breakdown by cadence type.
    """
    vault = Path(vault_root).resolve()
    try:
        from runtime.schedules.loader import list_schedules as _list_schedules
        intents = _list_schedules(vault_root=vault, check_registry=False)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to load schedules: {exc}",
            "surface": "studio_schedule_inspector",
            "boundary": _BOUNDARY,
            "authority": _BOUNDARY,
        }

    total = len(intents)
    enabled = sum(1 for i in intents if i.enabled)
    disabled = total - enabled

    by_runtime: dict[str, int] = {}
    by_cadence: dict[str, int] = {}
    by_kind: dict[str, int] = {}

    for intent in intents:
        rt = intent.runtime_adapter_target or "unknown"
        by_runtime[rt] = by_runtime.get(rt, 0) + 1

        ct = intent.cadence.type if intent.cadence else "unknown"
        by_cadence[ct] = by_cadence.get(ct, 0) + 1

        sk = intent.schedule_kind or "workflow"
        by_kind[sk] = by_kind.get(sk, 0) + 1

    # Most-recent state-change timestamp across all schedules
    all_entries = _load_schedule_state_log(vault)
    last_change = all_entries[-1].get("timestamp_utc") if all_entries else None

    return {
        "ok": True,
        "surface": "studio_schedule_inspector",
        "total": total,
        "enabled": enabled,
        "disabled": disabled,
        "by_runtime_adapter_target": by_runtime,
        "by_cadence_type": by_cadence,
        "by_schedule_kind": by_kind,
        "last_state_change_utc": last_change,
        "boundary": _BOUNDARY,
        "authority": _BOUNDARY,
        "operating_context": _schedule_operating_context(
            total=total,
            enabled=enabled,
            disabled=disabled,
            by_runtime=by_runtime,
            last_change=last_change,
        ),
        "readiness": _schedule_readiness(last_change),
        "feature_family_coverage": _schedule_feature_family_coverage(),
    }
