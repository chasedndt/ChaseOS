"""
test_pass8p2.py — ChaseOS Phase 8 Pass 2 Test Suite
Structural Intake Hardening + Canonical ChaseOS CLI

Run:
    python -m runtime.capture.test_pass8p2

Or via canonical CLI:
    chaseos test capture

Tests:
    P2-T01  ContentPacket: original_name field exists and optional
    P2-T02  ContentPacket: original_path_or_uri field exists and optional
    P2-T03  ContentPacket: detected_mime defaults to text/plain
    P2-T04  ContentPacket: workspace_hint field exists and optional
    P2-T05  router: route_input_class targets 00_QUARANTINE/ boundary
    P2-T06  router: get_route_reason returns correct string
    P2-T07  router: QUARANTINE_SUBDIR constant is "00_QUARANTINE"
    P2-T08  intake_writer: sidecar schema version is 8.2
    P2-T09  intake_writer: sidecar has quarantine_status = pending-review
    P2-T10  intake_writer: sidecar has source_package_status = not-ingested
    P2-T11  intake_writer: sidecar has route_reason with correct pattern
    P2-T12  intake_writer: sidecar has original_name from cli_connector
    P2-T13  intake_writer: sidecar has original_path_or_uri from cli_connector
    P2-T14  intake_writer: sidecar has detected_mime
    P2-T15  intake_writer: sidecar has workspace_hint (None by default)
    P2-T16  intake_writer: result dict has quarantine_dir key
    P2-T17  cli_connector: original_name populated from file
    P2-T18  cli_connector: original_path_or_uri populated from file (absolute)
    P2-T19  cli_connector: stdin capture has None original_name
    P2-T20  cli_connector: workspace_hint passed through
    P2-T21  chaseos CLI: doctor command exits 0 with pyproject.toml present
    P2-T22  chaseos CLI: intake ls runs without error
    P2-T23  chaseos CLI: capture file end-to-end via main()
    P2-T24  backward-compat: python -m runtime.capture.capture main() still works
    P2-T25  WORKED EXAMPLE: chaseos capture file -> quarantine boundary verified
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

# ── Test runner ────────────────────────────────────────────────────────────────

_PASS = 0
_FAIL = 0
_ERRORS: list[str] = []


def _ok(name: str) -> None:
    global _PASS
    _PASS += 1
    print(f"  PASS  {name}")


def _fail(name: str, reason: str) -> None:
    global _FAIL
    _FAIL += 1
    _ERRORS.append(f"{name}: {reason}")
    print(f"  FAIL  {name}: {reason}")


def _assert(cond: bool, name: str, msg: str = "") -> None:
    if cond:
        _ok(name)
    else:
        _fail(name, msg or "assertion failed")


def _run_test(label: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        _fail(label, f"EXCEPTION: {exc}\n{traceback.format_exc()}")


# ── Imports under test ─────────────────────────────────────────────────────────

from runtime.capture.content_packet import ContentPacket
from runtime.capture.router import (
    route_input_class,
    get_route_reason,
    QUARANTINE_SUBDIR,
)
from runtime.capture.intake_writer import write_intake
from runtime.capture.connectors.cli_connector import capture_from_cli
from runtime.capture.capture import capture_content, main as capture_main
from runtime.cli.main import main as chaseos_main


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_packet(**kwargs) -> ContentPacket:
    defaults = dict(
        content="Test content for Phase 8 Pass 2.",
        input_class="transcript",
        source_platform="youtube",
        title="Market Microstructure Pass 2 Test",
    )
    defaults.update(kwargs)
    return ContentPacket(**defaults)


def _vault_with_inputs() -> tempfile.TemporaryDirectory:
    """Return a temp dir with 03_INPUTS/ created."""
    tmp = tempfile.TemporaryDirectory()
    (Path(tmp.name) / "03_INPUTS").mkdir()
    return tmp


# ── P2-T01 to P2-T04: ContentPacket new fields ────────────────────────────────

def test_p2_t01():
    p = _make_packet(original_name="transcript.txt")
    _assert(p.original_name == "transcript.txt", "P2-T01a")
    p2 = _make_packet()
    _assert(p2.original_name is None, "P2-T01b", "default should be None")


def test_p2_t02():
    p = _make_packet(original_path_or_uri="/home/user/transcript.txt")
    _assert(p.original_path_or_uri == "/home/user/transcript.txt", "P2-T02a")
    p2 = _make_packet()
    _assert(p2.original_path_or_uri is None, "P2-T02b")


def test_p2_t03():
    p = _make_packet()
    _assert(p.detected_mime == "text/plain; charset=utf-8", "P2-T03a")
    p2 = _make_packet(detected_mime="application/pdf")
    _assert(p2.detected_mime == "application/pdf", "P2-T03b")


def test_p2_t04():
    p = _make_packet(workspace_hint="trading-2026")
    _assert(p.workspace_hint == "trading-2026", "P2-T04a")
    p2 = _make_packet()
    _assert(p2.workspace_hint is None, "P2-T04b")


# ── P2-T05 to P2-T07: Router quarantine boundary ──────────────────────────────

def test_p2_t05():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        path = route_input_class("transcript", vault)
        _assert("00_QUARANTINE" in str(path), "P2-T05a", f"path: {path}")
        _assert("Transcript-Raw" in str(path), "P2-T05b", f"path: {path}")
        _assert(path == vault / "03_INPUTS" / "00_QUARANTINE" / "Transcript-Raw",
                "P2-T05c", f"exact path wrong: {path}")


def test_p2_t06():
    reason = get_route_reason("transcript")
    _assert("transcript" in reason, "P2-T06a", f"reason: {reason}")
    _assert("00_QUARANTINE" in reason, "P2-T06b", f"reason: {reason}")
    _assert("Transcript-Raw" in reason, "P2-T06c", f"reason: {reason}")

    reason2 = get_route_reason("digest")
    _assert("digest" in reason2, "P2-T06d")
    _assert("Digests" in reason2, "P2-T06e")


def test_p2_t07():
    _assert(QUARANTINE_SUBDIR == "00_QUARANTINE", "P2-T07")


# ── P2-T08 to P2-T16: Sidecar schema v8.2 ────────────────────────────────────

def _write_and_sidecar(**kwargs) -> tuple[dict, dict]:
    """Write a packet and return (result, sidecar_dict)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(**kwargs), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        # Note: we need to keep the temp dir alive during sidecar read
        # Since we read inside the block, this is fine
        return result, sidecar


