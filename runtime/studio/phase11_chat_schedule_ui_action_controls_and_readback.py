"""Phase 11 Chat schedule UI action controls and readback contract.

This read-only contract describes the manual Studio Chat control chain for
schedule proposal, approval, local schedule write, activation, adapter export,
and local packet writeback. It exposes API/readback metadata only; the actual
mutating steps remain behind their existing explicit API methods and exact
approval/digest requirements.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.schedules.loader import VALID_RUNTIME_ADAPTERS, export_schedules_for_adapter, list_schedules
from runtime.studio.phase11_chat_schedule_proposal_packet import DEFAULT_RUNTIME_ADAPTER


MODEL_VERSION = "studio.phase11_chat_schedule_ui_action_controls_and_readback.v1"
SURFACE_ID = "phase11_chat_schedule_ui_action_controls_and_readback"
PASS_ID = "studio-chat-schedule-ui-action-controls-and-readback"
STATUS = "COMPLETE / UI ACTION CONTROLS + READBACK READY / EXTERNAL CRON BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-manual-ui-test-closeout"

APPROVAL_ROOT = Path("runtime/studio/approvals")
SCHEDULE_ROOT = Path("runtime/schedules")
SCHEDULE_PROPOSAL_ROOT = Path("runtime/studio/chat/schedule-proposals")
EXPORT_PACKET_ROOT = Path("runtime/studio/chat/schedule-adapter-exports")

API_METHODS = [
    "get_phase11_chat_schedule_proposal_packet",
    "request_phase11_chat_schedule_proposal_packet",
    "execute_phase11_chat_schedule_proposal_consumption",
    "execute_phase11_chat_approved_schedule_intent_writer",
    "get_phase11_chat_schedule_intent_activation_readiness",
    "request_phase11_chat_schedule_intent_activation",
    "execute_phase11_chat_approved_schedule_activation",
    "get_phase11_chat_schedule_adapter_export_readiness",
    "request_phase11_chat_schedule_adapter_export",
    "execute_phase11_chat_approved_schedule_adapter_export_packet_writer",
]

CONTROL_STEPS = [
    {
        "step_id": "preview_schedule_proposal",
        "label": "Preview Proposal",
        "api_method": "get_phase11_chat_schedule_proposal_packet",
        "writes": False,
        "requires": ["workflow_id", "cron_expression", "runtime_adapter_target"],
        "produces": ["schedule_digest", "schedule_id"],
    },
    {
        "step_id": "queue_schedule_proposal",
        "label": "Queue Proposal",
        "api_method": "request_phase11_chat_schedule_proposal_packet",
        "writes": True,
        "requires": ["schedule_digest"],
        "produces": ["approval_id"],
    },
    {
        "step_id": "consume_schedule_proposal",
        "label": "Consume Proposal",
        "api_method": "execute_phase11_chat_schedule_proposal_consumption",
        "writes": True,
        "requires": ["approval_id", "schedule_digest"],
        "produces": ["staged_proposal_path"],
    },
    {
        "step_id": "write_schedule_intent",
        "label": "Write Intent",
        "api_method": "execute_phase11_chat_approved_schedule_intent_writer",
        "writes": True,
        "requires": ["staged_proposal_path", "schedule_digest", "operator_schedule_write_statement"],
        "produces": ["schedule_id"],
    },
    {
        "step_id": "preview_activation",
        "label": "Preview Activation",
        "api_method": "get_phase11_chat_schedule_intent_activation_readiness",
        "writes": False,
        "requires": ["schedule_id"],
        "produces": ["activation_digest"],
    },
    {
        "step_id": "queue_activation",
        "label": "Queue Activation",
        "api_method": "request_phase11_chat_schedule_intent_activation",
        "writes": True,
        "requires": ["schedule_id", "activation_digest"],
        "produces": ["approval_id"],
    },
    {
        "step_id": "execute_activation",
        "label": "Activate",
        "api_method": "execute_phase11_chat_approved_schedule_activation",
        "writes": True,
        "requires": ["approval_id", "activation_digest", "operator_activation_statement"],
        "produces": ["enabled_schedule"],
    },
    {
        "step_id": "preview_adapter_export",
        "label": "Preview Export",
        "api_method": "get_phase11_chat_schedule_adapter_export_readiness",
        "writes": False,
        "requires": ["runtime_adapter_target"],
        "produces": ["export_digest"],
    },
    {
        "step_id": "queue_adapter_export",
        "label": "Queue Export",
        "api_method": "request_phase11_chat_schedule_adapter_export",
        "writes": True,
        "requires": ["runtime_adapter_target", "export_digest"],
        "produces": ["approval_id"],
    },
    {
        "step_id": "write_export_packet",
        "label": "Write Export Packet",
        "api_method": "execute_phase11_chat_approved_schedule_adapter_export_packet_writer",
        "writes": True,
        "requires": ["approval_id", "export_digest", "operator_export_write_statement"],
        "produces": ["local_export_packet"],
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _latest_json_records(vault: Path, root: Path, *, limit: int = 5) -> list[dict[str, Any]]:
    absolute_root = vault / root
    if not absolute_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(absolute_root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        records.append(
            {
                "path": _rel(vault, path),
                "filename": path.name,
                "status": payload.get("status") or payload.get("packet_type") or "json",
                "approval_id": payload.get("id") or payload.get("approval_id"),
                "schedule_id": payload.get("schedule_id")
                or (payload.get("target_write") or {}).get("schedule_id")
                or payload.get("schedule_id_filter"),
                "digest": payload.get("export_digest")
                or payload.get("schedule_digest")
                or payload.get("activation_digest"),
            }
        )
        if len(records) >= limit:
            break
    return records


def _approval_counts(vault: Path) -> dict[str, Any]:
    root = vault / APPROVAL_ROOT
    counts = {"pending": 0, "approved": 0, "executed": 0, "rejected": 0, "total": 0}
    latest: list[dict[str, Any]] = []
    if not root.exists():
        return {"counts": counts, "latest_schedule_approvals": latest}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path)
        if not payload:
            continue
        metadata = ((payload.get("action_spec") or {}).get("metadata") or {})
        schedule_related = any(
            metadata.get(key) is True
            for key in (
                "phase11_chat_schedule_proposal_packet",
                "phase11_chat_schedule_proposal_execution_blocked",
                "phase11_chat_schedule_intent_activation_readiness",
                "phase11_chat_schedule_adapter_export_readiness",
            )
        )
        if not schedule_related:
            continue
        status = str(payload.get("status") or "unknown")
        counts["total"] += 1
        if status in counts:
            counts[status] += 1
        if len(latest) < 5:
            latest.append(
                {
                    "approval_id": payload.get("id") or path.stem,
                    "status": status,
                    "path": _rel(vault, path),
                    "action_type": (payload.get("action_spec") or {}).get("action_type"),
                    "target_path": (payload.get("action_spec") or {}).get("target_path"),
                    "schedule_digest": metadata.get("schedule_digest"),
                    "activation_digest": metadata.get("activation_digest"),
                    "export_digest": metadata.get("export_digest"),
                }
            )
    return {"counts": counts, "latest_schedule_approvals": latest}


def _schedule_readback(vault: Path, adapter: str) -> dict[str, Any]:
    schedules = list_schedules(vault, check_registry=False)
    compact = [
        {
            "schedule_id": schedule.schedule_id,
            "workflow_id": schedule.workflow_id,
            "schedule_kind": schedule.schedule_kind,
            "command_id": schedule.command_id,
            "runtime_adapter_target": schedule.runtime_adapter_target,
            "cron_expression": schedule.cadence.cron_expression,
            "timezone": schedule.cadence.timezone,
            "enabled": schedule.enabled,
            "shadow_mode": schedule.shadow_mode,
        }
        for schedule in schedules
    ]
    try:
        adapter_entries = export_schedules_for_adapter(adapter, vault, enabled_only=True)
        adapter_error = None
    except Exception as exc:
        adapter_entries = []
        adapter_error = str(exc)
    return {
        "schedule_count": len(compact),
        "enabled_schedule_count": len([item for item in compact if item.get("enabled")]),
        "disabled_schedule_count": len([item for item in compact if not item.get("enabled")]),
        "latest_schedules": compact[:8],
        "adapter_enabled_entry_count": len(adapter_entries),
        "adapter_enabled_schedule_ids": [str(item.get("schedule_id") or "") for item in adapter_entries],
        "adapter_export_error": adapter_error,
    }


def build_phase11_chat_schedule_ui_action_controls_and_readback(
    vault_root: str | Path,
    *,
    default_runtime_adapter_target: str | None = None,
) -> dict[str, Any]:
    """Return the manual UI control/readback contract for the schedule chain."""

    vault = Path(vault_root).resolve()
    adapter = str(default_runtime_adapter_target or DEFAULT_RUNTIME_ADAPTER or "openclaw").strip().lower()
    adapter_registered = adapter in VALID_RUNTIME_ADAPTERS
    if not adapter_registered:
        adapter = "openclaw"

    readback = _schedule_readback(vault, adapter)
    approvals = _approval_counts(vault)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "read_only_contract": True,
        "summary": {
            "ui_controls_ready": True,
            "manual_ui_test_ready": True,
            "readback_ready": True,
            "default_runtime_adapter_target": adapter,
            "runtime_adapter_registered": adapter_registered,
            "control_step_count": len(CONTROL_STEPS),
            "api_method_count": len(API_METHODS),
            "manual_chain_requires_operator_clicks": True,
            "manual_chain_requires_exact_digests": True,
            "manual_chain_requires_approval_ids": True,
            "no_secret_fields_rendered": True,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "ui_contract": {
            "render_function": "_phase11ChatScheduleUiActionControlsAndReadback",
            "event_handler": "_phase11ScheduleRunAction",
            "controls_rendered": True,
            "readback_panel_rendered": True,
            "local_browser_state_used_for_last_response": True,
            "requires_manual_copying_of_digest_ids": False,
            "input_fields": [
                "workflow_id",
                "cron_expression",
                "timezone_name",
                "runtime_adapter_target",
                "schedule_summary",
                "schedule_id",
                "approval_id",
                "schedule_digest",
                "activation_digest",
                "export_digest",
                "operator_approval_statement",
                "operator_schedule_write_statement",
                "operator_activation_statement",
                "operator_export_write_statement",
            ],
            "secret_fields": [],
            "credential_fields": [],
        },
        "api_methods": API_METHODS,
        "control_steps": CONTROL_STEPS,
        "readback_roots": {
            "schedule_intents": SCHEDULE_ROOT.as_posix(),
            "schedule_index": "runtime/schedules/index.yaml",
            "approval_queue": APPROVAL_ROOT.as_posix(),
            "staged_schedule_proposals": SCHEDULE_PROPOSAL_ROOT.as_posix(),
            "local_adapter_export_packets": EXPORT_PACKET_ROOT.as_posix(),
            "proposal_consumption_markers": "runtime/studio/approvals/_chat_schedule_proposal_consumption_markers",
            "activation_markers": "runtime/studio/approvals/_chat_schedule_activation_markers",
            "adapter_export_packet_markers": "runtime/studio/approvals/_chat_schedule_adapter_export_packet_markers",
        },
        "latest_readback": {
            **readback,
            "schedule_approval_counts": approvals["counts"],
            "latest_schedule_approvals": approvals["latest_schedule_approvals"],
            "latest_staged_schedule_proposals": _latest_json_records(vault, SCHEDULE_PROPOSAL_ROOT),
            "latest_local_adapter_export_packets": _latest_json_records(vault, EXPORT_PACKET_ROOT),
        },
        "authority": {
            "ui_preview_allowed": True,
            "readback_allowed": True,
            "existing_api_methods_callable_from_ui": True,
            "schedule_proposal_approval_queue_write_allowed_with_digest": True,
            "approved_schedule_proposal_consumption_allowed": True,
            "approved_schedule_intent_write_allowed": True,
            "approved_schedule_activation_allowed": True,
            "approved_adapter_export_packet_write_allowed": True,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "studio_runtime_chat_schedule_ui_action_controls_and_readback_ready": True,
            "studio_chat_schedule_manual_ui_test_ready": True,
            "studio_chat_schedule_ui_controls_rendered": True,
            "studio_chat_schedule_ui_readback_ready": True,
            "studio_chat_schedule_ui_no_secret_fields": True,
            "studio_chat_schedule_external_cron_still_blocked": True,
            "studio_chat_schedule_runtime_dispatch_still_blocked": True,
        },
        "blocked_reasons": [],
        "warnings": [] if adapter_registered else ["default_runtime_adapter_target_not_registered_fell_back_to_openclaw"],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
