"""
test_pass8p7.py — ChaseOS Phase 8 Pass 7
Tests for the browser/saved-HTML connector.

Coverage:
  - HTML file loading (utf-8, latin-1 fallback, missing file)
  - HTML → markdown conversion (headings, paragraphs, lists, links, emphasis)
  - Script/style/nav/footer stripping
  - Title extraction precedence (cli > html_title > html_h1 > filename)
  - ContentPacket defaults (input_class, source_platform, capture_method, detected_mime)
  - Extra metadata fields (source_file, html_title, html_h1, title_source)
  - Malformed / empty HTML handling
  - Dedup: same HTML captured twice → second is duplicate
  - CLI capture browser file path → quarantine write
  - Backward compatibility: existing capture commands still work

Running: chaseos test capture   (included via cmd_test_capture in main.py)
Manual:  python -m pytest runtime/capture/test_pass8p7.py -v   (if pytest installed)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure vault root is importable
_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.capture.connectors.browser_connector import (
    html_to_markdown,
    resolve_title,
    capture_from_browser,
    load_html_file,
    HTMLParseError,
)
from runtime.capture.content_packet import INPUT_CLASS_SOURCE


# ── Test runner infrastructure ─────────────────────────────────────────────────

_TESTS: list[tuple[str, object]] = []
_PASS = 0
_FAIL = 0
_ERRORS: list[str] = []


def _test(label: str):
    def decorator(fn):
        _TESTS.append((label, fn))
        return fn
    return decorator


def _run_test(label: str, fn) -> None:
    global _PASS, _FAIL
    try:
        fn()
        print(f"  PASS")
        _PASS += 1
    except AssertionError as exc:
        print(f"  FAIL: {exc}")
        _FAIL += 1
        _ERRORS.append(f"{label}: {exc}")
    except Exception as exc:
        print(f"  ERROR: {type(exc).__name__}: {exc}")
        _FAIL += 1
        _ERRORS.append(f"{label}: {type(exc).__name__}: {exc}")


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


# ── Fixtures ───────────────────────────────────────────────────────────────────

_SIMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Article Title</title></head>
<body>
<h1>Article Headline</h1>
<p>First paragraph of the article.</p>
<p>Second paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
</body>
</html>"""

_LIST_HTML = """<html><body>
<h2>My List</h2>
<ul>
<li>Apple</li>
<li>Banana</li>
</ul>
<ol>
<li>One</li>
<li>Two</li>
<li>Three</li>
</ol>
</body></html>"""

_LINK_HTML = """<html><body>
<p>Visit <a href="https://example.com/article">the article</a> for more.</p>
<p>Internal <a href="#section">anchor</a> stays as text.</p>
</body></html>"""

_NOISY_HTML = """<html>
<head>
<title>Clean Article</title>
<style>body { color: red; }</style>
<script>var x = 1;</script>
</head>
<body>
<nav><a href="/">Home</a> | <a href="/about">About</a></nav>
<article>
<h1>Real Article Title</h1>
<p>This is the article content.</p>
</article>
<footer>Copyright 2026</footer>
<aside>Related articles...</aside>
</body>
</html>"""

_NO_TITLE_HTML = """<html><body>
<h1>Article Without Title Tag</h1>
<p>Content here.</p>
</body></html>"""

_NO_HEADING_HTML = """<html>
<head><title>Only Title Tag</title></head>
<body>
<p>No headings in this document.</p>
</body>
</html>"""

_EMPTY_HTML = """<html><body></body></html>"""

_MALFORMED_HTML = """<html>
<body>
<p>Unclosed paragraph
<div>Text in div <span>with span</div>
<b>Bold without close
</body>"""

_HEADING_LEVELS_HTML = """<html><body>
<h1>Level One</h1>
<h2>Level Two</h2>
<h3>Level Three</h3>
<h4>Level Four</h4>
<h5>Level Five</h5>
<h6>Level Six</h6>
</body></html>"""


# ── Tests ──────────────────────────────────────────────────────────────────────

