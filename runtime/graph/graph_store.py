"""Read-only GraphStore abstraction for the ChaseOS shared graph model."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

from runtime.graph.graph_models import (
    GraphEdge,
    GraphNode,
    GraphScene,
    GraphSnapshot,
    RuntimeOverlayEvent,
    normalize_trust_state,
    stable_digest,
)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00").replace("z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _window_start(window: Any, *, now: datetime | None = None) -> datetime | None:
    if window in (None, "", "all"):
        return None
    now_dt = now or datetime.now(timezone.utc)
    if isinstance(window, datetime):
        return window
    if isinstance(window, (int, float)):
        return now_dt - timedelta(seconds=float(window))
    text = str(window).strip().lower()
    if text in {"today", "day"}:
        return now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if text in {"week", "this_week", "7d"}:
        return now_dt - timedelta(days=7)
    if text in {"24h", "1d"}:
        return now_dt - timedelta(days=1)
    if text.endswith("h") and text[:-1].isdigit():
        return now_dt - timedelta(hours=int(text[:-1]))
    if text.endswith("d") and text[:-1].isdigit():
        return now_dt - timedelta(days=int(text[:-1]))
    parsed = _parse_iso(text)
    return parsed


def _within_window(value: str | None, window: Any, *, now: datetime | None = None) -> bool:
    start = _window_start(window, now=now)
    if start is None:
        return True
    parsed = _parse_iso(value)
    return bool(parsed and parsed >= start)


def _matches_filters(node: GraphNode, filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    for key, raw_allowed in filters.items():
        if raw_allowed in (None, "", [], (), set()):
            continue
        allowed = set(raw_allowed if isinstance(raw_allowed, (list, tuple, set)) else [raw_allowed])
        value = getattr(node, key, None)
        if key == "trust_state":
            value = normalize_trust_state(value)
        if value not in allowed:
            return False
    return True


def _event_matches_filters(event: RuntimeOverlayEvent, filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    for key, raw_allowed in filters.items():
        if raw_allowed in (None, "", [], (), set()):
            continue
        allowed = set(raw_allowed if isinstance(raw_allowed, (list, tuple, set)) else [raw_allowed])
        value = getattr(event, key, None)
        if value not in allowed:
            return False
    return True


def _paths_match(node_path: str | None, event_path: str | None) -> bool:
    if not node_path or not event_path:
        return False
    node = str(node_path).replace("\\", "/").strip("/")
    event = str(event_path).replace("\\", "/").strip("/")
    return node == event or event.endswith(f"/{node}") or node.endswith(f"/{event}")


class InMemoryGraphStore:
    """Derived in-memory GraphStore.

    This is the first abstraction seam for scenes, local graph queries, and live
    overlays. It deliberately performs no filesystem writes and has no authority
    to mutate canonical graph state.
    """

    def __init__(self, snapshot: GraphSnapshot | None = None) -> None:
        self.snapshot = snapshot or GraphSnapshot.from_nodes_edges([], [])
        self.nodes_by_id: dict[str, GraphNode] = {node.node_id: node for node in self.snapshot.nodes}
        self.edges_by_id: dict[str, GraphEdge] = {edge.edge_id: edge for edge in self.snapshot.edges}
        self.outgoing: dict[str, list[GraphEdge]] = defaultdict(list)
        self.incoming: dict[str, list[GraphEdge]] = defaultdict(list)
        for edge in self.snapshot.edges:
            self.outgoing[edge.source_node_id].append(edge)
            self.incoming[edge.target_node_id].append(edge)
            if edge.direction == "undirected":
                self.outgoing[edge.target_node_id].append(edge)
                self.incoming[edge.source_node_id].append(edge)
        self._scenes: dict[str, GraphScene] = {}
        self._overlay_events: dict[str, RuntimeOverlayEvent] = {}

    @classmethod
    def from_snapshot(cls, snapshot: GraphSnapshot) -> "InMemoryGraphStore":
        return cls(snapshot)

    def get_graph_summary(self) -> dict[str, Any]:
        node_type_counts: dict[str, int] = {}
        trust_state_counts: dict[str, int] = {}
        edge_type_counts: dict[str, int] = {}
        for node in self.snapshot.nodes:
            node_type_counts[node.node_type] = node_type_counts.get(node.node_type, 0) + 1
            trust_state_counts[node.trust_state] = trust_state_counts.get(node.trust_state, 0) + 1
        for edge in self.snapshot.edges:
            edge_type_counts[edge.edge_type] = edge_type_counts.get(edge.edge_type, 0) + 1
        return {
            "graph_version": self.snapshot.graph_version.to_dict(),
            "node_count": self.snapshot.node_count,
            "edge_count": self.snapshot.edge_count,
            "node_type_counts": dict(sorted(node_type_counts.items())),
            "trust_state_counts": dict(sorted(trust_state_counts.items())),
            "edge_type_counts": dict(sorted(edge_type_counts.items())),
        }

    def search_nodes(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        *,
        limit: int = 50,
    ) -> list[GraphNode]:
        terms = [part.lower() for part in str(query or "").split() if part.strip()]
        matches: list[GraphNode] = []
        for node in self.snapshot.nodes:
            if not _matches_filters(node, filters):
                continue
            haystack = " ".join(
                str(part or "")
                for part in (
                    node.title,
                    node.label,
                    node.path,
                    node.node_type,
                    node.project,
                    node.domain,
                    node.runtime_id,
                    " ".join(node.tags),
                )
            ).lower()
            if not terms or all(term in haystack for term in terms):
                matches.append(node)
        return matches[: max(0, int(limit))]

    def get_node(self, node_id: str) -> GraphNode | None:
        return self.nodes_by_id.get(str(node_id))

    def get_neighbors(
        self,
        node_id: str,
        *,
        depth: int = 1,
        filters: dict[str, Any] | None = None,
        limit: int = 250,
    ) -> dict[str, Any]:
        root = str(node_id)
        if root not in self.nodes_by_id:
            return {"root_node_id": root, "nodes": [], "edges": []}
        max_depth = max(0, int(depth))
        max_items = max(0, int(limit))
        seen_nodes = {root}
        seen_edges: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(root, 0)])
        while queue and len(seen_nodes) < max_items:
            current, current_depth = queue.popleft()
            if current_depth >= max_depth:
                continue
            for edge in self.outgoing.get(current, []) + self.incoming.get(current, []):
                seen_edges.add(edge.edge_id)
                other = edge.target_node_id if edge.source_node_id == current else edge.source_node_id
                node = self.nodes_by_id.get(other)
                if node is None or not _matches_filters(node, filters):
                    continue
                if other not in seen_nodes:
                    seen_nodes.add(other)
                    queue.append((other, current_depth + 1))
                    if len(seen_nodes) >= max_items:
                        break
        nodes = [self.nodes_by_id[item] for item in sorted(seen_nodes) if item in self.nodes_by_id]
        node_ids = {node.node_id for node in nodes}
        edges = [
            edge
            for edge in self.snapshot.edges
            if edge.edge_id in seen_edges
            and edge.source_node_id in node_ids
            and edge.target_node_id in node_ids
        ]
        return {"root_node_id": root, "nodes": nodes, "edges": edges}

    def get_local_graph(
        self,
        node_id: str,
        *,
        depth: int = 1,
        filters: dict[str, Any] | None = None,
        limit: int = 250,
    ) -> GraphSnapshot:
        local = self.get_neighbors(node_id, depth=depth, filters=filters, limit=limit)
        return GraphSnapshot.from_nodes_edges(
            list(local["nodes"]),
            list(local["edges"]),
            metadata={
                "source": "in_memory_graph_store.local_graph",
                "root_node_id": node_id,
                "depth": depth,
                "parent_graph_version": self.snapshot.graph_version.graph_hash,
            },
        )

    def get_focus_graph(
        self,
        query_or_node_id: str,
        *,
        depth: int = 1,
        filters: dict[str, Any] | None = None,
        limit: int = 250,
    ) -> GraphSnapshot:
        if query_or_node_id in self.nodes_by_id:
            return self.get_local_graph(query_or_node_id, depth=depth, filters=filters, limit=limit)
        matches = self.search_nodes(query_or_node_id, filters=filters, limit=limit)
        match_ids = {node.node_id for node in matches}
        edges = [
            edge
            for edge in self.snapshot.edges
            if edge.source_node_id in match_ids and edge.target_node_id in match_ids
        ]
        return GraphSnapshot.from_nodes_edges(
            matches,
            edges,
            metadata={"source": "in_memory_graph_store.focus_graph", "query": query_or_node_id},
        )

    def get_approval_overlay(self, filters: dict[str, Any] | None = None) -> GraphSnapshot:
        approval_nodes = [
            node
            for node in self.snapshot.nodes
            if node.node_type == "approval" or node.trust_state in {"suggested", "quarantined", "disputed"}
            if _matches_filters(node, filters)
        ]
        ids = {node.node_id for node in approval_nodes}
        edges = [
            edge
            for edge in self.snapshot.edges
            if edge.edge_type in {"pending_approval", "approval_blocked", "blocked_by_policy"}
            or edge.source_node_id in ids
            or edge.target_node_id in ids
        ]
        edge_node_ids = {item for edge in edges for item in (edge.source_node_id, edge.target_node_id)}
        nodes = {node.node_id: node for node in approval_nodes}
        nodes.update({node_id: self.nodes_by_id[node_id] for node_id in edge_node_ids if node_id in self.nodes_by_id})
        return GraphSnapshot.from_nodes_edges(
            list(nodes.values()),
            edges,
            metadata={"source": "in_memory_graph_store.approval_overlay"},
        )

    def get_provenance_chain(self, node_id: str) -> GraphSnapshot:
        root = str(node_id)
        if root not in self.nodes_by_id:
            return GraphSnapshot.from_nodes_edges([], [], metadata={"source": "in_memory_graph_store.provenance_chain"})
        node_ids = {root}
        edges: list[GraphEdge] = []
        queue: deque[str] = deque([root])
        while queue:
            current = queue.popleft()
            for edge in self.incoming.get(current, []):
                if edge.edge_type not in {"provenance", "generated_from", "canonicalized_from", "source_derived"}:
                    continue
                edges.append(edge)
                if edge.source_node_id not in node_ids:
                    node_ids.add(edge.source_node_id)
                    queue.append(edge.source_node_id)
        nodes = [self.nodes_by_id[item] for item in sorted(node_ids) if item in self.nodes_by_id]
        return GraphSnapshot.from_nodes_edges(nodes, edges, metadata={"source": "in_memory_graph_store.provenance_chain"})

    def get_hygiene_graph(self, filters: dict[str, Any] | None = None) -> GraphSnapshot:
        hygiene_nodes = [
            node
            for node in self.snapshot.nodes
            if node.trust_state in {"unknown", "disputed", "quarantined"} or (node.metadata.get("warnings") or [])
            if _matches_filters(node, filters)
        ]
        ids = {node.node_id for node in hygiene_nodes}
        edges = [edge for edge in self.snapshot.edges if edge.source_node_id in ids or edge.target_node_id in ids]
        return GraphSnapshot.from_nodes_edges(
            hygiene_nodes,
            edges,
            metadata={"source": "in_memory_graph_store.hygiene_graph"},
        )

    def get_recent_activity_graph(self, *, window: Any = None, limit: int = 100) -> GraphSnapshot:
        nodes = sorted(
            [
                node
                for node in self.snapshot.nodes
                if _within_window(node.modified_at or node.updated_at or node.created_at, window)
            ],
            key=lambda node: node.modified_at or node.updated_at or node.created_at or "",
            reverse=True,
        )[: max(0, int(limit))]
        ids = {node.node_id for node in nodes}
        edges = [edge for edge in self.snapshot.edges if edge.source_node_id in ids and edge.target_node_id in ids]
        return GraphSnapshot.from_nodes_edges(
            nodes,
            edges,
            metadata={"source": "in_memory_graph_store.recent_activity_graph", "window": window},
        )

    def get_runtime_trail(
        self,
        runtime_id: str,
        *,
        window: Any = None,
        filters: dict[str, Any] | None = None,
        limit: int = 250,
    ) -> GraphSnapshot:
        runtime = str(runtime_id)
        max_items = max(0, int(limit))
        runtime_nodes = [
            node
            for node in self.snapshot.nodes
            if node.runtime_id == runtime or node.node_id == runtime or node.label == runtime
        ]
        touched_nodes: dict[str, GraphNode] = {node.node_id: node for node in runtime_nodes if _matches_filters(node, filters)}
        trail_edges: dict[str, GraphEdge] = {}
        trail_events = [
            event
            for event in self.list_overlay_events(include_expired=True)
            if event.runtime_id == runtime or event.agent_id == runtime
            if _within_window(event.timestamp, window)
            if _event_matches_filters(event, filters)
        ]
        for edge in self.snapshot.edges:
            if edge.runtime_id == runtime or edge.edge_type in {"runtime_touch", "touched_by_agent", "produced_by_runtime"}:
                if edge.source_node_id in self.nodes_by_id and edge.target_node_id in self.nodes_by_id:
                    source = self.nodes_by_id[edge.source_node_id]
                    target = self.nodes_by_id[edge.target_node_id]
                    if source.runtime_id == runtime or target.runtime_id == runtime or edge.runtime_id == runtime:
                        if _matches_filters(source, filters):
                            touched_nodes[source.node_id] = source
                        if _matches_filters(target, filters):
                            touched_nodes[target.node_id] = target
                        trail_edges[edge.edge_id] = edge
        for event in trail_events:
            event_node = GraphNode(
                node_id=f"event:{event.event_id}",
                stable_key=f"runtime-event:{event.event_id}",
                title=event.event_type.replace("_", " ").title(),
                label=event.event_type,
                node_type="log",
                source_kind="runtime_overlay_event",
                runtime_id=runtime,
                trust_state="raw",
                created_at=event.timestamp,
                updated_at=event.timestamp,
                metadata=event.to_dict(),
            )
            touched_nodes[event_node.node_id] = event_node
            if event.node_id and event.node_id in self.nodes_by_id and _matches_filters(self.nodes_by_id[event.node_id], filters):
                touched_nodes[event.node_id] = self.nodes_by_id[event.node_id]
                trail_edges[f"event-edge:{event.event_id}:{event.node_id}"] = GraphEdge(
                    edge_id=f"event-edge:{event.event_id}:{event.node_id}",
                    source_node_id=event_node.node_id,
                    target_node_id=event.node_id,
                    edge_type="runtime_touch",
                    runtime_id=runtime,
                    created_at=event.timestamp,
                    metadata={"source": "runtime_overlay_event", "event_id": event.event_id},
                )
            if event.file_path:
                for node in self.snapshot.nodes:
                    if _paths_match(node.path, event.file_path) and _matches_filters(node, filters):
                        touched_nodes[node.node_id] = node
                        trail_edges[f"event-edge:{event.event_id}:{node.node_id}"] = GraphEdge(
                            edge_id=f"event-edge:{event.event_id}:{node.node_id}",
                            source_node_id=event_node.node_id,
                            target_node_id=node.node_id,
                            edge_type="runtime_touch",
                            runtime_id=runtime,
                            created_at=event.timestamp,
                            metadata={"source": "runtime_overlay_event", "event_id": event.event_id},
                        )
        nodes = list(touched_nodes.values())[:max_items]
        node_ids = {node.node_id for node in nodes}
        edges = [edge for edge in trail_edges.values() if edge.source_node_id in node_ids and edge.target_node_id in node_ids]
        return GraphSnapshot.from_nodes_edges(
            nodes,
            edges[:max_items],
            metadata={
                "source": "in_memory_graph_store.runtime_trail",
                "runtime_id": runtime,
                "window": window,
                "event_count": len(trail_events),
                "parent_graph_version": self.snapshot.graph_version.graph_hash,
            },
        )

    def get_agent_touch_heatmap(
        self,
        *,
        runtime_id: str | None = None,
        window: Any = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        touch_counts: dict[str, dict[str, Any]] = {}
        for edge in self.snapshot.edges:
            if edge.edge_type not in {"runtime_touch", "touched_by_agent", "produced_by_runtime"}:
                continue
            source_node = self.nodes_by_id.get(edge.source_node_id)
            runtime = edge.runtime_id or (source_node.runtime_id if source_node else None)
            if runtime_id and runtime != runtime_id:
                continue
            for node_id in (edge.source_node_id, edge.target_node_id):
                node = self.nodes_by_id.get(node_id)
                if node is None or not _matches_filters(node, filters):
                    continue
                item = touch_counts.setdefault(
                    node.node_id,
                    {
                        "node": node,
                        "touch_count": 0,
                        "runtime_counts": {},
                        "last_touch_at": None,
                        "event_ids": [],
                    },
                )
                item["touch_count"] += 1
                if runtime:
                    item["runtime_counts"][runtime] = item["runtime_counts"].get(runtime, 0) + 1
        for event in self.list_overlay_events(include_expired=True):
            if runtime_id and event.runtime_id != runtime_id and event.agent_id != runtime_id:
                continue
            if not _within_window(event.timestamp, window):
                continue
            if not _event_matches_filters(event, filters):
                continue
            candidate_ids: set[str] = set()
            if event.node_id:
                candidate_ids.add(event.node_id)
            if event.file_path:
                candidate_ids.update(node.node_id for node in self.snapshot.nodes if _paths_match(node.path, event.file_path))
            for node_id in candidate_ids:
                node = self.nodes_by_id.get(node_id)
                if node is None or not _matches_filters(node, filters):
                    continue
                item = touch_counts.setdefault(
                    node.node_id,
                    {
                        "node": node,
                        "touch_count": 0,
                        "runtime_counts": {},
                        "last_touch_at": None,
                        "event_ids": [],
                    },
                )
                item["touch_count"] += 1
                runtime = event.runtime_id or event.agent_id or "unknown"
                item["runtime_counts"][runtime] = item["runtime_counts"].get(runtime, 0) + 1
                item["event_ids"].append(event.event_id)
                if item["last_touch_at"] is None or event.timestamp > item["last_touch_at"]:
                    item["last_touch_at"] = event.timestamp
        nodes = [item["node"] for item in touch_counts.values()]
        node_ids = {node.node_id for node in nodes}
        edges = [
            edge
            for edge in self.snapshot.edges
            if edge.source_node_id in node_ids and edge.target_node_id in node_ids
        ]
        graph = GraphSnapshot.from_nodes_edges(
            nodes,
            edges,
            metadata={
                "source": "in_memory_graph_store.agent_touch_heatmap",
                "runtime_id": runtime_id,
                "window": window,
                "parent_graph_version": self.snapshot.graph_version.graph_hash,
            },
        )
        summary = [
            {
                "node_id": node_id,
                "path": item["node"].path,
                "source_path": item["node"].path,
                "label": item["node"].label,
                "node_type": item["node"].node_type,
                "touch_count": item["touch_count"],
                "runtime_counts": dict(sorted(item["runtime_counts"].items())),
                "last_touch_at": item["last_touch_at"],
                "event_ids": list(item["event_ids"]),
            }
            for node_id, item in sorted(touch_counts.items())
        ]
        return {"graph": graph, "touches": summary}

    def save_scene(self, scene: GraphScene) -> GraphScene:
        updated = replace(scene, updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        self._scenes[updated.scene_id] = updated
        return updated

    def get_scene(self, scene_id: str) -> GraphScene | None:
        scene = self._scenes.get(str(scene_id))
        if scene is None:
            return None
        updated = replace(scene, last_used_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        self._scenes[updated.scene_id] = updated
        return updated

    def list_scenes(self) -> list[GraphScene]:
        return sorted(self._scenes.values(), key=lambda scene: scene.last_used_at, reverse=True)

    def close_scene(self, scene_id: str) -> bool:
        return self._scenes.pop(str(scene_id), None) is not None

    def update_scene(self, scene_id: str, patch: dict[str, Any]) -> GraphScene | None:
        current = self._scenes.get(str(scene_id))
        if current is None:
            return None
        data = current.to_dict()
        data.update(dict(patch))
        updated = GraphScene.from_dict(data)
        self._scenes[updated.scene_id] = updated
        return updated

    def add_overlay_event(self, event: RuntimeOverlayEvent) -> RuntimeOverlayEvent:
        self._overlay_events[event.event_id] = event
        return event

    def list_overlay_events(self, *, include_expired: bool = False, now: datetime | None = None) -> list[RuntimeOverlayEvent]:
        now_dt = now or datetime.now(timezone.utc)
        events: list[RuntimeOverlayEvent] = []
        expired_ids: list[str] = []
        for event in self._overlay_events.values():
            timestamp = _parse_iso(event.timestamp)
            expired = bool(timestamp and event.ttl_seconds and (now_dt - timestamp).total_seconds() > event.ttl_seconds)
            if expired and not include_expired:
                expired_ids.append(event.event_id)
                continue
            events.append(event)
        for event_id in expired_ids:
            self._overlay_events.pop(event_id, None)
        return sorted(events, key=lambda event: event.timestamp, reverse=True)

    def make_scene_id(self, title: str, lens_type: str, query: str | None = None) -> str:
        return f"scene-{stable_digest([title, lens_type, query, self.snapshot.graph_version.graph_hash], length=16)}"
