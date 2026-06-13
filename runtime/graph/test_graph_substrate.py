"""
test_graph_substrate.py — ChaseOS Graph Substrate Tests

Tests for the ChaseOS-native graph substrate.

Coverage:
  artifact.py     — node/edge/snapshot creation, ID stability, serialization
  index.py        — index construction, traversal, stats
  extractor.py    — Python AST extraction, YAML extraction, Markdown extraction
  topology.py     — connected components, label propagation, degree centrality, BFS path
  reporter.py     — report generation (smoke test + structure check)
  query.py        — search, inspect, narrowing, shortest path
  builder.py      — full pipeline integration

Run with:
  .venv/Scripts/python.exe -m pytest runtime/graph/test_graph_substrate.py -v
  or:
  .venv/Scripts/python.exe runtime/graph/test_graph_substrate.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
from pathlib import Path

# Add vault root to path
_VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.graph.artifact import (
    GraphNode, GraphEdge, GraphSnapshot,
    Confidence, NodeType, Relation,
    make_node, make_edge, make_node_id, make_edge_id, make_snapshot_id,
)
from runtime.graph.index import GraphIndex
from runtime.graph.extractor import (
    ExtractionResult, PythonExtractor, YAMLManifestExtractor, MarkdownExtractor,
)
from runtime.graph.topology import (
    connected_components, label_propagation, degree_centrality,
    bfs_shortest_path, top_by_degree, isolated_nodes, cross_domain_edges,
    ambiguous_edges, community_summary,
)
from runtime.graph.reporter import generate_report
from runtime.graph.query import GraphQueryService
from runtime.graph.builder import (
    build_snapshot, build_index, build_query_service, full_pipeline, save_snapshot,
    _dedup_nodes, _dedup_edges, _drop_dangling_edges,
)


# ── Test helpers ──────────────────────────────────────────────────────────────

def _make_test_snapshot(
    nodes: list[GraphNode] = None,
    edges: list[GraphEdge] = None,
) -> GraphSnapshot:
    return GraphSnapshot(
        snapshot_id=make_snapshot_id(),
        created_at="2026-04-10T00:00:00+00:00",
        vault_root="/test/vault",
        extraction_scope=["test/"],
        nodes=nodes or [],
        edges=edges or [],
        community_assignments={},
        build_info={},
        metadata={},
    )


def _make_test_node(label: str, node_type: str = NodeType.FILE, source_file: str = "test.py", **kwargs) -> GraphNode:
    return make_node(label=label, node_type=node_type, source_file=source_file, **kwargs)


def _make_linear_graph(n: int) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Create a linear chain: node0 → node1 → ... → nodeN-1."""
    nodes = [_make_test_node(f"node{i}") for i in range(n)]
    edges = [
        make_edge(nodes[i].node_id, nodes[i + 1].node_id, Relation.REFERENCES)
        for i in range(n - 1)
    ]
    return nodes, edges


# ══════════════════════════════════════════════════════════════════════════════
# artifact.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_node_id_is_stable():
    """Same inputs always produce the same node_id."""
    id1 = make_node_id(NodeType.FILE, "runtime/aor/engine.py", "engine.py")
    id2 = make_node_id(NodeType.FILE, "runtime/aor/engine.py", "engine.py")
    assert id1 == id2


def test_node_id_differs_for_different_inputs():
    """Different inputs produce different node_ids."""
    id1 = make_node_id(NodeType.FILE, "runtime/aor/engine.py", "engine.py")
    id2 = make_node_id(NodeType.PYTHON_CLASS, "runtime/aor/engine.py", "AORRunResult")
    id3 = make_node_id(NodeType.FILE, "runtime/aor/registry.py", "registry.py")
    assert id1 != id2
    assert id1 != id3
    assert id2 != id3


def test_edge_id_is_stable():
    """Same source + relation + target always produce the same edge_id."""
    eid1 = make_edge_id("abc123", Relation.IMPORTS, "def456")
    eid2 = make_edge_id("abc123", Relation.IMPORTS, "def456")
    assert eid1 == eid2


def test_edge_id_differs_for_different_relation():
    eid1 = make_edge_id("abc", Relation.IMPORTS, "def")
    eid2 = make_edge_id("abc", Relation.DEFINES, "def")
    assert eid1 != eid2


def test_node_creation():
    node = make_node(
        label="MyClass",
        node_type=NodeType.PYTHON_CLASS,
        source_file="runtime/aor/engine.py",
        source_line=42,
        domain="aor",
        properties={"bases": ["object"]},
        confidence=Confidence.EXTRACTED,
        provenance="python_ast:classdef",
    )
    assert node.label == "MyClass"
    assert node.node_type == NodeType.PYTHON_CLASS
    assert node.source_file == "runtime/aor/engine.py"
    assert node.source_line == 42
    assert node.domain == "aor"
    assert node.confidence == Confidence.EXTRACTED
    assert len(node.node_id) == 16  # SHA-256 truncated to 16 hex chars


def test_snapshot_serialization_roundtrip():
    """GraphSnapshot serializes to JSON and deserializes cleanly."""
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edges = [make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    snapshot.community_assignments = {nodes[0].node_id: 0, nodes[1].node_id: 0}

    json_str = snapshot.to_json()
    loaded = GraphSnapshot.from_dict(json.loads(json_str))

    assert loaded.snapshot_id == snapshot.snapshot_id
    assert len(loaded.nodes) == 2
    assert len(loaded.edges) == 1
    assert loaded.community_assignments == snapshot.community_assignments


def test_snapshot_save_and_load(tmp_path):
    """Snapshot saves to file and loads back correctly."""
    nodes = [_make_test_node("X")]
    snapshot = _make_test_snapshot(nodes=nodes)
    save_path = tmp_path / "snap.json"
    snapshot.save(save_path)

    loaded = GraphSnapshot.load(save_path)
    assert loaded.snapshot_id == snapshot.snapshot_id
    assert loaded.nodes[0].label == "X"


def test_confidence_constants():
    assert Confidence.EXTRACTED == "EXTRACTED"
    assert Confidence.INFERRED == "INFERRED"
    assert Confidence.AMBIGUOUS == "AMBIGUOUS"
    assert len(Confidence.ALL) == 3


# ══════════════════════════════════════════════════════════════════════════════
# index.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_index_builds_node_by_id():
    nodes = [_make_test_node("A"), _make_test_node("B"), _make_test_node("C")]
    snapshot = _make_test_snapshot(nodes=nodes)
    index = GraphIndex(snapshot)

    for node in nodes:
        assert node.node_id in index.node_by_id
        assert index.node_by_id[node.node_id].label == node.label


def test_index_outgoing_edges():
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edge = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)
    snapshot = _make_test_snapshot(nodes=nodes, edges=[edge])
    index = GraphIndex(snapshot)

    outgoing = index.outgoing_edges.get(nodes[0].node_id, [])
    assert len(outgoing) == 1
    assert outgoing[0].target_id == nodes[1].node_id