def test_p2_t08():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["schema_version"] == "8.3", "P2-T08",
                f"got: {sidecar.get('schema_version')}")


def test_p2_t09():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["quarantine_status"] == "pending-review", "P2-T09",
                f"got: {sidecar.get('quarantine_status')}")


def test_p2_t10():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["source_package_status"] == "not-ingested", "P2-T10",
                f"got: {sidecar.get('source_package_status')}")


def test_p2_t11():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(input_class="digest"), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        reason = sidecar.get("route_reason", "")
        _assert("digest" in reason, "P2-T11a", f"reason: {reason}")
        _assert("00_QUARANTINE" in reason, "P2-T11b", f"reason: {reason}")
        _assert("Digests" in reason, "P2-T11c", f"reason: {reason}")


def test_p2_t12():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(original_name="my-transcript.txt"), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["original_name"] == "my-transcript.txt", "P2-T12")


def test_p2_t13():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(
            original_path_or_uri="/home/chase/downloads/transcript.txt"
        ), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(
            sidecar["original_path_or_uri"] == "/home/chase/downloads/transcript.txt",
            "P2-T13"
        )


def test_p2_t14():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert("detected_mime" in sidecar, "P2-T14a")
        _assert(sidecar["detected_mime"] == "text/plain; charset=utf-8", "P2-T14b",
                f"got: {sidecar.get('detected_mime')}")


def test_p2_t15():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        # No workspace_hint — should be None
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert("workspace_hint" in sidecar, "P2-T15a")
        _assert(sidecar["workspace_hint"] is None, "P2-T15b")

        # With workspace_hint
        result2 = write_intake(_make_packet(workspace_hint="sic-workspace-1"), vault)
        sidecar2 = json.loads(Path(result2["sidecar_path"]).read_text())
        _assert(sidecar2["workspace_hint"] == "sic-workspace-1", "P2-T15c")


