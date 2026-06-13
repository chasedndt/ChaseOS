"""Persistent layout cache for derived ChaseOS graph scenes.

The cache stores renderer positions only. It never changes graph truth, source
Markdown, approvals, Agent Bus state, or canonical runtime state.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.graph.graph_models import utc_now_iso


LAYOUT_CACHE_SCHEMA_VERSION = "chaseos.graph.layout_cache.v1"


class GraphLayoutCacheError(ValueError):
    """Raised when a layout cache read/write is malformed or out of bounds."""


@dataclass(frozen=True)
class GraphLayoutPosition:
    workspace_id: str
    scene_id: str
    graph_version: str
    layout_mode: str
    node_id: str
    x: float
    y: float
    z: float | None = None
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def cache_key(self) -> str:
        return make_layout_cache_key(
            workspace_id=self.workspace_id,
            scene_id=self.scene_id,
            graph_version=self.graph_version,
            layout_mode=self.layout_mode,
            node_id=self.node_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphLayoutPosition":
        return cls(
            workspace_id=str(payload["workspace_id"]),
            scene_id=str(payload["scene_id"]),
            graph_version=str(payload["graph_version"]),
            layout_mode=str(payload["layout_mode"]),
            node_id=str(payload["node_id"]),
            x=float(payload["x"]),
            y=float(payload["y"]),
            z=None if payload.get("z") is None else float(payload["z"]),
            updated_at=str(payload.get("updated_at") or utc_now_iso()),
            metadata=dict(payload.get("metadata") or {}),
        )


def make_layout_cache_key(
    *,
    workspace_id: str,
    scene_id: str,
    graph_version: str,
    layout_mode: str,
    node_id: str,
) -> str:
    return "|".join(
        str(part).replace("|", "_")
        for part in (workspace_id, scene_id, graph_version, layout_mode, node_id)
    )


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


class JsonGraphLayoutCache:
    """JSON-backed layout cache keyed by workspace, scene, version, mode, node."""

    def __init__(self, cache_path: str | Path) -> None:
        self.cache_path = Path(cache_path)

    def load_all(self) -> dict[str, GraphLayoutPosition]:
        if not self.cache_path.exists():
            return {}
        payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != LAYOUT_CACHE_SCHEMA_VERSION:
            raise GraphLayoutCacheError(f"unsupported layout cache schema: {payload.get('schema_version')!r}")
        positions = payload.get("positions") or {}
        return {
            key: GraphLayoutPosition.from_dict(value)
            for key, value in positions.items()
        }

    def save_positions(self, positions: list[GraphLayoutPosition]) -> None:
        existing = self.load_all()
        for position in positions:
            existing[position.cache_key] = position
        _atomic_write_json(
            self.cache_path,
            {
                "schema_version": LAYOUT_CACHE_SCHEMA_VERSION,
                "updated_at": utc_now_iso(),
                "positions": {key: value.to_dict() for key, value in sorted(existing.items())},
            },
        )

    def load_positions(
        self,
        *,
        workspace_id: str,
        scene_id: str,
        graph_version: str,
        layout_mode: str,
        node_ids: set[str] | None = None,
    ) -> dict[str, GraphLayoutPosition]:
        loaded = self.load_all()
        results: dict[str, GraphLayoutPosition] = {}
        for position in loaded.values():
            if position.workspace_id != workspace_id:
                continue
            if position.scene_id != scene_id:
                continue
            if position.graph_version != graph_version:
                continue
            if position.layout_mode != layout_mode:
                continue
            if node_ids is not None and position.node_id not in node_ids:
                continue
            results[position.node_id] = position
        return results

    def clear_scene(self, *, workspace_id: str, scene_id: str) -> int:
        loaded = self.load_all()
        kept: dict[str, GraphLayoutPosition] = {}
        removed = 0
        for key, position in loaded.items():
            if position.workspace_id == workspace_id and position.scene_id == scene_id:
                removed += 1
                continue
            kept[key] = position
        _atomic_write_json(
            self.cache_path,
            {
                "schema_version": LAYOUT_CACHE_SCHEMA_VERSION,
                "updated_at": utc_now_iso(),
                "positions": {key: value.to_dict() for key, value in sorted(kept.items())},
            },
        )
        return removed
