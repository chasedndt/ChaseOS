"""Pass 10L — SiteOps Inspector Panel tests.

Tests for:
  - StudioAPI get_siteops_runs / get_siteops_run_detail / get_siteops_approvals
  - index.html: sidebar button, panel structure
  - styles.css: .siteops-* classes
  - app.js: JS functions, panel switch, init wiring
"""

from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

VAULT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(VAULT))

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_api(vault_root=None):
    from runtime.studio.shell.api import StudioAPI
    return StudioAPI(str(vault_root or VAULT))


# ── TestAPISiteOpsRuns ─────────────────────────────────────────────────────────

class TestAPISiteOpsRuns:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_siteops_runs")
        assert callable(api.get_siteops_runs)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_siteops_runs()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_siteops_runs()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_runs()
            assert result["ok"] is True

    def test_data_has_runs_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_runs()
            assert "runs" in result["data"]

    def test_data_has_run_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_runs()
            assert "run_count" in result["data"]

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.studio.siteops_inspector.list_siteops_runs", side_effect=RuntimeError("boom")):
            result = api.get_siteops_runs()
        assert result["ok"] is False
        assert result["error"]["code"] == "siteops_runs_failed"

    def test_surface_is_siteops_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_runs()
        assert result["surface"] == "siteops_runs"


# ── TestAPISiteOpsRunDetail ───────────────────────────────────────────────────

