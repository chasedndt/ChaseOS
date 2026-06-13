"""Tests for Pass 10B supplemental native screenshot evidence intake."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import zlib

import pytest

from runtime.studio.pass10b_native_screenshot_evidence_intake import (
    build_pass10b_native_screenshot_evidence_intake,
    write_pass10b_native_screenshot_evidence_intake,
)


def _write_png(path: Path, width: int, height: int, pixels: list[bytes]) -> None:
    rows = []
    for row_index in range(height):
        start = row_index * width
        rows.append(b"\x00" + b"".join(pixels[start : start + width]))
    raw = zlib.compress(b"".join(rows))

    def chunk(kind: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", raw)
        + chunk(b"IEND", b"")
    )


def test_native_screenshot_evidence_intake_accepts_declared_native_nonblank(tmp_path: Path) -> None:
    screenshot = tmp_path / "native.png"
    colors = [b"\xff\xff\xff", b"\x00\x00\x00", b"\x38\xbd\xf8", b"\x22\xc5\x5e"] * 100
    _write_png(screenshot, 40, 10, colors)

    report = build_pass10b_native_screenshot_evidence_intake(
        tmp_path,
        screenshot_path=screenshot,
        declared_source="operator-native-packaged-window",
        min_unique_colors=4,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is True
    assert report["readiness"]["supplemental_native_screenshot_evidence_verified"] is True
    assert report["readiness"]["automated_packaged_visual_qa_complete"] is False
    assert report["readiness"]["can_close_pass10b_native_visual_proof"] is False
    assert checks["screenshot_nonblank"]["ok"] is True


def test_native_screenshot_evidence_intake_rejects_non_native_source(tmp_path: Path) -> None:
    screenshot = tmp_path / "browser.png"
    colors = [b"\xff\xff\xff", b"\x00\x00\x00", b"\x38\xbd\xf8", b"\x22\xc5\x5e"] * 100
    _write_png(screenshot, 40, 10, colors)

    report = build_pass10b_native_screenshot_evidence_intake(
        tmp_path,
        screenshot_path=screenshot,
        declared_source="browser-static-route",
        min_unique_colors=4,
    )

    assert report["ok"] is False
    assert report["status"] == "VISUAL_EVIDENCE_NONBLANK_BUT_NOT_NATIVE"
    assert report["readiness"]["can_support_manual_review"] is True
    assert report["readiness"]["can_close_pass10b_native_visual_proof"] is False


def test_native_screenshot_evidence_intake_rejects_outside_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.png"
    outside.write_bytes(b"not-png")

    with pytest.raises(ValueError):
        build_pass10b_native_screenshot_evidence_intake(
            tmp_path,
            screenshot_path=outside,
            declared_source="operator-native-packaged-window",
        )


def test_native_screenshot_evidence_intake_writes_durable_evidence(tmp_path: Path) -> None:
    screenshot = tmp_path / "native.png"
    colors = [b"\xff\xff\xff", b"\x00\x00\x00", b"\x38\xbd\xf8", b"\x22\xc5\x5e"] * 100
    _write_png(screenshot, 40, 10, colors)
    report = build_pass10b_native_screenshot_evidence_intake(
        tmp_path,
        screenshot_path=screenshot,
        declared_source="operator-native-packaged-window",
        min_unique_colors=4,
    )

    write = write_pass10b_native_screenshot_evidence_intake(
        tmp_path,
        report,
        evidence_slug="native-evidence",
        evidence_root="evidence",
    )

    json_path = tmp_path / write["json_path"]
    markdown_path = tmp_path / write["markdown_path"]
    assert write["written"] is True
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "cannot complete automated packaged visual QA" in json_path.read_text(encoding="utf-8")
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Pass 10B Native Screenshot Evidence Intake" in markdown
    assert "It does not complete automated packaged visual QA." in markdown


def test_native_screenshot_evidence_intake_writer_rejects_outside_root(tmp_path: Path) -> None:
    report = {"status": "fixture", "ok": False}

    with pytest.raises(ValueError):
        write_pass10b_native_screenshot_evidence_intake(
            tmp_path,
            report,
            evidence_root=tmp_path.parent / "outside-evidence",
        )


def test_native_screenshot_evidence_writer_rejects_slug_escape_from_evidence_root(tmp_path: Path) -> None:
    report = {"status": "fixture", "ok": False}

    with pytest.raises(ValueError, match="evidence output must stay inside the evidence root"):
        write_pass10b_native_screenshot_evidence_intake(
            tmp_path,
            report,
            evidence_root="evidence",
            evidence_slug="../vault-local-but-outside-evidence-root",
        )

    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.json").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.md").exists()


def test_native_screenshot_evidence_cli_returns_json_error_for_slug_escape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from runtime.cli.main import cmd_studio_pass10b_native_screenshot_evidence_intake

    screenshot = tmp_path / "native.png"
    colors = [b"\xff\xff\xff", b"\x00\x00\x00", b"\x38\xbd\xf8", b"\x22\xc5\x5e"] * 100
    _write_png(screenshot, 40, 10, colors)

    code = cmd_studio_pass10b_native_screenshot_evidence_intake(
        argparse.Namespace(
            vault_root=str(tmp_path),
            screenshot_path=str(screenshot),
            declared_source="operator-native-packaged-window",
            min_unique_colors=4,
            max_dominant_ratio=0.995,
            write_evidence=True,
            evidence_slug="../vault-local-but-outside-evidence-root",
            evidence_root="evidence",
            output_json=True,
        )
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert code == 1
    assert payload["ok"] is False
    assert "evidence output must stay inside the evidence root" in payload["error"]
    assert captured.err == ""
    assert not (tmp_path / "evidence").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.json").exists()
    assert not (tmp_path / "vault-local-but-outside-evidence-root.md").exists()


def test_native_screenshot_evidence_intake_parser() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "pass10b-native-screenshot-evidence-intake",
            "--screenshot-path",
            "shot.png",
            "--declared-source",
            "operator-native-packaged-window",
            "--min-unique-colors",
            "12",
            "--max-dominant-ratio",
            "0.9",
            "--write-evidence",
            "--evidence-slug",
            "native-evidence",
            "--evidence-root",
            "evidence",
        ]
    )

    assert args.screenshot_path == "shot.png"
    assert args.declared_source == "operator-native-packaged-window"
    assert args.min_unique_colors == 12
    assert args.max_dominant_ratio == 0.9
    assert args.write_evidence is True
    assert args.evidence_slug == "native-evidence"
    assert args.evidence_root == "evidence"
