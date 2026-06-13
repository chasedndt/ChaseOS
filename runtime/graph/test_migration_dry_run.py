from __future__ import annotations

from runtime.graph.migration import (
    build_graph_migration_approval_packet,
    classify_migration_dry_run,
    reject_stale_graph_execution,
)


def test_migration_dry_run_classifies_all_preview_only_safety_states() -> None:
    before = [
        {"source_key": "studio:file:unchanged.md", "durable_node_id": "node_unchanged", "source_path": "docs/unchanged.md", "node_type": "file", "label": "Unchanged", "content_sha256": "h1"},
        {"source_key": "studio:file:missing.md", "durable_node_id": "node_missing", "source_path": "docs/missing.md", "node_type": "file", "label": "Missing", "content_sha256": "h_missing"},
        {"source_key": "studio:file:renamed-old.md", "durable_node_id": "node_renamed", "source_path": "docs/renamed-old.md", "node_type": "file", "label": "Rename", "content_sha256": "h_rename"},
        {"source_key": "studio:file:changed.md", "durable_node_id": "node_changed", "source_path": "docs/changed.md", "node_type": "file", "label": "Changed", "content_sha256": "h_old"},
        {"source_key": "studio:file:split.md", "durable_node_id": "node_split", "source_path": "docs/split.md", "node_type": "file", "label": "Split", "content_sha256": "h_split"},
        {"source_key": "studio:file:merge-a.md", "durable_node_id": "node_merge_a", "source_path": "docs/merge-a.md", "node_type": "file", "label": "Merge A", "content_sha256": "h_merge_a"},
        {"source_key": "studio:file:merge-b.md", "durable_node_id": "node_merge_b", "source_path": "docs/merge-b.md", "node_type": "file", "label": "Merge B", "content_sha256": "h_merge_b"},
    ]
    after = [
        {"source_key": "studio:file:unchanged.md", "source_path": "docs/unchanged.md", "node_type": "file", "label": "Unchanged", "content_sha256": "h1"},
        {"source_key": "studio:file:new.md", "source_path": "docs/new.md", "node_type": "file", "label": "New", "content_sha256": "h_new"},
        {"source_key": "studio:file:renamed-new.md", "source_path": "docs/renamed-new.md", "node_type": "file", "label": "Rename", "content_sha256": "h_rename"},
        {"source_key": "studio:file:changed.md", "source_path": "docs/changed.md", "node_type": "file", "label": "Changed", "content_sha256": "h_new_changed"},
        {"source_key": "studio:file:split-part-a.md", "source_path": "docs/split-part-a.md", "node_type": "file", "label": "Split A", "content_sha256": "h_split"},
        {"source_key": "studio:file:split-part-b.md", "source_path": "docs/split-part-b.md", "node_type": "file", "label": "Split B", "content_sha256": "h_split"},
        {"source_key": "studio:file:merge.md", "source_path": "docs/merge.md", "node_type": "file", "label": "Merge", "content_sha256": "merge:h_merge_a+h_merge_b"},
    ]

    plan = classify_migration_dry_run(before, after, migration_id="mig_preview_001")

    assert plan["mode"] == "dry_run"
    assert plan["apply_allowed"] is False
    assert plan["artifact_root"] == "runtime/graph/store/migrations"
    assert plan["summary"] == {
        "unchanged": 1,
        "new": 1,
        "missing": 1,
        "path_renamed": 1,
        "content_changed": 1,
        "split_candidate": 1,
        "merge_candidate": 1,
    }
    by_state = {entry["state"]: entry for entry in plan["entries"]}
    assert by_state["path_renamed"]["durable_node_id"] == "node_renamed"
    assert by_state["content_changed"]["previous_source_hash"] == "h_old"
    assert by_state["split_candidate"]["candidate_count"] == 2
    assert by_state["merge_candidate"]["previous_count"] == 2


def test_graph_migration_approval_packet_includes_source_hashes_and_rejects_stale_execution() -> None:
    plan = classify_migration_dry_run(
        [{"source_key": "studio:file:a.md", "durable_node_id": "node_a", "source_path": "docs/a.md", "node_type": "file", "label": "A", "content_sha256": "hash_at_preview"}],
        [{"source_key": "studio:file:a.md", "source_path": "docs/a.md", "node_type": "file", "label": "A", "content_sha256": "hash_at_preview"}],
        migration_id="mig_preview_002",
    )

    packet = build_graph_migration_approval_packet(
        plan,
        requested_operation="graph_store.migration.write",
        artifact_path="runtime/graph/store/migrations/mig_preview_002.json",
    )

    assert packet["approval_style"] == "preview_only"
    assert packet["requested_operation"] == "graph_store.migration.write"
    assert packet["artifact_path"] == "runtime/graph/store/migrations/mig_preview_002.json"
    assert packet["canonical_mutation_allowed"] is False
    assert packet["source_hashes"] == {"docs/a.md": "hash_at_preview"}

    accepted = reject_stale_graph_execution(packet, {"docs/a.md": "hash_at_preview"})
    assert accepted == {"rejected": False, "reason": None, "stale_paths": []}

    rejected = reject_stale_graph_execution(packet, {"docs/a.md": "changed_after_preview"})
    assert rejected["rejected"] is True
    assert rejected["reason"] == "stale_source_hash"
    assert rejected["stale_paths"] == ["docs/a.md"]
