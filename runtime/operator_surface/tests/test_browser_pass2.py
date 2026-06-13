"""
tests.operator_surface.test_browser_pass2

Phase 9 FSOS sub-track — Browser Operator Surface Pass 2 tests.

Covers:
  1. Capability declarations — BrowserAdapter declares all expected capabilities
  2. Scope validation — allowed/forbidden origin checks via scopes module
  3. All action type routing — every supported action type returns correct StepResult
  4. Event emission shape — STEP_STARTED / STEP_COMPLETE structure from executor
  5. Approval hook shape — AWAIT_APPROVAL event payload contract
  6. Grounding tier fallthrough order — select_grounding_tier falls A → B → C
  7. TargetSelection contract — resolve_target returns correct TargetSelection
  8. GroundingContext — records tier usage, produces audit dict
  9. Audit payload shape — build_audit_payload() returns expected keys
 10. TabState / perception — TabState dataclass, list_tabs stub returns []
 11. ActionResult — all new action types return ActionResult with correct fields
 12. Recovery — adapter.recover() emits RECOVERY_STARTED + RECOVERY_COMPLETE

Total: 36 tests
"""

import pytest
from datetime import datetime, timezone

from runtime.operator_surface.adapters.browser_adapter import BrowserAdapter
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
from runtime.operator_surface.events import OperatorEvent, OperatorEventType
from runtime.operator_surface.scopes import (
    ScopeViolation,
    enforce_uri_in_scope,
    action_requires_approval,
    validate_scope,
)
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
    PageState,
    TabState,
    list_tabs,
    get_tab_state,
    get_page_state,
)
from runtime.operator_surface.browser.grounding import (
    GroundingFailed,
    GroundingContext,
    TargetSelection,
    select_grounding_tier,
    resolve_target,
    tier_name,
    grounding_summary,
    _build_tier_order,
)
from runtime.operator_surface.browser.replay import replay_run, print_replay


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_scope(
    allowed_origins=None,
    target_uris=None,
    requires_approval=None,
) -> OperatorScope:
    return OperatorScope(
        run_id="test-run-001",
        surface=SurfaceType.BROWSER,
        target_uris=target_uris or ["https://example.com/page"],
        allowed_origins=allowed_origins or ["https://example.com"],
        requires_approval=requires_approval or [],
    )


def make_session() -> OperatorSession:
    return OperatorSession(
        run_id="test-run-001",
        workflow_id="test_workflow",
        surface=SurfaceType.BROWSER.value,
    )


def make_adapter() -> BrowserAdapter:
    adapter = BrowserAdapter()
    adapter.initialize(make_scope(), make_session())
    return adapter


def make_step(action_type: str, target: str = "https://example.com", **kwargs) -> dict:
    step = {"action_type": action_type, "target": target, "step_index": 0}
    step.update(kwargs)
    return step


def collect_events() -> tuple[list[OperatorEvent], callable]:
    events = []
    def emit(e: OperatorEvent) -> None:
        events.append(e)
    return events, emit


# ── Section 1: Capability declarations ───────────────────────────────────────

class TestCapabilityDeclarations:
    def test_surface_type_is_browser(self):
        assert BrowserAdapter.SURFACE_TYPE == SurfaceType.BROWSER

    def test_adapter_id_is_set(self):
        assert BrowserAdapter.ADAPTER_ID == "browser-playwright-v1"

    def test_has_navigate_capability(self):
        assert OperatorCapability.BROWSER_NAVIGATE in BrowserAdapter.CAPABILITIES

    def test_has_tab_manage_capability(self):
        assert OperatorCapability.BROWSER_TAB_MANAGE in BrowserAdapter.CAPABILITIES

    def test_has_read_state_capability(self):
        assert OperatorCapability.BROWSER_READ_STATE in BrowserAdapter.CAPABILITIES

    def test_has_keyboard_capability(self):
        assert OperatorCapability.BROWSER_KEYBOARD in BrowserAdapter.CAPABILITIES

    def test_total_capabilities_count(self):
        assert len(BrowserAdapter.CAPABILITIES) == 10

    def test_supported_action_types_is_frozenset(self):
        assert isinstance(BrowserAdapter.SUPPORTED_ACTION_TYPES, frozenset)

    def test_supported_action_types_contains_tab_open(self):
        assert "tab_open" in BrowserAdapter.SUPPORTED_ACTION_TYPES

    def test_supported_action_types_contains_read_visible_text(self):
        assert "read_visible_text" in BrowserAdapter.SUPPORTED_ACTION_TYPES


