"""Read-only durable node identity registry resolver.

The registry maps stable derived source keys to reviewed durable node IDs. Loading
and resolving identity metadata does not mutate Markdown, frontmatter, or graph
source files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NODE_IDENTITY_REGISTRY_SCHEMA_VERSION = "node_identity_registry.v1"


@dataclass(frozen=True)
class NodeIdentityRegistry:
    schema_version: str
    updated_at: str | None
    authority: dict[str, Any]
    nodes: dict[str, dict[str, Any]]
    aliases: dict[str, dict[str, Any]]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "NodeIdentityRegistry":
        return cls(
            schema_version=str(payload.get("schema_version") or NODE_IDENTITY_REGISTRY_SCHEMA_VERSION),
            updated_at=payload.get("updated_at"),
            authority=dict(payload.get("authority") or {}),
            nodes={str(key): dict(value) for key, value in (payload.get("nodes") or {}).items()},
            aliases={str(key): dict(value) for key, value in (payload.get("aliases") or {}).items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "updated_at": self.updated_at,
            "authority": dict(self.authority),
            "nodes": dict(self.nodes),
            "aliases": dict(self.aliases),
        }


def load_node_identity_registry(path: str | Path) -> NodeIdentityRegistry:
    return NodeIdentityRegistry.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _is_file_like_studio_node(node: dict[str, Any]) -> bool:
    properties = node.get("properties") or {}
    stable_key = str(node.get("stable_key") or "")
    path = str(properties.get("path") or "")
    return bool(path and stable_key == path and node.get("confidence") == "direct_file_scan")


def studio_source_key_for_node(node: dict[str, Any]) -> str:
    """Return the stable registry source key for a derived Studio graph node."""

    explicit = node.get("source_key")
    if explicit:
        return str(explicit)
    stable_key = str(node.get("stable_key") or node.get("id") or "")
    if _is_file_like_studio_node(node):
        return f"studio:file:{stable_key}"
    return f"studio:{node.get('node_type')}:{stable_key}"


def resolve_studio_node_identity(
    node: dict[str, Any],
    registry: NodeIdentityRegistry | None,
    *,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Return a copy of ``node`` annotated with read-only durable identity metadata."""

    annotated = dict(node)
    source_key = studio_source_key_for_node(node)
    annotated["source_key"] = source_key
    annotated["read_only"] = True
    annotated["snapshot_id"] = snapshot_id
    annotated["registry_version"] = registry.schema_version if registry else NODE_IDENTITY_REGISTRY_SCHEMA_VERSION
    annotated["registration_required_for_mutation"] = True

    if registry is None:
        annotated["identity_state"] = "unregistered"
        return annotated

    entry = registry.nodes.get(source_key)
    if entry:
        durable_node_id = entry.get("durable_node_id")
        if durable_node_id:
            annotated["durable_node_id"] = durable_node_id
        annotated["identity_state"] = "registered" if entry.get("status", "active") == "active" else str(entry.get("status"))
        annotated["registry_entry"] = {
            "source_path": entry.get("source_path"),
            "node_type": entry.get("node_type"),
            "first_seen_snapshot": entry.get("first_seen_snapshot"),
            "last_seen_snapshot": entry.get("last_seen_snapshot"),
            "provenance": entry.get("provenance"),
            "canonical_ref": entry.get("canonical_ref"),
        }
        return annotated

    alias = registry.aliases.get(source_key) or registry.aliases.get(str(node.get("id") or ""))
    if alias:
        durable_node_id = alias.get("durable_node_id")
        if durable_node_id:
            annotated["durable_node_id"] = durable_node_id
        annotated["identity_state"] = "aliased"
        annotated["identity_alias"] = {
            "reason": alias.get("reason"),
            "review_ref": alias.get("review_ref"),
        }
        return annotated

    annotated["identity_state"] = "unregistered"
    return annotated


def annotate_studio_graph_nodes(
    nodes: list[dict[str, Any]],
    registry: NodeIdentityRegistry | None,
    *,
    snapshot_id: str | None = None,
) -> list[dict[str, Any]]:
    return [resolve_studio_node_identity(node, registry, snapshot_id=snapshot_id) for node in nodes]


def identity_annotation_summary(nodes: list[dict[str, Any]], registry: NodeIdentityRegistry | None) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    for node in nodes:
        state = str(node.get("identity_state") or "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
    return {
        "loaded": registry is not None,
        "schema_version": registry.schema_version if registry else NODE_IDENTITY_REGISTRY_SCHEMA_VERSION,
        "registered_node_count": len(registry.nodes) if registry else 0,
        "alias_count": len(registry.aliases) if registry else 0,
        "annotated_registered_node_count": state_counts.get("registered", 0),
        "annotated_unregistered_node_count": state_counts.get("unregistered", 0),
        "identity_state_counts": dict(sorted(state_counts.items())),
        "read_only": True,
        "writes_node_ids": False,
        "canonical_mutation_allowed": False,
    }


__all__ = [
    "NODE_IDENTITY_REGISTRY_SCHEMA_VERSION",
    "NodeIdentityRegistry",
    "annotate_studio_graph_nodes",
    "identity_annotation_summary",
    "load_node_identity_registry",
    "resolve_studio_node_identity",
    "studio_source_key_for_node",
]
