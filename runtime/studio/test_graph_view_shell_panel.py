"""Tests for the read-only Studio graph-view shell-panel contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.graph_view_browser_qa import STATIC_RENDER_ROOT
from runtime.studio.graph_view_shell_panel import (
    MODEL_VERSION,
    SURFACE_ID,
    build_graph_view_shell_panel_contract,
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


def _seed_static_evidence(vault: Path) -> None:
    evidence_root = vault / STATIC_RENDER_ROOT
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03T09-39-25-844850Z-graph-view-static.html").write_text(
        "<!doctype html><title>ChaseOS Studio Graph View</title>",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.png").write_bytes(b"png")


def _seed_shell_browser_qa(vault: Path) -> None:
    evidence_root = vault / STATIC_RENDER_ROOT
    evidence_root.mkdir(parents=True, exist_ok=True)
    (evidence_root / "2026-05-03-graph-view-shell-panel-browser-qa.md").write_text(
        "shell panel browser qa evidence\n",
        encoding="utf-8",
    )
    (evidence_root / "2026-05-03-graph-view-shell-panel-browser-qa.png").write_bytes(b"png")


def test_shell_panel_contract_reports_mount_contract_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    _seed_static_evidence(vault)
    before = _snapshot(vault)

    model = build_graph_view_shell_panel_contract(vault, folder_path="notes", layout_node_limit=12)

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["panel"]["panel_id"] == "studio.graph_view.shell_panel"
    assert model["panel"]["mount_target"] == "desktop-shell-app:workspace-main-panel"
    assert model["panel"]["source_artifact_path"].endswith("graph-view-static.html")
    assert model["panel"]["browser_qa_evidence_path"].endswith("browser-qa.md")
    assert model["readiness"]["graph_view_shell_panel_contract_ready"] is True
    assert model["readiness"]["static_graph_artifact_ready"] is True
    assert model["readiness"]["static_graph_browser_qa_ready"] is True
    assert model["readiness"]["desktop_shell_mount_ready"] is False
    assert model["readiness"]["graph_view_shell_panel_browser_qa_ready"] is False
    assert model["readiness"]["interactive_graph_controls_ready"] is False
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-shell-panel-mount"
    assert model["graph_view_truth"]["graph_view_shell_panel_contract_built"] is True
    assert model["graph_view_truth"]["graph_view_shell_panel_mounted"] is False
    assert model["graph_view_truth"]["graph_view_shell_panel_browser_qa_built"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["writes_settings"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_shell_panel_contract_advances_after_shell_browser_qa_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    _seed_static_evidence(vault)
    _seed_shell_browser_qa(vault)
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

    model = build_graph_view_shell_panel_contract(vault, folder_path="notes", layout_node_limit=12)

    assert model["ok"] is True
    assert model["status"] == "COMPLETE TARGETED / GRAPH SHELL PANEL BROWSER QA VERIFIED / READ-ONLY STUDIO MOUNT BUILT"
    assert model["panel"]["shell_panel_browser_qa_evidence_path"].endswith("shell-panel-browser-qa.md")
    assert model["panel"]["shell_panel_browser_qa_screenshot_path"].endswith("shell-panel-browser-qa.png")
    assert model["readiness"]["desktop_shell_mount_ready"] is True
    assert model["readiness"]["graph_view_shell_panel_browser_qa_ready"] is True
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-node-inspector-shell-panel-contract"
    assert model["graph_view_truth"]["graph_view_shell_panel_mounted"] is True
    assert model["graph_view_truth"]["graph_view_shell_panel_browser_qa_built"] is True


def test_shell_panel_contract_blocks_without_browser_qa_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    evidence_root = vault / STATIC_RENDER_ROOT
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03T09-39-25-844850Z-graph-view-static.html").write_text(
        "<!doctype html><title>ChaseOS Studio Graph View</title>",
        encoding="utf-8",
    )
    before = _snapshot(vault)

    model = build_graph_view_shell_panel_contract(vault, folder_path="notes", layout_node_limit=12)

    assert _snapshot(vault) == before
    assert model["ok"] is False
    assert model["readiness"]["graph_view_shell_panel_contract_ready"] is False
    assert "static-browser-qa-evidence-not-found" in model["readiness"]["blockers"]
    assert model["readiness"]["next_recommended_pass"] == "phase10-studio-graph-view-shell-panel-contract"


def test_shell_panel_contract_blocks_without_static_artifact(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    evidence_root = vault / STATIC_RENDER_ROOT
    evidence_root.mkdir(parents=True)
    (evidence_root / "2026-05-03-graph-view-static-render-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )

    model = build_graph_view_shell_panel_contract(vault, folder_path="notes", layout_node_limit=12)

    assert model["ok"] is False
    assert model["panel"]["source_artifact_path"] is None
    assert "static-graph-artifact-not-found" in model["readiness"]["blockers"]
    assert model["authority"]["starts_servers"] is False


def test_shell_panel_contract_reports_source_contract_blockers(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_static_evidence(vault)

    model = build_graph_view_shell_panel_contract(vault, folder_path="missing")

    assert model["ok"] is False
    assert "target-folder-does-not-exist" in model["readiness"]["blockers"]
    assert "static-render-source-contract-not-ready" in model["readiness"]["blockers"]
    assert model["authority"]["writes_opened_folder"] is False
