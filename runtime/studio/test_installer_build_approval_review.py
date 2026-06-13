"""Tests for the no-execution Studio installer-build approval review pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.installer_build_approval_review as review_module
from runtime.studio.installer_build_approval_review import (
    CONSUMED_STATUS,
    EXISTING_STATUS,
    NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS,
    NEXT_SIGNING_APPROVAL_PASS,
    READY_STATUS,
    WRITTEN_STATUS,
    build_studio_installer_build_approval_review,
    write_installer_build_approval_review_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_preview_report() -> dict:
    packet_id = "studio-installer-build-appr-testpacket"
    digest = "a" * 64
    return {
        "ok": True,
        "status": "ready_for_operator_installer_build_approval_review",
        "summary": {
            "release_readiness_governance_ready": True,
            "installer_build_gate_declared": True,
            "approval_packet_id": packet_id,
            "approval_packet_preview_ready": True,
            "approval_artifact_written": False,
            "approval_decision_consumed": False,
            "execution_allowed": False,
            "installer_build_allowed": False,
        },
        "approval_packet_preview": {
            "record_type": "studio_installer_build_approval_packet_preview",
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "installer_format": "zip-portable",
            "source_release_governance_status": "ready_for_operator_release_governance_review",
            "source_release_governance_next": "studio-governed-installer-build-approval",
            "packaged_executable": {
                "path": ".pytest_tmp_env/studio-packaging-proof/dist/ChaseOS-Studio/ChaseOS-Studio.exe",
                "exists": True,
                "size_bytes": 12,
            },
            "packaged_executable_sha256": "b" * 64,
            "approval_material": {
                "output_root": ".pytest_tmp_env/studio-installer-proof",
                "installer_format": "zip-portable",
            },
        },
        "future_approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/studio-installer-build-appr-testpacket.json",
            "exists": False,
            "matches_current_packet": False,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-testpacket.json",
            "exists": False,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "portable_zip": {
                "path": ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip",
                "exists": False,
                "size_bytes": 0,
            }
        },
        "checks": {
            "future_output_paths_clear": True,
        },
        "blockers": [],
    }


def _patch_preview(monkeypatch) -> None:
    monkeypatch.setattr(
        review_module,
        "build_studio_governed_installer_build_approval",
        lambda *args, **kwargs: _fake_preview_report(),
    )


def test_installer_build_approval_review_reports_ready_without_writing() -> None:
    report = build_studio_installer_build_approval_review(VAULT_ROOT, write_approval=False)

    if report["ok"] is False:
        assert report["status"] == "blocked_studio_installer_build_approval_review"
        assert report["blockers"]
        assert report["writes_performed"] is False
        assert report["authority"]["writes_approval_artifact"] is False
        assert report["authority"]["builds_installer"] is False
        assert report["authority"]["writes_installer"] is False
        return

    assert report["ok"] is True
    assert report["status"] in {READY_STATUS, EXISTING_STATUS, CONSUMED_STATUS}
    assert report["summary"]["approval_artifact_ready"] is True
    assert report["summary"]["execution_allowed"] is False
    assert report["summary"]["installer_build_allowed"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["writes_approval_artifact"] is False
    assert report["authority"]["reserves_idempotency_marker"] is False
    assert report["authority"]["builds_installer"] is False
    assert report["authority"]["writes_installer"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    if report["status"] == EXISTING_STATUS:
        assert report["next_recommended_pass"] == NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS
    if report["status"] == CONSUMED_STATUS:
        assert report["summary"]["approval_decision_consumed"] is True
        assert report["next_recommended_pass"] == NEXT_SIGNING_APPROVAL_PASS
    else:
        assert report["summary"]["approval_decision_consumed"] is False


def test_installer_build_approval_review_writes_only_scoped_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_installer_build_approval_review(
        tmp_path,
        approval_packet_id="studio-installer-build-appr-testpacket",
        write_approval=True,
        generated_at="2026-05-06T00:00:00Z",
    )

    artifact_path = tmp_path / report["approval_artifact"]["path"]
    marker_path = tmp_path / report["exact_once_marker_contract"]["path"]
    output_path = tmp_path / ".pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip"
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["approval_artifact_written"] is True
    assert report["summary"]["approval_artifact_write_status"] == "approval_artifact_written"
    assert payload["record_type"] == "studio_installer_build_approval_artifact"
    assert payload["approval_packet_id"] == "studio-installer-build-appr-testpacket"
    assert payload["operator_decision"] == "approved"
    assert payload["approval_scope"] == "one_installer_build_only"
    assert payload["execution_allowed_in_this_pass"] is False
    assert payload["installer_build_allowed_in_this_pass"] is False
    assert marker_path.exists() is False
    assert output_path.exists() is False
    assert report["next_recommended_pass"] == NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS


def test_installer_build_approval_review_reuses_existing_matching_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    first = build_studio_installer_build_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-06T00:00:00Z",
    )
    second = build_studio_installer_build_approval_review(
        tmp_path,
        write_approval=True,
        generated_at="2026-05-06T00:01:00Z",
    )

    assert first["status"] == WRITTEN_STATUS
    assert second["status"] == EXISTING_STATUS
    assert second["summary"]["approval_artifact_written"] is True
    assert second["summary"]["approval_artifact_write_status"] == "existing_matching_approval_present"
    assert second["writes_performed"] is False


def test_installer_build_approval_review_blocks_mismatched_packet(tmp_path: Path, monkeypatch) -> None:
    _patch_preview(monkeypatch)

    report = build_studio_installer_build_approval_review(
        tmp_path,
        approval_packet_id="studio-installer-build-appr-wrong",
        write_approval=True,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_studio_installer_build_approval_review"
    assert report["writes_performed"] is False
    assert "Requested approval packet id does not match" in " ".join(report["blockers"])


def test_installer_build_approval_review_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": "operator-review-studio-installer-build-approval-packet",
        "summary": {
            "approval_packet_id": "studio-installer-build-appr-test",
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
            "portable_zip": {"path": "out.zip", "exists": False},
        },
        "authority": {"writes_installer": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No installer build was attempted."],
    }

    evidence = write_installer_build_approval_review_evidence(
        tmp_path,
        report,
        evidence_slug="installer-build-approval-review-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
