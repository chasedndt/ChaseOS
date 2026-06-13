"""Capture to Markdown shortcut settings.

This module stores Studio-window shortcuts plus the opt-in setting that lets the
desktop shell register selected Capture collector shortcuts with Windows.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.capture_hotkey_settings.v1"
SURFACE_ID = "studio_capture_hotkey_settings"

ACTION_OPEN_CAPTURE = "open_capture_markdown"
ACTION_FOCUS_RAW_TEXT = "focus_capture_raw_text"
ACTION_PREVIEW_CAPTURE = "preview_capture_markdown"
ACTION_SAVE_CAPTURE = "save_capture_markdown"
ACTION_RUN_SCREEN_COLLECTOR = "run_screen_capture_collector"
ACTION_RUN_DISPLAY_REGION_COLLECTOR = "run_display_region_collector"
ACTION_RUN_ACTIVE_WINDOW_COLLECTOR = "run_active_window_collector"
ACTION_RUN_CLIPBOARD_TEXT_COLLECTOR = "run_clipboard_text_collector"
ACTION_RUN_AMBIENT_CLIPBOARD_MONITOR = "run_ambient_clipboard_monitor"
ACTION_RUN_SELECTED_TEXT_COLLECTOR = "run_selected_text_collector"
ACTION_RUN_ACCESSIBILITY_TREE_COLLECTOR = "run_accessibility_tree_collector"
ACTION_RUN_BROWSER_ARTIFACT_COLLECTOR = "run_browser_artifact_collector"
ACTION_RUN_BROWSER_EXTENSION_COLLECTOR = "run_browser_extension_collector"
ACTION_RUN_ACTIVE_CHASEOS_BROWSER_COLLECTOR = "run_active_browser_collector"
ACTION_RUN_CHASEOS_BROWSER_PAGE_COLLECTOR = "run_chaseos_browser_page_collector"
ACTION_RUN_DISCORD_ARTIFACT_COLLECTOR = "run_discord_artifact_collector"
ACTION_CAPTURE_SELECTED_TEXT = "capture_selected_text"
ACTION_CAPTURE_SCREENSHOT = "capture_screenshot"
ACTION_CAPTURE_CLIPBOARD_TEXT = "capture_clipboard_text"

ACTION_IDS = (
    ACTION_OPEN_CAPTURE,
    ACTION_FOCUS_RAW_TEXT,
    ACTION_PREVIEW_CAPTURE,
    ACTION_SAVE_CAPTURE,
    ACTION_RUN_SCREEN_COLLECTOR,
    ACTION_RUN_DISPLAY_REGION_COLLECTOR,
    ACTION_RUN_ACTIVE_WINDOW_COLLECTOR,
    ACTION_RUN_CLIPBOARD_TEXT_COLLECTOR,
    ACTION_RUN_AMBIENT_CLIPBOARD_MONITOR,
    ACTION_RUN_SELECTED_TEXT_COLLECTOR,
    ACTION_RUN_ACCESSIBILITY_TREE_COLLECTOR,
    ACTION_RUN_BROWSER_ARTIFACT_COLLECTOR,
    ACTION_RUN_BROWSER_EXTENSION_COLLECTOR,
    ACTION_RUN_ACTIVE_CHASEOS_BROWSER_COLLECTOR,
    ACTION_RUN_CHASEOS_BROWSER_PAGE_COLLECTOR,
    ACTION_RUN_DISCORD_ARTIFACT_COLLECTOR,
    ACTION_CAPTURE_SELECTED_TEXT,
    ACTION_CAPTURE_SCREENSHOT,
    ACTION_CAPTURE_CLIPBOARD_TEXT,
)

_ACTION_DEFINITIONS = {
    ACTION_OPEN_CAPTURE: {
        "label": "Open Capture",
        "default_chord": "Ctrl+Shift+C",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "description": "Switches the current Studio window to Capture.",
    },
    ACTION_FOCUS_RAW_TEXT: {
        "label": "Focus raw text",
        "default_chord": "Ctrl+Shift+M",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "description": "Switches to Capture and focuses the raw text field.",
    },
    ACTION_PREVIEW_CAPTURE: {
        "label": "Preview capture",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "description": "Runs the write-free Markdown preview when Capture is open.",
    },
    ACTION_SAVE_CAPTURE: {
        "label": "Save capture",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": True,
        "description": "Saves through the raw quarantine writer when Capture is open.",
    },
    ACTION_RUN_SCREEN_COLLECTOR: {
        "label": "Run screen collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": True,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "description": (
            "Runs the explicit screen collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings."
        ),
    },
    ACTION_RUN_DISPLAY_REGION_COLLECTOR: {
        "label": "Run display region collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": True,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "requires_operator_drag_select": True,
        "description": (
            "Runs the explicit display region collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings, then you drag a rectangle over the display."
        ),
    },
    ACTION_RUN_ACTIVE_WINDOW_COLLECTOR: {
        "label": "Run active window collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": True,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "description": (
            "Runs the explicit active window collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings."
        ),
    },
    ACTION_RUN_CLIPBOARD_TEXT_COLLECTOR: {
        "label": "Run clipboard text collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "description": (
            "Runs the explicit clipboard text collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings."
        ),
    },
    ACTION_RUN_AMBIENT_CLIPBOARD_MONITOR: {
        "label": "Run ambient clipboard monitor",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "requires_privacy_opt_in": True,
        "registers_global_hotkey": False,
        "description": (
            "Starts or polls the privacy-gated ambient clipboard monitor from the Studio window "
            "when Capture is open. The monitor must still be enabled in Settings."
        ),
    },
    ACTION_RUN_SELECTED_TEXT_COLLECTOR: {
        "label": "Run selected text collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "reads_selected_text_from_foreground_app": True,
        "description": (
            "Runs the explicit selected-text collector from the Studio window or a configured global hotkey. "
            "The collector must still be enabled in Settings."
        ),
    },
    ACTION_RUN_ACCESSIBILITY_TREE_COLLECTOR: {
        "label": "Run accessibility tree collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "reads_accessibility_tree_from_foreground_app": True,
        "description": (
            "Runs the explicit accessibility tree collector from the Studio window or a configured global hotkey. "
            "The collector must still be enabled in Settings."
        ),
    },
    ACTION_RUN_BROWSER_ARTIFACT_COLLECTOR: {
        "label": "Run browser artifact collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "requires_operator_selected_file": True,
        "requires_declared_url": True,
        "description": (
            "Runs the explicit browser artifact collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings and the Capture form must include an operator-selected artifact plus a declared address."
        ),
    },
    ACTION_RUN_BROWSER_EXTENSION_COLLECTOR: {
        "label": "Run browser extension collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "requires_operator_selected_file": True,
        "description": (
            "Runs the ChaseOS browser extension artifact collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings and the Capture form must include an operator-selected extension artifact."
        ),
    },
    ACTION_RUN_ACTIVE_CHASEOS_BROWSER_COLLECTOR: {
        "label": "Run active ChaseOS browser collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "description": (
            "Runs the active ChaseOS browser collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings and uses only ChaseOS-owned active browser state or controlled artifacts."
        ),
    },
    ACTION_RUN_CHASEOS_BROWSER_PAGE_COLLECTOR: {
        "label": "Run ChaseOS browser page collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": True,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "requires_declared_url": True,
        "description": (
            "Runs the explicit ChaseOS-owned browser page collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings and the Capture form must include a declared address."
        ),
    },
    ACTION_RUN_DISCORD_ARTIFACT_COLLECTOR: {
        "label": "Run Discord artifact collector",
        "default_chord": "",
        "scope": "studio_window",
        "available_in_studio": True,
        "write_action": False,
        "collector_action": True,
        "requires_capture_panel": True,
        "requires_collector_enabled": True,
        "requires_operator_selected_file": True,
        "requires_declared_source": True,
        "description": (
            "Runs the explicit Discord artifact collector from the Studio window when Capture is open. "
            "The collector must still be enabled in Settings and the Capture form must include an operator-selected ChaseOS Discord artifact plus a declared Discord source."
        ),
    },
    ACTION_CAPTURE_SELECTED_TEXT: {
        "label": "Capture selected text",
        "default_chord": "",
        "scope": "global_capture",
        "available_in_studio": False,
        "write_action": False,
        "description": "Requires a separate selected-text permission adapter.",
    },
    ACTION_CAPTURE_SCREENSHOT: {
        "label": "Global screen capture",
        "default_chord": "",
        "scope": "global_capture",
        "available_in_studio": False,
        "write_action": False,
        "description": "Requires a separate operating-system global shortcut permission adapter.",
    },
    ACTION_CAPTURE_CLIPBOARD_TEXT: {
        "label": "Global clipboard text capture",
        "default_chord": "",
        "scope": "global_capture",
        "available_in_studio": False,
        "write_action": False,
        "description": "Ambient clipboard capture is blocked; explicit paste remains available.",
    },
}

_MODIFIER_LABELS = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
    "option": "Alt",
    "meta": "Meta",
    "cmd": "Meta",
    "command": "Meta",
}
_MODIFIER_ORDER = ("Ctrl", "Shift", "Alt", "Meta")


class CaptureHotkeySettingsError(ValueError):
    """Raised when a Capture shortcut setting is invalid."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def capture_hotkey_settings_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve() / "runtime" / "studio" / "state" / "capture-hotkeys.json"


