from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from runtime.graph.graph_layout_cache import GraphLayoutPosition
from runtime.graph.graph_models import GraphEdge, GraphNode, GraphScene, GraphSnapshot, RuntimeOverlayEvent
from runtime.graph.graph_persistent_store import (
    PersistentGraphStore,
    PersistentGraphStoreError,
    compute_file_fingerprint,
    detect_dirty_files,
)


def _snapshot() -> GraphSnapshot:
    node_a = GraphNode(
        node_id="doc-a",
        stable_key="docs/a.md",
        title="Doc A",
        label="Doc A",
        node_type="doc",
        path="docs/a.md",
        trust_state="canonical",
    )
    node_b = GraphNode(
        node_id="runtime-codex",
        stable_key="runtime/codex",
        title="Codex",
        label="Codex",
        node_type="runtime",
        runtime_id="Codex",
        trust_state="promoted",
    )
    edge = GraphEdge(
        edge_id="edge-a-codex",
        source_node_id="runtime-codex",
        target_node_id="doc-a",
        edge_type="runtime_touch",
        runtime_id="Codex",
    )
    return GraphSnapshot.from_nodes_edges([node_a, node_b], [edge], snapshot_id="snapshot-1")


def test_persistent_graph_store_persists_snapshot_scene_layout_overlay_and_query_cache(tmp_path):
    store = PersistentGraphStore(tmp_path)
    snapshot = _snapshot()

    store.save_snapshot(snapshot)
    loaded = store.load_current_snapshot()
    in_memory_summary = store.get_graph_summary()

    scene = GraphScene(
        scene_id=store.make_scene_id("Runtime Trail", "runtime_trail", "Codex"),
        title="Runtime Trail",
        lens_type="runtime_trail",
        query="Codex",
        graph_version=snapshot.graph_version.graph_hash,
    )
    store.save_scene(scene)

    store.save_layout_positions(
        [
            GraphLayoutPosition(
                workspace_id="default",
                scene_id=scene.scene_id,
                graph_version=snapshot.graph_version.graph_hash,
                layout_mode="force_2d",
                node_id="doc-a",
                x=12.5,
                y=-3.0,
            )
        ]
    )

    event = RuntimeOverlayEvent(
        event_id="event-1",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        runtime_id="Codex",
        event_type="task_claimed",
        node_id="doc-a",
        ttl_seconds=60,
    )
    store.append_overlay_event(event)
    local = store.load_in_memory_store().get_local_graph("doc-a")
    cache_path = store.save_query_cache("local:doc-a:1", local)

    assert loaded.snapshot_id == "snapshot-1"
    assert in_memory_summary["node_count"] == 2
    assert store.get_scene(scene.scene_id).title == "Runtime Trail"
    assert store.load_layout_positions(
        workspace_id="default",
        scene_id=scene.scene_id,
        graph_version=snapshot.graph_version.graph_hash,
        layout_mode="force_2d",
    )["doc-a"].x == 12.5
    assert store.list_overlay_events()[0].event_id == "event-1"
    assert store.load_query_cache("local:doc-a:1", local.graph_version.graph_hash).node_count == 2
    assert cache_path.is_relative_to(tmp_path / ".chaseos" / "graph")


def test_persistent_graph_store_compacts_expired_overlay_events(tmp_path):
    store = PersistentGraphStore(tmp_path)
    old = datetime.now(timezone.utc) - timedelta(seconds=120)
    fresh = datetime.now(timezone.utc)
    store.append_overlay_event(
        RuntimeOverlayEvent(
            event_id="old",
            timestamp=old.isoformat().replace("+00:00", "Z"),
            event_type="runtime_heartbeat",
            ttl_seconds=1,
        )
    )
    store.append_overlay_event(
        RuntimeOverlayEvent(
            event_id="fresh",
            timestamp=fresh.isoformat().replace("+00:00", "Z"),
            event_type="runtime_heartbeat",
            ttl_seconds=300,
        )
    )

    visible = store.list_overlay_events(compact=True)
    lines = (tmp_path / ".chaseos" / "graph" / "runtime_overlay.jsonl").read_text(encoding="utf-8").splitlines()

    assert [event.event_id for event in visible] == ["fresh"]
    assert len(lines) == 1
    assert json.loads(lines[0])["event_id"] == "fresh"


def test_persistent_graph_store_rejects_non_default_or_escaping_store_roots(tmp_path):
    with pytest.raises(PersistentGraphStoreError):
        PersistentGraphStore(tmp_path, store_root=tmp_path / "runtime" / "graph" / "store")

    store = PersistentGraphStore(tmp_path)
    store.current_path.parent.mkdir(parents=True, exist_ok=True)
    store.current_path.write_text(
        json.dumps(
            {
                "schema_version": "chaseos.graph.persistent_store.v1",
                "snapshot_id": "bad",
                "snapshot_path": "runtime/graph/store/bad.json",
                "canonical_mutation_allowed": False,
                "generated_from_read_only_cache": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PersistentGraphStoreError):
        store.load_current_snapshot()


def test_file_fingerprint_and_dirty_detection_are_repo_bounded(tmp_path):
    source = tmp_path / "docs" / "a.md"
    source.parent.mkdir(parents=True)
    source.write_text("alpha\n", encoding="utf-8")

    first = compute_file_fingerprint(tmp_path, "docs/a.md")
    unchanged = detect_dirty_files(tmp_path, {first.path: first}, ["docs/a.md"])

    source.write_text("beta\n", encoding="utf-8")
    changed = detect_dirty_files(tmp_path, {first.path: first}, ["docs/a.md"])

    assert unchanged.unchanged == ("docs/a.md",)
    assert changed.changed == ("docs/a.md",)
    assert changed.current_fingerprints["docs/a.md"].sha256 != first.sha256

    with pytest.raises(PersistentGraphStoreError):
        compute_file_fingerprint(tmp_path, tmp_path.parent / "outside.md")


def test_dirty_detection_reports_deleted_requested_files(tmp_path):
    source = tmp_path / "docs" / "a.md"
    source.parent.mkdir(parents=True)
    source.write_text("alpha\n", encoding="utf-8")
    first = compute_file_fingerprint(tmp_path, "docs/a.md")
    source.unlink()

    result = detect_dirty_files(tmp_path, {first.path: first}, ["docs/a.md"])

    assert result.changed == ("docs/a.md",)
    assert result.deleted == ("docs/a.md",)
