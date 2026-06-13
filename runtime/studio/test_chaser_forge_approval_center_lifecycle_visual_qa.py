from __future__ import annotations

from pathlib import Path

from runtime.studio.chaser_forge_approval_center_lifecycle_visual_qa import (
    PASS_ID,
    build_chaser_forge_approval_center_lifecycle_visual_qa,
    format_chaser_forge_approval_center_lifecycle_visual_qa,
)


def test_chaser_forge_approval_center_lifecycle_visual_qa_builds_static_contract(tmp_path: Path) -> None:
    report = build_chaser_forge_approval_center_lifecycle_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-approval-center",
        capture_screenshots=False,
    )

    assert report["ok"] is True
    assert report["pass"] == PASS_ID
    assert report["summary"]["source_group_visible"] is True
    assert report["summary"]["source_specific_decision_handoff_visible"] is True
    assert report["summary"]["decision_handoff_api_method"] == "review_chaser_forge_approval_decision"
    assert set(report["summary"]["lifecycle_statuses"]) >= {
        "pending_operator_review",
        "approved_pending_execution",
        "consumed",
        "rejected",
        "invalid_packet",
    }
    assert report["summary"]["artifact_count"] == 5
    assert report["summary"]["pending_count"] == 1
    assert report["summary"]["ready_count"] == 2
    assert report["summary"]["blocked_count"] == 2
    assert report["authority"]["approval_decision_allowed"] is False
    assert report["authority"]["source_specific_decision_handoff_visible"] is True
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["forge_registry_mutation_allowed"] is False
    assert report["authority"]["extension_file_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert (tmp_path / str(report["evidence"]["html_path"])).is_file()
    assert (tmp_path / str(report["evidence"]["report_path"])).is_file()
    assert (tmp_path / str(report["evidence"]["markdown_path"])).is_file()
    assert report["evidence"]["fixture_vault_persisted"] is False
    assert not (tmp_path / "07_LOGS/Studio-Visual-QA/test-forge-approval-center/_fixture_vault").exists()
    app_js = (Path(__file__).resolve().parent / "shell" / "frontend" / "app.js").read_text(encoding="utf-8")
    assert "approvalCenterGroupSummary" in app_js
    assert "approvalCenterHandoffSummary" in app_js
    assert "Source-Specific Decision Handoffs" in app_js
    assert "status_counts" in app_js


def test_chaser_forge_approval_center_lifecycle_visual_qa_accepts_injected_screenshot_runner(tmp_path: Path) -> None:
    def fake_runner(**kwargs):
        output_dir = Path(kwargs["output_dir"])
        screenshots = []
        for name in ("desktop", "mobile"):
            path = output_dir / f"{name}-approval-center-forge-lifecycle.png"
            path.write_bytes(b"fake-png" * 2048)
            screenshots.append(
                {
                    "viewport": name,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "status_text": "Pending review",
                    "body_text_length": 512,
                    "source_group_visible": True,
                    "missing_lifecycle_tokens": [],
                    "not_blank": True,
                    "framework_overlay_detected": False,
                    "console_messages": [],
                }
            )
        return screenshots

    report = build_chaser_forge_approval_center_lifecycle_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-approval-center",
        capture_screenshots=True,
        screenshot_runner=fake_runner,
    )

    assert report["ok"] is True
    assert report["summary"]["screenshot_captured"] is True
    assert report["summary"]["desktop_and_mobile_checked"] is True
    assert len(report["evidence"]["screenshots"]) == 2
    assert all((tmp_path / item["path"]).is_file() for item in report["evidence"]["screenshots"])


def test_chaser_forge_approval_center_lifecycle_visual_qa_text_output_states_boundary(tmp_path: Path) -> None:
    report = build_chaser_forge_approval_center_lifecycle_visual_qa(
        tmp_path,
        output_dir="07_LOGS/Studio-Visual-QA/test-forge-approval-center",
        capture_screenshots=False,
    )
    output = format_chaser_forge_approval_center_lifecycle_visual_qa(report)

    assert "Chaser Forge Approval Center Lifecycle Visual QA" in output
    assert "source_group_visible: True" in output
    assert "source_specific_decision_handoff_visible: True" in output
    assert "screenshot_captured: False" in output
    assert "Boundary: visual proof only" in output
