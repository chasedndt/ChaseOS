from __future__ import annotations

import json
import time

import pytest

from runtime.studio.capture_hotkey_settings import (
    CaptureHotkeySettingsError,
    build_capture_hotkey_settings_model,
    capture_hotkey_settings_path,
    normalize_hotkey_chord,
    save_capture_hotkey_settings,
)
from runtime.studio.capture_global_hotkeys import (
    CaptureGlobalHotkeyRuntime,
    build_capture_global_hotkey_registration_plan,
    parse_windows_hotkey_chord,
)


def test_capture_hotkey_settings_defaults_are_studio_window_only(tmp_path):
    model = build_capture_hotkey_settings_model(tmp_path)

    assert model["surface"] == "studio_capture_hotkey_settings"
    assert model["bindings"]["open_capture_markdown"] == "Ctrl+Shift+C"
    assert model["bindings"]["focus_capture_raw_text"] == "Ctrl+Shift+M"
    assert model["bindings"]["run_screen_capture_collector"] == ""
    assert model["bindings"]["run_display_region_collector"] == ""
    assert model["bindings"]["run_active_window_collector"] == ""
    assert model["bindings"]["run_clipboard_text_collector"] == ""
    assert model["bindings"]["run_ambient_clipboard_monitor"] == ""
    assert model["bindings"]["run_selected_text_collector"] == ""
    assert model["bindings"]["run_accessibility_tree_collector"] == ""
    assert model["bindings"]["run_browser_artifact_collector"] == ""
    assert model["bindings"]["run_browser_extension_collector"] == ""
    assert model["bindings"]["run_active_browser_collector"] == ""
    assert model["bindings"]["run_chaseos_browser_page_collector"] == ""
    assert model["bindings"]["run_discord_artifact_collector"] == ""
    assert model["global_hotkeys_enabled"] is False
    assert model["authority"]["writes_studio_preferences"] is True
    assert model["authority"]["registers_global_hotkeys"] is False
    assert model["authority"]["runs_explicit_collectors_from_studio_shortcuts"] is True
    assert model["authority"]["captures_screen_pixels_from_shortcut_without_settings"] is False
    assert model["authority"]["reads_clipboard_from_shortcut_without_settings"] is False
    assert model["authority"]["reads_controlled_browser_artifact_from_shortcut_without_settings"] is False
    assert (
        model["authority"]["reads_chaseos_active_browser_state_from_shortcut_without_settings"]
        is False
    )
    assert model["authority"]["launches_chaseos_owned_browser_page_from_shortcut_without_settings"] is False
    assert model["authority"]["reads_discord_artifact_from_shortcut_without_settings"] is False
    assert model["authority"]["calls_discord_from_shortcut"] is False
    assert model["authority"]["reads_ambient_clipboard"] is False
    assert model["authority"]["captures_screen_pixels"] is False
    assert model["authority"]["reads_personal_active_browser_tab"] is False
    assert model["readiness"]["studio_window_shortcuts_configurable"] is True
    assert model["readiness"]["studio_window_collector_shortcuts_configurable"] is True
    assert model["readiness"]["studio_window_display_region_collector_shortcut_available"] is True
    assert model["readiness"]["studio_window_active_window_collector_shortcut_available"] is True
    assert model["readiness"]["studio_window_ambient_clipboard_monitor_shortcut_available"] is True
    assert model["readiness"]["studio_window_selected_text_collector_shortcut_available"] is True
    assert model["readiness"]["studio_window_browser_artifact_collector_shortcut_available"] is True
    assert (
        model["readiness"]["studio_window_active_chaseos_browser_collector_shortcut_available"]
        is True
    )
    assert model["readiness"]["studio_window_chaseos_browser_page_collector_shortcut_available"] is True
    assert model["readiness"]["studio_window_discord_artifact_collector_shortcut_available"] is True
    assert model["readiness"]["global_hotkey_registration_available"] is True
    assert model["readiness"]["global_hotkey_registration_enabled"] is False
    assert model["readiness"]["global_hotkey_registered_binding_count"] == 0
    assert model["readiness"]["global_hotkey_registration_blocked"] is False
    assert model["readiness"]["personal_active_browser_capture_blocked"] is True
    actions = {action["id"]: action for action in model["actions"]}
    assert actions["run_screen_capture_collector"]["available_in_studio"] is True
    assert actions["run_screen_capture_collector"]["collector_action"] is True
    assert actions["run_screen_capture_collector"]["requires_capture_panel"] is True
    assert actions["run_screen_capture_collector"]["requires_collector_enabled"] is True
    assert actions["run_display_region_collector"]["available_in_studio"] is True
    assert actions["run_display_region_collector"]["collector_action"] is True
    assert actions["run_display_region_collector"]["requires_capture_panel"] is True
    assert actions["run_display_region_collector"]["requires_collector_enabled"] is True
    assert actions["run_display_region_collector"]["requires_operator_drag_select"] is True
    assert actions["run_active_window_collector"]["available_in_studio"] is True
    assert actions["run_active_window_collector"]["collector_action"] is True
    assert actions["run_active_window_collector"]["requires_capture_panel"] is True
    assert actions["run_active_window_collector"]["requires_collector_enabled"] is True
    assert actions["run_clipboard_text_collector"]["available_in_studio"] is True
    assert actions["run_clipboard_text_collector"]["collector_action"] is True
    assert actions["run_ambient_clipboard_monitor"]["available_in_studio"] is True
    assert actions["run_ambient_clipboard_monitor"]["collector_action"] is True
    assert actions["run_ambient_clipboard_monitor"]["requires_privacy_opt_in"] is True
    assert actions["run_ambient_clipboard_monitor"]["global_registration_allowed"] is False
    assert actions["run_selected_text_collector"]["available_in_studio"] is True
    assert actions["run_selected_text_collector"]["collector_action"] is True
    assert actions["run_selected_text_collector"]["requires_capture_panel"] is True
    assert actions["run_selected_text_collector"]["requires_collector_enabled"] is True
    assert actions["run_selected_text_collector"]["reads_selected_text_from_foreground_app"] is True
    assert actions["run_accessibility_tree_collector"]["available_in_studio"] is True
    assert actions["run_accessibility_tree_collector"]["collector_action"] is True
    assert actions["run_accessibility_tree_collector"]["requires_capture_panel"] is True
    assert actions["run_accessibility_tree_collector"]["requires_collector_enabled"] is True
    assert (
        actions["run_accessibility_tree_collector"][
            "reads_accessibility_tree_from_foreground_app"
        ]
        is True
    )
    assert actions["run_browser_artifact_collector"]["available_in_studio"] is True
    assert actions["run_browser_artifact_collector"]["collector_action"] is True
    assert actions["run_browser_artifact_collector"]["requires_capture_panel"] is True
    assert actions["run_browser_artifact_collector"]["requires_collector_enabled"] is True
    assert actions["run_browser_artifact_collector"]["requires_operator_selected_file"] is True
    assert actions["run_browser_artifact_collector"]["requires_declared_url"] is True
    assert actions["run_browser_extension_collector"]["available_in_studio"] is True
    assert actions["run_browser_extension_collector"]["collector_action"] is True
    assert actions["run_browser_extension_collector"]["requires_capture_panel"] is True
    assert actions["run_browser_extension_collector"]["requires_collector_enabled"] is True
    assert actions["run_browser_extension_collector"]["requires_operator_selected_file"] is True
    assert actions["run_active_browser_collector"]["available_in_studio"] is True
    assert actions["run_active_browser_collector"]["collector_action"] is True
    assert actions["run_active_browser_collector"]["requires_capture_panel"] is True
    assert actions["run_active_browser_collector"]["requires_collector_enabled"] is True
    assert actions["run_chaseos_browser_page_collector"]["available_in_studio"] is True
    assert actions["run_chaseos_browser_page_collector"]["collector_action"] is True
    assert actions["run_chaseos_browser_page_collector"]["requires_capture_panel"] is True
    assert actions["run_chaseos_browser_page_collector"]["requires_collector_enabled"] is True
    assert actions["run_chaseos_browser_page_collector"]["requires_declared_url"] is True
    assert actions["run_discord_artifact_collector"]["available_in_studio"] is True
    assert actions["run_discord_artifact_collector"]["collector_action"] is True
    assert actions["run_discord_artifact_collector"]["requires_capture_panel"] is True
    assert actions["run_discord_artifact_collector"]["requires_collector_enabled"] is True
    assert actions["run_discord_artifact_collector"]["requires_operator_selected_file"] is True
    assert actions["run_discord_artifact_collector"]["requires_declared_source"] is True
    assert actions["capture_screenshot"]["available_in_studio"] is False


