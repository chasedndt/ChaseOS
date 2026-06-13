"""Pass 10T â€” Feature Filter Panel tests.

Covers: get_feature_filter API, HTML panel structure, CSS classes, JS functions,
and panel registry entry.
"""
from __future__ import annotations

import re
from pathlib import Path
import sys

import pytest

SHELL_DIR = Path(__file__).parent
VAULT_ROOT = SHELL_DIR.parent.parent.parent
sys.path.insert(0, str(SHELL_DIR.parent.parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api(tmp_path):
    from runtime.studio.shell.api import StudioAPI
    vault = tmp_path
    (vault / "04_SOPS").mkdir(parents=True)
    (vault / "runtime" / "aor").mkdir(parents=True)

    sop_md = vault / "04_SOPS" / "Feature-Filter-SOP.md"
    sop_md.write_text(
        "---\ntitle: Feature Filter SOP\nversion: '1.0'\n---\n\n# Feature Filter SOP\n\nQ1: What problem?\n",
        encoding="utf-8",
    )

    task_yaml = vault / "runtime" / "aor" / "task_type_table.yaml"
    task_yaml.write_text(
        "task_types:\n"
        "  - id: operator-briefing\n"
        "    description: Daily operator briefing\n"
        "    runtime_class: read-heavy\n"
        "    permission_ceiling: no_protected_file_writes\n"
        "    writeback_expectations: operator brief only\n"
        "    escalation_trigger:\n"
        "      - protected file write requested\n"
        "      - write outside declared writeback_targets\n"
        "  - id: audit-review\n"
        "    description: Read audit and build logs\n"
        "    runtime_class: read-only\n"
        "    permission_ceiling: read_only\n"
        "    writeback_expectations: none\n"
        "    escalation_trigger:\n"
        "      - any write requested\n",
        encoding="utf-8",
    )

    inst = StudioAPI.__new__(StudioAPI)
    inst._vault_root = str(vault)
    inst._dev_mode = False
    return inst


@pytest.fixture
def api_empty(tmp_path):
    from runtime.studio.shell.api import StudioAPI
    inst = StudioAPI.__new__(StudioAPI)
    inst._vault_root = str(tmp_path)
    inst._dev_mode = False
    return inst


# ---------------------------------------------------------------------------
# TestAPIFeatureFilter
# ---------------------------------------------------------------------------

class TestAPIFeatureFilter:
    def test_ok_envelope(self, api):
        r = api.get_feature_filter()
        assert r["ok"] is True
        assert r["status"] == "ok"

    def test_surface(self, api):
        r = api.get_feature_filter()
        assert r["surface"] == "feature_filter"

    def test_sop_content_present(self, api):
        r = api.get_feature_filter()
        assert "Feature Filter SOP" in r["data"]["sop_content"]

    def test_sop_size_bytes(self, api):
        r = api.get_feature_filter()
        assert r["data"]["sop_size_bytes"] > 0

    def test_sop_line_count(self, api):
        r = api.get_feature_filter()
        assert r["data"]["sop_line_count"] >= 5

    def test_task_types_list(self, api):
        r = api.get_feature_filter()
        types = r["data"]["task_types"]
        assert isinstance(types, list)
        assert len(types) == 2

    def test_task_type_count(self, api):
        r = api.get_feature_filter()
        assert r["data"]["task_type_count"] == 2

    def test_task_type_fields(self, api):
        r = api.get_feature_filter()
        tt = r["data"]["task_types"][0]
        assert tt["id"] == "operator-briefing"
        assert tt["description"] == "Daily operator briefing"
        assert tt["runtime_class"] == "read-heavy"
        assert tt["permission_ceiling"] == "no_protected_file_writes"
        assert tt["writeback_expectations"] == "operator brief only"
        assert tt["escalation_trigger_count"] == 2

    def test_escalation_trigger_count_second(self, api):
        r = api.get_feature_filter()
        tt = r["data"]["task_types"][1]
        assert tt["escalation_trigger_count"] == 1

    def test_yaml_raw_present(self, api):
        r = api.get_feature_filter()
        assert "task_types" in r["data"]["yaml_raw"]

    def test_missing_sop_warning(self, api_empty):
        r = api_empty.get_feature_filter()
        assert r["ok"] is True
        assert r["data"]["sop_content"] == ""
        assert any("Feature-Filter-SOP.md" in w for w in r["warnings"])

    def test_missing_yaml_warning(self, api_empty):
        r = api_empty.get_feature_filter()
        assert r["ok"] is True
        assert r["data"]["task_types"] == []
        assert any("task_type_table.yaml" in w for w in r["warnings"])

    def test_empty_task_type_count(self, api_empty):
        r = api_empty.get_feature_filter()
        assert r["data"]["task_type_count"] == 0

    def test_no_vault_write(self, api, tmp_path):
        before = set(tmp_path.rglob("*"))
        api.get_feature_filter()
        after = set(tmp_path.rglob("*"))
        assert before == after


# ---------------------------------------------------------------------------
# TestFeatureFilterHTML
# ---------------------------------------------------------------------------

class TestFeatureFilterHTML:
    @pytest.fixture(autouse=True)
    def html(self):
        self._html = (SHELL_DIR / "frontend" / "index.html").read_text(encoding="utf-8")

    def test_sidebar_button_f(self):
        assert 'data-panel="feature-filter"' in self._html

    def test_sidebar_button_label(self):
        assert 'nav-label">Feature Audit<' in self._html

    def test_panel_section_exists(self):
        assert 'id="panel-feature-filter"' in self._html

    def test_panel_read_only(self):
        assert 'data-read-only="true"' in self._html

    def test_panel_status_pill(self):
        assert 'id="feature-filter-status"' in self._html

    def test_task_types_tab(self):
        assert 'data-ff-tab="task-types"' in self._html

    def test_sop_tab(self):
        assert 'data-ff-tab="sop"' in self._html

    def test_search_input(self):
        assert 'id="feature-filter-search"' in self._html

    def test_task_list_div(self):
        assert 'id="feature-filter-task-list"' in self._html

    def test_sop_content_div(self):
        assert 'id="feature-filter-sop-content"' in self._html

    def test_tab_task_types_body(self):
        assert 'id="feature-filter-tab-task-types"' in self._html

    def test_tab_sop_body(self):
        assert 'id="feature-filter-tab-sop"' in self._html

    def test_panel_kicker_read_only(self):
        assert "READ-ONLY" in self._html

    def test_title_text(self):
        assert "Feature Audit" in self._html


# ---------------------------------------------------------------------------
# TestFeatureFilterCSS
# ---------------------------------------------------------------------------

class TestFeatureFilterCSS:
    @pytest.fixture(autouse=True)
    def css(self):
        self._css = (SHELL_DIR / "frontend" / "styles.css").read_text(encoding="utf-8")

    def test_feature_filter_panel_class(self):
        assert ".feature-filter-panel" in self._css

    def test_feature_filter_tabs_class(self):
        assert ".feature-filter-tabs" in self._css

    def test_ff_tab_class(self):
        assert ".ff-tab" in self._css

    def test_ff_tab_active_class(self):
        assert ".ff-tab--active" in self._css

    def test_feature_filter_tab_body(self):
        assert ".feature-filter-tab-body" in self._css

    def test_feature_filter_search_row(self):
        assert ".feature-filter-search-row" in self._css

    def test_feature_filter_task_list(self):
        assert ".feature-filter-task-list" in self._css

    def test_ff_task_item(self):
        assert ".ff-task-item" in self._css

    def test_ff_task_id(self):
        assert ".ff-task-id" in self._css

    def test_ff_task_desc(self):
        assert ".ff-task-desc" in self._css

    def test_ff_task_meta(self):
        assert ".ff-task-meta" in self._css

    def test_ff_task_empty(self):
        assert ".ff-task-empty" in self._css

    def test_feature_filter_sop_content(self):
        assert ".feature-filter-sop-content" in self._css


# ---------------------------------------------------------------------------
# TestFeatureFilterJS
# ---------------------------------------------------------------------------

class TestFeatureFilterJS:
    @pytest.fixture(autouse=True)
    def js(self):
        self._js = (SHELL_DIR / "frontend" / "app.js").read_text(encoding="utf-8")

    def test_state_var_loaded(self):
        assert "featureFilterLoaded" in self._js

    def test_state_var_task_types(self):
        assert "_taskTypesAll" in self._js

    def test_load_function_defined(self):
        assert "async function loadFeatureFilter" in self._js

    def test_render_function_defined(self):
        assert "function renderTaskTypeList" in self._js

    def test_init_function_defined(self):
        assert "function _initFeatureFilterPanel" in self._js

    def test_api_call_get_feature_filter(self):
        assert "get_feature_filter" in self._js

    def test_panel_switch_wired(self):
        assert "if (id === 'feature-filter') loadFeatureFilter()" in self._js

    def test_init_called_in_on_shell_ready(self):
        assert "_initFeatureFilterPanel();" in self._js

    def test_no_vault_write_in_js(self):
        assert "pywebview.api.create" not in self._js.split("function loadFeatureFilter")[1].split("function renderTaskTypeList")[0]

    def test_esc_html_used(self):
        assert "escHtml" in self._js.split("function loadFeatureFilter")[1].split("function renderTaskTypeList")[0]

    def test_tab_switching_wired(self):
        assert "ff-tab" in self._js


# ---------------------------------------------------------------------------
# TestFeatureFilterRegistry
# ---------------------------------------------------------------------------

class TestFeatureFilterRegistry:
    @pytest.fixture(autouse=True)
    def reg(self, tmp_path):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        self._reg = build_native_shell_panel_registry(str(tmp_path))

    def test_panel_mounted(self):
        panels = {p["id"]: p for p in self._reg["panels"]}
        assert "feature-filter" in panels
        assert panels["feature-filter"]["status"] == "mounted"

    def test_panel_read_only(self):
        panels = {p["id"]: p for p in self._reg["panels"]}
        assert panels["feature-filter"]["read_only"] is True

    def test_api_methods(self):
        panels = {p["id"]: p for p in self._reg["panels"]}
        assert "get_feature_filter" in panels["feature-filter"]["api_methods"]

    def test_readiness_key_set(self):
        assert self._reg["readiness"]["feature_filter_panel_mounted"] is True

    def test_next_pass_advanced(self):
        nxt = self._reg["readiness"]["next_recommended_pass"]
        assert nxt == "ventureops-operator-readiness-gate"
        assert "feature-filter" not in nxt
