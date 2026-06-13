"""P10 Studio MVP navigation IA and route contract tests."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

VAULT_ROOT = Path(__file__).parents[3]
FRONTEND = Path(__file__).parent / "frontend"

MVP_NAV_ORDER = [
    "dashboard",
    "chat",
    "project-workspace",
    # chaser-forge + workflow-packs migrated to Tier A in MVP consolidation
    "chaser-forge",
    "workflow-packs",
    "graph",
    "node-inspector",
    # graph-hygiene added in node-inspector overhaul (Phase E)
    "graph-hygiene",
    "provenance-explorer",
    "intake",
    "acquisition",
    "sic",
    # capture-markdown lives between sic and runtime-cockpit in current Tier A/B layout
    "capture-markdown",
    "runtime-cockpit",
]


class _NavParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.nav_buttons: list[dict[str, str]] = []
        self.panels: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "button" and "nav-btn" in data.get("class", ""):
            self.nav_buttons.append(data)
        if tag == "section" and data.get("id", "").startswith("panel-"):
            self.panels.add(data["id"].removeprefix("panel-"))


def _parse_nav() -> _NavParser:
    parser = _NavParser()
    parser.feed((FRONTEND / "index.html").read_text(encoding="utf-8"))
    return parser


def test_mvp_sidebar_order_starts_with_dashboard_and_declares_core_operator_flow() -> None:
    parser = _parse_nav()
    visible_nav = [item.get("data-panel") for item in parser.nav_buttons]

    assert visible_nav[: len(MVP_NAV_ORDER)] == MVP_NAV_ORDER
    assert visible_nav[0] == "dashboard"
    assert parser.nav_buttons[0].get("aria-current") == "page"


def test_every_mvp_nav_item_has_description_state_help_and_independent_panel() -> None:
    parser = _parse_nav()
    registry = build_native_shell_panel_registry(VAULT_ROOT)
    panels = {panel["id"]: panel for panel in registry["panels"]}

    for nav_item in parser.nav_buttons[: len(MVP_NAV_ORDER)]:
        panel_id = nav_item["data-panel"]
        assert panel_id in panels
        assert panel_id in parser.panels, f"{panel_id} must route to its own panel section"
        assert nav_item.get("aria-label"), panel_id
        assert nav_item.get("data-description"), panel_id
        assert nav_item.get("data-state") in {"live", "read-only", "write-capable", "blocked", "planned"}
        assert nav_item.get("data-help"), panel_id
        assert panels[panel_id].get("plain_english_description"), panel_id
        assert panels[panel_id].get("operator_state") in {"live", "read-only", "write-capable", "blocked", "planned"}


def test_nav_clicks_are_route_backed_pages_not_scroll_only_panel_toggles() -> None:
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert "panelRoutes" in js
    assert "window.location.hash" in js
    assert "hashchange" in js
    assert "history.replaceState" in js
    assert "showPanel(defaultRoutePanel())" in js
    assert re.search(r"function\s+routeForPanel\s*\(", js)
    assert re.search(r"function\s+panelFromRoute\s*\(", js)


def test_stale_skipped_fast_plan_labels_removed_from_shell_navigation() -> None:
    html = (FRONTEND / "index.html").read_text(encoding="utf-8").lower()
    js = (FRONTEND / "app.js").read_text(encoding="utf-8").lower()
    css = (FRONTEND / "styles.css").read_text(encoding="utf-8").lower()

    assert "skipped-fast-plan" not in html
    assert "skipped fast plan" not in html
    assert "skipped-fast-plan" not in js
    assert "skipped fast plan" not in js
    assert "skipped-fast-plan" not in css
    assert "skipped fast plan" not in css


def test_sidebar_css_exposes_active_hover_disabled_planned_and_help_affordances() -> None:
    css = (FRONTEND / "styles.css").read_text(encoding="utf-8")

    for token in [
        ".nav-btn:hover",
        ".nav-btn.active",
        ".nav-btn[disabled]",
        ".nav-btn[data-state=\"planned\"]",
        ".nav-btn[data-state=\"blocked\"]",
        ".nav-help",
        ".nav-btn::after",
    ]:
        assert token in css