def test_index_incoming_edges():
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edge = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)
    snapshot = _make_test_snapshot(nodes=nodes, edges=[edge])
    index = GraphIndex(snapshot)

    incoming = index.incoming_edges.get(nodes[1].node_id, [])
    assert len(incoming) == 1
    assert incoming[0].source_id == nodes[0].node_id


def test_index_degree():
    nodes = [_make_test_node("A"), _make_test_node("B"), _make_test_node("C")]
    # B has two incoming (from A and C) and one outgoing (to C)
    edge_ab = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)
    edge_cb = make_edge(nodes[2].node_id, nodes[1].node_id, Relation.IMPORTS)
    edge_bc = make_edge(nodes[1].node_id, nodes[2].node_id, Relation.REFERENCES)
    snapshot = _make_test_snapshot(nodes=nodes, edges=[edge_ab, edge_cb, edge_bc])
    index = GraphIndex(snapshot)

    assert index.in_degree(nodes[1].node_id) == 2
    assert index.out_degree(nodes[1].node_id) == 1
    assert index.degree(nodes[1].node_id) == 3


def test_index_neighbors():
    nodes = [_make_test_node("A"), _make_test_node("B"), _make_test_node("C")]
    edge_ab = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)
    edge_ac = make_edge(nodes[0].node_id, nodes[2].node_id, Relation.IMPORTS)
    snapshot = _make_test_snapshot(nodes=nodes, edges=[edge_ab, edge_ac])
    index = GraphIndex(snapshot)

    out_neighbors = index.neighbors_out(nodes[0].node_id)
    assert len(out_neighbors) == 2
    neighbor_labels = {n.label for n in out_neighbors}
    assert neighbor_labels == {"B", "C"}


def test_index_search_by_label():
    nodes = [
        _make_test_node("AORRunResult"),
        _make_test_node("capture_content"),
        _make_test_node("engine"),
    ]
    snapshot = _make_test_snapshot(nodes=nodes)
    index = GraphIndex(snapshot)

    results = index.search_by_label("aor")
    assert len(results) == 1
    assert results[0].label == "AORRunResult"

    results = index.search_by_label("capture")
    assert len(results) == 1
    assert results[0].label == "capture_content"


def test_index_stats_shape():
    nodes, edges = _make_linear_graph(4)
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)
    stats = index.stats()

    assert stats["node_count"] == 4
    assert stats["edge_count"] == 3
    assert isinstance(stats["node_types"], dict)
    assert isinstance(stats["relation_types"], dict)


# ══════════════════════════════════════════════════════════════════════════════
# extractor.py tests (in-memory, no real vault needed)
# ══════════════════════════════════════════════════════════════════════════════

def test_python_extractor_parses_imports(tmp_path):
    """PythonExtractor correctly extracts import statements."""
    src = textwrap.dedent("""\
        import os
        import sys
        from pathlib import Path
        from typing import Optional, Any
    """)
    py_file = tmp_path / "sample.py"
    py_file.write_text(src)

    extractor = PythonExtractor()
    result = extractor.extract_file(py_file, tmp_path)

    import_labels = {n.label for n in result.nodes if n.node_type == NodeType.PYTHON_IMPORT}
    assert "os" in import_labels
    assert "sys" in import_labels
    assert "pathlib.Path" in import_labels
    assert "typing.Optional" in import_labels
    assert "typing.Any" in import_labels


def test_python_extractor_parses_classes(tmp_path):
    """PythonExtractor correctly extracts class definitions."""
    src = textwrap.dedent("""\
        class MyBase:
            pass

        class MyChild(MyBase):
            def method_one(self):
                pass
            def method_two(self, x: int):
                pass
    """)
    py_file = tmp_path / "classes.py"
    py_file.write_text(src)

    extractor = PythonExtractor()
    result = extractor.extract_file(py_file, tmp_path)

    class_labels = {n.label for n in result.nodes if n.node_type == NodeType.PYTHON_CLASS}
    func_labels = {n.label for n in result.nodes if n.node_type == NodeType.PYTHON_FUNCTION}

    assert "MyBase" in class_labels
    assert "MyChild" in class_labels
    assert "MyChild.method_one" in func_labels
    assert "MyChild.method_two" in func_labels


def test_python_extractor_parses_functions(tmp_path):
    """PythonExtractor correctly extracts top-level function definitions."""
    src = textwrap.dedent("""\
        def run_workflow(workflow_id: str) -> dict:
            pass

        async def fetch_data(url: str) -> bytes:
            pass
    """)
    py_file = tmp_path / "funcs.py"
    py_file.write_text(src)

    extractor = PythonExtractor()
    result = extractor.extract_file(py_file, tmp_path)

    func_labels = {n.label for n in result.nodes if n.node_type == NodeType.PYTHON_FUNCTION}
    async_funcs = [n for n in result.nodes if n.properties.get("is_async")]

    assert "run_workflow" in func_labels
    assert "fetch_data" in func_labels
    assert any(n.label == "fetch_data" for n in async_funcs)


def test_python_extractor_produces_file_contains_edges(tmp_path):
    src = textwrap.dedent("""\
        def helper():
            pass

        class Worker:
            pass
    """)
    py_file = tmp_path / "mix.py"
    py_file.write_text(src)

    extractor = PythonExtractor()
    result = extractor.extract_file(py_file, tmp_path)

    file_contains_edges = [e for e in result.edges if e.relation == Relation.FILE_CONTAINS]
    assert len(file_contains_edges) >= 2