def default_capture_hotkey_settings() -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "updated_at_utc": None,
        "global_hotkeys_enabled": False,
        "bindings": {
            action_id: str(definition.get("default_chord") or "")
            for action_id, definition in _ACTION_DEFINITIONS.items()
        },
    }


def normalize_hotkey_chord(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "unassigned", "disabled"}:
        return ""
    parts = [part.strip() for part in text.replace(" ", "").split("+") if part.strip()]
    if len(parts) < 2:
        raise CaptureHotkeySettingsError("shortcut must include at least one modifier and one key")

    modifiers: set[str] = set()
    key = ""
    for part in parts:
        lowered = part.lower()
        if lowered in _MODIFIER_LABELS:
            modifiers.add(_MODIFIER_LABELS[lowered])
        else:
            if key:
                raise CaptureHotkeySettingsError("shortcut can include only one non-modifier key")
            key = _normalize_hotkey_key(part)

    if not modifiers or not key:
        raise CaptureHotkeySettingsError("shortcut must include at least one modifier and one key")
    ordered_modifiers = [label for label in _MODIFIER_ORDER if label in modifiers]
    return "+".join(ordered_modifiers + [key])


def _normalize_hotkey_key(value: str) -> str:
    text = str(value or "").strip()
    if len(text) == 1 and text.isalnum():
        return text.upper()
    lowered = text.lower()
    if lowered.startswith("f") and lowered[1:].isdigit():
        number = int(lowered[1:])
        if 1 <= number <= 24:
            return f"F{number}"
    named = {
        "space": "Space",
        "enter": "Enter",
        "return": "Enter",
        "escape": "Escape",
        "esc": "Escape",
        "tab": "Tab",
    }
    if lowered in named:
        return named[lowered]
    raise CaptureHotkeySettingsError(f"unsupported shortcut key: {value}")