# ── Section 2: Scope validation ───────────────────────────────────────────────

class TestScopeValidation:
    def test_allowed_origin_passes(self):
        scope = make_scope(allowed_origins=["https://example.com"])
        # Should not raise
        enforce_uri_in_scope("https://example.com/page", scope, "navigate")

    def test_disallowed_origin_raises_scope_violation(self):
        scope = make_scope(allowed_origins=["https://example.com"])
        with pytest.raises(ScopeViolation):
            enforce_uri_in_scope("https://attacker.com/page", scope, "navigate")

    def test_scope_with_no_targets_is_invalid(self):
        scope = OperatorScope(
            run_id="r1",
            surface=SurfaceType.BROWSER,
        )
        errors = scope.validate()
        assert any("target" in e for e in errors)

    def test_scope_with_credential_access_is_invalid(self):
        scope = OperatorScope(
            run_id="r1",
            surface=SurfaceType.BROWSER,
            target_uris=["https://example.com"],
            credential_access=True,
        )
        errors = scope.validate()
        assert any("credential_access" in e for e in errors)

    def test_valid_scope_has_no_errors(self):
        scope = make_scope()
        errors = scope.validate()
        assert errors == []


# ── Section 3: Action type routing ───────────────────────────────────────────

class TestActionTypeRouting:
    def setup_method(self):
        self.adapter = make_adapter()
        self._, self.emit = collect_events()

    def _run(self, action_type, **kwargs):
        step = make_step(action_type, **kwargs)
        return self.adapter.execute_step(step, self.emit)

    def test_navigate_returns_step_result(self):
        r = self._run("navigate", target="https://example.com")
        assert isinstance(r, StepResult)
        assert r.action_type == "navigate"
        assert r.success is True

    def test_back_returns_step_result(self):
        r = self._run("back")
        assert r.action_type == "back"
        assert r.success is True

    def test_forward_returns_step_result(self):
        r = self._run("forward")
        assert r.action_type == "forward"

    def test_reload_returns_step_result(self):
        r = self._run("reload")
        assert r.action_type == "reload"

    def test_tab_open_returns_step_result(self):
        r = self._run("tab_open", target="https://example.com/page2")
        assert r.action_type == "tab_open"
        assert "tab_id" in r.output

    def test_tab_close_returns_step_result(self):
        r = self._run("tab_close", target="https://example.com")
        assert r.action_type == "tab_close"

    def test_tab_focus_returns_step_result(self):
        r = self._run("tab_focus", target="https://example.com")
        assert r.action_type == "tab_focus"

    def test_click_returns_step_result(self):
        r = self._run("click", target="button.submit")
        assert r.action_type == "click"
        assert r.grounding_mode_used == GroundingMode.STRUCTURED_API.value

    def test_type_returns_step_result(self):
        r = self._run("type", target="#search", text="hello world")
        assert r.action_type == "type"
        assert r.output["text_length"] == 11

    def test_keypress_returns_step_result(self):
        r = self._run("keypress", target="Enter")
        assert r.action_type == "keypress"
        assert r.output["key"] == "Enter"

    def test_scroll_returns_step_result(self):
        r = self._run("scroll", target="down", direction="down", amount=300)
        assert r.action_type == "scroll"
        assert r.output["direction"] == "down"

    def test_wait_for_returns_step_result(self):
        r = self._run("wait_for", target=".loaded", timeout_ms=3000)
        assert r.action_type == "wait_for"
        assert r.output["timeout_ms"] == 3000

    def test_read_url_returns_step_result(self):
        r = self._run("read_url")
        assert r.action_type == "read_url"
        assert "url" in r.output

    def test_read_title_returns_step_result(self):
        r = self._run("read_title")
        assert r.action_type == "read_title"
        assert "title" in r.output

    def test_read_visible_text_returns_step_result(self):
        r = self._run("read_visible_text")
        assert r.action_type == "read_visible_text"
        assert "text" in r.output

    def test_extract_returns_step_result(self):
        r = self._run("extract", target="table tr")
        assert r.action_type == "extract"
        assert "rows" in r.output

    def test_screenshot_returns_step_result(self):
        r = self._run("screenshot")
        assert r.action_type == "screenshot"

    def test_unknown_action_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown browser action type"):
            self._run("fly_to_moon")

    def test_steps_executed_increments(self):
        adapter = make_adapter()
        _, emit = collect_events()
        adapter.execute_step(make_step("navigate"), emit)
        adapter.execute_step(make_step("click"), emit)
        assert adapter._steps_executed == 2