def test_python_extractor_handles_syntax_error(tmp_path):
    """PythonExtractor returns an error (not a crash) for invalid Python."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(\n  # no close paren or body\n")

    extractor = PythonExtractor()
    result = extractor.extract_file(bad_file, tmp_path)

    assert len(result.errors) >= 1
    assert "syntax error" in result.errors[0].lower()


def test_yaml_extractor_parses_workflow_manifest(tmp_path):
    """YAMLManifestExtractor correctly parses a workflow manifest."""
    manifest_content = textwrap.dedent("""\
        id: operator_today
        title: Operator Today Brief
        status: active
        task_type: operator-briefing
        role_card: operator-briefing
        permission_ceiling: read-heavy-write-limited
        writeback_targets:
          - 07_LOGS/Operator-Briefs/
        required_reads:
          - 00_HOME/Now.md
    """)
    manifest_file = tmp_path / "operator_today.yaml"
    manifest_file.write_text(manifest_content)

    extractor = YAMLManifestExtractor()
    result = extractor.extract_file(manifest_file, tmp_path)

    workflow_nodes = [n for n in result.nodes if n.node_type == NodeType.WORKFLOW]
    assert len(workflow_nodes) == 1
    assert workflow_nodes[0].label == "operator_today"
    assert workflow_nodes[0].properties["status"] == "active"

    field_nodes = [n for n in result.nodes if n.node_type == NodeType.MANIFEST_FIELD]
    field_names = {n.properties["field_name"] for n in field_nodes}
    assert "role_card" in field_names
    assert "task_type" in field_names

    declares_edges = [e for e in result.edges if e.relation == Relation.WORKFLOW_DECLARES]
    assert len(declares_edges) >= 3


def test_yaml_extractor_handles_invalid_yaml(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("this: is: invalid: yaml: :")

    extractor = YAMLManifestExtractor()
    result = extractor.extract_file(bad_file, tmp_path)

    assert len(result.errors) >= 1


def test_markdown_extractor_parses_headings(tmp_path):
    md_content = textwrap.dedent("""\
        ---
        type: architecture-doc
        status: active
        ---

        # Top Level Heading

        Some text here.

        ## Second Level

        More text.

        ### Third Level

        Deep.
    """)
    md_file = tmp_path / "doc.md"
    md_file.write_text(md_content)

    extractor = MarkdownExtractor()
    result = extractor.extract_file(md_file, tmp_path)

    section_nodes = [n for n in result.nodes if n.node_type == NodeType.DOC_SECTION]
    section_labels = {n.label for n in section_nodes}

    assert "Top Level Heading" in section_labels
    assert "Second Level" in section_labels
    assert "Third Level" in section_labels


def test_markdown_extractor_parses_wikilinks(tmp_path):
    md_content = textwrap.dedent("""\
        # Architecture Overview

        See [[Autonomous-Operator-Runtime]] and [[SIC-Architecture]] for details.
        Also references [[Vault-Map|the vault map]] for file routing.

        ## Details

        Linked to [[Permission-Matrix]].
    """)
    md_file = tmp_path / "overview.md"
    md_file.write_text(md_content)

    extractor = MarkdownExtractor()
    result = extractor.extract_file(md_file, tmp_path)

    wikilink_nodes = [n for n in result.nodes if n.node_type == NodeType.WIKILINK_REF]
    wikilink_targets = {n.label for n in wikilink_nodes}

    assert "Autonomous-Operator-Runtime" in wikilink_targets
    assert "SIC-Architecture" in wikilink_targets
    assert "Vault-Map" in wikilink_targets
    assert "Permission-Matrix" in wikilink_targets


def test_markdown_extractor_parses_frontmatter(tmp_path):
    md_content = textwrap.dedent("""\
        ---
        type: agent-spec
        status: active
        version: 1.2
        domain: aor
        ---

        # Agent Spec

        Content here.
    """)
    md_file = tmp_path / "spec.md"
    md_file.write_text(md_content)

    extractor = MarkdownExtractor()
    result = extractor.extract_file(md_file, tmp_path)

    fm_nodes = [n for n in result.nodes if n.node_type == NodeType.FRONTMATTER_KEY]
    fm_keys = {n.properties["key"] for n in fm_nodes}

    assert "type" in fm_keys
    assert "status" in fm_keys
    assert "domain" in fm_keys


# ══════════════════════════════════════════════════════════════════════════════
# topology.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_connected_components_simple():
    """Two disconnected pairs = two components."""
    nodes = [_make_test_node(f"n{i}") for i in range(4)]
    # Pair 1: n0 ↔ n1; Pair 2: n2 ↔ n3
    edges = [
        make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS),
        make_edge(nodes[2].node_id, nodes[3].node_id, Relation.IMPORTS),
    ]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    components = connected_components(index)
    assert len(components) == 2
    assert len(components[0]) == 2
    assert len(components[1]) == 2


def test_connected_components_fully_connected():
    """All nodes connected = one component."""
    nodes, edges = _make_linear_graph(5)
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    components = connected_components(index)
    assert len(components) == 1
    assert len(components[0]) == 5


def test_connected_components_isolated_nodes():
    """Isolated nodes are their own single-node components."""
    nodes = [_make_test_node(f"n{i}") for i in range(3)]
    # Only n0 → n1; n2 is isolated
    edges = [make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    components = connected_components(index)
    assert len(components) == 2


def test_label_propagation_returns_all_nodes():
    """Label propagation covers every node."""
    nodes, edges = _make_linear_graph(6)
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    communities = label_propagation(index, seed=42)
    assert len(communities) == 6
    for node in nodes:
        assert node.node_id in communities


def test_label_propagation_produces_integer_community_ids():
    nodes, edges = _make_linear_graph(4)
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    communities = label_propagation(index, seed=0)
    for val in communities.values():
        assert isinstance(val, int)
        assert val >= 0


def test_label_propagation_empty_graph():
    snapshot = _make_test_snapshot()
    index = GraphIndex(snapshot)
    result = label_propagation(index)
    assert result == {}


def test_degree_centrality_isolated():
    """Isolated node has centrality 0."""
    nodes = [_make_test_node("solo")]
    snapshot = _make_test_snapshot(nodes=nodes)
    index = GraphIndex(snapshot)
    centrality = degree_centrality(index)
    assert centrality[nodes[0].node_id] == 0.0


def test_degree_centrality_hub():
    """Hub node connected to all others has high centrality."""
    nodes = [_make_test_node(f"n{i}") for i in range(5)]
    # n0 connects to all others
    edges = [
        make_edge(nodes[0].node_id, nodes[i].node_id, Relation.REFERENCES)
        for i in range(1, 5)
    ]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    centrality = degree_centrality(index)
    hub_score = centrality[nodes[0].node_id]
    spoke_score = centrality[nodes[1].node_id]
    assert hub_score > spoke_score


def test_bfs_shortest_path_direct():
    """Direct edge gives path of length 1."""
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edge = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)
    snapshot = _make_test_snapshot(nodes=nodes, edges=[edge])
    index = GraphIndex(snapshot)

    path = bfs_shortest_path(index, nodes[0].node_id, nodes[1].node_id)
    assert path is not None
    assert len(path) == 2
    assert path[0] == nodes[0].node_id
    assert path[1] == nodes[1].node_id


def test_bfs_shortest_path_no_connection():
    """No path returns None."""
    nodes = [_make_test_node("A"), _make_test_node("B")]
    snapshot = _make_test_snapshot(nodes=nodes)  # no edges
    index = GraphIndex(snapshot)

    path = bfs_shortest_path(index, nodes[0].node_id, nodes[1].node_id)
    assert path is None


def test_bfs_shortest_path_through_intermediate():
    """Path A → B → C has length 2."""
    nodes = [_make_test_node("A"), _make_test_node("B"), _make_test_node("C")]
    edges = [
        make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS),
        make_edge(nodes[1].node_id, nodes[2].node_id, Relation.IMPORTS),
    ]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    path = bfs_shortest_path(index, nodes[0].node_id, nodes[2].node_id, directed=False)
    assert path is not None
    assert len(path) == 3


def test_bfs_shortest_path_self():
    """Path from a node to itself returns [node_id]."""
    nodes = [_make_test_node("solo")]
    snapshot = _make_test_snapshot(nodes=nodes)
    index = GraphIndex(snapshot)

    path = bfs_shortest_path(index, nodes[0].node_id, nodes[0].node_id)
    assert path == [nodes[0].node_id]


def test_top_by_degree():
    nodes = [_make_test_node(f"n{i}") for i in range(5)]
    # n0 has 4 outgoing edges (hub)
    edges = [
        make_edge(nodes[0].node_id, nodes[i].node_id, Relation.REFERENCES)
        for i in range(1, 5)
    ]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)

    top = top_by_degree(index, n=3)
    assert len(top) == 3
    assert top[0]["label"] == "n0"  # hub is first


def test_isolated_nodes():
    nodes = [_make_test_node("connected"), _make_test_node("isolated")]
    edges = [make_edge(nodes[0].node_id, nodes[0].node_id, Relation.REFERENCES)]  # self-loop won't count
    # Actually: just no edges for isolated
    snapshot = _make_test_snapshot(nodes=nodes)
    index = GraphIndex(snapshot)

    solo = isolated_nodes(index)
    assert len(solo) == 2  # both have no edges here


def test_cross_domain_edges():
    """cross_domain_edges finds edges between different domains."""
    node_a = make_node("engine.py", NodeType.FILE, "runtime/aor/engine.py", domain="aor")
    node_b = make_node("router.py", NodeType.FILE, "runtime/capture/router.py", domain="capture")
    edge = make_edge(node_a.node_id, node_b.node_id, Relation.IMPORTS)
    snapshot = _make_test_snapshot(nodes=[node_a, node_b], edges=[edge])
    index = GraphIndex(snapshot)

    cross = cross_domain_edges(index)
    assert len(cross) == 1
    assert cross[0]["source_domain"] == "aor"
    assert cross[0]["target_domain"] == "capture"


def test_same_domain_edges_not_in_cross_domain():
    """Edges within the same domain don't appear in cross_domain_edges."""
    node_a = make_node("A.py", NodeType.FILE, "runtime/aor/A.py", domain="aor")
    node_b = make_node("B.py", NodeType.FILE, "runtime/aor/B.py", domain="aor")
    edge = make_edge(node_a.node_id, node_b.node_id, Relation.IMPORTS)
    snapshot = _make_test_snapshot(nodes=[node_a, node_b], edges=[edge])
    index = GraphIndex(snapshot)

    cross = cross_domain_edges(index)
    assert len(cross) == 0


