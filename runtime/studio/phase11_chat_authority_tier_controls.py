"""Unified Phase 11 Chat authority-tier controls.

This surface groups the next high-authority Chat lanes into one operator-facing
control block. It is intentionally a control/readiness layer only: no provider
call, secret read, Discord call, Agent Bus write, runtime dispatch, cron apply,
or approval consumption happens here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.discord_bindings import build_discord_binding_validation
from runtime.studio.phase11_chat_live_provider_approval_preview import (
    build_phase11_chat_live_provider_execution_approval_preview,
)
from runtime.studio.phase11_chat_runtime_dispatch_readiness import (
    build_phase11_chat_runtime_dispatch_readiness,
)
from runtime.studio.phase11_chat_schedule_ui_action_controls_and_readback import (
    build_phase11_chat_schedule_ui_action_controls_and_readback,
)
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "studio.phase11_chat_authority_tier_controls.v1"
SURFACE_ID = "phase11_chat_authority_tier_controls"
PASS_ID = "studio-chat-authority-tier-controls"
STATUS = "PARTIAL / CHAT CONTROL SURFACE READY / DIRECT EXECUTION BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-authority-tier-approval-action-controls"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault(vault_root: str | Path) -> Path:
    return Path(vault_root).expanduser().resolve()


def _summary_status(ok: bool, ready: bool, blocked: bool) -> str:
    if ready and not blocked:
        return "ready"
    if ok:
        return "approval_gated" if blocked else "preview_ready"
    return "blocked"


def _lane(
    *,
    lane_id: str,
    label: str,
    purpose: str,
    source_surface: str,
    control_target: str,
    status: str,
    safe_preview_enabled: bool,
    approval_action_available: bool,
    direct_execution_allowed: bool = False,
    approval_required: bool = True,
    blocked_reasons: list[str] | None = None,
    authority_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "label": label,
        "purpose": purpose,
        "source_surface": source_surface,
        "control_target": control_target,
        "status": status,
        "safe_preview_enabled": safe_preview_enabled,
        "approval_action_available": approval_action_available,
        "approval_required": approval_required,
        "direct_execution_allowed": direct_execution_allowed,
        "chat_button": {
            "label": "Open lane",
            "enabled": True,
            "action": "scroll_to_existing_chat_surface",
            "target": control_target,
            "side_effect": "navigation_only",
        },
        "execute_button": {
            "label": "Execute",
            "enabled": False,
            "disabled_reason": "direct_execution_blocked_from_chat_authority_tier_controls",
            "side_effect": "none",
        },
        "blocked_reasons": list(dict.fromkeys(blocked_reasons or [])),
        "authority": {
            "direct_execution_allowed": direct_execution_allowed,
            "safe_preview_enabled": safe_preview_enabled,
            "approval_required": approval_required,
            "approval_action_available": approval_action_available,
            "credential_values_visible": False,
            "provider_call_performed": False,
            "discord_api_called": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "canonical_mutation_performed": False,
            **(authority_flags or {}),
        },
    }


def build_phase11_chat_authority_tier_controls(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
) -> dict[str, Any]:
    """Build a no-side-effect authority-tier control model for the Chat page."""

    root = _vault(vault_root)
    normalized_message = " ".join(str(message or "").strip().split())
    provider_readiness = build_studio_provider_readiness(root)
    provider_summary = provider_readiness.get("summary") or {}
    provider_authority = provider_readiness.get("authority") or {}
    live_provider = build_phase11_chat_live_provider_execution_approval_preview(
        root,
        message=normalized_message,
        explicit_intent=explicit_intent or "chat-answer",
    )
    live_summary = live_provider.get("summary") or {}
    runtime_dispatch = build_phase11_chat_runtime_dispatch_readiness(
        root,
        message=normalized_message,
        explicit_intent=explicit_intent or "runtime-task",
    )
    runtime_summary = runtime_dispatch.get("summary") or {}
    bus = runtime_dispatch.get("agent_bus_snapshot") or {}
    discord = build_discord_binding_validation(root)
    discord_summary = discord.get("summary") or {}
    schedule = build_phase11_chat_schedule_ui_action_controls_and_readback(root)
    schedule_summary = schedule.get("summary") or {}

    provider_ready = provider_summary.get("readiness_status") in {"ready", "degraded_ready", "configured"}
    provider_blockers = list(live_provider.get("blocked_reasons") or [])
    runtime_blockers = list(runtime_dispatch.get("blocked_reasons") or [])
    discord_blockers = list(discord.get("blockers") or [])
    schedule_blockers = list(schedule.get("blocked_reasons") or [])
    bus_readable = bool(bus.get("known_storage_readable") or bus.get("sqlite_present") or bus.get("mode") == "local")

    lanes = [
        _lane(
            lane_id="provider_calls",
            label="Provider Calls",
            purpose="Prepare a governed live model/provider call after credentials and approval are ready.",
            source_surface="phase11_chat_live_provider_execution_approval_preview",
            control_target=".phase11-chat-live-provider",
            status=_summary_status(bool(live_provider.get("ok")), bool(live_summary.get("approval_preview_ready")), True),
            safe_preview_enabled=True,
            approval_action_available=bool(live_summary.get("approval_preview_ready")),
            blocked_reasons=provider_blockers,
            authority_flags={
                "provider_calls_allowed": False,
                "approval_queue_write_allowed": False,
            },
        ),
        _lane(
            lane_id="credentials",
            label="Credentials",
            purpose="Show no-secret provider credential readiness so later OpenAI tests can run without exposing key values.",
            source_surface="studio_provider_readiness",
            control_target="#chat-provider-readiness",
            status=str(provider_summary.get("readiness_status") or "unknown"),
            safe_preview_enabled=True,
            approval_action_available=False,
            approval_required=False,
            blocked_reasons=list(provider_readiness.get("blocked_reasons") or []),
            authority_flags={
                "credential_reference_present": bool(
                    provider_summary.get("primary_provider_env_present")
                    or provider_authority.get("secret_reference_resolvable")
                ),
                "credential_values_visible": False,
                "secret_read_allowed": False,
            },
        ),
        _lane(
            lane_id="runtime_dispatch",
            label="Runtime Dispatch",
            purpose="Prepare an approved runtime dispatch request for Hermes, OpenClaw, Codex, or future runtimes.",
            source_surface="phase11_chat_runtime_dispatch_readiness_contract",
            control_target=".phase11-chat-runtime-dispatch",
            status=_summary_status(
                bool(runtime_dispatch.get("ok")),
                bool(runtime_summary.get("dispatch_preview_ready")),
                True,
            ),
            safe_preview_enabled=True,
            approval_action_available=bool(runtime_summary.get("dispatch_preview_ready")),
            blocked_reasons=runtime_blockers,
            authority_flags={
                "runtime_dispatch_allowed": False,
                "workflow_dispatch_allowed": False,
            },
        ),
        _lane(
            lane_id="agent_bus_tasks",
            label="Agent Bus Tasks",
            purpose="Inspect the bus and prepare future task packets without writing tasks directly from Chat.",
            source_surface="phase11_chat_runtime_dispatch_readiness_contract",
            control_target=".phase11-chat-runtime-dispatch",
            status="readable" if bus_readable else "blocked",
            safe_preview_enabled=True,
            approval_action_available=bool(runtime_summary.get("dispatch_preview_ready")),
            blocked_reasons=list(bus.get("blocked_reasons") or runtime_blockers),
            authority_flags={
                "agent_bus_task_write_allowed": False,
                "agent_bus_storage_readable": bus_readable,
            },
        ),
        _lane(
            lane_id="discord_actions",
            label="Discord Actions",
            purpose="Surface Discord control-plane readiness for future open chat, thread creation, and message send approvals.",
            source_surface="chaseos_discord_binding_validation",
            control_target=".phase11-chat-workspaces",
            status=str(discord_summary.get("status") or discord_summary.get("readiness_status") or "unknown"),
            safe_preview_enabled=True,
            approval_action_available=False,
            blocked_reasons=discord_blockers,
            authority_flags={
                "discord_api_calls_allowed": False,
                "discord_thread_create_allowed": False,
                "discord_message_send_allowed": False,
            },
        ),
        _lane(
            lane_id="external_cron_apply",
            label="External Cron Apply",
            purpose="Prepare the later bridge from ChaseOS schedule/export packets into OpenClaw or Hermes cron/runtime scheduling.",
            source_surface="phase11_chat_schedule_ui_action_controls_and_readback",
            control_target=".phase11-chat-schedule-ui-controls",
            status="local_schedule_controls_ready" if schedule_summary.get("manual_ui_test_ready") else "blocked",
            safe_preview_enabled=True,
            approval_action_available=bool(schedule_summary.get("manual_ui_test_ready")),
            blocked_reasons=schedule_blockers,
            authority_flags={
                "external_scheduler_mutation_allowed": False,
                "openclaw_cron_mutation_allowed": False,
                "hermes_cron_mutation_allowed": False,
            },
        ),
    ]

    authority = {
        "chat_authority_tier_controls_visible": True,
        "direct_execution_allowed": False,
        "safe_preview_navigation_allowed": True,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "secret_value_read": False,
        "discord_api_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_dispatch_allowed": False,
        "external_scheduler_mutation_allowed": False,
        "openclaw_cron_mutation_allowed": False,
        "hermes_cron_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "summary": {
            "lane_count": len(lanes),
            "visible_in_chat": True,
            "safe_preview_navigation_ready": True,
            "direct_execution_blocked": True,
            "provider_lane_present": True,
            "credential_lane_present": True,
            "runtime_dispatch_lane_present": True,
            "agent_bus_lane_present": True,
            "discord_lane_present": True,
            "external_cron_apply_lane_present": True,
            "manual_test_ready": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "lanes": lanes,
        "authority": authority,
        "readiness": {
            "phase11_chat_authority_tier_controls_ready": True,
            "phase11_chat_authority_tier_controls_visible": True,
            "phase11_chat_authority_tier_controls_navigation_only": True,
            "phase11_chat_authority_tier_direct_execution_blocked": True,
            "phase11_chat_authority_tier_no_secret_values": True,
            "phase11_chat_authority_tier_provider_calls_blocked": True,
            "phase11_chat_authority_tier_discord_calls_blocked": True,
            "phase11_chat_authority_tier_agent_bus_writes_blocked": True,
            "phase11_chat_authority_tier_runtime_dispatch_blocked": True,
            "phase11_chat_authority_tier_external_cron_blocked": True,
        },
        "blocked_reasons": [
            "direct_execution_blocked_from_chat_authority_tier_controls",
            "approval_consumption_requires_specific_executor",
            "external_actions_require_separate_operator_approval",
        ],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_phase11_chat_authority_tier_controls(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lanes = payload.get("lanes") or []
    return "\n".join(
        [
            f"Surface: {payload.get('surface')}",
            f"Status: {payload.get('status')}",
            f"Lanes: {summary.get('lane_count')}",
            "Direct execution: blocked",
            "Lane status:",
            *[
                f"- {lane.get('label')}: {lane.get('status')} ({lane.get('source_surface')})"
                for lane in lanes
            ],
        ]
    )