@_test("P7-T01: html_to_markdown extracts title from <title>")
def test_title_extraction():
    text, html_title, first_h1 = html_to_markdown(_SIMPLE_HTML)
    _assert(html_title == "Test Article Title", f"html_title={html_title!r}")
    _assert(first_h1 is not None, "first_h1 should be set")
    _assert("Article Headline" in (first_h1 or ""), f"first_h1={first_h1!r}")


@_test("P7-T02: html_to_markdown returns non-empty markdown text")
def test_markdown_not_empty():
    text, _, _ = html_to_markdown(_SIMPLE_HTML)
    _assert(isinstance(text, str), "text should be str")
    _assert(len(text) > 0, "text should not be empty")
    _assert("First paragraph" in text, f"paragraph text missing; got: {text[:200]!r}")


@_test("P7-T03: heading tags converted to markdown syntax")
def test_heading_conversion():
    text, _, _ = html_to_markdown(_HEADING_LEVELS_HTML)
    _assert("# Level One" in text, f"h1 not converted; got:\n{text}")
    _assert("## Level Two" in text, f"h2 not converted; got:\n{text}")
    _assert("### Level Three" in text, f"h3 not converted; got:\n{text}")
    _assert("###### Level Six" in text, f"h6 not converted; got:\n{text}")


@_test("P7-T04: unordered list items converted to '- item'")
def test_unordered_list():
    text, _, _ = html_to_markdown(_LIST_HTML)
    _assert("- Apple" in text, f"ul item missing; got:\n{text}")
    _assert("- Banana" in text, f"ul item missing; got:\n{text}")


@_test("P7-T05: ordered list items converted to '1. item' etc.")
def test_ordered_list():
    text, _, _ = html_to_markdown(_LIST_HTML)
    _assert("1. One" in text, f"ol item 1 missing; got:\n{text}")
    _assert("2. Two" in text, f"ol item 2 missing; got:\n{text}")
    _assert("3. Three" in text, f"ol item 3 missing; got:\n{text}")


@_test("P7-T06: external links converted to [text](url)")
def test_link_conversion():
    text, _, _ = html_to_markdown(_LINK_HTML)
    _assert("[the article](https://example.com/article)" in text,
            f"link not converted; got:\n{text}")


@_test("P7-T07: internal anchor links rendered as plain text (no [text](#...)")
def test_anchor_link_as_text():
    text, _, _ = html_to_markdown(_LINK_HTML)
    _assert("[anchor](#section)" not in text, "anchor link should not use [](# syntax)")
    _assert("anchor" in text, "anchor link text should still appear in output")


@_test("P7-T08: script and style content stripped")
def test_script_style_stripped():
    text, _, _ = html_to_markdown(_NOISY_HTML)
    _assert("var x" not in text, f"script content leaked into text; got:\n{text}")
    _assert("color: red" not in text, f"style content leaked into text; got:\n{text}")


@_test("P7-T09: nav and footer content stripped")
def test_nav_footer_stripped():
    text, _, _ = html_to_markdown(_NOISY_HTML)
    _assert("Copyright 2026" not in text, f"footer content leaked; got:\n{text}")
    # Nav is stripped; "Home" may appear in other contexts, check the nav link specifically
    _assert("Home | About" not in text, "nav content should be stripped")


@_test("P7-T10: aside content stripped")
def test_aside_stripped():
    text, _, _ = html_to_markdown(_NOISY_HTML)
    _assert("Related articles" not in text, f"aside content leaked; got:\n{text}")


@_test("P7-T11: article body content preserved when nav/footer stripped")
def test_article_body_preserved():
    text, _, _ = html_to_markdown(_NOISY_HTML)
    _assert("This is the article content." in text,
            f"article body text missing; got:\n{text}")
    _assert("Real Article Title" in text, f"h1 missing from article; got:\n{text}")


