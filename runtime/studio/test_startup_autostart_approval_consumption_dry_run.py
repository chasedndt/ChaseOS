"""Tests for the Studio startup/autostart approval consumption dry-run pass."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.startup_autostart_approval_consumption_dry_run as consumption_module
from runtime.studio.startup_autostart_approval_consumption_dry_run import (
    BLOCKED_STATUS,
    NEXT_RELEASE_PROMOTION_APPROVAL_PASS,
    NEXT_STARTUP_APPROVED_EXECUTION_PROOF_PASS,
    READY_STATUS,
    _marker_reservation_dry_run,
    build_studio_startup_autostart_approval_consumption_dry_run,
    write_startup_autostart_approval_consumption_dry_run_evidence,
)


VAULT_ROOT = Path(__file__).resolve().parents[2]


def _fake_review_report(tmp_path: Path, *, artifact_present: bool = True, marker_present: bool = False) -> dict:
    packet_id = "studio-startup-autostart-appr-testpacket"
    digest = "a" * 64
    signed_zip_sha = "b" * 64
    manifest_sha = "c" * 64
    signing_marker_sha = "d" * 64
    host_targets = [
        "windows-startup-folder-shortcut",
        "windows-task-scheduler",
        "windows-registry-run-key",
        "start-menu-shortcut",
        "desktop-shortcut",
    ]
    approval_path = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/studio-startup-autostart-appr-testpacket.json"
    )
    marker_path = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/studio-startup-autostart-appr-testpacket.json"
    )
    payload = {
        "record_type": "studio_startup_autostart_approval_artifact",
        "schema_version": "studio.startup_autostart_approval_review.v1",
        "status": "studio_startup_autostart_approval_artifact_written_no_host_mutation",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "approval_scope": "one_startup_autostart_proof_only",
        "approved_signing_execution_marker_sha256": signing_marker_sha,
        "approved_signed_portable_zip_sha256": signed_zip_sha,
        "approved_signing_manifest_sha256": manifest_sha,
        "approved_startup_mode": "windows-startup-folder-shortcut-preview",
        "approved_target_platform": "windows",
        "approved_host_targets": host_targets,
        "approval_consumption_required": True,
        "future_single_startup_autostart_proof_approved": True,
        "startup_mutation_allowed_in_this_pass": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "host_path_resolution_attempted": False,
        "resolves_host_startup_paths": False,
        "writes_host_startup": False,
        "registers_autostart": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
        "release_promotion_allowed": False,
        "writes_release_status": False,
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
    return {
        "ok": True,
        "status": "studio_startup_autostart_approval_artifact_existing_matching_no_host_mutation",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_ready": True,
            "approval_artifact_written": artifact_present,
            "approval_decision_consumed": False,
            "exact_once_marker_exists": marker_present,
            "host_path_resolution_attempted": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
            "release_promotion_allowed": False,
        },
        "source_preview": {
            "startup_autostart_approval_packet_preview": {
                "approval_packet_id": packet_id,
                "request_digest_sha256": digest,
                "approval_material": {
                    "startup_mode": "windows-startup-folder-shortcut-preview",
                    "target_platform": "windows",
                    "candidate_host_targets": host_targets,
                    "signed_portable_zip_sha256": signed_zip_sha,
                    "signing_manifest_sha256": manifest_sha,
                    "signing_execution_marker_sha256": signing_marker_sha,
                },
            },
            "source_artifacts": {
                "signing_exact_once_marker": {"path": "signing-marker.json", "exists": True, "sha256": signing_marker_sha},
                "signed_portable_zip": {
                    "path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
                    "exists": True,
                    "sha256": signed_zip_sha,
                },
                "signing_manifest": {
                    "path": ".pytest_tmp_env/studio-signing-proof/manifest/studio-signing-appr-test-signing-manifest.json",
                    "exists": True,
                    "sha256": manifest_sha,
                },
            },
        },
        "approval_artifact": {
            "path": "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/studio-startup-autostart-appr-testpacket.json",
            "exists_after": artifact_present,
            "matches_current_packet": artifact_present,
        },
        "exact_once_marker_contract": {
            "path": "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/studio-startup-autostart-appr-testpacket.json",
            "exists": marker_present,
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {"path": ".pytest_tmp_env/studio-startup-autostart-proof", "exists": False},
            "startup_dry_run_evidence": {
                "path": "07_LOGS/Studio-Graph-Views/studio-startup-autostart-appr-testpacket-startup-autostart-dry-run.json",
                "exists": False,
                "size_bytes": 0,
            },
            "startup_execution_evidence": {
                "path": "07_LOGS/Studio-Graph-Views/studio-startup-autostart-appr-testpacket-startup-autostart-execution.json",
                "exists": False,
                "size_bytes": 0,
            },
            "rollback_plan": {
                "path": ".pytest_tmp_env/studio-startup-autostart-proof/rollback/studio-startup-autostart-appr-testpacket-startup-autostart-rollback-plan.json",
                "exists": False,
                "size_bytes": 0,
            },
            "host_mutation_audit": {
                "path": ".pytest_tmp_env/studio-startup-autostart-proof/audit/studio-startup-autostart-appr-testpacket-startup-autostart-host-mutation-audit.json",
                "exists": False,
                "size_bytes": 0,
            },
        },
        "checks": {
            "future_output_paths_clear": True,
            "signing_execution_proof_complete": True,
        },
        "blockers": [],
    }


def test_startup_autostart_consumption_dry_run_validates_current_repo_approval_without_host_mutation() -> None:
    report = build_studio_startup_autostart_approval_consumption_dry_run(
        VAULT_ROOT,
        approval_packet_id="studio-startup-autostart-appr-a90e121d6b079a51",
    )

    marker_path = VAULT_ROOT / report["exact_once_marker_contract"]["path"]
    output_root = VAULT_ROOT / ".pytest_tmp_env/studio-startup-autostart-proof"

    if report["ok"] is False:
        assert report["status"] == BLOCKED_STATUS
        assert report["writes_performed"] is False
        assert report["summary"]["host_startup_mutation_allowed"] is False
        assert report["summary"]["autostart_registration_allowed"] is False
        assert report["authority"]["consumes_approval_decision"] is False
        assert report["authority"]["writes_idempotency_marker"] is False
        assert report["authority"]["writes_host_startup"] is False
        assert report["authority"]["registers_autostart"] is False
        assert report["authority"]["canonical_mutation_allowed"] is False
        assert report["blockers"]
        return

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["approval_artifact_present"] is True
    assert report["summary"]["approval_digest_matches"] is True
    assert report["summary"]["approval_scope_valid"] is True
    assert report["summary"]["signed_portable_zip_hash_matches"] is True
    assert report["summary"]["signing_manifest_hash_matches"] is True
    assert report["summary"]["signing_execution_marker_hash_matches"] is True
    assert report["summary"]["approved_host_targets_match"] is True
    assert report["summary"]["exact_once_marker_absent"] is True
    assert report["summary"]["marker_reservation_proof_passed"] is True
    assert report["summary"]["duplicate_consumption_blocked"] is True
    if report["summary"]["startup_autostart_execution_proof_complete"]:
        assert report["summary"]["approval_consumed"] is True
        assert report["summary"]["exact_once_marker_reserved"] is True
        assert report["next_recommended_pass"] == NEXT_RELEASE_PROMOTION_APPROVAL_PASS
    else:
        assert report["summary"]["approval_consumed"] is False
        assert report["summary"]["exact_once_marker_reserved"] is False
        assert report["next_recommended_pass"] == NEXT_STARTUP_APPROVED_EXECUTION_PROOF_PASS
    assert report["summary"]["host_path_resolution_attempted"] is False
    assert report["summary"]["host_startup_mutation_allowed"] is False
    assert report["summary"]["autostart_registration_allowed"] is False
    assert report["summary"]["registry_write_allowed"] is False
    assert report["summary"]["start_menu_write_allowed"] is False
    assert report["summary"]["desktop_shortcut_write_allowed"] is False
    assert report["writes_performed"] is False
    assert report["authority"]["consumes_approval_decision"] is False
    assert report["authority"]["writes_idempotency_marker"] is False
    assert report["authority"]["resolves_host_startup_paths"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["registers_autostart"] is False
    assert report["authority"]["writes_registry"] is False
    assert report["authority"]["writes_start_menu"] is False
    assert report["authority"]["writes_desktop_shortcut"] is False
    assert report["authority"]["promotes_release"] is False
    if report["summary"]["startup_autostart_execution_proof_complete"]:
        assert marker_path.exists() is True
        assert output_root.exists() is True
    else:
        assert marker_path.exists() is False
        assert output_root.exists() is False


def test_startup_autostart_consumption_dry_run_blocks_missing_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_startup_autostart_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path, artifact_present=False),
    )

    report = build_studio_startup_autostart_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "approval_artifact_present" in report["blockers"]
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False


def test_startup_autostart_consumption_dry_run_derives_signing_packet_from_existing_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    approval_path = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/studio-startup-autostart-appr-testpacket.json"
    )
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(
        json.dumps(
            {
                "record_type": "studio_startup_autostart_approval_artifact",
                "approval_packet_id": "studio-startup-autostart-appr-testpacket",
                "approved_signing_approval_packet_id": "studio-signing-appr-testpacket",
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_review(*args, **kwargs):
        captured.update(kwargs)
        return _fake_review_report(tmp_path)

    monkeypatch.setattr(consumption_module, "build_studio_startup_autostart_approval_review", fake_review)

    report = build_studio_startup_autostart_approval_consumption_dry_run(
        tmp_path,
        approval_packet_id="studio-startup-autostart-appr-testpacket",
    )

    assert report["ok"] is True
    assert captured["signing_approval_packet_id"] == "studio-signing-appr-testpacket"


def test_startup_autostart_consumption_dry_run_allows_existing_owned_output_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_review(*args, **kwargs):
        report = _fake_review_report(tmp_path)
        report["future_output_paths"]["output_root"]["exists"] = True
        return report

    monkeypatch.setattr(consumption_module, "build_studio_startup_autostart_approval_review", fake_review)

    report = build_studio_startup_autostart_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is True
    assert report["summary"]["future_output_paths_clear"] is True


def test_startup_autostart_consumption_dry_run_blocks_existing_marker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        consumption_module,
        "build_studio_startup_autostart_approval_review",
        lambda *args, **kwargs: _fake_review_report(tmp_path, marker_present=True),
    )

    report = build_studio_startup_autostart_approval_consumption_dry_run(tmp_path)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "real_marker_absent" in report["blockers"]
    assert "marker_reservation_proof_passed" in report["blockers"]
    assert report["marker_reservation_dry_run"]["first_reservation_allowed"] is False
    assert report["marker_reservation_dry_run"]["duplicate_reservation_blocked"] is True


def test_startup_autostart_marker_reservation_dry_run_proves_duplicate_block_without_writing() -> None:
    proof = _marker_reservation_dry_run(marker_exists=False)

    assert proof["proof_mode"] == "in_memory_no_real_marker_write"
    assert proof["first_reservation_allowed"] is True
    assert proof["duplicate_reservation_blocked"] is True
    assert proof["real_marker_written"] is False
    assert proof["real_marker_reserved"] is False
    assert proof["proof_passed"] is True


def test_startup_autostart_consumption_dry_run_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": READY_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_STARTUP_APPROVED_EXECUTION_PROOF_PASS,
        "summary": {
            "approval_packet_id": "studio-startup-autostart-appr-test",
            "request_digest_sha256": "abc",
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "signed_portable_zip_hash_matches": True,
            "signing_manifest_hash_matches": True,
            "approved_host_targets_match": True,
            "approval_consumed": False,
            "host_path_resolution_attempted": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
        },
        "approval_artifact": {"path": "approval.json"},
        "exact_once_marker_contract": {"path": "marker.json", "exists": False},
        "marker_reservation_dry_run": {
            "real_marker_written": False,
            "first_reservation_allowed": True,
            "duplicate_reservation_blocked": True,
            "proof_passed": True,
        },
        "future_output_paths": {
            "startup_execution_evidence": {"path": "out.json", "exists": False},
        },
        "checks": {"approval_artifact_present": True},
        "authority": {"writes_host_startup": False, "canonical_mutation_allowed": False},
        "blockers": [],
        "unverified": ["No host startup mutation was attempted."],
    }

    evidence = write_startup_autostart_approval_consumption_dry_run_evidence(
        tmp_path,
        report,
        evidence_slug="startup-autostart-approval-consumption-dry-run-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
