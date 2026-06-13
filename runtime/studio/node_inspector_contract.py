"""Read-only Studio node inspector contract.

This module provides the first bounded node-inspector model over the derived
graph-index contract. It can inspect a selected node by deterministic node id or
file path, include incoming/outgoing edge context, related nodes, and a bounded
source excerpt for file-backed nodes. It does not persist graph state, write
node IDs, mutate files, execute workflows, call providers/connectors, or write
canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_browser_qa import (
    STATIC_GRAPH_BROWSER_QA_PASS,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)
from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.provenance import inspect_provenance


MODEL_VERSION = "studio.node_inspector_contract.v1"
SURFACE_ID = "studio_node_inspector_contract"

DEFAULT_CONTENT_EXCERPT_BYTES = 4096
MAX_RELATED_ITEMS = 24


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_positive_int(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(1, int(value))


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _find_node(
    nodes: list[dict[str, Any]],
    *,
    node_id: str | None,
    path: str | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if node_id:
        for node in nodes:
            if node.get("id") == node_id:
                return node, {"selector_type": "node_id", "selector_value": node_id}
        return None, {"selector_type": "node_id", "selector_value": node_id}

    if path:
        wanted = _normalize_path(path).lower()
        for node in nodes:
            properties = node.get("properties") or {}
            candidates = [
                str(properties.get("path", "")),
                str(node.get("stable_key", "")),
            ]
            if any(_normalize_path(candidate).lower() == wanted for candidate in candidates if candidate):
                return node, {"selector_type": "path", "selector_value": _normalize_path(path)}
        return None, {"selector_type": "path", "selector_value": _normalize_path(path)}

    return None, {"selector_type": "none", "selector_value": None}


def _edge_context(
    node: dict[str, Any],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    node_id = str(node.get("id"))
    node_by_id = {str(item.get("id")): item for item in nodes}
    incoming = [edge for edge in edges if edge.get("target") == node_id]
    outgoing = [edge for edge in edges if edge.get("source") == node_id]
    related_ids: list[str] = []
    for edge in incoming:
        source = str(edge.get("source", ""))
        if source and source not in related_ids:
            related_ids.append(source)
    for edge in outgoing:
        target = str(edge.get("target", ""))
        if target and target not in related_ids:
            related_ids.append(target)
    related_nodes = [
        node_by_id[related_id]
        for related_id in related_ids[:MAX_RELATED_ITEMS]
        if related_id in node_by_id
    ]
    relation_counts: dict[str, int] = {}
    for edge in incoming + outgoing:
        relation = str(edge.get("relation"))
        relation_counts[relation] = relation_counts.get(relation, 0) + 1
    return {
        "incoming_edges": incoming[:MAX_RELATED_ITEMS],
        "outgoing_edges": outgoing[:MAX_RELATED_ITEMS],
        "related_nodes": related_nodes,
        "incoming_edge_count": len(incoming),
        "outgoing_edge_count": len(outgoing),
        "related_node_count": len(related_ids),
        "relation_counts": dict(sorted(relation_counts.items())),
    }


def _safe_source_path(target_root: Path, relative_path: str) -> Path | None:
    if not relative_path:
        return None
    candidate = (target_root / _normalize_path(relative_path)).resolve()
    try:
        candidate.relative_to(target_root.resolve())
    except ValueError:
        return None
    return candidate


def _source_excerpt(
    node: dict[str, Any],
    target: dict[str, Any],
    *,
    excerpt_bytes: int,
) -> dict[str, Any]:
    properties = node.get("properties") or {}
    relative_path = str(properties.get("path") or "")
    if not relative_path:
        return {
            "available": False,
            "reason": "node-has-no-file-path",
            "path": None,
            "bytes_read": 0,
            "truncated": False,
            "text": "",
        }
    resolved_target = target.get("resolved_path")
    if not resolved_target:
        return {
            "available": False,
            "reason": "target-root-unavailable",
            "path": relative_path,
            "bytes_read": 0,
            "truncated": False,
            "text": "",
        }
    source_path = _safe_source_path(Path(str(resolved_target)), relative_path)
    if source_path is None:
        return {
            "available": False,
            "reason": "source-path-outside-target",
            "path": relative_path,
            "bytes_read": 0,
            "truncated": False,
            "text": "",
        }
    if not source_path.exists() or not source_path.is_file():
        return {
            "available": False,
            "reason": "source-file-not-found",
            "path": relative_path,
            "bytes_read": 0,
            "truncated": False,
            "text": "",
        }

    try:
        with source_path.open("rb") as handle:
            raw = handle.read(excerpt_bytes + 1)
    except OSError as exc:
        return {
            "available": False,
            "reason": f"read-error:{exc}",
            "path": relative_path,
            "bytes_read": 0,
            "truncated": False,
            "text": "",
        }

    truncated = len(raw) > excerpt_bytes
    if truncated:
        raw = raw[:excerpt_bytes]
    return {
        "available": True,
        "reason": None,
        "path": relative_path,
        "resolved_path": str(source_path),
        "bytes_read": len(raw),
        "truncated": truncated,
        "text": raw.decode("utf-8", errors="replace"),
    }


def _relative_to_vault(vault: Path, value: str | Path | None) -> str | None:
    if value in (None, ""):
        return None
    try:
        return Path(str(value)).resolve().relative_to(vault.resolve()).as_posix()
    except (OSError, ValueError):
        return str(value)


def _provenance_status(provenance: dict[str, Any]) -> str:
    if provenance.get("ok") is True:
        return "present"
    error = str(provenance.get("error") or "").lower()
    if "no sidecar found" in error:
        return "missing"
    if "failed to read sidecar" in error:
        return "malformed"
    if "file not found" in error:
        return "file_missing"
    return "not_applicable"


def _node_identity(node: dict[str, Any] | None, source_excerpt: dict[str, Any]) -> dict[str, Any] | None:
    if node is None:
        return None
    properties = node.get("properties") or {}
    return {
        "id": node.get("id"),
        "label": node.get("label"),
        "node_type": node.get("node_type"),
        "node_family": node.get("node_family"),
        "stable_key": node.get("stable_key"),
        "path": properties.get("path") or source_excerpt.get("path"),
        "source": node.get("source"),
        "confidence": node.get("confidence"),
    }


def _metadata_evidence(
    vault: Path,
    node: dict[str, Any] | None,
    source_excerpt: dict[str, Any],
) -> dict[str, Any]:
    if node is None:
        return {
            "provenance_summary": {"status": "node-not-selected"},
            "trust_evidence": {
                "graph_trust_state": None,
                "provenance_trust_state": None,
                "metadata_conflict": False,
            },
            "metadata_state": {
                "stale_or_ambiguous_metadata": True,
                "reason": "node-not-selected",
            },
            "warnings": [],
        }

    properties = node.get("properties") or {}
    graph_trust = properties.get("trust_state") or node.get("trust_state")
    resolved_path = source_excerpt.get("resolved_path")
    if not resolved_path:
        return {
            "provenance_summary": {"status": "not_applicable", "error": source_excerpt.get("reason")},
            "trust_evidence": {
                "graph_trust_state": graph_trust,
                "provenance_trust_state": None,
                "metadata_conflict": False,
            },
            "metadata_state": {
                "stale_or_ambiguous_metadata": True,
                "reason": source_excerpt.get("reason") or "source-path-unavailable",
            },
            "warnings": ["node-provenance-unavailable"],
        }

    provenance = inspect_provenance(vault, resolved_path)
    status = _provenance_status(provenance)
    chain = provenance.get("chain") or {}
    provenance_trust = provenance.get("trust_state")
    metadata_conflict = bool(
        graph_trust
        and provenance_trust
        and status == "present"
        and str(graph_trust) != str(provenance_trust)
    )
    warnings: list[str] = []
    if status == "missing":
        warnings.append("sidecar-provenance-missing")
    elif status == "malformed":
        warnings.append("sidecar-provenance-malformed")
    elif status == "file_missing":
        warnings.append("target-file-missing")
    if metadata_conflict:
        warnings.append("metadata-trust-conflict")

    return {
        "provenance_summary": {
            "status": status,
            "capture_id": chain.get("capture_id"),
            "captured_at": chain.get("captured_at"),
            "source_platform": chain.get("source_platform"),
            "content_sha256": chain.get("content_sha256"),
            "injection_scan": provenance.get("injection_scan") or chain.get("injection_scan"),
            "promotion_status": provenance.get("promotion_status") or chain.get("promotion_status"),
            "quarantine_status": chain.get("quarantine_status"),
            "sidecar_path": _relative_to_vault(vault, provenance.get("sidecar_path")),
            "error": provenance.get("error"),
        },
        "trust_evidence": {
            "graph_trust_state": graph_trust,
            "provenance_trust_state": provenance_trust,
            "metadata_conflict": metadata_conflict,
            "dedup_status": provenance.get("dedup_status"),
            "injection_scan": provenance.get("injection_scan"),
            "promotion_status": provenance.get("promotion_status"),
        },
        "metadata_state": {
            "stale_or_ambiguous_metadata": status != "present" or metadata_conflict,
            "reason": "metadata-trust-conflict" if metadata_conflict else status,
        },
        "warnings": warnings,
    }


def build_node_inspector_contract(
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
    """Return the read-only Phase 10A/10B node inspector contract."""

    excerpt_limit = _as_positive_int(content_excerpt_bytes, DEFAULT_CONTENT_EXCERPT_BYTES)
    path_selector = str(path) if path is not None else None
    graph = build_graph_index_contract(
        str(vault_root),
        folder_path=str(folder_path) if folder_path is not None else None,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    graph_readiness = graph.get("readiness") or {}
    blockers = list(graph_readiness.get("blockers", []))
    warnings = list(graph_readiness.get("warnings", []))
    graph_view_contract_built = (
        Path(str(graph.get("vault_root", ""))) / "runtime/studio/graph_view_contract.py"
    ).exists()
    static_graph_renderer_built = (
        Path(str(graph.get("vault_root", ""))) / "runtime/studio/graph_view_static_renderer.py"
    ).exists()
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(graph.get("vault_root"))
    if not node_id and not path_selector:
        blockers.append("node-selector-required")

    nodes = (graph.get("graph") or {}).get("nodes") or []
    edges = (graph.get("graph") or {}).get("edges") or []
    selected_node, selector = _find_node(nodes, node_id=node_id, path=path_selector)
    if selected_node is None and "node-selector-required" not in blockers:
        blockers.append("node-not-found")

    edge_context = (
        _edge_context(selected_node, nodes, edges)
        if selected_node is not None
        else {
            "incoming_edges": [],
            "outgoing_edges": [],
            "related_nodes": [],
            "incoming_edge_count": 0,
            "outgoing_edge_count": 0,
            "related_node_count": 0,
            "relation_counts": {},
        }
    )
    source_excerpt = (
        _source_excerpt(selected_node, graph.get("target") or {}, excerpt_bytes=excerpt_limit)
        if selected_node is not None
        else {
            "available": False,
            "reason": "node-not-selected",
            "path": None,
            "bytes_read": 0,
            "truncated": False,
            "text": "",
        }
    )
    evidence = _metadata_evidence(Path(str(graph.get("vault_root") or vault_root)), selected_node, source_excerpt)
    for warning in evidence.get("warnings", []):
        if warning not in warnings:
            warnings.append(warning)
    inspector_ready = not blockers and selected_node is not None
    next_pass = graph_readiness.get("next_recommended_pass")

    return {
        "ok": inspector_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Node Inspector Contract",
        "phase": "Phase 10A/10B - Studio Core Shell / Graph + Node Model",
        "status": "PARTIAL / READ-ONLY NODE INSPECTOR CONTRACT BUILT / UI NOT BUILT",
        "vault_root": graph.get("vault_root"),
        "target": graph.get("target"),
        "selector": selector,
        "source_graph": {
            "surface": graph.get("surface"),
            "model_version": graph.get("model_version"),
            "ok": graph.get("ok"),
            "graph_limits": graph.get("graph_limits"),
            "graph_summary": graph.get("graph_summary"),
        },
        "selected_node": selected_node,
        "node_identity": _node_identity(selected_node, source_excerpt),
        "edge_context": edge_context,
        "source_excerpt": source_excerpt,
        "provenance_summary": evidence["provenance_summary"],
        "trust_evidence": evidence["trust_evidence"],
        "metadata_state": evidence["metadata_state"],
        "readiness": {
            "node_inspector_contract_ready": inspector_ready,
            "graph_index_contract_ready": bool(graph_readiness.get("graph_index_contract_ready")),
            "graph_scanner_parser_ready": bool(graph_readiness.get("graph_scanner_parser_ready")),
            "parser_backed_graph_input_ready": bool(graph_readiness.get("parser_backed_graph_input_ready")),
            "selected_node_found": selected_node is not None,
            "edge_context_ready": selected_node is not None,
            "source_excerpt_ready": bool(source_excerpt.get("available")),
            "node_identity_ready": selected_node is not None,
            "provenance_evidence_ready": evidence["provenance_summary"].get("status") == "present",
            "missing_provenance_tolerated": evidence["provenance_summary"].get("status") in {"missing", "not_applicable"},
            "malformed_sidecar_tolerated": evidence["provenance_summary"].get("status") == "malformed",
            "metadata_conflict_detected": bool(evidence["trust_evidence"].get("metadata_conflict")),
            "stale_or_ambiguous_metadata_detected": bool(
                evidence["metadata_state"].get("stale_or_ambiguous_metadata")
            ),
            "graph_view_contract_ready": graph_view_contract_built,
            "static_graph_renderer_ready": static_graph_renderer_built,
            "browser_visual_qa_ready": static_graph_browser_qa_built,
            "node_inspector_ui_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "inspector_truth": {
            "graph_scanner_parser_built": True,
            "parser_backed_graph_input_built": bool(graph_readiness.get("parser_backed_graph_input_ready")),
            "graph_index_contract_built": True,
            "node_inspector_contract_built": True,
            "node_detail_contract_built": True,
            "edge_context_contract_built": True,
            "bounded_source_excerpt_built": True,
            "node_identity_summary_built": True,
            "provenance_summary_built": True,
            "trust_evidence_summary_built": True,
            "stale_ambiguous_metadata_state_built": True,
            "graph_view_contract_built": graph_view_contract_built,
            "static_graph_renderer_built": static_graph_renderer_built,
            "static_graph_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_built": False,
            "node_inspector_ui_built": False,
            "node_editing_built": False,
            "service_layer_write_path_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": True,
            "reads_sidecar": True,
            "reads_dedup_registry": True,
            "bounded_file_count": (graph.get("source_scan") or {}).get("scan_limits", {}).get("max_files"),
            "bounded_bytes_per_file": (graph.get("source_scan") or {}).get("scan_limits", {}).get("max_bytes_per_file"),
            "bounded_node_count": (graph.get("graph_limits") or {}).get("max_nodes"),
            "bounded_edge_count": (graph.get("graph_limits") or {}).get("max_edges"),
            "bounded_content_excerpt_bytes": excerpt_limit,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "writes_sidecar": False,
            "writes_trust_state": False,
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
        "allowed_actions": ["inspect-node"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-node-inspector-readonly.md",
        ],
    }