class TestAPISiteOpsRunDetail:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_siteops_run_detail")
        assert callable(api.get_siteops_run_detail)

    def test_empty_run_id_returns_invalid(self):
        api = _make_api()
        result = api.get_siteops_run_detail("")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_run_id"

    def test_none_run_id_returns_invalid(self):
        api = _make_api()
        result = api.get_siteops_run_detail(None)
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_run_id"

    def test_missing_run_returns_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_run_detail("nonexistent_run_id_xyz")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_valid_run_returns_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs_dir = Path(tmp) / "07_LOGS" / "SiteOps-Runs"
            runs_dir.mkdir(parents=True)
            run_id = "siteops_test_run_001"
            run_data = {
                "run_id": run_id,
                "workflow_id": "test.workflow",
                "mode": "dry_run",
                "status": "succeeded",
                "started_at": "2026-05-06T10:00:00",
                "ended_at": "2026-05-06T10:01:00",
            }
            (runs_dir / f"{run_id}.json").write_text(json.dumps(run_data), encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_siteops_run_detail(run_id)
        assert result["ok"] is True

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.studio.siteops_inspector.inspect_siteops_run", side_effect=RuntimeError("boom")):
            result = api.get_siteops_run_detail("some_run_id")
        assert result["ok"] is False
        assert result["error"]["code"] == "siteops_run_detail_failed"

    def test_surface_is_siteops_run_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_run_detail("nonexistent_run")
        assert result["surface"] == "siteops_run_detail"


# ── TestAPISiteOpsApprovals ───────────────────────────────────────────────────

class TestAPISiteOpsApprovals:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_siteops_approvals")
        assert callable(api.get_siteops_approvals)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_siteops_approvals()
        assert isinstance(result, dict)

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_approvals()
            assert result["ok"] is True

    def test_data_has_approvals_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_approvals()
            assert "approvals" in result["data"]

    def test_data_has_approval_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_siteops_approvals()
            assert "approval_count" in result["data"]

    def test_exception_returns_error_envelope(self):
        api = _make_api()
        with patch("runtime.studio.siteops_inspector.list_siteops_approvals", side_effect=RuntimeError("boom")):
            result = api.get_siteops_approvals()
        assert result["ok"] is False
        assert result["error"]["code"] == "siteops_approvals_failed"


# ── TestSiteOpsHTMLStructure ──────────────────────────────────────────────────

HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"

def _html():
    return HTML_PATH.read_text(encoding="utf-8")


class TestSiteOpsHTMLStructure:
    def test_sidebar_button_exists(self):
        assert 'data-panel="siteops"' in _html()

    def test_sidebar_button_label_T(self):
        html = _html()
        assert 'nav-label">Site Skills<' in html

    def test_sidebar_button_title_attr(self):
        assert 'title="Site Skills"' in _html()

    def test_panel_section_exists(self):
        assert 'id="panel-siteops"' in _html()

    def test_panel_data_panel_id(self):
        assert 'data-panel-id="siteops"' in _html()

    def test_read_only_marker(self):
        html = _html()
        # The read-only marker must be inside the siteops panel
        idx = html.find('id="panel-siteops"')
        snippet = html[idx:idx + 500]
        assert "READ-ONLY" in snippet

    def test_panel_body_exists(self):
        assert 'id="siteops-body"' in _html()

    def test_breadcrumb_exists(self):
        assert 'id="siteops-breadcrumb"' in _html()

    def test_back_button_exists(self):
        assert 'id="siteops-back-btn"' in _html()

    def test_tab_row_exists(self):
        assert 'id="siteops-tab-row"' in _html()

    def test_runs_tab_button(self):
        assert 'id="siteops-tab-runs"' in _html()

    def test_approvals_tab_button(self):
        assert 'id="siteops-tab-approvals"' in _html()

    def test_stats_row_exists(self):
        assert 'id="siteops-stats-row"' in _html()

    def test_refresh_button_exists(self):
        assert 'id="siteops-refresh-btn"' in _html()


# ── TestSiteOpsCSSClasses ─────────────────────────────────────────────────────

CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"

def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestSiteOpsCSSClasses:
    def test_siteops_panel(self):
        assert ".siteops-panel" in _css()

    def test_siteops_tab_row(self):
        assert ".siteops-tab-row" in _css()

    def test_siteops_tab_btn(self):
        assert ".siteops-tab-btn" in _css()

    def test_siteops_stats_row(self):
        assert ".siteops-stats-row" in _css()

    def test_siteops_run_card(self):
        assert ".siteops-run-card" in _css()

    def test_siteops_badge(self):
        assert ".siteops-badge" in _css()

    def test_siteops_badge_success(self):
        assert ".siteops-badge-success" in _css()

    def test_siteops_badge_failed(self):
        assert ".siteops-badge-failed" in _css()

    def test_siteops_badge_pending(self):
        assert ".siteops-badge-pending" in _css()

    def test_siteops_approval_card(self):
        assert ".siteops-approval-card" in _css()


# ── TestSiteOpsJS ─────────────────────────────────────────────────────────────

JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"

def _js():
    return JS_PATH.read_text(encoding="utf-8")


class TestSiteOpsJS:
    def test_loadSiteOps_defined(self):
        assert "async function loadSiteOps()" in _js()

    def test_loadSiteOpsRunDetail_defined(self):
        assert "async function loadSiteOpsRunDetail(" in _js()

    def test_renderSiteOpsRuns_defined(self):
        assert "function renderSiteOpsRuns(" in _js()

    def test_renderSiteOpsRunDetail_defined(self):
        assert "function renderSiteOpsRunDetail(" in _js()

    def test_renderSiteOpsApprovals_defined(self):
        assert "function renderSiteOpsApprovals(" in _js()

    def test_initSiteOpsPanel_defined(self):
        assert "function _initSiteOpsPanel()" in _js()

    def test_panel_switch_wired(self):
        assert "if (id === 'siteops') loadSiteOps()" in _js()

    def test_init_called_in_onShellReady(self):
        assert "_initSiteOpsPanel()" in _js()

    def test_api_get_siteops_runs_called(self):
        assert "get_siteops_runs()" in _js()

    def test_api_get_siteops_run_detail_called(self):
        assert "get_siteops_run_detail(" in _js()

    def test_api_get_siteops_approvals_called(self):
        assert "get_siteops_approvals()" in _js()

    def test_tab_state_variable(self):
        assert "siteopsPanelTab" in _js()

    def test_detail_state_variable(self):
        assert "siteopsDetailId" in _js()

    def test_loaded_state_variable(self):
        assert "siteopsLoaded" in _js()
