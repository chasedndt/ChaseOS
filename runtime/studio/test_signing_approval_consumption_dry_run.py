"""Tests for the Studio signing approval consumption dry-run pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.signing_approval_consumption_dry_run as consumption_module
from runtime.studio.signing_approval_consumption_dry_run import (
    ALREADY_CONSUMED_STATUS,
    BLOCKED_STATUS,
    NEXT_STARTUP_AUTOSTART_APPROVAL_PASS,
    NEXT_SIGNING_APPROVED_EXECUTION_PROOF_PASS,
    READY_STATUS,
    _marker_reservation_dry_run,
    build_studio_signing_approval_consumption_dry_run,
    write_signing_approval_consumption_dry_run_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_review_report(tmp_path: Path, *, artifact_present: bool = True, marker_present: bool = False) -> dict:
    packet_id = "studio-signing-appr-testpacket"
    digest = "a" * 64
    zip_sha = "b" * 64
    manifest_sha = "c" * 64
    installer_marker_sha = "d" * 64
    approval_path = tmp_path / "07_LOGS/Agent-Activity/_studio_signing_approvals/studio-signing-appr-testpacket.json"
    marker_path = (
        tmp_path / "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-testpacket.json"
    )
    payload = {
        "record_type": "studio_signing_approval_artifact",
        "schema_version": "studio.signing_approval_review.v1",
        "status": "studio_signing_approval_artifact_written_no_execution",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "approval_scope": "one_signing_proof_only",
        "approved_installer_execution_marker_sha256": installer_marker_sha,
        "approved_unsigned_portable_zip_sha256": zip_sha,
        "approved_installer_manifest_sha256": manifest_sha,
        "approved_output_root": ".pytest_tmp_env/studio-signing-proof",
        "approval_consumption_required": True,
        "future_single_signing_proof_approved": True,
        "signing_allowed_in_this_pass": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "signing_certificate_read": False,
        "raw_certificate_values_visible": False,
        "signs_artifacts": False,
        "writes_signed_artifact": False,
        "verifies_signature": False,
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
        "status": "studio_signing_approval_artifact_existing_matching_no_execution",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_ready": True,
            "approval_artifact_written": artifact_present,
            "approval_decision_consumed": False,
            "exact_once_marker_exists": marker_present,
            "signing_allowed": False,
            "signing_certificate_read": False,
            "signed_artifact_written": False,
        },
        "source_preview": {
            "signing_approval_packet_preview": {
                "approval_packet_id": packet_id,
                "request_digest_sha256": digest,
            },
            "source_artifacts": {
                "exact_once_marker": {"path": "installer-marker.json", "exists": True, "sha256": installer_marker_sha},
                "portable_zip": {
                    "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                    "exists": True,
                    "sha256": zip_sha,
                },
                "installer_manifest": {
                    "path": ".pytest_tmp_env/studio-installer-proof/manifest/manifest.json",
                    "exists": True,
                    "sha256": manifest_sha,
                },
            },
        },
        "approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_signing_approvals/studio-signing-appr-testpacket.json",
            "exists_after": artifact_present,
            "matches_current_packet": artifact_present,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-testpacket.json",
            "exists": marker_present,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {"path": ".pytest_tmp_env/studio-signing-proof", "exists": False},
            "signed_portable_zip": {
                "path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                "exists": False,
                "size_bytes": 0,
            },
            "signing_manifest": {
                "path": ".pytest_tmp_env/studio-signing-proof/manifest/studio-signing-appr-testpacket-signing-manifest.json",
                "exists": False,
                "size_bytes": 0,
            },
        },
        "checks": {"future_output_paths_clear": True},
        "blockers": [],
    }


def test_signing_consumption_dry_run_validates_current_repo_approval_without_execution() -> None:
    report = build_studio_signing_approval_consumption_dry_run(
        VAULT_ROOT,
        approval_packet_id="studio-signing-appr-c6d0561f9a8f921e",
    )

    marker_path = VAULT_ROOT / report["exact_once_marker_contract"]["path"]
    output_root = VAULT_ROOT / ".pytest_tmp_env/studio-signing-proof"
    already_consumed = report["status"] == ALREADY_CONSUMED_STATUS

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["writes_performed"] is False
        assert report["summary"]["signing_allowed"] is False
        assert report["summary"]["signing_certificate_read"] is False
        assert report["authority"]["consumes_approval_decision"] is False
        assert report["authority"]["writes_idempotency_marker"] is False
        assert report["authority"]["reads_signing_certificate"] is False
        assert report["authority"]["signs_artifacts"] is False
        assert report["authority"]["writes_signed_artifact"] is False
        assert report["blockers"]
        return

    assert report["ok"] is True
    assert report["status"] in {READY_STATUS, ALREADY_CONSUMED_STATUS}
    assert report["summary"]["approval_artifact_present"] is True
    assert report["summary"]["approval_digest_matches"] is True
    assert report["summary"]["approval_scope_valid"] is True
    assert report["summary"]["unsigned_portable_zip_hash_matches"] is True
    assert report["summary"]["installer_manifest_hash_matches"] is True
    assert report["summary"]["exact_once_marker_absent"] is (not already_consumed)
    assert report["summary"]["marker_reservation_proof_passed"] is True
    assert report["summary"]["duplicate_consumption_blocked"] is True
    assert report["summary"]["approval_consumed"] is already_consumed
    assert report["summary"]["exact_once_marker_reserved"] is already_consumed
    assert report["summary"]["signing_allowed"] is False
    assert report["summary"]["signing_certificate_read"] is False
    assert report["summary"]["signed_artifact_written"] is already_consumed
    assert report["writes_performed"] is False
    assert report["authority"]["consumes_approval_decision"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["next_recommended_pass"] == (
        NEXT_STARTUP_AUTOSTART_APPROVAL_PASS if already_consumed else NEXT_SIGNING_APPROVED_EXECUTION_PROOF_PASS
    )
    assert marker_path.exists() is already_consumed
    assert output_root.exists() is already_consumed


def test_signing_consumption_dry_run_blocks_missing_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_signing_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path, artifact_present=False),
    )

    report = build_studio_signing_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "approval_artifact_present" in report["blockers"]
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False


def test_signing_consumption_dry_run_derives_installer_packet_from_existing_artifact(tmp_path: Path, monkeypatch) -> None:
    approval_path = tmp_path / "07_LOGS/Agent-Activity/_studio_signing_approvals/studio-signing-appr-testpacket.json"
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(
        json.dumps(
            {
                "record_type": "studio_signing_approval_artifact",
                "approval_packet_id": "studio-signing-appr-testpacket",
                "approved_installer_approval_packet_id": "studio-installer-build-appr-testpacket",
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_review(*args, **kwargs):
        captured.update(kwargs)
        return _fake_review_report(tmp_path)

    monkeypatch.setattr(consumption_module, "build_studio_signing_approval_review", fake_review)

    report = build_studio_signing_approval_consumption_dry_run(
        tmp_path,
        approval_packet_id="studio-signing-appr-testpacket",
    )

    assert report["ok"] is True
    assert captured["installer_approval_packet_id"] == "studio-installer-build-appr-testpacket"


def test_signing_consumption_dry_run_blocks_existing_marker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_signing_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path, marker_present=True),
    )

    report = build_studio_signing_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "real_marker_absent" in report["blockers"]
    assert "marker_reservation_proof_passed" in report["blockers"]
    assert report["marker_reservation_dry_run"]["first_reservation_allowed"] is False
    assert report["marker_reservation_dry_run"]["duplicate_reservation_blocked"] is True


def test_signing_marker_reservation_dry_run_proves_duplicate_block_without_writing() -> None:
    proof = _marker_reservation_dry_run(marker_exists=False)

    assert proof["proof_mode"] == "in_memory_no_real_marker_write"
    assert proof["first_reservation_allowed"] is True
    assert proof["duplicate_reservation_blocked"] is True
    assert proof["real_marker_written"] is False
    assert proof["proof_passed"] is True


def test_signing_consumption_dry_run_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_SIGNING_APPROVED_EXECUTION_PROOF_PASS,
        "summary": {
            "approval_packet_id": "studio-signing-appr-test",
            "request_digest_sha256": "abc",
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "unsigned_portable_zip_hash_matches": True,
            "installer_manifest_hash_matches": True,
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
            "signed_portable_zip": {"path": "out.zip", "exists": False},
        },
        "checks": {"approval_artifact_present": True},
        "authority": {"writes_signed_artifact": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No signing was attempted."],
    }

    evidence = write_signing_approval_consumption_dry_run_evidence(
        tmp_path,
        report,
        evidence_slug="signing-approval-consumption-dry-run-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
