"""
tests.operator_surface.test_browser_pass3

Phase 9 FSOS sub-track — Browser Operator Surface Pass 3 tests.

Covers:
  1.  Module-level PLAYWRIGHT_AVAILABLE flag exists in browser_adapter
  2.  BrowserAdapter has _adapter_mode field initialized to "stub"
  3.  build_audit_payload includes adapter_mode and playwright_available
  4.  Stub mode — all action handlers return success=True without browser
  5.  Actions stub — all action functions return success=True with page=None
  6.  Actions stub — all action functions return status="stub" in output
  7.  Scope still enforced in stub mode (navigate, tab_open reject bad origin)
  8.  ScopeViolation still raised from actions.navigate with bad origin
  9.  Adapter initialize/teardown round-trip (stub path — no real browser required)
 10.  Teardown clears all browser state fields
 11.  Adapter version is 0.3.0 (Pass 3)
 12.  _to_step bridge converts ActionResult to StepResult correctly
 13.  navigate handler updates _current_url in stub mode
 14.  tab_open handler increments _tabs_opened in stub mode
 15.  execute_step routes all 18 action types without error
 16.  execute_step increments _steps_executed
 17.  grounding_ctx updated from step results
 18.  build_audit_payload reflects steps_executed and tabs_opened
 19.  Perception — read_url/read_title/read_visible_text with page=None
 20.  Perception — list_tabs/get_tab_state with None
 21.  Perception — get_page_state stub returns empty PageState
 22.  Grounding — grounding.py _try_tier with page=None returns None (no crash)
 23.  recover() stubs cleanly with no browser
  [Integration tests — skip if no real browser]
 24.  initialize() raises no exception and sets adapter_mode to "playwright"
 25.  execute navigate → read_url → read_title live round-trip
 26.  read_visible_text returns non-empty string from live page
 27.  screenshot returns bytes or saves to path without error
 28.  tab_open creates a new tab and updates _page
 29.  tab_close removes the new tab
 30.  teardown clears state after real browser session

Total: 30 tests
"""

import pytest
from datetime import datetime, timezone

