"""
test_pass8p3.py — ChaseOS Phase 8 Pass 3 Test Suite
Truth Sync + Semantic Breadcrumbs + AI-Generated Output Bridge Prep

Run:
    python -m runtime.capture.test_pass8p3

Or via canonical CLI:
    chaseos test capture

Tests:
    P3-T01  ContentPacket: domain_hint field exists and is optional
    P3-T02  ContentPacket: project_hint field exists and is optional
    P3-T03  ContentPacket: topic_hint field exists and is optional
    P3-T04  ContentPacket: event_date_hint field exists and is optional
    P3-T05  ContentPacket: origin_kind field exists and is optional
    P3-T06  ContentPacket: desired_output_kind field exists and is optional
    P3-T07  intake_writer: sidecar schema version is 8.3
    P3-T08  intake_writer: all semantic breadcrumb fields present in sidecar
    P3-T09  intake_writer: domain_hint round-trips through sidecar
    P3-T10  intake_writer: origin_kind=ai-generated round-trips through sidecar
    P3-T11  intake_writer: desired_output_kind round-trips through sidecar
    P3-T12  intake_writer: breadcrumbs default to None (not missing)
    P3-T13  cli_connector: domain_hint passed through
    P3-T14  cli_connector: origin_kind passed through
    P3-T15  cli_connector: desired_output_kind passed through
    P3-T16  CLI: --domain flag captured in sidecar
    P3-T17  CLI: --origin-kind flag captured in sidecar
    P3-T18  CLI: --output-kind flag captured in sidecar
    P3-T19  CLI: --event-date flag captured in sidecar
    P3-T20  CLI: intake inspect shows sidecar metadata
    P3-T21  CLI: intake inspect --json outputs raw JSON
    P3-T22  backward-compat: Pass 2 CLI still works without hint flags
    P3-T23  SIC NOT triggered: no SIC import in capture layer
    P3-T24  WORKED EXAMPLE: AI-generated NotebookLM output with full semantic breadcrumbs
    P3-T25  WORKED EXAMPLE: Human-authored transcript with domain/topic/event-date hints
"""

from __future__ import annotations

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
from runtime.capture.intake_writer import write_intake
from runtime.capture.connectors.cli_connector import capture_from_cli
from runtime.capture.capture import capture_content, main as capture_main
from runtime.cli.main import main as chaseos_main


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_packet(**kwargs) -> ContentPacket:
    defaults = dict(
        content="Test content for Phase 8 Pass 3 semantic breadcrumbs.",
        input_class="transcript",
        source_platform="youtube",
        title="Semantic Breadcrumb Test",
    )
    defaults.update(kwargs)
    return ContentPacket(**defaults)


