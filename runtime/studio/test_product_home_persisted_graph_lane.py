from __future__ import annotations

from runtime.graph.artifact import GraphSnapshot, make_node, make_snapshot_id
from runtime.graph.store import write_snapshot_manifest
from runtime.studio.dashboard import _gather_studio_product_home_panel


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


def _persisted_lane(panel):
    return next(lane for lane in panel["open_release_lanes"] if lane["id"] == "persisted_graph_storage_scope")


def test_product_home_persisted_graph_lane_is_now_actionable_read_only_status_surface(tmp_path):
    panel = _gather_studio_product_home_panel(tmp_path, [])

    lane = _persisted_lane(panel)
    assert lane["status"] == "IN_PROGRESS / READ_ONLY_STORAGE_STATUS_SURFACE_BUILT"
    assert lane["next_surface"] == "persisted-graph-storage-status"
    assert lane["preview_command"] == "python -m runtime.cli.main studio persisted-graph-storage-status --json"
    assert lane["safe_preview_available"] is True
    assert lane["preview_only"] is True
    assert lane["storage_summary"]["cache_ready"] is False
    assert lane["authority"]["canonical_mutation_allowed"] is False


def test_product_home_persisted_graph_lane_reports_ready_cache_when_snapshot_exists(tmp_path):
    snapshot = _snapshot()
    write_snapshot_manifest(
        snapshot,
        repo_root=tmp_path,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
    )

    panel = _gather_studio_product_home_panel(tmp_path, [])

    lane = _persisted_lane(panel)
    assert lane["status"] == "PARTIAL / READ_ONLY_CURRENT_GRAPH_SNAPSHOT_AVAILABLE"
    assert lane["storage_summary"]["cache_ready"] is True
    assert lane["storage_summary"]["current_snapshot_id"] == snapshot.snapshot_id
