"""Pass 10R â€” Decision Ledger Panel tests.

Tests for:
  - StudioAPI get_decision_ledger / get_decision_detail
  - index.html: sidebar [D] button, panel structure
  - styles.css: .decision-* / .decision-ledger-* classes
  - app.js: JS functions, panel switch, init wiring
  - panel_registry: decision_ledger_panel_mounted + api_methods
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

VAULT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(VAULT))


def _make_api(vault_root=None):
    from runtime.studio.shell.api import StudioAPI
    return StudioAPI(str(vault_root or VAULT))


# â”€â”€ TestAPIDecisionLedger â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAPIDecisionLedger:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_decision_ledger")
        assert callable(api.get_decision_ledger)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_decision_ledger()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_decision_ledger()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_surface_is_decision_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        assert result["surface"] == "decision_ledger"

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        assert result["ok"] is True

    def test_data_has_decisions_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        assert "decisions" in result["data"]
        assert isinstance(result["data"]["decisions"], list)

    def test_data_has_decision_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        assert "decision_count" in result["data"]

    def test_data_has_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_ledger(limit=5)
        assert result["data"]["limit"] == 5

    def test_empty_vault_returns_zero_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        assert result["data"]["decision_count"] == 0

    def test_index_file_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "Decision-Ledger-Index.md").write_text("# Index", encoding="utf-8")
            (ledger_dir / "2026-03-21_my-decision.md").write_text("# Real", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        filenames = [d["filename"] for d in result["data"]["decisions"]]
        assert "Decision-Ledger-Index.md" not in filenames
        assert "2026-03-21_my-decision.md" in filenames

    def test_decisions_have_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test-decision.md").write_text(
                "---\ntype: decision-record\ndecision_id: test-decision\ndate: 2026-03-21\nstatus: STANDING\nowner: Chase\n---\n# Decision: Test\n\nBody.",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        d = result["data"]["decisions"][0]
        assert "filename" in d
        assert "date" in d
        assert "decision_id" in d
        assert "title" in d
        assert "status" in d
        assert "owner" in d

    def test_frontmatter_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test.md").write_text(
                "---\ndecision_id: my-id\ndate: 2026-03-21\nstatus: STANDING\nowner: Chase\n---\n# Decision: My Choice\n",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        d = result["data"]["decisions"][0]
        assert d["decision_id"] == "my-id"
        assert d["date"] == "2026-03-21"
        assert d["status"] == "STANDING"
        assert d["owner"] == "Chase"

    def test_h1_title_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test.md").write_text(
                "---\ndecision_id: x\n---\n# Decision: My Big Choice\n\nBody.",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        assert result["data"]["decisions"][0]["title"] == "Decision: My Big Choice"

    def test_decisions_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-01-01_old.md").write_text("# Old", encoding="utf-8")
            (ledger_dir / "2026-05-01_new.md").write_text("# New", encoding="utf-8")
            (ledger_dir / "2026-03-15_mid.md").write_text("# Mid", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_decision_ledger()
        filenames = [d["filename"] for d in result["data"]["decisions"]]
        assert filenames[0] == "2026-05-01_new.md"
        assert filenames[-1] == "2026-01-01_old.md"

    def test_exception_returns_error_envelope(self):
        from unittest.mock import patch
        api = _make_api()
        with patch("pathlib.Path.glob", side_effect=RuntimeError("boom")):
            result = api.get_decision_ledger()
        assert result["ok"] is False
        assert result["error"]["code"] == "decision_ledger_failed"


# â”€â”€ TestAPIDecisionDetail â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAPIDecisionDetail:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_decision_detail")
        assert callable(api.get_decision_detail)

    def test_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test.md").write_text("# Test", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_decision_detail("2026-03-21_test.md")
        assert isinstance(result, dict)

    def test_ok_true_for_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test.md").write_text("# Decision\nBody.", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_decision_detail("2026-03-21_test.md")
        assert result["ok"] is True
        assert result["surface"] == "decision_detail"

    def test_data_has_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test.md").write_text("# My Decision\nSome body text.", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_decision_detail("2026-03-21_test.md")
        assert "content" in result["data"]
        assert "My Decision" in result["data"]["content"]

    def test_data_has_size_and_line_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_dir = tmp_path / "07_LOGS" / "Decision-Ledger"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "2026-03-21_test.md").write_text("line1\nline2\n", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_decision_detail("2026-03-21_test.md")
        assert "size_bytes" in result["data"]
        assert "line_count" in result["data"]

    def test_not_found_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_detail("nonexistent.md")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_non_md_extension_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_detail("file.py")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_filename"

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_decision_detail("../../../CLAUDE.md")
        assert result["ok"] is False


# â”€â”€ TestDecisionLedgerHTML â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"


def _html():
    return HTML_PATH.read_text(encoding="utf-8")


class TestDecisionLedgerHTML:
    def test_sidebar_button_exists(self):
        assert 'data-panel="decision-ledger"' in _html()

    def test_sidebar_button_label_D(self):
        assert 'nav-label">Decisions<' in _html()

    def test_sidebar_button_title_attr(self):
        assert 'title="Decisions"' in _html()

    def test_panel_section_exists(self):
        assert 'id="panel-decision-ledger"' in _html()

    def test_panel_data_panel_id(self):
        assert 'data-panel-id="decision-ledger"' in _html()

    def test_read_only_marker(self):
        html = _html()
        idx = html.find('id="panel-decision-ledger"')
        snippet = html[idx:idx + 400]
        assert "READ-ONLY" in snippet

    def test_decision_ledger_list_exists(self):
        assert 'id="decision-ledger-list"' in _html()

    def test_decision_ledger_viewer_exists(self):
        assert 'id="decision-ledger-viewer"' in _html()

    def test_decision_ledger_search_exists(self):
        assert 'id="decision-ledger-search"' in _html()

    def test_decision_ledger_viewer_close_exists(self):
        assert 'id="decision-ledger-viewer-close"' in _html()

    def test_decision_ledger_viewer_content_exists(self):
        assert 'id="decision-ledger-viewer-content"' in _html()


# â”€â”€ TestDecisionLedgerCSSClasses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"


def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestDecisionLedgerCSSClasses:
    def test_decision_ledger_panel(self):
        assert ".decision-ledger-panel" in _css()

    def test_decision_ledger_search_row(self):
        assert ".decision-ledger-search-row" in _css()

    def test_decision_ledger_body(self):
        assert ".decision-ledger-body" in _css()

    def test_decision_ledger_list(self):
        assert ".decision-ledger-list" in _css()

    def test_decision_item(self):
        assert ".decision-item" in _css()

    def test_decision_item_active(self):
        assert ".decision-item--active" in _css()

    def test_decision_date(self):
        assert ".decision-date" in _css()

    def test_decision_title(self):
        assert ".decision-title" in _css()

    def test_decision_status_badge(self):
        assert ".decision-status-badge" in _css()

    def test_decision_ledger_viewer(self):
        assert ".decision-ledger-viewer" in _css()

    def test_decision_ledger_viewer_header(self):
        assert ".decision-ledger-viewer-header" in _css()

    def test_decision_ledger_viewer_content(self):
        assert ".decision-ledger-viewer-content" in _css()

    def test_decision_ledger_viewer_close(self):
        assert ".decision-ledger-viewer-close" in _css()

    def test_decision_ledger_empty(self):
        assert ".decision-ledger-empty" in _css()


# â”€â”€ TestDecisionLedgerJS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"


def _js():
    return JS_PATH.read_text(encoding="utf-8")


class TestDecisionLedgerJS:
    def test_loadDecisionLedger_defined(self):
        assert "async function loadDecisionLedger()" in _js()

    def test_renderDecisionList_defined(self):
        assert "function renderDecisionList(" in _js()

    def test_loadDecisionDetail_defined(self):
        assert "async function loadDecisionDetail(" in _js()

    def test_initDecisionLedgerPanel_defined(self):
        assert "function _initDecisionLedgerPanel()" in _js()

    def test_decisionLedgerLoaded_state_variable(self):
        assert "decisionLedgerLoaded" in _js()

    def test_api_get_decision_ledger_called(self):
        assert "get_decision_ledger(" in _js()

    def test_api_get_decision_detail_called(self):
        assert "get_decision_detail(" in _js()

    def test_panel_switch_wired(self):
        assert "if (id === 'decision-ledger') loadDecisionLedger()" in _js()

    def test_init_called_in_onShellReady(self):
        assert "_initDecisionLedgerPanel()" in _js()

    def test_decision_ledger_body_targeted(self):
        assert "decision-ledger-list" in _js()

    def test_viewer_close_handler_wired(self):
        assert "decision-ledger-viewer-close" in _js()

    def test_search_filter_logic(self):
        assert "decision-ledger-search" in _js()

    def test_filename_attribute_uses_attr_escape(self):
        assert 'data-filename="${escAttr(d.filename)}"' in _js()

    def test_no_vault_writes(self):
        js = _js()
        assert "save_decision" not in js
        assert "write_decision" not in js


# â”€â”€ TestDecisionLedgerRegistry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestDecisionLedgerRegistry:
    def test_registry_mounts_decision_ledger_panel(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["decision-ledger"]
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-decision-ledger"
        assert panel["route_hint"] == "#decision-ledger"
        assert "get_decision_ledger" in panel["api_methods"]
        assert "get_decision_detail" in panel["api_methods"]

    def test_registry_keeps_decision_ledger_read_only(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert panels["decision-ledger"]["read_only"] is True
        assert panels["decision-ledger"]["blocked_authority"]["canonical_mutation"] is False

    def test_registry_readiness_marks_decision_ledger_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["decision_ledger_panel_mounted"] is True

    def test_next_recommended_pass_updated(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"

