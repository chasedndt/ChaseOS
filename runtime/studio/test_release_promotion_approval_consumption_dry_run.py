"""Tests for the Studio release-promotion approval consumption dry-run pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.release_promotion_approval_consumption_dry_run as consumption_module
from runtime.studio.release_promotion_approval_consumption_dry_run import (
    BLOCKED_STATUS,
    NEXT_RELEASE_APPROVED_EXECUTION_PROOF_PASS,
    READY_STATUS,
    _marker_reservation_dry_run,
    build_studio_release_promotion_approval_consumption_dry_run,
    write_release_promotion_approval_consumption_dry_run_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_review_report(
    tmp_path: Path,
    *,
    artifact_present: bool = True,
    marker_present: bool = False,
    mismatched_digest: bool = False,
    output_collision: bool = False,
) -> dict:
    packet_id = "studio-release-promotion-appr-testpacket"
    digest = "a" * 64
    startup_packet_id = "studio-startup-autostart-appr-testpacket"
    hashes = {
        "startup_marker": "b" * 64,
        "signed_zip": "c" * 64,
        "signing_manifest": "d" * 64,
        "startup_evidence": "e" * 64,
        "startup_audit": "f" * 64,
        "startup_rollback": "1" * 64,
    }
    approval_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/{packet_id}.json"
    marker_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers/{packet_id}.json"
    status_preview = (
        tmp_path
        / f".pytest_tmp_env/studio-release-promotion-proof/release-status/{packet_id}-release-status-preview.json"
    )
    payload = {
        "record_type": "studio_release_promotion_approval_artifact",
        "schema_version": "studio.release_promotion_approval_review.v1",
        "status": "studio_release_promotion_approval_artifact_written_no_release_mutation",
        "approval_packet_id": packet_id,
        "request_digest_sha256": ("9" * 64 if mismatched_digest else digest),
        "operator_decision": "approved",
        "approval_scope": "one_release_promotion_proof_only",
        "approved_startup_approval_packet_id": startup_packet_id,
        "approved_startup_execution_marker_path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{startup_packet_id}.json",
        "approved_startup_execution_marker_sha256": hashes["startup_marker"],
        "approved_signed_portable_zip_path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
        "approved_signed_portable_zip_sha256": hashes["signed_zip"],
        "approved_signing_manifest_path": ".pytest_tmp_env/studio-signing-proof/manifest/test-signing-manifest.json",
        "approved_signing_manifest_sha256": hashes["signing_manifest"],
        "approved_startup_execution_evidence_path": f"07_LOGS/Studio-Graph-Views/{startup_packet_id}-startup-autostart-execution.json",
        "approved_startup_execution_evidence_sha256": hashes["startup_evidence"],
        "approved_startup_host_mutation_audit_path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{startup_packet_id}-startup-autostart-host-mutation-audit.json",
        "approved_startup_host_mutation_audit_sha256": hashes["startup_audit"],
        "approved_startup_rollback_plan_path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{startup_packet_id}-startup-autostart-rollback-plan.json",
        "approved_startup_rollback_plan_sha256": hashes["startup_rollback"],
        "approved_release_channel": "local-proof",
        "approved_release_mode": "workspace-release-status-preview",
        "approved_output_root": ".pytest_tmp_env/studio-release-promotion-proof",
        "approval_consumption_required": True,
        "future_single_release_promotion_proof_approved": True,
        "release_status_write_allowed_in_this_pass": False,
        "release_promotion_allowed_in_this_pass": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "writes_release_status": False,
        "promotes_release": False,
        "host_path_resolution_attempted": False,
        "resolves_host_startup_paths": False,
        "writes_host_startup": False,
        "registers_autostart": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
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
    if output_collision:
        status_preview.parent.mkdir(parents=True, exist_ok=True)
        status_preview.write_text(json.dumps({"record_type": "collision"}), encoding="utf-8")

    return {
        "ok": True,
        "status": "studio_release_promotion_approval_artifact_existing_matching_no_release_mutation",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
        },
        "source_preview": {
            "release_promotion_approval_packet_preview": {
                "approval_packet_id": packet_id,
                "request_digest_sha256": digest,
                "approval_material": {
                    "startup_approval_packet_id": startup_packet_id,
                    "startup_execution_marker_sha256": hashes["startup_marker"],
                    "signed_portable_zip_sha256": hashes["signed_zip"],
                    "signing_manifest_sha256": hashes["signing_manifest"],
                    "startup_execution_evidence_sha256": hashes["startup_evidence"],
                    "startup_host_mutation_audit_sha256": hashes["startup_audit"],
                    "startup_rollback_plan_sha256": hashes["startup_rollback"],
                    "release_channel": "local-proof",
                    "release_mode": "workspace-release-status-preview",
                },
            },
            "source_artifacts": {
                "startup_exact_once_marker": {"exists": True, "sha256": hashes["startup_marker"]},
                "signed_portable_zip": {"exists": True, "sha256": hashes["signed_zip"]},
                "signing_manifest": {"exists": True, "sha256": hashes["signing_manifest"]},
                "startup_execution_evidence": {"exists": True, "sha256": hashes["startup_evidence"]},
                "startup_host_mutation_audit": {"exists": True, "sha256": hashes["startup_audit"]},
                "startup_rollback_plan": {"exists": True, "sha256": hashes["startup_rollback"]},
            },
            "checks": {
                "startup_autostart_approved_execution_proof_complete": True,
                "startup_approval_consumed": True,
                "startup_exact_once_marker_complete": True,
                "release_status_write_blocked_in_this_pass": True,
                "release_promotion_blocked_in_this_pass": True,
            },
        },
        "approval_artifact": {
            "path": f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/{packet_id}.json",
            "exists_after": artifact_present,
        },
        "exact_once_marker_contract": {
            "path": f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers/{packet_id}.json",
            "exists": marker_present,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {
                "path": ".pytest_tmp_env/studio-release-promotion-proof",
                "exists": output_collision,
            },
            "release_dry_run_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-release-promotion-dry-run.json",
                "exists": False,
            },
            "release_execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-release-promotion-execution.json",
                "exists": False,
            },
            "release_manifest": {
                "path": f".pytest_tmp_env/studio-release-promotion-proof/manifest/{packet_id}-release-manifest.json",
                "exists": False,
            },
            "release_status_preview": {
                "path": f".pytest_tmp_env/studio-release-promotion-proof/release-status/{packet_id}-release-status-preview.json",
                "exists": output_collision,
            },
            "release_promotion_audit": {
                "path": f".pytest_tmp_env/studio-release-promotion-proof/audit/{packet_id}-release-promotion-audit.json",
                "exists": False,
            },
            "rollback_plan": {
                "path": f".pytest_tmp_env/studio-release-promotion-proof/rollback/{packet_id}-release-promotion-rollback-plan.json",
                "exists": False,
            },
        },
        "checks": {"future_output_paths_clear": not output_collision},
        "blockers": [],
    }


def _patch_review(monkeypatch, tmp_path: Path, **kwargs) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_release_promotion_approval_review",
        lambda *args, **_call_kwargs: _fake_review_report(tmp_path, **kwargs),
    )


def test_release_promotion_consumption_dry_run_validates_current_repo_approval_without_mutation() -> None:
    report = build_studio_release_promotion_approval_consumption_dry_run(
        VAULT_ROOT,
        approval_packet_id="studio-release-promotion-appr-d698d13b011ccf06",
    )

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["writes_performed"] is False
        assert report["summary"]["release_status_write_allowed"] is False
        assert report["summary"]["release_promotion_allowed"] is False
        assert report["authority"]["consumes_approval_decision"] is False
        assert report["authority"]["writes_idempotency_marker"] is False
        assert report["authority"]["promotes_release"] is False
        assert report["authority"]["canonical_mutation_allowed"] is False
        assert report["blockers"]
        return

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["approval_artifact_present"] is True
    assert report["summary"]["approval_digest_matches"] is True
    assert report["summary"]["approval_scope_valid"] is True
    assert report["summary"]["startup_marker_hash_matches"] is True
    assert report["summary"]["signed_portable_zip_hash_matches"] is True
    assert report["summary"]["signing_manifest_hash_matches"] is True
    assert report["summary"]["startup_execution_evidence_hash_matches"] is True
    assert report["summary"]["startup_audit_hash_matches"] is True
    assert report["summary"]["startup_rollback_hash_matches"] is True
    assert report["summary"]["duplicate_consumption_blocked"] is True
    assert report["summary"]["release_status_write_allowed"] is False
    assert report["summary"]["release_promotion_allowed"] is False
    assert report["summary"]["host_mutation_performed"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["consumes_approval_decision"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["writes_release_status"] is False
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["next_recommended_pass"] in {
        NEXT_RELEASE_APPROVED_EXECUTION_PROOF_PASS,
        "browser-runtime-production-closeout",
    }


def test_release_promotion_consumption_dry_run_blocks_missing_artifact(tmp_path: Path, monkeypatch) -> None:
    _patch_review(monkeypatch, tmp_path, artifact_present=False)

    report = build_studio_release_promotion_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "approval_artifact_present" in report["blockers"]
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False


def test_release_promotion_consumption_dry_run_blocks_mismatched_digest(tmp_path: Path, monkeypatch) -> None:
    _patch_review(monkeypatch, tmp_path, mismatched_digest=True)

    report = build_studio_release_promotion_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "request_digest_matches" in report["blockers"]
    assert report["writes_performed"] is False


def test_release_promotion_consumption_dry_run_blocks_existing_marker(tmp_path: Path, monkeypatch) -> None:
    _patch_review(monkeypatch, tmp_path, marker_present=True)

    report = build_studio_release_promotion_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "real_marker_absent" in report["blockers"]
    assert "marker_reservation_proof_passed" in report["blockers"]
    assert report["marker_reservation_dry_run"]["first_reservation_allowed"] is False
    assert report["marker_reservation_dry_run"]["duplicate_reservation_blocked"] is True


def test_release_promotion_consumption_dry_run_blocks_future_output_collision(tmp_path: Path, monkeypatch) -> None:
    _patch_review(monkeypatch, tmp_path, output_collision=True)

    report = build_studio_release_promotion_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "future_output_paths_clear" in report["blockers"]
    assert report["writes_performed"] is False


def test_release_promotion_consumption_dry_run_infers_startup_packet_from_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    packet_id = "studio-release-promotion-appr-testpacket"
    startup_packet_id = "studio-startup-autostart-appr-testpacket"
    _fake_review_report(tmp_path)
    calls: dict[str, object] = {}

    def fake_review(*args, **kwargs):
        calls.update(kwargs)
        return _fake_review_report(tmp_path)

    monkeypatch.setattr(consumption_module, "build_studio_release_promotion_approval_review", fake_review)

    report = build_studio_release_promotion_approval_consumption_dry_run(
        tmp_path,
        approval_packet_id=packet_id,
    )

    assert report["ok"] is True
    assert report["summary"]["startup_approval_packet_id"] == startup_packet_id
    assert calls["startup_approval_packet_id"] == startup_packet_id


def test_release_promotion_marker_reservation_dry_run_proves_duplicate_block_without_writing() -> None:
    proof = _marker_reservation_dry_run(marker_exists=False)

    assert proof["proof_mode"] == "in_memory_no_real_marker_write"
    assert proof["first_reservation_allowed"] is True
    assert proof["duplicate_reservation_blocked"] is True
    assert proof["real_marker_written"] is False
    assert proof["real_marker_reserved"] is False
    assert proof["proof_passed"] is True


def test_release_promotion_consumption_dry_run_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-07T00:00:00Z",
        "next_recommended_pass": NEXT_RELEASE_APPROVED_EXECUTION_PROOF_PASS,
        "summary": {
            "approval_packet_id": "studio-release-promotion-appr-test",
            "request_digest_sha256": "abc",
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "release_status_write_allowed": False,
            "release_promotion_allowed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
        },
        "approval_artifact": {"path": "approval.json"},
        "exact_once_marker_contract": {"path": "marker.json", "exists": False},
        "marker_reservation_dry_run": {
            "real_marker_written": False,
            "first_reservation_allowed": True,
            "duplicate_reservation_blocked": True,
            "proof_passed": True,
        },
        "future_output_paths": {"release_status_preview": {"path": "status.json", "exists": False}},
        "checks": {"approval_artifact_present": True},
        "blockers": [],
        "unverified": ["No real marker write was attempted."],
    }

    evidence = write_release_promotion_approval_consumption_dry_run_evidence(
        tmp_path,
        report,
        evidence_slug="release-promotion-consumption-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
