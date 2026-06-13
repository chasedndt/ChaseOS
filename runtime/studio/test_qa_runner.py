"""Tests for the bounded Studio QA runner."""

from __future__ import annotations

from pathlib import Path
import argparse

import pytest

from runtime.studio import qa_runner
from runtime.studio.qa_runner import (
    StudioQARunnerError,
    run_phase10_studio_qa_proof_lane,
    run_studio_qa_runner,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _blocked_current_repo_state(payload: dict) -> bool:
    return str(payload.get("status") or "").startswith("blocked_") and bool(payload.get("blockers") or [])


def test_native_shell_static_runner_does_not_start_server_or_write_evidence() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="native-shell",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["frontend_index_exists"]["ok"] is True
    assert checks["cytoscape_bundled_local"]["ok"] is True
    assert checks["frontend_inspector_tabs_exists"]["ok"] is True
    assert checks["panel_registry_ok"]["ok"] is True
    assert checks["panel_registry_ready"]["ok"] is True
    assert checks["panel_registry_safe_or_approval_gated"]["ok"] is True
    assert checks["panel_registry_exposes_blocked_authority"]["ok"] is True
    assert checks["browser_runtime_panel_ok"]["ok"] is True
    assert checks["browser_runtime_panel_mounted"]["ok"] is True
    assert checks["browser_runtime_panel_read_only"]["ok"] is True
    assert checks["browser_runtime_no_live_execution"]["ok"] is True
    assert checks["workspace_entry_panel_ok"]["ok"] is True
    assert checks["workspace_entry_panel_mounted"]["ok"] is True
    assert checks["workspace_entry_panel_read_only"]["ok"] is True
    assert checks["workspace_entry_categories_present"]["ok"] is True
    assert checks["workspace_entry_no_upgrade_writer"]["ok"] is True
    assert checks["workspace_entry_frontend_mount_present"]["ok"] is True
    assert checks["workspace_entry_frontend_api_binding_present"]["ok"] is True
    assert checks["workspace_entry_frontend_styles_present"]["ok"] is True
    assert checks["settings_panel_ok"]["ok"] is True
    assert checks["settings_panel_mounted"]["ok"] is True
    assert checks["settings_panel_operator_control"]["ok"] is True
    assert checks["settings_provider_config_status_present"]["ok"] is True
    assert checks["settings_runtime_startup_status_present"]["ok"] is True
    assert checks["settings_no_secret_values"]["ok"] is True
    assert checks["settings_runtime_gateway_controls_bounded"]["ok"] is True
    assert checks["settings_frontend_mount_present"]["ok"] is True
    assert checks["settings_frontend_api_binding_present"]["ok"] is True
    assert checks["settings_frontend_styles_present"]["ok"] is True
    assert checks["approval_center_panel_ok"]["ok"] is True
    assert checks["approval_center_panel_mounted"]["ok"] is True
    assert checks["approval_center_panel_read_only"]["ok"] is True
    assert checks["approval_center_required_sources_present"]["ok"] is True
    assert checks["approval_center_no_execution_authority"]["ok"] is True
    assert checks["approval_center_frontend_mount_present"]["ok"] is True
    assert checks["approval_center_frontend_api_binding_present"]["ok"] is True
    assert checks["approval_center_frontend_styles_present"]["ok"] is True
    assert checks["runtime_cockpit_panel_ok"]["ok"] is True
    assert checks["runtime_cockpit_panel_mounted"]["ok"] is True
    assert checks["runtime_cockpit_panel_approval_gated"]["ok"] is True
    assert checks["runtime_cockpit_health_depth_visible"]["ok"] is True
    assert checks["runtime_cockpit_no_execution_authority"]["ok"] is True
    assert checks["runtime_cockpit_frontend_mount_present"]["ok"] is True
    assert checks["runtime_cockpit_frontend_api_binding_present"]["ok"] is True
    assert checks["runtime_cockpit_frontend_styles_present"]["ok"] is True
    assert checks["provenance_explorer_panel_ok"]["ok"] is True
    assert checks["provenance_explorer_panel_mounted"]["ok"] is True
    assert checks["provenance_explorer_panel_read_only"]["ok"] is True
    assert checks["memory_ledger_panel_ok"]["ok"] is True
    assert checks["memory_ledger_panel_mounted"]["ok"] is True
    assert checks["memory_ledger_panel_read_only"]["ok"] is True
    assert checks["agent_identity_panel_ok"]["ok"] is True
    assert checks["agent_identity_panel_mounted"]["ok"] is True
    assert checks["agent_identity_panel_read_only"]["ok"] is True
    assert checks["runtime_navigation_panel_ok"]["ok"] is True
    assert checks["runtime_navigation_panel_mounted"]["ok"] is True
    assert checks["runtime_navigation_panel_read_only"]["ok"] is True
    assert checks["runtime_intelligence_no_writeback_authority"]["ok"] is True
    assert checks["runtime_intelligence_frontend_mounts_present"]["ok"] is True
    assert checks["runtime_intelligence_frontend_api_bindings_present"]["ok"] is True
    assert checks["runtime_intelligence_frontend_styles_present"]["ok"] is True
    assert checks["provenance_api_ok"]["ok"] is True
    assert checks["inspector_provenance_tab_ready"]["ok"] is True
    assert checks["write_surface_not_invoked_in_static_qa"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_workspace_entry_static_runner_validates_panel_without_server_or_upgrade_writer() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="workspace-entry",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "workspace-entry"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-real-desktop-packaging-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["workspace_entry_panel_ok"]["ok"] is True
    assert checks["workspace_entry_panel_mounted"]["ok"] is True
    assert checks["workspace_entry_panel_read_only"]["ok"] is True
    assert checks["workspace_entry_categories_present"]["ok"] is True
    assert checks["workspace_entry_no_upgrade_writer"]["ok"] is True
    assert checks["workspace_entry_frontend_mount_present"]["ok"] is True
    assert checks["workspace_entry_frontend_api_binding_present"]["ok"] is True
    assert checks["workspace_entry_frontend_styles_present"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_settings_static_runner_validates_panel_without_server_or_canonical_mutation() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="settings",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "settings"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-real-desktop-packaging-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["settings_panel_ok"]["ok"] is True
    assert checks["settings_panel_mounted"]["ok"] is True
    assert checks["settings_panel_operator_control"]["ok"] is True
    assert checks["settings_provider_config_status_present"]["ok"] is True
    assert checks["settings_runtime_startup_status_present"]["ok"] is True
    assert checks["settings_no_secret_values"]["ok"] is True
    assert checks["settings_runtime_gateway_controls_bounded"]["ok"] is True
    assert checks["settings_frontend_mount_present"]["ok"] is True
    assert checks["settings_frontend_api_binding_present"]["ok"] is True
    assert checks["settings_frontend_styles_present"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_approval_center_static_runner_validates_panel_without_server_or_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="approval-center",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "approval-center"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["approval_center_panel"]["native_panel_mounted"] is True
    assert report["approval_center_panel"]["approval_execution_available"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-real-desktop-packaging-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["approval_center_panel_ok"]["ok"] is True
    assert checks["approval_center_native_panel_mounted"]["ok"] is True
    assert checks["approval_center_registry_mounted"]["ok"] is True
    assert checks["approval_center_panel_read_only"]["ok"] is True
    assert checks["approval_center_required_sources_present"]["ok"] is True
    assert checks["approval_center_summary_present"]["ok"] is True
    assert checks["approval_center_no_execution_authority"]["ok"] is True
    assert checks["approval_center_no_possible_writes"]["ok"] is True
    assert checks["approval_center_allowed_inspection_only"]["ok"] is True
    assert checks["approval_center_frontend_mount_present"]["ok"] is True
    assert checks["approval_center_frontend_api_binding_present"]["ok"] is True
    assert checks["approval_center_frontend_styles_present"]["ok"] is True
    assert checks["approval_center_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_runtime_cockpit_static_runner_validates_panel_without_server_or_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="runtime-cockpit",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "runtime-cockpit"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["runtime_cockpit_panel"]["native_panel_mounted"] is True
    assert report["runtime_cockpit_panel"]["start_stop_restart_available"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-real-desktop-packaging-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["runtime_cockpit_panel_ok"]["ok"] is True
    assert checks["runtime_cockpit_native_panel_mounted"]["ok"] is True
    assert checks["runtime_cockpit_registry_mounted"]["ok"] is True
    assert checks["runtime_cockpit_panel_approval_gated"]["ok"] is True
    assert checks["runtime_cockpit_health_depth_visible"]["ok"] is True
    assert checks["runtime_cockpit_summary_present"]["ok"] is True
    assert checks["runtime_cockpit_contract_boundary_present"]["ok"] is True
    assert checks["runtime_cockpit_no_execution_authority"]["ok"] is True
    assert checks["runtime_cockpit_possible_writes_approval_request_only"]["ok"] is True
    assert checks["runtime_cockpit_allowed_actions_include_request"]["ok"] is True
    assert checks["runtime_cockpit_action_readiness_present"]["ok"] is True
    assert checks["runtime_cockpit_frontend_mount_present"]["ok"] is True
    assert checks["runtime_cockpit_frontend_api_binding_present"]["ok"] is True
    assert checks["runtime_cockpit_frontend_styles_present"]["ok"] is True
    assert checks["runtime_cockpit_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_runtime_intelligence_static_runner_validates_panels_without_server_or_writeback() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="runtime-intelligence",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "runtime-intelligence"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["runtime_intelligence_panels"]["provenance_explorer_mounted"] is True
    assert report["runtime_intelligence_panels"]["memory_ledger_mounted"] is True
    assert report["runtime_intelligence_panels"]["agent_identity_mounted"] is True
    assert report["runtime_intelligence_panels"]["runtime_navigation_mounted"] is True
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-real-desktop-packaging-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["runtime_intelligence_combined_ok"]["ok"] is True
    assert checks["provenance_explorer_panel_ok"]["ok"] is True
    assert checks["memory_ledger_panel_ok"]["ok"] is True
    assert checks["agent_identity_panel_ok"]["ok"] is True
    assert checks["runtime_navigation_panel_ok"]["ok"] is True
    assert checks["runtime_intelligence_native_panels_mounted"]["ok"] is True
    assert checks["runtime_intelligence_readiness_true"]["ok"] is True
    assert checks["runtime_intelligence_no_writeback_authority"]["ok"] is True
    assert checks["provenance_explorer_sidecar_only"]["ok"] is True
    assert checks["memory_ledger_approval_blocked"]["ok"] is True
    assert checks["agent_identity_policy_mutation_blocked"]["ok"] is True
    assert checks["runtime_navigation_writeback_blocked"]["ok"] is True
    assert checks["runtime_intelligence_frontend_mounts_present"]["ok"] is True
    assert checks["runtime_intelligence_frontend_api_bindings_present"]["ok"] is True
    assert checks["runtime_intelligence_frontend_styles_present"]["ok"] is True
    assert checks["runtime_intelligence_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_packaging_static_runner_validates_readiness_without_building() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="packaging",
        mode="static",
        timeout_seconds=2,
    )

    # installer_plan_ok is blocked until packaged exe + launch smoke + visual QA are present.
    # Static test mode cannot produce those artifacts, so ok=False is correct here.
    assert report["qa_surface"] == "packaging"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["packaging_readiness"]["local_packaging_proof_run"] is False
    assert report["packaging_readiness"]["installer_built"] is False
    # installer_plan_status is "blocked_installer_plan" until packaged exe evidence exists
    assert report["packaging_readiness"]["installer_plan_status"] in (
        "ready_for_governed_installer_design",
        "blocked_installer_plan",
    )
    assert report["next_recommended_pass"] == "phase10-studio-product-hardening"
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["packaging_readiness_ok"]["ok"] is True
    assert checks["packaging_native_shell_primary"]["ok"] is True
    assert checks["packaging_legacy_harness_secondary"]["ok"] is True
    assert checks["packaging_shell_entry_exists"]["ok"] is True
    assert checks["packaging_studio_api_exists"]["ok"] is True
    assert checks["packaging_frontend_assets_local"]["ok"] is True
    assert checks["packaging_frontend_package_data_declared"]["ok"] is True
    assert checks["packaging_pywebview_dependency_declared"]["ok"] is True
    assert checks["packaging_pyinstaller_dependency_declared"]["ok"] is True
    assert checks["packaging_spec_available"]["ok"] is True
    assert checks["packaging_meipass_frontend_resolution"]["ok"] is True
    assert checks["packaging_no_build_executed"]["ok"] is True
    assert checks["packaging_no_mutation_authority"]["ok"] is True
    # installer_plan_ok may be blocked in static mode when packaging artifacts are absent
    assert checks["installer_plan_ok"]["ok"] in (True, False)
    assert checks["installer_plan_requires_visual_qa"]["ok"] in (True, False)
    assert checks["installer_plan_governance_gates_present"]["ok"] is True
    assert checks["installer_plan_no_mutation_authority"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_product_hardening_static_runner_validates_release_boundary_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="product-hardening",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "product-hardening"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["product_hardening"]["browser_runtime_production_complete"] is True
    assert report["product_hardening"]["installer_governance_ready"] is True
    assert report["product_hardening"]["release_governance_deferred"] is True
    assert report["product_hardening"]["blockers"] == []
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["browser_use_cli_live_run"] is False
    assert report["authority"]["excalidraw_live_proof"] is False
    assert report["next_recommended_pass"] == "studio-release-readiness-governance"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["product_hardening_status_ok"]["ok"] is True
    assert checks["product_hardening_native_shell_primary"]["ok"] is True
    assert checks["product_hardening_panel_registry_ready"]["ok"] is True
    assert checks["product_hardening_browser_runtime_complete"]["ok"] is True
    assert checks["product_hardening_packaging_ready"]["ok"] is True
    assert checks["product_hardening_installer_governance_ready"]["ok"] is True
    assert checks["product_hardening_required_evidence_present"]["ok"] is True
    assert checks["product_hardening_release_governance_deferred"]["ok"] is True
    assert checks["product_hardening_no_mutation_authority"]["ok"] is True
    assert checks["product_hardening_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_release_governance_static_runner_validates_gate_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="release-governance",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "release-governance"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["release_governance"]["product_hardening_ready"] is True
    assert report["release_governance"]["installer_plan_ready"] is True
    assert report["release_governance"]["all_required_gates_declared"] is True
    assert report["release_governance"]["release_actions_allowed"] is False
    assert report["release_governance"]["blockers"] == []
    assert report["authority"]["creates_approval_artifact"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-governed-installer-build-approval"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["release_governance_status_ok"]["ok"] is True
    assert checks["release_governance_product_hardening_ready"]["ok"] is True
    assert checks["release_governance_installer_plan_ready"]["ok"] is True
    assert checks["release_governance_required_gates_present"]["ok"] is True
    assert checks["release_governance_operator_approval_required"]["ok"] is True
    assert checks["release_governance_dry_run_exact_once_rollback_required"]["ok"] is True
    assert checks["release_governance_release_actions_blocked"]["ok"] is True
    assert checks["release_governance_no_mutation_authority"]["ok"] is True
    assert checks["release_governance_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_installer_build_approval_static_runner_validates_preview_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="installer-build-approval",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "installer-build-approval"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    approval = report["installer_build_approval"]
    if _blocked_current_repo_state(approval):
        assert approval["execution_allowed"] is False
        assert approval["installer_build_allowed"] is False
        return
    assert approval["approval_packet_preview_ready"] is True
    approval_complete = approval.get("approved_execution_proof_complete") is True
    assert approval["approval_decision_consumed"] is approval_complete
    assert approval["execution_allowed"] is False
    assert approval["installer_build_allowed"] is False
    assert approval["blockers"] == []
    assert report["authority"]["creates_approval_artifact"] is False
    assert report["authority"]["writes_approval_artifact"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    expected_next = (
        "studio-signing-approval-preview"
        if approval_complete
        else
        "studio-installer-build-approval-consumption-dry-run"
        if approval["approval_artifact_written"]
        else "operator-review-studio-installer-build-approval-packet"
    )
    assert report["next_recommended_pass"] == expected_next
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["installer_build_approval_status_ok"]["ok"] is True
    assert checks["installer_build_approval_release_governance_ready"]["ok"] is True
    assert checks["installer_build_approval_gate_declared"]["ok"] is True
    assert checks["installer_build_approval_packet_preview_present"]["ok"] is True
    assert checks["installer_build_approval_artifact_absent_or_matching"]["ok"] is True
    assert checks["installer_build_approval_marker_absent"]["ok"] is True
    assert checks["installer_build_approval_future_output_paths_clear"]["ok"] is True
    assert checks["installer_build_approval_dry_run_plan_present"]["ok"] is True
    assert checks["installer_build_approval_rollback_audit_present"]["ok"] is True
    assert checks["installer_build_approval_execution_blocked"]["ok"] is True
    assert checks["installer_build_approval_no_mutation_authority"]["ok"] is True
    assert checks["installer_build_approval_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_installer_build_approval_review_static_runner_validates_review_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="installer-build-approval-review",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "installer-build-approval-review"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    review = report["installer_build_approval_review"]
    if _blocked_current_repo_state(review):
        assert review["execution_allowed"] is False
        assert review["installer_build_allowed"] is False
        return
    assert review["approval_artifact_ready"] is True
    review_complete = review.get("approved_execution_proof_complete") is True
    assert review["approval_decision_consumed"] is review_complete
    assert review["execution_allowed"] is False
    assert review["installer_build_allowed"] is False
    assert review["blockers"] == []
    assert report["authority"]["writes_approval_artifact"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["installer_build_approval_review_status_ok"]["ok"] is True
    assert checks["installer_build_approval_review_packet_matches"]["ok"] is True
    assert checks["installer_build_approval_review_artifact_ready_or_present"]["ok"] is True
    assert checks["installer_build_approval_review_marker_absent"]["ok"] is True
    assert checks["installer_build_approval_review_future_output_paths_clear"]["ok"] is True
    assert checks["installer_build_approval_review_execution_blocked"]["ok"] is True
    assert checks["installer_build_approval_review_no_runtime_mutation_authority"]["ok"] is True
    assert checks["installer_build_approval_review_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_installer_build_approval_consumption_static_runner_validates_dry_run_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="installer-build-approval-consumption-dry-run",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "installer-build-approval-consumption-dry-run"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    consumption = report["installer_build_approval_consumption_dry_run"]
    if _blocked_current_repo_state(consumption):
        assert consumption["execution_allowed"] is False
        assert consumption["installer_build_allowed"] is False
        return
    consumption_complete = consumption.get("approved_execution_proof_complete") is True
    assert consumption["approval_artifact_present"] is True
    assert consumption["approval_digest_matches"] is True
    assert consumption["approval_scope_valid"] is True
    assert consumption["approval_consumed"] is consumption_complete
    assert consumption["exact_once_marker_absent"] is (not consumption_complete)
    assert consumption["exact_once_marker_reserved"] is consumption_complete
    assert consumption["marker_reservation_proof_passed"] is True
    assert consumption["duplicate_consumption_blocked"] is True
    assert consumption["execution_allowed"] is False
    assert consumption["installer_build_allowed"] is False
    assert consumption["blockers"] == []
    assert report["authority"]["writes_approval_artifact"] is False
    assert report["authority"]["consumes_approval_decision"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == (
        "studio-signing-approval-preview"
        if consumption_complete
        else "studio-installer-build-approved-execution-proof"
    )
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["installer_build_approval_consumption_status_ok"]["ok"] is True
    assert checks["installer_build_approval_consumption_artifact_present"]["ok"] is True
    assert checks["installer_build_approval_consumption_digest_matches"]["ok"] is True
    assert checks["installer_build_approval_consumption_scope_valid"]["ok"] is True
    assert checks["installer_build_approval_consumption_marker_absent"]["ok"] is True
    assert checks["installer_build_approval_consumption_marker_reservation_proof_passed"]["ok"] is True
    assert checks["installer_build_approval_consumption_duplicate_blocked"]["ok"] is True
    assert checks["installer_build_approval_consumption_future_output_paths_clear"]["ok"] is True
    assert checks["installer_build_approval_consumption_execution_blocked"]["ok"] is True
    assert checks["installer_build_approval_consumption_no_runtime_mutation_authority"]["ok"] is True
    assert checks["installer_build_approval_consumption_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_installer_build_approved_execution_proof_static_runner_inspects_state_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="installer-build-approved-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "installer-build-approved-execution-proof"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    proof = report["installer_build_approved_execution_proof"]
    assert proof["execution_requested"] is False
    if _blocked_current_repo_state(proof):
        assert report["authority"]["writes_installer"] is False
        return
    assert proof["blockers"] == []
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["writes_packaging_output_root"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["installer_build_approved_execution_proof_status_ok"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_ready_or_complete"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_approval_valid"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_source_exe_valid"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_paths_scoped"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_complete_outputs_valid"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_signing_startup_release_blocked"]["ok"] is True
    assert checks["installer_build_approved_execution_proof_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_signing_approval_preview_static_runner_inspects_state_without_signing() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="signing-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "signing-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    preview = report["signing_approval_preview"]
    assert preview["signing_approval_packet_id"].startswith("studio-signing-appr-")
    if _blocked_current_repo_state(preview):
        assert preview["signing_allowed"] is False
        assert preview["signing_certificate_read"] is False
        return
    signing_complete = bool(preview.get("signing_execution_proof_complete"))
    assert preview["signing_allowed"] is False
    assert preview["signing_certificate_read"] is False
    assert preview["signed_artifact_written"] is signing_complete
    assert preview["blockers"] == []
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    expected_next = (
        "studio-startup-autostart-approval-preview"
        if signing_complete
        else "studio-signing-approval-consumption-dry-run"
        if preview["approval_artifact_written"]
        else "operator-review-studio-signing-approval-packet"
    )
    assert report["next_recommended_pass"] == expected_next
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["signing_approval_preview_status_ok"]["ok"] is True
    assert checks["signing_approval_preview_installer_execution_complete"]["ok"] is True
    assert checks["signing_approval_preview_marker_complete"]["ok"] is True
    assert checks["signing_approval_preview_zip_present"]["ok"] is True
    assert checks["signing_approval_preview_manifest_present"]["ok"] is True
    assert checks["signing_approval_preview_future_paths_clear"]["ok"] is True
    assert checks["signing_approval_preview_certificate_not_read"]["ok"] is True
    assert checks["signing_approval_preview_execution_blocked"]["ok"] is True
    assert checks["signing_approval_preview_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_signing_approval_review_static_runner_inspects_state_without_signing_or_marker_write() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="signing-approval-review",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "signing-approval-review"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    review = report["signing_approval_review"]
    signing_complete = bool(review.get("signing_execution_proof_complete"))
    assert review["approval_packet_id"].startswith("studio-signing-appr-")
    if _blocked_current_repo_state(review):
        assert review["signing_allowed"] is False
        assert review["signing_certificate_read"] is False
        return
    assert review["approval_artifact_ready"] is True
    assert review["approval_decision_consumed"] is signing_complete
    assert review["signing_allowed"] is False
    assert review["signing_certificate_read"] is False
    assert review["signed_artifact_written"] is signing_complete
    assert review["blockers"] == []
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    expected_next = (
        "studio-startup-autostart-approval-preview"
        if signing_complete
        else "studio-signing-approval-consumption-dry-run"
        if review["approval_artifact_written"]
        else "operator-review-studio-signing-approval-packet"
    )
    assert report["next_recommended_pass"] == expected_next
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["signing_approval_review_status_ok"]["ok"] is True
    assert checks["signing_approval_review_packet_matches"]["ok"] is True
    assert checks["signing_approval_review_artifact_ready_or_present"]["ok"] is True
    assert checks["signing_approval_review_marker_absent"]["ok"] is True
    assert checks["signing_approval_review_future_output_paths_clear"]["ok"] is True
    assert checks["signing_approval_review_execution_blocked"]["ok"] is True
    assert checks["signing_approval_review_no_runtime_mutation_authority"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_signing_approval_consumption_static_runner_validates_dry_run_without_signing() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="signing-approval-consumption-dry-run",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "signing-approval-consumption-dry-run"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    consumption = report["signing_approval_consumption_dry_run"]
    signing_complete = bool(consumption.get("signing_execution_proof_complete"))
    if _blocked_current_repo_state(consumption):
        assert consumption["signing_allowed"] is False
        assert consumption["signing_certificate_read"] is False
        return
    assert consumption["approval_artifact_present"] is True
    assert consumption["approval_digest_matches"] is True
    assert consumption["approval_scope_valid"] is True
    assert consumption["unsigned_portable_zip_hash_matches"] is True
    assert consumption["installer_manifest_hash_matches"] is True
    assert consumption["approval_consumed"] is signing_complete
    assert consumption["exact_once_marker_absent"] is (not signing_complete)
    assert consumption["exact_once_marker_reserved"] is signing_complete
    assert consumption["marker_reservation_proof_passed"] is True
    assert consumption["duplicate_consumption_blocked"] is True
    assert consumption["signing_allowed"] is False
    assert consumption["signing_certificate_read"] is False
    assert consumption["signed_artifact_written"] is signing_complete
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == (
        "studio-startup-autostart-approval-preview"
        if signing_complete
        else "studio-signing-approved-execution-proof"
    )
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["signing_approval_consumption_status_ok"]["ok"] is True
    assert checks["signing_approval_consumption_artifact_present"]["ok"] is True
    assert checks["signing_approval_consumption_digest_matches"]["ok"] is True
    assert checks["signing_approval_consumption_scope_valid"]["ok"] is True
    assert checks["signing_approval_consumption_source_hashes_match"]["ok"] is True
    assert checks["signing_approval_consumption_marker_absent"]["ok"] is True
    assert checks["signing_approval_consumption_marker_reservation_proof_passed"]["ok"] is True
    assert checks["signing_approval_consumption_duplicate_blocked"]["ok"] is True
    assert checks["signing_approval_consumption_future_output_paths_clear"]["ok"] is True
    assert checks["signing_approval_consumption_certificate_not_read"]["ok"] is True
    assert checks["signing_approval_consumption_execution_blocked"]["ok"] is True
    assert checks["signing_approval_consumption_no_runtime_mutation_authority"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_signing_approved_execution_proof_static_runner_inspects_state_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="signing-approved-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "signing-approved-execution-proof"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    proof = report["signing_approved_execution_proof"]
    assert proof["execution_requested"] is False
    if _blocked_current_repo_state(proof):
        assert report["authority"]["writes_signed_artifact"] is False
        return
    assert proof["blockers"] == []
    assert proof["approval_packet_id"].startswith("studio-signing-appr-")
    assert proof["certificate_reference_resolved"] is True
    assert proof["signing_certificate_read"] is False
    assert proof["production_code_signature_applied"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["signing_approved_execution_proof_status_ok"]["ok"] is True
    assert checks["signing_approved_execution_proof_ready_or_complete"]["ok"] is True
    assert checks["signing_approved_execution_proof_approval_valid"]["ok"] is True
    assert checks["signing_approved_execution_proof_source_artifacts_valid"]["ok"] is True
    assert checks["signing_approved_execution_proof_certificate_reference_safe"]["ok"] is True
    assert checks["signing_approved_execution_proof_paths_scoped"]["ok"] is True
    assert checks["signing_approved_execution_proof_complete_outputs_valid"]["ok"] is True
    assert checks["signing_approved_execution_proof_secret_startup_release_blocked"]["ok"] is True
    assert checks["signing_approved_execution_proof_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_startup_autostart_approval_preview_static_runner_inspects_state_without_host_mutation() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="startup-autostart-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "startup-autostart-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    preview = report["startup_autostart_approval_preview"]
    assert preview["startup_autostart_approval_packet_id"].startswith("studio-startup-autostart-appr-")
    assert preview["signing_approval_packet_id"].startswith("studio-signing-appr-")
    startup_execution_complete = preview.get("startup_autostart_execution_proof_complete") is True
    assert preview["approval_decision_consumed"] is startup_execution_complete
    assert preview["host_path_resolution_attempted"] is False
    assert preview["host_startup_mutation_allowed"] is False
    assert preview["autostart_registration_allowed"] is False
    assert preview["registry_write_allowed"] is False
    assert preview["start_menu_write_allowed"] is False
    assert preview["desktop_shortcut_write_allowed"] is False
    assert preview["release_promotion_allowed"] is False
    if _blocked_current_repo_state(preview):
        return
    assert preview["blockers"] == []
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["registers_autostart"] is False
    assert report["authority"]["writes_registry"] is False
    assert report["authority"]["writes_start_menu"] is False
    assert report["authority"]["writes_desktop_shortcut"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] in {
        "operator-review-studio-startup-autostart-approval-packet",
        "studio-startup-autostart-approval-consumption-dry-run",
        "studio-release-promotion-approval-preview",
    }
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["startup_autostart_approval_preview_status_ok"]["ok"] is True
    assert checks["startup_autostart_approval_preview_ready_or_pending"]["ok"] is True
    assert checks["startup_autostart_approval_preview_signing_complete"]["ok"] is True
    assert checks["startup_autostart_approval_preview_signed_artifacts_valid"]["ok"] is True
    assert checks["startup_autostart_approval_preview_approval_artifact_absent_or_matching"]["ok"] is True
    assert checks["startup_autostart_approval_preview_marker_absent"]["ok"] is True
    assert checks["startup_autostart_approval_preview_future_paths_clear"]["ok"] is True
    assert checks["startup_autostart_approval_preview_host_paths_not_resolved"]["ok"] is True
    assert checks["startup_autostart_approval_preview_host_mutation_blocked"]["ok"] is True
    assert checks["startup_autostart_approval_preview_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_startup_autostart_approval_review_static_runner_inspects_state_without_host_mutation() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="startup-autostart-approval-review",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "startup-autostart-approval-review"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["visual_browser_qa_complete"] is False
    assert report["writes_performed"] is False
    review = report["startup_autostart_approval_review"]
    assert review["approval_packet_id"].startswith("studio-startup-autostart-appr-")
    if _blocked_current_repo_state(review):
        assert review["host_startup_mutation_allowed"] is False
        return
    assert review["approval_artifact_ready"] is True
    startup_execution_complete = review.get("startup_autostart_execution_proof_complete") is True
    assert review["approval_decision_consumed"] is startup_execution_complete
    assert review["host_path_resolution_attempted"] is False
    assert review["host_startup_mutation_allowed"] is False
    assert review["autostart_registration_allowed"] is False
    assert review["registry_write_allowed"] is False
    assert review["start_menu_write_allowed"] is False
    assert review["desktop_shortcut_write_allowed"] is False
    assert review["release_promotion_allowed"] is False
    assert review["blockers"] == []
    assert report["authority"]["resolves_host_startup_paths"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["registers_autostart"] is False
    assert report["authority"]["writes_registry"] is False
    assert report["authority"]["writes_start_menu"] is False
    assert report["authority"]["writes_desktop_shortcut"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False

    checks = {item["name"]: item for item in report["checks"]}
    assert checks["startup_autostart_approval_review_status_ok"]["ok"] is True
    assert checks["startup_autostart_approval_review_ready_or_existing"]["ok"] is True
    assert checks["startup_autostart_approval_review_packet_matches"]["ok"] is True
    assert checks["startup_autostart_approval_review_artifact_ready_or_present"]["ok"] is True
    assert checks["startup_autostart_approval_review_marker_absent"]["ok"] is True
    assert checks["startup_autostart_approval_review_future_paths_clear"]["ok"] is True
    assert checks["startup_autostart_approval_review_signing_complete"]["ok"] is True
    assert checks["startup_autostart_approval_review_host_paths_not_resolved"]["ok"] is True
    assert checks["startup_autostart_approval_review_host_mutation_blocked"]["ok"] is True
    assert checks["startup_autostart_approval_review_execution_blocked"]["ok"] is True
    assert checks["startup_autostart_approval_review_no_runtime_mutation_authority"]["ok"] is True
    assert checks["startup_autostart_approval_review_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_startup_autostart_approval_consumption_static_runner_validates_dry_run_without_host_mutation() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="startup-autostart-approval-consumption-dry-run",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["server"]["started"] is False
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    consumption = report["startup_autostart_approval_consumption_dry_run"]
    if _blocked_current_repo_state(consumption):
        assert consumption["host_startup_mutation_allowed"] is False
        return
    assert consumption["approval_artifact_present"] is True
    assert consumption["approval_digest_matches"] is True
    assert consumption["approval_scope_valid"] is True
    assert consumption["signed_portable_zip_hash_matches"] is True
    assert consumption["signing_manifest_hash_matches"] is True
    startup_execution_complete = consumption.get("startup_autostart_execution_proof_complete") is True
    assert consumption["approval_consumed"] is startup_execution_complete
    assert consumption["exact_once_marker_absent"] is True
    assert consumption["exact_once_marker_reserved"] is startup_execution_complete
    assert consumption["marker_reservation_proof_passed"] is True
    assert consumption["duplicate_consumption_blocked"] is True
    assert consumption["host_path_resolution_attempted"] is False
    assert consumption["host_startup_mutation_allowed"] is False
    assert consumption["autostart_registration_allowed"] is False
    assert consumption["registry_write_allowed"] is False
    assert consumption["start_menu_write_allowed"] is False
    assert consumption["desktop_shortcut_write_allowed"] is False
    assert consumption["release_promotion_allowed"] is False
    assert report["next_recommended_pass"] == (
        "studio-release-promotion-approval-preview"
        if startup_execution_complete
        else "studio-startup-autostart-approved-execution-proof"
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert checks["startup_autostart_approval_consumption_status_ok"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_artifact_present"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_digest_matches"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_scope_valid"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_source_hashes_match"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_marker_absent"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_marker_reservation_proof_passed"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_duplicate_blocked"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_future_output_paths_clear"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_host_paths_not_resolved"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_host_mutation_blocked"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_execution_blocked"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_no_runtime_mutation_authority"]["ok"] is True
    assert checks["startup_autostart_approval_consumption_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_startup_autostart_approved_execution_proof_static_runner_inspects_state_without_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="startup-autostart-approved-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "startup-autostart-approved-execution-proof"
    assert report["server"]["started"] is False
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    proof = report["startup_autostart_approved_execution_proof"]
    assert proof["approval_packet_id"].startswith("studio-startup-autostart-appr-")
    assert proof["execution_requested"] is False
    if _blocked_current_repo_state(proof):
        assert proof["host_mutation_performed"] is False
        return
    assert proof["blockers"] == []
    assert proof["host_path_resolution_attempted"] is False
    assert proof["host_mutation_performed"] is False
    assert proof["release_promotion_allowed"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["writes_startup_autostart_audit"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["writes_registry"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] in {
        "run-with---execute",
        "studio-release-promotion-approval-preview",
    }

    checks = {item["name"]: item for item in report["checks"]}
    assert checks["startup_autostart_approved_execution_proof_status_ok"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_ready_or_complete"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_approval_valid"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_source_artifacts_valid"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_paths_scoped"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_complete_outputs_valid"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_no_host_mutation"]["ok"] is True
    assert checks["startup_autostart_approved_execution_proof_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_release_promotion_approval_preview_static_runner_inspects_state_without_release_write() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="release-promotion-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "release-promotion-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    preview = report["release_promotion_approval_preview"]
    assert preview["release_promotion_approval_packet_id"].startswith("studio-release-promotion-appr-")
    assert preview["startup_approval_packet_id"].startswith("studio-startup-autostart-appr-")
    release_execution_complete = preview.get("release_promotion_execution_proof_complete") is True
    assert preview["approval_decision_consumed"] is release_execution_complete
    assert preview["release_status_write_allowed"] is False
    assert preview["release_promotion_allowed"] is False
    assert preview["host_path_resolution_attempted"] is False
    assert preview["host_mutation_performed"] is False
    if _blocked_current_repo_state(preview):
        return
    assert preview["blockers"] == []
    assert report["authority"]["writes_release_status"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] in {
        "operator-review-studio-release-promotion-approval-packet",
        "studio-release-promotion-approval-consumption-dry-run",
        "browser-runtime-production-closeout",
    }

    checks = {item["name"]: item for item in report["checks"]}
    assert checks["release_promotion_approval_preview_status_ok"]["ok"] is True
    assert checks["release_promotion_approval_preview_ready_or_pending"]["ok"] is True
    assert checks["release_promotion_approval_preview_startup_proof_complete"]["ok"] is True
    assert checks["release_promotion_approval_preview_startup_marker_complete"]["ok"] is True
    assert checks["release_promotion_approval_preview_signed_artifacts_valid"]["ok"] is True
    assert checks["release_promotion_approval_preview_startup_evidence_valid"]["ok"] is True
    assert checks["release_promotion_approval_preview_startup_no_host_or_release_mutation"]["ok"] is True
    assert checks["release_promotion_approval_preview_approval_artifact_absent_or_matching"]["ok"] is True
    assert checks["release_promotion_approval_preview_marker_absent"]["ok"] is True
    assert checks["release_promotion_approval_preview_future_paths_clear"]["ok"] is True
    assert checks["release_promotion_approval_preview_release_status_write_blocked"]["ok"] is True
    assert checks["release_promotion_approval_preview_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_release_promotion_approval_review_static_runner_inspects_state_without_release_write() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="release-promotion-approval-review",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "release-promotion-approval-review"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    review = report["release_promotion_approval_review"]
    assert review["approval_packet_id"].startswith("studio-release-promotion-appr-")
    if _blocked_current_repo_state(review):
        assert review["release_status_write_allowed"] is False
        assert review["release_promotion_allowed"] is False
        return
    assert review["approval_artifact_ready"] is True
    assert review["release_status_write_allowed"] is False
    assert review["release_promotion_allowed"] is False
    assert review["host_path_resolution_attempted"] is False
    assert review["host_mutation_performed"] is False
    assert review["blockers"] == []
    assert report["authority"]["writes_release_status"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] in {
        "operator-review-studio-release-promotion-approval-packet",
        "studio-release-promotion-approval-consumption-dry-run",
        "browser-runtime-production-closeout",
    }

    checks = {item["name"]: item for item in report["checks"]}
    assert checks["release_promotion_approval_review_status_ok"]["ok"] is True
    assert checks["release_promotion_approval_review_ready_or_existing"]["ok"] is True
    assert checks["release_promotion_approval_review_packet_matches"]["ok"] is True
    assert checks["release_promotion_approval_review_artifact_ready_or_present"]["ok"] is True
    assert checks["release_promotion_approval_review_marker_absent"]["ok"] is True
    assert checks["release_promotion_approval_review_future_paths_clear"]["ok"] is True
    assert checks["release_promotion_approval_review_source_artifacts_valid"]["ok"] is True
    assert checks["release_promotion_approval_review_startup_no_host_or_release_mutation"]["ok"] is True
    assert checks["release_promotion_approval_review_release_status_write_blocked"]["ok"] is True
    assert checks["release_promotion_approval_review_execution_blocked"]["ok"] is True
    assert checks["release_promotion_approval_review_no_runtime_mutation_authority"]["ok"] is True
    assert checks["release_promotion_approval_review_static_qa_no_execution"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_browser_runtime_static_runner_validates_panel_without_server_or_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="browser-runtime",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "browser-runtime"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["visual_browser_qa_complete"] is False
    assert report["browser_runtime_panel"]["native_panel_mounted"] is True
    assert report["browser_runtime_panel"]["browser_use_cli_live_run"] is False
    assert report["browser_runtime_panel"]["excalidraw_live_proof"] is False
    assert report["authority"]["browser_use_cli_live_run"] is False
    assert report["authority"]["excalidraw_live_proof"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "studio-browser-runtime-panel-browser-qa"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["browser_runtime_panel_ok"]["ok"] is True
    assert checks["browser_runtime_native_panel_mounted"]["ok"] is True
    assert checks["browser_runtime_registry_mounted"]["ok"] is True
    assert checks["browser_runtime_panel_read_only"]["ok"] is True
    assert checks["browser_runtime_required_sections_present"]["ok"] is True
    assert checks["browser_runtime_summary_present"]["ok"] is True
    assert checks["browser_runtime_evidence_paths_present"]["ok"] is True
    assert checks["browser_runtime_no_live_execution"]["ok"] is True
    assert checks["browser_runtime_no_possible_writes"]["ok"] is True
    assert checks["browser_runtime_allowed_inspection_only"]["ok"] is True
    assert checks["browser_runtime_forbidden_effects_exposed"]["ok"] is True
    assert checks["browser_runtime_frontend_mount_present"]["ok"] is True
    assert checks["browser_runtime_frontend_api_binding_present"]["ok"] is True
    assert checks["browser_runtime_frontend_styles_present"]["ok"] is True
    assert checks["browser_runtime_static_qa_no_browser"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_graph_visual_overlays_static_runner_validates_overlays_without_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="graph-visual-overlays",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "graph-visual-overlays"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    overlays = report["graph_visual_overlays"]
    assert overlays["typed_graph_trust_overlays_ready"] is True
    assert overlays["node_family_count"] == 14
    assert overlays["edge_layer_count"] == 4
    assert overlays["trust_state_count"] == 8
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["graph_visual_overlays_status_ok"]["ok"] is True
    assert checks["graph_visual_overlays_all_14_families"]["ok"] is True
    assert checks["graph_visual_overlays_all_4_edge_layers"]["ok"] is True
    assert checks["graph_visual_overlays_all_8_trust_states"]["ok"] is True
    assert checks["graph_visual_overlays_frontend_rendering_present"]["ok"] is True
    assert checks["graph_visual_overlays_static_renderer_uses_overlays"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_graph_provenance_inspector_static_runner_validates_chain_without_writes() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="graph-provenance-inspector",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "graph-provenance-inspector"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    inspector = report["graph_provenance_inspector"]
    assert inspector["graph_node_resolved"] is True
    assert inspector["provenance_status"] in {"present", "missing", "malformed"}
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["graph_provenance_inspector_status_ok"]["ok"] is True
    assert checks["graph_provenance_chain_sections_present"]["ok"] is True
    assert checks["graph_provenance_shell_api_exposes_surface"]["ok"] is True
    assert checks["graph_provenance_registry_mounted"]["ok"] is True
    assert checks["graph_provenance_frontend_hydration_present"]["ok"] is True
    assert checks["graph_provenance_no_write_authority"]["ok"] is True
    assert checks["no_markdown_writes"]["ok"] is True
    assert checks["no_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_conversation_persistence_static_runner_validates_no_write_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-conversation-persistence-contract",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-conversation-persistence-contract"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["native_shell"]["pywebview_window_launched"] is False
    assert report["legacy_localhost_harness"]["used"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["conversation_persistence_allowed"] is False
    assert report["authority"]["approval_queue_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-approval-queue-write-execution-proof"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_conversation_contract_status_ok"]["ok"] is True
    assert checks["conversation_target_under_logs"]["ok"] is True
    assert checks["conversation_preview_ready_but_write_blocked"]["ok"] is True
    assert checks["conversation_history_not_canonical_memory"]["ok"] is True
    assert checks["conversation_log_not_written"]["ok"] is True
    assert checks["conversation_approval_packet_not_written"]["ok"] is True
    assert checks["prompt_injection_blocks_preview"]["ok"] is True
    assert checks["authority_readonly"]["ok"] is True
    assert checks["registry_exposes_conversation_contract"]["ok"] is True
    assert checks["api_exposes_conversation_contract"]["ok"] is True
    assert checks["frontend_tokens_present"]["ok"] is True
    assert checks["static_qa_no_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_approval_queue_write_static_runner_validates_bounded_write_proof() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-approval-queue-write-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-approval-queue-write-execution-proof"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_queue_write_allowed_with_digest"] is True
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-browser-dispatch-readiness-contract"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_queue_write_preview_ok"]["ok"] is True
    assert checks["write_requires_expected_digest"]["ok"] is True
    assert checks["temp_queue_write_creates_pending_approval"]["ok"] is True
    assert checks["duplicate_digest_returns_existing_request"]["ok"] is True
    assert checks["target_file_not_written"]["ok"] is True
    assert checks["chat_approval_execution_blocked"]["ok"] is True
    assert checks["approval_center_sees_chat_originated_request"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_live_provider_execution_approval_preview_static_runner_validates_no_call_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-live-provider-execution-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-live-provider-execution-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["approval_queue_write_allowed"] is False
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-browser-dispatch-readiness-contract"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_live_provider_preview_ok"]["ok"] is True
    assert checks["phase11_live_provider_pass_id"]["ok"] is True
    assert checks["request_digest_present"]["ok"] is True
    assert checks["future_approval_preview_no_write"]["ok"] is True
    assert checks["provider_call_blocked"]["ok"] is True
    assert checks["non_model_intent_blocks"]["ok"] is True
    assert checks["prompt_injection_blocks_provider_preview"]["ok"] is True
    assert checks["credentials_not_exposed"]["ok"] is True
    assert checks["conversation_audit_preview_only"]["ok"] is True
    assert checks["registry_exposes_live_provider_preview"]["ok"] is True
    assert checks["api_exposes_live_provider_preview"]["ok"] is True
    assert checks["frontend_tokens_present"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_markdown_snapshot_uses_bounded_file_aware_live_truth_zone_sentinel(tmp_path: Path) -> None:
    (tmp_path / "01_PROJECTS").mkdir()
    (tmp_path / "02_KNOWLEDGE").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "runtime" / "state").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Studio-Graph-Views").mkdir(parents=True)
    (tmp_path / "00_HOME").mkdir()
    (tmp_path / "00_HOME" / "Now.md").write_text("now\n", encoding="utf-8")
    fact_path = tmp_path / "02_KNOWLEDGE" / "fact.md"
    fact_path.write_text("alpha\n", encoding="utf-8")
    (tmp_path / "runtime" / "state" / "COMMAND-CONTRACT-README.md").write_text("source/runtime doc\n", encoding="utf-8")
    (tmp_path / "07_LOGS" / "Studio-Graph-Views" / "proof.md").write_text("generated proof\n", encoding="utf-8")

    before = qa_runner._markdown_snapshot(tmp_path)
    fact_path.write_text("bravo\n", encoding="utf-8")
    after = qa_runner._markdown_snapshot(tmp_path)

    assert "00_HOME/Now.md" not in before  # excluded by design: written by concurrent operator sessions
    assert "01_PROJECTS" in before
    assert "02_KNOWLEDGE" in before
    assert "06_AGENTS" in before
    assert "02_KNOWLEDGE/fact.md" in before
    assert before["02_KNOWLEDGE/fact.md"] != after["02_KNOWLEDGE/fact.md"]
    assert before != after
    assert "runtime/state/COMMAND-CONTRACT-README.md" not in before
    assert "07_LOGS/Studio-Graph-Views/proof.md" not in before


def test_phase11_chat_runtime_dispatch_readiness_static_runner_validates_no_dispatch_contract(monkeypatch) -> None:
    def fail_broad_markdown_snapshot(_vault):
        raise AssertionError("Phase 11 Chat static QA must use bounded forbidden-write snapshots, not full-vault markdown scans")

    monkeypatch.setattr(qa_runner, "_markdown_snapshot", fail_broad_markdown_snapshot)

    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-runtime-dispatch-readiness-contract",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-runtime-dispatch-readiness-contract"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["workflow_execution_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-browser-dispatch-readiness-contract"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_runtime_dispatch_preview_ok"]["ok"] is True
    assert checks["phase11_runtime_dispatch_pass_id"]["ok"] is True
    assert checks["runtime_dispatch_digest_present"]["ok"] is True
    assert checks["runtime_capabilities_loaded"]["ok"] is True
    assert checks["agent_bus_readiness_no_task_write"]["ok"] is True
    assert checks["aor_workflow_readiness_no_dispatch"]["ok"] is True
    assert checks["future_dispatch_preview_no_write"]["ok"] is True
    assert checks["non_runtime_intent_blocks"]["ok"] is True
    assert checks["prompt_injection_blocks_runtime_dispatch"]["ok"] is True
    assert checks["registry_exposes_runtime_dispatch_readiness"]["ok"] is True
    assert checks["api_exposes_runtime_dispatch_readiness"]["ok"] is True
    assert checks["frontend_tokens_present"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_runtime_dispatch_executor_static_runner_validates_approval_gated_task_enqueue() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-runtime-dispatch-executor",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-runtime-dispatch-executor"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["runtime_dispatch_enqueue_allowed"] is True
    assert report["authority"]["agent_bus_task_write_allowed"] is True
    assert report["authority"]["runtime_task_claim_allowed"] is False
    assert report["authority"]["workflow_execution_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-select-next-governed-executor-lane"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_runtime_dispatch_executor_ok"]["ok"] is True
    assert checks["phase11_runtime_dispatch_executor_pass_id"]["ok"] is True
    assert checks["missing_statement_blocks_real_vault_write"]["ok"] is True
    assert checks["temp_executor_writes_one_open_agent_bus_task"]["ok"] is True
    assert checks["duplicate_blocks_before_second_task_write"]["ok"] is True
    assert checks["registry_exposes_runtime_dispatch_executor"]["ok"] is True
    assert checks["api_blocks_runtime_dispatch_executor_without_digest"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_browser_dispatch_readiness_static_runner_validates_no_browser_dispatch_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-browser-dispatch-readiness-contract",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-browser-dispatch-readiness-contract"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["browser_dispatch_allowed"] is False
    assert report["authority"]["browser_launch_allowed"] is False
    assert report["authority"]["browser_navigation_allowed"] is False
    assert report["authority"]["screenshot_capture_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-approval-consumption-readiness-contract"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_browser_dispatch_preview_ok"]["ok"] is True
    assert checks["phase11_browser_dispatch_pass_id"]["ok"] is True
    assert checks["browser_dispatch_digest_present"]["ok"] is True
    assert checks["external_runtime_readiness_consumed_no_execution"]["ok"] is True
    assert checks["future_browser_dispatch_preview_no_browser_effects"]["ok"] is True
    assert checks["non_browser_intent_blocks"]["ok"] is True
    assert checks["prompt_injection_blocks_browser_dispatch"]["ok"] is True
    assert checks["registry_exposes_browser_dispatch_readiness"]["ok"] is True
    assert checks["api_exposes_browser_dispatch_readiness"]["ok"] is True
    assert checks["panel_embeds_browser_dispatch_readiness"]["ok"] is True
    assert checks["frontend_browser_tokens_present"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_approval_consumption_readiness_static_runner_validates_no_consumption_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-approval-consumption-readiness-contract",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-approval-consumption-readiness-contract"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_consumption_preview_allowed"] is True
    assert report["authority"]["approval_status_mutation_allowed"] is False
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["target_vault_write_allowed"] is False
    assert report["authority"]["exact_once_marker_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-companion-status-ui-shell"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_approval_consumption_pending_preview_ok"]["ok"] is True
    assert checks["phase11_approval_consumption_pass_id"]["ok"] is True
    assert checks["pending_approval_selected_without_execution"]["ok"] is True
    assert checks["approved_preflight_still_blocks_consumption_execution"]["ok"] is True
    assert checks["consumption_digest_and_marker_preview_present"]["ok"] is True
    assert checks["current_service_execution_blocks_before_target_write"]["ok"] is True
    assert checks["missing_approval_blocks_cleanly"]["ok"] is True
    assert checks["prompt_injection_blocks_consumption_preview"]["ok"] is True
    assert checks["source_message_digest_mismatch_blocks"]["ok"] is True
    assert checks["registry_exposes_approval_consumption_readiness"]["ok"] is True
    assert checks["api_exposes_approval_consumption_readiness"]["ok"] is True
    assert checks["panel_embeds_approval_consumption_readiness"]["ok"] is True
    assert checks["frontend_consumption_tokens_present"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_companion_status_ui_shell_static_runner_validates_readonly_ui_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-companion-status-ui-shell",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-companion-status-ui-shell"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["runtime_control_allowed"] is False
    assert report["authority"]["identity_ledger_mutation_allowed"] is False
    assert report["authority"]["role_card_write_allowed"] is False
    assert report["authority"]["profile_write_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-multi-companion-registry-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_status_contract_ok"]["ok"] is True
    assert checks["companion_cards_renderable"]["ok"] is True
    assert checks["registry_exposes_companion_status"]["ok"] is True
    assert checks["api_exposes_companion_status"]["ok"] is True
    assert checks["panel_embeds_companion_status"]["ok"] is True
    assert checks["frontend_companion_tokens_present"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_multi_companion_registry_readiness_static_runner_validates_readonly_registry_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-multi-companion-registry-readiness",
        mode="static",
        timeout_seconds=2,
    )
    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-multi-companion-registry-readiness"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["registry_loader_activated"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-companion-direction-before-roster-ui"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_multi_companion_registry_readiness_ok"]["ok"] is True
    assert checks["registry_json_and_schema_loaded_readonly"]["ok"] is True
    assert checks["registry_compares_to_builtin_cards"]["ok"] is True
    assert checks["registry_not_loaded_for_selection_and_target_not_written"]["ok"] is True
    assert checks["registry_exposes_multi_companion_readiness"]["ok"] is True
    assert checks["api_exposes_multi_companion_registry_readiness"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_operator_companion_direction_static_runner_validates_decision_packet_only_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="operator-companion-direction-before-roster-ui",
        mode="static",
        timeout_seconds=2,
    )
    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "operator-companion-direction-before-roster-ui"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["operator_decision_write_allowed"] is False
    assert report["authority"]["companion_roster_ui_mutation_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-answer-companion-direction-questions"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["operator_companion_direction_packet_ok"]["ok"] is True
    assert checks["companion_options_visible"]["ok"] is True
    assert checks["operator_questions_unanswered_and_roster_ui_blocked"]["ok"] is True
    assert checks["api_exposes_operator_companion_direction"]["ok"] is True
    assert checks["registry_exposes_operator_companion_direction"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_operator_companion_direction_answers_static_runner_validates_approved_policy_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="operator-answer-companion-direction-questions",
        mode="static",
        timeout_seconds=2,
    )
    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "operator-answer-companion-direction-questions"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["operator_decision_write_allowed"] is False
    assert report["authority"]["companion_roster_ui_mutation_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-roster-ui-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["operator_companion_direction_answers_ok"]["ok"] is True
    assert checks["operator_policy_approved_with_amendments"]["ok"] is True
    assert checks["v0_1_effect_boundaries_captured"]["ok"] is True
    assert checks["api_exposes_operator_companion_direction_answers"]["ok"] is True
    assert checks["registry_exposes_operator_companion_direction_answers"]["ok"] is True
    assert checks["answers_authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_companion_selection_preview_static_runner_validates_approval_preview_only_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-companion-selection-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-companion-selection-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_queue_write_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["identity_ledger_mutation_allowed"] is False
    assert report["authority"]["role_card_write_allowed"] is False
    assert report["authority"]["profile_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-companion-selection-queue-write-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_selection_preview_ok"]["ok"] is True
    assert checks["selection_digest_and_future_packet_present"]["ok"] is True
    assert checks["unknown_companion_blocks_cleanly"]["ok"] is True
    assert checks["noop_selection_blocks_cleanly"]["ok"] is True
    assert checks["prompt_injection_blocks_selection_preview"]["ok"] is True
    assert checks["registry_exposes_companion_selection_preview"]["ok"] is True
    assert checks["api_exposes_companion_selection_preview"]["ok"] is True
    assert checks["panel_embeds_companion_selection_preview"]["ok"] is True
    assert checks["frontend_companion_selection_tokens_present"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_companion_roster_ui_preview_static_runner_validates_readonly_roster_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-roster-ui-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-roster-ui-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["companion_roster_ui_preview_allowed"] is True
    assert report["authority"]["companion_roster_ui_mutation_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["provider_model_selection_granted"] is False
    assert report["authority"]["memory_access_granted"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-boundary-contract"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_roster_ui_preview_ok"]["ok"] is True
    assert checks["roster_cards_renderable"]["ok"] is True
    assert checks["abstract_visual_policy_bounded"]["ok"] is True
    assert checks["panel_embeds_companion_roster_ui_preview"]["ok"] is True
    assert checks["api_exposes_companion_roster_ui_preview"]["ok"] is True
    assert checks["registry_exposes_companion_roster_ui_preview"]["ok"] is True
    assert checks["frontend_companion_roster_tokens_present"]["ok"] is True
    assert checks["roster_authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_companion_memory_boundary_static_runner_validates_readonly_memory_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-boundary-contract",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-boundary-contract"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["separate_memory_namespace_declared"] is True
    assert report["authority"]["writes_companion_memory"] is False
    assert report["authority"]["memory_write_authority_granted"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-approval-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_boundary_contract_ok"]["ok"] is True
    assert checks["separate_memory_namespaces_declared"]["ok"] is True
    assert checks["memory_candidate_validation_blocks_denied_classes"]["ok"] is True
    assert checks["panel_embeds_companion_memory_boundary"]["ok"] is True
    assert checks["api_exposes_companion_memory_boundary"]["ok"] is True
    assert checks["registry_exposes_companion_memory_boundary"]["ok"] is True
    assert checks["frontend_companion_memory_tokens_present"]["ok"] is True
    assert checks["memory_authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_approval_preview_static_runner_validates_gated_memory_approval_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_queue_write_allowed_with_digest"] is True
    assert report["authority"]["writes_companion_memory"] is False
    assert report["authority"]["memory_write_authority_granted"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-approved-execution-proof"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_approval_preview_ok"]["ok"] is True
    assert checks["memory_approval_digest_and_packet_present"]["ok"] is True
    assert checks["denied_memory_candidate_blocks_preview"]["ok"] is True
    assert checks["panel_embeds_companion_memory_approval_preview"]["ok"] is True
    assert checks["api_exposes_companion_memory_approval_preview"]["ok"] is True
    assert checks["registry_exposes_companion_memory_approval_preview"]["ok"] is True
    assert checks["frontend_companion_memory_approval_tokens_present"]["ok"] is True
    assert checks["memory_approval_authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_approved_execution_proof_static_runner_validates_exact_once_proof_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-approved-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-approved-execution-proof"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_consumption_allowed"] is True
    assert report["authority"]["exact_once_marker_write_allowed"] is True
    assert report["authority"]["proof_output_write_allowed"] is True
    assert report["authority"]["memory_ledger_write_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-ledger-write-approval-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_execution_proof_ok"]["ok"] is True
    assert checks["execution_consumes_approval_once"]["ok"] is True
    assert checks["duplicate_execution_blocks_before_outputs"]["ok"] is True
    assert checks["generic_service_execution_blocked"]["ok"] is True
    assert checks["api_exposes_companion_memory_execution_proof"]["ok"] is True
    assert checks["registry_exposes_companion_memory_execution_proof"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_readback_search_preview_static_runner_validates_proof_index() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-readback-search-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-readback-search-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["proof_read_allowed"] is True
    assert report["authority"]["real_companion_memory_read_allowed"] is False
    assert report["authority"]["memory_ledger_write_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-ledger-write-approval-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_readback_search_preview_ok"]["ok"] is True
    assert checks["readback_indexes_executed_and_pending_proofs"]["ok"] is True
    assert checks["search_filters_companion_memory_proofs"]["ok"] is True
    assert checks["malformed_optional_approval_content_tolerated"]["ok"] is True
    assert checks["api_exposes_companion_memory_readback_search"]["ok"] is True
    assert checks["registry_exposes_companion_memory_readback_search"]["ok"] is True
    assert checks["panel_embeds_companion_memory_readback_search"]["ok"] is True
    assert checks["frontend_companion_memory_readback_tokens_present"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_ledger_write_approval_preview_static_runner_validates_queue_preview() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-ledger-write-approval-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-ledger-write-approval-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_queue_write_allowed_with_digest"] is True
    assert report["authority"]["memory_ledger_write_allowed"] is False
    assert report["authority"]["real_companion_memory_read_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-approved-ledger-write-execution-proof"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_ledger_write_approval_preview_ok"]["ok"] is True
    assert checks["ledger_write_preview_uses_executed_proof"]["ok"] is True
    assert checks["ledger_write_approval_queue_write_requires_exact_digest"]["ok"] is True
    assert checks["duplicate_ledger_write_approval_blocks_before_second_write"]["ok"] is True
    assert checks["mismatch_and_missing_proof_block_before_writes"]["ok"] is True
    assert checks["generic_service_execution_blocked_for_ledger_write_approval"]["ok"] is True
    assert checks["api_exposes_companion_memory_ledger_write_approval_preview"]["ok"] is True
    assert checks["registry_exposes_companion_memory_ledger_write_approval_preview"]["ok"] is True
    assert checks["panel_embeds_companion_memory_ledger_write_approval_preview"]["ok"] is True
    assert checks["frontend_companion_memory_ledger_write_tokens_present"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_approved_ledger_write_execution_proof_static_runner_validates_exact_once_ledger_write() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-approved-ledger-write-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-approved-ledger-write-execution-proof"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_consumption_allowed"] is True
    assert report["authority"]["memory_ledger_write_allowed"] is True
    assert report["authority"]["memory_root_create_allowed"] is True
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-ledger-read-model-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_approved_ledger_write_execution_proof_ok"]["ok"] is True
    assert checks["execution_consumes_approval_once_and_writes_ledger"]["ok"] is True
    assert checks["duplicate_execution_blocks_before_second_ledger_append"]["ok"] is True
    assert checks["generic_service_execution_blocked"]["ok"] is True
    assert checks["api_exposes_companion_memory_approved_ledger_write_execution_proof"]["ok"] is True
    assert checks["registry_exposes_companion_memory_approved_ledger_write_execution_proof"]["ok"] is True
    assert checks["panel_embeds_companion_memory_approved_ledger_write_execution_posture"]["ok"] is True
    assert checks["frontend_companion_memory_approved_ledger_write_tokens_present"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_ledger_read_model_preview_static_runner_validates_read_model() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-ledger-read-model-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-ledger-read-model-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["real_companion_memory_read_allowed"] is True
    assert report["authority"]["proof_backfill_read_allowed"] is True
    assert report["authority"]["memory_ledger_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-context-readiness-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_ledger_read_model_preview_ok"]["ok"] is True
    assert checks["ledger_read_model_reads_jsonl_entries"]["ok"] is True
    assert checks["ledger_read_model_filters_records"]["ok"] is True
    assert checks["ledger_read_model_uses_proof_backfill_when_ledger_absent"]["ok"] is True
    assert checks["ledger_read_model_tolerates_malformed_jsonl_lines"]["ok"] is True
    assert checks["api_exposes_companion_memory_ledger_read_model"]["ok"] is True
    assert checks["registry_exposes_companion_memory_ledger_read_model"]["ok"] is True
    assert checks["panel_embeds_companion_memory_ledger_read_model"]["ok"] is True
    assert checks["frontend_companion_memory_ledger_read_model_tokens_present"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_real_ledger_activation_closeout_static_runner_validates_activation() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-real-ledger-activation-closeout",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-real-ledger-activation-closeout"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["real_companion_memory_read_allowed"] is True
    assert report["authority"]["activation_closeout_allowed"] is True
    assert report["authority"]["memory_ledger_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-companion-memory-context-readiness-preview"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_real_ledger_activation_closeout_ok"]["ok"] is True
    assert checks["real_ledger_closeout_verifies_consumed_approval_marker_evidence"]["ok"] is True
    assert checks["real_ledger_closeout_reads_jsonl_record"]["ok"] is True
    assert checks["real_ledger_closeout_filters_records"]["ok"] is True
    assert checks["real_ledger_closeout_blocks_missing_ledger"]["ok"] is True
    assert checks["real_ledger_closeout_blocks_missing_evidence"]["ok"] is True
    assert checks["api_exposes_companion_memory_real_ledger_activation_closeout"]["ok"] is True
    assert checks["registry_exposes_companion_memory_real_ledger_activation_closeout"]["ok"] is True
    assert checks["panel_embeds_companion_memory_real_ledger_activation_closeout"]["ok"] is True
    assert checks["frontend_companion_memory_real_ledger_activation_tokens_present"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_companion_memory_context_readiness_preview_static_runner_validates_context_packet() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-companion-memory-context-readiness-preview",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-companion-memory-context-readiness-preview"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["real_companion_memory_read_allowed"] is True
    assert report["authority"]["context_preview_allowed"] is True
    assert report["authority"]["memory_ledger_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["model_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_memory_context_readiness_preview_ok"]["ok"] is True
    assert checks["context_readiness_builds_packet_from_real_ledger"]["ok"] is True
    assert checks["context_readiness_marks_raw_noncanonical_boundary"]["ok"] is True
    assert checks["context_readiness_respects_context_budget"]["ok"] is True
    assert checks["context_readiness_handles_no_records_without_writes"]["ok"] is True
    assert checks["context_readiness_uses_proof_backfill_when_ledger_absent"]["ok"] is True
    assert checks["api_exposes_companion_memory_context_readiness"]["ok"] is True
    assert checks["registry_exposes_companion_memory_context_readiness"]["ok"] is True
    assert checks["panel_embeds_companion_memory_context_readiness"]["ok"] is True
    assert checks["frontend_companion_memory_context_readiness_tokens_present"]["ok"] is True
    assert checks["context_readiness_authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True
    assert checks["static_qa_no_real_companion_memory_writes"]["ok"] is True


def test_phase11_chat_companion_selection_queue_write_readiness_static_runner_validates_no_queue_write_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-companion-selection-queue-write-readiness",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-companion-selection-queue-write-readiness"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["approval_queue_write_readiness_allowed"] is True
    assert report["authority"]["approval_queue_write_allowed"] is False
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["identity_ledger_mutation_allowed"] is False
    assert report["authority"]["role_card_write_allowed"] is False
    assert report["authority"]["profile_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-companion-selection-queue-write-execution-proof"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_selection_queue_write_readiness_ok"]["ok"] is True
    assert checks["phase11_companion_selection_queue_write_pass_id"]["ok"] is True
    assert checks["queue_digest_and_future_packet_present"]["ok"] is True
    assert checks["matching_digest_allows_readiness_without_write"]["ok"] is True
    assert checks["mismatched_digest_blocks_readiness_without_write"]["ok"] is True
    assert checks["registry_exposes_companion_selection_queue_write_readiness"]["ok"] is True
    assert checks["api_exposes_companion_selection_queue_write_readiness"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_companion_selection_queue_write_execution_static_runner_validates_pending_approval_only_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-companion-selection-queue-write-execution-proof",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-companion-selection-queue-write-execution-proof"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["writes_temp_approval_artifact_for_static_proof"] is True
    assert report["authority"]["approval_queue_write_allowed"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["identity_ledger_mutation_allowed"] is False
    assert report["authority"]["role_card_write_allowed"] is False
    assert report["authority"]["profile_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-companion-selection-approval-consumption-readiness"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_selection_queue_write_execution_proof_ok"]["ok"] is True
    assert checks["missing_digest_blocks_real_vault_write"]["ok"] is True
    assert checks["mismatched_digest_blocks_real_vault_write"]["ok"] is True
    assert checks["prompt_injection_and_unknown_runtime_block_queue_write"]["ok"] is True
    assert checks["temp_queue_write_creates_pending_approval_only"]["ok"] is True
    assert checks["duplicate_digest_blocks_second_write"]["ok"] is True
    assert checks["target_selection_file_not_written"]["ok"] is True
    assert checks["registry_exposes_companion_selection_queue_write_execution"]["ok"] is True
    assert checks["api_blocks_companion_selection_queue_write_execution_without_matching_digest"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_companion_selection_approval_consumption_static_runner_validates_readonly_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-companion-selection-approval-consumption-readiness",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-companion-selection-approval-consumption-readiness"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["approval_consumption_preview_allowed"] is True
    assert report["authority"]["approval_status_mutation_allowed"] is False
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["companion_selection_write_allowed"] is False
    assert report["authority"]["identity_ledger_mutation_allowed"] is False
    assert report["authority"]["role_card_write_allowed"] is False
    assert report["authority"]["profile_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-companion-selection-approval-consumption-executor"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_selection_approval_consumption_readiness_ok"]["ok"] is True
    assert checks["pending_approval_preview_is_read_only"]["ok"] is True
    assert checks["approved_approval_still_does_not_execute"]["ok"] is True
    assert checks["digest_mismatch_blocks_without_write"]["ok"] is True
    assert checks["missing_approval_blocks_cleanly"]["ok"] is True
    assert checks["studio_service_blocks_companion_selection_execute_before_mutation"]["ok"] is True
    assert checks["registry_exposes_companion_selection_approval_consumption_readiness"]["ok"] is True
    assert checks["api_exposes_companion_selection_approval_consumption_readiness"]["ok"] is True
    assert checks["panel_embeds_companion_selection_approval_consumption_readiness"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_companion_selection_approval_consumption_executor_static_runner_validates_bounded_execution() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-companion-selection-approval-consumption-executor",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-companion-selection-approval-consumption-executor"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["authority"]["approval_consumption_allowed"] is True
    assert report["authority"]["approval_status_mutation_allowed"] is True
    assert report["authority"]["exact_once_marker_write_allowed"] is True
    assert report["authority"]["companion_selection_write_allowed"] is True
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-select-next-governed-executor-lane"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_companion_selection_approval_consumption_executor_ok"]["ok"] is True
    assert checks["pending_approval_requires_operator_statement_or_prior_approval"]["ok"] is True
    assert checks["executor_writes_target_marker_and_consumes_approval"]["ok"] is True
    assert checks["duplicate_blocks_before_target_write"]["ok"] is True
    assert checks["generic_studio_service_execution_remains_blocked"]["ok"] is True
    assert checks["api_blocks_executor_without_matching_digest"]["ok"] is True
    assert checks["registry_exposes_companion_selection_approval_consumption_executor"]["ok"] is True
    assert checks["panel_keeps_ambient_chat_consumption_blocked"]["ok"] is True
    assert checks["authority_limited_to_companion_selection_consumption"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_readonly_slash_command_responses_static_runner_validates_readonly_cards() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-readonly-slash-command-responses",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-readonly-slash-command-responses"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-readonly-card-visual-qa"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["phase11_readonly_slash_command_responses_ok"]["ok"] is True
    assert checks["dashboard_cards_ready"]["ok"] is True
    assert checks["runtime_status_readonly"]["ok"] is True
    assert checks["pet_companion_status_readonly"]["ok"] is True
    assert checks["map_readonly_graph_summary"]["ok"] is True
    assert checks["write_command_blocked"]["ok"] is True
    assert checks["unknown_command_help_only"]["ok"] is True
    assert checks["api_exposes_readonly_slash_responses"]["ok"] is True
    assert checks["registry_exposes_readonly_slash_responses"]["ok"] is True
    assert checks["panel_embeds_readonly_slash_responses"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_readonly_slash_command_response_ui_static_runner_validates_frontend_cards() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-readonly-slash-command-response-ui",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-readonly-slash-command-response-ui"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-readonly-card-visual-qa"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["frontend_readonly_slash_response_renderer_present"]["ok"] is True
    assert checks["frontend_readonly_slash_response_styles_present"]["ok"] is True
    assert checks["frontend_embeds_readonly_response_contract"]["ok"] is True
    assert checks["frontend_command_execution_boundary_visible"]["ok"] is True
    assert checks["panel_contract_slash_response_data_ready"]["ok"] is True
    assert checks["api_slash_response_data_ready"]["ok"] is True
    assert checks["registry_marks_slash_response_ui_ready"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_chat_readonly_card_visual_qa_static_runner_validates_visual_artifact_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-readonly-card-visual-qa",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-readonly-card-visual-qa"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-no-hitl-feature-family-selection-audit"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["visual_artifact_contract_ready"]["ok"] is True
    assert checks["static_html_has_no_scripts"]["ok"] is True
    assert checks["responsive_visual_tokens_present"]["ok"] is True
    assert checks["visual_qa_summary_marks_browser_proof_pending"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_no_hitl_feature_family_selection_audit_static_runner_validates_selection_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-no-hitl-feature-family-selection-audit",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-no-hitl-feature-family-selection-audit"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-readonly-slash-command-catalog-audit"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["no_hitl_selection_audit_ready"]["ok"] is True
    assert checks["selected_candidate_is_read_only"]["ok"] is True
    assert checks["executor_and_live_surfaces_deferred"]["ok"] is True
    assert checks["prompt_objective_checklist_mapped"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_readonly_slash_command_catalog_audit_static_runner_validates_catalog_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-readonly-slash-command-catalog-audit",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-readonly-slash-command-catalog-audit"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-readonly-operator-dashboard-aggregate-audit"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["slash_command_catalog_audit_ready"]["ok"] is True
    assert checks["supported_readonly_commands_covered"]["ok"] is True
    assert checks["write_and_execution_commands_blocked"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_readonly_operator_dashboard_aggregate_audit_static_runner_validates_dashboard_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-readonly-operator-dashboard-aggregate-audit",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-readonly-operator-dashboard-aggregate-audit"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "phase11-chat-no-hitl-lane-completion-audit"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["operator_dashboard_aggregate_audit_ready"]["ok"] is True
    assert checks["dashboard_sources_covered"]["ok"] is True
    assert checks["source_cards_covered"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_no_hitl_lane_completion_audit_static_runner_validates_completion_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="phase11-chat-no-hitl-lane-completion-audit",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "phase11-chat-no-hitl-lane-completion-audit"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-selected-governed-executor-or-deferred-closeout"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["no_hitl_lane_completion_audit_ready"]["ok"] is True
    assert checks["prompt_to_artifact_checklist_complete"]["ok"] is True
    assert checks["completed_no_hitl_artifacts_indexed"]["ok"] is True
    assert checks["deferred_lanes_require_human_or_live_authority"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_operator_governed_executor_deferred_closeout_static_runner_validates_handoff_contract() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="operator-selected-governed-executor-or-deferred-closeout",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "operator-selected-governed-executor-or-deferred-closeout"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-action-required-no-autonomous-phase11-pass"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["operator_governed_handoff_ready"]["ok"] is True
    assert checks["no_autonomous_phase11_passes_remaining"]["ok"] is True
    assert checks["remaining_lanes_require_operator_selection"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_phase11_operator_action_required_no_autonomous_pass_static_runner_validates_decision_gate() -> None:
    report = run_studio_qa_runner(
        VAULT_ROOT,
        surface="operator-action-required-no-autonomous-phase11-pass",
        mode="static",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["qa_surface"] == "operator-action-required-no-autonomous-phase11-pass"
    assert report["server"]["started"] is False
    assert report["server"]["stopped"] is True
    assert report["writes_performed"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["approval_execution_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["writes_real_vault_markdown"] is False
    assert report["authority"]["writes_real_vault_approval_artifacts"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == "operator-select-governed-executor-lane-or-defer-closeout"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["operator_action_required_gate_ready"]["ok"] is True
    assert checks["no_autonomous_phase11_passes_remaining"]["ok"] is True
    assert checks["operator_decision_required"]["ok"] is True
    assert checks["available_lanes_are_governed"]["ok"] is True
    assert checks["authority_bounded"]["ok"] is True
    assert checks["static_qa_no_real_markdown_writes"]["ok"] is True
    assert checks["static_qa_no_real_approval_artifact_writes"]["ok"] is True


def test_legacy_graph_view_runner_uses_ephemeral_server_and_stops(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    def fake_smoke(*args, **kwargs):
        return {
            "ok": True,
            "base_url": "http://127.0.0.1:49152",
            "server_stopped": True,
            "checks": [
                {
                    "route": "/",
                    "ok": True,
                    "shell_root_present": True,
                    "graph_mount_present": True,
                    "graph_route_present": True,
                    "graph_iframe_title_present": True,
                    "script_tags": 0,
                },
                {
                    "route": "/graph-view-shell-panel.json",
                    "ok": True,
                    "writes_graph_index": False,
                    "writes_node_ids": False,
                    "node_editing_allowed": False,
                    "workflow_execution_allowed": False,
                    "provider_calls_allowed": False,
                    "connector_calls_allowed": False,
                    "canonical_mutation_allowed": False,
                },
                {"route": "/graph-view-static-artifact.html", "ok": True},
            ],
        }

    monkeypatch.setattr(qa_runner, "smoke_test_studio_desktop_shell_app", fake_smoke, raising=False)
    monkeypatch.setattr(
        "runtime.studio.desktop_shell_app.smoke_test_studio_desktop_shell_app",
        fake_smoke,
    )

    report = run_studio_qa_runner(
        vault,
        surface="graph-view",
        mode="legacy-browser",
        timeout_seconds=2,
        write_evidence=True,
        evidence_slug="qa-runner-test",
    )

    assert report["ok"] is True
    assert report["server"]["started"] is True
    assert report["server"]["stopped"] is True
    assert report["server"]["actual_base_url"] == "http://127.0.0.1:49152"
    assert report["legacy_localhost_harness"]["canonical_product_lane"] is False
    assert report["native_shell"]["canonical_product_lane"] is True
    assert report["evidence"]["written"] is True
    assert (vault / report["evidence"]["json_path"]).is_file()
    assert (vault / report["evidence"]["markdown_path"]).is_file()
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["graph_mount_present"]["ok"] is True
    assert checks["graph_no_provider_calls"]["ok"] is True
    assert checks["graph_no_canonical_mutation"]["ok"] is True


def test_qa_runner_rejects_unsafe_host(tmp_path: Path) -> None:
    with pytest.raises(StudioQARunnerError):
        run_studio_qa_runner(
            tmp_path,
            surface="graph-view",
            mode="legacy-browser",
            host="0.0.0.0",
        )


def test_legacy_browser_runtime_runner_uses_harness_support_without_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    def fake_smoke(*args, **kwargs):
        return {
            "ok": True,
            "base_url": "http://127.0.0.1:49153",
            "server_stopped": True,
            "checks": [
                {
                    "route": "/",
                    "ok": True,
                    "shell_root_present": True,
                    "browser_runtime_mount_present": True,
                    "browser_runtime_route_present": True,
                    "script_tags": 0,
                },
                {
                    "route": "/browser-runtime-panel.json",
                    "ok": True,
                    "browser_runtime_panel_ok": True,
                    "browser_runtime_required_sections_present": True,
                    "read_only": True,
                    "starts_servers": False,
                    "launches_browser": False,
                    "connects_cdp": False,
                    "invokes_mcp": False,
                    "runs_browser_use_cli_live": False,
                    "activates_skills": False,
                    "provider_calls_allowed": False,
                    "connector_calls_allowed": False,
                    "canonical_mutation_allowed": False,
                },
            ],
        }

    monkeypatch.setattr(
        "runtime.studio.desktop_shell_app.smoke_test_studio_desktop_shell_app",
        fake_smoke,
    )

    report = run_studio_qa_runner(
        vault,
        surface="browser-runtime",
        mode="legacy-browser",
        timeout_seconds=2,
    )

    assert report["ok"] is True
    assert report["server"]["started"] is True
    assert report["server"]["stopped"] is True
    assert report["legacy_localhost_harness"]["used"] is True
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["browser_runtime_mount_present"]["ok"] is True
    assert checks["browser_runtime_json_ok"]["ok"] is True
    assert checks["browser_runtime_required_sections_present"]["ok"] is True
    assert checks["browser_runtime_no_browser_use_cli_live"]["ok"] is True
    assert checks["browser_runtime_no_canonical_mutation"]["ok"] is True




def test_phase10_studio_qa_proof_lane_emits_structured_evidence_and_failure_buckets(tmp_path: Path) -> None:
    evidence_root = Path("07_LOGS") / "Studio-Graph-Views" / "phase10-qa-proof-test"

    report = run_phase10_studio_qa_proof_lane(
        VAULT_ROOT,
        write_evidence=True,
        evidence_slug="phase10-qa-proof-test",
        evidence_root=evidence_root,
    )

    assert report["surface"] == "studio_phase10_qa_proof_lane"
    assert report["status"] in {"phase10_studio_qa_proof_passed", "phase10_studio_qa_proof_blocked"}
    assert report["authority"]["read_only"] is True
    assert report["authority"]["launches_packaged_app"] is False
    assert report["authority"]["captures_screenshot"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["proof_commands"]["packaging_readiness"]["argv"] == [
        "chaseos",
        "studio",
        "packaging-readiness",
        "--json",
    ]
    assert report["proof_commands"]["local_packaging_proof"]["executes_build"] is False
    assert report["proof_commands"]["packaged_app_launch_smoke"]["documented_only"] is True
    assert report["proof_commands"]["packaged_app_visual_qa"]["documented_only"] is True
    assert set(report["checks_by_surface"]) >= {
        "packaging_readiness",
        "local_packaging_proof_preflight",
        "graph_view_browser_qa",
        "pass10b_visual_proof_completion_audit",
    }
    assert "deterministic_failures" in report["failure_buckets"]
    assert "flaky_failures" in report["failure_buckets"]
    assert report["evidence"]["written"] is True
    json_path = VAULT_ROOT / report["evidence"]["json_path"]
    markdown_path = VAULT_ROOT / report["evidence"]["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()


def test_phase10_studio_qa_proof_lane_classifies_missing_packaging_deps_as_environment_gap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from runtime.studio import graph_view_browser_qa, packaging_proof, packaging_readiness
    from runtime.studio import pass10b_visual_proof_completion_audit as pass10b_audit

    def fake_local_packaging(_vault_root, *, execute_build=False):
        return {
            "ok": False,
            "status": "blocked_local_packaging_proof",
            "surface": "studio_local_packaging_proof",
            "model_version": "studio.local_packaging_proof.v1",
            "dependencies": {"pyinstaller_available": False, "pywebview_available": False},
            "outputs": {
                "output_root": ".pytest_tmp_env/studio-packaging-proof",
                "expected_executable": ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio/ChaseOS-Studio",
                "executable_exists": False,
                "executable_sha256": None,
            },
            "blockers": [
                "PyInstaller is not installed in the active Python environment.",
                "pywebview is not installed in the active Python environment.",
            ],
        }

    monkeypatch.setattr(packaging_proof, "build_studio_local_packaging_proof", fake_local_packaging)
    monkeypatch.setattr(packaging_readiness, "build_studio_packaging_readiness", lambda _vault: {"ok": True, "status": "ready_for_local_packaging_proof"})
    monkeypatch.setattr(graph_view_browser_qa, "static_graph_browser_qa_evidence_built", lambda _vault: True)
    monkeypatch.setattr(graph_view_browser_qa, "graph_view_shell_panel_browser_qa_evidence_built", lambda _vault: True)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_artifact", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_browser_qa_note", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_browser_qa_screenshot", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_graph_view_shell_panel_browser_qa_note", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_graph_view_shell_panel_browser_qa_screenshot", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "next_graph_view_pass_after_browser_qa", lambda _vault: "studio-packaged-app-launch-smoke")
    monkeypatch.setattr(
        pass10b_audit,
        "build_pass10b_visual_proof_completion_audit",
        lambda _vault, *, probe_native_host_policy=False, packaged_visual_qa_report_path=None: {
            "ok": True,
            "status": "passed",
            "model_version": "test",
        },
    )

    report = run_phase10_studio_qa_proof_lane(tmp_path)
    local = report["checks_by_surface"]["local_packaging_proof_preflight"]

    assert local["ok"] is False
    assert local["failure_bucket"] == "environment_dependency"
    assert local["summary"]["failure_classification"] == "environment_dependency"
    assert local["summary"]["active_python_env_preflight"]["dependencies"] == {
        "pyinstaller_available": False,
        "pywebview_available": False,
    }
    assert report["failure_buckets"]["deterministic_failures"] == []
    assert report["failure_buckets"]["environment_dependency"][0]["surface"] == "local_packaging_proof_preflight"


def test_phase10_studio_qa_proof_lane_accepts_valid_local_packaging_evidence_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from runtime.studio import graph_view_browser_qa, packaging_proof, packaging_readiness
    from runtime.studio import pass10b_visual_proof_completion_audit as pass10b_audit

    executable = tmp_path / ".pytest_tmp_env" / "studio-packaging-proof" / "dist" / "ChaseOS-Studio" / "ChaseOS-Studio"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"valid deps-backed executable")
    digest = qa_runner._file_sha256(executable)
    evidence_path = tmp_path / "07_LOGS" / "Studio-Graph-Views" / "packaging-proof.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(
        qa_runner.json.dumps(
            {
                "ok": True,
                "surface": "studio_local_packaging_proof",
                "model_version": "studio.local_packaging_proof.v1",
                "status": "local_packaging_proof_complete",
                "execute_build_requested": True,
                "outputs": {
                    "expected_executable": ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio/ChaseOS-Studio",
                    "executable_exists": True,
                    "executable_sha256": digest,
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_local_packaging(_vault_root, *, execute_build=False):
        return {
            "ok": False,
            "status": "blocked_local_packaging_proof",
            "surface": "studio_local_packaging_proof",
            "model_version": "studio.local_packaging_proof.v1",
            "dependencies": {"pyinstaller_available": False, "pywebview_available": False},
            "outputs": {"expected_executable": ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio/ChaseOS-Studio"},
            "blockers": ["PyInstaller is not installed in the active Python environment."],
        }

    monkeypatch.setattr(packaging_proof, "build_studio_local_packaging_proof", fake_local_packaging)
    monkeypatch.setattr(packaging_readiness, "build_studio_packaging_readiness", lambda _vault: {"ok": True, "status": "ready_for_local_packaging_proof"})
    monkeypatch.setattr(graph_view_browser_qa, "static_graph_browser_qa_evidence_built", lambda _vault: True)
    monkeypatch.setattr(graph_view_browser_qa, "graph_view_shell_panel_browser_qa_evidence_built", lambda _vault: True)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_artifact", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_browser_qa_note", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_browser_qa_screenshot", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_graph_view_shell_panel_browser_qa_note", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_graph_view_shell_panel_browser_qa_screenshot", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "next_graph_view_pass_after_browser_qa", lambda _vault: "studio-packaged-app-launch-smoke")
    monkeypatch.setattr(
        pass10b_audit,
        "build_pass10b_visual_proof_completion_audit",
        lambda _vault, *, probe_native_host_policy=False, packaged_visual_qa_report_path=None: {
            "ok": True,
            "status": "passed",
            "model_version": "test",
        },
    )

    report = run_phase10_studio_qa_proof_lane(
        tmp_path,
        local_packaging_proof_evidence="07_LOGS/Studio-Graph-Views/packaging-proof.json",
    )
    local = report["checks_by_surface"]["local_packaging_proof_preflight"]

    assert local["ok"] is True
    assert local["failure_bucket"] is None
    assert local["status"] == "local_packaging_proof_context_accepted"
    assert local["summary"]["failure_classification"] == "dependency_context_reporting"
    assert local["summary"]["deps_backed_packaging_evidence"]["ok"] is True
    assert local["summary"]["deps_backed_packaging_evidence"]["json_path"] == "07_LOGS/Studio-Graph-Views/packaging-proof.json"
    assert "07_LOGS/Studio-Graph-Views/packaging-proof.json" in local["artifact_paths"]
    assert report["ok"] is True


def test_phase10_studio_qa_proof_lane_accepts_packaged_visual_qa_report_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from runtime.studio import graph_view_browser_qa, packaging_proof, packaging_readiness
    from runtime.studio import pass10b_visual_proof_completion_audit as pass10b_audit

    calls = {}

    monkeypatch.setattr(
        packaging_proof,
        "build_studio_local_packaging_proof",
        lambda _vault, *, execute_build=False: {"ok": True, "status": "ready_to_execute_local_packaging_proof", "model_version": "test"},
    )
    monkeypatch.setattr(packaging_readiness, "build_studio_packaging_readiness", lambda _vault: {"ok": True, "status": "ready_for_local_packaging_proof"})
    monkeypatch.setattr(graph_view_browser_qa, "static_graph_browser_qa_evidence_built", lambda _vault: True)
    monkeypatch.setattr(graph_view_browser_qa, "graph_view_shell_panel_browser_qa_evidence_built", lambda _vault: True)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_artifact", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_browser_qa_note", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_static_graph_browser_qa_screenshot", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_graph_view_shell_panel_browser_qa_note", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "latest_graph_view_shell_panel_browser_qa_screenshot", lambda _vault: None)
    monkeypatch.setattr(graph_view_browser_qa, "next_graph_view_pass_after_browser_qa", lambda _vault: "studio-packaged-app-launch-smoke")

    def fake_pass10b_audit(_vault, *, probe_native_host_policy=False, packaged_visual_qa_report_path=None):
        calls["packaged_visual_qa_report_path"] = packaged_visual_qa_report_path
        return {"ok": True, "status": "COMPLETE / VERIFIED", "model_version": "test"}

    monkeypatch.setattr(pass10b_audit, "build_pass10b_visual_proof_completion_audit", fake_pass10b_audit)

    report = run_phase10_studio_qa_proof_lane(
        tmp_path,
        packaged_visual_qa_report_evidence="07_LOGS/Studio-Graph-Views/packaged-visual-qa.json",
    )

    assert calls["packaged_visual_qa_report_path"] == "07_LOGS/Studio-Graph-Views/packaged-visual-qa.json"
    assert "--packaged-visual-qa-report-path" in report["proof_commands"]["pass10b_visual_proof_completion_audit"]["argv"]
    assert report["ok"] is True


def test_phase10_studio_qa_proof_lane_rejects_evidence_root_outside_vault(tmp_path: Path) -> None:
    outside_root = Path("/tmp") / "chaseos-phase10-qa-proof-outside"

    with pytest.raises(StudioQARunnerError, match="evidence root must stay inside"):
        run_phase10_studio_qa_proof_lane(
            VAULT_ROOT,
            write_evidence=True,
            evidence_root=outside_root,
        )


def test_studio_qa_runner_cli_can_route_to_phase10_proof_lane(monkeypatch, capsys) -> None:
    from runtime.cli import main as cli_main

    calls = {}

    def fake_phase10_lane(
        vault_root,
        *,
        write_evidence=False,
        evidence_slug=None,
        evidence_root=None,
        local_packaging_proof_evidence=None,
        packaged_visual_qa_report_evidence=None,
    ):
        calls["vault_root"] = vault_root
        calls["write_evidence"] = write_evidence
        calls["evidence_slug"] = evidence_slug
        calls["evidence_root"] = evidence_root
        calls["local_packaging_proof_evidence"] = local_packaging_proof_evidence
        calls["packaged_visual_qa_report_evidence"] = packaged_visual_qa_report_evidence
        return {
            "ok": True,
            "status": "phase10_studio_qa_proof_passed",
            "surface": "studio_phase10_qa_proof_lane",
            "checks_by_surface": {},
            "failure_buckets": {"deterministic_failures": [], "flaky_failures": []},
            "evidence": {"written": True, "markdown_path": "07_LOGS/Studio-Graph-Views/example.md"},
        }

    monkeypatch.setattr(qa_runner, "run_phase10_studio_qa_proof_lane", fake_phase10_lane)

    code = cli_main.cmd_studio_qa_runner(
        argparse.Namespace(
            vault_root=str(VAULT_ROOT),
            phase10_proof_lane=True,
            surface="native-shell",
            mode="static",
            host="127.0.0.1",
            port=8772,
            timeout_seconds=10.0,
            write_evidence=True,
            evidence_slug="example",
            evidence_root="07_LOGS/Studio-Graph-Views",
            local_packaging_proof_evidence="07_LOGS/Studio-Graph-Views/packaging-proof.json",
            packaged_visual_qa_report_evidence="07_LOGS/Studio-Graph-Views/packaged-visual-qa.json",
            output_json=False,
        )
    )

    output = capsys.readouterr().out
    assert code == 0
    assert calls["write_evidence"] is True
    assert calls["evidence_slug"] == "example"
    assert calls["local_packaging_proof_evidence"] == "07_LOGS/Studio-Graph-Views/packaging-proof.json"
    assert calls["packaged_visual_qa_report_evidence"] == "07_LOGS/Studio-Graph-Views/packaged-visual-qa.json"
    assert "Studio Phase 10 QA proof lane: PASS" in output
    assert "deterministic_failures: 0" in output
