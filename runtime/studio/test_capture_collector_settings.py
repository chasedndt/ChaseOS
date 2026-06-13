from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.capture_collector_settings import (
    AccessibilityTreeCapture,
    ActiveWindowCapture,
    BrowserPageCapture,
    ClipboardText,
    DisplayRegionCapture,
    ScreenCaptureImage,
    SelectedText,
    build_capture_collector_settings_model,
    capture_active_chaseos_browser_for_markdown,
    capture_active_window_for_markdown,
    capture_accessibility_tree_for_markdown,
    capture_browser_artifact_for_markdown,
    capture_browser_extension_artifact_for_markdown,
    capture_chaseos_browser_page_for_markdown,
    capture_clipboard_text_for_markdown,
    capture_display_region_for_markdown,
    capture_discord_artifact_for_markdown,
    capture_live_discord_command_for_markdown,
    capture_current_screen_for_markdown,
    capture_selected_text_for_markdown,
    clear_ambient_clipboard_monitor_state,
    get_ambient_clipboard_monitor_state,
    poll_ambient_clipboard_for_markdown,
    save_capture_collector_settings,
    save_active_browser_capture_state,
)
from runtime.studio.capture_to_markdown_panel import (
    preview_capture_to_markdown,
    save_capture_to_markdown,
)
from runtime.agent_bus import bus


PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15"
    "c4890000000d49444154789c6360000002000100ffff03000006000557bfab"
    "d40000000049454e44ae426082"
)


def _fake_screen_capture() -> ScreenCaptureImage:
    return ScreenCaptureImage(
        png_bytes=PNG_BYTES,
        width=1,
        height=1,
        source="unit_fixture",
    )


def _fake_display_region_capture() -> DisplayRegionCapture:
    return DisplayRegionCapture(
        image=ScreenCaptureImage(
            png_bytes=PNG_BYTES,
            width=1,
            height=1,
            source="unit_display_region",
        ),
        x=10,
        y=20,
        width=1,
        height=1,
    )


def _fake_active_window_capture() -> ActiveWindowCapture:
    return ActiveWindowCapture(
        image=ScreenCaptureImage(
            png_bytes=PNG_BYTES,
            width=1,
            height=1,
            source="unit_active_window",
        ),
        x=30,
        y=40,
        width=1,
        height=1,
        window_title="Unit Active Window",
        process_id=1234,
    )


def _fake_clipboard_text() -> ClipboardText:
    return ClipboardText(
        content="Clipboard text captured for Markdown review.",
        source="unit_clipboard",
    )


def _fake_empty_clipboard_text() -> ClipboardText:
    return ClipboardText(content="   ", source="unit_clipboard")


def _fake_selected_text() -> SelectedText:
    return SelectedText(
        content="Selected text copied from another application for Markdown review.",
        source="unit_selected_text",
        window_title="Unit Editor",
        process_id=5678,
        clipboard_restored=True,
    )


def _fake_empty_selected_text() -> SelectedText:
    return SelectedText(
        content="   ",
        source="unit_selected_text",
        window_title="Unit Editor",
        process_id=5678,
        clipboard_restored=True,
    )


def _fake_browser_page_capture(source_url: str) -> BrowserPageCapture:
    return BrowserPageCapture(
        title="Unit ChaseOS Browser Page",
        source_url=source_url,
        visible_text="ChaseOS browser page text for Markdown review.",
        html=(
            "<html><head><title>Unit ChaseOS Browser Page</title></head>"
            "<body><p>ChaseOS browser page text for Markdown review.</p></body></html>"
        ),
        screenshot_png=PNG_BYTES,
        width=1,
        height=1,
        source="unit_chaseos_browser",
    )


def _fake_accessibility_tree() -> AccessibilityTreeCapture:
    return AccessibilityTreeCapture(
        text="- Window: Unit App\n- Button: Save\n- Edit: Markdown body",
        source="unit_accessibility_tree",
        window_title="Unit App",
        process_id=9012,
        node_count=3,
        roles=("Window", "Button", "Edit"),
    )


def _fake_empty_accessibility_tree() -> AccessibilityTreeCapture:
    return AccessibilityTreeCapture(text="", source="unit_accessibility_tree")


