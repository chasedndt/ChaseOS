"""Pass 10U â€” Workflow Registry Panel tests.

Covers: get_workflow_registry / get_workflow_detail API, HTML panel structure,
CSS classes, JS functions, and panel registry entry.
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

SHELL_DIR = Path(__file__).parent
VAULT_ROOT = SHELL_DIR.parent.parent.parent
sys.path.insert(0, str(SHELL_DIR.parent.parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_manifest(path: Path, id: str, name: str, task_type: str = "operator-briefing",
                   status: str = "active", trigger_type: str = "manual") -> None:
    path.write_text(
        f"id: {id}\nname: \"{name}\"\ndescription: \"Test workflow\"\n"
        f"task_type: {task_type}\nrole_card: {task_type}\n"
        f"trigger_type: {trigger_type}\nstatus: {status}\nowner: operator\n",
        encoding="utf-8",
    )


@pytest.fixture
def api(tmp_path):
    from runtime.studio.shell.api import StudioAPI
    vault = tmp_path
    reg_dir = vault / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True)

    _make_manifest(reg_dir / "operator_today.yaml", "operator_today", "Operator Today Briefing",
                   task_type="operator-briefing", status="active", trigger_type="manual")
    _make_manifest(reg_dir / "graph_hygiene.yaml", "graph_hygiene", "Graph Hygiene",
                   task_type="os-graph-maintenance", status="active", trigger_type="scheduled")
    _make_manifest(reg_dir / "hermes_watch.yaml", "hermes_watch", "Hermes Watch Loop",
                   task_type="coordination", status="draft", trigger_type="scheduled")

    # Schema/template files should be excluded
    (reg_dir / "_schema.yaml").write_text("schema: true\n", encoding="utf-8")
    (reg_dir / "_sbp_base_template.yaml").write_text("template: true\n", encoding="utf-8")

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
# TestAPIWorkflowRegistry
# ---------------------------------------------------------------------------

class TestAPIWorkflowRegistry:
    def test_ok_envelope(self, api):
        r = api.get_workflow_registry()
        assert r["ok"] is True
        assert r["status"] == "ok"

    def test_surface(self, api):
        r = api.get_workflow_registry()
        assert r["surface"] == "workflow_registry"

    def test_workflow_count(self, api):
        r = api.get_workflow_registry()
        assert r["data"]["workflow_count"] == 3

    def test_workflows_list_type(self, api):
        r = api.get_workflow_registry()
        assert isinstance(r["data"]["workflows"], list)

    def test_schema_files_excluded(self, api):
        r = api.get_workflow_registry()
        ids = [w["id"] for w in r["data"]["workflows"]]
        assert "_schema" not in ids
        assert "_sbp_base_template" not in ids

    def test_workflow_fields(self, api):
        r = api.get_workflow_registry()
        wf = next(w for w in r["data"]["workflows"] if w["id"] == "operator_today")
        assert wf["name"] == "Operator Today Briefing"
        assert wf["task_type"] == "operator-briefing"
        assert wf["status"] == "active"
        assert wf["trigger_type"] == "manual"
        assert wf["size_bytes"] > 0

    def test_sorted_by_filename(self, api):
        r = api.get_workflow_registry()
        ids = [w["id"] for w in r["data"]["workflows"]]
        assert ids == sorted(ids)

    def test_status_filter_active(self, api):
        r = api.get_workflow_registry(status="active")
        assert r["ok"] is True
        assert all(w["status"] == "active" for w in r["data"]["workflows"])
        assert r["data"]["workflow_count"] == 2

    def test_status_filter_draft(self, api):
        r = api.get_workflow_registry(status="draft")
        assert r["data"]["workflow_count"] == 1
        assert r["data"]["workflows"][0]["id"] == "hermes_watch"

    def test_status_filter_empty_returns_all(self, api):
        r = api.get_workflow_registry(status="")
        assert r["data"]["workflow_count"] == 3

    def test_status_filter_in_data(self, api):
        r = api.get_workflow_registry(status="active")
        assert r["data"]["status_filter"] == "active"

    def test_missing_registry_dir_warning(self, api_empty):
        r = api_empty.get_workflow_registry()
        assert r["ok"] is True
        assert r["data"]["workflow_count"] == 0
        assert any("not found" in w for w in r["warnings"])

    def test_no_vault_write(self, api, tmp_path):
        before = set(tmp_path.rglob("*"))
        api.get_workflow_registry()
        after = set(tmp_path.rglob("*"))
        assert before == after


class TestAPIWorkflowDetail:
    def test_ok_envelope(self, api):
        r = api.get_workflow_detail("operator_today.yaml")
        assert r["ok"] is True

    def test_surface(self, api):
        r = api.get_workflow_detail("operator_today.yaml")
        assert r["surface"] == "workflow_detail"

    def test_content_present(self, api):
        r = api.get_workflow_detail("operator_today.yaml")
        assert "operator_today" in r["data"]["content"]

    def test_size_bytes(self, api):
        r = api.get_workflow_detail("operator_today.yaml")
        assert r["data"]["size_bytes"] > 0

    def test_line_count(self, api):
        r = api.get_workflow_detail("operator_today.yaml")
        assert r["data"]["line_count"] >= 5

    def test_not_found(self, api):
        r = api.get_workflow_detail("missing.yaml")
        assert r["ok"] is False
        assert r["error"]["code"] == "not_found"

    def test_invalid_extension(self, api):
        r = api.get_workflow_detail("operator_today.md")
        assert r["ok"] is False
        assert r["error"]["code"] == "invalid_filename"

    def test_path_traversal_slash(self, api):
        r = api.get_workflow_detail("../something.yaml")
        assert r["ok"] is False
        assert "path_traversal" in r["error"]["code"] or "invalid" in r["error"]["code"]

    def test_schema_file_blocked(self, api):
        r = api.get_workflow_detail("_schema.yaml")
        assert r["ok"] is False
        assert r["error"]["code"] == "schema_file"

    def test_template_file_blocked(self, api):
        r = api.get_workflow_detail("_sbp_base_template.yaml")
        assert r["ok"] is False
        assert r["error"]["code"] == "schema_file"

    def test_no_vault_write(self, api, tmp_path):
        before = set(tmp_path.rglob("*"))
        api.get_workflow_detail("operator_today.yaml")
        after = set(tmp_path.rglob("*"))
        assert before == after


# ---------------------------------------------------------------------------
# TestWorkflowRegistryHTML
# ---------------------------------------------------------------------------

class TestWorkflowRegistryHTML:
    @pytest.fixture(autouse=True)
    def html(self):
        self._html = (SHELL_DIR / "frontend" / "index.html").read_text(encoding="utf-8")

    def test_sidebar_button_o(self):
        assert 'data-panel="workflow-registry"' in self._html

    def test_sidebar_button_label(self):
        assert 'data-panel="workflow-registry"' in self._html

    def test_panel_section_exists(self):
        assert 'id="panel-workflow-registry"' in self._html

    def test_panel_read_only(self):
        assert 'data-read-only="true"' in self._html

    def test_status_pill(self):
        assert 'id="workflow-registry-status"' in self._html

    def test_search_input(self):
        assert 'id="workflow-registry-search"' in self._html

    def test_list_div(self):
        assert 'id="workflow-registry-list"' in self._html

    def test_viewer_div(self):
        assert 'id="workflow-registry-viewer"' in self._html

    def test_viewer_title(self):
        assert 'id="workflow-registry-viewer-title"' in self._html

    def test_viewer_close(self):
        assert 'id="workflow-registry-viewer-close"' in self._html

    def test_viewer_content(self):
        assert 'id="workflow-registry-viewer-content"' in self._html

    def test_panel_kicker_read_only(self):
        assert "READ-ONLY" in self._html

    def test_title_text(self):
        assert "Workflow Registry" in self._html


# ---------------------------------------------------------------------------
# TestWorkflowRegistryCSS
# ---------------------------------------------------------------------------

class TestWorkflowRegistryCSS:
    @pytest.fixture(autouse=True)
    def css(self):
        self._css = (SHELL_DIR / "frontend" / "styles.css").read_text(encoding="utf-8")

    def test_panel_class(self):
        assert ".workflow-registry-panel" in self._css

    def test_search_row_class(self):
        assert ".workflow-registry-search-row" in self._css

    def test_body_class(self):
        assert ".workflow-registry-body" in self._css

    def test_list_class(self):
        assert ".workflow-registry-list" in self._css

    def test_item_class(self):
        assert ".workflow-item" in self._css

    def test_item_active_class(self):
        assert ".workflow-item--active" in self._css

    def test_item_id_class(self):
        assert ".workflow-item-id" in self._css

    def test_item_name_class(self):
        assert ".workflow-item-name" in self._css

    def test_item_meta_class(self):
        assert ".workflow-item-meta" in self._css

    def test_viewer_class(self):
        assert ".workflow-registry-viewer" in self._css

    def test_viewer_content_class(self):
        assert ".workflow-registry-viewer-content" in self._css

    def test_empty_class(self):
        assert ".workflow-registry-empty" in self._css


# ---------------------------------------------------------------------------
# TestWorkflowRegistryJS
# ---------------------------------------------------------------------------

class TestWorkflowRegistryJS:
    @pytest.fixture(autouse=True)
    def js(self):
        self._js = (SHELL_DIR / "frontend" / "app.js").read_text(encoding="utf-8")

    def test_state_var_loaded(self):
        assert "workflowRegistryLoaded" in self._js

    def test_state_var_detail_file(self):
        assert "workflowDetailFile" in self._js

    def test_state_var_all(self):
        assert "_workflowsAll" in self._js

    def test_load_function_defined(self):
        assert "async function loadWorkflowRegistry" in self._js

    def test_render_function_defined(self):
        assert "function renderWorkflowList" in self._js

    def test_load_detail_function_defined(self):
        assert "async function loadWorkflowDetail" in self._js

    def test_init_function_defined(self):
        assert "function _initWorkflowRegistryPanel" in self._js

    def test_api_call_registry(self):
        assert "get_workflow_registry" in self._js

    def test_api_call_detail(self):
        assert "get_workflow_detail" in self._js

    def test_panel_switch_wired(self):
        assert "if (id === 'workflow-registry') loadWorkflowRegistry()" in self._js

    def test_init_called_in_on_shell_ready(self):
        assert "_initWorkflowRegistryPanel();" in self._js

    def test_esc_html_used(self):
        load_block = self._js.split("async function loadWorkflowRegistry")[1].split("function renderWorkflowList")[0]
        assert "escHtml" in load_block

    def test_esc_attr_used_in_render(self):
        render_block = self._js.split("function renderWorkflowList")[1].split("async function loadWorkflowDetail")[0]
        assert "escAttr" in render_block


# ---------------------------------------------------------------------------
# TestWorkflowRegistryRegistry
# ---------------------------------------------------------------------------

class TestWorkflowRegistryRegistry:
    @pytest.fixture(autouse=True)
    def reg(self, tmp_path):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        self._reg = build_native_shell_panel_registry(str(tmp_path))

    def test_panel_mounted(self):
        panels = {p["id"]: p for p in self._reg["panels"]}
        assert "workflow-registry" in panels
        assert panels["workflow-registry"]["status"] == "mounted"

    def test_panel_read_only(self):
        panels = {p["id"]: p for p in self._reg["panels"]}
        assert panels["workflow-registry"]["read_only"] is True

    def test_api_methods(self):
        panels = {p["id"]: p for p in self._reg["panels"]}
        methods = panels["workflow-registry"]["api_methods"]
        assert "get_workflow_registry" in methods
        assert "get_workflow_detail" in methods

    def test_readiness_key_set(self):
        assert self._reg["readiness"]["workflow_registry_panel_mounted"] is True

    def test_next_pass_advanced(self):
        nxt = self._reg["readiness"]["next_recommended_pass"]
        assert nxt == "ventureops-operator-readiness-gate"
        assert "workflow-registry" not in nxt