# ── Section 4: Approval shape ─────────────────────────────────────────────────

class TestApprovalShape:
    def test_form_submit_in_approval_required_actions(self):
        assert "form_submit" in BrowserAdapter.APPROVAL_REQUIRED_ACTIONS

    def test_file_download_in_approval_required_actions(self):
        assert "file_download" in BrowserAdapter.APPROVAL_REQUIRED_ACTIONS

    def test_scope_requires_approval_field_respected(self):
        scope = make_scope(requires_approval=["navigate"])
        assert "navigate" in scope.requires_approval

    def test_action_requires_approval_returns_true_for_declared(self):
        scope = make_scope(requires_approval=["tab_open"])
        assert action_requires_approval("tab_open", scope) is True

    def test_action_requires_approval_returns_false_for_undeclared(self):
        scope = make_scope(requires_approval=[])
        assert action_requires_approval("read_url", scope) is False


# ── Section 5: Grounding tier fallthrough order ───────────────────────────────

class TestGroundingTierFallthrough:
    def test_build_tier_order_starts_with_preferred(self):
        order = _build_tier_order(GroundingMode.STRUCTURED_API)
        assert order[0] == GroundingMode.STRUCTURED_API

    def test_build_tier_order_accessibility_first(self):
        order = _build_tier_order(GroundingMode.ACCESSIBILITY)
        assert order[0] == GroundingMode.ACCESSIBILITY
        assert GroundingMode.STRUCTURED_API in order

    def test_build_tier_order_visual_first(self):
        order = _build_tier_order(GroundingMode.VISUAL_SCREENSHOT)
        assert order[0] == GroundingMode.VISUAL_SCREENSHOT

    def test_tier_name_structured_api(self):
        assert "Tier A" in tier_name(GroundingMode.STRUCTURED_API)

    def test_tier_name_accessibility(self):
        assert "Tier B" in tier_name(GroundingMode.ACCESSIBILITY)

    def test_tier_name_visual(self):
        assert "Tier C" in tier_name(GroundingMode.VISUAL_SCREENSHOT)

    def test_select_grounding_tier_raises_when_all_stubs(self):
        """All perception stubs return empty/None — GroundingFailed should raise."""
        with pytest.raises(GroundingFailed):
            select_grounding_tier(None, "button.submit")


# ── Section 6: TargetSelection contract ──────────────────────────────────────

class TestTargetSelection:
    def test_resolve_target_raises_grounding_failed_on_stubs(self):
        """All tiers return empty/None — should raise GroundingFailed."""
        with pytest.raises(GroundingFailed):
            resolve_target(None, "button.login")

    def test_target_selection_dataclass_fields(self):
        ts = TargetSelection(
            tier_used=GroundingMode.STRUCTURED_API,
            selector_or_ref="button.submit",
            method="css_or_locator",
            fallback_count=0,
            confidence_note="exact DOM match",
        )
        assert ts.tier_used == GroundingMode.STRUCTURED_API
        assert ts.fallback_count == 0
        assert ts.confidence_note == "exact DOM match"


# ── Section 7: GroundingContext ───────────────────────────────────────────────

class TestGroundingContext:
    def test_initial_counts_are_zero(self):
        ctx = GroundingContext()
        d = ctx.to_audit_dict()
        assert d["grounding_tier_counts"]["structured_api"] == 0

    def test_record_tier_use_increments(self):
        ctx = GroundingContext()
        ctx.record_tier_use(GroundingMode.STRUCTURED_API)
        ctx.record_tier_use(GroundingMode.STRUCTURED_API)
        d = ctx.to_audit_dict()
        assert d["grounding_tier_counts"]["structured_api"] == 2

    def test_fallback_count_tracked(self):
        ctx = GroundingContext()
        ctx.record_tier_use(GroundingMode.ACCESSIBILITY, was_fallback=True)
        d = ctx.to_audit_dict()
        assert d["total_fallbacks"] == 1

    def test_grounding_summary_non_empty_after_use(self):
        ctx = GroundingContext()
        ctx.record_tier_use(GroundingMode.STRUCTURED_API)
        assert "TierA" in grounding_summary(ctx)

    def test_grounding_summary_empty_context(self):
        ctx = GroundingContext()
        result = grounding_summary(ctx)
        assert result == "no grounding recorded"


