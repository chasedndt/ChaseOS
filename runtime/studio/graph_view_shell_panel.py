"""Read-only Studio graph-view shell-panel contract.

This module describes how the verified static graph renderer can be mounted by
the Studio shell as a read-only panel. It does not start a server, mount a UI,
write settings, mutate opened folders, persist graph state, execute workflows,
call providers/connectors, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_browser_qa import (
    NEXT_GRAPH_VIEW_PASS_AFTER_BROWSER_QA,
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_CONTRACT,
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA,
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_MOUNT,
    STATIC_RENDER_ROOT,
    graph_view_shell_panel_browser_qa_evidence_built,
    graph_view_shell_panel_mount_built,
    latest_graph_view_shell_panel_browser_qa_note,
    latest_graph_view_shell_panel_browser_qa_screenshot,
    latest_static_graph_artifact,
    latest_static_graph_browser_qa_note,
    latest_static_graph_browser_qa_screenshot,
    static_graph_browser_qa_evidence_built,
)
from runtime.studio.graph_view_static_renderer import build_graph_view_static_render_model


MODEL_VERSION = "studio.graph_view_shell_panel.v1"
SURFACE_ID = "studio_graph_view_shell_panel_contract"
PANEL_ID = "studio.graph_view.shell_panel"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _file_uri(path: Path | None) -> str | None:
    return path.resolve().as_uri() if path is not None else None


def _static_render_command(
    *,
    focus_node_id: str | None,
    focus_path: str | Path | None,
    folder_path: str | Path | None,
    max_files: int | None,
    max_bytes_per_file: int | None,
    max_nodes: int | None,
    max_edges: int | None,
    layout_node_limit: int | None,
    content_excerpt_bytes: int | None,
) -> str:
    parts = ["chaseos", "studio", "graph-view-static-render"]
    if focus_node_id:
        parts.extend(["--focus-node-id", str(focus_node_id)])
    if focus_path is not None:
        parts.extend(["--focus-path", str(focus_path)])
    if folder_path is not None:
        parts.extend(["--folder", str(folder_path)])
    for flag, value in [
        ("--max-files", max_files),
        ("--max-bytes-per-file", max_bytes_per_file),
        ("--max-nodes", max_nodes),
        ("--max-edges", max_edges),
        ("--layout-node-limit", layout_node_limit),
        ("--content-excerpt-bytes", content_excerpt_bytes),
    ]:
        if value is not None:
            parts.extend([flag, str(value)])
    parts.extend(["--write", "--json"])
    return " ".join(parts)


def build_graph_view_shell_panel_contract(
    vault_root: str | Path,
    *,
    focus_node_id: str | None = None,
    focus_path: str | Path | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    layout_node_limit: int | None = None,
    content_excerpt_bytes: int | None = None,
) -> dict[str, Any]:
    """Return the read-only graph shell-panel contract."""

    vault = _vault_path(vault_root)
    static_model = build_graph_view_static_render_model(
        vault,
        focus_node_id=focus_node_id,
        focus_path=focus_path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        layout_node_limit=layout_node_limit,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    static_readiness = static_model.get("readiness") or {}
    static_summary = static_model.get("summary") or {}
    artifact_path = latest_static_graph_artifact(vault)
    qa_note_path = latest_static_graph_browser_qa_note(vault)
    screenshot_path = latest_static_graph_browser_qa_screenshot(vault)
    browser_qa_ready = static_graph_browser_qa_evidence_built(vault)
    shell_mount_ready = graph_view_shell_panel_mount_built(vault)
    shell_browser_qa_note_path = latest_graph_view_shell_panel_browser_qa_note(vault)
    shell_browser_qa_screenshot_path = latest_graph_view_shell_panel_browser_qa_screenshot(vault)
    shell_browser_qa_ready = graph_view_shell_panel_browser_qa_evidence_built(vault)

    blockers = list(static_readiness.get("blockers") or [])
    warnings = list(static_readiness.get("warnings") or [])
    if not static_model.get("ok"):
        blockers.append("static-render-source-contract-not-ready")
    if artifact_path is None:
        blockers.append("static-graph-artifact-not-found")
    if not browser_qa_ready:
        blockers.append("static-browser-qa-evidence-not-found")
    if screenshot_path is None:
        warnings.append("static-browser-qa-screenshot-not-found")

    panel_ready = bool(static_model.get("ok")) and artifact_path is not None and browser_qa_ready
    if shell_browser_qa_ready:
        next_pass = NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA
    elif shell_mount_ready:
        next_pass = NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_MOUNT
    elif panel_ready:
        next_pass = NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_CONTRACT
    else:
        next_pass = NEXT_GRAPH_VIEW_PASS_AFTER_BROWSER_QA
    command = _static_render_command(
        focus_node_id=focus_node_id,
        focus_path=focus_path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        layout_node_limit=layout_node_limit,
        content_excerpt_bytes=content_excerpt_bytes,
    )

    return {
        "ok": panel_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Graph View Shell Panel Contract",
        "phase": "Phase 10A/10B - Studio Core Shell / Graph + Node Model",
        "status": (
            "COMPLETE TARGETED / GRAPH SHELL PANEL BROWSER QA VERIFIED / READ-ONLY STUDIO MOUNT BUILT"
            if shell_browser_qa_ready
            else "PARTIAL / GRAPH SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT / BROWSER QA NOT VERIFIED"
            if shell_mount_ready
            else "PARTIAL / GRAPH SHELL PANEL CONTRACT BUILT / SHELL MOUNT NOT BUILT"
            if panel_ready
            else "BLOCKED / GRAPH SHELL PANEL CONTRACT BUILT / STATIC GRAPH EVIDENCE INCOMPLETE"
        ),
        "vault_root": str(vault),
        "panel": {
            "panel_id": PANEL_ID,
            "label": "Graph View",
            "surface_route": "#graph-view",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-static-graph-artifact-panel",
            "embedding_strategy": "local-file-iframe-or-webview",
            "source_artifact_path": _relative_to_vault(vault, artifact_path),
            "source_artifact_uri": _file_uri(artifact_path),
            "source_artifact_exists": artifact_path is not None,
            "browser_qa_evidence_path": _relative_to_vault(vault, qa_note_path),
            "browser_qa_screenshot_path": _relative_to_vault(vault, screenshot_path),
            "shell_panel_browser_qa_evidence_path": _relative_to_vault(vault, shell_browser_qa_note_path),
            "shell_panel_browser_qa_screenshot_path": _relative_to_vault(
                vault,
                shell_browser_qa_screenshot_path,
            ),
            "required_artifact_root": STATIC_RENDER_ROOT.as_posix(),
            "artifact_refresh_command": command,
            "artifact_refresh_requires_explicit_operator_action": True,
        },
        "summary": {
            "static_graph_status": static_model.get("status"),
            "visible_node_count": static_summary.get("visible_node_count", 0),
            "visible_edge_count": static_summary.get("visible_edge_count", 0),
            "source_node_count": static_summary.get("source_node_count", 0),
            "source_edge_count": static_summary.get("source_edge_count", 0),
            "layout_algorithm": static_summary.get("layout_algorithm"),
            "focus_requested": static_summary.get("focus_requested", False),
            "focus_ok": static_summary.get("focus_ok", True),
            "warning_count": len(warnings),
            "blocker_count": len(blockers),
        },
        "source_static_renderer": {
            "surface": static_model.get("surface"),
            "model_version": static_model.get("model_version"),
            "ok": static_model.get("ok"),
            "readiness": static_readiness,
            "artifact": static_model.get("artifact"),
        },
        "readiness": {
            "graph_view_shell_panel_contract_ready": panel_ready,
            "static_graph_renderer_ready": bool(static_readiness.get("static_graph_renderer_ready")),
            "graph_view_contract_ready": bool(static_readiness.get("graph_view_contract_ready")),
            "deterministic_layout_ready": bool(static_readiness.get("deterministic_layout_ready")),
            "static_graph_artifact_ready": artifact_path is not None,
            "static_graph_browser_qa_ready": browser_qa_ready,
            "desktop_shell_mount_ready": shell_mount_ready,
            "graph_view_shell_panel_browser_qa_ready": shell_browser_qa_ready,
            "interactive_graph_controls_ready": False,
            "persisted_graph_index_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "graph_view_truth": {
            "markdown_scan_contract_built": True,
            "graph_index_contract_built": True,
            "node_inspector_contract_built": True,
            "graph_view_contract_built": True,
            "deterministic_layout_contract_built": True,
            "static_graph_renderer_built": True,
            "static_graph_browser_qa_built": browser_qa_ready,
            "graph_view_shell_panel_contract_built": True,
            "graph_view_shell_panel_mounted": shell_mount_ready,
            "graph_view_shell_panel_browser_qa_built": shell_browser_qa_ready,
            "interactive_graph_controls_built": False,
            "persistent_graph_snapshot_built": False,
            "node_id_writer_built": False,
            "node_editing_built": False,
            "service_layer_write_path_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "requires_existing_static_artifact": True,
            "mounts_existing_artifact_only": True,
            "starts_servers": False,
            "starts_child_apps": False,
            "writes_html": False,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "writes_snapshot": False,
            "node_editing_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-graph-view-shell-panel-contract"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-graph-view-static-render-browser-qa.md",
        ],
    }
