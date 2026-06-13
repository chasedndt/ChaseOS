"""Pass 10S - Pivot Log Panel tests.

Tests for:
  - StudioAPI get_pivot_log / get_pivot_detail
  - index.html: sidebar [V] button, panel structure
  - styles.css: .pivot-* / .pivot-log-* classes
  - app.js: JS functions, panel switch, init wiring
  - panel_registry: pivot_log_panel_mounted + api_methods
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(VAULT))


def _make_api(vault_root=None):
    from runtime.studio.shell.api import StudioAPI

    return StudioAPI(str(vault_root or VAULT))


class TestAPIPivotLog:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_pivot_log")
        assert callable(api.get_pivot_log)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_pivot_log()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_pivot_log()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_surface_is_pivot_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log()
        assert result["surface"] == "pivot_log"

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log()
        assert result["ok"] is True

    def test_data_has_pivots_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log()
        assert "pivots" in result["data"]
        assert isinstance(result["data"]["pivots"], list)

    def test_data_has_pivot_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log()
        assert "pivot_count" in result["data"]

    def test_data_has_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log(limit=5)
        assert result["data"]["limit"] == 5

    def test_empty_vault_returns_zero_pivots(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log()
        assert result["data"]["pivot_count"] == 0

    def test_index_file_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "Pivot-Log-Index.md").write_text("# Index", encoding="utf-8")
            (pivot_dir / "2026-03-21_scope-reset.md").write_text("# Pivot: Real", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_log()
        filenames = [p["filename"] for p in result["data"]["pivots"]]
        assert "Pivot-Log-Index.md" not in filenames
        assert "2026-03-21_scope-reset.md" in filenames

    def test_pivots_have_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test-pivot.md").write_text(
                "---\n"
                "type: pivot-record\n"
                "system: ChaseOS\n"
                "pivot_id: test-pivot\n"
                "date: 2026-03-21\n"
                "approved_by: Chase\n"
                "---\n"
                "# Pivot: Test\n\nBody.",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_pivot_log()
        p = result["data"]["pivots"][0]
        assert "filename" in p
        assert "date" in p
        assert "pivot_id" in p
        assert "title" in p
        assert "approved_by" in p
        assert "system" in p

    def test_frontmatter_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test.md").write_text(
                "---\n"
                "pivot_id: my-id\n"
                "date: 2026-03-21\n"
                "approved_by: Chase\n"
                "system: ChaseOS\n"
                "---\n"
                "# Pivot: My Change\n",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_pivot_log()
        p = result["data"]["pivots"][0]
        assert p["pivot_id"] == "my-id"
        assert p["date"] == "2026-03-21"
        assert p["approved_by"] == "Chase"
        assert p["system"] == "ChaseOS"

    def test_h1_title_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test.md").write_text(
                "---\npivot_id: x\n---\n# Pivot: My Big Change\n\nBody.",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_pivot_log()
        assert result["data"]["pivots"][0]["title"] == "Pivot: My Big Change"

    def test_pivots_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-01-01_old.md").write_text("# Old", encoding="utf-8")
            (pivot_dir / "2026-05-01_new.md").write_text("# New", encoding="utf-8")
            (pivot_dir / "2026-03-15_mid.md").write_text("# Mid", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_log()
        filenames = [p["filename"] for p in result["data"]["pivots"]]
        assert filenames[0] == "2026-05-01_new.md"
        assert filenames[-1] == "2026-01-01_old.md"

    def test_limit_caps_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            for idx in range(5):
                (pivot_dir / f"2026-05-0{idx + 1}_pivot.md").write_text("# Pivot", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_log(limit=2)
        assert result["data"]["pivot_count"] == 2
        assert result["data"]["limit"] == 2

    def test_negative_limit_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-05-01_pivot.md").write_text("# Pivot", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_log(limit=-1)
        assert result["data"]["pivot_count"] == 0
        assert result["data"]["limit"] == 0

    def test_invalid_limit_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_log(limit="bad")
        assert result["data"]["limit"] == 50

    def test_exception_returns_error_envelope(self):
        from unittest.mock import patch

        api = _make_api()
        with patch("pathlib.Path.glob", side_effect=RuntimeError("boom")):
            result = api.get_pivot_log()
        assert result["ok"] is False
        assert result["error"]["code"] == "pivot_log_failed"


class TestAPIPivotDetail:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_pivot_detail")
        assert callable(api.get_pivot_detail)

    def test_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test.md").write_text("# Test", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_detail("2026-03-21_test.md")
        assert isinstance(result, dict)

    def test_ok_true_for_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test.md").write_text("# Pivot\nBody.", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_detail("2026-03-21_test.md")
        assert result["ok"] is True
        assert result["surface"] == "pivot_detail"

    def test_data_has_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test.md").write_text("# My Pivot\nSome body text.", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_detail("2026-03-21_test.md")
        assert "content" in result["data"]
        assert "My Pivot" in result["data"]["content"]

    def test_data_has_size_and_line_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "2026-03-21_test.md").write_text("line1\nline2\n", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_detail("2026-03-21_test.md")
        assert "size_bytes" in result["data"]
        assert "line_count" in result["data"]

    def test_not_found_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_detail("nonexistent.md")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_non_md_extension_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_detail("file.py")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_filename"

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_detail("../../../CLAUDE.md")
        assert result["ok"] is False
        assert result["error"]["code"] == "path_traversal"

    def test_backslash_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_pivot_detail("..\\..\\CLAUDE.md")
        assert result["ok"] is False
        assert result["error"]["code"] == "path_traversal"

    def test_index_file_rejected_as_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pivot_dir = tmp_path / "07_LOGS" / "Pivot-Log"
            pivot_dir.mkdir(parents=True)
            (pivot_dir / "Pivot-Log-Index.md").write_text("# Index", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_pivot_detail("Pivot-Log-Index.md")
        assert result["ok"] is False
        assert result["error"]["code"] == "index_not_record"


HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"
JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"
CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"


def _html():
    return HTML_PATH.read_text(encoding="utf-8")


def _js():
    return JS_PATH.read_text(encoding="utf-8")


def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestPivotLogHTML:
    def test_sidebar_button_exists(self):
        assert 'data-panel="pivot-log"' in _html()

    def test_sidebar_button_label_v(self):
        assert 'nav-label">Pivot Log<' in _html()

    def test_sidebar_button_title_attr(self):
        assert 'title="Pivot Log"' in _html()

    def test_panel_section_exists(self):
        assert 'id="panel-pivot-log"' in _html()

    def test_panel_is_read_only(self):
        html = _html()
        assert 'id="panel-pivot-log"' in html
        assert 'data-read-only="true"' in html

    def test_status_element_exists(self):
        assert 'id="pivot-log-status"' in _html()

    def test_search_input_exists(self):
        assert 'id="pivot-log-search"' in _html()

    def test_list_element_exists(self):
        assert 'id="pivot-log-list"' in _html()

    def test_viewer_element_exists(self):
        assert 'id="pivot-log-viewer"' in _html()

    def test_close_button_exists(self):
        assert 'id="pivot-log-viewer-close"' in _html()


class TestPivotLogJS:
    def test_init_called_on_startup(self):
        assert "_initPivotLogPanel();" in _js()

    def test_panel_switch_loads_pivot_log(self):
        js = _js()
        assert "id === 'pivot-log'" in js
        assert "loadPivotLog()" in js

    def test_load_function_exists(self):
        assert "async function loadPivotLog()" in _js()

    def test_render_function_exists(self):
        assert "function renderPivotList" in _js()

    def test_detail_function_exists(self):
        assert "async function loadPivotDetail" in _js()

    def test_init_function_exists(self):
        assert "function _initPivotLogPanel()" in _js()

    def test_api_get_pivot_log_called(self):
        assert "get_pivot_log(100)" in _js()

    def test_api_get_pivot_detail_called(self):
        assert "get_pivot_detail(filename)" in _js()

    def test_filename_attribute_uses_attr_escape(self):
        assert 'data-filename="${escAttr(p.filename)}"' in _js()

    def test_content_uses_text_content(self):
        assert "viewerContent.textContent = resp.data.content" in _js()

    def test_search_filters_title_and_id(self):
        js = _js()
        assert "p.title" in js
        assert "p.pivot_id" in js

    def test_search_filters_approved_by(self):
        assert "p.approved_by" in _js()

    def test_click_handler_uses_pivot_item(self):
        assert ".pivot-item" in _js()


class TestPivotLogCSS:
    def test_panel_class_exists(self):
        assert ".pivot-log-panel" in _css()

    def test_search_row_class_exists(self):
        assert ".pivot-log-search-row" in _css()

    def test_body_class_exists(self):
        assert ".pivot-log-body" in _css()

    def test_list_class_exists(self):
        assert ".pivot-log-list" in _css()

    def test_item_class_exists(self):
        assert ".pivot-item" in _css()

    def test_active_item_class_exists(self):
        assert ".pivot-item--active" in _css()

    def test_viewer_class_exists(self):
        assert ".pivot-log-viewer" in _css()

    def test_empty_class_exists(self):
        assert ".pivot-log-empty" in _css()


class TestPivotLogRegistry:
    def test_registry_mounts_pivot_log_panel(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["pivot-log"]
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-pivot-log"
        assert panel["route_hint"] == "#pivot-log"
        assert "get_pivot_log" in panel["api_methods"]
        assert "get_pivot_detail" in panel["api_methods"]

    def test_registry_marks_pivot_log_read_only(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert panels["pivot-log"]["read_only"] is True
        assert panels["pivot-log"]["blocked_authority"]["canonical_mutation"] is False

    def test_registry_readiness_marks_pivot_log_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["pivot_log_panel_mounted"] is True

    def test_next_recommended_pass_updated(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"

    def test_registry_panel_count_includes_pivot_log(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["mounted_panel_count"] >= 23