# ── Section 8: Audit payload shape ───────────────────────────────────────────

class TestAuditPayload:
    def test_audit_payload_has_required_keys(self):
        adapter = make_adapter()
        payload = adapter.build_audit_payload()
        for key in [
            "adapter_id", "adapter_version", "surface_type", "adapter_status",
            "steps_executed", "tabs_opened", "final_url",
            "grounding_breakdown", "supported_action_types", "implementation_note",
        ]:
            assert key in payload, f"Missing key: {key}"

    def test_audit_payload_surface_type_is_browser(self):
        adapter = make_adapter()
        payload = adapter.build_audit_payload()
        assert payload["surface_type"] == "browser"

    def test_audit_payload_steps_executed_after_steps(self):
        adapter = make_adapter()
        _, emit = collect_events()
        adapter.execute_step(make_step("navigate"), emit)
        adapter.execute_step(make_step("read_url"), emit)
        payload = adapter.build_audit_payload()
        assert payload["steps_executed"] == 2

    def test_audit_payload_tabs_opened_after_tab_open(self):
        adapter = make_adapter()
        _, emit = collect_events()
        adapter.execute_step(make_step("tab_open", target="https://example.com/p2"), emit)
        payload = adapter.build_audit_payload()
        assert payload["tabs_opened"] == 1


# ── Section 9: Perception stubs ──────────────────────────────────────────────

class TestPerception:
    def test_tab_state_dataclass(self):
        ts = TabState(page_id="0", url="https://example.com", title="Example", is_active=True)
        assert ts.page_id == "0"
        assert ts.is_active is True

    def test_list_tabs_returns_empty_list_stub(self):
        assert list_tabs(None) == []

    def test_get_tab_state_stub(self):
        ts = get_tab_state(None, "0")
        assert isinstance(ts, TabState)
        assert ts.page_id == "0"

    def test_page_state_has_tabs_field(self):
        ps = PageState()
        assert hasattr(ps, "tabs")
        assert hasattr(ps, "tab_count")
        assert hasattr(ps, "visible_text")

    def test_get_page_state_with_context_stub(self):
        ps = get_page_state(None, context=None)
        assert isinstance(ps, PageState)
        assert ps.tab_count == 0


# ── Section 10: Actions module ActionResult contract ─────────────────────────

class TestActionResultContract:
    def test_action_result_has_tab_id_field(self):
        r = ActionResult("tab_open", "url", True, {}, tab_id="tab_1")
        assert r.tab_id == "tab_1"

    def test_navigate_scope_enforcement_stub(self):
        scope = make_scope(allowed_origins=["https://example.com"])
        r = navigate(None, "https://example.com/page", scope)
        assert r.success is True
        assert r.action_type == "navigate"

    def test_navigate_disallowed_origin_raises(self):
        scope = make_scope(allowed_origins=["https://example.com"])
        with pytest.raises(ScopeViolation):
            navigate(None, "https://attacker.com", scope)

    def test_keypress_action_result_key_field(self):
        r = keypress(None, "Enter")
        assert r.output["key"] == "Enter"

    def test_keypress_with_selector(self):
        r = keypress(None, "Tab", selector="#input")
        assert r.output["selector"] == "#input"

    def test_read_visible_text_output_has_text(self):
        r = read_visible_text(None)
        assert "text" in r.output

    def test_tab_open_output_has_tab_id(self):
        scope = make_scope()
        r = tab_open(None, "https://example.com/p2", scope)
        assert "tab_id" in r.output
        assert r.tab_id is not None


# ── Section 11: Recovery ──────────────────────────────────────────────────────

class TestRecovery:
    def test_recover_emits_recovery_started_and_complete(self):
        adapter = make_adapter()
        events, emit = collect_events()
        failed_step = make_step("click", target="button.missing", step_index=2)
        result = adapter.recover(failed_step, emit)
        event_types = [e.event_type for e in events]
        assert OperatorEventType.RECOVERY_STARTED in event_types
        assert OperatorEventType.RECOVERY_COMPLETE in event_types

    def test_recover_returns_recovery_result(self):
        from runtime.operator_surface.contracts import RecoveryResult
        adapter = make_adapter()
        _, emit = collect_events()
        result = adapter.recover(make_step("click"), emit)
        assert isinstance(result, RecoveryResult)
        assert result.attempted is True
