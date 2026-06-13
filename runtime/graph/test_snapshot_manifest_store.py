from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.graph.artifact import GraphSnapshot, make_node, make_snapshot_id
from runtime.graph.store import (
    GraphStorePathError,
    load_current_snapshot,
    load_snapshot_manifest,
    write_snapshot_manifest,
)


def _snapshot() -> GraphSnapshot:
    node = make_node(label="HERMES.md", node_type="file", source_file="06_AGENTS/HERMES.md")
    return GraphSnapshot(
        snapshot_id=make_snapshot_id(),
        created_at="2026-05-12T01:02:03Z",
        vault_root="/test/vault",
        extraction_scope=["06_AGENTS/", "runtime/"],
        nodes=[node],
        edges=[],
        community_assignments={},
        build_info={"builder": "test"},
        metadata={},
    )


def test_snapshot_manifest_writer_persists_snapshot_manifest_and_current_pointer_under_store_only(tmp_path):
    snapshot = _snapshot()

    manifest = write_snapshot_manifest(
        snapshot,
        repo_root=tmp_path,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
        vault_root_hash="sha256:test-root",
        source_file_count=2,
    )

    store_root = tmp_path / "runtime" / "graph" / "store"
    snapshot_path = store_root / "snapshots" / f"{snapshot.snapshot_id}.json"
    manifest_path = store_root / "manifests" / "snapshots" / f"{snapshot.snapshot_id}.json"
    current_path = store_root / "manifests" / "current.json"

    assert snapshot_path.exists()
    assert manifest_path.exists()
    assert current_path.exists()
    assert manifest.snapshot_id == snapshot.snapshot_id
    assert manifest.node_count == 1
    assert manifest.edge_count == 0
    assert manifest.snapshot_path == f"runtime/graph/store/snapshots/{snapshot.snapshot_id}.json"

    current = json.loads(current_path.read_text(encoding="utf-8"))
    assert current == {
        "snapshot_id": snapshot.snapshot_id,
        "manifest_path": f"runtime/graph/store/manifests/snapshots/{snapshot.snapshot_id}.json",
        "canonical_mutation_allowed": False,
        "generated_from_read_only_scan": True,
    }


def test_snapshot_manifest_reader_loads_current_manifest_and_snapshot_without_scanning(tmp_path):
    snapshot = _snapshot()
    write_snapshot_manifest(
        snapshot,
        repo_root=tmp_path,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
        vault_root_hash="sha256:test-root",
        source_file_count=2,
    )

    manifest, loaded = load_current_snapshot(repo_root=tmp_path)

    assert manifest.snapshot_id == snapshot.snapshot_id
    assert loaded.snapshot_id == snapshot.snapshot_id
    assert loaded.nodes[0].source_file == "06_AGENTS/HERMES.md"


def test_snapshot_store_rejects_canonical_protected_and_arbitrary_roots(tmp_path):
    snapshot = _snapshot()

    forbidden_roots = [
        tmp_path / "02_KNOWLEDGE",
        tmp_path / "06_AGENTS",
        tmp_path / "06_AGENTS" / "Permission-Matrix.md",
        tmp_path / "runtime" / "graph" / "other-store",
        tmp_path / "outside",
    ]

    for forbidden_root in forbidden_roots:
        with pytest.raises(GraphStorePathError):
            write_snapshot_manifest(
                snapshot,
                repo_root=tmp_path,
                store_root=forbidden_root,
                builder="runtime.graph.builder.full_pipeline",
                source_model="runtime.graph.GraphSnapshot.v1",
            )


def test_snapshot_store_rejects_manifest_that_points_outside_store(tmp_path):
    store_root = tmp_path / "runtime" / "graph" / "store"
    manifest_path = store_root / "manifests" / "snapshots" / "bad.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "graph_snapshot_manifest.v1",
                "snapshot_id": "bad",
                "created_at": "2026-05-12T01:02:03Z",
                "builder": "test",
                "source_model": "runtime.graph.GraphSnapshot.v1",
                "vault_root_hash": None,
                "scope": [],
                "source_file_count": 0,
                "node_count": 0,
                "edge_count": 0,
                "snapshot_path": "02_KNOWLEDGE/bad.json",
                "source_hashes_path": None,
                "identity_registry_version": "node_identity_registry.v1",
                "canonical_mutation_allowed": False,
                "generated_from_read_only_scan": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(GraphStorePathError):
        load_snapshot_manifest(manifest_path, repo_root=tmp_path)


def test_snapshot_manifest_write_does_not_modify_markdown_frontmatter_or_node_id_sources(tmp_path):
    source_doc = tmp_path / "06_AGENTS" / "HERMES.md"
    source_doc.parent.mkdir(parents=True)
    original = "---\ntitle: Hermes\n---\n\n# HERMES\n"
    source_doc.write_text(original, encoding="utf-8")

    write_snapshot_manifest(
        _snapshot(),
        repo_root=tmp_path,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
    )

    assert source_doc.read_text(encoding="utf-8") == original
    assert not (tmp_path / "02_KNOWLEDGE").exists()
