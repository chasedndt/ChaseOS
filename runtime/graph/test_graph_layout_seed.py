"""Tests for Pass 1 — persisted layout seeding/cache wiring.

Covers the seeder (never-all-equal, grid collapse guard), the persistence
helper (write/reuse/fail-open/corrupt-cache), and the StudioAPI graph query
surface integration (x/y delivered, persisted flag flipped, NO vault writes).
"""

from __future__ import annotations

import json
from pathlib import Path

import math

from runtime.graph.graph_layout_seed import (
    BBOX_RATIO_LIMIT,
    FORCE_LAYOUT_MAX_NODES,
    apply_persisted_layout,
    force_layout,
    seed_positions,
)
from runtime.graph.graph_models import GraphEdge, GraphNode, GraphScene, GraphSnapshot


def _node(node_id: str, node_type: str = "doc") -> GraphNode:
    return GraphNode(
        node_id=node_id,
        stable_key=node_id,
        title=node_id,
        label=node_id,
        node_type=node_type,
    )


def _snapshot(node_ids: list[str], *, node_type: str = "doc") -> GraphSnapshot:
    nodes = [_node(nid, node_type) for nid in node_ids]
    return GraphSnapshot.from_nodes_edges(nodes, [])


def _scene() -> GraphScene:
    return GraphScene(
        scene_id="scene-test",
        title="Test scene",
        lens_type="current_workspace",
        layout_mode="clustered_2d",
        renderer_mode="2d",
    )


def _bbox_ratio(positions: dict[str, dict[str, float]]) -> float:
    xs = [p["x"] for p in positions.values()]
    ys = [p["y"] for p in positions.values()]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    lo = max(min(w, h), 1.0)
    hi = max(max(w, h), 1.0)
    return hi / lo


# --- seeder ---------------------------------------------------------------

def test_seed_positions_never_all_equal() -> None:
    snap = _snapshot([f"n{i}" for i in range(6)])
    positions, _ratio = seed_positions(snap)
    assert len(positions) == 6
    coords = {(round(x, 2), round(y, 2)) for x, y in positions.values()}
    assert len(coords) == 6  # all distinct, never collapsed to one point


def test_seed_positions_single_lane_triggers_grid_fallback() -> None:
    # 60 nodes all of one type would land in a single lane (a tall, thin column
    # → collapse). The grid fallback must rescue the bounding box.
    snap = _snapshot([f"doc{i}" for i in range(60)], node_type="doc")
    positions, ratio = seed_positions(snap)
    assert ratio <= BBOX_RATIO_LIMIT
    pos_map = {nid: {"x": x, "y": y} for nid, (x, y) in positions.items()}
    assert _bbox_ratio(pos_map) <= BBOX_RATIO_LIMIT


def test_seed_positions_empty_snapshot() -> None:
    positions, ratio = seed_positions(GraphSnapshot.from_nodes_edges([], []))
    assert positions == {}
    assert ratio == 1.0


# --- persistence ----------------------------------------------------------

def test_apply_persisted_layout_writes_then_reuses(tmp_path: Path) -> None:
    snap = _snapshot([f"n{i}" for i in range(8)])
    scene = _scene()
    cache_dir = tmp_path / "cache"

    first = apply_persisted_layout(snap, scene, tmp_path / "vault", cache_dir=cache_dir)
    assert first["cache_written"] is True
    assert first["cache_active"] is True
    assert first["seeded"] == 8
    assert first["reused"] == 0
    assert (cache_dir / "layout_cache.json").exists()
    assert all("x" in p and "y" in p for p in first["positions"].values())

    second = apply_persisted_layout(snap, scene, tmp_path / "vault", cache_dir=cache_dir)
    assert second["reused"] == 8
    assert second["seeded"] == 0
    assert second["cache_active"] is True  # reused-from-cache still counts as active
    # positions stable across loads
    assert first["positions"] == second["positions"]


