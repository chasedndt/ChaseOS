"""Tests for Phase 11 Chat safety/action-class policy."""

from __future__ import annotations

from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
from runtime.studio.phase11_chat_router_contract import build_phase11_chat_router_contract
from runtime.studio.phase11_chat_safety_policy import (
    DENIED_ACTION_CLASS_CATALOG,
    build_phase11_chat_safety_policy,
)

SECTION_6_DEPENDENCY_REPORT_FIELDS = {
    "missing_contract",
    "affected_phase10_or_phase11_surface",
    "lower_phase_owner_or_surface",
    "minimum_proof_needed",
    "blocked_action_reason",
}


def _assert_full_section_6_dependency_report(entry: dict) -> None:
    assert SECTION_6_DEPENDENCY_REPORT_FIELDS.issubset(entry)
    for field in SECTION_6_DEPENDENCY_REPORT_FIELDS:
        assert entry[field]


def test_safety_policy_is_deny_default_for_every_action_class(tmp_path) -> None:
    policy = build_phase11_chat_safety_policy(
        tmp_path,
        intent_class="runtime-task",
        requested_denied_actions=["runtime_dispatch", "credential_or_config_mutation"],
    )

    assert policy["read_only"] is True
    assert policy["policy_status"] == "denied_fail_closed"
    assert policy["execution_allowed"] is False
    assert policy["mutation_allowed"] is False
    assert policy["writes_allowed"] is False
    assert policy["authority_absent_fails_closed"] is True
    assert policy["all_capabilities_policy_aware"] is True
    assert set(policy["denied_action_classes"]) == set(DENIED_ACTION_CLASS_CATALOG)
    assert policy["policy_fail_closed_summary"]["allowed_action_class_count"] == 0
    assert policy["policy_fail_closed_summary"]["denied_action_class_count"] == len(DENIED_ACTION_CLASS_CATALOG)
    assert "runtime_dispatch" in policy["triggered_action_classes"]
    assert "credential_or_config_mutation" in policy["triggered_action_classes"]
    for entry in policy["denied_action_classes"].values():
        assert entry["policy_decision"] == "deny"
        assert entry["allowed_now"] is False
        assert entry["deny_default_gate"] is True
        assert entry["fail_closed_when_authority_absent"] is True
        assert entry["missing_contract"]
        assert entry["lower_phase_owner_or_surface"]
        _assert_full_section_6_dependency_report(entry)


def test_router_embeds_safety_policy_and_fails_closed_on_denied_prompt(tmp_path) -> None:
    contract = build_phase11_chat_router_contract(
        tmp_path,
        message="Dispatch Hermes, open a browser, use shell, mutate config, consume approval, and promote canonical knowledge",
    )
    policy = contract["safety_policy"]

    assert contract["route_decision"]["route_execution_allowed"] is False
    assert contract["route_decision"]["policy_execution_allowed"] is False
    assert contract["route_decision"]["safety_policy_status"] == "denied_fail_closed"
    assert policy["policy_status"] == "denied_fail_closed"
    assert policy["authority_matrix"]["runtime_dispatch_allowed"] is False
    assert policy["authority_matrix"]["browser_control_allowed"] is False
    assert policy["authority_matrix"]["shell_execution_allowed"] is False
    assert policy["authority_matrix"]["approval_consumption_allowed"] is False
    assert policy["authority_matrix"]["canonical_mutation_allowed"] is False
    assert "phase11_chat_deny_default_policy_active" in policy["blocked_reasons"]
    assert "action_class_requires_lower_phase_authority" in policy["blocked_reasons"]
    for entry in policy["denied_action_classes"].values():
        _assert_full_section_6_dependency_report(entry)
    assert contract["authority"]["runtime_dispatch_allowed"] is False
    assert contract["authority"]["canonical_mutation_allowed"] is False


def test_panel_surfaces_safety_policy_and_denied_action_ui(tmp_path) -> None:
    panel = build_phase11_chat_panel_contract(
        tmp_path,
        message="Start OpenClaw, call provider API, write a vault note, and reject the approval",
    )
    policy = panel["safety_policy"]

    assert panel["summary"]["safety_policy_status"] == "denied_fail_closed"
    assert panel["summary"]["policy_allowed_action_class_count"] == 0
    assert panel["readiness"]["safety_policy_ready"] is True
    assert panel["readiness"]["all_chat_capabilities_policy_aware"] is True
    assert panel["readiness"]["authority_absent_fails_closed"] is True
    assert policy["all_capabilities_policy_aware"] is True
    assert policy["authority_matrix"]["provider_calls_allowed"] is False
    assert policy["authority_matrix"]["approval_execution_allowed"] is False
    for entry in policy["denied_action_classes"].values():
        _assert_full_section_6_dependency_report(entry)
    assert panel["denied_action_rendering"]["all_denied_actions_unavailable"] is True
    assert panel["denied_action_rendering"]["policy_status"] == "denied_fail_closed"
    assert panel["authority"]["provider_calls_allowed"] is False
    assert panel["authority"]["approval_execution_allowed"] is False
