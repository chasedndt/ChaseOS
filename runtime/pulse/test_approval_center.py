from __future__ import annotations

from dataclasses import replace
import json
import shutil
from pathlib import Path

import pytest

from runtime.pulse.approval_center import (
    APPROVAL_CENTER_LANES,
    build_pulse_approval_center_readiness,
)
from runtime.pulse.bus_enqueue_evidence import create_agent_bus_enqueue_evidence_record
from runtime.pulse.real_approval_artifact_rehearsal import (
    run_real_approval_artifact_rehearsal,
)


def _temp_vault(name: str) -> Path:
    base = (Path(__file__).resolve().parent / "_tmp_approval_center").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if base.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {base}")
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _cleanup_temp_vault(vault: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_approval_center").resolve()
    if vault.resolve().parent != base:
        raise RuntimeError(f"Refusing unsafe test cleanup: {vault}")
    if vault.exists():
        shutil.rmtree(vault)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _write_user_deck(vault: Path) -> None:
    deck_path = vault / "07_LOGS" / "Pulse-Decks" / "users" / "2026-05-02-user-pulse.json"
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    deck_path.write_text(
        json.dumps(
            {
                "deck_id": "pulse-approval-center-test",
                "audience": "user",
                "generated_at": "2026-05-02T18:00:00+00:00",
                "cards": [
                    {
                        "card_id": "pulse-card-approval-center-001",
                        "audience": "user",
                        "card_class": "Project Momentum",
                        "title": "Approval center test card",
                        "summary": "Test card.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _seed_rehearsal(vault: Path) -> str:
    _write_user_deck(vault)
    rehearsal = run_real_approval_artifact_rehearsal(
        vault,
        generated_at="2026-05-02T18:05:00+00:00",
    )
    return rehearsal.approval_request_artifact.request_id


def test_empty_approval_center_is_read_only_and_exposes_all_lanes() -> None:
    vault = _temp_vault("empty")
    try:
        before = _snapshot(vault)

        surface = build_pulse_approval_center_readiness(
            vault,
            generated_at="2026-05-02T18:10:00+00:00",
            bus_tasks=[],
        )

        assert _snapshot(vault) == before
        assert surface.approval_center_status == "no_review_items"
        assert {lane.lane_id for lane in surface.lanes} == APPROVAL_CENTER_LANES
        assert surface.read_only is True
        assert surface.local_only is True
        assert surface.agent_bus_task_write_allowed is False
        assert surface.canonical_writeback_allowed is False
    finally:
        _cleanup_temp_vault(vault)


def test_approval_center_summarizes_blocked_request_without_writes() -> None:
    vault = _temp_vault("blocked")
    try:
        request_id = _seed_rehearsal(vault)
        before = _snapshot(vault)

        surface = build_pulse_approval_center_readiness(
            vault,
            request_id=request_id,
            generated_at="2026-05-02T18:15:00+00:00",
            bus_tasks=[],
        )

        assert _snapshot(vault) == before
        assert surface.latest_request_id == request_id
        assert surface.approval_center_status == "blocked_or_waiting_for_evidence"
        assert surface.approval_request_count == 1
        assert surface.pending_feedback_count == 1
        assert "operator_enqueue_approval" in surface.missing_approval_keys
        assert surface.final_gate_status == "blocked_required_evidence_missing"
        assert any(action.action_type == "capture_evidence_reference" for action in surface.action_previews)
        assert all(action.execution_allowed is False for action in surface.action_previews)
        assert surface.writes_review_decisions is False
        assert surface.applies_candidates is False
    finally:
        _cleanup_temp_vault(vault)


def test_approval_center_ready_request_still_does_not_execute() -> None:
    vault = _temp_vault("ready")
    try:
        request_id = _seed_rehearsal(vault)
        record, _artifact = create_agent_bus_enqueue_evidence_record(
            vault,
            request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="test operator approval",
            gate_policy_ref="test-gate-policy",
            external_sender_allowance_ref="test-external-sender",
            duplicate_review_ref="test-duplicate-review",
            created_at="2026-05-02T18:20:00+00:00",
        )
        before = _snapshot(vault)

        surface = build_pulse_approval_center_readiness(
            vault,
            request_id=request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-02T18:21:00+00:00",
            bus_tasks=[],
        )

        assert _snapshot(vault) == before
        assert surface.approval_center_status == "ready_for_operator_review"
        assert surface.missing_approval_keys == ()
        assert surface.final_gate_status == "ready_for_explicit_operator_live_enqueue"
        command_actions = [
            action
            for action in surface.action_previews
            if action.action_type == "preview_supervised_command"
        ]
        assert command_actions
        assert command_actions[0].command_preview
        assert command_actions[0].execution_allowed is False
        assert surface.agent_bus_task_write_allowed is False
        assert surface.grants_approvals is False
        assert surface.executes_approval is False
    finally:
        _cleanup_temp_vault(vault)


def test_approval_center_rejects_authority_flags() -> None:
    vault = _temp_vault("authority")
    try:
        surface = build_pulse_approval_center_readiness(vault, bus_tasks=[])

        for flag in (
            "writes_status_artifact",
            "writes_review_decisions",
            "writes_feedback_candidates",
            "applies_candidates",
            "grants_approvals",
            "executes_approval",
            "agent_bus_task_write_allowed",
            "runtime_dispatch_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
            "memory_approval_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_created",
            "rd_workbook_update_allowed",
        ):
            with pytest.raises(ValueError):
                replace(surface, **{flag: True}).validate()
    finally:
        _cleanup_temp_vault(vault)
