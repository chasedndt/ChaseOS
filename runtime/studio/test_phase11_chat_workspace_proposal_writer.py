"""Tests for the Phase 11 Studio Chat workspace proposal writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.phase11_chat_workspace_proposal_writer import (
    build_phase11_chat_workspace_proposal_writer,
)
from runtime.studio.service import StudioService, StudioServiceError


def test_preview_builds_digest_without_chat_or_runtime_effects(tmp_path: Path) -> None:
    payload = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message="Create an OpenClaw runtime thread for approval triage",
    )
    summary = payload["summary"]
    digest = payload["digest_proof"]
    target = payload["target_write_proof"]
    authority = payload["authority"]

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_chat_workspace_proposal_writer"
    assert summary["proposal_kind"] == "create_thread"
    assert summary["runtime_id"] == "OpenClaw"
    assert summary["queue_write_preview_ready"] is True
    assert digest["proposal_digest"]
    assert digest["digest_required_for_write"] is True
    assert summary["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert target["target_path"].startswith("runtime/studio/chat/workspace-proposals/")
    assert target["target_file_written"] is False
    assert (tmp_path / target["target_path"]).exists() is False
    assert target["chat_thread_created"] is False
    assert target["discord_api_called"] is False
    assert target["agent_bus_task_written"] is False
    assert target["runtime_board_written"] is False
    assert target["schedule_mutated"] is False
    assert target["provider_call_performed"] is False
    assert authority["approval_queue_write_allowed_with_digest"] is True
    assert authority["chat_thread_create_allowed"] is False
    assert "chat_thread_create" in payload["denied_by_this_surface"]


def test_write_requires_exact_proposal_digest(tmp_path: Path) -> None:
    preview = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message="Create a Hermes runtime thread",
    )
    payload = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message="Create a Hermes runtime thread",
        expected_proposal_digest="bad-digest",
        write_approval=True,
    )

    assert preview["digest_proof"]["proposal_digest"]
    assert payload["ok"] is False
    assert "expected_proposal_digest_mismatch" in payload["blocked_reasons"]
    assert payload["summary"]["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert (tmp_path / StudioService.APPROVAL_DIR).exists() is False


def test_exact_digest_queues_pending_approval_without_target_write_and_blocks_ambient_execution(
    tmp_path: Path,
) -> None:
    message = "Create an OpenClaw runtime thread for venture board review"
    preview = build_phase11_chat_workspace_proposal_writer(tmp_path, message=message)
    digest = preview["digest_proof"]["proposal_digest"]

    payload = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message=message,
        expected_proposal_digest=digest,
        write_approval=True,
    )
    summary = payload["summary"]
    target_path = Path(summary["target_path_preview"])

    assert payload["ok"] is True
    assert summary["approval_request_created"] is True
    assert summary["approval_id"]
    assert payload["approval_queue_write"]["queue_writer_called"] is True
    assert payload["audit_record"]["audit_record_written"] is True
    assert payload["target_write_proof"]["target_file_written"] is False
    assert (tmp_path / target_path).exists() is False
    assert (tmp_path / payload["approval_queue_write"]["approval_artifact_path"]).exists()
    assert (tmp_path / payload["audit_record"]["audit_record_path"]).exists()

    service = StudioService(tmp_path)
    service.approve(summary["approval_id"])
    with pytest.raises(StudioServiceError, match="workspace proposal"):
        service.execute_approved(summary["approval_id"])
    assert (tmp_path / target_path).exists() is False


def test_duplicate_digest_returns_existing_active_request(tmp_path: Path) -> None:
    message = "Create a Codex runtime thread for repo inspection"
    preview = build_phase11_chat_workspace_proposal_writer(tmp_path, message=message)
    digest = preview["digest_proof"]["proposal_digest"]

    first = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message=message,
        expected_proposal_digest=digest,
        write_approval=True,
    )
    second = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message=message,
        expected_proposal_digest=digest,
        write_approval=True,
    )

    assert first["summary"]["approval_request_created"] is True
    assert second["ok"] is True
    assert second["summary"]["approval_request_created"] is False
    assert second["summary"]["duplicate_active_request_present"] is True
    assert second["summary"]["duplicate_returned_existing_request"] is True
    assert second["summary"]["approval_id"] == first["summary"]["approval_id"]
    assert second["approval_queue_write"]["duplicate"]["approval_id"] == first["summary"]["approval_id"]


def test_secret_bearing_input_blocks_queue_write_and_redacts_payload(tmp_path: Path) -> None:
    raw_secret = "test-key-abcdefghijklmnopqrstuvwxyz123456"
    payload = build_phase11_chat_workspace_proposal_writer(
        tmp_path,
        message=f"Create an OpenClaw thread with api_key={raw_secret}",
        expected_proposal_digest="not-used",
        write_approval=True,
    )
    encoded = json.dumps(payload)

    assert payload["ok"] is False
    assert "secret_or_credential_indicator_present" in payload["blocked_reasons"]
    assert payload["secret_redaction"]["source_contains_secret"] is True
    assert payload["secret_redaction"]["source_redacted"] is True
    assert payload["summary"]["approval_request_created"] is False
    assert payload["approval_queue_write"]["queue_writer_called"] is False
    assert raw_secret not in encoded
    assert "[REDACTED_SECRET]" in encoded
