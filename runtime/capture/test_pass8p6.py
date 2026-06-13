"""
test_pass8p6.py — ChaseOS Phase 8 Pass 6 Test Suite
SHA-256 Dedup Registry + Feed Recapture Protection

Run:
    python -m runtime.capture.test_pass8p6

Or via canonical CLI:
    chaseos test capture

Tests:
    P6-T01  dedup_registry: registry_path returns .chaseos/dedup_registry.json under vault root
    P6-T02  dedup_registry: load_registry returns empty registry when file does not exist
    P6-T03  dedup_registry: is_duplicate returns False for unknown sha256
    P6-T04  dedup_registry: register_capture adds entry; is_duplicate returns True for same sha256
    P6-T05  dedup_registry: get_entry returns None for unknown sha256
    P6-T06  dedup_registry: get_entry returns entry dict for registered sha256
    P6-T07  dedup_registry: save + load round-trip preserves all entry fields
    P6-T08  dedup_registry: register_capture does not overwrite existing entry (first-capture wins)
    P6-T09  dedup_registry: empty registry on corrupt file (fail-open)
    P6-T10  capture_content: normal capture writes file and returns is_duplicate=False
    P6-T11  capture_content: duplicate capture returns is_duplicate=True with no new file written
    P6-T12  capture_content: duplicate result has correct content_sha256 and duplicate_of fields
    P6-T13  capture_content: registry file is created after first capture
    P6-T14  capture_content: registry persists across multiple sequential captures
    P6-T15  capture_content: different content (different SHA) is not a duplicate
    P6-T16  rss: second run on same feed items returns duplicate results
    P6-T17  rss: first-run captures count = total items; second-run duplicate count = same total
    P6-T18  CLI: capture rss --json includes duplicate_count key
    P6-T19  CLI: capture rss human output shows duplicates line on second run
    P6-T20  CLI: intake dedup-stats shows entry count
    P6-T21  CLI: intake dedup-stats --json returns parseable JSON with entry_count
    P6-T22  backward-compat: capture file duplicate detection works
    P6-T23  backward-compat: capture file still works normally when not a duplicate
    P6-T24  dedup_registry: build_registry_entry returns dict with all expected keys
    P6-T25  capture_content: duplicate result does not write a new quarantine content file
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

from runtime.capture.dedup_registry import (
    registry_path,
    load_registry,
    save_registry,
    is_duplicate,
    get_entry,
    register_capture,
    build_registry_entry,
    _empty_registry,
    REGISTRY_SCHEMA_VERSION,
)
from runtime.capture.content_packet import ContentPacket, INPUT_CLASS_SOURCE
from runtime.capture.capture import capture_content
from runtime.cli.main import main as chaseos_main


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _make_vault(tmp: str) -> Path:
    """Create a minimal vault structure in a temp directory."""
    vault = Path(tmp)
    (vault / "03_INPUTS").mkdir(parents=True, exist_ok=True)
    return vault


def _make_packet(content: str = "Test content.", title: str = "Test Title") -> ContentPacket:
    return ContentPacket(
        content=content,
        input_class=INPUT_CLASS_SOURCE,
        source_platform="test-platform",
        title=title,
        source_url="https://example.com/article",
        capture_method="cli",
    )


def _content_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── RSS fixture ────────────────────────────────────────────────────────────────

_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Dedup Test Feed</title>
    <item>
      <title>Article One</title>
      <link>https://example.com/article-one</link>
      <description>Content for article one.</description>
      <pubDate>Mon, 28 Mar 2026 14:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/article-two</link>
      <description>Content for article two.</description>
      <pubDate>Mon, 28 Mar 2026 13:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""

def _mock_fetch_feed(url, timeout=30):
    return _RSS_FEED


# ── P6-T01 to P6-T09: dedup_registry module ───────────────────────────────────

def test_p6_t01():
    """registry_path returns .chaseos/dedup_registry.json under vault root."""
    vault = Path("/fake/vault")
    path = registry_path(vault)
    _assert(str(path).endswith("dedup_registry.json"), "P6-T01a",
            f"got: {path}")
    _assert(".chaseos" in str(path), "P6-T01b",
            f".chaseos not in path: {path}")
    _assert(str(path) == str(vault / ".chaseos" / "dedup_registry.json"), "P6-T01c")


def test_p6_t02():
    """load_registry returns empty registry when file does not exist."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        reg = load_registry(vault)
        _assert(isinstance(reg, dict), "P6-T02a")
        _assert("entries" in reg, "P6-T02b", f"got keys: {list(reg.keys())}")
        _assert(reg["entries"] == {}, "P6-T02c", f"entries not empty: {reg['entries']}")
        _assert(reg.get("schema_version") == REGISTRY_SCHEMA_VERSION, "P6-T02d")


