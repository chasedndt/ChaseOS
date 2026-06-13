"""Tests for Studio Chat schedule UI action controls and readback."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_chat_schedule_ui_action_controls_and_readback import (
    API_METHODS,
    CONTROL_STEPS,
    build_phase11_chat_schedule_ui_action_controls_and_readback,
)


def test_schedule_ui_action_controls_contract_is_manual_test_ready(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_ui_action_controls_and_readback(tmp_path)

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_chat_schedule_ui_action_controls_and_readback"
    assert payload["summary"]["ui_controls_ready"] is True
    assert payload["summary"]["manual_ui_test_ready"] is True
    assert payload["summary"]["readback_ready"] is True
    assert payload["summary"]["no_secret_fields_rendered"] is True
    assert payload["summary"]["external_scheduler_mutation_allowed"] is False
    assert payload["summary"]["openclaw_cron_mutation_allowed"] is False
    assert payload["summary"]["hermes_cron_mutation_allowed"] is False
    assert payload["summary"]["agent_bus_task_write_allowed"] is False
    assert payload["summary"]["runtime_dispatch_allowed"] is False
    assert payload["summary"]["discord_api_calls_allowed"] is False
    assert payload["summary"]["provider_calls_allowed"] is False
    assert payload["summary"]["credential_values_visible"] is False
    assert payload["readiness"]["studio_runtime_chat_schedule_ui_action_controls_and_readback_ready"] is True
    assert payload["readiness"]["studio_chat_schedule_external_cron_still_blocked"] is True


def test_schedule_ui_action_controls_lists_full_local_chain(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_ui_action_controls_and_readback(tmp_path)
    step_ids = [step["step_id"] for step in payload["control_steps"]]

    assert payload["api_methods"] == API_METHODS
    assert payload["control_steps"] == CONTROL_STEPS
    assert "preview_schedule_proposal" in step_ids
    assert "queue_schedule_proposal" in step_ids
    assert "consume_schedule_proposal" in step_ids
    assert "write_schedule_intent" in step_ids
    assert "preview_activation" in step_ids
    assert "execute_activation" in step_ids
    assert "preview_adapter_export" in step_ids
    assert "write_export_packet" in step_ids
    assert "execute_phase11_chat_approved_schedule_adapter_export_packet_writer" in payload["api_methods"]


def test_schedule_ui_action_controls_exposes_git_safe_readback_roots(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_ui_action_controls_and_readback(tmp_path)

    assert payload["readback_roots"]["schedule_intents"] == "runtime/schedules"
    assert payload["readback_roots"]["approval_queue"] == "runtime/studio/approvals"
    assert payload["readback_roots"]["local_adapter_export_packets"] == (
        "runtime/studio/chat/schedule-adapter-exports"
    )
    assert payload["ui_contract"]["secret_fields"] == []
    assert payload["ui_contract"]["credential_fields"] == []
    assert "approval_id" in payload["ui_contract"]["input_fields"]
    assert "export_digest" in payload["ui_contract"]["input_fields"]
