"""Tests for the no-execution Studio installer-build approval preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.installer_build_approval import (
    NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS,
    NEXT_OPERATOR_REVIEW_PASS,
    NEXT_SIGNING_APPROVAL_PASS,
    build_studio_governed_installer_build_approval,
    write_installer_build_approval_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_governed_installer_build_approval_preview_blocks_execution() -> None:
    report = build_studio_governed_installer_build_approval(VAULT_ROOT)

    if report["ok"] is False:
        assert report["status"] == "blocked_installer_build_approval_preview"
        assert report["blockers"]
        assert report["summary"]["execution_allowed"] is False
        assert report["summary"]["installer_build_allowed"] is False
        assert report["authority"]["writes_approval_artifact"] is False
        assert report["authority"]["builds_installer"] is False
        assert report["authority"]["writes_installer"] is False
        return

    assert report["ok"] is True
    approval_artifact_written = bool(report["summary"]["approval_artifact_written"])
    approved_execution_complete = bool(report["summary"].get("approved_execution_proof_complete"))
    expected_status = (
        "studio_installer_build_approved_execution_proof_complete"
        if approved_execution_complete
        else
        "installer_build_approval_artifact_present_pending_consumption"
        if approval_artifact_written
        else "ready_for_operator_installer_build_approval_review"
    )
    assert report["status"] == expected_status
    assert report["summary"]["release_readiness_governance_ready"] is True
    assert report["summary"]["installer_build_gate_declared"] is True
    assert report["summary"]["approval_packet_preview_ready"] is True
    assert report["summary"]["approval_decision_consumed"] is approved_execution_complete
    assert report["summary"]["execution_allowed"] is False
    assert report["summary"]["installer_build_allowed"] is False
    preview = report["approval_packet_preview"]
    assert preview["approval_packet_id"].startswith("studio-installer-build-appr-")
    assert preview["request_digest_sha256"]
    assert preview["approval_artifact_written"] is approval_artifact_written
    assert preview["execution_allowed_in_this_pass"] is False
    assert report["future_approval_artifact"]["matches_current_packet"] is approval_artifact_written
    assert report["future_approval_artifact"]["write_allowed_in_this_pass"] is False
    assert report["exact_once_marker_contract"]["exists"] is approved_execution_complete
    assert report["exact_once_marker_contract"]["reserved_in_this_pass"] is False
    assert report["checks"]["future_output_paths_clear"] is (not approved_execution_complete)
    assert len(report["dry_run_plan"]) >= 5
    assert len(report["rollback_audit_requirements"]) >= 3
    assert report["authority"]["approval_packet_preview_only"] is True
    assert report["authority"]["creates_approval_artifact"] is False
    assert report["authority"]["writes_approval_artifact"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["writes_packaging_output_root"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["connector_calls_allowed"] is False
    assert report["authority"]["writes_agent_bus_tasks"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["blockers"] == []
    expected_next = (
        NEXT_SIGNING_APPROVAL_PASS
        if approved_execution_complete
        else NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS
        if approval_artifact_written
        else NEXT_OPERATOR_REVIEW_PASS
    )
    assert report["next_recommended_pass"] == expected_next


def test_installer_build_approval_packet_id_is_stable_for_same_inputs() -> None:
    first = build_studio_governed_installer_build_approval(VAULT_ROOT, generated_at="2026-05-06T00:00:00Z")
    second = build_studio_governed_installer_build_approval(VAULT_ROOT, generated_at="2026-05-06T01:00:00Z")

    assert first["approval_packet_preview"]["approval_packet_id"] == second["approval_packet_preview"]["approval_packet_id"]
    assert first["approval_packet_preview"]["request_digest_sha256"] == second["approval_packet_preview"]["request_digest_sha256"]


def test_installer_build_approval_can_bind_existing_completed_packet() -> None:
    packet_id = "studio-installer-build-appr-ac14811da651baec"
    marker = (
        VAULT_ROOT
        / "07_LOGS"
        / "Agent-Activity"
        / "_studio_installer_build_approvals"
        / "_execution_markers"
        / f"{packet_id}.json"
    )
    if not marker.is_file():
        return

    report = build_studio_governed_installer_build_approval(
        VAULT_ROOT,
        approval_packet_id=packet_id,
    )

    assert report["ok"] is True
    assert report["status"] == "studio_installer_build_approved_execution_proof_complete"
    assert report["summary"]["approval_packet_id"] == packet_id
    assert report["summary"]["approved_execution_proof_complete"] is True
    assert report["summary"]["approval_decision_consumed"] is True
    assert report["summary"]["execution_allowed"] is False
    assert report["summary"]["installer_build_allowed"] is False
    assert report["next_recommended_pass"] == NEXT_SIGNING_APPROVAL_PASS
    assert report["authority"]["writes_approval_artifact"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False


def test_installer_build_approval_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": "ready_for_operator_installer_build_approval_review",
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_OPERATOR_REVIEW_PASS,
        "approval_packet_preview": {
            "approval_packet_id": "studio-installer-build-appr-test",
            "request_digest_sha256": "abc",
        },
        "future_approval_artifact": {"path": "approval.json", "exists": False},
        "exact_once_marker_contract": {"path": "marker.json", "exists": False},
        "future_output_paths": {
            "portable_zip": {"path": "out.zip", "exists": False},
        },
        "dry_run_plan": [{"step": "verify_approval_artifact", "required": True, "effect_now": "preview_only"}],
        "authority": {"writes_installer": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No installer build was attempted."],
    }

    evidence = write_installer_build_approval_evidence(
        tmp_path,
        report,
        evidence_slug="installer-build-approval-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
