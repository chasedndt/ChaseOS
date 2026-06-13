from __future__ import annotations

from pathlib import Path

from runtime.studio.chaser_forge_live_studio_control_proof import (
    PASS_ID,
    build_chaser_forge_live_studio_control_proof,
    render_chaser_forge_live_studio_control_proof,
)


def test_live_studio_control_proof_exercises_forge_controls_in_temp_fixtures(tmp_path: Path) -> None:
    report = build_chaser_forge_live_studio_control_proof(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-chaser-forge-live-control-proof",
        generated_at="2026-05-21T08:00:00Z",
    )

    assert report["ok"] is True
    assert report["pass_id"] == PASS_ID
    assert report["status"] == "COMPLETE / MARKETPLACE LIVE STUDIO CONTROL PROOF VERIFIED"
    assert report["lifecycle_controls"]["checks"]["sandbox_registry_written"] is True
    assert report["lifecycle_controls"]["checks"]["live_install_executed"] is True
    assert report["lifecycle_controls"]["checks"]["rollback_executed"] is True
    assert report["lifecycle_controls"]["checks"]["registry_returned_to_sandbox"] is True
    assert report["lifecycle_controls"]["sandbox"]["approval_consumed"] is True
    assert report["lifecycle_controls"]["live_install"]["approval_consumed"] is True
    assert report["lifecycle_controls"]["rollback"]["approval_consumed"] is True
    assert report["marketplace_controls"]["checks"]["package_artifact_written"] is True
    assert report["marketplace_controls"]["checks"]["catalog_listing_written"] is True
    assert report["marketplace_controls"]["checks"]["import_approval_written"] is True
    assert report["marketplace_controls"]["checks"]["sandbox_request_written"] is True
    assert report["marketplace_controls"]["checks"]["marketplace_install_executed"] is True
    assert report["marketplace_controls"]["checks"]["marketplace_import_approval_consumed_by_install"] is True
    assert report["marketplace_controls"]["checks"]["registry_written_by_marketplace_install"] is True
    assert report["marketplace_controls"]["marketplace_install"]["marketplace_install_executed"] is True
    assert report["marketplace_controls"]["marketplace_install"]["registry_written"] is True
    assert report["marketplace_controls"]["marketplace_install"]["extension_files_written"]
    assert report["marketplace_controls"]["marketplace_install"]["exact_once_marker_reserved"] is True
    assert report["fixture_policy"]["lifecycle_cleanup_completed"] is True
    assert report["fixture_policy"]["marketplace_cleanup_completed"] is True
    assert report["authority"]["real_vault_registry_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert (tmp_path / report["report_path"]).is_file()
    assert (tmp_path / report["markdown_report_path"]).is_file()


def test_live_studio_control_proof_dry_run_does_not_write_report(tmp_path: Path) -> None:
    report = build_chaser_forge_live_studio_control_proof(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-chaser-forge-live-control-proof",
        generated_at="2026-05-21T08:05:00Z",
        write=False,
    )

    assert report["ok"] is True
    assert report["write_executed"] is False
    assert not (tmp_path / report["report_path"]).exists()
    assert not (tmp_path / report["markdown_report_path"]).exists()


def test_live_studio_control_proof_markdown_states_boundary(tmp_path: Path) -> None:
    report = build_chaser_forge_live_studio_control_proof(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-chaser-forge-live-control-proof",
        generated_at="2026-05-21T08:10:00Z",
        write=False,
    )

    output = render_chaser_forge_live_studio_control_proof(report)

    assert "Chaser Forge Live Studio Control Proof" in output
    assert "Sandbox registry written: true" in output
    assert "Live install executed: true" in output
    assert "Rollback executed: true" in output
    assert "Catalog listing written in fixture: true" in output
    assert "Registry written by marketplace install: true" in output
    assert "temporary fixture vaults only" in output
