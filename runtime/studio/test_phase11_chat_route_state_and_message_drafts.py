"""Tests for Studio Chat local route-state and draft persistence."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_route_state_and_message_drafts import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_chat_route_state_and_message_drafts,
)
from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation


def test_route_state_writer_persists_selected_thread_without_runtime_side_effects(tmp_path: Path) -> None:
    result = build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="runtime-ops-openclaw-chat",
        operator_id="test",
        write_route_state=True,
    )
    route_path = tmp_path / result["state_writes"]["route_state_path"]
    route_payload = json.loads(route_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["surface"] == "phase11_chat_route_state_and_message_drafts"
    assert result["summary"]["route_state_persistence_built"] is True
    assert result["summary"]["route_state_written"] is True
    assert result["summary"]["draft_written"] is False
    assert result["summary"]["selected_workspace_id"] == "runtime-ops"
    assert result["summary"]["selected_thread_id"] == "runtime-ops-openclaw-chat"
    assert result["summary"]["route_preview"] == "#chat/runtime-ops/threads/runtime-ops-openclaw-chat"
    assert result["summary"]["chat_message_sent"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["runtime_board_written"] is False
    assert result["summary"]["schedule_mutated"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["readiness"]["message_send_blocked"] is True
    assert route_payload["record_type"] == "route_state"
    assert route_payload["runtime_id"] == "OpenClaw"
    assert route_payload["chat_message_sent"] is False


def test_message_draft_writer_persists_draft_and_message_intent_only(tmp_path: Path) -> None:
    result = build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="runtime-ops-hermes-chat",
        draft_text="Summarize the morning runtime status before I decide what to run.",
        message_intent="runtime_status_draft",
        title="Morning runtime status",
        operator_id="test",
        write_route_state=True,
        write_draft=True,
    )
    draft_path = tmp_path / result["state_writes"]["draft_state_path"]
    draft_payload = json.loads(draft_path.read_text(encoding="utf-8"))
    foundation = build_phase11_chat_workspaces_foundation(tmp_path)
    thread = next(item for item in foundation["threads"] if item["thread_id"] == "runtime-ops-hermes-chat")

    assert result["ok"] is True
    assert result["summary"]["route_state_written"] is True
    assert result["summary"]["draft_written"] is True
    assert result["summary"]["message_intent"] == "runtime_status_draft"
    assert result["summary"]["draft_id"] == "runtime-ops-hermes-chat__current"
    assert result["summary"]["chat_message_sent"] is False
    assert result["summary"]["chat_transcript_written"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["runtime_dispatched"] is False
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert draft_payload["record_type"] == "message_draft"
    assert draft_payload["thread_id"] == "runtime-ops-hermes-chat"
    assert draft_payload["runtime_id"] == "Hermes"
    assert draft_payload["message_intent"] == "runtime_status_draft"
    assert draft_payload["draft_text_sha256"]
    assert draft_payload["future_send_requires_approval"] is True
    assert draft_payload["chat_message_sent"] is False
    assert thread["selected_in_route_state"] is True
    assert thread["draft_count"] == 1
    assert thread["message_draft_state_persisted"] is True
    assert foundation["summary"]["route_state_persisted"] is True
    assert foundation["summary"]["draft_count"] == 1
    assert foundation["native_navigation_model"]["route_state_persistence_built"] is True
    assert foundation["native_navigation_model"]["message_draft_state_persistence_built"] is True


def test_message_draft_blocks_secret_like_content_without_write(tmp_path: Path) -> None:
    result = build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="runtime-ops-openclaw-chat",
        draft_text="OPENAI_API_KEY=test-key-thisShouldNeverPersist123456789",
        operator_id="test",
        write_draft=True,
    )

    assert result["ok"] is False
    assert "secret_or_credential_indicator_present" in result["blocked_reasons"]
    assert result["summary"]["secret_indicator_present"] is True
    assert result["state_writes"]["draft_written"] is False
    assert "[REDACTED_SECRET]" in result["secret_report"]["redacted_preview"]
    assert not (tmp_path / "runtime/studio/chat/native-state/drafts").exists()


def test_route_state_rejects_unknown_thread_without_write(tmp_path: Path) -> None:
    result = build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="missing-thread",
        operator_id="test",
        write_route_state=True,
    )

    assert result["ok"] is False
    assert "selected_thread_not_found" in result["blocked_reasons"]
    assert result["state_writes"]["route_state_written"] is False
    assert not (tmp_path / "runtime/studio/chat/native-state/route-state/current.json").exists()


def test_preview_reads_existing_route_and_drafts_without_writing(tmp_path: Path) -> None:
    first = build_phase11_chat_route_state_and_message_drafts(
        tmp_path,
        selected_thread_id="runtime-ops-codex-patches",
        draft_text="Patch the next focused test failure after review.",
        message_intent="code_patch_draft",
        operator_id="test",
        write_route_state=True,
        write_draft=True,
    )

    preview = build_phase11_chat_route_state_and_message_drafts(tmp_path)

    assert first["ok"] is True
    assert preview["ok"] is True
    assert preview["summary"]["route_state_written"] is False
    assert preview["summary"]["draft_written"] is False
    assert preview["summary"]["current_route_state_persisted"] is True
    assert preview["summary"]["draft_count"] == 1
    assert preview["current_route_state"]["thread_id"] == "runtime-ops-codex-patches"
    assert preview["drafts"][0]["message_intent"] == "code_patch_draft"
