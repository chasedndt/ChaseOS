from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_readonly_card_visual_qa import (
    PASS_ID,
    build_phase11_readonly_card_visual_qa,
    format_phase11_readonly_card_visual_qa,
)


def test_phase11_readonly_card_visual_qa_preview_builds_static_html_without_writes(tmp_path: Path) -> None:
    report = build_phase11_readonly_card_visual_qa(tmp_path)

    assert report["ok"] is True
    assert report["pass"] == PASS_ID
    assert report["summary"]["visual_artifact_ready"] is True
    assert report["summary"]["card_count"] >= 4
    assert report["summary"]["script_tags_present"] is False
    assert report["summary"]["responsive_viewport_ready"] is True
    assert report["summary"]["visual_browser_qa_complete"] is False
    assert report["authority"]["read_only"] is True
    assert report["authority"]["command_execution_allowed"] is False
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["browser_control_allowed"] is False
    assert report["authority"]["vault_writes_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["evidence"]["written"] is False
    assert not (tmp_path / "07_LOGS" / "Studio-Graph-Views").exists()

    html = report["artifact_preview"]["html"]
    assert "phase11-chat-slash-responses" in html
    assert "phase11-chat-slash-card-grid" in html
    assert "Read-Only Slash Responses" in html
    assert "Command Execution" in html
    assert "<script" not in html.lower()


def test_phase11_readonly_card_visual_qa_write_evidence_stays_in_log_root(tmp_path: Path) -> None:
    report = build_phase11_readonly_card_visual_qa(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-card-visual-qa",
    )

    assert report["ok"] is True
    assert report["evidence"]["written"] is True
    html_path = tmp_path / report["evidence"]["html_path"]
    json_path = tmp_path / report["evidence"]["json_path"]
    markdown_path = tmp_path / report["evidence"]["markdown_path"]
    assert html_path.is_file()
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "07_LOGS/Studio-Graph-Views/phase11-readonly-card-visual-qa" in report["evidence"]["html_path"]
    assert "phase11-chat-slash-response-card" in html_path.read_text(encoding="utf-8")
    assert report["summary"]["screenshot_captured"] is False


def test_phase11_readonly_card_visual_qa_capture_uses_loopback_and_records_screenshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_screenshot_runner(**kwargs):
        output_path = Path(str(kwargs["output_path"]))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-png")
        calls.append(kwargs)
        return {
            "success": True,
            "screenshot_path": str(output_path),
            "visual_verification": {
                "ok": True,
                "unique_color_count": 16,
                "dominant_color_ratio": 0.42,
            },
            "adapter_mode": "test",
            "run_id": "browser-test-run",
            "outcome": "COMPLETE",
        }

    report = build_phase11_readonly_card_visual_qa(
        tmp_path,
        write_evidence=True,
        capture_screenshot=True,
        screenshot_runner=fake_screenshot_runner,
        evidence_slug="test-phase11-card-visual-qa",
    )

    assert report["ok"] is True
    assert report["summary"]["visual_browser_qa_complete"] is True
    assert report["summary"]["screenshot_captured"] is True
    assert report["evidence"]["screenshot_path"].endswith(".png")
    assert (tmp_path / report["evidence"]["screenshot_path"]).is_file()
    assert calls
    assert str(calls[0]["url"]).startswith("http://127.0.0.1:")
    assert calls[0]["require_nonblank"] is True
    assert calls[0]["clip_selector"] == ".phase11-readonly-card-visual-qa-root"


def test_phase11_readonly_card_visual_qa_text_output_states_boundary(tmp_path: Path) -> None:
    report = build_phase11_readonly_card_visual_qa(tmp_path)
    output = format_phase11_readonly_card_visual_qa(report)

    assert "Phase 11 Read-Only Card Visual QA" in output
    assert "visual_artifact_ready: True" in output
    assert "command_execution_allowed: False" in output
    assert "Boundary: visual evidence only" in output
