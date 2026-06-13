"""Lightweight Graph query/layout benchmark for ChaseOS Studio Graph.

This benchmark uses synthetic, deterministic graph snapshots to measure the
local graph substrate without reading source Markdown, dispatching runtimes,
writing Agent Bus tasks, consuming approvals, or mutating canonical graph state.
Optional report writes are proof artifacts only.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from runtime.graph.graph_layout_seed import apply_persisted_layout
from runtime.graph.graph_models import GraphEdge, GraphNode, GraphSnapshot, RuntimeOverlayEvent, utc_now_iso
from runtime.graph.graph_query import GraphQuery
from runtime.graph.graph_scenes import create_scene_for_lens
from runtime.graph.graph_store import InMemoryGraphStore


BENCHMARK_MODEL_VERSION = "chaseos.graph.performance_benchmark.v1"
DEFAULT_BENCHMARK_CASES: tuple[tuple[int, int], ...] = ((500, 1_000), (2_000, 5_000))


@dataclass(frozen=True)
class BenchmarkCase:
    node_count: int
    edge_count: int

    @property
    def case_id(self) -> str:
        return f"{self.node_count}_nodes_{self.edge_count}_edges"


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000.0, 3)


def _time_call(fn):
    start = perf_counter()
    result = fn()
    return result, _elapsed_ms(start)


def build_synthetic_graph_snapshot(node_count: int, edge_count: int) -> GraphSnapshot:
    """Build a deterministic graph with docs, runtimes, approvals, logs, and artifacts."""

    if node_count < 8:
        raise ValueError("node_count must be at least 8")
    if edge_count < node_count:
        raise ValueError("edge_count must be at least node_count")

    nodes: list[GraphNode] = [
        GraphNode(
            node_id="runtime-codex",
            stable_key="runtime:codex",
            title="Codex",
            label="Codex",
            node_type="runtime",
            runtime_id="Codex",
            trust_state="promoted",
            metadata={"benchmark_runtime": True},
        )
    ]
    node_types = ("doc", "log", "approval", "artifact", "workflow", "source_package", "generated")
    trust_states = ("canonical", "raw", "suggested", "generated", "promoted", "quarantined", "disputed")
    for index in range(node_count - 1):
        node_type = node_types[index % len(node_types)]
        path = f"benchmark/{node_type}-{index:04d}.md"
        nodes.append(
            GraphNode(
                node_id=f"node-{index:04d}",
                stable_key=path,
                title=f"Benchmark {node_type.title()} {index:04d}",
                label=f"Benchmark {node_type.title()} {index:04d}",
                node_type=node_type,
                path=path,
                source_kind="synthetic_benchmark",
                trust_state=trust_states[index % len(trust_states)],
                modified_at=f"2026-06-{(index % 28) + 1:02d}T09:00:00Z",
                runtime_id="Codex" if index % 41 == 0 else None,
                tags=("benchmark", node_type),
                metadata={"benchmark_index": index},
            )
        )

    edges: list[GraphEdge] = []
    edge_types = (
        "explicit_link",
        "structural_link",
        "runtime_touch",
        "linked_to_audit_log",
        "provenance",
        "pending_approval",
        "generated_from",
    )
    doc_ids = [node.node_id for node in nodes if node.node_id != "runtime-codex"]
    stride = 37
    for index in range(edge_count):
        source_index = index % len(doc_ids)
        target_index = (index * stride + (index // len(doc_ids)) + 11) % len(doc_ids)
        if source_index == target_index:
            target_index = (target_index + 1) % len(doc_ids)
        source = doc_ids[source_index]
        target = doc_ids[target_index]
        edge_type = edge_types[index % len(edge_types)]
        runtime_id = "Codex" if edge_type == "runtime_touch" or index % 29 == 0 else None
        if index % 17 == 0:
            source = "runtime-codex"
            edge_type = "runtime_touch"
            runtime_id = "Codex"
        edges.append(
            GraphEdge(
                edge_id=f"edge-{index:05d}",
                source_node_id=source,
                target_node_id=target,
                edge_type=edge_type,
                runtime_id=runtime_id,
                created_at=f"2026-06-{(index % 28) + 1:02d}T10:00:00Z",
                weight=1.0 + (index % 5) / 10.0,
                metadata={"synthetic_benchmark": True},
            )
        )

    return GraphSnapshot.from_nodes_edges(
        nodes,
        edges,
        snapshot_id=f"benchmark-{node_count}-{edge_count}",
        metadata={
            "source": "runtime.graph.graph_performance_benchmark",
            "synthetic": True,
            "read_only": True,
        },
    )


def _add_overlay_events(store: InMemoryGraphStore, *, count: int = 100) -> int:
    for index in range(count):
        node_id = f"node-{index:04d}"
        store.add_overlay_event(
            RuntimeOverlayEvent(
                event_id=f"benchmark-overlay-{index:04d}",
                timestamp=f"2026-06-{(index % 28) + 1:02d}T11:00:00Z",
                runtime_id="Codex",
                event_type="node_touch_finished",
                node_id=node_id,
                file_path=f"benchmark/doc-{index:04d}.md",
                source="graph_performance_benchmark",
                ttl_seconds=3_600,
            )
        )
    return count


def _benchmark_case(case: BenchmarkCase, *, cache_root: Path) -> dict[str, Any]:
    snapshot, snapshot_build_ms = _time_call(lambda: build_synthetic_graph_snapshot(case.node_count, case.edge_count))
    query, first_load_ms = _time_call(lambda: GraphQuery(InMemoryGraphStore.from_snapshot(snapshot)))
    summary, summary_ms = _time_call(query.get_graph_summary)
    search_results, search_latency_ms = _time_call(lambda: query.search_nodes("Benchmark Doc 0007", limit=10))
    focus_graph, focus_graph_latency_ms = _time_call(lambda: query.get_focus_graph("Benchmark Doc 0105", depth=1))

    local_graphs: dict[str, Any] = {}
    for depth in (1, 2, 3):
        graph, elapsed = _time_call(lambda d=depth: query.get_local_graph("node-0000", depth=d, limit=2_000))
        local_graphs[f"depth_{depth}"] = {
            "latency_ms": elapsed,
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
        }

    overlay_count, overlay_update_latency_ms = _time_call(lambda: _add_overlay_events(query.store))
    runtime_trail, runtime_trail_latency_ms = _time_call(
        lambda: query.get_runtime_trail("Codex", window="2026-06-01T00:00:00Z", limit=500)
    )
    heatmap, heatmap_latency_ms = _time_call(
        lambda: query.get_agent_touch_heatmap(runtime_id="Codex", window="2026-06-01T00:00:00Z")
    )

    scene = create_scene_for_lens(
        "current_workspace",
        graph_version=snapshot.graph_version.graph_hash,
        title=f"Benchmark {case.case_id}",
    )
    case_cache = cache_root / case.case_id
    miss_result, layout_cache_miss_ms = _time_call(
        lambda: apply_persisted_layout(
            snapshot,
            scene,
            ".",
            workspace_id=f"benchmark:{case.case_id}",
            cache_dir=case_cache,
        )
    )
    hit_result, layout_cache_hit_ms = _time_call(
        lambda: apply_persisted_layout(
            snapshot,
            scene,
            ".",
            workspace_id=f"benchmark:{case.case_id}",
            cache_dir=case_cache,
        )
    )

    return {
        "case_id": case.case_id,
        "node_count": case.node_count,
        "edge_count": case.edge_count,
        "snapshot_build_ms": snapshot_build_ms,
        "first_load_ms": first_load_ms,
        "summary_latency_ms": summary_ms,
        "search_latency_ms": search_latency_ms,
        "search_result_count": len(search_results),
        "focus_graph_latency_ms": focus_graph_latency_ms,
        "focus_graph_node_count": focus_graph.node_count,
        "focus_graph_edge_count": focus_graph.edge_count,
        "local_graphs": local_graphs,
        "overlay_event_update_latency_ms": overlay_update_latency_ms,
        "overlay_event_count": overlay_count,
        "runtime_trail_latency_ms": runtime_trail_latency_ms,
        "runtime_trail_node_count": runtime_trail.node_count,
        "runtime_trail_edge_count": runtime_trail.edge_count,
        "agent_touch_heatmap_latency_ms": heatmap_latency_ms,
        "agent_touch_heatmap_touch_count": len(heatmap["touches"]),
        "layout_cache_miss_ms": layout_cache_miss_ms,
        "layout_cache_hit_ms": layout_cache_hit_ms,
        "layout_cache_seeded": miss_result.get("seeded"),
        "layout_cache_reused": hit_result.get("reused"),
        "layout_cache_written": miss_result.get("cache_written"),
        "layout_cache_active_on_hit": hit_result.get("cache_active"),
        "layout_bbox_ratio": hit_result.get("bbox_ratio"),
        "graph_summary": summary,
    }


def run_graph_performance_benchmark(
    cases: tuple[tuple[int, int], ...] = DEFAULT_BENCHMARK_CASES,
    *,
    cache_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run the Graph performance benchmark and return a JSON-serializable report."""

    benchmark_cases = tuple(BenchmarkCase(nodes, edges) for nodes, edges in cases)
    if cache_root is None:
        with tempfile.TemporaryDirectory(prefix="chaseos-graph-benchmark-") as tmp:
            return _run_graph_performance_benchmark(benchmark_cases, cache_root=Path(tmp), temporary_cache=True)
    return _run_graph_performance_benchmark(benchmark_cases, cache_root=Path(cache_root), temporary_cache=False)


