"""Local image text extraction quality fixtures for Capture to Markdown."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import struct
import zlib
from typing import Any

from runtime.capture.visual_capture.ocr import (
    DEFAULT_OCR_TIMEOUT_SECONDS,
    LocalOpticalCharacterRecognitionError,
    extract_text_from_image,
    resolve_local_ocr_engine,
)
from runtime.capture.visual_capture.local_image_text_engine import render_common_font_text_png


MODEL_VERSION = "studio.capture_local_image_text_quality_fixtures.v1"
SURFACE_ID = "studio_capture_local_image_text_quality_fixtures"
FIXTURE_SET_ID = "capture-to-markdown-local-image-text-quality-v1"


@dataclass(frozen=True)
class QualityFixture:
    fixture_id: str
    label: str
    text: str
    expected_tokens: tuple[str, ...]
    expected_text: bool = True
    foreground: tuple[int, int, int] = (8, 14, 28)
    background: tuple[int, int, int] = (252, 252, 250)
    scale: int = 10
    required: bool = True
    renderer: str = "pixel"


QUALITY_FIXTURES: tuple[QualityFixture, ...] = (
    QualityFixture(
        fixture_id="no_text",
        label="No text",
        text="",
        expected_tokens=(),
        expected_text=False,
        required=True,
    ),
    QualityFixture(
        fixture_id="dense_text",
        label="Dense text",
        text="CHASEOS MARKDOWN CAPTURE\nVISIBLE TEXT SAMPLE\nLOCAL ENGINE QUALITY",
        expected_tokens=("CHASEOS", "MARKDOWN", "CAPTURE", "VISIBLE", "TEXT", "LOCAL", "ENGINE"),
        required=True,
    ),
    QualityFixture(
        fixture_id="low_contrast",
        label="Low contrast text",
        text="LOW CONTRAST CAPTURE\nREADABILITY CHECK",
        expected_tokens=("LOW", "CONTRAST", "CAPTURE", "READABILITY", "CHECK"),
        foreground=(112, 112, 112),
        background=(236, 236, 236),
        required=True,
    ),
    QualityFixture(
        fixture_id="table_text",
        label="Table text",
        text="ITEM COUNT STATUS\nALPHA 12 READY\nBETA 34 REVIEW",
        expected_tokens=("ITEM", "COUNT", "STATUS", "ALPHA", "12", "BETA", "34", "REVIEW"),
        required=True,
    ),
    QualityFixture(
        fixture_id="mixed_language",
        label="Mixed language",
        text="MIXED LANGUAGE SAMPLE\nHOLA BONJOUR CAFE\nRESUME NAIVE TEXT",
        expected_tokens=("MIXED", "LANGUAGE", "HOLA", "BONJOUR", "CAFE", "RESUME", "NAIVE"),
        required=True,
    ),
    QualityFixture(
        fixture_id="studio_font_screenshot",
        label="Studio font screenshot",
        text="CAPTURE TO MARKDOWN\nSCREEN TEXT FROM STUDIO\nDISCORD BROWSER READY",
        expected_tokens=(
            "CAPTURE",
            "MARKDOWN",
            "SCREEN",
            "TEXT",
            "STUDIO",
            "DISCORD",
            "BROWSER",
            "READY",
        ),
        required=True,
        renderer="common_font",
    ),
)


_FONT_5X7: dict[str, tuple[str, ...]] = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "?": ("11110", "00001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "11100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_run_id(value: str | None = None) -> str:
    raw = str(value or _slug_timestamp()).strip()
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip(".-")
    return safe[:80] or _slug_timestamp()


def fixture_output_dir(vault_root: str | Path, run_id: str) -> Path:
    return Path(vault_root).resolve() / "07_LOGS" / "Operator-Screenshots" / "Capture-OCR-Fixtures" / run_id


def quality_report_dir(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve() / "07_LOGS" / "Studio-Graph-Views"


def latest_quality_report_path(vault_root: str | Path) -> Path | None:
    root = quality_report_dir(vault_root)
    reports = sorted(root.glob("*capture-local-image-text-quality-fixtures*.json"))
    return reports[-1] if reports else None


def build_capture_local_image_text_quality_fixture_model(
    vault_root: str | Path,
    *,
    command: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Return read-only readiness for the real local image text quality fixture lane."""

    vault = Path(vault_root).resolve()
    engine = resolve_local_ocr_engine(command)
    latest = latest_quality_report_path(vault)
    latest_payload: dict[str, Any] = {}
    if latest:
        try:
            loaded = json.loads(latest.read_text(encoding="utf-8"))
            latest_payload = loaded if isinstance(loaded, dict) else {}
        except Exception:
            latest_payload = {"status": "unreadable_latest_report"}

    latest_summary = latest_payload.get("summary") if isinstance(latest_payload.get("summary"), dict) else {}
    latest_verified = bool(latest_summary.get("real_engine_quality_verified"))
    latest_status = latest_payload.get("status") or "none"
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "fixture_set_id": FIXTURE_SET_ID,
        "vault_root": str(vault),
        "status": "quality_verified" if latest_verified else ("engine_available_fixture_run_required" if engine.available else "blocked_missing_local_engine"),
        "engine": engine.to_dict(),
        "fixture_count": len(QUALITY_FIXTURES),
        "required_fixture_count": len([fixture for fixture in QUALITY_FIXTURES if fixture.required]),
        "fixtures": [
            {
                "id": fixture.fixture_id,
                "label": fixture.label,
                "expected_text": fixture.expected_text,
                "expected_tokens": list(fixture.expected_tokens),
                "required": fixture.required,
            }
            for fixture in QUALITY_FIXTURES
        ],
        "latest_report": {
            "available": latest is not None,
            "path": str(latest) if latest else "",
            "relative_path": _relative_to_vault(vault, latest) if latest else "",
            "status": latest_status,
            "real_engine_quality_verified": latest_verified,
            "passed_fixture_count": int(latest_summary.get("passed_fixture_count") or 0),
            "failed_fixture_count": int(latest_summary.get("failed_fixture_count") or 0),
            "blocked_fixture_count": int(latest_summary.get("blocked_fixture_count") or 0),
        },
        "summary": {
            "fixture_runner_ready": True,
            "local_engine_available": engine.available,
            "real_engine_quality_verified": latest_verified,
            "latest_report_available": latest is not None,
            "latest_report_status": latest_status,
        },
        "authority": {
            "read_only_status_surface": True,
            "writes_on_settings_load": False,
            "writes_fixture_images_when_runner_invoked": True,
            "writes_quality_report_when_runner_invoked": True,
            "writes_raw_quarantine_markdown": False,
            "captures_live_screen": False,
            "reads_active_window": False,
            "reads_active_browser_tab": False,
            "calls_providers": False,
            "cloud_optical_character_recognition_allowed": False,
            "starts_shell_launchers": False,
        },
        "readiness": {
            "settings_readback_ready": True,
            "fixture_runner_available": True,
            "explicit_operator_command_required_to_run": True,
            "local_engine_available": engine.available,
            "real_engine_quality_verified": latest_verified,
            "blocked_until_local_engine_available": not engine.available,
            "no_text_fixture_defined": True,
            "dense_text_fixture_defined": True,
            "low_contrast_fixture_defined": True,
            "table_text_fixture_defined": True,
            "mixed_language_fixture_defined": True,
            "studio_font_screenshot_fixture_defined": True,
        },
        "recommended_command": (
            f'python -m runtime.studio.capture_ocr_quality_fixtures --vault-root "{vault}" --write-report --json'
        ),
    }


