"""Pass 10Z - graph provenance inspector shell/API tests."""

from __future__ import annotations

from pathlib import Path
import sys

VAULT = Path(__file__).resolve().parents[3]
SHELL = Path(__file__).resolve().parent
sys.path.insert(0, str(VAULT))


def test_api_exposes_graph_node_provenance_envelope(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI

    (tmp_path / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    api = StudioAPI(str(tmp_path))

    response = api.get_graph_node_provenance("", "alpha.md", max_nodes=50)

    assert response["ok"] is True
    assert response["surface"] == "graph_node_provenance"
    data = response["data"]
    assert data["surface"] == "studio_graph_provenance_inspector"
    assert data["readiness"]["graph_provenance_inspector_ready"] is True
    assert data["provenance_status"] == "missing"
    assert data["readiness"]["missing_provenance_tolerated"] is True
    assert data["possible_writes"] == []


def test_registry_advances_to_current_phase11_readonly_companion_after_graph_provenance() -> None:
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    registry = build_native_shell_panel_registry(VAULT)
    graph_panel = next(panel for panel in registry["panels"] if panel["id"] == "graph")
    node_panel = next(panel for panel in registry["panels"] if panel["id"] == "node-inspector")

    assert "get_graph_node_provenance" in graph_panel["api_methods"]
    assert "get_graph_node_provenance" in node_panel["api_methods"]
    assert registry["readiness"]["graph_provenance_inspector_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
    assert registry["readiness"]["phase11_chat_companion_status_readonly_ready"] is True
    assert registry["authority"]["possible_writes"] == []


def test_inspector_html_declares_graph_provenance_mount() -> None:
    html = (SHELL / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'data-graph-provenance-inspector="mounted"' in html
    assert 'data-panel-id="node-inspector"' in html


def test_inspector_tabs_hydrate_graph_provenance_contract() -> None:
    js = (SHELL / "frontend" / "inspectorTabs.js").read_text(encoding="utf-8")

    assert "get_graph_node_provenance" in js
    assert "function renderGraphProvenanceInspector(graphProv)" in js
    assert "Graph Provenance Chain" in js
    assert "Generated vs Canonical" in js
    assert "missing_provenance_tolerated" in js


def test_graph_provenance_css_exists() -> None:
    css = (SHELL / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert ".graph-provenance-inspector" in css
    assert ".graph-provenance-chain" in css
    assert ".graph-provenance-step" in css





