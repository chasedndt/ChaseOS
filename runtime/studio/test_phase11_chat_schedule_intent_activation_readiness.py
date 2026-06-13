"""Tests for Studio Chat schedule activation readiness packets."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.schedules.loader import load_schedule
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


def _write_disabled_schedule_from_chat(root: Path) -> tuple[str, str]:
    preview = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for activation readiness.",
    )
    schedule_digest = preview["digest_proof"]["schedule_digest"]
    queued = build_phase11_chat_schedule_proposal_packet(
        root,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for activation readiness.",
        expected_schedule_digest=schedule_digest,
        write_approval=True,
    )
    consumed = execute_phase11_chat_schedule_proposal_consumption(
        root,
        approval_id=queued["summary"]["approval_id"],
        expected_schedule_digest=schedule_digest,
        operator_approval_statement="Approved for staged schedule proposal.",
    )
    written = execute_phase11_chat_approved_schedule_intent_writer(
        root,
        staged_proposal_path=consumed["target_write"]["staged_schedule_proposal_path"],
        expected_schedule_digest=schedule_digest,
        operator_schedule_write_statement="Approved to write disabled schedule intent.",
    )
    assert written["ok"] is True
    return written["target_write"]["schedule_id"], schedule_digest


def test_activation_readiness_requires_schedule_id(tmp_path: Path) -> None:
    payload = build_phase11_chat_schedule_intent_activation_readiness(tmp_path)

    assert payload["ok"] is False
    assert "schedule_id_required" in payload["blocked_reasons"]
    assert payload["target_write_proof"]["schedule_enabled"] is False
    assert payload["target_write_proof"]["schedule_index_regenerated"] is False


def test_activation_readiness_previews_enable_without_writing(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id, _schedule_digest = _write_disabled_schedule_from_chat(tmp_path)

    payload = build_phase11_chat_schedule_intent_activation_readiness(
        tmp_path,
        schedule_id=schedule_id,
    )
    intent = load_schedule(schedule_id, tmp_path, check_registry=True)

    assert payload["ok"] is True
    assert payload["summary"]["activation_preview_ready"] is True
    assert payload["digest_proof"]["activation_digest"]
    assert payload["future_activation_preview"]["future_executor_required"] is True
    assert "enabled: true" in payload["future_activation_preview"]["future_enabled_yaml_preview"]
    assert payload["target_write_proof"]["target_file_written"] is False
    assert payload["target_write_proof"]["schedule_enabled"] is False
    assert payload["target_write_proof"]["external_scheduler_changed"] is False
    assert payload["target_write_proof"]["agent_bus_task_written"] is False
    assert payload["target_write_proof"]["runtime_dispatched"] is False
    assert payload["target_write_proof"]["discord_api_called"] is False
    assert payload["target_write_proof"]["provider_call_performed"] is False
    assert payload["target_write_proof"]["credential_value_read"] is False
    assert payload["adapter_export_preview"]["currently_enabled_export_count"] == 0
    assert intent is not None
    assert intent.enabled is False


def test_activation_readiness_queues_digest_bound_approval_only(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id, _schedule_digest = _write_disabled_schedule_from_chat(tmp_path)
    preview = build_phase11_chat_schedule_intent_activation_readiness(tmp_path, schedule_id=schedule_id)
    digest = preview["digest_proof"]["activation_digest"]

    queued = build_phase11_chat_schedule_intent_activation_readiness(
        tmp_path,
        schedule_id=schedule_id,
        expected_activation_digest=digest,
        write_approval=True,
    )
    duplicate = build_phase11_chat_schedule_intent_activation_readiness(
        tmp_path,
        schedule_id=schedule_id,
        expected_activation_digest=digest,
        write_approval=True,
    )
    approval_path = tmp_path / queued["approval_queue_write"]["approval_path"]
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    intent = load_schedule(schedule_id, tmp_path, check_registry=True)
    service = StudioService(tmp_path)
    req = service.get_approval(queued["approval_queue_write"]["approval_id"])
    assert req is not None
    req.status = "approved"
    service._write_approval_record(req)  # type: ignore[attr-defined]

    assert queued["ok"] is True
    assert queued["approval_queue_write"]["approval_request_created"] is True
    assert queued["target_write_proof"]["schedule_enabled"] is False
    assert approval["action_spec"]["metadata"]["phase11_chat_schedule_activation_readiness"] is True
    assert approval["action_spec"]["metadata"]["phase11_chat_schedule_activation_execution_blocked"] is True
    assert approval["action_spec"]["metadata"]["activation_digest"] == digest
    assert duplicate["ok"] is True
    assert duplicate["approval_queue_write"]["duplicate_active_request_present"] is True
    assert duplicate["approval_queue_write"]["approval_request_created"] is False
    assert intent is not None
    assert intent.enabled is False
    try:
        service.execute_approved(req.approval_id)
    except StudioServiceError as exc:
        assert "schedule activation approval requests" in str(exc)
    else:  # pragma: no cover - execute_approved must stay blocked for this artifact class.
        raise AssertionError("ambient Studio execution unexpectedly enabled a schedule")


def test_activation_readiness_blocks_digest_mismatch(tmp_path: Path) -> None:
    _seed_operator_today_workflow(tmp_path)
    schedule_id, _schedule_digest = _write_disabled_schedule_from_chat(tmp_path)

    payload = build_phase11_chat_schedule_intent_activation_readiness(
        tmp_path,
        schedule_id=schedule_id,
        expected_activation_digest="bad-digest",
        write_approval=True,
    )

    assert payload["ok"] is False
    assert "expected_activation_digest_mismatch" in payload["blocked_reasons"]
    assert payload["approval_queue_write"]["approval_request_created"] is False
    assert load_schedule(schedule_id, tmp_path, check_registry=True).enabled is False  # type: ignore[union-attr]