def test_capture_collector_settings_default_to_disabled_screen_capture(tmp_path: Path) -> None:
    model = build_capture_collector_settings_model(tmp_path)

    assert model["surface"] == "studio_capture_collectors"
    assert model["screen_capture_enabled"] is False
    assert model["display_region_capture_enabled"] is False
    assert model["active_window_capture_enabled"] is False
    assert model["clipboard_capture_enabled"] is False
    assert model["ambient_clipboard_monitoring_enabled"] is False
    assert model["ambient_clipboard_retention_limit"] == 5
    assert model["selected_text_capture_enabled"] is False
    assert model["accessibility_tree_capture_enabled"] is False
    assert model["browser_artifact_capture_enabled"] is False
    assert model["browser_extension_capture_enabled"] is False
    assert model["active_chaseos_browser_capture_enabled"] is False
    assert model["chaseos_browser_page_capture_enabled"] is False
    assert model["discord_artifact_capture_enabled"] is False
    assert model["summary"]["screen_capture_collector_built"] is True
    assert model["summary"]["screen_capture_status"] == "disabled_in_settings"
    assert model["summary"]["display_region_capture_collector_built"] is True
    assert model["summary"]["display_region_capture_status"] == "disabled_in_settings"
    assert model["summary"]["active_window_capture_collector_built"] is True
    assert model["summary"]["active_window_capture_status"] == "disabled_in_settings"
    assert model["summary"]["clipboard_capture_collector_built"] is True
    assert model["summary"]["clipboard_capture_status"] == "disabled_in_settings"
    assert model["summary"]["ambient_clipboard_monitor_built"] is True
    assert model["summary"]["ambient_clipboard_status"] == "disabled_in_settings"
    assert model["summary"]["selected_text_capture_collector_built"] is True
    assert model["summary"]["selected_text_capture_status"] == "disabled_in_settings"
    assert model["summary"]["accessibility_tree_capture_collector_built"] is True
    assert model["summary"]["accessibility_tree_capture_status"] == "disabled_in_settings"
    assert model["summary"]["browser_artifact_capture_collector_built"] is True
    assert model["summary"]["browser_artifact_capture_status"] == "disabled_in_settings"
    assert model["summary"]["browser_extension_capture_collector_built"] is True
    assert model["summary"]["browser_extension_capture_status"] == "disabled_in_settings"
    assert model["summary"]["active_chaseos_browser_capture_collector_built"] is True
    assert model["summary"]["active_chaseos_browser_capture_status"] == "disabled_in_settings"
    assert model["summary"]["chaseos_browser_page_capture_collector_built"] is True
    assert model["summary"]["chaseos_browser_page_capture_status"] == "disabled_in_settings"
    assert model["summary"]["discord_artifact_capture_collector_built"] is True
    assert model["summary"]["discord_artifact_capture_status"] == "disabled_in_settings"
    assert model["authority"]["captures_screen_pixels_on_settings_load"] is False
    assert model["authority"]["reads_clipboard_on_settings_load"] is False
    assert model["authority"]["reads_clipboard_on_capture_panel_load"] is False
    assert model["authority"]["reads_ambient_clipboard_on_settings_load"] is False
    assert model["authority"]["reads_ambient_clipboard_on_capture_panel_load"] is False
    assert model["authority"]["reads_active_browser_tab"] is False
    assert model["authority"]["reads_browser_profile"] is False
    assert model["authority"]["writes_raw_quarantine_markdown_on_click"] is False
    assert model["readiness"]["screen_capture_requires_operator_click"] is True
    assert model["readiness"]["display_region_capture_requires_operator_drag"] is True
    assert model["readiness"]["active_window_capture_requires_operator_click"] is True
    assert model["readiness"]["clipboard_capture_requires_operator_click"] is True
    assert model["readiness"]["ambient_clipboard_monitor_requires_privacy_opt_in"] is True
    assert model["readiness"]["ambient_clipboard_monitor_writes_no_markdown_on_poll"] is True
    assert model["readiness"]["selected_text_capture_requires_operator_click"] is True
    assert model["readiness"]["selected_text_capture_uses_temporary_clipboard_copy"] is True
    assert model["readiness"]["selected_text_capture_restores_text_clipboard_when_possible"] is True
    assert model["readiness"]["selected_text_capture_reads_on_settings_load"] is False
    assert model["readiness"]["selected_text_capture_reads_on_capture_panel_load"] is False
    assert model["readiness"]["accessibility_tree_capture_requires_operator_click"] is True
    assert model["readiness"]["accessibility_tree_capture_reads_on_settings_load"] is False
    assert model["readiness"]["accessibility_tree_capture_reads_on_capture_panel_load"] is False
    assert model["readiness"]["browser_artifact_capture_requires_operator_click"] is True
    assert model["readiness"]["browser_extension_capture_requires_operator_click"] is True
    assert model["readiness"]["browser_extension_package_built"] is True
    assert model["readiness"]["active_chaseos_browser_capture_requires_operator_click"] is True
    assert model["readiness"]["active_chaseos_browser_capture_reads_personal_browser"] is False
    assert model["readiness"]["chaseos_browser_page_capture_requires_operator_click"] is True
    assert model["readiness"]["chaseos_browser_page_capture_reads_personal_browser"] is False
    assert model["readiness"]["discord_artifact_capture_requires_operator_click"] is True


