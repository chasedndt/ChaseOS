"""Tests for Phase 10F3 general Markdown inference preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.general_markdown_inference_preview import (
    NEXT_RECOMMENDED_PASS,
    build_general_markdown_inference_preview,
)


def _snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_plain_markdown_folder_infers_non_canonical_graph_shape(tmp_path: Path) -> None:
    (tmp_path / "Projects").mkdir()
    (tmp_path / "Projects" / "Alpha.md").write_text(
        "---\ntitle: Alpha\ndomain: client\ntags: [phase10, graph]\n---\n"
        "# Alpha\nSee [[Beta]] and [Docs](https://example.com).\n- [ ] Build preview\n",
        encoding="utf-8",
    )
    (tmp_path / "Beta.md").write_text("# Beta\n#tag\n", encoding="utf-8")
    before = _snapshot(tmp_path)

    model = build_general_markdown_inference_preview(tmp_path)

    assert model["ok"] is True
    assert model["pass"] == "phase10f3-general-markdown-inference-preview"
    assert model["summary"]["preview_ready"] is True
    assert model["summary"]["non_canonical"] is True
    assert model["summary"]["candidate_node_count"] >= 2
    assert model["summary"]["candidate_edge_count"] >= 1
    assert model["candidate_model"]["candidate_node_type_counts"]
    assert model["candidate_model"]["candidate_edge_layer_counts"]
    assert model["candidate_model"]["source_domain_counts"]
    assert model["readiness"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert model["authority_boundary"]["writes_sidecar_hints"] is False
    assert model["authority_boundary"]["writes_graph_index"] is False
    assert model["authority_boundary"]["writes_approval_artifacts"] is False
    assert _snapshot(tmp_path) == before


def test_obsidian_folder_composes_detection_with_inference(tmp_path: Path) -> None:
    obsidian = tmp_path / ".obsidian"
    obsidian.mkdir()
    (obsidian / "workspace.json").write_text('{"main": {}}', encoding="utf-8")
    (tmp_path / "Index.md").write_text("[[Target]]\n", encoding="utf-8")
    (tmp_path / "Target.md").write_text("# Target\n", encoding="utf-8")

    model = build_general_markdown_inference_preview(tmp_path)

    assert model["ok"] is True
    assert model["target"]["obsidian_classification"] == "obsidian_vault_detected"
    assert model["component_surfaces"]["obsidian_vault_detection"]["ok"] is True
    assert model["component_surfaces"]["graph_scanner_parser"]["parser_backed_graph_input_ready"] is True


def test_unknown_and_malformed_frontmatter_are_preview_warnings(tmp_path: Path) -> None:
    (tmp_path / "Unknown.md").write_text(
        "---\nstrange_field: value\nowner: test\n---\n# Unknown\n",
        encoding="utf-8",
    )
    (tmp_path / "Bad.md").write_text("---\ntitle: Bad\n# no close\n", encoding="utf-8")

    model = build_general_markdown_inference_preview(tmp_path)
    warning_codes = {item["code"] for item in model["migration_warnings"]}

    assert model["ok"] is True
    assert "unknown-frontmatter-keys-detected" in warning_codes
    assert "malformed-frontmatter-preview-only" in warning_codes
    assert model["authority_boundary"]["migration_writer_built"] is False


def test_missing_and_file_targets_block_cleanly(tmp_path: Path) -> None:
    missing = build_general_markdown_inference_preview(tmp_path, folder_path=tmp_path / "missing")
    file_path = tmp_path / "file.md"
    file_path.write_text("# File\n", encoding="utf-8")
    file_target = build_general_markdown_inference_preview(tmp_path, folder_path=file_path)

    assert missing["ok"] is False
    assert "target-folder-does-not-exist" in missing["readiness"]["blockers"]
    assert file_target["ok"] is False
    assert "target-path-is-not-a-directory" in file_target["readiness"]["blockers"]


def test_bounded_scan_limit_is_reported_without_writes(tmp_path: Path) -> None:
    for idx in range(6):
        (tmp_path / f"note-{idx}.md").write_text(f"# Note {idx}\n[[note-{(idx + 1) % 6}]]\n", encoding="utf-8")
    before = _snapshot(tmp_path)

    model = build_general_markdown_inference_preview(tmp_path, max_files=2, max_nodes=4, max_edges=4)
    warning_codes = {item["code"] for item in model["migration_warnings"]}

    assert model["ok"] is True
    assert model["summary"]["bounded_scan_truncated"] is True
    assert "bounded-scan-truncated" in warning_codes
    assert len(model["preview_graph"]["nodes"]) <= 4
    assert len(model["preview_graph"]["edges"]) <= 4
    assert _snapshot(tmp_path) == before