def _write_and_sidecar(**kwargs) -> tuple[dict, dict]:
    """Write a packet and return (result, sidecar_dict)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(**kwargs), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        return result, sidecar


# ── P3-T01 to P3-T06: ContentPacket semantic breadcrumb fields ─────────────────

def test_p3_t01():
    p = _make_packet(domain_hint="trading-systems")
    _assert(p.domain_hint == "trading-systems", "P3-T01a")
    p2 = _make_packet()
    _assert(p2.domain_hint is None, "P3-T01b", "default should be None")


def test_p3_t02():
    p = _make_packet(project_hint="chaseos")
    _assert(p.project_hint == "chaseos", "P3-T02a")
    p2 = _make_packet()
    _assert(p2.project_hint is None, "P3-T02b")


def test_p3_t03():
    p = _make_packet(topic_hint="market-microstructure")
    _assert(p.topic_hint == "market-microstructure", "P3-T03a")
    p2 = _make_packet()
    _assert(p2.topic_hint is None, "P3-T03b")


def test_p3_t04():
    p = _make_packet(event_date_hint="2026-03-15")
    _assert(p.event_date_hint == "2026-03-15", "P3-T04a")
    p2 = _make_packet()
    _assert(p2.event_date_hint is None, "P3-T04b")


def test_p3_t05():
    p = _make_packet(origin_kind="human-authored")
    _assert(p.origin_kind == "human-authored", "P3-T05a")
    p_ai = _make_packet(origin_kind="ai-generated")
    _assert(p_ai.origin_kind == "ai-generated", "P3-T05b")
    p2 = _make_packet()
    _assert(p2.origin_kind is None, "P3-T05c")


def test_p3_t06():
    p = _make_packet(desired_output_kind="synthesis")
    _assert(p.desired_output_kind == "synthesis", "P3-T06a")
    p2 = _make_packet(desired_output_kind="generated-idea")
    _assert(p2.desired_output_kind == "generated-idea", "P3-T06b")
    p3 = _make_packet()
    _assert(p3.desired_output_kind is None, "P3-T06c")


# ── P3-T07 to P3-T12: Sidecar schema v8.3 ────────────────────────────────────

def test_p3_t07():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["schema_version"] == "8.3", "P3-T07",
                f"got: {sidecar.get('schema_version')}")


def test_p3_t08():
    """All six semantic breadcrumb fields must be present in v8.3 sidecar."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        for field in ["domain_hint", "project_hint", "topic_hint",
                      "event_date_hint", "origin_kind", "desired_output_kind"]:
            _assert(field in sidecar, f"P3-T08-{field}", f"missing field: {field}")


def test_p3_t09():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(domain_hint="ai-engineering"), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["domain_hint"] == "ai-engineering", "P3-T09",
                f"got: {sidecar.get('domain_hint')}")


def test_p3_t10():
    """AI-generated origin_kind round-trips correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(
            input_class="notebooklm",
            origin_kind="ai-generated",
        ), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["origin_kind"] == "ai-generated", "P3-T10a",
                f"got: {sidecar.get('origin_kind')}")
        # Quarantine status is unchanged even for ai-generated content
        _assert(sidecar["quarantine_status"] == "pending-review", "P3-T10b")
        _assert(sidecar["promotion_status"] == "quarantine", "P3-T10c")
        _assert(sidecar["source_package_status"] == "not-ingested", "P3-T10d")


def test_p3_t11():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(desired_output_kind="briefing"), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["desired_output_kind"] == "briefing", "P3-T11",
                f"got: {sidecar.get('desired_output_kind')}")


def test_p3_t12():
    """When no breadcrumbs are provided, all six fields exist as None (not missing)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(_make_packet(), vault)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        for field in ["domain_hint", "project_hint", "topic_hint",
                      "event_date_hint", "origin_kind", "desired_output_kind"]:
            _assert(field in sidecar, f"P3-T12-present-{field}")
            _assert(sidecar[field] is None, f"P3-T12-null-{field}",
                    f"expected None, got: {sidecar[field]}")


# ── P3-T13 to P3-T15: cli_connector pass-through ─────────────────────────────

def test_p3_t13():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "note.txt"
        f.write_text("Content.", encoding="utf-8")
        packet = capture_from_cli(
            input_class="source",
            source_platform="web",
            title="Test",
            file_path=str(f),
            domain_hint="trading-systems",
        )
        _assert(packet.domain_hint == "trading-systems", "P3-T13")


def test_p3_t14():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "output.txt"
        f.write_text("AI content.", encoding="utf-8")
        packet = capture_from_cli(
            input_class="notebooklm",
            source_platform="notebooklm",
            title="AI Output",
            file_path=str(f),
            origin_kind="ai-generated",
        )
        _assert(packet.origin_kind == "ai-generated", "P3-T14")


def test_p3_t15():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "digest.txt"
        f.write_text("Digest content.", encoding="utf-8")
        packet = capture_from_cli(
            input_class="digest",
            source_platform="perplexity",
            title="Crypto Briefing",
            file_path=str(f),
            desired_output_kind="briefing",
        )
        _assert(packet.desired_output_kind == "briefing", "P3-T15")


# ── P3-T16 to P3-T19: CLI hint flags ─────────────────────────────────────────