def test_screen_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_current_screen_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        image_provider=_fake_screen_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["screen_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Operator-Screenshots").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_display_region_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_display_region_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        region_provider=_fake_display_region_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["display_region_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Operator-Screenshots").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_display_region_capture_requires_explicit_operator_click_or_shortcut(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"display_region_capture_enabled": True})

    result = capture_display_region_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
        region_provider=_fake_display_region_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["operator_confirmation_required"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Operator-Screenshots").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_active_window_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_active_window_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        window_provider=_fake_active_window_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["active_window_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Operator-Screenshots").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_active_window_capture_requires_explicit_operator_click_or_shortcut(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"active_window_capture_enabled": True})

    result = capture_active_window_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
        window_provider=_fake_active_window_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["operator_confirmation_required"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Operator-Screenshots").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_active_window_capture_writes_evidence_for_image_text_markdown_flow(tmp_path: Path) -> None:
    settings = save_capture_collector_settings(tmp_path, {"active_window_capture_enabled": True})
    assert settings["active_window_capture_enabled"] is True

    captured = capture_active_window_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "run_id": "unit-window", "title": ""},
        window_provider=_fake_active_window_capture,
    )

    assert captured["ok"] is True
    assert captured["status"] == "active_window_capture_ready_for_markdown"
    assert captured["source_mode"] == "screenshot_text_extraction"
    assert captured["title"] == "Unit Active Window"
    assert captured["file_path"] == "07_LOGS/Operator-Screenshots/Capture-to-Markdown/unit-window-active-window.png"
    assert captured["window"]["title"] == "Unit Active Window"
    assert captured["window"]["process_id"] == 1234
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["authority"]["registers_global_hotkeys"] is False
    screenshot_path = tmp_path / captured["file_path"]
    assert screenshot_path.read_bytes() == PNG_BYTES
    audit_path = Path(captured["audit_path"])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["status"] == "active_window_capture_ready_for_markdown"
    assert audit["window"]["title"] == "Unit Active Window"
    assert audit["authority"]["reads_active_window_metadata"] is True
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_display_region_capture_writes_evidence_for_image_text_markdown_flow(tmp_path: Path) -> None:
    settings = save_capture_collector_settings(tmp_path, {"display_region_capture_enabled": True})
    assert settings["display_region_capture_enabled"] is True

    captured = capture_display_region_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "run_id": "unit-region", "title": "Unit Region"},
        region_provider=_fake_display_region_capture,
    )

    assert captured["ok"] is True
    assert captured["status"] == "display_region_capture_ready_for_markdown"
    assert captured["source_mode"] == "screenshot_text_extraction"
    assert captured["file_path"] == "07_LOGS/Operator-Screenshots/Capture-to-Markdown/unit-region-display-region.png"
    assert captured["region"] == {"x": 10, "y": 20, "width": 1, "height": 1}
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["authority"]["registers_global_hotkeys"] is False
    assert captured["authority"]["reads_active_browser_tab"] is False
    screenshot_path = tmp_path / captured["file_path"]
    assert screenshot_path.read_bytes() == PNG_BYTES
    audit_path = Path(captured["audit_path"])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["status"] == "display_region_capture_ready_for_markdown"
    assert audit["region"] == {"x": 10, "y": 20, "width": 1, "height": 1}
    assert audit["authority"]["operator_drag_select_confirmed"] is True
    assert not (tmp_path / "03_INPUTS").exists()


