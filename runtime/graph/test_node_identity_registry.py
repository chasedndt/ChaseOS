from __future__ import annotations

import json
from pathlib import Path

from runtime.graph.store.identity import (
    NODE_IDENTITY_REGISTRY_SCHEMA_VERSION,
    load_node_identity_registry,
    resolve_studio_node_identity,
)


def test_node_identity_registry_loads_and_resolves_stable_source_keys(tmp_path: Path) -> None:
    registry_path = tmp_path / "runtime" / "graph" / "store" / "identity" / "node_identity_registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": NODE_IDENTITY_REGISTRY_SCHEMA_VERSION,
                "updated_at": "2026-05-12T01:02:03Z",
                "authority": {
                    "canonical_write_allowed": False,
                    "requires_gate_for_source_write": True,
                    "generated_by": "phase9_graph_storage_contract",
                },
                "nodes": {
                    "studio:file:06_AGENTS/HERMES.md": {
                        "durable_node_id": "node_hermes_runtime_profile",
                        "source_key": "studio:file:06_AGENTS/HERMES.md",
                        "current_derived_ids": ["studio:agent_control_doc:abc123"],
                        "source_path": "06_AGENTS/HERMES.md",
                        "node_type": "agent_control_doc",
                        "first_seen_snapshot": "graph-snap-a",
                        "last_seen_snapshot": "graph-snap-b",
                        "status": "active",
                        "provenance": "derived_from_markdown_scan_contract",
                        "canonical_ref": None,
                    }
                },
                "aliases": {},
            }
        ),
        encoding="utf-8",
    )

    registry = load_node_identity_registry(registry_path)
    resolved = resolve_studio_node_identity(
        {
            "id": "studio:agent_control_doc:abc123",
            "node_type": "agent_control_doc",
            "stable_key": "06_AGENTS/HERMES.md",
            "confidence": "direct_file_scan",
            "properties": {"path": "06_AGENTS/HERMES.md"},
        },
        registry,
        snapshot_id="graph-snap-b",
    )

    assert registry.schema_version == NODE_IDENTITY_REGISTRY_SCHEMA_VERSION
    assert registry.authority["canonical_write_allowed"] is False
    assert resolved["source_key"] == "studio:file:06_AGENTS/HERMES.md"
    assert resolved["durable_node_id"] == "node_hermes_runtime_profile"
    assert resolved["identity_state"] == "registered"
    assert resolved["snapshot_id"] == "graph-snap-b"
    assert resolved["registry_version"] == NODE_IDENTITY_REGISTRY_SCHEMA_VERSION
    assert resolved["read_only"] is True


def test_unregistered_studio_nodes_are_explicit_read_only_without_durable_ids() -> None:
    resolved = resolve_studio_node_identity(
        {
            "id": "studio:markdown_heading:def456",
            "node_type": "markdown_heading",
            "stable_key": "06_AGENTS/HERMES.md#heading:11:HERMES",
            "confidence": "derived_heading",
            "properties": {"path": "06_AGENTS/HERMES.md", "line": 11},
        },
        registry=None,
        snapshot_id="graph-snap-b",
    )

    assert resolved["source_key"] == "studio:markdown_heading:06_AGENTS/HERMES.md#heading:11:HERMES"
    assert "durable_node_id" not in resolved
    assert resolved["identity_state"] == "unregistered"
    assert resolved["read_only"] is True
    assert resolved["registration_required_for_mutation"] is True
