"""Tests for the no-execution Studio startup/autostart approval review pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.startup_autostart_approval_review as review_module
from runtime.studio.startup_autostart_approval_review import (
    BLOCKED_STATUS,
    CONSUMED_STATUS,
    EXISTING_STATUS,
    NEXT_STARTUP_CONSUMPTION_DRY_RUN_PASS,
    READY_STATUS,
    WRITTEN_STATUS,
    build_studio_startup_autostart_approval_review,
    write_startup_autostart_approval_review_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_preview_report() -> dict:
    packet_id = "studio-startup-autostart-appr-testpacket"
    digest = "a" * 64
    return {
        "ok": True,
        "status": "ready_for_operator_studio_startup_autostart_approval_review",
        "summary": {
            "signing_approval_packet_id": "studio-signing-appr-testpacket",
            "startup_autostart_approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "startup_autostart_approval_preview_ready": True,
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
            "record_type": "studio_startup_autostart_approval_packet_preview",
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_material": {
                "signing_approval_packet_id": "studio-signing-appr-testpacket",
                "signing_execution_marker_path": "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-testpacket.json",
                "signing_execution_marker_sha256": "b" * 64,
                "signed_portable_zip_path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                "signed_portable_zip_sha256": "c" * 64,
                "signing_manifest_path": ".pytest_tmp_env/studio-signing-proof/manifest/studio-signing-appr-testpacket-signing-manifest.json",
                "signing_manifest_sha256": "d" * 64,
                "startup_mode": "windows-startup-folder-shortcut-preview",
                "target_platform": "windows",
                "candidate_host_targets": ["windows-startup-folder-shortcut"],
            },
        },
        "source_artifacts": {
            "signing_exact_once_marker": {
                "path": "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-testpacket.json",
                "exists": True,
                "sha256": "b" * 64,
            },
            "signed_portable_zip": {
                "path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                "exists": True,
                "sha256": "c" * 64,
            },
            "signing_manifest": {
                "path": ".pytest_tmp_env/studio-signing-proof/manifest/studio-signing-appr-testpacket-signing-manifest.json",
                "exists": True,
                "sha256": "d" * 64,
            },
        },
        "future_approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/studio-startup-autostart-appr-testpacket.json",
            "exists": False,
            "matches_current_packet": False,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/studio-startup-autostart-appr-testpacket.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "startup_dry_run_evidence": {
                "path": "07_LOGS/Studio-Graph-Views/studio-startup-autostart-appr-testpacket-startup-autostart-dry-run.json",
                "exists": False,
            },
        },
        "host_target_previews": [
            {
                "id": "windows-startup-folder-shortcut",
                "kind": "startup_folder_shortcut",
                "status": "approval_required_before_host_mutation",
                "host_path_resolved_now": False,
                "write_allowed_in_this_pass": False,
            }
        ],
        "checks": {
            "signing_execution_proof_complete": True,
            "signed_portable_zip_present": True,
            "signed_portable_zip_hash_present": True,
            "signing_manifest_present": True,
            "signing_manifest_hash_present": True,
            "future_startup_output_paths_clear": True,
            "host_paths_not_resolved": True,
            "host_mutation_blocked_in_this_pass": True,
        },
        "blockers": [],
    }


def _patch_preview(monkeypatch) -> None:
    monkeypatch.setattr(
        review_module,
        "build_studio_startup_autostart_approval_preview",
        lambda *args, **kwargs: _fake_preview_report(),
    )


def test_startup_autostart_approval_review_reports_ready_without_writing() -> None:
    report = build_studio_startup_autostart_approval_review(VAULT_ROOT, write_approval=False)

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["summary"]["host_path_resolution_attempted"] is False
        assert report["summary"]["host_startup_mutation_allowed"] is False
        assert report["writes_performed"] is False
        assert report["authority"]["reserves_idempotency_marker"] is False
        assert report["authority"]["resolves_host_startup_paths"] is False
        assert report["authority"]["writes_host_startup"] is False
        assert report["authority"]["registers_autostart"] is False
        assert report["authority"]["canonical_mutation_allowed"] is False
        assert report["blockers"]
        return

    assert report["ok"] is True
    assert report["status"] in {READY_STATUS, EXISTING_STATUS, CONSUMED_STATUS}
    assert report["summary"]["approval_artifact_ready"] is True
    if report["status"] == CONSUMED_STATUS:
        assert report["summary"]["approval_decision_consumed"] is True
    else:
        assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["host_path_resolution_attempted"] is False
    assert report["summary"]["host_startup_mutation_allowed"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["resolves_host_startup_paths"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["registers_autostart"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False


def test_startup_autostart_approval_review_writes_only_scoped_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_startup_autostart_approval_review(
        tmp_path,
        approval_packet_id="studio-startup-autostart-appr-testpacket",
        write_approval=True,
        generated_at="2026-05-06T00:00:00Z",
    )

    artifact_path = tmp_path / report["approval_artifact"]["path"]
    marker_path = tmp_path / report["exact_once_marker_contract"]["path"]
    proof_root = tmp_path / ".pytest_tmp_env/studio-startup-autostart-proof"
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["approval_artifact_written"] is True
    assert report["summary"]["approval_artifact_write_status"] == "approval_artifact_written"
    assert payload["record_type"] == "studio_startup_autostart_approval_artifact"
    assert payload["approval_packet_id"] == "studio-startup-autostart-appr-testpacket"
    assert payload["operator_decision"] == "approved"
    assert payload["approval_scope"] == "one_startup_autostart_proof_only"
    assert payload["startup_mutation_allowed_in_this_pass"] is False
    assert payload["approval_decision_consumed"] is False
    assert payload["host_path_resolution_attempted"] is False
    assert payload["writes_host_startup"] is False
    assert payload["registers_autostart"] is False
    assert marker_path.exists() is False
    assert proof_root.exists() is False
    assert report["next_recommended_pass"] == NEXT_STARTUP_CONSUMPTION_DRY_RUN_PASS


def test_startup_autostart_approval_review_forwards_signing_packet_id(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_preview(*args, **kwargs):
        captured.update(kwargs)
        return _fake_preview_report()

    monkeypatch.setattr(review_module, "build_studio_startup_autostart_approval_preview", fake_preview)

    report = build_studio_startup_autostart_approval_review(
        tmp_path,
        approval_packet_id="studio-startup-autostart-appr-testpacket",
        signing_approval_packet_id="studio-signing-appr-testpacket",
        write_approval=False,
    )

    assert report["ok"] is True
    assert captured["signing_approval_packet_id"] == "studio-signing-appr-testpacket"


def test_startup_autostart_approval_review_reuses_existing_matching_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    first = build_studio_startup_autostart_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-06T00:00:00Z",
    )
    second = build_studio_startup_autostart_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-06T00:01:00Z",
    )

    assert first["status"] == WRITTEN_STATUS
    assert second["status"] == EXISTING_STATUS
    assert second["summary"]["approval_artifact_written"] is True
    assert second["summary"]["approval_artifact_write_status"] == "existing_matching_approval_present"
    assert second["writes_performed"] is False


def test_startup_autostart_approval_review_blocks_mismatched_packet(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_startup_autostart_approval_review(
        tmp_path,
        approval_packet_id="studio-startup-autostart-appr-wrong",
        write_approval=True,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_studio_startup_autostart_approval_review"
    assert report["writes_performed"] is False
    assert "Requested approval packet id does not match" in " ".join(report["blockers"])


def test_startup_autostart_approval_review_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": "operator-review-studio-startup-autostart-approval-packet",
        "summary": {
            "approval_packet_id": "studio-startup-autostart-appr-test",
            "request_digest_sha256": "abc",
            "operator_decision": "approved",
            "approval_artifact_written": False,
            "approval_artifact_write_status": "not_requested",
            "host_path_resolution_attempted": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
            "writes_performed": False,
        },
        "approval_artifact": {"path": "approval.json"},
        "exact_once_marker_contract": {
            "path": "marker.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "dry_run": {"path": "dry-run.json", "exists": False},
        },
        "authority": {"writes_host_startup": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No host startup mutation was attempted."],
    }

    evidence = write_startup_autostart_approval_review_evidence(
        tmp_path,
        report,
        evidence_slug="startup-autostart-approval-review-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
