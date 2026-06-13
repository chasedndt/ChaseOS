"""Tests for Studio Chat schedule proposal approval consumption."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_schedule_proposal_consumption_executor import (
    execute_phase11_chat_schedule_proposal_consumption,
)
from runtime.studio.phase11_chat_schedule_proposal_packet import (
    build_phase11_chat_schedule_proposal_packet,
)
from runtime.studio.service import StudioService


def _queue_schedule_proposal(root: Path) -> tuple[str, str, str]:
    kwargs = {
        "workflow_id": "operator_today",
        "cron_expression": "0 8 * * 1-5",
        "schedule_summary": "Schedule operator_today for a governed Studio staging pass.",
    }
    preview = build_phase11_chat_schedule_proposal_packet(root, **kwargs)
    digest = preview["digest_proof"]["schedule_digest"]
    queued = build_phase11_chat_schedule_proposal_packet(
        root,
        **kwargs,
        expected_schedule_digest=digest,
        write_approval=True,
    )
    return queued["summary"]["approval_id"], digest, queued["summary"]["target_path_preview"]


def test_schedule_proposal_consumption_requires_exact_inputs(tmp_path: Path) -> None:
    payload = execute_phase11_chat_schedule_proposal_consumption(tmp_path)

    assert payload["ok"] is False
    assert "approval_id_required_for_schedule_proposal_consumption" in payload["blocked_reasons"]
    assert "expected_schedule_digest_required" in payload["blocked_reasons"]
    assert payload["target_write"]["staged_schedule_proposal_written"] is False
    assert payload["target_write"]["schedule_intent_written"] is False


def test_consumes_pending_schedule_proposal_into_staged_record_without_schedule_effects(
    tmp_path: Path,
) -> None:
    approval_id, digest, target_path = _queue_schedule_proposal(tmp_path)

    payload = execute_phase11_chat_schedule_proposal_consumption(
        tmp_path,
        approval_id=approval_id,
        expected_schedule_digest=digest,
        operator_id="studio-operator",
        operator_approval_statement="Approved for staged schedule proposal consumption only.",
    )
    target = payload["target_write"]
    marker = payload["exact_once_marker"]
    staged_path = tmp_path / target["staged_schedule_proposal_path"]
    record = json.loads(staged_path.read_text(encoding="utf-8"))
    service = StudioService(tmp_path)
    req = service.get_approval(approval_id)

    assert payload["ok"] is True
    assert payload["summary"]["approval_consumed"] is True
    assert payload["summary"]["operator_approval_recorded_from_statement"] is True
    assert payload["digest_proof"]["schedule_digest_matched"] is True
    assert marker["marker_written"] is True
    assert (tmp_path / marker["marker_path"]).exists()
    assert staged_path.exists()
    assert (tmp_path / target_path).exists() is False
    assert target["target_file_written"] is False
    assert target["staged_schedule_proposal_written"] is True
    assert target["schedule_intent_written"] is False
    assert target["schedule_index_regenerated"] is False
    assert target["external_scheduler_changed"] is False
    assert target["agent_bus_task_written"] is False
    assert target["runtime_dispatched"] is False
    assert target["discord_api_called"] is False
    assert record["schema_version"] == "phase11_chat_approved_schedule_proposal_record.v1"
    assert record["schedule_intent_writer_required"] is True
    assert record["target_schedule_path"] == target_path
    assert record["future_schedule_intent"]["workflow_id"] == "operator_today"
    assert record["schedule_intent_written"] is False
    assert req is not None
    assert req.status == "executed"
    assert req.action_spec.metadata["phase11_chat_schedule_proposal_consumption_executor"] is True


def test_duplicate_schedule_proposal_consumption_blocks_before_second_write(tmp_path: Path) -> None:
    approval_id, digest, _target_path = _queue_schedule_proposal(tmp_path)
    first = execute_phase11_chat_schedule_proposal_consumption(
        tmp_path,
        approval_id=approval_id,
        expected_schedule_digest=digest,
        operator_approval_statement="Approved once.",
    )
    second = execute_phase11_chat_schedule_proposal_consumption(
        tmp_path,
        approval_id=approval_id,
        expected_schedule_digest=digest,
        operator_approval_statement="Approved twice.",
    )

    assert first["ok"] is True
    assert second["ok"] is False
    assert "exact_once_marker_already_present" in second["blocked_reasons"]
    assert second["target_write"]["staged_schedule_proposal_written"] is False


def test_schedule_proposal_consumption_blocks_mismatched_digest(tmp_path: Path) -> None:
    approval_id, _digest, target_path = _queue_schedule_proposal(tmp_path)

    payload = execute_phase11_chat_schedule_proposal_consumption(
        tmp_path,
        approval_id=approval_id,
        expected_schedule_digest="bad-digest",
        operator_approval_statement="Approved but wrong digest.",
    )

    assert payload["ok"] is False
    assert "schedule_digest_mismatch" in payload["blocked_reasons"]
    assert payload["target_write"]["staged_schedule_proposal_written"] is False
    assert (tmp_path / target_path).exists() is False