def test_apply_persisted_layout_no_vault_write(tmp_path: Path) -> None:
    """Persistence goes to the cache dir, never into the vault root."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "keep.md").write_text("# keep\n", encoding="utf-8")
    before = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*"))

    snap = _snapshot([f"n{i}" for i in range(4)])
    apply_persisted_layout(snap, _scene(), vault, cache_dir=tmp_path / "cache")

    after = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*"))
    assert after == before  # vault untouched


def test_apply_persisted_layout_non_degenerate_multi_lane(tmp_path: Path) -> None:
    nodes = (
        [_node(f"d{i}", "doc") for i in range(20)]
        + [_node(f"r{i}", "runtime") for i in range(5)]
        + [_node(f"a{i}", "approval") for i in range(5)]
    )
    snap = GraphSnapshot.from_nodes_edges(nodes, [])
    result = apply_persisted_layout(snap, _scene(), tmp_path / "v", cache_dir=tmp_path / "c")
    assert result["bbox_ratio"] <= BBOX_RATIO_LIMIT


def test_apply_persisted_layout_empty_is_fail_open(tmp_path: Path) -> None:
    empty = GraphSnapshot.from_nodes_edges([], [])
    result = apply_persisted_layout(empty, _scene(), tmp_path / "v", cache_dir=tmp_path / "c")
    assert result["positions"] == {}
    assert result["cache_active"] is False
    assert result["cache_written"] is False


def test_apply_persisted_layout_corrupt_cache_reseeds(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "layout_cache.json").write_text("{ not valid json", encoding="utf-8")

    snap = _snapshot([f"n{i}" for i in range(5)])
    result = apply_persisted_layout(snap, _scene(), tmp_path / "v", cache_dir=cache_dir)
    # corrupt cache is tolerated: positions are reseeded and returned
    assert len(result["positions"]) == 5
    assert all("x" in p and "y" in p for p in result["positions"].values())


# --- surface integration --------------------------------------------------

def _seed_two_note_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\nLinks to [[Beta]].\n#graph\n", encoding="utf-8")
    (notes / "beta.md").write_text("# Beta\nBack to [[Alpha]].\n", encoding="utf-8")
    return vault


def test_read_surface_delivers_positions_without_writing_anything(
    tmp_path: Path, monkeypatch
) -> None:
    """The read surface seeds x/y in-memory and writes nothing (not the vault,
    not the cache). On a cold cache, persisted_graph_cache_written is False but
    positions are still delivered."""
    from runtime.studio.graph_query_surface import build_graph_query_surface

    cache_dir = tmp_path / "studio-graph-cache"
    monkeypatch.setenv("CHASEOS_GRAPH_LAYOUT_CACHE_DIR", str(cache_dir))
    vault = _seed_two_note_vault(tmp_path)
    before = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*"))

    surface = build_graph_query_surface(vault, folder_path="notes", max_nodes=50, max_edges=50)

    # vault untouched, and the read surface did not create the cache
    assert sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*")) == before
    assert not (cache_dir / "layout_cache.json").exists()

    readiness = surface["readiness"]
    assert readiness["persisted_graph_cache_written"] is False  # cold cache
    assert readiness["layout_bbox_ratio"] <= BBOX_RATIO_LIMIT

    nodes = surface["default_graph"]["nodes"]
    assert nodes
    assert all("x" in n and "y" in n for n in nodes)  # x/y delivered anyway

    assert surface["authority"]["read_only"] is True
    assert surface["authority"]["graph_mutation_allowed"] is False
    assert surface["possible_writes"] == []


def test_warm_cache_then_read_surface_reports_persisted(tmp_path: Path, monkeypatch) -> None:
    """After the sanctioned warmer writes the cache (to the non-vault Studio
    state dir), the read surface reuses it and reports persisted=True."""
    from runtime.studio.graph_query_surface import (
        build_graph_query_surface,
        warm_graph_layout_cache,
    )

    cache_dir = tmp_path / "studio-graph-cache"
    monkeypatch.setenv("CHASEOS_GRAPH_LAYOUT_CACHE_DIR", str(cache_dir))
    vault = _seed_two_note_vault(tmp_path)
    before = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*"))

    warm = warm_graph_layout_cache(vault, folder_path="notes", max_nodes=50, max_edges=50)
    assert warm["ok"] is True
    assert warm["cache_written"] is True
    assert warm["positions_seeded"] >= 1
    assert (cache_dir / "layout_cache.json").exists()
    # warmer writes only the cache, never the vault
    assert sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*")) == before

    surface = build_graph_query_surface(vault, folder_path="notes", max_nodes=50, max_edges=50)
    assert surface["readiness"]["persisted_graph_cache_written"] is True
    assert surface["readiness"]["layout_positions_reused"] >= 1


# --- force-directed layout (the "layout worker") --------------------------

def _edge(eid: str, src: str, tgt: str) -> GraphEdge:
    return GraphEdge(edge_id=eid, source_node_id=src, target_node_id=tgt, edge_type="explicit_link")


def _two_clique_snapshot() -> tuple[GraphSnapshot, list[str], list[str]]:
    a_ids = [f"a{i}" for i in range(5)]
    b_ids = [f"b{i}" for i in range(5)]
    nodes = [_node(x) for x in a_ids + b_ids]
    edges: list[GraphEdge] = []
    for group in (a_ids, b_ids):
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                edges.append(_edge(f"e-{group[i]}-{group[j]}", group[i], group[j]))
    return GraphSnapshot.from_nodes_edges(nodes, edges), a_ids, b_ids


def _dist(p: dict[str, tuple[float, float]], a: str, b: str) -> float:
    return math.hypot(p[a][0] - p[b][0], p[a][1] - p[b][1])


def _mean_pairwise(p: dict[str, tuple[float, float]], group_a: list[str], group_b: list[str]) -> float:
    pairs = [(a, b) for a in group_a for b in group_b if a != b]
    return sum(_dist(p, a, b) for a, b in pairs) / max(1, len(pairs))


def test_force_layout_empty() -> None:
    positions, ratio = force_layout(GraphSnapshot.from_nodes_edges([], []))
    assert positions == {}
    assert ratio == 1.0


def test_force_layout_non_degenerate() -> None:
    snap, a, b = _two_clique_snapshot()
    positions, ratio = force_layout(snap)
    assert len(positions) == 10
    assert ratio <= BBOX_RATIO_LIMIT


def test_force_layout_is_deterministic() -> None:
    snap, _a, _b = _two_clique_snapshot()
    p1, _r1 = force_layout(snap)
    p2, _r2 = force_layout(snap)
    assert {k: (round(x, 4), round(y, 4)) for k, (x, y) in p1.items()} == {
        k: (round(x, 4), round(y, 4)) for k, (x, y) in p2.items()
    }


def test_force_layout_separates_disconnected_clusters() -> None:
    """Two disconnected cliques: intra-cluster spacing < inter-cluster spacing."""
    snap, a, b = _two_clique_snapshot()
    positions, _ratio = force_layout(snap)
    intra = (_mean_pairwise(positions, a, a) + _mean_pairwise(positions, b, b)) / 2.0
    inter = _mean_pairwise(positions, a, b)
    assert intra < inter, f"clusters not separated: intra={intra:.1f} inter={inter:.1f}"


def test_force_layout_large_falls_back_to_seed() -> None:
    big = _snapshot([f"n{i}" for i in range(FORCE_LAYOUT_MAX_NODES + 5)])
    force_pos, _fr = force_layout(big)
    seed_pos, _sr = seed_positions(big)
    assert force_pos == seed_pos  # above cap → cheap seed, bounded cost


def test_apply_persisted_layout_quality_writes_and_differs_from_seed(tmp_path) -> None:
    from pathlib import Path  # noqa: F401 (kept local; tmp_path is a Path)

    snap, _a, _b = _two_clique_snapshot()
    scene = _scene()
    cache_dir = tmp_path / "cache"
    result = apply_persisted_layout(snap, scene, tmp_path / "v", cache_dir=cache_dir, quality=True)
    assert result["cache_written"] is True
    assert (cache_dir / "layout_cache.json").exists()
    # quality (force) layout should move nodes off their lane-seed positions
    seed_pos, _ = seed_positions(snap)
    moved = any(
        abs(result["positions"][nid]["x"] - seed_pos[nid][0]) > 1.0
        or abs(result["positions"][nid]["y"] - seed_pos[nid][1]) > 1.0
        for nid in seed_pos
    )
    assert moved
