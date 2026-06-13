"""Pass 10M — Acquisition Cockpit Panel tests.

Tests for:
  - StudioAPI get_acquisition_summary / get_acquisition_runs / run_acquisition_dry_run
  - index.html: sidebar button, panel structure
  - styles.css: .acquisition-* classes
  - app.js: JS functions, panel switch, init wiring
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

VAULT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(VAULT))


def _make_api(vault_root=None):
    from runtime.studio.shell.api import StudioAPI
    return StudioAPI(str(vault_root or VAULT))


# ── TestAPIAcquisitionSummary ─────────────────────────────────────────────────

class TestAPIAcquisitionSummary:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_acquisition_summary")
        assert callable(api.get_acquisition_summary)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_acquisition_summary()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_acquisition_summary()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_summary()
        assert result["ok"] is True

    def test_data_has_total_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_summary()
        assert "total_artifacts" in result["data"]

    def test_data_has_today_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_summary()
        assert "today_artifacts" in result["data"]

    def test_data_has_by_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_summary()
        assert "by_platform" in result["data"]

    def test_empty_db_returns_zero_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_summary()
        assert result["data"]["total_artifacts"] == 0

    def test_surface_is_acquisition_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_summary()
        assert result["surface"] == "acquisition_summary"

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.acquisition.artifact_store.artifact_stats", side_effect=RuntimeError("boom")):
            result = api.get_acquisition_summary()
        assert result["ok"] is False
        assert result["error"]["code"] == "acquisition_summary_failed"


# ── TestAPIAcquisitionRuns ────────────────────────────────────────────────────

class TestAPIAcquisitionRuns:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_acquisition_runs")
        assert callable(api.get_acquisition_runs)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_acquisition_runs()
        assert isinstance(result, dict)

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_runs()
        assert result["ok"] is True

    def test_data_has_executions_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_runs()
        assert "executions" in result["data"]

    def test_data_has_execution_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_runs()
        assert "execution_count" in result["data"]

    def test_surface_is_acquisition_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_runs()
        assert result["surface"] == "acquisition_runs"

    def test_accepts_limit_param(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_acquisition_runs(limit=5)
        assert result["ok"] is True

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.studio.aor_pipeline_monitor.list_recent_executions", side_effect=RuntimeError("boom")):
            result = api.get_acquisition_runs()
        assert result["ok"] is False
        assert result["error"]["code"] == "acquisition_runs_failed"


class TestAPISourcesProductModel:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_sources_product_model")
        assert callable(api.get_sources_product_model)

    def test_returns_read_only_product_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sources_product_model()
        assert result["ok"] is True
        data = result["data"]
        assert "summary" in data
        assert "source_packs" in data
        assert "normalized_packs" in data
        assert "briefing_inputs" in data
        assert "provenance" in data
        assert "advanced" in data
        assert data["authority"]["provider_calls"] is False
        assert data["authority"]["connector_calls"] is False
        assert data["authority"]["workflow_execution"] is False
        assert data["authority"]["approval_consumption"] is False
        assert data["authority"]["canonical_writeback"] is False


# ── TestAPIAcquisitionDryRun ──────────────────────────────────────────────────

class TestAPIAcquisitionDryRun:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "run_acquisition_dry_run")
        assert callable(api.run_acquisition_dry_run)

    def test_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.run_acquisition_dry_run()
        assert isinstance(result, dict)

    def test_routes_through_approval_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.run_acquisition_dry_run()
        # Must either require approval or be gate_blocked — never direct execution
        assert result["status"] in ("requires_approval", "blocked_or_failed")

    def test_requires_approval_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.run_acquisition_dry_run()
        assert result["status"] == "requires_approval"

    def test_approval_has_approval_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.run_acquisition_dry_run()
        assert result.get("approval", {}).get("approval_id")

    def test_surface_is_acquisition_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.run_acquisition_dry_run()
        assert result["surface"] == "acquisition_dry_run"

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.studio.service.StudioService.validate_action", side_effect=RuntimeError("boom")):
            result = api.run_acquisition_dry_run()
        assert result["ok"] is False
        assert result["error"]["code"] == "acquisition_dry_run_failed"


# ── TestAcquisitionHTMLStructure ──────────────────────────────────────────────

# -- TestAcquisitionPanelRegistry ------------------------------------------------

class TestAcquisitionPanelRegistry:
    def test_registry_mounts_acquisition_panel(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["acquisition"]
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-acquisition"
        # P10 MVP IA routes are hash-path backed pages; keep the registry route hint
        # aligned with the sidebar/app.js route contract instead of the legacy
        # scroll-anchor-style #acquisition hint.
        assert panel["route_hint"] == "#/acquisition"
        assert "get_acquisition_summary" in panel["api_methods"]
        assert "get_acquisition_runs" in panel["api_methods"]
        assert "get_sources_product_model" in panel["api_methods"]
        assert "run_acquisition_dry_run" in panel["api_methods"]

    def test_registry_keeps_acquisition_read_only_and_gated(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["acquisition"]
        blocked = panel["blocked_authority"]
        assert panel["read_only"] is True
        assert blocked["canonical_mutation"] is False
        assert blocked["provider_calls"] is False
        assert blocked["connector_calls"] is False
        assert blocked["workflow_execution"] is False
        assert "source-plan approval request" in panel["blocked_reason"]

    def test_registry_readiness_marks_mainline_panels_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        readiness = registry["readiness"]
        assert readiness["intake_panel_mounted"] is True
        assert readiness["sic_panel_mounted"] is True
        assert readiness["aor_panel_mounted"] is True
        assert readiness["schedules_panel_mounted"] is True
        assert readiness["siteops_panel_mounted"] is True
        assert readiness["acquisition_panel_mounted"] is True


# -- TestAcquisitionHTMLStructure ------------------------------------------------

HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"

def _html():
    return HTML_PATH.read_text(encoding="utf-8")


class TestAcquisitionHTMLStructure:
    def test_sidebar_button_exists(self):
        assert 'data-panel="acquisition"' in _html()

    def test_sidebar_button_label_X(self):
        assert 'nav-label">Sources<' in _html()

    def test_sidebar_button_title_attr(self):
        assert 'aria-label="Sources"' in _html()

    def test_productized_sources_header(self):
        html = _html()
        assert "<h2>Sources</h2>" in html
        assert "Source Packs" in html
        assert "Normalized Packs" in html
        assert "Briefing Inputs" in html
        assert "No external collection" not in html
        assert "Dry-run proposal" not in html

    def test_panel_section_exists(self):
        assert 'id="panel-acquisition"' in _html()

    def test_panel_data_panel_id(self):
        assert 'data-panel-id="acquisition"' in _html()

    def test_read_only_marker(self):
        html = _html()
        idx = html.find('id="panel-acquisition"')
        snippet = html[idx:idx + 600]
        assert "CONTENT SOURCES" in snippet

    def test_stats_row_exists(self):
        assert 'id="acquisition-stats-row"' in _html()

    def test_sources_row_exists(self):
        assert 'id="acquisition-sources-row"' in _html()

    def test_runs_body_exists(self):
        assert 'id="acquisition-runs-body"' in _html()

    def test_actions_row_exists(self):
        assert 'id="acquisition-tab-row"' in _html()

    def test_product_tab_bodies_exist(self):
        html = _html()
        for element_id in (
            "acquisition-source-packs-body",
            "acquisition-normalized-packs-body",
            "acquisition-briefing-inputs-body",
            "acquisition-provenance-body",
            "acquisition-advanced-body",
        ):
            assert f'id="{element_id}"' in html

    def test_dry_run_button_exists(self):
        assert 'id="acquisition-dry-run-btn"' in _html()

    def test_refresh_button_exists(self):
        assert 'id="acquisition-refresh-btn"' in _html()

    def test_action_msg_span_exists(self):
        assert 'id="acquisition-action-msg"' in _html()


# ── TestAcquisitionCSSClasses ─────────────────────────────────────────────────

CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"

def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestAcquisitionCSSClasses:
    def test_acquisition_panel(self):
        assert ".acquisition-panel" in _css()

    def test_acquisition_stats_row(self):
        assert ".acquisition-stats-row" in _css()

    def test_acquisition_stat_pill(self):
        assert ".acquisition-stat-pill" in _css()

    def test_acquisition_source_card(self):
        assert ".acquisition-source-card" in _css()

    def test_acquisition_source_count(self):
        assert ".acquisition-source-count" in _css()

    def test_acquisition_run_card(self):
        assert ".acquisition-run-card" in _css()

    def test_acquisition_badge(self):
        assert ".acquisition-badge" in _css()

    def test_acquisition_badge_success(self):
        assert ".acquisition-badge-success" in _css()

    def test_acquisition_badge_failed(self):
        assert ".acquisition-badge-failed" in _css()

    def test_acquisition_actions_row(self):
        assert ".acquisition-actions-row" in _css()

    def test_acquisition_tab_classes(self):
        css = _css()
        for selector in (
            ".acquisition-tab-row",
            ".acquisition-tab-btn",
            ".acquisition-search-row",
            ".acquisition-tab-panel",
            ".acquisition-product-body",
        ):
            assert selector in css

    def test_acquisition_msg_ok(self):
        assert ".acquisition-msg-ok" in _css()

    def test_acquisition_msg_error(self):
        assert ".acquisition-msg-error" in _css()

    def test_acquisition_css_uses_defined_shell_theme_vars(self):
        css = _css()
        start = css.index(".acquisition-panel")
        end = css.index("/*", start + 1)
        block = css[start:end]
        assert "var(--bg-tertiary)" not in block
        assert "var(--bg-secondary)" not in block
        assert "var(--border-color)" not in block
        assert "var(--accent-color)" not in block
        assert "var(--bg-raised)" in block
        assert "var(--bg-surface)" in block
        assert "var(--border)" in block
        assert "var(--accent)" in block


# ── TestAcquisitionJS ─────────────────────────────────────────────────────────

JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"

def _js():
    return JS_PATH.read_text(encoding="utf-8")


class TestAcquisitionJS:
    def test_loadAcquisition_defined(self):
        assert "async function loadAcquisition()" in _js()

    def test_renderAcquisitionRuns_defined(self):
        assert "function renderAcquisitionRuns(" in _js()

    def test_initAcquisitionPanel_defined(self):
        assert "function _initAcquisitionPanel()" in _js()

    def test_panel_switch_wired(self):
        assert "if (id === 'acquisition') runPanelLoader(loadAcquisition)" in _js()

    def test_init_called_in_onShellReady(self):
        assert "_initAcquisitionPanel()" in _js()

    def test_api_get_acquisition_summary_called(self):
        assert "get_acquisition_summary()" in _js()

    def test_api_get_acquisition_runs_called(self):
        assert "get_acquisition_runs(" in _js()

    def test_api_get_sources_product_model_called(self):
        assert "get_sources_product_model(" in _js()

    def test_api_run_acquisition_dry_run_called(self):
        assert "run_acquisition_dry_run()" in _js()

    def test_loaded_state_variable(self):
        assert "acquisitionLoaded" in _js()

    def test_dry_run_btn_wired(self):
        assert "acquisition-dry-run-btn" in _js()

    def test_refresh_btn_wired(self):
        assert "acquisition-refresh-btn" in _js()

    def test_approval_badge_refresh_called(self):
        assert "refreshApprovalBadge" in _js()

    def test_approval_badge_uses_modal_namespace(self):
        assert "window.ApprovalModal.refreshApprovalBadge()" in _js()

    def test_dynamic_values_are_escaped(self):
        js = _js()
        assert "escHtml(plat || '(unknown)')" in js
        assert "escHtml(label)" in js
        assert "escHtml(ex.filename" in js
        assert "escHtml(productLabel(status, 'Unknown'))" in js

    def test_status_class_is_sanitized(self):
        assert "replace(/[^a-z0-9-]/g, '')" in _js()
