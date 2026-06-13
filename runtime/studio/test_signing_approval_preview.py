"""Tests for the no-execution Studio signing approval preview."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.signing_approval_preview as signing_module
from runtime.studio.packaging_proof import _sha256
from runtime.studio.signing_approval_preview import (
    BLOCKED_STATUS,
    NEXT_OPERATOR_REVIEW_PASS,
    READY_STATUS,
    build_studio_signing_approval_preview,
    write_signing_approval_preview_evidence,
)


def _fake_installer_execution_report(tmp_path: Path, *, complete: bool = True) -> dict:
    packet_id = "studio-installer-build-appr-testpacket"
    marker = tmp_path / f"07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/{packet_id}.json"
    zip_path = tmp_path / ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip"
    manifest = tmp_path / f".pytest_tmp_env/studio-installer-proof/manifest/{packet_id}-installer-build-manifest.json"
    execution = tmp_path / f"07_LOGS/Studio-Graph-Views/{packet_id}-installer-build-execution.json"
    for path, text in [
        (marker, json.dumps({"record_type": "studio_installer_build_execution_marker", "status": "studio_installer_build_approved_execution_proof_complete"})),
        (zip_path, "fake zip bytes"),
        (manifest, json.dumps({"approval_packet_id": packet_id})),
        (execution, json.dumps({"approval_packet_id": packet_id})),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    status = "studio_installer_build_approved_execution_proof_complete" if complete else "blocked"
    return {
        "ok": complete,
        "status": status,
        "summary": {
            "approval_packet_id": packet_id,
            "approval_consumed": complete,
            "duplicate_execution_blocked": complete,
            "portable_zip_path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
            "portable_zip_sha256": _sha256(zip_path),
            "manifest_path": f".pytest_tmp_env/studio-installer-proof/manifest/{packet_id}-installer-build-manifest.json",
            "next_recommended_pass": "studio-signing-approval-preview",
        },
        "paths": {
            "exact_once_marker": {
                "path": f"07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/{packet_id}.json",
                "exists": marker.is_file(),
                "sha256": _sha256(marker),
            },
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": zip_path.is_file(),
                "sha256": _sha256(zip_path),
            },
            "build_manifest": {
                "path": f".pytest_tmp_env/studio-installer-proof/manifest/{packet_id}-installer-build-manifest.json",
                "exists": manifest.is_file(),
                "sha256": _sha256(manifest),
            },
            "execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-installer-build-execution.json",
                "exists": execution.is_file(),
                "sha256": _sha256(execution),
            },
        },
        "next_recommended_pass": "studio-signing-approval-preview",
    }


def test_signing_approval_preview_is_ready_without_reading_certificate_or_writing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        signing_module,
        "build_studio_installer_build_approved_execution_proof",
        lambda *args, **kwargs: _fake_installer_execution_report(tmp_path),
    )

    report = build_studio_signing_approval_preview(tmp_path, generated_at="2026-05-06T00:00:00Z")

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["signing_approval_packet_id"].startswith("studio-signing-appr-")
    assert report["summary"]["signing_allowed"] is False
    assert report["summary"]["signing_certificate_read"] is False
    assert report["summary"]["signed_artifact_written"] is False
    assert report["future_approval_artifact"]["exists"] is False
    assert report["exact_once_marker_contract"]["exists"] is False
    assert report["checks"]["portable_zip_hash_present"] is True
    assert report["checks"]["signing_certificate_not_read"] is True
    assert report["checks"]["future_signing_output_paths_clear"] is True
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["reads_signing_certificate"] is False
    assert report["authority"]["writes_signed_artifact"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["next_recommended_pass"] == NEXT_OPERATOR_REVIEW_PASS
    assert not (tmp_path / ".pytest_tmp_env/studio-signing-proof").exists()


def test_signing_approval_preview_ignores_historical_generic_signed_zip_collision(
    tmp_path: Path, monkeypatch
) -> None:
    historical_signed_zip = tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip"
    historical_signed_zip.parent.mkdir(parents=True, exist_ok=True)
    historical_signed_zip.write_text("older proof-signed output", encoding="utf-8")
    monkeypatch.setattr(
        signing_module,
        "build_studio_installer_build_approved_execution_proof",
        lambda *args, **kwargs: _fake_installer_execution_report(tmp_path),
    )

    report = build_studio_signing_approval_preview(tmp_path, generated_at="2026-05-13T00:00:00Z")
    signed_path = report["future_output_paths"]["signed_portable_zip"]["path"]

    assert report["ok"] is True
    assert report["checks"]["future_signing_output_paths_clear"] is True
    assert "studio-signing-appr-" in signed_path
    assert signed_path.endswith("/ChaseOS-Studio-portable-signed.zip")
    assert historical_signed_zip.is_file()


def test_signing_approval_packet_id_is_stable_for_same_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        signing_module,
        "build_studio_installer_build_approved_execution_proof",
        lambda *args, **kwargs: _fake_installer_execution_report(tmp_path),
    )

    first = build_studio_signing_approval_preview(tmp_path, generated_at="2026-05-06T00:00:00Z")
    second = build_studio_signing_approval_preview(tmp_path, generated_at="2026-05-06T01:00:00Z")

    assert first["summary"]["signing_approval_packet_id"] == second["summary"]["signing_approval_packet_id"]
    assert first["summary"]["request_digest_sha256"] == second["summary"]["request_digest_sha256"]


def test_signing_approval_preview_blocks_without_completed_installer_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        signing_module,
        "build_studio_installer_build_approved_execution_proof",
        lambda *args, **kwargs: _fake_installer_execution_report(tmp_path, complete=False),
    )

    report = build_studio_signing_approval_preview(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "Installer-build approved execution proof is not complete." in report["blockers"]
    assert report["summary"]["signing_allowed"] is False
    assert report["writes_performed"] is False


def test_signing_approval_preview_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_OPERATOR_REVIEW_PASS,
        "summary": {
            "signing_approval_packet_id": "studio-signing-appr-test",
            "request_digest_sha256": "abc",
            "installer_approval_packet_id": "studio-installer-build-appr-test",
            "signing_allowed": False,
            "signing_certificate_read": False,
        },
        "signing_approval_packet_preview": {"approval_packet_id": "studio-signing-appr-test"},
        "future_approval_artifact": {"path": "approval.json", "exists": False},
        "exact_once_marker_contract": {"path": "marker.json", "exists": False},
        "source_artifacts": {"portable_zip": {"path": "out.zip", "exists": True, "sha256": "abc"}},
        "future_output_paths": {"signed_portable_zip": {"path": "signed.zip", "exists": False}},
        "dry_run_plan": [{"step": "verify_portable_zip_hash", "required": True, "effect_now": "read_only_check"}],
        "authority": {"signs_artifacts": False, "reads_signing_certificate": False},
        "blockers": [],
        "unverified": ["No signing was attempted."],
    }

    evidence = write_signing_approval_preview_evidence(
        tmp_path,
        report,
        evidence_slug="signing-approval-preview-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