def test_p2_t16():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        _assert("quarantine_dir" in result, "P2-T16a")
        _assert("00_QUARANTINE" in result["quarantine_dir"], "P2-T16b",
                f"quarantine_dir: {result.get('quarantine_dir')}")


# ── P2-T17 to P2-T20: cli_connector pass-2 fields ────────────────────────────

def test_p2_t17():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "lecture.txt"
        f.write_text("Content here.", encoding="utf-8")
        packet = capture_from_cli(
            input_class="transcript",
            source_platform="youtube",
            title="Test",
            file_path=str(f),
        )
        _assert(packet.original_name == "lecture.txt", "P2-T17",
                f"got: {packet.original_name}")


def test_p2_t18():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "lecture.txt"
        f.write_text("Content here.", encoding="utf-8")
        packet = capture_from_cli(
            input_class="transcript",
            source_platform="youtube",
            title="Test",
            file_path=str(f),
        )
        expected = str(f.resolve())
        _assert(packet.original_path_or_uri == expected, "P2-T18",
                f"got: {packet.original_path_or_uri}")


def test_p2_t19():
    with patch("sys.stdin", io.StringIO("stdin content")):
        packet = capture_from_cli(
            input_class="clipboard",
            source_platform="manual",
            title="Stdin Test",
            file_path=None,
        )
    _assert(packet.original_name is None, "P2-T19a")
    _assert(packet.original_path_or_uri is None, "P2-T19b")


def test_p2_t20():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "note.txt"
        f.write_text("Note content.", encoding="utf-8")
        packet = capture_from_cli(
            input_class="source",
            source_platform="web",
            title="Test Note",
            file_path=str(f),
            workspace_hint="defi-research",
        )
        _assert(packet.workspace_hint == "defi-research", "P2-T20")


# ── P2-T21 to P2-T24: CLI commands ────────────────────────────────────────────

def test_p2_t21():
    """chaseos doctor: should exit 0 when vault is detected (pyproject.toml exists)."""
    # Run doctor from the real vault (where pyproject.toml exists)
    # We capture stdout to avoid noise
    with patch("sys.stdout", io.StringIO()) as mock_out:
        ret = chaseos_main(["doctor"])
    _assert(ret == 0, "P2-T21", f"doctor returned {ret}")


def test_p2_t22():
    """chaseos intake ls: should run without error."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        # Populate quarantine so there's something to list
        write_intake(_make_packet(), vault)
        with patch("sys.stdout", io.StringIO()) as mock_out:
            ret = chaseos_main(["intake", "ls", "--vault-root", str(vault)])
    _assert(ret == 0, "P2-T22a", f"intake ls returned {ret}")


def test_p2_t23():
    """chaseos capture file end-to-end via main()."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        # Write a temp file to capture
        src = Path(tmp) / "content.txt"
        src.write_text("DeFi lending mechanics explained.", encoding="utf-8")

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main([
                "capture", "file", str(src),
                "--class", "source",
                "--source", "web",
                "--title", "DeFi Lending Mechanics",
                "--vault-root", str(vault),
                "--json",
            ])

        _assert(ret == 0, "P2-T23a", f"exit code: {ret}")
        output = out.getvalue()
        envelope = json.loads(output)
        # CLI wraps captures in an envelope: {"ok": ..., "result": {...}, ...}
        result = envelope.get("result", envelope)
        _assert("filename" in result, "P2-T23b")
        _assert("quarantine_dir" in result, "P2-T23c")
        _assert("00_QUARANTINE" in result["quarantine_dir"], "P2-T23d",
                f"quarantine_dir: {result.get('quarantine_dir')}")
        _assert("source" in result["filename"], "P2-T23e")

        # Verify sidecar
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["original_name"] == "content.txt", "P2-T23f",
                f"got: {sidecar.get('original_name')}")
        _assert(sidecar["schema_version"] == "8.3", "P2-T23g")
        _assert(sidecar["quarantine_status"] == "pending-review", "P2-T23h")
        _assert(sidecar["source_package_status"] == "not-ingested", "P2-T23i")