def test_p6_t03():
    """is_duplicate returns False for unknown sha256."""
    reg = _empty_registry()
    _assert(not is_duplicate("deadbeef" * 8, reg), "P6-T03")


def test_p6_t04():
    """register_capture adds entry; is_duplicate returns True for same sha256."""
    reg = _empty_registry()
    sha = "a" * 64
    entry = build_registry_entry(
        content_sha256=sha, capture_id="test-id",
        first_captured_at="2026-03-28T12:00:00+00:00",
        title="T", source_platform="web", source_url=None,
        input_class="source", capture_method="cli",
    )
    _assert(not is_duplicate(sha, reg), "P6-T04a-before")
    register_capture(sha, entry, reg)
    _assert(is_duplicate(sha, reg), "P6-T04b-after",
            f"sha not found after register; entries={list(reg['entries'].keys())[:3]}")


def test_p6_t05():
    """get_entry returns None for unknown sha256."""
    reg = _empty_registry()
    _assert(get_entry("unknown-sha", reg) is None, "P6-T05")


def test_p6_t06():
    """get_entry returns entry dict for registered sha256."""
    reg = _empty_registry()
    sha = "b" * 64
    entry = build_registry_entry(
        content_sha256=sha, capture_id="cap-123",
        first_captured_at="2026-03-28T00:00:00+00:00",
        title="Article", source_platform="rss", source_url="https://x.com",
        input_class="source", capture_method="rss",
    )
    register_capture(sha, entry, reg)
    retrieved = get_entry(sha, reg)
    _assert(retrieved is not None, "P6-T06a")
    _assert(retrieved["capture_id"] == "cap-123", "P6-T06b",
            f"got: {retrieved.get('capture_id')!r}")
    _assert(retrieved["source_platform"] == "rss", "P6-T06c")


