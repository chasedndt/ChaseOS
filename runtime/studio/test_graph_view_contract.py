"""Tests for the read-only Studio graph view contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.graph_view_contract import (
    MODEL_VERSION,
    SURFACE_ID,
    build_graph_view_contract,
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


def test_graph_view_contract_builds_layout_filters_and_legend_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_graph_view_contract(vault, folder_path="notes", layout_node_limit=12)

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["readiness"]["graph_view_contract_ready"] is True
    assert model["readiness"]["graph_view_ui_ready"] is False
    assert model["readiness"]["graph_scanner_parser_ready"] is True
    assert model["readiness"]["parser_backed_graph_input_ready"] is True
    assert model["readiness"]["typed_graph_trust_overlays_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["view_model"]["viewport"]["visible_node_count"] >= 2
    assert model["view_model"]["viewport"]["visible_edge_count"] >= 1
    assert model["view_model"]["layout"]["algorithm"] == "deterministic-grid-v1"
    assert model["view_model"]["layout"]["node_positions"]
    assert "markdown_heading" in model["view_model"]["filters"]["node_type_counts"]
    assert "contains_heading" in model["view_model"]["filters"]["relation_counts"]
    assert model["view_model"]["legend"]["node_types"]
    assert len(model["view_model"]["legend"]["node_families"]) == 14
    assert len(model["view_model"]["legend"]["edge_layers"]) == 4
    assert len(model["view_model"]["legend"]["trust_states"]) == 8
    assert model["view_model"]["visual_overlays"]["coverage"]["all_14_node_families_available"] is True
    explainability = model["explainability"]
    assert explainability["node_identity"]["identity_scope"] == "derived-studio-view-id"
    assert explainability["node_identity"]["id_scheme"] == "studio:<node_type>:<sha-prefix>"
    assert explainability["node_identity"]["canonical_node_id_writer_built"] is False
    assert explainability["relationship_context"]["relation_counts"]["contains_heading"] >= 1
    assert explainability["trust_evidence_overlay"]["all_14_node_families_available"] is True
    assert explainability["provenance_summary"]["writes_canonical_graph_state"] is False
    assert explainability["provenance_summary"]["persists_graph_snapshot"] is False
    assert "studio_graph_index_contract" in explainability["provenance_summary"]["source_contracts"]
    assert model["view_model"]["focus"]["requested"] is False
    assert model["graph_view_truth"]["graph_view_contract_built"] is True
    assert model["graph_view_truth"]["graph_view_ui_built"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["renders_ui"] is False
    assert model["authority"]["writes_node_ids"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_graph_view_contract_advances_after_static_browser_qa_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True)
    (studio / "graph_view_static_renderer.py").write_text("placeholder\n", encoding="utf-8")
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )

    model = build_graph_view_contract(vault, folder_path="notes", layout_node_limit=12)

    assert model["ok"] is True
    assert model["readiness"]["static_graph_renderer_ready"] is True
    assert model["readiness"]["browser_visual_qa_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["graph_view_truth"]["static_graph_browser_qa_built"] is True


def test_graph_view_contract_can_include_focus_inspector_context(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)

    model = build_graph_view_contract(
        vault,
        folder_path="notes",
        focus_path="alpha.md",
        content_excerpt_bytes=128,
    )

    focus = model["view_model"]["focus"]
    assert model["ok"] is True
    assert focus["requested"] is True
    assert focus["ok"] is True
    assert focus["selected_node"]["properties"]["path"] == "alpha.md"
    assert focus["edge_context"]["outgoing_edge_count"] >= 1
    assert focus["source_excerpt"]["available"] is True
    assert focus["source_excerpt"]["bytes_read"] <= 128


def test_graph_view_contract_respects_layout_limit(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    for index in range(6):
        (vault / f"note-{index}.md").write_text(f"# Note {index}\n", encoding="utf-8")

    model = build_graph_view_contract(vault, max_files=6, layout_node_limit=3)

    assert model["ok"] is True
    assert model["view_model"]["viewport"]["layout_node_limit"] == 3
    assert model["view_model"]["viewport"]["visible_node_count"] == 3
    assert model["view_model"]["viewport"]["node_output_truncated"] is True
    assert "graph-view-node-layout-limit-reached" in model["readiness"]["warnings"]


def test_graph_view_contract_fails_closed_for_missing_focus_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_graph_view_contract(vault, folder_path="notes", focus_path="missing.md")

    assert _snapshot(vault) == before
    assert model["ok"] is False
    assert "focus:node-not-found" in model["readiness"]["blockers"]
    assert model["view_model"]["focus"]["ok"] is False
    assert model["authority"]["writes_vault"] is False


def test_graph_view_contract_reports_missing_target(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    missing = vault / "missing"

    model = build_graph_view_contract(vault, folder_path=missing)

    assert model["ok"] is False
    assert model["target"]["exists"] is False
    assert model["readiness"]["graph_view_contract_ready"] is False
    assert "target-folder-does-not-exist" in model["readiness"]["blockers"]
    assert missing.exists() is False