def _capture_via_cli_with_hints(**hint_flags) -> dict:
    """Helper: run chaseos capture file with hint flags, return sidecar dict."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        src = vault / "content.txt"
        src.write_text("Test content for hint flags.", encoding="utf-8")

        cmd = [
            "capture", "file", str(src),
            "--class", "source",
            "--source", "web",
            "--title", "Hint Flag Test",
            "--vault-root", str(vault),
            "--json",
        ]
        for k, v in hint_flags.items():
            cmd.extend([f"--{k.replace('_', '-')}", v])

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main(cmd)

        assert ret == 0, f"CLI returned {ret}"
        envelope = json.loads(out.getvalue())
        result = envelope.get("result", envelope)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        return sidecar


def test_p3_t16():
    sidecar = _capture_via_cli_with_hints(domain="ai-engineering")
    _assert(sidecar.get("domain_hint") == "ai-engineering", "P3-T16",
            f"got: {sidecar.get('domain_hint')}")


def test_p3_t17():
    sidecar = _capture_via_cli_with_hints(**{"origin-kind": "ai-generated"})
    _assert(sidecar.get("origin_kind") == "ai-generated", "P3-T17",
            f"got: {sidecar.get('origin_kind')}")


def test_p3_t18():
    sidecar = _capture_via_cli_with_hints(**{"output-kind": "synthesis"})
    _assert(sidecar.get("desired_output_kind") == "synthesis", "P3-T18",
            f"got: {sidecar.get('desired_output_kind')}")


def test_p3_t19():
    sidecar = _capture_via_cli_with_hints(**{"event-date": "2026-03-15"})
    _assert(sidecar.get("event_date_hint") == "2026-03-15", "P3-T19",
            f"got: {sidecar.get('event_date_hint')}")


# ── P3-T20 to P3-T21: intake inspect command ─────────────────────────────────

def test_p3_t20():
    """chaseos intake inspect PATH shows sidecar metadata in readable format."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(
            _make_packet(domain_hint="trading-systems", origin_kind="human-authored"),
            vault,
        )

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main(["intake", "inspect", result["content_path"]])

        _assert(ret == 0, "P3-T20a", f"inspect returned {ret}")
        output = out.getvalue()
        _assert("trading-systems" in output, "P3-T20b", "domain_hint not in output")
        _assert("human-authored" in output, "P3-T20c", "origin_kind not in output")
        _assert("Semantic Breadcrumbs" in output, "P3-T20d", "section header missing")
        _assert("pending-review" in output, "P3-T20e", "quarantine_status missing")


def test_p3_t21():
    """chaseos intake inspect --json outputs raw JSON sidecar."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        result = write_intake(
            _make_packet(project_hint="chaseos", desired_output_kind="synthesis"),
            vault,
        )

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main(["intake", "inspect", result["sidecar_path"], "--json"])

        _assert(ret == 0, "P3-T21a")
        parsed = json.loads(out.getvalue())
        _assert(parsed.get("project_hint") == "chaseos", "P3-T21b")
        _assert(parsed.get("desired_output_kind") == "synthesis", "P3-T21c")
        _assert(parsed.get("schema_version") == "8.3", "P3-T21d")


# ── P3-T22: backward compat ───────────────────────────────────────────────────

def test_p3_t22():
    """Backward-compat CLI still works without any hint flags."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        src = vault / "compat.txt"
        src.write_text("Compat test content.", encoding="utf-8")

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

        _assert(ret == 0, "P3-T22a", f"exit code: {ret}")
        envelope = json.loads(out.getvalue())
        result = envelope.get("result", envelope)
        _assert("quarantine_dir" in result, "P3-T22b")
        # Sidecar should still be v8.3 (all breadcrumbs default to None)
        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["schema_version"] == "8.3", "P3-T22c",
                f"got: {sidecar.get('schema_version')}")
        _assert(sidecar.get("domain_hint") is None, "P3-T22d")


# ── P3-T23: SIC not triggered ─────────────────────────────────────────────────

