"""Pass 10Q â€” Build Log Viewer panel tests.

Tests for:
  - StudioAPI get_build_logs / get_build_log_content
  - index.html: sidebar [L] button, panel structure
  - styles.css: .build-log-* / .build-logs-* classes
  - app.js: JS functions, panel switch, init wiring
  - panel_registry: build_logs_panel_mounted
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


# â”€â”€ TestAPIBuildLogs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAPIBuildLogs:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_build_logs")
        assert callable(api.get_build_logs)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_build_logs()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_build_logs()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_surface_is_build_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert result["surface"] == "build_logs"

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert result["ok"] is True

    def test_data_has_logs_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert "logs" in result["data"]
        assert isinstance(result["data"]["logs"], list)

    def test_data_has_log_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert "log_count" in result["data"]

    def test_data_has_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_logs(limit=5)
        assert result["data"]["limit"] == 5

    def test_empty_vault_returns_zero_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert result["data"]["log_count"] == 0

    def test_logs_have_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-05-06-test-log.md").write_text(
                "---\ntitle: Test Log\n---\n# Content", encoding="utf-8"
            )
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert result["data"]["log_count"] == 1
        log = result["data"]["logs"][0]
        assert "filename" in log
        assert "date" in log
        assert "title" in log
        assert "size_bytes" in log

    def test_title_extracted_from_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-05-06-test-log.md").write_text(
                '---\ntitle: "My Custom Title"\n---\n# Body', encoding="utf-8"
            )
            api = _make_api(tmp)
            result = api.get_build_logs()
        assert result["data"]["logs"][0]["title"] == "My Custom Title"

    def test_index_file_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "Build-Logs-Index.md").write_text("# Index", encoding="utf-8")
            (logs_dir / "2026-05-06-real-log.md").write_text("# Real", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_build_logs()
        filenames = [l["filename"] for l in result["data"]["logs"]]
        assert "Build-Logs-Index.md" not in filenames
        assert "2026-05-06-real-log.md" in filenames

    def test_logs_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-03-01-old.md").write_text("# Old", encoding="utf-8")
            (logs_dir / "2026-05-01-new.md").write_text("# New", encoding="utf-8")
            (logs_dir / "2026-04-15-mid.md").write_text("# Mid", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_build_logs()
        filenames = [l["filename"] for l in result["data"]["logs"]]
        assert filenames[0] == "2026-05-01-new.md"
        assert filenames[-1] == "2026-03-01-old.md"


# â”€â”€ TestAPIBuildLogContent â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAPIBuildLogContent:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_build_log_content")
        assert callable(api.get_build_log_content)

    def test_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-05-06-test.md").write_text("# Test", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_build_log_content("2026-05-06-test.md")
        assert isinstance(result, dict)

    def test_ok_true_for_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-05-06-test.md").write_text("# Hello", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_build_log_content("2026-05-06-test.md")
        assert result["ok"] is True
        assert result["surface"] == "build_log_content"

    def test_data_has_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-05-06-test.md").write_text("# Hello World", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_build_log_content("2026-05-06-test.md")
        assert "content" in result["data"]
        assert "Hello World" in result["data"]["content"]

    def test_data_has_size_and_line_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            logs_dir = tmp_path / "07_LOGS" / "Build-Logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "2026-05-06-test.md").write_text("line1\nline2\n", encoding="utf-8")
            api = _make_api(tmp)
            result = api.get_build_log_content("2026-05-06-test.md")
        assert "size_bytes" in result["data"]
        assert "line_count" in result["data"]

    def test_not_found_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_log_content("nonexistent.md")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_non_md_extension_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_log_content("somefile.py")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_filename"

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_build_log_content("../../../CLAUDE.md")
        assert result["ok"] is False


# â”€â”€ TestBuildLogsHTML â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"


def _html():
    return HTML_PATH.read_text(encoding="utf-8")


class TestBuildLogsHTML:
    def test_sidebar_button_exists(self):
        assert 'data-panel="build-logs"' in _html()

    def test_sidebar_button_label_L(self):
        assert 'nav-label">Logs / Audit<' in _html()

    def test_sidebar_button_title_attr(self):
        assert 'title="Logs / Audit"' in _html()

    def test_panel_section_exists(self):
        assert 'id="panel-build-logs"' in _html()

    def test_panel_data_panel_id(self):
        assert 'data-panel-id="build-logs"' in _html()

    def test_read_only_marker(self):
        html = _html()
        idx = html.find('id="panel-build-logs"')
        snippet = html[idx:idx + 400]
        assert "READ-ONLY" in snippet

    def test_build_logs_list_exists(self):
        assert 'id="build-logs-list"' in _html()

    def test_build_logs_viewer_exists(self):
        assert 'id="build-logs-viewer"' in _html()

    def test_build_logs_search_exists(self):
        assert 'id="build-logs-search"' in _html()

    def test_build_logs_viewer_close_exists(self):
        assert 'id="build-logs-viewer-close"' in _html()

    def test_build_logs_viewer_content_exists(self):
        assert 'id="build-logs-viewer-content"' in _html()


# â”€â”€ TestBuildLogsCSSClasses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"


def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestBuildLogsCSSClasses:
    def test_build_logs_panel(self):
        assert ".build-logs-panel" in _css()

    def test_build_logs_search_row(self):
        assert ".build-logs-search-row" in _css()

    def test_build_logs_body(self):
        assert ".build-logs-body" in _css()

    def test_build_logs_list(self):
        assert ".build-logs-list" in _css()

    def test_build_log_item(self):
        assert ".build-log-item" in _css()

    def test_build_log_item_active(self):
        assert ".build-log-item--active" in _css()

    def test_build_log_date(self):
        assert ".build-log-date" in _css()

    def test_build_log_title(self):
        assert ".build-log-title" in _css()

    def test_build_logs_viewer(self):
        assert ".build-logs-viewer" in _css()

    def test_build_logs_viewer_header(self):
        assert ".build-logs-viewer-header" in _css()

    def test_build_logs_viewer_content(self):
        assert ".build-logs-viewer-content" in _css()

    def test_build_logs_viewer_close(self):
        assert ".build-logs-viewer-close" in _css()

    def test_build_log_text(self):
        assert ".build-log-text" in _css()

    def test_build_logs_empty(self):
        assert ".build-logs-empty" in _css()


# â”€â”€ TestBuildLogsJS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"


def _js():
    return JS_PATH.read_text(encoding="utf-8")


class TestBuildLogsJS:
    def test_loadBuildLogs_defined(self):
        assert "async function loadBuildLogs()" in _js()

    def test_renderBuildLogsList_defined(self):
        assert "function renderBuildLogsList(" in _js()

    def test_loadBuildLogContent_defined(self):
        assert "async function loadBuildLogContent(" in _js()

    def test_initBuildLogsPanel_defined(self):
        assert "function _initBuildLogsPanel()" in _js()

    def test_panel_switch_wired(self):
        assert "if (id === 'build-logs') loadBuildLogs()" in _js()

    def test_init_called_in_onShellReady(self):
        assert "_initBuildLogsPanel()" in _js()

    def test_api_get_build_logs_called(self):
        assert "get_build_logs(" in _js()

    def test_api_get_build_log_content_called(self):
        assert "get_build_log_content(" in _js()

    def test_build_logs_loaded_state_variable(self):
        assert "buildLogsLoaded" in _js()

    def test_build_log_detail_file_state(self):
        assert "buildLogDetailFile" in _js()

    def test_viewer_close_handler_wired(self):
        assert "build-logs-viewer-close" in _js()

    def test_search_filter_logic(self):
        assert "build-logs-search" in _js()


# â”€â”€ TestBuildLogsRegistry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestBuildLogsRegistry:
    def test_registry_mounts_build_logs_panel(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        panel = panels["build-logs"]
        assert panel["status"] == "mounted"
        assert panel["frontend_target"] == "panel-build-logs"
        assert panel["route_hint"] == "#build-logs"
        assert "get_build_logs" in panel["api_methods"]
        assert "get_build_log_content" in panel["api_methods"]

    def test_registry_keeps_build_logs_read_only(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert panels["build-logs"]["read_only"] is True
        assert panels["build-logs"]["blocked_authority"]["canonical_mutation"] is False

    def test_registry_readiness_marks_build_logs_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["build_logs_panel_mounted"] is True

    def test_next_recommended_pass_updated(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"

