"""Tests for Phase 10F2 bounded Obsidian vault detection."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.obsidian_vault_detection import (
    MAX_MARKDOWN_FILES_ANALYZED,
    build_obsidian_vault_detection,
)


def _snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_detects_obsidian_vault_with_plugins_aliases_links_embeds_and_canvas(tmp_path: Path) -> None:
    obsidian = tmp_path / ".obsidian"
    (obsidian / "plugins" / "dataview").mkdir(parents=True)
    (obsidian / "snippets").mkdir()
    (obsidian / "community-plugins.json").write_text('["dataview", "templater"]', encoding="utf-8")
    (obsidian / "app.json").write_text('{"attachmentFolderPath": "assets"}', encoding="utf-8")
    (obsidian / "workspace.json").write_text('{"main": {}}', encoding="utf-8")
    (obsidian / "appearance.json").write_text('{"theme": "moonstone"}', encoding="utf-8")
    (obsidian / "snippets" / "style.css").write_text("body {}\n", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "image.png").write_bytes(b"png")
    (tmp_path / "Map.canvas").write_text('{"nodes": [], "edges": []}', encoding="utf-8")
    (tmp_path / "Root.md").write_text(
        "---\naliases:\n  - Root Alias\nstatus: draft\n---\n"
        "# Root\nSee [[Target Note]] and ![[assets/image.png]].\n"
        "![Alt](assets/image.png)\n^block-id\n",
        encoding="utf-8",
    )
    before = _snapshot(tmp_path)

    model = build_obsidian_vault_detection(tmp_path)

    assert model["ok"] is True
    assert model["pass"] == "phase10f2-obsidian-vault-detection"
    assert model["summary"]["classification"] == "obsidian_vault_detected"
    assert model["summary"]["enabled_plugin_count"] == 2
    assert model["summary"]["plugin_dir_count"] == 1
    assert model["summary"]["alias_count"] == 1
    assert model["summary"]["wikilink_count"] == 1
    assert model["summary"]["embed_count"] == 2
    assert model["summary"]["canvas_file_count"] == 1
    assert model["authority_boundary"]["writes_obsidian_config"] is False
    assert model["authority_boundary"]["activates_plugins"] is False
    assert model["performance_contract"]["reads_markdown_contents_bounded"] is True
    assert _snapshot(tmp_path) == before


def test_partial_obsidian_config_warns_without_blocking(tmp_path: Path) -> None:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / "Note.md").write_text("# Note\n", encoding="utf-8")

    model = build_obsidian_vault_detection(tmp_path)

    assert model["ok"] is True
    assert model["summary"]["classification"] == "obsidian_config_partial"
    assert "partial-obsidian-config" in model["readiness"]["warnings"]


def test_markdown_with_obsidian_features_without_config(tmp_path: Path) -> None:
    (tmp_path / "Note.md").write_text("---\nalias: Nick\n---\n[[Other]]\n", encoding="utf-8")

    model = build_obsidian_vault_detection(tmp_path)

    assert model["ok"] is True
    assert model["summary"]["classification"] == "markdown_with_obsidian_features"
    assert model["summary"]["alias_count"] == 1
    assert model["summary"]["wikilink_count"] == 1


def test_markdown_without_obsidian_features_reports_no_feature_note(tmp_path: Path) -> None:
    (tmp_path / "Note.md").write_text("# Plain\nJust markdown.\n", encoding="utf-8")

    model = build_obsidian_vault_detection(tmp_path)

    assert model["ok"] is True
    assert model["summary"]["classification"] == "markdown_without_obsidian_features"
    assert any(item["code"] == "no-obsidian-features-detected" for item in model["risk_notes"])


def test_missing_and_file_targets_block_cleanly(tmp_path: Path) -> None:
    missing = build_obsidian_vault_detection(tmp_path, folder_path=tmp_path / "missing")
    file_path = tmp_path / "file.md"
    file_path.write_text("# File\n", encoding="utf-8")
    file_target = build_obsidian_vault_detection(tmp_path, folder_path=file_path)

    assert missing["ok"] is False
    assert missing["summary"]["classification"] == "invalid_missing"
    assert "target-folder-does-not-exist" in missing["readiness"]["blockers"]
    assert file_target["ok"] is False
    assert file_target["summary"]["classification"] == "invalid_not_directory"
    assert "target-path-is-not-a-directory" in file_target["readiness"]["blockers"]


def test_bounded_markdown_analysis_limit(tmp_path: Path) -> None:
    for idx in range(MAX_MARKDOWN_FILES_ANALYZED + 4):
        (tmp_path / f"note-{idx:03d}.md").write_text(f"# Note {idx}\n[[Target]]\n", encoding="utf-8")

    model = build_obsidian_vault_detection(tmp_path)

    assert model["ok"] is True
    assert model["summary"]["markdown_files_analyzed"] == MAX_MARKDOWN_FILES_ANALYZED
    assert model["summary"]["truncated"] is True
    assert "markdown_analysis_limit_reached" in model["content_signals"]["truncation_reasons"]


def test_malformed_config_and_frontmatter_are_tolerated_as_warnings(tmp_path: Path) -> None:
    obsidian = tmp_path / ".obsidian"
    obsidian.mkdir()
    (obsidian / "community-plugins.json").write_text("[", encoding="utf-8")
    (tmp_path / "Bad.md").write_text("---\ntitle: Bad\n# missing close\n", encoding="utf-8")

    model = build_obsidian_vault_detection(tmp_path)

    assert model["ok"] is True
    assert "read-errors-present" in model["readiness"]["warnings"]
    assert "malformed-frontmatter-present" in model["readiness"]["warnings"]
