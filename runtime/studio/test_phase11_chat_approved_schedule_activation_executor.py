"""Tests for Studio Chat approved schedule activation execution."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.schedules.loader import export_schedules_for_adapter, load_schedule
from runtime.studio.phase11_chat_approved_schedule_activation_executor import (
    execute_phase11_chat_approved_schedule_activation,
)
from runtime.studio.phase11_chat_approved_schedule_intent_writer import (
    execute_phase11_chat_approved_schedule_intent_writer,
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


def _queue_activation(root: Path) -> tuple[str, str, str]:
    preview = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for approved activation.",
    )
    schedule_digest = preview["digest_proof"]["schedule_digest"]
    queued_schedule = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for approved activation.",
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
    assert queued_activation["ok"] is True
    return queued_activation["approval_queue_write"]["approval_id"], activation_digest, schedule_id


def test_activation_executor_requires_exact_inputs(tmp_path: Path) -> None:
    payload = execute_phase11_chat_approved_schedule_activation(tmp_path)

    assert payload["ok"] is False
    assert "approval_id_required_for_schedule_activation" in payload["blocked_reasons"]
    assert "expected_activation_digest_required" in payload["blocked_reasons"]
    assert "operator_activation_statement_required" in payload["blocked_reasons"]
    assert payload["target_write"]["schedule_enabled"] is False
    assert payload["target_write"]["schedule_index_regenerated"] is False


def test_activation_executor_enables_schedule_and_index_only(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    approval_id, activation_digest, schedule_id = _queue_activation(tmp_path)

    payload = execute_phase11_chat_approved_schedule_activation(
        tmp_path,
        approval_id=approval_id,
        expected_activation_digest=activation_digest,
        operator_id="studio-operator",
        operator_activation_statement="Approved to enable this schedule and regenerate the schedule index only.",
    )
    target = payload["target_write"]
    approval_record = json.loads((tmp_path / "runtime" / "studio" / "approvals" / f"{approval_id}.json").read_text(encoding="utf-8"))
    intent = load_schedule(schedule_id, tmp_path, check_registry=True)
    adapter_export = export_schedules_for_adapter("openclaw", tmp_path, enabled_only=True)

    assert payload["ok"] is True
    assert target["target_file_written"] is True
    assert target["schedule_enabled"] is True
    assert target["schedule_index_regenerated"] is True
    assert target["external_scheduler_changed"] is False
    assert target["openclaw_cron_changed"] is False
    assert target["hermes_cron_changed"] is False
    assert target["agent_bus_task_written"] is False
    assert target["runtime_dispatched"] is False
    assert target["workflow_dispatched"] is False
    assert target["discord_api_called"] is False
    assert target["provider_call_performed"] is False
    assert target["credential_value_read"] is False
    assert (tmp_path / "runtime" / "schedules" / "index.yaml").exists()
    assert intent is not None
    assert intent.enabled is True
    assert schedule_id in [item["schedule_id"] for item in adapter_export]
    assert payload["adapter_export_read_model"]["external_scheduler_changed"] is False
    assert approval_record["status"] == "executed"
    assert approval_record["action_spec"]["metadata"]["phase11_chat_approved_schedule_activation_executor"] is True
    assert approval_record["action_spec"]["metadata"]["schedule_enabled"] is True
    assert approval_record["action_spec"]["metadata"]["schedule_index_regenerated"] is True
    assert approval_record["action_spec"]["metadata"]["external_scheduler_changed"] is False


def test_activation_executor_blocks_duplicate_before_second_enable(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    approval_id, activation_digest, schedule_id = _queue_activation(tmp_path)
    first = execute_phase11_chat_approved_schedule_activation(
        tmp_path,
        approval_id=approval_id,
        expected_activation_digest=activation_digest,
        operator_activation_statement="Approved once.",
    )
    second = execute_phase11_chat_approved_schedule_activation(
        tmp_path,
        approval_id=approval_id,
        expected_activation_digest=activation_digest,
        operator_activation_statement="Approved twice.",
    )

    assert first["ok"] is True
    assert second["ok"] is False
    assert "exact_once_marker_already_present" in second["blocked_reasons"]
    assert second["target_write"]["target_file_written"] is False
    assert load_schedule(schedule_id, tmp_path, check_registry=True).enabled is True  # type: ignore[union-attr]


def test_activation_executor_blocks_digest_mismatch_without_enablement(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    approval_id, _activation_digest, schedule_id = _queue_activation(tmp_path)

    payload = execute_phase11_chat_approved_schedule_activation(
        tmp_path,
        approval_id=approval_id,
        expected_activation_digest="bad-digest",
        operator_activation_statement="Approved with an incorrect digest.",
    )

    assert payload["ok"] is False
    assert "activation_digest_mismatch" in payload["blocked_reasons"]
    assert payload["target_write"]["schedule_enabled"] is False
    assert load_schedule(schedule_id, tmp_path, check_registry=True).enabled is False  # type: ignore[union-attr]
