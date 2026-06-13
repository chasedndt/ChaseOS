"""Graph scene and lens helpers for the shared ChaseOS graph substrate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.graph.graph_models import GraphScene, GraphSnapshot, stable_digest


BUILT_IN_LENSES = {
    "current_workspace": {
        "title": "Current Workspace",
        "layout_mode": "clustered_2d",
        "renderer_mode": "2d",
        "description": "Workspace-scoped graph slice, not an all-graph hairball.",
    },
    "recent_activity": {
        "title": "Recent Activity",
        "layout_mode": "timeline_2d",
        "renderer_mode": "2d",
        "description": "Recently changed or touched nodes.",
    },
    "pending_attention": {
        "title": "Pending Attention",
        "layout_mode": "governance_2d",
        "renderer_mode": "2d",
        "description": "Approvals, quarantined, disputed, and graph-hygiene candidates.",
    },
    "local_neighborhood": {
        "title": "Local Neighborhood",
        "layout_mode": "local_neighborhood_2d",
        "renderer_mode": "2d",
        "description": "Selected/root node plus bounded neighbor depth.",
    },
    "runtime_trail": {
        "title": "Runtime Trail",
        "layout_mode": "runtime_trail_2d",
        "renderer_mode": "2d",
        "description": "Runtime node, events, touched nodes, outputs, and approvals.",
    },
    "agent_touch_heatmap": {
        "title": "Agent Touch Heatmap",
        "layout_mode": "heatmap_2d",
        "renderer_mode": "2d",
        "description": "Nodes touched by one or more runtimes.",
    },
    "approval_overlay": {
        "title": "Approval Overlay",
        "layout_mode": "governance_2d",
        "renderer_mode": "2d",
        "description": "Approval packets and affected graph nodes.",
    },
    "trust_overlay": {
        "title": "Trust Overlay",
        "layout_mode": "clustered_2d",
        "renderer_mode": "2d",
        "description": "Raw, quarantined, suggested, promoted, canonical, generated, archived, and disputed nodes.",
    },
    "provenance_chain": {
        "title": "Provenance Chain",
        "layout_mode": "dag_2d",
        "renderer_mode": "2d",
        "description": "Source-to-output chain for a selected node.",
    },
    "hygiene_issues": {
        "title": "Hygiene Issues",
        "layout_mode": "hygiene_2d",
        "renderer_mode": "2d",
        "description": "Orphans, unresolved links, stale nodes, disputed nodes, and review candidates.",
    },
}

DEFAULT_LENS_ORDER = ("current_workspace", "recent_activity", "pending_attention")


@dataclass(frozen=True)
class GraphLensResult:
    lens_type: str
    title: str
    scene: GraphScene
    graph: GraphSnapshot
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "lens_type": self.lens_type,
            "title": self.title,
            "scene": self.scene.to_dict(),
            "graph": self.graph.to_dict(),
            "summary": dict(self.summary),
        }


def list_builtin_lenses() -> list[dict[str, Any]]:
    return [
        {"lens_type": lens_type, **BUILT_IN_LENSES[lens_type]}
        for lens_type in DEFAULT_LENS_ORDER
    ] + [
        {"lens_type": lens_type, **payload}
        for lens_type, payload in BUILT_IN_LENSES.items()
        if lens_type not in DEFAULT_LENS_ORDER
    ]


def make_scene_id(
    *,
    lens_type: str,
    graph_version: str,
    title: str | None = None,
    query: str | None = None,
    root_node_id: str | None = None,
) -> str:
    return f"scene-{stable_digest([lens_type, graph_version, title, query, root_node_id], length=16)}"


def create_scene_for_lens(
    lens_type: str,
    *,
    graph_version: str,
    title: str | None = None,
    query: str | None = None,
    root_node_id: str | None = None,
    depth: int = 1,
    filters: dict[str, Any] | None = None,
    pinned_node_ids: tuple[str, ...] = (),
    selected_node_id: str | None = None,
) -> GraphScene:
    lens = BUILT_IN_LENSES.get(lens_type, BUILT_IN_LENSES["current_workspace"])
    scene_title = title or lens["title"]
    return GraphScene(
        scene_id=make_scene_id(
            lens_type=lens_type,
            graph_version=graph_version,
            title=scene_title,
            query=query,
            root_node_id=root_node_id,
        ),
        title=scene_title,
        lens_type=lens_type,
        query=query,
        root_node_id=root_node_id,
        depth=depth,
        filters=dict(filters or {}),
        layout_mode=str(lens["layout_mode"]),
        renderer_mode=str(lens["renderer_mode"]),
        pinned_node_ids=pinned_node_ids,
        selected_node_id=selected_node_id,
        graph_version=graph_version,
    )


def choose_default_scene(existing_scenes: list[GraphScene], graph_version: str) -> GraphScene:
    if existing_scenes:
        return sorted(existing_scenes, key=lambda scene: scene.last_used_at, reverse=True)[0]
    return create_scene_for_lens("recent_activity", graph_version=graph_version)