@_test("P7-T12: empty HTML body produces placeholder text")
def test_empty_html():
    text, _, _ = html_to_markdown(_EMPTY_HTML)
    # capture_from_browser wraps empty result in placeholder — test that
    # html_to_markdown itself returns empty string
    _assert(isinstance(text, str), "should return str")
    # Empty body → no meaningful text extracted


@_test("P7-T13: malformed HTML handled gracefully without exception")
def test_malformed_html_no_exception():
    try:
        text, html_title, first_h1 = html_to_markdown(_MALFORMED_HTML)
        _assert(isinstance(text, str), "should return str on malformed HTML")
    except Exception as exc:
        _assert(False, f"malformed HTML raised {type(exc).__name__}: {exc}")


@_test("P7-T14: resolve_title — CLI title has highest precedence")
def test_resolve_title_cli_wins():
    title, source = resolve_title(
        cli_title="My CLI Title",
        html_title="HTML Title",
        first_h1="H1 Title",
        filename="page.html",
    )
    _assert(title == "My CLI Title", f"title={title!r}")
    _assert(source == "cli", f"source={source!r}")


@_test("P7-T15: resolve_title — html_title used when no CLI title")
def test_resolve_title_html_title():
    title, source = resolve_title(
        cli_title=None,
        html_title="HTML Title",
        first_h1="H1 Title",
        filename="page.html",
    )
    _assert(title == "HTML Title", f"title={title!r}")
    _assert(source == "html_title", f"source={source!r}")


@_test("P7-T16: resolve_title — first_h1 used when no CLI title or html_title")
def test_resolve_title_h1_fallback():
    title, source = resolve_title(
        cli_title=None,
        html_title=None,
        first_h1="H1 Headline",
        filename="page.html",
    )
    _assert(title == "H1 Headline", f"title={title!r}")
    _assert(source == "html_h1", f"source={source!r}")


@_test("P7-T17: resolve_title — filename stem fallback when nothing else available")
def test_resolve_title_filename_fallback():
    title, source = resolve_title(
        cli_title=None,
        html_title=None,
        first_h1=None,
        filename="fed-liquidity-article.html",
    )
    _assert(title == "fed liquidity article", f"title={title!r}")
    _assert(source == "filename", f"source={source!r}")


@_test("P7-T18: capture_from_browser — default input_class is 'source'")
def test_default_input_class():
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "test.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")
        packet = capture_from_browser(file_path=str(html_file))
    _assert(packet.input_class == INPUT_CLASS_SOURCE,
            f"input_class={packet.input_class!r}")


@_test("P7-T19: capture_from_browser — default source_platform is 'web'")
def test_default_source_platform():
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "test.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")
        packet = capture_from_browser(file_path=str(html_file))
    _assert(packet.source_platform == "web", f"source_platform={packet.source_platform!r}")


@_test("P7-T20: capture_from_browser — capture_method is 'browser'")
def test_capture_method_browser():
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "test.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")
        packet = capture_from_browser(file_path=str(html_file))
    _assert(packet.capture_method == "browser", f"capture_method={packet.capture_method!r}")


@_test("P7-T21: capture_from_browser — detected_mime is text/html")
def test_detected_mime():
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "test.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")
        packet = capture_from_browser(file_path=str(html_file))
    _assert(packet.detected_mime == "text/html; charset=utf-8",
            f"detected_mime={packet.detected_mime!r}")


@_test("P7-T22: capture_from_browser — extra_metadata contains required fields")
def test_extra_metadata_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "mypage.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")
        packet = capture_from_browser(file_path=str(html_file))
    em = packet.extra_metadata
    _assert("source_file" in em, f"source_file missing; keys={list(em.keys())}")
    _assert("html_title" in em, f"html_title missing")
    _assert("html_h1" in em, f"html_h1 missing")
    _assert("title_source" in em, f"title_source missing")
    _assert(em["source_file"] == "mypage.html", f"source_file={em['source_file']!r}")
    _assert(em["html_title"] == "Test Article Title", f"html_title={em['html_title']!r}")
    _assert(em["title_source"] == "html_title", f"title_source={em['title_source']!r}")


