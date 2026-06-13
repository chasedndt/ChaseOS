"""Bounded repo-local graph-store package.

Re-exports snapshot manifest helpers plus read-only durable identity helpers.
All approved graph-store writes stay under ``runtime/graph/store/`` and do not
mutate source Markdown or canonical ChaseOS knowledge.
"""

from runtime.graph.store.manifest import (
    GRAPH_SNAPSHOT_MANIFEST_SCHEMA_VERSION,
    GRAPH_STORE_RELATIVE_ROOT,
    GraphSnapshotManifest,
    GraphStorePathError,
    load_current_snapshot,
    load_snapshot_manifest,
    write_snapshot_manifest,
)

__all__ = [
    "GRAPH_SNAPSHOT_MANIFEST_SCHEMA_VERSION",
    "GRAPH_STORE_RELATIVE_ROOT",
    "GraphSnapshotManifest",
    "GraphStorePathError",
    "load_current_snapshot",
    "load_snapshot_manifest",
    "write_snapshot_manifest",
]
