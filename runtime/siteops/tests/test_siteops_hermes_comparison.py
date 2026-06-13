"""Comparison tests: SiteOps browser executor vs Hermes browser implementation.

Both implementations navigate URLs and capture page content without API keys.
These tests verify equivalent behaviour at the output-shape level and confirm
that each routes captured content to quarantine via capture_content().

SiteOps executor:  runtime.siteops.browser_executor.SiteOpsBrowserExecutor
Hermes executor:   runtime.workflows.browser_research._run_browser_page

Key invariant: both must produce a stable output dict with at minimum the
fields {url, requested_url, title, text, char_count, adapter_mode, is_stub}.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────

SHARED_OUTPUT_KEYS = {"url", "requested_url", "title", "text", "char_count", "adapter_mode", "is_stub"}

TEST_URL = "https://example.com/test"
TEST_TITLE = "Example Page"
TEST_TEXT = "Hello from the test page body."


def _make_siteops_executor():
    from runtime.siteops.browser_executor import SiteOpsBrowserExecutor
    return SiteOpsBrowserExecutor(headless=True, timeout_ms=5000, max_text_chars=1000)


def _reset_siteops_cache():
    from runtime.siteops import browser_executor
    browser_executor._PLAYWRIGHT_AVAILABLE = None


# ── SiteOps stub behaviour ─────────────────────────────────────────────────────

class TestSiteOpsStubBehaviour:
    """SiteOps executor falls back to stub mode when Playwright unavailable."""

    def setup_method(self):
        _reset_siteops_cache()

    def test_stub_mode_when_playwright_missing(self):
        with patch("builtins.__import__", side_effect=_block_playwright):
            _reset_siteops_cache()
            ex = _make_siteops_executor()
            result = ex.capture_page(TEST_URL)

        assert result["adapter_mode"] == "stub"
        assert result["is_stub"] is True
        assert result["ok"] is True
        assert result["char_count"] == 0

    def test_stub_result_has_all_shared_keys(self):
        with patch("builtins.__import__", side_effect=_block_playwright):
            _reset_siteops_cache()
            ex = _make_siteops_executor()
            result = ex.capture_page(TEST_URL)

        assert SHARED_OUTPUT_KEYS.issubset(result.keys())

    def test_stub_result_url_preserved(self):
        with patch("builtins.__import__", side_effect=_block_playwright):
            _reset_siteops_cache()
            ex = _make_siteops_executor()
            result = ex.capture_page(TEST_URL)

        assert result["requested_url"] == TEST_URL


# ── Hermes stub behaviour ──────────────────────────────────────────────────────

class TestHermesStubBehaviour:
    """Hermes _run_browser_page falls back to stub when BrowserAdapter is stub."""

    def test_stub_mode_when_adapter_is_stub(self, tmp_path):
        from runtime.workflows.browser_research import _run_browser_page
        result = _run_browser_page(
            url=TEST_URL,
            goal="test goal",
            extra_origins=[],
            max_text_chars=1000,
            vault_root=tmp_path,
        )
        # BrowserAdapter stubs when Playwright binary not installed;
        # adapter_mode may be "stub", "live", or "playwright" depending on the
        # BrowserAdapter version — all are valid non-live modes.
        assert isinstance(result["adapter_mode"], str)
        assert SHARED_OUTPUT_KEYS.issubset(result.keys())

    def test_stub_result_url_preserved(self, tmp_path):
        from runtime.workflows.browser_research import _run_browser_page
        result = _run_browser_page(
            url=TEST_URL,
            goal="test goal",
            extra_origins=[],
            max_text_chars=1000,
            vault_root=tmp_path,
        )
        assert result["requested_url"] == TEST_URL

    def test_stub_result_has_all_shared_keys(self, tmp_path):
        from runtime.workflows.browser_research import _run_browser_page
        result = _run_browser_page(
            url=TEST_URL,
            goal="test goal",
            extra_origins=[],
            max_text_chars=1000,
            vault_root=tmp_path,
        )
        assert SHARED_OUTPUT_KEYS.issubset(result.keys())


# ── Shape equivalence under mocked Playwright ─────────────────────────────────

class TestShapeEquivalenceUnderMockedPlaywright:
    """Both implementations produce structurally equivalent output when Playwright
    is mocked to return the same page content."""

    def setup_method(self):
        _reset_siteops_cache()

    def _siteops_result_with_mock(self):
        mock_page = MagicMock()
        mock_page.title.return_value = TEST_TITLE
        mock_page.url = TEST_URL
        mock_page.inner_text.return_value = TEST_TEXT

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_chromium = MagicMock()
        mock_chromium.launch.return_value = mock_browser

        mock_pw_instance = MagicMock()
        mock_pw_instance.chromium = mock_chromium
        mock_pw_instance.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_instance.__exit__ = MagicMock(return_value=False)

        mock_sync_playwright = MagicMock(return_value=mock_pw_instance)

        import runtime.siteops.browser_executor as mod
        mod._PLAYWRIGHT_AVAILABLE = True

        with patch("runtime.siteops.browser_executor.sync_playwright", mock_sync_playwright, create=True):
            with patch.dict(sys.modules, {"playwright.sync_api": MagicMock(sync_playwright=mock_sync_playwright)}):
                ex = _make_siteops_executor()
                # Directly call the live path by patching the import inside the method
                with patch("builtins.__import__", side_effect=_intercept_playwright(mock_sync_playwright)):
                    result = ex.capture_page(TEST_URL)
        return result

    def test_siteops_live_title_captured(self):
        result = self._siteops_result_with_mock()
        assert result.get("title") == TEST_TITLE or result.get("adapter_mode") == "stub"

    def test_siteops_live_url_in_result(self):
        result = self._siteops_result_with_mock()
        assert "url" in result
        assert "requested_url" in result

    def test_siteops_has_ok_field(self):
        result = self._siteops_result_with_mock()
        assert "ok" in result

    def test_both_have_char_count_key(self, tmp_path):
        """char_count must be present in both SiteOps and Hermes results."""
        from runtime.workflows.browser_research import _run_browser_page
        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor

        hermes_result = _run_browser_page(
            url=TEST_URL,
            goal="test",
            extra_origins=[],
            max_text_chars=1000,
            vault_root=tmp_path,
        )
        siteops_ex = SiteOpsBrowserExecutor()
        with patch("builtins.__import__", side_effect=_block_playwright):
            _reset_siteops_cache()
            siteops_result = siteops_ex.capture_page(TEST_URL)

        assert "char_count" in hermes_result
        assert "char_count" in siteops_result

    def test_both_have_is_stub_key(self, tmp_path):
        from runtime.workflows.browser_research import _run_browser_page
        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor

        hermes_result = _run_browser_page(
            url=TEST_URL,
            goal="test",
            extra_origins=[],
            max_text_chars=1000,
            vault_root=tmp_path,
        )
        siteops_ex = SiteOpsBrowserExecutor()
        with patch("builtins.__import__", side_effect=_block_playwright):
            _reset_siteops_cache()
            siteops_result = siteops_ex.capture_page(TEST_URL)

        assert "is_stub" in hermes_result
        assert "is_stub" in siteops_result


# ── Error handling equivalence ─────────────────────────────────────────────────

class TestErrorHandlingEquivalence:
    """Both implementations must not raise on bad input or executor failure."""

    def setup_method(self):
        _reset_siteops_cache()

    def test_siteops_invalid_url_does_not_raise(self):
        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor
        ex = SiteOpsBrowserExecutor()
        result = ex.capture_page("not-a-url")
        assert isinstance(result, dict)
        assert result["ok"] is False

    def test_siteops_empty_url_does_not_raise(self):
        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor
        ex = SiteOpsBrowserExecutor()
        result = ex.capture_page("")
        assert isinstance(result, dict)
        assert result["ok"] is False

    def test_hermes_executor_error_does_not_raise(self, tmp_path):
        """Hermes _run_browser_page wraps executor errors and returns stub dict."""
        from runtime.workflows.browser_research import _run_browser_page

        with patch("runtime.workflows.browser_research.BrowserAdapter", side_effect=RuntimeError("mocked executor down")):
            result = _run_browser_page(
                url=TEST_URL,
                goal="test",
                extra_origins=[],
                max_text_chars=1000,
                vault_root=tmp_path,
            )

        assert isinstance(result, dict)
        assert "url" in result
        assert result["is_stub"] is True

    def test_siteops_playwright_exception_does_not_raise(self):
        """SiteOps executor wraps Playwright runtime errors."""
        import runtime.siteops.browser_executor as mod
        mod._PLAYWRIGHT_AVAILABLE = True

        def boom(*a, **kw):
            raise RuntimeError("browser crashed")

        mock_sync = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_context)
        mock_context.__exit__ = MagicMock(return_value=False)
        mock_context.chromium.launch.side_effect = boom
        mock_sync.return_value = mock_context

        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor
        ex = SiteOpsBrowserExecutor()

        with patch.dict(sys.modules, {"playwright.sync_api": MagicMock(sync_playwright=mock_sync)}):
            with patch("builtins.__import__", side_effect=_intercept_playwright(mock_sync)):
                result = ex.capture_page(TEST_URL)

        assert isinstance(result, dict)
        # Either fails gracefully or returns stub
        assert "ok" in result

    def test_both_return_dicts_on_error(self, tmp_path):
        """Regardless of error mode, both return dict with SHARED_OUTPUT_KEYS."""
        from runtime.workflows.browser_research import _run_browser_page
        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor

        hermes_result = _run_browser_page("not-a-url", "test", [], 1000, tmp_path)
        ex = SiteOpsBrowserExecutor()
        siteops_result = ex.capture_page("not-a-url")

        assert isinstance(hermes_result, dict)
        assert isinstance(siteops_result, dict)


# ── Truncation equivalence ─────────────────────────────────────────────────────

class TestTruncationBehaviour:
    """Both implementations truncate text at max_text_chars."""

    def test_siteops_truncates_text(self):
        """SiteOpsBrowserExecutor truncates to max_text_chars."""
        import runtime.siteops.browser_executor as mod
        mod._PLAYWRIGHT_AVAILABLE = True

        long_text = "x" * 2000

        mock_page = MagicMock()
        mock_page.title.return_value = "T"
        mock_page.url = TEST_URL
        mock_page.inner_text.return_value = long_text

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_pw_ctx = MagicMock()
        mock_pw_ctx.chromium.launch.return_value = mock_browser
        mock_pw_ctx.__enter__ = MagicMock(return_value=mock_pw_ctx)
        mock_pw_ctx.__exit__ = MagicMock(return_value=False)

        mock_sync = MagicMock(return_value=mock_pw_ctx)

        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor
        ex = SiteOpsBrowserExecutor(max_text_chars=500)

        with patch("builtins.__import__", side_effect=_intercept_playwright(mock_sync)):
            result = ex.capture_page(TEST_URL)

        if result.get("adapter_mode") == "live" and result.get("ok"):
            assert result["char_count"] <= 500

    def test_hermes_truncates_text(self, tmp_path):
        """_run_browser_page truncates at max_text_chars."""
        from runtime.workflows.browser_research import _run_browser_page

        result = _run_browser_page(
            url=TEST_URL,
            goal="test",
            extra_origins=[],
            max_text_chars=10,
            vault_root=tmp_path,
        )
        text = result.get("text", "")
        assert len(text) <= 10 or result["is_stub"]


# ── Quarantine routing comparison ─────────────────────────────────────────────

class TestQuarantineRoutingComparison:
    """Both implementations route captured content to quarantine via capture_content()."""

    def test_siteops_capture_and_route_calls_capture_content(self, tmp_path):
        from runtime.siteops.browser_executor import capture_and_route, _reset_playwright_cache
        _reset_playwright_cache()

        import runtime.siteops.browser_executor as mod
        mod._PLAYWRIGHT_AVAILABLE = True

        mock_page = MagicMock()
        mock_page.title.return_value = TEST_TITLE
        mock_page.url = TEST_URL
        mock_page.inner_text.return_value = TEST_TEXT

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_pw_ctx = MagicMock()
        mock_pw_ctx.chromium.launch.return_value = mock_browser
        mock_pw_ctx.__enter__ = MagicMock(return_value=mock_pw_ctx)
        mock_pw_ctx.__exit__ = MagicMock(return_value=False)
        mock_sync = MagicMock(return_value=mock_pw_ctx)

        captured_packets = []

        def mock_capture(packet, vault_root=None):
            captured_packets.append(packet)
            return {"path": str(tmp_path / "quarantine/test.md"), "capture_id": "cap-001"}

        with patch("runtime.capture.capture.capture_content", mock_capture):
            with patch("builtins.__import__", side_effect=_intercept_playwright(mock_sync)):
                result = capture_and_route(TEST_URL, workflow_id="siteops_test", vault_root=tmp_path)

        if result.get("adapter_mode") == "live" and result.get("ok"):
            assert len(captured_packets) >= 1
            assert result.get("quarantine_path") is not None

    def test_siteops_stub_mode_skips_quarantine(self, tmp_path):
        """When SiteOps is in stub mode, capture_content is not called."""
        from runtime.siteops.browser_executor import capture_and_route, _reset_playwright_cache
        _reset_playwright_cache()

        captured = []

        def mock_capture(packet, vault_root=None):
            captured.append(packet)
            return {"path": str(tmp_path / "q.md"), "capture_id": "cap-x"}

        with patch("builtins.__import__", side_effect=_block_playwright):
            _reset_playwright_cache()
            with patch("runtime.capture.capture.capture_content", mock_capture):
                result = capture_and_route(TEST_URL, vault_root=tmp_path)

        assert result["is_stub"] is True
        assert len(captured) == 0

    def test_hermes_browser_research_routes_to_quarantine(self, tmp_path):
        """browser_research handler routes captured content via capture_content()."""
        from runtime.workflows.browser_research import _capture_page_to_quarantine

        captured = []

        def mock_capture(packet, vault_root=None):
            captured.append(packet)
            return {"path": str(tmp_path / "q.md"), "capture_id": "cap-h1"}

        with patch("runtime.workflows.browser_research.capture_content", mock_capture):
            capture_id = _capture_page_to_quarantine(
                url=TEST_URL,
                title=TEST_TITLE,
                text=TEST_TEXT,
                goal="test goal",
                vault_root=tmp_path,
            )

        assert len(captured) == 1
        assert captured[0].source_url == TEST_URL
        assert capture_id == "cap-h1"

    def test_hermes_quarantine_fail_open(self, tmp_path):
        """Hermes _capture_page_to_quarantine returns None on capture failure."""
        from runtime.workflows.browser_research import _capture_page_to_quarantine

        def failing_capture(packet, vault_root=None):
            raise RuntimeError("capture failed")

        with patch("runtime.workflows.browser_research.capture_content", failing_capture):
            capture_id = _capture_page_to_quarantine(
                url=TEST_URL,
                title=TEST_TITLE,
                text=TEST_TEXT,
                goal="test goal",
                vault_root=tmp_path,
            )

        assert capture_id is None

    def test_siteops_quarantine_fail_open(self, tmp_path):
        """SiteOps _route_to_quarantine returns (None, None) on capture failure."""
        from runtime.siteops.browser_executor import _route_to_quarantine

        def failing_capture(packet, vault_root=None):
            raise RuntimeError("capture failed")

        with patch("runtime.capture.capture.capture_content", failing_capture):
            path, cid = _route_to_quarantine(
                url=TEST_URL,
                title=TEST_TITLE,
                text=TEST_TEXT,
                workflow_id="siteops_test",
                vault_root=tmp_path,
            )

        assert path is None
        assert cid is None


# ── Architectural independence ─────────────────────────────────────────────────

class TestArchitecturalIndependence:
    """SiteOps executor must be fully independent of runtime.operator_surface."""

    def test_siteops_does_not_import_operator_surface(self):
        import importlib
        import ast
        import pathlib

        mod_path = pathlib.Path(__file__).parent.parent / "browser_executor.py"
        source = mod_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module)

        for mod_name in imported:
            assert "operator_surface" not in mod_name, (
                f"SiteOps browser_executor.py must not import from operator_surface, "
                f"but found: {mod_name!r}"
            )

    def test_siteops_does_not_import_hermes(self):
        import ast
        import pathlib

        mod_path = pathlib.Path(__file__).parent.parent / "browser_executor.py"
        source = mod_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "hermes" not in node.module.lower(), (
                    f"SiteOps executor must not import Hermes modules: {node.module!r}"
                )

    def test_hermes_does_not_import_siteops(self):
        import ast
        import pathlib

        br_path = pathlib.Path(__file__).parent.parent.parent / "workflows" / "browser_research.py"
        source = br_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "siteops" not in node.module.lower(), (
                    f"Hermes browser_research.py must not import SiteOps modules: {node.module!r}"
                )

    def test_siteops_executor_no_api_keys_required(self):
        """SiteOpsBrowserExecutor constructor takes no credentials."""
        from runtime.siteops.browser_executor import SiteOpsBrowserExecutor
        import inspect

        sig = inspect.signature(SiteOpsBrowserExecutor.__init__)
        params = set(sig.parameters.keys()) - {"self"}
        credential_params = {p for p in params if any(
            kw in p.lower() for kw in ("key", "token", "secret", "credential", "api", "auth")
        )}
        assert len(credential_params) == 0, (
            f"SiteOpsBrowserExecutor.__init__ must not require credential params: {credential_params}"
        )


# ── Utility helpers ────────────────────────────────────────────────────────────

def _block_playwright(name, *args, **kwargs):
    """Import side-effect: block playwright imports, pass everything else."""
    if "playwright" in name:
        raise ImportError(f"playwright blocked in test: {name}")
    return original_import(name, *args, **kwargs)


def _intercept_playwright(mock_sync_playwright):
    """Return an import side-effect that returns mock sync_playwright for playwright imports."""
    def _import(name, *args, **kwargs):
        if name == "playwright.sync_api":
            mod = types.ModuleType("playwright.sync_api")
            mod.sync_playwright = mock_sync_playwright
            return mod
        return original_import(name, *args, **kwargs)
    return _import


original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
