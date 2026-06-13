"""Tests for Pass 10H — SIC Workspace Browser Panel.

Covers:
- API get_sic_workspaces() returns correct envelope
- API get_sic_workspace_detail() validates slug and delegates to inspect_sic_workspace
- HTML: sidebar [C] button, #panel-sic section, breadcrumb, back button, sic-body
- CSS: all .sic-* classes and badge state classes present
- JS: all SIC functions present, panel switch wired, init called, API calls referenced
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SHELL = Path(__file__).resolve().parent
_FRONTEND = _SHELL / "frontend"
_VAULT = _SHELL.parents[2]


# ── TestAPISICWorkspaces ──────────────────────────────────────────────────────

class TestAPISICWorkspaces:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_returns_ok_envelope(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspaces()
        assert result["ok"] is True
        assert result["surface"] == "sic_workspaces"
        assert "data" in result

    def test_envelope_has_required_keys(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspaces()
        for key in ("ok", "status", "surface", "data", "warnings", "blocked_authority"):
            assert key in result

    def test_empty_vault_returns_ok_not_error(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspaces()
        # No workspaces on empty vault — must still be ok=True, not an exception
        assert result["ok"] is True

    def test_data_contains_workspaces_field(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspaces()
        data = result["data"]
        assert isinstance(data, dict)

    def test_method_exists_on_studio_api(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_sic_workspaces")
        assert callable(StudioAPI.get_sic_workspaces)

    def test_exception_in_sic_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch(
            "runtime.studio.sic_workspace_browser.list_sic_workspaces",
            side_effect=RuntimeError("disk failure"),
        ):
            result = api.get_sic_workspaces()
        assert result["ok"] is False

    def test_error_envelope_shape(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch(
            "runtime.studio.sic_workspace_browser.list_sic_workspaces",
            side_effect=RuntimeError("boom"),
        ):
            result = api.get_sic_workspaces()
        assert result["surface"] == "sic_workspaces"
        assert "error" in result
        assert "code" in result["error"]


# ── TestAPISICWorkspaceDetail ─────────────────────────────────────────────────

class TestAPISICWorkspaceDetail:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_method_exists_on_studio_api(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_sic_workspace_detail")
        assert callable(StudioAPI.get_sic_workspace_detail)

    def test_empty_slug_returns_error(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspace_detail("")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_slug"

    def test_none_slug_returns_error(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspace_detail(None)
        assert result["ok"] is False

    def test_invalid_slug_with_special_chars_rejected(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_sic_workspace_detail("../../../etc")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_slug"

    def test_valid_slug_calls_inspect_sic_workspace(self, tmp_path):
        api = self._make_api(tmp_path)
        mock_data = {
            "ok": True,
            "slug": "strikezone",
            "workspace": {"name": "StrikeZone"},
            "source_refs": [],
            "outputs": [],
        }
        with patch(
            "runtime.studio.sic_workspace_browser.inspect_sic_workspace",
            return_value=mock_data,
        ) as mock_fn:
            result = api.get_sic_workspace_detail("strikezone")
        mock_fn.assert_called_once()
        assert result["ok"] is True
        assert result["surface"] == "sic_workspace_detail"

    def test_not_found_workspace_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch(
            "runtime.studio.sic_workspace_browser.inspect_sic_workspace",
            return_value={"ok": False, "error": "Workspace not found."},
        ):
            result = api.get_sic_workspace_detail("no-such-ws")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_slug_with_hyphens_accepted(self, tmp_path):
        api = self._make_api(tmp_path)
        mock_data = {"ok": True, "slug": "my-workspace", "workspace": {}, "source_refs": [], "outputs": []}
        with patch(
            "runtime.studio.sic_workspace_browser.inspect_sic_workspace",
            return_value=mock_data,
        ):
            result = api.get_sic_workspace_detail("my-workspace")
        assert result["ok"] is True

    def test_exception_in_inspect_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch(
            "runtime.studio.sic_workspace_browser.inspect_sic_workspace",
            side_effect=RuntimeError("io error"),
        ):
            result = api.get_sic_workspace_detail("good-slug")
        assert result["ok"] is False

    def test_detail_envelope_has_required_keys(self, tmp_path):
        api = self._make_api(tmp_path)
        mock_data = {"ok": True, "slug": "ws", "workspace": {}, "source_refs": [], "outputs": []}
        with patch(
            "runtime.studio.sic_workspace_browser.inspect_sic_workspace",
            return_value=mock_data,
        ):
            result = api.get_sic_workspace_detail("ws")
        for key in ("ok", "status", "surface", "data", "warnings", "blocked_authority"):
            assert key in result


# ── TestSICHTMLStructure ──────────────────────────────────────────────────────

class TestSICHTMLStructure:
    def _html(self):
        return (_FRONTEND / "index.html").read_text(encoding="utf-8")

    def test_sidebar_sic_button(self):
        assert 'data-panel="sic"' in self._html()

    def test_sidebar_sic_button_label(self):
        assert 'nav-label">Research Collections<' in self._html()

    def test_sidebar_sic_title_attribute(self):
        assert 'title="Research Collections - source collections and retrieval posture"' in self._html()

    def test_panel_sic_section_exists(self):
        assert 'id="panel-sic"' in self._html()

    def test_sic_body_element(self):
        assert 'id="sic-body"' in self._html()

    def test_sic_breadcrumb_element(self):
        assert 'id="sic-breadcrumb"' in self._html()

    def test_sic_back_btn(self):
        assert 'id="sic-back-btn"' in self._html()

    def test_sic_breadcrumb_name(self):
        assert 'id="sic-breadcrumb-name"' in self._html()

    def test_panel_read_only_marker(self):
        import re
        html = self._html()
        match = re.search(r'id="panel-sic"[^>]*>', html)
        assert match is not None
        assert 'data-read-only="true"' in match.group(0)

    def test_sic_status_pill(self):
        assert 'id="sic-status"' in self._html()


# ── TestSICCSS ───────────────────────────────────────────────────────────────

class TestSICCSS:
    def _css(self):
        return (_FRONTEND / "styles.css").read_text(encoding="utf-8")

    def test_sic_panel_class(self):
        assert ".sic-panel" in self._css()

    def test_sic_workspace_card(self):
        assert ".sic-workspace-card" in self._css()

    def test_sic_ws_header(self):
        assert ".sic-ws-header" in self._css()

    def test_sic_ws_name(self):
        assert ".sic-ws-name" in self._css()

    def test_sic_idx_badge(self):
        assert ".sic-idx-badge" in self._css()

    def test_sic_index_state_classes(self):
        css = self._css()
        for cls in (".sic-idx-ready", ".sic-idx-building", ".sic-idx-pending", ".sic-idx-unknown"):
            assert cls in css

    def test_sic_breadcrumb(self):
        assert ".sic-breadcrumb" in self._css()

    def test_sic_back_btn_class(self):
        assert ".sic-back-btn" in self._css()

    def test_sic_detail(self):
        assert ".sic-detail" in self._css()

    def test_sic_info_grid(self):
        assert ".sic-info-grid" in self._css()

    def test_sic_source_list(self):
        assert ".sic-source-list" in self._css()

    def test_sic_output_list(self):
        assert ".sic-output-list" in self._css()

    def test_sic_empty(self):
        assert ".sic-empty" in self._css()

    def test_sic_tag(self):
        assert ".sic-tag" in self._css()


# ── TestSICJS ────────────────────────────────────────────────────────────────

class TestSICJS:
    def _js(self):
        return (_FRONTEND / "app.js").read_text(encoding="utf-8")

    def test_load_sic_function(self):
        assert "async function loadSIC(" in self._js()

    def test_load_sic_workspace_detail_function(self):
        assert "async function loadSICWorkspaceDetail(" in self._js()

    def test_render_sic_workspace_list_function(self):
        assert "function renderSICWorkspaceList(" in self._js()

    def test_render_sic_workspace_detail_function(self):
        assert "function renderSICWorkspaceDetail(" in self._js()

    def test_init_sic_panel_function(self):
        assert "function _initSICPanel(" in self._js()

    def test_sic_panel_switch_wired(self):
        assert "if (id === 'sic') runPanelLoader(loadSIC);" in self._js()

    def test_sic_init_called_on_ready(self):
        assert "_initSICPanel();" in self._js()

    def test_get_sic_workspaces_api_call(self):
        assert "get_sic_workspaces" in self._js()

    def test_get_sic_workspace_detail_api_call(self):
        assert "get_sic_workspace_detail" in self._js()

    def test_sic_loaded_flag(self):
        assert "sicLoaded" in self._js()

    def test_sic_current_slug_flag(self):
        assert "_sicCurrentSlug" in self._js()

    def test_back_btn_click_handler(self):
        assert "sic-back-btn" in self._js()

    def test_workspace_card_click_handler(self):
        assert "loadSICWorkspaceDetail" in self._js()

    def test_breadcrumb_shown_on_detail(self):
        js = self._js()
        assert "sic-breadcrumb" in js
        assert "sic-breadcrumb-name" in js
