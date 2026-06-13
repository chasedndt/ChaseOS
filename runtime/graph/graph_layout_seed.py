"""Deterministic layout seeding + persistence for derived ChaseOS graph scenes.

This module turns a derived ``GraphSnapshot`` into stable, non-degenerate 2D
renderer positions and persists them through the existing
``JsonGraphLayoutCache``. It exists to fix two observed problems:

1. Node payloads carried no ``x``/``y`` — layout was recomputed from scratch on
   every load, which (in the WebGL 2D projection) can settle near-collinear (the
   "line collapse"). Seeding positions by node-type lane guarantees a
   non-degenerate starting bounding box.
2. ``persisted_graph_cache_written`` was always ``False`` — the layout cache was
   built but never written. This module writes/reuses it.

It is **derived-only and fail-open**: it never reads or writes source Markdown,
approvals, Agent Bus state, canonical graph truth, or runtime state. Positions
are written only under ``<vault>/.chaseos/graph/`` (a derived cache directory).
Any failure degrades to "no positions, cache_written=False" — the caller's read
surface still returns normally.
"""

from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
from typing import Any

from runtime.graph.graph_layout_cache import (
    GraphLayoutPosition,
    JsonGraphLayoutCache,
)
from runtime.graph.graph_models import GraphScene, GraphSnapshot


# Node-type → lane (column) index. Lanes keep related node families in distinct
# horizontal bands so the seeded layout is never a single vertical line.
_LANE_FOR_TYPE: dict[str, int] = {
    "project": 0,
    "domain": 0,
    "doc": 1,
    "sop": 1,
    "template": 1,
    "decision": 1,
    "runtime": 2,
    "runtime_profile": 2,
    "agent": 2,
    "source_package": 3,
    "memory_node": 3,
    "approval": 4,
    "log": 4,
    "audit": 4,
    "workflow": 5,
    "artifact": 5,
    "generated": 5,
    "unknown": 6,
}
_DEFAULT_LANE = 6

LANE_SPACING = 340.0
NODE_SPACING = 64.0
JITTER = 22.0
BBOX_RATIO_LIMIT = 12.0


def _hash_unit(value: str) -> float:
    """Deterministic float in [0, 1) derived from a string."""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 1_000_000) / 1_000_000.0


def _lane_for(node_type: str) -> int:
    return _LANE_FOR_TYPE.get(str(node_type or "unknown"), _DEFAULT_LANE)


def _bbox_ratio(positions: dict[str, tuple[float, float]]) -> float:
    """Aspect ratio of the position bounding box (>= 1.0).

    A large ratio means the layout has collapsed toward a line.
    """
    if not positions:
        return 1.0
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    lo = max(min(width, height), 1.0)
    hi = max(max(width, height), 1.0)
    return hi / lo


def _grid_positions(node_ids: list[str], *, spacing: float = NODE_SPACING) -> dict[str, tuple[float, float]]:
    """Balanced square-ish grid fallback that guarantees a non-degenerate bbox."""
    ordered = sorted(node_ids)
    count = len(ordered)
    if count == 0:
        return {}
    cols = max(1, int(math.ceil(math.sqrt(count))))
    positions: dict[str, tuple[float, float]] = {}
    for index, node_id in enumerate(ordered):
        row = index // cols
        col = index % cols
        jx = _hash_unit(node_id) * JITTER - JITTER / 2.0
        jy = _hash_unit(node_id + ":y") * JITTER - JITTER / 2.0
        positions[node_id] = (col * spacing + jx, row * spacing + jy)
    return positions


def seed_positions(
    snapshot: GraphSnapshot,
    *,
    lane_spacing: float = LANE_SPACING,
    node_spacing: float = NODE_SPACING,
    jitter: float = JITTER,
    bbox_ratio_limit: float = BBOX_RATIO_LIMIT,
) -> tuple[dict[str, tuple[float, float]], float]:
    """Seed deterministic 2D positions for every node, never all-equal.

    Returns ``(positions, bbox_ratio)``. If the lane layout collapses (one
    dominant lane → tall thin bbox), it falls back to a balanced grid so the
    returned ratio is within ``bbox_ratio_limit`` whenever a grid can achieve it.
    """
    nodes = list(snapshot.nodes)
    if not nodes:
        return {}, 1.0

    lanes: dict[int, list[str]] = {}
    for node in nodes:
        lanes.setdefault(_lane_for(node.node_type), []).append(node.node_id)

    positions: dict[str, tuple[float, float]] = {}
    for lane_idx, ids in lanes.items():
        ordered = sorted(ids)
        count = len(ordered)
        for i, node_id in enumerate(ordered):
            jx = _hash_unit(node_id) * (2 * jitter) - jitter
            jy = _hash_unit(node_id + ":y") * (2 * jitter) - jitter
            x = lane_idx * lane_spacing + jx
            y = (i - count / 2.0) * node_spacing + jy
            positions[node_id] = (x, y)

    ratio = _bbox_ratio(positions)
    if ratio > bbox_ratio_limit:
        positions = _grid_positions([node.node_id for node in nodes], spacing=node_spacing)
        ratio = _bbox_ratio(positions)
    return positions, ratio