def test_capture_hotkey_settings_save_normalizes_and_persists(tmp_path):
    model = save_capture_hotkey_settings(
        tmp_path,
        {
            "global_hotkeys_enabled": True,
            "bindings": {
                "open_capture_markdown": "ctrl+alt+m",
                "preview_capture_markdown": "Ctrl+Shift+P",
                "run_screen_capture_collector": "Ctrl+Alt+S",
                "run_display_region_collector": "Ctrl+Alt+R",
                "run_active_window_collector": "Ctrl+Alt+W",
                "run_clipboard_text_collector": "Ctrl+Alt+V",
                "run_ambient_clipboard_monitor": "Ctrl+Alt+L",
                "run_selected_text_collector": "Ctrl+Alt+T",
                "run_accessibility_tree_collector": "Ctrl+Alt+U",
                "run_browser_artifact_collector": "Ctrl+Alt+A",
                "run_browser_extension_collector": "Ctrl+Alt+E",
                "run_active_browser_collector": "Ctrl+Alt+Q",
                "run_chaseos_browser_page_collector": "Ctrl+Alt+B",
                "run_discord_artifact_collector": "Ctrl+Alt+D",
            }
        },
    )

    path = capture_hotkey_settings_path(tmp_path)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["global_hotkeys_enabled"] is True
    assert persisted["bindings"]["open_capture_markdown"] == "Ctrl+Alt+M"
    assert model["global_hotkeys_enabled"] is True
    assert model["authority"]["registers_global_hotkeys"] is True
    assert model["authority"]["runs_explicit_collectors_from_global_hotkeys"] is True
    assert model["readiness"]["global_hotkey_registration_enabled"] is True
    assert model["readiness"]["global_hotkey_registered_binding_count"] == 6
    assert model["bindings"]["open_capture_markdown"] == "Ctrl+Alt+M"
    assert model["bindings"]["preview_capture_markdown"] == "Ctrl+Shift+P"
    assert model["bindings"]["run_screen_capture_collector"] == "Ctrl+Alt+S"
    assert model["bindings"]["run_display_region_collector"] == "Ctrl+Alt+R"
    assert model["bindings"]["run_active_window_collector"] == "Ctrl+Alt+W"
    assert model["bindings"]["run_clipboard_text_collector"] == "Ctrl+Alt+V"
    assert model["bindings"]["run_ambient_clipboard_monitor"] == "Ctrl+Alt+L"
    assert model["bindings"]["run_selected_text_collector"] == "Ctrl+Alt+T"
    assert model["bindings"]["run_accessibility_tree_collector"] == "Ctrl+Alt+U"
    assert model["bindings"]["run_browser_artifact_collector"] == "Ctrl+Alt+A"
    assert model["bindings"]["run_browser_extension_collector"] == "Ctrl+Alt+E"
    assert model["bindings"]["run_active_browser_collector"] == "Ctrl+Alt+Q"
    assert model["bindings"]["run_chaseos_browser_page_collector"] == "Ctrl+Alt+B"
    assert model["bindings"]["run_discord_artifact_collector"] == "Ctrl+Alt+D"


