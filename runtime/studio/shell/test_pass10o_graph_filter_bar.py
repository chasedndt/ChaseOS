"""Pass 10O - Graph Filter Bar tests.

Tests the read-only, Cytoscape-side graph filter bar. This pass adds no backend
API and no graph/node write authority.
"""

from __future__ import annotations

import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(VAULT))

HTML_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "index.html"
JS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "app.js"
CSS_PATH = VAULT / "runtime" / "studio" / "shell" / "frontend" / "styles.css"


def _html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


def _js() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


class TestGraphFilterBarHTML:
    def test_graph_product_header_exists(self):
        html = _html()
        assert 'class="graph-product-header"' in html
        assert 'id="graph-quick-switch-btn"' in html
        assert 'id="graph-filter-toggle"' in html
        assert 'class="graph-focus-controls"' in html
        assert 'data-graph-focus-depth="0"' in html
        assert 'data-graph-focus-depth="1"' in html
        assert 'data-graph-focus-depth="2"' in html
        assert 'id="graph-open-inspector"' in html

    def test_graph_filter_panel_is_inline_bar(self):
        html = _html()
        assert 'id="graph-filter-panel"' in html
        assert 'class="graph-filter-bar"' in html

    def test_graph_filter_panel_is_hidden_by_default(self):
        html = _html()
        start = html.index('id="graph-filter-panel"')
        fragment = html[start:html.index('>', start)]
        assert "hidden" in fragment

    def test_graph_filter_reset_exists(self):
        assert 'id="graph-filter-reset"' in _html()

    def test_node_type_filters_exist(self):
        assert 'id="node-type-filters"' in _html()

    def test_trust_state_filters_exist(self):
        assert 'id="trust-state-filters"' in _html()

    def test_domain_filters_exist(self):
        assert 'id="domain-filters"' in _html()

    def test_relation_filters_preserved(self):
        assert 'id="relation-filters"' in _html()


class TestGraphFilterBarJS:
    def test_graph_product_chrome_wired(self):
        js = _js()
        assert "function initGraphProductChrome()" in js
        assert "routeButton('graph-open-inspector', 'node-inspector')" in js
        assert "routeButton('graph-open-hygiene', 'graph-hygiene')" in js
        assert "routeButton('graph-open-provenance', 'provenance-explorer')" in js

    def test_graph_filter_toggle_updates_aria_state(self):
        js = _js()
        assert "function syncGraphFilterToggleState()" in js
        assert "filterToggle.setAttribute('aria-expanded'" in js
        assert "function toggleGraphFilterPanel()" in js

    def test_graph_local_focus_controls_are_wired(self):
        js = _js()
        assert "function setGraphLocalFocusDepth(depth)" in js
        assert "function syncGraphLocalFocusControls()" in js
        assert "_graphLocalFocusDepthOverride" in js
        assert "document.querySelectorAll('[data-graph-focus-depth]')" in js

    def test_selected_node_updates_object_inspector(self):
        js = _js()
        assert "function renderObjectInspectorNodeContext(context)" in js
        assert "renderObjectInspectorNodeContext(graphNodeContext(node))" in js
        assert "objectActionButton('focus-graph'" in js
        assert "objectActionButton('copy-ref'" in js

    def test_graph_filters_has_domains_set(self):
        assert "domains: new Set()" in _js()

    def test_infer_node_domain_defined(self):
        assert "function inferNodeDomain(node)" in _js()

    def test_domain_legend_defined(self):
        assert "function buildDomainLegend(nodes)" in _js()

    def test_build_elements_adds_domain_to_node_data(self):
        assert "domain: inferNodeDomain(n)" in _js()

    def test_render_graph_controls_builds_domain_legend(self):
        js = _js()
        assert "const domains = buildDomainLegend(nodes)" in js
        assert "renderFilterGroup('domain-filters', domains, graphFilters.domains, 'domain')" in js

    def test_domain_filter_events_route_to_domain_set(self):
        assert "kind === 'domain' ? graphFilters.domains" in _js()

    def test_reset_restores_domain_filters(self):
        assert "graphFilters.domains = new Set(domains.map(item => item.id))" in _js()

    def test_node_matches_filters_checks_domain(self):
        assert "graphFilters.domains.has(data.domain || 'unknown')" in _js()

    def test_apply_graph_filters_uses_graph3d(self):
        js = _js()
        assert "function applyGraphFilters()" in js
        assert "graph3d.graphData(" in js

    def test_no_new_graph_filter_api_call(self):
        js = _js()
        assert "get_graph_filter" not in js
        assert "save_graph_filter" not in js


class TestGraphFilterBarCSS:
    def test_graph_filter_bar_class_exists(self):
        assert ".graph-filter-bar" in _css()

    def test_graph_focus_and_object_inspector_styles_exist(self):
        css = _css()
        assert ".graph-focus-controls" in css
        assert ".graph-focus-btn" in css
        assert ".object-inspector-node" in css
        assert ".object-inspector-button-grid" in css

    def test_graph_filter_panel_spans_canvas_width(self):
        css = _css()
        assert "#graph-filter-panel" in css
        assert "right: 8px" in css

    def test_filter_options_are_row_chips(self):
        css = _css()
        assert "flex-direction: row" in css
        assert "border-radius: 999px" in css

    def test_filter_option_inputs_preserved(self):
        assert ".filter-option input" in _css()

    def test_theme_vars_are_defined_shell_vars(self):
        block = _css()[_css().index("#graph-filter-panel"):_css().index("#graph-legend")]
        assert "var(--bg-surface)" in block
        assert "var(--border)" in block
        assert "var(--bg-raised)" in block
        assert "var(--accent)" in block


class TestGraphFilterBarRegistry:
    def test_registry_marks_graph_filter_bar_mounted(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        assert registry["readiness"]["graph_filter_bar_mounted"] is True
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"

    def test_registry_keeps_graph_panel_approval_gated_without_direct_authority(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

        registry = build_native_shell_panel_registry(VAULT)
        panels = {panel["id"]: panel for panel in registry["panels"]}
        assert panels["graph"]["read_only"] is False
        assert panels["graph"]["write_mode"] == "approval_gated"
        assert panels["graph"]["possible_writes"] == [
            "create_node_approval_request",
            "visual_link_approval_request",
        ]
        assert panels["graph"]["blocked_authority"]["graph_index_writes"] is False
        assert panels["graph"]["blocked_authority"]["node_editing"] is False
