"""
studio/graph_view.py — Studio Graph View Layer

Wraps the ChaseOS graph substrate (`runtime/graph/`) to produce UI-ready models
for the Studio Node Inspector (Phase 10B foundation) and graph surface.

This module is read-only — it never modifies the graph snapshot or vault state.
All outputs are plain dicts suitable for JSON serialization or static HTML rendering.

Outputs:
  - Node inspector model (single node + neighbors + edges + provenance chain)
  - Graph search results (nodes matching a query string)
  - Community summary model (nodes in a community + cross-domain edges)
  - Graph statistics model (counts, top nodes, health indicators)

Governance:
  - Read-only: no vault writes
  - Snapshot must exist at 07_LOGS/Graph-Snapshots/ — returns error model if absent
  - Inferred edges are always surfaced with confidence marker in the model
  - Generated vs canonical distinction must always be visible in node models
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


_BOUNDARY = {
    "reads_snapshot": True,
    "writes_vault": False,
    "writes_snapshot": False,
    "canonical_mutation_allowed": False,
}


# ── Snapshot loader ───────────────────────────────────────────────────────────

def _load_latest_snapshot(vault_root: Path):
    """Load the most recent graph snapshot. Returns None if none exists."""
    try:
        from runtime.graph.builder import load_latest_snapshot
        return load_latest_snapshot(vault_root)
    except Exception:
        return None


def _build_index(snapshot):
    """Build a GraphIndex from a snapshot. Returns None on failure."""
    try:
        from runtime.graph.index import GraphIndex
        return GraphIndex(snapshot)
    except Exception:
        return None


# ── Node model builders ───────────────────────────────────────────────────────

def _node_to_dict(node) -> dict[str, Any]:
    """Convert a GraphNode dataclass to a plain UI-ready dict."""
    return {
        "id": node.node_id,
        "label": node.label,
        "node_type": node.node_type,
        "source_file": node.source_file,
        "domain": node.domain,
        "confidence": node.confidence,
        "properties": node.properties if hasattr(node, "properties") else {},
    }


def _edge_to_dict(edge) -> dict[str, Any]:
    """Convert a GraphEdge dataclass to a plain UI-ready dict."""
    return {
        "id": edge.edge_id,
        "source": edge.source_id,
        "target": edge.target_id,
        "relation": edge.relation,
        "confidence": edge.confidence,
        "properties": edge.properties if hasattr(edge, "properties") else {},
    }


# ── Public API ────────────────────────────────────────────────────────────────

def inspect_node(vault_root: str | Path, node_id: str) -> dict[str, Any]:
    """
    Return a UI-ready Node Inspector model for a single node.

    Includes the node itself, all direct neighbors, and all edges touching it.
    Inferred edges are always surfaced with their confidence marker.
    Returns an error model if no snapshot exists or the node is not found.
    """
    vault = Path(vault_root).resolve()
    snapshot = _load_latest_snapshot(vault)
    if snapshot is None:
        return {
            "ok": False,
            "error": "No graph snapshot found. Run 'chaseos graph build' first.",
            "surface": "studio_node_inspector",
            "boundary": _BOUNDARY,
        }

    index = _build_index(snapshot)
    if index is None:
        return {
            "ok": False,
            "error": "Failed to build graph index from snapshot.",
            "surface": "studio_node_inspector",
            "boundary": _BOUNDARY,
        }

    node = index.node_by_id.get(node_id)
    if node is None:
        return {
            "ok": False,
            "error": f"Node '{node_id}' not found in the current snapshot.",
            "surface": "studio_node_inspector",
            "node_id": node_id,
            "boundary": _BOUNDARY,
        }

    outgoing_edges = index.outgoing_edges.get(node_id, [])
    incoming_edges = index.incoming_edges.get(node_id, [])
    all_edges = [_edge_to_dict(e) for e in outgoing_edges + incoming_edges]

    neighbor_ids = {e.target_id for e in outgoing_edges} | {e.source_id for e in incoming_edges}
    neighbor_ids.discard(node_id)
    neighbors = [
        _node_to_dict(index.node_by_id[nid])
        for nid in neighbor_ids
        if nid in index.node_by_id
    ]

    return {
        "ok": True,
        "surface": "studio_node_inspector",
        "node": _node_to_dict(node),
        "edges": all_edges,
        "edge_count": len(all_edges),
        "neighbors": neighbors,
        "neighbor_count": len(neighbors),
        "snapshot_id": snapshot.snapshot_id,
        "boundary": _BOUNDARY,
    }


def search_nodes(
    vault_root: str | Path,
    query: str,
    *,
    limit: int = 20,
    node_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    Search graph nodes by label substring (case-insensitive).

    Optionally filter by node_type. Returns up to `limit` results.
    """
    vault = Path(vault_root).resolve()
    snapshot = _load_latest_snapshot(vault)
    if snapshot is None:
        return {
            "ok": False,
            "error": "No graph snapshot found. Run 'chaseos graph build' first.",
            "surface": "studio_graph_search",
            "boundary": _BOUNDARY,
        }

    index = _build_index(snapshot)
    if index is None:
        return {
            "ok": False,
            "error": "Failed to build graph index from snapshot.",
            "surface": "studio_graph_search",
            "boundary": _BOUNDARY,
        }

    q_lower = query.strip().lower()
    results = []

    if node_type:
        candidates = index.nodes_by_type.get(node_type, [])
    else:
        candidates = snapshot.nodes

    for node in candidates:
        if q_lower and q_lower not in node.label.lower():
            continue
        results.append(_node_to_dict(node))
        if len(results) >= limit:
            break

    return {
        "ok": True,
        "surface": "studio_graph_search",
        "query": query,
        "node_type_filter": node_type,
        "results": results,
        "result_count": len(results),
        "limit": limit,
        "snapshot_id": snapshot.snapshot_id,
        "boundary": _BOUNDARY,
    }


