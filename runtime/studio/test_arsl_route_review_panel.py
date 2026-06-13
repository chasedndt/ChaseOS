"""Tests for the read-only Studio ARSL route-review panel contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.arsl_route_review_panel import (
    DEFAULT_CAPABILITY,
    build_arsl_route_review_panel_contract,
)


ROOT = Path(__file__).resolve().parents[2]


def test_arsl_route_review_panel_contract_is_read_only() -> None:
    model = build_arsl_route_review_panel_contract(ROOT, capability="browser.click")

    assert model["ok"] is True
    assert model["surface"] == "studio_arsl_route_review_panel_contract"
    assert model["panel"]["panel_id"] == "studio.arsl.route_review.panel"
    assert model["panel"]["surface_route"] == "#arsl-route-review"
    assert model["panel"]["source_command"] == "chaseos runtime surfaces route-review --capability browser.click --json"
    assert model["panel"]["default_capability"] == DEFAULT_CAPABILITY
    assert model["summary"]["requested_capability"] == "browser.click"
    assert model["summary"]["preview_decision"] == "approval_required"
    assert model["summary"]["review_row_count"] >= 1
    assert model["readiness"]["arsl_route_review_panel_contract_ready"] is True
    assert model["readiness"]["desktop_shell_mount_ready"] is True
    assert model["readiness"]["route_execution_ui_ready"] is False
    assert model["readiness"]["approval_grant_ui_ready"] is False
    assert model["readiness"]["ledger_write_ui_ready"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["executes_routes"] is False
    assert model["authority"]["commits_route_proposals"] is False
    assert model["authority"]["writes_routing_ledger"] is False
    assert model["authority"]["grants_approvals"] is False
    assert model["authority"]["mutates_gate_policy"] is False
    assert model["authority"]["dispatches_runtimes"] is False
    assert model["authority"]["provider_calls_allowed"] is False
    assert model["authority"]["browser_control_allowed"] is False
    assert model["authority"]["mcp_tools_exposed"] is False
    assert model["authority"]["raw_manifest_exposed"] is False
    assert model["authority"]["credential_values_visible"] is False
    assert model["authority"]["browser_profile_visible"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []
    assert model["source_route_review"]["safety"]["execution_performed"] is False
    assert model["source_route_review"]["safety"]["ledger_written"] is False
    assert model["source_route_review"]["safety"]["browser_control_performed"] is False
    assert model["source_route_review"]["safety"]["raw_manifest_exposed"] is False