def run_capture_local_image_text_quality_fixtures(
    vault_root: str | Path,
    *,
    command: str | list[str] | tuple[str, ...] | None = None,
    timeout_seconds: int | None = None,
    run_id: str | None = None,
    write_report: bool = False,
    use_saved_settings: bool = True,
) -> dict[str, Any]:
    """Run the local engine against fixture images and optionally write evidence."""

    vault = Path(vault_root).resolve()
    resolved_command = command
    resolved_timeout = int(timeout_seconds or DEFAULT_OCR_TIMEOUT_SECONDS)
    if use_saved_settings and resolved_command is None:
        try:
            from runtime.studio.capture_ocr_settings import load_capture_local_image_text_settings

            settings = load_capture_local_image_text_settings(vault)
            resolved_command = settings.get("local_ocr_command") or None
            resolved_timeout = int(settings.get("local_ocr_timeout_seconds") or resolved_timeout)
        except Exception:
            resolved_command = command

    safe_run_id = _safe_run_id(run_id)
    engine = resolve_local_ocr_engine(resolved_command)
    fixture_dir = fixture_output_dir(vault, safe_run_id)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_records = _write_fixture_images(vault, fixture_dir)
    results: list[dict[str, Any]] = []

    if not engine.available:
        for record in fixture_records:
            results.append(
                {
                    **record,
                    "status": "not_run_engine_missing",
                    "passed": False,
                    "blocked": True,
                    "error": engine.reason or engine.status,
                    "extracted_text": "",
                    "matched_tokens": [],
                    "missing_tokens": list(record.get("expected_tokens") or []),
                }
            )
    else:
        for record in fixture_records:
            results.append(
                _run_one_fixture(
                    vault,
                    record,
                    command=resolved_command,
                    timeout_seconds=resolved_timeout,
                )
            )

    required_results = [item for item in results if item.get("required")]
    passed_count = len([item for item in results if item.get("passed")])
    failed_count = len([item for item in results if not item.get("passed") and not item.get("blocked")])
    blocked_count = len([item for item in results if item.get("blocked")])
    required_passed = all(bool(item.get("passed")) for item in required_results)
    verified = bool(engine.available and required_passed)
    status = (
        "verified"
        if verified
        else "blocked_missing_local_engine"
        if not engine.available
        else "quality_gaps_detected"
    )
    report: dict[str, Any] = {
        "ok": verified,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "fixture_set_id": FIXTURE_SET_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "run_id": safe_run_id,
        "vault_root": str(vault),
        "engine": engine.to_dict(),
        "fixture_dir": str(fixture_dir),
        "fixture_dir_relative": _relative_to_vault(vault, fixture_dir),
        "fixtures": results,
        "summary": {
            "fixture_count": len(results),
            "required_fixture_count": len(required_results),
            "passed_fixture_count": passed_count,
            "failed_fixture_count": failed_count,
            "blocked_fixture_count": blocked_count,
            "real_engine_quality_verified": verified,
            "safe_to_mark_real_engine_quality_verified": verified,
            "raw_quarantine_markdown_written": False,
            "approval_artifacts_written": False,
            "provider_calls_performed": False,
            "live_screen_capture_performed": False,
        },
        "authority": {
            "writes_fixture_images": True,
            "writes_quality_report": bool(write_report),
            "writes_raw_quarantine_markdown": False,
            "writes_approval_artifacts": False,
            "captures_live_screen": False,
            "reads_active_browser_tab": False,
            "calls_providers": False,
            "cloud_optical_character_recognition_allowed": False,
            "starts_shell_launchers": False,
        },
    }
    if write_report:
        json_path = _write_json_report(vault, report, safe_run_id)
        markdown_path = _write_markdown_report(vault, report, json_path, safe_run_id)
        report["report_path"] = str(json_path)
        report["report_relative_path"] = _relative_to_vault(vault, json_path)
        report["markdown_report_path"] = str(markdown_path)
        report["markdown_report_relative_path"] = _relative_to_vault(vault, markdown_path)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return report