def get_community(vault_root: str | Path, community_id: int) -> dict[str, Any]:
    """
    Return a UI-ready community model: member nodes + cross-domain edges.
    """
    vault = Path(vault_root).resolve()
    snapshot = _load_latest_snapshot(vault)
    if snapshot is None:
        return {
            "ok": False,
            "error": "No graph snapshot found. Run 'chaseos graph build' first.",
            "surface": "studio_community_view",
            "boundary": _BOUNDARY,
        }

    index = _build_index(snapshot)
    if index is None:
        return {
            "ok": False,
            "error": "Failed to build graph index from snapshot.",
            "surface": "studio_community_view",
            "boundary": _BOUNDARY,
        }

    member_ids = set(index.nodes_by_community.get(community_id, []))
    if not member_ids:
        return {
            "ok": False,
            "error": f"Community {community_id} not found or empty.",
            "surface": "studio_community_view",
            "community_id": community_id,
            "boundary": _BOUNDARY,
        }

    members = [
        _node_to_dict(index.node_by_id[nid])
        for nid in member_ids
        if nid in index.node_by_id
    ]
    cross_edges = [
        _edge_to_dict(e)
        for e in snapshot.edges
        if (e.source_id in member_ids) != (e.target_id in member_ids)
    ]

    return {
        "ok": True,
        "surface": "studio_community_view",
        "community_id": community_id,
        "members": members,
        "member_count": len(members),
        "cross_domain_edges": cross_edges,
        "cross_domain_edge_count": len(cross_edges),
        "snapshot_id": snapshot.snapshot_id,
        "boundary": _BOUNDARY,
    }


def get_graph_stats(vault_root: str | Path) -> dict[str, Any]:
    """
    Return a UI-ready graph statistics model: counts, top nodes, health indicators.
    """
    vault = Path(vault_root).resolve()
    snapshot = _load_latest_snapshot(vault)
    if snapshot is None:
        return {
            "ok": False,
            "error": "No graph snapshot found. Run 'chaseos graph build' first.",
            "surface": "studio_graph_stats",
            "boundary": _BOUNDARY,
        }

    index = _build_index(snapshot)
    if index is None:
        return {
            "ok": False,
            "error": "Failed to build graph index from snapshot.",
            "surface": "studio_graph_stats",
            "boundary": _BOUNDARY,
        }

    node_count = len(snapshot.nodes)
    edge_count = len(snapshot.edges)

    # Node type breakdown using index
    type_counts = {nt: len(nodes) for nt, nodes in index.nodes_by_type.items()}

    # Confidence breakdown
    extracted = sum(1 for n in snapshot.nodes if n.confidence == "EXTRACTED")
    inferred = sum(1 for n in snapshot.nodes if n.confidence == "INFERRED")
    ambiguous = sum(1 for n in snapshot.nodes if n.confidence == "AMBIGUOUS")

    # Degree map from outgoing + incoming
    degree_map: dict[str, int] = {}
    for edge in snapshot.edges:
        degree_map[edge.source_id] = degree_map.get(edge.source_id, 0) + 1
        degree_map[edge.target_id] = degree_map.get(edge.target_id, 0) + 1

    top_node_ids = sorted(degree_map, key=lambda nid: degree_map[nid], reverse=True)[:10]
    top_nodes = []
    for nid in top_node_ids:
        node = index.node_by_id.get(nid)
        if node:
            top_nodes.append({**_node_to_dict(node), "degree": degree_map[nid]})

    community_count = len(index.nodes_by_community)

    return {
        "ok": True,
        "surface": "studio_graph_stats",
        "node_count": node_count,
        "edge_count": edge_count,
        "community_count": community_count,
        "node_type_breakdown": type_counts,
        "confidence_breakdown": {
            "EXTRACTED": extracted,
            "INFERRED": inferred,
            "AMBIGUOUS": ambiguous,
        },
        "top_nodes_by_degree": top_nodes,
        "snapshot_id": snapshot.snapshot_id,
        "boundary": _BOUNDARY,
    }
