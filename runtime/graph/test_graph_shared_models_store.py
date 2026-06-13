from __future__ import annotations

from datetime import datetime, timezone

from runtime.graph.artifact import GraphSnapshot as RuntimeGraphSnapshot
from runtime.graph.artifact import make_edge, make_node
from runtime.graph.graph_models import (
    GraphEdge,
    GraphNode,
    GraphScene,
    GraphSnapshot,
    RuntimeOverlayEvent,
    normalize_edge_type,
    normalize_node_type,
)
from runtime.graph.graph_overlay import runtime_overlay_events_from_agent_bus_rows
from runtime.graph.graph_query import GraphQuery
from runtime.graph.graph_store import InMemoryGraphStore


def test_shared_snapshot_adapts_runtime_graph_snapshot() -> None:
    runtime_node = make_node(
        "Agent Control Plane",
        "doc_section",
        "06_AGENTS/Agent-Control-Plane.md",
        properties={"trust_state": "canonical", "tags": ["agent", "governance"]},
        provenance="markdown_heading",
    )
    runtime_edge = make_edge(
        "source-node",
        runtime_node.node_id,
        "references",
        properties={"weight": 2},
        provenance="wikilink",
    )
    runtime_snapshot = RuntimeGraphSnapshot(
        snapshot_id="runtime-snapshot",
        created_at="2026-06-01T00:00:00Z",
        vault_root=".",
        extraction_scope=["06_AGENTS"],
        nodes=[runtime_node],
        edges=[runtime_edge],
        community_assignments={},
        build_info={},
        metadata={},
    )

    shared = GraphSnapshot.from_runtime_snapshot(runtime_snapshot)

    assert shared.snapshot_id == "runtime-snapshot"
    assert shared.node_count == 1
    assert shared.edge_count == 1
    assert shared.nodes[0].node_type == "doc"
    assert shared.nodes[0].trust_state == "canonical"
    assert shared.nodes[0].path == "06_AGENTS/Agent-Control-Plane.md"
    assert shared.edges[0].edge_type == "explicit_link"
    assert shared.graph_version.graph_hash


def test_shared_snapshot_adapts_studio_graph_contract_and_queries_local_graph() -> None:
    contract = {
        "model_version": "studio.graph_index_contract.v1",
        "generated_at": "2026-06-01T00:00:00Z",
        "graph": {
            "nodes": [
                {
                    "id": "n1",
                    "node_type": "project_doc",
                    "label": "Launch Plan",
                    "stable_key": "01_PROJECTS/Launch.md",
                    "properties": {"path": "01_PROJECTS/Launch.md", "trust_state": "promoted"},
                },
                {
                    "id": "n2",
                    "node_type": "build_log",
                    "label": "Build Log",
                    "stable_key": "07_LOGS/Build-Logs/X.md",
                    "properties": {"path": "07_LOGS/Build-Logs/X.md", "trust_state": "raw"},
                },
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "n1",
                    "target": "n2",
                    "relation": "linked_to_audit_log",
                    "properties": {"trust_state": "suggested"},
                }
            ],
        },
    }

    shared = GraphSnapshot.from_studio_contract(contract)
    query = GraphQuery.from_snapshot(shared)
    local = query.get_local_graph("n1", depth=1)

    assert shared.nodes[0].node_type == "doc"
    assert shared.nodes[0].trust_state == "promoted"
    assert shared.edges[0].edge_type == "linked_to_audit_log"
    assert local.node_count == 2
    assert local.edge_count == 1
    assert query.search_nodes("launch")[0].node_id == "n1"
    assert query.get_graph_summary()["trust_state_counts"]["promoted"] == 1


def test_in_memory_store_scenes_and_overlay_ttl() -> None:
    snapshot = GraphSnapshot.from_nodes_edges(
        [GraphNode(node_id="n1", stable_key="n1", title="Runtime", label="Runtime", node_type="runtime")],
        [],
    )
    store = InMemoryGraphStore.from_snapshot(snapshot)
    scene = GraphScene(
        scene_id=store.make_scene_id("Runtime Trail", "runtime_trail", "Codex"),
        title="Runtime Trail",
        lens_type="runtime_trail",
        query="Codex",
        graph_version=snapshot.graph_version.graph_hash,
    )
    saved = store.save_scene(scene)
    event = RuntimeOverlayEvent(
        event_id="evt-1",
        timestamp="2026-06-01T00:00:00Z",
        runtime_id="Codex",
        event_type="runtime_heartbeat",
        ttl_seconds=1,
    )

    store.add_overlay_event(event)

    assert store.get_scene(saved.scene_id).title == "Runtime Trail"
    assert len(store.list_scenes()) == 1
    assert store.list_overlay_events(now=datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc))[0].event_id == "evt-1"
    assert store.list_overlay_events(now=datetime(2026, 6, 1, 0, 0, 3, tzinfo=timezone.utc)) == []


def test_runtime_overlay_events_from_agent_bus_rows_are_read_only_models() -> None:
    events = runtime_overlay_events_from_agent_bus_rows(
        heartbeats=[
            {
                "runtime": "Codex",
                "runtime_instance_id": "Axiom-Codex",
                "status": "idle",
                "updated_at": "2026-06-01T00:00:00Z",
            }
        ],
        tasks=[
            {
                "task_id": "task-1",
                "run_id": "run-1",
                "recipient": "Codex",
                "owner": "Codex",
                "status": "claimed",
                "updated_at": "2026-06-01T00:01:00Z",
            }
        ],
    )

    assert [event.event_type for event in events] == ["runtime_heartbeat", "task_claimed"]
    assert events[0].runtime_id == "Codex"
    assert events[1].task_id == "task-1"


def test_normalizers_keep_unknowns_safe() -> None:
    assert normalize_node_type("project_doc") == "doc"
    assert normalize_edge_type("links_to_note") == "explicit_link"
    assert normalize_edge_type("not-a-real-edge") == "unknown"