def test_screen_capture_requires_explicit_operator_click(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"screen_capture_enabled": True})

    result = capture_current_screen_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
        image_provider=_fake_screen_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["operator_confirmation_required"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Operator-Screenshots").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_screen_capture_writes_evidence_only_then_uses_existing_markdown_flow(tmp_path: Path) -> None:
    settings = save_capture_collector_settings(tmp_path, {"screen_capture_enabled": True})
    assert settings["screen_capture_enabled"] is True

    captured = capture_current_screen_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "run_id": "unit-screen", "title": "Unit Screen"},
        image_provider=_fake_screen_capture,
    )

    assert captured["ok"] is True
    assert captured["status"] == "screen_capture_ready_for_markdown"
    assert captured["source_mode"] == "screenshot_attachment"
    assert captured["file_path"] == "07_LOGS/Operator-Screenshots/Capture-to-Markdown/unit-screen-screen.png"
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["authority"]["registers_global_hotkeys"] is False
    assert captured["authority"]["reads_active_browser_tab"] is False
    screenshot_path = tmp_path / captured["file_path"]
    assert screenshot_path.read_bytes() == PNG_BYTES
    audit_path = Path(captured["audit_path"])
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["status"] == "screen_capture_ready_for_markdown"
    assert audit["authority"]["operator_click_confirmed"] is True
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "file_path": captured["file_path"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Screenshot attachment imported for operator review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def test_clipboard_text_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_clipboard_text_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        text_provider=_fake_clipboard_text,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["clipboard_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_clipboard_text_capture_requires_explicit_operator_click(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"clipboard_capture_enabled": True})

    result = capture_clipboard_text_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
        text_provider=_fake_clipboard_text,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["operator_confirmation_required"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_clipboard_text_capture_blocks_empty_text(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"clipboard_capture_enabled": True})

    result = capture_clipboard_text_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        text_provider=_fake_empty_clipboard_text,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["clipboard_text_empty"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_clipboard_text_capture_fills_raw_text_then_uses_existing_markdown_flow(tmp_path: Path) -> None:
    settings = save_capture_collector_settings(tmp_path, {"clipboard_capture_enabled": True})
    assert settings["clipboard_capture_enabled"] is True

    captured = capture_clipboard_text_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "title": "Unit Clipboard"},
        text_provider=_fake_clipboard_text,
    )

    assert captured["ok"] is True
    assert captured["status"] == "clipboard_text_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert captured["raw_text"] == "Clipboard text captured for Markdown review."
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_clipboard_on_settings_load"] is False
    assert captured["authority"]["reads_clipboard_on_capture_panel_load"] is False
    assert captured["authority"]["registers_global_hotkeys"] is False
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "raw_text": captured["raw_text"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Clipboard text captured for Markdown review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def test_ambient_clipboard_monitor_requires_privacy_opt_in_and_session(
    tmp_path: Path,
) -> None:
    disabled = poll_ambient_clipboard_for_markdown(
        tmp_path,
        {"monitoring_session_confirmed": True},
        text_provider=_fake_clipboard_text,
    )
    assert disabled["ok"] is False
    assert disabled["blockers"] == ["ambient_clipboard_monitoring_disabled_in_settings"]

    save_capture_collector_settings(
        tmp_path, {"ambient_clipboard_monitoring_enabled": True}
    )
    no_session = poll_ambient_clipboard_for_markdown(
        tmp_path,
        {"monitoring_session_confirmed": False},
        text_provider=_fake_clipboard_text,
    )
    assert no_session["ok"] is False
    assert no_session["blockers"] == ["ambient_clipboard_monitoring_session_required"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_ambient_clipboard_monitor_polls_state_then_uses_markdown_flow(
    tmp_path: Path,
) -> None:
    settings = save_capture_collector_settings(
        tmp_path,
        {
            "ambient_clipboard_monitoring_enabled": True,
            "ambient_clipboard_retention_limit": 2,
        },
    )
    assert settings["ambient_clipboard_monitoring_enabled"] is True
    assert settings["ambient_clipboard_retention_limit"] == 2

    captured = poll_ambient_clipboard_for_markdown(
        tmp_path,
        {"monitoring_session_confirmed": True, "title": "Unit Ambient Clipboard"},
        text_provider=_fake_clipboard_text,
    )

    assert captured["ok"] is True
    assert captured["status"] == "ambient_clipboard_text_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert captured["raw_text"] == "Clipboard text captured for Markdown review."
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["writes_state_ring_buffer"] is True
    assert captured["retention_limit"] == 2
    assert captured["authority"]["reads_clipboard_on_settings_load"] is False
    assert captured["authority"]["reads_clipboard_on_capture_panel_load"] is False
    assert not (tmp_path / "03_INPUTS").exists()

    state = get_ambient_clipboard_monitor_state(tmp_path)
    assert state["entry_count"] == 1
    assert state["entries"][0]["preview"] == "Clipboard text captured for Markdown review."

    duplicate = poll_ambient_clipboard_for_markdown(
        tmp_path,
        {"monitoring_session_confirmed": True},
        text_provider=_fake_clipboard_text,
    )
    assert duplicate["duplicate_of_latest"] is True
    assert duplicate["entry_count"] == 1

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "raw_text": captured["raw_text"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Clipboard text captured for Markdown review." in preview["markdown"]

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert Path(saved["content_path"]).exists()

    denied_clear = clear_ambient_clipboard_monitor_state(tmp_path, {})
    assert denied_clear["ok"] is False
    assert denied_clear["blockers"] == ["ambient_clipboard_clear_confirmation_required"]

    cleared = clear_ambient_clipboard_monitor_state(
        tmp_path, {"confirmation_phrase": "CLEAR AMBIENT CLIPBOARD"}
    )
    assert cleared["ok"] is True
    assert not (tmp_path / "runtime" / "studio" / "state" / "capture-ambient-clipboard.json").exists()


def test_selected_text_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_selected_text_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        text_provider=_fake_selected_text,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["selected_text_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_selected_text_capture_requires_explicit_operator_click_or_shortcut(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"selected_text_capture_enabled": True})

    result = capture_selected_text_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
        text_provider=_fake_selected_text,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["operator_confirmation_required"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_selected_text_capture_blocks_empty_text(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"selected_text_capture_enabled": True})

    result = capture_selected_text_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        text_provider=_fake_empty_selected_text,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["selected_text_empty"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_selected_text_capture_fills_raw_text_then_uses_existing_markdown_flow(
    tmp_path: Path,
) -> None:
    settings = save_capture_collector_settings(tmp_path, {"selected_text_capture_enabled": True})
    assert settings["selected_text_capture_enabled"] is True

    captured = capture_selected_text_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "title": "Unit Selected Text"},
        text_provider=_fake_selected_text,
    )

    assert captured["ok"] is True
    assert captured["status"] == "selected_text_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert captured["raw_text"] == "Selected text copied from another application for Markdown review."
    assert captured["window"]["title"] == "Unit Editor"
    assert captured["window"]["process_id"] == 5678
    assert captured["clipboard_restored"] is True
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_selected_text"] is True
    assert captured["authority"]["uses_temporary_clipboard_copy"] is True
    assert captured["authority"]["restores_text_clipboard_when_possible"] is True
    assert captured["authority"]["reads_clipboard_on_settings_load"] is False
    assert captured["authority"]["reads_clipboard_on_capture_panel_load"] is False
    assert captured["authority"]["registers_global_hotkeys"] is False
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "raw_text": captured["raw_text"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Selected text copied from another application for Markdown review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def test_accessibility_tree_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_accessibility_tree_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        tree_provider=_fake_accessibility_tree,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["accessibility_tree_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_accessibility_tree_capture_requires_explicit_operator_click_or_shortcut(
    tmp_path: Path,
) -> None:
    save_capture_collector_settings(tmp_path, {"accessibility_tree_capture_enabled": True})

    result = capture_accessibility_tree_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
        tree_provider=_fake_accessibility_tree,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["operator_confirmation_required"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_accessibility_tree_capture_blocks_empty_text(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"accessibility_tree_capture_enabled": True})

    result = capture_accessibility_tree_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        tree_provider=_fake_empty_accessibility_tree,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["accessibility_tree_empty"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_accessibility_tree_capture_fills_raw_text_then_uses_existing_markdown_flow(
    tmp_path: Path,
) -> None:
    settings = save_capture_collector_settings(
        tmp_path, {"accessibility_tree_capture_enabled": True}
    )
    assert settings["accessibility_tree_capture_enabled"] is True

    captured = capture_accessibility_tree_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "title": "Unit Accessibility Tree"},
        tree_provider=_fake_accessibility_tree,
    )

    assert captured["ok"] is True
    assert captured["status"] == "accessibility_tree_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert "Button: Save" in captured["raw_text"]
    assert captured["window"]["title"] == "Unit App"
    assert captured["window"]["process_id"] == 9012
    assert captured["node_count"] == 3
    assert captured["roles"] == ["Window", "Button", "Edit"]
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_accessibility_tree"] is True
    assert captured["authority"]["reads_accessibility_tree_on_settings_load"] is False
    assert captured["authority"]["reads_accessibility_tree_on_capture_panel_load"] is False
    assert captured["authority"]["registers_global_hotkeys"] is False
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "raw_text": captured["raw_text"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Button: Save" in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def _write_browser_artifact(root: Path) -> Path:
    artifact = root / "07_LOGS" / "Browser-Runs" / "local" / "default" / "active-browser.html"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        "<html><head><title>Controlled Browser Artifact</title></head>"
        "<body><p>Browser artifact text for Markdown review.</p></body></html>",
        encoding="utf-8",
    )
    return artifact


def _write_browser_extension_artifact(root: Path) -> Path:
    artifact = (
        root
        / "03_INPUTS"
        / "00_QUARANTINE"
        / "Browser-Extension-Captures"
        / "extension-capture.json"
    )
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        json.dumps(
            {
                "schema_version": "chaseos.capture.browser_extension.v1",
                "captured_at_utc": "2026-05-29T16:35:00Z",
                "capture_scope": "visible_page_text",
                "title": "Extension Captured Page",
                "source_url": "https://example.test/extension-capture",
                "visible_text": "Browser extension text captured for Markdown review.",
                "includes_cookies": False,
                "includes_browser_history": False,
                "includes_browser_storage": False,
            }
        ),
        encoding="utf-8",
    )
    return artifact


def test_browser_artifact_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    _write_browser_artifact(tmp_path)

    result = capture_browser_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "07_LOGS/Browser-Runs/local/default/active-browser.html",
            "source_url": "https://example.test/browser-artifact",
        },
    )

    assert result["ok"] is False
    assert result["blockers"] == ["browser_artifact_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_browser_artifact_capture_requires_click_file_and_declared_url(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"browser_artifact_capture_enabled": True})

    missing_click = capture_browser_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": False,
            "file_path": "07_LOGS/Browser-Runs/local/default/active-browser.html",
            "source_url": "https://example.test/browser-artifact",
        },
    )
    missing_file = capture_browser_artifact_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "source_url": "https://example.test/browser-artifact"},
    )
    missing_url = capture_browser_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "07_LOGS/Browser-Runs/local/default/active-browser.html",
        },
    )

    assert missing_click["blockers"] == ["operator_confirmation_required"]
    assert missing_file["blockers"] == ["browser_artifact_file_required"]
    assert missing_url["blockers"] == ["browser_artifact_declared_url_required"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_browser_artifact_capture_validates_artifact_then_uses_existing_markdown_flow(tmp_path: Path) -> None:
    _write_browser_artifact(tmp_path)
    settings = save_capture_collector_settings(
        tmp_path,
        {"browser_artifact_capture_enabled": True},
    )
    assert settings["browser_artifact_capture_enabled"] is True

    captured = capture_browser_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "07_LOGS/Browser-Runs/local/default/active-browser.html",
            "source_url": "https://example.test/browser-artifact",
        },
    )

    assert captured["ok"] is True
    assert captured["status"] == "browser_artifact_ready_for_markdown"
    assert captured["source_mode"] == "controlled_html_artifact"
    assert captured["file_path"] == "07_LOGS/Browser-Runs/local/default/active-browser.html"
    assert captured["source_url"] == "https://example.test/browser-artifact"
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_active_browser_tab"] is False
    assert captured["authority"]["reads_browser_profile"] is False
    assert captured["authority"]["reads_browser_history"] is False
    assert "Browser artifact text for Markdown review." in captured["extracted_text_preview"]
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "file_path": captured["file_path"],
        "source_url": captured["source_url"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Browser artifact text for Markdown review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def test_browser_extension_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    _write_browser_extension_artifact(tmp_path)

    result = capture_browser_extension_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "03_INPUTS/00_QUARANTINE/Browser-Extension-Captures/extension-capture.json",
        },
    )

    assert result["ok"] is False
    assert result["blockers"] == ["browser_extension_capture_disabled_in_settings"]
    assert result["write_performed"] is False


