"""
test_connector_size_guards.py — Tests for P-C1 / P-C2 / P-C3 hardening

P-C1: rss_connector.py  — MAX_ITEMS_PER_FEED hard ceiling
P-C2: watch_folders.py  — MAX_WATCHED_FILE_SIZE_BYTES skip guard
P-C3: browser_connector.py — MAX_HTML_INPUT_CHARS input guard
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.capture.connectors.rss_connector import (
    MAX_ITEMS_PER_FEED,
    items_to_packets,
)
from runtime.capture.connectors.browser_connector import (
    MAX_HTML_INPUT_CHARS,
    capture_from_browser,
)
from runtime.capture.watch_folders import (
    MAX_WATCHED_FILE_SIZE_BYTES,
    FileSkipped,
    scan_folder,
    load_config,
    load_processed,
    save_config,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_item(title: str = "Test Item", link: str = "https://example.com/1") -> dict:
    return {"title": title, "link": link, "description": "body"}


def _make_items(n: int) -> list[dict]:
    return [_make_item(f"Item {i}", f"https://example.com/{i}") for i in range(n)]


# ─────────────────────────────────────────────────────────────────────────────
# P-C1: RSS MAX_ITEMS_PER_FEED
# ─────────────────────────────────────────────────────────────────────────────

class TestRssMaxItemsConstant:
    def test_constant_exists(self):
        assert MAX_ITEMS_PER_FEED == 200

    def test_constant_is_positive_int(self):
        assert isinstance(MAX_ITEMS_PER_FEED, int)
        assert MAX_ITEMS_PER_FEED > 0


class TestRssMaxItemsCeiling:
    """items_to_packets() must enforce MAX_ITEMS_PER_FEED regardless of operator limit."""

    def _call(self, items, limit=None):
        packets, skipped = items_to_packets(
            items,
            feed_url="https://example.com/feed.rss",
            feed_title="Test Feed",
            feed_type="rss",
            source_platform="example-com",
            limit=limit,
        )
        return packets, skipped

    def test_exactly_max_items_passes_through(self):
        items = _make_items(MAX_ITEMS_PER_FEED)
        packets, _ = self._call(items)
        assert len(packets) == MAX_ITEMS_PER_FEED

    def test_over_max_items_truncated_to_ceiling(self):
        items = _make_items(MAX_ITEMS_PER_FEED + 50)
        packets, _ = self._call(items)
        assert len(packets) == MAX_ITEMS_PER_FEED

    def test_far_over_max_items_truncated(self):
        items = _make_items(MAX_ITEMS_PER_FEED * 5)
        packets, _ = self._call(items)
        assert len(packets) == MAX_ITEMS_PER_FEED

    def test_under_max_items_not_affected(self):
        items = _make_items(10)
        packets, _ = self._call(items)
        assert len(packets) == 10

    def test_zero_items_ok(self):
        packets, _ = self._call([])
        assert len(packets) == 0

    def test_operator_limit_further_reduces_below_ceiling(self):
        # If there are 300 items and operator limit=5, result should be 5
        items = _make_items(300)
        packets, _ = self._call(items, limit=5)
        assert len(packets) == 5

    def test_operator_limit_cannot_exceed_ceiling(self):
        # If there are 300 items and operator limit=300, ceiling caps at MAX_ITEMS_PER_FEED
        items = _make_items(300)
        packets, _ = self._call(items, limit=300)
        assert len(packets) == MAX_ITEMS_PER_FEED

    def test_operator_limit_at_exactly_ceiling(self):
        items = _make_items(MAX_ITEMS_PER_FEED + 10)
        packets, _ = self._call(items, limit=MAX_ITEMS_PER_FEED)
        assert len(packets) == MAX_ITEMS_PER_FEED

    def test_ceiling_applied_before_operator_limit(self):
        # Ceiling truncates first; operator limit reduces second.
        # 250 items, ceiling=200, limit=150 → 150 packets
        items = _make_items(250)
        packets, _ = self._call(items, limit=150)
        assert len(packets) == 150

    def test_packet_titles_are_from_first_n_items(self):
        # After ceiling truncation, we should have the first MAX_ITEMS_PER_FEED items
        items = _make_items(MAX_ITEMS_PER_FEED + 10)
        packets, _ = self._call(items)
        assert packets[0].title == "Item 0"
        assert packets[-1].title == f"Item {MAX_ITEMS_PER_FEED - 1}"


# ─────────────────────────────────────────────────────────────────────────────
# P-C2: watch_folders MAX_WATCHED_FILE_SIZE_BYTES
# ─────────────────────────────────────────────────────────────────────────────

class TestWatchFoldersSizeConstant:
    def test_constant_exists(self):
        assert MAX_WATCHED_FILE_SIZE_BYTES == 10 * 1024 * 1024

    def test_constant_is_positive_int(self):
        assert isinstance(MAX_WATCHED_FILE_SIZE_BYTES, int)
        assert MAX_WATCHED_FILE_SIZE_BYTES > 0


class TestWatchFoldersSizeGuard:
    """scan_folder() must skip files exceeding MAX_WATCHED_FILE_SIZE_BYTES."""

    def _setup_vault(self, tmp: Path) -> Path:
        vault = tmp / "vault"
        vault.mkdir()
        (vault / ".chaseos").mkdir()
        return vault

    def _add_folder_to_config(self, vault: Path, folder: Path) -> None:
        config = load_config(vault)
        if "folders" not in config:
            config["folders"] = []
        config["folders"].append({
            "path": str(folder),
            "enabled": True,
            "input_class": "source",
            "source_platform": "watched-folder",
            "extensions": [".txt"],
        })
        save_config(vault, config)

    def test_oversized_file_produces_file_skipped(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        folder = tmp_path / "watch_dir"
        folder.mkdir()

        big_file = folder / "big.txt"
        # Write a file that is exactly one byte over the limit
        big_file.write_bytes(b"x" * (MAX_WATCHED_FILE_SIZE_BYTES + 1))

        self._add_folder_to_config(vault, folder)
        config = load_config(vault)
        folder_def = config["folders"][0]
        processed = load_processed(vault)

        result = scan_folder(folder_def, vault, processed)
        assert len(result.skipped) == 1
        assert result.skipped[0].file_path == big_file
        assert result.skipped[0].reason == "file_too_large"
        assert len(result.captured) == 0

    def test_exactly_at_limit_not_skipped(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        folder = tmp_path / "watch_dir"
        folder.mkdir()

        ok_file = folder / "ok.txt"
        # Exactly at the limit — must not be skipped due to size
        ok_file.write_bytes(b"x" * MAX_WATCHED_FILE_SIZE_BYTES)

        self._add_folder_to_config(vault, folder)
        config = load_config(vault)
        folder_def = config["folders"][0]
        processed = load_processed(vault)

        result = scan_folder(folder_def, vault, processed)
        # May be captured or duplicated — just not skipped with reason=file_too_large
        size_skipped = [s for s in result.skipped if s.reason == "file_too_large"]
        assert len(size_skipped) == 0

    def test_normal_small_file_is_not_skipped(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        folder = tmp_path / "watch_dir"
        folder.mkdir()

        small_file = folder / "small.txt"
        small_file.write_text("hello world", encoding="utf-8")

        self._add_folder_to_config(vault, folder)
        config = load_config(vault)
        folder_def = config["folders"][0]
        processed = load_processed(vault)

        result = scan_folder(folder_def, vault, processed)
        size_skipped = [s for s in result.skipped if s.reason == "file_too_large"]
        assert len(size_skipped) == 0

    def test_oversized_file_is_marked_processed(self, tmp_path):
        """Oversized file must be marked processed to prevent infinite retry."""
        vault = self._setup_vault(tmp_path)
        folder = tmp_path / "watch_dir"
        folder.mkdir()

        big_file = folder / "big.txt"
        big_file.write_bytes(b"x" * (MAX_WATCHED_FILE_SIZE_BYTES + 1))

        self._add_folder_to_config(vault, folder)
        config = load_config(vault)
        folder_def = config["folders"][0]

        # First scan — file should be skipped as too large
        processed1 = load_processed(vault)
        result1 = scan_folder(folder_def, vault, processed1)
        assert len(result1.skipped) == 1

        # Simulate persisting processed state by saving it
        from runtime.capture.watch_folders import save_processed
        save_processed(vault, processed1)

        # Second scan — file has not changed; already in processed registry
        processed2 = load_processed(vault)
        result2 = scan_folder(folder_def, vault, processed2)
        # Already processed — silently skipped, no entry in skipped list
        assert len(result2.skipped) == 0
        assert len(result2.errors) == 0

    def test_mixed_sizes_only_oversized_skipped(self, tmp_path):
        vault = self._setup_vault(tmp_path)
        folder = tmp_path / "watch_dir"
        folder.mkdir()

        small = folder / "small.txt"
        small.write_text("small content", encoding="utf-8")

        big = folder / "big.txt"
        big.write_bytes(b"x" * (MAX_WATCHED_FILE_SIZE_BYTES + 1))

        self._add_folder_to_config(vault, folder)
        config = load_config(vault)
        folder_def = config["folders"][0]
        processed = load_processed(vault)

        result = scan_folder(folder_def, vault, processed)
        size_skipped = [s for s in result.skipped if s.reason == "file_too_large"]
        assert len(size_skipped) == 1
        assert size_skipped[0].file_path == big
        # Small file was processed normally
        assert len(result.errors) == 0


# ─────────────────────────────────────────────────────────────────────────────
# P-C3: browser_connector MAX_HTML_INPUT_CHARS
# ─────────────────────────────────────────────────────────────────────────────

class TestBrowserConnectorSizeConstant:
    def test_constant_exists(self):
        assert MAX_HTML_INPUT_CHARS == 500_000

    def test_constant_is_positive_int(self):
        assert isinstance(MAX_HTML_INPUT_CHARS, int)
        assert MAX_HTML_INPUT_CHARS > 0


class TestBrowserConnectorSizeGuard:
    """capture_from_browser() must raise ValueError for HTML exceeding MAX_HTML_INPUT_CHARS."""

    def test_oversized_html_raises_value_error(self, tmp_path):
        big_html = tmp_path / "big.html"
        # Build an HTML file with content body exceeding the limit
        body = "x" * (MAX_HTML_INPUT_CHARS + 1)
        big_html.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")

        with pytest.raises(ValueError, match="HTML input too large"):
            capture_from_browser(file_path=str(big_html))

    def test_exactly_at_limit_does_not_raise(self, tmp_path):
        at_limit_html = tmp_path / "atlimit.html"
        # Build content that totals exactly MAX_HTML_INPUT_CHARS after the wrapper
        # Use a body that with wrapper stays at exactly MAX_HTML_INPUT_CHARS characters
        wrapper = "<html><body></body></html>"
        body_len = MAX_HTML_INPUT_CHARS - len(wrapper)
        body = "y" * body_len
        html_str = f"<html><body>{body}</body></html>"
        assert len(html_str) == MAX_HTML_INPUT_CHARS
        at_limit_html.write_text(html_str, encoding="utf-8")

        # Should not raise
        packet = capture_from_browser(file_path=str(at_limit_html))
        assert packet is not None

    def test_error_message_contains_char_counts(self, tmp_path):
        big_html = tmp_path / "big.html"
        oversized = MAX_HTML_INPUT_CHARS + 100
        body = "z" * (oversized - len("<html><body></body></html>"))
        big_html.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            capture_from_browser(file_path=str(big_html))

        msg = str(exc_info.value)
        assert "MAX_HTML_INPUT_CHARS" in msg
        assert "chars" in msg.lower()

    def test_normal_sized_html_produces_packet(self, tmp_path):
        small_html = tmp_path / "article.html"
        small_html.write_text(
            "<html><head><title>Test Article</title></head>"
            "<body><h1>Headline</h1><p>Content paragraph.</p></body></html>",
            encoding="utf-8",
        )
        packet = capture_from_browser(file_path=str(small_html))
        assert packet.title == "Test Article"
        assert "Headline" in packet.content

    def test_missing_file_still_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            capture_from_browser(file_path=str(tmp_path / "nonexistent.html"))

    def test_guard_fires_before_html_to_markdown(self, tmp_path, monkeypatch):
        """Verify the guard is placed before html_to_markdown(), not after."""
        from runtime.capture.connectors import browser_connector

        called = []

        original = browser_connector.html_to_markdown
        def spy_html_to_markdown(content):
            called.append(len(content))
            return original(content)

        monkeypatch.setattr(browser_connector, "html_to_markdown", spy_html_to_markdown)

        big_html = tmp_path / "big.html"
        body = "a" * (MAX_HTML_INPUT_CHARS + 1)
        big_html.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")

        with pytest.raises(ValueError, match="HTML input too large"):
            capture_from_browser(file_path=str(big_html))

        # html_to_markdown must NOT have been called
        assert len(called) == 0
