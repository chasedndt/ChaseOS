from __future__ import annotations

from runtime.graph.graph_models import GraphEdge, GraphNode, GraphSnapshot, RuntimeOverlayEvent
from runtime.graph.graph_query import GraphQuery
from runtime.graph.graph_scenes import choose_default_scene, create_scene_for_lens, list_builtin_lenses
from runtime.graph.graph_store import InMemoryGraphStore


def _snapshot() -> GraphSnapshot:
    runtime = GraphNode(
        node_id="runtime-codex",
        stable_key="runtime:codex",
        title="Codex",
        label="Codex",
        node_type="runtime",
        runtime_id="Codex",
        trust_state="promoted",
    )
    doc = GraphNode(
        node_id="doc-readme",
        stable_key="README.md",
        title="README",
        label="README.md",
        node_type="doc",
        path="README.md",
        trust_state="canonical",
        modified_at="2026-06-01T09:00:00Z",
    )
    artifact = GraphNode(
        node_id="artifact-log",
        stable_key="07_LOGS/Build-Logs/X.md",
        title="Build Log",
        label="Build Log",
        node_type="log",
        path="07_LOGS/Build-Logs/X.md",
        trust_state="raw",
        modified_at="2026-05-01T09:00:00Z",
    )
    edge = GraphEdge(
        edge_id="codex-readme",
        source_node_id="runtime-codex",
        target_node_id="doc-readme",
        edge_type="runtime_touch",
        runtime_id="Codex",
        created_at="2026-06-01T09:01:00Z",
    )
    output = GraphEdge(
        edge_id="readme-log",
        source_node_id="doc-readme",
        target_node_id="artifact-log",
        edge_type="linked_to_audit_log",
        created_at="2026-06-01T09:02:00Z",
    )
    return GraphSnapshot.from_nodes_edges([runtime, doc, artifact], [edge, output], snapshot_id="query-scenes")


def test_runtime_trail_includes_runtime_touches_and_overlay_event_nodes() -> None:
    store = InMemoryGraphStore.from_snapshot(_snapshot())
    store.add_overlay_event(
        RuntimeOverlayEvent(
            event_id="evt-codex-read",
            timestamp="2026-06-01T10:00:00Z",
            runtime_id="Codex",
            event_type="node_read_started",
            node_id="doc-readme",
            file_path="README.md",
        )
    )
    query = GraphQuery(store)

    trail = query.get_runtime_trail("Codex", window="7d")

    assert {node.node_id for node in trail.nodes} >= {"runtime-codex", "doc-readme", "event:evt-codex-read"}
    assert any(edge.edge_type == "runtime_touch" for edge in trail.edges)
    assert trail.metadata["runtime_id"] == "Codex"


def test_agent_touch_heatmap_summarizes_runtime_counts() -> None:
    store = InMemoryGraphStore.from_snapshot(_snapshot())
    store.add_overlay_event(
        RuntimeOverlayEvent(
            event_id="evt-codex-edit",
            timestamp="2026-06-01T10:00:00Z",
            runtime_id="Codex",
            event_type="node_edit_finished",
            node_id="doc-readme",
        )
    )
    query = GraphQuery(store)

    heatmap = query.get_agent_touch_heatmap(runtime_id="Codex", window="2026-06-01T00:00:00Z")

    readme = [item for item in heatmap["touches"] if item["node_id"] == "doc-readme"][0]
    assert readme["path"] == "README.md"
    assert readme["source_path"] == "README.md"
    assert readme["label"] == "README.md"
    assert readme["node_type"] == "doc"
    assert readme["touch_count"] >= 2
    assert readme["runtime_counts"]["Codex"] >= 1
    assert heatmap["graph"].node_count >= 1


def test_recent_activity_graph_respects_window() -> None:
    query = GraphQuery.from_snapshot(_snapshot())

    recent = query.get_recent_activity_graph(window="2026-06-01T00:00:00Z")

    assert {node.node_id for node in recent.nodes} == {"doc-readme"}


def test_scene_helpers_create_default_and_runtime_lens_scenes() -> None:
    snapshot = _snapshot()
    lenses = list_builtin_lenses()
    default_scene = choose_default_scene([], snapshot.graph_version.graph_hash)
    runtime_scene = create_scene_for_lens(
        "runtime_trail",
        graph_version=snapshot.graph_version.graph_hash,
        query="Codex",
    )

    assert lenses[0]["lens_type"] == "current_workspace"
    assert default_scene.lens_type == "recent_activity"
    assert runtime_scene.renderer_mode == "2d"
    assert runtime_scene.layout_mode == "runtime_trail_2d"


def test_open_scene_for_lens_returns_scene_and_graph_slice() -> None:
    query = GraphQuery.from_snapshot(_snapshot())

    result = query.open_scene_for_lens("runtime_trail", query="Codex", window="7d")

    assert result.scene.lens_type == "runtime_trail"
    assert result.graph.node_count >= 2
    assert query.get_scene(result.scene.scene_id).scene_id == result.scene.scene_id


def test_local_neighborhood_lens_returns_bounded_root_graph() -> None:
    query = GraphQuery.from_snapshot(_snapshot())

    result = query.open_scene_for_lens("local_neighborhood", root_node_id="doc-readme", depth=1)

    assert result.scene.lens_type == "local_neighborhood"
    assert result.scene.root_node_id == "doc-readme"
    assert result.scene.depth == 1
    assert result.scene.layout_mode == "local_neighborhood_2d"
    assert {node.node_id for node in result.graph.nodes} == {
        "runtime-codex",
        "doc-readme",
        "artifact-log",
    }
    assert result.summary["node_count"] == 3