def test_capture_global_hotkey_registration_plan_maps_collector_bindings(tmp_path):
    save_capture_hotkey_settings(
        tmp_path,
        {
            "global_hotkeys_enabled": True,
            "bindings": {
                "run_display_region_collector": "Ctrl+Alt+R",
                "run_active_window_collector": "Ctrl+Alt+W",
                "run_selected_text_collector": "Ctrl+Alt+T",
                "run_accessibility_tree_collector": "Ctrl+Alt+U",
            },
        },
    )

    plan = build_capture_global_hotkey_registration_plan(tmp_path)
    registrations = {item["action_id"]: item for item in plan["registrations"]}
    assert registrations["run_display_region_collector"]["handler_name"] == "captureDisplayRegionForMarkdown"
    assert registrations["run_active_window_collector"]["handler_name"] == "captureActiveWindowForMarkdown"
    assert registrations["run_selected_text_collector"]["handler_name"] == "captureSelectedTextForMarkdown"
    assert registrations["run_accessibility_tree_collector"]["handler_name"] == "captureAccessibilityTreeForMarkdown"
    assert registrations["run_display_region_collector"]["virtual_key"] == ord("R")
    assert registrations["run_active_window_collector"]["virtual_key"] == ord("W")
    assert registrations["run_selected_text_collector"]["virtual_key"] == ord("T")
    assert registrations["run_accessibility_tree_collector"]["virtual_key"] == ord("U")


