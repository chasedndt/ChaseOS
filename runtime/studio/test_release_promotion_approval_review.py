"""Tests for the no-execution Studio release-promotion approval review pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.release_promotion_approval_review as review_module
from runtime.studio.release_promotion_approval_review import (
    BLOCKED_STATUS,
    CONSUMED_STATUS,
    EXISTING_STATUS,
    NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
    NEXT_OPERATOR_REVIEW_PASS,
    NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS,
    READY_STATUS,
    WRITTEN_STATUS,
    build_studio_release_promotion_approval_review,
    write_release_promotion_approval_review_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_preview_report() -> dict:
    packet_id = "studio-release-promotion-appr-testpacket"
    digest = "f" * 64
    startup_packet_id = "studio-startup-autostart-appr-testpacket"
    return {
        "ok": True,
        "status": "ready_for_operator_studio_release_promotion_approval_review",
        "summary": {
            "startup_approval_packet_id": startup_packet_id,
            "release_promotion_approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "release_promotion_approval_preview_ready": True,
            "release_promotion_execution_proof_complete": False,
            "approval_artifact_written": False,
            "approval_decision_consumed": False,
            "release_status_write_allowed": False,
            "release_promotion_allowed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
        },
        "release_promotion_approval_packet_preview": {
            "record_type": "studio_release_promotion_approval_packet_preview",
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_material": {
                "startup_approval_packet_id": startup_packet_id,
                "startup_execution_marker_path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{startup_packet_id}.json",
                "startup_execution_marker_sha256": "a" * 64,
                "signed_portable_zip_path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                "signed_portable_zip_sha256": "b" * 64,
                "signing_manifest_path": f".pytest_tmp_env/studio-signing-proof/manifest/{startup_packet_id}-signing-manifest.json",
                "signing_manifest_sha256": "c" * 64,
                "startup_execution_evidence_path": f"07_LOGS/Studio-Graph-Views/{startup_packet_id}-startup-autostart-execution.json",
                "startup_execution_evidence_sha256": "d" * 64,
                "startup_host_mutation_audit_path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{startup_packet_id}-startup-autostart-host-mutation-audit.json",
                "startup_host_mutation_audit_sha256": "e" * 64,
                "startup_rollback_plan_path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{startup_packet_id}-startup-autostart-rollback-plan.json",
                "startup_rollback_plan_sha256": "1" * 64,
                "release_channel": "local-proof",
                "release_mode": "workspace-release-status-preview",
                "output_root": ".pytest_tmp_env/studio-release-promotion-proof",
            },
        },
        "source_artifacts": {
            "startup_exact_once_marker": {
                "path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{startup_packet_id}.json",
                "exists": True,
                "sha256": "a" * 64,
            },
            "signed_portable_zip": {
                "path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                "exists": True,
                "sha256": "b" * 64,
            },
            "signing_manifest": {
                "path": f".pytest_tmp_env/studio-signing-proof/manifest/{startup_packet_id}-signing-manifest.json",
                "exists": True,
                "sha256": "c" * 64,
            },
            "startup_execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{startup_packet_id}-startup-autostart-execution.json",
                "exists": True,
                "sha256": "d" * 64,
            },
            "startup_host_mutation_audit": {
                "path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{startup_packet_id}-startup-autostart-host-mutation-audit.json",
                "exists": True,
                "sha256": "e" * 64,
            },
            "startup_rollback_plan": {
                "path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{startup_packet_id}-startup-autostart-rollback-plan.json",
                "exists": True,
                "sha256": "1" * 64,
            },
        },
        "future_approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_release_promotion_approvals/studio-release-promotion-appr-testpacket.json",
            "exists": False,
            "matches_current_packet": False,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers/studio-release-promotion-appr-testpacket.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "release_status_preview": {
                "path": ".pytest_tmp_env/studio-release-promotion-proof/release-status/ChaseOS-Studio-release-status-preview.json",
                "exists": False,
            },
        },
        "checks": {
            "startup_autostart_approved_execution_proof_complete": True,
            "startup_approval_consumed": True,
            "startup_exact_once_marker_complete": True,
            "signed_portable_zip_present": True,
            "signed_portable_zip_hash_present": True,
            "signing_manifest_present": True,
            "signing_manifest_hash_present": True,
            "startup_execution_evidence_present": True,
            "startup_execution_evidence_hash_present": True,
            "startup_host_mutation_audit_present": True,
            "startup_host_mutation_audit_hash_present": True,
            "startup_rollback_plan_present": True,
            "startup_rollback_plan_hash_present": True,
            "host_path_resolution_not_attempted": True,
            "host_mutation_not_performed": True,
            "startup_release_promotion_blocked": True,
            "future_release_output_paths_clear": True,
        },
        "blockers": [],
    }


def _patch_preview(monkeypatch) -> None:
    monkeypatch.setattr(
        review_module,
        "build_studio_release_promotion_approval_preview",
        lambda *args, **kwargs: _fake_preview_report(),
    )


def test_release_promotion_approval_review_reports_ready_without_writing() -> None:
    report = build_studio_release_promotion_approval_review(VAULT_ROOT, write_approval=False)
    release_complete = report["status"] == CONSUMED_STATUS

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["summary"]["release_status_write_allowed"] is False
        assert report["summary"]["release_promotion_allowed"] is False
        assert report["summary"]["host_path_resolution_attempted"] is False
        assert report["summary"]["host_mutation_performed"] is False
        assert report["writes_performed"] is False
        assert report["authority"]["reserves_idempotency_marker"] is False
        assert report["authority"]["writes_release_status"] is False
        assert report["authority"]["promotes_release"] is False
        assert report["authority"]["canonical_mutation_allowed"] is False
        assert report["blockers"]
        return

    assert report["ok"] is True
    assert report["status"] in {READY_STATUS, EXISTING_STATUS, CONSUMED_STATUS}
    assert report["summary"]["approval_artifact_ready"] is True
    assert report["summary"]["release_status_write_allowed"] is False
    assert report["summary"]["release_promotion_allowed"] is False
    assert report["summary"]["host_path_resolution_attempted"] is False
    assert report["summary"]["host_mutation_performed"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["writes_release_status"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    if release_complete:
        assert report["next_recommended_pass"] == NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS
    elif report["status"] == EXISTING_STATUS:
        assert report["next_recommended_pass"] == NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS
    else:
        assert report["next_recommended_pass"] == NEXT_OPERATOR_REVIEW_PASS


def test_release_promotion_approval_review_writes_only_scoped_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_release_promotion_approval_review(
        tmp_path,
        approval_packet_id="studio-release-promotion-appr-testpacket",
        write_approval=True,
        generated_at="2026-05-07T00:00:00Z",
    )

    artifact_path = tmp_path / report["approval_artifact"]["path"]
    marker_path = tmp_path / report["exact_once_marker_contract"]["path"]
    proof_root = tmp_path / ".pytest_tmp_env/studio-release-promotion-proof"
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["approval_artifact_written"] is True
    assert report["summary"]["approval_artifact_write_status"] == "approval_artifact_written"
    assert payload["record_type"] == "studio_release_promotion_approval_artifact"
    assert payload["approval_packet_id"] == "studio-release-promotion-appr-testpacket"
    assert payload["operator_decision"] == "approved"
    assert payload["approval_scope"] == "one_release_promotion_proof_only"
    assert payload["release_status_write_allowed_in_this_pass"] is False
    assert payload["release_promotion_allowed_in_this_pass"] is False
    assert payload["approval_decision_consumed"] is False
    assert payload["idempotency_marker_reserved"] is False
    assert payload["writes_release_status"] is False
    assert payload["promotes_release"] is False
    assert marker_path.exists() is False
    assert proof_root.exists() is False
    assert report["next_recommended_pass"] == NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS


def test_release_promotion_approval_review_reuses_existing_matching_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    first = build_studio_release_promotion_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-07T00:00:00Z",
    )
    second = build_studio_release_promotion_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-07T00:01:00Z",
    )

    assert first["status"] == WRITTEN_STATUS
    assert second["status"] == EXISTING_STATUS
    assert second["summary"]["approval_artifact_written"] is True
    assert second["summary"]["approval_artifact_write_status"] == "existing_matching_approval_present"
    assert second["writes_performed"] is False


def test_release_promotion_approval_review_blocks_mismatched_packet(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_release_promotion_approval_review(
        tmp_path,
        approval_packet_id="studio-release-promotion-appr-wrong",
        write_approval=True,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_studio_release_promotion_approval_review"
    assert report["writes_performed"] is False
    assert "Requested approval packet id does not match" in " ".join(report["blockers"])


def test_release_promotion_approval_review_passes_startup_packet_selector(tmp_path: Path, monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_preview(*args, **kwargs):
        calls.update(kwargs)
        return _fake_preview_report()

    monkeypatch.setattr(review_module, "build_studio_release_promotion_approval_preview", fake_preview)

    report = build_studio_release_promotion_approval_review(
        tmp_path,
        startup_approval_packet_id="studio-startup-autostart-appr-selected",
        write_approval=False,
    )

    assert report["ok"] is True
    assert calls["startup_approval_packet_id"] == "studio-startup-autostart-appr-selected"


def test_release_promotion_approval_review_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-07T00:00:00Z",
        "next_recommended_pass": "operator-review-studio-release-promotion-approval-packet",
        "summary": {
            "approval_packet_id": "studio-release-promotion-appr-test",
            "request_digest_sha256": "abc",
            "operator_decision": "approved",
            "approval_artifact_written": False,
            "approval_artifact_write_status": "not_requested",
            "release_status_write_allowed": False,
            "release_promotion_allowed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "writes_performed": False,
        },
        "approval_artifact": {"path": "approval.json"},
        "exact_once_marker_contract": {
            "path": "marker.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "release_status": {"path": "release-status.json", "exists": False},
        },
        "authority": {"writes_release_status": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No release-status write was attempted."],
    }

    evidence = write_release_promotion_approval_review_evidence(
        tmp_path,
        report,
        evidence_slug="release-promotion-approval-review-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
