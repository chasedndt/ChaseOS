"""Tests for the read-only Studio product hardening status."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.product_hardening_status import (
    NEXT_RELEASE_GOVERNANCE_PASS,
    build_studio_product_hardening_status,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_product_hardening_status_composes_phase10_truth_without_authority() -> None:
    report = build_studio_product_hardening_status(VAULT_ROOT)

    assert report["ok"] is True
    assert report["status"] == "studio_product_hardened_ready_for_release_governance"
    assert report["product_lane"]["primary_command"] == "chaseos studio shell"
    assert report["summary"]["native_shell_primary"] is True
    assert report["summary"]["mounted_panel_count"] >= 13
    assert report["summary"]["browser_runtime_production_complete"] is True
    assert report["summary"]["installer_governance_ready"] is True
    assert report["summary"]["release_governance_deferred"] is True
    assert report["readiness"]["required_evidence_present"] is True
    assert report["readiness"]["no_mutation_authority"] is True
    assert report["readiness"]["product_hardening_status_ready"] is True
    assert report["readiness"]["next_recommended_pass"] == NEXT_RELEASE_GOVERNANCE_PASS
    assert report["blockers"] == []
    assert report["authority"]["launches_pywebview"] is False
    assert report["authority"]["starts_servers"] is False
    assert report["authority"]["builds_executable"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["browser_use_cli_live_run"] is False
    assert report["authority"]["excalidraw_live_proof"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["connector_calls_allowed"] is False
    assert report["authority"]["writes_agent_bus_tasks"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["source_contracts"]["panel_registry"]["next_recommended_pass"]
    assert report["source_contracts"]["installer_plan"]["status"] == "ready_for_governed_installer_design"
    assert report["source_contracts"]["installer_plan"]["next_recommended_pass"] == "studio-governed-installer-build-approval"
    assert report["next_recommended_pass"] == NEXT_RELEASE_GOVERNANCE_PASS





