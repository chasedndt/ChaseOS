from __future__ import annotations

import json
from pathlib import Path

from runtime.graph.graph_performance_benchmark import (
    BENCHMARK_MODEL_VERSION,
    build_synthetic_graph_snapshot,
    run_graph_performance_benchmark,
    write_graph_performance_benchmark_report,
)


def test_synthetic_benchmark_snapshot_has_requested_shape() -> None:
    snapshot = build_synthetic_graph_snapshot(50, 100)

    assert snapshot.node_count == 50
    assert snapshot.edge_count == 100
    assert snapshot.metadata["synthetic"] is True
    assert snapshot.metadata["read_only"] is True
    assert any(node.node_id == "runtime-codex" for node in snapshot.nodes)
    assert any(edge.edge_type == "runtime_touch" for edge in snapshot.edges)


def test_graph_performance_benchmark_reports_acceptance_coverage(tmp_path: Path) -> None:
    report = run_graph_performance_benchmark(
        cases=((50, 100), (80, 160)),
        cache_root=tmp_path / "cache",
    )

    assert report["ok"] is True
    assert report["status"] == "complete"
    assert report["model_version"] == BENCHMARK_MODEL_VERSION
    assert report["surface"] == "runtime_graph_performance_benchmark"
    assert len(report["cases"]) == 2
    assert report["acceptance_coverage"]["covers_local_depth_1_2_3"] is True
    assert report["acceptance_coverage"]["covers_layout_cache_hit_vs_miss"] is True
    assert report["acceptance_coverage"]["covers_search_latency"] is True
    assert report["acceptance_coverage"]["covers_scene_query_latency"] is True
    assert report["acceptance_coverage"]["covers_overlay_event_update_latency"] is True
    assert report["acceptance_coverage"]["covers_first_load_time"] is True
    assert report["authority"]["read_only"] is True
    assert report["authority"]["provider_calls_allowed"] is False
    assert report["authority"]["runtime_dispatch_allowed"] is False
    assert report["authority"]["agent_bus_task_write_allowed"] is False
    assert report["authority"]["approval_consumption_allowed"] is False
    assert report["authority"]["canonical_mutation_allowed"] is False
    assert report["authority"]["graph_mutation_allowed"] is False
    assert report["authority"]["writes_vault"] is False
    assert report["authority"]["writes_source_markdown"] is False
    assert report["authority"]["writes_performed"] is False

    first = report["cases"][0]
    assert first["search_result_count"] >= 1
    assert first["local_graphs"]["depth_1"]["node_count"] >= 1
    assert first["local_graphs"]["depth_2"]["node_count"] >= first["local_graphs"]["depth_1"]["node_count"]
    assert first["local_graphs"]["depth_3"]["node_count"] >= first["local_graphs"]["depth_2"]["node_count"]
    assert first["layout_cache_written"] is True
    assert first["layout_cache_active_on_hit"] is True
    assert first["layout_cache_reused"] == first["node_count"]
    assert first["layout_bbox_ratio"] <= 12.0


def test_default_graph_performance_benchmark_covers_prompt_sizes(tmp_path: Path) -> None:
    report = run_graph_performance_benchmark(cache_root=tmp_path / "cache")

    coverage = report["acceptance_coverage"]
    assert coverage["covers_500_nodes_1000_edges"] is True
    assert coverage["covers_2000_nodes_5000_edges"] is True
    assert len(report["cases"]) == 2
    assert report["cases"][0]["node_count"] == 500
    assert report["cases"][1]["edge_count"] == 5000


def test_write_graph_performance_benchmark_report_writes_json_artifact(tmp_path: Path) -> None:
    report = run_graph_performance_benchmark(cases=((50, 100),), cache_root=tmp_path / "cache")
    output = write_graph_performance_benchmark_report(report, tmp_path / "reports" / "benchmark.json")

    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["model_version"] == BENCHMARK_MODEL_VERSION
    assert payload["cases"][0]["case_id"] == "50_nodes_100_edges"