FORCE_LAYOUT_MAX_NODES = 1500
FORCE_LAYOUT_ITERATIONS = 150
FORCE_LAYOUT_AREA = 1_000_000.0


def force_layout(
    snapshot: GraphSnapshot,
    *,
    iterations: int = FORCE_LAYOUT_ITERATIONS,
    max_nodes: int = FORCE_LAYOUT_MAX_NODES,
    bbox_ratio_limit: float = BBOX_RATIO_LIMIT,
) -> tuple[dict[str, tuple[float, float]], float]:
    """Deterministic Fruchterman-Reingold force-directed layout.

    Edges attract their endpoints; every node repels every other. The result is
    a readable, clustered layout instead of the crude lane/grid seed — this is
    the "layout worker" the warmer runs once and caches.

    Determinism: initial positions come from :func:`seed_positions` (no RNG), so
    the same graph always yields the same layout. For graphs larger than
    ``max_nodes`` it falls back to the cheap seed to keep the pure-Python O(n^2)
    cost bounded; iterations scale down for mid-size graphs.
    """
    nodes = list(snapshot.nodes)
    n = len(nodes)
    if n == 0:
        return {}, 1.0
    if n > max_nodes:
        return seed_positions(snapshot)

    ids = [node.node_id for node in nodes]
    id_index = {nid: i for i, nid in enumerate(ids)}

    seed, _seed_ratio = seed_positions(snapshot)
    px = [0.0] * n
    py = [0.0] * n
    for i, nid in enumerate(ids):
        x, y = seed.get(nid, (0.0, 0.0))
        px[i] = float(x)
        py[i] = float(y)

    edges: list[tuple[int, int]] = []
    for edge in snapshot.edges:
        a = id_index.get(edge.source_node_id)
        b = id_index.get(edge.target_node_id)
        if a is not None and b is not None and a != b:
            edges.append((a, b))

    k = math.sqrt(FORCE_LAYOUT_AREA / n)  # ideal edge length
    temp = math.sqrt(FORCE_LAYOUT_AREA) / 10.0
    cooling = 0.95
    iters = iterations if n <= 300 else max(60, iterations * 300 // n)
    cell = k                       # spatial-grid cell ≈ ideal distance
    cutoff2 = (2.5 * k) ** 2       # repulsion is negligible beyond ~2.5k → skip

    for _ in range(max(1, iters)):
        dx = [0.0] * n
        dy = [0.0] * n
        # Spatial grid for this iteration so repulsion is local, not O(n^2).
        grid: dict[tuple[int, int], list[int]] = {}
        for i in range(n):
            key = (int(px[i] // cell), int(py[i] // cell))
            bucket = grid.get(key)
            if bucket is None:
                grid[key] = [i]
            else:
                bucket.append(i)
        # Repulsion — each node only against same/adjacent cells (each pair once).
        for (cx, cy), bucket in grid.items():
            neighbors: list[int] = []
            for gx in (cx - 1, cx, cx + 1):
                for gy in (cy - 1, cy, cy + 1):
                    nb = grid.get((gx, gy))
                    if nb:
                        neighbors.extend(nb)
            for a in bucket:
                xa = px[a]
                ya = py[a]
                for b in neighbors:
                    if b <= a:
                        continue
                    ddx = xa - px[b]
                    ddy = ya - py[b]
                    dist2 = ddx * ddx + ddy * ddy
                    if dist2 > cutoff2:
                        continue
                    if dist2 < 1e-6:
                        # Deterministic separation nudge for coincident nodes.
                        ddx = (a - b) * 0.01 + 0.01
                        ddy = (b - a) * 0.01 + 0.01
                        dist2 = ddx * ddx + ddy * ddy
                    dist = math.sqrt(dist2)
                    force = (k * k) / dist
                    ux = ddx / dist
                    uy = ddy / dist
                    dx[a] += ux * force
                    dy[a] += uy * force
                    dx[b] -= ux * force
                    dy[b] -= uy * force
        # Attraction — along edges.
        for a, b in edges:
            ddx = px[a] - px[b]
            ddy = py[a] - py[b]
            dist = math.sqrt(ddx * ddx + ddy * ddy) or 0.01
            force = (dist * dist) / k
            ux = ddx / dist
            uy = ddy / dist
            dx[a] -= ux * force
            dy[a] -= uy * force
            dx[b] += ux * force
            dy[b] += uy * force
        # Apply, limited by temperature.
        for i in range(n):
            d = math.sqrt(dx[i] * dx[i] + dy[i] * dy[i]) or 0.01
            mv = min(d, temp)
            px[i] += (dx[i] / d) * mv
            py[i] += (dy[i] / d) * mv
        temp *= cooling

    positions = {ids[i]: (px[i], py[i]) for i in range(n)}
    ratio = _bbox_ratio(positions)
    if ratio > bbox_ratio_limit:
        positions = _grid_positions(ids, spacing=NODE_SPACING)
        ratio = _bbox_ratio(positions)
    return positions, ratio


def _resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    """Resolve the layout-cache directory.

    The layout cache is a derived **Studio** artifact, not vault content, so it
    is stored under the Studio user state dir (``~/.chaseos/studio/graph/``) —
    never inside the vault. This keeps the graph query surface a true read-only
    surface over the vault. Resolution order:

    1. explicit ``cache_dir`` argument (used by tests for hermeticity),
    2. ``CHASEOS_GRAPH_LAYOUT_CACHE_DIR`` environment override,
    3. ``~/.chaseos/studio/graph/``.
    """
    if cache_dir is not None:
        return Path(cache_dir)
    env_dir = os.environ.get("CHASEOS_GRAPH_LAYOUT_CACHE_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".chaseos" / "studio" / "graph"


def _cache_path(cache_dir: str | Path | None) -> Path:
    return _resolve_cache_dir(cache_dir) / "layout_cache.json"


def apply_persisted_layout(
    snapshot: GraphSnapshot,
    scene: GraphScene,
    vault_root: str | Path,
    *,
    workspace_id: str | None = None,
    persist: bool = True,
    cache_dir: str | Path | None = None,
    quality: bool = False,
) -> dict[str, Any]:
    """Reuse cached positions where possible, seed the rest, and optionally persist.

    Fail-open. Returns a dict::

        {
          "positions": {node_id: {"x": float, "y": float}},
          "cache_written": bool,
          "bbox_ratio": float,
          "reused": int,
          "seeded": int,
        }

    On any error returns positions={}, cache_written=False.
    """
    empty = {"positions": {}, "cache_written": False, "cache_active": False, "bbox_ratio": 1.0, "reused": 0, "seeded": 0}
    try:
        nodes = list(snapshot.nodes)
        if not nodes:
            return dict(empty)

        workspace = workspace_id or str(Path(vault_root))
        graph_version = snapshot.graph_version.graph_hash
        layout_mode = scene.layout_mode
        scene_id = scene.scene_id

        cache = JsonGraphLayoutCache(_cache_path(cache_dir))
        try:
            cached = cache.load_positions(
                workspace_id=workspace,
                scene_id=scene_id,
                graph_version=graph_version,
                layout_mode=layout_mode,
            )
        except Exception:
            # Corrupt / unsupported cache → treat as empty and remove the bad
            # file so a subsequent save starts from a clean slate (save_positions
            # re-reads the file to merge and would otherwise re-raise).
            cached = {}
            try:
                cache.cache_path.unlink()
            except OSError:
                pass

        # The warmer ("layout worker") runs the expensive force-directed layout
        # once and caches it; read surfaces use the cheap seed for cold caches.
        seeded, bbox_ratio = force_layout(snapshot) if quality else seed_positions(snapshot)

        positions: dict[str, dict[str, float]] = {}
        new_positions: list[GraphLayoutPosition] = []
        reused = 0
        for node in nodes:
            node_id = node.node_id
            if node_id in cached:
                cp = cached[node_id]
                positions[node_id] = {"x": float(cp.x), "y": float(cp.y)}
                reused += 1
                continue
            x, y = seeded.get(node_id, (0.0, 0.0))
            positions[node_id] = {"x": float(x), "y": float(y)}
            new_positions.append(
                GraphLayoutPosition(
                    workspace_id=workspace,
                    scene_id=scene_id,
                    graph_version=graph_version,
                    layout_mode=layout_mode,
                    node_id=node_id,
                    x=float(x),
                    y=float(y),
                )
            )

        wrote_new = bool(persist and new_positions)
        if wrote_new:
            cache.save_positions(new_positions)

        # The persisted cache layer is "active" whenever the returned positions
        # are backed by the cache — either freshly written this call, or reused
        # from a prior write. Only a fail-open path leaves it False.
        cache_active = bool(positions) and (wrote_new or reused > 0)

        return {
            "positions": positions,
            "cache_written": wrote_new,
            "cache_active": cache_active,
            "bbox_ratio": bbox_ratio if not (reused and not new_positions) else _bbox_ratio(
                {nid: (p["x"], p["y"]) for nid, p in positions.items()}
            ),
            "reused": reused,
            "seeded": len(new_positions),
        }
    except Exception:
        return dict(empty)
