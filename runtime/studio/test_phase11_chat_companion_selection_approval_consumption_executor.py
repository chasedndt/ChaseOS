"""Tests for Phase 11 companion-selection approval consumption executor."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_companion_selection_approval_consumption_readiness import (
    build_phase11_chat_companion_selection_approval_consumption_readiness,
)
from runtime.studio.phase11_chat_companion_selection_approval_consumption_executor import (
    NEXT_RECOMMENDED_PASS,
    execute_phase11_chat_companion_selection_approval_consumption,
)
from runtime.studio.phase11_chat_companion_selection_queue_write_execution import (
    execute_phase11_chat_companion_selection_queue_write,
)
from runtime.studio.phase11_chat_companion_selection_queue_write_readiness import (
    build_phase11_chat_companion_selection_queue_write_readiness,
)
from runtime.studio.service import StudioService, StudioServiceError


MESSAGE = "Switch companion to Hermes"
TARGET = Path("runtime/studio/chat/companion-selection.json")


def _queue_companion_selection(root: Path, *, message: str = MESSAGE) -> str:
    readiness = build_phase11_chat_companion_selection_queue_write_readiness(
        root,
        requested_runtime="hermes",
        current_runtime="openclaw",
        message=message,
    )
    written = execute_phase11_chat_companion_selection_queue_write(
        root,
        requested_runtime="hermes",
        current_runtime="openclaw",
        message=message,
        expected_queue_write_digest=readiness["digest_proof"]["queue_write_digest"],
        operator_id="test",
    )
    return str(written["approval_record"]["approval_id"])


def _consumption_digest(root: Path, approval_id: str, *, message: str = MESSAGE) -> str:
    readiness = build_phase11_chat_companion_selection_approval_consumption_readiness(
        root,
        approval_id=approval_id,
        message=message,
    )
    return str(readiness["digest_proof"]["consumption_digest"])


def test_approved_companion_selection_consumption_writes_target_marker_and_audit(tmp_path: Path) -> None:
    approval_id = _queue_companion_selection(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")
    expected_digest = _consumption_digest(tmp_path, approval_id)

    result = execute_phase11_chat_companion_selection_approval_consumption(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
        expected_consumption_digest=expected_digest,
        operator_id="test",
    )

    target_path = tmp_path / TARGET
    marker_path = tmp_path / result["exact_once_marker"]["marker_path"]
    approval_path = tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json"
    target_payload = json.loads(target_path.read_text(encoding="utf-8"))
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["surface"] == "phase11_chat_companion_selection_approval_consumption_executor"
    assert result["pass"] == "phase11-chat-companion-selection-approval-consumption-executor"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["approval_status_mutated"] is True
    assert result["summary"]["exact_once_marker_written"] is True
    assert result["summary"]["companion_selection_written"] is True
    assert result["summary"]["target_write_performed"] is True
    assert result["summary"]["runtime_control_performed"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["digest_proof"]["consumption_digest"] == expected_digest
    assert target_payload["selected_runtime_id"] == "hermes"
    assert target_payload["previous_runtime_id"] == "openclaw"
    assert target_payload["selection_digest"]
    assert target_payload["queue_write_digest"]
    assert marker_payload["status"] == "executed"
    assert marker_payload["approval_id"] == approval_id
    assert marker_payload["target_path"] == TARGET.as_posix()
    assert approval_payload["status"] == "executed"
    assert approval_payload["execution_status"] == "completed"
    assert approval_payload["result_action_id"] == result["execution_record"]["execution_id"]
    assert Path(tmp_path / result["audit_record"]["audit_record_path"]).is_file()


def test_pending_without_current_operator_statement_blocks_before_writes(tmp_path: Path) -> None:
    approval_id = _queue_companion_selection(tmp_path)
    expected_digest = _consumption_digest(tmp_path, approval_id)

    result = execute_phase11_chat_companion_selection_approval_consumption(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
        expected_consumption_digest=expected_digest,
        operator_id="test",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is False
    assert "operator_decision_not_approved" in result["blocked_reasons"]
    assert result["summary"]["companion_selection_written"] is False
    assert approval_payload["status"] == "pending"
    assert not (tmp_path / TARGET).exists()


def test_pending_with_current_operator_statement_records_approval_then_consumes(tmp_path: Path) -> None:
    approval_id = _queue_companion_selection(tmp_path)
    expected_digest = _consumption_digest(tmp_path, approval_id)

    result = execute_phase11_chat_companion_selection_approval_consumption(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
        expected_consumption_digest=expected_digest,
        operator_id="test",
        operator_approval_statement="operator approved companion selection consumption",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is True
    assert result["summary"]["operator_approval_recorded_from_statement"] is True
    assert result["summary"]["approval_consumed"] is True
    assert approval_payload["reviewed_by"] == "test"
    assert approval_payload["reason"] == "operator approved companion selection consumption"
    assert (tmp_path / TARGET).is_file()


def test_digest_mismatch_duplicate_and_target_collision_block_before_writes(tmp_path: Path) -> None:
    approval_id = _queue_companion_selection(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")
    expected_digest = _consumption_digest(tmp_path, approval_id)

    mismatch = execute_phase11_chat_companion_selection_approval_consumption(
        tmp_path,
        approval_id=approval_id,
        message="Switch companion to Archon",
        expected_consumption_digest=expected_digest,
        operator_id="test",
    )
    assert mismatch["ok"] is False
    assert "queue_write_digest_mismatch" in mismatch["blocked_reasons"]
    assert not (tmp_path / TARGET).exists()

    first = execute_phase11_chat_companion_selection_approval_consumption(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
        expected_consumption_digest=expected_digest,
        operator_id="test",
    )
    target_bytes = (tmp_path / TARGET).read_bytes()
    duplicate = execute_phase11_chat_companion_selection_approval_consumption(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
        expected_consumption_digest=expected_digest,
        operator_id="test",
    )

    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert duplicate["summary"]["duplicate_blocked_before_target_write"] is True
    assert (tmp_path / TARGET).read_bytes() == target_bytes

    second_root = tmp_path / "collision"
    second_root.mkdir()
    second_approval_id = _queue_companion_selection(second_root)
    StudioService(second_root).approve(second_approval_id, reviewed_by="test")
    (second_root / TARGET).parent.mkdir(parents=True)
    (second_root / TARGET).write_text('{"selected_runtime_id":"openclaw"}\n', encoding="utf-8")
    collision_digest = _consumption_digest(second_root, second_approval_id)
    collision = execute_phase11_chat_companion_selection_approval_consumption(
        second_root,
        approval_id=second_approval_id,
        message=MESSAGE,
        expected_consumption_digest=collision_digest,
        operator_id="test",
    )
    assert collision["ok"] is False
    assert "future_companion_selection_target_collision" in collision["blocked_reasons"]


def test_generic_studio_service_execution_remains_blocked_for_companion_selection(tmp_path: Path) -> None:
    approval_id = _queue_companion_selection(tmp_path)
    service = StudioService(tmp_path)
    service.approve(approval_id, reviewed_by="test")

    try:
        service.execute_approved(approval_id)
    except StudioServiceError as exc:
        error = str(exc)
    else:  # pragma: no cover - the assertion below is clearer than pytest.raises for status checks.
        error = ""

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert "companion selection" in error
    assert approval_payload["status"] == "approved"
    assert not (tmp_path / TARGET).exists()
