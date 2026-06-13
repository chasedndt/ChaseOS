from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.graph_index_contract import build_graph_index_contract


def test_graph_index_contract_can_annotate_durable_node_identity_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    agents = vault / "06_AGENTS"
    agents.mkdir(parents=True)
    source_doc = agents / "HERMES.md"
    original = "---\ntitle: Hermes\n---\n\n# HERMES\n"
    source_doc.write_text(original, encoding="utf-8")
    registry_path = vault / "runtime" / "graph" / "store" / "identity" / "node_identity_registry.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "node_identity_registry.v1",
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
                        "current_derived_ids": [],
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

    model = build_graph_index_contract(
        vault,
        identity_registry_path=registry_path,
        snapshot_id="graph-snap-b",
    )

    hermes_node = next(node for node in model["graph"]["nodes"] if node["properties"].get("path") == "06_AGENTS/HERMES.md")
    assert source_doc.read_text(encoding="utf-8") == original
    assert hermes_node["durable_node_id"] == "node_hermes_runtime_profile"
    assert hermes_node["identity_state"] == "registered"
    assert hermes_node["source_key"] == "studio:file:06_AGENTS/HERMES.md"
    assert model["identity_registry"]["registered_node_count"] == 1
    assert model["identity_registry"]["annotated_registered_node_count"] == 1
    assert model["authority"]["writes_node_ids"] is False
    assert model["possible_writes"] == []


def test_graph_index_contract_marks_nodes_unregistered_without_registry(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\n", encoding="utf-8")

    model = build_graph_index_contract(vault, folder_path="notes", snapshot_id="graph-snap-b")

    assert model["identity_registry"]["loaded"] is False
    assert model["identity_registry"]["annotated_unregistered_node_count"] == len(model["graph"]["nodes"])
    assert {node["identity_state"] for node in model["graph"]["nodes"]} == {"unregistered"}
    assert all("durable_node_id" not in node for node in model["graph"]["nodes"])
