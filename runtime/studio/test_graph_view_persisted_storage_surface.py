from __future__ import annotations

from runtime.graph.artifact import GraphSnapshot, make_node, make_snapshot_id
from runtime.graph.store import write_snapshot_manifest
from runtime.studio.graph_view_contract import build_graph_view_contract


def _seed_vault(tmp_path):
    (tmp_path / "06_AGENTS").mkdir(parents=True)
    (tmp_path / "06_AGENTS" / "HERMES.md").write_text("# HERMES\n\n[[Runtime-Instance-Authority-Parity]]\n", encoding="utf-8")
    (tmp_path / "06_AGENTS" / "Runtime-Instance-Authority-Parity.md").write_text("# Runtime Instance Authority Parity\n", encoding="utf-8")


def _snapshot() -> GraphSnapshot:
    node = make_node(label="HERMES.md", node_type="file", source_file="06_AGENTS/HERMES.md")
    return GraphSnapshot(
        snapshot_id=make_snapshot_id(),
        created_at="2026-05-30T12:00:00Z",
        vault_root="/test/vault",
        extraction_scope=["06_AGENTS/"],
        nodes=[node],
        edges=[],
        community_assignments={},
        build_info={"builder": "test"},
        metadata={},
    )


def test_graph_view_contract_surfaces_missing_persisted_storage_as_read_only_gap(tmp_path):
    _seed_vault(tmp_path)

    model = build_graph_view_contract(tmp_path, folder_path="06_AGENTS", max_files=10)

    persisted = model["persisted_graph_storage"]
    assert persisted["surface"] == "persisted_graph_storage_status"
    assert persisted["summary"]["cache_ready"] is False
    assert persisted["authority"]["writes_snapshot"] is False
    assert model["readiness"]["persisted_graph_storage_status_ready"] is True
    assert model["readiness"]["persisted_graph_index_ready"] is False
    assert model["graph_view_truth"]["persistent_graph_snapshot_built"] is False
    assert "inspect-persisted-graph-storage-status" in model["allowed_actions"]


def test_graph_view_contract_uses_persisted_storage_status_when_current_snapshot_exists(tmp_path):
    _seed_vault(tmp_path)
    snapshot = _snapshot()
    write_snapshot_manifest(
        snapshot,
        repo_root=tmp_path,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
        vault_root_hash="sha256:test-root",
    )

    model = build_graph_view_contract(tmp_path, folder_path="06_AGENTS", max_files=10)

    persisted = model["persisted_graph_storage"]
    assert persisted["summary"]["cache_ready"] is True
    assert persisted["summary"]["current_snapshot_id"] == snapshot.snapshot_id
    assert model["readiness"]["persisted_graph_index_ready"] is True
    assert model["graph_view_truth"]["persistent_graph_snapshot_built"] is True
    assert model["authority"]["writes_snapshot"] is False
