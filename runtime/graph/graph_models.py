"""Shared graph model layer for ChaseOS Studio Graph.

These dataclasses normalize the existing runtime graph snapshot model and the
Studio graph contract into one renderer/query-neutral shape. They are derived
artifacts only: this module does not read or write source files, consume
approvals, dispatch runtimes, or mutate canonical graph state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


TRUST_STATES = frozenset(
    {
        "raw",
        "quarantined",
        "suggested",
        "promoted",
        "canonical",
        "archived",
        "disputed",
        "generated",
        "unknown",
    }
)

NODE_TYPES = frozenset(
    {
        "project",
        "domain",
        "doc",
        "runtime_profile",
        "runtime",
        "agent",
        "source_package",
        "memory_node",
        "approval",
        "log",
        "audit",
        "workflow",
        "artifact",
        "decision",
        "template",
        "sop",
        "generated",
        "unknown",
    }
)

EDGE_TYPES = frozenset(
    {
        "explicit_link",
        "structural_link",
        "backlink",
        "source_derived",
        "provenance",
        "runtime_touch",
        "touched_by_agent",
        "used_by_workflow",
        "produced_by_runtime",
        "pending_approval",
        "blocked_by_policy",
        "linked_to_audit_log",
        "generated_from",
        "canonicalized_from",
        "suggested_semantic",
        "unknown",
    }
)

RUNTIME_OVERLAY_EVENT_TYPES = frozenset(
    {
        "runtime_heartbeat",
        "daemon_heartbeat",
        "task_claimed",
        "task_started",
        "node_read_started",
        "node_read_finished",
        "node_edit_started",
        "node_edit_finished",
        "node_touch_started",
        "node_touch_finished",
        "approval_requested",
        "approval_blocked",
        "artifact_generated",
        "log_written",
        "run_failed",
        "run_completed",
        "daemon_degraded",
        "unknown",
    }
)

MODEL_VERSION = "chaseos.graph.shared.v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_digest(payload: Any, *, length: int = 20) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:length]


def normalize_trust_state(value: Any) -> str:
    normalized = str(value or "unknown").strip().lower().replace("-", "_")
    return normalized if normalized in TRUST_STATES else "unknown"


def normalize_node_type(value: Any) -> str:
    raw = str(value or "unknown").strip().lower()
    if raw in NODE_TYPES:
        return raw
    if raw.endswith("_doc") or raw in {"markdown_note", "system_root_doc", "chaseos_markdown_doc", "file", "doc_section"}:
        return "doc"
    if "runtime" in raw and "profile" in raw:
        return "runtime_profile"
    if raw in {"build_log", "daily_note", "documentation_history_note"}:
        return "log"
    if raw in {"agent_control_doc", "agent"}:
        return "agent"
    return raw or "unknown"


def normalize_edge_type(value: Any) -> str:
    raw = str(value or "unknown").strip().lower().replace("-", "_")
    if raw in EDGE_TYPES:
        return raw
    if raw.startswith("links_to") or raw in {"references", "section_links", "explicit"}:
        return "explicit_link"
    if raw.startswith("contains_") or raw in {"file_contains", "has_tag", "defines"}:
        return "structural_link"
    if "unresolved" in raw or "external" in raw or "suggested" in raw:
        return "suggested_semantic"
    if "approval" in raw and "block" in raw:
        return "blocked_by_policy"
    if "approval" in raw:
        return "pending_approval"
    if "policy" in raw or "blocked" in raw:
        return "blocked_by_policy"
    if "workflow" in raw:
        return "used_by_workflow"
    if "runtime" in raw or "agent" in raw or "touch" in raw:
        return "runtime_touch"
    if "provenance" in raw:
        return "provenance"
    if "generated" in raw:
        return "generated_from"
    if "canonical" in raw:
        return "canonicalized_from"
    return "unknown"


def normalize_overlay_event_type(value: Any) -> str:
    raw = str(value or "unknown").strip().lower().replace("-", "_")
    if raw in RUNTIME_OVERLAY_EVENT_TYPES:
        return raw
    if raw in {"heartbeat", "runtime_liveness"}:
        return "runtime_heartbeat"
    if raw in {"claimed"}:
        return "task_claimed"
    if raw in {"started", "in_progress"}:
        return "task_started"
    if raw in {"completed", "complete", "done"}:
        return "run_completed"
    if raw in {"failed", "error"}:
        return "run_failed"
    if raw in {"blocked"}:
        return "approval_blocked"
    return "unknown"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    stable_key: str
    title: str
    label: str
    node_type: str = "unknown"
    path: str | None = None
    source_kind: str = "unknown"
    trust_state: str = "unknown"
    provenance_id: str | None = None
    provenance_summary: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    modified_at: str | None = None
    tags: tuple[str, ...] = ()
    runtime_id: str | None = None
    workspace_id: str | None = None
    project: str | None = None
    domain: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_type", normalize_node_type(self.node_type))
        object.__setattr__(self, "trust_state", normalize_trust_state(self.trust_state))
        object.__setattr__(self, "tags", tuple(str(tag) for tag in self.tags))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphNode":
        data = dict(payload)
        data["tags"] = tuple(data.get("tags") or ())
        return cls(**data)


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str = "unknown"
    direction: str = "directed"
    trust_state: str = "unknown"
    provenance_id: str | None = None
    runtime_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_type", normalize_edge_type(self.edge_type))
        object.__setattr__(self, "trust_state", normalize_trust_state(self.trust_state))
        if self.direction not in {"directed", "undirected"}:
            object.__setattr__(self, "direction", "directed")
        object.__setattr__(self, "weight", float(self.weight))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphEdge":
        return cls(**dict(payload))


@dataclass(frozen=True)
class GraphVersion:
    graph_hash: str
    node_count: int
    edge_count: int
    generated_at: str
    model_version: str = MODEL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_graph(cls, nodes: list[GraphNode], edges: list[GraphEdge]) -> "GraphVersion":
        payload = {
            "nodes": [node.to_dict() for node in sorted(nodes, key=lambda item: item.node_id)],
            "edges": [edge.to_dict() for edge in sorted(edges, key=lambda item: item.edge_id)],
        }
        return cls(
            graph_hash=stable_digest(payload, length=32),
            node_count=len(nodes),
            edge_count=len(edges),
            generated_at=utc_now_iso(),
        )


@dataclass(frozen=True)
class GraphSnapshot:
    snapshot_id: str
    created_at: str
    graph_version: GraphVersion
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "graph_version": self.graph_version.to_dict(),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphSnapshot":
        return cls(
            snapshot_id=str(payload["snapshot_id"]),
            created_at=str(payload["created_at"]),
            graph_version=GraphVersion(**dict(payload["graph_version"])),
            nodes=tuple(GraphNode.from_dict(item) for item in payload.get("nodes", [])),
            edges=tuple(GraphEdge.from_dict(item) for item in payload.get("edges", [])),
            metadata=dict(payload.get("metadata") or {}),
        )

    @classmethod
    def from_nodes_edges(
        cls,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        *,
        snapshot_id: str | None = None,
        created_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "GraphSnapshot":
        version = GraphVersion.from_graph(nodes, edges)
        return cls(
            snapshot_id=snapshot_id or f"shared-{version.graph_hash[:16]}",
            created_at=created_at or version.generated_at,
            graph_version=version,
            nodes=tuple(nodes),
            edges=tuple(edges),
            metadata=metadata or {},
        )

    @classmethod
    def from_runtime_snapshot(cls, snapshot: Any) -> "GraphSnapshot":
        nodes: list[GraphNode] = []
        for node in getattr(snapshot, "nodes", []) or []:
            props = dict(getattr(node, "properties", {}) or {})
            nodes.append(
                GraphNode(
                    node_id=str(getattr(node, "node_id")),
                    stable_key=str(props.get("stable_key") or getattr(node, "source_file", "") or getattr(node, "node_id")),
                    title=str(getattr(node, "label", "")),
                    label=str(getattr(node, "label", "")),
                    node_type=normalize_node_type(getattr(node, "node_type", "unknown")),
                    path=getattr(node, "source_file", None),
                    source_kind=str(props.get("source_kind") or "runtime_graph_snapshot"),
                    trust_state=props.get("trust_state") or "unknown",
                    provenance_id=props.get("provenance_id"),
                    provenance_summary=str(getattr(node, "provenance", "") or "") or None,
                    created_at=props.get("created_at"),
                    updated_at=props.get("updated_at"),
                    modified_at=props.get("modified_at"),
                    tags=tuple(props.get("tags") or ()),
                    runtime_id=props.get("runtime_id"),
                    workspace_id=props.get("workspace_id"),
                    project=getattr(node, "project", None),
                    domain=getattr(node, "domain", None),
                    metadata=props,
                )
            )
        edges: list[GraphEdge] = []
        for edge in getattr(snapshot, "edges", []) or []:
            props = dict(getattr(edge, "properties", {}) or {})
            edges.append(
                GraphEdge(
                    edge_id=str(getattr(edge, "edge_id")),
                    source_node_id=str(getattr(edge, "source_id")),
                    target_node_id=str(getattr(edge, "target_id")),
                    edge_type=normalize_edge_type(getattr(edge, "relation", "unknown")),
                    trust_state=props.get("trust_state") or "unknown",
                    provenance_id=props.get("provenance_id"),
                    runtime_id=props.get("runtime_id"),
                    created_at=props.get("created_at"),
                    updated_at=props.get("updated_at"),
                    weight=float(props.get("weight") or 1.0),
                    metadata={**props, "relation": getattr(edge, "relation", "unknown"), "provenance": getattr(edge, "provenance", "")},
                )
            )
        return cls.from_nodes_edges(
            nodes,
            edges,
            snapshot_id=str(getattr(snapshot, "snapshot_id", "")) or None,
            created_at=str(getattr(snapshot, "created_at", "")) or None,
            metadata={"source_model": "runtime.graph.GraphSnapshot"},
        )

    @classmethod
    def from_studio_contract(cls, contract: dict[str, Any]) -> "GraphSnapshot":
        graph_payload = contract.get("graph") or contract.get("source_graph", {}).get("graph") or contract.get("view_model") or {}
        raw_nodes = list(graph_payload.get("nodes") or [])
        raw_edges = list(graph_payload.get("edges") or [])
        nodes: list[GraphNode] = []
        for node in raw_nodes:
            props = dict(node.get("properties") or {})
            path = props.get("path") or props.get("source_path") or node.get("path")
            label = str(node.get("label") or node.get("title") or node.get("id"))
            nodes.append(
                GraphNode(
                    node_id=str(node.get("id")),
                    stable_key=str(node.get("stable_key") or path or node.get("id")),
                    title=str(node.get("title") or label),
                    label=label,
                    node_type=node.get("node_type") or "unknown",
                    path=path,
                    source_kind=str(props.get("source_kind") or node.get("source") or "studio_graph_contract"),
                    trust_state=props.get("trust_state") or node.get("trust_state") or "unknown",
                    provenance_id=props.get("provenance_id"),
                    provenance_summary=props.get("provenance_summary") or node.get("source"),
                    created_at=props.get("created_at"),
                    updated_at=props.get("updated_at"),
                    modified_at=props.get("modified_at") or node.get("modified_at"),
                    tags=tuple(props.get("tags") or node.get("tags") or ()),
                    runtime_id=props.get("runtime_id") or node.get("runtime_id"),
                    workspace_id=props.get("workspace_id") or node.get("workspace_id"),
                    project=props.get("project") or node.get("project"),
                    domain=props.get("domain") or node.get("domain"),
                    metadata=props,
                )
            )
        edges: list[GraphEdge] = []
        for edge in raw_edges:
            props = dict(edge.get("properties") or {})
            relation = edge.get("relation") or edge.get("edge_type") or props.get("edge_type")
            edges.append(
                GraphEdge(
                    edge_id=str(edge.get("id") or stable_digest(edge)),
                    source_node_id=str(edge.get("source") or edge.get("source_node_id")),
                    target_node_id=str(edge.get("target") or edge.get("target_node_id")),
                    edge_type=props.get("edge_type") or relation or "unknown",
                    trust_state=props.get("trust_state") or edge.get("trust_state") or "unknown",
                    provenance_id=props.get("provenance_id"),
                    runtime_id=props.get("runtime_id") or edge.get("runtime_id"),
                    created_at=props.get("created_at"),
                    updated_at=props.get("updated_at"),
                    weight=float(props.get("weight") or edge.get("weight") or 1.0),
                    metadata={**props, "relation": relation, "source_contract": edge.get("source_contract")},
                )
            )
        return cls.from_nodes_edges(
            nodes,
            edges,
            snapshot_id=str(contract.get("snapshot_id") or "") or None,
            created_at=str(contract.get("generated_at") or "") or None,
            metadata={"source_model": contract.get("model_version") or "studio.graph_contract"},
        )


@dataclass(frozen=True)
class GraphScene:
    scene_id: str
    title: str
    lens_type: str
    query: str | None = None
    root_node_id: str | None = None
    depth: int = 1
    filters: dict[str, Any] = field(default_factory=dict)
    layout_mode: str = "force_2d"
    renderer_mode: str = "2d"
    pinned_node_ids: tuple[str, ...] = ()
    selected_node_id: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    last_used_at: str = field(default_factory=utc_now_iso)
    graph_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "depth", max(0, int(self.depth)))
        object.__setattr__(self, "pinned_node_ids", tuple(str(item) for item in self.pinned_node_ids))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pinned_node_ids"] = list(self.pinned_node_ids)
        return data

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphScene":
        data = dict(payload)
        data["pinned_node_ids"] = tuple(data.get("pinned_node_ids") or ())
        return cls(**data)


@dataclass(frozen=True)
class RuntimeOverlayEvent:
    event_id: str
    timestamp: str
    runtime_id: str | None = None
    agent_id: str | None = None
    event_type: str = "unknown"
    node_id: str | None = None
    file_path: str | None = None
    task_id: str | None = None
    run_id: str | None = None
    status: str | None = None
    confidence: str = "observed"
    source: str = "unknown"
    ttl_seconds: int = 900
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", normalize_overlay_event_type(self.event_type))
        object.__setattr__(self, "ttl_seconds", max(0, int(self.ttl_seconds)))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuntimeOverlayEvent":
        return cls(**dict(payload))
