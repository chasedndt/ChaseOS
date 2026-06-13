"""Tests for the Phase 11 Studio Chat workspace target-state executor."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_workspace_proposal_consumption_executor import (
    execute_phase11_chat_workspace_proposal_consumption,
)
from runtime.studio.phase11_chat_workspace_proposal_writer import build_phase11_chat_workspace_proposal_writer
from runtime.studio.phase11_chat_workspace_target_state_executor import (
    NEXT_RECOMMENDED_PASS,
    execute_phase11_chat_workspace_target_state,
)
from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation


MESSAGE = "Create an OpenClaw runtime thread for venture board review"


def _consumed_proposal(
    root: Path,
    *,
    message: str = MESSAGE,
    proposal_kind: str | None = None,
    folder_id: str | None = None,
    title: str | None = None,
) -> dict:
    preview = build_phase11_chat_workspace_proposal_writer(
        root,
        message=message,
        proposal_kind=proposal_kind,
        folder_id=folder_id,
        title=title,
        operator_id="test",
    )
    digest = str(preview["digest_proof"]["proposal_digest"])
    queued = build_phase11_chat_workspace_proposal_writer(
        root,
        message=message,
        proposal_kind=proposal_kind,
        folder_id=folder_id,
        title=title,
        expected_proposal_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    consumed = execute_phase11_chat_workspace_proposal_consumption(
        root,
        approval_id=queued["summary"]["approval_id"],
        expected_proposal_digest=digest,
        operator_id="test",
        operator_approval_statement="operator approved workspace proposal consumption",
    )
    return {
        "proposal_digest": digest,
        "proposal_path": consumed["target_write"]["target_path"],
        "proposal_id": consumed["target_write"]["proposal_id"],
        "queued": queued,
        "consumed": consumed,
    }


def test_target_state_executor_writes_native_thread_state_and_foundation_reads_it(tmp_path: Path) -> None:
    consumed = _consumed_proposal(tmp_path)

    result = execute_phase11_chat_workspace_target_state(
        tmp_path,
        proposal_path=consumed["proposal_path"],
        expected_proposal_digest=consumed["proposal_digest"],
        operator_id="test",
        operator_target_state_statement="operator approved native target state write",
    )

    written_paths = result["state_writes"]["written_paths"]
    thread_path = next(path for path in written_paths if "/threads/" in path)
    folder_path = next(path for path in written_paths if "/folders/" in path)
    marker_path = tmp_path / result["exact_once_marker"]["marker_path"]
    proposal_payload = json.loads((tmp_path / consumed["proposal_path"]).read_text(encoding="utf-8"))
    thread_payload = json.loads((tmp_path / thread_path).read_text(encoding="utf-8"))
    folder_payload = json.loads((tmp_path / folder_path).read_text(encoding="utf-8"))
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    foundation = build_phase11_chat_workspaces_foundation(tmp_path)
    persisted_threads = [thread for thread in foundation["threads"] if thread.get("native_state_persisted")]

    assert result["ok"] is True
    assert result["surface"] == "phase11_chat_workspace_target_state_executor"
    assert result["summary"]["native_chat_state_written"] is True
    assert result["summary"]["workspace_state_written"] is False
    assert result["summary"]["folder_state_written"] is True
    assert result["summary"]["thread_state_written"] is True
    assert result["summary"]["proposal_record_mutated"] is True
    assert result["summary"]["chat_thread_created"] is True
    assert result["summary"]["discord_api_called"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["runtime_board_written"] is False
    assert result["summary"]["schedule_mutated"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["credential_value_read"] is False
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["digest_proof"]["proposal_digest_matched"] is True
    assert proposal_payload["status"] == "target_state_applied"
    assert proposal_payload["target_state_applied"] is True
    assert proposal_payload["chat_thread_created"] is True
    assert proposal_payload["discord_api_called"] is False
    assert thread_payload["record_type"] == "thread"
    assert thread_payload["runtime_id"] == "OpenClaw"
    assert thread_payload["native_state_persisted"] is True
    assert thread_payload["discord_api_called"] is False
    assert folder_payload["record_type"] == "folder"
    assert marker_payload["status"] == "executed"
    assert marker_payload["discord_api_called"] is False
    assert foundation["summary"]["native_state_thread_count"] == 1
    assert foundation["summary"]["native_state_folder_count"] == 1
    assert foundation["readiness"]["native_chat_state_read_model_ready"] is True
    assert any(thread["thread_id"] == thread_payload["thread_id"] for thread in persisted_threads)


def test_target_state_executor_requires_digest_and_operator_statement(tmp_path: Path) -> None:
    consumed = _consumed_proposal(tmp_path)

    result = execute_phase11_chat_workspace_target_state(
        tmp_path,
        proposal_path=consumed["proposal_path"],
        expected_proposal_digest="",
        operator_id="test",
    )

    assert result["ok"] is False
    assert "expected_proposal_digest_required" in result["blocked_reasons"]
    assert "operator_target_state_statement_required" in result["blocked_reasons"]
    assert result["state_writes"]["workspace_state_written"] is False
    assert result["state_writes"]["folder_state_written"] is False
    assert result["state_writes"]["thread_state_written"] is False
    assert not (tmp_path / "runtime/studio/chat/native-state").exists()


def test_target_state_executor_blocks_digest_mismatch_without_writes(tmp_path: Path) -> None:
    consumed = _consumed_proposal(tmp_path)

    result = execute_phase11_chat_workspace_target_state(
        tmp_path,
        proposal_path=consumed["proposal_path"],
        expected_proposal_digest="bad-digest",
        operator_id="test",
        operator_target_state_statement="operator approved native target state write",
    )

    assert result["ok"] is False
    assert "proposal_digest_mismatch" in result["blocked_reasons"]
    assert not (tmp_path / "runtime/studio/chat/native-state").exists()


def test_target_state_executor_duplicate_blocks_before_second_state_write(tmp_path: Path) -> None:
    consumed = _consumed_proposal(tmp_path)
    first = execute_phase11_chat_workspace_target_state(
        tmp_path,
        proposal_path=consumed["proposal_path"],
        expected_proposal_digest=consumed["proposal_digest"],
        operator_id="test",
        operator_target_state_statement="operator approved native target state write",
    )
    thread_path = next(path for path in first["state_writes"]["written_paths"] if "/threads/" in path)
    thread_bytes = (tmp_path / thread_path).read_bytes()

    duplicate = execute_phase11_chat_workspace_target_state(
        tmp_path,
        proposal_path=consumed["proposal_path"],
        expected_proposal_digest=consumed["proposal_digest"],
        operator_id="test",
        operator_target_state_statement="operator approved native target state write",
    )

    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert duplicate["summary"]["duplicate_blocked_before_state_write"] is True
    assert (tmp_path / thread_path).read_bytes() == thread_bytes


def test_target_state_executor_writes_folder_state_without_runtime_side_effects(tmp_path: Path) -> None:
    consumed = _consumed_proposal(
        tmp_path,
        message="Create a VentureOps client evidence folder",
        proposal_kind="create_folder",
        folder_id="client-evidence-review",
        title="Client Evidence Review",
    )

    result = execute_phase11_chat_workspace_target_state(
        tmp_path,
        proposal_path=consumed["proposal_path"],
        expected_proposal_digest=consumed["proposal_digest"],
        operator_id="test",
        operator_target_state_statement="operator approved native folder state write",
    )
    foundation = build_phase11_chat_workspaces_foundation(tmp_path)
    runtime_ops = next(workspace for workspace in foundation["workspaces"] if workspace["workspace_id"] == "runtime-ops")
    folder = next(item for item in runtime_ops["folders"] if item["folder_id"] == "client-evidence-review")

    assert result["ok"] is True
    assert result["summary"]["folder_state_written"] is True
    assert result["summary"]["thread_state_written"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["discord_api_called"] is False
    assert folder["native_state_persisted"] is True
    assert foundation["summary"]["native_state_folder_count"] == 1
    assert foundation["summary"]["native_state_thread_count"] == 0
