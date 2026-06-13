"""Tests for Phase 10Y typed graph/trust visual overlays."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.graph_visual_model import (
    EDGE_LAYER_EXPORT_LABELS,
    MODEL_VERSION as VISUAL_MODEL_VERSION,
    build_graph_visual_model,
    normalize_edge_layer,
)
from runtime.studio.graph_visual_overlays import (
    MODEL_VERSION,
    SURFACE_ID,
    build_graph_visual_overlays,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _seed_notes(vault: Path) -> None:
    (vault / "01_PROJECTS").mkdir(parents=True)
    (vault / "02_KNOWLEDGE" / "canonical").mkdir(parents=True)
    (vault / "02_KNOWLEDGE" / "generated").mkdir(parents=True)
    (vault / "03_INPUTS").mkdir(parents=True)
    (vault / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (vault / "01_PROJECTS" / "Apollo.md").write_text(
        "---\nstatus: promoted\n---\n# Apollo\nLinks to [[Canonical]] and [[Missing Target]].\n",
        encoding="utf-8",
    )
    (vault / "02_KNOWLEDGE" / "canonical" / "Canonical.md").write_text(
        "---\nstatus: canonical\n---\n# Canonical\n",
        encoding="utf-8",
    )
    (vault / "02_KNOWLEDGE" / "generated" / "Generated.md").write_text(
        "---\nknowledge_class: generated\n---\n# Generated\n",
        encoding="utf-8",
    )
    (vault / "03_INPUTS" / "Raw Capture.md").write_text("# Raw Capture\n", encoding="utf-8")
    (vault / "07_LOGS" / "Build-Logs" / "2026-05-07-Test.md").write_text("# Log\n", encoding="utf-8")


def test_graph_visual_overlays_builds_complete_read_only_contract(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_graph_visual_overlays(vault, max_files=20, max_nodes=200, max_edges=300)

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["readiness"]["typed_graph_trust_overlays_ready"] is True
    assert model["readiness"]["all_14_node_families_available"] is True
    assert model["readiness"]["all_4_edge_layers_available"] is True
    assert model["readiness"]["all_8_trust_states_available"] is True
    assert model["readiness"]["runtime_action_layer_available"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["visual_model"]["model_version"] == VISUAL_MODEL_VERSION
    assert len(model["visual_model"]["legend"]["node_families"]) == 14
    assert len(model["visual_model"]["legend"]["edge_layers"]) == 4
    assert len(model["visual_model"]["legend"]["trust_states"]) == 8
    assert any(item["canonical"] for item in model["visual_model"]["node_visuals"])
    assert any(item["generated"] for item in model["visual_model"]["node_visuals"])
    assert model["authority"]["writes_trust_state"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_graph_visual_model_normalizes_runtime_action_alias_and_badges() -> None:
    nodes = [
        {
            "id": "n1",
            "node_type": "generated_artifact_doc",
            "node_family": "generated_artifact",
            "label": "Generated Proposal",
            "properties": {"trust_state": "generated"},
        },
        {
            "id": "n2",
            "node_type": "knowledge_doc",
            "label": "Canonical Note",
            "properties": {"trust_state": "canonical"},
        },
    ]
    edges = [
        {"id": "e1", "source": "n1", "target": "n2", "relation": "output_of", "edge_layer": "runtime-action"}
    ]

    model = build_graph_visual_model(nodes, edges)

    assert normalize_edge_layer("runtime-action") == "runtime"
    assert EDGE_LAYER_EXPORT_LABELS["runtime"] == "Runtime-Action"
    assert model["edge_visuals"][0]["edge_layer"] == "runtime"
    assert model["edge_visuals"][0]["canonical_layer"] == "runtime-action"
    assert "content--generated" in model["node_visuals"][0]["classes"]
    assert "content--canonical" in model["node_visuals"][1]["classes"]
    assert "AI" in model["node_visuals"][0]["display_badges"]


def test_graph_visual_overlays_missing_target_fails_cleanly_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    model = build_graph_visual_overlays(vault, folder_path="missing")

    assert _snapshot(vault) == before
    assert model["ok"] is False
    assert model["readiness"]["typed_graph_trust_overlays_ready"] is False
    assert "target-folder-does-not-exist" in model["readiness"]["blockers"]
    assert model["authority"]["canonical_mutation_allowed"] is False