def test_p6_t07():
    """save + load round-trip preserves all entry fields."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        sha = "c" * 64
        reg = _empty_registry()
        entry = build_registry_entry(
            content_sha256=sha, capture_id="uuid-xyz",
            first_captured_at="2026-03-28T09:00:00+00:00",
            title="Round-trip test", source_platform="web",
            source_url="https://example.com", input_class="digest",
            capture_method="cli",
        )
        register_capture(sha, reg, reg)   # wrong — let's do it right:
        reg2 = _empty_registry()
        register_capture(sha, entry, reg2)
        save_registry(vault, reg2)

        loaded = load_registry(vault)
        _assert("entries" in loaded, "P6-T07a")
        _assert(sha in loaded["entries"], "P6-T07b")
        retrieved = loaded["entries"][sha]
        _assert(retrieved["capture_id"] == "uuid-xyz", "P6-T07c",
                f"got: {retrieved.get('capture_id')!r}")
        _assert(retrieved["source_url"] == "https://example.com", "P6-T07d")


def test_p6_t08():
    """register_capture does not overwrite existing entry (first-capture wins)."""
    reg = _empty_registry()
    sha = "d" * 64
    entry1 = build_registry_entry(
        content_sha256=sha, capture_id="first-id",
        first_captured_at="2026-01-01T00:00:00+00:00",
        title="First", source_platform="a", source_url=None,
        input_class="source", capture_method="cli",
    )
    entry2 = build_registry_entry(
        content_sha256=sha, capture_id="second-id",
        first_captured_at="2026-06-01T00:00:00+00:00",
        title="Second (should not overwrite)", source_platform="b", source_url=None,
        input_class="source", capture_method="rss",
    )
    register_capture(sha, entry1, reg)
    register_capture(sha, entry2, reg)  # should be no-op
    _assert(reg["entries"][sha]["capture_id"] == "first-id", "P6-T08",
            f"got: {reg['entries'][sha].get('capture_id')!r} (first-capture-wins violated)")


def test_p6_t09():
    """load_registry returns empty registry when file is corrupt (fail-open)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        path = registry_path(vault)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("NOT VALID JSON {{{", encoding="utf-8")
        reg = load_registry(vault)
        _assert(isinstance(reg, dict), "P6-T09a")
        _assert(reg.get("entries") == {}, "P6-T09b",
                f"expected empty entries, got: {reg.get('entries')}")


# ── P6-T10 to P6-T15: capture_content dedup integration ──────────────────────

def test_p6_t10():
    """Normal capture writes file and returns is_duplicate=False."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        packet = _make_packet("Unique content for P6-T10.")
        result = capture_content(packet, vault_root=vault)
        _assert(result.get("is_duplicate") is False, "P6-T10a",
                f"is_duplicate={result.get('is_duplicate')!r}")
        _assert("filename" in result, "P6-T10b")
        _assert(Path(result["content_path"]).exists(), "P6-T10c",
                f"content file not found: {result.get('content_path')}")


def test_p6_t11():
    """Duplicate capture returns is_duplicate=True with no new file written."""
    content = "Duplicate test content P6-T11 — unique string."
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        # First capture
        packet1 = _make_packet(content, title="First Capture")
        result1 = capture_content(packet1, vault_root=vault)
        _assert(result1.get("is_duplicate") is False, "P6-T11a-first")

        # Count files before second capture
        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        file_count_before = len(list(sources_dir.glob("*.md")))

        # Second capture — same content
        packet2 = _make_packet(content, title="Second Capture (same body)")
        result2 = capture_content(packet2, vault_root=vault)
        _assert(result2.get("is_duplicate") is True, "P6-T11b-second",
                f"is_duplicate={result2.get('is_duplicate')!r}")

        # No new file should have been written
        file_count_after = len(list(sources_dir.glob("*.md")))
        _assert(file_count_after == file_count_before, "P6-T11c",
                f"expected {file_count_before} files, got {file_count_after}")


def test_p6_t12():
    """Duplicate result has content_sha256 and duplicate_of fields."""
    content = "Content for P6-T12 dedup field check."
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        packet1 = _make_packet(content)
        result1 = capture_content(packet1, vault_root=vault)
        original_id = result1["capture_id"]
        original_sha = result1["content_sha256"]

        packet2 = _make_packet(content, title="Repeat")
        result2 = capture_content(packet2, vault_root=vault)

        _assert(result2.get("is_duplicate") is True, "P6-T12a")
        _assert(result2.get("content_sha256") == original_sha, "P6-T12b",
                f"sha mismatch: {result2.get('content_sha256')!r} vs {original_sha!r}")
        _assert(result2.get("duplicate_of") == original_id, "P6-T12c",
                f"duplicate_of={result2.get('duplicate_of')!r} vs original={original_id!r}")
        _assert("original_captured_at" in result2, "P6-T12d")


def test_p6_t13():
    """Registry file is created after first capture."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _assert(not registry_path(vault).exists(), "P6-T13a-before")

        packet = _make_packet("P6-T13 registry creation test content.")
        capture_content(packet, vault_root=vault)
        _assert(registry_path(vault).exists(), "P6-T13b-after",
                f"registry not created at: {registry_path(vault)}")


