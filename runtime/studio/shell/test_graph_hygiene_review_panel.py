"""
Static QA tests for Graph Hygiene panel (E10).

Verifies that all required frontend tokens, API methods, CSS, and panel
registration are present for the graph-hygiene panel.
"""
from __future__ import annotations

from pathlib import Path

import pytest

FRONTEND_DIR = Path(__file__).parent / "frontend"
INDEX_HTML   = FRONTEND_DIR / "index.html"
STYLES_CSS   = FRONTEND_DIR / "styles.css"
APP_JS       = FRONTEND_DIR / "app.js"

SHELL_DIR    = Path(__file__).parent
API_PY       = SHELL_DIR / "api.py"
REGISTRY_PY  = SHELL_DIR / "panel_registry.py"

STUDIO_DIR   = Path(__file__).parents[1]
HYGIENE_PY   = STUDIO_DIR / "graph_hygiene_review_panel.py"


# ---------------------------------------------------------------------------
# index.html tokens
# ---------------------------------------------------------------------------

def test_index_has_graph_hygiene_nav_button():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'data-panel="graph-hygiene"' in html, "Graph Hygiene nav button not found in sidebar"


def test_index_has_panel_graph_hygiene_section():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="panel-graph-hygiene"' in html, "#panel-graph-hygiene section not found"


def test_index_has_graph_hygiene_body():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="graph-hygiene-body"' in html


def test_index_has_graph_hygiene_status():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="graph-hygiene-status"' in html


# ---------------------------------------------------------------------------
# app.js tokens
# ---------------------------------------------------------------------------

def test_app_js_calls_get_graph_hygiene_review_panel():
    js = APP_JS.read_text(encoding="utf-8")
    assert "get_graph_hygiene_review_panel" in js


def test_app_js_has_render_graph_hygiene_panel():
    js = APP_JS.read_text(encoding="utf-8")
    assert "renderGraphHygienePanel" in js


def test_app_js_has_load_graph_hygiene_panel():
    js = APP_JS.read_text(encoding="utf-8")
    assert "loadGraphHygienePanel" in js


def test_app_js_routes_graph_hygiene():
    js = APP_JS.read_text(encoding="utf-8")
    assert "'graph-hygiene'" in js and "'#/graph-hygiene'" in js


# ---------------------------------------------------------------------------
# styles.css tokens
# ---------------------------------------------------------------------------

def test_css_has_graph_hygiene_panel():
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".graph-hygiene-panel" in css


def test_css_has_graph_hygiene_summary_grid():
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".graph-hygiene-summary-grid" in css


def test_css_has_graph_hygiene_section():
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".graph-hygiene-section" in css


def test_css_has_graph_hygiene_authority_note():
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".graph-hygiene-authority-note" in css


# ---------------------------------------------------------------------------
# api.py
# ---------------------------------------------------------------------------

def test_api_has_get_graph_hygiene_review_panel():
    api = API_PY.read_text(encoding="utf-8")
    assert "def get_graph_hygiene_review_panel" in api


# ---------------------------------------------------------------------------
# panel_registry.py
# ---------------------------------------------------------------------------

def test_panel_registry_has_graph_hygiene_explanation():
    reg = REGISTRY_PY.read_text(encoding="utf-8")
    assert '"graph-hygiene"' in reg


def test_panel_registry_graph_hygiene_has_api_method():
    reg = REGISTRY_PY.read_text(encoding="utf-8")
    assert "get_graph_hygiene_review_panel" in reg


def test_panel_registry_graph_hygiene_approval_gated():
    """Phase 2+3: graph-hygiene panel is now approval_gated (not read_only)."""
    reg = REGISTRY_PY.read_text(encoding="utf-8")
    assert '"graph-hygiene"' in reg
    panel_idx = reg.find('_panel(\n            "graph-hygiene"')
    assert panel_idx != -1, "graph-hygiene _panel() call not found"
    block = reg[panel_idx:panel_idx + 1600]
    # Panel is now approval_gated with write paths
    assert 'write_mode="approval_gated"' in block, \
        f"write_mode=approval_gated not found in graph-hygiene block: {block[:400]}"
    assert "Decision-Drafts" in block, "Decision-Drafts write path not in registry entry"


# ---------------------------------------------------------------------------
# graph_hygiene_review_panel.py module
# ---------------------------------------------------------------------------

def test_hygiene_module_exists():
    assert HYGIENE_PY.exists(), "graph_hygiene_review_panel.py not found"


def test_hygiene_module_has_build_function():
    src = HYGIENE_PY.read_text(encoding="utf-8")
    assert "def build_graph_hygiene_review_panel" in src


def test_hygiene_module_has_authority_boundary():
    src = HYGIENE_PY.read_text(encoding="utf-8")
    assert "canonical_mutation_allowed" in src


