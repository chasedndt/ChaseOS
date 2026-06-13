"""Lightweight, local graph layout/cache benchmark.

Measures the cost of the layout pipeline (cheap seed vs. force-directed quality
layout vs. persisted cache reuse) over synthetic clustered graphs of several
sizes. Pure-Python, deterministic, no network, no vault writes (uses a temp
cache dir). Run directly::

    python -m runtime.graph.graph_benchmark --sizes 100,500,1000,2000

or call :func:`run_benchmark` and inspect the returned dict.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from runtime.graph.graph_layout_seed import (
    FORCE_LAYOUT_MAX_NODES,
    apply_persisted_layout,
    force_layout,
    seed_positions,
)
from runtime.graph.graph_models import GraphEdge, GraphNode, GraphScene, GraphSnapshot


_NODE_TYPES = ("doc", "runtime", "approval", "source_package", "workflow", "log", "project")
DEFAULT_SIZES = (100, 500, 1000, 2000)


def _scene() -> GraphScene:
    return GraphScene(
        scene_id="bench-scene",
        title="Benchmark",
        lens_type="current_workspace",
        layout_mode="clustered_2d",
        renderer_mode="2d",
    )


def synthetic_snapshot(n_nodes: int, *, cluster_size: int = 10) -> GraphSnapshot:
    """Deterministic clustered graph: dense within clusters, sparse between."""
    nodes = [
        GraphNode(
            node_id=f"n{i}",
            stable_key=f"n{i}",
            title=f"n{i}",
            label=f"node {i}",
            node_type=_NODE_TYPES[i % len(_NODE_TYPES)],
            trust_state="canonical",
        )
        for i in range(n_nodes)
    ]
    edges: list[GraphEdge] = []
    eid = 0
    for i in range(n_nodes):
        for off in (1, 2):
            j = i + off
            if j < n_nodes and (i // cluster_size) == (j // cluster_size):
                edges.append(GraphEdge(edge_id=f"e{eid}", source_node_id=f"n{i}", target_node_id=f"n{j}", edge_type="explicit_link"))
                eid += 1
        if i % cluster_size == 0 and i + cluster_size < n_nodes:
            edges.append(GraphEdge(edge_id=f"e{eid}", source_node_id=f"n{i}", target_node_id=f"n{i + cluster_size}", edge_type="explicit_link"))
            eid += 1
    return GraphSnapshot.from_nodes_edges(nodes, edges)


def _ms(fn) -> tuple[Any, float]:
    start = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - start) * 1000.0


def benchmark_size(n_nodes: int) -> dict[str, Any]:
    snapshot = synthetic_snapshot(n_nodes)
    scene = _scene()
    edge_count = snapshot.edge_count

    (seed_pos, seed_ratio), seed_ms = _ms(lambda: seed_positions(snapshot))
    (force_pos, force_ratio), force_ms = _ms(lambda: force_layout(snapshot))
    force_used = n_nodes <= FORCE_LAYOUT_MAX_NODES

    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp) / "cache"
        # cold warm (writes the quality layout)
        warm, warm_ms = _ms(
            lambda: apply_persisted_layout(snapshot, scene, tmp, cache_dir=cache_dir, persist=True, quality=True)
        )
        # subsequent read (reuse from cache)
        reuse, reuse_ms = _ms(
            lambda: apply_persisted_layout(snapshot, scene, tmp, cache_dir=cache_dir, persist=False, quality=False)
        )

    return {
        "nodes": n_nodes,
        "edges": edge_count,
        "seed_ms": round(seed_ms, 2),
        "seed_bbox_ratio": round(seed_ratio, 3),
        "force_ms": round(force_ms, 2),
        "force_bbox_ratio": round(force_ratio, 3),
        "force_layout_used": force_used,
        "warm_quality_ms": round(warm_ms, 2),
        "cache_reuse_ms": round(reuse_ms, 2),
        "warm_reused": int(warm.get("reused", 0)),
        "reuse_reused": int(reuse.get("reused", 0)),
    }


def run_benchmark(sizes: tuple[int, ...] | list[int] = DEFAULT_SIZES) -> dict[str, Any]:
    results = [benchmark_size(int(n)) for n in sizes]
    return {
        "benchmark": "graph_layout_cache",
        "force_layout_max_nodes": FORCE_LAYOUT_MAX_NODES,
        "results": results,
    }


def _format_table(report: dict[str, Any]) -> str:
    cols = ["nodes", "edges", "seed_ms", "force_ms", "force_layout_used", "force_bbox_ratio", "warm_quality_ms", "cache_reuse_ms"]
    lines = [" | ".join(c.rjust(16) for c in cols)]
    lines.append("-" * len(lines[0]))
    for row in report["results"]:
        lines.append(" | ".join(str(row.get(c, "")).rjust(16) for c in cols))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ChaseOS graph layout benchmark")
    parser.add_argument("--sizes", default=",".join(str(s) for s in DEFAULT_SIZES), help="comma-separated node counts")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args(argv)
    sizes = tuple(int(s) for s in str(args.sizes).split(",") if s.strip())
    report = run_benchmark(sizes)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format_table(report))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
