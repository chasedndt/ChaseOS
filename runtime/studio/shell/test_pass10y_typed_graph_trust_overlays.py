"""Pass 10Y - typed graph and trust overlay shell/API tests."""

from __future__ import annotations

from pathlib import Path
import sys

VAULT = Path(__file__).resolve().parents[3]
SHELL = Path(__file__).resolve().parent
sys.path.insert(0, str(VAULT))


def test_api_exposes_graph_visual_overlay_envelope(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI

    (tmp_path / "alpha.generated.md").write_text("# Alpha\n[[Beta]]\n", encoding="utf-8")
    (tmp_path / "beta.md").write_text("---\nstatus: canonical\n---\n# Beta\n", encoding="utf-8")
    api = StudioAPI(str(tmp_path))

    response = api.get_graph_visual_overlays(max_nodes=100)

    assert response["ok"] is True
    assert response["surface"] == "graph_visual_overlays"
    data = response["data"]
    assert data["readiness"]["typed_graph_trust_overlays_ready"] is True
    assert data["readiness"]["all_14_node_families_available"] is True
    assert data["readiness"]["all_4_edge_layers_available"] is True
    assert data["readiness"]["all_8_trust_states_available"] is True
    assert data["possible_writes"] == []


def test_graph_contract_includes_visual_overlay_model(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI

    (tmp_path / "alpha.md").write_text("# Alpha\n[[Beta]]\n", encoding="utf-8")
    (tmp_path / "beta.md").write_text("# Beta\n", encoding="utf-8")
    api = StudioAPI(str(tmp_path))

    response = api.get_graph_contract(max_nodes=100)

    assert response["ok"] is True
    data = response["data"]
    overlays = data["view_model"]["visual_overlays"]
    assert overlays["coverage"]["all_14_node_families_available"] is True
    assert overlays["coverage"]["all_4_edge_layers_available"] is True
    assert overlays["coverage"]["all_8_trust_states_available"] is True
    assert data["readiness"]["typed_graph_trust_overlays_ready"] is True
    assert data["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert "node_families" in data["view_model"]["legend"]
    assert "edge_layers" in data["view_model"]["legend"]
    assert "trust_states" in data["view_model"]["legend"]


def test_registry_advances_to_phase10aa_after_graph_provenance() -> None:
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    registry = build_native_shell_panel_registry(VAULT)
    graph_panel = next(panel for panel in registry["panels"] if panel["id"] == "graph")

    assert "get_graph_visual_overlays" in graph_panel["api_methods"]
    assert registry["readiness"]["typed_graph_trust_overlays_mounted"] is True
    assert registry["readiness"]["graph_provenance_inspector_mounted"] is True
    assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
    assert registry["authority"]["possible_writes"] == []


def test_graph_panel_contains_edge_layer_and_overlay_targets() -> None:
    html = (SHELL / "frontend" / "index.html").read_text(encoding="utf-8")

    assert 'id="edge-layer-filters"' in html
    assert 'id="graph-overlay-summary"' in html
    # D3 refactor: status chips now share graph-status-chip class inside graph-status-dock
    assert 'class="graph-status-chip"' in html


def test_graph_frontend_renders_visual_overlay_contract() -> None:
    js = (SHELL / "frontend" / "app.js").read_text(encoding="utf-8")
    styles_js = (SHELL / "frontend" / "graphStyles.js").read_text(encoding="utf-8")

    assert "nodeVisualMap" in js
    assert "edgeVisualMap" in js
    assert "function renderGraphOverlaySummary(contract)" in js
    assert "graphFilters.edgeLayers" in js
    assert "content--generated" in js
    assert "content--canonical" in js
    assert "data(display_label)" in styles_js
    assert "normalizeEdgeLayer" in styles_js
    assert "runtime-action" in styles_js


def test_graph_overlay_css_exists() -> None:
    css = (SHELL / "frontend" / "styles.css").read_text(encoding="utf-8")

    # D3 refactor: .graph-overlay-summary consolidated into .graph-status-chip inside .graph-status-dock
    assert ".graph-status-chip" in css
    assert ".legend-node-swatch" in css
    assert ".legend-trust-ring" in css