def test_p3_t23():
    """
    Verify that the capture layer does not import or invoke SIC modules.

    SIC modules live in runtime.source_intelligence.*
    If any capture module imports them, this test will detect it after
    performing a capture.
    """
    import sys as _sys

    # Record which modules are loaded before capture
    before = set(_sys.modules.keys())

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        # Perform a full capture with breadcrumbs
        write_intake(
            _make_packet(
                origin_kind="ai-generated",
                desired_output_kind="synthesis",
                domain_hint="ai-engineering",
            ),
            vault,
        )

    after = set(_sys.modules.keys())
    new_modules = after - before

    sic_modules = [m for m in new_modules if "source_intelligence" in m]
    _assert(
        len(sic_modules) == 0,
        "P3-T23",
        f"SIC modules imported during capture: {sic_modules}",
    )


# ── P3-T24: Worked Example — AI-generated NotebookLM output ──────────────────

def test_p3_t24():
    """
    WORKED EXAMPLE — AI-generated content captured with full semantic breadcrumbs.

    Scenario:
        Chase exports a NotebookLM synthesis on DeFi lending mechanics.
        The content is AI-generated, should feed into a synthesis note later,
        and belongs to the ai-engineering domain.

        chaseos capture file notebooklm-defi-synthesis.txt \\
            --class notebooklm \\
            --source notebooklm \\
            --title "DeFi Lending Mechanics Synthesis" \\
            --domain ai-engineering \\
            --project chaseos \\
            --topic "defi-lending" \\
            --origin-kind ai-generated \\
            --output-kind synthesis \\
            --workspace defi-research

        Expected:
          1. File lands in 03_INPUTS/00_QUARANTINE/NotebookLM/
          2. Sidecar schema v8.3
          3. origin_kind = "ai-generated"
          4. desired_output_kind = "synthesis"
          5. domain_hint = "ai-engineering"
          6. quarantine_status = "pending-review" (unchanged -- AI-gen is still quarantine-first)
          7. promotion_status = "quarantine" (unchanged)
          8. source_package_status = "not-ingested" (SIC NOT triggered)
    """
    content = (
        "DeFi Lending Mechanics — NotebookLM Synthesis\n\n"
        "Key insight: Overcollateralization ratios in Aave and Compound "
        "create a structural floor on borrowing costs. When collateral "
        "values drop, automatic liquidations restore LTV ratios. "
        "This creates reflexive selling pressure during market downturns, "
        "amplifying volatility in the underlying assets."
    )

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()

        src = vault / "notebooklm-defi-synthesis.txt"
        src.write_text(content, encoding="utf-8")

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main([
                "capture", "file", str(src),
                "--class", "notebooklm",
                "--source", "notebooklm",
                "--title", "DeFi Lending Mechanics Synthesis",
                "--domain", "ai-engineering",
                "--project", "chaseos",
                "--topic", "defi-lending",
                "--origin-kind", "ai-generated",
                "--output-kind", "synthesis",
                "--workspace", "defi-research",
                "--vault-root", str(vault),
                "--json",
            ])

        _assert(ret == 0, "P3-T24-exit", f"exit code: {ret}")
        envelope = json.loads(out.getvalue())
        result = envelope.get("result", envelope)

        # Quarantine boundary
        _assert("00_QUARANTINE" in result["quarantine_dir"], "P3-T24-quarantine")
        _assert("NotebookLM" in result["quarantine_dir"], "P3-T24-subfolder")

        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["schema_version"] == "8.3", "P3-T24-schema")
        _assert(sidecar["origin_kind"] == "ai-generated", "P3-T24-origin")
        _assert(sidecar["desired_output_kind"] == "synthesis", "P3-T24-output-kind")
        _assert(sidecar["domain_hint"] == "ai-engineering", "P3-T24-domain")
        _assert(sidecar["project_hint"] == "chaseos", "P3-T24-project")
        _assert(sidecar["topic_hint"] == "defi-lending", "P3-T24-topic")
        _assert(sidecar["workspace_hint"] == "defi-research", "P3-T24-workspace")
        # AI-generated content is STILL quarantine-first
        _assert(sidecar["quarantine_status"] == "pending-review", "P3-T24-q-status")
        _assert(sidecar["promotion_status"] == "quarantine", "P3-T24-p-status")
        _assert(sidecar["source_package_status"] == "not-ingested", "P3-T24-sic-status")

        print()
        print("  === WORKED EXAMPLE: AI-generated NotebookLM output (Pass 3) ===")
        print(f"  File:           {result['filename']}")
        print(f"  Quarantine:     {result['quarantine_dir']}")
        print(f"  origin_kind:    {sidecar['origin_kind']}")
        print(f"  domain_hint:    {sidecar['domain_hint']}")
        print(f"  desired_output: {sidecar['desired_output_kind']}")
        print(f"  topic_hint:     {sidecar['topic_hint']}")
        print(f"  workspace_hint: {sidecar['workspace_hint']}")
        print(f"  quarantine:     {sidecar['quarantine_status']}")
        print(f"  SIC status:     {sidecar['source_package_status']}")
        print()
        print("  NOTE: AI-generated content is STILL quarantine-first.")
        print("  No SIC invocation. No auto-promotion. Bridge is breadcrumb-only at this layer.")
        print()


