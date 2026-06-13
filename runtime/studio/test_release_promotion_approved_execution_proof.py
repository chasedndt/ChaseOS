"""Tests for the governed Studio release-promotion approved execution proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import runtime.studio.release_promotion_approved_execution_proof as proof_module
from runtime.studio.release_promotion_approved_execution_proof import (
    BLOCKED_STATUS,
    COMPLETE_STATUS,
    DUPLICATE_BLOCKED_STATUS,
    NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
    READY_STATUS,
    build_studio_release_promotion_approved_execution_proof,
    write_release_promotion_approved_execution_proof_evidence,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _fake_consumption_report(
    tmp_path: Path,
    *,
    packet_id: str = "studio-release-promotion-appr-testpacket",
    output_collision: bool = False,
) -> dict:
    digest = "a" * 64
    startup_packet_id = "studio-startup-autostart-appr-testpacket"
    startup_marker = tmp_path / f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{startup_packet_id}.json"
    signed_zip = tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip"
    signing_manifest = tmp_path / ".pytest_tmp_env/studio-signing-proof/manifest/test-signing-manifest.json"
    startup_evidence = tmp_path / f"07_LOGS/Studio-Graph-Views/{startup_packet_id}-startup-autostart-execution.json"
    startup_audit = tmp_path / f".pytest_tmp_env/studio-startup-autostart-proof/audit/{startup_packet_id}-startup-autostart-host-mutation-audit.json"
    startup_rollback = tmp_path / f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{startup_packet_id}-startup-autostart-rollback-plan.json"
    _write_json(startup_marker, {"record_type": "studio_startup_autostart_execution_marker", "status": "complete"})
    _write_bytes(signed_zip, b"fake signed studio zip")
    _write_json(signing_manifest, {"record_type": "studio_signing_manifest"})
    _write_json(startup_evidence, {"record_type": "studio_startup_autostart_execution_evidence"})
    _write_json(startup_audit, {"record_type": "studio_startup_autostart_host_mutation_audit", "host_mutation_performed": False})
    _write_json(startup_rollback, {"record_type": "studio_startup_autostart_rollback_plan"})

    approval_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/{packet_id}.json"
    marker_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers/{packet_id}.json"
    proof_root = tmp_path / ".pytest_tmp_env/studio-release-promotion-proof"
    release_status_preview = proof_root / f"release-status/{packet_id}-release-status-preview.json"
    if output_collision:
        _write_json(release_status_preview, {"record_type": "collision"})
    approval_payload = {
        "record_type": "studio_release_promotion_approval_artifact",
        "schema_version": "studio.release_promotion_approval_review.v1",
        "status": "studio_release_promotion_approval_artifact_written_no_release_mutation",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "approval_scope": "one_release_promotion_proof_only",
        "approved_startup_approval_packet_id": startup_packet_id,
        "approved_startup_execution_marker_path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{startup_packet_id}.json",
        "approved_startup_execution_marker_sha256": _sha256(startup_marker),
        "approved_signed_portable_zip_path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
        "approved_signed_portable_zip_sha256": _sha256(signed_zip),
        "approved_signing_manifest_path": ".pytest_tmp_env/studio-signing-proof/manifest/test-signing-manifest.json",
        "approved_signing_manifest_sha256": _sha256(signing_manifest),
        "approved_startup_execution_evidence_path": f"07_LOGS/Studio-Graph-Views/{startup_packet_id}-startup-autostart-execution.json",
        "approved_startup_execution_evidence_sha256": _sha256(startup_evidence),
        "approved_startup_host_mutation_audit_path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{startup_packet_id}-startup-autostart-host-mutation-audit.json",
        "approved_startup_host_mutation_audit_sha256": _sha256(startup_audit),
        "approved_startup_rollback_plan_path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{startup_packet_id}-startup-autostart-rollback-plan.json",
        "approved_startup_rollback_plan_sha256": _sha256(startup_rollback),
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
    _write_json(approval_path, approval_payload)
    return {
        "ok": not output_collision,
        "status": "studio_release_promotion_approval_consumption_dry_run_ready_no_release_mutation"
        if not output_collision
        else "blocked_studio_release_promotion_approval_consumption_dry_run",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "approval_consumed": False,
        },
        "approval_artifact": {
            "path": f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/{packet_id}.json",
            "exists": True,
        },
        "exact_once_marker_contract": {
            "path": f"07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers/{packet_id}.json",
            "exists": marker_path.exists(),
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {"path": ".pytest_tmp_env/studio-release-promotion-proof", "exists": proof_root.exists()},
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
                "exists": release_status_preview.exists(),
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
        "blockers": [] if not output_collision else ["future_output_paths_clear"],
    }


def _patch_consumption(monkeypatch, tmp_path: Path, **kwargs) -> None:
    monkeypatch.setattr(
        proof_module,
        "build_studio_release_promotion_approval_consumption_dry_run",
        lambda *args, **_call_kwargs: _fake_consumption_report(tmp_path, **kwargs),
    )


def test_release_promotion_approved_execution_proof_reports_ready_without_writing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_release_promotion_approved_execution_proof(tmp_path, execute=False)

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["writes_performed"] is False
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["release_status_write_allowed"] is False
    assert report["summary"]["release_publication_performed"] is False
    assert report["summary"]["host_mutation_performed"] is False
    assert not (tmp_path / ".pytest_tmp_env/studio-release-promotion-proof").exists()


def test_release_promotion_approved_execution_proof_writes_marker_outputs_and_blocks_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_release_promotion_approved_execution_proof(tmp_path, execute=True)

    summary = report["summary"]
    marker_path = tmp_path / "07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers/studio-release-promotion-appr-testpacket.json"
    dry_run_path = tmp_path / "07_LOGS/Studio-Graph-Views/studio-release-promotion-appr-testpacket-release-promotion-dry-run.json"
    execution_path = tmp_path / "07_LOGS/Studio-Graph-Views/studio-release-promotion-appr-testpacket-release-promotion-execution.json"
    manifest_path = tmp_path / ".pytest_tmp_env/studio-release-promotion-proof/manifest/studio-release-promotion-appr-testpacket-release-manifest.json"
    status_path = (
        tmp_path
        / ".pytest_tmp_env/studio-release-promotion-proof/release-status/studio-release-promotion-appr-testpacket-release-status-preview.json"
    )
    audit_path = tmp_path / ".pytest_tmp_env/studio-release-promotion-proof/audit/studio-release-promotion-appr-testpacket-release-promotion-audit.json"
    rollback_path = tmp_path / ".pytest_tmp_env/studio-release-promotion-proof/rollback/studio-release-promotion-appr-testpacket-release-promotion-rollback-plan.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    dry_run = json.loads(dry_run_path.read_text(encoding="utf-8"))
    release_status = json.loads(status_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == COMPLETE_STATUS
    assert report["writes_performed"] is True
    assert summary["approval_consumed"] is True
    assert summary["exact_once_marker_reserved"] is True
    assert summary["duplicate_execution_blocked"] is True
    assert summary["release_status_preview_written"] is True
    assert summary["release_publication_performed"] is False
    assert summary["release_promotion_allowed"] is False
    assert summary["host_mutation_performed"] is False
    assert marker["status"] == COMPLETE_STATUS
    assert marker["marker_reserved_before_output_writes"] is True
    assert dry_run["exact_once_marker_reserved_before_this_write"] is True
    assert manifest_path.is_file()
    assert status_path.is_file()
    assert audit_path.is_file()
    assert rollback_path.is_file()
    assert execution_path.is_file()
    assert release_status["proof_only"] is True
    assert release_status["release_publication_performed"] is False
    assert audit["release_publication_performed"] is False
    assert report["post_execution_checks"]["release_status_preview_proof_only"] is True
    assert report["post_execution_checks"]["release_audit_no_publication"] is True
    assert report["authority"]["writes_idempotency_marker"] is True
    assert report["authority"]["writes_release_status"] is True
    assert report["authority"]["promotes_release"] is False
    assert report["authority"]["writes_host_startup"] is False
    assert report["next_recommended_pass"] == NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS

    duplicate = build_studio_release_promotion_approved_execution_proof(tmp_path, execute=True)

    assert duplicate["ok"] is False
    assert duplicate["status"] == DUPLICATE_BLOCKED_STATUS
    assert duplicate["summary"]["duplicate_execution_blocked"] is True
    assert duplicate["writes_performed"] is False


def test_release_promotion_approved_execution_proof_requires_execute_for_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_release_promotion_approved_execution_proof(tmp_path, execute=False)

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert not (tmp_path / "07_LOGS/Agent-Activity/_studio_release_promotion_approvals/_execution_markers").exists()
    assert not (tmp_path / ".pytest_tmp_env/studio-release-promotion-proof").exists()


def test_release_promotion_approved_execution_proof_blocks_mismatched_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_release_promotion_approved_execution_proof(
        tmp_path,
        approval_packet_id="studio-release-promotion-appr-wrong",
        execute=True,
    )

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert report["writes_performed"] is False
    assert "approval_packet_argument_matches" in report["blockers"]


def test_release_promotion_approved_execution_proof_blocks_future_output_collision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path, output_collision=True)

    report = build_studio_release_promotion_approved_execution_proof(tmp_path, execute=True)

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert report["writes_performed"] is False
    assert "consumption_dry_run_ok" in report["blockers"]
    assert "future_output_paths_clear_before_execution" in report["blockers"]


def test_release_promotion_approved_execution_proof_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": COMPLETE_STATUS,
        "generated_at": "2026-05-07T00:00:00Z",
        "next_recommended_pass": NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
        "summary": {
            "approval_packet_id": "studio-release-promotion-appr-test",
            "approval_consumed": True,
            "execution_performed": True,
            "duplicate_execution_blocked": True,
            "release_status_preview_path": "status.json",
            "release_manifest_path": "manifest.json",
            "release_promotion_audit_path": "audit.json",
            "rollback_plan_path": "rollback.json",
            "release_publication_performed": False,
            "host_mutation_performed": False,
        },
        "post_execution_checks": {"release_status_preview_proof_only": True},
        "rollback_boundary": {"owned_output_root": ".pytest_tmp_env/studio-release-promotion-proof"},
        "authority": {"writes_release_status": True, "promotes_release": False},
        "blockers": [],
        "unverified": ["No real release publication was attempted."],
    }

    evidence = write_release_promotion_approved_execution_proof_evidence(
        tmp_path,
        report,
        evidence_slug="release-promotion-approved-execution-proof-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