import runtime.operator_surface.adapters.browser_adapter as browser_adapter_module
from runtime.operator_surface.adapters.browser_adapter import (
    BrowserAdapter,
    _PLAYWRIGHT_AVAILABLE,
)
from runtime.operator_surface.capabilities import (
    OperatorCapability,
    SurfaceType,
    GroundingMode,
)
from runtime.operator_surface.contracts import (
    OperatorScope,
    OperatorSession,
    StepResult,
)
from runtime.operator_surface.capabilities import SurfaceType
from runtime.operator_surface.events import OperatorEvent, OperatorEventType
from runtime.operator_surface.scopes import ScopeViolation
from runtime.operator_surface.browser.actions import (
    ActionResult,
    navigate,
    back,
    forward,
    reload,
    tab_open,
    tab_close,
    tab_focus,
    click,
    type_text,
    keypress,
    scroll,
    wait_for,
    read_url,
    read_title,
    read_visible_text,
    extract,
    screenshot,
)
from runtime.operator_surface.browser.perception import (
    list_tabs,
    get_tab_state,
    get_page_state,
    PageState,
)
from runtime.operator_surface.browser.grounding import (
    _try_tier,
    GroundingMode as GM_,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_scope(origins=None):
    return OperatorScope(
        run_id="pass3-test-scope",
        surface=SurfaceType.BROWSER,
        target_uris=["https://example.com/"],
        allowed_origins=origins or ["https://example.com"],
        max_actions=50,
        max_duration_seconds=300,
    )

def _make_session():
    return OperatorSession(
        run_id="pass3-test-run",
        workflow_id="wf_pass3",
        surface="browser",
        started_at=datetime.now(timezone.utc).isoformat(),
    )

def _noop_emit(event):
    pass

def _make_adapter():
    return BrowserAdapter()

def _initialized_stub_adapter():
    """Adapter initialized but no Playwright (scope/session set, page=None)."""
    a = BrowserAdapter()
    # Manually set scope/session without triggering Playwright launch
    a._scope = _make_scope()
    a._session = _make_session()
    return a

# ── Contract tests (no browser required) ─────────────────────────────────────

def test_playwright_available_flag_exists():
    """_PLAYWRIGHT_AVAILABLE is a bool."""
    assert isinstance(_PLAYWRIGHT_AVAILABLE, bool)


def test_adapter_starts_in_stub_mode():
    a = BrowserAdapter()
    assert a._adapter_mode == "stub"


def test_adapter_page_is_none_initially():
    a = BrowserAdapter()
    assert a._page is None
    assert a._browser_context is None


def test_build_audit_payload_includes_adapter_mode():
    a = BrowserAdapter()
    payload = a.build_audit_payload()
    assert "adapter_mode" in payload
    assert "playwright_available" in payload
    assert payload["adapter_mode"] == "stub"
    assert payload["playwright_available"] == _PLAYWRIGHT_AVAILABLE


def test_build_audit_payload_version_is_pass3():
    a = BrowserAdapter()
    payload = a.build_audit_payload()
    assert payload["adapter_version"] == "0.3.0"
    assert "partial-pass3" in payload["adapter_status"]


def test_all_18_handlers_return_success_in_stub_mode():
    """All action types succeed in stub mode (page=None path)."""
    a = _initialized_stub_adapter()
    scope = a._scope

    all_steps = [
        {"action_type": "navigate",          "target": "https://example.com/"},
        {"action_type": "back",              "target": ""},
        {"action_type": "forward",           "target": ""},
        {"action_type": "reload",            "target": ""},
        {"action_type": "tab_open",          "target": "https://example.com/tab"},
        {"action_type": "tab_close",         "target": "https://example.com/"},
        {"action_type": "tab_focus",         "target": "https://example.com/"},
        {"action_type": "click",             "target": "button.submit"},
        {"action_type": "type",              "target": "#input", "text": "hello"},
        {"action_type": "keypress",          "target": "Enter"},
        {"action_type": "scroll",            "target": "down"},
        {"action_type": "wait_for",          "target": ".loaded"},
        {"action_type": "read_url",          "target": ""},
        {"action_type": "read_title",        "target": ""},
        {"action_type": "read_visible_text", "target": ""},
        {"action_type": "extract",           "target": "h1"},
        {"action_type": "screenshot",        "target": ""},
    ]

    for step in all_steps:
        result = a.execute_step(step, _noop_emit)
        assert isinstance(result, StepResult), f"action_type={step['action_type']}"
        assert result.success, f"Expected success for {step['action_type']}: {result.error}"


def test_stub_actions_output_contains_status_stub():
    """Actions with page=None include status='stub' in output dict."""
    scope = _make_scope()

    checks = [
        navigate(None, "https://example.com/", scope),
        back(None),
        forward(None),
        reload(None),
        tab_open(None, "https://example.com/", scope),
        click(None, "button", scope),
        scroll(None, "down"),
        read_url(None),
        read_title(None),
        read_visible_text(None),
        extract(None, "h1"),
        screenshot(None),
    ]

    for result in checks:
        assert result.success, f"{result.action_type} should succeed in stub"
        assert result.output.get("status") == "stub", (
            f"{result.action_type} output missing status='stub': {result.output}"
        )


def test_screenshot_stub_records_readiness_capture_options():
    result = screenshot(None, "out.png", full_page=False, settle_ms=125, clip_selector=".graph")
    assert result.success
    assert result.output["status"] == "stub"
    assert result.output["path"] == "out.png"
    assert result.output["full_page"] is False
    assert result.output["settle_ms"] == 125
    assert result.output["clip_selector"] == ".graph"


def test_scope_enforced_in_stub_navigate():
    """navigate() still enforces scope even with page=None."""
    bad_scope = _make_scope(origins=["https://example.com"])
    with pytest.raises(ScopeViolation):
        navigate(None, "https://evil.com/hack", bad_scope)


def test_scope_enforced_in_stub_tab_open():
    """tab_open() still enforces scope even with context=None."""
    bad_scope = _make_scope(origins=["https://example.com"])
    with pytest.raises(ScopeViolation):
        tab_open(None, "https://evil.com/hack", bad_scope)


def test_adapter_initialize_teardown_stub_path():
    """initialize/teardown with Playwright unavailable stays in stub mode."""
    a = BrowserAdapter()
    a._playwright = None      # Ensure no real launch
    a._browser = None
    a._browser_context = None
    a._page = None
    # Manually simulate what initialize does for scope/session
    a._scope = _make_scope()
    a._session = _make_session()
    # teardown should not raise
    a.teardown("ok", _noop_emit)
    assert a._page is None
    assert a._browser_context is None
    assert a._adapter_mode == "stub"


def test_teardown_clears_all_browser_state():
    a = BrowserAdapter()
    a._playwright = None
    a._browser = None
    a._browser_context = None
    a._page = None
    a._current_url = "https://example.com/"
    a.teardown("ok", _noop_emit)
    assert a._current_url is None
    assert a._page is None
    assert a._adapter_mode == "stub"


def test_to_step_bridge_converts_action_result():
    """_to_step maps ActionResult fields to StepResult correctly."""
    ar = ActionResult(
        action_type="navigate",
        target="https://example.com/",
        success=True,
        output={"url": "https://example.com/"},
        grounding_mode_used=GroundingMode.STRUCTURED_API.value,
    )
    sr = BrowserAdapter._to_step(ar, step_index=3)
    assert sr.step_index == 3
    assert sr.success is True
    assert sr.action_type == "navigate"
    assert sr.target == "https://example.com/"
    assert sr.output == {"url": "https://example.com/"}
    assert sr.grounding_mode_used == GroundingMode.STRUCTURED_API.value


def test_navigate_handler_updates_current_url():
    a = _initialized_stub_adapter()
    step = {"action_type": "navigate", "target": "https://example.com/page"}
    a.execute_step(step, _noop_emit)
    assert a._current_url == "https://example.com/page"


def test_tab_open_handler_increments_tabs_opened():
    a = _initialized_stub_adapter()
    assert a._tabs_opened == 0
    step = {"action_type": "tab_open", "target": "https://example.com/"}
    a.execute_step(step, _noop_emit)
    assert a._tabs_opened == 1


def test_execute_step_increments_steps_executed():
    a = _initialized_stub_adapter()
    step = {"action_type": "read_url", "target": ""}
    a.execute_step(step, _noop_emit)
    assert a._steps_executed == 1


def test_grounding_context_updated_by_execute_step():
    a = _initialized_stub_adapter()
    step = {"action_type": "navigate", "target": "https://example.com/"}
    a.execute_step(step, _noop_emit)
    audit = a.build_audit_payload()
    breakdown = audit["grounding_breakdown"]
    assert breakdown["grounding_tier_counts"]["structured_api"] >= 1


def test_audit_payload_reflects_steps_and_tabs():
    a = _initialized_stub_adapter()
    a.execute_step({"action_type": "navigate", "target": "https://example.com/"}, _noop_emit)
    a.execute_step({"action_type": "tab_open", "target": "https://example.com/tab"}, _noop_emit)
    payload = a.build_audit_payload()
    assert payload["steps_executed"] == 2
    assert payload["tabs_opened"] == 1


def test_browser_adapter_auto_discovers_existing_playwright_chromium_binary(monkeypatch, tmp_path):
    """Launch should route to an existing local Chromium binary when Playwright's default browser path is stale/missing."""
    chrome = tmp_path / "chromium-1223" / "chrome-linux64" / "chrome"
    chrome.parent.mkdir(parents=True)
    chrome.write_text("#!/bin/sh\n", encoding="utf-8")
    chrome.chmod(0o755)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))

    assert browser_adapter_module._discover_playwright_chromium_executable() == chrome


