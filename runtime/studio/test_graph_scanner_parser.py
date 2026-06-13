"""Tests for Phase 10X parser-backed graph scanner input."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.graph_scanner_parser import (
    MODEL_VERSION,
    SURFACE_ID,
    build_graph_scanner_parser,
    write_graph_scanner_parser_evidence,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_graph_scanner_parser_extracts_full_markdown_and_obsidian_signals(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text(
        "\n".join(
            [
                "---",
                "title: Alpha",
                "aliases:",
                "  - Alpha Alias",
                "knowledge_class: generated-ideas",
                "---",
                "# Alpha",
                "Links to [[Beta#Deep Section|beta heading]] and [[Alpha Alias]].",
                "Embed ![[Beta]] and [local](beta.md#Deep Section).",
                "External [site](https://example.com).",
                "#research/tag",
                "- [x] finished task",
                "stable block ^alpha-block",
                "```",
                "# Ignored Code Heading",
                "[[Ignored Code Link]]",
                "```",
            ]
        ),
        encoding="utf-8",
    )
    (notes / "beta.md").write_text(
        "\n".join(
            [
                "---",
                "title: Beta",
                "---",
                "# Beta",
                "## Deep Section",
                "Back to [[Alpha]].",
            ]
        ),
        encoding="utf-8",
    )
    (notes / ".git").mkdir()
    (notes / ".git" / "ignored.md").write_text("# ignored\n", encoding="utf-8")
    before = _snapshot(vault)

    model = build_graph_scanner_parser(vault, folder_path="notes")
    repeat = build_graph_scanner_parser(vault, folder_path="notes")

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["readiness"]["graph_scanner_parser_ready"] is True
    assert model["readiness"]["parser_backed_graph_input_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10aa-controlled-node-create-edit"
    assert model["parser_summary"]["discovered_file_count"] == 2
    assert model["parser_summary"]["scanned_file_count"] == 2
    assert model["parser_summary"]["frontmatter_file_count"] == 2
    assert model["parser_summary"]["heading_count"] == 3
    assert model["parser_summary"]["wikilink_count"] == 3
    assert model["parser_summary"]["markdown_link_count"] == 2
    assert model["parser_summary"]["embed_count"] == 1
    assert model["parser_summary"]["tag_count"] == 1
    assert model["parser_summary"]["task_count"] == 1
    assert model["parser_summary"]["block_id_marker_count"] == 1
    assert model["graph_summary"]["node_count"] > 0
    assert model["graph_summary"]["edge_count"] > 0
    assert model["graph_summary"]["trust_state_counts"]["generated"] >= 1
    assert model["graph_summary"]["edge_layer_counts"]["explicit"] >= 1
    assert model["graph_summary"]["edge_layer_counts"]["structural"] >= 1
    assert model["graph_summary"]["node_family_counts"]["knowledge"] >= 1
    assert model["authority"]["read_only"] is True
    assert model["authority"]["writes_vault_source_files"] is False
    assert model["authority"]["writes_graph_index"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []
    assert {node["id"] for node in model["graph_input"]["nodes"]} == {
        node["id"] for node in repeat["graph_input"]["nodes"]
    }
    assert {edge["id"] for edge in model["graph_input"]["edges"]} == {
        edge["id"] for edge in repeat["graph_input"]["edges"]
    }
    relations = {edge["relation"] for edge in model["graph_input"]["edges"]}
    assert {"contains_heading", "links_to_heading", "embeds_note", "links_to_external_resource"} <= relations


def test_graph_scanner_parser_reports_unresolved_references(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "alpha.md").write_text("# Alpha\n[[Missing Note]]\n[bad](missing.md)\n", encoding="utf-8")

    model = build_graph_scanner_parser(vault)

    assert model["ok"] is True
    assert model["graph_summary"]["unresolved_reference_count"] == 2
    assert "links_to_unresolved_wikilink" in model["graph_summary"]["relation_counts"]
    assert "links_to_unresolved_markdown_link" in model["graph_summary"]["relation_counts"]
    assert model["graph_summary"]["edge_layer_counts"]["suggested"] >= 2


def test_graph_scanner_parser_tolerates_malformed_optional_frontmatter(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "alpha.md").write_text("---\ntitle: Alpha\n# Not closed\n[[Beta]]\n", encoding="utf-8")
    (vault / "beta.md").write_text("# Beta\n", encoding="utf-8")

    model = build_graph_scanner_parser(vault)

    assert model["ok"] is True
    assert model["parser_summary"]["files_with_unclosed_frontmatter"] == 1
    assert model["parser_summary"]["parser_warning_count"] == 1
    assert model["readiness"]["parser_backed_graph_input_ready"] is True


def test_graph_scanner_parser_respects_limits_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    for index in range(3):
        (vault / f"note-{index}.md").write_text(f"# Note {index}\n", encoding="utf-8")
    before = _snapshot(vault)

    model = build_graph_scanner_parser(vault, max_files=2, max_nodes=2, max_edges=20)
    edge_limited = build_graph_scanner_parser(vault, max_files=2, max_nodes=20, max_edges=1)

    assert _snapshot(vault) == before
    assert model["parser_summary"]["discovered_file_count"] == 3
    assert model["parser_summary"]["scanned_file_count"] == 2
    assert model["parser_summary"]["file_scan_truncated"] is True
    assert model["graph_summary"]["node_output_truncated"] is True
    assert edge_limited["graph_summary"]["edge_output_truncated"] is True
    assert "graph-parser-file-scan-limit-reached" in model["readiness"]["warnings"]


def test_graph_scanner_parser_missing_target_fails_cleanly(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    missing = vault / "missing"

    model = build_graph_scanner_parser(vault, folder_path=missing)

    assert model["ok"] is False
    assert model["target"]["exists"] is False
    assert model["readiness"]["blockers"] == ["target-folder-does-not-exist"]
    assert missing.exists() is False


def test_graph_scanner_parser_evidence_write_is_explicit_and_scoped(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "alpha.md").write_text("# Alpha\n", encoding="utf-8")

    dry_run = build_graph_scanner_parser(vault)
    assert dry_run["evidence"]["written"] is False
    assert not (vault / "07_LOGS").exists()

    written = write_graph_scanner_parser_evidence(
        vault,
        evidence_slug="phase10x-test-graph-scanner-parser",
    )

    assert written["evidence"]["written"] is True
    assert written["evidence"]["json_path"].startswith("07_LOGS/Studio-Graph-Views/")
    assert written["evidence"]["markdown_path"].startswith("07_LOGS/Studio-Graph-Views/")
    assert (vault / written["evidence"]["json_path"]).is_file()
    assert (vault / written["evidence"]["markdown_path"]).is_file()
