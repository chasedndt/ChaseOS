"""Pass 10X - Graph Scanner Parser shell/API tests."""

from __future__ import annotations

from pathlib import Path
import sys

VAULT = Path(__file__).resolve().parents[3]
SHELL = Path(__file__).resolve().parent
sys.path.insert(0, str(VAULT))


def test_api_exposes_graph_scanner_parser_envelope(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI

    (tmp_path / "alpha.md").write_text("# Alpha\n[[Beta]]\n", encoding="utf-8")
    (tmp_path / "beta.md").write_text("# Beta\n", encoding="utf-8")
    api = StudioAPI(str(tmp_path))

    response = api.get_graph_scanner_parser(max_files=20, max_nodes=100)

    assert response["ok"] is True
    assert response["surface"] == "graph_scanner_parser"
    assert response["data"]["readiness"]["parser_backed_graph_input_ready"] is True
    assert response["data"]["graph_scanner_truth"]["parser_backed_graph_input_built"] is True
    assert response["data"]["authority"]["writes_graph_index"] is False
    assert response["data"]["possible_writes"] == []


def test_graph_contract_uses_parser_backed_input(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI

    (tmp_path / "alpha.md").write_text("# Alpha\n[[Beta]]\n", encoding="utf-8")
    (tmp_path / "beta.md").write_text("# Beta\n", encoding="utf-8")
    api = StudioAPI(str(tmp_path))

    response = api.get_graph_contract(max_nodes=100)

    assert response["ok"] is True
    data = response["data"]
    assert data["readiness"]["graph_scanner_parser_ready"] is True
    assert data["readiness"]["parser_backed_graph_input_ready"] is True
    assert data["source_parser"]["surface"] == "studio_graph_scanner_parser"
    assert data["graph_view_truth"]["parser_backed_graph_input_built"] is True


def test_registry_advances_to_phase10y_after_graph_scanner_parser() -> None:
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    registry = build_native_shell_panel_registry(VAULT)
    graph_panel = next(panel for panel in registry["panels"] if panel["id"] == "graph")

    assert "get_graph_scanner_parser" in graph_panel["api_methods"]
    assert registry["readiness"]["graph_scanner_parser_mounted"] is True
    assert registry["readiness"]["parser_backed_graph_input_ready"] is True
    assert registry["readiness"]["typed_graph_trust_overlays_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
    assert registry["authority"]["possible_writes"] == []


def test_graph_panel_contains_parser_summary_target() -> None:
    html = (SHELL / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'id="graph-parser-summary"' in html
    # D3 refactor: status elements now live in graph-status-dock with graph-status-chip class
    assert 'id="graph-status-dock"' in html


def test_graph_frontend_renders_parser_summary() -> None:
    js = (SHELL / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "function renderGraphParserSummary(contract)" in js
    assert "contract.source_parser" in js
    assert "parser_backed_graph_input_ready" in js
    assert "renderGraphParserSummary(contract)" in js
    assert "get_graph_scanner_parser" not in js


def test_graph_frontend_uses_parser_edge_layers_and_node_families() -> None:
    js = (SHELL / "frontend" / "app.js").read_text(encoding="utf-8")

    assert "node_family: visual.node_family || n.node_family || n.node_type" in js
    assert "e.edge_layer || (e.properties || {}).edge_layer || edgeStyleFamily(e.relation)" in js
    assert "relation_layer: layer" in js


def test_graph_parser_summary_css_exists() -> None:
    css = (SHELL / "frontend" / "styles.css").read_text(encoding="utf-8")

    # D3 refactor: individual status overlay rules consolidated into .graph-status-dock/.graph-status-chip
    assert ".graph-status-dock" in css
    assert "text-overflow: ellipsis" in css





