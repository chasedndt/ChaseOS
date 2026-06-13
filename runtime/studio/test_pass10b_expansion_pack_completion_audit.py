"""Tests for the read-only Pass 10B expansion-pack completion audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import runtime.studio.pass10b_expansion_pack_completion_audit as audit_module
from runtime.studio.pass10b_expansion_pack_completion_audit import (
    COMPLETE_STATUS,
    DEFAULT_APPROVAL_PACKET_ID,
    NEXT_EXECUTION_PASS,
    NEXT_SIGNING_APPROVAL_PASS,
    PARTIAL_STATUS,
    build_pass10b_expansion_pack_completion_audit,
    build_pass10b_operator_handoff_integrity_verifier,
    format_pass10b_expansion_pack_completion_audit,
    format_pass10b_operator_handoff_integrity_verifier,
    format_pass10b_operator_execution_handoff,
    write_pass10b_expansion_pack_completion_audit,
    write_pass10b_operator_execution_handoff,
)


def _installer_plan() -> dict:
    return {
        "ok": True,
        "status": "ready_for_studio_installer_build_plan",
        "evidence": {
            "pass10b_completion_audit": {
                "path": "07_LOGS/Studio-Graph-Views/pass10b-completion-audits/current.json",
                "exists": True,
                "ok": True,
                "status": "COMPLETE / VERIFIED",
                "native_packaged_visual_qa_complete": True,
                "packaged_visual_qa_saved_report_valid": True,
            }
        },
    }


def _approval_review() -> dict:
    return {
        "ok": True,
        "status": "studio_installer_build_approval_artifact_existing_matching_no_execution",
        "summary": {
            "approval_packet_id": DEFAULT_APPROVAL_PACKET_ID,
            "request_digest_sha256": "a" * 64,
            "approval_artifact_written": True,
            "future_single_build_approved": True,
            "approval_decision_consumed": False,
        },
        "authority": {
            "signs_artifacts": False,
            "writes_host_startup": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _consumption_dry_run() -> dict:
    return {
        "ok": True,
        "status": "studio_installer_build_approval_consumption_dry_run_ready_no_execution",
        "summary": {
            "approval_digest_matches": True,
            "marker_reservation_proof_passed": True,
            "duplicate_consumption_blocked": True,
            "approval_consumed": False,
        },
        "authority": {
            "signs_artifacts": False,
            "writes_host_startup": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _execution_readiness() -> dict:
    return {
        "ok": True,
        "status": "ready_for_studio_installer_build_approved_execution_proof",
        "summary": {
            "execution_requested": False,
            "execution_performed": False,
            "already_executed": False,
            "approval_consumed": False,
            "future_output_paths_clear": True,
        },
        "paths": {
            "exact_once_marker": {
                "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/"
                f"{DEFAULT_APPROVAL_PACKET_ID}.json",
                "exists": False,
            },
            "output_root": {"path": ".pytest_tmp_env/studio-installer-proof", "exists": False},
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": False,
            },
            "build_manifest": {
                "path": f".pytest_tmp_env/studio-installer-proof/manifest/{DEFAULT_APPROVAL_PACKET_ID}-installer-build-manifest.json",
                "exists": False,
            },
            "execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{DEFAULT_APPROVAL_PACKET_ID}-installer-build-execution.json",
                "exists": False,
            },
        },
        "preflight_checks": {"approval_artifact_present": True},
        "authority": {
            "signs_artifacts": False,
            "writes_host_startup": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _execution_complete() -> dict:
    return {
        "ok": True,
        "status": "studio_installer_build_approved_execution_proof_complete",
        "summary": {
            "execution_requested": False,
            "execution_performed": False,
            "already_executed": True,
            "approval_consumed": True,
            "duplicate_execution_blocked": True,
            "portable_zip_exists": True,
            "manifest_exists": True,
            "portable_zip_sha256": "b" * 64,
            "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS,
        },
        "paths": {
            "exact_once_marker": {
                "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/"
                f"{DEFAULT_APPROVAL_PACKET_ID}.json",
                "exists": True,
            },
            "output_root": {"path": ".pytest_tmp_env/studio-installer-proof", "exists": True},
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": True,
            },
            "build_manifest": {
                "path": f".pytest_tmp_env/studio-installer-proof/manifest/{DEFAULT_APPROVAL_PACKET_ID}-installer-build-manifest.json",
                "exists": True,
            },
            "execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{DEFAULT_APPROVAL_PACKET_ID}-installer-build-execution.json",
                "exists": True,
            },
        },
        "post_execution_checks": {
            "approval_consumed_by_marker": True,
            "exact_once_marker_exists": True,
            "duplicate_execution_blocked": True,
            "portable_zip_exists": True,
            "manifest_exists": True,
            "execution_evidence_exists": True,
            "signing_startup_release_still_blocked": True,
        },
        "authority": {
            "signs_artifacts": False,
            "writes_host_startup": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _card_inventory() -> dict:
    return {
        "ok": True,
        "status": "card_inventory_packet_ready_pass10b_current_audit_green",
        "summary": {
            "pass10b_current_green": True,
            "live_registry_mounted_panel_count": 32,
            "approval_gated_panel_count": 4,
            "full_desktop_card_ui_closed": False,
        },
        "evidence": {
            "current_pass10b_completion_audit": {
                "path": "07_LOGS/Studio-Graph-Views/pass10b-completion-audits/current.json",
                "status": "COMPLETE / VERIFIED",
            },
            "latest_webview2_operator_remediation_packet": {
                "path": "07_LOGS/Studio-Graph-Views/webview2-operator-remediation-packets/current.json",
                "exists": True,
                "status": "webview2_operator_remediation_packet_ready_for_operator",
            },
        },
        "authority": {
            "signs_artifacts": False,
            "writes_host_startup": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _patch_builders(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audit_module, "build_studio_installer_plan", lambda *args, **kwargs: _installer_plan())
    monkeypatch.setattr(
        audit_module,
        "build_studio_installer_build_approval_review",
        lambda *args, **kwargs: _approval_review(),
    )
    monkeypatch.setattr(
        audit_module,
        "build_studio_installer_build_approval_consumption_dry_run",
        lambda *args, **kwargs: _consumption_dry_run(),
    )
    monkeypatch.setattr(
        audit_module,
        "build_studio_installer_build_approved_execution_proof",
        lambda *args, **kwargs: _execution_readiness(),
    )
    monkeypatch.setattr(
        audit_module,
        "build_full_desktop_card_ui_inventory_proof",
        lambda *args, **kwargs: _card_inventory(),
    )


def test_expansion_pack_audit_reports_not_complete_until_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_builders(monkeypatch)

    report = build_pass10b_expansion_pack_completion_audit(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
    )

    checklist = {row["id"]: row for row in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is False
    assert report["complete"] is False
    assert report["status"] == PARTIAL_STATUS
    assert checklist["pass10b_visual_proof_current"]["ok"] is True
    assert checklist["installer_build_approval_artifact_written"]["ok"] is True
    assert checklist["installer_build_consumption_dry_run_verified"]["ok"] is True
    assert checklist["installer_build_execution_readiness_verified"]["ok"] is True
    assert checklist["installer_build_approved_execution_performed"]["ok"] is False
    assert checklist["no_forbidden_mutation"]["ok"] is True
    assert report["summary"]["approved_execution_performed"] is False
    assert report["summary"]["installer_outputs_present"] is False
    assert report["operator_execution_handoff"]["status"] == "READY_FOR_OPERATOR_APPROVAL"
    assert "--execute" in report["operator_execution_handoff"]["execution_command"]
    assert DEFAULT_APPROVAL_PACKET_ID in report["operator_execution_handoff"]["execution_command"]
    assert "post-execution-audit" in report["operator_execution_handoff"]["post_execution_audit_command"]
    assert report["next_recommended_pass"] == NEXT_EXECUTION_PASS


def test_expansion_pack_audit_reports_complete_after_approved_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_builders(monkeypatch)
    monkeypatch.setattr(
        audit_module,
        "build_studio_installer_build_approved_execution_proof",
        lambda *args, **kwargs: _execution_complete(),
    )

    report = build_pass10b_expansion_pack_completion_audit(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
    )

    checklist = {row["id"]: row for row in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is True
    assert report["complete"] is True
    assert report["status"] == COMPLETE_STATUS
    assert checklist["installer_build_approval_artifact_written"]["ok"] is True
    assert checklist["installer_build_consumption_dry_run_verified"]["ok"] is True
    assert checklist["installer_build_execution_readiness_verified"]["ok"] is True
    assert checklist["installer_build_approved_execution_performed"]["ok"] is True
    assert "blocker" not in checklist["installer_build_approved_execution_performed"]
    assert checklist["no_forbidden_mutation"]["ok"] is True
    assert checklist["no_forbidden_mutation"]["evidence"]["approved_execution_state_valid"] is True
    assert report["operator_execution_handoff"]["status"] == "EXECUTION_COMPLETE"
    assert report["operator_execution_handoff"]["requires_explicit_operator_approval"] is False
    assert report["next_recommended_pass"] == NEXT_SIGNING_APPROVAL_PASS


def test_expansion_pack_audit_writer_stays_inside_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_builders(monkeypatch)

    report = write_pass10b_expansion_pack_completion_audit(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
        report_slug="test-pass10b-expansion-pack",
    )

    assert report["written_report"] == (
        "07_LOGS/Studio-Graph-Views/pass10b-expansion-pack-completion-audits/test-pass10b-expansion-pack.json"
    )
    written = tmp_path / report["written_report"]
    assert written.is_file()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["complete"] is False

    with pytest.raises(ValueError):
        write_pass10b_expansion_pack_completion_audit(
            tmp_path,
            output_path=tmp_path.parent / "escaped.json",
        )


def test_expansion_pack_audit_text_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_builders(monkeypatch)

    report = build_pass10b_expansion_pack_completion_audit(tmp_path)
    output = format_pass10b_expansion_pack_completion_audit(report)

    assert "Pass 10B expansion-pack completion audit" in output
    assert "complete: False" in output
    assert "approved_execution_performed: False" in output
    assert "handoff_status: READY_FOR_OPERATOR_APPROVAL" in output
    assert "--execute" in output
    assert NEXT_EXECUTION_PASS in output


def test_operator_execution_handoff_markdown_writer_stays_inside_vault(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_builders(monkeypatch)

    report = write_pass10b_operator_execution_handoff(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
        report_slug="test-pass10b-execution",
    )

    assert report["written_handoff"] == (
        "07_LOGS/Studio-Graph-Views/pass10b-expansion-pack-completion-audits/"
        "test-pass10b-execution-operator-handoff.md"
    )
    written = tmp_path / report["written_handoff"]
    assert written.is_file()
    content = written.read_text(encoding="utf-8")
    assert report["written_handoff_sha256"] == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert report["written_handoff_size_bytes"] == len(content.encode("utf-8"))
    text_output = format_pass10b_expansion_pack_completion_audit(report)
    assert f"handoff_sha256: {report['written_handoff_sha256']}" in text_output
    assert f"handoff_size_bytes: {report['written_handoff_size_bytes']}" in text_output
    assert "Pass 10B Execution Operator Handoff" in content
    assert "READY_FOR_OPERATOR_APPROVAL" in content
    assert DEFAULT_APPROVAL_PACKET_ID in content
    assert "--execute" in content
    assert "Forbidden Even If Approved" in content
    assert "No duplicate policy recorded" not in content

    with pytest.raises(ValueError):
        write_pass10b_operator_execution_handoff(
            tmp_path,
            output_path=tmp_path.parent / "escaped.md",
        )


def test_operator_execution_handoff_updates_written_json_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_builders(monkeypatch)

    report = write_pass10b_expansion_pack_completion_audit(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
        report_slug="test-pass10b-with-handoff",
    )
    report = write_pass10b_operator_execution_handoff(
        tmp_path,
        report=report,
        report_slug="test-pass10b-with-handoff",
    )

    written_report = tmp_path / report["written_report"]
    payload = json.loads(written_report.read_text(encoding="utf-8"))
    assert payload["written_handoff"] == report["written_handoff"]
    assert payload["written_handoff_sha256"] == report["written_handoff_sha256"]
    assert payload["written_handoff_size_bytes"] == report["written_handoff_size_bytes"]


def test_operator_handoff_integrity_verifier_matches_written_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_builders(monkeypatch)

    report = write_pass10b_expansion_pack_completion_audit(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
        report_slug="test-pass10b-integrity",
    )
    report = write_pass10b_operator_execution_handoff(
        tmp_path,
        report=report,
        report_slug="test-pass10b-integrity",
    )

    integrity = build_pass10b_operator_handoff_integrity_verifier(
        tmp_path,
        report_path=report["written_report"],
        generated_at="2026-05-12T00:01:00Z",
    )
    output = format_pass10b_operator_handoff_integrity_verifier(integrity)

    assert integrity["ok"] is True
    assert integrity["summary"]["digest_matches"] is True
    assert integrity["summary"]["size_matches"] is True
    assert integrity["summary"]["no_execution"] is True
    assert integrity["blockers"] == []
    assert "digest_matches: True" in output


def test_operator_handoff_integrity_verifier_blocks_tampered_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_builders(monkeypatch)

    report = write_pass10b_expansion_pack_completion_audit(
        tmp_path,
        generated_at="2026-05-12T00:00:00Z",
        report_slug="test-pass10b-tampered",
    )
    report = write_pass10b_operator_execution_handoff(
        tmp_path,
        report=report,
        report_slug="test-pass10b-tampered",
    )
    handoff_path = tmp_path / report["written_handoff"]
    handoff_path.write_text(handoff_path.read_text(encoding="utf-8") + "\nTampered.\n", encoding="utf-8")

    integrity = build_pass10b_operator_handoff_integrity_verifier(
        tmp_path,
        report_path=report["written_report"],
        generated_at="2026-05-12T00:01:00Z",
    )

    assert integrity["ok"] is False
    assert integrity["summary"]["digest_matches"] is False
    assert integrity["summary"]["size_matches"] is False
    assert "handoff_sha256_mismatch" in integrity["blockers"]
    assert "handoff_size_mismatch" in integrity["blockers"]


def test_operator_execution_handoff_markdown_format_contains_expected_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_builders(monkeypatch)

    report = build_pass10b_expansion_pack_completion_audit(tmp_path)
    content = format_pass10b_operator_execution_handoff(report)

    assert "## Execution Command" in content
    assert "## Post-Execution Audit Command" in content
    assert "exact_once_marker" in content
    assert "portable_zip" in content
    assert "canonical ChaseOS mutation" in content
