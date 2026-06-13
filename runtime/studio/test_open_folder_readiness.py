"""Tests for the read-only Studio Open Folder readiness contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.open_folder_readiness import (
    MODEL_VERSION,
    SURFACE_ID,
    build_open_folder_readiness,
)


def _chaseos_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    for folder in [
        "00_HOME",
        "01_PROJECTS",
        "02_KNOWLEDGE",
        "03_INPUTS",
        "04_SOPS",
        "05_TEMPLATES",
        "06_AGENTS",
        "07_LOGS",
        "99_ARCHIVE",
        "runtime",
    ]:
        (vault / folder).mkdir(parents=True, exist_ok=True)
    for file_path in [
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "06_AGENTS/ChaseOS-Studio-Architecture.md",
    ]:
        target = vault / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("placeholder\n", encoding="utf-8")
    return vault


def test_open_folder_readiness_detects_chaseos_native_workspace(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)

    model = build_open_folder_readiness(vault)

    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["target"]["mode"] == "chaseos_native_detected"
    assert model["chaseos_shape"]["native_required_shape_complete"] is True
    assert model["readiness"]["folder_selectable"] is True
    assert model["readiness"]["open_folder_ready"] is True
    assert model["readiness"]["workspace_import_ready"] is True
    assert model["readiness"]["chaseos_native_ready"] is True
    assert model["readiness"]["recommended_mode"] == "chaseos-native"
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-markdown-scan-contract"
    assert model["authority"]["read_only"] is True
    assert model["authority"]["reads_file_contents"] is False
    assert model["authority"]["writes_opened_folder"] is False
    assert model["authority"]["writes_node_ids"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_open_folder_readiness_advances_after_scanner_and_graph_contracts_exist(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True, exist_ok=True)
    (studio / "markdown_scan_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "graph_index_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_open_folder_readiness(vault)

    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-readonly"
    assert model["flow_truth"]["markdown_scan_contract_built"] is True
    assert model["flow_truth"]["graph_index_contract_built"] is True


def test_open_folder_readiness_advances_after_node_inspector_contract_exists(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True, exist_ok=True)
    (studio / "markdown_scan_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "graph_index_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "node_inspector_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_open_folder_readiness(vault)

    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-readonly-contract"
    assert model["flow_truth"]["node_inspector_contract_built"] is True


def test_open_folder_readiness_advances_after_graph_view_contract_exists(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True, exist_ok=True)
    (studio / "markdown_scan_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "graph_index_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "node_inspector_contract.py").write_text("placeholder\n", encoding="utf-8")
    (studio / "graph_view_contract.py").write_text("placeholder\n", encoding="utf-8")

    model = build_open_folder_readiness(vault)

    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-local-static-render"
    assert model["flow_truth"]["graph_view_contract_built"] is True
    assert model["flow_truth"]["graph_view_built"] is False


def test_open_folder_readiness_advances_after_static_browser_qa_evidence(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    studio = vault / "runtime" / "studio"
    studio.mkdir(parents=True, exist_ok=True)
    for filename in [
        "markdown_scan_contract.py",
        "graph_index_contract.py",
        "node_inspector_contract.py",
        "graph_view_contract.py",
        "graph_view_static_renderer.py",
    ]:
        (studio / filename).write_text("placeholder\n", encoding="utf-8")
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )

    model = build_open_folder_readiness(vault)

    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-shell-panel-contract"
    assert model["flow_truth"]["static_graph_renderer_built"] is True
    assert model["flow_truth"]["static_graph_browser_qa_built"] is True


def test_open_folder_readiness_detects_general_markdown_or_obsidian_workspace(tmp_path: Path) -> None:
    vault = tmp_path / "general-vault"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "notes").mkdir()
    (vault / "notes" / "alpha.md").write_text("# Alpha\n", encoding="utf-8")

    model = build_open_folder_readiness(vault)

    assert model["ok"] is True
    assert model["target"]["mode"] == "general_markdown_or_obsidian"
    assert model["target"]["has_obsidian_config"] is True
    assert model["markdown_inventory"]["markdown_file_count"] == 1
    assert model["readiness"]["open_folder_ready"] is True
    assert model["readiness"]["workspace_import_ready"] is True
    assert model["readiness"]["chaseos_native_ready"] is False
    assert model["readiness"]["general_markdown_ready"] is True
    assert model["readiness"]["recommended_mode"] == "general-markdown-compatible"
    assert "not-a-complete-chaseos-native-workspace" in model["readiness"]["warnings"]


def test_open_folder_readiness_reports_missing_target_without_mutating(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    missing = vault / "missing"

    model = build_open_folder_readiness(vault, folder_path=missing)

    assert model["ok"] is False
    assert model["target"]["mode"] == "invalid_missing"
    assert model["target"]["exists"] is False
    assert model["target"]["is_directory"] is False
    assert model["readiness"]["folder_selectable"] is False
    assert model["readiness"]["open_folder_ready"] is False
    assert model["readiness"]["recommended_mode"] == "not-ready"
    assert model["readiness"]["blockers"] == ["target-folder-does-not-exist"]
    assert missing.exists() is False
    assert model["authority"]["writes_opened_folder"] is False


def test_open_folder_readiness_resolves_relative_folder_against_vault_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    docs = vault / "docs"
    (docs / "00_HOME").mkdir(parents=True)
    (docs / "README.md").write_text("general markdown workspace\n", encoding="utf-8")
    (docs / "ROADMAP.md").write_text("roadmap\n", encoding="utf-8")
    (docs / "00_HOME" / "Now.md").write_text("now\n", encoding="utf-8")

    model = build_open_folder_readiness(vault, folder_path="docs")

    assert model["ok"] is True
    assert model["target"]["requested_path"] == "docs"
    assert model["target"]["resolved_path"] == str(docs.resolve())
    assert model["target"]["mode"] == "chaseos_partial_detected"
    assert model["readiness"]["recommended_mode"] == "chaseos-partial-review"