def test_parse_windows_hotkey_chord_supports_named_keys():
    modifiers, virtual_key = parse_windows_hotkey_chord("Ctrl+Alt+F8")

    assert modifiers
    assert virtual_key == 0x77


def test_capture_global_hotkey_runtime_dispatches_to_capture_page_handler(tmp_path):
    save_capture_hotkey_settings(
        tmp_path,
        {
            "global_hotkeys_enabled": True,
            "bindings": {"run_display_region_collector": "Ctrl+Alt+R"},
        },
    )

    class FakeBackend:
        def __init__(self):
            self.registrations = []
            self.stop_called = False

        def run(self, registrations, callback, stop_event, ready_event):
            self.registrations = registrations
            ready_event.set()
            callback("run_display_region_collector")
            while not stop_event.is_set():
                time.sleep(0.01)

        def stop(self):
            self.stop_called = True

    class FakeWindow:
        def __init__(self):
            self.scripts = []

        def evaluate_js(self, script):
            self.scripts.append(script)

    backend = FakeBackend()
    window = FakeWindow()
    runtime = CaptureGlobalHotkeyRuntime(tmp_path, backend=backend)

    status = runtime.start(window)
    try:
        assert status["active"] is True
        assert status["registered_count"] == 1
        assert backend.registrations[0].action_id == "run_display_region_collector"
        assert window.scripts
        assert "captureDisplayRegionForMarkdown" in window.scripts[0]
        assert "#/capture-markdown" in window.scripts[0]
    finally:
        runtime.stop()
    assert backend.stop_called is True


def test_capture_hotkey_settings_rejects_unknown_actions(tmp_path):
    with pytest.raises(CaptureHotkeySettingsError):
        save_capture_hotkey_settings(
            tmp_path,
            {"bindings": {"not_a_capture_action": "Ctrl+Shift+X"}},
        )


def test_capture_hotkey_settings_rejects_blocked_global_capture_actions(tmp_path):
    with pytest.raises(CaptureHotkeySettingsError):
        save_capture_hotkey_settings(
            tmp_path,
            {"bindings": {"capture_screenshot": "Ctrl+Shift+S"}},
        )

    with pytest.raises(CaptureHotkeySettingsError):
        save_capture_hotkey_settings(
            tmp_path,
            {"bindings": {"capture_clipboard_text": "Ctrl+Shift+V"}},
        )


def test_capture_hotkey_settings_rejects_duplicate_studio_shortcuts(tmp_path):
    with pytest.raises(CaptureHotkeySettingsError):
        save_capture_hotkey_settings(
            tmp_path,
            {"bindings": {"preview_capture_markdown": "Ctrl+Shift+C"}},
        )


def test_capture_hotkey_settings_requires_modifier():
    with pytest.raises(CaptureHotkeySettingsError):
        normalize_hotkey_chord("M")

    assert normalize_hotkey_chord("Unassigned") == ""
