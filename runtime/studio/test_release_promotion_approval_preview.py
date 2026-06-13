"""Tests for the no-execution Studio release-promotion approval preview."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import runtime.studio.release_promotion_approval_preview as release_module
from runtime.studio.release_promotion_approval_preview import (
    BLOCKED_STATUS,
    NEXT_OPERATOR_REVIEW_PASS,
    READY_STATUS,
    build_studio_release_promotion_approval_preview,
    write_release_promotion_approval_preview_evidence,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _fake_startup_execution_report(tmp_path: Path, *, complete: bool = True) -> dict:
    packet_id = "studio-startup-autostart-appr-testpacket"
    marker = _write(
        tmp_path / f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{packet_id}.json",
        json.dumps(
            {
                "record_type": "studio_startup_autostart_execution_marker",
                "approval_packet_id": packet_id,
                "status": "studio_startup_autostart_approved_execution_proof_complete",
                "host_path_resolution_attempted": False,
                "host_mutation_performed": False,
                "release_promotion_allowed": False,
            }
        ),
    )
    signed_zip = _write(
        tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
        "fake signed zip bytes",
    )
    manifest = _write(
        tmp_path / f".pytest_tmp_env/studio-signing-proof/manifest/{packet_id}-signing-manifest.json",
        json.dumps({"approval_packet_id": packet_id, "record_type": "studio_signing_manifest"}),
    )
    execution = _write(
        tmp_path / f"07_LOGS/Studio-Graph-Views/{packet_id}-startup-autostart-execution.json",
        json.dumps({"summary": {"approval_packet_id": packet_id}, "record_type": "studio_startup_autostart_execution_evidence"}),
    )
    audit = _write(
        tmp_path / f".pytest_tmp_env/studio-startup-autostart-proof/audit/{packet_id}-startup-autostart-host-mutation-audit.json",
        json.dumps({"approval_packet_id": packet_id, "host_mutation_performed": False, "release_promotion_allowed": False}),
    )
    rollback = _write(
        tmp_path / f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{packet_id}-startup-autostart-rollback-plan.json",
        json.dumps({"approval_packet_id": packet_id, "rollback_scope": "owned_startup_autostart_proof_root_only"}),
    )
    status = "studio_startup_autostart_approved_execution_proof_complete" if complete else "blocked"
    return {
        "ok": complete,
        "status": status,
        "summary": {
            "approval_packet_id": packet_id,
            "approval_consumed": complete,
            "duplicate_execution_blocked": complete,
            "signed_portable_zip_path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
            "signed_portable_zip_sha256": _sha256(signed_zip),
            "signing_manifest_path": f".pytest_tmp_env/studio-signing-proof/manifest/{packet_id}-signing-manifest.json",
            "execution_evidence_path": f"07_LOGS/Studio-Graph-Views/{packet_id}-startup-autostart-execution.json",
            "rollback_plan_path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{packet_id}-startup-autostart-rollback-plan.json",
            "host_mutation_audit_path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{packet_id}-startup-autostart-host-mutation-audit.json",
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "release_promotion_allowed": False,
            "next_recommended_pass": "studio-release-promotion-approval-preview",
        },
        "paths": {
            "exact_once_marker": {
                "path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{packet_id}.json",
                "exists": marker.is_file(),
                "sha256": _sha256(marker),
            },
            "signed_portable_zip": {
                "path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                "exists": signed_zip.is_file(),
                "sha256": _sha256(signed_zip),
            },
            "signing_manifest": {
                "path": f".pytest_tmp_env/studio-signing-proof/manifest/{packet_id}-signing-manifest.json",
                "exists": manifest.is_file(),
                "sha256": _sha256(manifest),
            },
            "execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-startup-autostart-execution.json",
                "exists": execution.is_file(),
                "sha256": _sha256(execution),
            },
            "host_mutation_audit": {
                "path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{packet_id}-startup-autostart-host-mutation-audit.json",
                "exists": audit.is_file(),
                "sha256": _sha256(audit),
            },
            "rollback_plan": {
                "path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{packet_id}-startup-autostart-rollback-plan.json",
                "exists": rollback.is_file(),
                "sha256": _sha256(rollback),
            },
        },
        "next_recommended_pass": "studio-release-promotion-approval-preview",
    }


def test_release_promotion_approval_preview_ready_without_release_write(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        release_module,
        "build_studio_startup_autostart_approved_execution_proof",
        lambda *args, **kwargs: _fake_startup_execution_report(tmp_path),
    )

    report = build_studio_release_promotion_approval_preview(tmp_path, generated_at="2026-05-07T00:00:00Z")

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["release_promotion_approval_packet_id"].startswith("studio-release-promotion-appr-")
    assert report["summary"]["startup_approval_packet_id"].startswith("studio-startup-autostart-appr-")
    assert report["summary"]["release_status_write_allowed"] is False
    assert report["summary"]["release_promotion_allowed"] is False
    assert report["future_approval_artifact"]["exists"] is False
    assert report["exact_once_marker_contract"]["exists"] is False
    assert report["checks"]["startup_autostart_approved_execution_proof_complete"] is True
    assert report["checks"]["future_release_output_paths_clear"] is True
    assert report["checks"]["release_status_write_blocked_in_this_pass"] is True
    assert report["authority"]["writes_release_status"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] == NEXT_OPERATOR_REVIEW_PASS
    assert not (tmp_path / ".pytest_tmp_env/studio-release-promotion-proof").exists()


def test_release_promotion_approval_packet_id_is_stable_for_same_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        release_module,
        "build_studio_startup_autostart_approved_execution_proof",
        lambda *args, **kwargs: _fake_startup_execution_report(tmp_path),
    )

    first = build_studio_release_promotion_approval_preview(tmp_path, generated_at="2026-05-07T00:00:00Z")
    second = build_studio_release_promotion_approval_preview(tmp_path, generated_at="2026-05-07T01:00:00Z")

    assert first["summary"]["release_promotion_approval_packet_id"] == second["summary"]["release_promotion_approval_packet_id"]
    assert first["summary"]["request_digest_sha256"] == second["summary"]["request_digest_sha256"]


def test_release_promotion_approval_preview_blocks_without_completed_startup_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        release_module,
        "build_studio_startup_autostart_approved_execution_proof",
        lambda *args, **kwargs: _fake_startup_execution_report(tmp_path, complete=False),
    )

    report = build_studio_release_promotion_approval_preview(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "Studio startup/autostart approved execution proof is not complete." in report["blockers"]
    assert report["summary"]["release_status_write_allowed"] is False
    assert report["writes_performed"] is False


def test_release_promotion_approval_preview_evidence_writer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        release_module,
        "build_studio_startup_autostart_approved_execution_proof",
        lambda *args, **kwargs: _fake_startup_execution_report(tmp_path),
    )
    report = build_studio_release_promotion_approval_preview(tmp_path, generated_at="2026-05-07T00:00:00Z")

    evidence = write_release_promotion_approval_preview_evidence(
        tmp_path,
        report,
        evidence_slug="release-promotion-approval-preview-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
