"""Tests for the read-only Studio release-readiness governance gate."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.release_readiness_governance import (
    NEXT_INSTALLER_APPROVAL_PASS,
    REQUIRED_GATE_IDS,
    build_studio_release_readiness_governance,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_release_readiness_governance_requires_approval_before_release_actions() -> None:
    report = build_studio_release_readiness_governance(VAULT_ROOT)

    assert report["ok"] is True
    assert report["status"] == "ready_for_operator_release_governance_review"
    assert report["summary"]["product_hardening_ready"] is True
    assert report["summary"]["installer_plan_ready"] is True
    assert report["summary"]["all_required_gates_declared"] is True
    assert report["summary"]["release_actions_allowed"] is False
    assert report["summary"]["next_recommended_pass"] == NEXT_INSTALLER_APPROVAL_PASS
    assert report["readiness"]["operator_approval_required_before_release_actions"] is True
    assert report["readiness"]["approval_artifacts_required_before_execution"] is True
    assert report["readiness"]["dry_run_required_before_write"] is True
    assert report["readiness"]["exact_once_marker_required_before_write"] is True
    assert report["readiness"]["rollback_audit_required_before_host_mutation"] is True
    assert report["readiness"]["release_actions_allowed"] is False
    gate_ids = {item["id"] for item in report["approval_requirements"]}
    assert set(REQUIRED_GATE_IDS).issubset(gate_ids)
    assert all(item["execution_allowed"] is False for item in report["approval_requirements"])
    assert all(item["approval_artifact_present"] is False for item in report["approval_requirements"])
    assert report["authority"]["creates_approval_artifact"] is False
    assert report["authority"]["executes_approval_decisions"] is False
    assert report["authority"]["builds_executable"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["writes_release_status"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["connector_calls_allowed"] is False
    assert report["authority"]["writes_agent_bus_tasks"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["blockers"] == []
    assert report["source_contracts"]["product_hardening_status"]["status"] == "studio_product_hardened_ready_for_release_governance"
    assert report["source_contracts"]["installer_plan"]["status"] == "ready_for_governed_installer_design"
    assert report["next_recommended_pass"] == NEXT_INSTALLER_APPROVAL_PASS