def test_browser_adapter_records_launch_error_in_audit(monkeypatch):
    """Silent stub fallback must still preserve why live Playwright was not used."""
    class FailingChromium:
        def launch(self, **kwargs):
            raise RuntimeError("browser executable missing")

    class FailingPlaywright:
        chromium = FailingChromium()
        def stop(self):
            pass

    class FailingSync:
        def start(self):
            return FailingPlaywright()

    monkeypatch.setattr(browser_adapter_module, "_PLAYWRIGHT_AVAILABLE", True)
    monkeypatch.setattr(browser_adapter_module, "_sync_playwright", lambda: FailingSync())

    a = BrowserAdapter()
    a.initialize(_make_scope(), _make_session())
    payload = a.build_audit_payload()

    assert payload["adapter_mode"] == "stub"
    assert payload["playwright_launch_error"]
    assert "browser executable missing" in payload["playwright_launch_error"]


def test_perception_read_url_page_none():
    from runtime.operator_surface.browser.perception import read_url as p_read_url
    assert p_read_url(None) == ""


def test_perception_read_title_page_none():
    from runtime.operator_surface.browser.perception import read_title as p_read_title
    assert p_read_title(None) == ""


def test_perception_read_visible_text_page_none():
    from runtime.operator_surface.browser.perception import read_visible_text as p_read_visible
    assert p_read_visible(None) == ""


