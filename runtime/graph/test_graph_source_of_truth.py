"""Tests for the persisted GraphSnapshot source of truth + its wiring into the
default graph query surface (serve-from-persisted, scan only when stale)."""

from __future__ import annotations

from pathlib import Path

from runtime.graph.graph_models import GraphEdge, GraphNode, GraphSnapshot
from runtime.graph.graph_source_of_truth import (
    persist_snapshot,
    persisted_snapshot_if_fresh,
)


def _snapshot() -> GraphSnapshot:
    nodes = [
        GraphNode(node_id="n1", stable_key="n1", title="n1", label="n1", node_type="doc"),
        GraphNode(node_id="n2", stable_key="n2", title="n2", label="n2", node_type="doc"),
    ]
    edges = [GraphEdge(edge_id="e1", source_node_id="n1", target_node_id="n2", edge_type="explicit_link")]
    return GraphSnapshot.from_nodes_edges(nodes, edges)


def _seed_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "a.md").write_text("# A\n[[B]]\n", encoding="utf-8")
    (notes / "b.md").write_text("# B\n[[A]]\n", encoding="utf-8")
    return vault


def test_persist_then_load_fresh(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SOT_DIR", str(tmp_path / "sot"))
    vault = _seed_vault(tmp_path)
    assert persisted_snapshot_if_fresh(vault) is None  # cold
    assert persist_snapshot(vault, _snapshot()) is True
    loaded = persisted_snapshot_if_fresh(vault)
    assert loaded is not None
    assert loaded.node_count == 2
    assert loaded.edge_count == 1


def test_stale_when_vault_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SOT_DIR", str(tmp_path / "sot"))
    vault = _seed_vault(tmp_path)
    persist_snapshot(vault, _snapshot())
    assert persisted_snapshot_if_fresh(vault) is not None
    # a vault write changes the fingerprint → the persisted snapshot is stale
    (vault / "notes" / "a.md").write_text("# A changed\n[[B]]\nmore\n", encoding="utf-8")
    assert persisted_snapshot_if_fresh(vault) is None


def test_empty_snapshot_not_persisted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CHASEOS_GRAPH_SOT_DIR", str(tmp_path / "sot"))
    vault = _seed_vault(tmp_path)
    empty = GraphSnapshot.from_nodes_edges([], [])
    assert persist_snapshot(vault, empty) is False
    assert persisted_snapshot_if_fresh(vault) is None


def test_surface_serves_from_persisted_snapshot_on_second_load(tmp_path: Path, monkeypatch) -> None:
    """The default graph surface scans on the first load, then serves the
    persisted snapshot (no scan) on the next unchanged load."""
    monkeypatch.setenv("CHASEOS_GRAPH_SOT_DIR", str(tmp_path / "sot"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "sc"))
    monkeypatch.setenv("CHASEOS_GRAPH_PARSE_INDEX_DIR", str(tmp_path / "pidx"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "0")  # isolate the SOT path from the memo
    from runtime.studio.graph_query_surface import build_graph_query_surface

    vault = _seed_vault(tmp_path)

    first = build_graph_query_surface(vault, folder_path="notes", max_nodes=50, max_edges=50)
    assert first["graph_source"]["persisted_graph_snapshot_used"] is False
    assert first["graph_source"]["source_contract_scan_performed"] is True
    assert first["default_graph"]["nodes"]

    second = build_graph_query_surface(vault, folder_path="notes", max_nodes=50, max_edges=50)
    assert second["graph_source"]["persisted_graph_snapshot_used"] is True
    assert second["graph_source"]["active_source"] == "persisted_source_of_truth"
    assert second["graph_source"]["source_contract_scan_performed"] is False
    # same graph is served
    assert len(second["default_graph"]["nodes"]) == len(first["default_graph"]["nodes"])

    # change the vault → next load rescans (and re-persists)
    (vault / "notes" / "a.md").write_text("# A changed\n[[B]]\nnew line\n", encoding="utf-8")
    third = build_graph_query_surface(vault, folder_path="notes", max_nodes=50, max_edges=50)
    assert third["graph_source"]["persisted_graph_snapshot_used"] is False
    assert third["graph_source"]["source_contract_scan_performed"] is True


def test_lens_scene_serves_from_persisted_snapshot(tmp_path: Path, monkeypatch) -> None:
    """open_graph_lens_scene also serves from the persisted snapshot when fresh."""
    monkeypatch.setenv("CHASEOS_GRAPH_SOT_DIR", str(tmp_path / "sot"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_CACHE_DIR", str(tmp_path / "sc"))
    monkeypatch.setenv("CHASEOS_GRAPH_PARSE_INDEX_DIR", str(tmp_path / "pidx"))
    monkeypatch.setenv("CHASEOS_GRAPH_SCAN_MEMO_TTL", "0")
    from runtime.studio.graph_query_surface import open_graph_lens_scene

    vault = _seed_vault(tmp_path)
    first = open_graph_lens_scene(vault, "current_workspace", folder_path="notes", max_nodes=50, max_edges=50)
    assert first["graph_source"]["persisted_graph_snapshot_used"] is False

    second = open_graph_lens_scene(vault, "current_workspace", folder_path="notes", max_nodes=50, max_edges=50)
    assert second["graph_source"]["persisted_graph_snapshot_used"] is True
    assert second["graph_source"]["source_contract_scan_performed"] is False
