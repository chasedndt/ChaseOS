"""Pass 10N — Agent Bus Diagnostics Panel tests.

Tests for:
  - StudioAPI get_bus_diagnostics / get_bus_tasks / get_bus_events
  - index.html: sidebar button, panel structure
  - styles.css: .bus-* classes
  - app.js: JS functions, panel switch, init wiring
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

VAULT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(VAULT))


def _make_api(vault_root=None):
    from runtime.studio.shell.api import StudioAPI
    return StudioAPI(str(vault_root or VAULT))


# ── TestAPIBusDiagnostics ─────────────────────────────────────────────────────

class TestAPIBusDiagnostics:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_bus_diagnostics")
        assert callable(api.get_bus_diagnostics)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_bus_diagnostics()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_bus_diagnostics()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert result["ok"] is True

    def test_data_has_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert "mode" in result["data"]

    def test_data_has_heartbeats(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert "heartbeats" in result["data"]
        assert isinstance(result["data"]["heartbeats"], list)

    def test_data_has_heartbeat_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert "heartbeat_count" in result["data"]

    def test_data_has_total_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert "total_tasks" in result["data"]

    def test_data_has_tasks_by_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert "tasks_by_status" in result["data"]
        assert isinstance(result["data"]["tasks_by_status"], dict)

    def test_data_has_product_operating_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        context = result["data"]["operating_context"]
        assert context["title"] == "Bus Operating Context"
        assert "safe_action" in context
        assert context["cards"]

    def test_data_has_readiness_and_feature_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert "readiness" in result["data"]
        assert result["data"]["readiness"]["rows"]
        coverage = result["data"]["feature_family_coverage"]
        assert any(item["capability"] == "Agent Bus coordination queue" for item in coverage)

    def test_authority_blocks_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        authority = result["data"]["authority"]
        assert authority["read_only"] is True
        assert authority["writes_agent_bus_tasks"] is False
        assert authority["claims_tasks"] is False
        assert authority["dispatches_tasks"] is False
        assert authority["approval_consumption_allowed"] is False
        assert authority["canonical_mutation_allowed"] is False

    def test_empty_bus_returns_zero_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert result["data"]["total_tasks"] == 0

    def test_mode_is_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert isinstance(result["data"]["mode"], str)

    def test_surface_is_bus_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_diagnostics()
        assert result["surface"] == "bus_diagnostics"

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.agent_bus.bus.get_bus_mode", side_effect=RuntimeError("boom")):
            result = api.get_bus_diagnostics()
        assert result["ok"] is False
        assert result["error"]["code"] == "bus_diagnostics_failed"


# ── TestAPIBusTasks ───────────────────────────────────────────────────────────

class TestAPIBusTasks:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_bus_tasks")
        assert callable(api.get_bus_tasks)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_bus_tasks()
        assert isinstance(result, dict)

    def test_ok_true_with_empty_bus(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_tasks()
        assert result["ok"] is True

    def test_data_has_tasks_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_tasks()
        assert "tasks" in result["data"]

    def test_data_has_task_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_tasks()
        assert "task_count" in result["data"]

    def test_data_has_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_tasks(status="open", runtime="Hermes", limit=5)
        assert result["data"]["status_filter"] == "open"
        assert result["data"]["runtime_filter"] == "Hermes"
        assert result["data"]["limit"] == 5

    def test_empty_status_treated_as_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_tasks(status="")
        assert result["data"]["status_filter"] is None

    def test_surface_is_bus_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_tasks()
        assert result["surface"] == "bus_tasks"

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.agent_bus.bus.list_tasks", side_effect=RuntimeError("boom")):
            result = api.get_bus_tasks()
        assert result["ok"] is False
        assert result["error"]["code"] == "bus_tasks_failed"


# ── TestAPIBusEvents ──────────────────────────────────────────────────────────

class TestAPIBusEvents:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_bus_events")
        assert callable(api.get_bus_events)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_bus_events()
        assert isinstance(result, dict)

    def test_ok_true_with_empty_bus(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_events()
        assert result["ok"] is True

    def test_data_has_events_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_events()
        assert "events" in result["data"]
        assert isinstance(result["data"]["events"], list)

    def test_data_has_event_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_events()
        assert "event_count" in result["data"]

    def test_accepts_limit_param(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_events(limit=10)
        assert result["ok"] is True
        assert result["data"]["limit"] == 10

    def test_surface_is_bus_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_bus_events()
        assert result["surface"] == "bus_events"

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.agent_bus.bus.list_tasks", side_effect=RuntimeError("boom")):
            result = api.get_bus_events()
        assert result["ok"] is False
        assert result["error"]["code"] == "bus_events_failed"


# ── TestBusHTMLStructure ──────────────────────────────────────────────────────

# -- TestBusPanelRegistry --------------------------------------------------------

class TestBusPanelRegistry:
    def test_registry_mounts_bus_panel(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["bus"]
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-bus"
        assert panel["route_hint"] == "#bus"
        assert "get_bus_diagnostics" in panel["api_methods"]
        assert "get_bus_tasks" in panel["api_methods"]
        assert "get_bus_events" in panel["api_methods"]

    def test_registry_keeps_bus_read_only(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        blocked = panels["bus"]["blocked_authority"]
        assert panels["bus"]["read_only"] is True
        assert blocked["workflow_execution"] is False
        assert blocked["approval_execution"] is False
        assert blocked["canonical_mutation"] is False

    def test_registry_readiness_marks_bus_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["bus_diagnostics_panel_mounted"] is True


HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"

def _html():
    return HTML_PATH.read_text(encoding="utf-8")


class TestBusHTMLStructure:
    def test_sidebar_button_exists(self):
        assert 'data-panel="bus"' in _html()

    def test_sidebar_button_label_U(self):
        assert 'nav-label">Agent Bus<' in _html()

    def test_sidebar_button_title_attr(self):
        assert 'title="Agent Bus"' in _html()

    def test_panel_section_exists(self):
        assert 'id="panel-bus"' in _html()

    def test_panel_subtitle_productized(self):
        html = _html()
        idx = html.find('id="panel-bus"')
        snippet = html[idx:idx + 900]
        assert "Coordinate local runtime work" in snippet

    def test_product_context_slots_exist(self):
        html = _html()
        idx = html.find('id="panel-bus"')
        snippet = html[idx:idx + 1400]
        assert 'id="bus-operating-context"' in snippet
        assert 'id="bus-readiness"' in snippet
        assert 'id="bus-feature-coverage"' in snippet

    def test_runtime_authority_row_present(self):
        html = _html()
        idx = html.find('id="panel-bus"')
        snippet = html[idx:idx + 900]
        assert 'class="runtime-authority-row"' in snippet

    def test_panel_data_panel_id(self):
        assert 'data-panel-id="bus"' in _html()

    def test_read_only_marker(self):
        html = _html()
        idx = html.find('id="panel-bus"')
        snippet = html[idx:idx + 600]
        assert "READ-ONLY" in snippet

    def test_mode_banner_exists(self):
        assert 'id="bus-mode-banner"' in _html()

    def test_tab_row_exists(self):
        assert 'id="bus-tab-row"' in _html()

    def test_tasks_tab_exists(self):
        assert 'id="bus-tab-tasks"' in _html()

    def test_heartbeats_tab_exists(self):
        assert 'id="bus-tab-heartbeats"' in _html()

    def test_events_tab_exists(self):
        assert 'id="bus-tab-events"' in _html()

    def test_stats_row_exists(self):
        assert 'id="bus-stats-row"' in _html()

    def test_filter_row_exists(self):
        assert 'id="bus-filter-row"' in _html()

    def test_status_filter_exists(self):
        assert 'id="bus-status-filter"' in _html()

    def test_runtime_filter_exists(self):
        assert 'id="bus-runtime-filter"' in _html()

    def test_refresh_button_exists(self):
        assert 'id="bus-refresh-btn"' in _html()

    def test_body_exists(self):
        assert 'id="bus-body"' in _html()


# ── TestBusCSSClasses ─────────────────────────────────────────────────────────

CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"

def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestBusCSSClasses:
    def test_bus_panel(self):
        assert ".bus-panel" in _css()

    def test_bus_context_panel(self):
        assert ".bus-context-panel" in _css()

    def test_bus_feature_coverage(self):
        assert ".bus-feature-coverage" in _css()

    def test_bus_stat_card(self):
        assert ".bus-stat-card" in _css()

    def test_bus_mode_banner(self):
        assert ".bus-mode-banner" in _css()

    def test_bus_tab_row(self):
        assert ".bus-tab-row" in _css()

    def test_bus_tab_btn(self):
        assert ".bus-tab-btn" in _css()

    def test_bus_stats_row(self):
        assert ".bus-stats-row" in _css()

    def test_bus_filter_row(self):
        assert ".bus-filter-row" in _css()

    def test_bus_task_card(self):
        assert ".bus-task-card" in _css()

    def test_runtime_authority_row(self):
        assert ".runtime-authority-row" in _css()

    def test_bus_badge(self):
        assert ".bus-badge" in _css()

    def test_bus_badge_open(self):
        assert ".bus-badge-open" in _css()

    def test_bus_badge_done(self):
        assert ".bus-badge-done" in _css()

    def test_bus_badge_blocked(self):
        assert ".bus-badge-blocked" in _css()

    def test_bus_heartbeat_grid(self):
        assert ".bus-heartbeat-grid" in _css()

    def test_bus_heartbeat_card(self):
        assert ".bus-heartbeat-card" in _css()

    def test_bus_event_log(self):
        assert ".bus-event-log" in _css()

    def test_bus_event_row(self):
        assert ".bus-event-row" in _css()

    def test_bus_css_uses_defined_shell_theme_vars(self):
        css = _css()
        start = css.index(".bus-panel")
        later_sections = [
            idx for idx in (
                css.find(".sprint-focus-section", start + 1),
                css.find(".build-logs-panel", start + 1),
            )
            if idx != -1
        ]
        end = min(later_sections) if later_sections else len(css)
        block = css[start:end]
        assert "var(--bg-tertiary)" not in block
        assert "var(--bg-secondary)" not in block
        assert "var(--border-color)" not in block
        assert "var(--accent-color)" not in block
        assert "var(--bg-raised)" in block
        assert "var(--bg-surface)" in block
        assert "var(--border)" in block
        assert "var(--accent)" in block


# ── TestBusJS ─────────────────────────────────────────────────────────────────

JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"

def _js():
    return JS_PATH.read_text(encoding="utf-8")


class TestBusJS:
    def test_loadBus_defined(self):
        assert "async function loadBus()" in _js()

    def test_renderBusTasks_defined(self):
        assert "function renderBusTasks(" in _js()

    def test_runtime_object_inspector_for_bus_tasks(self):
        assert "function renderObjectInspectorBusTaskContext(" in _js()

    def test_renderBusHeartbeats_defined(self):
        assert "function renderBusHeartbeats(" in _js()

    def test_renderBusEvents_defined(self):
        assert "function renderBusEvents(" in _js()

    def test_renderBusOperatingContext_defined(self):
        assert "function renderBusOperatingContext(" in _js()

    def test_renderBusReadiness_defined(self):
        assert "function renderBusReadiness(" in _js()

    def test_renderBusFeatureCoverage_defined(self):
        assert "function renderBusFeatureCoverage(" in _js()

    def test_bus_task_card_data_attr(self):
        assert 'data-agent-bus-task-card="task"' in _js()

    def test_initBusPanel_defined(self):
        assert "function _initBusPanel()" in _js()

    def test_panel_switch_wired(self):
        assert "if (id === 'bus') loadBus()" in _js()

    def test_init_called_in_onShellReady(self):
        assert "_initBusPanel()" in _js()

    def test_api_get_bus_diagnostics_called(self):
        assert "get_bus_diagnostics()" in _js()

    def test_api_get_bus_tasks_called(self):
        assert "get_bus_tasks(" in _js()

    def test_api_get_bus_events_called(self):
        assert "get_bus_events(" in _js()

    def test_panel_tab_state_variable(self):
        assert "busPanelTab" in _js()

    def test_bus_loaded_state_variable(self):
        assert "busLoaded" in _js()

    def test_tab_heartbeats_branch(self):
        assert "busPanelTab === 'heartbeats'" in _js()

    def test_tab_events_branch(self):
        assert "busPanelTab === 'events'" in _js()

    def test_dynamic_values_are_escaped(self):
        js = _js()
        assert "escHtml((diagRes && diagRes.error" in js
        assert "escHtml(d.mode || 'local')" in js
        assert "escHtml(t.task_id" in js
        assert "escHtml(h.runtime" in js
        assert "escHtml(e.message" in js

    def test_status_class_is_sanitized(self):
        assert "replace(/[^a-z0-9-]/g, '')" in _js()