def _read_persisted_settings(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_capture_hotkey_settings(vault_root: str | Path) -> dict[str, Any]:
    path = capture_hotkey_settings_path(vault_root)
    settings = default_capture_hotkey_settings()
    persisted = _read_persisted_settings(path)
    settings["global_hotkeys_enabled"] = bool(persisted.get("global_hotkeys_enabled"))
    bindings = persisted.get("bindings") if isinstance(persisted.get("bindings"), dict) else {}
    for action_id in ACTION_IDS:
        if action_id not in bindings:
            continue
        settings["bindings"][action_id] = normalize_hotkey_chord(bindings.get(action_id))
    settings["updated_at_utc"] = persisted.get("updated_at_utc")
    return settings


def _write_capture_hotkey_settings(vault_root: str | Path, settings: dict[str, Any]) -> None:
    path = capture_hotkey_settings_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")


def save_capture_hotkey_settings(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = payload or {}
    requested_bindings = request.get("bindings") if isinstance(request.get("bindings"), dict) else {}
    settings = load_capture_hotkey_settings(vault_root)
    if "global_hotkeys_enabled" in request:
        settings["global_hotkeys_enabled"] = bool(request.get("global_hotkeys_enabled"))
    for action_id, value in requested_bindings.items():
        if action_id not in ACTION_IDS:
            raise CaptureHotkeySettingsError(f"unsupported Capture shortcut action: {action_id}")
        chord = normalize_hotkey_chord(value)
        if chord and not _ACTION_DEFINITIONS[action_id].get("available_in_studio"):
            raise CaptureHotkeySettingsError(
                "blocked Capture shortcut actions cannot be assigned until their permission adapter exists"
            )
        settings["bindings"][action_id] = chord
    _validate_capture_hotkey_settings(settings)
    settings["schema_version"] = MODEL_VERSION
    settings["updated_at_utc"] = _now_utc()
    _write_capture_hotkey_settings(vault_root, settings)
    return build_capture_hotkey_settings_model(vault_root)


def _validate_capture_hotkey_settings(settings: dict[str, Any]) -> None:
    bindings = settings.get("bindings") if isinstance(settings.get("bindings"), dict) else {}
    active_chords: dict[str, str] = {}
    for action_id in ACTION_IDS:
        chord = normalize_hotkey_chord(bindings.get(action_id))
        if not chord:
            continue
        if not _ACTION_DEFINITIONS[action_id].get("available_in_studio"):
            raise CaptureHotkeySettingsError(
                "blocked Capture shortcut actions cannot be assigned until their permission adapter exists"
            )
        if chord in active_chords:
            raise CaptureHotkeySettingsError(
                f"shortcut {chord} is already assigned to {active_chords[chord]}"
            )
        active_chords[chord] = action_id


def build_capture_hotkey_settings_model(vault_root: str | Path) -> dict[str, Any]:
    settings = load_capture_hotkey_settings(vault_root)
    bindings = settings.get("bindings") if isinstance(settings.get("bindings"), dict) else {}
    global_hotkeys_enabled = bool(settings.get("global_hotkeys_enabled"))
    global_action_ids = {
        ACTION_RUN_SCREEN_COLLECTOR,
        ACTION_RUN_DISPLAY_REGION_COLLECTOR,
        ACTION_RUN_ACTIVE_WINDOW_COLLECTOR,
        ACTION_RUN_CLIPBOARD_TEXT_COLLECTOR,
        ACTION_RUN_SELECTED_TEXT_COLLECTOR,
        ACTION_RUN_ACCESSIBILITY_TREE_COLLECTOR,
    }
    global_binding_count = sum(
        1 for action_id in global_action_ids if str(bindings.get(action_id) or "").strip()
    )
    actions = []
    for action_id in ACTION_IDS:
        definition = dict(_ACTION_DEFINITIONS[action_id])
        chord = normalize_hotkey_chord(bindings.get(action_id))
        global_scope = definition.get("scope") == "global_capture"
        actions.append(
            {
                "id": action_id,
                "label": definition.get("label"),
                "description": definition.get("description"),
                "scope": definition.get("scope"),
                "chord": chord,
                "default_chord": definition.get("default_chord") or "",
                "available_in_studio": bool(definition.get("available_in_studio")),
                "registered_globally": (
                    global_hotkeys_enabled
                    and action_id in global_action_ids
                    and bool(chord)
                ),
                "global_registration_allowed": action_id in global_action_ids,
                "write_action": bool(definition.get("write_action")),
                "collector_action": bool(definition.get("collector_action")),
                "requires_capture_panel": bool(definition.get("requires_capture_panel")),
                "requires_collector_enabled": bool(definition.get("requires_collector_enabled")),
                "requires_operator_selected_file": bool(definition.get("requires_operator_selected_file")),
                "requires_declared_url": bool(definition.get("requires_declared_url")),
                "requires_declared_source": bool(definition.get("requires_declared_source")),
                "requires_operator_drag_select": bool(definition.get("requires_operator_drag_select")),
                "requires_privacy_opt_in": bool(definition.get("requires_privacy_opt_in")),
                "reads_selected_text_from_foreground_app": bool(
                    definition.get("reads_selected_text_from_foreground_app")
                ),
                "reads_accessibility_tree_from_foreground_app": bool(
                    definition.get("reads_accessibility_tree_from_foreground_app")
                ),
                "blocked_reason": (
                    "Global operating-system capture is blocked by the Capture authority policy."
                    if global_scope
                    else ""
                ),
            }
        )
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "settings_path": str(capture_hotkey_settings_path(vault_root)),
        "updated_at_utc": settings.get("updated_at_utc"),
        "global_hotkeys_enabled": global_hotkeys_enabled,
        "bindings": {action["id"]: action["chord"] for action in actions},
        "actions": actions,
        "authority": {
            "writes_studio_preferences": True,
            "registers_global_hotkeys": global_hotkeys_enabled and global_binding_count > 0,
            "reads_selected_text": False,
            "reads_accessibility_tree": False,
            "reads_ambient_clipboard": False,
            "runs_explicit_collectors_from_studio_shortcuts": True,
            "runs_explicit_collectors_from_global_hotkeys": global_hotkeys_enabled,
            "captures_screen_pixels_from_shortcut_without_settings": False,
            "reads_clipboard_from_shortcut_without_settings": False,
            "reads_controlled_browser_artifact_from_shortcut_without_settings": False,
            "reads_chaseos_active_browser_state_from_shortcut_without_settings": False,
            "launches_chaseos_owned_browser_page_from_shortcut_without_settings": False,
            "reads_discord_artifact_from_shortcut_without_settings": False,
            "reads_accessibility_tree_from_shortcut_without_settings": False,
            "calls_discord_from_shortcut": False,
            "captures_screen_pixels": False,
            "reads_active_browser_tab": False,
            "reads_personal_active_browser_tab": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "settings_page_visible": True,
            "studio_window_shortcuts_configurable": True,
            "studio_window_collector_shortcuts_configurable": True,
            "studio_window_screen_collector_shortcut_available": True,
            "studio_window_display_region_collector_shortcut_available": True,
            "studio_window_active_window_collector_shortcut_available": True,
            "studio_window_clipboard_collector_shortcut_available": True,
            "studio_window_ambient_clipboard_monitor_shortcut_available": True,
            "studio_window_selected_text_collector_shortcut_available": True,
            "studio_window_accessibility_tree_collector_shortcut_available": True,
            "studio_window_browser_artifact_collector_shortcut_available": True,
            "studio_window_browser_extension_collector_shortcut_available": True,
            "studio_window_active_chaseos_browser_collector_shortcut_available": True,
            "studio_window_chaseos_browser_page_collector_shortcut_available": True,
            "studio_window_discord_artifact_collector_shortcut_available": True,
            "studio_window_shortcuts_available": True,
            "global_hotkey_registration_available": True,
            "global_hotkey_registration_enabled": global_hotkeys_enabled,
            "global_hotkey_registered_binding_count": global_binding_count,
            "global_hotkey_registration_blocked": False,
            "personal_active_browser_capture_blocked": True,
            "selected_text_capture_blocked": False,
            "accessibility_tree_capture_blocked": False,
            "screen_capture_blocked": True,
            "ambient_clipboard_capture_blocked": False,
        },
    }
