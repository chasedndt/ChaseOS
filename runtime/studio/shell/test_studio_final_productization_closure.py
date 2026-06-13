"""Static checks for Studio final productization closure surfaces."""

from __future__ import annotations

from pathlib import Path


FRONTEND = Path(__file__).parent / "frontend"
INDEX = FRONTEND / "index.html"
APP = FRONTEND / "app.js"
CSS = FRONTEND / "styles.css"


def _html() -> str:
    return INDEX.read_text(encoding="utf-8")


def _js() -> str:
    return APP.read_text(encoding="utf-8")


def _css() -> str:
    return CSS.read_text(encoding="utf-8")


def test_chat_shell_is_product_framed() -> None:
    html = _html()
    js = _js()
    css = _css()

    assert "phase11-chat-shell" in html
    assert "phase11-chat-left-rail" in html
    assert "phase11-chat-main" in html
    assert "Saved conversations with local runtimes" in html
    assert "function _phase11ChatProductDesk" in js
    assert "phase11-chat-product-desk" in js
    assert "phase11-chat-advanced-proof" in js
    assert ".phase11-chat-shell" in css
    assert ".phase11-chat-product-grid" in css


def test_workspaces_surface_uses_product_label_and_hub() -> None:
    html = _html()
    js = _js()
    css = _css()

    assert "<h2>Workspaces</h2>" in html
    assert "Project, client, and context hubs" in html
    assert "workspace-hub-hero" in js
    assert "WORKSPACE HUB" in js
    assert "Workspace Operating Context" in js
    assert "Workspace Readiness" in js
    assert "Workspace Surfaces" in js
    assert "workspace-surface-card" in js
    assert "data-project-workspace-card" in js
    assert "data-workspace-surface" in js
    assert "_wireProjectWorkspaceInspector" in js
    assert "Workspace Domains" in js
    assert ".workspace-hub-hero" in css
    assert ".workspace-context-grid" in css
    assert ".workspace-readiness-grid" in css
    assert ".workspace-surface-grid" in css
    assert ".workspace-domain-board" in css

    workspace_segment = js[
        js.find("function renderProjectWorkspacePanel"):
        js.find("function _readinessTone")
    ]
    for internal_label in (
        "No writes",
        "Vault writes",
        "Provider calls",
        "Model calls",
        "inspection mode",
        "Inspect only",
        "read-only Studio",
    ):
        assert internal_label not in workspace_segment


def test_graph_hygiene_surface_is_review_workspace() -> None:
    html = _html()
    js = _js()
    css = _css()

    assert "Review vault graph issues" in html
    assert "Changes require approval" in html
    assert "graph-hygiene-hero" in js
    assert "GRAPH REVIEW WORKSPACE" in js
    assert "Open Decision Drafts" in js
    assert "Decision Drafts &amp; Execution" not in js
    assert "graph-hygiene-evidence-details" in js
    assert "body.innerHTML = advancedProofHtml" in js
    assert ".graph-hygiene-hero" in css
    assert ".graph-hygiene-workspace-grid" in css


def test_responsive_closure_rules_cover_mobile_shells() -> None:
    css = _css()

    assert "@media (max-width: 900px)" in css
    assert ".phase11-chat-shell" in css
    assert ".workspace-hub-hero" in css
    assert ".graph-hygiene-workspace-grid" in css
    assert "@media (max-width: 560px)" in css
