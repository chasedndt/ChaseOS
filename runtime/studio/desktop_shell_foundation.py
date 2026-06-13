"""Read-only Studio desktop shell foundation contract.

This module gives Phase 10A a machine-readable foundation map for the real
Studio shell. It records what is already implemented as local footholds, what
still has to be built, and which authority boundaries the shell must preserve.
It does not start apps, scan broadly, write files, execute workflows, call
providers, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.pulse.product_shell_browser_qa import (
    PULSE_PRODUCT_SHELL_BROWSER_QA_PASS,
    pulse_product_shell_browser_qa_evidence_built,
    pulse_product_shell_panel_contract_built,
    pulse_product_shell_studio_mount_built,
)
from runtime.studio.graph_view_browser_qa import (
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_CONTRACT,
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA,
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_MOUNT,
    STATIC_GRAPH_BROWSER_QA_PASS,
    graph_view_shell_panel_browser_qa_evidence_built,
    graph_view_shell_panel_mount_built,
    graph_view_shell_panel_contract_built,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)
from runtime.studio.node_inspector_shell_panel import (
    NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_CONTRACT,
    NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_MOUNT,
)


MODEL_VERSION = "studio.desktop_shell_foundation.v1"
SURFACE_ID = "studio_desktop_shell_foundation_contract"

_CHASEOS_DIRS = [
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
]

_CHASEOS_FILES = [
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "00_HOME/Now.md",
    "06_AGENTS/ChaseOS-Studio-Architecture.md",
]

_FOOTHOLDS = [
    {
        "id": "runtime-cockpit-contract",
        "label": "Runtime Cockpit contract",
        "phase_lane": "10D",
        "command": "chaseos studio runtime-cockpit --runtime all --json",
        "module": "runtime.studio.runtime_cockpit",
        "path": "runtime/studio/runtime_cockpit.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only desktop contract over dashboard, app launcher, and runtime startup controls",
    },
    {
        "id": "runtime-cockpit-app",
        "label": "Runtime Cockpit local mount",
        "phase_lane": "10D",
        "command": "chaseos studio runtime-cockpit-app --runtime all --host 127.0.0.1 --port 8771",
        "module": "runtime.studio.runtime_cockpit_app",
        "path": "runtime/studio/runtime_cockpit_app.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "localhost-only read-only app over the Runtime Cockpit contract",
    },
    {
        "id": "desktop-shell-app",
        "label": "ChaseOS Studio MVP shell",
        "phase_lane": "10A/10D",
        "command": "chaseos studio desktop-shell-app --runtime all --host 127.0.0.1 --port 8772",
        "module": "runtime.studio.desktop_shell_app",
        "path": "runtime/studio/desktop_shell_app.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "localhost-only read-only MVP shell over Runtime Cockpit and App Launcher",
    },
    {
        "id": "open-folder-readiness-contract",
        "label": "Studio Open Folder readiness contract",
        "phase_lane": "10A/10F",
        "command": "chaseos studio open-folder-readiness --json",
        "module": "runtime.studio.open_folder_readiness",
        "path": "runtime/studio/open_folder_readiness.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only operator-selected folder mode/readiness detection",
    },
    {
        "id": "markdown-scan-contract",
        "label": "Studio markdown scan contract",
        "phase_lane": "10A",
        "command": "chaseos studio markdown-scan-contract --json",
        "module": "runtime.studio.markdown_scan_contract",
        "path": "runtime/studio/markdown_scan_contract.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only bounded markdown scanner for future graph-index input",
    },
    {
        "id": "graph-index-contract",
        "label": "Studio graph index contract",
        "phase_lane": "10A/10B",
        "command": "chaseos studio graph-index-contract --json",
        "module": "runtime.studio.graph_index_contract",
        "path": "runtime/studio/graph_index_contract.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only derived graph model with deterministic node and edge identities",
    },
    {
        "id": "node-inspector-contract",
        "label": "Studio node inspector contract",
        "phase_lane": "10A/10B",
        "command": "chaseos studio node-inspector-contract --path README.md --json",
        "module": "runtime.studio.node_inspector_contract",
        "path": "runtime/studio/node_inspector_contract.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only node detail, edge context, related nodes, and bounded source excerpt over the graph contract",
    },
    {
        "id": "node-inspector-shell-panel-contract",
        "label": "Studio node inspector shell-panel contract",
        "phase_lane": "10A/10B",
        "command": "chaseos studio node-inspector-shell-panel --json",
        "module": "runtime.studio.node_inspector_shell_panel",
        "path": "runtime/studio/node_inspector_shell_panel.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only shell-panel contract over selected node detail and graph context",
    },
    {
        "id": "node-inspector-shell-panel-mount",
        "label": "Studio node inspector shell-panel mount",
        "phase_lane": "10A/10B",
        "command": "chaseos studio desktop-shell-app --dry-run --json",
        "module": "runtime.studio.desktop_shell_app",
        "path": "06_AGENTS/ChaseOS-Studio-Node-Inspector-Shell-Panel-Mount.md",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only mounted selected-node detail panel inside the Studio MVP shell",
    },
    {
        "id": "graph-view-contract",
        "label": "Studio graph view contract",
        "phase_lane": "10A/10B",
        "command": "chaseos studio graph-view-contract --json",
        "module": "runtime.studio.graph_view_contract",
        "path": "runtime/studio/graph_view_contract.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only graph view payload, deterministic layout, filters, legend, and optional focus context over the derived graph model",
    },
    {
        "id": "graph-view-static-renderer",
        "label": "Studio graph view static renderer",
        "phase_lane": "10A/10B",
        "command": "chaseos studio graph-view-static-render --json",
        "module": "runtime.studio.graph_view_static_renderer",
        "path": "runtime/studio/graph_view_static_renderer.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "local static HTML rendering proof over the read-only graph-view contract",
    },
    {
        "id": "graph-view-shell-panel-contract",
        "label": "Studio graph view shell-panel contract",
        "phase_lane": "10A/10B",
        "command": "chaseos studio graph-view-shell-panel --json",
        "module": "runtime.studio.graph_view_shell_panel",
        "path": "runtime/studio/graph_view_shell_panel.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only shell-panel contract over the verified static graph artifact",
    },
    {
        "id": "graph-view-shell-panel-mount",
        "label": "Studio graph view shell-panel mount",
        "phase_lane": "10A/10B",
        "command": "chaseos studio desktop-shell-app --dry-run --json",
        "module": "runtime.studio.desktop_shell_app",
        "path": "06_AGENTS/ChaseOS-Studio-Graph-View-Shell-Panel-Mount.md",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only mounted graph-view panel inside the Studio MVP shell",
    },
    {
        "id": "app-launcher",
        "label": "Studio App Launcher registry",
        "phase_lane": "10A/10D",
        "command": "chaseos studio app-launcher --dry-run --json",
        "module": "runtime.studio.app_launcher",
        "path": "runtime/studio/app_launcher.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only discovery registry for local Studio apps",
    },
    {
        "id": "dashboard",
        "label": "Studio Dashboard",
        "phase_lane": "10D",
        "command": "chaseos studio dashboard --json",
        "module": "runtime.studio.dashboard",
        "path": "runtime/studio/dashboard.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only system status aggregation surface",
    },
    {
        "id": "acquisition-cockpit",
        "label": "Acquisition Intake Cockpit",
        "phase_lane": "10A0",
        "command": "chaseos studio acquisition-cockpit --json",
        "module": "runtime.studio.acquisition_cockpit",
        "path": "runtime/studio/acquisition_cockpit.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "local governed acquisition workflow foothold",
    },
    {
        "id": "pulse-deck-app",
        "label": "Pulse Deck app",
        "phase_lane": "Pulse / 10D",
        "command": "chaseos studio pulse-deck-app --host 127.0.0.1 --port 8767",
        "module": "runtime.studio.pulse_deck_app",
        "path": "runtime/studio/pulse_deck_app.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "local Pulse deck UI proof with feedback-candidate-only writes",
    },
    {
        "id": "pulse-product-shell-panel-contract",
        "label": "Pulse product shell panel contract",
        "phase_lane": "Pulse / 10D",
        "command": "chaseos studio pulse-product-shell-panel --json",
        "module": "runtime.studio.pulse_product_shell_panel",
        "path": "runtime/studio/pulse_product_shell_panel.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only Studio panel contract over the browser-QA verified static Pulse product shell",
    },
    {
        "id": "pulse-product-shell-studio-mount",
        "label": "Pulse product shell Studio mount",
        "phase_lane": "Pulse / 10D",
        "command": "chaseos studio desktop-shell-app --dry-run --json",
        "module": "runtime.studio.desktop_shell_app",
        "path": "06_AGENTS/ChaseOS-Pulse-Studio-Product-Shell-Mount.md",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "read-only mounted Pulse product shell panel inside the Studio MVP shell",
    },
    {
        "id": "product-ui-test-app",
        "label": "Product UI test target",
        "phase_lane": "Browser Runtime / 10A",
        "command": "chaseos studio product-ui-test-app --host 127.0.0.1 --port 8770",
        "module": "runtime.studio.product_ui_test_app",
        "path": "runtime/studio/product_ui_test_app.py",
        "status": "COMPLETE / VERIFIED TARGETED",
        "role": "localhost-only safe-mode synthetic product UI target for browser proofing",
    },
]

_PLANNED_GAPS = [
    {
        "id": "standalone-desktop-packaging",
        "phase_lane": "10A",
        "status": "PLANNED / NOT BUILT",
        "needed_for": "real desktop app process, installer, and OS-level shell lifecycle",
    },
    {
        "id": "start-new-open-folder-flow",
        "phase_lane": "10A",
        "status": "PARTIAL / READINESS CONTRACT BUILT / UI NOT BUILT",
        "needed_for": "operator-selected workspace entry, ChaseOS-native/general-markdown mode detection, and UI entry flow",
    },
    {
        "id": "file-scanner-markdown-parser",
        "phase_lane": "10A",
        "status": "PARTIAL / MARKDOWN SCAN CONTRACT BUILT / FULL PARSER NOT BUILT",
        "needed_for": "deterministic file inventory, frontmatter parsing, markdown link detection, and derived graph input",
    },
    {
        "id": "graph-index-foundation",
        "phase_lane": "10A/10B",
        "status": "PARTIAL / GRAPH INDEX CONTRACT BUILT / PERSISTED GRAPH ENGINE NOT BUILT",
        "needed_for": "rebuildable node and edge index over vault files",
    },
    {
        "id": "node-inspector-read-only",
        "phase_lane": "10A/10B",
        "status": "PARTIAL / NODE INSPECTOR CONTRACT BUILT / UI NOT BUILT",
        "needed_for": "first read-only node detail panel backed by derived graph identity",
    },
    {
        "id": "node-inspector-shell-panel-contract",
        "phase_lane": "10A/10B",
        "status": "PLANNED / GRAPH SHELL BROWSER QA REQUIRED FIRST / SHELL MOUNT NOT BUILT",
        "needed_for": "read-only selected-node detail panel backed by derived graph identity",
    },
    {
        "id": "node-inspector-shell-panel-mount",
        "phase_lane": "10A/10B",
        "status": "PLANNED / NODE INSPECTOR SHELL-PANEL CONTRACT REQUIRED FIRST / BROWSER QA NOT VERIFIED",
        "needed_for": "read-only selected-node detail panel beside or below the graph in Studio shell",
    },
    {
        "id": "node-inspector-shell-panel-browser-qa",
        "phase_lane": "10A/10B",
        "status": "PLANNED / SHELL MOUNT REQUIRED FIRST / BROWSER QA NOT VERIFIED",
        "needed_for": "live browser proof that the read-only node inspector renders inside Studio without edit or write authority",
    },
    {
        "id": "graph-view-read-only",
        "phase_lane": "10A/10B",
        "status": "PARTIAL / GRAPH VIEW CONTRACT BUILT / STATIC RENDERER BUILT / FULL UI NOT BUILT",
        "needed_for": "first read-only visual graph surface backed by derived graph identity",
    },
    {
        "id": "graph-view-static-browser-qa",
        "phase_lane": "10A/10B",
        "status": "PLANNED / STATIC RENDERER BUILT / BROWSER QA NOT VERIFIED",
        "needed_for": "in-app/browser visual QA before mounting the graph renderer inside the Studio shell",
    },
    {
        "id": "graph-view-shell-panel-contract",
        "phase_lane": "10A/10B",
        "status": "PLANNED / BROWSER QA REQUIRED FIRST / SHELL MOUNT NOT BUILT",
        "needed_for": "read-only graph renderer mount contract inside the Studio shell without graph persistence or edit authority",
    },
    {
        "id": "graph-view-shell-panel-mount",
        "phase_lane": "10A/10B",
        "status": "PLANNED / SHELL-PANEL CONTRACT REQUIRED FIRST / BROWSER QA NOT VERIFIED",
        "needed_for": "read-only graph artifact mount inside Studio shell before browser QA",
    },
    {
        "id": "graph-view-shell-panel-browser-qa",
        "phase_lane": "10A/10B",
        "status": "PLANNED / SHELL MOUNT REQUIRED FIRST / BROWSER QA NOT VERIFIED",
        "needed_for": "live browser proof that the read-only graph panel renders inside the Studio shell without script or write authority",
    },
    {
        "id": "approval-center-ui",
        "phase_lane": "10D",
        "status": "PLANNED / NOT BUILT",
        "needed_for": "unified approval queue over OSRIL, startup controls, Gate requests, and runtime resumes",
    },
    {
        "id": "pulse-product-shell-browser-qa",
        "phase_lane": "Pulse / 10D",
        "status": "PLANNED / PRODUCT SHELL BUILT / BROWSER QA NOT VERIFIED",
        "needed_for": "targeted browser verification before Studio mounts the integrated Pulse product shell",
    },
    {
        "id": "pulse-product-shell-panel-contract",
        "phase_lane": "Pulse / 10D",
        "status": "PLANNED / BROWSER QA REQUIRED FIRST / SHELL MOUNT NOT BUILT",
        "needed_for": "read-only Studio panel contract for the integrated Pulse product shell",
    },
    {
        "id": "pulse-product-shell-studio-mount",
        "phase_lane": "Pulse / 10D",
        "status": "PLANNED / PANEL CONTRACT BUILT / SHELL MOUNT NOT BUILT",
        "needed_for": "first read-only Pulse product-shell panel inside the local Studio MVP shell",
    },
    {
        "id": "governed-settings-ui",
        "phase_lane": "10F",
        "status": "PLANNED / NOT BUILT",
        "needed_for": "provider/config/startup preferences with no credential display and service-layer routing",
    },
    {
        "id": "approval-driven-host-mutation-executor",
        "phase_lane": "10D",
        "status": "PLANNED / NOT BUILT",
        "needed_for": "UI-triggered runtime startup mutation after approval consumption and exact-once marker checks",
    },
]

_IMPLEMENTATION_SEQUENCE = [
    {
        "pass_id": "phase10-studio-desktop-shell-foundation-plan",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "read-only CLI/model contract for the real shell foundation",
        "must_not": "claim full shell built",
    },
    {
        "pass_id": "phase10-studio-open-folder-readiness-contract",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "workspace open/readiness contract with ChaseOS-native vs general-markdown mode detection",
        "must_not": "mutate opened folders",
    },
    {
        "pass_id": "phase10-studio-markdown-scan-contract",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "bounded scanner model for markdown files, frontmatter, wikilinks, and block candidates",
        "must_not": "write node IDs into files yet",
    },
    {
        "pass_id": "phase10-studio-graph-index-contract",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "derived graph index contract with deterministic node/edge identity",
        "must_not": "create an unrebuildable hidden source of truth",
    },
    {
        "pass_id": "phase10-studio-node-inspector-readonly",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "first read-only node inspector over the derived model",
        "must_not": "enable edits before service-layer write governance is proven",
    },
    {
        "pass_id": "phase10-studio-graph-view-readonly-contract",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "read-only graph-view payload, deterministic layout, filters, legend, and optional focus context over the derived graph model",
        "must_not": "claim persisted graph engine or write authority",
    },
    {
        "pass_id": "phase10-studio-graph-view-local-static-render",
        "status": "IMPLEMENTED / VERIFIED TARGETED",
        "output": "first static/local graph rendering proof over the graph-view contract",
        "must_not": "claim persisted graph engine, node editing, or service-layer write authority",
    },
    {
        "pass_id": "phase10-studio-graph-view-static-render-browser-qa",
        "status": "NEXT RECOMMENDED",
        "output": "browser/in-app visual QA over the generated static graph artifact",
        "must_not": "claim mounted graph UI, persisted graph engine, node editing, or service-layer write authority",
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel_exists(vault: Path, rel_path: str) -> bool:
    return (vault / rel_path).exists()


def _workspace_detection(vault: Path) -> dict[str, Any]:
    present_dirs = [path for path in _CHASEOS_DIRS if _rel_exists(vault, path)]
    missing_dirs = [path for path in _CHASEOS_DIRS if path not in present_dirs]
    present_files = [path for path in _CHASEOS_FILES if _rel_exists(vault, path)]
    missing_files = [path for path in _CHASEOS_FILES if path not in present_files]
    if not missing_dirs and not missing_files:
        mode = "chaseos_native_detected"
    elif any((vault / path).exists() for path in ("README.md", ".obsidian")):
        mode = "partial_or_general_markdown"
    else:
        mode = "unknown_or_empty"
    return {
        "mode": mode,
        "required_dir_count": len(_CHASEOS_DIRS),
        "present_dir_count": len(present_dirs),
        "missing_dirs": missing_dirs,
        "required_file_count": len(_CHASEOS_FILES),
        "present_file_count": len(present_files),
        "missing_files": missing_files,
        "detection_is_read_only": True,
    }


def _footholds(vault: Path) -> list[dict[str, Any]]:
    footholds = []
    for item in _FOOTHOLDS:
        present = _rel_exists(vault, item["path"])
        foothold = dict(item)
        foothold["present"] = present
        foothold["local_truth_status"] = item["status"] if present else "MISSING IN THIS WORKSPACE"
        footholds.append(foothold)
    return footholds


def _node_inspector_shell_panel_contract_built(vault: Path) -> bool:
    return _rel_exists(vault, "runtime/studio/node_inspector_shell_panel.py")


def _node_inspector_shell_panel_mount_built(vault: Path) -> bool:
    shell_app = vault / "runtime" / "studio" / "desktop_shell_app.py"
    if not shell_app.exists():
        return False
    try:
        text = shell_app.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return all(
        marker in text
        for marker in (
            "build_node_inspector_shell_panel_contract",
            "/node-inspector-shell-panel.json",
            "node-inspector-panel-mount",
        )
    )


def _node_inspector_shell_panel_browser_qa_evidence_built(vault: Path) -> bool:
    evidence_root = vault / "07_LOGS" / "Studio-Graph-Views"
    return (
        any(evidence_root.glob("*node-inspector-shell-panel-browser-qa.md"))
        and any(evidence_root.glob("*node-inspector-shell-panel-browser-qa.png"))
        if evidence_root.exists()
        else False
    )


def _planned_gaps(vault: Path) -> list[dict[str, Any]]:
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(vault)
    shell_panel_contract_built = graph_view_shell_panel_contract_built(vault)
    shell_panel_mount_built = graph_view_shell_panel_mount_built(vault)
    shell_panel_browser_qa_built = graph_view_shell_panel_browser_qa_evidence_built(vault)
    node_shell_panel_contract_built = _node_inspector_shell_panel_contract_built(vault)
    node_shell_panel_mount_built = _node_inspector_shell_panel_mount_built(vault)
    node_shell_panel_browser_qa_built = _node_inspector_shell_panel_browser_qa_evidence_built(vault)
    pulse_shell_browser_qa_built = pulse_product_shell_browser_qa_evidence_built(vault)
    pulse_shell_panel_contract_built = pulse_product_shell_panel_contract_built(vault)
    pulse_shell_mount_built = pulse_product_shell_studio_mount_built(vault)
    gaps = [dict(item) for item in _PLANNED_GAPS]
    if static_graph_browser_qa_built:
        for item in gaps:
            if item["id"] == "graph-view-static-browser-qa":
                item["status"] = "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
                item["needed_for"] = "browser evidence is now available before the graph renderer is mounted inside the Studio shell"
            if item["id"] == "graph-view-shell-panel-contract":
                item["status"] = "PLANNED / BROWSER QA VERIFIED / SHELL MOUNT NOT BUILT"
            if item["id"] == "graph-view-shell-panel-mount":
                item["status"] = "PLANNED / BROWSER QA VERIFIED / SHELL-PANEL CONTRACT REQUIRED"
    if shell_panel_contract_built:
        for item in gaps:
            if item["id"] == "graph-view-shell-panel-contract":
                item["status"] = "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
                item["needed_for"] = "shell-panel contract is available before the graph renderer is mounted inside the Studio shell"
            if item["id"] == "graph-view-shell-panel-mount":
                item["status"] = "PLANNED / PANEL CONTRACT VERIFIED / SHELL MOUNT NOT BUILT"
                item["needed_for"] = "mount the read-only graph artifact inside Studio shell before browser QA"
    if shell_panel_mount_built:
        for item in gaps:
            if item["id"] == "graph-view-static-browser-qa":
                item["status"] = "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
                item["needed_for"] = "static graph browser evidence exists and the read-only shell mount is now built"
            if item["id"] == "graph-view-shell-panel-contract":
                item["status"] = "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
                item["needed_for"] = "graph shell-panel contract is mounted read-only inside the Studio MVP shell"
            if item["id"] == "graph-view-shell-panel-mount":
                item["status"] = "COMPLETE / VERIFIED TARGETED / BROWSER QA NOT VERIFIED"
                item["needed_for"] = "browser/visual QA remains separate; this mount is read-only"
            if item["id"] == "graph-view-shell-panel-browser-qa":
                item["status"] = "NEXT RECOMMENDED / READ-ONLY SHELL MOUNT BUILT / BROWSER QA NOT VERIFIED"
                item["needed_for"] = "verify the mounted graph panel in the live Studio shell before graph/node productization"
    if shell_panel_browser_qa_built:
        for item in gaps:
            if item["id"] == "graph-view-shell-panel-mount":
                item["status"] = "COMPLETE / VERIFIED TARGETED / BROWSER QA VERIFIED"
                item["needed_for"] = "read-only graph mount has live browser evidence"
            if item["id"] == "graph-view-shell-panel-browser-qa":
                item["status"] = (
                    "COMPLETE / VERIFIED TARGETED / NODE INSPECTOR PANEL CONTRACT BUILT"
                    if node_shell_panel_contract_built
                    else "COMPLETE / VERIFIED TARGETED / NEXT NODE INSPECTOR PANEL CONTRACT"
                )
                item["needed_for"] = "browser evidence is durable; graph/node productization can continue"
            if item["id"] == "node-inspector-shell-panel-contract":
                item["status"] = (
                    "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
                    if node_shell_panel_mount_built
                    else "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
                    if node_shell_panel_contract_built
                    else "NEXT RECOMMENDED / GRAPH SHELL BROWSER QA VERIFIED / SHELL MOUNT NOT BUILT"
                )
                item["needed_for"] = "first read-only selected-node detail panel backed by derived graph identity"
            if item["id"] == "node-inspector-shell-panel-mount":
                item["status"] = (
                    "COMPLETE / VERIFIED TARGETED / BROWSER QA NOT VERIFIED"
                    if node_shell_panel_mount_built
                    else "NEXT RECOMMENDED / NODE INSPECTOR SHELL-PANEL CONTRACT BUILT / BROWSER QA NOT VERIFIED"
                    if node_shell_panel_contract_built
                    else item["status"]
                )
                item["needed_for"] = "browser/visual QA remains separate; this mount is read-only"
            if item["id"] == "node-inspector-shell-panel-browser-qa" and node_shell_panel_mount_built:
                item["status"] = "NEXT RECOMMENDED / READ-ONLY SHELL MOUNT BUILT / BROWSER QA NOT VERIFIED"
                item["needed_for"] = "verify selected-node details render live beside or below the graph with no edit authority"
    if node_shell_panel_browser_qa_built:
        for item in gaps:
            if item["id"] == "node-inspector-shell-panel-mount":
                item["status"] = "COMPLETE / VERIFIED TARGETED / BROWSER QA VERIFIED"
                item["needed_for"] = "read-only node inspector mount has live browser evidence"
            if item["id"] == "node-inspector-shell-panel-browser-qa":
                item["status"] = "COMPLETE / VERIFIED TARGETED / NEXT OPEN FOLDER WORKSPACE ENTRY"
                item["needed_for"] = "browser evidence is durable; Open Folder workspace entry can continue"
    if pulse_shell_browser_qa_built:
        for item in gaps:
            if item["id"] == "pulse-product-shell-browser-qa":
                item["status"] = "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
                item["needed_for"] = "browser evidence is now available before the Pulse product shell is mounted inside Studio"
            if item["id"] == "pulse-product-shell-panel-contract":
                item["status"] = "PLANNED / BROWSER QA VERIFIED / SHELL MOUNT NOT BUILT"
    if pulse_shell_panel_contract_built:
        for item in gaps:
            if item["id"] == "pulse-product-shell-panel-contract":
                item["status"] = "COMPLETE / VERIFIED TARGETED / SHELL MOUNT NOT BUILT"
                item["needed_for"] = "Pulse product-shell panel contract is available before actual Studio mounting"
            if item["id"] == "pulse-product-shell-studio-mount":
                item["status"] = "PLANNED / PANEL CONTRACT VERIFIED / SHELL MOUNT NOT BUILT"
    if pulse_shell_mount_built:
        for item in gaps:
            if item["id"] == "pulse-product-shell-panel-contract":
                item["status"] = "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
                item["needed_for"] = "Pulse product-shell panel contract is now mounted read-only inside the Studio MVP shell"
            if item["id"] == "pulse-product-shell-studio-mount":
                item["status"] = "COMPLETE / VERIFIED TARGETED / READ-ONLY SHELL MOUNT BUILT"
                item["needed_for"] = "interactive governed controls remain separate; this mount is read-only"
    return gaps


def _implementation_sequence(vault: Path) -> list[dict[str, Any]]:
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(vault)
    shell_panel_contract_built = graph_view_shell_panel_contract_built(vault)
    shell_panel_mount_built = graph_view_shell_panel_mount_built(vault)
    shell_panel_browser_qa_built = graph_view_shell_panel_browser_qa_evidence_built(vault)
    node_shell_panel_contract_built = _node_inspector_shell_panel_contract_built(vault)
    node_shell_panel_mount_built = _node_inspector_shell_panel_mount_built(vault)
    node_shell_panel_browser_qa_built = _node_inspector_shell_panel_browser_qa_evidence_built(vault)
    pulse_shell_browser_qa_built = pulse_product_shell_browser_qa_evidence_built(vault)
    pulse_shell_panel_contract_built = pulse_product_shell_panel_contract_built(vault)
    pulse_shell_mount_built = pulse_product_shell_studio_mount_built(vault)
    sequence = [dict(item) for item in _IMPLEMENTATION_SEQUENCE]
    if static_graph_browser_qa_built:
        for item in sequence:
            if item["pass_id"] == STATIC_GRAPH_BROWSER_QA_PASS:
                item["status"] = "IMPLEMENTED / VERIFIED TARGETED"
                item["output"] = "in-app browser QA evidence over the generated static graph artifact"
        sequence.append(
            {
                "pass_id": "phase10-studio-graph-view-shell-panel-contract",
                "status": "NEXT RECOMMENDED" if not shell_panel_contract_built else "IMPLEMENTED / VERIFIED TARGETED",
                "output": "read-only graph renderer panel/mount contract inside the Studio shell",
                "must_not": "claim persisted graph engine, graph editing, or service-layer write authority",
            }
        )
    if shell_panel_contract_built:
        sequence.append(
            {
                "pass_id": NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_CONTRACT,
                "status": "NEXT RECOMMENDED" if not shell_panel_mount_built else "IMPLEMENTED / VERIFIED TARGETED",
                "output": "mount the read-only graph panel in the Studio shell without adding graph write authority",
                "must_not": "claim interactive graph controls, persisted graph engine, node editing, or service-layer write authority",
            }
        )
    if shell_panel_mount_built:
        sequence.append(
            {
                "pass_id": NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_MOUNT,
                "status": (
                    "IMPLEMENTED / VERIFIED TARGETED"
                    if shell_panel_browser_qa_built
                    else "NEXT RECOMMENDED"
                ),
                "output": "browser/visual QA over the read-only graph panel mounted inside the Studio shell",
                "must_not": "claim interactive graph controls, persisted graph engine, node editing, or service-layer write authority",
            }
        )
    if shell_panel_browser_qa_built:
        sequence.append(
            {
                "pass_id": NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA,
                "status": "IMPLEMENTED / VERIFIED TARGETED" if node_shell_panel_contract_built else "NEXT RECOMMENDED",
                "output": "add a read-only node detail shell-panel contract beside or under the graph",
                "must_not": "write node IDs, edit source files, persist graph state, or add service-layer write authority",
            }
        )
    if node_shell_panel_contract_built:
        sequence.append(
            {
                "pass_id": NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_CONTRACT,
                "status": "IMPLEMENTED / VERIFIED TARGETED" if node_shell_panel_mount_built else "NEXT RECOMMENDED",
                "output": "mount the read-only selected-node detail panel inside the Studio shell",
                "must_not": "write node IDs, edit source files, persist graph state, or add service-layer write authority",
            }
        )
    if node_shell_panel_mount_built:
        sequence.append(
            {
                "pass_id": NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_MOUNT,
                "status": "IMPLEMENTED / VERIFIED TARGETED" if node_shell_panel_browser_qa_built else "NEXT RECOMMENDED",
                "output": "browser/visual QA over the read-only node inspector panel mounted inside the Studio shell",
                "must_not": "write node IDs, edit source files, persist graph state, run providers/connectors, or add canonical mutation",
            }
        )
    sequence.append(
        {
            "pass_id": PULSE_PRODUCT_SHELL_BROWSER_QA_PASS,
            "status": "IMPLEMENTED / VERIFIED TARGETED" if pulse_shell_browser_qa_built else "NEXT RECOMMENDED",
            "output": "in-app browser QA evidence over the integrated static Pulse product shell",
            "must_not": "claim Studio shell mount, feedback execution, approval execution, candidate apply, schedule activation, or canonical writeback",
        }
    )
    if pulse_shell_browser_qa_built:
        sequence.append(
            {
                "pass_id": "chaseos-pulse-product-shell-studio-panel-contract",
                "status": "IMPLEMENTED / VERIFIED TARGETED" if pulse_shell_panel_contract_built else "NEXT RECOMMENDED",
                "output": "read-only Studio panel contract over the verified static Pulse product shell",
                "must_not": "claim Studio shell mount, feedback execution, approval execution, or canonical writeback",
            }
        )
    if pulse_shell_panel_contract_built:
        sequence.append(
            {
                "pass_id": "chaseos-pulse-studio-product-shell-mount",
                "status": "IMPLEMENTED / VERIFIED TARGETED" if pulse_shell_mount_built else "NEXT RECOMMENDED",
                "output": "mount the read-only Pulse product-shell panel in the Studio shell",
                "must_not": "add direct approval execution, candidate apply, schedule activation, provider calls, or canonical writeback",
            }
        )
    if pulse_shell_mount_built:
        sequence.append(
            {
                "pass_id": "chaseos-pulse-interactive-governed-controls",
                "status": "NEXT RECOMMENDED",
                "output": "add visible controls that only create governed review candidates, without executing approvals or applying candidates",
                "must_not": "submit real approvals, mutate Personal Map/runtime memory, dispatch runtimes, activate schedules, or write canonical truth",
            }
        )
    return sequence


def build_studio_desktop_shell_foundation(vault_root: str | Path) -> dict[str, Any]:
    """Return the read-only Phase 10A Studio shell foundation contract."""

    vault = Path(vault_root).resolve()
    footholds = _footholds(vault)
    present_footholds = [item for item in footholds if item["present"]]
    workspace = _workspace_detection(vault)
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(vault)
    shell_panel_contract_built = graph_view_shell_panel_contract_built(vault)
    shell_panel_mount_built = graph_view_shell_panel_mount_built(vault)
    shell_panel_browser_qa_built = graph_view_shell_panel_browser_qa_evidence_built(vault)
    node_shell_panel_contract_built = _node_inspector_shell_panel_contract_built(vault)
    node_shell_panel_mount_built = _node_inspector_shell_panel_mount_built(vault)
    node_shell_panel_browser_qa_built = _node_inspector_shell_panel_browser_qa_evidence_built(vault)
    pulse_shell_browser_qa_built = pulse_product_shell_browser_qa_evidence_built(vault)
    pulse_shell_panel_contract_built = pulse_product_shell_panel_contract_built(vault)
    pulse_shell_mount_built = pulse_product_shell_studio_mount_built(vault)
    planned_gaps = _planned_gaps(vault)
    implementation_sequence = _implementation_sequence(vault)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Desktop Shell Foundation",
        "phase": "Phase 10A - Studio Core Shell",
        "status": "PARTIAL / FOUNDATION CONTRACT BUILT / FULL DESKTOP SHELL NOT BUILT",
        "vault_root": str(vault),
        "workspace": workspace,
        "shell_truth": {
            "full_standalone_desktop_shell_built": False,
            "read_only_studio_shell_mvp_built": any(item["id"] == "desktop-shell-app" and item["present"] for item in footholds),
            "foundation_contract_built": True,
            "start_new_open_folder_built": False,
            "open_folder_readiness_contract_built": _rel_exists(vault, "runtime/studio/open_folder_readiness.py"),
            "markdown_scan_contract_built": _rel_exists(vault, "runtime/studio/markdown_scan_contract.py"),
            "graph_index_contract_built": _rel_exists(vault, "runtime/studio/graph_index_contract.py"),
            "node_inspector_contract_built": _rel_exists(vault, "runtime/studio/node_inspector_contract.py"),
            "node_inspector_shell_panel_contract_built": node_shell_panel_contract_built,
            "node_inspector_shell_panel_mounted": node_shell_panel_mount_built,
            "node_inspector_shell_panel_browser_qa_built": node_shell_panel_browser_qa_built,
            "graph_view_contract_built": _rel_exists(vault, "runtime/studio/graph_view_contract.py"),
            "graph_view_static_renderer_built": _rel_exists(vault, "runtime/studio/graph_view_static_renderer.py"),
            "graph_view_static_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_shell_panel_contract_built": shell_panel_contract_built,
            "graph_view_shell_panel_mounted": shell_panel_mount_built,
            "graph_view_shell_panel_browser_qa_built": shell_panel_browser_qa_built,
            "pulse_product_shell_browser_qa_built": pulse_shell_browser_qa_built,
            "pulse_product_shell_panel_contract_built": pulse_shell_panel_contract_built,
            "pulse_product_shell_mounted": pulse_shell_mount_built,
            "file_scanner_markdown_parser_built": False,
            "graph_engine_foundation_built": False,
            "node_inspector_built": False,
            "graph_view_built": False,
            "approval_center_ui_built": False,
            "settings_ui_built": False,
        },
        "footholds": footholds,
        "readiness": {
            "contract_ready": True,
            "current_foothold_count": len(footholds),
            "present_foothold_count": len(present_footholds),
            "missing_foothold_ids": [item["id"] for item in footholds if not item["present"]],
            "planned_gap_count": len(planned_gaps),
            "next_recommended_pass": (
                NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_MOUNT
                if shell_panel_browser_qa_built and node_shell_panel_mount_built and not node_shell_panel_browser_qa_built
                else NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_CONTRACT
                if shell_panel_browser_qa_built and node_shell_panel_contract_built and not node_shell_panel_mount_built
                else NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA
                if shell_panel_browser_qa_built
                else
                next_graph_view_pass_after_browser_qa(vault)
                if static_graph_browser_qa_built
                else STATIC_GRAPH_BROWSER_QA_PASS
            ),
        },
        "planned_gaps": planned_gaps,
        "implementation_sequence": implementation_sequence,
        "authority": {
            "read_only": True,
            "starts_servers": False,
            "starts_child_apps": False,
            "writes_vault": False,
            "writes_host_startup": False,
            "writes_settings": False,
            "approval_consumption_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-foundation-contract"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "06_AGENTS/Runtime-Startup-Controls-Portable-Handoff.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-node-inspector-readonly.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-graph-view-readonly-contract.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-graph-view-local-static-render.md",
        ],
    }
