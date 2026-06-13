"""Tests for the read-only Studio node inspector contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.node_inspector_contract import (
    MODEL_VERSION,
    SURFACE_ID,
    build_node_inspector_contract,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _seed_notes(vault: Path) -> None:
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text(
        "\n".join(
            [
                "# Alpha",
                "Links to [[Beta]] and [site](https://example.com).",
                "#tag",
                "- [ ] follow up",
                "stable block ^alpha-block",
            ]
        ),
        encoding="utf-8",
    )
    (notes / "beta.md").write_text("# Beta\nBack to [[Alpha]].\n", encoding="utf-8")


def test_node_inspector_contract_inspects_file_node_by_path_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_node_inspector_contract(vault, path="alpha.md", folder_path="notes")

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["selector"] == {"selector_type": "path", "selector_value": "alpha.md"}
    assert model["selected_node"]["properties"]["path"] == "alpha.md"
    assert model["edge_context"]["outgoing_edge_count"] >= 1
    assert "contains_heading" in model["edge_context"]["relation_counts"]
    assert model["source_excerpt"]["available"] is True
    assert "# Alpha" in model["source_excerpt"]["text"]
    assert model["readiness"]["node_inspector_contract_ready"] is True
    assert model["readiness"]["node_inspector_ui_ready"] is False
    assert model["readiness"]["graph_scanner_parser_ready"] is True
    assert model["readiness"]["parser_backed_graph_input_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["inspector_truth"]["node_inspector_contract_built"] is True
    assert model["inspector_truth"]["node_inspector_ui_built"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["writes_node_ids"] is False
    assert model["authority"]["node_editing_allowed"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_node_inspector_contract_surfaces_identity_trust_and_provenance_evidence_read_only(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    sidecar = {
        "schema_version": "1.0",
        "capture_id": "cap-alpha",
        "content_sha256": "abc123",
        "source_platform": "local",
        "captured_at": "2026-05-07T00:00:00Z",
        "injection_scan": "clean",
        "promotion_status": "promoted",
        "quarantine_status": "reviewed",
    }
    (vault / "notes" / "alpha.meta.json").write_text(json.dumps(sidecar), encoding="utf-8")
    before = _snapshot(vault)

    model = build_node_inspector_contract(vault, path="alpha.md", folder_path="notes")

    assert _snapshot(vault) == before
    assert model["node_identity"] == {
        "id": model["selected_node"]["id"],
        "label": "alpha",
        "node_type": "markdown_note",
        "node_family": "knowledge",
        "stable_key": "alpha.md",
        "path": "alpha.md",
        "source": "parsed_markdown_graph_scanner",
        "confidence": "direct_file_scan",
    }
    assert model["provenance_summary"]["status"] == "present"
    assert model["provenance_summary"]["capture_id"] == "cap-alpha"
    assert model["provenance_summary"]["sidecar_path"] == "notes/alpha.meta.json"
    assert model["trust_evidence"]["graph_trust_state"] == "raw"
    assert model["trust_evidence"]["provenance_trust_state"] == "promoted"
    assert model["trust_evidence"]["metadata_conflict"] is True
    assert model["metadata_state"]["stale_or_ambiguous_metadata"] is True
    assert model["readiness"]["provenance_evidence_ready"] is True
    assert "metadata-trust-conflict" in model["readiness"]["warnings"]
    assert model["authority"]["writes_sidecar"] is False
    assert model["authority"]["writes_trust_state"] is False


def test_node_inspector_contract_tolerates_missing_provenance_sidecar_as_stale_metadata(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_node_inspector_contract(vault, path="alpha.md", folder_path="notes")

    assert _snapshot(vault) == before
    assert model["provenance_summary"]["status"] == "missing"
    assert model["metadata_state"]["stale_or_ambiguous_metadata"] is True
    assert model["readiness"]["missing_provenance_tolerated"] is True
    assert "sidecar-provenance-missing" in model["readiness"]["warnings"]
    assert model["possible_writes"] == []


def test_node_inspector_contract_inspects_heading_node_by_id(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    graph = build_graph_index_contract(vault, folder_path="notes")
    heading = next(node for node in graph["graph"]["nodes"] if node["node_type"] == "markdown_heading")

    model = build_node_inspector_contract(vault, node_id=heading["id"], folder_path="notes")

    assert model["ok"] is True
    assert model["selector"]["selector_type"] == "node_id"
    assert model["selected_node"]["id"] == heading["id"]
    assert model["selected_node"]["node_type"] == "markdown_heading"
    assert model["edge_context"]["incoming_edge_count"] >= 1
    assert model["source_excerpt"]["available"] is True
    assert model["source_excerpt"]["path"] == "alpha.md"


def test_node_inspector_contract_advances_after_graph_view_contract_exists(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True)
    (studio / "graph_view_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_node_inspector_contract(vault, path="alpha.md", folder_path="notes")

    assert model["readiness"]["graph_view_contract_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["inspector_truth"]["graph_view_contract_built"] is True
    assert model["inspector_truth"]["graph_view_built"] is False


def test_node_inspector_contract_requires_selector_without_mutating(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_node_inspector_contract(vault, folder_path="notes")

    assert _snapshot(vault) == before
    assert model["ok"] is False
    assert model["readiness"]["selected_node_found"] is False
    assert model["readiness"]["blockers"] == ["node-selector-required"]
    assert model["authority"]["writes_vault"] is False


def test_node_inspector_contract_reports_missing_node(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)

    model = build_node_inspector_contract(vault, node_id="missing-node", folder_path="notes")

    assert model["ok"] is False
    assert model["readiness"]["blockers"] == ["node-not-found"]
    assert model["source_excerpt"]["available"] is False
    assert model["source_excerpt"]["reason"] == "node-not-selected"
