"""Tests for the governed Studio signing approved execution proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import runtime.studio.signing_approved_execution_proof as proof_module
from runtime.studio.signing_approved_execution_proof import (
    BLOCKED_STATUS,
    COMPLETE_STATUS,
    DUPLICATE_BLOCKED_STATUS,
    NEXT_STARTUP_AUTOSTART_APPROVAL_PASS,
    READY_STATUS,
    build_studio_signing_approved_execution_proof,
    write_signing_approved_execution_proof_evidence,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_zip(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ChaseOS-Studio/ChaseOS-Studio.exe", b"fake executable")


def _fake_consumption_report(tmp_path: Path, *, packet_id: str = "studio-signing-appr-testpacket") -> dict:
    digest = "a" * 64
    unsigned_zip = tmp_path / ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip"
    _write_zip(unsigned_zip)
    installer_manifest = tmp_path / ".pytest_tmp_env/studio-installer-proof/manifest/installer-manifest.json"
    installer_manifest.parent.mkdir(parents=True, exist_ok=True)
    installer_manifest.write_text(json.dumps({"record_type": "studio_installer_build_manifest"}), encoding="utf-8")
    installer_marker = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-test.json"
    )
    installer_marker.parent.mkdir(parents=True, exist_ok=True)
    installer_marker.write_text(json.dumps({"record_type": "studio_installer_build_execution_marker"}), encoding="utf-8")
    approval_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_signing_approvals/{packet_id}.json"
    marker_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/{packet_id}.json"
    output_root = tmp_path / ".pytest_tmp_env/studio-signing-proof"
    approval_payload = {
        "record_type": "studio_signing_approval_artifact",
        "schema_version": "studio.signing_approval_review.v1",
        "status": "studio_signing_approval_artifact_written_no_execution",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "approval_scope": "one_signing_proof_only",
        "approved_installer_execution_marker_path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-test.json",
        "approved_installer_execution_marker_sha256": _sha256(installer_marker),
        "approved_unsigned_portable_zip_path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
        "approved_unsigned_portable_zip_sha256": _sha256(unsigned_zip),
        "approved_installer_manifest_path": ".pytest_tmp_env/studio-installer-proof/manifest/installer-manifest.json",
        "approved_installer_manifest_sha256": _sha256(installer_manifest),
        "approved_signing_profile": "operator-provided-code-signing-certificate",
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
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "writes_agent_bus_tasks": False,
        "mutates_gate": False,
        "canonical_mutation_allowed": False,
    }
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(json.dumps(approval_payload, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "status": "studio_signing_approval_consumption_dry_run_ready_no_execution",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "approval_consumed": False,
        },
        "approval_artifact": {
            "path": f"07_LOGS/Agent-Activity/_studio_signing_approvals/{packet_id}.json",
            "exists": True,
        },
        "exact_once_marker_contract": {
            "path": f"07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/{packet_id}.json",
            "exists": marker_path.exists(),
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {"path": ".pytest_tmp_env/studio-signing-proof", "exists": output_root.exists()},
            "signed_portable_zip": {
                "path": f".pytest_tmp_env/studio-signing-proof/dist/{packet_id}/ChaseOS-Studio-portable-signed.zip",
                "exists": False,
                "size_bytes": 0,
            },
            "signing_manifest": {
                "path": f".pytest_tmp_env/studio-signing-proof/manifest/{packet_id}-signing-manifest.json",
                "exists": False,
                "size_bytes": 0,
            },
            "signing_dry_run_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-signing-dry-run.json",
                "exists": False,
                "size_bytes": 0,
            },
            "signing_execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-signing-execution.json",
                "exists": False,
                "size_bytes": 0,
            },
        },
        "checks": {"future_output_paths_clear": True},
        "blockers": [],
    }


def _patch_consumption(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        proof_module,
        "build_studio_signing_approval_consumption_dry_run",
        lambda *args, **kwargs: _fake_consumption_report(tmp_path),
    )


def test_signing_approved_execution_proof_reports_ready_without_writing(tmp_path: Path, monkeypatch) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_signing_approved_execution_proof(tmp_path, execute=False)

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["writes_performed"] is False
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["certificate_reference_resolved"] is True
    assert report["summary"]["signing_certificate_read"] is False
    assert not (tmp_path / ".pytest_tmp_env/studio-signing-proof").exists()


def test_signing_approved_execution_proof_writes_marker_signed_zip_manifest_and_blocks_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_signing_approved_execution_proof(tmp_path, execute=True)

    summary = report["summary"]
    marker_path = tmp_path / "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-testpacket.json"
    signed_zip = tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/studio-signing-appr-testpacket/ChaseOS-Studio-portable-signed.zip"
    manifest_path = tmp_path / ".pytest_tmp_env/studio-signing-proof/manifest/studio-signing-appr-testpacket-signing-manifest.json"
    execution_path = tmp_path / "07_LOGS/Studio-Graph-Views/studio-signing-appr-testpacket-signing-execution.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == COMPLETE_STATUS
    assert report["writes_performed"] is True
    assert summary["approval_consumed"] is True
    assert summary["exact_once_marker_reserved"] is True
    assert summary["duplicate_execution_blocked"] is True
    assert summary["proof_signature_verified"] is True
    assert summary["signing_certificate_read"] is False
    assert summary["production_code_signature_applied"] is False
    assert marker["status"] == COMPLETE_STATUS
    assert signed_zip.is_file()
    assert manifest_path.is_file()
    assert execution_path.is_file()
    assert manifest["signed_portable_zip_sha256"] == _sha256(signed_zip)
    assert report["post_execution_checks"]["manifest_signature_digest_matches"] is True
    assert report["authority"]["writes_idempotency_marker"] is True
    assert report["authority"]["signs_artifacts"] is True
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["next_recommended_pass"] == NEXT_STARTUP_AUTOSTART_APPROVAL_PASS

    with zipfile.ZipFile(signed_zip, "r") as archive:
        assert "unsigned/ChaseOS-Studio-portable.zip" in archive.namelist()
        assert "CHASEOS-SIGNING-PROOF.json" in archive.namelist()

    duplicate = build_studio_signing_approved_execution_proof(tmp_path, execute=True)

    assert duplicate["ok"] is False
    assert duplicate["status"] == DUPLICATE_BLOCKED_STATUS
    assert duplicate["summary"]["duplicate_execution_blocked"] is True
    assert duplicate["writes_performed"] is False


def test_signing_approved_execution_proof_blocks_mismatched_packet(tmp_path: Path, monkeypatch) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_signing_approved_execution_proof(
        tmp_path,
        approval_packet_id="studio-signing-appr-wrong",
        execute=True,
    )

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert report["writes_performed"] is False


def test_signing_approved_execution_proof_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": COMPLETE_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS,
        "summary": {
            "approval_packet_id": "studio-signing-appr-test",
            "approval_consumed": True,
            "execution_performed": True,
            "duplicate_execution_blocked": True,
            "signed_portable_zip_path": "dist/test.zip",
            "signed_portable_zip_sha256": "abc",
            "signing_manifest_path": "manifest.json",
            "certificate_reference_resolved": True,
            "signing_certificate_read": False,
            "raw_certificate_values_visible": False,
            "proof_signature_verified": True,
            "production_code_signature_applied": False,
        },
        "post_execution_checks": {"signed_portable_zip_exists": True},
        "rollback_boundary": {"owned_output_root": ".pytest_tmp_env/studio-signing-proof"},
        "authority": {"signs_artifacts": True, "reads_signing_certificate": False},
        "blockers": [],
        "unverified": ["No production code-signing certificate was read."],
    }

    evidence = write_signing_approved_execution_proof_evidence(
        tmp_path,
        report,
        evidence_slug="signing-approved-execution-proof-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
