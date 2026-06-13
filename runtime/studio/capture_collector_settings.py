"""Studio Capture to Markdown collector settings and explicit collectors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import time
from typing import Any, Callable
from urllib.parse import urlparse
import zlib

from runtime.capture.visual_capture.attachments import build_screenshot_attachment


MODEL_VERSION = "studio.capture_collectors.v1"
SURFACE_ID = "studio_capture_collectors"
SCREEN_CAPTURE_POLICY_ID = "capture_to_markdown.explicit_studio_screen_capture.v1"
DISPLAY_REGION_CAPTURE_POLICY_ID = "capture_to_markdown.explicit_display_region_capture.v1"
ACTIVE_WINDOW_CAPTURE_POLICY_ID = "capture_to_markdown.explicit_active_window_capture.v1"
CLIPBOARD_TEXT_POLICY_ID = "capture_to_markdown.explicit_studio_clipboard_text_capture.v1"
AMBIENT_CLIPBOARD_POLICY_ID = "capture_to_markdown.ambient_clipboard_monitor.v1"
SELECTED_TEXT_POLICY_ID = "capture_to_markdown.explicit_selected_text_capture.v1"
ACCESSIBILITY_TREE_POLICY_ID = "capture_to_markdown.explicit_accessibility_tree_capture.v1"
BROWSER_ARTIFACT_POLICY_ID = "capture_to_markdown.explicit_browser_artifact_capture.v1"
BROWSER_EXTENSION_CAPTURE_POLICY_ID = "capture_to_markdown.browser_extension_capture.v1"
ACTIVE_CHASEOS_BROWSER_POLICY_ID = "capture_to_markdown.active_chaseos_browser_capture.v1"
CHASEOS_BROWSER_PAGE_POLICY_ID = "capture_to_markdown.explicit_chaseos_browser_page_capture.v1"
DISCORD_ARTIFACT_POLICY_ID = "capture_to_markdown.explicit_discord_artifact_capture.v1"
LIVE_DISCORD_COMMAND_POLICY_ID = "capture_to_markdown.live_discord_command_capture.v1"

DISCORD_ARTIFACT_DIRS = (
    "07_LOGS/Discord-Captures",
    "runtime/discord/artifacts",
    "runtime/studio/discord_artifacts",
)

BROWSER_EXTENSION_ARTIFACT_DIRS = (
    "03_INPUTS/00_QUARANTINE/Browser-Extension-Captures",
    "07_LOGS/Browser-Extension-Captures",
    "07_LOGS/Browser-Runs/Extension-Captures",
)

_DISCORD_FORBIDDEN_PATH_MARKERS = (
    ".env",
    "token",
    "webhook",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "discord_instance_bindings",
)

_BROWSER_EXTENSION_FORBIDDEN_PATH_MARKERS = (
    ".env",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "history",
    "password",
    "profile",
    "secret",
    "secrets",
    "session",
    "sessions",
    "storage",
    "token",
)

_MAX_DISCORD_ARTIFACT_CHARS = 500_000
_MAX_BROWSER_EXTENSION_ARTIFACT_CHARS = 500_000
_DEFAULT_AMBIENT_CLIPBOARD_RETENTION_LIMIT = 5
_MAX_AMBIENT_CLIPBOARD_RETENTION_LIMIT = 25


class CaptureCollectorError(ValueError):
    """Raised when a Capture collector cannot run."""


@dataclass(frozen=True)
class ScreenCaptureImage:
    png_bytes: bytes
    width: int
    height: int
    source: str = "primary_screen"


ScreenCaptureProvider = Callable[[], ScreenCaptureImage]


@dataclass(frozen=True)
class DisplayRegionCapture:
    image: ScreenCaptureImage
    x: int
    y: int
    width: int
    height: int


DisplayRegionProvider = Callable[[], DisplayRegionCapture]


@dataclass(frozen=True)
class ActiveWindowCapture:
    image: ScreenCaptureImage
    x: int
    y: int
    width: int
    height: int
    window_title: str = ""
    process_id: int = 0


ActiveWindowProvider = Callable[[], ActiveWindowCapture]


@dataclass(frozen=True)
class ClipboardText:
    content: str
    source: str = "system_clipboard"


ClipboardTextProvider = Callable[[], ClipboardText]


@dataclass(frozen=True)
class SelectedText:
    content: str
    source: str = "windows_selected_text"
    window_title: str = ""
    process_id: int = 0
    clipboard_restored: bool = False


SelectedTextProvider = Callable[[], SelectedText]


@dataclass(frozen=True)
class AccessibilityTreeCapture:
    text: str
    source: str = "windows_accessibility_tree"
    window_title: str = ""
    process_id: int = 0
    node_count: int = 0
    roles: tuple[str, ...] = ()


AccessibilityTreeProvider = Callable[[], AccessibilityTreeCapture]


@dataclass(frozen=True)
class BrowserPageCapture:
    title: str
    source_url: str
    visible_text: str
    html: str
    screenshot_png: bytes = b""
    width: int = 0
    height: int = 0
    source: str = "chaseos_owned_browser_runtime"


BrowserPageProvider = Callable[[str], BrowserPageCapture]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_run_id(value: str | None = None) -> str:
    raw = str(value or _slug_timestamp()).strip()
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip(".-")
    return safe[:80] or _slug_timestamp()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _ambient_clipboard_retention_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = _DEFAULT_AMBIENT_CLIPBOARD_RETENTION_LIMIT
    return max(1, min(limit, _MAX_AMBIENT_CLIPBOARD_RETENTION_LIMIT))


def _read_ambient_clipboard_state(vault: Path) -> dict[str, Any]:
    path = ambient_clipboard_monitor_state_path(vault)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "schema_version": MODEL_VERSION,
            "updated_at_utc": None,
            "retention_limit": _DEFAULT_AMBIENT_CLIPBOARD_RETENTION_LIMIT,
            "entry_count": 0,
            "entries": [],
        }
    return payload if isinstance(payload, dict) else {}


def _write_ambient_clipboard_state(vault: Path, state: dict[str, Any]) -> None:
    path = ambient_clipboard_monitor_state_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _collision_safe_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def capture_collector_settings_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve() / "runtime" / "studio" / "state" / "capture-collectors.json"


def active_browser_capture_state_path(vault_root: str | Path) -> Path:
    return (
        Path(vault_root).resolve()
        / "runtime"
        / "studio"
        / "state"
        / "capture-active-browser.json"
    )


def ambient_clipboard_monitor_state_path(vault_root: str | Path) -> Path:
    return (
        Path(vault_root).resolve()
        / "runtime"
        / "studio"
        / "state"
        / "capture-ambient-clipboard.json"
    )


def default_capture_collector_settings() -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "updated_at_utc": None,
        "screen_capture_enabled": False,
        "display_region_capture_enabled": False,
        "active_window_capture_enabled": False,
        "clipboard_capture_enabled": False,
        "ambient_clipboard_monitoring_enabled": False,
        "ambient_clipboard_retention_limit": _DEFAULT_AMBIENT_CLIPBOARD_RETENTION_LIMIT,
        "selected_text_capture_enabled": False,
        "accessibility_tree_capture_enabled": False,
        "browser_artifact_capture_enabled": False,
        "browser_extension_capture_enabled": False,
        "active_chaseos_browser_capture_enabled": False,
        "discord_artifact_capture_enabled": False,
        "live_discord_command_capture_enabled": False,
        "chaseos_browser_page_capture_enabled": False,
    }


def _read_persisted_settings(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_capture_collector_settings(vault_root: str | Path) -> dict[str, Any]:
    path = capture_collector_settings_path(vault_root)
    settings = default_capture_collector_settings()
    persisted = _read_persisted_settings(path)
    settings["screen_capture_enabled"] = bool(persisted.get("screen_capture_enabled"))
    settings["display_region_capture_enabled"] = bool(
        persisted.get("display_region_capture_enabled")
    )
    settings["active_window_capture_enabled"] = bool(
        persisted.get("active_window_capture_enabled")
    )
    settings["clipboard_capture_enabled"] = bool(persisted.get("clipboard_capture_enabled"))
    settings["ambient_clipboard_monitoring_enabled"] = bool(
        persisted.get("ambient_clipboard_monitoring_enabled")
    )
    settings["ambient_clipboard_retention_limit"] = _ambient_clipboard_retention_limit(
        persisted.get("ambient_clipboard_retention_limit")
    )
    settings["selected_text_capture_enabled"] = bool(
        persisted.get("selected_text_capture_enabled")
    )
    settings["accessibility_tree_capture_enabled"] = bool(
        persisted.get("accessibility_tree_capture_enabled")
    )
    settings["browser_artifact_capture_enabled"] = bool(
        persisted.get("browser_artifact_capture_enabled")
    )
    settings["browser_extension_capture_enabled"] = bool(
        persisted.get("browser_extension_capture_enabled")
    )
    settings["active_chaseos_browser_capture_enabled"] = bool(
        persisted.get("active_chaseos_browser_capture_enabled")
    )
    settings["discord_artifact_capture_enabled"] = bool(
        persisted.get("discord_artifact_capture_enabled")
    )
    settings["live_discord_command_capture_enabled"] = bool(
        persisted.get("live_discord_command_capture_enabled")
    )
    settings["chaseos_browser_page_capture_enabled"] = bool(
        persisted.get("chaseos_browser_page_capture_enabled")
    )
    settings["updated_at_utc"] = persisted.get("updated_at_utc")
    return settings


def _write_capture_collector_settings(vault_root: str | Path, settings: dict[str, Any]) -> None:
    path = capture_collector_settings_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")


def save_capture_collector_settings(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = payload or {}
    settings = load_capture_collector_settings(vault_root)
    if "screen_capture_enabled" in request:
        settings["screen_capture_enabled"] = bool(request.get("screen_capture_enabled"))
    if "display_region_capture_enabled" in request:
        settings["display_region_capture_enabled"] = bool(
            request.get("display_region_capture_enabled")
        )
    if "active_window_capture_enabled" in request:
        settings["active_window_capture_enabled"] = bool(
            request.get("active_window_capture_enabled")
        )
    if "clipboard_capture_enabled" in request:
        settings["clipboard_capture_enabled"] = bool(request.get("clipboard_capture_enabled"))
    if "ambient_clipboard_monitoring_enabled" in request:
        settings["ambient_clipboard_monitoring_enabled"] = bool(
            request.get("ambient_clipboard_monitoring_enabled")
        )
    if "ambient_clipboard_retention_limit" in request:
        settings["ambient_clipboard_retention_limit"] = _ambient_clipboard_retention_limit(
            request.get("ambient_clipboard_retention_limit")
        )
    if "selected_text_capture_enabled" in request:
        settings["selected_text_capture_enabled"] = bool(
            request.get("selected_text_capture_enabled")
        )
    if "accessibility_tree_capture_enabled" in request:
        settings["accessibility_tree_capture_enabled"] = bool(
            request.get("accessibility_tree_capture_enabled")
        )
    if "browser_artifact_capture_enabled" in request:
        settings["browser_artifact_capture_enabled"] = bool(
            request.get("browser_artifact_capture_enabled")
        )
    if "browser_extension_capture_enabled" in request:
        settings["browser_extension_capture_enabled"] = bool(
            request.get("browser_extension_capture_enabled")
        )
    if "active_chaseos_browser_capture_enabled" in request:
        settings["active_chaseos_browser_capture_enabled"] = bool(
            request.get("active_chaseos_browser_capture_enabled")
        )
    if "discord_artifact_capture_enabled" in request:
        settings["discord_artifact_capture_enabled"] = bool(
            request.get("discord_artifact_capture_enabled")
        )
    if "live_discord_command_capture_enabled" in request:
        settings["live_discord_command_capture_enabled"] = bool(
            request.get("live_discord_command_capture_enabled")
        )
    if "chaseos_browser_page_capture_enabled" in request:
        settings["chaseos_browser_page_capture_enabled"] = bool(
            request.get("chaseos_browser_page_capture_enabled")
        )
    settings["schema_version"] = MODEL_VERSION
    settings["updated_at_utc"] = _now_utc()
    _write_capture_collector_settings(vault_root, settings)
    return build_capture_collector_settings_model(vault_root)


def explicit_screen_capture_policy() -> dict[str, Any]:
    return {
        "policy_id": SCREEN_CAPTURE_POLICY_ID,
        "status": "manual_click_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "writes_screenshot_evidence": True,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "reads_active_window_metadata": False,
        "reads_active_browser_tab": False,
        "reads_ambient_clipboard": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
    }


def explicit_display_region_capture_policy() -> dict[str, Any]:
    return {
        "policy_id": DISPLAY_REGION_CAPTURE_POLICY_ID,
        "status": "manual_drag_select_only",
        "settings_enable_required": True,
        "operator_click_or_studio_shortcut_required": True,
        "operator_drag_select_required": True,
        "writes_screenshot_evidence": True,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "uses_local_image_text_extraction_on_preview_or_save": True,
        "registers_global_hotkeys": False,
        "reads_active_window_metadata": False,
        "reads_active_browser_tab": False,
        "reads_ambient_clipboard": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
    }


def explicit_active_window_capture_policy() -> dict[str, Any]:
    return {
        "policy_id": ACTIVE_WINDOW_CAPTURE_POLICY_ID,
        "status": "manual_active_window_only",
        "settings_enable_required": True,
        "operator_click_or_studio_shortcut_required": True,
        "captures_foreground_window_rectangle": True,
        "writes_screenshot_evidence": True,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "uses_local_image_text_extraction_on_preview_or_save": True,
        "registers_global_hotkeys": False,
        "reads_active_window_metadata": True,
        "reads_active_browser_tab": False,
        "reads_ambient_clipboard": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
    }


def explicit_clipboard_text_policy() -> dict[str, Any]:
    return {
        "policy_id": CLIPBOARD_TEXT_POLICY_ID,
        "status": "manual_click_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "reads_clipboard_text": True,
        "reads_clipboard_on_settings_load": False,
        "reads_clipboard_on_capture_panel_load": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "reads_active_window_metadata": False,
        "reads_active_browser_tab": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def ambient_clipboard_monitor_policy() -> dict[str, Any]:
    return {
        "policy_id": AMBIENT_CLIPBOARD_POLICY_ID,
        "status": "privacy_gated_monitoring_session",
        "settings_enable_required": True,
        "operator_monitoring_session_required": True,
        "reads_clipboard_text": True,
        "reads_clipboard_on_settings_load": False,
        "reads_clipboard_on_capture_panel_load": False,
        "reads_clipboard_only_during_active_monitor_session": True,
        "writes_studio_state_ring_buffer": True,
        "retention_limit_default": _DEFAULT_AMBIENT_CLIPBOARD_RETENTION_LIMIT,
        "retention_limit_max": _MAX_AMBIENT_CLIPBOARD_RETENTION_LIMIT,
        "clear_requires_exact_confirmation": True,
        "clear_confirmation_phrase": "CLEAR AMBIENT CLIPBOARD",
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_selected_text_policy() -> dict[str, Any]:
    return {
        "policy_id": SELECTED_TEXT_POLICY_ID,
        "status": "manual_selected_text_only",
        "settings_enable_required": True,
        "operator_click_or_shortcut_required": True,
        "reads_selected_text_from_foreground_app": True,
        "uses_temporary_clipboard_copy": True,
        "restores_text_clipboard_when_possible": True,
        "reads_clipboard_on_settings_load": False,
        "reads_clipboard_on_capture_panel_load": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "reads_active_window_metadata": True,
        "reads_active_browser_tab": False,
        "reads_ambient_clipboard": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_accessibility_tree_policy() -> dict[str, Any]:
    return {
        "policy_id": ACCESSIBILITY_TREE_POLICY_ID,
        "status": "manual_accessibility_tree_only",
        "settings_enable_required": True,
        "operator_click_or_shortcut_required": True,
        "reads_accessibility_tree_from_foreground_app": True,
        "reads_accessibility_tree_on_settings_load": False,
        "reads_accessibility_tree_on_capture_panel_load": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "reads_active_window_metadata": True,
        "reads_active_browser_tab": False,
        "reads_ambient_clipboard": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_browser_artifact_policy() -> dict[str, Any]:
    return {
        "policy_id": BROWSER_ARTIFACT_POLICY_ID,
        "status": "manual_artifact_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "operator_selected_file_required": True,
        "declared_source_url_required": True,
        "reads_controlled_browser_artifact": True,
        "reads_active_browser_tab": False,
        "reads_browser_profile": False,
        "reads_browser_history": False,
        "reads_browser_cookies": False,
        "reads_browser_sessions": False,
        "reads_browser_storage": False,
        "reads_active_window_metadata": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_browser_extension_capture_policy() -> dict[str, Any]:
    return {
        "policy_id": BROWSER_EXTENSION_CAPTURE_POLICY_ID,
        "status": "manual_extension_artifact_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "operator_selected_file_required": True,
        "reads_chaseos_browser_extension_artifact": True,
        "reads_active_browser_tab": False,
        "reads_browser_profile": False,
        "reads_browser_history": False,
        "reads_browser_cookies": False,
        "reads_browser_sessions": False,
        "reads_browser_storage": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "extension_package_path": "runtime/browser_extension/capture_to_markdown",
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_active_chaseos_browser_policy() -> dict[str, Any]:
    return {
        "policy_id": ACTIVE_CHASEOS_BROWSER_POLICY_ID,
        "status": "chaseos_owned_active_artifact_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "reads_chaseos_active_browser_state": True,
        "reads_controlled_browser_artifact": True,
        "declared_source_url_required": True,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "reads_personal_active_browser_tab": False,
        "reads_browser_profile": False,
        "reads_browser_history": False,
        "reads_browser_cookies": False,
        "reads_browser_sessions": False,
        "reads_browser_storage": False,
        "reads_active_window_metadata": False,
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_chaseos_browser_page_policy() -> dict[str, Any]:
    return {
        "policy_id": CHASEOS_BROWSER_PAGE_POLICY_ID,
        "status": "manual_chaseos_owned_browser_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "declared_target_url_required": True,
        "launches_chaseos_owned_isolated_browser": True,
        "reads_chaseos_owned_browser_page": True,
        "writes_controlled_browser_artifact": True,
        "writes_screenshot_evidence": True,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "reads_personal_active_browser_tab": False,
        "reads_browser_profile": False,
        "reads_browser_history": False,
        "reads_browser_cookies": False,
        "reads_browser_sessions": False,
        "reads_browser_storage": False,
        "reads_active_window_metadata": False,
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def explicit_discord_artifact_policy() -> dict[str, Any]:
    return {
        "policy_id": DISCORD_ARTIFACT_POLICY_ID,
        "status": "manual_artifact_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "operator_selected_file_required": True,
        "declared_discord_source_required": True,
        "reads_chaseos_owned_discord_artifact": True,
        "allowed_artifact_dirs": list(DISCORD_ARTIFACT_DIRS),
        "calls_discord_api": False,
        "reads_discord_token": False,
        "reads_discord_webhook": False,
        "reads_discord_bindings": False,
        "listens_to_discord_events": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def live_discord_command_capture_policy() -> dict[str, Any]:
    return {
        "policy_id": LIVE_DISCORD_COMMAND_POLICY_ID,
        "status": "agent_bus_ingress_only",
        "settings_enable_required": True,
        "operator_click_required": True,
        "reads_chaseos_agent_bus_discord_ingress": True,
        "reads_discord_bindings": False,
        "calls_discord_api": False,
        "reads_discord_token": False,
        "reads_discord_webhook": False,
        "opens_discord_gateway": False,
        "direct_discord_event_listener": False,
        "writes_raw_quarantine_markdown": False,
        "preview_or_save_required_for_markdown": True,
        "registers_global_hotkeys": False,
        "provider_calls_allowed": False,
        "external_send_allowed": False,
        "canonical_mutation_allowed": False,
    }


def build_capture_collector_settings_model(vault_root: str | Path) -> dict[str, Any]:
    settings = load_capture_collector_settings(vault_root)
    screen_enabled = bool(settings.get("screen_capture_enabled"))
    screen_status = "available_click_to_capture" if screen_enabled else "disabled_in_settings"
    display_region_enabled = bool(settings.get("display_region_capture_enabled"))
    display_region_status = (
        "available_drag_select_to_capture"
        if display_region_enabled
        else "disabled_in_settings"
    )
    active_window_enabled = bool(settings.get("active_window_capture_enabled"))
    active_window_status = (
        "available_active_window_capture"
        if active_window_enabled
        else "disabled_in_settings"
    )
    clipboard_enabled = bool(settings.get("clipboard_capture_enabled"))
    clipboard_status = "available_click_to_capture" if clipboard_enabled else "disabled_in_settings"
    ambient_clipboard_enabled = bool(settings.get("ambient_clipboard_monitoring_enabled"))
    ambient_clipboard_status = (
        "available_privacy_gated_monitor"
        if ambient_clipboard_enabled
        else "disabled_in_settings"
    )
    ambient_clipboard_retention_limit = _ambient_clipboard_retention_limit(
        settings.get("ambient_clipboard_retention_limit")
    )
    selected_text_enabled = bool(settings.get("selected_text_capture_enabled"))
    selected_text_status = (
        "available_selected_text_capture"
        if selected_text_enabled
        else "disabled_in_settings"
    )
    accessibility_tree_enabled = bool(settings.get("accessibility_tree_capture_enabled"))
    accessibility_tree_status = (
        "available_accessibility_tree_capture"
        if accessibility_tree_enabled
        else "disabled_in_settings"
    )
    browser_artifact_enabled = bool(settings.get("browser_artifact_capture_enabled"))
    browser_artifact_status = (
        "available_select_artifact"
        if browser_artifact_enabled
        else "disabled_in_settings"
    )
    browser_extension_enabled = bool(settings.get("browser_extension_capture_enabled"))
    browser_extension_status = (
        "available_select_extension_artifact"
        if browser_extension_enabled
        else "disabled_in_settings"
    )
    active_browser_enabled = bool(settings.get("active_chaseos_browser_capture_enabled"))
    active_browser_status = (
        "available_click_to_capture"
        if active_browser_enabled
        else "disabled_in_settings"
    )
    discord_artifact_enabled = bool(settings.get("discord_artifact_capture_enabled"))
    discord_artifact_status = (
        "available_select_artifact"
        if discord_artifact_enabled
        else "disabled_in_settings"
    )
    live_discord_command_enabled = bool(
        settings.get("live_discord_command_capture_enabled")
    )
    live_discord_command_status = (
        "available_agent_bus_ingress"
        if live_discord_command_enabled
        else "disabled_in_settings"
    )
    chaseos_browser_page_enabled = bool(settings.get("chaseos_browser_page_capture_enabled"))
    chaseos_browser_page_status = (
        "available_click_to_capture"
        if chaseos_browser_page_enabled
        else "disabled_in_settings"
    )
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "settings_path": str(capture_collector_settings_path(vault_root)),
        "updated_at_utc": settings.get("updated_at_utc"),
        "screen_capture_enabled": screen_enabled,
        "display_region_capture_enabled": display_region_enabled,
        "active_window_capture_enabled": active_window_enabled,
        "clipboard_capture_enabled": clipboard_enabled,
        "ambient_clipboard_monitoring_enabled": ambient_clipboard_enabled,
        "ambient_clipboard_retention_limit": ambient_clipboard_retention_limit,
        "selected_text_capture_enabled": selected_text_enabled,
        "accessibility_tree_capture_enabled": accessibility_tree_enabled,
        "browser_artifact_capture_enabled": browser_artifact_enabled,
        "browser_extension_capture_enabled": browser_extension_enabled,
        "active_chaseos_browser_capture_enabled": active_browser_enabled,
        "discord_artifact_capture_enabled": discord_artifact_enabled,
        "live_discord_command_capture_enabled": live_discord_command_enabled,
        "chaseos_browser_page_capture_enabled": chaseos_browser_page_enabled,
        "collectors": [
            {
                "id": "screen_capture",
                "label": "Screen capture",
                "status": screen_status,
                "available_in_studio": screen_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "action": "run_screen_capture_collector" if screen_enabled else "open_settings_collectors",
                "description": (
                    "Capture the current screen after this Settings toggle and an explicit Capture page click."
                    if screen_enabled
                    else "Disabled until you enable explicit screen capture in Settings."
                ),
                "policy": explicit_screen_capture_policy(),
            },
            {
                "id": "display_region_capture",
                "label": "Display region capture",
                "status": display_region_status,
                "available_in_studio": display_region_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "screenshot_text_extraction" if display_region_enabled else None,
                "action": (
                    "run_display_region_collector"
                    if display_region_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Drag a rectangle over the display after this Settings toggle and a Capture page click or Studio shortcut."
                    if display_region_enabled
                    else "Disabled until you enable explicit display region capture in Settings."
                ),
                "policy": explicit_display_region_capture_policy(),
            },
            {
                "id": "active_window_capture",
                "label": "Active window capture",
                "status": active_window_status,
                "available_in_studio": active_window_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "screenshot_text_extraction" if active_window_enabled else None,
                "action": (
                    "run_active_window_collector"
                    if active_window_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Capture the foreground window rectangle after this Settings toggle and a Capture page click or Studio shortcut."
                    if active_window_enabled
                    else "Disabled until you enable explicit active window capture in Settings."
                ),
                "policy": explicit_active_window_capture_policy(),
            },
            {
                "id": "clipboard_text_capture",
                "label": "Clipboard text",
                "status": clipboard_status,
                "available_in_studio": clipboard_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "action": "run_clipboard_text_collector" if clipboard_enabled else "open_settings_collectors",
                "description": (
                    "Read current clipboard text after this Settings toggle and an explicit Capture page click."
                    if clipboard_enabled
                    else "Disabled until you enable explicit clipboard text capture in Settings."
                ),
                "policy": explicit_clipboard_text_policy(),
            },
            {
                "id": "ambient_clipboard_monitor",
                "label": "Ambient clipboard monitor",
                "status": ambient_clipboard_status,
                "available_in_studio": ambient_clipboard_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "manual_text" if ambient_clipboard_enabled else None,
                "action": (
                    "run_ambient_clipboard_monitor"
                    if ambient_clipboard_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Poll clipboard text only during an explicit monitoring session and keep a small local buffer."
                    if ambient_clipboard_enabled
                    else "Disabled until you opt into privacy-gated ambient clipboard monitoring in Settings."
                ),
                "policy": ambient_clipboard_monitor_policy(),
            },
            {
                "id": "selected_text_capture",
                "label": "Selected text",
                "status": selected_text_status,
                "available_in_studio": selected_text_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "manual_text" if selected_text_enabled else None,
                "action": (
                    "run_selected_text_collector"
                    if selected_text_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Copy selected text from the foreground application after this Settings toggle and a Capture page click or configured shortcut."
                    if selected_text_enabled
                    else "Disabled until you enable explicit selected-text capture in Settings."
                ),
                "policy": explicit_selected_text_policy(),
            },
            {
                "id": "accessibility_tree_capture",
                "label": "Accessibility tree",
                "status": accessibility_tree_status,
                "available_in_studio": accessibility_tree_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "manual_text" if accessibility_tree_enabled else None,
                "action": (
                    "run_accessibility_tree_collector"
                    if accessibility_tree_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Read the foreground application's accessibility tree text after this Settings toggle and a Capture page click or configured shortcut."
                    if accessibility_tree_enabled
                    else "Disabled until you enable explicit accessibility tree capture in Settings."
                ),
                "policy": explicit_accessibility_tree_policy(),
            },
            {
                "id": "active_browser_artifact_capture",
                "label": "Browser artifact capture",
                "status": browser_artifact_status,
                "available_in_studio": browser_artifact_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "controlled_html_artifact" if browser_artifact_enabled else None,
                "action": (
                    "run_browser_artifact_collector"
                    if browser_artifact_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Validate an operator-selected ChaseOS browser artifact and declared address after this Settings toggle and a Capture page click."
                    if browser_artifact_enabled
                    else "Disabled until you enable explicit browser artifact capture in Settings."
                ),
                "policy": explicit_browser_artifact_policy(),
            },
            {
                "id": "browser_extension_capture",
                "label": "Browser extension capture",
                "status": browser_extension_status,
                "available_in_studio": browser_extension_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "manual_text" if browser_extension_enabled else None,
                "action": (
                    "run_browser_extension_collector"
                    if browser_extension_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Import a ChaseOS browser extension capture artifact after this Settings toggle and a Capture page click."
                    if browser_extension_enabled
                    else "Disabled until you enable ChaseOS browser extension capture in Settings."
                ),
                "policy": explicit_browser_extension_capture_policy(),
            },
            {
                "id": "chaseos_browser_page_capture",
                "label": "ChaseOS browser page",
                "status": chaseos_browser_page_status,
                "available_in_studio": chaseos_browser_page_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "controlled_html_artifact" if chaseos_browser_page_enabled else None,
                "action": (
                    "run_chaseos_browser_page_collector"
                    if chaseos_browser_page_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Launch an isolated ChaseOS-owned browser page for the declared address after this Settings toggle and a Capture page click."
                    if chaseos_browser_page_enabled
                    else "Disabled until you enable explicit ChaseOS-owned browser page capture in Settings."
                ),
                "policy": explicit_chaseos_browser_page_policy(),
            },
            {
                "id": "active_browser_tab_capture",
                "label": "Active ChaseOS browser",
                "status": active_browser_status,
                "available_in_studio": active_browser_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "controlled_html_artifact" if active_browser_enabled else None,
                "action": (
                    "run_active_browser_collector"
                    if active_browser_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Capture the current ChaseOS-owned active browser artifact after this Settings toggle and a Capture page click."
                    if active_browser_enabled
                    else "Disabled until you enable active ChaseOS browser capture in Settings."
                ),
                "policy": explicit_active_chaseos_browser_policy(),
            },
            {
                "id": "discord_capture",
                "label": "Discord capture",
                "status": discord_artifact_status,
                "available_in_studio": discord_artifact_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "manual_text" if discord_artifact_enabled else None,
                "action": (
                    "run_discord_artifact_collector"
                    if discord_artifact_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Import an operator-selected ChaseOS Discord artifact and declared Discord source after this Settings toggle and a Capture page click."
                    if discord_artifact_enabled
                    else "Disabled until you enable explicit Discord artifact capture in Settings."
                ),
                "policy": explicit_discord_artifact_policy(),
            },
            {
                "id": "live_discord_command_capture",
                "label": "Live Discord command",
                "status": live_discord_command_status,
                "available_in_studio": live_discord_command_enabled,
                "settings_configurable": True,
                "target_panel": "capture-markdown",
                "source_mode": "manual_text" if live_discord_command_enabled else None,
                "action": (
                    "run_live_discord_command_collector"
                    if live_discord_command_enabled
                    else "open_settings_collectors"
                ),
                "description": (
                    "Import the latest or selected Discord-origin Agent Bus command after this Settings toggle and a Capture page click."
                    if live_discord_command_enabled
                    else "Disabled until you enable live Discord command capture in Settings."
                ),
                "policy": live_discord_command_capture_policy(),
            },
        ],
        "summary": {
            "settings_page_visible": True,
            "screen_capture_collector_built": True,
            "screen_capture_enabled": screen_enabled,
            "screen_capture_status": screen_status,
            "display_region_capture_collector_built": True,
            "display_region_capture_enabled": display_region_enabled,
            "display_region_capture_status": display_region_status,
            "active_window_capture_collector_built": True,
            "active_window_capture_enabled": active_window_enabled,
            "active_window_capture_status": active_window_status,
            "clipboard_capture_collector_built": True,
            "clipboard_capture_enabled": clipboard_enabled,
            "clipboard_capture_status": clipboard_status,
            "ambient_clipboard_monitor_built": True,
            "ambient_clipboard_monitoring_enabled": ambient_clipboard_enabled,
            "ambient_clipboard_status": ambient_clipboard_status,
            "ambient_clipboard_retention_limit": ambient_clipboard_retention_limit,
            "selected_text_capture_collector_built": True,
            "selected_text_capture_enabled": selected_text_enabled,
            "selected_text_capture_status": selected_text_status,
            "accessibility_tree_capture_collector_built": True,
            "accessibility_tree_capture_enabled": accessibility_tree_enabled,
            "accessibility_tree_capture_status": accessibility_tree_status,
            "browser_artifact_capture_collector_built": True,
            "browser_artifact_capture_enabled": browser_artifact_enabled,
            "browser_artifact_capture_status": browser_artifact_status,
            "browser_extension_capture_collector_built": True,
            "browser_extension_capture_enabled": browser_extension_enabled,
            "browser_extension_capture_status": browser_extension_status,
            "active_chaseos_browser_capture_collector_built": True,
            "active_chaseos_browser_capture_enabled": active_browser_enabled,
            "active_chaseos_browser_capture_status": active_browser_status,
            "chaseos_browser_page_capture_collector_built": True,
            "chaseos_browser_page_capture_enabled": chaseos_browser_page_enabled,
            "chaseos_browser_page_capture_status": chaseos_browser_page_status,
            "discord_artifact_capture_collector_built": True,
            "discord_artifact_capture_enabled": discord_artifact_enabled,
            "discord_artifact_capture_status": discord_artifact_status,
            "live_discord_command_capture_collector_built": True,
            "live_discord_command_capture_enabled": live_discord_command_enabled,
            "live_discord_command_capture_status": live_discord_command_status,
            "active_browser_capture_built": True,
            "personal_active_browser_capture_built": False,
            "discord_capture_built": True,
            "live_discord_capture_built": True,
        },
        "authority": {
            "writes_studio_preferences": True,
            "captures_screen_pixels_only_after_settings_and_click": True,
            "captures_display_region_pixels_only_after_settings_and_drag": True,
            "captures_active_window_pixels_only_after_settings_and_click": True,
            "captures_screen_pixels_on_settings_load": False,
            "captures_screen_pixels_on_capture_panel_load": False,
            "reads_clipboard_text_only_after_settings_and_click": True,
            "reads_ambient_clipboard_only_after_privacy_opt_in_and_monitor_start": True,
            "reads_selected_text_only_after_settings_and_click": True,
            "reads_accessibility_tree_only_after_settings_and_click": True,
            "reads_clipboard_on_settings_load": False,
            "reads_clipboard_on_capture_panel_load": False,
            "reads_ambient_clipboard_on_settings_load": False,
            "reads_ambient_clipboard_on_capture_panel_load": False,
            "reads_accessibility_tree_on_settings_load": False,
            "reads_accessibility_tree_on_capture_panel_load": False,
            "writes_screenshot_evidence_on_click": True,
            "writes_raw_quarantine_markdown_on_click": False,
            "reads_controlled_browser_artifact_only_after_settings_file_and_click": True,
            "reads_browser_extension_artifact_only_after_settings_file_and_click": True,
            "reads_controlled_browser_artifact_on_settings_load": False,
            "reads_controlled_browser_artifact_on_capture_panel_load": False,
            "reads_browser_extension_artifact_on_settings_load": False,
            "reads_browser_extension_artifact_on_capture_panel_load": False,
            "reads_chaseos_active_browser_state_only_after_settings_and_click": True,
            "reads_chaseos_active_browser_state_on_settings_load": False,
            "reads_chaseos_active_browser_state_on_capture_panel_load": False,
            "reads_chaseos_owned_browser_page_only_after_settings_url_and_click": True,
            "launches_chaseos_owned_isolated_browser_only_after_settings_url_and_click": True,
            "reads_chaseos_owned_browser_page_on_settings_load": False,
            "reads_chaseos_owned_browser_page_on_capture_panel_load": False,
            "reads_chaseos_discord_artifact_only_after_settings_file_and_click": True,
            "reads_chaseos_agent_bus_discord_ingress_only_after_settings_and_click": True,
            "reads_chaseos_discord_artifact_on_settings_load": False,
            "reads_chaseos_discord_artifact_on_capture_panel_load": False,
            "reads_chaseos_agent_bus_discord_ingress_on_settings_load": False,
            "reads_chaseos_agent_bus_discord_ingress_on_capture_panel_load": False,
            "calls_discord_api": False,
            "reads_discord_token": False,
            "reads_discord_webhook": False,
            "reads_discord_bindings": False,
            "listens_to_discord_events": False,
            "registers_global_hotkeys": False,
            "reads_active_window_metadata": False,
            "reads_selected_text": selected_text_enabled,
            "reads_accessibility_tree": accessibility_tree_enabled,
            "reads_active_browser_tab": False,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "reads_ambient_clipboard": ambient_clipboard_enabled,
            "ambient_clipboard_ring_buffer_write_allowed": ambient_clipboard_enabled,
            "ambient_clipboard_clear_requires_exact_confirmation": True,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "settings_page_visible": True,
            "screen_capture_settings_configurable": True,
            "screen_capture_collector_built": True,
            "screen_capture_enabled": screen_enabled,
            "screen_capture_requires_operator_click": True,
            "screen_capture_writes_evidence_only": True,
            "screen_capture_markdown_save_uses_existing_quarantine_flow": True,
            "display_region_capture_settings_configurable": True,
            "display_region_capture_collector_built": True,
            "display_region_capture_enabled": display_region_enabled,
            "display_region_capture_requires_operator_drag": True,
            "display_region_capture_writes_evidence_only": True,
            "display_region_capture_markdown_save_uses_existing_quarantine_flow": True,
            "display_region_capture_uses_screenshot_text_extraction": True,
            "active_window_capture_settings_configurable": True,
            "active_window_capture_collector_built": True,
            "active_window_capture_enabled": active_window_enabled,
            "active_window_capture_requires_operator_click": True,
            "active_window_capture_writes_evidence_only": True,
            "active_window_capture_reads_active_window_metadata": True,
            "active_window_capture_markdown_save_uses_existing_quarantine_flow": True,
            "active_window_capture_uses_screenshot_text_extraction": True,
            "clipboard_capture_settings_configurable": True,
            "clipboard_capture_collector_built": True,
            "clipboard_capture_enabled": clipboard_enabled,
            "clipboard_capture_requires_operator_click": True,
            "clipboard_capture_writes_no_markdown_on_click": True,
            "clipboard_capture_markdown_save_uses_existing_quarantine_flow": True,
            "ambient_clipboard_monitor_settings_configurable": True,
            "ambient_clipboard_monitor_built": True,
            "ambient_clipboard_monitoring_enabled": ambient_clipboard_enabled,
            "ambient_clipboard_monitor_requires_privacy_opt_in": True,
            "ambient_clipboard_monitor_requires_operator_start": True,
            "ambient_clipboard_monitor_reads_on_settings_load": False,
            "ambient_clipboard_monitor_reads_on_capture_panel_load": False,
            "ambient_clipboard_monitor_writes_state_ring_buffer_only": True,
            "ambient_clipboard_monitor_writes_no_markdown_on_poll": True,
            "ambient_clipboard_monitor_markdown_save_uses_existing_quarantine_flow": True,
            "ambient_clipboard_monitor_retention_limit": ambient_clipboard_retention_limit,
            "ambient_clipboard_monitor_clear_requires_exact_confirmation": True,
            "selected_text_capture_settings_configurable": True,
            "selected_text_capture_collector_built": True,
            "selected_text_capture_enabled": selected_text_enabled,
            "selected_text_capture_requires_operator_click": True,
            "selected_text_capture_uses_temporary_clipboard_copy": True,
            "selected_text_capture_restores_text_clipboard_when_possible": True,
            "selected_text_capture_reads_on_settings_load": False,
            "selected_text_capture_reads_on_capture_panel_load": False,
            "selected_text_capture_writes_no_markdown_on_click": True,
            "selected_text_capture_markdown_save_uses_existing_quarantine_flow": True,
            "accessibility_tree_capture_settings_configurable": True,
            "accessibility_tree_capture_collector_built": True,
            "accessibility_tree_capture_enabled": accessibility_tree_enabled,
            "accessibility_tree_capture_requires_operator_click": True,
            "accessibility_tree_capture_reads_foreground_app_tree": True,
            "accessibility_tree_capture_reads_on_settings_load": False,
            "accessibility_tree_capture_reads_on_capture_panel_load": False,
            "accessibility_tree_capture_writes_no_markdown_on_click": True,
            "accessibility_tree_capture_markdown_save_uses_existing_quarantine_flow": True,
            "browser_artifact_capture_settings_configurable": True,
            "browser_artifact_capture_collector_built": True,
            "browser_artifact_capture_enabled": browser_artifact_enabled,
            "browser_artifact_capture_requires_operator_click": True,
            "browser_artifact_capture_requires_operator_selected_file": True,
            "browser_artifact_capture_requires_declared_url": True,
            "browser_artifact_capture_writes_no_markdown_on_click": True,
            "browser_artifact_capture_markdown_save_uses_existing_quarantine_flow": True,
            "browser_artifact_capture_reads_live_browser": False,
            "browser_extension_capture_settings_configurable": True,
            "browser_extension_capture_collector_built": True,
            "browser_extension_capture_enabled": browser_extension_enabled,
            "browser_extension_capture_requires_operator_click": True,
            "browser_extension_capture_requires_operator_selected_file": True,
            "browser_extension_capture_writes_no_markdown_on_click": True,
            "browser_extension_capture_markdown_save_uses_existing_quarantine_flow": True,
            "browser_extension_package_built": True,
            "browser_extension_capture_reads_personal_browser_profile": False,
            "active_chaseos_browser_capture_settings_configurable": True,
            "active_chaseos_browser_capture_collector_built": True,
            "active_chaseos_browser_capture_enabled": active_browser_enabled,
            "active_chaseos_browser_capture_requires_operator_click": True,
            "active_chaseos_browser_capture_reads_chaseos_state": True,
            "active_chaseos_browser_capture_reads_personal_browser": False,
            "active_chaseos_browser_capture_writes_no_markdown_on_click": True,
            "active_chaseos_browser_capture_markdown_save_uses_existing_quarantine_flow": True,
            "chaseos_browser_page_capture_settings_configurable": True,
            "chaseos_browser_page_capture_collector_built": True,
            "chaseos_browser_page_capture_enabled": chaseos_browser_page_enabled,
            "chaseos_browser_page_capture_requires_operator_click": True,
            "chaseos_browser_page_capture_requires_declared_url": True,
            "chaseos_browser_page_capture_writes_controlled_artifact": True,
            "chaseos_browser_page_capture_writes_no_markdown_on_click": True,
            "chaseos_browser_page_capture_markdown_save_uses_existing_quarantine_flow": True,
            "chaseos_browser_page_capture_reads_personal_browser": False,
            "discord_artifact_capture_settings_configurable": True,
            "discord_artifact_capture_collector_built": True,
            "discord_artifact_capture_enabled": discord_artifact_enabled,
            "discord_artifact_capture_requires_operator_click": True,
            "discord_artifact_capture_requires_operator_selected_file": True,
            "discord_artifact_capture_requires_declared_source": True,
            "discord_artifact_capture_writes_no_markdown_on_click": True,
            "discord_artifact_capture_markdown_save_uses_existing_quarantine_flow": True,
            "discord_artifact_capture_calls_discord_api": False,
            "live_discord_command_capture_settings_configurable": True,
            "live_discord_command_capture_collector_built": True,
            "live_discord_command_capture_enabled": live_discord_command_enabled,
            "live_discord_command_capture_requires_operator_click": True,
            "live_discord_command_capture_reads_agent_bus": True,
            "live_discord_command_capture_reads_discord_api": False,
            "live_discord_command_capture_writes_no_markdown_on_click": True,
            "live_discord_command_capture_markdown_save_uses_existing_quarantine_flow": True,
            "global_hotkey_registration_blocked": True,
            "active_browser_capture_blocked": False,
            "personal_active_browser_capture_blocked": True,
            "discord_capture_blocked": False,
            "live_discord_capture_blocked": False,
        },
    }


def _validate_discord_artifact_path(vault: Path, file_path: str | Path) -> tuple[Path, str]:
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(vault).as_posix()
    except ValueError as exc:
        raise ValueError("Discord artifact path resolves outside the vault root.") from exc
    if not any(relative == allowed or relative.startswith(f"{allowed}/") for allowed in DISCORD_ARTIFACT_DIRS):
        raise ValueError(
            "Discord artifact path is not under an allowed ChaseOS Discord artifact directory."
        )
    lowered = relative.lower()
    if any(marker in lowered for marker in _DISCORD_FORBIDDEN_PATH_MARKERS):
        raise ValueError(
            "Discord artifact path appears to reference credentials, tokens, webhooks, bindings, or secrets."
        )
    if not resolved.exists():
        raise ValueError("Discord artifact file does not exist.")
    if not resolved.is_file():
        raise ValueError("Discord artifact path must be a file.")
    if resolved.stat().st_size < 1:
        raise ValueError("Discord artifact file is empty.")
    return resolved, relative


def _coerce_discord_author(value: Any) -> str:
    if isinstance(value, dict):
        return (
            str(value.get("display_name") or value.get("username") or value.get("name") or "")
            .strip()
        )
    return str(value or "").strip()


def _discord_message_line(message: dict[str, Any]) -> str:
    timestamp = str(
        message.get("timestamp")
        or message.get("created_at")
        or message.get("time")
        or ""
    ).strip()
    author = _coerce_discord_author(message.get("author") or message.get("user") or message.get("username"))
    content = str(message.get("content") or message.get("text") or message.get("message") or "").strip()
    prefix_parts = [part for part in (timestamp, author) if part]
    prefix = " | ".join(prefix_parts)
    return f"- {prefix}: {content}" if prefix else f"- {content}"


def _extract_discord_artifact_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    if len(raw) > _MAX_DISCORD_ARTIFACT_CHARS:
        raise ValueError(
            f"Discord artifact is too large: {len(raw):,} chars exceeds {_MAX_DISCORD_ARTIFACT_CHARS:,}."
        )
    if path.suffix.lower() != ".json":
        text = raw.strip()
        if not text:
            raise ValueError("Discord artifact contains no text.")
        return text

    try:
        payload = json.loads(raw)
    except Exception as exc:
        raise ValueError("Discord artifact JSON could not be parsed.") from exc

    if isinstance(payload, list):
        messages = payload
        heading = "Discord Messages"
    elif isinstance(payload, dict):
        if isinstance(payload.get("messages"), list):
            messages = payload["messages"]
            heading = str(payload.get("title") or payload.get("channel_name") or "Discord Messages").strip()
        else:
            for key in ("markdown", "content", "text", "transcript"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            raise ValueError("Discord artifact JSON must contain messages or text content.")
    else:
        raise ValueError("Discord artifact JSON must be an object or a message list.")

    lines = [f"# {heading or 'Discord Messages'}", ""]
    count = 0
    for item in messages:
        if not isinstance(item, dict):
            continue
        line = _discord_message_line(item)
        if line.strip(" -:"):
            lines.append(line)
            count += 1
    if not count:
        raise ValueError("Discord artifact JSON contains no readable messages.")
    return "\n".join(lines).strip()


def capture_browser_artifact_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an explicit browser artifact for the Capture page without saving Markdown."""

    from runtime.capture.visual_capture.extractors import (
        capture_from_controlled_browser_artifact,
    )

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("browser_artifact_capture_enabled"):
        return _browser_artifact_capture_blocked(
            vault,
            "browser_artifact_capture_disabled_in_settings",
            "Browser artifact capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _browser_artifact_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Browser artifact capture requires an explicit Capture page click.",
        )

    file_path = str(request.get("file_path") or "").strip()
    source_url = str(request.get("source_url") or request.get("declared_url") or "").strip()
    if not file_path:
        return _browser_artifact_capture_blocked(
            vault,
            "browser_artifact_file_required",
            "Browser artifact capture requires an explicit vault-local artifact path.",
        )
    if not source_url:
        return _browser_artifact_capture_blocked(
            vault,
            "browser_artifact_declared_url_required",
            "Browser artifact capture requires the declared source address.",
        )

    try:
        packet = capture_from_controlled_browser_artifact(
            file_path=file_path,
            vault_root=vault,
            declared_url=source_url,
            allowed_origin=str(request.get("allowed_origin") or "").strip() or None,
            source_selector=str(request.get("controlled_source") or "browser_runtime_artifact"),
            title=str(request.get("title") or "").strip() or None,
            profile=str(request.get("profile") or "research_note"),
        )
    except Exception as exc:
        return _browser_artifact_capture_blocked(
            vault,
            "browser_artifact_validation_failed",
            str(exc),
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_browser_artifact_for_markdown",
        "status": "browser_artifact_ready_for_markdown",
        "source_mode": "controlled_html_artifact",
        "title": packet.title,
        "file_path": packet.source.declared_source,
        "source_url": packet.source.source_url,
        "source_app": packet.source.source_app,
        "capture_method": packet.capture_method,
        "extracted_text_preview": packet.content.raw_extracted_text[:500],
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_browser_artifact_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "reads_controlled_browser_artifact": True,
            "reads_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def save_active_browser_capture_state(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist the current ChaseOS-owned browser artifact pointer for Capture."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    file_path = str(
        request.get("file_path")
        or request.get("artifact_path")
        or request.get("html_path")
        or ""
    ).strip()
    source_url = str(
        request.get("source_url")
        or request.get("declared_url")
        or request.get("url")
        or ""
    ).strip()
    if not file_path:
        raise CaptureCollectorError("Active ChaseOS browser state requires an artifact path.")
    if not source_url:
        raise CaptureCollectorError("Active ChaseOS browser state requires a source address.")

    state = {
        "schema_version": MODEL_VERSION,
        "updated_at_utc": _now_utc(),
        "file_path": file_path,
        "source_url": source_url,
        "title": str(request.get("title") or "").strip(),
        "allowed_origin": str(request.get("allowed_origin") or "").strip(),
        "source_selector": str(request.get("source_selector") or "browser_runtime_artifact").strip()
        or "browser_runtime_artifact",
    }
    path = active_browser_capture_state_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "status": "active_chaseos_browser_state_saved",
        "state_path": str(path),
        "state_relative_path": _relative_to_vault(vault, path),
        "file_path": file_path,
        "source_url": source_url,
        "title": state["title"],
        "authority": {
            "writes_studio_state": True,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
        },
    }