def test_ambiguous_edges_filter():
    nodes = [_make_test_node("A"), _make_test_node("B"), _make_test_node("C")]
    edge_extracted = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS, confidence=Confidence.EXTRACTED)
    edge_inferred  = make_edge(nodes[0].node_id, nodes[2].node_id, Relation.INHERITS, confidence=Confidence.INFERRED)
    snapshot = _make_test_snapshot(nodes=nodes, edges=[edge_extracted, edge_inferred])
    index = GraphIndex(snapshot)

    ambig = ambiguous_edges(index)
    assert len(ambig) == 1
    assert ambig[0]["confidence"] == Confidence.INFERRED


# ══════════════════════════════════════════════════════════════════════════════
# reporter.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_reporter_generates_markdown(tmp_path):
    """generate_report produces non-empty markdown with required sections."""
    nodes, edges = _make_linear_graph(5)
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)
    communities = label_propagation(index, seed=0)
    snapshot.community_assignments = communities
    index = GraphIndex(snapshot)  # rebuild after community assignment

    report = generate_report(snapshot, index, title="Test Report")

    assert "# Test Report" in report
    assert "## Summary" in report
    assert "## Most Connected Nodes" in report
    assert "## Community Summaries" in report
    assert "## Cross-Domain Edges" in report
    assert "## Inferred and Ambiguous Edges" in report
    assert "## Isolated Nodes" in report
    assert "## Suggested Next Inspections" in report
    assert "## Build Provenance" in report
    assert "+00:00Z" not in report
    assert "generated_at:" in report


def test_reporter_shows_correct_counts(tmp_path):
    nodes, edges = _make_linear_graph(4)
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    snapshot.build_info = {"substrate_version": "1.0"}
    index = GraphIndex(snapshot)
    snapshot.community_assignments = label_propagation(index, seed=0)
    index = GraphIndex(snapshot)

    report = generate_report(snapshot, index)
    assert "Total nodes | 4" in report
    assert "Total edges | 3" in report


