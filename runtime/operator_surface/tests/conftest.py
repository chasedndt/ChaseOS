"""
runtime.operator_surface.tests.conftest

Shared pytest fixtures for operator surface tests.

Provides:
  PLAYWRIGHT_AVAILABLE  — module-level bool, same detection as browser_adapter.py
  browser_available     — session-scoped fixture, True if Chromium can launch

Test split convention:
  Contract tests (no browser required) — use page=None / context=None
  Integration tests (browser required) — skip if not browser_available

Skip marker:
  @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
  or use the browser_available fixture for launch-level detection.
"""

import pytest

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment]
    PLAYWRIGHT_AVAILABLE = False


@pytest.fixture(scope="session")
def browser_available() -> bool:
    """
    Session-scoped fixture. Returns True if Playwright is installed AND
    Chromium can be launched. Skips the full Chromium download check —
    just attempts a launch and closes immediately.

    Tests that require a real browser should skipif(not browser_available).
    """
    if not PLAYWRIGHT_AVAILABLE:
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False
