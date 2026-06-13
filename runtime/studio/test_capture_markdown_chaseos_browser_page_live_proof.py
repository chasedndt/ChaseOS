from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.capture_collector_settings import (
    BrowserPageCapture,
    load_capture_collector_settings,
    save_capture_collector_settings,
)
from runtime.studio.capture_markdown_chaseos_browser_page_live_proof import (
    CONTROLLED_PAGE_SENTINEL,
    run_chaseos_browser_page_live_proof,
)


PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)


def _fake_browser_page(source_url: str) -> BrowserPageCapture:
    return BrowserPageCapture(
        title="Unit Controlled Browser Page",
        source_url=source_url,
        visible_text=f"{CONTROLLED_PAGE_SENTINEL} controlled page body",
        html=(
            "<!doctype html><html><head><title>Unit Controlled Browser Page</title></head>"
            f"<body><main><p>{CONTROLLED_PAGE_SENTINEL}</p></main></body></html>"
        ),
        screenshot_png=PNG_BYTES,
        width=1,
        height=1,
        source="unit_injected_browser_provider",
    )


def test_chaseos_browser_page_live_proof_uses_collector_preview_and_restores_settings(
    tmp_path: Path,
) -> None:
    save_capture_collector_settings(
        tmp_path,
        {
            "clipboard_capture_enabled": True,
            "chaseos_browser_page_capture_enabled": False,
        },
    )

    proof = run_chaseos_browser_page_live_proof(
        vault_root=tmp_path,
        evidence_slug="unit-browser-page-live-proof",
        write_evidence=True,
        browser_provider=_fake_browser_page,
    )

    assert proof["ok"] is True
    assert proof["status"] == "chaseos_browser_page_live_capture_preview_verified"
    assert proof["authority"]["test_injected_browser_provider"] is True
    assert proof["authority"]["launches_chaseos_owned_isolated_browser"] is False
    assert proof["authority"]["reads_personal_active_browser_tab"] is False
    assert proof["capture"]["writes_raw_quarantine_markdown"] is False
    assert proof["preview"]["contains_sentinel"] is True
    assert proof["save"]["requested"] is False

    checks = proof["verification"]["checks"]
    assert checks["collector_capture_ok"] is True
    assert checks["controlled_html_artifact_contains_sentinel"] is True
    assert checks["preview_write_free"] is True
    assert checks["save_markdown_not_requested"] is True

    settings = load_capture_collector_settings(tmp_path)
    assert settings["clipboard_capture_enabled"] is True
    assert settings["chaseos_browser_page_capture_enabled"] is False

    evidence = proof["evidence"]
    json_path = tmp_path / evidence["json_path"]
    markdown_path = tmp_path / evidence["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert json.loads(json_path.read_text(encoding="utf-8"))["ok"] is True
    assert CONTROLLED_PAGE_SENTINEL in markdown_path.read_text(encoding="utf-8")


def test_chaseos_browser_page_live_proof_reports_failed_capture_and_restores_settings(
    tmp_path: Path,
) -> None:
    def failing_browser_page(source_url: str) -> BrowserPageCapture:
        raise RuntimeError(f"blocked test provider for {source_url}")

    proof = run_chaseos_browser_page_live_proof(
        vault_root=tmp_path,
        evidence_slug="unit-browser-page-live-proof-blocked",
        write_evidence=True,
        browser_provider=failing_browser_page,
    )

    assert proof["ok"] is False
    assert proof["status"] == "chaseos_browser_page_live_capture_preview_blocked"
    assert "collector_capture_ok" in proof["verification"]["failed_checks"]
    assert proof["capture"]["blockers"] == ["chaseos_browser_page_capture_failed"]
    assert proof["authority"]["settings_restored_after_run"] is True
    assert not (tmp_path / "runtime" / "studio" / "state" / "capture-collectors.json").exists()

    evidence = proof["evidence"]
    assert (tmp_path / evidence["json_path"]).is_file()
    assert (tmp_path / evidence["markdown_path"]).is_file()
