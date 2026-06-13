"""Preview-only graph-store migration safety helpers.

This module intentionally produces dry-run artifacts and approval-style packets
only. It does not apply graph migrations, mutate source Markdown, or write
canonical files. Future executors must perform their own Gate/runtime policy
checks before any graph-store artifact write.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Iterable

GRAPH_STORE_MIGRATION_ROOT = "runtime/graph/store/migrations"
MIGRATION_STATES = (
    "unchanged",
    "new",
    "missing",
    "path_renamed",
    "content_changed",
    "split_candidate",
    "merge_candidate",
)


class GraphMigrationSafetyError(ValueError):
    """Raised when a preview packet requests an unsafe graph migration shape."""


def _record(value: dict[str, Any]) -> dict[str, Any]:
    rec = dict(value)
    rec.setdefault("source_key", rec.get("source_path") or rec.get("node_id") or "")
    rec.setdefault("source_path", rec.get("source_file") or rec.get("source_key") or "")
    rec.setdefault("content_sha256", rec.get("source_sha256") or rec.get("content_hash"))
    rec.setdefault("node_type", rec.get("type") or rec.get("node_type"))
    rec.setdefault("label", rec.get("title") or rec.get("label") or rec.get("source_path"))
    return rec


def _hash(rec: dict[str, Any]) -> str | None:
    value = rec.get("content_sha256") or rec.get("source_sha256") or rec.get("content_hash")
    return str(value) if value is not None else None


def _entry(state: str, **payload: Any) -> dict[str, Any]:
    data = {"state": state}
    data.update({k: v for k, v in payload.items() if v is not None})
    return data


def _merge_hash_parts(value: str | None) -> list[str]:
    if not value or not value.startswith("merge:"):
        return []
    return [part for part in value.removeprefix("merge:").split("+") if part]


def _summary(entries: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(entry["state"] for entry in entries)
    return {state: counts.get(state, 0) for state in MIGRATION_STATES}


def classify_migration_dry_run(
    previous_nodes: Iterable[dict[str, Any]],
    current_nodes: Iterable[dict[str, Any]],
    *,
    migration_id: str,
) -> dict[str, Any]:
    """Classify node-identity migration risk without writing or applying it.

    Inputs are intentionally simple serializable node/registry records so the
    helper can be used from snapshot, registry, or Studio-derived dry-run code.
    It reports one preview entry per resolved safety state and keeps ambiguous
    split/merge decisions as candidates for approval rather than applying them.
    """

    previous = [_record(node) for node in previous_nodes]
    current = [_record(node) for node in current_nodes]
    previous_by_key = {node["source_key"]: node for node in previous}
    current_by_key = {node["source_key"]: node for node in current}
    previous_used: set[str] = set()
    current_used: set[str] = set()
    entries: list[dict[str, Any]] = []

    # Same source key: either unchanged or content changed.
    for source_key in sorted(set(previous_by_key) & set(current_by_key)):
        before = previous_by_key[source_key]
        after = current_by_key[source_key]
        before_hash = _hash(before)
        after_hash = _hash(after)
        previous_used.add(source_key)
        current_used.add(source_key)
        if before_hash == after_hash:
            entries.append(
                _entry(
                    "unchanged",
                    source_key=source_key,
                    durable_node_id=before.get("durable_node_id"),
                    source_path=after.get("source_path"),
                    source_hash=after_hash,
                )
            )
        else:
            entries.append(
                _entry(
                    "content_changed",
                    source_key=source_key,
                    durable_node_id=before.get("durable_node_id"),
                    source_path=after.get("source_path"),
                    previous_source_hash=before_hash,
                    current_source_hash=after_hash,
                )
            )

    remaining_previous = [node for node in previous if node["source_key"] not in previous_used]
    remaining_current = [node for node in current if node["source_key"] not in current_used]
    current_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in remaining_current:
        node_hash = _hash(node)
        if node_hash:
            current_by_hash[node_hash].append(node)

    # One previous node mapping to multiple current nodes with the same content
    # hash is a split candidate, never an automatic apply.
    for before in list(remaining_previous):
        before_hash = _hash(before)
        candidates = [node for node in current_by_hash.get(before_hash or "", []) if node["source_key"] not in current_used]
        if len(candidates) > 1:
            previous_used.add(before["source_key"])
            for candidate in candidates:
                current_used.add(candidate["source_key"])
            entries.append(
                _entry(
                    "split_candidate",
                    source_key=before.get("source_key"),
                    durable_node_id=before.get("durable_node_id"),
                    previous_source_path=before.get("source_path"),
                    previous_source_hash=before_hash,
                    candidate_count=len(candidates),
                    candidates=[
                        {
                            "source_key": candidate.get("source_key"),
                            "source_path": candidate.get("source_path"),
                            "source_hash": _hash(candidate),
                        }
                        for candidate in candidates
                    ],
                )
            )

    # Multiple previous nodes collapsing into a current aggregate is a merge
    # candidate. The preview may declare constituent hashes as merge:h1+h2.
    remaining_previous = [node for node in previous if node["source_key"] not in previous_used]
    for after in [node for node in current if node["source_key"] not in current_used]:
        parts = set(_merge_hash_parts(_hash(after)))
        if len(parts) < 2:
            continue
        candidates = [node for node in remaining_previous if _hash(node) in parts]
        if len(candidates) >= 2:
            current_used.add(after["source_key"])
            for candidate in candidates:
                previous_used.add(candidate["source_key"])
            entries.append(
                _entry(
                    "merge_candidate",
                    source_key=after.get("source_key"),
                    source_path=after.get("source_path"),
                    current_source_hash=_hash(after),
                    previous_count=len(candidates),
                    previous=[
                        {
                            "source_key": candidate.get("source_key"),
                            "durable_node_id": candidate.get("durable_node_id"),
                            "source_path": candidate.get("source_path"),
                            "source_hash": _hash(candidate),
                        }
                        for candidate in candidates
                    ],
                )
            )

    # One-to-one content-hash move after split/merge candidates are removed.
    remaining_previous = [node for node in previous if node["source_key"] not in previous_used]
    remaining_current = [node for node in current if node["source_key"] not in current_used]
    current_by_hash = defaultdict(list)
    for node in remaining_current:
        node_hash = _hash(node)
        if node_hash:
            current_by_hash[node_hash].append(node)
    for before in list(remaining_previous):
        before_hash = _hash(before)
        candidates = [node for node in current_by_hash.get(before_hash or "", []) if node["source_key"] not in current_used]
        if len(candidates) == 1:
            after = candidates[0]
            previous_used.add(before["source_key"])
            current_used.add(after["source_key"])
            entries.append(
                _entry(
                    "path_renamed",
                    source_key=after.get("source_key"),
                    durable_node_id=before.get("durable_node_id"),
                    previous_source_key=before.get("source_key"),
                    previous_source_path=before.get("source_path"),
                    current_source_path=after.get("source_path"),
                    source_hash=before_hash,
                )
            )

    for before in sorted((node for node in previous if node["source_key"] not in previous_used), key=lambda node: node["source_key"]):
        entries.append(
            _entry(
                "missing",
                source_key=before.get("source_key"),
                durable_node_id=before.get("durable_node_id"),
                source_path=before.get("source_path"),
                previous_source_hash=_hash(before),
            )
        )
    for after in sorted((node for node in current if node["source_key"] not in current_used), key=lambda node: node["source_key"]):
        entries.append(
            _entry(
                "new",
                source_key=after.get("source_key"),
                source_path=after.get("source_path"),
                current_source_hash=_hash(after),
            )
        )

    entries.sort(key=lambda entry: (MIGRATION_STATES.index(entry["state"]), entry.get("source_key", "")))
    return {
        "schema_version": "graph_migration_dry_run.v1",
        "migration_id": migration_id,
        "mode": "dry_run",
        "apply_allowed": False,
        "canonical_mutation_allowed": False,
        "artifact_root": GRAPH_STORE_MIGRATION_ROOT,
        "summary": _summary(entries),
        "entries": entries,
    }


def _packet_source_hashes(plan: dict[str, Any]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for entry in plan.get("entries", []):
        for path_key, hash_key in (
            ("source_path", "source_hash"),
            ("source_path", "current_source_hash"),
            ("current_source_path", "source_hash"),
            ("current_source_path", "current_source_hash"),
            ("previous_source_path", "previous_source_hash"),
        ):
            path = entry.get(path_key)
            value = entry.get(hash_key)
            if path and value:
                hashes[str(path)] = str(value)
        for collection_key in ("candidates", "previous"):
            for item in entry.get(collection_key, []) or []:
                path = item.get("source_path")
                value = item.get("source_hash")
                if path and value:
                    hashes[str(path)] = str(value)
    return dict(sorted(hashes.items()))


def build_graph_migration_approval_packet(
    dry_run_plan: dict[str, Any],
    *,
    requested_operation: str,
    artifact_path: str,
) -> dict[str, Any]:
    """Build an approval-style packet with source hashes for stale checks."""

    if dry_run_plan.get("mode") != "dry_run" or dry_run_plan.get("apply_allowed") is not False:
        raise GraphMigrationSafetyError("graph migration packets must be built from dry-run-only plans")
    if requested_operation not in {"graph_store.migration.write", "graph_store.identity.write"}:
        raise GraphMigrationSafetyError("graph migration packets may only request graph-store operations")
    if not artifact_path.startswith(f"{GRAPH_STORE_MIGRATION_ROOT}/") or ".." in artifact_path.split("/"):
        raise GraphMigrationSafetyError("migration artifact path must stay under runtime/graph/store/migrations")

    packet = {
        "schema_version": "graph_migration_approval_packet.v1",
        "approval_style": "preview_only",
        "requested_operation": requested_operation,
        "migration_id": dry_run_plan.get("migration_id"),
        "artifact_path": artifact_path,
        "artifact_root": GRAPH_STORE_MIGRATION_ROOT,
        "canonical_mutation_allowed": False,
        "source_mutation_allowed": False,
        "apply_allowed": False,
        "source_hashes": _packet_source_hashes(dry_run_plan),
        "dry_run_plan": deepcopy(dry_run_plan),
    }
    return packet


def reject_stale_graph_execution(packet: dict[str, Any], current_source_hashes: dict[str, str]) -> dict[str, Any]:
    """Return a fail-closed stale-source decision for a preview packet."""

    expected = packet.get("source_hashes") or {}
    stale_paths = [
        path
        for path, expected_hash in sorted(expected.items())
        if current_source_hashes.get(path) != expected_hash
    ]
    if stale_paths:
        return {"rejected": True, "reason": "stale_source_hash", "stale_paths": stale_paths}
    return {"rejected": False, "reason": None, "stale_paths": []}