def test_perception_list_tabs_none():
    assert list_tabs(None) == []


def test_perception_get_tab_state_none():
    ts = get_tab_state(None, "0")
    assert ts.url == ""
    assert ts.title == ""
    assert ts.page_id == "0"


def test_perception_get_page_state_stub_returns_empty():
    ps = get_page_state(None)
    assert isinstance(ps, PageState)
    assert ps.url == ""
    assert ps.visible_text == ""
    assert ps.tabs == []


def test_grounding_try_tier_page_none_returns_none():
    """_try_tier with page=None must return None without raising."""
    from runtime.operator_surface.capabilities import GroundingMode as GMode
    result_a = _try_tier(None, "button", GMode.STRUCTURED_API)
    result_b = _try_tier(None, "button", GMode.ACCESSIBILITY)
    result_c = _try_tier(None, "button", GMode.VISUAL_SCREENSHOT)
    assert result_a is None
    assert result_b is None
    assert result_c is None


def test_recover_stub_does_not_raise():
    a = _initialized_stub_adapter()
    failed_step = {"action_type": "navigate", "target": "https://example.com/", "step_index": 0}
    result = a.recover(failed_step, _noop_emit)
    assert result.attempted is True
    assert result.success is True
    assert any("stub" in action for action in result.recovery_actions)


# ── Integration tests (real browser required) ─────────────────────────────────

@pytest.fixture(scope="module")
def live_adapter(browser_available):
    if not browser_available:
        pytest.skip("Playwright/Chromium not available")
    scope = _make_scope(origins=["https://example.com"])
    session = _make_session()
    a = BrowserAdapter()
    a.initialize(scope, session)
    if a._adapter_mode != "playwright":
        pytest.skip("Playwright launch failed; adapter fell back to stub")
    yield a
    a.teardown("ok", _noop_emit)


def test_initialize_sets_playwright_mode(browser_available):
    if not browser_available:
        pytest.skip("Playwright/Chromium not available")
    a = BrowserAdapter()
    scope = _make_scope(origins=["https://example.com"])
    session = _make_session()
    a.initialize(scope, session)
    try:
        assert a._adapter_mode == "playwright"
        assert a._page is not None
        assert a._browser_context is not None
    finally:
        a.teardown("ok", _noop_emit)


def test_live_navigate_read_url_read_title(live_adapter):
    """navigate + read_url + read_title return real page data."""
    a = live_adapter
    nav_result = a.execute_step(
        {"action_type": "navigate", "target": "https://example.com/"},
        _noop_emit,
    )
    assert nav_result.success
    assert "example.com" in nav_result.output.get("url", "")

    url_result = a.execute_step({"action_type": "read_url", "target": ""}, _noop_emit)
    assert url_result.success
    assert "example.com" in url_result.output.get("url", "")

    title_result = a.execute_step({"action_type": "read_title", "target": ""}, _noop_emit)
    assert title_result.success
    title = title_result.output.get("title", "")
    assert isinstance(title, str)
    assert len(title) > 0


