"""Tests for the no-execution Studio startup/autostart approval preview."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import runtime.studio.startup_autostart_approval_preview as startup_module
from runtime.studio.startup_autostart_approval_preview import (
    BLOCKED_STATUS,
    NEXT_OPERATOR_REVIEW_PASS,
    READY_STATUS,
    build_studio_startup_autostart_approval_preview,
    write_startup_autostart_approval_preview_evidence,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fake_signing_execution_report(tmp_path: Path, *, complete: bool = True) -> dict:
    packet_id = "studio-signing-appr-testpacket"
    marker = tmp_path / f"07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/{packet_id}.json"
    signed_zip = tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip"
    manifest = tmp_path / f".pytest_tmp_env/studio-signing-proof/manifest/{packet_id}-signing-manifest.json"
    execution = tmp_path / f"07_LOGS/Studio-Graph-Views/{packet_id}-signing-execution.json"
    for path, text in [
        (marker, json.dumps({"record_type": "studio_signing_execution_marker", "status": "studio_signing_approved_execution_proof_complete"})),
        (signed_zip, "fake signed zip bytes"),
        (manifest, json.dumps({"approval_packet_id": packet_id, "record_type": "studio_signing_manifest"})),
        (execution, json.dumps({"approval_packet_id": packet_id, "record_type": "studio_signing_execution_evidence"})),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    status = "studio_signing_approved_execution_proof_complete" if complete else "blocked"
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
            "next_recommended_pass": "studio-startup-autostart-approval-preview",
        },
        "paths": {
            "exact_once_marker": {
                "path": f"07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/{packet_id}.json",
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
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-signing-execution.json",
                "exists": execution.is_file(),
                "sha256": _sha256(execution),
            },
        },
        "next_recommended_pass": "studio-startup-autostart-approval-preview",
    }


def test_startup_autostart_approval_preview_is_ready_without_host_mutation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        startup_module,
        "build_studio_signing_approved_execution_proof",
        lambda *args, **kwargs: _fake_signing_execution_report(tmp_path),
    )

    report = build_studio_startup_autostart_approval_preview(tmp_path, generated_at="2026-05-06T00:00:00Z")

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["startup_autostart_approval_packet_id"].startswith("studio-startup-autostart-appr-")
    assert report["summary"]["host_path_resolution_attempted"] is False
    assert report["summary"]["host_startup_mutation_allowed"] is False
    assert report["summary"]["autostart_registration_allowed"] is False
    assert report["future_approval_artifact"]["exists"] is False
    assert report["exact_once_marker_contract"]["exists"] is False
    assert report["checks"]["signing_execution_proof_complete"] is True
    assert report["checks"]["future_startup_output_paths_clear"] is True
    assert report["checks"]["host_paths_not_resolved"] is True
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["registers_autostart"] is False
    assert report["authority"]["writes_registry"] is False
    assert report["authority"]["writes_start_menu"] is False
    assert report["authority"]["writes_desktop_shortcut"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["next_recommended_pass"] == NEXT_OPERATOR_REVIEW_PASS
    assert all(item["write_allowed_in_this_pass"] is False for item in report["host_target_previews"])
    assert not (tmp_path / ".pytest_tmp_env/studio-startup-autostart-proof").exists()


def test_startup_autostart_approval_packet_id_is_stable_for_same_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        startup_module,
        "build_studio_signing_approved_execution_proof",
        lambda *args, **kwargs: _fake_signing_execution_report(tmp_path),
    )

    first = build_studio_startup_autostart_approval_preview(tmp_path, generated_at="2026-05-06T00:00:00Z")
    second = build_studio_startup_autostart_approval_preview(tmp_path, generated_at="2026-05-06T01:00:00Z")

    assert first["summary"]["startup_autostart_approval_packet_id"] == second["summary"]["startup_autostart_approval_packet_id"]
    assert first["summary"]["request_digest_sha256"] == second["summary"]["request_digest_sha256"]


def test_startup_autostart_approval_preview_blocks_without_completed_signing_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        startup_module,
        "build_studio_signing_approved_execution_proof",
        lambda *args, **kwargs: _fake_signing_execution_report(tmp_path, complete=False),
    )

    report = build_studio_startup_autostart_approval_preview(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "Studio signing approved execution proof is not complete." in report["blockers"]
    assert report["summary"]["host_startup_mutation_allowed"] is False
    assert report["writes_performed"] is False


def test_startup_autostart_approval_preview_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_OPERATOR_REVIEW_PASS,
        "summary": {
            "signing_approval_packet_id": "studio-signing-appr-test",
            "startup_autostart_approval_packet_id": "studio-startup-autostart-appr-test",
            "request_digest_sha256": "abc",
            "approval_artifact_written": False,
            "approval_decision_consumed": False,
            "host_path_resolution_attempted": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
            "release_promotion_allowed": False,
        },
        "startup_autostart_approval_packet_preview": {
            "approval_packet_id": "studio-startup-autostart-appr-test"
        },
        "future_approval_artifact": {"path": "approval.json", "exists": False},
        "exact_once_marker_contract": {"path": "marker.json", "exists": False, "future_write_mode": "exclusive"},
        "source_artifacts": {
            "signed_portable_zip": {"path": "signed.zip", "exists": True, "sha256": "abc"},
            "signing_manifest": {"path": "manifest.json", "exists": True, "sha256": "def"},
            "signing_exact_once_marker": {"path": "marker.json", "exists": True, "sha256": "ghi"},
        },
        "host_target_previews": [{"id": "windows-startup-folder-shortcut", "status": "blocked", "write_allowed_in_this_pass": False, "host_path_resolved_now": False}],
        "dry_run_plan": [{"step": "verify_signed_portable_zip_hash", "required": True, "effect_now": "read_only_check"}],
        "authority": {"writes_host_startup": False, "registers_autostart": False},
        "blockers": [],
        "unverified": ["No host startup mutation was attempted."],
    }

    evidence = write_startup_autostart_approval_preview_evidence(
        tmp_path,
        report,
        evidence_slug="startup-autostart-approval-preview-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
