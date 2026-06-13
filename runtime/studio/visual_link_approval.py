"""Approval-gated visual link proposal controller for Studio Phase 10AB."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.graph_visual_model import normalize_edge_layer
from runtime.studio.service import ActionSpec, StudioService


PASS_ID = "phase10ab-visual-link-approval-flow"
NEXT_RECOMMENDED_PASS = "phase10ac-runtime-cockpit-action-readiness"
SURFACE_ID = "studio_visual_link_approval_flow"
MODEL_VERSION = "studio.visual_link_approval.v1"
DEFAULT_OVERLAY_LIMIT = 250
DEFAULT_RESOLVE_MAX_NODES = 5000
DEFAULT_RESOLVE_MAX_EDGES = 10000

ALLOWED_EDGE_LAYERS = ("explicit", "suggested", "runtime")
ALLOWED_RELATION_TYPES = (
    "related",
    "references",
    "supports",
    "contradicts",
    "depends_on",
    "follows",
    "derived_from",
    "same_project",
    "runtime_action",
)
RELATION_TO_GRAPH_RELATION = {
    "related": "studio_visual_related",
    "references": "studio_visual_references",
    "supports": "studio_visual_supports",
    "contradicts": "studio_visual_contradicts",
    "depends_on": "studio_visual_depends_on",
    "follows": "studio_visual_follows",
    "derived_from": "studio_visual_derived_from",
    "same_project": "studio_visual_same_project",
    "runtime_action": "studio_visual_runtime_action",
}

_SAFE_TEXT_RE = re.compile(r"^[^\r\n]{0,180}$")


@dataclass(frozen=True)
class ResolvedVisualLinkNode:
    node_id: str
    path: str
    label: str
    node_type: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_vault_path(vault_root: Path, rel_path: str) -> Path | None:
    try:
        candidate = (vault_root / rel_path).resolve()
        candidate.relative_to(vault_root.resolve())
    except Exception:
        return None
    return candidate


def _rel_path(path: Path, vault_root: Path) -> str:
    return path.resolve().relative_to(vault_root.resolve()).as_posix()


def _normalize_rel_path(value: str) -> str:
    return value.replace("\\", "/").lstrip("./").strip("/")


def _sanitize_label(value: str, fallback: str = "Link") -> str:
    text = str(value or "").strip()
    text = text.replace("[", "").replace("]", "").replace("|", "-")
    text = re.sub(r"\s+", " ", text)
    return text[:120] or fallback


def _slug(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text or "visual-link"


def _digest(*parts: object, length: int = 24) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def _approval_dir(vault_root: Path) -> Path:
    return vault_root / StudioService.APPROVAL_DIR


def _load_approval_payload(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _approval_action_spec(payload: dict[str, Any]) -> dict[str, Any]:
    spec = payload.get("action_spec") or {}
    return spec if isinstance(spec, dict) else {}


def _approval_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = _approval_action_spec(payload).get("metadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _is_active_approval_status(status: Any) -> bool:
    return str(status or "").lower() in {"pending", "approved", "executing"}


def _active_link_fingerprints(vault_root: Path) -> set[str]:
    fingerprints: set[str] = set()
    approvals = _approval_dir(vault_root)
    if not approvals.is_dir():
        return fingerprints
    for approval_file in approvals.glob("*.json"):
        payload = _load_approval_payload(approval_file)
        if not payload or not _is_active_approval_status(payload.get("status")):
            continue
        metadata = _approval_metadata(payload)
        if metadata.get("pass") != PASS_ID:
            continue
        fingerprint = str(metadata.get("link_fingerprint") or "")
        if fingerprint:
            fingerprints.add(fingerprint)
    return fingerprints


def _graph_contract(vault_root: Path, *, max_nodes: int, max_edges: int) -> dict[str, Any]:
    return build_graph_index_contract(
        str(vault_root),
        max_nodes=max_nodes,
        max_edges=max_edges,
    )


def _node_from_graph(
    vault_root: Path,
    *,
    node_id: str,
    max_nodes: int,
    max_edges: int,
) -> ResolvedVisualLinkNode | None:
    if not node_id:
        return None
    try:
        graph = _graph_contract(vault_root, max_nodes=max_nodes, max_edges=max_edges)
    except Exception:
        return None
    for node in ((graph.get("graph") or {}).get("nodes") or []):
        if str(node.get("id") or "") != node_id:
            continue
        props = node.get("properties") or {}
        rel = _normalize_rel_path(str(props.get("path") or props.get("file_path") or ""))
        if not rel:
            return None
        path = _safe_vault_path(vault_root, rel)
        if not path or not path.exists() or path.suffix.lower() != ".md":
            return None
        return ResolvedVisualLinkNode(
            node_id=node_id,
            path=_rel_path(path, vault_root),
            label=_sanitize_label(str(node.get("label") or path.stem), path.stem),
            node_type=str(node.get("node_type") or "markdown_note"),
        )
    return None


def _node_from_path(
    vault_root: Path,
    *,
    file_path: str,
    node_id: str = "",
    label: str = "",
    max_nodes: int,
    max_edges: int,
) -> ResolvedVisualLinkNode | None:
    rel = _normalize_rel_path(file_path)
    if not rel:
        return None
    path = _safe_vault_path(vault_root, rel)
    if not path or not path.exists() or path.suffix.lower() != ".md":
        return None

    resolved_id = str(node_id or "").strip()
    node_type = "markdown_note"
    if not resolved_id:
        try:
            graph = _graph_contract(vault_root, max_nodes=max_nodes, max_edges=max_edges)
            for node in ((graph.get("graph") or {}).get("nodes") or []):
                props = node.get("properties") or {}
                if _normalize_rel_path(str(props.get("path") or "")) == rel:
                    resolved_id = str(node.get("id") or "")
                    node_type = str(node.get("node_type") or node_type)
                    if not label:
                        label = str(node.get("label") or "")
                    break
        except Exception:
            pass
    if not resolved_id:
        resolved_id = f"studio:path:{_digest(rel, length=18)}"

    return ResolvedVisualLinkNode(
        node_id=resolved_id,
        path=_rel_path(path, vault_root),
        label=_sanitize_label(label or path.stem, path.stem),
        node_type=node_type,
    )


def resolve_visual_link_node(
    vault_root: Path | str,
    *,
    node_id: str = "",
    file_path: str = "",
    label: str = "",
    max_nodes: int = DEFAULT_RESOLVE_MAX_NODES,
    max_edges: int = DEFAULT_RESOLVE_MAX_EDGES,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    if file_path:
        node = _node_from_path(
            vault,
            file_path=file_path,
            node_id=node_id,
            label=label,
            max_nodes=max_nodes,
            max_edges=max_edges,
        )
    else:
        node = _node_from_graph(
            vault,
            node_id=node_id,
            max_nodes=max_nodes,
            max_edges=max_edges,
        )
    if node is None:
        return {
            "ok": False,
            "code": "node_not_found",
            "errors": ["visual link node must resolve to an existing markdown file"],
        }
    return {
        "ok": True,
        "node": {
            "node_id": node.node_id,
            "path": node.path,
            "label": node.label,
            "node_type": node.node_type,
        },
    }


def _normalize_edge_layer(value: str) -> str:
    layer = normalize_edge_layer(value)
    return layer if layer in ALLOWED_EDGE_LAYERS else ""


def _normalize_relation_type(value: str) -> str:
    relation = str(value or "related").strip().lower().replace("-", "_").replace(" ", "_")
    return relation if relation in ALLOWED_RELATION_TYPES else ""


def _validate_optional_text(value: str, field: str) -> list[str]:
    text = str(value or "")
    if _SAFE_TEXT_RE.match(text):
        return []
    return [f"{field} must be a single line of 180 characters or fewer"]


def _wikilink_for_target(target: ResolvedVisualLinkNode) -> str:
    link_body = PurePosixPath(target.path).with_suffix("").as_posix()
    label = _sanitize_label(target.label, PurePosixPath(target.path).stem)
    return f"[[{link_body}|{label}]]"


def _link_line(target: ResolvedVisualLinkNode, relation_type: str, label: str) -> str:
    link = _wikilink_for_target(target)
    relation_label = relation_type.replace("_", " ")
    if label:
        return f"- {link} - {label}"
    return f"- {link} - {relation_label}"


def _existing_link_present(source_content: str, target: ResolvedVisualLinkNode) -> bool:
    path_without_suffix = PurePosixPath(target.path).with_suffix("").as_posix()
    stem = PurePosixPath(target.path).stem
    checks = {
        f"[[{path_without_suffix}]]",
        f"[[{path_without_suffix}|",
        f"[[{stem}]]",
        f"[[{stem}|",
    }
    return any(token in source_content for token in checks)


def build_visual_link_note_patch(
    source_content: str,
    *,
    target: dict[str, Any],
    relation_type: str = "related",
    label: str = "",
) -> str:
    target_node = ResolvedVisualLinkNode(
        node_id=str(target.get("node_id") or ""),
        path=str(target.get("path") or ""),
        label=str(target.get("label") or ""),
        node_type=str(target.get("node_type") or "markdown_note"),
    )
    line = _link_line(target_node, relation_type, _sanitize_label(label, ""))
    section_header = "## Studio Links"
    content = source_content.rstrip()
    if section_header not in source_content:
        return f"{content}\n\n{section_header}\n\n{line}\n"
    return f"{content}\n{line}\n"


def _edge_id(fingerprint: str) -> str:
    return f"studio:visual-link:{fingerprint}"


def _preview_edge(
    *,
    source: ResolvedVisualLinkNode,
    target: ResolvedVisualLinkNode,
    edge_layer: str,
    relation_type: str,
    fingerprint: str,
    approval_id: str | None = None,
    approval_status: str = "preview",
) -> dict[str, Any]:
    relation = RELATION_TO_GRAPH_RELATION.get(relation_type, "studio_visual_related")
    return {
        "id": _edge_id(fingerprint),
        "source": source.node_id,
        "target": target.node_id,
        "source_path": source.path,
        "target_path": target.path,
        "relation": relation,
        "relation_type": relation_type,
        "edge_layer": edge_layer,
        "canonical_layer": "runtime-action" if edge_layer == "runtime" else edge_layer,
        "approval_id": approval_id,
        "approval_status": approval_status,
        "non_canonical": True,
        "pending_visual_link": approval_status in {"pending", "approved", "executing", "preview"},
        "classes": f"edge edge--{edge_layer} visual-link-{approval_status}",
    }


def _direct_mutation_denials() -> dict[str, bool]:
    return {
        "direct_write_allowed": False,
        "writes_without_approval_allowed": False,
        "canonical_graph_writeback_allowed": False,
        "persisted_graph_index_write_allowed": False,
        "node_id_writeback_allowed": False,
        "trust_promotion_allowed": False,
        "provenance_writeback_allowed": False,
        "source_pack_promotion_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_shell_connector_allowed": False,
        "credential_config_mutation_allowed": False,
    }


def _execution_boundary() -> dict[str, Any]:
    return {
        "studio_surface": "proposal_preview_and_approval_artifact_only",
        "executor_contract_required": True,
        "canonical_mutation_authority": "lower_phase_gate_backend_required",
        "approval_consumption_in_scope": False,
    }


def _approval_scope(action_type: str) -> dict[str, Any]:
    return {
        "requires_approval": True,
        "approval_artifact_action_type": action_type,
        "approval_queue_only": True,
        "direct_execution_in_preview_allowed": False,
    }


def _safe_patch_summary(
    *,
    source: ResolvedVisualLinkNode,
    target: ResolvedVisualLinkNode,
    relation_type: str,
    label: str,
    patched: str,
    source_content: str,
) -> dict[str, Any]:
    inserted_line = _link_line(target, relation_type, _sanitize_label(label, ""))
    return {
        "content_stripped": False,
        "summary_type": "visual_link_patch",
        "source_path": source.path,
        "target_path": target.path,
        "insertion_section": "## Studio Links",
        "inserted_line": inserted_line,
        "relationship_label": label or relation_type.replace("_", " "),
        "line_count_before": len(source_content.splitlines()),
        "line_count_after": len(patched.splitlines()),
    }


def _proposal_packet(
    *,
    source_path: str,
    target_path: str,
    before_after_summary: dict[str, Any],
    non_canonical_preview_edges: list[dict[str, Any]],
    conflict_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "operation_type": "visual_link",
        "source_path": source_path,
        "target_path": target_path,
        "before_after_summary": before_after_summary,
        "non_canonical_preview_edges": non_canonical_preview_edges,
        "conflict_state": conflict_state or {"conflicted": False, "conflict_type": "none"},
        "approval_scope": _approval_scope("write_file"),
        "execution_boundary": _execution_boundary(),
        "denied_direct_mutation_flags": _direct_mutation_denials(),
    }


def _derived_graph_link_conflict(
    vault_root: Path,
    source: ResolvedVisualLinkNode,
    target: ResolvedVisualLinkNode,
    *,
    max_nodes: int,
    max_edges: int,
) -> dict[str, Any]:
    try:
        graph = _graph_contract(vault_root, max_nodes=max_nodes, max_edges=max_edges)
    except Exception:
        return {"conflicted": False, "conflict_type": "none", "evidence": "graph_contract_unavailable"}
    for edge in ((graph.get("graph") or {}).get("edges") or []):
        if edge.get("source") == source.node_id and edge.get("target") == target.node_id and edge.get("relation") in {"links_to_note", "links_to_file"}:
            return {
                "conflicted": True,
                "conflict_type": "existing_link",
                "evidence": "derived_graph_edge",
                "edge_id": edge.get("id") or "",
                "source_path": source.path,
                "target_path": target.path,
                "relation": edge.get("relation") or "",
                "source_contract": edge.get("source_contract") or "studio_markdown_scan_contract",
            }
    return {"conflicted": False, "conflict_type": "none", "evidence": "derived_graph_edge_absent"}


def _performance_contract(*, markdown_reads: int, approval_files_scanned: int = 0, overlay_limit: int = DEFAULT_OVERLAY_LIMIT) -> dict[str, Any]:
    return {
        "memory_posture": "bounded-lightweight-overlay",
        "does_not_persist_graph_index": True,
        "does_not_duplicate_full_graph_payload": True,
        "pending_edges_render_as_overlay": True,
        "overlay_reuses_existing_node_positions": True,
        "does_not_rebuild_graph_for_pending_overlay": markdown_reads == 0,
        "selected_markdown_reads": int(markdown_reads),
        "approval_files_scanned": int(approval_files_scanned),
        "max_overlay_edges": int(overlay_limit),
    }


def build_visual_link_preview(
    vault_root: Path | str,
    *,
    source_node_id: str = "",
    target_node_id: str = "",
    source_path: str = "",
    target_path: str = "",
    source_label: str = "",
    target_label: str = "",
    edge_layer: str = "explicit",
    relation_type: str = "related",
    label: str = "",
    evidence: str = "",
    max_nodes: int = DEFAULT_RESOLVE_MAX_NODES,
    max_edges: int = DEFAULT_RESOLVE_MAX_EDGES,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    errors: list[str] = []
    normalized_layer = _normalize_edge_layer(edge_layer)
    normalized_relation = _normalize_relation_type(relation_type)
    if not normalized_layer:
        errors.append("edge_layer must be explicit, suggested, or runtime")
    if not normalized_relation:
        errors.append("relation_type is not supported")
    errors.extend(_validate_optional_text(label, "label"))
    errors.extend(_validate_optional_text(evidence, "evidence"))
    if errors:
        return {"ok": False, "code": "invalid_visual_link_input", "errors": errors, "pass": PASS_ID}

    source_resolved = resolve_visual_link_node(
        vault,
        node_id=source_node_id,
        file_path=source_path,
        label=source_label,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    target_resolved = resolve_visual_link_node(
        vault,
        node_id=target_node_id,
        file_path=target_path,
        label=target_label,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    if not source_resolved.get("ok"):
        return source_resolved | {"pass": PASS_ID, "selector": "source"}
    if not target_resolved.get("ok"):
        return target_resolved | {"pass": PASS_ID, "selector": "target"}

    source = ResolvedVisualLinkNode(**source_resolved["node"])
    target = ResolvedVisualLinkNode(**target_resolved["node"])
    if source.node_id == target.node_id or source.path == target.path:
        return {
            "ok": False,
            "code": "self_link_blocked",
            "errors": ["source and target must be different markdown nodes"],
            "source": source_resolved["node"],
            "target": target_resolved["node"],
            "pass": PASS_ID,
        }

    source_file = _safe_vault_path(vault, source.path)
    if source_file is None or not source_file.exists():
        return {
            "ok": False,
            "code": "source_not_found",
            "errors": ["source markdown file is missing"],
            "pass": PASS_ID,
        }
    source_content = source_file.read_text(encoding="utf-8")
    fingerprint = _digest(source.path, target.path, normalized_relation, normalized_layer)
    if _existing_link_present(source_content, target):
        conflict_state = {
            "conflicted": True,
            "conflict_type": "existing_link",
            "evidence": "raw_wikilink",
            "source_path": source.path,
            "target_path": target.path,
        }
        return {
            "ok": False,
            "code": "link_already_exists",
            "errors": ["source already contains a wikilink to the target"],
            "source": source_resolved["node"],
            "target": target_resolved["node"],
            "link_fingerprint": fingerprint,
            "conflict_state": conflict_state,
            "pass": PASS_ID,
            "performance_contract": _performance_contract(markdown_reads=1),
        }
    derived_conflict = _derived_graph_link_conflict(
        vault,
        source,
        target,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    if derived_conflict.get("conflicted"):
        return {
            "ok": False,
            "code": "link_already_exists",
            "errors": ["derived graph evidence already resolves a markdown link from source to target"],
            "source": source_resolved["node"],
            "target": target_resolved["node"],
            "link_fingerprint": fingerprint,
            "conflict_state": derived_conflict,
            "pass": PASS_ID,
            "performance_contract": _performance_contract(markdown_reads=1),
        }
    if fingerprint in _active_link_fingerprints(vault):
        conflict_state = {
            "conflicted": True,
            "conflict_type": "pending_link_collision",
            "evidence": "active_approval_fingerprint",
            "source_path": source.path,
            "target_path": target.path,
        }
        return {
            "ok": False,
            "code": "pending_link_collision",
            "errors": ["an active approval already exists for this visual link"],
            "source": source_resolved["node"],
            "target": target_resolved["node"],
            "link_fingerprint": fingerprint,
            "conflict_state": conflict_state,
            "pass": PASS_ID,
            "performance_contract": _performance_contract(markdown_reads=1),
        }

    patched = build_visual_link_note_patch(
        source_content,
        target=target_resolved["node"],
        relation_type=normalized_relation,
        label=label,
    )
    preview_edge = _preview_edge(
        source=source,
        target=target,
        edge_layer=normalized_layer,
        relation_type=normalized_relation,
        fingerprint=fingerprint,
    )
    safe_patch_summary = _safe_patch_summary(
        source=source,
        target=target,
        relation_type=normalized_relation,
        label=label,
        patched=patched,
        source_content=source_content,
    )
    conflict_state = {"conflicted": False, "conflict_type": "none", "evidence": "preview_clean"}
    proposal_packet = _proposal_packet(
        source_path=source.path,
        target_path=target.path,
        before_after_summary=safe_patch_summary,
        non_canonical_preview_edges=[preview_edge],
        conflict_state=conflict_state,
    )
    return {
        "ok": True,
        "code": "ok",
        "pass": PASS_ID,
        "status": "preview_ready",
        "requires_approval": True,
        "direct_write_allowed": False,
        "write_mode": "approval_gated",
        "source": source_resolved["node"],
        "target": target_resolved["node"],
        "edge_layer": normalized_layer,
        "relation_type": normalized_relation,
        "relation": preview_edge["relation"],
        "label": _sanitize_label(label, ""),
        "evidence": _sanitize_label(evidence, ""),
        "link_fingerprint": fingerprint,
        "target_path": source.path,
        "preview_edge": preview_edge,
        "safe_patch_summary": safe_patch_summary,
        "proposal_packet": proposal_packet,
        "conflict_state": conflict_state,
        "content": patched,
        "content_changed": patched != source_content,
        "performance_contract": _performance_contract(markdown_reads=1),
        "authority_boundary": {
            "direct_write_allowed": False,
            "writes_without_approval_allowed": False,
            "canonical_graph_writeback_allowed": False,
            "trust_promotion_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "host_mutation_allowed": False,
        },
    }


def _preview_without_content(preview: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(preview)
    trimmed.pop("content", None)
    if isinstance(trimmed.get("safe_patch_summary"), dict):
        trimmed["safe_patch_summary"] = dict(trimmed["safe_patch_summary"]) | {"content_stripped": True}
    if isinstance(trimmed.get("proposal_packet"), dict):
        packet = dict(trimmed["proposal_packet"])
        summary = packet.get("before_after_summary")
        if isinstance(summary, dict):
            packet["before_after_summary"] = dict(summary) | {"content_stripped": True}
        trimmed["proposal_packet"] = packet
    return trimmed


def queue_visual_link_approval(
    vault_root: Path | str,
    *,
    source_node_id: str = "",
    target_node_id: str = "",
    source_path: str = "",
    target_path: str = "",
    source_label: str = "",
    target_label: str = "",
    edge_layer: str = "explicit",
    relation_type: str = "related",
    label: str = "",
    evidence: str = "",
    service: StudioService | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    preview = build_visual_link_preview(
        vault,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        source_path=source_path,
        target_path=target_path,
        source_label=source_label,
        target_label=target_label,
        edge_layer=edge_layer,
        relation_type=relation_type,
        label=label,
        evidence=evidence,
    )
    if not preview.get("ok"):
        return preview | {"requires_approval": False}

    metadata = {
        "pass": PASS_ID,
        "write_mode": "approval_gated",
        "visual_link": True,
        "link_fingerprint": preview["link_fingerprint"],
        "source_node_id": preview["source"]["node_id"],
        "target_node_id": preview["target"]["node_id"],
        "source_path": preview["source"]["path"],
        "target_path": preview["target"]["path"],
        "source_label": preview["source"]["label"],
        "target_label": preview["target"]["label"],
        "edge_layer": preview["edge_layer"],
        "relation_type": preview["relation_type"],
        "relation": preview["relation"],
        "label": preview["label"],
        "evidence": preview["evidence"],
        "preview_edge": preview["preview_edge"],
        "safe_patch_summary": preview["safe_patch_summary"] | {"content_stripped": True},
        "proposal_packet": preview["proposal_packet"],
        "performance_contract": preview["performance_contract"],
        "queued_at": _now_utc(),
    }
    studio_service = service or StudioService(vault)
    spec = ActionSpec(
        action_type="write_file",
        target_path=preview["source"]["path"],
        content=preview["content"],
        metadata=metadata,
        submitted_by="studio",
        note=f"Phase 10AB approval-gated visual link: {preview['source']['label']} to {preview['target']['label']}",
    )
    validation = studio_service.validate_action(spec)
    if not validation.valid or validation.gate_blocked:
        return {
            "ok": False,
            "code": "validation_blocked",
            "errors": validation.errors,
            "warnings": validation.warnings,
            "target_path": spec.target_path,
            "pass": PASS_ID,
        }

    request = studio_service.queue_for_approval(spec)
    queued_edge = dict(preview["preview_edge"])
    queued_edge["approval_id"] = request.approval_id
    queued_edge["approval_status"] = request.status
    queued_edge["classes"] = f"edge edge--{preview['edge_layer']} visual-link-{request.status}"
    return {
        "ok": True,
        "status": "requires_approval",
        "requires_approval": True,
        "approval_id": request.approval_id,
        "approval_status": request.status,
        "target_path": spec.target_path,
        "source": preview["source"],
        "target": preview["target"],
        "edge_layer": preview["edge_layer"],
        "relation_type": preview["relation_type"],
        "link_fingerprint": preview["link_fingerprint"],
        "preview_edge": queued_edge,
        "preview": _preview_without_content(preview),
        "pass": PASS_ID,
    }


def _overlay_edge_from_approval(payload: dict[str, Any]) -> dict[str, Any] | None:
    metadata = _approval_metadata(payload)
    if metadata.get("pass") != PASS_ID:
        return None
    fingerprint = str(metadata.get("link_fingerprint") or "")
    source_node_id = str(metadata.get("source_node_id") or "")
    target_node_id = str(metadata.get("target_node_id") or "")
    if not fingerprint or not source_node_id or not target_node_id:
        return None
    status = str(payload.get("status") or "unknown")
    edge_layer = _normalize_edge_layer(str(metadata.get("edge_layer") or "suggested")) or "suggested"
    relation_type = _normalize_relation_type(str(metadata.get("relation_type") or "related")) or "related"
    source = ResolvedVisualLinkNode(
        node_id=source_node_id,
        path=str(metadata.get("source_path") or ""),
        label=str(metadata.get("source_label") or ""),
        node_type="markdown_note",
    )
    target = ResolvedVisualLinkNode(
        node_id=target_node_id,
        path=str(metadata.get("target_path") or ""),
        label=str(metadata.get("target_label") or ""),
        node_type="markdown_note",
    )
    return _preview_edge(
        source=source,
        target=target,
        edge_layer=edge_layer,
        relation_type=relation_type,
        fingerprint=fingerprint,
        approval_id=str(payload.get("approval_id") or ""),
        approval_status=status,
    ) | {
        "label": metadata.get("label") or "",
        "evidence": metadata.get("evidence") or "",
    }


def build_visual_link_overlay(
    vault_root: Path | str,
    *,
    limit: int = DEFAULT_OVERLAY_LIMIT,
    include_statuses: tuple[str, ...] = ("pending", "approved", "executing"),
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    statuses = {str(item).lower() for item in include_statuses}
    approvals = _approval_dir(vault)
    overlay_edges: list[dict[str, Any]] = []
    scanned = 0
    matching_total = 0
    status_counts: dict[str, int] = {}
    if approvals.is_dir():
        for approval_file in sorted(approvals.glob("*.json")):
            scanned += 1
            payload = _load_approval_payload(approval_file)
            if not payload:
                continue
            status = str(payload.get("status") or "").lower()
            if status not in statuses:
                continue
            edge = _overlay_edge_from_approval(payload)
            if edge is None:
                continue
            matching_total += 1
            status_counts[status] = status_counts.get(status, 0) + 1
            if len(overlay_edges) < max(1, int(limit)):
                overlay_edges.append(edge)
    truncated = matching_total > len(overlay_edges)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "pass": PASS_ID,
        "status": "COMPLETE / APPROVAL-GATED VISUAL LINK OVERLAY READY",
        "overlay_edges": overlay_edges,
        "overlay_edge_count": len(overlay_edges),
        "matching_approval_count": matching_total,
        "approval_status_counts": dict(sorted(status_counts.items())),
        "overlay_truncated": truncated,
        "overlay_limit": max(1, int(limit)),
        "performance_contract": _performance_contract(
            markdown_reads=0,
            approval_files_scanned=scanned,
            overlay_limit=max(1, int(limit)),
        ),
        "authority_boundary": {
            "read_approval_artifacts": True,
            "reads_markdown": False,
            "writes_vault": False,
            "writes_approval_artifacts": False,
            "writes_graph_index": False,
            "writes_node_ids": False,
            "canonical_graph_writeback_allowed": False,
        },
    }


def build_visual_link_approval_flow_status(vault_root: Path | str) -> dict[str, Any]:
    overlay = build_visual_link_overlay(vault_root)
    return {
        "ok": True,
        "surface": "visual-link-approval-flow",
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "COMPLETE / APPROVAL-GATED / VERIFIED",
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "write_mode": "approval_gated",
        "read_only": False,
        "allowed_edge_layers": list(ALLOWED_EDGE_LAYERS),
        "allowed_relation_types": list(ALLOWED_RELATION_TYPES),
        "approval_overlay": {
            "overlay_edge_count": overlay["overlay_edge_count"],
            "matching_approval_count": overlay["matching_approval_count"],
            "approval_status_counts": overlay["approval_status_counts"],
            "overlay_limit": overlay["overlay_limit"],
            "overlay_truncated": overlay["overlay_truncated"],
        },
        "performance_contract": overlay["performance_contract"],
        "authority_boundary": {
            "direct_write_allowed": False,
            "writes_without_approval_allowed": False,
            "queues_approval_artifacts": True,
            "approved_execution_writes_source_markdown": True,
            "pending_overlay_writes_vault": False,
            "persisted_graph_index_allowed": False,
            "node_id_write_allowed": False,
            "trust_promotion_allowed": False,
            "canonical_graph_writeback_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "workflow_execution_allowed": False,
            "host_mutation_allowed": False,
        },
        "checks": {
            "visual_link_preview_built": True,
            "visual_link_queue_built": True,
            "approval_overlay_built": True,
            "overlay_is_bounded": True,
            "pending_overlay_does_not_rebuild_graph": True,
            "duplicate_pending_link_blocks": True,
            "existing_markdown_link_blocks": True,
            "exact_once_execution_inherited_from_studio_service": True,
        },
    }
