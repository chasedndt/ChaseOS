"""Pulse CLI contract coverage for approval evidence slot surfaces."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "runtime" / "cli" / "command_contract.json"


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _command_by_path(contract: dict, *path: str) -> dict:
    for command in contract["commands"]:
        if tuple(command["path"]) == path:
            return command
    raise AssertionError(f"missing command contract for {' '.join(path)}")


def test_pulse_approval_readiness_contract_exposes_slot_shape() -> None:
    contract = _load_contract()
    shape = contract["json_shapes"]["pulse_approval_readiness_summary"]
    slot_shape = shape["nested_shapes"]["approval_evidence_slots"]

    assert shape["supported"] is True
    assert "approval_evidence_slots" in shape["required_keys"]
    assert "supervised_live_command_preview" in shape["required_keys"]
    assert "agent_bus_task_written" in shape["required_keys"]
    assert "canonical_writeback_allowed" in shape["required_keys"]
    assert "ref_placeholder" in slot_shape["required_keys"]
    assert "requires_real_ref" in slot_shape["required_keys"]
    assert "placeholder_ref_rejected" in slot_shape["required_keys"]

    command = _command_by_path(contract, "pulse", "approval-readiness")
    assert command["json_shape"] == "pulse_approval_readiness_summary"
    assert "read:agent_bus (list_tasks only)" in command["side_effects"]
    assert "no evidence write" in command["side_effects"]
    assert "no Agent Bus task write" in command["side_effects"]
    assert "no canonical writeback" in command["side_effects"]


def test_pulse_operator_gate_contract_exposes_slot_shape() -> None:
    contract = _load_contract()
    shape = contract["json_shapes"]["pulse_operator_gate_approval_ui_contract"]
    slot_shape = shape["nested_shapes"]["approval_evidence_slots"]

    assert shape["supported"] is True
    assert "approval_evidence_slots" in shape["required_keys"]
    assert "decision_controls" in shape["required_keys"]
    assert "live_agent_bus_handoff_allowed" in shape["required_keys"]
    assert "canonical_writeback_allowed" in shape["required_keys"]
    assert "ref_placeholder" in slot_shape["required_keys"]
    assert "requires_real_ref" in slot_shape["required_keys"]
    assert "placeholder_ref_rejected" in slot_shape["required_keys"]

    command = _command_by_path(contract, "pulse", "operator-gate-contract")
    assert command["json_shape"] == "pulse_operator_gate_approval_ui_contract"
    assert "read:agent_bus (list_tasks only)" in command["side_effects"]
    assert "no approval grant" in command["side_effects"]
    assert "no live enqueue execution" in command["side_effects"]
    assert "no Agent Bus task write" in command["side_effects"]


def test_pulse_final_evidence_gate_contract_exposes_final_slot_shape() -> None:
    contract = _load_contract()
    shape = contract["json_shapes"]["pulse_final_evidence_gate_status"]
    slot_shape = shape["nested_shapes"]["approval_evidence_slots"]
    missing_slot_shape = shape["nested_shapes"]["missing_operator_action_slots"]
    authority_slot_shape = shape["nested_shapes"]["missing_authority_action_slots"]
    runtime_slot_shape = shape["nested_shapes"]["missing_runtime_self_satisfiable_slots"]

    assert shape["supported"] is True
    assert "gate_status" in shape["required_keys"]
    assert "operator_action_required" in shape["required_keys"]
    assert "can_runtime_self_satisfy_remaining" in shape["required_keys"]
    assert "closure_status" in shape["required_keys"]
    assert "closure_authority_classes" in shape["required_keys"]
    assert "closure_runtime_action_keys" in shape["required_keys"]
    assert "missing_operator_action_slots" in shape["required_keys"]
    assert "missing_authority_action_slots" in shape["required_keys"]
    assert "missing_runtime_self_satisfiable_slots" in shape["required_keys"]
    assert "final_feature_blockers" in shape["required_keys"]
    assert "supervised_live_command_preview" in shape["required_keys"]
    assert "ref_placeholder" in slot_shape["required_keys"]
    assert "requires_real_ref" in slot_shape["required_keys"]
    assert "placeholder_ref_rejected" in slot_shape["required_keys"]
    assert "authority_class" in slot_shape["required_keys"]
    assert "runtime_self_satisfiable" in slot_shape["required_keys"]
    assert "authority_class" in missing_slot_shape["required_keys"]
    assert "runtime_self_satisfiable" in missing_slot_shape["required_keys"]
    assert "authority_class" in authority_slot_shape["required_keys"]
    assert "runtime_self_satisfiable" in authority_slot_shape["required_keys"]
    assert "authority_class" in runtime_slot_shape["required_keys"]
    assert "runtime_self_satisfiable" in runtime_slot_shape["required_keys"]

    command = _command_by_path(contract, "pulse", "final-evidence-gate")
    assert command["json_shape"] == "pulse_final_evidence_gate_status"
    assert "read:agent_bus (list_tasks only)" in command["side_effects"]
    assert "no evidence write" in command["side_effects"]
    assert "no live enqueue execution" in command["side_effects"]
    assert "no Agent Bus task write" in command["side_effects"]
    assert "no R&D workbook update" in command["side_effects"]
