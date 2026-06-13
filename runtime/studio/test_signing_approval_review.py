"""Tests for the no-execution Studio signing approval review pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.signing_approval_review as review_module
from runtime.studio.signing_approval_review import (
    BLOCKED_STATUS,
    CONSUMED_STATUS,
    EXISTING_STATUS,
    NEXT_OPERATOR_REVIEW_PASS,
    NEXT_SIGNING_CONSUMPTION_DRY_RUN_PASS,
    NEXT_STARTUP_AUTOSTART_APPROVAL_PASS,
    READY_STATUS,
    WRITTEN_STATUS,
    build_studio_signing_approval_review,
    write_signing_approval_review_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_preview_report() -> dict:
    packet_id = "studio-signing-appr-testpacket"
    digest = "c" * 64
    return {
        "ok": True,
        "status": "ready_for_operator_studio_signing_approval_review",
        "summary": {
            "installer_approval_packet_id": "studio-installer-build-appr-testpacket",
            "signing_approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "signing_approval_preview_ready": True,
            "approval_artifact_written": False,
            "approval_decision_consumed": False,
            "signing_allowed": False,
            "signing_certificate_read": False,
            "signed_artifact_written": False,
        },
        "signing_approval_packet_preview": {
            "record_type": "studio_signing_approval_packet_preview",
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_material": {
                "installer_approval_packet_id": "studio-installer-build-appr-testpacket",
                "installer_execution_marker_path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-testpacket.json",
                "installer_execution_marker_sha256": "d" * 64,
                "portable_zip_path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "portable_zip_sha256": "e" * 64,
                "installer_manifest_path": ".pytest_tmp_env/studio-installer-proof/manifest/studio-installer-build-appr-testpacket-installer-build-manifest.json",
                "installer_manifest_sha256": "f" * 64,
                "signing_profile": "operator-provided-code-signing-certificate",
                "output_root": ".pytest_tmp_env/studio-signing-proof",
            },
        },
        "source_artifacts": {
            "exact_once_marker": {
                "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-testpacket.json",
                "exists": True,
                "sha256": "d" * 64,
            },
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": True,
                "sha256": "e" * 64,
            },
            "installer_manifest": {
                "path": ".pytest_tmp_env/studio-installer-proof/manifest/studio-installer-build-appr-testpacket-installer-build-manifest.json",
                "exists": True,
                "sha256": "f" * 64,
            },
        },
        "future_approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_signing_approvals/studio-signing-appr-testpacket.json",
            "exists": False,
            "matches_current_packet": False,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-testpacket.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "signed_portable_zip": {
                "path": ".pytest_tmp_env/studio-signing-proof/dist/studio-signing-appr-testpacket/ChaseOS-Studio-portable-signed.zip",
                "exists": False,
                "size_bytes": 0,
            },
        },
        "checks": {
            "installer_execution_proof_complete": True,
            "portable_zip_present": True,
            "portable_zip_hash_present": True,
            "installer_manifest_present": True,
            "installer_manifest_hash_present": True,
            "future_signing_output_paths_clear": True,
        },
        "blockers": [],
    }


def _patch_preview(monkeypatch) -> None:
    monkeypatch.setattr(
        review_module,
        "build_studio_signing_approval_preview",
        lambda *args, **kwargs: _fake_preview_report(),
    )


def test_signing_approval_review_reports_ready_without_writing() -> None:
    report = build_studio_signing_approval_review(VAULT_ROOT, write_approval=False)
    signing_complete = report["status"] == CONSUMED_STATUS

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["summary"]["signing_allowed"] is False
        assert report["summary"]["signing_certificate_read"] is False
        assert report["writes_performed"] is False
        assert report["authority"]["reserves_idempotency_marker"] is False
        assert report["authority"]["signs_artifacts"] is False
        assert report["authority"]["reads_signing_certificate"] is False
        assert report["authority"]["writes_signed_artifact"] is False
        assert report["authority"]["canonical_mutation_allowed"] is False
        assert report["blockers"]
        return

    assert report["ok"] is True
    assert report["status"] in {READY_STATUS, EXISTING_STATUS, CONSUMED_STATUS}
    assert report["summary"]["approval_artifact_ready"] is True
    assert report["summary"]["signing_allowed"] is False
    assert report["summary"]["signing_certificate_read"] is False
    assert report["summary"]["signed_artifact_written"] is signing_complete
    expected_next = NEXT_OPERATOR_REVIEW_PASS
    if report["status"] == EXISTING_STATUS:
        expected_next = NEXT_SIGNING_CONSUMPTION_DRY_RUN_PASS
    if signing_complete:
        expected_next = NEXT_STARTUP_AUTOSTART_APPROVAL_PASS
    assert report["next_recommended_pass"] == expected_next
    assert report["writes_performed"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False


def test_signing_approval_review_writes_only_scoped_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_signing_approval_review(
        tmp_path,
        approval_packet_id="studio-signing-appr-testpacket",
        write_approval=True,
        generated_at="2026-05-06T00:00:00Z",
    )

    artifact_path = tmp_path / report["approval_artifact"]["path"]
    marker_path = tmp_path / report["exact_once_marker_contract"]["path"]
    signed_zip = tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/studio-signing-appr-testpacket/ChaseOS-Studio-portable-signed.zip"
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["approval_artifact_written"] is True
    assert report["summary"]["approval_artifact_write_status"] == "approval_artifact_written"
    assert payload["record_type"] == "studio_signing_approval_artifact"
    assert payload["approval_packet_id"] == "studio-signing-appr-testpacket"
    assert payload["operator_decision"] == "approved"
    assert payload["approval_scope"] == "one_signing_proof_only"
    assert payload["signing_allowed_in_this_pass"] is False
    assert payload["approval_decision_consumed"] is False
    assert payload["signing_certificate_read"] is False
    assert payload["writes_signed_artifact"] is False
    assert marker_path.exists() is False
    assert signed_zip.exists() is False
    assert report["next_recommended_pass"] == NEXT_SIGNING_CONSUMPTION_DRY_RUN_PASS


def test_signing_approval_review_forwards_installer_packet_id(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_preview(*args, **kwargs):
        captured.update(kwargs)
        return _fake_preview_report()

    monkeypatch.setattr(review_module, "build_studio_signing_approval_preview", fake_preview)

    report = build_studio_signing_approval_review(
        tmp_path,
        approval_packet_id="studio-signing-appr-testpacket",
        installer_approval_packet_id="studio-installer-build-appr-testpacket",
        write_approval=False,
    )

    assert report["ok"] is True
    assert captured["installer_approval_packet_id"] == "studio-installer-build-appr-testpacket"


def test_signing_approval_review_reuses_existing_matching_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    first = build_studio_signing_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-06T00:00:00Z",
    )
    second = build_studio_signing_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-06T00:01:00Z",
    )

    assert first["status"] == WRITTEN_STATUS
    assert second["status"] == EXISTING_STATUS
    assert second["summary"]["approval_artifact_written"] is True
    assert second["summary"]["approval_artifact_write_status"] == "existing_matching_approval_present"
    assert second["writes_performed"] is False


def test_signing_approval_review_blocks_mismatched_packet(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_signing_approval_review(
        tmp_path,
        approval_packet_id="studio-signing-appr-wrong",
        write_approval=True,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_studio_signing_approval_review"
    assert report["writes_performed"] is False
    assert "Requested approval packet id does not match" in " ".join(report["blockers"])


def test_signing_approval_review_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": "operator-review-studio-signing-approval-packet",
        "summary": {
            "approval_packet_id": "studio-signing-appr-test",
            "request_digest_sha256": "abc",
            "operator_decision": "approved",
            "approval_artifact_written": False,
            "approval_artifact_write_status": "not_requested",
            "writes_performed": False,
        },
        "approval_artifact": {"path": "approval.json"},
        "exact_once_marker_contract": {
            "path": "marker.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "signed_zip": {"path": "signed.zip", "exists": False},
        },
        "authority": {"signs_artifacts": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No signing was attempted."],
    }

    evidence = write_signing_approval_review_evidence(
        tmp_path,
        report,
        evidence_slug="signing-approval-review-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
