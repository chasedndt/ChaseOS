"""Tests for the Phase 11 operator-governed executor/deferred closeout handoff."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_operator_governed_executor_deferred_closeout import (
    NEXT_OPERATOR_ACTION,
    PASS_ID,
    build_phase11_operator_governed_executor_deferred_closeout,
    format_phase11_operator_governed_executor_deferred_closeout,
)
from runtime.studio.test_phase11_no_hitl_lane_completion_audit import _seed_completion_vault


EXPECTED_LANES = {
    "browser_dispatch_executor",
    "approval_target_mutation_executor",
    "agent_bus_or_canonical_writeback",
}

EXPECTED_RETIRED_LANES = {
    "live_provider_model_execution",
}


def test_operator_handoff_declares_no_autonomous_passes_and_next_operator_action(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    handoff = build_phase11_operator_governed_executor_deferred_closeout(tmp_path)
    summary = handoff["summary"]
    checklist = {item["id"]: item for item in handoff["handoff_checklist"]}

    assert handoff["ok"] is True
    assert handoff["surface"] == "phase11_operator_governed_executor_deferred_closeout"
    assert handoff["pass"] == PASS_ID
    assert PASS_ID == "operator-selected-governed-executor-or-deferred-closeout"
    assert handoff["status"] == "COMPLETE / READ-ONLY / VERIFIED / OPERATOR HANDOFF READY"
    assert summary["handoff_ready"] is True
    assert summary["no_hitl_lane_complete"] is True
    assert summary["substantial_no_hitl_passes_remaining"] == 0
    assert summary["substantial_handoff_passes_remaining"] == 0
    assert summary["operator_selection_required"] is True
    assert summary["implementation_authority_granted"] is False
    assert summary["next_operator_action"] == NEXT_OPERATOR_ACTION
    assert NEXT_OPERATOR_ACTION == "operator-select-governed-executor-or-defer-closeout"

    for key in [
        "no_hitl_lane_completion_verified",
        "no_autonomous_phase11_passes_remaining",
        "operator_selection_required_before_executor_work",
        "deferred_closeout_path_available",
        "handoff_is_read_only",
    ]:
        assert checklist[key]["satisfied"] is True


def test_operator_handoff_marks_remaining_lanes_operator_governed(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    handoff = build_phase11_operator_governed_executor_deferred_closeout(tmp_path)
    lanes = {item["lane_id"]: item for item in handoff["operator_governed_lanes"]}
    retired = {item["lane_id"]: item for item in handoff.get("retired_lanes", [])}

    assert EXPECTED_LANES.issubset(set(lanes))
    assert EXPECTED_RETIRED_LANES.issubset(set(retired))
    # retired lanes must not appear in operator_governed_lanes
    assert not EXPECTED_RETIRED_LANES.intersection(set(lanes))
    assert handoff["summary"]["operator_governed_remaining_lane_count"] == 3
    assert handoff["summary"]["retired_lane_count"] == 1
    assert retired["live_provider_model_execution"]["retired"] is True
    for lane in lanes.values():
        assert lane["requires_operator_selection"] is True
        assert lane["eligible_for_autonomous_execution"] is False
        assert lane["selected_now"] is False
        assert lane["implementation_authority_granted"] is False


def test_operator_handoff_authority_is_bounded_and_formatted(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    handoff = build_phase11_operator_governed_executor_deferred_closeout(tmp_path)
    authority = handoff["authority"]
    text = format_phase11_operator_governed_executor_deferred_closeout(handoff)

    assert authority["read_only"] is True
    assert authority["operator_handoff_only"] is True
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "Operator-Governed Executor / Deferred Closeout" in text
    assert "substantial_no_hitl_passes_remaining: 0" in text
    assert "Boundary: operator handoff only" in text


def test_operator_handoff_writes_bounded_json_and_markdown_evidence(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    handoff = build_phase11_operator_governed_executor_deferred_closeout(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-operator-governed-executor-deferred-closeout",
    )

    assert handoff["ok"] is True
    assert handoff["evidence"]["written"] is True
    assert handoff["evidence"]["json_path"].endswith(
        "test-phase11-operator-governed-executor-deferred-closeout.json"
    )
    assert handoff["evidence"]["markdown_path"].endswith(
        "test-phase11-operator-governed-executor-deferred-closeout.md"
    )
    json_path = tmp_path / handoff["evidence"]["json_path"]
    markdown_path = tmp_path / handoff["evidence"]["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["surface"] == "phase11_operator_governed_executor_deferred_closeout"
    assert payload["summary"]["operator_selection_required"] is True
    assert "Phase 11 Operator-Governed Executor / Deferred Closeout" in markdown_path.read_text(
        encoding="utf-8"
    )