def test_browser_extension_capture_requires_click_and_file(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"browser_extension_capture_enabled": True})

    missing_click = capture_browser_extension_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": False,
            "file_path": "03_INPUTS/00_QUARANTINE/Browser-Extension-Captures/extension-capture.json",
        },
    )
    missing_file = capture_browser_extension_artifact_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
    )

    assert missing_click["blockers"] == ["operator_confirmation_required"]
    assert missing_file["blockers"] == ["browser_extension_artifact_required"]


def test_enabled_browser_extension_capture_imports_artifact_then_uses_markdown_flow(
    tmp_path: Path,
) -> None:
    _write_browser_extension_artifact(tmp_path)
    settings = save_capture_collector_settings(
        tmp_path, {"browser_extension_capture_enabled": True}
    )
    assert settings["browser_extension_capture_enabled"] is True

    captured = capture_browser_extension_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "03_INPUTS/00_QUARANTINE/Browser-Extension-Captures/extension-capture.json",
        },
    )

    assert captured["ok"] is True
    assert captured["status"] == "browser_extension_artifact_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert captured["source_url"] == "https://example.test/extension-capture"
    assert "Browser extension text captured for Markdown review." in captured["raw_text"]
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_browser_profile"] is False
    assert captured["authority"]["reads_browser_cookies"] is False
    assert captured["authority"]["reads_browser_history"] is False

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "raw_text": captured["raw_text"],
        "source_url": captured["source_url"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Browser extension text captured for Markdown review." in preview["markdown"]

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()


def test_active_chaseos_browser_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    _write_browser_artifact(tmp_path)
    save_active_browser_capture_state(
        tmp_path,
        {
            "file_path": "07_LOGS/Browser-Runs/local/default/active-browser.html",
            "source_url": "https://example.test/active-browser",
            "title": "Active Browser State",
        },
    )

    result = capture_active_chaseos_browser_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
    )

    assert result["ok"] is False
    assert result["blockers"] == ["active_chaseos_browser_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_active_chaseos_browser_capture_requires_click_and_state(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"active_chaseos_browser_capture_enabled": True})

    missing_click = capture_active_chaseos_browser_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
    )
    missing_state = capture_active_chaseos_browser_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
    )

    assert missing_click["blockers"] == ["operator_confirmation_required"]
    assert missing_state["blockers"] == ["active_chaseos_browser_capture_failed"]
    assert "No ChaseOS active browser artifact" in missing_state["message"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_active_chaseos_browser_capture_uses_state_then_existing_markdown_flow(tmp_path: Path) -> None:
    _write_browser_artifact(tmp_path)
    settings = save_capture_collector_settings(
        tmp_path,
        {"active_chaseos_browser_capture_enabled": True},
    )
    assert settings["active_chaseos_browser_capture_enabled"] is True
    state = save_active_browser_capture_state(
        tmp_path,
        {
            "file_path": "07_LOGS/Browser-Runs/local/default/active-browser.html",
            "source_url": "https://example.test/active-browser",
            "title": "Active Browser State",
        },
    )
    assert state["ok"] is True

    captured = capture_active_chaseos_browser_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
    )

    assert captured["ok"] is True
    assert captured["status"] == "active_chaseos_browser_ready_for_markdown"
    assert captured["source_mode"] == "controlled_html_artifact"
    assert captured["file_path"] == "07_LOGS/Browser-Runs/local/default/active-browser.html"
    assert captured["source_url"] == "https://example.test/active-browser"
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_chaseos_active_browser_state"] is True
    assert captured["authority"]["reads_personal_active_browser_tab"] is False
    assert captured["authority"]["reads_browser_profile"] is False
    assert captured["authority"]["reads_browser_history"] is False
    assert "Browser artifact text for Markdown review." in captured["extracted_text_preview"]
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "file_path": captured["file_path"],
        "source_url": captured["source_url"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Browser artifact text for Markdown review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def test_chaseos_browser_page_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    result = capture_chaseos_browser_page_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "source_url": "https://example.test/browser-page",
        },
        browser_provider=_fake_browser_page_capture,
    )

    assert result["ok"] is False
    assert result["blockers"] == ["chaseos_browser_page_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "07_LOGS" / "Browser-Runs").exists()
    assert not (tmp_path / "03_INPUTS").exists()


def test_chaseos_browser_page_capture_requires_click_and_declared_url(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"chaseos_browser_page_capture_enabled": True})

    missing_click = capture_chaseos_browser_page_for_markdown(
        tmp_path,
        {
            "operator_confirmed": False,
            "source_url": "https://example.test/browser-page",
        },
        browser_provider=_fake_browser_page_capture,
    )
    missing_url = capture_chaseos_browser_page_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
        browser_provider=_fake_browser_page_capture,
    )
    bad_url = capture_chaseos_browser_page_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "source_url": "file:///secret.html"},
        browser_provider=_fake_browser_page_capture,
    )

    assert missing_click["blockers"] == ["operator_confirmation_required"]
    assert missing_url["blockers"] == ["chaseos_browser_page_declared_url_required"]
    assert bad_url["blockers"] == ["chaseos_browser_page_declared_url_invalid"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_chaseos_browser_page_capture_writes_artifact_then_uses_existing_markdown_flow(tmp_path: Path) -> None:
    settings = save_capture_collector_settings(
        tmp_path,
        {"chaseos_browser_page_capture_enabled": True},
    )
    assert settings["chaseos_browser_page_capture_enabled"] is True

    captured = capture_chaseos_browser_page_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "title": "Unit Browser Page",
            "source_url": "https://example.test/browser-page",
            "run_id": "unit-browser-page",
        },
        browser_provider=_fake_browser_page_capture,
    )

    assert captured["ok"] is True
    assert captured["status"] == "chaseos_browser_page_ready_for_markdown"
    assert captured["source_mode"] == "controlled_html_artifact"
    assert captured["file_path"] == "07_LOGS/Browser-Runs/Capture-to-Markdown/unit-browser-page-browser-page.html"
    assert captured["source_url"] == "https://example.test/browser-page"
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is True
    assert captured["authority"]["reads_chaseos_owned_browser_page"] is True
    assert captured["authority"]["reads_personal_active_browser_tab"] is False
    assert captured["authority"]["reads_browser_cookies"] is False
    assert captured["authority"]["reads_browser_history"] is False
    assert captured["authority"]["provider_calls_allowed"] is False
    assert captured["authority"]["writes_chaseos_active_browser_state"] is True
    assert "ChaseOS browser page text for Markdown review." in captured["extracted_text_preview"]
    assert (tmp_path / captured["file_path"]).is_file()
    assert (tmp_path / captured["screenshot_path"]).read_bytes() == PNG_BYTES
    assert (tmp_path / captured["audit_path"]).is_file()
    assert (tmp_path / captured["active_browser_state_path"]).is_file()
    assert not (tmp_path / "03_INPUTS").exists()

    save_capture_collector_settings(tmp_path, {"active_chaseos_browser_capture_enabled": True})
    active_browser = capture_active_chaseos_browser_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
    )
    assert active_browser["ok"] is True
    assert active_browser["file_path"] == captured["file_path"]
    assert active_browser["source_url"] == captured["source_url"]
    assert active_browser["writes_raw_quarantine_markdown"] is False
    assert active_browser["authority"]["reads_chaseos_active_browser_state"] is True
    assert active_browser["authority"]["reads_personal_active_browser_tab"] is False

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "file_path": captured["file_path"],
        "source_url": captured["source_url"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "ChaseOS browser page text for Markdown review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def _write_discord_artifact(root: Path) -> Path:
    artifact = root / "07_LOGS" / "Discord-Captures" / "runtime-chat" / "thread.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        json.dumps(
            {
                "channel_name": "runtime-chat",
                "messages": [
                    {
                        "timestamp": "2026-05-28T10:00:00Z",
                        "author": {"username": "operator"},
                        "content": "Discord artifact text for Markdown review.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return artifact


def test_discord_artifact_capture_blocks_without_settings_enablement(tmp_path: Path) -> None:
    _write_discord_artifact(tmp_path)

    result = capture_discord_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "07_LOGS/Discord-Captures/runtime-chat/thread.json",
            "declared_source": "discord:runtime-chat",
        },
    )

    assert result["ok"] is False
    assert result["blockers"] == ["discord_artifact_capture_disabled_in_settings"]
    assert result["write_performed"] is False
    assert not (tmp_path / "03_INPUTS").exists()


def test_discord_artifact_capture_requires_click_file_and_declared_source(tmp_path: Path) -> None:
    save_capture_collector_settings(tmp_path, {"discord_artifact_capture_enabled": True})

    missing_click = capture_discord_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": False,
            "file_path": "07_LOGS/Discord-Captures/runtime-chat/thread.json",
            "declared_source": "discord:runtime-chat",
        },
    )
    missing_file = capture_discord_artifact_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "declared_source": "discord:runtime-chat"},
    )
    missing_source = capture_discord_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "file_path": "07_LOGS/Discord-Captures/runtime-chat/thread.json",
        },
    )

    assert missing_click["blockers"] == ["operator_confirmation_required"]
    assert missing_file["blockers"] == ["discord_artifact_file_required"]
    assert missing_source["blockers"] == ["discord_artifact_declared_source_required"]
    assert not (tmp_path / "03_INPUTS").exists()