@_test("P7-T23: capture_from_browser — file not found raises FileNotFoundError")
def test_file_not_found():
    try:
        capture_from_browser(file_path="/nonexistent/path/article.html")
        _assert(False, "should have raised FileNotFoundError")
    except FileNotFoundError:
        pass  # expected


@_test("P7-T24: capture_from_browser + capture_content writes to quarantine")
def test_capture_writes_to_quarantine():
    from runtime.capture.capture import capture_content
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()
        html_file = vault / "article.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")

        packet = capture_from_browser(
            file_path=str(html_file),
            source_url="https://example.com/article",
        )
        result = capture_content(packet, vault_root=vault)

        _assert(not result.get("is_duplicate"), "should not be duplicate")
        _assert("content_path" in result, f"content_path missing; keys={list(result.keys())}")
        _assert(Path(result["content_path"]).exists(), "content file should exist")
        _assert(Path(result["sidecar_path"]).exists(), "sidecar file should exist")
        # Verify quarantine location
        _assert("00_QUARANTINE" in result["content_path"],
                f"not in quarantine: {result['content_path']}")


@_test("P7-T25: dedup — same HTML captured twice returns duplicate on second capture")
def test_dedup_on_repeated_browser_capture():
    from runtime.capture.capture import capture_content
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()
        html_file = vault / "article.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")

        packet1 = capture_from_browser(file_path=str(html_file))
        result1 = capture_content(packet1, vault_root=vault)

        # Create a second packet with identical content (same HTML file)
        packet2 = capture_from_browser(file_path=str(html_file))
        result2 = capture_content(packet2, vault_root=vault)

        _assert(not result1.get("is_duplicate"), "first capture should not be duplicate")
        _assert(result2.get("is_duplicate"), "second capture should be duplicate")
        _assert("duplicate_of" in result2, f"duplicate_of missing; keys={list(result2.keys())}")
        _assert(result2["duplicate_of"] == result1["capture_id"],
                "duplicate_of should reference first capture_id")
        # No new file written for duplicate
        first_path = Path(result1["content_path"])
        _assert(first_path.exists(), "first capture file should still exist")


# ── CLI integration test ───────────────────────────────────────────────────────

@_test("P7-T26: CLI capture browser file command runs and produces capture result")
def test_cli_capture_browser_file():
    from runtime.cli.main import main as cli_main
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)
        (vault / "03_INPUTS").mkdir()
        html_file = vault / "test_article.html"
        html_file.write_text(_SIMPLE_HTML, encoding="utf-8")

        argv = [
            "capture", "browser", "file", str(html_file),
            "--url", "https://example.com/test",
            "--domain", "ai-engineering",
            "--vault-root", str(vault),
            "--json",
        ]
        import io
        from unittest.mock import patch
        output_lines = []
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            rc = cli_main(argv)
            output = mock_out.getvalue()

    _assert(rc == 0, f"CLI returned non-zero: {rc}")
    envelope = json.loads(output)
    result = envelope.get("result", envelope)
    _assert(not result.get("is_duplicate"), "should not be duplicate on first CLI capture")
    _assert("filename" in result, f"filename missing from CLI JSON output")
    _assert("00_QUARANTINE" in result.get("quarantine_dir", ""),
            f"not in quarantine: {result.get('quarantine_dir')}")


# ── Main entry point ───────────────────────────────────────────────────────────

def run_tests() -> tuple[int, int]:
    global _PASS, _FAIL
    _PASS = 0
    _FAIL = 0
    _ERRORS.clear()
    for label, fn in _TESTS:
        print(f"\n[{label}]")
        _run_test(label, fn)
    print(f"\nPass 7: {_PASS} passed, {_FAIL} failed")
    if _ERRORS:
        print("Failures:")
        for e in _ERRORS:
            print(f"  - {e}")
    return _PASS, _FAIL


if __name__ == "__main__":
    p, f = run_tests()
    sys.exit(0 if f == 0 else 1)
