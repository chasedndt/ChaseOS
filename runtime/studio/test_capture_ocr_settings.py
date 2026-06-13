from __future__ import annotations

import json
import sys

import pytest

from runtime.capture.visual_capture import ocr
from runtime.capture.visual_capture.ocr import LocalOpticalCharacterRecognitionError
from runtime.studio.capture_ocr_settings import (
    CaptureLocalImageTextSettingsError,
    build_capture_local_image_text_settings_model,
    capture_local_image_text_settings_path,
    normalize_local_ocr_command,
    normalize_local_ocr_timeout_seconds,
    save_capture_local_image_text_settings,
)


def test_capture_local_image_text_settings_defaults_are_local_only(tmp_path):
    model = build_capture_local_image_text_settings_model(tmp_path)

    assert model["surface"] == "studio_capture_local_image_text_settings"
    assert model["local_ocr_command"] == ""
    assert model["local_ocr_timeout_seconds"] == 20
    assert model["readiness"]["settings_page_visible"] is True
    assert model["readiness"]["local_command_configurable"] is True
    assert model["readiness"]["explicit_vault_local_image_required"] is True
    assert model["readiness"]["quality_fixture_runner_available"] is True
    assert model["readiness"]["real_engine_quality_verified"] is False
    assert model["quality_fixture_proof"]["surface"] == "studio_capture_local_image_text_quality_fixtures"
    assert model["quality_fixture_proof"]["authority"]["writes_on_settings_load"] is False
    assert model["readiness"]["cloud_optical_character_recognition_blocked"] is True
    assert model["readiness"]["provider_call_blocked"] is True
    assert model["authority"]["provider_calls_allowed"] is False
    assert model["authority"]["cloud_optical_character_recognition_allowed"] is False
    assert model["authority"]["captures_screen_pixels"] is False


def test_capture_local_image_text_settings_save_persists_command_and_timeout(tmp_path):
    command = json.dumps([sys.executable, "-c", "print('local text')"])

    model = save_capture_local_image_text_settings(
        tmp_path,
        {
            "local_ocr_command": command,
            "local_ocr_timeout_seconds": 45,
        },
    )

    path = capture_local_image_text_settings_path(tmp_path)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["local_ocr_command"] == command
    assert persisted["local_ocr_timeout_seconds"] == 45
    assert model["local_ocr_command"] == command
    assert model["local_ocr_timeout_seconds"] == 45
    assert model["summary"]["configured_command_present"] is True
    assert model["summary"]["local_engine_available"] is True
    assert model["local_optical_character_recognition"]["engine"]["engine_id"] == "configured-command"
    assert model["summary"]["quality_fixture_status"] == "engine_available_fixture_run_required"
    assert model["quality_fixture_proof"]["summary"]["fixture_runner_ready"] is True
    assert model["quality_fixture_proof"]["summary"]["real_engine_quality_verified"] is False


def test_capture_local_image_text_settings_rejects_secret_like_command(tmp_path):
    with pytest.raises(CaptureLocalImageTextSettingsError):
        save_capture_local_image_text_settings(
            tmp_path,
            {"local_ocr_command": "tesseract --token test-key-abcdefghijklmnop1234"},
        )


def test_capture_local_image_text_settings_rejects_shell_launcher(tmp_path):
    with pytest.raises(CaptureLocalImageTextSettingsError):
        save_capture_local_image_text_settings(
            tmp_path,
            {"local_ocr_command": "powershell -File run-image-text.ps1"},
        )


def test_capture_local_image_text_settings_blocks_environment_shell_launcher(tmp_path, monkeypatch):
    monkeypatch.setenv(ocr.LOCAL_OCR_ENV_COMMAND, "powershell -File run-image-text.ps1")
    monkeypatch.setattr(
        ocr.shutil,
        "which",
        lambda exe: r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        if str(exe).lower() == "powershell"
        else None,
    )

    model = build_capture_local_image_text_settings_model(tmp_path)
    engine = model["local_optical_character_recognition"]["engine"]

    assert engine["available"] is False
    assert engine["engine_id"] == "blocked-shell-launcher"
    assert engine["status"] == "blocked_by_policy"
    assert "Shell launchers are blocked" in engine["reason"]


def test_local_image_text_shell_launcher_is_rejected_before_subprocess(tmp_path, monkeypatch):
    image = tmp_path / "07_LOGS" / "Operator-Screenshots" / "sample.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(
        bytes.fromhex("89504e470d0a1a0a")
        + b"not a blank image; only signature and byte posture are validated"
    )
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(ocr.subprocess, "run", fake_run)

    with pytest.raises(
        LocalOpticalCharacterRecognitionError,
        match="Shell launchers are blocked",
    ):
        ocr.extract_text_from_image(
            image,
            vault_root=tmp_path,
            command="powershell -File run-image-text.ps1",
        )

    assert calls == []


def test_capture_local_image_text_settings_normalizes_timeout_bounds():
    assert normalize_local_ocr_timeout_seconds("0") == 1
    assert normalize_local_ocr_timeout_seconds("999") == 120
    assert normalize_local_ocr_timeout_seconds("bad") == 20


def test_capture_local_image_text_settings_rejects_multiline_command():
    with pytest.raises(CaptureLocalImageTextSettingsError):
        normalize_local_ocr_command("tesseract\nother")
