"""
test_pass8p5.py — ChaseOS Phase 8 Pass 5 Test Suite
RSS/Atom Connector

Run:
    python -m runtime.capture.test_pass8p5

Or via canonical CLI:
    chaseos test capture

Tests:
    P5-T01  rss_connector: parse_rss returns feed title from <channel><title>
    P5-T02  rss_connector: parse_rss returns correct item count
    P5-T03  rss_connector: parse_rss extracts item title, link, description
    P5-T04  rss_connector: parse_rss extracts pubDate per item
    P5-T05  rss_connector: parse_rss handles item with no description (no crash)
    P5-T06  rss_connector: parse_atom returns feed title from Atom feed element
    P5-T07  rss_connector: parse_atom returns correct item count
    P5-T08  rss_connector: parse_atom extracts entry title, link, summary
    P5-T09  rss_connector: parse_atom extracts published date
    P5-T10  rss_connector: detect_and_parse detects RSS correctly
    P5-T11  rss_connector: detect_and_parse detects Atom correctly
    P5-T12  rss_connector: parse_feed_date parses RFC 2822 date (RSS pubDate)
    P5-T13  rss_connector: parse_feed_date parses ISO 8601 date (Atom published)
    P5-T14  rss_connector: parse_feed_date returns None for garbage string
    P5-T15  rss_connector: derive_source_platform extracts hostname slug
    P5-T16  rss_connector: derive_source_platform strips www prefix
    P5-T17  rss_connector: items_to_packets returns correct ContentPacket count
    P5-T18  rss_connector: ContentPacket has capture_method="rss"
    P5-T19  rss_connector: ContentPacket source_url = item link
    P5-T20  rss_connector: ContentPacket extra_metadata carries feed_url and feed_title
    P5-T21  rss_connector: items_to_packets uses per-item event_date from pubDate
    P5-T22  rss_connector: event_date_hint_override overrides per-item date
    P5-T23  rss_connector: items_to_packets skips item with no title, no link, no description
    P5-T24  rss_connector: build_item_content strips HTML tags from description
    P5-T25  rss_connector: FeedParseError raised on malformed XML
    P5-T26  rss_connector: parse_rss raises FeedParseError with no <channel>
    P5-T27  CLI: capture rss command exists in parser
    P5-T28  CLI: capture rss with mocked fetch writes to quarantine
    P5-T29  CLI: capture rss --limit 1 captures only 1 item
    P5-T30  CLI: capture rss --json outputs JSON summary
    P5-T31  backward-compat: capture file still works after rss addition
    P5-T32  quarantine: rss captures go to source class subfolder by default
    P5-T33  sidecar: rss captures have schema_version 8.3
    P5-T34  sidecar: rss captures have capture_method=rss
    P5-T35  sidecar: rss captures have feed_url in extra_metadata
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch, MagicMock

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

from runtime.capture.connectors.rss_connector import (
    parse_rss,
    parse_atom,
    detect_and_parse,
    parse_feed_date,
    derive_source_platform,
    build_item_content,
    items_to_packets,
    fetch_and_parse_feed,
    FeedFetchError,
    FeedParseError,
    FEED_TYPE_RSS,
    FEED_TYPE_ATOM,
)
from runtime.capture.content_packet import ContentPacket, INPUT_CLASS_SOURCE
from runtime.capture.capture import capture_content
from runtime.cli.main import main as chaseos_main


# ── Fixture data ───────────────────────────────────────────────────────────────

_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Markets Feed</title>
    <link>https://example.com</link>
    <description>Test RSS Feed</description>
    <item>
      <title>Fed Holds Rates in Split Decision</title>
      <link>https://example.com/article/fed-rates</link>
      <description>The Federal Reserve held interest rates steady &amp; cited inflation risks.</description>
      <pubDate>Mon, 28 Mar 2026 14:30:00 +0000</pubDate>
      <guid>https://example.com/article/fed-rates</guid>
    </item>
    <item>
      <title>Oil Falls on Demand Concerns</title>
      <link>https://example.com/article/oil-falls</link>
      <description>Crude prices fell on weak demand data from China.</description>
      <pubDate>Mon, 28 Mar 2026 12:00:00 +0000</pubDate>
      <guid>https://example.com/article/oil-falls</guid>
    </item>
    <item>
      <title>No Description Item</title>
      <link>https://example.com/article/no-desc</link>
      <pubDate>Mon, 28 Mar 2026 10:00:00 +0000</pubDate>
      <guid>https://example.com/article/no-desc</guid>
    </item>
  </channel>
</rss>"""