def test_p6_t14():
    """Registry persists across multiple sequential captures."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        for i in range(3):
            packet = _make_packet(f"Distinct content #{i} for P6-T14.", title=f"Item {i}")
            capture_content(packet, vault_root=vault)

        reg = load_registry(vault)
        entries = reg.get("entries", {})
        _assert(len(entries) == 3, "P6-T14",
                f"expected 3 registry entries, got {len(entries)}")


def test_p6_t15():
    """Different content (different SHA-256) is not treated as duplicate."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        r1 = capture_content(_make_packet("Content A for P6-T15."), vault_root=vault)
        r2 = capture_content(_make_packet("Content B for P6-T15."), vault_root=vault)
        _assert(r1.get("is_duplicate") is False, "P6-T15a")
        _assert(r2.get("is_duplicate") is False, "P6-T15b",
                "different content incorrectly flagged as duplicate")


# ── P6-T16 to P6-T17: RSS repeated-run behavior ───────────────────────────────

def test_p6_t16():
    """Second RSS run on same feed items returns duplicate results (no re-capture)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        # First run — should capture all items
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            rc1 = chaseos_main([
                "capture", "rss", "https://example.com/dedup-test.rss",
                "--vault-root", str(vault),
            ])
        _assert(rc1 == 0, "P6-T16a", f"first run exit code: {rc1}")

        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        files_after_first = len(list(sources_dir.glob("*.md")))
        _assert(files_after_first == 2, "P6-T16b",
                f"expected 2 files after first run, got {files_after_first}")

        # Second run — same feed, same items → duplicates
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            rc2 = chaseos_main([
                "capture", "rss", "https://example.com/dedup-test.rss",
                "--vault-root", str(vault),
            ])
        _assert(rc2 == 0, "P6-T16c", f"second run exit code: {rc2}")

        files_after_second = len(list(sources_dir.glob("*.md")))
        _assert(files_after_second == files_after_first, "P6-T16d",
                f"files grew on second run: before={files_after_first}, after={files_after_second}")


def test_p6_t17():
    """JSON output: first run captured_count=2; second run duplicate_count=2."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        # First run — JSON output
        buf1 = io.StringIO()
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            with patch("sys.stdout", buf1):
                chaseos_main([
                    "capture", "rss", "https://example.com/dedup.rss",
                    "--vault-root", str(vault),
                    "--json",
                ])
        data1 = json.loads(buf1.getvalue())
        _assert(data1.get("captured_count") == 2, "P6-T17a",
                f"first run captured_count={data1.get('captured_count')!r}")
        _assert(data1.get("duplicate_count") == 0, "P6-T17b",
                f"first run duplicate_count={data1.get('duplicate_count')!r}")

        # Second run — same feed → duplicates
        buf2 = io.StringIO()
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            with patch("sys.stdout", buf2):
                chaseos_main([
                    "capture", "rss", "https://example.com/dedup.rss",
                    "--vault-root", str(vault),
                    "--json",
                ])
        data2 = json.loads(buf2.getvalue())
        _assert(data2.get("captured_count") == 0, "P6-T17c",
                f"second run captured_count={data2.get('captured_count')!r}")
        _assert(data2.get("duplicate_count") == 2, "P6-T17d",
                f"second run duplicate_count={data2.get('duplicate_count')!r}")


# ── P6-T18 to P6-T21: CLI output ─────────────────────────────────────────────

