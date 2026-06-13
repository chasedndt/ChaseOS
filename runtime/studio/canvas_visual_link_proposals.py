"""Preview-only Canvas visual-link proposal bridge for Studio Phase 10E.

Canvas visual links are workspace-local drawing links. This bridge can translate a
selected ``canvas_visual_link`` into the existing visual-link approval preview
shape, but it never queues approval artifacts and never writes markdown, graph
edges, graph snapshots, provenance records, or canonical knowledge. Approved
execution remains owned by ``runtime.studio.visual_link_approval`` and the
Studio/Gate service-layer rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.studio.canvas_drafts import (
    CANVAS_SAVE_BLOCKED_AUTHORITY,
    CANVAS_SAVE_WRITE_CONTRACT,
    CanvasDraftError,
    CanvasLink,
    load_canvas_draft,
)
from runtime.studio.canvas_graph_node_refs import resolve_canvas_graph_node_refs
from runtime.studio.visual_link_approval import build_visual_link_preview

SURFACE_ID = "studio_canvas_visual_link_proposal_bridge"
MODEL_VERSION = "studio.canvas_visual_link_proposal_bridge.v1"
VISUAL_LINK_APPROVAL_OWNER = "studio_visual_link_approval_flow"
VISUAL_LINK_PROPOSAL_SURFACE = "visual-link-approval-flow"

_AUTHORITY: dict[str, bool] = {
    "preview_only": True,
    "read_only": True,
    "queues_approval_artifacts": False,
    "writes_vault": False,
    "writes_markdown": False,
    "writes_graph_edges": False,
    "writes_graph_index": False,
    "writes_graph_snapshot": False,
    "writes_provenance": False,
    "writes_source_package": False,
    "canonical_mutation_allowed": False,
    "graph_mutation_allowed": False,
    "approved_execution_in_scope": False,
    "promotion_requires_gate": True,
    "browser_control_allowed": False,
}


def build_canvas_visual_link_proposals(
    vault_root: str | Path,
    draft_name: str,
    *,
    selected_link_ids: list[str] | tuple[str, ...] | set[str] | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    content_excerpt_bytes: int | None = None,
) -> dict[str, Any]:
    """Build preview-only approval proposals from Canvas visual links.

    ``selected_link_ids`` optionally narrows conversion to specific Canvas link
    IDs. The returned proposal keeps the Canvas ``link_id`` separate from the
    non-canonical graph preview edge ID emitted by the existing visual-link
    approval preview path.
    """

    vault = Path(vault_root)
    try:
        document = load_canvas_draft(vault, draft_name)
    except CanvasDraftError as exc:
        return _response_base(ok=False, status="blocked_or_failed") | {
            "error": {"code": exc.code, "message": exc.message},
            "draft_name": draft_name,
            "canvas_id": None,
            "proposals": [],
            "summary": _summary([]),
        }

    selected = {str(item) for item in selected_link_ids or [] if str(item)}
    refs_response = resolve_canvas_graph_node_refs(
        vault,
        draft_name,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    refs_by_object_id = {
        str(ref.get("object_id")): ref
        for ref in refs_response.get("references", [])
        if isinstance(ref, dict) and ref.get("object_id")
    }

    proposals: list[dict[str, Any]] = []
    for link in document.links:
        if link.kind != "canvas_visual_link":
            continue
        if selected and link.link_id not in selected:
            continue
        proposals.append(
            _proposal_for_link(
                vault,
                link,
                refs_by_object_id=refs_by_object_id,
                folder_path=folder_path,
                max_nodes=max_nodes,
                max_edges=max_edges,
            )
        )

    return _response_base(ok=True, status="ok") | {
        "draft_name": draft_name,
        "canvas_id": document.canvas_id,
        "selected_link_ids": sorted(selected),
        "node_resolution_surface": refs_response.get("surface"),
        "proposals": proposals,
        "summary": _summary(proposals),
    }


def _proposal_for_link(
    vault: Path,
    link: CanvasLink,
    *,
    refs_by_object_id: dict[str, dict[str, Any]],
    folder_path: str | Path | None,
    max_nodes: int | None,
    max_edges: int | None,
) -> dict[str, Any]:
    source_ref = refs_by_object_id.get(link.source_object_id)
    target_ref = refs_by_object_id.get(link.target_object_id)
    conversion = dict(link.conversion or {})
    relation_type = _text(conversion.get("relation_type"), fallback="related")
    edge_layer = _text(conversion.get("edge_layer"), fallback="suggested")
    evidence = _text(conversion.get("evidence"), fallback="canvas visual link")
    label = _text(link.label, fallback=relation_type)

    base = {
        "canvas_link_id": link.link_id,
        "canvas_link_kind": link.kind,
        "canvas_source_object_id": link.source_object_id,
        "canvas_target_object_id": link.target_object_id,
        "canvas_label": link.label,
        "source_ref": source_ref,
        "target_ref": target_ref,
        "approval_posture": _approval_posture(),
        "conversion_request": {
            "proposal_surface": VISUAL_LINK_PROPOSAL_SURFACE,
            "edge_layer": edge_layer,
            "relation_type": relation_type,
            "label": label,
            "evidence": evidence,
        },
    }

    warnings = _resolution_warnings(source_ref, target_ref)
    if warnings:
        return base | {
            "ok": False,
            "state": "blocked_unresolved_graph_nodes",
            "graph_edge_id": None,
            "visual_link_preview": None,
            "warnings": warnings,
        }

    assert source_ref is not None
    assert target_ref is not None
    preview = build_visual_link_preview(
        vault,
        source_node_id=str(source_ref.get("node_id") or ""),
        target_node_id=str(target_ref.get("node_id") or ""),
        source_path=_preview_source_path(vault, source_ref, folder_path),
        target_path=_preview_source_path(vault, target_ref, folder_path),
        edge_layer=edge_layer,
        relation_type=relation_type,
        label=label,
        evidence=evidence,
        max_nodes=max_nodes or 5000,
        max_edges=max_edges or 10000,
    )
    stripped_preview = _strip_content(preview)
    preview_edge = stripped_preview.get("preview_edge") if isinstance(stripped_preview, dict) else None
    graph_edge_id = preview_edge.get("id") if isinstance(preview_edge, dict) else None
    return base | {
        "ok": bool(preview.get("ok")),
        "state": "preview_ready" if preview.get("ok") else "visual_link_preview_blocked",
        "graph_edge_id": graph_edge_id,
        "visual_link_preview": stripped_preview,
        "warnings": [],
    }


def _preview_source_path(vault: Path, ref: dict[str, Any], folder_path: str | Path | None) -> str:
    raw_path = str(ref.get("current_source_path") or ref.get("source_path") or "").strip()
    if not raw_path:
        return ""
    normalized = raw_path.replace("\\", "/").lstrip("./")
    if (vault / normalized).is_file():
        return normalized
    if folder_path is not None:
        candidate = (Path(str(folder_path).replace("\\", "/")) / normalized).as_posix().lstrip("./")
        if (vault / candidate).is_file():
            return candidate
    return normalized


def _response_base(*, ok: bool, status: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "status": status,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "authority": dict(_AUTHORITY),
        "blocked_authority": list(CANVAS_SAVE_BLOCKED_AUTHORITY),
        "write_contract": dict(CANVAS_SAVE_WRITE_CONTRACT) | {
            "canvas_draft_json_writes": False,
            "approval_artifact_writes": False,
        },
        "allowed_actions": ["preview-canvas-visual-link-approval-proposal"],
        "execution_boundary": {
            "preview_reuses": VISUAL_LINK_APPROVAL_OWNER,
            "approval_queue_in_scope": False,
            "approved_execution_owned_by": VISUAL_LINK_APPROVAL_OWNER,
            "gate_required_for_any_execution": True,
        },
    }


def _approval_posture() -> dict[str, Any]:
    return {
        "proposal_surface": VISUAL_LINK_PROPOSAL_SURFACE,
        "preview_only": True,
        "approval_required_for_execution": True,
        "queued_approval_artifact": False,
        "approved_execution_owned_by": VISUAL_LINK_APPROVAL_OWNER,
    }


def _resolution_warnings(source_ref: dict[str, Any] | None, target_ref: dict[str, Any] | None) -> list[str]:
    warnings: list[str] = []
    warnings.extend(_ref_warning("source", source_ref))
    warnings.extend(_ref_warning("target", target_ref))
    return warnings


def _ref_warning(prefix: str, ref: dict[str, Any] | None) -> list[str]:
    if ref is None:
        return [f"{prefix}-ref-missing"]
    state = str(ref.get("state") or "")
    if state == "existing_node":
        return []
    if state == "stale_node_source_path_moved":
        return [f"{prefix}-ref-stale"]
    if state == "missing_node":
        return [f"{prefix}-ref-missing"]
    return [f"{prefix}-ref-unresolved"]


def _strip_content(value: dict[str, Any]) -> dict[str, Any]:
    stripped = dict(value)
    stripped.pop("content", None)
    if isinstance(stripped.get("safe_patch_summary"), dict):
        stripped["safe_patch_summary"] = dict(stripped["safe_patch_summary"]) | {"content_stripped": True}
    if isinstance(stripped.get("proposal_packet"), dict):
        packet = dict(stripped["proposal_packet"])
        summary = packet.get("before_after_summary")
        if isinstance(summary, dict):
            packet["before_after_summary"] = dict(summary) | {"content_stripped": True}
        stripped["proposal_packet"] = packet
    return stripped


def _summary(proposals: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_canvas_visual_links": len(proposals),
        "preview_ready": sum(1 for proposal in proposals if proposal.get("state") == "preview_ready"),
        "blocked_unresolved_graph_nodes": sum(
            1 for proposal in proposals if proposal.get("state") == "blocked_unresolved_graph_nodes"
        ),
        "visual_link_preview_blocked": sum(
            1 for proposal in proposals if proposal.get("state") == "visual_link_preview_blocked"
        ),
    }


def _text(value: Any, *, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback
