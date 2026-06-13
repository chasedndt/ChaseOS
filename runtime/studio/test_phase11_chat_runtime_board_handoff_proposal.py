"""Tests for Studio Chat runtime board handoff approval proposals."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.phase11_chat_route_state_and_message_drafts import (
    build_phase11_chat_route_state_and_message_drafts,
)
from runtime.studio.phase11_chat_runtime_board_handoff_proposal import (
    build_phase11_chat_runtime_board_handoff_proposal,
)
from runtime.studio.service import StudioService, StudioServiceError


def test_preview_builds_board_handoff_digest_without_runtime_or_board_effects(tmp_path: Path) -> None:
    payload = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary="Move this OpenClaw runtime chat into the triage board for review.",
    )
    summary = payload["summary"]
    digest = payload["digest_proof"]
    target = payload["target_write_proof"]
    authority = payload["authority"]

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_chat_runtime_board_handoff_proposal"
    assert summary["runtime_id"] == "OpenClaw"
    assert summary["thread_id"] == "runtime-ops-openclaw-chat"
    assert summary["board_target_id"] == "openclaw-kanban"
    assert summary["board_lane"] == "triage"
    assert summary["queue_write_preview_ready"] is True
    assert digest["handoff_digest"]
    assert digest["digest_required_for_write"] is True
    assert summary["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert target["target_path"].startswith("runtime/boards/openclaw/openclaw-kanban/")
    assert target["target_file_written"] is False
    assert (tmp_path / target["target_path"]).exists() is False
    assert target["runtime_board_written"] is False
    assert target["agent_bus_task_written"] is False
    assert target["runtime_dispatched"] is False
    assert target["discord_api_called"] is False
    assert target["provider_call_performed"] is False
    assert authority["approval_queue_write_allowed_with_digest"] is True
    assert authority["runtime_board_write_allowed"] is False
    assert "runtime_board_write" in payload["denied_by_this_surface"]


def test_preview_uses_route_state_and_draft_when_no_explicit_thread_or_summary(tmp_path: Path) -> None:
    build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="runtime-ops-hermes-chat",
        draft_text="Ask Hermes to keep this follow-up visible on the runtime board.",
        message_intent="runtime_board_handoff_draft",
        write_route_state=True,
        write_draft=True,
    )

    payload = build_phase11_chat_runtime_board_handoff_proposal(tmp_path)

    assert payload["ok"] is True
    assert payload["summary"]["runtime_id"] == "Hermes"
    assert payload["summary"]["thread_id"] == "runtime-ops-hermes-chat"
    assert payload["summary"]["route_state_used"] is True
    assert payload["summary"]["source_text_kind"] == "message_draft"
    assert payload["source_preview"]["draft_found"] is True
    assert payload["future_board_item_preview"]["handoff_summary"].startswith("Ask Hermes")
    assert payload["target_write_proof"]["runtime_board_written"] is False


def test_write_requires_exact_handoff_digest(tmp_path: Path) -> None:
    preview = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        selected_thread_id="runtime-ops-codex-patches",
        handoff_summary="Put this repo inspection request into the Codex patch queue.",
    )
    payload = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        selected_thread_id="runtime-ops-codex-patches",
        handoff_summary="Put this repo inspection request into the Codex patch queue.",
        expected_handoff_digest="bad-digest",
        write_approval=True,
    )

    assert preview["digest_proof"]["handoff_digest"]
    assert payload["ok"] is False
    assert "expected_handoff_digest_mismatch" in payload["blocked_reasons"]
    assert payload["summary"]["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert (tmp_path / StudioService.APPROVAL_DIR).exists() is False


def test_exact_digest_queues_approval_without_target_write_and_blocks_ambient_execution(
    tmp_path: Path,
) -> None:
    message = "Send this OpenClaw chat to the board for review."
    preview = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary=message,
    )
    digest = preview["digest_proof"]["handoff_digest"]

    payload = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary=message,
        expected_handoff_digest=digest,
        write_approval=True,
    )
    summary = payload["summary"]
    target_path = Path(summary["target_path_preview"])

    assert payload["ok"] is True
    assert summary["approval_request_created"] is True
    assert payload["approval_queue_write"]["queue_writer_called"] is True
    assert payload["audit_record"]["audit_record_written"] is True
    assert payload["target_write_proof"]["target_file_written"] is False
    assert (tmp_path / target_path).exists() is False
    assert (tmp_path / payload["approval_queue_write"]["approval_artifact_path"]).exists()
    assert (tmp_path / payload["audit_record"]["audit_record_path"]).exists()

    service = StudioService(tmp_path)
    service.approve(summary["approval_id"])
    with pytest.raises(StudioServiceError, match="runtime board handoff"):
        service.execute_approved(summary["approval_id"])
    assert (tmp_path / target_path).exists() is False


def test_duplicate_handoff_digest_returns_existing_request(tmp_path: Path) -> None:
    kwargs = {
        "selected_thread_id": "runtime-ops-codex-patches",
        "handoff_summary": "Queue Codex patch follow-up on the runtime board.",
    }
    preview = build_phase11_chat_runtime_board_handoff_proposal(tmp_path, **kwargs)
    digest = preview["digest_proof"]["handoff_digest"]

    first = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        **kwargs,
        expected_handoff_digest=digest,
        write_approval=True,
    )
    second = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        **kwargs,
        expected_handoff_digest=digest,
        write_approval=True,
    )

    assert first["summary"]["approval_request_created"] is True
    assert second["ok"] is True
    assert second["summary"]["approval_request_created"] is False
    assert second["summary"]["duplicate_active_request_present"] is True
    assert second["summary"]["duplicate_returned_existing_request"] is True
    assert second["summary"]["approval_id"] == first["summary"]["approval_id"]


def test_secret_bearing_handoff_blocks_queue_write_and_redacts_payload(tmp_path: Path) -> None:
    raw_secret = "test-key-abcdefghijklmnopqrstuvwxyz123456"
    payload = build_phase11_chat_runtime_board_handoff_proposal(
        tmp_path,
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary=f"Move this to the board with token={raw_secret}",
        expected_handoff_digest="not-used",
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
