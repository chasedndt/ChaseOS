"""Read-only Studio node inspector shell-panel contract.

This module wraps the existing node inspector contract as a mountable Studio
shell panel. It derives a default selected node from the rebuildable graph
contract when the operator has not provided a selector. It does not write node
IDs, persist graph state, edit files, execute workflows, call providers or
connectors, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.graph_view_browser_qa import (
    NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA,
)
from runtime.studio.graph_view_shell_panel import build_graph_view_shell_panel_contract
from runtime.studio.node_inspector_contract import build_node_inspector_contract


MODEL_VERSION = "studio.node_inspector_shell_panel.v1"
SURFACE_ID = "studio_node_inspector_shell_panel_contract"
PANEL_ID = "studio.node_inspector.shell_panel"
NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_CONTRACT = "phase10-studio-node-inspector-shell-panel-mount"
NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_MOUNT = "phase10-studio-node-inspector-shell-panel-browser-qa"


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


def _default_selector_from_graph(
    vault: Path,
    *,
    folder_path: str | Path | None,
    max_files: int | None,
    max_bytes_per_file: int | None,
    max_nodes: int | None,
    max_edges: int | None,
) -> dict[str, Any]:
    graph = build_graph_index_contract(
        vault,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    nodes = (graph.get("graph") or {}).get("nodes") or []
    file_node = next((node for node in nodes if (node.get("properties") or {}).get("path")), None)
    selected = file_node or (nodes[0] if nodes else None)
    if selected is None:
        return {
            "selector_type": "derived-default-node",
            "selector_value": None,
            "selected_node_id": None,
            "selected_path": None,
            "graph_ok": bool(graph.get("ok")),
            "graph_blockers": (graph.get("readiness") or {}).get("blockers", []),
        }
    properties = selected.get("properties") or {}
    selected_path = properties.get("path")
    return {
        "selector_type": "derived-default-path" if selected_path else "derived-default-node-id",
        "selector_value": selected_path or selected.get("id"),
        "selected_node_id": selected.get("id"),
        "selected_path": selected_path,
        "selected_node_label": selected.get("label"),
        "selected_node_type": selected.get("node_type"),
        "graph_ok": bool(graph.get("ok")),
        "graph_blockers": (graph.get("readiness") or {}).get("blockers", []),
    }


def _resolve_selection(
    vault: Path,
    *,
    node_id: str | None,
    path: str | Path | None,
    folder_path: str | Path | None,
    max_files: int | None,
    max_bytes_per_file: int | None,
    max_nodes: int | None,
    max_edges: int | None,
) -> dict[str, Any]:
    if node_id:
        return {
            "selector_type": "explicit-node-id",
            "selector_value": node_id,
            "selected_node_id": node_id,
            "selected_path": None,
            "selection_source": "operator-provided-read-only-selector",
        }
    if path is not None:
        return {
            "selector_type": "explicit-path",
            "selector_value": str(path),
            "selected_node_id": None,
            "selected_path": str(path),
            "selection_source": "operator-provided-read-only-selector",
        }
    selector = _default_selector_from_graph(
        vault,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    selector["selection_source"] = "derived-from-rebuildable-graph-contract"
    return selector


def build_node_inspector_shell_panel_contract(
    vault_root: str | Path,
    *,
    node_id: str | None = None,
    path: str | Path | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    content_excerpt_bytes: int | None = None,
) -> dict[str, Any]:
    """Return the read-only node inspector shell-panel contract."""

    vault = _vault_path(vault_root)
    selection = _resolve_selection(
        vault,
        node_id=node_id,
        path=path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    inspector = build_node_inspector_contract(
        vault,
        node_id=selection.get("selected_node_id") if not selection.get("selected_path") else None,
        path=selection.get("selected_path"),
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    graph_panel = build_graph_view_shell_panel_contract(
        vault,
        focus_node_id=selection.get("selected_node_id"),
        focus_path=selection.get("selected_path"),
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    inspector_readiness = inspector.get("readiness") or {}
    graph_readiness = graph_panel.get("readiness") or {}
    selected_node = inspector.get("selected_node")
    edge_context = inspector.get("edge_context") or {}
    source_excerpt = inspector.get("source_excerpt") or {}
    blockers = list(inspector_readiness.get("blockers") or [])
    warnings = list(inspector_readiness.get("warnings") or [])
    if not graph_readiness.get("graph_view_shell_panel_browser_qa_ready"):
        blockers.append("graph-shell-panel-browser-qa-required")
    shell_mount_ready = _node_inspector_shell_panel_mount_built(vault)
    contract_ready = (
        bool(inspector.get("ok"))
        and bool(selected_node)
        and bool(graph_readiness.get("graph_view_shell_panel_browser_qa_ready"))
        and not blockers
    )
    next_pass = (
        NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_MOUNT
        if shell_mount_ready and contract_ready
        else NEXT_NODE_INSPECTOR_PASS_AFTER_SHELL_PANEL_CONTRACT
        if contract_ready
        else NEXT_GRAPH_VIEW_PASS_AFTER_SHELL_PANEL_BROWSER_QA
    )
    selected_properties = (selected_node or {}).get("properties") or {}
    source_path = selected_properties.get("path") or source_excerpt.get("path")
    return {
        "ok": contract_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Node Inspector Shell Panel Contract",
        "phase": "Phase 10A/10B - Studio Core Shell / Graph + Node Model",
        "status": (
            "COMPLETE TARGETED / NODE INSPECTOR SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT"
            if shell_mount_ready and contract_ready
            else "PARTIAL / NODE INSPECTOR SHELL PANEL CONTRACT BUILT / SHELL MOUNT NOT BUILT"
            if contract_ready
            else "BLOCKED / NODE INSPECTOR SHELL PANEL CONTRACT BUILT / GRAPH OR NODE EVIDENCE INCOMPLETE"
        ),
        "vault_root": str(vault),
        "panel": {
            "panel_id": PANEL_ID,
            "label": "Node Inspector",
            "surface_route": "#node-inspector",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-selected-node-detail-panel",
            "selection_source": selection.get("selection_source"),
            "selector_type": selection.get("selector_type"),
            "selector_value": selection.get("selector_value"),
            "selected_node_id": (selected_node or {}).get("id"),
            "selected_node_label": (selected_node or {}).get("label"),
            "selected_node_type": (selected_node or {}).get("node_type"),
            "selected_node_path": source_path,
            "source_excerpt_available": bool(source_excerpt.get("available")),
            "source_excerpt_bytes": source_excerpt.get("bytes_read", 0),
            "graph_shell_panel_route": "#graph-view",
            "graph_shell_panel_contract_ready": bool(graph_readiness.get("graph_view_shell_panel_contract_ready")),
            "graph_shell_panel_browser_qa_ready": bool(
                graph_readiness.get("graph_view_shell_panel_browser_qa_ready")
            ),
        },
        "summary": {
            "selected_node_found": selected_node is not None,
            "selected_node_label": (selected_node or {}).get("label"),
            "selected_node_type": (selected_node or {}).get("node_type"),
            "source_path": source_path,
            "incoming_edge_count": edge_context.get("incoming_edge_count", 0),
            "outgoing_edge_count": edge_context.get("outgoing_edge_count", 0),
            "related_node_count": edge_context.get("related_node_count", 0),
            "source_excerpt_available": bool(source_excerpt.get("available")),
            "source_excerpt_truncated": bool(source_excerpt.get("truncated")),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
        },
        "source_node_inspector": inspector,
        "source_graph_shell_panel": {
            "surface": graph_panel.get("surface"),
            "model_version": graph_panel.get("model_version"),
            "ok": graph_panel.get("ok"),
            "status": graph_panel.get("status"),
            "readiness": graph_readiness,
            "panel": graph_panel.get("panel"),
        },
        "readiness": {
            "node_inspector_shell_panel_contract_ready": contract_ready,
            "node_inspector_contract_ready": bool(inspector_readiness.get("node_inspector_contract_ready")),
            "selected_node_found": selected_node is not None,
            "edge_context_ready": bool(inspector_readiness.get("edge_context_ready")),
            "source_excerpt_ready": bool(inspector_readiness.get("source_excerpt_ready")),
            "graph_view_shell_panel_browser_qa_ready": bool(
                graph_readiness.get("graph_view_shell_panel_browser_qa_ready")
            ),
            "desktop_shell_mount_ready": shell_mount_ready,
            "node_inspector_shell_panel_browser_qa_ready": False,
            "node_inspector_editing_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "node_inspector_truth": {
            "graph_index_contract_built": True,
            "node_inspector_contract_built": True,
            "graph_view_shell_panel_browser_qa_built": bool(
                graph_readiness.get("graph_view_shell_panel_browser_qa_ready")
            ),
            "node_inspector_shell_panel_contract_built": True,
            "node_inspector_shell_panel_mounted": shell_mount_ready,
            "node_inspector_shell_panel_browser_qa_built": False,
            "node_id_writer_built": False,
            "node_editing_built": False,
            "service_layer_write_path_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "reads_file_contents": True,
            "derives_selected_node_from_graph": selection.get("selection_source")
            == "derived-from-rebuildable-graph-contract",
            "uses_existing_derived_node_identity": True,
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
        "allowed_actions": ["inspect-node-shell-panel-contract"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-node-inspector-readonly.md",
        ],
    }
