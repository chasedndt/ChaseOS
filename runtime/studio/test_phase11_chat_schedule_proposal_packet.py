"""Tests for Studio Chat schedule proposal approval packets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.phase11_chat_route_state_and_message_drafts import (
    build_phase11_chat_route_state_and_message_drafts,
)
from runtime.studio.phase11_chat_schedule_proposal_packet import (
    build_phase11_chat_schedule_proposal_packet,
)
from runtime.studio.service import StudioService, StudioServiceError


def test_preview_builds_schedule_digest_without_schedule_or_scheduler_effects(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        selected_thread_id="runtime-ops-schedules",
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today at 0800 on weekdays for a guarded shadow run.",
    )
    summary = payload["summary"]
    digest = payload["digest_proof"]
    target = payload["target_write_proof"]
    intent = payload["future_schedule_intent_preview"]
    authority = payload["authority"]

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_chat_schedule_proposal_packet"
    assert summary["schedule_kind"] == "workflow"
    assert summary["workflow_id"] == "operator_today"
    assert summary["workflow_task_type"] == "operator-briefing"
    assert summary["cron_expression"] == "0 8 * * 1-5"
    assert summary["runtime_adapter_target"] == "openclaw"
    assert summary["enabled_after_future_execution"] is False
    assert summary["shadow_mode_after_future_execution"] is True
    assert summary["queue_write_preview_ready"] is True
    assert digest["schedule_digest"]
    assert digest["digest_required_for_write"] is True
    assert summary["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert target["target_path"].startswith("runtime/schedules/sch-studio-chat-operator-today-")
    assert target["target_path"].endswith(".yaml")
    assert (tmp_path / target["target_path"]).exists() is False
    assert target["schedule_intent_written"] is False
    assert target["schedule_index_regenerated"] is False
    assert target["external_scheduler_changed"] is False
    assert target["runtime_dispatched"] is False
    assert target["provider_call_performed"] is False
    assert intent["workflow_id"] == "operator_today"
    assert "operator-briefing" in intent["allowed_workflow_task_types"]
    assert "operator_today" in payload["future_schedule_yaml_preview"]
    assert authority["approval_queue_write_allowed_with_digest"] is True
    assert authority["schedule_intent_write_allowed"] is False
    assert "schedule_intent_write" in payload["denied_by_this_surface"]


def test_preview_uses_route_state_and_draft_when_no_explicit_thread_or_summary(tmp_path: Path) -> None:
    build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="runtime-ops-schedules",
        draft_text="Create a weekday close-day schedule for operator_close_day at 19:00.",
        message_intent="schedule_proposal_draft",
        write_route_state=True,
        write_draft=True,
    )

    payload = build_phase11_chat_schedule_proposal_packet(tmp_path)

    assert payload["ok"] is True
    assert payload["summary"]["workflow_id"] == "operator_close_day"
    assert payload["summary"]["cron_expression"] == "0 19 * * 1-5"
    assert payload["summary"]["route_state_used"] is True
    assert payload["summary"]["source_text_kind"] == "message_draft"
    assert payload["source_preview"]["draft_found"] is True
    assert payload["target_write_proof"]["schedule_intent_written"] is False


def test_command_schedule_preview_uses_valid_command_contract(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        schedule_kind="command",
        command_id="events.watch",
        cron_expression="* * * * *",
        schedule_summary="Run the events watcher every minute through the schedule intent layer.",
    )
    intent = payload["future_schedule_intent_preview"]

    assert payload["ok"] is True
    assert payload["summary"]["schedule_kind"] == "command"
    assert payload["summary"]["command_id"] == "events.watch"
    assert intent["command"] == "chaseos events watch --once --execute"
    assert intent["allowed_command_ids"] == ["events.watch"]
    assert payload["target_write_proof"]["schedule_intent_written"] is False


def test_write_requires_exact_schedule_digest(tmp_path: Path) -> None:
    preview = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    payload = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
        expected_schedule_digest="bad-digest",
        write_approval=True,
    )

    assert preview["digest_proof"]["schedule_digest"]
    assert payload["ok"] is False
    assert "expected_schedule_digest_mismatch" in payload["blocked_reasons"]
    assert payload["summary"]["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert (tmp_path / StudioService.APPROVAL_DIR).exists() is False


def test_exact_digest_queues_approval_without_schedule_write_and_blocks_ambient_execution(
    tmp_path: Path,
) -> None:
    kwargs = {
        "workflow_id": "operator_today",
        "cron_expression": "0 8 * * 1-5",
        "schedule_summary": "Schedule operator_today for a later morning check.",
    }
    preview = build_phase11_chat_schedule_proposal_packet(tmp_path, **kwargs)
    digest = preview["digest_proof"]["schedule_digest"]

    payload = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        **kwargs,
        expected_schedule_digest=digest,
        write_approval=True,
    )
    summary = payload["summary"]
    target_path = Path(summary["target_path_preview"])

    assert payload["ok"] is True
    assert summary["approval_request_created"] is True
    assert payload["approval_queue_write"]["queue_writer_called"] is True
    assert payload["audit_record"]["audit_record_written"] is True
    assert payload["target_write_proof"]["target_file_written"] is False
    assert payload["target_write_proof"]["schedule_intent_written"] is False
    assert (tmp_path / target_path).exists() is False
    assert (tmp_path / payload["approval_queue_write"]["approval_artifact_path"]).exists()
    assert (tmp_path / payload["audit_record"]["audit_record_path"]).exists()

    service = StudioService(tmp_path)
    service.approve(summary["approval_id"])
    with pytest.raises(StudioServiceError, match="schedule proposal"):
        service.execute_approved(summary["approval_id"])
    assert (tmp_path / target_path).exists() is False


def test_duplicate_schedule_digest_returns_existing_request(tmp_path: Path) -> None:
    kwargs = {
        "workflow_id": "operator_today",
        "cron_expression": "0 8 * * 1-5",
        "schedule_summary": "Schedule operator_today for a later morning check.",
    }
    preview = build_phase11_chat_schedule_proposal_packet(tmp_path, **kwargs)
    digest = preview["digest_proof"]["schedule_digest"]

    first = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        **kwargs,
        expected_schedule_digest=digest,
        write_approval=True,
    )
    second = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        **kwargs,
        expected_schedule_digest=digest,
        write_approval=True,
    )

    assert first["summary"]["approval_request_created"] is True
    assert second["ok"] is True
    assert second["summary"]["approval_request_created"] is False
    assert second["summary"]["duplicate_active_request_present"] is True
    assert second["summary"]["duplicate_returned_existing_request"] is True
    assert second["summary"]["approval_id"] == first["summary"]["approval_id"]


def test_secret_bearing_schedule_request_blocks_queue_write_and_redacts_payload(tmp_path: Path) -> None:
    raw_secret = "test-key-abcdefghijklmnopqrstuvwxyz123456"
    payload = build_phase11_chat_schedule_proposal_packet(
        tmp_path,
        workflow_id="operator_today",
        schedule_summary=f"Schedule this with api_key={raw_secret}",
        expected_schedule_digest="not-used",
        write_approval=True,
    )
    encoded = json.dumps(payload)

    assert payload["ok"] is False
    assert "secret_or_credential_indicator_present" in payload["blocked_reasons"]
    assert payload["secret_redaction"]["source_contains_secret"] is True
    assert payload["summary"]["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert raw_secret not in encoded
    assert "[REDACTED_SECRET]" in encoded