def _run_graph_performance_benchmark(
    cases: tuple[BenchmarkCase, ...],
    *,
    cache_root: Path,
    temporary_cache: bool,
) -> dict[str, Any]:
    started_at = utc_now_iso()
    case_results = [_benchmark_case(case, cache_root=cache_root) for case in cases]
    return {
        "ok": True,
        "status": "complete",
        "surface": "runtime_graph_performance_benchmark",
        "model_version": BENCHMARK_MODEL_VERSION,
        "generated_at": utc_now_iso(),
        "started_at": started_at,
        "cases": case_results,
        "acceptance_coverage": {
            "node_edge_cases": [case.case_id for case in cases],
            "covers_500_nodes_1000_edges": any(case.node_count == 500 and case.edge_count == 1_000 for case in cases),
            "covers_2000_nodes_5000_edges": any(case.node_count == 2_000 and case.edge_count == 5_000 for case in cases),
            "covers_local_depth_1_2_3": all(
                all(f"depth_{depth}" in result["local_graphs"] for depth in (1, 2, 3))
                for result in case_results
            ),
            "covers_layout_cache_hit_vs_miss": all(
                result["layout_cache_written"] is True
                and int(result["layout_cache_seeded"] or 0) > 0
                and int(result["layout_cache_reused"] or 0) == result["node_count"]
                for result in case_results
            ),
            "covers_search_latency": all("search_latency_ms" in result for result in case_results),
            "covers_scene_query_latency": all("focus_graph_latency_ms" in result for result in case_results),
            "covers_overlay_event_update_latency": all(
                "overlay_event_update_latency_ms" in result for result in case_results
            ),
            "covers_first_load_time": all("first_load_ms" in result for result in case_results),
        },
        "authority": {
            "read_only": True,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "approval_consumption_allowed": False,
            "canonical_mutation_allowed": False,
            "graph_mutation_allowed": False,
            "writes_vault": False,
            "writes_source_markdown": False,
            "writes_performed": False,
            "writes_report_artifact_only_when_requested": True,
            "temporary_layout_cache": temporary_cache,
        },
        "unverified": [
            "Benchmark uses synthetic graph snapshots, not live packaged Studio rendering.",
            "Benchmark does not prove packaged executable performance.",
            "Benchmark does not repair current pointers or promote release artifacts.",
        ],
    }


def write_graph_performance_benchmark_report(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ChaseOS Graph performance benchmark.")
    parser.add_argument("--output-path", help="Optional JSON report path to write.")
    parser.add_argument("--cache-root", help="Optional derived layout-cache root for benchmark cache timing.")
    parser.add_argument("--json", action="store_true", help="Print the benchmark report as JSON.")
    args = parser.parse_args(argv)

    report = run_graph_performance_benchmark(cache_root=args.cache_root)
    if args.output_path:
        written = write_graph_performance_benchmark_report(report, args.output_path)
        report = {**report, "report_path": str(written)}
    if args.json or not args.output_path:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
