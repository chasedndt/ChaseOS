"""Tests for the read-only Studio graph index contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.graph_index_contract import (
    MODEL_VERSION,
    SURFACE_ID,
    build_graph_index_contract,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_graph_index_contract_derives_stable_nodes_and_edges_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text(
        "\n".join(
            [
                "---",
                "title: Alpha",
                "---",
                "# Alpha",
                "Links to [[Beta]] and [site](https://example.com).",
                "#tag",
                "- [ ] follow up",
                "stable block ^alpha-block",
            ]
        ),
        encoding="utf-8",
    )
    (notes / "beta.md").write_text("# Beta\n", encoding="utf-8")
    before = _snapshot(vault)

    model = build_graph_index_contract(vault, folder_path="notes")
    repeat = build_graph_index_contract(vault, folder_path="notes")

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["target"]["open_folder_mode"] == "general_markdown_or_obsidian"
    assert model["source_scan"]["scan_summary"]["scanned_file_count"] == 2
    assert model["readiness"]["graph_index_contract_ready"] is True
    assert model["readiness"]["persisted_graph_index_ready"] is False
    assert model["readiness"]["node_inspector_ready"] is False
    assert model["readiness"]["graph_scanner_parser_ready"] is True
    assert model["readiness"]["parser_backed_graph_input_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["source_parser"]["surface"] == "studio_graph_scanner_parser"
    assert model["graph_truth"]["derived_graph_index_contract_built"] is True
    assert model["graph_truth"]["parser_backed_graph_input_built"] is True
    assert model["graph_truth"]["persistent_graph_snapshot_built"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["writes_graph_index"] is False
    assert model["authority"]["writes_node_ids"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []

    node_ids = {node["id"] for node in model["graph"]["nodes"]}
    edge_relations = {edge["relation"] for edge in model["graph"]["edges"]}
    assert node_ids == {node["id"] for node in repeat["graph"]["nodes"]}
    assert {edge["id"] for edge in model["graph"]["edges"]} == {
        edge["id"] for edge in repeat["graph"]["edges"]
    }
    assert "contains_heading" in edge_relations
    assert "links_to_note" in edge_relations
    assert "links_to_external_resource" in edge_relations
    assert "has_tag" in edge_relations
    assert "contains_task" in edge_relations
    assert "contains_block_marker" in edge_relations


def test_graph_index_contract_reports_unresolved_references(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "alpha.md").write_text("# Alpha\n[[Missing Note]]\n", encoding="utf-8")

    model = build_graph_index_contract(vault)

    assert model["ok"] is True
    assert model["graph_summary"]["unresolved_reference_count"] == 1
    assert model["samples"]["unresolved_references"][0]["target"] == "Missing Note"
    assert "links_to_unresolved_wikilink" in model["graph_summary"]["relation_counts"]


def test_graph_index_contract_advances_after_graph_view_contract_exists(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True)
    (studio / "node_inspector_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "graph_view_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_graph_index_contract(vault, folder_path="notes")

    assert model["readiness"]["node_inspector_contract_ready"] is True
    assert model["readiness"]["graph_view_contract_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["graph_truth"]["graph_view_contract_built"] is True
    assert model["graph_truth"]["graph_view_built"] is False


def test_graph_index_contract_respects_node_and_edge_limits(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "alpha.md").write_text(
        "\n".join(["# Alpha", "## One", "## Two", "## Three", "[site](https://example.com)"]),
        encoding="utf-8",
    )

    node_limited = build_graph_index_contract(vault, max_nodes=2, max_edges=10)
    edge_limited = build_graph_index_contract(vault, max_nodes=20, max_edges=1)

    assert node_limited["graph_limits"]["max_nodes"] == 2
    assert node_limited["graph_summary"]["node_output_truncated"] is True
    assert "graph-node-output-limit-reached" in node_limited["readiness"]["warnings"]

    assert edge_limited["graph_limits"]["max_nodes"] == 20
    assert edge_limited["graph_limits"]["max_edges"] == 1
    assert edge_limited["graph_summary"]["edge_output_truncated"] is True
    assert "graph-edge-output-limit-reached" in edge_limited["readiness"]["warnings"]


def test_graph_index_contract_reports_missing_target_without_mutating(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    missing = vault / "missing"

    model = build_graph_index_contract(vault, folder_path=missing)

    assert model["ok"] is False
    assert model["target"]["exists"] is False
    assert model["readiness"]["graph_index_contract_ready"] is False
    assert model["readiness"]["blockers"] == ["target-folder-does-not-exist"]
    assert missing.exists() is False
    assert model["authority"]["writes_opened_folder"] is False
