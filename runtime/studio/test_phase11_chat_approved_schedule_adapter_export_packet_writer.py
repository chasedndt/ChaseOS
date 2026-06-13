"""Tests for approved Studio Chat schedule adapter export packet writer."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_approved_schedule_activation_executor import (
    execute_phase11_chat_approved_schedule_activation,
)
from runtime.studio.phase11_chat_approved_schedule_adapter_export_packet_writer import (
    execute_phase11_chat_approved_schedule_adapter_export_packet_writer,
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
from runtime.studio.service import StudioService


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
        schedule_summary="Schedule operator_today for adapter export packet writer.",
    )
    schedule_digest = preview["digest_proof"]["schedule_digest"]
    queued_schedule = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for adapter export packet writer.",
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


def _queue_export(root: Path, schedule_id: str) -> tuple[str, str, str]:
    preview = build_phase11_chat_schedule_adapter_export_readiness(root, schedule_id=schedule_id)
    export_digest = preview["digest_proof"]["export_digest"]
    queued = build_phase11_chat_schedule_adapter_export_readiness(
        root,
        schedule_id=schedule_id,
        expected_export_digest=export_digest,
        write_approval=True,
    )
    assert queued["ok"] is True
    return (
        queued["approval_queue_write"]["approval_id"],
        export_digest,
        queued["target_write_proof"]["target_path"],
    )


def test_adapter_export_packet_writer_requires_approval_digest_and_statement(tmp_path: Path) -> None:
    payload = execute_phase11_chat_approved_schedule_adapter_export_packet_writer(tmp_path)

    assert payload["ok"] is False
    assert "approval_id_required_for_adapter_export_packet_write" in payload["blocked_reasons"]
    assert "expected_export_digest_required" in payload["blocked_reasons"]
    assert "operator_export_write_statement_required" in payload["blocked_reasons"]
    assert payload["target_write"]["export_packet_written"] is False
    assert payload["target_write"]["external_scheduler_changed"] is False


def test_adapter_export_packet_writer_writes_local_packet_only(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id = _enable_schedule_from_chat(tmp_path)
    approval_id, export_digest, target_path = _queue_export(tmp_path, schedule_id)

    payload = execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
        tmp_path,
        approval_id=approval_id,
        expected_export_digest=export_digest,
        operator_export_write_statement="Approved to write the local adapter export packet only.",
    )
    target = tmp_path / target_path
    packet = json.loads(target.read_text(encoding="utf-8"))
    approval = StudioService(tmp_path).get_approval(approval_id)

    assert payload["ok"] is True
    assert target.exists()
    assert packet["packet_type"] == "phase11_chat_schedule_adapter_export_packet"
    assert packet["export_digest"] == export_digest
    assert packet["runtime_adapter_target"] == "openclaw"
    assert packet["entry_count"] == 1
    assert payload["target_write"]["target_file_written"] is True
    assert payload["target_write"]["export_packet_written"] is True
    assert payload["target_write"]["external_scheduler_changed"] is False
    assert payload["target_write"]["openclaw_cron_changed"] is False
    assert payload["target_write"]["hermes_cron_changed"] is False
    assert payload["target_write"]["agent_bus_task_written"] is False
    assert payload["target_write"]["runtime_dispatched"] is False
    assert payload["target_write"]["workflow_dispatched"] is False
    assert payload["target_write"]["discord_api_called"] is False
    assert payload["target_write"]["provider_call_performed"] is False
    assert payload["target_write"]["credential_value_read"] is False
    assert payload["exact_once_marker"]["marker_written"] is True
    assert approval is not None
    assert approval.status == "executed"
    assert approval.action_spec.metadata["phase11_chat_approved_schedule_adapter_export_packet_writer"] is True


def test_adapter_export_packet_writer_blocks_digest_mismatch(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id = _enable_schedule_from_chat(tmp_path)
    approval_id, _export_digest, target_path = _queue_export(tmp_path, schedule_id)

    payload = execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
        tmp_path,
        approval_id=approval_id,
        expected_export_digest="bad-digest",
        operator_export_write_statement="Approved to write the local adapter export packet only.",
    )

    assert payload["ok"] is False
    assert "export_digest_mismatch" in payload["blocked_reasons"]
    assert "packet_export_digest_mismatch" in payload["blocked_reasons"]
    assert not (tmp_path / target_path).exists()


def test_adapter_export_packet_writer_blocks_duplicate_execution(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id = _enable_schedule_from_chat(tmp_path)
    approval_id, export_digest, target_path = _queue_export(tmp_path, schedule_id)
    first = execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
        tmp_path,
        approval_id=approval_id,
        expected_export_digest=export_digest,
        operator_export_write_statement="Approved to write the local adapter export packet only.",
    )
    second = execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
        tmp_path,
        approval_id=approval_id,
        expected_export_digest=export_digest,
        operator_export_write_statement="Approved to write the local adapter export packet only.",
    )

    assert first["ok"] is True
    assert second["ok"] is False
    assert "exact_once_marker_already_present" in second["blocked_reasons"]
    assert "target_packet_already_exists_before_execution" in second["blocked_reasons"]
    assert (tmp_path / target_path).exists()