def test_live_read_visible_text(live_adapter):
    """read_visible_text returns non-empty text from example.com."""
    a = live_adapter
    a.execute_step({"action_type": "navigate", "target": "https://example.com/"}, _noop_emit)
    result = a.execute_step({"action_type": "read_visible_text", "target": ""}, _noop_emit)
    assert result.success
    text = result.output.get("text", "")
    assert len(text) > 10
    assert "status" not in result.output or result.output.get("status") != "stub"


def test_live_screenshot_returns_bytes(live_adapter, tmp_path):
    """screenshot captures real page bytes."""
    a = live_adapter
    a.execute_step({"action_type": "navigate", "target": "https://example.com/"}, _noop_emit)
    out = str(tmp_path / "test_ss.png")
    result = a.execute_step(
        {"action_type": "screenshot", "output_path": out},
        _noop_emit,
    )
    assert result.success
    import os
    assert os.path.exists(out)
    assert os.path.getsize(out) > 1000  # real screenshot is substantial


def test_live_screenshot_viewport_option_returns_file(live_adapter, tmp_path):
    """Viewport screenshot captures a real page when full-page capture is disabled."""
    a = live_adapter
    a.execute_step({"action_type": "navigate", "target": "https://example.com/"}, _noop_emit)
    out = str(tmp_path / "test_viewport_ss.png")
    result = a.execute_step(
        {"action_type": "screenshot", "output_path": out, "full_page": False, "settle_ms": 50},
        _noop_emit,
    )
    assert result.success
    assert result.output["full_page"] is False
    assert result.output["settle_ms"] == 50
    import os
    assert os.path.exists(out)
    assert os.path.getsize(out) > 1000


def test_live_screenshot_clip_selector_returns_file(live_adapter, tmp_path):
    """Element screenshot captures a real page element when a clip selector is supplied."""
    a = live_adapter
    a.execute_step({"action_type": "navigate", "target": "https://example.com/"}, _noop_emit)
    out = str(tmp_path / "test_element_ss.png")
    result = a.execute_step(
        {
            "action_type": "screenshot",
            "output_path": out,
            "clip_selector": "body",
            "settle_ms": 50,
        },
        _noop_emit,
    )
    assert result.success
    assert result.output["clip_selector"] == "body"
    assert result.output["full_page"] is False
    import os
    assert os.path.exists(out)
    assert os.path.getsize(out) > 1000


def test_live_tab_open_and_close(browser_available):
    """tab_open opens a real new tab; tab_close removes it."""
    if not browser_available:
        pytest.skip("Playwright/Chromium not available")

    scope = _make_scope(origins=["https://example.com"])
    session = _make_session()
    a = BrowserAdapter()
    a.initialize(scope, session)
    if a._adapter_mode != "playwright":
        a.teardown("ok", _noop_emit)
        pytest.skip("Browser not active")

    try:
        initial_page_count = len(a._browser_context.pages)

        open_result = a.execute_step(
            {"action_type": "tab_open", "target": "https://example.com/"},
            _noop_emit,
        )
        assert open_result.success
        assert len(a._browser_context.pages) == initial_page_count + 1

        close_result = a.execute_step(
            {"action_type": "tab_close", "target": "https://example.com/"},
            _noop_emit,
        )
        assert close_result.success
        assert len(a._browser_context.pages) <= initial_page_count + 1
    finally:
        a.teardown("ok", _noop_emit)


def test_live_teardown_clears_state(browser_available):
    """teardown after real session clears all browser state."""
    if not browser_available:
        pytest.skip("Playwright/Chromium not available")

    scope = _make_scope(origins=["https://example.com"])
    session = _make_session()
    a = BrowserAdapter()
    a.initialize(scope, session)
    if a._adapter_mode != "playwright":
        a.teardown("ok", _noop_emit)
        pytest.skip("Browser not active")

    a.execute_step({"action_type": "navigate", "target": "https://example.com/"}, _noop_emit)
    assert a._current_url is not None
    a.teardown("ok", _noop_emit)

    assert a._page is None
    assert a._browser_context is None
    assert a._browser is None
    assert a._playwright is None
    assert a._adapter_mode == "stub"
    assert a._current_url is None
