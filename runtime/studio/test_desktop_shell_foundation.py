"""Tests for the read-only Studio desktop shell foundation contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.desktop_shell_foundation import (
    MODEL_VERSION,
    SURFACE_ID,
    build_studio_desktop_shell_foundation,
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
        "runtime/studio",
        "07_LOGS/Pulse-Decks/product-shell",
    ]:
        (vault / folder).mkdir(parents=True, exist_ok=True)
    for file_path in [
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "06_AGENTS/ChaseOS-Studio-Architecture.md",
        "06_AGENTS/ChaseOS-Studio-Graph-View-Shell-Panel-Mount.md",
        "06_AGENTS/ChaseOS-Studio-Node-Inspector-Shell-Panel-Mount.md",
        "06_AGENTS/ChaseOS-Pulse-Studio-Product-Shell-Mount.md",
        "runtime/studio/runtime_cockpit.py",
        "runtime/studio/runtime_cockpit_app.py",
        "runtime/studio/desktop_shell_app.py",
        "runtime/studio/open_folder_readiness.py",
        "runtime/studio/markdown_scan_contract.py",
        "runtime/studio/graph_index_contract.py",
        "runtime/studio/node_inspector_contract.py",
        "runtime/studio/node_inspector_shell_panel.py",
        "runtime/studio/graph_view_contract.py",
        "runtime/studio/graph_view_static_renderer.py",
        "runtime/studio/graph_view_shell_panel.py",
        "runtime/studio/pulse_product_shell_panel.py",
        "runtime/studio/app_launcher.py",
        "runtime/studio/dashboard.py",
        "runtime/studio/acquisition_cockpit.py",
        "runtime/studio/pulse_deck_app.py",
        "runtime/studio/product_ui_test_app.py",
    ]:
        target = vault / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("placeholder\n", encoding="utf-8")
    (vault / "07_LOGS/Pulse-Decks/product-shell/2026-05-03-pulse-product-shell.html").write_text(
        "<html>Pulse product shell</html>\n",
        encoding="utf-8",
    )
    (vault / "07_LOGS/Pulse-Decks/product-shell/2026-05-03-pulse-product-shell-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )
    return vault


def test_foundation_contract_reports_real_shell_truth_and_boundaries(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)

    model = build_studio_desktop_shell_foundation(vault)

    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["workspace"]["mode"] == "chaseos_native_detected"
    assert model["shell_truth"]["foundation_contract_built"] is True
    assert model["shell_truth"]["read_only_studio_shell_mvp_built"] is True
    assert model["shell_truth"]["full_standalone_desktop_shell_built"] is False
    assert model["shell_truth"]["start_new_open_folder_built"] is False
    assert model["shell_truth"]["open_folder_readiness_contract_built"] is True
    assert model["shell_truth"]["markdown_scan_contract_built"] is True
    assert model["shell_truth"]["graph_index_contract_built"] is True
    assert model["shell_truth"]["node_inspector_contract_built"] is True
    assert model["shell_truth"]["node_inspector_shell_panel_contract_built"] is True
    assert model["shell_truth"]["node_inspector_shell_panel_mounted"] is False
    assert model["shell_truth"]["node_inspector_shell_panel_browser_qa_built"] is False
    assert model["shell_truth"]["graph_view_contract_built"] is True
    assert model["shell_truth"]["graph_view_static_renderer_built"] is True
    assert model["shell_truth"]["graph_view_static_browser_qa_built"] is False
    assert model["shell_truth"]["graph_view_shell_panel_contract_built"] is True
    assert model["shell_truth"]["graph_view_shell_panel_mounted"] is False
    assert model["shell_truth"]["pulse_product_shell_browser_qa_built"] is True
    assert model["shell_truth"]["pulse_product_shell_panel_contract_built"] is True
    assert model["shell_truth"]["pulse_product_shell_mounted"] is True
    assert model["shell_truth"]["graph_engine_foundation_built"] is False
    assert model["shell_truth"]["graph_view_built"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["starts_servers"] is False
    assert model["authority"]["starts_child_apps"] is False
    assert model["authority"]["writes_vault"] is False
    assert model["authority"]["writes_host_startup"] is False
    assert model["authority"]["workflow_execution_allowed"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-static-render-browser-qa"


def test_foundation_contract_lists_current_footholds_and_planned_gaps(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)

    model = build_studio_desktop_shell_foundation(vault)

    footholds = {item["id"]: item for item in model["footholds"]}
    assert footholds["runtime-cockpit-contract"]["present"] is True
    assert footholds["runtime-cockpit-app"]["present"] is True
    assert footholds["desktop-shell-app"]["present"] is True
    assert footholds["open-folder-readiness-contract"]["present"] is True
    assert footholds["markdown-scan-contract"]["present"] is True
    assert footholds["graph-index-contract"]["present"] is True
    assert footholds["node-inspector-contract"]["present"] is True
    assert footholds["node-inspector-shell-panel-contract"]["present"] is True
    assert footholds["node-inspector-shell-panel-mount"]["present"] is True
    assert footholds["graph-view-contract"]["present"] is True
    assert footholds["graph-view-static-renderer"]["present"] is True
    assert footholds["graph-view-shell-panel-contract"]["present"] is True
    assert footholds["pulse-product-shell-panel-contract"]["present"] is True
    assert footholds["pulse-product-shell-studio-mount"]["present"] is True
    assert footholds["app-launcher"]["present"] is True
    assert footholds["product-ui-test-app"]["present"] is True
    assert model["readiness"]["present_foothold_count"] == model["readiness"]["current_foothold_count"]

    gaps = {item["id"]: item for item in model["planned_gaps"]}
    assert gaps["standalone-desktop-packaging"]["status"] == "PLANNED / NOT BUILT"
    assert gaps["start-new-open-folder-flow"]["phase_lane"] == "10A"
    assert gaps["start-new-open-folder-flow"]["status"] == "PARTIAL / READINESS CONTRACT BUILT / UI NOT BUILT"
    assert gaps["file-scanner-markdown-parser"]["status"] == "PARTIAL / MARKDOWN SCAN CONTRACT BUILT / FULL PARSER NOT BUILT"
    assert gaps["graph-index-foundation"]["status"] == "PARTIAL / GRAPH INDEX CONTRACT BUILT / PERSISTED GRAPH ENGINE NOT BUILT"
    assert gaps["node-inspector-read-only"]["status"] == "PARTIAL / NODE INSPECTOR CONTRACT BUILT / UI NOT BUILT"
    assert gaps["node-inspector-shell-panel-contract"]["status"] == "PLANNED / GRAPH SHELL BROWSER QA REQUIRED FIRST / SHELL MOUNT NOT BUILT"
    assert gaps["node-inspector-shell-panel-mount"]["status"] == "PLANNED / NODE INSPECTOR SHELL-PANEL CONTRACT REQUIRED FIRST / BROWSER QA NOT VERIFIED"
    assert gaps["graph-view-read-only"]["status"] == "PARTIAL / GRAPH VIEW CONTRACT BUILT / STATIC RENDERER BUILT / FULL UI NOT BUILT"
    assert gaps["graph-view-static-browser-qa"]["status"] == "PLANNED / STATIC RENDERER BUILT / BROWSER QA NOT VERIFIED"
    assert gaps["graph-view-shell-panel-browser-qa"]["status"] == "PLANNED / SHELL MOUNT REQUIRED FIRST / BROWSER QA NOT VERIFIED"
    assert gaps["pulse-product-shell-browser-qa"]["status"] == "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
    assert gaps["pulse-product-shell-panel-contract"]["status"] == "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
    assert gaps["pulse-product-shell-studio-mount"]["status"] == "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
    assert gaps["approval-driven-host-mutation-executor"]["status"] == "PLANNED / NOT BUILT"


def test_foundation_contract_advances_after_static_browser_qa_evidence(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )

    model = build_studio_desktop_shell_foundation(vault)

    assert model["shell_truth"]["graph_view_static_browser_qa_built"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-shell-panel-mount"
    gaps = {item["id"]: item for item in model["planned_gaps"]}
    assert gaps["graph-view-static-browser-qa"]["status"] == "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
    assert gaps["graph-view-shell-panel-contract"]["status"] == "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
    sequence = {item["pass_id"]: item for item in model["implementation_sequence"]}
    assert sequence["phase10-studio-graph-view-static-render-browser-qa"]["status"] == "IMPLEMENTED / VERIFIED TARGETED"
    assert sequence["phase10-studio-graph-view-shell-panel-contract"]["status"] == "IMPLEMENTED / VERIFIED TARGETED"
    assert sequence["phase10-studio-graph-view-shell-panel-mount"]["status"] == "NEXT RECOMMENDED"


def test_foundation_contract_static_browser_qa_status_reflects_built_shell_mount(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03T09-39-25-844850Z-graph-view-static.html").write_text(
        "<html>Graph</html>\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "static browser qa evidence\n",
        encoding="utf-8",
    )
    (vault / "runtime/studio/desktop_shell_app.py").write_text(
        "build_graph_view_shell_panel_contract\n/graph-view-shell-panel.json\ngraph-view-panel-mount\n",
        encoding="utf-8",
    )

    model = build_studio_desktop_shell_foundation(vault)

    assert model["shell_truth"]["graph_view_shell_panel_mounted"] is True
    assert model["shell_truth"]["graph_view_shell_panel_browser_qa_built"] is False
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-shell-panel-browser-qa"
    gaps = {item["id"]: item for item in model["planned_gaps"]}
    assert gaps["graph-view-static-browser-qa"]["status"] == "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
    assert gaps["graph-view-shell-panel-browser-qa"]["status"] == "NEXT RECOMMENDED / READ-ONLY SHELL MOUNT BUILT / BROWSER QA NOT VERIFIED"


def test_foundation_contract_advances_after_shell_panel_browser_qa(tmp_path: Path) -> None:
    vault = _chaseos_vault(tmp_path)
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03T09-39-25-844850Z-graph-view-static.html").write_text(
        "<html>Graph</html>\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "static browser qa evidence\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-shell-panel-browser-qa.md").write_text(
        "shell panel browser qa evidence\n",
        encoding="utf-8",
    )
    (vault / "runtime/studio/desktop_shell_app.py").write_text(
        "build_graph_view_shell_panel_contract\n/graph-view-shell-panel.json\ngraph-view-panel-mount\n",
        encoding="utf-8",
    )

    model = build_studio_desktop_shell_foundation(vault)

    assert model["shell_truth"]["graph_view_shell_panel_mounted"] is True
    assert model["shell_truth"]["graph_view_shell_panel_browser_qa_built"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-shell-panel-mount"
    gaps = {item["id"]: item for item in model["planned_gaps"]}
    assert gaps["graph-view-shell-panel-browser-qa"]["status"] == "COMPLETE / VERIFIED TARGETED / NODE INSPECTOR PANEL CONTRACT BUILT"
    assert gaps["node-inspector-shell-panel-contract"]["status"] == "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
    assert gaps["node-inspector-shell-panel-mount"]["status"] == "NEXT RECOMMENDED / NODE INSPECTOR SHELL-PANEL CONTRACT BUILT / BROWSER QA NOT VERIFIED"
    sequence = {item["pass_id"]: item for item in model["implementation_sequence"]}
    assert sequence["phase10-studio-graph-view-shell-panel-browser-qa"]["status"] == "IMPLEMENTED / VERIFIED TARGETED"
    assert sequence["phase10-studio-node-inspector-shell-panel-contract"]["status"] == "IMPLEMENTED / VERIFIED TARGETED"
    assert sequence["phase10-studio-node-inspector-shell-panel-mount"]["status"] == "NEXT RECOMMENDED"


def test_foundation_contract_detects_partial_or_unknown_workspace(tmp_path: Path) -> None:
    vault = tmp_path / "markdown"
    vault.mkdir()
    (vault / "README.md").write_text("general markdown workspace\n", encoding="utf-8")

    model = build_studio_desktop_shell_foundation(vault)

    assert model["workspace"]["mode"] == "partial_or_general_markdown"
    assert model["workspace"]["missing_dirs"]
    assert model["workspace"]["detection_is_read_only"] is True
    assert model["shell_truth"]["read_only_studio_shell_mvp_built"] is False
    assert "desktop-shell-app" in model["readiness"]["missing_foothold_ids"]