def test_p6_t18():
    """CLI capture rss --json output includes duplicate_count key."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        buf = io.StringIO()
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            with patch("sys.stdout", buf):
                chaseos_main([
                    "capture", "rss", "https://example.com/rss",
                    "--vault-root", str(vault),
                    "--json",
                ])
        envelope = json.loads(buf.getvalue())
        data = envelope.get("result", envelope)
        _assert("duplicate_count" in data, "P6-T18a",
                f"keys: {list(data.keys())}")
        _assert("duplicates" in data, "P6-T18b",
                f"keys: {list(data.keys())}")
        _assert(isinstance(data["duplicate_count"], int), "P6-T18c")


def test_p6_t19():
    """CLI capture rss human output mentions 'Duplicates' on second run."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        # First run
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            chaseos_main([
                "capture", "rss", "https://example.com/rss",
                "--vault-root", str(vault),
            ])

        # Second run — capture output
        buf = io.StringIO()
        with patch("runtime.capture.connectors.rss_connector.fetch_feed",
                   side_effect=_mock_fetch_feed):
            with patch("sys.stdout", buf):
                chaseos_main([
                    "capture", "rss", "https://example.com/rss",
                    "--vault-root", str(vault),
                ])
        output = buf.getvalue()
        _assert("Duplicates" in output or "duplicate" in output.lower(), "P6-T19",
                f"no 'Duplicates' in second-run output:\n{output[:400]!r}")


def test_p6_t20():
    """CLI intake dedup-stats shows entry count."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        # No entries yet
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = chaseos_main(["intake", "dedup-stats", "--vault-root", str(vault)])
        _assert(rc == 0, "P6-T20a", f"exit code: {rc}")
        output = buf.getvalue()
        _assert("Registry" in output or "registry" in output.lower(), "P6-T20b",
                f"no registry mention: {output[:200]!r}")

        # Capture one item, then check stats
        capture_content(_make_packet("P6-T20 stats test content."), vault_root=vault)
        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            chaseos_main(["intake", "dedup-stats", "--vault-root", str(vault)])
        output2 = buf2.getvalue()
        _assert("1" in output2, "P6-T20c",
                f"expected '1' in stats output after one capture: {output2!r}")


def test_p6_t21():
    """CLI intake dedup-stats --json returns parseable JSON with entry_count."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        # Capture two items first
        for i in range(2):
            capture_content(
                _make_packet(f"Stats JSON test content #{i}.", title=f"Item {i}"),
                vault_root=vault,
            )

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = chaseos_main(["intake", "dedup-stats", "--vault-root", str(vault), "--json"])
        _assert(rc == 0, "P6-T21a", f"exit code: {rc}")
        envelope = json.loads(buf.getvalue())
        data = envelope.get("result", envelope)
        _assert("entry_count" in data, "P6-T21b", f"keys: {list(data.keys())}")
        _assert(data["entry_count"] == 2, "P6-T21c",
                f"expected 2, got {data.get('entry_count')!r}")
        _assert("registry_path" in data, "P6-T21d")


# ── P6-T22 to P6-T23: Backward compat ────────────────────────────────────────

def test_p6_t22():
    """capture file: duplicate detection works via capture_content."""
    content = "P6-T22 backward compat duplicate test content string."
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        content_file = vault / "test.md"
        content_file.write_text(content, encoding="utf-8")

        # First capture — should succeed
        rc1 = chaseos_main([
            "capture", "file", str(content_file),
            "--class", "source", "--source", "web", "--title", "Dup Test",
            "--vault-root", str(vault),
        ])
        _assert(rc1 == 0, "P6-T22a", f"first capture exit code: {rc1}")

        # Second capture — same content → duplicate
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc2 = chaseos_main([
                "capture", "file", str(content_file),
                "--class", "source", "--source", "web", "--title", "Dup Test Again",
                "--vault-root", str(vault),
            ])
        _assert(rc2 == 0, "P6-T22b", f"duplicate capture exit code: {rc2}")
        output = buf.getvalue()
        _assert("DUPLICATE" in output or "duplicate" in output.lower(), "P6-T22c",
                f"no DUPLICATE in output: {output!r}")