_ATOM_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <link href="https://example.com"/>
  <updated>2026-03-28T14:30:00Z</updated>
  <entry>
    <title>Crypto Markets Rally on ETF Flows</title>
    <link rel="alternate" href="https://example.com/atom/crypto-rally"/>
    <summary>Bitcoin and Ethereum gained on strong ETF inflows.</summary>
    <published>2026-03-28T14:00:00Z</published>
    <id>https://example.com/atom/crypto-rally</id>
    <author><name>Jane Smith</name></author>
  </entry>
  <entry>
    <title>Yield Curve Flattens as Shorts Cover</title>
    <link rel="alternate" href="https://example.com/atom/yield-curve"/>
    <summary>Treasury yields narrowed across the curve.</summary>
    <published>2026-03-28T11:00:00Z</published>
    <id>https://example.com/atom/yield-curve</id>
  </entry>
</feed>"""

_MALFORMED_XML = """<?xml version="1.0"?>
<rss><channel><title>Bad Feed</title><item><title>Test</title></channel>"""

_HTML_DESCRIPTION = "<p>This is <b>bold</b> and <a href='#'>linked</a> text &amp; more.</p>"


# ── P5-T01 to P5-T05: RSS parsing ─────────────────────────────────────────────

def test_p5_t01():
    feed_title, items = parse_rss(_RSS_FEED)
    _assert(feed_title == "Test Markets Feed", "P5-T01", f"got: {feed_title}")


def test_p5_t02():
    feed_title, items = parse_rss(_RSS_FEED)
    _assert(len(items) == 3, "P5-T02", f"expected 3 items, got {len(items)}")


def test_p5_t03():
    _, items = parse_rss(_RSS_FEED)
    item = items[0]
    _assert(item["title"] == "Fed Holds Rates in Split Decision", "P5-T03a")
    _assert(item["link"] == "https://example.com/article/fed-rates", "P5-T03b")
    _assert("Federal Reserve" in (item["description"] or ""), "P5-T03c",
            f"description missing expected text: {item['description']!r}")


def test_p5_t04():
    _, items = parse_rss(_RSS_FEED)
    _assert(items[0]["pub_date"] == "Mon, 28 Mar 2026 14:30:00 +0000", "P5-T04",
            f"got: {items[0]['pub_date']!r}")


def test_p5_t05():
    _, items = parse_rss(_RSS_FEED)
    # item[2] has no <description> — should not crash; description should be None
    _assert(items[2]["description"] is None, "P5-T05a")
    _assert(items[2]["title"] == "No Description Item", "P5-T05b")


# ── P5-T06 to P5-T09: Atom parsing ────────────────────────────────────────────

def test_p5_t06():
    feed_title, items = parse_atom(_ATOM_FEED)
    _assert(feed_title == "Test Atom Feed", "P5-T06", f"got: {feed_title}")


def test_p5_t07():
    _, items = parse_atom(_ATOM_FEED)
    _assert(len(items) == 2, "P5-T07", f"expected 2 items, got {len(items)}")


def test_p5_t08():
    _, items = parse_atom(_ATOM_FEED)
    item = items[0]
    _assert(item["title"] == "Crypto Markets Rally on ETF Flows", "P5-T08a")
    _assert(item["link"] == "https://example.com/atom/crypto-rally", "P5-T08b")
    _assert("ETF inflows" in (item["description"] or ""), "P5-T08c",
            f"description: {item['description']!r}")


def test_p5_t09():
    _, items = parse_atom(_ATOM_FEED)
    _assert(items[0]["pub_date"] == "2026-03-28T14:00:00Z", "P5-T09",
            f"got: {items[0]['pub_date']!r}")


# ── P5-T10 to P5-T11: Feed type detection ─────────────────────────────────────

def test_p5_t10():
    feed_type, feed_title, items = detect_and_parse(_RSS_FEED)
    _assert(feed_type == FEED_TYPE_RSS, "P5-T10a", f"got: {feed_type}")
    _assert(len(items) == 3, "P5-T10b")


def test_p5_t11():
    feed_type, feed_title, items = detect_and_parse(_ATOM_FEED)
    _assert(feed_type == FEED_TYPE_ATOM, "P5-T11a", f"got: {feed_type}")
    _assert(len(items) == 2, "P5-T11b")


# ── P5-T12 to P5-T14: Date parsing ────────────────────────────────────────────

def test_p5_t12():
    result = parse_feed_date("Mon, 28 Mar 2026 14:30:00 +0000")
    _assert(result == "2026-03-28", "P5-T12", f"got: {result!r}")


def test_p5_t13():
    result = parse_feed_date("2026-03-28T14:00:00Z")
    _assert(result == "2026-03-28", "P5-T13", f"got: {result!r}")


def test_p5_t14():
    _assert(parse_feed_date(None) is None, "P5-T14a")
    _assert(parse_feed_date("not a date") is None, "P5-T14b",
            f"got: {parse_feed_date('not a date')!r}")


# ── P5-T15 to P5-T16: Source platform derivation ──────────────────────────────

def test_p5_t15():
    slug = derive_source_platform("https://feeds.reuters.com/reuters/businessNews")
    _assert("reuters" in slug, "P5-T15", f"got: {slug!r}")


def test_p5_t16():
    slug = derive_source_platform("https://www.ft.com/rss/home/uk")
    _assert("www" not in slug, "P5-T16a", f"got: {slug!r} (www should be stripped)")
    _assert("ft" in slug, "P5-T16b", f"got: {slug!r}")


# ── P5-T17 to P5-T23: ContentPacket normalization ─────────────────────────────

def test_p5_t17():
    _, items = parse_rss(_RSS_FEED)
    feed_type = FEED_TYPE_RSS
    packets, skipped = items_to_packets(
        items,
        feed_url="https://example.com/rss",
        feed_title="Test Markets Feed",
        feed_type=feed_type,
        source_platform="example-com",
    )
    # item[2] has no description but has a link — should be captured (link is content)
    _assert(len(packets) == 3, "P5-T17", f"expected 3 packets, got {len(packets)}, skipped: {skipped}")


def test_p5_t18():
    _, items = parse_rss(_RSS_FEED)
    packets, _ = items_to_packets(
        items[:1],
        feed_url="https://example.com/rss",
        feed_title="Test",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
    )
    _assert(packets[0].capture_method == "rss", "P5-T18",
            f"got: {packets[0].capture_method!r}")


def test_p5_t19():
    _, items = parse_rss(_RSS_FEED)
    packets, _ = items_to_packets(
        items[:1],
        feed_url="https://example.com/rss",
        feed_title="Test",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
    )
    _assert(packets[0].source_url == "https://example.com/article/fed-rates", "P5-T19",
            f"got: {packets[0].source_url!r}")


def test_p5_t20():
    _, items = parse_rss(_RSS_FEED)
    packets, _ = items_to_packets(
        items[:1],
        feed_url="https://example.com/rss",
        feed_title="Test Markets Feed",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
    )
    extra = packets[0].extra_metadata
    _assert(extra.get("feed_url") == "https://example.com/rss", "P5-T20a",
            f"got: {extra.get('feed_url')!r}")
    _assert(extra.get("feed_title") == "Test Markets Feed", "P5-T20b",
            f"got: {extra.get('feed_title')!r}")


def test_p5_t21():
    _, items = parse_rss(_RSS_FEED)
    packets, _ = items_to_packets(
        items[:1],
        feed_url="https://example.com/rss",
        feed_title="Test",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
    )
    # pubDate "Mon, 28 Mar 2026 14:30:00 +0000" should parse to 2026-03-28
    _assert(packets[0].event_date_hint == "2026-03-28", "P5-T21",
            f"got: {packets[0].event_date_hint!r}")


def test_p5_t22():
    _, items = parse_rss(_RSS_FEED)
    packets, _ = items_to_packets(
        items[:1],
        feed_url="https://example.com/rss",
        feed_title="Test",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
        event_date_hint_override="2026-01-01",  # override
    )
    _assert(packets[0].event_date_hint == "2026-01-01", "P5-T22",
            f"got: {packets[0].event_date_hint!r}")


def test_p5_t23():
    no_content_items = [{"title": None, "link": None, "description": None, "pub_date": None, "guid": None}]
    packets, skipped = items_to_packets(
        no_content_items,
        feed_url="https://example.com/rss",
        feed_title="Test",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
    )
    _assert(len(packets) == 0, "P5-T23a", f"expected 0 packets, got {len(packets)}")
    _assert(len(skipped) == 1, "P5-T23b", f"expected 1 skipped, got {len(skipped)}")


# ── P5-T24: HTML stripping ─────────────────────────────────────────────────────

def test_p5_t24():
    content = build_item_content(
        title="Test",
        link=None,
        description=_HTML_DESCRIPTION,
        author=None,
        pub_date_raw=None,
    )
    _assert("<b>" not in content, "P5-T24a", "HTML <b> tag should be stripped")
    _assert("<p>" not in content, "P5-T24b", "HTML <p> tag should be stripped")
    _assert("bold" in content, "P5-T24c", "text content should remain after stripping")
    _assert("&amp;" not in content, "P5-T24d", "HTML entities should be decoded")
    _assert("&" in content, "P5-T24e", "& should be present after entity decoding")


# ── P5-T25 to P5-T26: Error handling ─────────────────────────────────────────

def test_p5_t25():
    raised = False
    try:
        detect_and_parse(_MALFORMED_XML)
    except FeedParseError:
        raised = True
    _assert(raised, "P5-T25", "FeedParseError should be raised on malformed XML")


def test_p5_t26():
    bad_rss = """<?xml version="1.0"?><rss version="2.0"><notchannel/></rss>"""
    raised = False
    try:
        parse_rss(bad_rss)
    except FeedParseError as exc:
        raised = True
        _assert("channel" in str(exc).lower(), "P5-T26b",
                f"error should mention channel, got: {exc}")
    _assert(raised, "P5-T26a", "FeedParseError should be raised when <channel> missing")


# ── P5-T27: CLI parser has capture rss ────────────────────────────────────────

def test_p5_t27():
    import argparse
    from runtime.cli.main import _build_parser
    parser = _build_parser()
    # Should not raise — capture rss should be a valid subcommand
    args = parser.parse_args([
        "capture", "rss", "https://example.com/rss",
        "--limit", "3",
    ])
    _assert(args.capture_mode == "rss", "P5-T27a", f"got: {args.capture_mode!r}")
    _assert(args.feed_url == "https://example.com/rss", "P5-T27b")
    _assert(args.limit == 3, "P5-T27c", f"got: {args.limit!r}")


# ── P5-T28 to P5-T30: CLI integration with mocked HTTP ────────────────────────

def _mock_fetch_feed(url, timeout=30):
    """Substitute for fetch_feed that returns fixture RSS data."""
    return _RSS_FEED


def test_p5_t28():
    """CLI capture rss writes quarantine files when feed fetch succeeds."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()

        with patch("runtime.capture.connectors.rss_connector.fetch_feed", side_effect=_mock_fetch_feed):
            rc = chaseos_main([
                "capture", "rss", "https://example.com/rss",
                "--vault-root", str(vault),
            ])

        _assert(rc == 0, "P5-T28a", f"exit code: {rc}")

        # Check quarantine/Sources/ exists and has files
        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        _assert(sources_dir.exists(), "P5-T28b", "Sources quarantine dir should exist")
        md_files = [f for f in sources_dir.iterdir() if f.suffix == ".md"]
        _assert(len(md_files) == 3, "P5-T28c", f"expected 3 captured files, got {len(md_files)}")


