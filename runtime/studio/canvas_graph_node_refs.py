"""Read-only Canvas graph-node reference resolver for Studio Phase 10E.

Canvas graph-node references are pointers only. This resolver composes the
workspace-local Canvas draft loader with the existing read-only Node Inspector
contract so a Canvas card can report whether its target still resolves without
persisting graph IDs, rewriting markdown, mutating graph snapshots, or creating
canonical/provenance state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.studio.canvas_drafts import (
    CANVAS_BLOCKED_AUTHORITY,
    CANVAS_WRITE_CONTRACT,
    CanvasDraftError,
    CanvasObject,
    load_canvas_draft,
)
from runtime.studio.node_inspector_contract import (
    SURFACE_ID as NODE_INSPECTOR_SURFACE_ID,
    build_node_inspector_contract,
)

SURFACE_ID = "studio_canvas_graph_node_ref_resolver"
MODEL_VERSION = "studio.canvas_graph_node_ref_resolver.v1"


_RESOLVER_AUTHORITY: dict[str, bool] = {
    "read_only": True,
    "writes_vault": False,
    "writes_markdown": False,
    "writes_node_ids": False,
    "writes_graph_index": False,
    "writes_snapshot": False,
    "writes_provenance": False,
    "writes_source_package": False,
    "canonical_mutation_allowed": False,
    "graph_mutation_allowed": False,
    "promotion_requires_gate": True,
    "browser_control_allowed": False,
}


def resolve_canvas_graph_node_refs(
    vault_root: str | Path,
    draft_name: str,
    *,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    content_excerpt_bytes: int | None = None,
) -> dict[str, Any]:
    """Resolve graph_node_ref objects in a Canvas draft through Node Inspector.

    The return value is JSON-serializable and reports one state per graph-node
    reference:
    - ``existing_node``: stored node id resolves and stored source path still matches.
    - ``missing_node``: neither node id nor source path resolves to an existing node.
    - ``stale_node_source_path_moved``: the pointer resolves, but node id/source path
      no longer agree with the current derived graph identity.
    - ``unsupported_target_type``: the Canvas object is malformed for graph-node
      resolution, e.g. target_ref.type is not ``graph_node``.
    """

    vault = Path(vault_root)
    try:
        document = load_canvas_draft(vault, draft_name)
    except CanvasDraftError as exc:
        return _response_base(ok=False, status="blocked_or_failed") | {
            "error": {"code": exc.code, "message": exc.message},
            "references": [],
            "summary": _summary([]),
        }

    refs: list[dict[str, Any]] = []
    for obj in document.objects:
        if obj.kind != "graph_node_ref":
            continue
        refs.append(
            _resolve_object(
                vault,
                obj,
                folder_path=folder_path,
                max_files=max_files,
                max_bytes_per_file=max_bytes_per_file,
                max_nodes=max_nodes,
                max_edges=max_edges,
                content_excerpt_bytes=content_excerpt_bytes,
            )
        )

    return _response_base(ok=True, status="ok") | {
        "draft_name": draft_name,
        "canvas_id": document.canvas_id,
        "references": refs,
        "summary": _summary(refs),
    }


def _resolve_object(
    vault: Path,
    obj: CanvasObject,
    *,
    folder_path: str | Path | None,
    max_files: int | None,
    max_bytes_per_file: int | None,
    max_nodes: int | None,
    max_edges: int | None,
    content_excerpt_bytes: int | None,
) -> dict[str, Any]:
    target = obj.target_ref or {}
    target_type = target.get("type")
    node_id = _string_or_none(target.get("node_id"))
    source_path = _normalize_path(_string_or_none(target.get("source_path")))
    target_trust_state = _string_or_none(target.get("trust_state"))

    if target_type != "graph_node" or not node_id:
        return _reference_base(obj, target, node_id=node_id, source_path=source_path) | {
            "state": "unsupported_target_type",
            "current_source_path": None,
            "node_inspector_link": None,
            "selected_node": None,
            "trust_source_posture": _trust_source_posture(None, target_trust_state, None),
            "warnings": ["unsupported-target-type"],
        }

    inspector = build_node_inspector_contract(
        vault,
        node_id=node_id,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    selected = inspector.get("selected_node")
    current_source_path = _current_source_path(inspector, selected)

    if selected is not None:
        moved = bool(source_path and current_source_path and source_path != current_source_path)
        state = "stale_node_source_path_moved" if moved else "existing_node"
        return _reference_base(obj, target, node_id=node_id, source_path=source_path) | {
            "state": state,
            "current_source_path": current_source_path,
            "node_inspector_link": _inspector_link(inspector),
            "selected_node": _selected_node_summary(selected),
            "trust_source_posture": _trust_source_posture(inspector, target_trust_state, selected),
            "warnings": _warnings(inspector) + (["source-path-moved"] if moved else []),
        }

    path_inspector: dict[str, Any] | None = None
    path_selected: dict[str, Any] | None = None
    if source_path:
        path_inspector = build_node_inspector_contract(
            vault,
            path=source_path,
            folder_path=folder_path,
            max_files=max_files,
            max_bytes_per_file=max_bytes_per_file,
            max_nodes=max_nodes,
            max_edges=max_edges,
            content_excerpt_bytes=content_excerpt_bytes,
        )
        path_selected = path_inspector.get("selected_node")

    if path_selected is not None:
        return _reference_base(obj, target, node_id=node_id, source_path=source_path) | {
            "state": "stale_node_source_path_moved",
            "current_source_path": _current_source_path(path_inspector or {}, path_selected),
            "node_inspector_link": _inspector_link(path_inspector or {}),
            "selected_node": _selected_node_summary(path_selected),
            "trust_source_posture": _trust_source_posture(path_inspector, target_trust_state, path_selected),
            "warnings": _warnings(inspector) + ["node-id-stale-source-path-resolved"],
        }

    return _reference_base(obj, target, node_id=node_id, source_path=source_path) | {
        "state": "missing_node",
        "current_source_path": None,
        "node_inspector_link": None,
        "selected_node": None,
        "trust_source_posture": _trust_source_posture(inspector, target_trust_state, None),
        "warnings": _warnings(inspector) or ["node-not-found"],
    }


def _response_base(*, ok: bool, status: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "status": status,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "authority": dict(_RESOLVER_AUTHORITY),
        "blocked_authority": list(CANVAS_BLOCKED_AUTHORITY),
        "write_contract": dict(CANVAS_WRITE_CONTRACT),
        "possible_writes": [],
        "allowed_actions": ["resolve-canvas-graph-node-reference", "open-read-only-node-inspector"],
    }


def _reference_base(
    obj: CanvasObject,
    target: dict[str, Any],
    *,
    node_id: str | None,
    source_path: str | None,
) -> dict[str, Any]:
    return {
        "object_id": obj.object_id,
        "label": obj.label,
        "kind": obj.kind,
        "target_type": target.get("type"),
        "node_id": node_id,
        "source_path": source_path,
        "target_ref_trust_state": _string_or_none(target.get("trust_state")),
    }


def _inspector_link(inspector: dict[str, Any]) -> dict[str, Any] | None:
    selected = inspector.get("selected_node")
    selector = inspector.get("selector")
    if selected is None or not isinstance(selector, dict):
        return None
    return {
        "surface": NODE_INSPECTOR_SURFACE_ID,
        "read_only": True,
        "selector": dict(selector),
        "allowed_action": "inspect-node",
    }


def _current_source_path(inspector: dict[str, Any], selected: dict[str, Any] | None) -> str | None:
    identity = inspector.get("node_identity") if isinstance(inspector, dict) else None
    if isinstance(identity, dict):
        path = _normalize_path(_string_or_none(identity.get("path")))
        if path:
            return path
    properties = (selected or {}).get("properties") or {}
    return _normalize_path(_string_or_none(properties.get("path")))


def _selected_node_summary(node: dict[str, Any]) -> dict[str, Any]:
    properties = node.get("properties") or {}
    return {
        "id": node.get("id"),
        "label": node.get("label"),
        "node_type": node.get("node_type"),
        "node_family": node.get("node_family"),
        "stable_key": node.get("stable_key"),
        "source_path": _normalize_path(_string_or_none(properties.get("path"))),
        "source": node.get("source"),
        "confidence": node.get("confidence"),
    }


def _trust_source_posture(
    inspector: dict[str, Any] | None,
    target_trust_state: str | None,
    selected: dict[str, Any] | None,
) -> dict[str, Any]:
    trust = (inspector or {}).get("trust_evidence") or {}
    metadata = (inspector or {}).get("metadata_state") or {}
    provenance = (inspector or {}).get("provenance_summary") or {}
    selected_props = (selected or {}).get("properties") or {}
    return {
        "target_ref_trust_state": target_trust_state,
        "graph_trust_state": trust.get("graph_trust_state") or selected_props.get("trust_state") or "raw",
        "provenance_trust_state": trust.get("provenance_trust_state"),
        "metadata_conflict": bool(trust.get("metadata_conflict")),
        "stale_or_ambiguous_metadata": bool(metadata.get("stale_or_ambiguous_metadata")),
        "source": (selected or {}).get("source"),
        "confidence": (selected or {}).get("confidence"),
        "provenance_status": provenance.get("status"),
    }


def _warnings(inspector: dict[str, Any] | None) -> list[str]:
    readiness = (inspector or {}).get("readiness") or {}
    warnings = list(readiness.get("warnings") or [])
    for blocker in readiness.get("blockers") or []:
        if blocker not in warnings:
            warnings.append(str(blocker))
    return warnings


def _summary(refs: list[dict[str, Any]]) -> dict[str, int]:
    states = {
        "existing_node": 0,
        "missing_node": 0,
        "stale_node_source_path_moved": 0,
        "unsupported_target_type": 0,
    }
    for ref in refs:
        state = str(ref.get("state"))
        states[state] = states.get(state, 0) + 1
    return {"total_graph_node_refs": len(refs), **states}


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_path(path: str | None) -> str | None:
    if not path:
        return None
    return path.replace("\\", "/").lstrip("./")
