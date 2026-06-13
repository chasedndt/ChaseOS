"""Tests for the graph layout benchmark harness."""

from __future__ import annotations

from runtime.graph.graph_benchmark import (
    FORCE_LAYOUT_MAX_NODES,
    benchmark_size,
    run_benchmark,
    synthetic_snapshot,
)


def test_synthetic_snapshot_is_connected_and_deterministic() -> None:
    a = synthetic_snapshot(40)
    b = synthetic_snapshot(40)
    assert a.node_count == 40
    assert a.edge_count > 0
    assert a.edge_count == b.edge_count  # deterministic


def test_benchmark_size_structure_small_uses_force() -> None:
    row = benchmark_size(60)
    assert row["nodes"] == 60
    assert row["force_layout_used"] is True
    assert row["seed_ms"] >= 0.0
    assert row["force_ms"] >= 0.0
    assert row["warm_quality_ms"] >= 0.0
    # warm writes positions; the subsequent read reuses all of them
    assert row["warm_reused"] == 0
    assert row["reuse_reused"] == 60
    # non-degenerate
    assert row["force_bbox_ratio"] <= 12.0


def test_benchmark_large_falls_back_to_seed() -> None:
    row = benchmark_size(FORCE_LAYOUT_MAX_NODES + 50)
    assert row["force_layout_used"] is False


def test_run_benchmark_report_shape() -> None:
    report = run_benchmark((30, 80))
    assert report["benchmark"] == "graph_layout_cache"
    assert report["force_layout_max_nodes"] == FORCE_LAYOUT_MAX_NODES
    assert [r["nodes"] for r in report["results"]] == [30, 80]
