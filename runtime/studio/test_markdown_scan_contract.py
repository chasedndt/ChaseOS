"""Tests for the read-only Studio markdown scan contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.markdown_scan_contract import (
    MODEL_VERSION,
    SURFACE_ID,
    build_markdown_scan_contract,
)


def test_markdown_scan_contract_extracts_bounded_markdown_signals(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text(
        "\n".join(
            [
                "---",
                "title: Alpha",
                "tags:",
                "custom_key: value",
                "---",
                "# Alpha",
                "Links to [[Beta|beta note]] and [site](https://example.com).",
                "- [ ] follow up",
                "stable block ^alpha-block",
            ]
        ),
        encoding="utf-8",
    )
    (notes / "beta.md").write_text("# Beta\n#tag\n", encoding="utf-8")

    model = build_markdown_scan_contract(vault, folder_path="notes")

    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["target"]["open_folder_mode"] == "general_markdown_or_obsidian"
    assert model["scan_summary"]["discovered_file_count"] == 2
    assert model["scan_summary"]["scanned_file_count"] == 2
    assert model["scan_summary"]["frontmatter_file_count"] == 1
    assert model["scan_summary"]["heading_count"] == 2
    assert model["scan_summary"]["wikilink_count"] == 1
    assert model["scan_summary"]["markdown_link_count"] == 1
    assert model["scan_summary"]["task_count"] == 1
    assert model["scan_summary"]["block_id_marker_count"] == 1
    assert set(model["samples"]["frontmatter_keys"]) >= {"title", "tags", "custom_key"}
    assert model["samples"]["wikilink_targets"] == ["Beta"]
    assert model["readiness"]["content_scan_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-index-contract"
    assert model["scanner_truth"]["markdown_scan_contract_built"] is True
    assert model["scanner_truth"]["graph_index_built"] is False
    assert model["scanner_truth"]["node_id_writer_built"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["reads_file_contents"] is True
    assert model["authority"]["writes_node_ids"] is False
    assert model["authority"]["writes_graph_index"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_markdown_scan_contract_advances_after_graph_contract_exists(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True)
    (studio / "graph_index_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_markdown_scan_contract(vault, folder_path="notes")

    assert model["readiness"]["graph_index_contract_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-readonly"
    assert model["scanner_truth"]["graph_index_contract_built"] is True
    assert model["scanner_truth"]["graph_index_built"] is False


def test_markdown_scan_contract_advances_after_node_inspector_contract_exists(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True)
    (studio / "graph_index_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "node_inspector_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_markdown_scan_contract(vault, folder_path="notes")

    assert model["readiness"]["node_inspector_contract_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-readonly-contract"
    assert model["scanner_truth"]["node_inspector_contract_built"] is True


def test_markdown_scan_contract_advances_after_graph_view_contract_exists(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\n", encoding="utf-8")
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True)
    (studio / "graph_index_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "node_inspector_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "graph_view_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_markdown_scan_contract(vault, folder_path="notes")

    assert model["readiness"]["graph_view_contract_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-local-static-render"
    assert model["scanner_truth"]["graph_view_contract_built"] is True
    assert model["scanner_truth"]["graph_view_built"] is False


def test_markdown_scan_contract_respects_file_limit(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    for index in range(3):
        (vault / f"note-{index}.md").write_text(f"# Note {index}\n", encoding="utf-8")

    model = build_markdown_scan_contract(vault, max_files=2)

    assert model["ok"] is True
    assert model["scan_limits"]["max_files"] == 2
    assert model["scan_summary"]["discovered_file_count"] == 3
    assert model["scan_summary"]["scanned_file_count"] == 2
    assert model["scan_summary"]["file_scan_truncated"] is True
    assert "markdown-file-scan-limit-reached" in model["readiness"]["warnings"]


def test_markdown_scan_contract_reports_missing_target_without_mutating(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    missing = vault / "missing"

    model = build_markdown_scan_contract(vault, folder_path=missing)

    assert model["ok"] is False
    assert model["target"]["exists"] is False
    assert model["scan_summary"]["discovered_file_count"] == 0
    assert model["scan_summary"]["scanned_file_count"] == 0
    assert model["readiness"]["folder_scan_ready"] is False
    assert model["readiness"]["content_scan_ready"] is False
    assert model["readiness"]["blockers"] == ["target-folder-does-not-exist"]
    assert missing.exists() is False
    assert model["authority"]["writes_opened_folder"] is False


def test_markdown_scan_contract_respects_byte_limit(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "large.md").write_text("# Large\n" + ("word " * 500), encoding="utf-8")

    model = build_markdown_scan_contract(vault, max_bytes_per_file=24)

    assert model["ok"] is True
    assert model["scan_limits"]["max_bytes_per_file"] == 24
    assert model["files"][0]["truncated"] is True
    assert "markdown-file-byte-limit-reached" in model["readiness"]["warnings"]
