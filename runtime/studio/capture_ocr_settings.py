"""Settings for Capture to Markdown local image text extraction."""

from __future__ import annotations

import json
import os
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.capture.visual_capture.ocr import (
    DEFAULT_OCR_TIMEOUT_SECONDS,
    LOCAL_OCR_ENV_COMMAND,
    LocalOpticalCharacterRecognitionError,
    build_local_ocr_status_model,
)
from runtime.capture.visual_capture.redaction import scan_secret_like_text
from runtime.studio.capture_ocr_quality_fixtures import (
    build_capture_local_image_text_quality_fixture_model,
)


MODEL_VERSION = "studio.capture_local_image_text_settings.v1"
SURFACE_ID = "studio_capture_local_image_text_settings"

DEFAULT_TIMEOUT_SECONDS = DEFAULT_OCR_TIMEOUT_SECONDS
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 120
_BLOCKED_SHELL_COMMANDS = {
    "cmd",
    "cmd.exe",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
    "wscript",
    "wscript.exe",
    "cscript",
    "cscript.exe",
}


class CaptureLocalImageTextSettingsError(ValueError):
    """Raised when local image text extraction settings are invalid."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def capture_local_image_text_settings_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve() / "runtime" / "studio" / "state" / "capture-local-image-text.json"


def default_capture_local_image_text_settings() -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "updated_at_utc": None,
        "local_ocr_command": "",
        "local_ocr_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
    }


def normalize_local_ocr_command(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "unassigned", "disabled"}:
        return ""
    if "\n" in text or "\r" in text:
        raise CaptureLocalImageTextSettingsError(
            "Local optical character recognition command must be a single line."
        )
    report = scan_secret_like_text(text)
    if report.contains_secret:
        raise CaptureLocalImageTextSettingsError(
            "Local optical character recognition command must not contain secret-like material."
        )
    prefix = _coerce_command_prefix_for_validation(text)
    if not prefix:
        return ""
    executable = Path(prefix[0]).name.lower()
    if executable in _BLOCKED_SHELL_COMMANDS:
        raise CaptureLocalImageTextSettingsError(
            "Shell launchers are blocked for local optical character recognition commands."
        )
    return text


def normalize_local_ocr_timeout_seconds(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS
    return min(MAX_TIMEOUT_SECONDS, max(MIN_TIMEOUT_SECONDS, parsed))


def _coerce_command_prefix_for_validation(command: str) -> tuple[str, ...]:
    raw = str(command or "").strip()
    if not raw:
        return ()
    if raw.startswith("["):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CaptureLocalImageTextSettingsError(
                "Local optical character recognition command JSON is invalid."
            ) from exc
        if not isinstance(decoded, list) or not all(isinstance(item, str) and item.strip() for item in decoded):
            raise CaptureLocalImageTextSettingsError(
                "Local optical character recognition command JSON must be an array of non-empty strings."
            )
        return tuple(item.strip() for item in decoded)
    if Path(raw).exists():
        return (raw,)
    try:
        return tuple(part for part in shlex.split(raw, posix=False) if part)
    except ValueError as exc:
        raise CaptureLocalImageTextSettingsError(
            "Local optical character recognition command could not be parsed."
        ) from exc


def _read_persisted_settings(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_capture_local_image_text_settings(vault_root: str | Path) -> dict[str, Any]:
    path = capture_local_image_text_settings_path(vault_root)
    settings = default_capture_local_image_text_settings()
    persisted = _read_persisted_settings(path)
    settings["local_ocr_command"] = normalize_local_ocr_command(
        persisted.get("local_ocr_command")
    )
    settings["local_ocr_timeout_seconds"] = normalize_local_ocr_timeout_seconds(
        persisted.get("local_ocr_timeout_seconds")
    )
    settings["updated_at_utc"] = persisted.get("updated_at_utc")
    return settings


def _write_capture_local_image_text_settings(vault_root: str | Path, settings: dict[str, Any]) -> None:
    path = capture_local_image_text_settings_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")


def save_capture_local_image_text_settings(
    vault_root: str | Path,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = payload or {}
    settings = load_capture_local_image_text_settings(vault_root)
    if "local_ocr_command" in request:
        settings["local_ocr_command"] = normalize_local_ocr_command(
            request.get("local_ocr_command")
        )
    if "local_ocr_timeout_seconds" in request:
        settings["local_ocr_timeout_seconds"] = normalize_local_ocr_timeout_seconds(
            request.get("local_ocr_timeout_seconds")
        )
    settings["schema_version"] = MODEL_VERSION
    settings["updated_at_utc"] = _now_utc()
    _write_capture_local_image_text_settings(vault_root, settings)
    return build_capture_local_image_text_settings_model(vault_root)


def build_capture_local_image_text_settings_model(vault_root: str | Path) -> dict[str, Any]:
    settings = load_capture_local_image_text_settings(vault_root)
    configured_command = settings.get("local_ocr_command") or ""
    try:
        local_status = build_local_ocr_status_model(
            command=configured_command or None,
        )
    except LocalOpticalCharacterRecognitionError as exc:
        local_status = {
            "ok": False,
            "surface": "capture_to_markdown_local_optical_character_recognition",
            "errors": [str(exc)],
            "policy": {},
            "engine": {
                "available": False,
                "engine_id": "configured-command",
                "protocol": "invalid",
                "command": [],
                "status": "invalid",
                "reason": str(exc),
                "cloud_optical_character_recognition_allowed": False,
                "provider_call_allowed": False,
            },
            "readiness": {
                "local_optical_character_recognition_adapter_ready": True,
                "local_engine_available": False,
                "cloud_optical_character_recognition_blocked": True,
                "provider_call_blocked": True,
                "explicit_image_required": True,
                "screen_capture_blocked": True,
                "secret_scan_after_extraction_required": True,
            },
        }
    engine = local_status.get("engine") if isinstance(local_status.get("engine"), dict) else {}
    quality_fixture_proof = build_capture_local_image_text_quality_fixture_model(
        vault_root,
        command=configured_command or None,
    )
    quality_summary = (
        quality_fixture_proof.get("summary")
        if isinstance(quality_fixture_proof.get("summary"), dict)
        else {}
    )
    configured = bool(configured_command)
    env_configured = bool(os.environ.get(LOCAL_OCR_ENV_COMMAND))
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "settings_path": str(capture_local_image_text_settings_path(vault_root)),
        "updated_at_utc": settings.get("updated_at_utc"),
        "local_ocr_command": configured_command,
        "local_ocr_timeout_seconds": int(settings.get("local_ocr_timeout_seconds") or DEFAULT_TIMEOUT_SECONDS),
        "local_optical_character_recognition": local_status,
        "quality_fixture_proof": quality_fixture_proof,
        "summary": {
            "configured_command_present": configured,
            "environment_command_present": env_configured,
            "local_engine_available": bool(engine.get("available")),
            "engine_id": engine.get("engine_id") or "none",
            "engine_status": engine.get("status") or "unknown",
            "quality_fixture_status": quality_fixture_proof.get("status") or "unknown",
            "quality_fixture_report_available": bool(
                quality_summary.get("latest_report_available")
            ),
            "real_engine_quality_verified": bool(
                quality_summary.get("real_engine_quality_verified")
            ),
        },
        "authority": {
            "writes_studio_preferences": True,
            "provider_calls_allowed": False,
            "cloud_optical_character_recognition_allowed": False,
            "captures_screen_pixels": False,
            "reads_active_window": False,
            "reads_active_browser_tab": False,
            "reads_ambient_clipboard": False,
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "settings_page_visible": True,
            "local_command_configurable": True,
            "local_command_viewable": True,
            "local_engine_available": bool(engine.get("available")),
            "configured_command_present": configured,
            "environment_command_present": env_configured,
            "explicit_vault_local_image_required": True,
            "cloud_optical_character_recognition_blocked": True,
            "provider_call_blocked": True,
            "screen_capture_blocked": True,
            "active_window_capture_blocked": True,
            "active_browser_capture_blocked": True,
            "secret_scan_after_extraction_required": True,
            "quality_fixture_runner_available": True,
            "quality_fixture_report_available": bool(
                quality_summary.get("latest_report_available")
            ),
            "real_engine_quality_verified": bool(
                quality_summary.get("real_engine_quality_verified")
            ),
        },
    }
