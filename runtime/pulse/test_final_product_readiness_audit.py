from __future__ import annotations

from pathlib import Path

from runtime.pulse.final_product_readiness_audit import (
    BLOCKED_EFFECTS,
    build_pulse_final_product_readiness_audit,
)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_final_product_readiness_audit_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    audit = build_pulse_final_product_readiness_audit(
        vault,
        generated_at="2026-05-03T04:10:00+01:00",
    )

    assert _snapshot(vault) == before
    assert audit.current_v1_local_lane_complete is False
    assert audit.full_product_grade_complete is False
    assert audit.read_only is True
    assert audit.writes_audit_artifact is False
    assert audit.agent_bus_task_write_allowed is False
    assert audit.schedule_activation_allowed is False
    assert audit.canonical_writeback_allowed is False
    assert audit.rd_workbook_update_allowed is False
    assert set(audit.blocked_effects) == set(BLOCKED_EFFECTS)


def test_final_product_readiness_audit_validates_authority_flags(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    payload = build_pulse_final_product_readiness_audit(vault).to_dict()

    assert payload["read_only"] is True
    assert payload["local_only"] is True
    assert payload["applies_candidates"] is False
    assert payload["mutates_memory"] is False
    assert payload["mutates_personal_map"] is False
    assert payload["updates_runtime_brains"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["second_datastore_created"] is False
    assert "interactive_pulse_governed_controls" in payload["remaining_full_product_lanes"]
    assert "personal_map_live_apply_proof_and_interactive_ui" in payload["remaining_full_product_lanes"]


def test_final_product_readiness_audit_reports_current_repo_status() -> None:
    vault = Path(__file__).resolve().parents[2]

    audit = build_pulse_final_product_readiness_audit(vault)
    payload = audit.to_dict()

    assert payload["audit_status"] in {
        "current_v1_local_lane_complete_full_product_partial",
        "partial",
    }
    assert payload["full_product_grade_complete"] is False
    assert payload["prior_pass_count"] <= payload["expected_prior_pass_count"]
    assert payload["live_surface_summary"]["runtime_brain_dashboard"]["status"] in {
        "runtime_brain_dashboard_contract_ready",
        "runtime_brain_dashboard_contract_partial",
        "runtime_brain_dashboard_contract_empty",
        "runtime_brain_dashboard_contract_blocked",
    }
    assert payload["live_surface_summary"]["connector_source_scanner_readiness"]["status"] in {
        "contract_ready_live_execution_blocked",
        "partial",
        "missing",
    }
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["status"] in {
        "runner_ready_activation_blocked",
        "runner_partial_manifest_gap",
    }
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["schedule_daemon_started"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["schedule_manifest_written"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["schedule_activation_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["run_queue_written"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["agent_bus_task_write_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["runtime_dispatch_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["workflow_execution_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_runner_proof"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["status"] in {
        "blocked_missing_activation_evidence",
        "ready_for_operator_supervised_activation",
        "missing",
    }
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["approval_granted"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["approval_execution_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["schedule_activation_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["schedule_manifest_write_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["schedule_daemon_started"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["run_queue_written"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["agent_bus_task_write_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["runtime_dispatch_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["workflow_execution_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["external_scheduler_install_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_activation_gate"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["status"] in {
        "blocked_activation_gate_not_ready",
        "run_queue_audit_proof_ready",
        "missing",
    }
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["real_run_queue_written"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["real_audit_event_written"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["schedule_activation_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["schedule_manifest_write_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["schedule_daemon_started"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["agent_bus_task_write_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["runtime_dispatch_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["workflow_execution_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["approval_execution_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["external_scheduler_install_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_run_queue_audit_proof"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["status"] in {
        "blocked_activation_gate_not_ready",
        "ready_for_supervised_activation_execution",
        "missing",
    }
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["execute_requested"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["write_executed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["manifest_patch_count"] == 0
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["schedule_manifest_write_executed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["schedule_activation_executed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["schedule_daemon_started"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["real_run_queue_written"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["real_audit_event_written"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["agent_bus_task_write_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["runtime_dispatch_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["workflow_execution_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["external_scheduler_install_allowed"] is False
    assert payload["live_surface_summary"]["native_schedule_supervised_activation_execution"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_readiness"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_readiness"]["unrestricted_web_scan_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_local_preview"]["status"] in {
        "ready",
        "empty",
        "partial",
    }
    assert payload["live_surface_summary"]["connector_source_scanner_local_preview"]["source_content_read"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_local_preview"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_local_preview"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_candidate_cards"]["status"] in {
        "ready",
        "empty",
    }
    assert payload["live_surface_summary"]["connector_source_scanner_candidate_cards"]["source_content_read"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_candidate_cards"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_candidate_cards"]["source_promotion_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_candidate_cards"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["status"] in {
        "blocked_missing_operator_permission_envelope",
        "blocked_no_external_connector_targets",
    }
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["source_content_read"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["approval_granted"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["approval_execution_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["source_promotion_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_approved_proof"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["status"] in {
        "blocked_missing_operator_permission_envelope",
        "ready_for_live_connector_execution",
        "blocked_missing_live_connector_runner",
    }
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["connector_id"] == "acquisition_rss_live"
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["execute_requested"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["write_executed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["connector_runner_bound"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["live_connector_execution_executed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["provider_or_connector_call_executed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["source_content_read"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["unrestricted_web_scan_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["browser_history_ingest_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["credential_or_secret_read_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["schedule_activation_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["agent_bus_task_write_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["approval_granted"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["approval_execution_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["source_promotion_allowed"] is False
    assert payload["live_surface_summary"]["connector_source_scanner_live_execution_proof"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["visual_card_deck_shell"]["status"] in {
        "first_static_shell_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["pulse_product_shell"]["status"] in {
        "first_integrated_static_shell_present",
        "browser_qa_and_panel_contract_present",
        "studio_read_only_mount_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["pulse_product_shell"]["starts_server"] is False
    assert payload["live_surface_summary"]["pulse_product_shell"]["studio_panel_contract_present"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["pulse_product_shell"]["studio_read_only_mount_present"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["pulse_product_shell"]["interactive_governed_controls_present"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["pulse_product_shell"]["interactive_governed_controls_complete"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["personal_map_visualization"]["status"] in {
        "first_contract_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["personal_map_review_apply"]["status"] in {
        "first_static_surface_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["personal_map_review_apply"]["surface_runs_live_apply"] is False
    assert payload["live_surface_summary"]["personal_map_live_apply_proof"]["status"] in {
        "first_static_proof_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["personal_map_live_apply_proof"]["surface_runs_live_apply"] is False
    assert payload["live_surface_summary"]["personal_map_live_apply_proof"]["writes_runtime_memory_graph"] is False
    assert payload["live_surface_summary"]["personal_map_apply_transaction_proof"]["status"] in {
        "blocked_no_ready_personal_map_candidates",
        "proof_artifact_present",
        "transaction_proof_ready",
    }
    assert payload["live_surface_summary"]["personal_map_apply_transaction_proof"]["live_apply_allowed"] is False
    assert payload["live_surface_summary"]["personal_map_apply_transaction_proof"]["applies_personal_map_candidates"] is False
    assert payload["live_surface_summary"]["personal_map_apply_transaction_proof"]["writes_runtime_memory_graph"] is False
    assert payload["live_surface_summary"]["personal_map_apply_transaction_proof"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["status"] in {
        "local_v1_product_grade_ready_external_lanes_deferred",
        "not_present",
    }
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["full_product_grade_complete"] is False
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["rd_workbook_final_sync_complete"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["provider_or_connector_call_allowed"] is False
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["schedule_activation_allowed"] is False
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["approval_execution_allowed"] is False
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["canonical_writeback_allowed"] is False
    assert payload["live_surface_summary"]["product_grade_local_closeout"]["rd_workbook_update_allowed"] is False
    assert payload["live_surface_summary"]["runtime_brain_visualization"]["status"] in {
        "first_static_ui_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["runtime_brain_visualization"]["updates_runtime_brains"] is False
    assert payload["live_surface_summary"]["approval_queue_ui"]["status"] in {
        "studio_read_only_mount_present",
        "first_static_ui_present",
        "not_present",
    }
    assert payload["live_surface_summary"]["approval_queue_ui"]["studio_panel_mount_present"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["approval_queue_ui"]["full_approval_queue_ui_complete"] in {
        True,
        False,
    }
    assert payload["live_surface_summary"]["approval_queue_ui"]["grants_approvals"] is False