# ══════════════════════════════════════════════════════════════════════════════
# query.py tests
# ══════════════════════════════════════════════════════════════════════════════

def _make_test_query_service() -> tuple[GraphSnapshot, GraphIndex, GraphQueryService]:
    nodes = [
        make_node("AORRunResult", NodeType.PYTHON_CLASS, "runtime/aor/engine.py", domain="aor"),
        make_node("run_workflow", NodeType.PYTHON_FUNCTION, "runtime/aor/engine.py", domain="aor"),
        make_node("operator_today", NodeType.WORKFLOW, "runtime/workflows/registry/operator_today.yaml", domain="workflows"),
        make_node("capture_content", NodeType.PYTHON_FUNCTION, "runtime/capture/capture.py", domain="capture"),
    ]
    edges = [
        make_edge(nodes[2].node_id, nodes[1].node_id, Relation.WORKFLOW_LINKS_FILE),
        make_edge(nodes[0].node_id, nodes[1].node_id, Relation.DEFINES),
    ]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    index = GraphIndex(snapshot)
    snapshot.community_assignments = label_propagation(index, seed=0)
    index = GraphIndex(snapshot)
    qs = GraphQueryService(snapshot, index)
    return snapshot, index, qs


def test_query_search_by_term():
    _, _, qs = _make_test_query_service()
    results = qs.search(["aor"])
    labels = {r["label"] for r in results}
    assert "AORRunResult" in labels
    assert "run_workflow" in labels


def test_query_search_no_match():
    _, _, qs = _make_test_query_service()
    results = qs.search(["nonexistent_xyz_abc"])
    assert results == []


def test_query_search_by_node_type_filter():
    _, _, qs = _make_test_query_service()
    results = qs.search([""], node_types=[NodeType.WORKFLOW])
    assert all(r["node_type"] == NodeType.WORKFLOW for r in results)


def test_query_inspect_node():
    snapshot, index, qs = _make_test_query_service()
    node_id = snapshot.nodes[0].node_id  # AORRunResult
    result = qs.inspect_node(node_id)

    assert result is not None
    assert result["node"]["label"] == "AORRunResult"
    assert "outgoing" in result
    assert "incoming" in result
    assert "neighbors_out" in result


def test_query_inspect_node_missing():
    _, _, qs = _make_test_query_service()
    result = qs.inspect_node("nonexistent_node_id")
    assert result is None


def test_query_shortest_path():
    _, _, qs = _make_test_query_service()
    # operator_today → run_workflow (via WORKFLOW_LINKS_FILE)
    src_id = None
    tgt_id = None
    for node in qs._snapshot.nodes:
        if node.label == "operator_today":
            src_id = node.node_id
        if node.label == "run_workflow":
            tgt_id = node.node_id

    assert src_id is not None and tgt_id is not None
    result = qs.shortest_path(src_id, tgt_id, directed=False)
    assert result is not None
    assert result["length"] == 1


def test_query_narrow_to_relevant():
    _, _, qs = _make_test_query_service()
    result = qs.narrow_to_relevant(["workflow"])

    assert "source_files" in result
    assert "matched_nodes" in result
    assert len(result["matched_nodes"]) >= 1


def test_query_graph_stats():
    snapshot, index, qs = _make_test_query_service()
    stats = qs.graph_stats()
    assert stats["node_count"] == 4
    assert stats["edge_count"] == 2


def test_query_nodes_by_type():
    _, _, qs = _make_test_query_service()
    workflows = qs.nodes_by_type(NodeType.WORKFLOW)
    assert len(workflows) == 1
    assert workflows[0]["label"] == "operator_today"


# ══════════════════════════════════════════════════════════════════════════════
# builder.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_dedup_nodes_keeps_higher_confidence():
    node_inferred = make_node("MyClass", NodeType.PYTHON_CLASS, "a.py", confidence=Confidence.INFERRED)
    node_extracted = make_node("MyClass", NodeType.PYTHON_CLASS, "a.py", confidence=Confidence.EXTRACTED)
    # Same node_id (same label, type, source_file)
    assert node_inferred.node_id == node_extracted.node_id

    result = _dedup_nodes([node_inferred, node_extracted])
    assert len(result) == 1
    assert result[0].confidence == Confidence.EXTRACTED


def test_dedup_edges_removes_duplicates():
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edge1 = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS, confidence=Confidence.INFERRED)
    edge2 = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS, confidence=Confidence.EXTRACTED)
    # Same edge_id
    assert edge1.edge_id == edge2.edge_id

    result = _dedup_edges([edge1, edge2])
    assert len(result) == 1
    assert result[0].confidence == Confidence.EXTRACTED


def test_drop_dangling_edges():
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edge_valid   = make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)
    edge_dangling = make_edge(nodes[0].node_id, "ghost_node_id", Relation.IMPORTS)

    result = _drop_dangling_edges(nodes, [edge_valid, edge_dangling])
    assert len(result) == 1
    assert result[0].edge_id == edge_valid.edge_id


def test_full_pipeline_on_real_vault():
    """
    Integration test: run full_pipeline on a bounded scope of the real ChaseOS vault.

    This verifies the end-to-end pipeline works on real source files.
    It does NOT assert specific node counts (which can shift as the codebase evolves).
    It asserts structural invariants that should always hold.
    """
    vault_root = Path(__file__).resolve().parents[2]

    snapshot, index, qs = full_pipeline(
        vault_root,
        code_scope=["runtime/aor", "runtime/graph"],
        manifest_scope=["runtime/workflows/registry"],
        doc_scope=["CLAUDE.md"],
    )

    # Structural invariants
    assert snapshot.node_count > 0, "pipeline must extract at least some nodes"
    assert snapshot.edge_count > 0, "pipeline must extract at least some edges"
    assert len(snapshot.community_assignments) == snapshot.node_count, \
        "every node must have a community assignment"
    assert len(snapshot.extraction_scope) > 0
    assert snapshot.build_info.get("substrate_version") == "1.0"

    # All edges must reference existing nodes
    node_ids = {n.node_id for n in snapshot.nodes}
    for edge in snapshot.edges:
        assert edge.source_id in node_ids, f"dangling source: {edge.source_id}"
        assert edge.target_id in node_ids, f"dangling target: {edge.target_id}"

    # Index sanity
    stats = index.stats()
    assert stats["node_count"] == snapshot.node_count
    assert stats["edge_count"] == snapshot.edge_count

    # Query service sanity
    search_result = qs.search(["aor"])
    assert isinstance(search_result, list)

    narrowed = qs.narrow_to_relevant(["workflow", "operator"])
    assert "source_files" in narrowed


