from __future__ import annotations

from pathlib import Path

from runtime.chaser.runtime_activation_gate import (
    build_chaser_runtime_activation_gate_design,
)


def test_runtime_activation_gate_design_is_read_only(tmp_path: Path) -> None:
    result = build_chaser_runtime_activation_gate_design(tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_gate_design"
    assert result["schema_version"] == "chaser_runtime_activation_gate_design.v1"
    assert result["design_status"] == "design_ready_no_activation"
    assert result["live_runtime_ready"] is False
    assert result["ready_for_activation_now"] is False
    assert result["ready_to_write_activation_request_now"] is True
    assert result["activation_request_write_available"] is True
    assert result["activation_approval_decision_preflight_available"] is True
    assert result["activation_approval_consumption_design_available"] is True
    assert result["activation_approval_consumption_write_guard_available"] is True
    assert result["activation_post_consumption_readiness_available"] is True
    assert result["activation_executor_design_available"] is True
    assert result["activation_executor_write_guard_available"] is True
    assert result["activation_state_readiness_available"] is True
    assert result["profile_toolset_activation_design_available"] is True
    assert result["profile_toolset_activation_write_guard_available"] is True
    assert result["profile_toolset_activation_readiness_available"] is True
    assert result["terminal_toolset_binding_design_available"] is False
    assert result["terminal_toolset_binding_write_guard_available"] is False
    assert result["activation_approval_consumption_available"] is True
    assert result["activation_approval_consumption_scope"] == (
        "exact_once_marker_and_append_only_audit_only"
    )
    assert all(value is False for value in result["authority"].values())
    assert result["requested_activation"]["runtime_id"] == "chaser"
    assert result["requested_activation"]["profile_id"] == "ops"
    assert result["requested_activation"]["toolset_id"] == "terminal-preview"
    assert result["readiness_dependency"]["ok"] is True
    assert result["readiness_dependency"]["live_runtime_ready"] is False
    assert result["activation_gate_contract"]["contract_status"] == "design_only"
    assert result["activation_gate_contract"]["approval_required_before_any_activation"] is True
    assert result["activation_gate_contract"]["approval_request_writer_available_now"] is True
    assert result["activation_gate_contract"]["approval_decision_preflight_available_now"] is True
    assert result["activation_gate_contract"]["approval_consumption_design_available_now"] is True
    assert result["activation_gate_contract"]["approval_consumption_write_guard_available_now"] is True
    assert result["activation_gate_contract"]["approval_consumption_available_now"] is True
    assert result["activation_gate_contract"]["activation_executor_design_available_now"] is True
    assert result["activation_gate_contract"]["activation_executor_write_guard_available_now"] is True
    assert result["activation_gate_contract"]["activation_state_readiness_available_now"] is True
    assert result["activation_gate_contract"]["profile_toolset_activation_design_available_now"] is True
    assert result["activation_gate_contract"]["profile_toolset_activation_write_guard_available_now"] is True
    assert result["activation_gate_contract"]["profile_toolset_activation_readiness_available_now"] is True
    assert result["activation_gate_contract"]["terminal_toolset_binding_design_available_now"] is False
    assert result["activation_gate_contract"]["terminal_toolset_binding_write_guard_available_now"] is False
    preview_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_approval_request_preview"
    )
    assert preview_phase["implemented_now"] is True
    assert preview_phase["writes_now"] is False
    assert preview_phase["executes_now"] is False
    write_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_approval_request_write"
    )
    assert write_phase["implemented_now"] is True
    assert write_phase["writes_now"] is True
    assert write_phase["executes_now"] is False
    decision_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_approval_decision_preflight"
    )
    assert decision_phase["implemented_now"] is True
    assert decision_phase["writes_now"] is False
    assert decision_phase["executes_now"] is False
    consumption_design_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_approval_consumption_design"
    )
    assert consumption_design_phase["implemented_now"] is True
    assert consumption_design_phase["writes_now"] is False
    assert consumption_design_phase["executes_now"] is False
    consumption_write_guard_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_approval_consumption_write_guard"
    )
    assert consumption_write_guard_phase["implemented_now"] is True
    assert consumption_write_guard_phase["writes_now"] is True
    assert consumption_write_guard_phase["executes_now"] is False
    post_consumption_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_post_consumption_readiness"
    )
    assert post_consumption_phase["implemented_now"] is True
    assert post_consumption_phase["writes_now"] is False
    assert post_consumption_phase["executes_now"] is False
    executor_design_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_executor_design"
    )
    assert executor_design_phase["implemented_now"] is True
    assert executor_design_phase["writes_now"] is False
    assert executor_design_phase["executes_now"] is False
    executor_write_guard_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_executor_write_guard"
    )
    assert executor_write_guard_phase["implemented_now"] is True
    assert executor_write_guard_phase["writes_now"] is True
    assert executor_write_guard_phase["executes_now"] is False
    state_readiness_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "activation_state_readiness"
    )
    assert state_readiness_phase["implemented_now"] is True
    assert state_readiness_phase["writes_now"] is False
    assert state_readiness_phase["executes_now"] is False
    profile_toolset_design_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "profile_toolset_activation_design"
    )
    assert profile_toolset_design_phase["implemented_now"] is True
    assert profile_toolset_design_phase["writes_now"] is False
    assert profile_toolset_design_phase["executes_now"] is False
    profile_toolset_write_guard_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "profile_toolset_activation_write_guard"
    )
    assert profile_toolset_write_guard_phase["implemented_now"] is True
    assert profile_toolset_write_guard_phase["writes_now"] is True
    assert profile_toolset_write_guard_phase["executes_now"] is False
    profile_toolset_readiness_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "profile_toolset_activation_readiness"
    )
    assert profile_toolset_readiness_phase["implemented_now"] is True
    assert profile_toolset_readiness_phase["writes_now"] is False
    assert profile_toolset_readiness_phase["executes_now"] is False
    terminal_toolset_binding_design_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "terminal_toolset_binding_design"
    )
    assert terminal_toolset_binding_design_phase["implemented_now"] is False
    assert terminal_toolset_binding_design_phase["writes_now"] is False
    assert terminal_toolset_binding_design_phase["executes_now"] is False
    terminal_toolset_binding_write_guard_phase = next(
        phase
        for phase in result["gate_phases"]
        if phase["phase"] == "terminal_toolset_binding_write_guard"
    )
    assert terminal_toolset_binding_write_guard_phase["implemented_now"] is False
    assert terminal_toolset_binding_write_guard_phase["writes_now"] is False
    assert terminal_toolset_binding_write_guard_phase["executes_now"] is False
    assert result["terminal_binding_contract"]["terminal_binding_allowed_now"] is False
    assert result["terminal_binding_contract"]["terminal_execution_allowed_now"] is False
    assert "activation_approval_request_writer_not_implemented" not in result["future_gate_blockers"]
    assert "activation_approval_decision_preflight_not_implemented" not in result["future_gate_blockers"]
    assert "activation_approval_consumption_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert "activation_post_consumption_readiness_not_implemented" not in result["future_gate_blockers"]
    assert "activation_approval_consumption_activation_executor_not_implemented" not in result["future_gate_blockers"]
    assert "activation_executor_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert "activation_state_readiness_not_implemented" not in result["future_gate_blockers"]
    assert "profile_toolset_activation_design_not_implemented" not in result["future_gate_blockers"]
    assert "profile_toolset_activation_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert "profile_toolset_activation_readiness_not_implemented" not in result["future_gate_blockers"]
    assert "terminal_toolset_binding_design_not_implemented" in result["future_gate_blockers"]
    assert "terminal_toolset_binding_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert result["next_recommended_pass"] == (
        "terminal-n29-studio-full-terminal-product-contract"
    )
    assert "terminal_toolset_binding_executor_not_implemented" in result["future_gate_blockers"]
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs").exists()


def test_runtime_activation_gate_design_blocks_unknown_profile(tmp_path: Path) -> None:
    result = build_chaser_runtime_activation_gate_design(
        tmp_path,
        profile_id="missing",
        toolset_id="terminal-preview",
    )

    assert result["ok"] is False
    assert result["design_status"] == "design_blocked"
    assert "unknown_profile:missing" in result["blockers"]
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()
