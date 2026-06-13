"""Tests for the Studio installer-build approval consumption dry-run pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.installer_build_approval_consumption_dry_run as consumption_module
from runtime.studio.installer_build_approval_consumption_dry_run import (
    ALREADY_CONSUMED_STATUS,
    BLOCKED_STATUS,
    NEXT_APPROVED_EXECUTION_PROOF_PASS,
    NEXT_SIGNING_APPROVAL_PASS,
    READY_STATUS,
    _marker_reservation_dry_run,
    build_studio_installer_build_approval_consumption_dry_run,
    write_installer_build_approval_consumption_dry_run_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_review_report(tmp_path: Path, *, artifact_present: bool = True, marker_present: bool = False) -> dict:
    packet_id = "studio-installer-build-appr-testpacket"
    digest = "a" * 64
    executable_sha = "b" * 64
    approval_path = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_installer_build_approvals/studio-installer-build-appr-testpacket.json"
    )
    marker_path = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-testpacket.json"
    )
    payload = {
        "record_type": "studio_installer_build_approval_artifact",
        "schema_version": "studio.installer_build_approval_review.v1",
        "status": "studio_installer_build_approval_artifact_written_no_execution",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "approval_scope": "one_installer_build_only",
        "approved_installer_format": "zip-portable",
        "approved_output_root": ".pytest_tmp_env/studio-installer-proof",
        "approved_packaged_executable_sha256": executable_sha,
        "approval_consumption_required": True,
        "future_single_build_approved": True,
        "execution_allowed_in_this_pass": False,
        "installer_build_allowed_in_this_pass": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "builds_executable": False,
        "builds_installer": False,
        "writes_installer": False,
        "writes_packaging_output_root": False,
        "signing_allowed": False,
        "reads_signing_certificate": False,
        "startup_mutation_allowed": False,
        "autostart_registration_allowed": False,
        "registry_write_allowed": False,
        "start_menu_write_allowed": False,
        "desktop_shortcut_write_allowed": False,
        "release_promotion_allowed": False,
        "release_status_write_allowed": False,
        "pywebview_launch_allowed": False,
        "server_start_allowed": False,
        "executable_launch_allowed": False,
        "browser_use_cli_live_run": False,
        "excalidraw_live_proof": False,
        "mutates_gate": False,
        "executes_workflows": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "writes_agent_bus_tasks": False,
        "canonical_mutation_allowed": False,
    }
    if artifact_present:
        approval_path.parent.mkdir(parents=True, exist_ok=True)
        approval_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if marker_present:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(json.dumps({"record_type": "marker"}), encoding="utf-8")
    return {
        "ok": True,
        "status": "studio_installer_build_approval_artifact_existing_matching_no_execution",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_ready": True,
            "approval_artifact_written": artifact_present,
            "approval_decision_consumed": False,
            "exact_once_marker_exists": marker_present,
            "execution_allowed": False,
            "installer_build_allowed": False,
        },
        "source_preview": {
            "approval_packet_preview": {
                "approval_packet_id": packet_id,
                "request_digest_sha256": digest,
                "packaged_executable_sha256": executable_sha,
            }
        },
        "approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/studio-installer-build-appr-testpacket.json",
            "exists_after": artifact_present,
            "matches_current_packet": artifact_present,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-testpacket.json",
            "exists": marker_present,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {"path": ".pytest_tmp_env/studio-installer-proof", "exists": False},
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": False,
                "size_bytes": 0,
            },
            "build_manifest": {
                "path": ".pytest_tmp_env/studio-installer-proof/manifest/studio-installer-build-appr-testpacket-installer-build-manifest.json",
                "exists": False,
                "size_bytes": 0,
            },
        },
        "checks": {"future_output_paths_clear": True},
        "blockers": [],
    }


def test_consumption_dry_run_validates_current_repo_approval_without_execution() -> None:
    report = build_studio_installer_build_approval_consumption_dry_run(
        VAULT_ROOT,
        approval_packet_id="studio-installer-build-appr-4efe404083dae669",
    )

    marker_path = VAULT_ROOT / report["exact_once_marker_contract"]["path"]
    output_root = VAULT_ROOT / ".pytest_tmp_env/studio-installer-proof"
    already_consumed = report["status"] == ALREADY_CONSUMED_STATUS

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["blockers"]
        assert report["summary"]["execution_allowed"] is False
        assert report["summary"]["installer_build_allowed"] is False
        assert report["writes_performed"] is False
        assert report["authority"]["consumes_approval_decision"] is False
        assert report["authority"]["writes_idempotency_marker"] is False
        assert report["authority"]["writes_installer"] is False
        return

    assert report["ok"] is True
    assert report["status"] in {READY_STATUS, ALREADY_CONSUMED_STATUS}
    assert report["summary"]["approval_artifact_present"] is True
    assert report["summary"]["approval_digest_matches"] is True
    assert report["summary"]["approval_scope_valid"] is True
    assert report["summary"]["exact_once_marker_absent"] is (not already_consumed)
    assert report["summary"]["marker_reservation_proof_passed"] is True
    assert report["summary"]["duplicate_consumption_blocked"] is True
    assert report["summary"]["approval_consumed"] is already_consumed
    assert report["summary"]["exact_once_marker_reserved"] is already_consumed
    assert report["summary"]["execution_allowed"] is False
    assert report["summary"]["installer_build_allowed"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["consumes_approval_decision"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["next_recommended_pass"] == (
        NEXT_SIGNING_APPROVAL_PASS if already_consumed else NEXT_APPROVED_EXECUTION_PROOF_PASS
    )
    assert marker_path.exists() is already_consumed
    assert output_root.exists() is already_consumed


def test_consumption_dry_run_blocks_missing_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_installer_build_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path, artifact_present=False),
    )

    report = build_studio_installer_build_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "approval_artifact_present" in report["blockers"]
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False


def test_consumption_dry_run_blocks_existing_marker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_installer_build_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path, marker_present=True),
    )

    report = build_studio_installer_build_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "real_marker_absent" in report["blockers"]
    assert "marker_reservation_proof_passed" in report["blockers"]
    assert report["marker_reservation_dry_run"]["first_reservation_allowed"] is False
    assert report["marker_reservation_dry_run"]["duplicate_reservation_blocked"] is True


def test_marker_reservation_dry_run_proves_duplicate_block_without_writing() -> None:
    proof = _marker_reservation_dry_run(marker_exists=False)

    assert proof["proof_mode"] == "in_memory_no_real_marker_write"
    assert proof["first_reservation_allowed"] is True
    assert proof["duplicate_reservation_blocked"] is True
    assert proof["real_marker_written"] is False
    assert proof["proof_passed"] is True


def test_consumption_dry_run_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_APPROVED_EXECUTION_PROOF_PASS,
        "summary": {
            "approval_packet_id": "studio-installer-build-appr-test",
            "request_digest_sha256": "abc",
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "approval_consumed": False,
        },
        "approval_artifact": {"path": "approval.json"},
        "exact_once_marker_contract": {"path": "marker.json", "exists": False},
        "marker_reservation_dry_run": {
            "real_marker_written": False,
            "first_reservation_allowed": True,
            "duplicate_reservation_blocked": True,
            "proof_passed": True,
        },
        "future_output_paths": {
            "portable_zip": {"path": "out.zip", "exists": False},
        },
        "checks": {"approval_artifact_present": True},
        "authority": {"writes_installer": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No installer build was attempted."],
    }

    evidence = write_installer_build_approval_consumption_dry_run_evidence(
        tmp_path,
        report,
        evidence_slug="installer-build-approval-consumption-dry-run-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
