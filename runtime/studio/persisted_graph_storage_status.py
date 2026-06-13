"""Read-only persisted graph storage status for Studio product surfaces.

This module reports whether the Phase 9 graph store has a current persisted
snapshot available. It never scans the vault to build a graph and never writes
snapshots, identity registries, Markdown, or canonical state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.graph.store import GraphStorePathError, load_current_snapshot

SURFACE_ID = "persisted_graph_storage_status"
MODEL_VERSION = "studio.persisted_graph_storage_status.v1"
GRAPH_STORE_RELATIVE_ROOT = "runtime/graph/store"


def _count_json_files(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    return sum(1 for item in path.glob("*.json") if item.is_file())


def _relative_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "writes_snapshot": False,
        "writes_identity_registry": False,
        "writes_markdown": False,
        "canonical_mutation_allowed": False,
    }


def build_persisted_graph_storage_status(repo_root: str | Path) -> dict[str, Any]:
    """Return read-only graph-store cache/snapshot status for Studio.

    The model intentionally distinguishes between the storage implementation
    existing and a current snapshot being available. Missing cache state remains
    a safe product-facing gap, not a failure that triggers a scan or write.
    """

    root = Path(repo_root).expanduser().resolve()
    store_root = root / GRAPH_STORE_RELATIVE_ROOT
    snapshots_dir = store_root / "snapshots"
    manifests_dir = store_root / "manifests" / "snapshots"
    current_pointer = store_root / "manifests" / "current.json"
    snapshot_count = _count_json_files(snapshots_dir)
    manifest_count = _count_json_files(manifests_dir)
    blockers: list[str] = []
    warnings: list[str] = []
    current_manifest: dict[str, Any] | None = None
    summary: dict[str, Any] = {
        "cache_ready": False,
        "current_snapshot_id": None,
        "current_node_count": 0,
        "current_edge_count": 0,
        "snapshot_count": snapshot_count,
        "manifest_count": manifest_count,
        "current_pointer_exists": current_pointer.exists(),
    }

    try:
        manifest, snapshot = load_current_snapshot(repo_root=root)
        current_manifest = manifest.to_dict()
        summary.update(
            {
                "cache_ready": True,
                "current_snapshot_id": snapshot.snapshot_id,
                "current_node_count": snapshot.node_count,
                "current_edge_count": snapshot.edge_count,
                "snapshot_count": snapshot_count,
                "manifest_count": manifest_count,
                "current_pointer_exists": True,
            }
        )
        status = "READY / READ_ONLY_CURRENT_GRAPH_SNAPSHOT_AVAILABLE"
    except FileNotFoundError:
        status = "NOT_READY / NO_CURRENT_GRAPH_SNAPSHOT"
        blockers.append("persisted_graph_storage_current_snapshot_missing")
    except (GraphStorePathError, ValueError, KeyError) as exc:
        status = "BLOCKED / GRAPH_STORE_POINTER_INVALID"
        blockers.append("persisted_graph_storage_pointer_invalid")
        warnings.append(str(exc))
    except Exception as exc:  # defensive fail-open dashboard model
        status = "BLOCKED / GRAPH_STORE_STATUS_UNAVAILABLE"
        blockers.append("persisted_graph_storage_status_unavailable")
        warnings.append(str(exc))

    return {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "storage_root": GRAPH_STORE_RELATIVE_ROOT,
        "storage_paths": {
            "current_pointer": _relative_path(root, current_pointer),
            "snapshots_dir": _relative_path(root, snapshots_dir),
            "manifests_dir": _relative_path(root, manifests_dir),
        },
        "summary": summary,
        "current_manifest": current_manifest,
        "safe_preview_available": True,
        "readiness": {
            "persisted_graph_storage_status_ready": True,
            "persisted_graph_index_ready": bool(summary["cache_ready"]),
            "current_snapshot_available": bool(summary["cache_ready"]),
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": (
                "graph-view-contract"
                if summary["cache_ready"]
                else "persisted-graph-snapshot-write-approval"
            ),
        },
        "next_actions": [
            {
                "label": "Inspect graph view contract",
                "command": "python -m runtime.cli.main studio graph-view-contract --json",
                "preview_only": True,
            },
            {
                "label": "Review persisted graph architecture contract",
                "path": "06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md",
                "preview_only": True,
            },
        ],
        "authority": _authority(),
    }


__all__ = ["build_persisted_graph_storage_status"]