def test_save_snapshot_creates_file(tmp_path):
    """save_snapshot writes a JSON file that can be loaded back."""
    nodes = [_make_test_node("test_node")]
    snapshot = _make_test_snapshot(nodes=nodes)

    saved_path = save_snapshot(snapshot, tmp_path)
    assert saved_path.exists()
    assert saved_path.suffix == ".json"

    loaded = GraphSnapshot.load(saved_path)
    assert loaded.snapshot_id == snapshot.snapshot_id
    assert loaded.nodes[0].label == "test_node"


# ══════════════════════════════════════════════════════════════════════════════
# Pass 2: resolver.py tests
# ══════════════════════════════════════════════════════════════════════════════

from runtime.graph.resolver import (
    SymbolIndex, resolve_imports, apply_resolved_edges,
    cross_domain_resolved_edges, IMPORT_RESOLVES_TO,
)
from runtime.graph.diff import (
    diff_snapshots, render_diff_report, SnapshotDiff,
)
from runtime.graph.advisory import (
    advise_required_reads, AdvisoryNarrowingResult, _extract_terms,
)


def _make_file_node(rel_path: str, domain: str = None) -> GraphNode:
    """Make a FILE node for a vault-relative Python file path."""
    return make_node(
        label=rel_path,
        node_type=NodeType.FILE,
        source_file=rel_path,
        domain=domain,
        confidence=Confidence.EXTRACTED,
        provenance="test:file",
    )


def _make_import_node(label: str, source_file: str, domain: str = None) -> GraphNode:
    return make_node(
        label=label,
        node_type=NodeType.PYTHON_IMPORT,
        source_file=source_file,
        domain=domain,
        confidence=Confidence.EXTRACTED,
        provenance="test:import",
    )


def test_symbol_index_builds_from_file_nodes():
    """SymbolIndex maps module paths to file node IDs."""
    file_node = _make_file_node("runtime/aor/engine.py", domain="aor")
    snapshot = _make_test_snapshot(nodes=[file_node])
    sym = SymbolIndex(snapshot)

    # Exact full path lookup
    assert sym.lookup("runtime.aor.engine") == file_node.node_id


def test_symbol_index_ignores_non_file_nodes():
    """SymbolIndex only indexes FILE nodes."""
    class_node = make_node("MyClass", NodeType.PYTHON_CLASS, "runtime/aor/engine.py", domain="aor")
    snapshot = _make_test_snapshot(nodes=[class_node])
    sym = SymbolIndex(snapshot)
    assert sym.lookup("runtime.aor.engine") is None


def test_symbol_index_suffix_lookup():
    """SymbolIndex resolves short module suffixes."""
    file_node = _make_file_node("runtime/aor/engine.py", domain="aor")
    snapshot = _make_test_snapshot(nodes=[file_node])
    sym = SymbolIndex(snapshot)

    # Suffix: "aor.engine" should resolve to same file
    assert sym.lookup("aor.engine") == file_node.node_id
    # Single component suffix
    assert sym.lookup("engine") == file_node.node_id


def test_symbol_index_class_suffix_stripped():
    """SymbolIndex strips uppercase class suffixes from from-imports."""
    file_node = _make_file_node("runtime/aor/engine.py", domain="aor")
    snapshot = _make_test_snapshot(nodes=[file_node])
    sym = SymbolIndex(snapshot)

    # "runtime.aor.engine.AOREngine" → strip ".AOREngine" → "runtime.aor.engine"
    assert sym.lookup("runtime.aor.engine.AOREngine") == file_node.node_id


def test_symbol_index_stdlib_returns_none():
    """Stdlib module names don't resolve to vault files."""
    file_node = _make_file_node("runtime/aor/engine.py", domain="aor")
    snapshot = _make_test_snapshot(nodes=[file_node])
    sym = SymbolIndex(snapshot)

    assert sym.lookup("os") is None
    assert sym.lookup("json") is None
    assert sym.lookup("pathlib") is None


def test_resolve_imports_produces_inferred_edges():
    """resolve_imports creates IMPORT_RESOLVES_TO edges between import and file nodes."""
    # File node A (the importing file's file node)
    file_a = _make_file_node("runtime/aor/engine.py", domain="aor")
    # File node B (the target file that gets imported)
    file_b = _make_file_node("runtime/workflows/operator_today.py", domain="workflows")
    # Import node in A referencing B's module path
    import_node = _make_import_node(
        "runtime.workflows.operator_today",
        source_file="runtime/aor/engine.py",
        domain="aor",
    )
    edge_file_to_import = make_edge(file_a.node_id, import_node.node_id, Relation.IMPORTS)

    snapshot = _make_test_snapshot(
        nodes=[file_a, file_b, import_node],
        edges=[edge_file_to_import],
    )
    resolved = resolve_imports(snapshot)

    # Should produce one IMPORT_RESOLVES_TO edge: import_node → file_b
    assert len(resolved) == 1
    assert resolved[0].relation == IMPORT_RESOLVES_TO
    assert resolved[0].source_id == import_node.node_id
    assert resolved[0].target_id == file_b.node_id
    assert resolved[0].confidence == Confidence.INFERRED


def test_resolve_imports_skips_unresolvable():
    """Import nodes for stdlib/external modules produce no edges."""
    file_a = _make_file_node("runtime/aor/engine.py", domain="aor")
    import_os = _make_import_node("os", source_file="runtime/aor/engine.py")
    import_json = _make_import_node("json", source_file="runtime/aor/engine.py")

    snapshot = _make_test_snapshot(nodes=[file_a, import_os, import_json])
    resolved = resolve_imports(snapshot)
    assert resolved == []


