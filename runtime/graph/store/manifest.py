"""Graph snapshot manifest store helpers.

The graph store is a repo-local derived-artifact root. These helpers only write
under ``runtime/graph/store/`` and never mutate Markdown/source files.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.graph.artifact import GraphSnapshot

GRAPH_STORE_RELATIVE_ROOT = Path("runtime/graph/store")
GRAPH_SNAPSHOT_MANIFEST_SCHEMA_VERSION = "graph_snapshot_manifest.v1"


class GraphStorePathError(ValueError):
    """Raised when a graph-store read/write attempts to escape the store root."""


@dataclass(frozen=True)
class GraphSnapshotManifest:
    schema_version: str
    snapshot_id: str
    created_at: str
    builder: str
    source_model: str
    vault_root_hash: str | None
    scope: list[str]
    source_file_count: int
    node_count: int
    edge_count: int
    snapshot_path: str
    source_hashes_path: str | None
    identity_registry_version: str
    canonical_mutation_allowed: bool
    generated_from_read_only_scan: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GraphSnapshotManifest":
        if payload.get("schema_version") != GRAPH_SNAPSHOT_MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported graph snapshot manifest schema: {payload.get('schema_version')!r}"
            )
        if payload.get("canonical_mutation_allowed") is not False:
            raise ValueError("snapshot manifests cannot allow canonical mutation")
        if payload.get("generated_from_read_only_scan") is not True:
            raise ValueError("snapshot manifests must be generated from a read-only scan")
        return cls(
            schema_version=str(payload["schema_version"]),
            snapshot_id=str(payload["snapshot_id"]),
            created_at=str(payload["created_at"]),
            builder=str(payload["builder"]),
            source_model=str(payload["source_model"]),
            vault_root_hash=payload.get("vault_root_hash"),
            scope=list(payload.get("scope") or []),
            source_file_count=int(payload.get("source_file_count") or 0),
            node_count=int(payload.get("node_count") or 0),
            edge_count=int(payload.get("edge_count") or 0),
            snapshot_path=str(payload["snapshot_path"]),
            source_hashes_path=payload.get("source_hashes_path"),
            identity_registry_version=str(payload.get("identity_registry_version") or "node_identity_registry.v1"),
            canonical_mutation_allowed=False,
            generated_from_read_only_scan=True,
        )


def _repo_root(repo_root: str | Path) -> Path:
    return Path(repo_root).expanduser().resolve()


def _default_store_root(repo_root: Path) -> Path:
    return (repo_root / GRAPH_STORE_RELATIVE_ROOT).resolve()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_store_root(repo_root: Path, store_root: str | Path | None = None) -> Path:
    expected = _default_store_root(repo_root)
    actual = Path(store_root).expanduser().resolve() if store_root is not None else expected
    if actual != expected:
        raise GraphStorePathError(
            f"graph store writes are restricted to {GRAPH_STORE_RELATIVE_ROOT.as_posix()}"
        )
    return actual


def _relative_store_path(repo_root: Path, path: Path) -> str:
    resolved = path.resolve()
    store_root = _default_store_root(repo_root)
    if not _is_relative_to(resolved, store_root):
        raise GraphStorePathError(f"path escapes graph store: {path}")
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise GraphStorePathError(f"path escapes repository: {path}") from exc


def _resolve_repo_relative_store_path(repo_root: Path, rel_path: str) -> Path:
    candidate = (repo_root / rel_path).resolve()
    store_root = _default_store_root(repo_root)
    if not _is_relative_to(candidate, store_root):
        raise GraphStorePathError(f"manifest path escapes graph store: {rel_path}")
    return candidate


def write_snapshot_manifest(
    snapshot: GraphSnapshot,
    *,
    repo_root: str | Path,
    store_root: str | Path | None = None,
    builder: str,
    source_model: str,
    vault_root_hash: str | None = None,
    source_file_count: int | None = None,
    source_hashes_path: str | None = None,
    scope: list[str] | None = None,
    identity_registry_version: str = "node_identity_registry.v1",
    write_current: bool = True,
) -> GraphSnapshotManifest:
    """Persist a snapshot, immutable manifest, and current pointer under the graph store.

    ``store_root`` may not redirect writes; it is accepted only so callers and
    tests can prove forbidden roots fail closed. Snapshot JSON is written through
    ``GraphSnapshot.save``.
    """

    root = _repo_root(repo_root)
    store = _validate_store_root(root, store_root)
    snapshot_path = store / "snapshots" / f"{snapshot.snapshot_id}.json"
    manifest_path = store / "manifests" / "snapshots" / f"{snapshot.snapshot_id}.json"
    current_path = store / "manifests" / "current.json"

    manifest = GraphSnapshotManifest(
        schema_version=GRAPH_SNAPSHOT_MANIFEST_SCHEMA_VERSION,
        snapshot_id=snapshot.snapshot_id,
        created_at=snapshot.created_at,
        builder=builder,
        source_model=source_model,
        vault_root_hash=vault_root_hash,
        scope=list(scope if scope is not None else snapshot.extraction_scope),
        source_file_count=int(
            source_file_count
            if source_file_count is not None
            else len({node.source_file for node in snapshot.nodes})
        ),
        node_count=snapshot.node_count,
        edge_count=snapshot.edge_count,
        snapshot_path=_relative_store_path(root, snapshot_path),
        source_hashes_path=source_hashes_path,
        identity_registry_version=identity_registry_version,
        canonical_mutation_allowed=False,
        generated_from_read_only_scan=True,
    )

    if manifest.source_hashes_path:
        _resolve_repo_relative_store_path(root, manifest.source_hashes_path)

    snapshot.save(snapshot_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if write_current:
        current_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.write_text(
            json.dumps(
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "manifest_path": _relative_store_path(root, manifest_path),
                    "canonical_mutation_allowed": False,
                    "generated_from_read_only_scan": True,
                },
                indent=2,
                sort_keys=False,
            )
            + "\n",
            encoding="utf-8",
        )
    return manifest


def load_snapshot_manifest(path: str | Path, *, repo_root: str | Path) -> GraphSnapshotManifest:
    """Load and validate a manifest from inside ``runtime/graph/store``."""

    root = _repo_root(repo_root)
    manifest_path = Path(path).expanduser().resolve()
    store_root = _default_store_root(root)
    if not _is_relative_to(manifest_path, store_root):
        raise GraphStorePathError(f"manifest path escapes graph store: {path}")
    manifest = GraphSnapshotManifest.from_dict(json.loads(manifest_path.read_text(encoding="utf-8")))
    _resolve_repo_relative_store_path(root, manifest.snapshot_path)
    if manifest.source_hashes_path:
        _resolve_repo_relative_store_path(root, manifest.source_hashes_path)
    return manifest


def load_current_snapshot(*, repo_root: str | Path) -> tuple[GraphSnapshotManifest, GraphSnapshot]:
    """Load the current manifest pointer and its serialized GraphSnapshot."""

    root = _repo_root(repo_root)
    current_path = _default_store_root(root) / "manifests" / "current.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    if current.get("canonical_mutation_allowed") is not False:
        raise ValueError("current graph-store pointer cannot allow canonical mutation")
    if current.get("generated_from_read_only_scan") is not True:
        raise ValueError("current graph-store pointer must reference a read-only scan")
    manifest_path = _resolve_repo_relative_store_path(root, str(current["manifest_path"]))
    manifest = load_snapshot_manifest(manifest_path, repo_root=root)
    snapshot = GraphSnapshot.load(_resolve_repo_relative_store_path(root, manifest.snapshot_path))
    return manifest, snapshot