def test_p5_t29():
    """CLI capture rss --limit 1 captures only 1 item."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()

        with patch("runtime.capture.connectors.rss_connector.fetch_feed", side_effect=_mock_fetch_feed):
            rc = chaseos_main([
                "capture", "rss", "https://example.com/rss",
                "--limit", "1",
                "--vault-root", str(vault),
            ])

        _assert(rc == 0, "P5-T29a", f"exit code: {rc}")
        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        md_files = [f for f in sources_dir.iterdir() if f.suffix == ".md"]
        _assert(len(md_files) == 1, "P5-T29b", f"expected 1 file, got {len(md_files)}")


def test_p5_t30():
    """CLI capture rss --json outputs parseable JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()

        buf = io.StringIO()
        with patch("runtime.capture.connectors.rss_connector.fetch_feed", side_effect=_mock_fetch_feed):
            with patch("sys.stdout", buf):
                rc = chaseos_main([
                    "capture", "rss", "https://example.com/rss",
                    "--limit", "1",
                    "--vault-root", str(vault),
                    "--json",
                ])

        output = buf.getvalue()
        _assert(rc == 0, "P5-T30a", f"exit code: {rc}")
        try:
            data = json.loads(output)
            _assert(isinstance(data, dict), "P5-T30b", f"expected dict, got {type(data)}")
            _assert("captured" in data, "P5-T30c", f"JSON missing 'captured' key: {list(data.keys())}")
        except json.JSONDecodeError as exc:
            _fail("P5-T30", f"output was not valid JSON: {exc}\nOutput: {output[:200]!r}")