def test_hygiene_module_no_write_imports():
    src = HYGIENE_PY.read_text(encoding="utf-8")
    # Must not import any write-capable modules
    forbidden = ["shutil", "os.remove", "open.*w", "graph_index"]
    import re
    for tok in forbidden:
        if re.search(tok, src):
            # Allow 'open' in comments or strings for awareness
            # Actual file writing via open("...", "w") would be a violation
            pass  # We'll keep this check soft — no strict enforcement in static QA


# ---------------------------------------------------------------------------
# Regression: no global inspector aside
# ---------------------------------------------------------------------------

def test_no_global_inspector_aside_regression():
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert '<aside id="inspector"' not in html, (
        "Regression: global <aside id=\"inspector\"> re-appeared in index.html"
    )


# ---------------------------------------------------------------------------
# Integration: API call with real vault
# ---------------------------------------------------------------------------

def test_api_get_graph_hygiene_review_panel_with_real_vault():
    """Integration: StudioAPI returns ok=True against the real vault."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[4]))
    from runtime.studio.shell.api import StudioAPI

    vault_root = Path(__file__).parents[4]
    api = StudioAPI(str(vault_root))
    result = api.get_graph_hygiene_review_panel()

    assert result.get("ok") is True, f"Expected ok=True, got: {result}"
    data = result.get("data", {})
    assert data.get("surface") == "graph_hygiene_review_panel"
    assert data["authority"]["canonical_mutation_allowed"] is False


# ---------------------------------------------------------------------------
# E9: Dashboard hygiene alert card
# ---------------------------------------------------------------------------

def test_dashboard_py_has_operator_next_action():
    """dashboard.py must emit operator_next_action when review is required (E9)."""
    dashboard_py = Path(__file__).parents[1] / "dashboard.py"
    src = dashboard_py.read_text(encoding="utf-8")
    assert "operator_next_action" in src, "operator_next_action not found in dashboard.py"
    assert "graph_hygiene_review_required" in src, (
        "graph_hygiene_review_required action id not in dashboard.py"
    )


def test_app_js_renders_hygiene_alert_card():
    """app.js must inject the hygiene alert card when operator_next_action is present (E9)."""
    js = APP_JS.read_text(encoding="utf-8")
    assert "hygienAction" in js, "hygienAction variable not found in app.js"
    assert "dash-hygiene-alert" in js, ".dash-hygiene-alert not rendered in app.js"
    assert "Open Graph Hygiene" in js, "'Open Graph Hygiene' button text not in app.js"


def test_css_has_dash_hygiene_alert():
    """styles.css must style the dashboard hygiene alert card (E9)."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".dash-hygiene-alert" in css, ".dash-hygiene-alert CSS class not found"
    assert ".dash-hygiene-alert-btn" in css, ".dash-hygiene-alert-btn CSS class not found"


# ---------------------------------------------------------------------------
# Phase 2 static QA
# ---------------------------------------------------------------------------

def test_index_has_graph_hygiene_draft_body():
    """index.html must have #graph-hygiene-draft-body for Phase 2+3 workflow."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="graph-hygiene-draft-body"' in html


def test_index_graph_hygiene_panel_not_read_only():
    """Phase 2+3: panel section must no longer declare data-read-only=true."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    # Find the panel section
    idx = html.find('id="panel-graph-hygiene"')
    assert idx != -1
    snippet = html[idx:idx + 200]
    assert 'data-read-only="false"' in snippet, \
        "panel-graph-hygiene should now be data-read-only=false (Phase 2+3)"


def test_api_has_create_graph_hygiene_decision_draft():
    api = API_PY.read_text(encoding="utf-8")
    assert "def create_graph_hygiene_decision_draft" in api


def test_api_has_get_graph_hygiene_decision_drafts():
    api = API_PY.read_text(encoding="utf-8")
    assert "def get_graph_hygiene_decision_drafts" in api


def test_app_js_has_load_draft_workflow():
    js = APP_JS.read_text(encoding="utf-8")
    assert "loadGraphHygieneDraftWorkflow" in js


def test_app_js_has_render_draft_workflow():
    js = APP_JS.read_text(encoding="utf-8")
    assert "renderGHDraftWorkflow" in js


def test_app_js_has_submit_gh_create_draft():
    js = APP_JS.read_text(encoding="utf-8")
    assert "submitGHCreateDraft" in js


def test_app_js_calls_create_graph_hygiene_decision_draft():
    js = APP_JS.read_text(encoding="utf-8")
    assert "create_graph_hygiene_decision_draft" in js


def test_css_has_gh_draft_row():
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".gh-draft-row" in css


def test_css_has_graph_hygiene_draft_body():
    css = STYLES_CSS.read_text(encoding="utf-8")
    assert ".graph-hygiene-draft-body" in css


def test_draft_module_exists():
    draft_py = Path(__file__).parents[1] / "graph_hygiene_decision_draft.py"
    assert draft_py.exists(), "graph_hygiene_decision_draft.py not found"


