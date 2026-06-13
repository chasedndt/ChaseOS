"""Read-only Studio Canvas / Whiteboard shell-panel contract.

This module mounts the Phase 10E workspace-local Canvas draft loader as a
visualization-only Studio panel. It does not save canvas positions, edit cards,
mutate graph truth, write canonical/provenance/source-package state, or control
browser/Excalidraw surfaces.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.canvas_drafts import (
    CANVAS_BLOCKED_AUTHORITY,
    CANVAS_WRITE_CONTRACT,
    CanvasDraftError,
    CanvasObject,
    load_canvas_draft,
)
from runtime.studio.canvas_graph_node_refs import resolve_canvas_graph_node_refs

MODEL_VERSION = "studio.canvas_panel.v1"
SURFACE_ID = "studio_canvas_panel_contract"
PANEL_ID = "studio.canvas.panel"
DEFAULT_DRAFT_NAME = "phase10e_seed_canvas.json"
BOUNDARY_BANNER = (
    "Workspace-local canvas draft. This board does not mutate graph truth or canonical knowledge. "
    "Promotion and graph writes require Gate approval."
)

_OBJECT_BADGES: dict[str, tuple[str, str]] = {
    "graph_node_ref": ("derived/existing graph node", "source"),
    "note_card": ("workspace-local draft", "draft"),
    "group": ("workspace-local draft group", "draft"),
    "image_ref": ("workspace-local image/proof reference", "source"),
    "artifact_ref": ("audit/log/proof artifact", "source"),
    "proposal_card": ("approval-required proposal preview", "draft"),
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _object_badge(obj: CanvasObject) -> dict[str, Any]:
    badge, badge_family = _OBJECT_BADGES.get(obj.kind, ("workspace-local draft", "draft"))
    target = obj.target_ref or {}
    return {
        "object_id": obj.object_id,
        "kind": obj.kind,
        "label": obj.label,
        "badge": badge,
        "badge_family": badge_family,
        "source_path": target.get("source_path") or target.get("path"),
        "node_id": target.get("node_id"),
        "target_type": target.get("type"),
        "read_only": True,
    }


def _visual_object(obj: CanvasObject, badge: dict[str, Any]) -> dict[str, Any]:
    return {
        "object_id": obj.object_id,
        "kind": obj.kind,
        "label": obj.label,
        "position": dict(obj.position),
        "size": dict(obj.size),
        "style": dict(obj.style),
        "badge": badge["badge"],
        "badge_family": badge["badge_family"],
        "draft_text": obj.draft_text,
        "target_ref": dict(obj.target_ref or {}),
        "read_only": True,
        "draggable": False,
        "editable": False,
        "save_enabled": False,
    }


def _summary(objects: list[CanvasObject], links: list[Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for obj in objects:
        counts[obj.kind] = counts.get(obj.kind, 0) + 1
    return {
        "object_count": len(objects),
        "link_count": len(links),
        "object_kind_counts": counts,
        "graph_node_ref_count": counts.get("graph_node_ref", 0),
        "note_card_count": counts.get("note_card", 0),
        "artifact_ref_count": counts.get("artifact_ref", 0),
        "proposal_card_count": counts.get("proposal_card", 0),
        "group_count": counts.get("group", 0),
    }


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "local_only": True,
        "workspace_local_draft_only": True,
        "canvas_draft_save_allowed": False,
        "card_editing_allowed": False,
        "drag_save_allowed": False,
        "graph_mutation_allowed": False,
        "canonical_mutation_allowed": False,
        "provenance_write_allowed": False,
        "source_package_write_allowed": False,
        "browser_control_allowed": False,
        "excalidraw_control_allowed": False,
        "workflow_execution_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "promotion_requires_gate": True,
    }


def _blocked_response(vault: Path, draft_name: str, exc: CanvasDraftError) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Canvas Panel Contract",
        "phase": "Phase 10E - Studio Canvas / Whiteboard / Spatial Mode",
        "status": "BLOCKED / CANVAS PANEL CONTRACT BUILT / DRAFT LOAD FAILED",
        "vault_root": str(vault),
        "boundary_banner": BOUNDARY_BANNER,
        "panel": {
            "panel_id": PANEL_ID,
            "label": "Canvas / Whiteboard",
            "surface_route": "#canvas",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-canvas-draft-visualization",
            "draft_name": draft_name,
            "visualization_only": True,
        },
        "summary": _summary([], []),
        "source_badges": [],
        "visualization": {"objects": [], "links": []},
        "graph_node_refs": {"references": [], "summary": {"total_graph_node_refs": 0}},
        "readiness": {
            "canvas_panel_contract_ready": False,
            "canvas_draft_loaded": False,
            "desktop_shell_mount_ready": False,
            "blockers": [exc.code],
            "warnings": [],
            "next_recommended_pass": "phase10e-canvas-panel-contract-fix-draft-loader",
        },
        "authority": _authority(),
        "blocked_authority": list(CANVAS_BLOCKED_AUTHORITY),
        "write_contract": dict(CANVAS_WRITE_CONTRACT),
        "possible_writes": [],
        "allowed_actions": [],
        "error": {"code": exc.code, "message": exc.message},
    }


def build_canvas_panel_contract(
    vault_root: str | Path,
    *,
    draft_name: str | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    content_excerpt_bytes: int | None = None,
) -> dict[str, Any]:
    """Return the read-only Studio Canvas shell-panel contract."""

    vault = _vault_path(vault_root)
    selected_draft = draft_name or DEFAULT_DRAFT_NAME
    try:
        document = load_canvas_draft(vault, selected_draft)
    except CanvasDraftError as exc:
        return _blocked_response(vault, selected_draft, exc)

    badges = [_object_badge(obj) for obj in document.objects]
    badge_by_id = {badge["object_id"]: badge for badge in badges}
    graph_refs = resolve_canvas_graph_node_refs(
        vault,
        selected_draft,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    warnings = [] if graph_refs.get("ok") else ["graph-node-ref-resolution-unavailable"]
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Canvas Panel Contract",
        "phase": "Phase 10E - Studio Canvas / Whiteboard / Spatial Mode",
        "status": "PARTIAL / CANVAS PANEL CONTRACT BUILT / READ-ONLY SHELL VISUALIZATION",
        "vault_root": str(vault),
        "boundary_banner": BOUNDARY_BANNER,
        "panel": {
            "panel_id": PANEL_ID,
            "label": "Canvas / Whiteboard",
            "surface_route": "#canvas",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-canvas-draft-visualization",
            "draft_name": selected_draft,
            "canvas_id": document.canvas_id,
            "visualization_only": True,
            "source_contract": "runtime.studio.canvas_drafts.load_canvas_draft + runtime.studio.canvas_graph_node_refs.resolve_canvas_graph_node_refs",
        },
        "summary": _summary(document.objects, document.links),
        "source_badges": badges,
        "visualization": {
            "objects": [_visual_object(obj, badge_by_id[obj.object_id]) for obj in document.objects],
            "links": [link.to_dict() for link in document.links],
            "view_state": dict(document.view_state),
        },
        "graph_node_refs": graph_refs,
        "readiness": {
            "canvas_panel_contract_ready": True,
            "canvas_draft_loaded": True,
            "desktop_shell_mount_ready": True,
            "canvas_save_boundary_ready": False,
            "browser_or_excalidraw_control_ready": False,
            "blockers": [],
            "warnings": warnings,
            "next_recommended_pass": "phase10e-canvas-workspace-local-draft-save-boundary",
        },
        "authority": _authority(),
        "blocked_authority": list(CANVAS_BLOCKED_AUTHORITY),
        "write_contract": dict(CANVAS_WRITE_CONTRACT),
        "possible_writes": [],
        "allowed_actions": ["open-read-only-node-inspector"],
    }
