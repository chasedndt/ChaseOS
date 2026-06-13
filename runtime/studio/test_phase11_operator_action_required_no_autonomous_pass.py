"""Tests for the Phase 11 operator-action-required no-autonomous-pass gate."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_operator_action_required_no_autonomous_pass import (
    NEXT_RECOMMENDED_ACTION,
    PASS_ID,
    build_phase11_operator_action_required_no_autonomous_pass,
    format_phase11_operator_action_required_no_autonomous_pass,
)
from runtime.studio.test_phase11_no_hitl_lane_completion_audit import _seed_completion_vault


EXPECTED_DECISIONS = {
    "select_governed_executor_lane",
    "defer_phase11_closeout",
}

EXPECTED_LANES = {
    # "live_provider_model_execution" was retired: Studio never calls providers directly
    # (provider-agnostic architecture rule — all LLM dispatch via Agent Bus → runtime)
    "browser_dispatch_executor",
    "approval_target_mutation_executor",
    "agent_bus_or_canonical_writeback",
}


def test_operator_action_gate_requires_explicit_decision_without_authority(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    gate = build_phase11_operator_action_required_no_autonomous_pass(tmp_path)
    summary = gate["summary"]
    checks = {item["id"]: item for item in gate["decision_checklist"]}

    assert gate["ok"] is True
    assert gate["surface"] == "phase11_operator_action_required_no_autonomous_pass"
    assert gate["pass"] == PASS_ID
    assert PASS_ID == "operator-action-required-no-autonomous-phase11-pass"
    assert gate["status"] == "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DECISION REQUIRED"
    assert summary["decision_gate_ready"] is True
    assert summary["autonomous_phase11_passes_remaining"] == 0
    assert summary["substantial_no_hitl_passes_remaining"] == 0
    assert summary["operator_decision_required"] is True
    assert summary["implementation_authority_granted"] is False
    assert summary["selected_lane_id"] is None
    assert summary["next_recommended_action"] == NEXT_RECOMMENDED_ACTION
    assert NEXT_RECOMMENDED_ACTION == "operator-select-governed-executor-lane-or-defer-closeout"

    for key in [
        "handoff_ready",
        "zero_autonomous_phase11_passes_remaining",
        "operator_decision_required",
        "no_lane_selected_implicitly",
        "authority_bounded",
    ]:
        assert checks[key]["satisfied"] is True


def test_operator_action_gate_lists_decision_options_and_governed_lanes(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    gate = build_phase11_operator_action_required_no_autonomous_pass(tmp_path)
    decisions = {item["decision_id"]: item for item in gate["available_decisions"]}
    lanes = {item["lane_id"]: item for item in gate["operator_governed_lanes"]}

    assert EXPECTED_DECISIONS.issubset(decisions)
    assert EXPECTED_LANES.issubset(lanes)
    for decision in decisions.values():
        assert decision["selected_now"] is False
        assert decision["implementation_authority_granted"] is False
    for lane in lanes.values():
        assert lane["requires_operator_selection"] is True
        assert lane["selected_now"] is False
        assert lane["implementation_authority_granted"] is False


def test_operator_action_gate_authority_is_bounded_and_formatted(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    gate = build_phase11_operator_action_required_no_autonomous_pass(tmp_path)
    authority = gate["authority"]
    text = format_phase11_operator_action_required_no_autonomous_pass(gate)

    assert authority["read_only"] is True
    assert authority["operator_decision_gate_only"] is True
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "Operator Action Required / No Autonomous Phase 11 Pass" in text
    assert "autonomous_phase11_passes_remaining: 0" in text
    assert "Boundary: decision gate only" in text


def test_operator_action_gate_writes_bounded_json_and_markdown_evidence(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    gate = build_phase11_operator_action_required_no_autonomous_pass(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-operator-action-required-no-autonomous-pass",
    )

    assert gate["ok"] is True
    assert gate["evidence"]["written"] is True
    assert gate["evidence"]["json_path"].endswith(
        "test-phase11-operator-action-required-no-autonomous-pass.json"
    )
    assert gate["evidence"]["markdown_path"].endswith(
        "test-phase11-operator-action-required-no-autonomous-pass.md"
    )
    json_path = tmp_path / gate["evidence"]["json_path"]
    markdown_path = tmp_path / gate["evidence"]["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["surface"] == "phase11_operator_action_required_no_autonomous_pass"
    assert payload["summary"]["operator_decision_required"] is True
    assert "Phase 11 Operator Action Required / No Autonomous Phase 11 Pass" in markdown_path.read_text(
        encoding="utf-8"
    )