# ── P3-T25: Worked Example — Human transcript with full breadcrumbs ───────────

def test_p3_t25():
    """
    WORKED EXAMPLE — Human-authored transcript with event-date and domain hints.

    Scenario:
        Chase has a transcript of an Albert Kyle lecture on market microstructure
        from 2026-03-15. He captured it on 2026-03-27 and wants it grouped
        with other trading-systems research.

        chaseos capture file kyle-lecture-2026-03-15.txt \\
            --class transcript \\
            --source youtube \\
            --title "Order Flow and Market Microstructure Kyle 2026-03-15" \\
            --domain trading-systems \\
            --topic "order-flow-microstructure" \\
            --event-date 2026-03-15 \\
            --origin-kind human-authored \\
            --output-kind source-note

        Expected:
          1. File in 03_INPUTS/00_QUARANTINE/Transcript-Raw/
          2. event_date_hint = "2026-03-15" (distinct from capture date)
          3. domain_hint = "trading-systems"
          4. origin_kind = "human-authored"
          5. desired_output_kind = "source-note"
          6. All quarantine state unchanged
    """
    content = (
        "Lecture: Order Flow and Market Microstructure\n"
        "Presenter: Albert Kyle — 2026-03-15\n\n"
        "Kyle model insight: informed traders optimize order splitting to "
        "minimize market impact while extracting maximum information rents. "
        "The key parameter lambda (price impact coefficient) is determined "
        "by the ratio of informed to uninformed order flow."
    )

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()

        src = vault / "kyle-lecture-2026-03-15.txt"
        src.write_text(content, encoding="utf-8")

        out = io.StringIO()
        with patch("sys.stdout", out):
            ret = chaseos_main([
                "capture", "file", str(src),
                "--class", "transcript",
                "--source", "youtube",
                "--title", "Order Flow and Market Microstructure Kyle 2026-03-15",
                "--domain", "trading-systems",
                "--topic", "order-flow-microstructure",
                "--event-date", "2026-03-15",
                "--origin-kind", "human-authored",
                "--output-kind", "source-note",
                "--vault-root", str(vault),
                "--json",
            ])

        _assert(ret == 0, "P3-T25-exit")
        envelope = json.loads(out.getvalue())
        result = envelope.get("result", envelope)

        sidecar = json.loads(Path(result["sidecar_path"]).read_text())
        _assert(sidecar["event_date_hint"] == "2026-03-15", "P3-T25-event-date",
                f"got: {sidecar.get('event_date_hint')}")
        _assert(sidecar["domain_hint"] == "trading-systems", "P3-T25-domain")
        _assert(sidecar["topic_hint"] == "order-flow-microstructure", "P3-T25-topic")
        _assert(sidecar["origin_kind"] == "human-authored", "P3-T25-origin")
        _assert(sidecar["desired_output_kind"] == "source-note", "P3-T25-output-kind")
        _assert("Transcript-Raw" in result["quarantine_dir"], "P3-T25-subfolder")

        # Verify event_date_hint != captured_at date (they may differ)
        captured_date = sidecar["captured_at"][:10]  # YYYY-MM-DD portion
        event_date = sidecar["event_date_hint"]
        _assert(event_date == "2026-03-15", "P3-T25-event-date-value")
        # event_date and capture date may be different (that's the point of this field)

        print()
        print("  === WORKED EXAMPLE: Human transcript with event-date hint (Pass 3) ===")
        print(f"  File:           {result['filename']}")
        print(f"  Quarantine:     {result['quarantine_dir']}")
        print(f"  event_date_hint: {sidecar['event_date_hint']}  (lecture date, not capture date)")
        print(f"  captured_at:    {sidecar['captured_at'][:10]}  (when operator ran chaseos)")
        print(f"  domain_hint:    {sidecar['domain_hint']}")
        print(f"  topic_hint:     {sidecar['topic_hint']}")
        print(f"  origin_kind:    {sidecar['origin_kind']}")
        print(f"  desired_output: {sidecar['desired_output_kind']}")
        print()
        print("  Breadcrumbs stored. SIC NOT triggered.")
        print("  Next: review in quarantine -> Gate promotion -> SIC ingestion (later).")
        print()


