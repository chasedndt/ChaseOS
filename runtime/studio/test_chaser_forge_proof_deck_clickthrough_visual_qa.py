from __future__ import annotations

import json
from pathlib import Path

from runtime.forge.proof_deck import (
    BUILD_LOG_RELATIVE_PATHS,
    DOC_RELATIVE_PATHS,
    LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH,
    MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH,
    MARKETPLACE_BRIDGE_VISUAL_QA_REPORT_RELATIVE_PATH,
    VISUAL_QA_REPORT_RELATIVE_PATH,
)
from runtime.studio.chaser_forge_proof_deck_clickthrough_visual_qa import (
    REQUIRED_TOKENS,
    build_chaser_forge_proof_deck_clickthrough_visual_qa,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_proof_deck_evidence(vault: Path) -> None:
    for rel_path in BUILD_LOG_RELATIVE_PATHS:
        _write(vault / rel_path, f"# {rel_path.stem}\n\n- Status: PARTIAL / VERIFIED\n")
    for rel_path in DOC_RELATIVE_PATHS:
        _write(vault / rel_path, f"# {rel_path.stem}\n\nStatus: PARTIAL / VERIFIED\n")
    report = {
        "ok": True,
        "status": "PARTIAL / STATIC UI LIFECYCLE PROOF / VERIFIED",
        "summary": {
            "source_group_visible": True,
            "lifecycle_statuses": [
                "approved_pending_execution",
                "consumed",
                "invalid_packet",
                "pending_operator_review",
                "rejected",
            ],
            "lifecycle_tokens_visible": True,
            "artifact_count": 5,
            "pending_count": 1,
            "ready_count": 2,
            "blocked_count": 2,
            "desktop_and_mobile_checked": True,
        },
        "forge_source_group": {
            "status_counts": {
                "approved_pending_execution": 1,
                "consumed": 1,
                "invalid_packet": 1,
                "pending_operator_review": 1,
                "rejected": 1,
            },
            "artifact_count": 5,
            "pending_count": 1,
            "ready_count": 2,
            "blocked_count": 2,
        },
        "evidence": {
            "fixture_vault_persisted": False,
            "screenshots": [
                {
                    "viewport": "desktop",
                    "path": "07_LOGS/Studio-Visual-QA/test/desktop.png",
                    "bytes": 100,
                    "not_blank": True,
                    "source_group_visible": True,
                    "missing_lifecycle_tokens": [],
                },
                {
                    "viewport": "mobile",
                    "path": "07_LOGS/Studio-Visual-QA/test/mobile.png",
                    "bytes": 80,
                    "not_blank": True,
                    "source_group_visible": True,
                    "missing_lifecycle_tokens": [],
                },
            ],
        },
    }
    _write(vault / VISUAL_QA_REPORT_RELATIVE_PATH, json.dumps(report, indent=2) + "\n")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/desktop.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/mobile.png", "mobile")
    marketplace_bridge_report = {
        "ok": True,
        "status": "COMPLETE / MARKETPLACE PUBLISH AND INSTALL STUDIO UI VISUAL QA VERIFIED",
        "summary": {
            "marketplace_section_visible": True,
            "bridge_api_tokens_visible": True,
            "bridge_written_state_visible": True,
            "desktop_and_mobile_checked": True,
        },
        "fixture_evidence": {
            "sandbox_approval_request_written": True,
            "sandbox_approval_artifact_path": "07_LOGS/Agent-Activity/_forge_sandbox_approvals/forge-test.json",
            "marketplace_import_approval_status": "approved",
            "marketplace_import_approval_consumed": False,
            "sandbox_approval_consumed": False,
            "registry_written": False,
            "extension_files_written": [],
            "exact_once_marker_reserved": False,
        },
        "missing_required_tokens": [],
        "console_errors_or_warnings": [],
        "page_errors": [],
        "screenshots": [
            {
                "viewport": "desktop",
                "path": "07_LOGS/Studio-Visual-QA/test/marketplace-desktop.png",
                "bytes": 120,
                "not_blank": True,
                "marketplace_section_visible": True,
                "bridge_api_tokens_visible": True,
                "bridge_written_state_visible": True,
                "missing_required_tokens": [],
            },
            {
                "viewport": "mobile",
                "path": "07_LOGS/Studio-Visual-QA/test/marketplace-mobile.png",
                "bytes": 90,
                "not_blank": True,
                "marketplace_section_visible": True,
                "bridge_api_tokens_visible": True,
                "bridge_written_state_visible": True,
                "missing_required_tokens": [],
            },
        ],
    }
    _write(
        vault / MARKETPLACE_BRIDGE_VISUAL_QA_FALLBACK_REPORT_RELATIVE_PATH,
        json.dumps(marketplace_bridge_report, indent=2) + "\n",
    )
    _write(vault / "07_LOGS/Studio-Visual-QA/test/marketplace-desktop.png", "desktop")
    _write(vault / "07_LOGS/Studio-Visual-QA/test/marketplace-mobile.png", "mobile")
    live_control_report = {
        "ok": True,
        "status": "COMPLETE / MARKETPLACE LIVE STUDIO CONTROL PROOF VERIFIED",
        "fixture_policy": {
            "lifecycle_cleanup_completed": True,
            "marketplace_cleanup_completed": True,
        },
        "lifecycle_controls": {
            "checks": {
                "sandbox_wrong_digest_blocked": True,
                "sandbox_decision_recorded": True,
                "sandbox_ready_without_write": True,
                "sandbox_registry_written": True,
                "sandbox_approval_consumed": True,
                "live_wrong_digest_blocked": True,
                "live_decision_recorded": True,
                "live_ready_without_write": True,
                "live_install_executed": True,
                "live_approval_consumed": True,
                "rollback_wrong_digest_blocked": True,
                "rollback_decision_recorded": True,
                "rollback_ready_without_write": True,
                "rollback_executed": True,
                "rollback_approval_consumed": True,
                "registry_returned_to_sandbox": True,
                "extension_files_retained_after_rollback": True,
                "protected_core_mutation_blocked": True,
            }
        },
        "marketplace_controls": {
            "marketplace_publish": {
                "catalog_listing_written": True,
                "catalog_entry_count": 1,
            },
            "sandbox_request_bridge": {
                "marketplace_import_approval_consumed": False,
                "registry_written": False,
                "extension_files_written": [],
                "exact_once_marker_reserved": False,
            },
            "marketplace_install": {
                "marketplace_install_executed": True,
                "marketplace_import_approval_consumed": True,
                "sandbox_approval_consumed": True,
                "registry_written": True,
                "extension_files_written": ["extensions/ugc-campaign-studio/manifest.install.json"],
                "exact_once_marker_reserved": True,
            },
            "checks": {
                "package_wrong_digest_blocked": True,
                "package_artifact_written": True,
                "import_preview_ok": True,
                "import_preview_no_install": True,
                "catalog_initially_readable": True,
                "publish_preview_ok": True,
                "publish_wrong_digest_blocked": True,
                "catalog_listing_written": True,
                "catalog_entry_readable": True,
                "import_approval_wrong_digest_blocked": True,
                "import_approval_written": True,
                "import_decision_recorded": True,
                "bridge_preview_ok": True,
                "bridge_wrong_digest_blocked": True,
                "sandbox_request_written": True,
                "sandbox_decision_recorded": True,
                "marketplace_install_ready_without_write": True,
                "marketplace_install_executed": True,
                "marketplace_import_approval_consumed_by_install": True,
                "sandbox_approval_consumed_by_install": True,
                "registry_written_by_marketplace_install": True,
                "extension_files_written_by_marketplace_install": True,
                "exact_once_marker_reserved_by_marketplace_install": True,
                "duplicate_marketplace_install_blocked": True,
            },
        },
        "authority": {
            "real_vault_forge_approval_write_allowed": False,
            "real_vault_registry_write_allowed": False,
            "real_vault_extension_file_write_allowed": False,
            "real_vault_exact_once_marker_write_allowed": False,
            "provider_or_model_call_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "protected_core_mutation_allowed": False,
            "pulse_memory_mutation_allowed": False,
            "personal_map_mutation_allowed": False,
            "rnd_truth_state_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }
    _write(
        vault / LIVE_STUDIO_CONTROL_PROOF_FALLBACK_REPORT_RELATIVE_PATH,
        json.dumps(live_control_report, indent=2) + "\n",
    )


def _fake_runner(vault: Path, output_dir: Path, panel_data: dict) -> dict:
    shot_paths = []
    for viewport in ("desktop", "mobile"):
        path = output_dir / f"{viewport}-chaser-forge-proof-deck-clickthrough.png"
        _write(path, "x" * 2048)
        shot_paths.append(
            {
                "viewport": viewport,
                "path": path.relative_to(vault).as_posix(),
                "exists": True,
                "bytes": path.stat().st_size,
                "not_blank": True,
                "proof_deck_section_visible": True,
                "missing_required_tokens": [],
            }
        )
    assert panel_data["proof_deck"]["surface"] == "chaser_forge_proof_deck"
    return {
        "url": "file:///stub/index.html#/chaser-forge",
        "screenshots": shot_paths,
        "console_errors_or_warnings": [],
        "page_errors": [],
    }


def test_clickthrough_visual_qa_reports_rendered_proof_deck_section(tmp_path: Path) -> None:
    _seed_proof_deck_evidence(tmp_path)

    report = build_chaser_forge_proof_deck_clickthrough_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-proof-deck-clickthrough",
        screenshot_runner=_fake_runner,
    )

    assert report["ok"] is True
    assert report["status"] == "COMPLETE / MARKETPLACE PROOF DECK STUDIO CLICKTHROUGH VERIFIED"
    assert report["proof_deck_status"] == "COMPLETE / PROOF DECK READY"
    assert report["proof_deck_read_only"] is True
    assert report["blockers"] == []
    assert report["required_tokens"] == list(REQUIRED_TOKENS)
    assert len(report["screenshots"]) == 2
    assert all(shot["proof_deck_section_visible"] is True for shot in report["screenshots"])
    assert (tmp_path / report["report_path"]).is_file()
    assert (tmp_path / report["markdown_report_path"]).is_file()
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["forge_registry_mutation_allowed"] is False


def test_clickthrough_visual_qa_blocks_when_proof_deck_evidence_missing(tmp_path: Path) -> None:
    report = build_chaser_forge_proof_deck_clickthrough_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-proof-deck-clickthrough",
        screenshot_runner=_fake_runner,
    )

    assert report["ok"] is False
    assert "proof_deck_not_ready" in report["blockers"]
