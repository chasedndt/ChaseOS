"""Pass 10P â€” Sprint Focus Quick Panel tests.

Tests for:
  - StudioAPI get_sprint_focus
  - index.html: #sprint-focus-section, #sprint-focus-body inside project-workspace
  - styles.css: .sprint-focus-* classes
  - app.js: JS functions, panel switch wiring
  - panel_registry: sprint_focus_section_mounted + api_methods
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


# â”€â”€ TestAPISprintFocus â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestAPISprintFocus:
    def test_method_exists(self):
        api = _make_api()
        assert hasattr(api, "get_sprint_focus")
        assert callable(api.get_sprint_focus)

    def test_returns_dict(self):
        api = _make_api()
        result = api.get_sprint_focus()
        assert isinstance(result, dict)

    def test_ok_envelope_shape(self):
        api = _make_api()
        result = api.get_sprint_focus()
        assert "ok" in result
        assert "status" in result
        assert "surface" in result

    def test_surface_is_sprint_focus(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert result["surface"] == "sprint_focus"

    def test_ok_true_with_empty_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert result["ok"] is True

    def test_data_has_sprint_focus_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert "sprint_focus" in result["data"]

    def test_data_has_now_md_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert "now_md_found" in result["data"]

    def test_data_has_task_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert "task_count" in result["data"]

    def test_data_has_tasks_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert "tasks" in result["data"]
        assert isinstance(result["data"]["tasks"], list)

    def test_data_has_open_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert "open_count" in result["data"]

    def test_data_has_done_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert "done_count" in result["data"]

    def test_no_now_md_returns_ok_no_sprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert result["ok"] is True
        assert result["data"]["now_md_found"] is False
        assert result["data"]["sprint_focus"] is None

    def test_now_md_with_tasks_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "00_HOME"
            home.mkdir()
            (home / "Now.md").write_text(
                "## Current Phase\n- [ ] Task A\n- [x] Task B done\n",
                encoding="utf-8",
            )
            api = _make_api(tmp)
            result = api.get_sprint_focus()
        assert result["ok"] is True
        assert result["data"]["task_count"] == 2
        assert result["data"]["open_count"] == 1
        assert result["data"]["done_count"] == 1
        tasks = result["data"]["tasks"]
        assert any(not t["done"] and "Task A" in t["text"] for t in tasks)
        assert any(t["done"] and "Task B" in t["text"] for t in tasks)

    def test_exception_returns_error_envelope(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "00_HOME").mkdir()
            (tmp_path / "00_HOME" / "Now.md").write_text(
                "## Current Phase\n- [ ] x\n", encoding="utf-8"
            )
            api2 = _make_api(tmp)
            with patch("pathlib.Path.read_text", side_effect=RuntimeError("boom")):
                result = api2.get_sprint_focus()
        assert result["ok"] is False
        assert result["error"]["code"] == "sprint_focus_failed"


# â”€â”€ TestSprintFocusHTML â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"


def _html():
    return HTML_PATH.read_text(encoding="utf-8")


class TestSprintFocusHTML:
    def test_sprint_focus_section_exists(self):
        assert 'id="sprint-focus-section"' in _html()

    def test_sprint_focus_section_class(self):
        assert 'class="sprint-focus-section"' in _html()

    def test_sprint_focus_body_exists(self):
        assert 'id="sprint-focus-body"' in _html()

    def test_sprint_focus_header_exists(self):
        html = _html()
        assert 'sprint-focus-header' in html

    def test_sprint_focus_inside_project_workspace(self):
        html = _html()
        pw_idx = html.find('id="panel-project-workspace"')
        sf_idx = html.find('id="sprint-focus-section"')
        pw_end = html.find('</section>', pw_idx)
        assert pw_idx < sf_idx < pw_end

    def test_sprint_focus_before_workspace_body(self):
        html = _html()
        sf_idx = html.find('id="sprint-focus-section"')
        body_idx = html.find('id="project-workspace-body"')
        assert sf_idx < body_idx


# â”€â”€ TestSprintFocusCSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"


def _css():
    return CSS_PATH.read_text(encoding="utf-8")


class TestSprintFocusCSS:
    def test_sprint_focus_section_class(self):
        assert ".sprint-focus-section" in _css()

    def test_sprint_focus_header_class(self):
        assert ".sprint-focus-header" in _css()

    def test_sprint_focus_body_class(self):
        assert ".sprint-focus-body" in _css()

    def test_sprint_focus_task_class(self):
        assert ".sprint-focus-task" in _css()

    def test_sprint_focus_task_done_class(self):
        assert ".sprint-focus-task--done" in _css()

    def test_sprint_focus_task_check_class(self):
        assert ".sprint-focus-task-check" in _css()

    def test_sprint_focus_task_text_class(self):
        assert ".sprint-focus-task-text" in _css()

    def test_sprint_focus_text_class(self):
        assert ".sprint-focus-text" in _css()

    def test_sprint_focus_empty_class(self):
        assert ".sprint-focus-empty" in _css()


# â”€â”€ TestSprintFocusJS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"


def _js():
    return JS_PATH.read_text(encoding="utf-8")


class TestSprintFocusJS:
    def test_loadSprintFocus_defined(self):
        assert "async function loadSprintFocus()" in _js()

    def test_renderSprintFocusSection_defined(self):
        assert "function renderSprintFocusSection(" in _js()

    def test_sprintFocusLoaded_state_variable(self):
        assert "sprintFocusLoaded" in _js()

    def test_api_get_sprint_focus_called(self):
        assert "get_sprint_focus()" in _js()

    def test_sprint_focus_body_targeted(self):
        assert "sprint-focus-body" in _js()

    def test_sprint_focus_task_rendering(self):
        assert "sprint-focus-task" in _js()

    def test_sprint_focus_task_done_class_applied(self):
        assert "sprint-focus-task--done" in _js()

    def test_panel_switch_wired(self):
        assert "loadSprintFocus()" in _js()
        assert "project-workspace" in _js()

    def test_no_vault_writes_in_sprint_focus(self):
        js = _js()
        assert "save_sprint_focus" not in js
        assert "write_sprint_focus" not in js


# â”€â”€ TestSprintFocusRegistry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TestSprintFocusRegistry:
    def test_project_workspace_has_get_sprint_focus(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert "get_sprint_focus" in panels["project-workspace"]["api_methods"]

    def test_sprint_focus_section_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["sprint_focus_section_mounted"] is True

    def test_project_workspace_still_read_only(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert panels["project-workspace"]["read_only"] is True
        assert panels["project-workspace"]["blocked_authority"]["canonical_mutation"] is False

    def test_next_recommended_pass_updated(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"


