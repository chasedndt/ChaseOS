"""Tests for the Phase 11 Studio Chat workspace proposal consumption executor."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_workspace_proposal_consumption_executor import (
    NEXT_RECOMMENDED_PASS,
    execute_phase11_chat_workspace_proposal_consumption,
)
from runtime.studio.phase11_chat_workspace_proposal_writer import (
    build_phase11_chat_workspace_proposal_writer,
)
from runtime.studio.service import ActionSpec, StudioService, StudioServiceError


MESSAGE = "Create an OpenClaw runtime thread for venture board review"


def _queue_workspace_proposal(root: Path, *, message: str = MESSAGE) -> dict:
    preview = build_phase11_chat_workspace_proposal_writer(root, message=message, operator_id="test")
    digest = str(preview["digest_proof"]["proposal_digest"])
    queued = build_phase11_chat_workspace_proposal_writer(
        root,
        message=message,
        expected_proposal_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    return {
        "approval_id": queued["summary"]["approval_id"],
        "proposal_digest": digest,
        "target_path": queued["summary"]["target_path_preview"],
        "queued": queued,
    }


def test_consumes_pending_workspace_proposal_with_statement_and_writes_target_marker_and_audit(
    tmp_path: Path,
) -> None:
    queued = _queue_workspace_proposal(tmp_path)

    result = execute_phase11_chat_workspace_proposal_consumption(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_proposal_digest=queued["proposal_digest"],
        operator_id="test",
        operator_approval_statement="operator approved workspace proposal consumption",
    )

    target_path = tmp_path / queued["target_path"]
    marker_path = tmp_path / result["exact_once_marker"]["marker_path"]
    approval_path = tmp_path / StudioService.APPROVAL_DIR / f"{queued['approval_id']}.json"
    target_payload = json.loads(target_path.read_text(encoding="utf-8"))
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["surface"] == "phase11_chat_workspace_proposal_consumption_executor"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["approval_status_mutated"] is True
    assert result["summary"]["operator_approval_recorded_from_statement"] is True
    assert result["summary"]["exact_once_marker_written"] is True
    assert result["summary"]["target_workspace_proposal_written"] is True
    assert result["summary"]["chat_thread_created"] is False
    assert result["summary"]["discord_api_called"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["runtime_board_written"] is False
    assert result["summary"]["schedule_mutated"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["credential_value_read"] is False
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["digest_proof"]["proposal_digest"] == queued["proposal_digest"]
    assert result["digest_proof"]["proposal_digest_matched"] is True
    assert target_payload["status"] == "approved_proposal_recorded"
    assert target_payload["approval_consumed"] is True
    assert target_payload["target_state_executor_required"] is True
    assert target_payload["chat_thread_created"] is False
    assert target_payload["discord_api_called"] is False
    assert target_payload["agent_bus_task_written"] is False
    assert target_payload["runtime_board_written"] is False
    assert target_payload["schedule_mutated"] is False
    assert target_payload["provider_call_performed"] is False
    assert marker_payload["status"] == "executed"
    assert marker_payload["target_workspace_proposal_written"] is True
    assert marker_payload["discord_api_called"] is False
    assert approval_payload["status"] == "executed"
    assert approval_payload["reviewed_by"] == "test"
    assert approval_payload["execution_status"] == "completed"
    assert approval_payload["action_spec"]["metadata"]["target_workspace_proposal_write_performed"] is True
    assert Path(tmp_path / result["audit_record"]["audit_record_path"]).is_file()


def test_pending_without_operator_statement_blocks_before_writes(tmp_path: Path) -> None:
    queued = _queue_workspace_proposal(tmp_path)

    result = execute_phase11_chat_workspace_proposal_consumption(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_proposal_digest=queued["proposal_digest"],
        operator_id="test",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{queued['approval_id']}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is False
    assert "operator_decision_not_approved" in result["blocked_reasons"]
    assert result["summary"]["target_workspace_proposal_written"] is False
    assert approval_payload["status"] == "pending"
    assert not (tmp_path / queued["target_path"]).exists()


def test_wrong_proposal_digest_blocks_without_marker_or_target_write(tmp_path: Path) -> None:
    queued = _queue_workspace_proposal(tmp_path)
    StudioService(tmp_path).approve(queued["approval_id"], reviewed_by="test")

    result = execute_phase11_chat_workspace_proposal_consumption(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_proposal_digest="bad-digest",
        operator_id="test",
    )

    assert result["ok"] is False
    assert "proposal_digest_mismatch" in result["blocked_reasons"]
    assert result["exact_once_marker"]["marker_written"] is False
    assert not (tmp_path / queued["target_path"]).exists()
    assert not (tmp_path / result["exact_once_marker"]["marker_path"]).exists()


def test_duplicate_consumption_blocks_before_second_target_write(tmp_path: Path) -> None:
    queued = _queue_workspace_proposal(tmp_path)
    StudioService(tmp_path).approve(queued["approval_id"], reviewed_by="test")

    first = execute_phase11_chat_workspace_proposal_consumption(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_proposal_digest=queued["proposal_digest"],
        operator_id="test",
    )
    target_bytes = (tmp_path / queued["target_path"]).read_bytes()
    duplicate = execute_phase11_chat_workspace_proposal_consumption(
        tmp_path,
        approval_id=queued["approval_id"],
        expected_proposal_digest=queued["proposal_digest"],
        operator_id="test",
    )

    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert duplicate["summary"]["duplicate_blocked_before_target_write"] is True
    assert (tmp_path / queued["target_path"]).read_bytes() == target_bytes


def test_rejects_generic_approval_and_generic_studio_execution_remains_blocked(tmp_path: Path) -> None:
    queued = _queue_workspace_proposal(tmp_path)
    service = StudioService(tmp_path)
    service.approve(queued["approval_id"], reviewed_by="test")

    try:
        service.execute_approved(queued["approval_id"])
    except StudioServiceError as exc:
        error = str(exc)
    else:  # pragma: no cover
        error = ""

    wrong = service.queue_for_approval(
        ActionSpec(
            action_type="create_file",
            target_path="runtime/studio/chat/workspace-proposals/not-from-writer.json",
            content='{"proposal_kind":"create_thread"}\n',
            metadata={"source_surface": "other"},
        )
    )
    service.approve(wrong.approval_id, reviewed_by="test")
    result = execute_phase11_chat_workspace_proposal_consumption(
        tmp_path,
        approval_id=wrong.approval_id,
        expected_proposal_digest="not-present",
        operator_id="test",
    )

    assert "workspace proposal" in error
    assert not (tmp_path / queued["target_path"]).exists()
    assert result["ok"] is False
    assert "approval_not_workspace_proposal_writer_artifact" in result["blocked_reasons"]
    assert not (tmp_path / "runtime/studio/chat/workspace-proposals/not-from-writer.json").exists()