# ── P5-T31: Backward-compat: capture file still works ─────────────────────────

def test_p5_t31():
    """Existing capture file command still works after RSS addition."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        content_file = vault / "test_source.md"
        content_file.write_text("Test content for backward compat check.", encoding="utf-8")

        rc = chaseos_main([
            "capture", "file", str(content_file),
            "--class", "source",
            "--source", "web",
            "--title", "Backward Compat Test",
            "--vault-root", str(vault),
        ])
        _assert(rc == 0, "P5-T31", f"exit code: {rc}")


# ── P5-T32 to P5-T35: Sidecar metadata for RSS captures ──────────────────────

def _write_rss_capture(vault: Path) -> dict:
    """Helper: write one RSS-sourced capture and return the sidecar dict."""
    _, items = parse_rss(_RSS_FEED)
    packets, _ = items_to_packets(
        items[:1],
        feed_url="https://example.com/rss",
        feed_title="Test Markets Feed",
        feed_type=FEED_TYPE_RSS,
        source_platform="example-com",
    )
    result = capture_content(packets[0], vault_root=vault)
    sidecar = json.loads(Path(result["sidecar_path"]).read_text(encoding="utf-8"))
    return sidecar


def test_p5_t32():
    """RSS captures go to Sources/ quarantine subfolder (default input_class=source)."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        sidecar = _write_rss_capture(vault)
        _assert(sidecar["input_class"] == "source", "P5-T32a",
                f"got: {sidecar.get('input_class')!r}")
        # Verify the file landed in Sources/
        sources_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "Sources"
        _assert(sources_dir.exists(), "P5-T32b", "Sources/ dir should exist")


