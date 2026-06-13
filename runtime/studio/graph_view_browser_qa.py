"""Shared readiness helpers for Studio graph-view browser QA evidence."""

from __future__ import annotations

from pathlib import Path


STATIC_RENDER_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
STATIC_GRAPH_BROWSER_QA_PASS = "phase10-studio-graph-view-static-render-browser-qa"
NEXT_GRAPH_VIEW_PASS_AFTER_BROWSER_QA = "phase10-studio-graph-view-shell-panel-contract"
NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_CONTRACT = "phase10-studio-graph-view-shell-panel-mount"
NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_MOUNT = "phase10-studio-graph-view-shell-panel-browser-qa"
NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA = "phase10-studio-node-inspector-shell-panel-contract"
GRAPH_VIEW_SHELL_PANEL_CONTRACT_PATH = Path("runtime") / "studio" / "graph_view_shell_panel.py"
GRAPH_VIEW_SHELL_PANEL_MOUNT_DOC_PATH = (
    Path("06_AGENTS") / "ChaseOS-Studio-Graph-View-Shell-Panel-Mount.md"
)
SHELL_PANEL_BROWSER_QA_NOTE_NAME = "2026-05-03-graph-view-shell-panel-browser-qa.md"
SHELL_PANEL_BROWSER_QA_SCREENSHOT_NAME = "2026-05-03-graph-view-shell-panel-browser-qa.png"


def static_graph_browser_qa_evidence_built(vault_root: str | Path | None) -> bool:
    """Return true when a durable static graph browser-QA note exists."""

    if vault_root is None or str(vault_root) == "":
        return False
    evidence_root = Path(vault_root).resolve() / STATIC_RENDER_ROOT
    if not evidence_root.exists():
        return False
    return any(path.is_file() for path in evidence_root.glob("*browser-qa*.md"))


def latest_static_graph_artifact(vault_root: str | Path | None) -> Path | None:
    """Return the newest persisted static graph artifact, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    artifact_root = Path(vault_root).resolve() / STATIC_RENDER_ROOT
    if not artifact_root.exists():
        return None
    candidates = [path for path in artifact_root.glob("*graph-view-static.html") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def latest_static_graph_browser_qa_note(vault_root: str | Path | None) -> Path | None:
    """Return the newest static graph browser-QA note, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    evidence_root = Path(vault_root).resolve() / STATIC_RENDER_ROOT
    if not evidence_root.exists():
        return None
    candidates = [path for path in evidence_root.glob("*browser-qa*.md") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def latest_static_graph_browser_qa_screenshot(vault_root: str | Path | None) -> Path | None:
    """Return the newest static graph browser-QA screenshot, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    evidence_root = Path(vault_root).resolve() / STATIC_RENDER_ROOT
    if not evidence_root.exists():
        return None
    candidates = [path for path in evidence_root.glob("*browser-qa*.png") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def latest_graph_view_shell_panel_browser_qa_note(vault_root: str | Path | None) -> Path | None:
    """Return the newest shell-panel browser-QA note, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    evidence_root = Path(vault_root).resolve() / STATIC_RENDER_ROOT
    if not evidence_root.exists():
        return None
    candidates = [path for path in evidence_root.glob("*shell-panel-browser-qa*.md") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def latest_graph_view_shell_panel_browser_qa_screenshot(vault_root: str | Path | None) -> Path | None:
    """Return the newest shell-panel browser-QA screenshot, if one exists."""

    if vault_root is None or str(vault_root) == "":
        return None
    evidence_root = Path(vault_root).resolve() / STATIC_RENDER_ROOT
    if not evidence_root.exists():
        return None
    candidates = [path for path in evidence_root.glob("*shell-panel-browser-qa*.png") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def graph_view_shell_panel_browser_qa_evidence_built(vault_root: str | Path | None) -> bool:
    """Return true when shell-panel browser-QA evidence exists."""

    return latest_graph_view_shell_panel_browser_qa_note(vault_root) is not None


def graph_view_shell_panel_contract_built(vault_root: str | Path | None) -> bool:
    """Return true when the shell-panel contract module exists in this workspace."""

    if vault_root is None or str(vault_root) == "":
        return False
    return (Path(vault_root).resolve() / GRAPH_VIEW_SHELL_PANEL_CONTRACT_PATH).is_file()


def graph_view_shell_panel_mount_built(vault_root: str | Path | None) -> bool:
    """Return true when the graph-view panel is mounted in the Studio shell."""

    if vault_root is None or str(vault_root) == "":
        return False
    vault = Path(vault_root).resolve()
    shell_app = vault / "runtime" / "studio" / "desktop_shell_app.py"
    if not shell_app.is_file():
        return False
    try:
        shell_text = shell_app.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return (
        (vault / GRAPH_VIEW_SHELL_PANEL_CONTRACT_PATH).is_file()
        and (vault / GRAPH_VIEW_SHELL_PANEL_MOUNT_DOC_PATH).is_file()
        and latest_static_graph_artifact(vault) is not None
        and static_graph_browser_qa_evidence_built(vault)
        and "build_graph_view_shell_panel_contract" in shell_text
        and "/graph-view-shell-panel.json" in shell_text
        and "graph-view-panel-mount" in shell_text
    )


def next_graph_view_pass_after_browser_qa(vault_root: str | Path | None) -> str:
    """Return the next graph-view pass after browser QA for this workspace."""

    if graph_view_shell_panel_browser_qa_evidence_built(vault_root):
        return NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA
    if graph_view_shell_panel_mount_built(vault_root):
        return NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_MOUNT
    if graph_view_shell_panel_contract_built(vault_root):
        return NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_CONTRACT
    return NEXT_GRAPH_VIEW_PASS_AFTER_BROWSER_QA