def _write_fixture_images(vault: Path, fixture_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for fixture in QUALITY_FIXTURES:
        path = fixture_dir / f"{fixture.fixture_id}.png"
        path.write_bytes(_fixture_png(fixture))
        records.append(
            {
                "id": fixture.fixture_id,
                "label": fixture.label,
                "path": str(path),
                "relative_path": _relative_to_vault(vault, path),
                "expected_text": fixture.expected_text,
                "expected_tokens": list(fixture.expected_tokens),
                "required": fixture.required,
            }
        )
    return records


def _run_one_fixture(
    vault: Path,
    record: dict[str, Any],
    *,
    command: str | list[str] | tuple[str, ...] | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    expected_tokens = list(record.get("expected_tokens") or [])
    expected_text = bool(record.get("expected_text"))
    try:
        result = extract_text_from_image(
            record["relative_path"],
            vault_root=vault,
            command=command,
            timeout_seconds=timeout_seconds,
        )
    except LocalOpticalCharacterRecognitionError as exc:
        if not expected_text and "returned no text" in str(exc).lower():
            return {
                **record,
                "status": "passed_no_text_blocked",
                "passed": True,
                "blocked": False,
                "error": "",
                "extracted_text": "",
                "matched_tokens": [],
                "missing_tokens": [],
            }
        return {
            **record,
            "status": "failed_extraction_error",
            "passed": False,
            "blocked": False,
            "error": str(exc),
            "extracted_text": "",
            "matched_tokens": [],
            "missing_tokens": expected_tokens,
        }

    extracted = result.text
    normalized = _normalize_for_token_match(extracted)
    if not expected_text:
        return {
            **record,
            "status": "failed_unexpected_text",
            "passed": False,
            "blocked": False,
            "error": "Fixture expected no text, but the engine returned text.",
            "extracted_text": extracted,
            "matched_tokens": [],
            "missing_tokens": [],
        }
    matched = [token for token in expected_tokens if token.upper() in normalized]
    missing = [token for token in expected_tokens if token.upper() not in normalized]
    passed = not missing
    return {
        **record,
        "status": "passed" if passed else "failed_missing_expected_tokens",
        "passed": passed,
        "blocked": False,
        "error": "" if passed else "Expected fixture tokens were missing.",
        "extracted_text": extracted,
        "extracted_text_sha256": result.text_sha256,
        "matched_tokens": matched,
        "missing_tokens": missing,
    }


def _normalize_for_token_match(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(text or "").upper())


def _write_json_report(vault: Path, report: dict[str, Any], run_id: str) -> Path:
    root = quality_report_dir(vault)
    root.mkdir(parents=True, exist_ok=True)
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _collision_safe_path(root / f"{date_prefix}-capture-local-image-text-quality-fixtures-{run_id}.json")


def _write_markdown_report(vault: Path, report: dict[str, Any], json_path: Path, run_id: str) -> Path:
    root = quality_report_dir(vault)
    date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _collision_safe_path(root / f"{date_prefix}-capture-local-image-text-quality-fixtures-{run_id}.md")


def _collision_safe_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    for index in range(2, 1000):
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not allocate collision-safe report path for {path}")


def _markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        f"# Capture Local Image Text Quality Fixtures - {report.get('run_id')}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Engine: `{((report.get('engine') or {}).get('engine_id') or 'none')}`",
        f"- Real engine quality verified: `{summary.get('real_engine_quality_verified')}`",
        f"- Passed fixtures: `{summary.get('passed_fixture_count')}`",
        f"- Failed fixtures: `{summary.get('failed_fixture_count')}`",
        f"- Blocked fixtures: `{summary.get('blocked_fixture_count')}`",
        f"- Raw quarantine Markdown written: `{summary.get('raw_quarantine_markdown_written')}`",
        f"- Provider calls performed: `{summary.get('provider_calls_performed')}`",
        "",
        "## Fixture Results",
        "",
    ]
    for fixture in report.get("fixtures") or []:
        lines.extend(
            [
                f"### {fixture.get('label') or fixture.get('id')}",
                "",
                f"- Status: `{fixture.get('status')}`",
                f"- Passed: `{fixture.get('passed')}`",
                f"- Missing tokens: `{', '.join(fixture.get('missing_tokens') or [])}`",
                f"- Image: `{fixture.get('relative_path')}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _fixture_png(fixture: QualityFixture) -> bytes:
    if fixture.renderer == "common_font":
        image_bytes, _width, _height = render_common_font_text_png(
            tuple(fixture.text.splitlines()),
            point_size=30,
            foreground=fixture.foreground,
            background=fixture.background,
            min_width=820,
            min_height=260,
        )
        return image_bytes
    if not fixture.text:
        return _png_with_decorative_lines(760, 260, fixture.background, (170, 170, 170))
    lines = fixture.text.splitlines()
    char_w = 5 * fixture.scale
    char_h = 7 * fixture.scale
    spacing = 2 * fixture.scale
    line_gap = 3 * fixture.scale
    margin = 4 * fixture.scale
    width = max(760, max(len(line) for line in lines) * (char_w + spacing) + margin * 2)
    height = max(240, len(lines) * char_h + (len(lines) - 1) * line_gap + margin * 2)
    pixels = _new_pixels(width, height, fixture.background)
    y = margin
    for line in lines:
        x = margin
        for char in line.upper():
            pattern = _FONT_5X7.get(char, _FONT_5X7["?"])
            _draw_char(pixels, width, height, x, y, pattern, fixture.scale, fixture.foreground)
            x += char_w + spacing
        y += char_h + line_gap
    return _encode_png(width, height, pixels)


def _png_with_decorative_lines(
    width: int,
    height: int,
    background: tuple[int, int, int],
    foreground: tuple[int, int, int],
) -> bytes:
    pixels = _new_pixels(width, height, background)
    for x in range(30, width - 30):
        _set_pixel(pixels, width, height, x, 40, foreground)
        _set_pixel(pixels, width, height, x, height - 40, foreground)
    for y in range(40, height - 40):
        _set_pixel(pixels, width, height, 30, y, foreground)
        _set_pixel(pixels, width, height, width - 30, y, foreground)
    for offset in range(0, 160):
        _set_pixel(pixels, width, height, 120 + offset, 110 + offset // 4, foreground)
        _set_pixel(pixels, width, height, 440 + offset, 150 - offset // 5, foreground)
    return _encode_png(width, height, pixels)


def _new_pixels(width: int, height: int, color: tuple[int, int, int]) -> bytearray:
    row = bytes(color) * width
    return bytearray(row * height)


def _draw_char(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    pattern: tuple[str, ...],
    scale: int,
    color: tuple[int, int, int],
) -> None:
    for row_index, row in enumerate(pattern):
        for col_index, flag in enumerate(row):
            if flag != "1":
                continue
            for dy in range(scale):
                for dx in range(scale):
                    _set_pixel(
                        pixels,
                        width,
                        height,
                        x + col_index * scale + dx,
                        y + row_index * scale + dy,
                        color,
                    )


def _set_pixel(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return
    idx = (y * width + x) * 3
    pixels[idx : idx + 3] = bytes(color)


def _encode_png(width: int, height: int, rgb: bytearray) -> bytes:
    raw = bytearray()
    row_bytes = width * 3
    for y in range(height):
        raw.append(0)
        start = y * row_bytes
        raw.extend(rgb[start : start + row_bytes])
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9)),
            _png_chunk(b"IEND", b""),
        ]
    )


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    payload = chunk_type + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Capture to Markdown local image text quality fixtures.")
    parser.add_argument("--vault-root", default=".", help="Vault root to use for fixture and report paths.")
    parser.add_argument("--local-command", default=None, help="Optional local image text extraction command.")
    parser.add_argument("--timeout-seconds", type=int, default=None, help="Timeout per fixture image.")
    parser.add_argument("--run-id", default=None, help="Optional evidence run identifier.")
    parser.add_argument("--write-report", action="store_true", help="Write fixture images and JSON/Markdown evidence.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    report = run_capture_local_image_text_quality_fixtures(
        args.vault_root,
        command=args.local_command,
        timeout_seconds=args.timeout_seconds,
        run_id=args.run_id,
        write_report=args.write_report,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_markdown_report(report))
    return 0 if report.get("status") in {"verified", "blocked_missing_local_engine", "quality_gaps_detected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