def test_p6_t23():
    """capture file works normally when content is new (not duplicate)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        content_file = vault / "unique.md"
        content_file.write_text("P6-T23 unique content — not a duplicate.", encoding="utf-8")

        rc = chaseos_main([
            "capture", "file", str(content_file),
            "--class", "source", "--source", "web", "--title", "Unique Item",
            "--vault-root", str(vault),
        ])
        _assert(rc == 0, "P6-T23a", f"exit code: {rc}")

        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        md_files = list(sources_dir.glob("*.md"))
        _assert(len(md_files) == 1, "P6-T23b", f"expected 1 file, got {len(md_files)}")


# ── P6-T24 to P6-T25: Additional coverage ─────────────────────────────────────

def test_p6_t24():
    """build_registry_entry returns dict with all expected keys."""
    entry = build_registry_entry(
        content_sha256="e" * 64,
        capture_id="test-uuid",
        first_captured_at="2026-03-28T10:00:00+00:00",
        title="Entry Test",
        source_platform="rss",
        source_url="https://example.com",
        input_class="source",
        capture_method="rss",
    )
    required_keys = {
        "content_sha256", "capture_id", "first_captured_at",
        "title", "source_platform", "source_url", "input_class", "capture_method",
    }
    missing = required_keys - set(entry.keys())
    _assert(not missing, "P6-T24", f"missing keys: {missing}")
    _assert(entry["capture_method"] == "rss", "P6-T24b")


def test_p6_t25():
    """Duplicate capture does not write a new .md or .meta.json file."""
    content = "P6-T25 no-write-on-duplicate test content string."
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)

        # First capture
        capture_content(_make_packet(content, title="First"), vault_root=vault)

        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        md_count = len(list(sources_dir.glob("*.md")))
        json_count = len(list(sources_dir.glob("*.json")))

        # Second capture — same content
        result = capture_content(_make_packet(content, title="Second"), vault_root=vault)
        _assert(result.get("is_duplicate") is True, "P6-T25a")
        _assert(len(list(sources_dir.glob("*.md"))) == md_count, "P6-T25b",
                "extra .md file written on duplicate")
        _assert(len(list(sources_dir.glob("*.json"))) == json_count, "P6-T25c",
                "extra .json file written on duplicate")


# ── Test registry and runner ───────────────────────────────────────────────────

_TESTS = [
    ("P6-T01", test_p6_t01),
    ("P6-T02", test_p6_t02),
    ("P6-T03", test_p6_t03),
    ("P6-T04", test_p6_t04),
    ("P6-T05", test_p6_t05),
    ("P6-T06", test_p6_t06),
    ("P6-T07", test_p6_t07),
    ("P6-T08", test_p6_t08),
    ("P6-T09", test_p6_t09),
    ("P6-T10", test_p6_t10),
    ("P6-T11", test_p6_t11),
    ("P6-T12", test_p6_t12),
    ("P6-T13", test_p6_t13),
    ("P6-T14", test_p6_t14),
    ("P6-T15", test_p6_t15),
    ("P6-T16", test_p6_t16),
    ("P6-T17", test_p6_t17),
    ("P6-T18", test_p6_t18),
    ("P6-T19", test_p6_t19),
    ("P6-T20", test_p6_t20),
    ("P6-T21", test_p6_t21),
    ("P6-T22", test_p6_t22),
    ("P6-T23", test_p6_t23),
    ("P6-T24", test_p6_t24),
    ("P6-T25", test_p6_t25),
]


def run_all() -> int:
    global _PASS, _FAIL
    _PASS = 0
    _FAIL = 0
    _ERRORS.clear()

    for label, fn in _TESTS:
        print(f"\n[{label}]")
        _run_test(label, fn)

    print(f"\n{'='*50}")
    print(f"Pass 6: {_PASS} passed, {_FAIL} failed")
    if _ERRORS:
        print("\nFailed tests:")
        for e in _ERRORS:
            print(f"  {e}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