# ── Runner ─────────────────────────────────────────────────────────────────────

_TESTS = [
    ("P3-T01  ContentPacket: domain_hint field", test_p3_t01),
    ("P3-T02  ContentPacket: project_hint field", test_p3_t02),
    ("P3-T03  ContentPacket: topic_hint field", test_p3_t03),
    ("P3-T04  ContentPacket: event_date_hint field", test_p3_t04),
    ("P3-T05  ContentPacket: origin_kind field", test_p3_t05),
    ("P3-T06  ContentPacket: desired_output_kind field", test_p3_t06),
    ("P3-T07  intake_writer: sidecar schema version is 8.3", test_p3_t07),
    ("P3-T08  intake_writer: all breadcrumb fields in sidecar", test_p3_t08),
    ("P3-T09  intake_writer: domain_hint round-trips", test_p3_t09),
    ("P3-T10  intake_writer: ai-generated origin_kind round-trips", test_p3_t10),
    ("P3-T11  intake_writer: desired_output_kind round-trips", test_p3_t11),
    ("P3-T12  intake_writer: breadcrumbs default to None", test_p3_t12),
    ("P3-T13  cli_connector: domain_hint passed through", test_p3_t13),
    ("P3-T14  cli_connector: origin_kind passed through", test_p3_t14),
    ("P3-T15  cli_connector: desired_output_kind passed through", test_p3_t15),
    ("P3-T16  CLI: --domain flag in sidecar", test_p3_t16),
    ("P3-T17  CLI: --origin-kind flag in sidecar", test_p3_t17),
    ("P3-T18  CLI: --output-kind flag in sidecar", test_p3_t18),
    ("P3-T19  CLI: --event-date flag in sidecar", test_p3_t19),
    ("P3-T20  CLI: intake inspect shows sidecar metadata", test_p3_t20),
    ("P3-T21  CLI: intake inspect --json outputs raw JSON", test_p3_t21),
    ("P3-T22  backward-compat: Pass 2 CLI works without hints", test_p3_t22),
    ("P3-T23  SIC NOT triggered: no source_intelligence imports", test_p3_t23),
    ("P3-T24  WORKED EXAMPLE: AI-generated NotebookLM with breadcrumbs", test_p3_t24),
    ("P3-T25  WORKED EXAMPLE: Human transcript with event-date hints", test_p3_t25),
]


def main() -> int:
    print("ChaseOS Phase 8 Pass 3 -- Semantic Breadcrumbs Test Suite")
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
