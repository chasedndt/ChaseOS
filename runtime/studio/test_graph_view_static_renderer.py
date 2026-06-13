"""Tests for the Studio graph-view static renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.studio.graph_view_static_renderer import (
    MODEL_VERSION,
    STATIC_RENDER_ROOT,
    SURFACE_ID,
    build_graph_view_static_render_model,
    render_graph_view_static_html,
    write_graph_view_static_html,
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


def test_static_render_model_renders_html_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before = _snapshot(vault)

    model = build_graph_view_static_render_model(vault, folder_path="notes", layout_node_limit=12)
    html = render_graph_view_static_html(model)

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["readiness"]["static_graph_renderer_ready"] is True
    assert model["readiness"]["browser_visual_qa_ready"] is False
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-static-render-browser-qa"
    assert model["summary"]["visible_node_count"] >= 2
    assert model["summary"]["node_family_count"] == 14
    assert model["summary"]["edge_layer_count"] == 4
    assert model["summary"]["trust_state_count"] == 8
    assert model["authority"]["writes_html_only_when_explicit"] is True
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["writes"] == []
    assert model["explainability"]["provenance_summary"]["writes_canonical_graph_state"] is False
    assert model["explainability"]["node_identity"]["identity_scope"] == "derived-studio-view-id"
    assert "<svg" in html
    assert "Alpha" in html
    assert "Node Families" in html
    assert "Trust States" in html
    assert "Edge Layers" in html
    assert "Graph Truth" in html
    assert "Studio explains graph truth but does not create canonical graph truth" in html
    assert "trust-ring" in html
    assert "deterministic-grid-v1" in html
    assert "<script" not in html.lower()


def test_static_render_model_advances_after_browser_qa_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    evidence_root = vault / STATIC_RENDER_ROOT
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )

    model = build_graph_view_static_render_model(vault, folder_path="notes", layout_node_limit=12)

    assert model["ok"] is True
    assert model["summary"]["static_browser_qa_built"] is True
    assert model["readiness"]["browser_visual_qa_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-shell-panel-contract"
    assert model["graph_view_truth"]["static_graph_browser_qa_built"] is True


def test_static_render_write_requires_explicit_call_and_writes_only_artifact(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    before_alpha = (vault / "notes" / "alpha.md").read_text(encoding="utf-8")

    model = write_graph_view_static_html(
        vault,
        folder_path="notes",
        layout_node_limit=12,
        generated_at="2026-05-03T10:15:00Z",
    )

    assert model["ok"] is True
    assert model["artifact"]["write_executed"] is True
    assert model["artifact"]["html_output_path"].startswith(STATIC_RENDER_ROOT.as_posix())
    assert model["writes"] == [model["artifact"]["html_output_path"]]
    output = vault / model["artifact"]["html_output_path"]
    assert output.exists()
    assert output.suffix == ".html"
    assert "ChaseOS Studio Graph View" in output.read_text(encoding="utf-8")
    assert (vault / "notes" / "alpha.md").read_text(encoding="utf-8") == before_alpha


def test_static_render_blocks_output_outside_artifact_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    outside = tmp_path / "outside.html"

    with pytest.raises(ValueError):
        write_graph_view_static_html(vault, folder_path="notes", output_path=outside)

    assert outside.exists() is False


def test_static_render_focus_context_visible(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)

    model = build_graph_view_static_render_model(
        vault,
        folder_path="notes",
        focus_path="alpha.md",
        content_excerpt_bytes=128,
    )
    html = render_graph_view_static_html(model)

    assert model["ok"] is True
    assert model["summary"]["focus_requested"] is True
    assert model["summary"]["focus_ok"] is True
    assert model["view_model"]["focus"]["source_excerpt"]["available"] is True
    assert "Alpha" in html
    assert "stable block" in html


def test_static_render_reports_missing_target_without_write(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    model = build_graph_view_static_render_model(vault, folder_path="missing")
    html = render_graph_view_static_html(model)

    assert _snapshot(vault) == before
    assert model["ok"] is False
    assert "target-folder-does-not-exist" in model["readiness"]["blockers"]
    assert "SOURCE CONTRACT NOT READY" in model["status"]
    assert "target-folder-does-not-exist" in html
