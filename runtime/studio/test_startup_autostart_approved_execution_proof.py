"""Tests for the governed Studio startup/autostart approved execution proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import runtime.studio.startup_autostart_approved_execution_proof as proof_module
from runtime.studio.startup_autostart_approved_execution_proof import (
    BLOCKED_STATUS,
    COMPLETE_STATUS,
    DUPLICATE_BLOCKED_STATUS,
    NEXT_RELEASE_PROMOTION_APPROVAL_PASS,
    READY_STATUS,
    build_studio_startup_autostart_approved_execution_proof,
    write_startup_autostart_approved_execution_proof_evidence,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fake_consumption_report(
    tmp_path: Path,
    *,
    packet_id: str = "studio-startup-autostart-appr-testpacket",
) -> dict:
    digest = "b" * 64
    signed_zip = tmp_path / ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip"
    signed_zip.parent.mkdir(parents=True, exist_ok=True)
    signed_zip.write_bytes(b"fake signed portable zip")
    signing_manifest = tmp_path / ".pytest_tmp_env/studio-signing-proof/manifest/signing-manifest.json"
    signing_manifest.parent.mkdir(parents=True, exist_ok=True)
    signing_manifest.write_text(json.dumps({"record_type": "studio_signing_manifest"}), encoding="utf-8")
    signing_marker = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-test.json"
    )
    signing_marker.parent.mkdir(parents=True, exist_ok=True)
    signing_marker.write_text(json.dumps({"record_type": "studio_signing_execution_marker"}), encoding="utf-8")
    approval_path = tmp_path / f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/{packet_id}.json"
    marker_path = (
        tmp_path
        / f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{packet_id}.json"
    )
    output_root = tmp_path / ".pytest_tmp_env/studio-startup-autostart-proof"
    targets = [
        "windows-startup-folder-shortcut",
        "windows-task-scheduler",
        "windows-registry-run-key",
        "start-menu-shortcut",
        "desktop-shortcut",
    ]
    approval_payload = {
        "record_type": "studio_startup_autostart_approval_artifact",
        "schema_version": "studio.startup_autostart_approval_review.v1",
        "status": "studio_startup_autostart_approval_artifact_written_no_host_mutation",
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "operator_decision": "approved",
        "reviewer_id": "operator",
        "requested_by": "Codex",
        "approval_scope": "one_startup_autostart_proof_only",
        "approved_signing_approval_packet_id": "studio-signing-appr-test",
        "approved_signing_execution_marker_path": "07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-test.json",
        "approved_signing_execution_marker_sha256": _sha256(signing_marker),
        "approved_signed_portable_zip_path": ".pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip",
        "approved_signed_portable_zip_sha256": _sha256(signed_zip),
        "approved_signing_manifest_path": ".pytest_tmp_env/studio-signing-proof/manifest/signing-manifest.json",
        "approved_signing_manifest_sha256": _sha256(signing_manifest),
        "approved_startup_mode": "windows-startup-folder-shortcut-preview",
        "approved_target_platform": "windows",
        "approved_host_targets": targets,
        "host_target_previews": [
            {
                "id": target,
                "kind": "startup_folder_shortcut" if target == "windows-startup-folder-shortcut" else "deferred_target",
                "status": "approval_required_before_host_mutation",
                "host_path_resolved_now": False,
                "write_allowed_in_this_pass": False,
            }
            for target in targets
        ],
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
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(json.dumps(approval_payload, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "status": "studio_startup_autostart_approval_consumption_dry_run_ready_no_host_mutation",
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": digest,
            "approval_artifact_present": True,
            "approval_digest_matches": True,
            "approval_scope_valid": True,
            "approval_consumed": False,
        },
        "approval_artifact": {
            "path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/{packet_id}.json",
            "exists": True,
        },
        "exact_once_marker_contract": {
            "path": f"07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/{packet_id}.json",
            "exists": marker_path.exists(),
            "reserved_in_this_pass": False,
        },
        "future_output_paths": {
            "output_root": {"path": ".pytest_tmp_env/studio-startup-autostart-proof", "exists": output_root.exists()},
            "startup_dry_run_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-startup-autostart-dry-run.json",
                "exists": False,
                "size_bytes": 0,
            },
            "startup_execution_evidence": {
                "path": f"07_LOGS/Studio-Graph-Views/{packet_id}-startup-autostart-execution.json",
                "exists": False,
                "size_bytes": 0,
            },
            "rollback_plan": {
                "path": f".pytest_tmp_env/studio-startup-autostart-proof/rollback/{packet_id}-startup-autostart-rollback-plan.json",
                "exists": False,
                "size_bytes": 0,
            },
            "host_mutation_audit": {
                "path": f".pytest_tmp_env/studio-startup-autostart-proof/audit/{packet_id}-startup-autostart-host-mutation-audit.json",
                "exists": False,
                "size_bytes": 0,
            },
        },
        "checks": {"future_output_paths_clear": True},
        "blockers": [],
    }


def _patch_consumption(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        proof_module,
        "build_studio_startup_autostart_approval_consumption_dry_run",
        lambda *args, **kwargs: _fake_consumption_report(tmp_path),
    )


def test_startup_autostart_approved_execution_proof_reports_ready_without_writing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_startup_autostart_approved_execution_proof(tmp_path, execute=False)

    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["writes_performed"] is False
    assert report["summary"]["approval_consumed"] is False
    assert report["summary"]["host_path_resolution_attempted"] is False
    assert report["summary"]["host_mutation_performed"] is False
    assert not (tmp_path / ".pytest_tmp_env/studio-startup-autostart-proof").exists()


def test_startup_autostart_approved_execution_proof_writes_marker_audit_and_blocks_duplicate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_startup_autostart_approved_execution_proof(tmp_path, execute=True)

    summary = report["summary"]
    marker_path = (
        tmp_path
        / "07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/studio-startup-autostart-appr-testpacket.json"
    )
    rollback_path = (
        tmp_path
        / ".pytest_tmp_env/studio-startup-autostart-proof/rollback/studio-startup-autostart-appr-testpacket-startup-autostart-rollback-plan.json"
    )
    host_audit_path = (
        tmp_path
        / ".pytest_tmp_env/studio-startup-autostart-proof/audit/studio-startup-autostart-appr-testpacket-startup-autostart-host-mutation-audit.json"
    )
    shortcut_preview = (
        tmp_path
        / ".pytest_tmp_env/studio-startup-autostart-proof/shortcuts/studio-startup-autostart-appr-testpacket-ChaseOS-Studio-startup-shortcut-preview.json"
    )
    host_target_path = (
        tmp_path
        / ".pytest_tmp_env/studio-startup-autostart-proof/host-targets/studio-startup-autostart-appr-testpacket-windows-startup-folder-shortcut.json"
    )
    execution_path = tmp_path / "07_LOGS/Studio-Graph-Views/studio-startup-autostart-appr-testpacket-startup-autostart-execution.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    host_audit = json.loads(host_audit_path.read_text(encoding="utf-8"))
    shortcut_payload = json.loads(shortcut_preview.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == COMPLETE_STATUS
    assert report["writes_performed"] is True
    assert summary["approval_consumed"] is True
    assert summary["exact_once_marker_reserved"] is True
    assert summary["duplicate_execution_blocked"] is True
    assert summary["host_path_resolution_attempted"] is False
    assert summary["host_mutation_performed"] is False
    assert marker["status"] == COMPLETE_STATUS
    assert marker["host_mutation_performed"] is False
    assert rollback_path.is_file()
    assert host_audit_path.is_file()
    assert execution_path.is_file()
    assert shortcut_preview.is_file()
    assert host_target_path.is_file()
    assert host_audit["host_mutation_performed"] is False
    assert host_audit["registry_run_key_written"] is False
    assert shortcut_payload["workspace_preview_only"] is True
    assert shortcut_payload["host_shortcut_written"] is False
    assert report["post_execution_checks"]["shortcut_preview_no_host_write"] is True
    assert report["authority"]["writes_idempotency_marker"] is True
    assert report["authority"]["writes_startup_autostart_audit"] is True
    assert report["authority"]["writes_host_startup"] is False
    assert report["authority"]["writes_registry"] is False
    assert report["next_recommended_pass"] == NEXT_RELEASE_PROMOTION_APPROVAL_PASS

    duplicate = build_studio_startup_autostart_approved_execution_proof(tmp_path, execute=True)

    assert duplicate["ok"] is False
    assert duplicate["status"] == DUPLICATE_BLOCKED_STATUS
    assert duplicate["summary"]["duplicate_execution_blocked"] is True
    assert duplicate["writes_performed"] is False


def test_startup_autostart_approved_execution_proof_blocks_mismatched_packet(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)

    report = build_studio_startup_autostart_approved_execution_proof(
        tmp_path,
        approval_packet_id="studio-startup-autostart-appr-wrong",
        execute=True,
    )

    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert report["writes_performed"] is False


def test_startup_autostart_approved_execution_proof_ignores_prior_packet_workspace_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_consumption(monkeypatch, tmp_path)
    stale_shortcut = (
        tmp_path / ".pytest_tmp_env/studio-startup-autostart-proof/shortcuts/ChaseOS-Studio-startup-shortcut-preview.json"
    )
    stale_target = (
        tmp_path / ".pytest_tmp_env/studio-startup-autostart-proof/host-targets/windows-startup-folder-shortcut.json"
    )
    stale_shortcut.parent.mkdir(parents=True, exist_ok=True)
    stale_target.parent.mkdir(parents=True, exist_ok=True)
    stale_shortcut.write_text(
        json.dumps(
            {
                "record_type": "studio_startup_shortcut_preview_manifest",
                "approval_packet_id": "studio-startup-autostart-appr-old",
                "workspace_preview_only": True,
            }
        ),
        encoding="utf-8",
    )
    stale_target.write_text(
        json.dumps(
            {
                "record_type": "studio_startup_autostart_host_target_proof",
                "approval_packet_id": "studio-startup-autostart-appr-old",
                "workspace_proof_only": True,
            }
        ),
        encoding="utf-8",
    )

    report = build_studio_startup_autostart_approved_execution_proof(tmp_path, execute=True)

    assert report["ok"] is True
    assert report["status"] == COMPLETE_STATUS
    assert report["summary"]["approval_consumed"] is True


def test_startup_autostart_approved_execution_proof_evidence_writer(tmp_path: Path) -> None:
    report = {
        "ok": True,
        "status": COMPLETE_STATUS,
        "generated_at": "2026-05-06T00:00:00Z",
        "next_recommended_pass": NEXT_RELEASE_PROMOTION_APPROVAL_PASS,
        "summary": {
            "approval_packet_id": "studio-startup-autostart-appr-test",
            "approval_consumed": True,
            "execution_performed": True,
            "duplicate_execution_blocked": True,
            "signed_portable_zip_path": "dist/test.zip",
            "signed_portable_zip_sha256": "abc",
            "rollback_plan_path": "rollback.json",
            "host_mutation_audit_path": "audit.json",
            "shortcut_preview_manifest_path": "shortcut.json",
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "release_promotion_allowed": False,
        },
        "post_execution_checks": {"host_mutation_audit_no_host_mutation": True},
        "rollback_boundary": {"owned_output_root": ".pytest_tmp_env/studio-startup-autostart-proof"},
        "authority": {"writes_startup_autostart_audit": True, "writes_host_startup": False},
        "blockers": [],
        "unverified": ["No real host startup write was attempted."],
    }

    evidence = write_startup_autostart_approved_execution_proof_evidence(
        tmp_path,
        report,
        evidence_slug="startup-autostart-approved-execution-proof-test",
    )

    assert evidence["written"] is True
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