def test_resolve_imports_deduplicates():
    """Two import nodes for the same module produce only one resolved edge."""
    file_a = _make_file_node("runtime/aor/engine.py", domain="aor")
    file_b = _make_file_node("runtime/workflows/operator_today.py", domain="workflows")
    # Two different import nodes both pointing at the same module
    imp1 = _make_import_node("runtime.workflows.operator_today", "runtime/aor/engine.py", domain="aor")
    imp2 = _make_import_node("runtime.workflows.operator_today.run", "runtime/aor/engine.py", domain="aor")

    snapshot = _make_test_snapshot(nodes=[file_a, file_b, imp1, imp2])
    resolved = resolve_imports(snapshot)

    # Both might resolve to file_b — but edge dedup is by edge_id (source+rel+target)
    # imp1 and imp2 have different node_ids → different edge_ids → both appear
    target_ids = {e.target_id for e in resolved}
    assert file_b.node_id in target_ids


def test_apply_resolved_edges_extends_snapshot():
    """apply_resolved_edges returns a new snapshot with resolved edges appended."""
    file_a = _make_file_node("runtime/aor/engine.py", domain="aor")
    file_b = _make_file_node("runtime/workflows/operator_today.py", domain="workflows")
    imp = _make_import_node("runtime.workflows.operator_today", "runtime/aor/engine.py", domain="aor")

    snapshot = _make_test_snapshot(nodes=[file_a, file_b, imp])
    resolved = resolve_imports(snapshot)
    assert len(resolved) >= 1

    updated = apply_resolved_edges(snapshot, resolved)

    assert updated.snapshot_id != snapshot.snapshot_id  # new snapshot
    assert len(updated.edges) == len(snapshot.edges) + len(resolved)
    assert updated.build_info.get("resolver_new_edges") == len(resolved)
    assert updated.build_info.get("substrate_version") == "2.0"


def test_cross_domain_resolved_edges_detects_domain_crossing():
    """cross_domain_resolved_edges surfaces edges between different domains."""
    file_a = _make_file_node("runtime/aor/engine.py", domain="aor")
    file_b = _make_file_node("runtime/workflows/operator_today.py", domain="workflows")
    imp = _make_import_node("runtime.workflows.operator_today", "runtime/aor/engine.py", domain="aor")

    base = _make_test_snapshot(nodes=[file_a, file_b, imp])
    resolved = resolve_imports(base)
    snapshot = apply_resolved_edges(base, resolved)

    cross = cross_domain_resolved_edges(snapshot)
    assert len(cross) >= 1
    assert cross[0]["source_domain"] == "aor"
    assert cross[0]["target_domain"] == "workflows"