def test_p5_t33():
    """RSS captures have sidecar schema_version 8.3."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        sidecar = _write_rss_capture(vault)
        _assert(sidecar["schema_version"] == "8.3", "P5-T33",
                f"got: {sidecar.get('schema_version')!r}")


def test_p5_t34():
    """RSS captures have capture_method='rss' in sidecar."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        sidecar = _write_rss_capture(vault)
        _assert(sidecar["capture_method"] == "rss", "P5-T34",
                f"got: {sidecar.get('capture_method')!r}")


def test_p5_t35():
    """RSS captures have feed_url in sidecar extra_metadata."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        (vault / "03_INPUTS").mkdir()
        sidecar = _write_rss_capture(vault)
        extra = sidecar.get("extra_metadata", {})
        _assert(extra.get("feed_url") == "https://example.com/rss", "P5-T35",
                f"got extra_metadata: {extra}")


# ── Test registry and runner ───────────────────────────────────────────────────

_TESTS = [
    ("P5-T01", test_p5_t01),
    ("P5-T02", test_p5_t02),
    ("P5-T03", test_p5_t03),
    ("P5-T04", test_p5_t04),
    ("P5-T05", test_p5_t05),
    ("P5-T06", test_p5_t06),
    ("P5-T07", test_p5_t07),
    ("P5-T08", test_p5_t08),
    ("P5-T09", test_p5_t09),
    ("P5-T10", test_p5_t10),
    ("P5-T11", test_p5_t11),
    ("P5-T12", test_p5_t12),
    ("P5-T13", test_p5_t13),
    ("P5-T14", test_p5_t14),
    ("P5-T15", test_p5_t15),
    ("P5-T16", test_p5_t16),
    ("P5-T17", test_p5_t17),
    ("P5-T18", test_p5_t18),
    ("P5-T19", test_p5_t19),
    ("P5-T20", test_p5_t20),
    ("P5-T21", test_p5_t21),
    ("P5-T22", test_p5_t22),
    ("P5-T23", test_p5_t23),
    ("P5-T24", test_p5_t24),
    ("P5-T25", test_p5_t25),
    ("P5-T26", test_p5_t26),
    ("P5-T27", test_p5_t27),
    ("P5-T28", test_p5_t28),
    ("P5-T29", test_p5_t29),
    ("P5-T30", test_p5_t30),
    ("P5-T31", test_p5_t31),
    ("P5-T32", test_p5_t32),
    ("P5-T33", test_p5_t33),
    ("P5-T34", test_p5_t34),
    ("P5-T35", test_p5_t35),
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
    print(f"Pass 5: {_PASS} passed, {_FAIL} failed")
    if _ERRORS:
        print("\nFailed tests:")
        for e in _ERRORS:
            print(f"  {e}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
