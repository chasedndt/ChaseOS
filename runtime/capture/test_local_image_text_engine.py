from __future__ import annotations

import subprocess
from pathlib import Path

from runtime.capture.visual_capture.local_image_text_engine import (
    ENGINE_ID,
    extract_text_from_pixel_image,
    local_image_text_engine_command,
    render_common_font_text_png,
    render_pixel_text_png,
)
from runtime.capture.visual_capture.ocr import extract_text_from_image, resolve_local_ocr_engine


def test_builtin_local_image_text_engine_extracts_rendered_pixel_text(tmp_path: Path) -> None:
    image_bytes, width, height = render_pixel_text_png(
        ("CHASEOS MARKDOWN CAPTURE", "TEXT 2026 05 28"),
        scale=8,
        min_width=640,
        min_height=180,
    )
    image_path = tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown" / "pixel-text.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image_bytes)

    assert width >= 640
    assert height >= 180
    assert extract_text_from_pixel_image(image_path) == "CHASEOS MARKDOWN CAPTURE\nTEXT 2026 05 28"


def test_builtin_local_image_text_engine_command_prints_text(tmp_path: Path) -> None:
    image_bytes, _width, _height = render_pixel_text_png(("LOCAL ENGINE READY",), scale=9)
    image_path = tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown" / "engine.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image_bytes)

    completed = subprocess.run(
        [*local_image_text_engine_command(), str(image_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        shell=False,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == "LOCAL ENGINE READY"


def test_builtin_local_image_text_engine_extracts_common_font_screenshot_text(tmp_path: Path) -> None:
    image_bytes, width, height = render_common_font_text_png(
        ("CAPTURE TO MARKDOWN", "SCREEN TEXT SAMPLE"),
        font_family="Segoe UI",
        point_size=32,
        min_width=760,
        min_height=220,
    )
    image_path = tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown" / "common-font.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image_bytes)

    extracted = extract_text_from_pixel_image(image_path)
    normalized = " ".join(extracted.upper().split())

    assert width >= 760
    assert height >= 220
    for token in ("CAPTURE", "MARKDOWN", "SCREEN", "TEXT", "SAMPLE"):
        assert token in normalized


def test_capture_to_markdown_resolves_builtin_engine_when_no_external_engine(monkeypatch) -> None:
    monkeypatch.delenv("CHASEOS_LOCAL_OCR_COMMAND", raising=False)
    monkeypatch.setattr("runtime.capture.visual_capture.ocr.shutil.which", lambda _exe: None)
    monkeypatch.setattr("runtime.capture.visual_capture.ocr._windows_ocr_engine_available", lambda: False)

    engine = resolve_local_ocr_engine()

    assert engine.available is True
    assert engine.engine_id == ENGINE_ID
    assert engine.protocol == "stdout_image_path"
    assert Path(engine.command[-1]).name == "local_image_text_engine.py"


def test_capture_to_markdown_default_engine_extracts_from_vault_image(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CHASEOS_LOCAL_OCR_COMMAND", raising=False)
    monkeypatch.setattr("runtime.capture.visual_capture.ocr.shutil.which", lambda _exe: None)
    monkeypatch.setattr("runtime.capture.visual_capture.ocr._windows_ocr_engine_available", lambda: False)
    image_bytes, _width, _height = render_pixel_text_png(("SOURCE TEXT FROM IMAGE",), scale=8)
    image_path = tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown" / "source.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image_bytes)

    result = extract_text_from_image(
        "07_LOGS/Operator-Screenshots/Capture-to-Markdown/source.png",
        vault_root=tmp_path,
    )

    assert result.engine.engine_id == ENGINE_ID
    assert result.text == "SOURCE TEXT FROM IMAGE"
    assert result.text_sha256
    assert "cloud_optical_character_recognition_blocked" in result.warnings


def test_capture_to_markdown_windows_media_ocr_engine_is_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CHASEOS_LOCAL_OCR_COMMAND", raising=False)
    monkeypatch.setattr("runtime.capture.visual_capture.ocr.shutil.which", lambda _exe: None)
    monkeypatch.setattr("runtime.capture.visual_capture.ocr._windows_ocr_engine_available", lambda: True)
    monkeypatch.setattr(
        "runtime.capture.visual_capture.ocr._extract_text_with_windows_ocr",
        lambda _path: "Windows local optical character recognition text.",
    )
    image_bytes, _width, _height = render_common_font_text_png(
        ("WINDOWS LOCAL OCR",),
        point_size=32,
        min_width=760,
        min_height=220,
    )
    image_path = tmp_path / "07_LOGS" / "Operator-Screenshots" / "Capture-to-Markdown" / "windows-ocr.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(image_bytes)

    engine = resolve_local_ocr_engine()
    result = extract_text_from_image(
        "07_LOGS/Operator-Screenshots/Capture-to-Markdown/windows-ocr.png",
        vault_root=tmp_path,
    )

    assert engine.engine_id == "windows-media-ocr"
    assert engine.protocol == "windows_media_ocr"
    assert result.engine.engine_id == "windows-media-ocr"
    assert result.text == "Windows local optical character recognition text."
    assert "local_optical_character_recognition_engine:windows-media-ocr" in result.warnings
    assert "cloud_optical_character_recognition_blocked" in result.warnings