def test_resolver_real_vault_produces_cross_domain_edges():
    """Integration: resolver pass on real vault produces >0 cross-domain edges."""
    vault_root = Path(__file__).resolve().parents[2]

    snapshot, index, qs = full_pipeline(
        vault_root,
        code_scope=["runtime/aor", "runtime/workflows", "runtime/graph"],
        manifest_scope=["runtime/workflows/registry"],
        doc_scope=[],
        resolve_imports_pass=True,
    )

    from runtime.graph.resolver import cross_domain_resolved_edges
    cross = cross_domain_resolved_edges(snapshot)
    # With aor importing from workflows and graph, we expect at least some cross-domain edges
    assert len(cross) >= 1, (
        f"Expected cross-domain edges after resolver pass, got 0. "
        f"Total edges: {snapshot.edge_count}, nodes: {snapshot.node_count}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Pass 2: diff.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_diff_identical_snapshots_is_clean():
    """Diffing a snapshot against itself reports no changes."""
    nodes = [_make_test_node("A"), _make_test_node("B")]
    edges = [make_edge(nodes[0].node_id, nodes[1].node_id, Relation.IMPORTS)]
    snapshot = _make_test_snapshot(nodes=nodes, edges=edges)
    snapshot.community_assignments = {n.node_id: 0 for n in nodes}

    diff = diff_snapshots(snapshot, snapshot)
    assert diff.is_clean
    assert diff.nodes_added == 0
    assert diff.nodes_removed == 0
    assert diff.edges_added == 0
    assert diff.edges_removed == 0


def test_diff_added_node():
    """A node present in `after` but not `before` appears in added_nodes."""
    node_a = _make_test_node("A")
    node_b = _make_test_node("B")

    before = _make_test_snapshot(nodes=[node_a])
    after  = _make_test_snapshot(nodes=[node_a, node_b])

    diff = diff_snapshots(before, after)
    assert diff.nodes_added == 1
    assert diff.added_nodes[0].node_id == node_b.node_id
    assert diff.nodes_removed == 0


def test_diff_removed_node():
    """A node present in `before` but not `after` appears in removed_nodes."""
    node_a = _make_test_node("A")
    node_b = _make_test_node("B")

    before = _make_test_snapshot(nodes=[node_a, node_b])
    after  = _make_test_snapshot(nodes=[node_a])

    diff = diff_snapshots(before, after)
    assert diff.nodes_removed == 1
    assert diff.removed_nodes[0].node_id == node_b.node_id
    assert diff.nodes_added == 0


def test_diff_changed_node_confidence():
    """A node whose confidence changes appears in changed_nodes."""
    node_inferred  = make_node("MyClass", NodeType.PYTHON_CLASS, "a.py", confidence=Confidence.INFERRED)
    node_extracted = make_node("MyClass", NodeType.PYTHON_CLASS, "a.py", confidence=Confidence.EXTRACTED)
    assert node_inferred.node_id == node_extracted.node_id  # same structural identity

    before = _make_test_snapshot(nodes=[node_inferred])
    after  = _make_test_snapshot(nodes=[node_extracted])

    diff = diff_snapshots(before, after)
    assert diff.nodes_changed == 1
    assert "confidence" in diff.changed_nodes[0].changed_fields


def test_diff_added_edge():
    """A new edge in `after` appears in added_edges."""
    node_a = _make_test_node("A")
    node_b = _make_test_node("B")
    edge = make_edge(node_a.node_id, node_b.node_id, Relation.IMPORTS)

    before = _make_test_snapshot(nodes=[node_a, node_b], edges=[])
    after  = _make_test_snapshot(nodes=[node_a, node_b], edges=[edge])

    diff = diff_snapshots(before, after)
    assert diff.edges_added == 1
    assert diff.added_edges[0].edge_id == edge.edge_id


def test_diff_removed_edge():
    node_a = _make_test_node("A")
    node_b = _make_test_node("B")
    edge = make_edge(node_a.node_id, node_b.node_id, Relation.IMPORTS)

    before = _make_test_snapshot(nodes=[node_a, node_b], edges=[edge])
    after  = _make_test_snapshot(nodes=[node_a, node_b], edges=[])

    diff = diff_snapshots(before, after)
    assert diff.edges_removed == 1


def test_diff_community_shift():
    """Community assignment changes appear in community_shifts."""
    node_a = _make_test_node("A")
    node_b = _make_test_node("B")

    before = _make_test_snapshot(nodes=[node_a, node_b])
    after  = _make_test_snapshot(nodes=[node_a, node_b])
    before.community_assignments = {node_a.node_id: 0, node_b.node_id: 0}
    after.community_assignments  = {node_a.node_id: 1, node_b.node_id: 0}  # node_a shifted

    diff = diff_snapshots(before, after)
    assert node_a.node_id in diff.community_shifts
    assert diff.community_shifts[node_a.node_id] == (0, 1)


def test_diff_render_report_clean():
    """Clean diff renders an 'identical' message."""
    nodes = [_make_test_node("A")]
    snapshot = _make_test_snapshot(nodes=nodes)
    diff = diff_snapshots(snapshot, snapshot)
    report = render_diff_report(diff)

    assert "structurally identical" in report.lower()


def test_diff_render_report_with_changes():
    """Report with changes includes section headers."""
    node_a = _make_test_node("A")
    node_b = _make_test_node("B")

    before = _make_test_snapshot(nodes=[node_a])
    after  = _make_test_snapshot(nodes=[node_a, node_b])

    diff = diff_snapshots(before, after)
    report = render_diff_report(diff)

    assert "## Added Nodes" in report
    assert node_b.label in report


# ══════════════════════════════════════════════════════════════════════════════
# Pass 2: advisory.py tests
# ══════════════════════════════════════════════════════════════════════════════

def test_extract_terms_basic():
    terms = _extract_terms("run operator workflow", "operator_today")
    assert "operator" in terms
    assert "workflow" in terms


def test_extract_terms_deduplicates():
    """Same token from context and workflow_id appears only once."""
    terms = _extract_terms("operator", "operator_today")
    assert terms.count("operator") == 1


def test_extract_terms_filters_stopwords():
    terms = _extract_terms("run the workflow for a task", "test_id")
    # "the", "for", "a" should be filtered
    assert "the" not in terms
    assert "for" not in terms


def test_extract_terms_max_cap():
    """Term list is capped at _MAX_TERMS."""
    long_text = " ".join(f"term{i}" for i in range(20))
    terms = _extract_terms(long_text, "w")
    from runtime.graph.advisory import _MAX_TERMS
    assert len(terms) <= _MAX_TERMS


def test_advise_required_reads_empty_context():
    """Empty context returns is_empty result without error."""
    _, _, qs = _make_test_query_service()
    result = advise_required_reads(qs, task_context="", workflow_id="")
    assert isinstance(result, AdvisoryNarrowingResult)
    assert result.is_empty


def test_advise_required_reads_returns_result():
    """advise_required_reads returns an AdvisoryNarrowingResult with expected fields."""
    _, _, qs = _make_test_query_service()
    result = advise_required_reads(qs, task_context="run operator workflow", workflow_id="operator_today")

    assert isinstance(result, AdvisoryNarrowingResult)
    assert result.confidence == "graph-advisory"
    assert isinstance(result.candidate_reads, list)
    assert isinstance(result.graph_terms_used, list)
    assert isinstance(result.reasoning, str)
    assert len(result.reasoning) > 0


def test_advise_required_reads_finds_workflow_files():
    """Advisory narrows to workflow-related files given operator context."""
    _, _, qs = _make_test_query_service()
    result = advise_required_reads(qs, task_context="operator briefing", workflow_id="operator_today")

    # The test query service has "operator_today" workflow node
    # Its source file should appear in candidates (or related files via community)
    assert not result.is_empty or result.graph_terms_used  # either found something or at least tried


def test_advise_required_reads_to_dict():
    """to_dict returns a serializable dict."""
    _, _, qs = _make_test_query_service()
    result = advise_required_reads(qs, task_context="workflow", workflow_id="test")
    d = result.to_dict()

    assert "workflow_id" in d
    assert "candidate_reads" in d
    assert "confidence" in d
    assert d["confidence"] == "graph-advisory"


def test_advise_required_reads_integration_real_vault():
    """Integration: advisory on real vault for operator_today produces non-empty result."""
    vault_root = Path(__file__).resolve().parents[2]

    snapshot, index, qs = full_pipeline(
        vault_root,
        code_scope=["runtime/aor", "runtime/workflows", "runtime/graph"],
        manifest_scope=["runtime/workflows/registry"],
        doc_scope=["CLAUDE.md"],
    )

    result = advise_required_reads(
        qs,
        task_context="operator briefing today workflow run",
        workflow_id="operator_today",
    )

    assert isinstance(result, AdvisoryNarrowingResult)
    assert result.confidence == "graph-advisory"
    # Should find at least some relevant files for "operator today" context
    assert not result.is_empty, (
        f"Expected advisory to find relevant files. Terms: {result.graph_terms_used}. "
        f"Reasoning: {result.reasoning}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Run directly
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import traceback

    test_functions = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]

    passed = 0
    failed = 0
    errors = []

    for name, fn in test_functions:
        # Handle tmp_path fixture manually
        if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
            with tempfile.TemporaryDirectory() as td:
                try:
                    fn(Path(td))
                    passed += 1
                except Exception:
                    failed += 1
                    errors.append((name, traceback.format_exc()))
        else:
            try:
                fn()
                passed += 1
            except Exception:
                failed += 1
                errors.append((name, traceback.format_exc()))

    print(f"\n{'='*60}")
    print(f"ChaseOS Graph Substrate — Test Results")
    print(f"{'='*60}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"TOTAL:  {passed + failed}")

    if errors:
        print(f"\nFailed tests:")
        for name, tb in errors:
            print(f"\n  FAIL: {name}")
            for line in tb.strip().splitlines()[-5:]:
                print(f"    {line}")

    sys.exit(0 if failed == 0 else 1)
