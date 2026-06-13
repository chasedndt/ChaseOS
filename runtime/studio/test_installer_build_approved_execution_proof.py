"""Tests for the governed Studio installer-build approved execution proof."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.installer_build_approved_execution_proof as execution_module
from runtime.studio.installer_build_approved_execution_proof import (
    BLOCKED_STATUS,
    COMPLETE_STATUS,
    DUPLICATE_BLOCKED_STATUS,
    NEXT_SIGNING_APPROVAL_PASS,
    READY_STATUS,
    build_studio_installer_build_approved_execution_proof,
    write_installer_build_approved_execution_proof_evidence,
)
from runtime.studio.packaging_proof import _sha256


def _fake_review_report(tmp_path: Path, *, packet_id: str = "studio-installer-build-appr-testpacket") -> dict:
    source_dir = tmp_path / ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio"
    source_dir.mkdir(parents=True, exist_ok=True)
    exe = source_dir / "ChaseOS-Studio.exe"
    exe.write_text("fake executable", encoding="utf-8")
    internal = source_dir / "_internal"
    internal.mkdir(exist_ok=True)
    (internal / "asset.txt").write_text("asset", encoding="utf-8")
    exe_sha = _sha256(exe)
    digest = "a" * 64
    approval_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_installer_build_approvals/{packet_id}.json"
    marker_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/{packet_id}.json"
    output_root = tmp_path / ".pytest_tmp_env/studio-installer-proof"
    approval_payload = {
        "record_type": "studio_installer_build_approval_artifact",
        "schema_version": "studio.installer_build_approval_review.v1",
        "status": "studio_installer_build_approval_artifact_written_no_execution",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "approval_scope": "one_installer_build_only",
        "approved_installer_format": "zip-portable",
        "approved_output_root": ".pytest_tmp_env/studio-installer-proof",
        "approved_packaged_executable_sha256": exe_sha,
        "approved_packaged_executable": {
            "path": ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio/ChaseOS-Studio.exe",
            "exists": True,
            "size_bytes": exe.stat().st_size,
        },
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
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(json.dumps(approval_payload, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "status": "studio_installer_build_approval_artifact_existing_matching_no_execution",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_ready": True,
            "approval_artifact_written": True,
            "approval_decision_consumed": False,
            "approved_execution_proof_complete": False,
            "exact_once_marker_exists": marker_path.exists(),
            "execution_allowed": False,
            "installer_build_allowed": False,
        },
        "approval_artifact": {
            "path": f"07_LOGS/Agent-Activity/_studio_installer_build_approvals/{packet_id}.json",
            "exists_after": True,
            "matches_current_packet": True,
        },
        "exact_once_marker_contract": {
            "path": f"07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/{packet_id}.json",
            "exists": marker_path.exists(),
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {
                "path": ".pytest_tmp_env/studio-installer-proof",
                "exists": output_root.exists(),
            },
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": (output_root / "dist/ChaseOS-Studio-portable.zip").exists(),
                "size_bytes": 0,
            },
            "build_manifest": {
                "path": f".pytest_tmp_env/studio-installer-proof/manifest/{packet_id}-installer-build-manifest.json",
                "exists": (output_root / f"manifest/{packet_id}-installer-build-manifest.json").exists(),
                "size_bytes": 0,
            },
            "dry_run_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-installer-build-dry-run.json",
                "exists": (tmp_path / f"07_LOGS/Studio-Graph-Views/{packet_id}-installer-build-dry-run.json").exists(),
                "size_bytes": 0,
            },
            "execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-installer-build-execution.json",
                "exists": (tmp_path / f"07_LOGS/Studio-Graph-Views/{packet_id}-installer-build-execution.json").exists(),
                "size_bytes": 0,
            },
        },
        "checks": {
            "future_output_paths_clear": not output_root.exists(),
            "approved_execution_proof_complete": False,
        },
        "blockers": [],
    }


def _patch_review(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        execution_module,
        "build_studio_installer_build_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path),
    )


def test_approved_execution_proof_reports_ready_without_writing(tmp_path: Path, monkeypatch) -> None:
    _patch_review(monkeypatch, tmp_path)

    report = build_studio_installer_build_approved_execution_proof(tmp_path, execute=False)

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["writes_performed"] is False
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["future_output_paths_clear"] is True
    assert report["authority"]["writes_installer"] is False
    assert not (tmp_path / ".pytest_tmp_env/studio-installer-proof").exists()


def test_approved_execution_proof_writes_marker_zip_manifest_audit_and_blocks_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_review(monkeypatch, tmp_path)

    report = build_studio_installer_build_approved_execution_proof(tmp_path, execute=True)

    summary = report["summary"]
    marker_path = tmp_path / "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-testpacket.json"
    zip_path = tmp_path / ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip"
    manifest_path = tmp_path / ".pytest_tmp_env/studio-installer-proof/manifest/studio-installer-build-appr-testpacket-installer-build-manifest.json"
    execution_path = tmp_path / "07_LOGS/Studio-Graph-Views/studio-installer-build-appr-testpacket-installer-build-execution.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == COMPLETE_STATUS
    assert report["writes_performed"] is True
    assert summary["approval_consumed"] is True
    assert summary["exact_once_marker_reserved"] is True
    assert summary["duplicate_execution_blocked"] is True
    assert marker["status"] == COMPLETE_STATUS
    assert zip_path.is_file()
    assert manifest_path.is_file()
    assert execution_path.is_file()
    assert manifest["portable_zip_sha256"] == _sha256(zip_path)
    assert report["post_execution_checks"]["manifest_zip_hash_matches"] is True
    assert report["authority"]["writes_idempotency_marker"] is True
    assert report["authority"]["writes_installer"] is True
    assert report["authority"]["signs_artifacts"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["next_recommended_pass"] == NEXT_SIGNING_APPROVAL_PASS

    duplicate = build_studio_installer_build_approved_execution_proof(tmp_path, execute=True)

    assert duplicate["ok"] is False
    assert duplicate["status"] == DUPLICATE_BLOCKED_STATUS
    assert duplicate["summary"]["duplicate_execution_blocked"] is True
    assert duplicate["writes_performed"] is False


def test_approved_execution_proof_blocks_mismatched_packet(tmp_path: Path, monkeypatch) -> None:
    _patch_review(monkeypatch, tmp_path)

    report = build_studio_installer_build_approved_execution_proof(
        tmp_path,
        approval_packet_id="studio-installer-build-appr-wrong",
        execute=True,
    )

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert report["writes_performed"] is False


def test_approved_execution_proof_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": COMPLETE_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS,
        "summary": {
            "approval_packet_id": "studio-installer-build-appr-test",
            "approval_consumed": True,
            "execution_performed": True,
            "duplicate_execution_blocked": True,
            "portable_zip_path": "dist/test.zip",
            "portable_zip_sha256": "abc",
            "manifest_path": "manifest.json",
        },
        "post_execution_checks": {"portable_zip_exists": True},
        "rollback_boundary": {"owned_output_root": ".pytest_tmp_env/studio-installer-proof"},
        "authority": {"writes_installer": True, "signs_artifacts": False},
        "blockers": [],
        "unverified": ["No signing was attempted."],
    }

    evidence = write_installer_build_approved_execution_proof_evidence(
        tmp_path,
        report,
        evidence_slug="installer-build-approved-execution-proof-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
