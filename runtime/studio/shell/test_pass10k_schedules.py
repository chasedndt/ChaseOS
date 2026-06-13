"""Tests for Pass 10K — Schedule Manager Panel.

Covers:
- API get_schedules() returns correct envelope
- API get_schedule_detail() validates schedule_id and delegates to inspect_schedule
- API toggle_schedule() routes through approval gate
- HTML: sidebar [K] button, #panel-schedules section, filter row, stats row, breadcrumb, back button
- CSS: all .schedules-* classes present
- JS: all Schedule functions present, panel switch wired, init called, API calls referenced
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_SHELL = Path(__file__).resolve().parent
_FRONTEND = _SHELL / "frontend"


# ── TestAPIGetSchedules ───────────────────────────────────────────────────────

class TestAPIGetSchedules:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_schedules")
        assert callable(StudioAPI.get_schedules)

    def test_returns_ok_envelope(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules()
        assert result["ok"] is True
        assert result["surface"] == "schedules"
        assert "data" in result

    def test_envelope_has_required_keys(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules()
        for key in ("ok", "status", "surface", "data", "warnings", "blocked_authority"):
            assert key in result

    def test_empty_vault_returns_ok(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules()
        assert result["ok"] is True

    def test_data_contains_schedules(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules()
        assert "schedules" in result["data"]

    def test_runtime_filter_passthrough(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules(runtime_filter="openclaw")
        assert result["ok"] is True

    def test_cadence_filter_passthrough(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules(cadence_filter="cron")
        assert result["ok"] is True

    def test_enabled_only_passthrough(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedules(enabled_only=True)
        assert result["ok"] is True

    def test_exception_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch("runtime.studio.schedule_inspector.list_schedules",
                   side_effect=RuntimeError("boom")):
            result = api.get_schedules()
        assert result["ok"] is False
        assert result["error"]["code"] == "schedules_failed"


# ── TestAPIGetScheduleDetail ──────────────────────────────────────────────────

class TestAPIGetScheduleSummary:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_schedule_summary")
        assert callable(StudioAPI.get_schedule_summary)

    def test_product_context_passes_through(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedule_summary()
        assert result["ok"] is True
        assert result["surface"] == "schedule_summary"
        assert "operating_context" in result["data"]
        assert "readiness" in result["data"]
        assert "feature_family_coverage" in result["data"]
        assert result["data"]["authority"]["runtime_dispatch_allowed"] is False

    def test_exception_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch("runtime.studio.schedule_inspector.get_schedule_summary",
                   side_effect=RuntimeError("boom")):
            result = api.get_schedule_summary()
        assert result["ok"] is False
        assert result["error"]["code"] == "schedule_summary_failed"


class TestAPIGetScheduleDetail:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "get_schedule_detail")
        assert callable(StudioAPI.get_schedule_detail)

    def test_empty_id_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedule_detail("")
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_schedule_id"

    def test_none_id_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedule_detail(None)
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_schedule_id"

    def test_missing_schedule_returns_not_found(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedule_detail("sch-does-not-exist")
        assert result["ok"] is False
        assert result["error"]["code"] == "not_found"

    def test_exception_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch("runtime.studio.schedule_inspector.inspect_schedule",
                   side_effect=RuntimeError("boom")):
            result = api.get_schedule_detail("sch-some-id")
        assert result["ok"] is False
        assert result["error"]["code"] == "schedule_detail_failed"

    def test_envelope_shape(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.get_schedule_detail("")
        for key in ("ok", "status", "surface", "error"):
            assert key in result
        assert "code" in result["error"]


# ── TestAPIToggleSchedule ─────────────────────────────────────────────────────

class TestAPIToggleSchedule:
    def _make_api(self, vault_root):
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault_root))

    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        assert hasattr(StudioAPI, "toggle_schedule")
        assert callable(StudioAPI.toggle_schedule)

    def test_empty_id_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.toggle_schedule("", True)
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_schedule_id"

    def test_none_id_returns_invalid(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.toggle_schedule(None, True)
        assert result["ok"] is False
        assert result["error"]["code"] == "invalid_schedule_id"

    def test_returns_approval_required_status(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.toggle_schedule("sch-operator-today-0700", True)
        assert result["status"] == "requires_approval"
        assert "approval" in result
        assert "approval_id" in result["approval"]

    def test_enable_produces_approval(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.toggle_schedule("sch-operator-today-0700", True)
        assert result["status"] == "requires_approval"

    def test_disable_produces_approval(self, tmp_path):
        api = self._make_api(tmp_path)
        result = api.toggle_schedule("sch-operator-today-0700", False)
        assert result["status"] == "requires_approval"

    def test_exception_returns_ok_false(self, tmp_path):
        api = self._make_api(tmp_path)
        with patch("runtime.studio.service.StudioService.validate_action",
                   side_effect=RuntimeError("boom")):
            result = api.toggle_schedule("sch-id", True)
        assert result["ok"] is False
        assert result["error"]["code"] == "toggle_failed"


# ── TestSchedulesHTMLStructure ────────────────────────────────────────────────

class TestSchedulesHTMLStructure:
    @pytest.fixture(autouse=True)
    def html(self):
        self._html = (_FRONTEND / "index.html").read_text(encoding="utf-8")

    def test_sidebar_button_present(self):
        assert 'data-panel="schedules"' in self._html

    def test_sidebar_button_label(self):
        assert 'nav-label">Schedules<' in self._html

    def test_sidebar_button_title(self):
        assert 'title="Schedules"' in self._html

    def test_panel_section_present(self):
        assert 'id="panel-schedules"' in self._html

    def test_panel_subtitle_productized(self):
        import re
        panel_block = re.search(r'id="panel-schedules".*?</section>', self._html, re.DOTALL)
        assert panel_block and 'Inspect local schedule intents' in panel_block.group()

    def test_runtime_authority_row_present(self):
        import re
        panel_block = re.search(r'id="panel-schedules".*?</section>', self._html, re.DOTALL)
        assert panel_block and 'class="runtime-authority-row"' in panel_block.group()

    def test_panel_read_only_marker(self):
        assert 'data-read-only="true"' in self._html

    def test_schedules_body_present(self):
        assert 'id="schedules-body"' in self._html

    def test_schedules_breadcrumb_present(self):
        assert 'id="schedules-breadcrumb"' in self._html

    def test_schedules_back_button_present(self):
        assert 'id="schedules-back-btn"' in self._html

    def test_schedules_breadcrumb_name_present(self):
        assert 'id="schedules-breadcrumb-name"' in self._html

    def test_schedules_filter_row_present(self):
        assert 'id="schedules-filter-row"' in self._html

    def test_schedules_runtime_filter_present(self):
        assert 'id="schedules-runtime-filter"' in self._html

    def test_schedules_cadence_filter_present(self):
        assert 'id="schedules-cadence-filter"' in self._html

    def test_schedules_enabled_only_present(self):
        assert 'id="schedules-enabled-only"' in self._html

    def test_schedules_refresh_button_present(self):
        assert 'id="schedules-refresh-btn"' in self._html

    def test_schedules_stats_row_present(self):
        assert 'id="schedules-stats-row"' in self._html

    def test_schedules_operating_context_present(self):
        assert 'id="schedules-operating-context"' in self._html

    def test_schedules_readiness_present(self):
        assert 'id="schedules-readiness"' in self._html

    def test_schedules_feature_coverage_present(self):
        assert 'id="schedules-feature-coverage"' in self._html

    def test_no_cron_dispatch_label_present(self):
        assert 'No cron / dispatch' in self._html

    def test_panel_kicker_read_only(self):
        import re
        panel_block = re.search(r'id="panel-schedules".*?</section>', self._html, re.DOTALL)
        assert panel_block and 'READ-ONLY' in panel_block.group()


# ── TestSchedulesCSS ──────────────────────────────────────────────────────────

class TestSchedulesCSS:
    @pytest.fixture(autouse=True)
    def css(self):
        self._css = (_FRONTEND / "styles.css").read_text(encoding="utf-8")

    def test_schedules_panel(self):
        assert '.schedules-panel' in self._css

    def test_schedules_breadcrumb(self):
        assert '.schedules-breadcrumb' in self._css

    def test_schedules_back_btn(self):
        assert '.schedules-back-btn' in self._css

    def test_schedules_filter_row(self):
        assert '.schedules-filter-row' in self._css

    def test_schedules_filter_select(self):
        assert '.schedules-filter-select' in self._css

    def test_schedules_stats_row(self):
        assert '.schedules-stats-row' in self._css

    def test_schedules_stat_enabled(self):
        assert '.schedules-stat-enabled' in self._css

    def test_schedules_stat_disabled(self):
        assert '.schedules-stat-disabled' in self._css

    def test_schedules_list(self):
        assert '.schedules-list' in self._css

    def test_schedules_card(self):
        assert '.schedules-card' in self._css

    def test_runtime_authority_row(self):
        assert '.runtime-authority-row' in self._css

    def test_schedules_badge_enabled(self):
        assert '.schedules-badge-enabled' in self._css

    def test_schedules_badge_disabled(self):
        assert '.schedules-badge-disabled' in self._css

    def test_schedules_info_grid(self):
        assert '.schedules-info-grid' in self._css

    def test_schedules_detail(self):
        assert '.schedules-detail' in self._css

    def test_schedules_change_log(self):
        assert '.schedules-change-log' in self._css

    def test_schedules_change_row(self):
        assert '.schedules-change-row' in self._css

    def test_schedules_context_panel(self):
        assert '.schedules-context-panel' in self._css

    def test_schedules_readiness_panel(self):
        assert '.schedules-readiness-panel' in self._css

    def test_schedules_feature_coverage(self):
        assert '.schedules-feature-coverage' in self._css

    def test_schedules_board(self):
        assert '.schedules-board' in self._css

    def test_schedules_stat_card(self):
        assert '.schedules-stat-card' in self._css

    def test_schedules_detail_hero(self):
        assert '.schedules-detail-hero' in self._css

    def test_schedules_boundary_list(self):
        assert '.schedules-boundary-list' in self._css


# ── TestSchedulesJS ───────────────────────────────────────────────────────────

class TestSchedulesJS:
    @pytest.fixture(autouse=True)
    def js(self):
        self._js = (_FRONTEND / "app.js").read_text(encoding="utf-8")

    def test_load_schedules_function(self):
        assert 'async function loadSchedules()' in self._js

    def test_load_schedule_detail_function(self):
        assert 'async function loadScheduleDetail(' in self._js

    def test_render_schedule_list_function(self):
        assert 'function renderScheduleList(' in self._js

    def test_render_schedule_detail_function(self):
        assert 'function renderScheduleDetail(' in self._js

    def test_render_schedules_operating_context_function(self):
        assert 'function renderSchedulesOperatingContext(' in self._js

    def test_render_schedules_readiness_function(self):
        assert 'function renderSchedulesReadiness(' in self._js

    def test_render_schedules_feature_coverage_function(self):
        assert 'function renderSchedulesFeatureCoverage(' in self._js

    def test_schedule_cards_select_inspector_data_attr(self):
        assert 'data-schedule-card="schedule"' in self._js

    def test_schedule_intents_board_present(self):
        assert 'data-schedules-board="schedule-intents"' in self._js

    def test_schedule_inspector_note_blocks_authority(self):
        assert 'No schedule enable/disable' in self._js
        assert 'Agent Bus task write' in self._js

    def test_render_object_inspector_schedule_context_function(self):
        assert 'function renderObjectInspectorScheduleContext(' in self._js

    def test_init_schedules_panel_function(self):
        assert 'function _initSchedulesPanel()' in self._js

    def test_panel_switch_wired(self):
        assert "if (id === 'schedules') loadSchedules()" in self._js

    def test_init_called_in_shell_ready(self):
        assert '_initSchedulesPanel()' in self._js

    def test_get_schedules_called(self):
        assert 'get_schedules(' in self._js

    def test_get_schedule_detail_called(self):
        assert 'get_schedule_detail(' in self._js

    def test_get_schedule_summary_called(self):
        assert 'get_schedule_summary()' in self._js

    def test_schedules_loaded_flag(self):
        assert 'schedulesLoaded' in self._js

    def test_schedules_detail_id_flag(self):
        assert 'schedulesDetailId' in self._js

    def test_back_button_clears_detail(self):
        assert 'schedulesDetailId = null' in self._js

    def test_runtime_filter_triggers_reload(self):
        assert 'schedules-runtime-filter' in self._js

    def test_cadence_filter_triggers_reload(self):
        assert 'schedules-cadence-filter' in self._js
