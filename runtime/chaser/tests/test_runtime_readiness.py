from __future__ import annotations

from pathlib import Path

from runtime.chaser.runtime_readiness import build_chaser_runtime_readiness


def test_chaser_runtime_readiness_is_read_only_and_blocks_live_wiring(tmp_path: Path) -> None:
    result = build_chaser_runtime_readiness(tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_readiness_review"
    assert result["schema_version"] == "chaser_runtime_readiness_review.v1"
    assert result["review_status"] == "readiness_review_complete_live_wiring_blocked"
    assert result["live_runtime_ready"] is False
    assert result["ready_for_runtime_activation"] is False
    assert result["read_only_review_available"] is True
    assert result["activation_gate_design_available"] is True
    assert result["activation_gate_design_surface"] == "chaser_runtime_activation_gate_design"
    assert result["activation_approval_preview_available"] is True
    assert result["activation_approval_preview_surface"] == "chaser_runtime_activation_approval_preview"
    assert result["activation_approval_request_write_available"] is True
    assert result["activation_approval_request_write_surface"] == (
        "chaser_runtime_activation_approval_request_write_gate"
    )
    assert result["activation_approval_decision_preflight_available"] is True
    assert result["activation_approval_decision_preflight_surface"] == (
        "chaser_runtime_activation_approval_decision_preflight"
    )
    assert result["activation_approval_consumption_design_available"] is True
    assert result["activation_approval_consumption_design_surface"] == (
        "chaser_runtime_activation_approval_consumption_design"
    )
    assert result["activation_approval_consumption_write_guard_available"] is True
    assert result["activation_approval_consumption_write_guard_surface"] == (
        "chaser_runtime_activation_approval_consumption_write_guard"
    )
    assert result["activation_post_consumption_readiness_available"] is True
    assert result["activation_post_consumption_readiness_surface"] == (
        "chaser_runtime_activation_post_consumption_readiness"
    )
    assert result["activation_executor_design_available"] is True
    assert result["activation_executor_design_surface"] == (
        "chaser_runtime_activation_executor_design"
    )
    assert result["activation_executor_write_guard_available"] is True
    assert result["activation_executor_write_guard_surface"] == (
        "chaser_runtime_activation_executor_write_guard"
    )
    assert result["activation_state_readiness_available"] is True
    assert result["activation_state_readiness_surface"] == (
        "chaser_runtime_activation_state_readiness"
    )
    assert result["profile_toolset_activation_design_available"] is True
    assert result["profile_toolset_activation_design_surface"] == (
        "chaser_runtime_profile_toolset_activation_design"
    )
    assert result["profile_toolset_activation_write_guard_available"] is True
    assert result["profile_toolset_activation_write_guard_surface"] == (
        "chaser_runtime_profile_toolset_activation_write_guard"
    )
    assert result["profile_toolset_activation_readiness_available"] is True
    assert result["profile_toolset_activation_readiness_surface"] == (
        "chaser_runtime_profile_toolset_activation_readiness"
    )
    assert result["terminal_toolset_binding_design_available"] is False
    assert result["terminal_toolset_binding_design_surface"] == ""
    assert result["terminal_toolset_binding_write_guard_available"] is False
    assert result["terminal_toolset_binding_runtime_binding_available"] is False
    assert result["next_recommended_pass"] == (
        "terminal-n29-studio-full-terminal-product-contract"
    )
    assert result["contract_summary"]["checks_failed"] == 0
    assert all(check["ok"] is True for check in result["contract_checks"])
    assert all(value is False for value in result["authority"].values())
    assert all(value is False for value in result["chaser_no_authority"].values())
    assert result["activation_posture"]["terminal_execution_allowed"] is False
    assert result["activation_posture"]["approval_queue_write_allowed"] is True
    assert result["activation_posture"]["approval_queue_write_scope"] == (
        "chaser_runtime_activation_approval_request_only"
    )
    assert result["activation_posture"]["approval_decision_preflight_allowed"] is True
    assert result["activation_posture"]["approval_decision_preflight_scope"] == (
        "chaser_runtime_activation_approval_request_only"
    )
    assert result["activation_posture"]["approval_consumption_design_allowed"] is True
    assert result["activation_posture"]["approval_consumption_design_scope"] == (
        "chaser_runtime_activation_approval_request_only"
    )
    assert result["activation_posture"]["approval_consumption_write_guard_allowed"] is True
    assert result["activation_posture"]["approval_consumption_write_guard_scope"] == (
        "exact_once_marker_and_append_only_audit_only"
    )
    assert result["activation_posture"]["approval_consumption_allowed"] is True
    assert result["activation_posture"]["approval_consumption_scope"] == (
        "exact_once_marker_and_append_only_audit_only"
    )
    assert result["activation_posture"]["post_consumption_readiness_allowed"] is True
    assert result["activation_posture"]["post_consumption_readiness_scope"] == (
        "read_only_marker_and_audit_validation_only"
    )
    assert result["activation_posture"]["activation_executor_design_allowed"] is True
    assert result["activation_posture"]["activation_executor_design_scope"] == (
        "read_only_fail_closed_design_only"
    )
    assert result["activation_posture"]["activation_executor_write_guard_allowed"] is True
    assert result["activation_posture"]["activation_executor_write_guard_scope"] == (
        "exact_once_activation_marker_state_and_audit_only"
    )
    assert result["activation_posture"]["activation_state_readiness_allowed"] is True
    assert result["activation_posture"]["activation_state_readiness_scope"] == (
        "read_only_activation_marker_state_and_audit_validation_only"
    )
    assert result["activation_posture"]["profile_toolset_activation_design_allowed"] is True
    assert result["activation_posture"]["profile_toolset_activation_design_scope"] == (
        "read_only_profile_toolset_activation_design_only"
    )
    assert result["activation_posture"]["profile_toolset_activation_write_guard_allowed"] is True
    assert result["activation_posture"]["profile_toolset_activation_write_guard_scope"] == (
        "exact_once_marker_profile_state_toolset_state_and_append_only_audit_only"
    )
    assert result["activation_posture"]["profile_toolset_activation_readiness_allowed"] is True
    assert result["activation_posture"]["profile_toolset_activation_readiness_scope"] == (
        "read_only_profile_toolset_marker_state_and_audit_validation_only"
    )
    assert result["activation_posture"]["terminal_toolset_binding_design_allowed"] is False
    assert result["activation_posture"]["terminal_toolset_binding_design_scope"] == (
        "deferred_until_human_studio_terminal_foundation_exists"
    )
    assert result["activation_posture"]["terminal_toolset_binding_write_guard_allowed"] is False
    assert result["activation_posture"]["agent_bus_mutation_allowed"] is False
    assert result["activation_posture"]["provider_call_allowed"] is False
    assert "chaser_runtime_adapter_not_installed" in result["blockers_for_live_wiring"]
    assert "terminal_toolset_binding_not_implemented" in result["blockers_for_live_wiring"]
    assert "profile_toolset_activation_write_guard_not_implemented" not in result["blockers_for_live_wiring"]
    assert "profile_toolset_activation_readiness_not_implemented" not in result["blockers_for_live_wiring"]
    assert "live_runtime_activation_approval_gate_not_implemented" in result["blockers_for_live_wiring"]
    profile_toolset_design_gate = next(
        gate
        for gate in result["activation_gates"]
        if gate["name"] == "profile_toolset_activation_design"
    )
    assert profile_toolset_design_gate["satisfied"] is True
    profile_toolset_write_guard_gate = next(
        gate
        for gate in result["activation_gates"]
        if gate["name"] == "profile_toolset_activation_write_guard"
    )
    assert profile_toolset_write_guard_gate["satisfied"] is True
    profile_toolset_readiness_gate = next(
        gate
        for gate in result["activation_gates"]
        if gate["name"] == "profile_toolset_activation_readiness"
    )
    assert profile_toolset_readiness_gate["satisfied"] is True
    assert all(
        gate["name"] != "terminal_toolset_binding_design"
        for gate in result["activation_gates"]
    )
    assert result["terminal_authority_audit"]["ok"] is True
    assert result["trust_tier"] == "Tier 4"
    assert result["terminal_output_trusted"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs").exists()


def test_chaser_runtime_readiness_fails_closed_on_profile_authority_claim(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from runtime.chaser import runtime_readiness

    def bad_profiles() -> list[dict]:
        return [{
            "profile_id": "bad",
            "grants_permission": True,
            "activates_runtime": False,
            "calls_provider": False,
            "authority": {},
        }]

    monkeypatch.setattr(runtime_readiness, "list_profiles", bad_profiles)

    result = runtime_readiness.build_chaser_runtime_readiness(tmp_path)

    assert result["ok"] is False
    assert result["review_status"] == "readiness_review_contract_failure"
    assert "profile_views_descriptive_only" in result["contract_summary"]["failed_checks"]
    assert not (tmp_path / "runtime" / "agent_bus").exists()
