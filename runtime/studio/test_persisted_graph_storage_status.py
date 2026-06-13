from __future__ import annotations

from runtime.graph.artifact import GraphSnapshot, make_node, make_snapshot_id
from runtime.graph.store import write_snapshot_manifest
from runtime.studio.persisted_graph_storage_status import build_persisted_graph_storage_status


def _snapshot() -> GraphSnapshot:
    node = make_node(label="HERMES.md", node_type="file", source_file="06_AGENTS/HERMES.md")
    return GraphSnapshot(
        snapshot_id=make_snapshot_id(),
        created_at="2026-05-30T12:00:00Z",
        vault_root="/test/vault",
        extraction_scope=["06_AGENTS/", "runtime/"],
        nodes=[node],
        edges=[],
        community_assignments={},
        build_info={"builder": "test"},
        metadata={},
    )


def test_persisted_graph_storage_status_reports_missing_cache_as_safe_read_only_gap(tmp_path):
    status = build_persisted_graph_storage_status(tmp_path)

    assert status["surface"] == "persisted_graph_storage_status"
    assert status["status"] == "NOT_READY / NO_CURRENT_GRAPH_SNAPSHOT"
    assert status["summary"]["cache_ready"] is False
    assert status["summary"]["current_snapshot_id"] is None
    assert status["summary"]["snapshot_count"] == 0
    assert status["summary"]["manifest_count"] == 0
    assert status["storage_root"] == "runtime/graph/store"
    assert status["safe_preview_available"] is True
    assert status["authority"] == {
        "read_only": True,
        "writes_snapshot": False,
        "writes_identity_registry": False,
        "writes_markdown": False,
        "canonical_mutation_allowed": False,
    }
    assert "persisted_graph_storage_current_snapshot_missing" in status["readiness"]["blockers"]


def test_persisted_graph_storage_status_loads_current_manifest_without_scanning_or_writing(tmp_path):
    snapshot = _snapshot()
    write_snapshot_manifest(
        snapshot,
        repo_root=tmp_path,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
        vault_root_hash="sha256:test-root",
        source_file_count=2,
    )

    status = build_persisted_graph_storage_status(tmp_path)

    assert status["status"] == "READY / READ_ONLY_CURRENT_GRAPH_SNAPSHOT_AVAILABLE"
    assert status["summary"]["cache_ready"] is True
    assert status["summary"]["current_snapshot_id"] == snapshot.snapshot_id
    assert status["summary"]["current_node_count"] == 1
    assert status["summary"]["current_edge_count"] == 0
    assert status["summary"]["snapshot_count"] == 1
    assert status["summary"]["manifest_count"] == 1
    assert status["current_manifest"]["snapshot_path"] == f"runtime/graph/store/snapshots/{snapshot.snapshot_id}.json"
    assert status["readiness"]["persisted_graph_index_ready"] is True
    assert status["readiness"]["blockers"] == []
    assert status["next_actions"][0]["command"] == "python -m runtime.cli.main studio graph-view-contract --json"
