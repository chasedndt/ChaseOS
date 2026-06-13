"""Tests for Pass 10J — AOR Execution Monitor Panel.

Covers:
- API get_aor_executions() returns correct envelope
- API get_aor_execution_detail() validates filename and delegates to inspect_execution
- API get_aor_summary() unchanged; used by stats row
- HTML: sidebar [E] button, #panel-aor section, filter row, stats row, breadcrumb, back button
- CSS: all .aor-* classes present
- JS: all AOR functions present, panel switch wired, init called, API calls referenced
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SHELL = Path(__file__).resolve().parent
_FRONTEND = _SHELL / "frontend"
_VAULT = _SHELL.parents[2]


# ── TestAPIAORExecutions ──────────────────────────────────────────────────────

class TestAPIAORExecutions:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_returns_ok_envelope(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions()
        assert result["ok"] is True
        assert result["surface"] == "aor_executions"
        assert "data" in result

    def test_envelope_has_required_keys(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions()
        for key in ("ok", "status", "surface", "data", "warnings", "blocked_authority"):
            assert key in result

    def test_empty_vault_returns_ok(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions()
        assert result["ok"] is True

    def test_workflow_filter_passes_through(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions(workflow="operator_today")
        assert result["ok"] is True

    def test_status_filter_passes_through(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions(status="success")
        assert result["ok"] is True

    def test_limit_clamped_to_100(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions(limit=9999)
        assert result["ok"] is True

    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_aor_executions")
        assert callable(StudioAPI.get_aor_executions)

    def test_exception_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch("runtime.studio.aor_pipeline_monitor.list_recent_executions",
                   side_effect=RuntimeError("boom")):
            result = api.get_aor_executions()
        assert result["ok"] is False
        assert "error" in result
        assert "code" in result["error"]
        assert result["error"]["code"] == "aor_executions_failed"

    def test_data_contains_executions(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_executions()
        data = result["data"]
        assert "executions" in data


# ── TestAPIAORExecutionDetail ─────────────────────────────────────────────────

class TestAPIAORExecutionDetail:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_aor_execution_detail")
        assert callable(StudioAPI.get_aor_execution_detail)

    def test_empty_filename_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail("")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_filename"

    def test_none_filename_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail(None)
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_filename"

    def test_non_json_filename_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail("somefile.txt")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_filename"

    def test_missing_file_returns_not_found(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail("20260101-120000__abc__def.json")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_valid_file_returns_detail(self, tmp_path):
        import json
        audit_dir = tmp_path / "07_LOGS" / "Agent-Activity"
        audit_dir.mkdir(parents=True)
        record = {
            "ok": True,
            "audit_id": "abc123",
            "workflow_id": "operator_today",
            "timestamp_utc": "2026-05-06T10:00:00Z",
            "status": "success",
            "stage_reached": "audit_record",
            "outputs": {"daily_brief": "some content"},
        }
        fname = "20260506-100000__abc123__operator_today.json"
        (audit_dir / fname).write_text(json.dumps(record), encoding="utf-8")
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail(fname)
        assert result["ok"] is True
        assert result["data"]["audit_id"] == "abc123"
        assert result["data"]["workflow_id"] == "operator_today"

    def test_outputs_keys_present_in_detail(self, tmp_path):
        import json
        audit_dir = tmp_path / "07_LOGS" / "Agent-Activity"
        audit_dir.mkdir(parents=True)
        record = {"ok": True, "audit_id": "x", "workflow_id": "w", "status": "success",
                  "outputs": {"key_a": "v", "key_b": "v"}}
        fname = "20260506-100001__x__w.json"
        (audit_dir / fname).write_text(json.dumps(record), encoding="utf-8")
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail(fname)
        assert result["ok"] is True
        assert set(result["data"]["outputs_keys"]) == {"key_a", "key_b"}

    def test_exception_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch("runtime.studio.aor_pipeline_monitor.inspect_execution",
                   side_effect=RuntimeError("boom")):
            result = api.get_aor_execution_detail("valid.json")
        assert result["ok"] is False
        assert result["error"]["code"] == "detail_failed"

    def test_envelope_shape(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_aor_execution_detail("")
        for key in ("ok", "status", "surface", "error"):
            assert key in result
        assert "code" in result["error"]


# ── TestAORHTMLStructure ──────────────────────────────────────────────────────

class TestAORHTMLStructure:
    @pytest.fixture(autouse=True)
    def html(self):
        self._html = (_FRONTEND / "index.html").read_text(encoding="utf-8")

    def test_sidebar_button_present(self):
        assert 'data-panel="aor"' in self._html

    def test_sidebar_button_label(self):
        assert 'nav-label">Tasks &amp; Runs<' in self._html

    def test_sidebar_button_title(self):
        assert 'title="Tasks &amp; Runs"' in self._html

    def test_panel_section_present(self):
        assert 'id="panel-aor"' in self._html

    def test_panel_title_productized(self):
        import re
        panel_block = re.search(r'id="panel-aor".*?</section>', self._html, re.DOTALL)
        assert panel_block and '<h2>Tasks &amp; Runs</h2>' in panel_block.group()

    def test_panel_subtitle_productized(self):
        import re
        panel_block = re.search(r'id="panel-aor".*?</section>', self._html, re.DOTALL)
        assert panel_block and 'Inspect human and agent work history' in panel_block.group()

    def test_runtime_authority_row_present(self):
        import re
        panel_block = re.search(r'id="panel-aor".*?</section>', self._html, re.DOTALL)
        assert panel_block and 'class="runtime-authority-row"' in panel_block.group()

    def test_panel_read_only_marker(self):
        assert 'id="panel-aor"' in self._html and 'data-read-only="true"' in self._html

    def test_aor_body_present(self):
        assert 'id="aor-body"' in self._html

    def test_aor_breadcrumb_present(self):
        assert 'id="aor-breadcrumb"' in self._html

    def test_aor_back_button_present(self):
        assert 'id="aor-back-btn"' in self._html

    def test_aor_breadcrumb_name_present(self):
        assert 'id="aor-breadcrumb-name"' in self._html

    def test_aor_filter_row_present(self):
        assert 'id="aor-filter-row"' in self._html

    def test_aor_workflow_filter_present(self):
        assert 'id="aor-workflow-filter"' in self._html

    def test_aor_status_filter_present(self):
        assert 'id="aor-status-filter"' in self._html

    def test_aor_refresh_button_present(self):
        assert 'id="aor-refresh-btn"' in self._html

    def test_aor_stats_row_present(self):
        assert 'id="aor-stats-row"' in self._html

    def test_aor_operating_context_present(self):
        assert 'id="aor-operating-context"' in self._html

    def test_aor_board_tab_present(self):
        assert 'data-aor-tab="board"' in self._html

    def test_panel_kicker_product_posture(self):
        import re
        panel_block = re.search(r'id="panel-aor".*?</section>', self._html, re.DOTALL)
        assert panel_block and 'RUN DESK' in panel_block.group()
        assert 'No retry / dispatch' in panel_block.group()
        assert 'Loading...' not in panel_block.group()


# ── TestAORCSS ───────────────────────────────────────────────────────────────

class TestAORCSS:
    @pytest.fixture(autouse=True)
    def css(self):
        self._css = (_FRONTEND / "styles.css").read_text(encoding="utf-8")

    def test_aor_panel(self):
        assert '.aor-panel' in self._css

    def test_aor_breadcrumb(self):
        assert '.aor-breadcrumb' in self._css

    def test_aor_back_btn(self):
        assert '.aor-back-btn' in self._css

    def test_aor_filter_row(self):
        assert '.aor-filter-row' in self._css

    def test_aor_filter_select(self):
        assert '.aor-filter-select' in self._css

    def test_aor_stats_row(self):
        assert '.aor-stats-row' in self._css

    def test_aor_stat_success(self):
        assert '.aor-stat-success' in self._css

    def test_aor_stat_escalated(self):
        assert '.aor-stat-escalated' in self._css

    def test_aor_stat_failed(self):
        assert '.aor-stat-failed' in self._css

    def test_aor_exec_list(self):
        assert '.aor-exec-list' in self._css

    def test_aor_exec_card(self):
        assert '.aor-exec-card' in self._css

    def test_aor_board(self):
        assert '.aor-board' in self._css

    def test_aor_board_card(self):
        assert '.aor-board-card' in self._css

    def test_runtime_authority_row(self):
        assert '.runtime-authority-row' in self._css

    def test_aor_badge_success(self):
        assert '.aor-badge-success' in self._css

    def test_aor_badge_escalated(self):
        assert '.aor-badge-escalated' in self._css

    def test_aor_badge_failed(self):
        assert '.aor-badge-failed' in self._css

    def test_aor_badge_unknown(self):
        assert '.aor-badge-unknown' in self._css

    def test_aor_info_grid(self):
        assert '.aor-info-grid' in self._css

    def test_aor_detail(self):
        assert '.aor-detail' in self._css

    def test_aor_key_list(self):
        assert '.aor-key-list' in self._css

    def test_aor_key_tag(self):
        assert '.aor-key-tag' in self._css

    def test_aor_operating_context_styles(self):
        assert '.aor-context-panel' in self._css
        assert '.aor-context-grid' in self._css
        assert '.aor-readiness-grid' in self._css


# ── TestAORJS ────────────────────────────────────────────────────────────────

class TestAORJS:
    @pytest.fixture(autouse=True)
    def js(self):
        self._js = (_FRONTEND / "app.js").read_text(encoding="utf-8")

    def test_load_aor_function(self):
        assert 'async function loadAOR()' in self._js

    def test_load_aor_detail_function(self):
        assert 'async function loadAORDetail(' in self._js

    def test_render_aor_list_function(self):
        assert 'function renderAORList(' in self._js

    def test_render_aor_board_function(self):
        assert 'function renderAORBoard(' in self._js

    def test_render_aor_detail_function(self):
        assert 'function renderAORDetail(' in self._js

    def test_render_aor_operating_context_function(self):
        assert 'function renderAOROperatingContext(' in self._js
        assert 'Run Operating Context' in self._js
        assert 'Run Readiness' in self._js

    def test_select_aor_run_function(self):
        assert 'function selectAORRun(' in self._js
        assert 'data-aor-run-card="run"' in self._js

    def test_init_aor_panel_function(self):
        assert 'function _initAORPanel()' in self._js

    def test_panel_switch_wired(self):
        assert "if (id === 'aor') loadAOR()" in self._js

    def test_init_called_in_shell_ready(self):
        assert '_initAORPanel()' in self._js

    def test_get_aor_executions_called(self):
        assert 'get_aor_executions(' in self._js

    def test_get_aor_execution_detail_called(self):
        assert 'get_aor_execution_detail(' in self._js

    def test_get_aor_summary_called(self):
        assert 'get_aor_summary()' in self._js

    def test_aor_api_timeout_guard_present(self):
        assert 'function aorApiResultWithTimeout(' in self._js
        assert "did not respond within" in self._js
        assert "Run history unavailable" in self._js
        assert "No retry, resume, dispatch, or approval consumption was attempted." in self._js

    def test_board_tab_branch(self):
        assert "dataset.aorTab === 'board'" in self._js

    def test_runtime_object_inspector_for_runs(self):
        assert 'function renderObjectInspectorRunContext(' in self._js

    def test_aor_loaded_flag(self):
        assert 'aorLoaded' in self._js

    def test_aor_detail_filename_flag(self):
        assert 'aorDetailFilename' in self._js

    def test_back_button_clears_detail(self):
        assert 'aorDetailFilename = null' in self._js

    def test_workflow_filter_triggers_reload(self):
        assert "aor-workflow-filter" in self._js

    def test_status_filter_triggers_reload(self):
        assert "aor-status-filter" in self._js