def test_enabled_discord_artifact_capture_validates_artifact_then_uses_existing_markdown_flow(tmp_path: Path) -> None:
    _write_discord_artifact(tmp_path)
    settings = save_capture_collector_settings(
        tmp_path,
        {"discord_artifact_capture_enabled": True},
    )
    assert settings["discord_artifact_capture_enabled"] is True

    captured = capture_discord_artifact_for_markdown(
        tmp_path,
        {
            "operator_confirmed": True,
            "title": "Unit Discord",
            "file_path": "07_LOGS/Discord-Captures/runtime-chat/thread.json",
            "declared_source": "discord:runtime-chat",
        },
    )

    assert captured["ok"] is True
    assert captured["status"] == "discord_artifact_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert captured["file_path"] == "07_LOGS/Discord-Captures/runtime-chat/thread.json"
    assert captured["declared_source"] == "discord:runtime-chat"
    assert "Discord artifact text for Markdown review." in captured["raw_text"]
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["calls_discord_api"] is False
    assert captured["authority"]["reads_discord_token"] is False
    assert captured["authority"]["reads_discord_webhook"] is False
    assert captured["authority"]["listens_to_discord_events"] is False
    assert not (tmp_path / "03_INPUTS").exists()

    payload = {
        "source_mode": captured["source_mode"],
        "profile": "research_note",
        "title": captured["title"],
        "raw_text": captured["raw_text"],
        "source_url": captured["declared_source"],
    }
    preview = preview_capture_to_markdown(tmp_path, payload)
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Discord artifact text for Markdown review." in preview["markdown"]
    assert not (tmp_path / "03_INPUTS").exists()

    saved = save_capture_to_markdown(tmp_path, payload)
    assert saved["ok"] is True
    assert saved["write_performed"] is True
    assert saved["status"] == "raw_ingested"
    assert Path(saved["content_path"]).exists()
    assert Path(saved["visual_capture_packet_path"]).exists()


