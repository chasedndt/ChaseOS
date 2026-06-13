"""Persistent local GraphStore/cache for ChaseOS Studio Graph.

This module persists derived graph state under ``.chaseos/graph`` by default:
snapshots, scene state, layout positions, runtime overlay events, file
fingerprints, and query slices. It is a local cache layer only. It does not
scan source files, mutate Markdown, consume approvals, write Agent Bus tasks,
dispatch runtimes, or promote canonical graph state.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.graph.graph_layout_cache import GraphLayoutPosition, JsonGraphLayoutCache
from runtime.graph.graph_models import GraphScene, GraphSnapshot, RuntimeOverlayEvent, stable_digest, utc_now_iso
from runtime.graph.graph_store import InMemoryGraphStore


PERSISTENT_GRAPH_STORE_SCHEMA_VERSION = "chaseos.graph.persistent_store.v1"
SCENES_SCHEMA_VERSION = "chaseos.graph.scenes.v1"
FINGERPRINTS_SCHEMA_VERSION = "chaseos.graph.file_fingerprints.v1"
QUERY_CACHE_SCHEMA_VERSION = "chaseos.graph.query_cache.v1"
DEFAULT_GRAPH_STORE_RELATIVE_ROOT = Path(".chaseos") / "graph"


class PersistentGraphStoreError(ValueError):
    """Raised when the persistent graph cache is invalid or unsafe."""


@dataclass(frozen=True)
class GraphFileFingerprint:
    path: str
    sha256: str
    size_bytes: int
    mtime_ns: int
    fingerprinted_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphFileFingerprint":
        return cls(
            path=str(payload["path"]),
            sha256=str(payload["sha256"]),
            size_bytes=int(payload.get("size_bytes") or 0),
            mtime_ns=int(payload.get("mtime_ns") or 0),
            fingerprinted_at=str(payload.get("fingerprinted_at") or utc_now_iso()),
        )


@dataclass(frozen=True)
class DirtyFileDetection:
    changed: tuple[str, ...] = ()
    deleted: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()
    current_fingerprints: dict[str, GraphFileFingerprint] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": list(self.changed),
            "deleted": list(self.deleted),
            "unchanged": list(self.unchanged),
            "current_fingerprints": {
                key: value.to_dict()
                for key, value in sorted(self.current_fingerprints.items())
            },
        }


def _repo_root(repo_root: str | Path) -> Path:
    return Path(repo_root).expanduser().resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _default_store_root(repo_root: Path) -> Path:
    return (repo_root / DEFAULT_GRAPH_STORE_RELATIVE_ROOT).resolve()


def _validate_store_root(repo_root: Path, store_root: str | Path | None = None) -> Path:
    expected = _default_store_root(repo_root)
    actual = Path(store_root).expanduser().resolve() if store_root is not None else expected
    if actual != expected:
        raise PersistentGraphStoreError(
            f"persistent graph cache writes are restricted to {DEFAULT_GRAPH_STORE_RELATIVE_ROOT.as_posix()}"
        )
    return actual


def _safe_child_path(store_root: Path, *parts: str) -> Path:
    candidate = store_root.joinpath(*parts).resolve()
    if not _is_relative_to(candidate, store_root):
        raise PersistentGraphStoreError(f"path escapes graph cache root: {candidate}")
    return candidate


def _repo_relative_path(repo_root: Path, path: Path) -> str:
    resolved = path.resolve()
    if not _is_relative_to(resolved, repo_root):
        raise PersistentGraphStoreError(f"path escapes repository: {path}")
    return resolved.relative_to(repo_root).as_posix()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_file_fingerprint(repo_root: str | Path, path: str | Path) -> GraphFileFingerprint:
    """Hash one repo-contained file for incremental graph rebuild detection."""

    root = _repo_root(repo_root)
    candidate = (root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not _is_relative_to(candidate, root):
        raise PersistentGraphStoreError(f"fingerprint path escapes repository: {path}")
    if not candidate.is_file():
        raise PersistentGraphStoreError(f"fingerprint path is not a file: {path}")
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = candidate.stat()
    return GraphFileFingerprint(
        path=_repo_relative_path(root, candidate),
        sha256=digest.hexdigest(),
        size_bytes=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )


def detect_dirty_files(
    repo_root: str | Path,
    previous: dict[str, GraphFileFingerprint] | dict[str, dict[str, Any]],
    paths: list[str | Path],
) -> DirtyFileDetection:
    """Compare stored fingerprints with current files without rebuilding graph truth."""

    root = _repo_root(repo_root)
    previous_models: dict[str, GraphFileFingerprint] = {}
    for key, value in previous.items():
        previous_models[str(key)] = value if isinstance(value, GraphFileFingerprint) else GraphFileFingerprint.from_dict(value)

    current: dict[str, GraphFileFingerprint] = {}
    changed: list[str] = []
    unchanged: list[str] = []

    for raw_path in paths:
        candidate = (root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        rel_path = _repo_relative_path(root, candidate)
        if not candidate.exists():
            changed.append(rel_path)
            continue
        fingerprint = compute_file_fingerprint(root, candidate)
        current[rel_path] = fingerprint
        previous_fingerprint = previous_models.get(rel_path)
        if previous_fingerprint is None or previous_fingerprint.sha256 != fingerprint.sha256:
            changed.append(rel_path)
        else:
            unchanged.append(rel_path)

    requested = {
        _repo_relative_path(root, (root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve())
        for raw_path in paths
    }
    deleted = sorted(
        rel_path
        for rel_path in previous_models
        if rel_path in requested and not (root / rel_path).exists()
    )
    return DirtyFileDetection(
        changed=tuple(sorted(set(changed))),
        deleted=tuple(deleted),
        unchanged=tuple(sorted(set(unchanged))),
        current_fingerprints=current,
    )


class PersistentGraphStore:
    """JSON/JSONL persistent cache for shared GraphSnapshot, scenes, layout, and overlays."""

    def __init__(self, repo_root: str | Path, store_root: str | Path | None = None) -> None:
        self.repo_root = _repo_root(repo_root)
        self.store_root = _validate_store_root(self.repo_root, store_root)
        self.snapshots_dir = _safe_child_path(self.store_root, "snapshots")
        self.current_path = _safe_child_path(self.store_root, "current_snapshot.json")
        self.scenes_path = _safe_child_path(self.store_root, "scenes.json")
        self.layout_cache_path = _safe_child_path(self.store_root, "layout_cache.json")
        self.overlay_path = _safe_child_path(self.store_root, "runtime_overlay.jsonl")
        self.fingerprints_path = _safe_child_path(self.store_root, "file_fingerprints.json")
        self.query_cache_dir = _safe_child_path(self.store_root, "query_cache")
        self.layout_cache = JsonGraphLayoutCache(self.layout_cache_path)

    def save_snapshot(self, snapshot: GraphSnapshot, *, write_current: bool = True) -> Path:
        snapshot_path = _safe_child_path(self.snapshots_dir, f"{snapshot.snapshot_id}.json")
        _atomic_write_json(snapshot_path, snapshot.to_dict())
        if write_current:
            _atomic_write_json(
                self.current_path,
                {
                    "schema_version": PERSISTENT_GRAPH_STORE_SCHEMA_VERSION,
                    "snapshot_id": snapshot.snapshot_id,
                    "snapshot_path": _repo_relative_path(self.repo_root, snapshot_path),
                    "graph_hash": snapshot.graph_version.graph_hash,
                    "node_count": snapshot.node_count,
                    "edge_count": snapshot.edge_count,
                    "updated_at": utc_now_iso(),
                    "canonical_mutation_allowed": False,
                    "generated_from_read_only_cache": True,
                },
            )
        return snapshot_path

    def load_snapshot(self, snapshot_id: str) -> GraphSnapshot:
        snapshot_path = _safe_child_path(self.snapshots_dir, f"{snapshot_id}.json")
        return GraphSnapshot.from_dict(json.loads(snapshot_path.read_text(encoding="utf-8")))

    def load_current_snapshot(self) -> GraphSnapshot:
        current = json.loads(self.current_path.read_text(encoding="utf-8"))
        if current.get("canonical_mutation_allowed") is not False:
            raise PersistentGraphStoreError("current graph cache pointer cannot allow canonical mutation")
        if current.get("generated_from_read_only_cache") is not True:
            raise PersistentGraphStoreError("current graph cache pointer must be derived-only")
        snapshot_path = (self.repo_root / str(current["snapshot_path"])).resolve()
        if not _is_relative_to(snapshot_path, self.store_root):
            raise PersistentGraphStoreError("current snapshot pointer escapes graph cache root")
        return GraphSnapshot.from_dict(json.loads(snapshot_path.read_text(encoding="utf-8")))

    def load_in_memory_store(self) -> InMemoryGraphStore:
        return InMemoryGraphStore.from_snapshot(self.load_current_snapshot())

    def get_graph_summary(self) -> dict[str, Any]:
        return self.load_in_memory_store().get_graph_summary()

    def save_scene(self, scene: GraphScene) -> GraphScene:
        scenes = {item.scene_id: item for item in self.list_scenes()}
        scenes[scene.scene_id] = scene
        self._write_scenes(scenes)
        return scene

    def get_scene(self, scene_id: str) -> GraphScene | None:
        for scene in self.list_scenes():
            if scene.scene_id == scene_id:
                updated = GraphScene.from_dict({**scene.to_dict(), "last_used_at": utc_now_iso()})
                self.save_scene(updated)
                return updated
        return None

    def list_scenes(self) -> list[GraphScene]:
        if not self.scenes_path.exists():
            return []
        payload = json.loads(self.scenes_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != SCENES_SCHEMA_VERSION:
            raise PersistentGraphStoreError(f"unsupported graph scenes schema: {payload.get('schema_version')!r}")
        scenes = [GraphScene.from_dict(item) for item in payload.get("scenes", [])]
        return sorted(scenes, key=lambda scene: scene.last_used_at, reverse=True)

    def close_scene(self, scene_id: str) -> bool:
        scenes = {item.scene_id: item for item in self.list_scenes()}
        removed = scenes.pop(scene_id, None) is not None
        self._write_scenes(scenes)
        return removed

    def _write_scenes(self, scenes: dict[str, GraphScene]) -> None:
        _atomic_write_json(
            self.scenes_path,
            {
                "schema_version": SCENES_SCHEMA_VERSION,
                "updated_at": utc_now_iso(),
                "scenes": [scene.to_dict() for scene in sorted(scenes.values(), key=lambda item: item.scene_id)],
            },
        )

    def save_layout_positions(self, positions: list[GraphLayoutPosition]) -> None:
        self.layout_cache.save_positions(positions)

    def load_layout_positions(
        self,
        *,
        workspace_id: str,
        scene_id: str,
        graph_version: str,
        layout_mode: str,
        node_ids: set[str] | None = None,
    ) -> dict[str, GraphLayoutPosition]:
        return self.layout_cache.load_positions(
            workspace_id=workspace_id,
            scene_id=scene_id,
            graph_version=graph_version,
            layout_mode=layout_mode,
            node_ids=node_ids,
        )

    def append_overlay_event(self, event: RuntimeOverlayEvent) -> RuntimeOverlayEvent:
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        with self.overlay_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        return event

    def list_overlay_events(self, *, include_expired: bool = False, compact: bool = False) -> list[RuntimeOverlayEvent]:
        if not self.overlay_path.exists():
            return []
        now = datetime.now(timezone.utc)
        retained: list[RuntimeOverlayEvent] = []
        visible: list[RuntimeOverlayEvent] = []
        for line in self.overlay_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = RuntimeOverlayEvent.from_dict(json.loads(line))
            timestamp = _parse_iso(event.timestamp)
            expired = bool(timestamp and event.ttl_seconds and (now - timestamp).total_seconds() > event.ttl_seconds)
            if not expired:
                retained.append(event)
                visible.append(event)
            elif include_expired:
                visible.append(event)
        if compact:
            self._write_overlay_events(retained)
        return sorted(visible, key=lambda item: item.timestamp, reverse=True)

    def _write_overlay_events(self, events: list[RuntimeOverlayEvent]) -> None:
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.overlay_path.with_suffix(self.overlay_path.suffix + ".tmp")
        tmp_path.write_text(
            "".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )
        os.replace(tmp_path, self.overlay_path)

    def save_file_fingerprints(self, fingerprints: dict[str, GraphFileFingerprint]) -> None:
        _atomic_write_json(
            self.fingerprints_path,
            {
                "schema_version": FINGERPRINTS_SCHEMA_VERSION,
                "updated_at": utc_now_iso(),
                "fingerprints": {
                    key: value.to_dict()
                    for key, value in sorted(fingerprints.items())
                },
            },
        )

    def load_file_fingerprints(self) -> dict[str, GraphFileFingerprint]:
        if not self.fingerprints_path.exists():
            return {}
        payload = json.loads(self.fingerprints_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != FINGERPRINTS_SCHEMA_VERSION:
            raise PersistentGraphStoreError(f"unsupported fingerprint schema: {payload.get('schema_version')!r}")
        return {
            key: GraphFileFingerprint.from_dict(value)
            for key, value in (payload.get("fingerprints") or {}).items()
        }

    def detect_dirty_files(self, paths: list[str | Path]) -> DirtyFileDetection:
        return detect_dirty_files(self.repo_root, self.load_file_fingerprints(), paths)

    def save_query_cache(self, cache_key: str, snapshot: GraphSnapshot, *, metadata: dict[str, Any] | None = None) -> Path:
        safe_key = stable_digest([cache_key, snapshot.graph_version.graph_hash], length=32)
        cache_path = _safe_child_path(self.query_cache_dir, f"{safe_key}.json")
        _atomic_write_json(
            cache_path,
            {
                "schema_version": QUERY_CACHE_SCHEMA_VERSION,
                "cache_key": cache_key,
                "graph_hash": snapshot.graph_version.graph_hash,
                "updated_at": utc_now_iso(),
                "snapshot": snapshot.to_dict(),
                "metadata": dict(metadata or {}),
            },
        )
        return cache_path

    def load_query_cache(self, cache_key: str, graph_hash: str) -> GraphSnapshot | None:
        safe_key = stable_digest([cache_key, graph_hash], length=32)
        cache_path = _safe_child_path(self.query_cache_dir, f"{safe_key}.json")
        if not cache_path.exists():
            return None
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != QUERY_CACHE_SCHEMA_VERSION:
            raise PersistentGraphStoreError(f"unsupported query cache schema: {payload.get('schema_version')!r}")
        if payload.get("graph_hash") != graph_hash:
            return None
        return GraphSnapshot.from_dict(dict(payload["snapshot"]))

    def make_scene_id(self, title: str, lens_type: str, query: str | None = None) -> str:
        graph_hash = "no-current-snapshot"
        if self.current_path.exists():
            graph_hash = self.load_current_snapshot().graph_version.graph_hash
        return f"scene-{stable_digest([title, lens_type, query, graph_hash], length=16)}"
