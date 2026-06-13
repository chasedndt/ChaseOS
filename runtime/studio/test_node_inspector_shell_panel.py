"""Tests for the read-only Studio node inspector shell-panel contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.graph_view_browser_qa import STATIC_RENDER_ROOT
from runtime.studio.node_inspector_shell_panel import (
    MODEL_VERSION,
    SURFACE_ID,
    build_node_inspector_shell_panel_contract,
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
                "Links to [[Beta]].",
                "#tag",
                "stable block ^alpha-block",
            ]
        ),
        encoding="utf-8",
    )
    (notes / "beta.md").write_text("# Beta\nBack to [[Alpha]].\n", encoding="utf-8")


def _seed_graph_shell_browser_qa(vault: Path) -> None:
    evidence_root = vault / STATIC_RENDER_ROOT
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03T09-39-25-844850Z-graph-view-static.html").write_text(
        "<!doctype html><title>ChaseOS Studio Graph View</title>",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "static browser qa evidence\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.png").write_bytes(b"png")
    (evidence_root / "2026-05-03-graph-view-shell-panel-browser-qa.md").write_text(
        "shell panel browser qa evidence\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-shell-panel-browser-qa.png").write_bytes(b"png")


def _seed_graph_shell_mount(vault: Path) -> None:
    mount_doc = vault / "06_AGENTS" / "ChaseOS-Studio-Graph-View-Shell-Panel-Mount.md"
    mount_doc.parent.mkdir(parents=True)
    mount_doc.write_text("mount doc\n", encoding="utf-8")
    shell_app = vault / "runtime" / "studio" / "desktop_shell_app.py"
    shell_app.parent.mkdir(parents=True)
    shell_app.write_text(
        "build_graph_view_shell_panel_contract\n/graph-view-shell-panel.json\ngraph-view-panel-mount\n",
        encoding="utf-8",
    )
    (vault / "runtime" / "studio" / "graph_view_shell_panel.py").write_text(
        "contract placeholder\n",
        encoding="utf-8",
    )


def _seed_node_shell_mount(vault: Path) -> None:
    shell_app = vault / "runtime" / "studio" / "desktop_shell_app.py"
    text = shell_app.read_text(encoding="utf-8")
    shell_app.write_text(
        text
        + "\nbuild_node_inspector_shell_panel_contract\n/node-inspector-shell-panel.json\nnode-inspector-panel-mount\n",
        encoding="utf-8",
    )


def test_node_inspector_shell_panel_contract_derives_default_node_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    _seed_graph_shell_browser_qa(vault)
    _seed_graph_shell_mount(vault)
    before = _snapshot(vault)

    model = build_node_inspector_shell_panel_contract(vault, folder_path="notes")

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["panel"]["panel_id"] == "studio.node_inspector.shell_panel"
    assert model["panel"]["surface_route"] == "#node-inspector"
    assert model["panel"]["selection_source"] == "derived-from-rebuildable-graph-contract"
    assert model["panel"]["selected_node_path"] == "alpha.md"
    assert model["summary"]["selected_node_found"] is True
    assert model["summary"]["outgoing_edge_count"] >= 1
    assert model["readiness"]["node_inspector_shell_panel_contract_ready"] is True
    assert model["readiness"]["graph_view_shell_panel_browser_qa_ready"] is True
    assert model["readiness"]["desktop_shell_mount_ready"] is False
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-shell-panel-mount"
    assert model["authority"]["read_only"] is True
    assert model["authority"]["uses_existing_derived_node_identity"] is True
    assert model["authority"]["writes_node_ids"] is False
    assert model["authority"]["node_editing_allowed"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_node_inspector_shell_panel_contract_reports_mount_ready(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    _seed_graph_shell_browser_qa(vault)
    _seed_graph_shell_mount(vault)
    _seed_node_shell_mount(vault)

    model = build_node_inspector_shell_panel_contract(vault, path="alpha.md", folder_path="notes")

    assert model["ok"] is True
    assert model["status"] == "COMPLETE TARGETED / NODE INSPECTOR SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT"
    assert model["panel"]["selector_type"] == "explicit-path"
    assert model["readiness"]["desktop_shell_mount_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-shell-panel-browser-qa"
    assert model["node_inspector_truth"]["node_inspector_shell_panel_mounted"] is True


def test_node_inspector_shell_panel_contract_blocks_without_graph_shell_browser_qa(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)

    model = build_node_inspector_shell_panel_contract(vault, folder_path="notes")

    assert model["ok"] is False
    assert "graph-shell-panel-browser-qa-required" in model["readiness"]["blockers"]
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-shell-panel-contract"
    assert model["authority"]["writes_graph_index"] is False