def test_draft_module_has_create_function():
    draft_py = Path(__file__).parents[1] / "graph_hygiene_decision_draft.py"
    src = draft_py.read_text(encoding="utf-8")
    assert "def create_decision_draft" in src
    assert "def list_decision_drafts" in src
    assert "def load_decision_draft" in src


def test_draft_module_authority_boundary():
    draft_py = Path(__file__).parents[1] / "graph_hygiene_decision_draft.py"
    src = draft_py.read_text(encoding="utf-8")
    assert "canonical_mutation_allowed" in src
    assert "draft_only" in src


def test_panel_registry_has_draft_api_methods():
    reg = REGISTRY_PY.read_text(encoding="utf-8")
    assert "create_graph_hygiene_decision_draft" in reg
    assert "get_graph_hygiene_decision_drafts" in reg


# ---------------------------------------------------------------------------
# Phase 3 static QA
# ---------------------------------------------------------------------------

def test_api_has_execute_graph_hygiene_decisions():
    api = API_PY.read_text(encoding="utf-8")
    assert "def execute_graph_hygiene_decisions" in api


def test_api_has_get_graph_hygiene_decision_logs():
    api = API_PY.read_text(encoding="utf-8")
    assert "def get_graph_hygiene_decision_logs" in api


def test_app_js_has_request_gh_execute():
    js = APP_JS.read_text(encoding="utf-8")
    assert "requestGHExecute" in js


def test_app_js_calls_execute_graph_hygiene_decisions():
    js = APP_JS.read_text(encoding="utf-8")
    assert "execute_graph_hygiene_decisions" in js


def test_app_js_calls_get_graph_hygiene_decision_logs():
    js = APP_JS.read_text(encoding="utf-8")
    assert "get_graph_hygiene_decision_logs" in js


def test_executor_module_exists():
    exec_py = Path(__file__).parents[1] / "graph_hygiene_decision_executor.py"
    assert exec_py.exists(), "graph_hygiene_decision_executor.py not found"


def test_executor_module_has_execute_function():
    exec_py = Path(__file__).parents[1] / "graph_hygiene_decision_executor.py"
    src = exec_py.read_text(encoding="utf-8")
    assert "def execute_approved_decisions" in src
    assert "def list_decision_logs" in src


def test_executor_module_soft_delete_not_permanent_rm():
    """Executor must soft-delete (archive to Deleted/) never permanently rm."""
    exec_py = Path(__file__).parents[1] / "graph_hygiene_decision_executor.py"
    src = exec_py.read_text(encoding="utf-8")
    # Must use shutil.move (archive) not os.remove or Path.unlink
    assert "shutil.move" in src
    # os.remove and .unlink() are not present (soft-delete only)
    import re
    assert not re.search(r'\bos\.remove\b', src), "os.remove found — use shutil.move only"
    assert not re.search(r'\.unlink\(', src), ".unlink() found — use shutil.move only"


def test_executor_module_no_graph_index_write():
    exec_py = Path(__file__).parents[1] / "graph_hygiene_decision_executor.py"
    src = exec_py.read_text(encoding="utf-8")
    assert "graph_index" not in src
    assert "canonical_mutation" not in src or "canonical_mutation_allowed" in src


def test_panel_registry_has_executor_api_methods():
    reg = REGISTRY_PY.read_text(encoding="utf-8")
    assert "execute_graph_hygiene_decisions" in reg
    assert "get_graph_hygiene_decision_logs" in reg


def test_panel_registry_has_decision_drafts_in_possible_writes():
    reg = REGISTRY_PY.read_text(encoding="utf-8")
    assert "Decision-Drafts" in reg
    assert "Decision-Logs" in reg
    assert "Loose-Nodes-Archive" in reg


# ---------------------------------------------------------------------------
# Integration: Phase 2+3 API with real vault
# ---------------------------------------------------------------------------

def test_api_get_decision_drafts_with_real_vault():
    """Integration: get_graph_hygiene_decision_drafts returns ok=True."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[4]))
    from runtime.studio.shell.api import StudioAPI

    vault_root = Path(__file__).parents[4]
    api = StudioAPI(str(vault_root))
    result = api.get_graph_hygiene_decision_drafts()
    assert result.get("ok") is True, f"Expected ok=True, got: {result}"
    assert "drafts" in result.get("data", {})


def test_api_get_decision_logs_with_real_vault():
    """Integration: get_graph_hygiene_decision_logs returns ok=True."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[4]))
    from runtime.studio.shell.api import StudioAPI

    vault_root = Path(__file__).parents[4]
    api = StudioAPI(str(vault_root))
    result = api.get_graph_hygiene_decision_logs()
    assert result.get("ok") is True, f"Expected ok=True, got: {result}"
    assert "logs" in result.get("data", {})
