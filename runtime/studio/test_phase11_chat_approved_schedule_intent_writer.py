"""Tests for Studio Chat approved schedule-intent writes."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.schedules.loader import load_schedule
from runtime.studio.phase11_chat_approved_schedule_intent_writer import (
    execute_phase11_chat_approved_schedule_intent_writer,
)
from runtime.studio.phase11_chat_schedule_proposal_consumption_executor import (
    execute_phase11_chat_schedule_proposal_consumption,
)
from runtime.studio.phase11_chat_schedule_proposal_packet import (
    build_phase11_chat_schedule_proposal_packet,
)


def _seed_operator_today_workflow(root: Path) -> None:
    registry = root / "runtime" / "workflows" / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / "operator_today.yaml").write_text(
        "\n".join(
            [
                "id: operator_today",
                "name: Operator Today",
                "version: '1.0'",
                "description: Test operator briefing workflow.",
                "task_type: operator-briefing",
                "role_card: operator-briefing",
                "trigger_type: manual",
                "owner: operator",
                "status: active",
                "permission_ceiling: standard",
                "writeback_targets:",
                "  - 07_LOGS/Operator-Briefs/",
                "failure_behavior: escalate",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _stage_approved_schedule(root: Path) -> tuple[str, str, str]:
    preview = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a governed Studio schedule-intent write.",
    )
    digest = preview["digest_proof"]["schedule_digest"]
    queued = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a governed Studio schedule-intent write.",
        expected_schedule_digest=digest,
        write_approval=True,
    )
    consumed = execute_phase11_chat_schedule_proposal_consumption(
        root,
        approval_id=queued["summary"]["approval_id"],
        expected_schedule_digest=digest,
        operator_id="studio-operator",
        operator_approval_statement="Approved for staged proposal consumption.",
    )
    assert consumed["ok"] is True
    return (
        consumed["target_write"]["staged_schedule_proposal_path"],
        digest,
        consumed["target_write"]["schedule_id"],
    )


def test_approved_schedule_intent_writer_requires_exact_inputs(tmp_path: Path) -> None:
    payload = execute_phase11_chat_approved_schedule_intent_writer(tmp_path)

    assert payload["ok"] is False
    assert "expected_schedule_digest_required" in payload["blocked_reasons"]
    assert "operator_schedule_write_statement_required" in payload["blocked_reasons"]
    assert "staged_proposal_path_or_schedule_id_required" in payload["blocked_reasons"]
    assert payload["target_write"]["schedule_intent_written"] is False
    assert payload["target_write"]["schedule_index_regenerated"] is False


def test_writes_approved_schedule_intent_and_regenerates_index_only(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    staged_path, digest, schedule_id = _stage_approved_schedule(tmp_path)

    payload = execute_phase11_chat_approved_schedule_intent_writer(
        tmp_path,
        staged_proposal_path=staged_path,
        expected_schedule_digest=digest,
        operator_id="studio-operator",
        operator_schedule_write_statement="Approved to write schedule YAML and regenerate the schedule index only.",
    )
    target = payload["target_write"]
    record = json.loads((tmp_path / staged_path).read_text(encoding="utf-8"))
    intent = load_schedule(schedule_id, tmp_path, check_registry=True)

    assert payload["ok"] is True
    assert target["target_file_written"] is True
    assert target["schedule_intent_written"] is True
    assert target["schedule_index_regenerated"] is True
    assert target["schedule_enabled"] is False
    assert target["external_scheduler_changed"] is False
    assert target["openclaw_cron_changed"] is False
    assert target["hermes_cron_changed"] is False
    assert target["agent_bus_task_written"] is False
    assert target["runtime_dispatched"] is False
    assert target["workflow_dispatched"] is False
    assert target["discord_api_called"] is False
    assert target["provider_call_performed"] is False
    assert target["credential_value_read"] is False
    assert (tmp_path / target["target_path"]).exists()
    assert (tmp_path / "runtime" / "schedules" / "index.yaml").exists()
    assert intent is not None
    assert intent.schedule_id == schedule_id
    assert intent.enabled is False
    assert record["status"] == "schedule_intent_written"
    assert record["schedule_intent_writer_required"] is False
    assert record["schedule_intent_written"] is True
    assert record["schedule_index_regenerated"] is True


def test_approved_schedule_intent_writer_blocks_duplicate_before_overwrite(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    staged_path, digest, _schedule_id = _stage_approved_schedule(tmp_path)
    first = execute_phase11_chat_approved_schedule_intent_writer(
        tmp_path,
        staged_proposal_path=staged_path,
        expected_schedule_digest=digest,
        operator_schedule_write_statement="Approved once.",
    )
    second = execute_phase11_chat_approved_schedule_intent_writer(
        tmp_path,
        staged_proposal_path=staged_path,
        expected_schedule_digest=digest,
        operator_schedule_write_statement="Approved twice.",
    )

    assert first["ok"] is True
    assert second["ok"] is False
    assert "exact_once_marker_already_present" in second["blocked_reasons"]
    assert second["target_write"]["target_file_written"] is False


def test_approved_schedule_intent_writer_blocks_digest_mismatch(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    staged_path, _digest, schedule_id = _stage_approved_schedule(tmp_path)

    payload = execute_phase11_chat_approved_schedule_intent_writer(
        tmp_path,
        staged_proposal_path=staged_path,
        expected_schedule_digest="bad-digest",
        operator_schedule_write_statement="Approved with an incorrect digest.",
    )

    assert payload["ok"] is False
    assert "schedule_digest_mismatch" in payload["blocked_reasons"]
    assert (tmp_path / "runtime" / "schedules" / f"{schedule_id}.yaml").exists() is False