def _read_active_browser_capture_state(vault: Path, request: dict[str, Any]) -> dict[str, Any]:
    file_path = str(
        request.get("file_path")
        or request.get("artifact_path")
        or request.get("html_path")
        or ""
    ).strip()
    source_url = str(
        request.get("source_url")
        or request.get("declared_url")
        or request.get("url")
        or ""
    ).strip()
    if file_path or source_url:
        return {
            "file_path": file_path,
            "source_url": source_url,
            "title": str(request.get("title") or "").strip(),
            "allowed_origin": str(request.get("allowed_origin") or "").strip(),
            "source_selector": str(request.get("source_selector") or "browser_runtime_artifact").strip()
            or "browser_runtime_artifact",
            "state_path": "",
        }

    path = active_browser_capture_state_path(vault)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CaptureCollectorError(
            "No ChaseOS active browser artifact is registered for Capture."
        ) from exc
    except Exception as exc:
        raise CaptureCollectorError("Active ChaseOS browser state could not be read.") from exc
    if not isinstance(payload, dict):
        raise CaptureCollectorError("Active ChaseOS browser state is invalid.")
    payload["state_path"] = _relative_to_vault(vault, path)
    return payload


def capture_active_chaseos_browser_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read the current ChaseOS-owned browser artifact for Capture without saving Markdown."""

    from runtime.capture.visual_capture.extractors import (
        capture_from_controlled_browser_artifact,
    )

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("active_chaseos_browser_capture_enabled"):
        return _active_chaseos_browser_capture_blocked(
            vault,
            "active_chaseos_browser_capture_disabled_in_settings",
            "Active ChaseOS browser capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _active_chaseos_browser_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Active ChaseOS browser capture requires an explicit Capture page click.",
        )

    try:
        state = _read_active_browser_capture_state(vault, request)
        file_path = str(
            state.get("file_path")
            or state.get("artifact_path")
            or state.get("html_path")
            or ""
        ).strip()
        source_url = str(
            state.get("source_url")
            or state.get("declared_url")
            or state.get("url")
            or ""
        ).strip()
        if not file_path:
            raise CaptureCollectorError("Active ChaseOS browser capture requires an artifact path.")
        if not source_url:
            raise CaptureCollectorError("Active ChaseOS browser capture requires a source address.")
        packet = capture_from_controlled_browser_artifact(
            file_path=file_path,
            vault_root=vault,
            declared_url=source_url,
            allowed_origin=str(state.get("allowed_origin") or "").strip() or None,
            source_selector=str(state.get("source_selector") or "browser_runtime_artifact").strip()
            or "browser_runtime_artifact",
            title=str(request.get("title") or state.get("title") or "").strip() or None,
            profile=str(request.get("profile") or "research_note"),
        )
    except Exception as exc:
        return _active_chaseos_browser_capture_blocked(
            vault,
            "active_chaseos_browser_capture_failed",
            str(exc),
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_active_chaseos_browser_for_markdown",
        "status": "active_chaseos_browser_ready_for_markdown",
        "source_mode": "controlled_html_artifact",
        "title": packet.title,
        "file_path": packet.source.declared_source,
        "source_url": packet.source.source_url,
        "source_app": packet.source.source_app,
        "capture_method": packet.capture_method,
        "state_path": str(state.get("state_path") or ""),
        "extracted_text_preview": packet.content.raw_extracted_text[:500],
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_active_chaseos_browser_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "reads_chaseos_active_browser_state": True,
            "reads_controlled_browser_artifact": True,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def capture_browser_extension_artifact_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Import a ChaseOS browser extension capture artifact without saving Markdown."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("browser_extension_capture_enabled"):
        return _browser_extension_capture_blocked(
            vault,
            "browser_extension_capture_disabled_in_settings",
            "Browser extension capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _browser_extension_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Browser extension capture requires an explicit Capture page click.",
        )

    file_path = str(
        request.get("file_path")
        or request.get("artifact_path")
        or request.get("extension_artifact_path")
        or ""
    ).strip()
    if not file_path:
        return _browser_extension_capture_blocked(
            vault,
            "browser_extension_artifact_required",
            "Browser extension capture requires an operator-selected extension artifact file.",
        )

    try:
        artifact_path = _resolve_allowed_browser_extension_artifact(vault, file_path)
        artifact = _read_browser_extension_artifact(artifact_path)
        title = str(request.get("title") or artifact.get("title") or "").strip()
        raw_text = _browser_extension_artifact_text(artifact)
        source_url = str(
            request.get("source_url") or artifact.get("source_url") or artifact.get("url") or ""
        ).strip()
        if source_url:
            _validate_browser_extension_url(source_url)
    except Exception as exc:
        return _browser_extension_capture_blocked(
            vault,
            "browser_extension_capture_failed",
            str(exc),
        )

    relative_artifact = _relative_to_vault(vault, artifact_path)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_browser_extension_artifact_for_markdown",
        "status": "browser_extension_artifact_ready_for_markdown",
        "source_mode": "manual_text",
        "title": title or "Browser Extension Capture",
        "raw_text": raw_text,
        "file_path": relative_artifact,
        "source_url": source_url,
        "source": "chaseos_browser_extension_artifact",
        "artifact": {
            "path": str(artifact_path),
            "relative_path": relative_artifact,
            "schema_version": str(artifact.get("schema_version") or ""),
            "captured_at_utc": str(artifact.get("captured_at_utc") or ""),
            "capture_scope": str(artifact.get("capture_scope") or ""),
            "text_length": len(raw_text),
        },
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_browser_extension_capture_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "reads_chaseos_browser_extension_artifact": True,
            "reads_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def capture_chaseos_browser_page_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    browser_provider: BrowserPageProvider | None = None,
) -> dict[str, Any]:
    """Capture a declared page through a ChaseOS-owned isolated browser without saving Markdown."""

    from runtime.capture.visual_capture.extractors import (
        capture_from_controlled_browser_artifact,
    )

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("chaseos_browser_page_capture_enabled"):
        return _chaseos_browser_page_capture_blocked(
            vault,
            "chaseos_browser_page_capture_disabled_in_settings",
            "ChaseOS-owned browser page capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _chaseos_browser_page_capture_blocked(
            vault,
            "operator_confirmation_required",
            "ChaseOS-owned browser page capture requires an explicit Capture page click.",
        )

    source_url = str(
        request.get("source_url")
        or request.get("target_url")
        or request.get("declared_url")
        or ""
    ).strip()
    if not source_url:
        return _chaseos_browser_page_capture_blocked(
            vault,
            "chaseos_browser_page_declared_url_required",
            "ChaseOS-owned browser page capture requires the declared source address.",
        )
    try:
        safe_url = _validate_chaseos_browser_page_url(source_url)
    except ValueError as exc:
        return _chaseos_browser_page_capture_blocked(
            vault,
            "chaseos_browser_page_declared_url_invalid",
            str(exc),
        )

    try:
        page = (browser_provider or _capture_chaseos_owned_browser_page)(safe_url)
        if not isinstance(page, BrowserPageCapture):
            raise CaptureCollectorError("Browser page provider returned an invalid value.")
        html_relative, screenshot_relative, audit_relative = _write_chaseos_browser_page_artifacts(
            vault,
            page,
            run_id=str(request.get("run_id") or ""),
        )
        packet = capture_from_controlled_browser_artifact(
            file_path=html_relative,
            vault_root=vault,
            declared_url=page.source_url or safe_url,
            allowed_origin=str(request.get("allowed_origin") or "").strip() or None,
            source_selector="browser_runtime_artifact",
            title=str(request.get("title") or page.title or "").strip() or None,
            profile=str(request.get("profile") or "research_note"),
        )
        active_browser_state = save_active_browser_capture_state(
            vault,
            {
                "file_path": html_relative,
                "source_url": packet.source.source_url,
                "title": packet.title,
                "allowed_origin": str(request.get("allowed_origin") or "").strip(),
                "source_selector": "browser_runtime_artifact",
            },
        )
    except Exception as exc:
        return _chaseos_browser_page_capture_blocked(
            vault,
            "chaseos_browser_page_capture_failed",
            str(exc),
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_chaseos_browser_page_for_markdown",
        "status": "chaseos_browser_page_ready_for_markdown",
        "source_mode": "controlled_html_artifact",
        "title": packet.title,
        "file_path": packet.source.declared_source,
        "source_url": packet.source.source_url,
        "source_app": packet.source.source_app,
        "capture_method": packet.capture_method,
        "screenshot_path": screenshot_relative,
        "audit_path": audit_relative,
        "active_browser_state_path": active_browser_state.get("state_relative_path") or "",
        "extracted_text_preview": packet.content.raw_extracted_text[:500],
        "write_performed": True,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_chaseos_browser_page_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "launches_chaseos_owned_isolated_browser": True,
            "reads_chaseos_owned_browser_page": True,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "writes_controlled_browser_artifact": True,
            "writes_chaseos_active_browser_state": True,
            "writes_screenshot_evidence": bool(screenshot_relative),
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def _task_matches_live_discord_request(task: dict[str, Any], request: dict[str, Any]) -> bool:
    ingress = task.get("ingress_context") if isinstance(task.get("ingress_context"), dict) else {}
    if str(ingress.get("source_platform") or "").lower() != "discord":
        return False
    task_id = str(request.get("task_id") or "").strip()
    if task_id and str(task.get("task_id") or task.get("id") or "") != task_id:
        return False
    origin_message_id = str(request.get("origin_message_id") or "").strip()
    if origin_message_id and str(ingress.get("origin_message_id") or "") != origin_message_id:
        return False
    conversation_key = str(request.get("conversation_key") or "").strip()
    if conversation_key and str(ingress.get("conversation_key") or "") != conversation_key:
        return False
    return True


def _latest_live_discord_task(vault: Path, request: dict[str, Any]) -> dict[str, Any] | None:
    from runtime.agent_bus import bus

    candidates = [
        task
        for task in bus.list_tasks(vault)
        if isinstance(task, dict) and _task_matches_live_discord_request(task, request)
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda task: str(
            task.get("updated_at")
            or task.get("created_at")
            or task.get("created_at_utc")
            or ""
        ),
        reverse=True,
    )
    return candidates[0]


def _live_discord_task_markdown(task: dict[str, Any], title: str) -> tuple[str, str]:
    ingress = task.get("ingress_context") if isinstance(task.get("ingress_context"), dict) else {}
    task_id = str(task.get("task_id") or task.get("id") or "").strip()
    conversation_key = str(ingress.get("conversation_key") or "").strip()
    source_channel_id = str(ingress.get("source_channel_id") or "").strip()
    source_thread_id = str(ingress.get("source_thread_id") or "").strip()
    origin_message_id = str(ingress.get("origin_message_id") or "").strip()
    declared_source = conversation_key or (
        f"discord:{source_channel_id}:{source_thread_id}"
        if source_thread_id
        else f"discord:{source_channel_id}"
    )
    lines = [
        f"# {title}",
        "",
        "- Capture method: live Discord command via ChaseOS Agent Bus",
        f"- Task id: {task_id or 'unknown'}",
        f"- Recipient: {task.get('recipient') or 'unknown'}",
        f"- Sender: {task.get('sender') or 'unknown'}",
        f"- Priority: {task.get('priority') or 'unknown'}",
        f"- Status: {task.get('status') or 'unknown'}",
        f"- Conversation: {conversation_key or 'unknown'}",
        f"- Source channel id present: {bool(source_channel_id)}",
        f"- Source thread id present: {bool(source_thread_id)}",
        f"- Origin message id present: {bool(origin_message_id)}",
        "",
        "## Request",
        "",
        str(task.get("request") or "").strip() or "(empty)",
        "",
        "## Expected Output",
        "",
        str(task.get("expected_output") or "").strip() or "(empty)",
    ]
    notes = str(task.get("notes") or "").strip()
    if notes:
        lines.extend(["", "## Notes", "", notes])
    return "\n".join(lines).strip(), declared_source


def capture_live_discord_command_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Import a Discord-origin Agent Bus command for Capture without saving Markdown."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("live_discord_command_capture_enabled"):
        return _live_discord_command_capture_blocked(
            vault,
            "live_discord_command_capture_disabled_in_settings",
            "Live Discord command capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _live_discord_command_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Live Discord command capture requires an explicit Capture page click.",
        )

    task = _latest_live_discord_task(vault, request)
    if task is None:
        return _live_discord_command_capture_blocked(
            vault,
            "discord_agent_bus_task_not_found",
            "No matching Discord-origin Agent Bus command was found.",
        )

    title = str(request.get("title") or "").strip() or "Live Discord Command Capture"
    raw_text, declared_source = _live_discord_task_markdown(task, title)
    task_id = str(task.get("task_id") or task.get("id") or "").strip()
    ingress = task.get("ingress_context") if isinstance(task.get("ingress_context"), dict) else {}
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_live_discord_command_for_markdown",
        "status": "live_discord_command_ready_for_markdown",
        "source_mode": "manual_text",
        "title": title,
        "raw_text": raw_text,
        "task_id": task_id,
        "declared_source": declared_source,
        "conversation_key": str(ingress.get("conversation_key") or ""),
        "source_app": "discord-agent-bus",
        "capture_method": "live_discord_command_ingress",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": live_discord_command_capture_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "reads_chaseos_agent_bus_discord_ingress": True,
            "calls_discord_api": False,
            "reads_discord_token": False,
            "reads_discord_webhook": False,
            "reads_discord_bindings": False,
            "direct_discord_event_listener": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def capture_discord_artifact_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an explicit Discord artifact for the Capture page without saving Markdown."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("discord_artifact_capture_enabled"):
        return _discord_artifact_capture_blocked(
            vault,
            "discord_artifact_capture_disabled_in_settings",
            "Discord artifact capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _discord_artifact_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Discord artifact capture requires an explicit Capture page click.",
        )

    file_path = str(request.get("file_path") or "").strip()
    declared_source = str(
        request.get("declared_source")
        or request.get("discord_source")
        or request.get("source_url")
        or request.get("channel_name")
        or ""
    ).strip()
    if not file_path:
        return _discord_artifact_capture_blocked(
            vault,
            "discord_artifact_file_required",
            "Discord artifact capture requires an explicit vault-local artifact path.",
        )
    if not declared_source:
        return _discord_artifact_capture_blocked(
            vault,
            "discord_artifact_declared_source_required",
            "Discord artifact capture requires the declared Discord source.",
        )

    try:
        artifact_path, relative_path = _validate_discord_artifact_path(vault, file_path)
        extracted_text = _extract_discord_artifact_text(artifact_path)
    except Exception as exc:
        return _discord_artifact_capture_blocked(
            vault,
            "discord_artifact_validation_failed",
            str(exc),
        )

    title = str(request.get("title") or "").strip() or "Discord Artifact Capture"
    raw_text = (
        f"# {title}\n\n"
        f"- Declared Discord source: {declared_source}\n"
        f"- Source artifact: {relative_path}\n"
        "- Capture method: explicit ChaseOS Discord artifact\n\n"
        f"{extracted_text}"
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_discord_artifact_for_markdown",
        "status": "discord_artifact_ready_for_markdown",
        "source_mode": "manual_text",
        "title": title,
        "raw_text": raw_text,
        "file_path": relative_path,
        "declared_source": declared_source,
        "source_app": "discord-artifact",
        "capture_method": "controlled_discord_artifact",
        "extracted_text_preview": extracted_text[:500],
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_discord_artifact_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "reads_chaseos_owned_discord_artifact": True,
            "calls_discord_api": False,
            "reads_discord_token": False,
            "reads_discord_webhook": False,
            "reads_discord_bindings": False,
            "listens_to_discord_events": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def capture_clipboard_text_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    text_provider: ClipboardTextProvider | None = None,
) -> dict[str, Any]:
    """Read current clipboard text for the Capture page without saving Markdown."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("clipboard_capture_enabled"):
        return _clipboard_capture_blocked(
            vault,
            "clipboard_capture_disabled_in_settings",
            "Clipboard text capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _clipboard_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Clipboard text capture requires an explicit Capture page click.",
        )

    clipboard = (text_provider or _read_windows_clipboard_text)()
    if not isinstance(clipboard, ClipboardText):
        raise CaptureCollectorError("Clipboard text provider returned an invalid value.")
    raw_text = str(clipboard.content or "")
    if not raw_text.strip():
        return _clipboard_capture_blocked(
            vault,
            "clipboard_text_empty",
            "Clipboard text capture found no text content.",
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_clipboard_text_for_markdown",
        "status": "clipboard_text_ready_for_markdown",
        "source_mode": "manual_text",
        "title": str(request.get("title") or "Clipboard Capture").strip() or "Clipboard Capture",
        "raw_text": raw_text,
        "source": clipboard.source,
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_clipboard_text_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "reads_clipboard_text": True,
            "reads_clipboard_on_settings_load": False,
            "reads_clipboard_on_capture_panel_load": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "reads_active_browser_tab": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def poll_ambient_clipboard_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    text_provider: ClipboardTextProvider | None = None,
) -> dict[str, Any]:
    """Poll clipboard text during an explicit privacy-gated monitor session."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("ambient_clipboard_monitoring_enabled"):
        return _ambient_clipboard_capture_blocked(
            vault,
            "ambient_clipboard_monitoring_disabled_in_settings",
            "Ambient clipboard monitoring is disabled in Settings.",
        )
    if not bool(request.get("monitoring_session_confirmed") or request.get("operator_confirmed")):
        return _ambient_clipboard_capture_blocked(
            vault,
            "ambient_clipboard_monitoring_session_required",
            "Ambient clipboard monitoring requires an explicit monitoring session.",
        )

    clipboard = (text_provider or _read_windows_clipboard_text)()
    if not isinstance(clipboard, ClipboardText):
        raise CaptureCollectorError("Clipboard text provider returned an invalid value.")
    raw_text = str(clipboard.content or "")
    if not raw_text.strip():
        return _ambient_clipboard_capture_blocked(
            vault,
            "ambient_clipboard_text_empty",
            "Ambient clipboard monitoring found no text content.",
        )

    now = _now_utc()
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    retention_limit = _ambient_clipboard_retention_limit(
        request.get("retention_limit") or settings.get("ambient_clipboard_retention_limit")
    )
    state = _read_ambient_clipboard_state(vault)
    entries = [
        entry
        for entry in state.get("entries", [])
        if isinstance(entry, dict) and entry.get("sha256")
    ]
    duplicate_of_latest = bool(entries and entries[0].get("sha256") == digest)
    if not duplicate_of_latest:
        entries.insert(
            0,
            {
                "captured_at_utc": now,
                "source": clipboard.source,
                "sha256": digest,
                "char_count": len(raw_text),
                "text": raw_text,
            },
        )
    entries = entries[:retention_limit]
    state = {
        "schema_version": MODEL_VERSION,
        "updated_at_utc": now,
        "retention_limit": retention_limit,
        "latest_sha256": digest,
        "entry_count": len(entries),
        "entries": entries,
    }
    _write_ambient_clipboard_state(vault, state)

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "poll_ambient_clipboard_for_markdown",
        "status": (
            "ambient_clipboard_latest_unchanged"
            if duplicate_of_latest
            else "ambient_clipboard_text_ready_for_markdown"
        ),
        "source_mode": "manual_text",
        "title": str(request.get("title") or "Ambient Clipboard Capture").strip()
        or "Ambient Clipboard Capture",
        "raw_text": raw_text,
        "source": clipboard.source,
        "state_path": str(ambient_clipboard_monitor_state_path(vault)),
        "state_relative_path": _relative_to_vault(
            vault, ambient_clipboard_monitor_state_path(vault)
        ),
        "entry_count": len(entries),
        "retention_limit": retention_limit,
        "duplicate_of_latest": duplicate_of_latest,
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "writes_state_ring_buffer": True,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": ambient_clipboard_monitor_policy(),
        "authority": {
            "settings_enabled": True,
            "monitoring_session_confirmed": True,
            "reads_clipboard_text": True,
            "reads_clipboard_on_settings_load": False,
            "reads_clipboard_on_capture_panel_load": False,
            "writes_state_ring_buffer": True,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def get_ambient_clipboard_monitor_state(vault_root: str | Path) -> dict[str, Any]:
    """Return ambient clipboard monitor state without reading the clipboard."""

    vault = Path(vault_root).resolve()
    state = _read_ambient_clipboard_state(vault)
    entries = [
        {
            "captured_at_utc": str(entry.get("captured_at_utc") or ""),
            "source": str(entry.get("source") or ""),
            "sha256": str(entry.get("sha256") or ""),
            "char_count": int(entry.get("char_count") or 0),
            "preview": str(entry.get("text") or "")[:180],
        }
        for entry in state.get("entries", [])
        if isinstance(entry, dict)
    ]
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "get_ambient_clipboard_monitor_state",
        "status": "ambient_clipboard_state_loaded",
        "state_path": str(ambient_clipboard_monitor_state_path(vault)),
        "state_relative_path": _relative_to_vault(vault, ambient_clipboard_monitor_state_path(vault)),
        "entry_count": len(entries),
        "retention_limit": _ambient_clipboard_retention_limit(state.get("retention_limit")),
        "entries": entries,
        "authority": {
            "reads_clipboard_text": False,
            "reads_state_only": True,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def clear_ambient_clipboard_monitor_state(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Clear the local ambient clipboard ring buffer after exact confirmation."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    phrase = str(request.get("confirmation_phrase") or "").strip()
    if phrase != "CLEAR AMBIENT CLIPBOARD":
        return _ambient_clipboard_capture_blocked(
            vault,
            "ambient_clipboard_clear_confirmation_required",
            "Ambient clipboard monitor state cleanup requires exact confirmation.",
        )
    path = ambient_clipboard_monitor_state_path(vault)
    if path.exists():
        path.unlink()
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "clear_ambient_clipboard_monitor_state",
        "status": "ambient_clipboard_state_cleared",
        "state_path": str(path),
        "state_relative_path": _relative_to_vault(vault, path),
        "write_performed": True,
        "authority": {
            "clears_local_studio_state_only": True,
            "reads_clipboard_text": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def capture_selected_text_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    text_provider: SelectedTextProvider | None = None,
) -> dict[str, Any]:
    """Copy selected text from the foreground app for the Capture page without saving Markdown."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("selected_text_capture_enabled"):
        return _selected_text_capture_blocked(
            vault,
            "selected_text_capture_disabled_in_settings",
            "Selected-text capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _selected_text_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Selected-text capture requires an explicit Capture page click or configured shortcut.",
        )

    selected = (text_provider or _read_windows_selected_text)()
    if not isinstance(selected, SelectedText):
        raise CaptureCollectorError("Selected-text provider returned an invalid value.")
    raw_text = str(selected.content or "")
    if not raw_text.strip():
        return _selected_text_capture_blocked(
            vault,
            "selected_text_empty",
            "Selected-text capture found no selected text content.",
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_selected_text_for_markdown",
        "status": "selected_text_ready_for_markdown",
        "source_mode": "manual_text",
        "title": str(request.get("title") or "Selected Text Capture").strip()
        or "Selected Text Capture",
        "raw_text": raw_text,
        "source": selected.source,
        "window": {
            "title": selected.window_title,
            "process_id": int(selected.process_id),
        },
        "clipboard_restored": bool(selected.clipboard_restored),
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_selected_text_policy(),
        "authority": {
            "operator_click_or_shortcut_confirmed": True,
            "settings_enabled": True,
            "reads_selected_text": True,
            "uses_temporary_clipboard_copy": True,
            "restores_text_clipboard_when_possible": bool(selected.clipboard_restored),
            "reads_clipboard_on_settings_load": False,
            "reads_clipboard_on_capture_panel_load": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "reads_active_window_metadata": True,
            "reads_active_browser_tab": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def capture_accessibility_tree_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    tree_provider: AccessibilityTreeProvider | None = None,
) -> dict[str, Any]:
    """Read foreground app accessibility text for the Capture page without saving Markdown."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("accessibility_tree_capture_enabled"):
        return _accessibility_tree_capture_blocked(
            vault,
            "accessibility_tree_capture_disabled_in_settings",
            "Accessibility tree capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _accessibility_tree_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Accessibility tree capture requires an explicit Capture page click or configured shortcut.",
        )

    captured = (tree_provider or _read_windows_accessibility_tree)()
    if not isinstance(captured, AccessibilityTreeCapture):
        raise CaptureCollectorError("Accessibility tree provider returned an invalid value.")
    raw_text = str(captured.text or "")
    if not raw_text.strip():
        return _accessibility_tree_capture_blocked(
            vault,
            "accessibility_tree_empty",
            "Accessibility tree capture found no readable text.",
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_accessibility_tree_for_markdown",
        "status": "accessibility_tree_ready_for_markdown",
        "source_mode": "manual_text",
        "title": str(request.get("title") or "Accessibility Tree Capture").strip()
        or "Accessibility Tree Capture",
        "raw_text": raw_text,
        "source": captured.source,
        "window": {
            "title": captured.window_title,
            "process_id": int(captured.process_id),
        },
        "node_count": int(captured.node_count),
        "roles": list(captured.roles),
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_accessibility_tree_policy(),
        "authority": {
            "operator_click_or_shortcut_confirmed": True,
            "settings_enabled": True,
            "reads_accessibility_tree": True,
            "reads_accessibility_tree_on_settings_load": False,
            "reads_accessibility_tree_on_capture_panel_load": False,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "reads_active_window_metadata": True,
            "reads_active_browser_tab": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": [],
    }


def capture_current_screen_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    image_provider: ScreenCaptureProvider | None = None,
) -> dict[str, Any]:
    """Capture the current screen as explicit evidence for the Capture page.

    This writes a screenshot evidence file and audit JSON only. It does not
    save Capture Markdown; the caller must still preview or save through the
    normal Capture to Markdown quarantine flow.
    """

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("screen_capture_enabled"):
        return _screen_capture_blocked(
            vault,
            "screen_capture_disabled_in_settings",
            "Screen capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _screen_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Screen capture requires an explicit Capture page click.",
        )

    run_id = _safe_run_id(str(request.get("run_id") or ""))
    image = (image_provider or _capture_primary_screen_png)()
    if not isinstance(image, ScreenCaptureImage):
        raise CaptureCollectorError("Screen capture provider returned an invalid image.")
    if not image.png_bytes:
        raise CaptureCollectorError("Screen capture returned no image bytes.")

    evidence_dir = vault / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = _collision_safe_path(evidence_dir / f"{run_id}-screen.png")
    screenshot_path.write_bytes(image.png_bytes)
    digest = hashlib.sha256(image.png_bytes).hexdigest()

    attachment = build_screenshot_attachment(screenshot_path, vault_root=vault)
    audit_path = screenshot_path.with_suffix(".json")
    audit = {
        "schema_version": MODEL_VERSION,
        "surface": SURFACE_ID,
        "status": "screen_capture_ready_for_markdown",
        "captured_at_utc": _now_utc(),
        "run_id": run_id,
        "screenshot_path": str(screenshot_path),
        "screenshot_relative_path": _relative_to_vault(vault, screenshot_path),
        "screenshot_sha256": digest,
        "size_bytes": len(image.png_bytes),
        "width": image.width,
        "height": image.height,
        "source": image.source,
        "policy": explicit_screen_capture_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "writes_screenshot_evidence": True,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "reads_active_browser_tab": False,
            "reads_ambient_clipboard": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    relative_screenshot = _relative_to_vault(vault, screenshot_path)
    relative_audit = _relative_to_vault(vault, audit_path)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_current_screen_for_markdown",
        "status": "screen_capture_ready_for_markdown",
        "source_mode": "screenshot_attachment",
        "title": str(request.get("title") or "Screen Capture").strip() or "Screen Capture",
        "file_path": relative_screenshot,
        "screenshot": {
            "path": str(screenshot_path),
            "relative_path": relative_screenshot,
            "sha256": digest,
            "size_bytes": len(image.png_bytes),
            "width": image.width,
            "height": image.height,
            "attachment": attachment.attachment.to_dict(),
        },
        "audit_path": str(audit_path),
        "audit_relative_path": relative_audit,
        "write_performed": True,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_screen_capture_policy(),
        "authority": audit["authority"],
        "blockers": [],
    }


def capture_display_region_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    region_provider: DisplayRegionProvider | None = None,
) -> dict[str, Any]:
    """Drag-select a display region and prepare it for Markdown extraction.

    The collector writes only image evidence and audit JSON. Text extraction and
    Markdown creation remain in the normal Capture to Markdown preview/save flow.
    """

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("display_region_capture_enabled"):
        return _display_region_capture_blocked(
            vault,
            "display_region_capture_disabled_in_settings",
            "Display region capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _display_region_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Display region capture requires a Capture page click or configured Studio shortcut.",
        )

    run_id = _safe_run_id(str(request.get("run_id") or ""))
    region = (region_provider or _select_display_region_capture)()
    if not isinstance(region, DisplayRegionCapture):
        raise CaptureCollectorError("Display region provider returned an invalid region.")
    image = region.image
    if not isinstance(image, ScreenCaptureImage):
        raise CaptureCollectorError("Display region provider returned an invalid image.")
    if not image.png_bytes:
        raise CaptureCollectorError("Display region capture returned no image bytes.")
    if region.width <= 0 or region.height <= 0:
        raise CaptureCollectorError("Display region capture returned an empty rectangle.")

    evidence_dir = vault / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = _collision_safe_path(evidence_dir / f"{run_id}-display-region.png")
    screenshot_path.write_bytes(image.png_bytes)
    digest = hashlib.sha256(image.png_bytes).hexdigest()

    attachment = build_screenshot_attachment(screenshot_path, vault_root=vault)
    audit_path = screenshot_path.with_suffix(".json")
    audit = {
        "schema_version": MODEL_VERSION,
        "surface": SURFACE_ID,
        "status": "display_region_capture_ready_for_markdown",
        "captured_at_utc": _now_utc(),
        "run_id": run_id,
        "screenshot_path": str(screenshot_path),
        "screenshot_relative_path": _relative_to_vault(vault, screenshot_path),
        "screenshot_sha256": digest,
        "size_bytes": len(image.png_bytes),
        "width": image.width,
        "height": image.height,
        "source": image.source,
        "region": {
            "x": int(region.x),
            "y": int(region.y),
            "width": int(region.width),
            "height": int(region.height),
        },
        "policy": explicit_display_region_capture_policy(),
        "authority": {
            "operator_click_or_shortcut_confirmed": True,
            "operator_drag_select_confirmed": True,
            "settings_enabled": True,
            "writes_screenshot_evidence": True,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "reads_active_browser_tab": False,
            "reads_ambient_clipboard": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    relative_screenshot = _relative_to_vault(vault, screenshot_path)
    relative_audit = _relative_to_vault(vault, audit_path)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_display_region_for_markdown",
        "status": "display_region_capture_ready_for_markdown",
        "source_mode": "screenshot_text_extraction",
        "title": str(request.get("title") or "Display Region Capture").strip()
        or "Display Region Capture",
        "file_path": relative_screenshot,
        "screenshot": {
            "path": str(screenshot_path),
            "relative_path": relative_screenshot,
            "sha256": digest,
            "size_bytes": len(image.png_bytes),
            "width": image.width,
            "height": image.height,
            "attachment": attachment.attachment.to_dict(),
        },
        "region": audit["region"],
        "audit_path": str(audit_path),
        "audit_relative_path": relative_audit,
        "write_performed": True,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_display_region_capture_policy(),
        "authority": audit["authority"],
        "blockers": [],
    }


def capture_active_window_for_markdown(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
    *,
    window_provider: ActiveWindowProvider | None = None,
) -> dict[str, Any]:
    """Capture the current foreground window as explicit Capture evidence."""

    vault = Path(vault_root).resolve()
    request = payload or {}
    settings = load_capture_collector_settings(vault)
    if not settings.get("active_window_capture_enabled"):
        return _active_window_capture_blocked(
            vault,
            "active_window_capture_disabled_in_settings",
            "Active window capture is disabled in Settings.",
        )
    if not bool(request.get("operator_confirmed")):
        return _active_window_capture_blocked(
            vault,
            "operator_confirmation_required",
            "Active window capture requires a Capture page click or configured Studio shortcut.",
        )

    run_id = _safe_run_id(str(request.get("run_id") or ""))
    captured = (window_provider or _capture_active_window)()
    if not isinstance(captured, ActiveWindowCapture):
        raise CaptureCollectorError("Active window provider returned an invalid capture.")
    image = captured.image
    if not isinstance(image, ScreenCaptureImage):
        raise CaptureCollectorError("Active window provider returned an invalid image.")
    if not image.png_bytes:
        raise CaptureCollectorError("Active window capture returned no image bytes.")
    if captured.width <= 0 or captured.height <= 0:
        raise CaptureCollectorError("Active window capture returned an empty rectangle.")

    evidence_dir = vault / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = _collision_safe_path(evidence_dir / f"{run_id}-active-window.png")
    screenshot_path.write_bytes(image.png_bytes)
    digest = hashlib.sha256(image.png_bytes).hexdigest()
    attachment = build_screenshot_attachment(screenshot_path, vault_root=vault)
    audit_path = screenshot_path.with_suffix(".json")
    audit = {
        "schema_version": MODEL_VERSION,
        "surface": SURFACE_ID,
        "status": "active_window_capture_ready_for_markdown",
        "captured_at_utc": _now_utc(),
        "run_id": run_id,
        "screenshot_path": str(screenshot_path),
        "screenshot_relative_path": _relative_to_vault(vault, screenshot_path),
        "screenshot_sha256": digest,
        "size_bytes": len(image.png_bytes),
        "width": image.width,
        "height": image.height,
        "source": image.source,
        "window": {
            "title": captured.window_title,
            "process_id": int(captured.process_id),
            "x": int(captured.x),
            "y": int(captured.y),
            "width": int(captured.width),
            "height": int(captured.height),
        },
        "policy": explicit_active_window_capture_policy(),
        "authority": {
            "operator_click_or_shortcut_confirmed": True,
            "settings_enabled": True,
            "reads_active_window_metadata": True,
            "writes_screenshot_evidence": True,
            "writes_raw_quarantine_markdown": False,
            "registers_global_hotkeys": False,
            "reads_active_browser_tab": False,
            "reads_ambient_clipboard": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    relative_screenshot = _relative_to_vault(vault, screenshot_path)
    relative_audit = _relative_to_vault(vault, audit_path)
    title = str(request.get("title") or "").strip() or captured.window_title or "Active Window Capture"
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "capture_active_window_for_markdown",
        "status": "active_window_capture_ready_for_markdown",
        "source_mode": "screenshot_text_extraction",
        "title": title,
        "file_path": relative_screenshot,
        "screenshot": {
            "path": str(screenshot_path),
            "relative_path": relative_screenshot,
            "sha256": digest,
            "size_bytes": len(image.png_bytes),
            "width": image.width,
            "height": image.height,
            "attachment": attachment.attachment.to_dict(),
        },
        "window": audit["window"],
        "audit_path": str(audit_path),
        "audit_relative_path": relative_audit,
        "write_performed": True,
        "writes_raw_quarantine_markdown": False,
        "next_action": "preview_or_save_capture_to_markdown",
        "policy": explicit_active_window_capture_policy(),
        "authority": audit["authority"],
        "blockers": [],
    }


def _screen_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_current_screen_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_screen_capture_policy(),
    }


def _display_region_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_display_region_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_display_region_capture_policy(),
    }


def _active_window_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_active_window_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_active_window_capture_policy(),
    }


def _clipboard_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_clipboard_text_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_clipboard_text_policy(),
    }


def _ambient_clipboard_capture_blocked(
    vault: Path, blocker: str, message: str
) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "poll_ambient_clipboard_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "state_path": str(ambient_clipboard_monitor_state_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": ambient_clipboard_monitor_policy(),
    }


def _selected_text_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_selected_text_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_selected_text_policy(),
    }


def _accessibility_tree_capture_blocked(
    vault: Path, blocker: str, message: str
) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_accessibility_tree_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_accessibility_tree_policy(),
    }


def _browser_extension_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_browser_extension_artifact_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_browser_extension_capture_policy(),
    }


def _browser_artifact_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_browser_artifact_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_browser_artifact_policy(),
    }


def _active_chaseos_browser_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_active_chaseos_browser_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "state_path": str(active_browser_capture_state_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_active_chaseos_browser_policy(),
    }


def _chaseos_browser_page_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_chaseos_browser_page_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_chaseos_browser_page_policy(),
    }


def _discord_artifact_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_discord_artifact_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": explicit_discord_artifact_policy(),
    }


def _live_discord_command_capture_blocked(vault: Path, blocker: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "action": "capture_live_discord_command_for_markdown",
        "status": "blocked",
        "write_performed": False,
        "writes_raw_quarantine_markdown": False,
        "settings_path": str(capture_collector_settings_path(vault)),
        "blockers": [blocker],
        "message": message,
        "policy": live_discord_command_capture_policy(),
    }


def _validate_chaseos_browser_page_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("ChaseOS-owned browser page capture requires an http or https address.")
    if not parsed.netloc:
        raise ValueError("ChaseOS-owned browser page capture requires a host in the source address.")
    return source_url


def _capture_chaseos_owned_browser_page(source_url: str) -> BrowserPageCapture:
    from runtime.browser_runtime.cdp_live import IsolatedBrowserLauncher, MinimalCDPClient

    launcher = IsolatedBrowserLauncher(headless=True, timeout_seconds=20)
    client = MinimalCDPClient(timeout_seconds=20)
    try:
        launched = launcher.launch()
        endpoint = str(launched.get("cdp_endpoint") or "")
        client.connect(endpoint)
        client.navigate(source_url)
        state = client.read_state()
        screenshot = client.capture_screenshot()
        title = str(state.get("title") or "").strip() or source_url
        visible_text = str(state.get("visible_text") or "").strip()
        dom = state.get("dom_snapshot") if isinstance(state.get("dom_snapshot"), dict) else {}
        html = str(dom.get("outer_html_preview") or "").strip()
        if not html:
            html = _html_from_browser_page_capture(title, source_url, visible_text)
        return BrowserPageCapture(
            title=title,
            source_url=str(state.get("url") or source_url),
            visible_text=visible_text,
            html=html,
            screenshot_png=screenshot,
            source="chaseos_owned_isolated_cdp_browser",
        )
    finally:
        client.close()
        launcher.close()


def _html_from_browser_page_capture(title: str, source_url: str, visible_text: str) -> str:
    escaped_title = _html_escape(title or source_url)
    escaped_text = _html_escape(visible_text or "")
    return (
        "<!doctype html><html><head>"
        f"<title>{escaped_title}</title>"
        "</head><body>"
        f"<main><pre>{escaped_text}</pre></main>"
        "</body></html>"
    )


def _html_escape(value: str) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _write_chaseos_browser_page_artifacts(
    vault: Path,
    page: BrowserPageCapture,
    *,
    run_id: str,
) -> tuple[str, str, str]:
    safe_run = _safe_run_id(run_id)
    artifact_dir = vault / "07_LOGS" / "Browser-Runs" / "Capture-to-Markdown"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    html_path = _collision_safe_path(artifact_dir / f"{safe_run}-browser-page.html")
    screenshot_path = _collision_safe_path(artifact_dir / f"{safe_run}-browser-page.png")
    audit_path = _collision_safe_path(artifact_dir / f"{safe_run}-browser-page.json")

    html = page.html.strip() or _html_from_browser_page_capture(
        page.title,
        page.source_url,
        page.visible_text,
    )
    html_path.write_text(html, encoding="utf-8")
    screenshot_relative = ""
    screenshot_sha256 = ""
    if page.screenshot_png:
        screenshot_path.write_bytes(page.screenshot_png)
        screenshot_relative = _relative_to_vault(vault, screenshot_path)
        screenshot_sha256 = hashlib.sha256(page.screenshot_png).hexdigest()

    audit = {
        "schema_version": MODEL_VERSION,
        "surface": SURFACE_ID,
        "status": "chaseos_browser_page_ready_for_markdown",
        "captured_at_utc": _now_utc(),
        "run_id": safe_run,
        "title": page.title,
        "source_url": page.source_url,
        "source": page.source,
        "html_relative_path": _relative_to_vault(vault, html_path),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "screenshot_relative_path": screenshot_relative,
        "screenshot_sha256": screenshot_sha256,
        "visible_text_char_count": len(page.visible_text or ""),
        "policy": explicit_chaseos_browser_page_policy(),
        "authority": {
            "operator_click_confirmed": True,
            "settings_enabled": True,
            "launches_chaseos_owned_isolated_browser": True,
            "reads_chaseos_owned_browser_page": True,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "writes_controlled_browser_artifact": True,
            "writes_raw_quarantine_markdown": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
        },
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    return (
        _relative_to_vault(vault, html_path),
        screenshot_relative,
        _relative_to_vault(vault, audit_path),
    )


def _read_windows_clipboard_text() -> ClipboardText:
    if os.name != "nt":
        raise CaptureCollectorError("Clipboard text capture is only implemented for Windows in this pass.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    cf_unicode_text = 13

    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    user32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
    user32.IsClipboardFormatAvailable.restype = ctypes.c_bool
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.restype = ctypes.c_bool
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool

    if not user32.OpenClipboard(None):
        raise CaptureCollectorError("Clipboard text capture could not open the clipboard.")
    try:
        if not user32.IsClipboardFormatAvailable(cf_unicode_text):
            return ClipboardText(content="", source="windows_clipboard")
        handle = user32.GetClipboardData(cf_unicode_text)
        if not handle:
            raise CaptureCollectorError("Clipboard text capture could not read clipboard data.")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise CaptureCollectorError("Clipboard text capture could not lock clipboard data.")
        try:
            return ClipboardText(content=ctypes.wstring_at(pointer), source="windows_clipboard")
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def _write_windows_clipboard_text(content: str) -> None:
    if os.name != "nt":
        raise CaptureCollectorError("Clipboard restore is only implemented for Windows in this pass.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    cf_unicode_text = 13
    gmem_moveable = 0x0002
    data = (str(content or "") + "\0").encode("utf-16le")

    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    user32.EmptyClipboard.restype = ctypes.c_bool
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.restype = ctypes.c_bool
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p

    if not user32.OpenClipboard(None):
        raise CaptureCollectorError("Selected-text capture could not open the clipboard for restore.")
    handle = None
    transferred = False
    try:
        if not user32.EmptyClipboard():
            raise CaptureCollectorError("Selected-text capture could not prepare clipboard restore.")
        handle = kernel32.GlobalAlloc(gmem_moveable, len(data))
        if not handle:
            raise CaptureCollectorError("Selected-text capture could not allocate clipboard restore data.")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise CaptureCollectorError("Selected-text capture could not lock clipboard restore data.")
        try:
            ctypes.memmove(pointer, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(cf_unicode_text, handle):
            raise CaptureCollectorError("Selected-text capture could not restore clipboard text.")
        transferred = True
    finally:
        user32.CloseClipboard()
        if handle and not transferred:
            kernel32.GlobalFree(handle)


def _active_window_text_metadata() -> tuple[str, int]:
    if os.name != "nt":
        return "", 0
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "", 0
    user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
    length = int(user32.GetWindowTextLengthW(hwnd))
    buffer = ctypes.create_unicode_buffer(max(length + 1, 2))
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    process_id = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    return str(buffer.value or ""), int(process_id.value)


def _read_windows_selected_text() -> SelectedText:
    if os.name != "nt":
        raise CaptureCollectorError("Selected-text capture is only implemented for Windows in this pass.")

    window_title, process_id = _active_window_text_metadata()
    try:
        previous_clipboard = _read_windows_clipboard_text().content
    except Exception:
        previous_clipboard = ""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    vk_control = 0x11
    vk_c = 0x43
    keyeventf_keyup = 0x0002
    user32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ulong, ctypes.c_void_p]
    user32.keybd_event.restype = None
    user32.keybd_event(vk_control, 0, 0, None)
    user32.keybd_event(vk_c, 0, 0, None)
    user32.keybd_event(vk_c, 0, keyeventf_keyup, None)
    user32.keybd_event(vk_control, 0, keyeventf_keyup, None)

    captured = ""
    for _ in range(10):
        time.sleep(0.08)
        try:
            captured = _read_windows_clipboard_text().content
        except Exception:
            captured = ""
        if captured.strip():
            break

    clipboard_restored = False
    try:
        _write_windows_clipboard_text(previous_clipboard)
        clipboard_restored = True
    except Exception:
        clipboard_restored = False

    return SelectedText(
        content=captured,
        source="windows_selected_text_via_temporary_clipboard_copy",
        window_title=window_title,
        process_id=process_id,
        clipboard_restored=clipboard_restored,
    )


def _read_windows_accessibility_tree() -> AccessibilityTreeCapture:
    if os.name != "nt":
        raise CaptureCollectorError(
            "Accessibility tree capture is only implemented for Windows in this pass."
        )

    window_title, process_id = _active_window_text_metadata()
    script = r"""
Add-Type -AssemblyName UIAutomationClient
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class ChaseOSUser32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
}
"@
$hwnd = [ChaseOSUser32]::GetForegroundWindow()
if ($hwnd -eq [IntPtr]::Zero) {
    throw "No foreground window is available for accessibility tree capture."
}
$root = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
if ($null -eq $root) {
    throw "Foreground window did not expose an accessibility root."
}
$nodes = $root.FindAll(
    [System.Windows.Automation.TreeScope]::Subtree,
    [System.Windows.Automation.Condition]::TrueCondition
)
$limit = [Math]::Min([int]$nodes.Count, 250)
$items = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt $limit; $i++) {
    $node = $nodes.Item($i)
    if ($null -eq $node) { continue }
    $current = $node.Current
    $name = [string]$current.Name
    $controlType = ""
    if ($null -ne $current.ControlType) {
        $controlType = ([string]$current.ControlType.ProgrammaticName) -replace '^ControlType\.', ''
    }
    $className = [string]$current.ClassName
    $automationId = [string]$current.AutomationId
    if ([string]::IsNullOrWhiteSpace($name) -and [string]::IsNullOrWhiteSpace($controlType) -and [string]::IsNullOrWhiteSpace($className) -and [string]::IsNullOrWhiteSpace($automationId)) {
        continue
    }
    $items.Add([pscustomobject]@{
        name = $name
        role = $controlType
        class_name = $className
        automation_id = $automationId
    }) | Out-Null
}
[pscustomobject]@{
    node_count = [int]$nodes.Count
    captured_node_count = [int]$items.Count
    items = $items
} | ConvertTo-Json -Depth 4 -Compress
"""
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "-",
        ],
        input=script,
        text=True,
        capture_output=True,
        timeout=8,
        check=False,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "").strip()
        raise CaptureCollectorError(
            f"Accessibility tree capture failed through Windows automation: {stderr}"
        )
    try:
        payload = json.loads((completed.stdout or "").strip())
    except Exception as exc:
        raise CaptureCollectorError("Accessibility tree capture returned invalid data.") from exc

    items = payload.get("items") if isinstance(payload, dict) else []
    if isinstance(items, dict):
        items = [items]
    lines: list[str] = []
    roles: list[str] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        name = str(item.get("name") or "").strip()
        class_name = str(item.get("class_name") or "").strip()
        automation_id = str(item.get("automation_id") or "").strip()
        if role and role not in roles:
            roles.append(role)
        label = name or automation_id or class_name or role
        if not label:
            continue
        metadata = ", ".join(part for part in (class_name, automation_id) if part)
        suffix = f" [{metadata}]" if metadata else ""
        prefix = f"{role}: " if role else ""
        lines.append(f"- {prefix}{label}{suffix}")

    return AccessibilityTreeCapture(
        text="\n".join(lines),
        source="windows_ui_automation_accessibility_tree",
        window_title=window_title,
        process_id=process_id,
        node_count=int(payload.get("node_count") or len(lines)),
        roles=tuple(roles),
    )


def _resolve_allowed_browser_extension_artifact(vault: Path, file_path: str) -> Path:
    raw = str(file_path or "").strip()
    if not raw:
        raise CaptureCollectorError("Browser extension artifact path is required.")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = vault / candidate
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(vault.resolve()).as_posix()
    except ValueError as exc:
        raise CaptureCollectorError(
            "Browser extension artifact must be inside the selected vault."
        ) from exc
    normalized = relative.lower()
    if not any(
        normalized == allowed.lower() or normalized.startswith(f"{allowed.lower()}/")
        for allowed in BROWSER_EXTENSION_ARTIFACT_DIRS
    ):
        allowed = ", ".join(BROWSER_EXTENSION_ARTIFACT_DIRS)
        raise CaptureCollectorError(
            f"Browser extension artifact must be under one of: {allowed}."
        )
    if any(marker in normalized for marker in _BROWSER_EXTENSION_FORBIDDEN_PATH_MARKERS):
        raise CaptureCollectorError(
            "Browser extension artifact path appears to reference profile, cookie, history, session, credential, token, or secret data."
        )
    if resolved.suffix.lower() != ".json":
        raise CaptureCollectorError("Browser extension artifact must be a JSON file.")
    if not resolved.is_file():
        raise CaptureCollectorError("Browser extension artifact file does not exist.")
    return resolved


def _read_browser_extension_artifact(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if len(raw) > _MAX_BROWSER_EXTENSION_ARTIFACT_CHARS:
        raise CaptureCollectorError("Browser extension artifact is too large.")
    try:
        payload = json.loads(raw)
    except Exception as exc:
        raise CaptureCollectorError("Browser extension artifact is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise CaptureCollectorError("Browser extension artifact must be a JSON object.")
    schema = str(payload.get("schema_version") or "")
    if not schema.startswith("chaseos.capture.browser_extension."):
        raise CaptureCollectorError("Browser extension artifact schema is not recognized.")
    if bool(payload.get("includes_cookies") or payload.get("includes_browser_history")):
        raise CaptureCollectorError(
            "Browser extension artifact claims cookie or browser history content."
        )
    return payload


def _browser_extension_artifact_text(payload: dict[str, Any]) -> str:
    for key in ("selected_text", "visible_text", "markdown", "text_content", "body_text"):
        value = str(payload.get(key) or "")
        if value.strip():
            if len(value) > _MAX_BROWSER_EXTENSION_ARTIFACT_CHARS:
                raise CaptureCollectorError("Browser extension artifact text is too large.")
            return value
    raise CaptureCollectorError("Browser extension artifact contains no readable text.")


def _validate_browser_extension_url(url: str) -> None:
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise CaptureCollectorError("Browser extension source address must be http or https.")
    if parsed.username or parsed.password:
        raise CaptureCollectorError("Browser extension source address must not contain credentials.")
    if any(marker in parsed.query.lower() for marker in ("token", "secret", "password", "session")):
        raise CaptureCollectorError(
            "Browser extension source address query contains credential-like markers."
        )


def _select_display_region_capture() -> DisplayRegionCapture:
    if os.name != "nt":
        raise CaptureCollectorError("Display region capture is only implemented for Windows in this pass.")

    import tkinter as tk

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    virtual_x = int(user32.GetSystemMetrics(76))
    virtual_y = int(user32.GetSystemMetrics(77))
    virtual_width = int(user32.GetSystemMetrics(78))
    virtual_height = int(user32.GetSystemMetrics(79))
    if virtual_width <= 0 or virtual_height <= 0:
        virtual_x = 0
        virtual_y = 0
        virtual_width = int(user32.GetSystemMetrics(0))
        virtual_height = int(user32.GetSystemMetrics(1))
    if virtual_width <= 0 or virtual_height <= 0:
        raise CaptureCollectorError("Display region capture could not determine display size.")

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.28)
    root.configure(bg="#000000")
    root.geometry(f"{virtual_width}x{virtual_height}+{virtual_x}+{virtual_y}")
    root.cursor = "crosshair"
    canvas = tk.Canvas(root, bg="#000000", highlightthickness=0, cursor="crosshair")
    canvas.pack(fill="both", expand=True)
    canvas.create_text(
        24,
        24,
        text="Drag to capture. Esc cancels.",
        anchor="nw",
        fill="#ffffff",
        font=("Segoe UI", 13, "bold"),
    )
    state: dict[str, Any] = {"start": None, "rect": None, "selection": None, "cancelled": False}

    def on_press(event: Any) -> None:
        state["start"] = (int(event.x_root), int(event.y_root))
        if state["rect"] is not None:
            canvas.delete(state["rect"])
        state["rect"] = canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="#39e6d2",
            width=3,
            fill="#39e6d2",
            stipple="gray25",
        )

    def on_move(event: Any) -> None:
        start = state.get("start")
        rect = state.get("rect")
        if not start or rect is None:
            return
        x0 = start[0] - virtual_x
        y0 = start[1] - virtual_y
        canvas.coords(rect, x0, y0, int(event.x_root) - virtual_x, int(event.y_root) - virtual_y)

    def on_release(event: Any) -> None:
        start = state.get("start")
        if not start:
            return
        x0, y0 = start
        x1, y1 = int(event.x_root), int(event.y_root)
        left = min(x0, x1)
        top = min(y0, y1)
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        if width < 4 or height < 4:
            state["cancelled"] = True
        else:
            state["selection"] = (left, top, width, height)
        root.destroy()

    def on_cancel(_event: Any = None) -> None:
        state["cancelled"] = True
        root.destroy()

    root.bind("<ButtonPress-1>", on_press)
    root.bind("<B1-Motion>", on_move)
    root.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_cancel)
    root.focus_force()
    root.mainloop()

    if state.get("cancelled") or not state.get("selection"):
        raise CaptureCollectorError("Display region capture was cancelled.")
    left, top, width, height = state["selection"]
    image = _capture_screen_region_png(left, top, width, height)
    return DisplayRegionCapture(image=image, x=left, y=top, width=width, height=height)


def _capture_screen_region_png(x: int, y: int, width: int, height: int) -> ScreenCaptureImage:
    if os.name != "nt":
        raise CaptureCollectorError("Screen region capture is only implemented for Windows in this pass.")
    if width <= 0 or height <= 0:
        raise CaptureCollectorError("Screen region capture requires a non-empty rectangle.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    hdc_screen = user32.GetDC(None)
    if not hdc_screen:
        raise CaptureCollectorError("Screen region capture could not open the display context.")
    hdc_mem = None
    hbmp = None
    old_obj = None
    try:
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        if not hdc_mem:
            raise CaptureCollectorError("Screen region capture could not create a memory display context.")
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, int(width), int(height))
        if not hbmp:
            raise CaptureCollectorError("Screen region capture could not create a bitmap.")
        old_obj = gdi32.SelectObject(hdc_mem, hbmp)
        if not gdi32.BitBlt(hdc_mem, 0, 0, int(width), int(height), hdc_screen, int(x), int(y), 0x00CC0020):
            raise CaptureCollectorError("Screen region capture failed while copying display pixels.")

        class BitmapInfoHeader(ctypes.Structure):
            _fields_ = [
                ("biSize", ctypes.c_uint32),
                ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32),
                ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16),
                ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32),
            ]

        class BitmapInfo(ctypes.Structure):
            _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", ctypes.c_uint32 * 3)]

        bitmap_info = BitmapInfo()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        bitmap_info.bmiHeader.biWidth = int(width)
        bitmap_info.bmiHeader.biHeight = -int(height)
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = 0
        buffer = ctypes.create_string_buffer(int(width) * int(height) * 4)
        lines = gdi32.GetDIBits(hdc_mem, hbmp, 0, int(height), buffer, ctypes.byref(bitmap_info), 0)
        if int(lines) != int(height):
            raise CaptureCollectorError("Screen region capture could not read display pixels.")
        return ScreenCaptureImage(
            png_bytes=_png_from_bgra(buffer.raw, int(width), int(height)),
            width=int(width),
            height=int(height),
            source="display_region",
        )
    finally:
        if old_obj and hdc_mem:
            gdi32.SelectObject(hdc_mem, old_obj)
        if hbmp:
            gdi32.DeleteObject(hbmp)
        if hdc_mem:
            gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)


def _capture_active_window() -> ActiveWindowCapture:
    if os.name != "nt":
        raise CaptureCollectorError("Active window capture is only implemented for Windows in this pass.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise CaptureCollectorError("Active window capture could not find a foreground window.")

    class Rect(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = Rect()
    user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(Rect)]
    user32.GetWindowRect.restype = ctypes.c_bool
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise CaptureCollectorError("Active window capture could not read the foreground window rectangle.")
    width = int(rect.right - rect.left)
    height = int(rect.bottom - rect.top)
    if width <= 0 or height <= 0:
        raise CaptureCollectorError("Active window capture found an empty foreground window rectangle.")

    user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    length = int(user32.GetWindowTextLengthW(hwnd))
    buffer = ctypes.create_unicode_buffer(max(length + 1, 2))
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    process_id = ctypes.c_ulong(0)
    user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    user32.GetWindowThreadProcessId.restype = ctypes.c_ulong
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    image = _capture_screen_region_png(int(rect.left), int(rect.top), width, height)
    return ActiveWindowCapture(
        image=ScreenCaptureImage(
            png_bytes=image.png_bytes,
            width=image.width,
            height=image.height,
            source="active_window",
        ),
        x=int(rect.left),
        y=int(rect.top),
        width=width,
        height=height,
        window_title=str(buffer.value or ""),
        process_id=int(process_id.value),
    )


def _capture_primary_screen_png() -> ScreenCaptureImage:
    if os.name != "nt":
        raise CaptureCollectorError("Screen capture is only implemented for Windows in this pass.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    width = int(user32.GetSystemMetrics(0))
    height = int(user32.GetSystemMetrics(1))
    if width <= 0 or height <= 0:
        raise CaptureCollectorError("Screen capture could not determine the primary display size.")

    hdc_screen = user32.GetDC(None)
    if not hdc_screen:
        raise CaptureCollectorError("Screen capture could not open the display context.")
    hdc_mem = None
    hbmp = None
    old_obj = None
    try:
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        if not hdc_mem:
            raise CaptureCollectorError("Screen capture could not create a memory display context.")
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
        if not hbmp:
            raise CaptureCollectorError("Screen capture could not create a bitmap.")
        old_obj = gdi32.SelectObject(hdc_mem, hbmp)
        if not gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0, 0x00CC0020):
            raise CaptureCollectorError("Screen capture failed while copying display pixels.")

        class BitmapInfoHeader(ctypes.Structure):
            _fields_ = [
                ("biSize", ctypes.c_uint32),
                ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32),
                ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16),
                ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32),
            ]

        class BitmapInfo(ctypes.Structure):
            _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", ctypes.c_uint32 * 3)]

        bitmap_info = BitmapInfo()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        bitmap_info.bmiHeader.biWidth = width
        bitmap_info.bmiHeader.biHeight = -height
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = 0
        buffer = ctypes.create_string_buffer(width * height * 4)
        lines = gdi32.GetDIBits(hdc_mem, hbmp, 0, height, buffer, ctypes.byref(bitmap_info), 0)
        if int(lines) != height:
            raise CaptureCollectorError("Screen capture could not read display pixels.")
        return ScreenCaptureImage(
            png_bytes=_png_from_bgra(buffer.raw, width, height),
            width=width,
            height=height,
        )
    finally:
        if old_obj and hdc_mem:
            gdi32.SelectObject(hdc_mem, old_obj)
        if hbmp:
            gdi32.DeleteObject(hbmp)
        if hdc_mem:
            gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)


def _png_from_bgra(bgra: bytes, width: int, height: int) -> bytes:
    rgba = bytearray(width * height * 4)
    for i in range(width * height):
        b = bgra[i * 4]
        g = bgra[i * 4 + 1]
        r = bgra[i * 4 + 2]
        rgba[i * 4] = r
        rgba[i * 4 + 1] = g
        rgba[i * 4 + 2] = b
        rgba[i * 4 + 3] = 255
    rows = []
    row_len = width * 4
    for y in range(height):
        start = y * row_len
        rows.append(b"\x00" + bytes(rgba[start:start + row_len]))
    return _png_rgba(width, height, b"".join(rows))


def _png_rgba(width: int, height: int, filtered_rows: bytes) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(filtered_rows))
        + chunk(b"IEND", b"")
    )
