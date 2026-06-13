"""
test_studio_graph_view.py — Tests for Studio Graph View Layer

Covers:
  TestInspectNodeNoSnapshot  (3 tests) — error model when no snapshot
  TestInspectNode            (6 tests) — node inspector with real snapshot
  TestSearchNodes            (5 tests) — label search + type filter
  TestGetCommunity           (4 tests) — community model
  TestGetGraphStats          (5 tests) — stats model
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.graph.artifact import GraphNode, GraphEdge, GraphSnapshot
from runtime.graph.builder import save_snapshot
from runtime.studio.graph_view import (
    get_community,
    get_graph_stats,
    inspect_node,
    search_nodes,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "07_LOGS" / "Graph-Snapshots").mkdir(parents=True)
    return vault


def _make_node(node_id: str, label: str, node_type: str = "function",
               domain: str = "aor", confidence: str = "EXTRACTED") -> GraphNode:
    return GraphNode(
        node_id=node_id,
        label=label,
        node_type=node_type,
        source_file="runtime/aor/engine.py",
        source_line=1,
        domain=domain,
        project=None,
        properties={},
        confidence=confidence,
        provenance="test",
    )


def _make_edge(edge_id: str, source_id: str, target_id: str,
               relation: str = "CALLS", confidence: str = "EXTRACTED") -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        confidence=confidence,
        properties={},
        provenance="test",
    )


def _make_snapshot(vault: Path, nodes=None, edges=None, community_assignments=None) -> GraphSnapshot:
    snap = GraphSnapshot(
        snapshot_id="test-snap-001",
        created_at="2026-04-29T12:00:00Z",
        vault_root=str(vault),
        extraction_scope=["runtime/"],
        nodes=nodes or [],
        edges=edges or [],
        community_assignments=community_assignments or {},
        build_info={"errors": []},
        metadata={},
    )
    snapshot_dir = vault / "07_LOGS" / "Graph-Snapshots"
    save_snapshot(snap, snapshot_dir)
    return snap


# ── TestInspectNodeNoSnapshot ─────────────────────────────────────────────────

class TestInspectNodeNoSnapshot:
    def test_returns_error_model_when_no_snapshot(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_node(vault, "any-node-id")
        assert result["ok"] is False
        assert "No graph snapshot" in result["error"]
        assert result["surface"] == "studio_node_inspector"

    def test_error_model_contains_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_node(vault, "any-node-id")
        assert result["boundary"]["canonical_mutation_allowed"] is False
        assert result["boundary"]["writes_vault"] is False

    def test_search_returns_error_when_no_snapshot(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = search_nodes(vault, "anything")
        assert result["ok"] is False
        assert result["surface"] == "studio_graph_search"


# ── TestInspectNode ───────────────────────────────────────────────────────────

class TestInspectNode:
    def test_returns_node_model_for_known_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "run_engine")]
        _make_snapshot(vault, nodes=nodes)
        result = inspect_node(vault, "n1")
        assert result["ok"] is True
        assert result["node"]["id"] == "n1"
        assert result["node"]["label"] == "run_engine"

    def test_returns_error_for_unknown_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_snapshot(vault, nodes=[_make_node("n1", "run_engine")])
        result = inspect_node(vault, "nonexistent-node")
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_includes_outgoing_edges(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "caller"), _make_node("n2", "callee")]
        edges = [_make_edge("e1", "n1", "n2")]
        _make_snapshot(vault, nodes=nodes, edges=edges)
        result = inspect_node(vault, "n1")
        assert result["ok"] is True
        assert len(result["edges"]) == 1
        assert result["edges"][0]["relation"] == "CALLS"

    def test_includes_incoming_edges(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "base"), _make_node("n2", "user")]
        edges = [_make_edge("e1", "n2", "n1")]
        _make_snapshot(vault, nodes=nodes, edges=edges)
        result = inspect_node(vault, "n1")
        assert len(result["edges"]) == 1
        assert result["edges"][0]["source"] == "n2"

    def test_includes_neighbors(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "hub"), _make_node("n2", "spoke")]
        edges = [_make_edge("e1", "n1", "n2")]
        _make_snapshot(vault, nodes=nodes, edges=edges)
        result = inspect_node(vault, "n1")
        assert result["neighbor_count"] == 1
        assert result["neighbors"][0]["id"] == "n2"

    def test_node_confidence_in_model(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "inferred_fn", confidence="INFERRED")]
        _make_snapshot(vault, nodes=nodes)
        result = inspect_node(vault, "n1")
        assert result["node"]["confidence"] == "INFERRED"


# ── TestSearchNodes ───────────────────────────────────────────────────────────

class TestSearchNodes:
    def test_finds_node_by_label_substring(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [
            _make_node("n1", "run_engine"),
            _make_node("n2", "build_snapshot"),
        ]
        _make_snapshot(vault, nodes=nodes)
        result = search_nodes(vault, "engine")
        assert result["ok"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["id"] == "n1"

    def test_case_insensitive_search(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "RunEngine")]
        _make_snapshot(vault, nodes=nodes)
        result = search_nodes(vault, "runengine")
        assert len(result["results"]) == 1

    def test_empty_query_returns_all_up_to_limit(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node(f"n{i}", f"func_{i}") for i in range(5)]
        _make_snapshot(vault, nodes=nodes)
        result = search_nodes(vault, "", limit=3)
        assert result["result_count"] == 3

    def test_node_type_filter(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [
            _make_node("n1", "MyClass", node_type="class"),
            _make_node("n2", "my_func", node_type="function"),
        ]
        _make_snapshot(vault, nodes=nodes)
        result = search_nodes(vault, "", node_type="class")
        ids = [r["id"] for r in result["results"]]
        assert "n1" in ids
        assert "n2" not in ids

    def test_no_match_returns_empty_results(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "run_engine")]
        _make_snapshot(vault, nodes=nodes)
        result = search_nodes(vault, "xyznotfound")
        assert result["result_count"] == 0
        assert result["results"] == []


# ── TestGetCommunity ──────────────────────────────────────────────────────────

class TestGetCommunity:
    def test_returns_community_members(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "a"), _make_node("n2", "b"), _make_node("n3", "c")]
        assignments = {"n1": 0, "n2": 0, "n3": 1}
        _make_snapshot(vault, nodes=nodes, community_assignments=assignments)
        result = get_community(vault, 0)
        assert result["ok"] is True
        ids = {m["id"] for m in result["members"]}
        assert ids == {"n1", "n2"}
        assert result["member_count"] == 2

    def test_cross_domain_edges_included(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "a"), _make_node("n2", "b")]
        edges = [_make_edge("e1", "n1", "n2")]
        assignments = {"n1": 0, "n2": 1}
        _make_snapshot(vault, nodes=nodes, edges=edges, community_assignments=assignments)
        result = get_community(vault, 0)
        assert result["cross_domain_edge_count"] == 1

    def test_nonexistent_community_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_snapshot(vault)
        result = get_community(vault, 999)
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_no_snapshot_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_community(vault, 0)
        assert result["ok"] is False


# ── TestGetGraphStats ─────────────────────────────────────────────────────────

class TestGetGraphStats:
    def test_returns_node_and_edge_counts(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node("n1", "a"), _make_node("n2", "b")]
        edges = [_make_edge("e1", "n1", "n2")]
        _make_snapshot(vault, nodes=nodes, edges=edges)
        result = get_graph_stats(vault)
        assert result["ok"] is True
        assert result["node_count"] == 2
        assert result["edge_count"] == 1

    def test_confidence_breakdown(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [
            _make_node("n1", "a", confidence="EXTRACTED"),
            _make_node("n2", "b", confidence="INFERRED"),
        ]
        _make_snapshot(vault, nodes=nodes)
        result = get_graph_stats(vault)
        assert result["confidence_breakdown"]["EXTRACTED"] == 1
        assert result["confidence_breakdown"]["INFERRED"] == 1

    def test_node_type_breakdown(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [
            _make_node("n1", "a", node_type="class"),
            _make_node("n2", "b", node_type="class"),
            _make_node("n3", "c", node_type="function"),
        ]
        _make_snapshot(vault, nodes=nodes)
        result = get_graph_stats(vault)
        assert result["node_type_breakdown"]["class"] == 2
        assert result["node_type_breakdown"]["function"] == 1

    def test_top_nodes_by_degree(self, tmp_path):
        vault = _make_vault(tmp_path)
        nodes = [_make_node(f"n{i}", f"fn_{i}") for i in range(4)]
        # n0 is a hub — connects to n1, n2, n3
        edges = [
            _make_edge("e1", "n0", "n1"),
            _make_edge("e2", "n0", "n2"),
            _make_edge("e3", "n0", "n3"),
        ]
        _make_snapshot(vault, nodes=nodes, edges=edges)
        result = get_graph_stats(vault)
        top_ids = [n["id"] for n in result["top_nodes_by_degree"]]
        assert "n0" == top_ids[0]

    def test_no_snapshot_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_graph_stats(vault)
        assert result["ok"] is False
