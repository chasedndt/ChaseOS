"""Tests for Studio Chat schedule adapter export readiness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.phase11_chat_approved_schedule_activation_executor import (
    execute_phase11_chat_approved_schedule_activation,
)
from runtime.studio.phase11_chat_approved_schedule_intent_writer import (
    execute_phase11_chat_approved_schedule_intent_writer,
)
from runtime.studio.phase11_chat_schedule_adapter_export_readiness import (
    build_phase11_chat_schedule_adapter_export_readiness,
)
from runtime.studio.phase11_chat_schedule_intent_activation_readiness import (
    build_phase11_chat_schedule_intent_activation_readiness,
)
from runtime.studio.phase11_chat_schedule_proposal_consumption_executor import (
    execute_phase11_chat_schedule_proposal_consumption,
)
from runtime.studio.phase11_chat_schedule_proposal_packet import (
    build_phase11_chat_schedule_proposal_packet,
)
from runtime.studio.service import StudioService, StudioServiceError


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


def _enable_schedule_from_chat(root: Path) -> str:
    preview = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for adapter export readiness.",
    )
    schedule_digest = preview["digest_proof"]["schedule_digest"]
    queued_schedule = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for adapter export readiness.",
        expected_schedule_digest=schedule_digest,
        write_approval=True,
    )
    consumed = execute_phase11_chat_schedule_proposal_consumption(
        root,
        approval_id=queued_schedule["summary"]["approval_id"],
        expected_schedule_digest=schedule_digest,
        operator_approval_statement="Approved for staged schedule proposal.",
    )
    written = execute_phase11_chat_approved_schedule_intent_writer(
        root,
        staged_proposal_path=consumed["target_write"]["staged_schedule_proposal_path"],
        expected_schedule_digest=schedule_digest,
        operator_schedule_write_statement="Approved to write disabled schedule intent.",
    )
    schedule_id = written["target_write"]["schedule_id"]
    activation_preview = build_phase11_chat_schedule_intent_activation_readiness(root, schedule_id=schedule_id)
    activation_digest = activation_preview["digest_proof"]["activation_digest"]
    queued_activation = build_phase11_chat_schedule_intent_activation_readiness(
        root,
        schedule_id=schedule_id,
        expected_activation_digest=activation_digest,
        write_approval=True,
    )
    activated = execute_phase11_chat_approved_schedule_activation(
        root,
        approval_id=queued_activation["approval_queue_write"]["approval_id"],
        expected_activation_digest=activation_digest,
        operator_activation_statement="Approved to enable this schedule and regenerate the schedule index only.",
    )
    assert activated["ok"] is True
    return schedule_id


def test_adapter_export_readiness_blocks_invalid_adapter_and_missing_digest(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_adapter_export_readiness(
        tmp_path,
        runtime_adapter_target="../openclaw",
        write_approval=True,
    )

    assert payload["ok"] is False
    assert "runtime_adapter_target_not_path_safe" in payload["blocked_reasons"]
    assert "runtime_adapter_target_not_registered" in payload["blocked_reasons"]
    assert "expected_export_digest_required_for_queue_write" in payload["blocked_reasons"]
    assert payload["target_write_proof"]["export_packet_written"] is False
    assert payload["target_write_proof"]["external_scheduler_changed"] is False


def test_adapter_export_readiness_queues_digest_bound_local_packet_only(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id = _enable_schedule_from_chat(tmp_path)

    preview = build_phase11_chat_schedule_adapter_export_readiness(tmp_path, schedule_id=schedule_id)
    export_digest = preview["digest_proof"]["export_digest"]
    queued = build_phase11_chat_schedule_adapter_export_readiness(
        tmp_path,
        schedule_id=schedule_id,
        expected_export_digest=export_digest,
        write_approval=True,
    )
    approval_path = tmp_path / queued["approval_queue_write"]["approval_path"]
    approval_record = json.loads(approval_path.read_text(encoding="utf-8"))
    packet = json.loads(approval_record["action_spec"]["content"])

    assert preview["ok"] is True
    assert preview["summary"]["runtime_adapter_target"] == "openclaw"
    assert preview["summary"]["enabled_schedule_count"] == 1
    assert schedule_id in preview["summary"]["enabled_schedule_ids"]
    assert queued["ok"] is True
    assert queued["approval_queue_write"]["approval_request_created"] is True
    assert queued["target_write_proof"]["export_packet_written"] is False
    assert queued["target_write_proof"]["external_scheduler_changed"] is False
    assert queued["target_write_proof"]["openclaw_cron_changed"] is False
    assert queued["target_write_proof"]["agent_bus_task_written"] is False
    assert queued["target_write_proof"]["runtime_dispatched"] is False
    assert queued["target_write_proof"]["discord_api_called"] is False
    assert queued["target_write_proof"]["provider_call_performed"] is False
    assert queued["target_write_proof"]["credential_value_read"] is False
    assert packet["export_digest"] == export_digest
    assert packet["runtime_adapter_target"] == "openclaw"
    assert packet["entry_count"] == 1
    assert packet["external_scheduler_mutation_allowed"] is False
    assert approval_record["action_spec"]["metadata"]["phase11_chat_schedule_adapter_export_readiness"] is True
    assert approval_record["action_spec"]["metadata"]["phase11_chat_schedule_adapter_export_execution_blocked"] is True


def test_adapter_export_readiness_blocks_mismatch_without_queue_write(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id = _enable_schedule_from_chat(tmp_path)

    payload = build_phase11_chat_schedule_adapter_export_readiness(
        tmp_path,
        schedule_id=schedule_id,
        expected_export_digest="bad-digest",
        write_approval=True,
    )

    assert payload["ok"] is False
    assert "expected_export_digest_mismatch" in payload["blocked_reasons"]
    assert payload["approval_queue_write"]["approval_request_created"] is False
    assert not (tmp_path / "runtime" / "studio" / "chat" / "schedule-adapter-exports").exists()


def test_adapter_export_approval_is_not_ambiently_executable(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id = _enable_schedule_from_chat(tmp_path)
    preview = build_phase11_chat_schedule_adapter_export_readiness(tmp_path, schedule_id=schedule_id)
    queued = build_phase11_chat_schedule_adapter_export_readiness(
        tmp_path,
        schedule_id=schedule_id,
        expected_export_digest=preview["digest_proof"]["export_digest"],
        write_approval=True,
    )
    approval_id = queued["approval_queue_write"]["approval_id"]
    service = StudioService(tmp_path)
    service.approve(approval_id)

    with pytest.raises(StudioServiceError, match="adapter export packet writer"):
        service.execute_approved(approval_id)

    assert not (tmp_path / queued["target_write_proof"]["target_path"]).exists()
