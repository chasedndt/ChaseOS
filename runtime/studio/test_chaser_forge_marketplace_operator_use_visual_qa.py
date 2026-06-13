from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.chaser_forge_marketplace_operator_use_visual_qa import (
    PASS_ID,
    REQUIRED_API_METHODS,
    build_chaser_forge_marketplace_operator_use_visual_qa,
    format_chaser_forge_marketplace_operator_use_visual_qa,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_installed_fixture(fixture: Path) -> None:
    _write(
        fixture / "runtime/forge/registry/extensions.json",
        json.dumps(
            {
                "entries": [
                    {
                        "extension_id": "ugc-campaign-studio",
                        "registry_status": "sandbox_installed",
                        "install_environment": "sandbox",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
    )
    _write(fixture / "extensions/ugc-campaign-studio/manifest.install.json", "{}\n")
    _write(
        fixture / "07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/import.json",
        json.dumps({"status": "consumed", "approval_consumed": True}, indent=2) + "\n",
    )
    _write(
        fixture / "07_LOGS/Agent-Activity/_forge_sandbox_approvals/sandbox.json",
        json.dumps({"status": "consumed", "approval_consumed": True}, indent=2) + "\n",
    )
    _write(
        fixture / "07_LOGS/Agent-Activity/_forge_sandbox_approvals/_sandbox_markers/marker.json",
        json.dumps({"status": "completed"}, indent=2) + "\n",
    )


def _fake_runner(vault: Path, output_dir: Path, fixture: Path) -> dict:
    _seed_installed_fixture(fixture)
    screenshots = []
    for step, viewport, status_text, status_state in (
        ("initial", "desktop", "", ""),
        ("after-publish", "desktop", "Published ugc-campaign-studio", "complete"),
        ("after-install", "desktop", "Marketplace install complete", "complete"),
        ("after-install", "mobile", "Marketplace install complete", "complete"),
    ):
        path = output_dir / f"{step}-{viewport}.png"
        _write(path, "x" * 12048)
        screenshots.append(
            {
                "step": step,
                "viewport": viewport,
                "path": path.relative_to(vault).as_posix(),
                "exists": True,
                "bytes": path.stat().st_size,
                "not_blank": True,
                "marketplace_section_visible": True,
                "publish_button_visible": True,
                "install_button_visible": True,
                "status_text": status_text,
                "status_state": status_state,
                "framework_overlay_detected": False,
            }
        )
    return {
        "url": "file:///stub/index.html#/chaser-forge",
        "title": "ChaseOS Studio",
        "publish_button_count": 1,
        "install_button_count": 1,
        "publish_status_text": "Published ugc-campaign-studio",
        "publish_status_state": "complete",
        "install_status_text": "Marketplace install complete",
        "install_status_state": "complete",
        "operator_confirmations": [
            "Approve marketplace import review?",
            "Approve sandbox install from marketplace?",
        ],
        "js_call_log": [{"method": method} for method in REQUIRED_API_METHODS],
        "api_call_log": [{"method": method, "ok": True} for method in REQUIRED_API_METHODS],
        "screenshots": screenshots,
        "console_errors_or_warnings": [],
        "page_errors": [],
    }


def test_operator_use_visual_qa_reports_button_flow_and_fixture_install(tmp_path: Path) -> None:
    report = build_chaser_forge_marketplace_operator_use_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-chaser-forge-operator-use",
        generated_at="2026-05-21T12:00:00Z",
        flow_runner=_fake_runner,
    )

    assert report["ok"] is True
    assert report["pass_id"] == PASS_ID
    assert report["status"] == "COMPLETE / MARKETPLACE OPERATOR USE STUDIO BUTTON FLOW VERIFIED"
    assert report["summary"]["publish_status_visible_after_refresh"] is True
    assert report["summary"]["install_status_visible_after_refresh"] is True
    assert report["summary"]["required_api_methods_called"] is True
    assert report["summary"]["operator_confirmations_accepted"] == 2
    assert report["summary"]["fixture_registry_written"] is True
    assert report["summary"]["fixture_extension_files_written"] is True
    assert report["summary"]["fixture_import_approval_consumed"] is True
    assert report["summary"]["fixture_sandbox_approval_consumed"] is True
    assert report["summary"]["fixture_exact_once_marker_written"] is True
    assert report["summary"]["fixture_cleanup_completed"] is True
    assert report["authority"]["real_vault_registry_write_allowed"] is False
    assert report["authority"]["remote_marketplace_call_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert (tmp_path / report["report_path"]).is_file()
    assert (tmp_path / report["markdown_report_path"]).is_file()


def test_operator_use_visual_qa_blocks_when_install_status_not_visible(tmp_path: Path) -> None:
    def missing_status_runner(vault: Path, output_dir: Path, fixture: Path) -> dict:
        result = _fake_runner(vault, output_dir, fixture)
        result["install_status_text"] = ""
        result["install_status_state"] = ""
        return result

    report = build_chaser_forge_marketplace_operator_use_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-chaser-forge-operator-use",
        generated_at="2026-05-21T12:05:00Z",
        flow_runner=missing_status_runner,
    )

    assert report["ok"] is False
    assert "summary_check_failed:install_status_visible_after_refresh" in report["blockers"]


def test_operator_use_visual_qa_text_output_states_boundary(tmp_path: Path) -> None:
    report = build_chaser_forge_marketplace_operator_use_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-chaser-forge-operator-use",
        generated_at="2026-05-21T12:10:00Z",
        flow_runner=_fake_runner,
    )
    output = format_chaser_forge_marketplace_operator_use_visual_qa(report)

    assert "Chaser Forge Marketplace Operator Use Studio Proof" in output
    assert "publish_status_visible_after_refresh: True" in output
    assert "install_status_visible_after_refresh: True" in output
    assert "registry_written: True" in output
    assert "Boundary: production frontend button proof" in output