def test_p2_t24():
    """Backward-compat: python -m runtime.capture.capture main() still works."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        src = Path(tmp) / "compat.txt"
        src.write_text("Backward compat test content.", encoding="utf-8")

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = capture_main([
                "--input-class", "clipboard",
                "--source-platform", "manual",
                "--title", "Compat Test",
                "--file", str(src),
                "--vault-root", str(vault),
                "--json",
            ])

        _assert(ret == 0, "P2-T24a", f"exit code: {ret}")
        envelope = json.loads(out.getvalue())
        result = envelope.get("result", envelope)
        _assert("quarantine_dir" in result, "P2-T24b")
        _assert("00_QUARANTINE" in result["quarantine_dir"], "P2-T24c")


# ── P2-T25: Worked Example ─────────────────────────────────────────────────────

def test_p2_t25():
    """
    WORKED EXAMPLE — chaseos capture file, Phase 8 Pass 2.

    Scenario:
        Chase has a Perplexity digest about crypto funding rates saved as
        "perplexity-digest-2026-03-27.txt". He runs:

          chaseos capture file perplexity-digest-2026-03-27.txt \\
              --class digest \\
              --source perplexity \\
              --title "Crypto Perps Funding Rate Deep Dive" \\
              --workspace "crypto-trading"

        Expected:
          1. File written to 03_INPUTS/00_QUARANTINE/Digests/
          2. Named: YYYYMMDD-HHMMSS__digest__perplexity__crypto-perps-funding-rate.md
          3. Sidecar: same name + .meta.json
          4. Sidecar schema v8.2
          5. original_name = "perplexity-digest-2026-03-27.txt"
          6. workspace_hint = "crypto-trading"
          7. quarantine_status = "pending-review"
          8. source_package_status = "not-ingested"
          9. promotion_status = "quarantine" (Gate-facing field unchanged)
          10. SIC NOT triggered (no SIC import, no SIC call)
    """
    digest_content = (
        "Crypto Perps Funding Rate Deep Dive\n\n"
        "Funding rates on perpetual futures markets reflect the balance between "
        "long and short interest. When longs dominate, funding is positive — "
        "longs pay shorts. During extreme speculation (e.g., BTC at ATH), "
        "funding rates can reach 0.1% per 8 hours (36.5% annualized). "
        "This creates carry opportunities for delta-neutral traders."
    )

    original_filename = "perplexity-digest-2026-03-27.txt"

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()

        # Create the source file
        src = Path(tmp) / original_filename
        src.write_text(digest_content, encoding="utf-8")

        # Run via canonical CLI
        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main([
                "capture", "file", str(src),
                "--class", "digest",
                "--source", "perplexity",
                "--title", "Crypto Perps Funding Rate Deep Dive",
                "--workspace", "crypto-trading",
                "--vault-root", str(vault),
                "--json",
            ])

        _assert(ret == 0, "P2-T25-exit-code", f"exit code: {ret}")
        envelope = json.loads(out.getvalue())
        result = envelope.get("result", envelope)

        # Quarantine boundary
        _assert(
            "00_QUARANTINE" in result["quarantine_dir"],
            "P2-T25-quarantine-boundary",
            f"quarantine_dir: {result.get('quarantine_dir')}",
        )
        _assert(
            "Digests" in result["quarantine_dir"],
            "P2-T25-subfolder",
            f"quarantine_dir: {result.get('quarantine_dir')}",
        )

        # Filename format
        filename = result["filename"]
        parts = filename.replace(".md", "").split("__")
        _assert(len(parts) == 4, "P2-T25-filename-parts", f"parts: {parts}")
        _assert(parts[1] == "digest", "P2-T25-class", f"class: {parts[1]}")
        _assert(parts[2] == "perplexity", "P2-T25-source", f"source: {parts[2]}")
        _assert("crypto-perps" in parts[3], "P2-T25-slug", f"slug: {parts[3]}")

        # Sidecar
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["schema_version"] == "8.3", "P2-T25-schema")
        _assert(sidecar["original_name"] == original_filename, "P2-T25-original-name",
                f"got: {sidecar.get('original_name')}")
        _assert(sidecar["workspace_hint"] == "crypto-trading", "P2-T25-workspace-hint")
        _assert(sidecar["quarantine_status"] == "pending-review", "P2-T25-quarantine-status")
        _assert(sidecar["source_package_status"] == "not-ingested", "P2-T25-sp-status")
        _assert(sidecar["promotion_status"] == "quarantine", "P2-T25-promotion-status")
        _assert("00_QUARANTINE" in sidecar["route_reason"], "P2-T25-route-reason",
                f"route_reason: {sidecar.get('route_reason')}")

        # SHA256
        expected_sha = hashlib.sha256(digest_content.encode("utf-8")).hexdigest()
        _assert(sidecar["content_sha256"] == expected_sha, "P2-T25-sha256")

        # Print worked example
        print()
        print("  === WORKED EXAMPLE: chaseos capture file (Pass 2) ===")
        print(f"  Command:    chaseos capture file {original_filename} --class digest")
        print(f"              --source perplexity --title '...' --workspace crypto-trading")
        print(f"  Filename:   {filename}")
        print(f"  Quarantine: {result['quarantine_dir']}")
        print(f"  Schema:     v{sidecar['schema_version']}")
        print(f"  original_name: {sidecar['original_name']}")
        print(f"  workspace_hint: {sidecar['workspace_hint']}")
        print(f"  quarantine_status: {sidecar['quarantine_status']}")
        print(f"  source_package_status: {sidecar['source_package_status']}")
        print(f"  promotion_status: {sidecar['promotion_status']}")
        print(f"  route_reason: {sidecar['route_reason']}")
        print()
        print("  SIC was NOT triggered. Capture -> quarantine only.")
        print("  Next: human review -> Gate promotion -> SIC ingestion (separate step).")
        print()


# ── Runner ─────────────────────────────────────────────────────────────────────

_TESTS = [
    ("P2-T01  ContentPacket: original_name field", test_p2_t01),
    ("P2-T02  ContentPacket: original_path_or_uri field", test_p2_t02),
    ("P2-T03  ContentPacket: detected_mime defaults to text/plain", test_p2_t03),
    ("P2-T04  ContentPacket: workspace_hint field", test_p2_t04),
    ("P2-T05  router: route_input_class targets 00_QUARANTINE/", test_p2_t05),
    ("P2-T06  router: get_route_reason returns correct string", test_p2_t06),
    ("P2-T07  router: QUARANTINE_SUBDIR == 00_QUARANTINE", test_p2_t07),
    ("P2-T08  intake_writer: sidecar schema version is 8.2", test_p2_t08),
    ("P2-T09  intake_writer: quarantine_status = pending-review", test_p2_t09),
    ("P2-T10  intake_writer: source_package_status = not-ingested", test_p2_t10),
    ("P2-T11  intake_writer: route_reason correct pattern", test_p2_t11),
    ("P2-T12  intake_writer: original_name in sidecar", test_p2_t12),
    ("P2-T13  intake_writer: original_path_or_uri in sidecar", test_p2_t13),
    ("P2-T14  intake_writer: detected_mime in sidecar", test_p2_t14),
    ("P2-T15  intake_writer: workspace_hint in sidecar", test_p2_t15),
    ("P2-T16  intake_writer: result has quarantine_dir key", test_p2_t16),
    ("P2-T17  cli_connector: original_name from file", test_p2_t17),
    ("P2-T18  cli_connector: original_path_or_uri from file (absolute)", test_p2_t18),
    ("P2-T19  cli_connector: stdin capture has None original fields", test_p2_t19),
    ("P2-T20  cli_connector: workspace_hint passed through", test_p2_t20),
    ("P2-T21  chaseos CLI: doctor exits 0", test_p2_t21),
    ("P2-T22  chaseos CLI: intake ls runs without error", test_p2_t22),
    ("P2-T23  chaseos CLI: capture file end-to-end via main()", test_p2_t23),
    ("P2-T24  backward-compat: python -m runtime.capture.capture still works", test_p2_t24),
    ("P2-T25  WORKED EXAMPLE: chaseos capture file -> quarantine verified", test_p2_t25),
]


def main() -> int:
    print("ChaseOS Phase 8 Pass 2 -- Test Suite")
    print("=" * 60)
    for label, fn in _TESTS:
        print(f"\n[{label}]")
        _run_test(label, fn)

    print()
    print("=" * 60)
    print(f"Results: {_PASS} passed, {_FAIL} failed")
    if _ERRORS:
        print("\nFailures:")
        for e in _ERRORS:
            print(f"  - {e}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
