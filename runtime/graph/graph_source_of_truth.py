"""Persisted GraphSnapshot as the graph's single source of truth.

The architectural shift this begins: instead of re-deriving the graph from a full
vault scan on every load, the assembled graph is persisted as a versioned
``GraphSnapshot`` and *that* is what the query/scene/renderer layers read. The
scan becomes an incremental updater that only runs when the persisted snapshot is
stale (vault fingerprint changed).

This unifies the two graph systems that exist today — the live scanner/parser
path and the shared ``runtime.graph`` model substrate — behind one persisted
structure.

Governance: derived-only. The snapshot + pointer live in the Studio state dir
(``~/.chaseos/studio/graph/source_of_truth/``), never the vault. No source,
canonical, approval, Agent Bus, runtime, or provider access.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from runtime.graph.contract_cache import _enabled, vault_md_fingerprint
from runtime.graph.graph_models import GraphSnapshot

SOT_SCHEMA = "chaseos.graph.source_of_truth.v1"


def _sot_dir() -> Path:
    env = os.environ.get("CHASEOS_GRAPH_SOT_DIR")
    if env:
        return Path(env)
    return Path.home() / ".chaseos" / "studio" / "graph" / "source_of_truth"


def _pointer_path(vault_root: str | Path, folder_path: Any = None) -> Path:
    import hashlib

    key_src = json.dumps(
        {"vault": str(Path(vault_root).resolve()), "folder": str(folder_path) if folder_path else None},
        sort_keys=True,
        default=str,
    )
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:24]
    return _sot_dir() / f"{key}.json"


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, default=str), encoding="utf-8")
    os.replace(tmp, path)


def persist_snapshot(vault_root: str | Path, snapshot: GraphSnapshot, *, folder_path: Any = None) -> bool:
    """Persist ``snapshot`` as the current source of truth for (vault, folder).

    Records the vault fingerprint so a later load knows whether it is still
    fresh. Fail-open; returns True on write.
    """
    if not _enabled():
        return False
    if snapshot.node_count == 0:
        return False
    try:
        fingerprint, _count = vault_md_fingerprint(vault_root, folder_path)
        _atomic_write(
            _pointer_path(vault_root, folder_path),
            {
                "schema_version": SOT_SCHEMA,
                "fingerprint": fingerprint,
                "graph_hash": snapshot.graph_version.graph_hash,
                "node_count": snapshot.node_count,
                "edge_count": snapshot.edge_count,
                "created_at": snapshot.created_at,
                "snapshot": snapshot.to_dict(),
                "canonical_mutation_allowed": False,
                "generated_from_read_only_cache": True,
            },
        )
        return True
    except Exception:
        return False


def persisted_snapshot_if_fresh(vault_root: str | Path, *, folder_path: Any = None) -> GraphSnapshot | None:
    """Return the persisted snapshot iff the vault is unchanged since it was
    persisted (fingerprint match). Else None. Fail-open."""
    if not _enabled():
        return None
    path = _pointer_path(vault_root, folder_path)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if payload.get("schema_version") != SOT_SCHEMA:
        return None
    if payload.get("canonical_mutation_allowed") is not False:
        return None
    if payload.get("generated_from_read_only_cache") is not True:
        return None
    try:
        fingerprint, _count = vault_md_fingerprint(vault_root, folder_path)
    except Exception:
        return None
    if payload.get("fingerprint") != fingerprint:
        return None  # vault changed since persist → stale
    snap = payload.get("snapshot")
    if not isinstance(snap, dict):
        return None
    try:
        return GraphSnapshot.from_dict(snap)
    except Exception:
        return None