def test_live_discord_command_capture_imports_agent_bus_ingress_without_discord_api(tmp_path: Path) -> None:
    save_capture_collector_settings(
        tmp_path,
        {"live_discord_command_capture_enabled": True},
    )
    task = bus.create_task(
        tmp_path,
        sender="OpenClaw",
        recipient="Codex",
        intent="TASK",
        priority="normal",
        request="Convert this Discord command into Markdown.",
        expected_output="Markdown capture.",
        notes="Operator command from Discord.",
        ingress_context={
            "source_platform": "discord",
            "source_channel_id": "1493226873080119397",
            "source_thread_id": "1496197360382906398",
            "origin_message_id": "1497000000000000001",
            "conversation_key": "discord:1493226873080119397:1496197360382906398",
        },
        work_fingerprint="discord:Codex:1497000000000000001",
    )

    captured = capture_live_discord_command_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "task_id": task["task_id"], "title": "Discord Command"},
    )

    assert captured["ok"] is True
    assert captured["status"] == "live_discord_command_ready_for_markdown"
    assert captured["source_mode"] == "manual_text"
    assert captured["task_id"] == task["task_id"]
    assert captured["declared_source"] == "discord:1493226873080119397:1496197360382906398"
    assert "Convert this Discord command into Markdown." in captured["raw_text"]
    assert captured["writes_raw_quarantine_markdown"] is False
    assert captured["write_performed"] is False
    assert captured["authority"]["reads_chaseos_agent_bus_discord_ingress"] is True
    assert captured["authority"]["calls_discord_api"] is False
    assert captured["authority"]["reads_discord_token"] is False
    assert captured["authority"]["reads_discord_webhook"] is False
    assert captured["authority"]["direct_discord_event_listener"] is False
    assert not (tmp_path / "03_INPUTS").exists()

    preview = preview_capture_to_markdown(
        tmp_path,
        {
            "source_mode": captured["source_mode"],
            "profile": "research_note",
            "title": captured["title"],
            "raw_text": captured["raw_text"],
            "source_url": captured["declared_source"],
        },
    )
    assert preview["ok"] is True
    assert preview["write_performed"] is False
    assert "Convert this Discord command into Markdown." in preview["markdown"]


def test_live_discord_command_capture_requires_settings_click_and_matching_discord_task(tmp_path: Path) -> None:
    disabled = capture_live_discord_command_for_markdown(
        tmp_path,
        {"operator_confirmed": True},
    )
    assert disabled["blockers"] == ["live_discord_command_capture_disabled_in_settings"]

    save_capture_collector_settings(
        tmp_path,
        {"live_discord_command_capture_enabled": True},
    )
    missing_click = capture_live_discord_command_for_markdown(
        tmp_path,
        {"operator_confirmed": False},
    )
    missing_task = capture_live_discord_command_for_markdown(
        tmp_path,
        {"operator_confirmed": True, "task_id": "task-missing"},
    )

    assert missing_click["blockers"] == ["operator_confirmation_required"]
    assert missing_task["blockers"] == ["discord_agent_bus_task_not_found"]
    assert not (tmp_path / "03_INPUTS").exists()
