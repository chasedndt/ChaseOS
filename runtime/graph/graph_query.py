"""Read-only query facade for shared ChaseOS graph models."""

from __future__ import annotations

from typing import Any

from runtime.graph.graph_models import GraphScene, GraphSnapshot
from runtime.graph.graph_scenes import GraphLensResult, choose_default_scene, create_scene_for_lens, list_builtin_lenses
from runtime.graph.graph_store import InMemoryGraphStore


class GraphQuery:
    """Small facade matching the target Graph page query vocabulary."""

    def __init__(self, store: InMemoryGraphStore) -> None:
        self.store = store

    @classmethod
    def from_snapshot(cls, snapshot: GraphSnapshot) -> "GraphQuery":
        return cls(InMemoryGraphStore.from_snapshot(snapshot))

    def get_graph_summary(self) -> dict[str, Any]:
        return self.store.get_graph_summary()

    def list_builtin_lenses(self):
        return list_builtin_lenses()

    def choose_default_scene(self):
        return choose_default_scene(self.store.list_scenes(), self.store.snapshot.graph_version.graph_hash)

    def create_scene_for_lens(
        self,
        lens_type: str,
        *,
        title: str | None = None,
        query: str | None = None,
        root_node_id: str | None = None,
        depth: int = 1,
        filters: dict[str, Any] | None = None,
    ) -> GraphScene:
        scene = create_scene_for_lens(
            lens_type,
            graph_version=self.store.snapshot.graph_version.graph_hash,
            title=title,
            query=query,
            root_node_id=root_node_id,
            depth=depth,
            filters=filters,
        )
        return self.store.save_scene(scene)

    def open_scene_for_lens(
        self,
        lens_type: str,
        *,
        query: str | None = None,
        root_node_id: str | None = None,
        depth: int = 1,
        filters: dict[str, Any] | None = None,
        window=None,
        limit: int = 250,
    ) -> GraphLensResult:
        scene = self.create_scene_for_lens(
            lens_type,
            query=query,
            root_node_id=root_node_id,
            depth=depth,
            filters=filters,
        )
        if lens_type == "local_neighborhood" and root_node_id:
            graph = self.get_local_graph(root_node_id, depth=depth, filters=filters, limit=limit)
        elif lens_type == "local_neighborhood" and query:
            graph = self.get_focus_graph(query, depth=depth, filters=filters)
        elif lens_type in {"current_workspace", "trust_overlay"}:
            graph = self.store.snapshot
        elif lens_type == "runtime_trail" and query:
            graph = self.get_runtime_trail(query, window=window, filters=filters, limit=limit)
        elif lens_type == "agent_touch_heatmap":
            heatmap = self.get_agent_touch_heatmap(runtime_id=query, window=window, filters=filters)
            graph = heatmap["graph"]
        elif lens_type == "approval_overlay" or lens_type == "pending_attention":
            graph = self.get_approval_overlay(filters)
        elif lens_type == "provenance_chain" and root_node_id:
            graph = self.get_provenance_chain(root_node_id)
        elif lens_type == "hygiene_issues":
            graph = self.get_hygiene_graph(filters)
        elif lens_type == "recent_activity":
            graph = self.get_recent_activity_graph(window=window, limit=limit)
        elif root_node_id:
            graph = self.get_local_graph(root_node_id, depth=depth, filters=filters, limit=limit)
        elif query:
            graph = self.get_focus_graph(query, depth=depth, filters=filters)
        else:
            graph = self.get_recent_activity_graph(window=window, limit=limit)
        return GraphLensResult(
            lens_type=lens_type,
            title=scene.title,
            scene=scene,
            graph=graph,
            summary={"node_count": graph.node_count, "edge_count": graph.edge_count},
        )

    def search_nodes(self, query: str, filters: dict[str, Any] | None = None, limit: int = 50):
        return self.store.search_nodes(query, filters, limit=limit)

    def get_node(self, node_id: str):
        return self.store.get_node(node_id)

    def get_neighbors(self, node_id: str, depth: int = 1, filters: dict[str, Any] | None = None, limit: int = 250):
        return self.store.get_neighbors(node_id, depth=depth, filters=filters, limit=limit)

    def get_local_graph(self, node_id: str, depth: int = 1, filters: dict[str, Any] | None = None, limit: int = 250):
        return self.store.get_local_graph(node_id, depth=depth, filters=filters, limit=limit)

    def get_focus_graph(self, query_or_node_id: str, depth: int = 1, filters: dict[str, Any] | None = None):
        return self.store.get_focus_graph(query_or_node_id, depth=depth, filters=filters)

    def get_runtime_trail(self, runtime_id: str, window=None, filters: dict[str, Any] | None = None, limit: int = 250):
        return self.store.get_runtime_trail(runtime_id, window=window, filters=filters, limit=limit)

    def get_agent_touch_heatmap(self, runtime_id: str | None = None, window=None, filters: dict[str, Any] | None = None):
        return self.store.get_agent_touch_heatmap(runtime_id=runtime_id, window=window, filters=filters)

    def get_approval_overlay(self, filters: dict[str, Any] | None = None):
        return self.store.get_approval_overlay(filters)

    def get_provenance_chain(self, node_id: str):
        return self.store.get_provenance_chain(node_id)

    def get_hygiene_graph(self, filters: dict[str, Any] | None = None):
        return self.store.get_hygiene_graph(filters)

    def get_recent_activity_graph(self, window=None, limit: int = 100):
        return self.store.get_recent_activity_graph(window=window, limit=limit)

    def get_scene(self, scene_id: str):
        return self.store.get_scene(scene_id)

    def save_scene(self, scene: GraphScene):
        return self.store.save_scene(scene)

    def list_scenes(self):
        return self.store.list_scenes()

    def close_scene(self, scene_id: str):
        return self.store.close_scene(scene_id)

    def update_scene(self, scene_id: str, patch: dict[str, Any]):
        return self.store.update_scene(scene_id, patch)
