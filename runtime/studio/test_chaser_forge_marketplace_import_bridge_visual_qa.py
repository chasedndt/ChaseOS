from __future__ import annotations

from pathlib import Path

from runtime.studio.chaser_forge_marketplace_import_bridge_visual_qa import (
    PASS_ID,
    REQUIRED_TOKENS,
    build_chaser_forge_marketplace_import_bridge_visual_qa,
    format_chaser_forge_marketplace_import_bridge_visual_qa,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fake_runner(vault: Path, output_dir: Path, panel_data: dict) -> dict:
    shot_paths = []
    marketplace = panel_data["marketplace"]
    bridge = marketplace["import_sandbox_request"]
    assert bridge["status"] == "forge_marketplace_import_sandbox_request_written"
    assert bridge["sandbox_approval_request_written"] is True
    assert bridge["marketplace_import_approval_consumed"] is False
    assert bridge["registry_written"] is False
    for viewport in ("desktop", "mobile"):
        path = output_dir / f"{viewport}-chaser-forge-marketplace-bridge.png"
        _write(path, "x" * 12048)
        shot_paths.append(
            {
                "viewport": viewport,
                "path": path.relative_to(vault).as_posix(),
                "exists": True,
                "bytes": path.stat().st_size,
                "not_blank": True,
                "marketplace_section_visible": True,
                "bridge_api_tokens_visible": True,
                "bridge_written_state_visible": True,
                "framework_overlay_detected": False,
                "missing_required_tokens": [],
            }
        )
    return {
        "url": "file:///stub/index.html#/chaser-forge",
        "screenshots": shot_paths,
        "console_errors_or_warnings": [],
        "page_errors": [],
    }


def test_marketplace_import_bridge_visual_qa_reports_rendered_bridge_state(tmp_path: Path) -> None:
    report = build_chaser_forge_marketplace_import_bridge_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-marketplace-bridge",
        screenshot_runner=_fake_runner,
    )

    assert report["ok"] is True
    assert report["pass_id"] == PASS_ID
    assert report["status"] == "COMPLETE / MARKETPLACE PUBLISH AND INSTALL STUDIO UI VISUAL QA VERIFIED"
    assert report["summary"]["marketplace_section_visible"] is True
    assert report["summary"]["bridge_api_tokens_visible"] is True
    assert report["summary"]["bridge_written_state_visible"] is True
    assert report["summary"]["desktop_and_mobile_checked"] is True
    assert report["required_tokens"] == list(REQUIRED_TOKENS)
    assert report["fixture_evidence"]["marketplace_import_approval_status"] == "approved"
    assert report["fixture_evidence"]["marketplace_import_approval_consumed"] is False
    assert report["fixture_evidence"]["sandbox_approval_request_written"] is True
    assert report["fixture_evidence"]["sandbox_approval_status"] == "pending_operator_decision"
    assert report["fixture_evidence"]["sandbox_approval_consumed"] is False
    assert report["fixture_evidence"]["registry_written"] is False
    assert report["fixture_evidence"]["extension_files_written"] == []
    assert report["fixture_evidence"]["exact_once_marker_reserved"] is False
    assert report["authority"]["real_vault_approval_artifact_write_allowed"] is False
    assert report["authority"]["real_vault_sandbox_approval_request_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["forge_registry_mutation_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert len(report["screenshots"]) == 2
    assert (tmp_path / report["report_path"]).is_file()
    assert (tmp_path / report["markdown_report_path"]).is_file()
    assert not (tmp_path / "_cfvqa").exists()


def test_marketplace_import_bridge_visual_qa_blocks_when_bridge_tokens_missing(tmp_path: Path) -> None:
    def missing_token_runner(vault: Path, output_dir: Path, panel_data: dict) -> dict:
        path = output_dir / "desktop-chaser-forge-marketplace-bridge.png"
        _write(path, "x" * 12048)
        return {
            "url": "file:///stub/index.html#/chaser-forge",
            "screenshots": [
                {
                    "viewport": "desktop",
                    "path": path.relative_to(vault).as_posix(),
                    "exists": True,
                    "bytes": path.stat().st_size,
                    "not_blank": True,
                    "marketplace_section_visible": True,
                    "bridge_api_tokens_visible": False,
                    "bridge_written_state_visible": False,
                    "framework_overlay_detected": False,
                    "missing_required_tokens": ["request_chaser_forge_marketplace_import_sandbox_request"],
                }
            ],
            "console_errors_or_warnings": [],
            "page_errors": [],
        }

    report = build_chaser_forge_marketplace_import_bridge_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-marketplace-bridge",
        screenshot_runner=missing_token_runner,
    )

    assert report["ok"] is False
    assert "bridge_api_tokens_not_visible" in report["blockers"]
    assert "bridge_written_state_not_visible" in report["blockers"]
    assert "missing_required_token:request_chaser_forge_marketplace_import_sandbox_request" in report["blockers"]


def test_marketplace_import_bridge_visual_qa_text_output_states_boundary(tmp_path: Path) -> None:
    report = build_chaser_forge_marketplace_import_bridge_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-marketplace-bridge",
        screenshot_runner=_fake_runner,
    )
    output = format_chaser_forge_marketplace_import_bridge_visual_qa(report)

    assert "Chaser Forge Marketplace Import Sandbox Request Bridge Visual QA" in output
    assert "marketplace_section_visible: True" in output
    assert "bridge_api_tokens_visible: True" in output
    assert "sandbox_approval_request_written: True" in output
    assert "marketplace_import_approval_consumed: False" in output
    assert "Boundary: visual proof only" in output
