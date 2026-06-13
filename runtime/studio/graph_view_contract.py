"""Read-only Studio graph view contract.

This module gives Phase 10A/10B a bounded graph-view model over the derived
graph-index contract. It prepares deterministic UI-ready graph payloads,
filters, legends, layout coordinates, and optional focus-node inspector context
without rendering a UI, persisting graph state, writing node IDs, executing
workflows, calling providers/connectors, or mutating canonical state.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_browser_qa import (
    STATIC_GRAPH_BROWSER_QA_PASS,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)
from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.graph_visual_model import (
    NEXT_RECOMMENDED_PASS as GRAPH_VISUAL_NEXT_PASS,
    build_graph_visual_model,
    visual_model_ready,
)
from runtime.studio.node_inspector_contract import build_node_inspector_contract
from runtime.studio.persisted_graph_storage_status import build_persisted_graph_storage_status


MODEL_VERSION = "studio.graph_view_contract.v1"
SURFACE_ID = "studio_graph_view_contract"

DEFAULT_LAYOUT_NODE_LIMIT = 120
DEFAULT_CONTENT_EXCERPT_BYTES = 2048
MAX_SAMPLE_ITEMS = 12


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_positive_int(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(1, int(value))


def _degree_counts(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
    node_ids = {str(node.get("id")) for node in nodes}
    degrees = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in degrees:
            degrees[source] += 1
        if target in degrees:
            degrees[target] += 1
    return degrees


def _visible_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    layout_node_limit: int,
) -> dict[str, Any]:
    visible_nodes = nodes[:layout_node_limit]
    visible_node_ids = {str(node.get("id")) for node in visible_nodes}
    visible_edges = [
        edge
        for edge in edges
        if str(edge.get("source")) in visible_node_ids and str(edge.get("target")) in visible_node_ids
    ]
    degrees = _degree_counts(visible_nodes, visible_edges)
    columns = max(1, math.ceil(math.sqrt(max(1, len(visible_nodes)))))
    layout_nodes: list[dict[str, Any]] = []
    for index, node in enumerate(visible_nodes):
        node_id = str(node.get("id"))
        layout_nodes.append(
            {
                "id": node_id,
                "x": (index % columns) * 180,
                "y": (index // columns) * 130,
                "pinned": False,
                "degree": degrees.get(node_id, 0),
            }
        )
    layout_edges = [
        {
            "id": edge.get("id"),
            "source": edge.get("source"),
            "target": edge.get("target"),
            "relation": edge.get("relation"),
        }
        for edge in visible_edges
    ]
    return {
        "nodes": visible_nodes,
        "edges": visible_edges,
        "layout": {
            "algorithm": "deterministic-grid-v1",
            "node_spacing_x": 180,
            "node_spacing_y": 130,
            "columns": columns,
            "node_positions": layout_nodes,
            "edge_routes": layout_edges,
        },
        "visible_node_count": len(visible_nodes),
        "visible_edge_count": len(visible_edges),
        "node_output_truncated": len(nodes) > len(visible_nodes),
        "edge_output_truncated": len(edges) > len(visible_edges),
    }


def _legend(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [{"id": key, "label": key.replace("_", " "), "count": value} for key, value in sorted(counts.items())]


def _sample_node_identity(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for node in nodes[:MAX_SAMPLE_ITEMS]:
        properties = node.get("properties") or {}
        samples.append(
            {
                "id": node.get("id"),
                "label": node.get("label"),
                "node_type": node.get("node_type"),
                "stable_key": node.get("stable_key"),
                "confidence": node.get("confidence"),
                "source": node.get("source"),
                "path": properties.get("path"),
            }
        )
    return samples


def _sample_relationships(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for edge in edges[:MAX_SAMPLE_ITEMS]:
        properties = edge.get("properties") or {}
        samples.append(
            {
                "id": edge.get("id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "relation": edge.get("relation"),
                "confidence": edge.get("confidence"),
                "edge_layer": edge.get("edge_layer") or properties.get("edge_layer") or "explicit",
                "source_contract": edge.get("source_contract"),
                "resolved": properties.get("resolved"),
            }
        )
    return samples


def _explainability_summary(
    graph: dict[str, Any],
    visible: dict[str, Any],
    visual_overlays: dict[str, Any],
) -> dict[str, Any]:
    """Return read-only graph truth explanation for Studio panels."""

    graph_summary = graph.get("graph_summary") or {}
    graph_limits = graph.get("graph_limits") or {}
    source_parser = graph.get("source_parser") or {}
    source_scan = graph.get("source_scan") or {}
    scan_limits = source_scan.get("scan_limits") or {}
    visual_summary = visual_overlays.get("summary") or {}
    visual_coverage = visual_overlays.get("coverage") or {}
    samples = graph.get("samples") or {}
    return {
        "node_identity": {
            "identity_scope": "derived-studio-view-id",
            "id_scheme": "studio:<node_type>:<sha-prefix>",
            "deterministic_node_identity_ready": bool((graph.get("readiness") or {}).get("derived_node_identity_ready")),
            "canonical_node_id_writer_built": False,
            "visible_node_count": visible["visible_node_count"],
            "source_node_count": graph_summary.get("node_count", 0),
            "sample_nodes": _sample_node_identity(visible["nodes"]),
        },
        "relationship_context": {
            "visible_edge_count": visible["visible_edge_count"],
            "source_edge_count": graph_summary.get("edge_count", 0),
            "relation_counts": graph_summary.get("relation_counts") or {},
            "edge_layer_counts": graph_summary.get("edge_layer_counts") or {},
            "unresolved_reference_count": graph_summary.get("unresolved_reference_count", 0),
            "unresolved_reference_samples": (samples.get("unresolved_references") or [])[:MAX_SAMPLE_ITEMS],
            "sample_edges": _sample_relationships(visible["edges"]),
        },
        "trust_evidence_overlay": {
            "node_family_counts": visual_summary.get("node_family_counts") or {},
            "trust_state_counts": visual_summary.get("trust_state_counts") or {},
            "edge_layer_counts": visual_summary.get("edge_layer_counts") or {},
            "generated_count": visual_summary.get("generated_count", 0),
            "canonical_count": visual_summary.get("canonical_count", 0),
            "generated_vs_canonical_ready": bool(visual_summary.get("generated_vs_canonical_ready")),
            "all_14_node_families_available": bool(visual_coverage.get("all_14_node_families_available")),
            "all_4_edge_layers_available": bool(visual_coverage.get("all_4_edge_layers_available")),
            "all_8_trust_states_available": bool(visual_coverage.get("all_8_trust_states_available")),
        },
        "provenance_summary": {
            "source_contracts": [
                source_parser.get("surface"),
                graph.get("surface"),
                SURFACE_ID,
            ],
            "parser_model_version": source_parser.get("model_version"),
            "graph_model_version": graph.get("model_version"),
            "target": graph.get("target"),
            "scan_limits": scan_limits,
            "graph_limits": graph_limits,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "writes_canonical_graph_state": False,
            "persists_graph_snapshot": False,
            "provenance_note": "Derived from bounded Markdown scanner/parser and graph-index contract; Studio explains graph truth but does not create canonical graph truth.",
        },
    }


def _focus_context(
    vault_root: str | Path,
    *,
    focus_node_id: str | None,
    focus_path: str | Path | None,
    folder_path: str | Path | None,
    max_files: int | None,
    max_bytes_per_file: int | None,
    max_nodes: int | None,
    max_edges: int | None,
    content_excerpt_bytes: int | None,
) -> dict[str, Any]:
    if not focus_node_id and focus_path is None:
        return {
            "requested": False,
            "ok": True,
            "selector": {"selector_type": "none", "selector_value": None},
            "selected_node": None,
            "edge_context": {
                "incoming_edge_count": 0,
                "outgoing_edge_count": 0,
                "related_node_count": 0,
                "relation_counts": {},
            },
            "source_excerpt": {
                "available": False,
                "reason": "focus-not-requested",
                "path": None,
                "bytes_read": 0,
                "truncated": False,
                "text": "",
            },
            "blockers": [],
        }

    inspector = build_node_inspector_contract(
        vault_root,
        node_id=focus_node_id,
        path=focus_path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    readiness = inspector.get("readiness") or {}
    edge_context = inspector.get("edge_context") or {}
    return {
        "requested": True,
        "ok": bool(inspector.get("ok")),
        "selector": inspector.get("selector"),
        "selected_node": inspector.get("selected_node"),
        "edge_context": {
            "incoming_edges": edge_context.get("incoming_edges", [])[:MAX_SAMPLE_ITEMS],
            "outgoing_edges": edge_context.get("outgoing_edges", [])[:MAX_SAMPLE_ITEMS],
            "related_nodes": edge_context.get("related_nodes", [])[:MAX_SAMPLE_ITEMS],
            "incoming_edge_count": edge_context.get("incoming_edge_count", 0),
            "outgoing_edge_count": edge_context.get("outgoing_edge_count", 0),
            "related_node_count": edge_context.get("related_node_count", 0),
            "relation_counts": edge_context.get("relation_counts", {}),
        },
        "source_excerpt": inspector.get("source_excerpt"),
        "blockers": readiness.get("blockers", []),
    }


def build_graph_view_contract(
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
    """Return the read-only Phase 10A/10B graph view contract."""

    layout_limit = _as_positive_int(layout_node_limit, DEFAULT_LAYOUT_NODE_LIMIT)
    excerpt_limit = _as_positive_int(content_excerpt_bytes, DEFAULT_CONTENT_EXCERPT_BYTES)
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
    nodes = (graph.get("graph") or {}).get("nodes") or []
    edges = (graph.get("graph") or {}).get("edges") or []
    visible = _visible_graph(nodes, edges, layout_node_limit=layout_limit)
    if visible["node_output_truncated"] and "graph-view-node-layout-limit-reached" not in warnings:
        warnings.append("graph-view-node-layout-limit-reached")
    if visible["edge_output_truncated"] and "graph-view-edge-layout-limit-reached" not in warnings:
        warnings.append("graph-view-edge-layout-limit-reached")

    focus = _focus_context(
        vault_root,
        focus_node_id=focus_node_id,
        focus_path=focus_path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        content_excerpt_bytes=excerpt_limit,
    )
    if focus["requested"] and not focus["ok"]:
        blockers.extend(f"focus:{item}" for item in focus["blockers"])

    graph_ready = bool(graph_readiness.get("graph_index_contract_ready"))
    view_ready = graph_ready and not blockers and visible["visible_node_count"] > 0
    static_graph_renderer_built = (
        Path(str(graph.get("vault_root", ""))) / "runtime/studio/graph_view_static_renderer.py"
    ).exists()
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(graph.get("vault_root"))
    next_pass = graph_readiness.get("next_recommended_pass")
    graph_summary = graph.get("graph_summary") or {}
    node_type_counts = graph_summary.get("node_type_counts") or {}
    node_family_counts = graph_summary.get("node_family_counts") or {}
    trust_state_counts = graph_summary.get("trust_state_counts") or {}
    relation_counts = graph_summary.get("relation_counts") or {}
    edge_layer_counts = graph_summary.get("edge_layer_counts") or {}
    visual_overlays = build_graph_visual_model(
        visible["nodes"],
        visible["edges"],
        graph_summary=graph_summary,
    )
    visual_ready = visual_model_ready(
        visual_overlays,
        graph_ready=view_ready,
        blockers=blockers,
    )
    if visual_ready:
        next_pass = GRAPH_VISUAL_NEXT_PASS
    explainability = _explainability_summary(graph, visible, visual_overlays)
    persisted_graph_storage = build_persisted_graph_storage_status(vault_root)
    persisted_readiness = persisted_graph_storage.get("readiness") or {}
    persisted_summary = persisted_graph_storage.get("summary") or {}
    persisted_graph_index_ready = bool(persisted_readiness.get("persisted_graph_index_ready"))

    return {
        "ok": view_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Graph View Contract",
        "phase": "Phase 10A/10B - Studio Core Shell / Graph + Node Model",
        "status": (
            "COMPLETE / READ-ONLY GRAPH VIEW CONTRACT BUILT OVER PARSER-BACKED INPUT"
            if static_graph_renderer_built
            else "COMPLETE / READ-ONLY GRAPH VIEW CONTRACT BUILT OVER PARSER-BACKED INPUT / STATIC RENDERER NOT FOUND"
        ),
        "vault_root": graph.get("vault_root"),
        "target": graph.get("target"),
        "source_graph": {
            "surface": graph.get("surface"),
            "model_version": graph.get("model_version"),
            "ok": graph.get("ok"),
            "graph_limits": graph.get("graph_limits"),
            "graph_summary": graph_summary,
        },
        "source_parser": graph.get("source_parser"),
        "view_model": {
            "viewport": {
                "mode": "read-only-derived-graph",
                "layout_node_limit": layout_limit,
                "visible_node_count": visible["visible_node_count"],
                "visible_edge_count": visible["visible_edge_count"],
                "node_output_truncated": visible["node_output_truncated"],
                "edge_output_truncated": visible["edge_output_truncated"],
            },
            "nodes": visible["nodes"],
            "edges": visible["edges"],
            "layout": visible["layout"],
            "filters": {
                "node_type_counts": node_type_counts,
                "node_family_counts": node_family_counts,
                "trust_state_counts": trust_state_counts,
                "relation_counts": relation_counts,
                "edge_layer_counts": edge_layer_counts,
                "available_node_types": sorted(node_type_counts),
                "available_node_families": sorted((visual_overlays.get("summary") or {}).get("node_family_counts") or {}),
                "available_trust_states": sorted((visual_overlays.get("summary") or {}).get("trust_state_counts") or {}),
                "available_relations": sorted(relation_counts),
                "available_edge_layers": sorted((visual_overlays.get("summary") or {}).get("edge_layer_counts") or {}),
            },
            "legend": {
                "node_types": _legend(node_type_counts),
                "node_families": (visual_overlays.get("legend") or {}).get("node_families", []),
                "relations": _legend(relation_counts),
                "edge_layers": (visual_overlays.get("legend") or {}).get("edge_layers", []),
                "trust_states": (visual_overlays.get("legend") or {}).get("trust_states", []),
                "generated_vs_canonical": (visual_overlays.get("legend") or {}).get("generated_vs_canonical", []),
            },
            "visual_overlays": visual_overlays,
            "focus": focus,
        },
        "explainability": explainability,
        "persisted_graph_storage": persisted_graph_storage,
        "readiness": {
            "graph_view_contract_ready": view_ready,
            "graph_index_contract_ready": graph_ready,
            "graph_scanner_parser_ready": bool(graph_readiness.get("graph_scanner_parser_ready")),
            "parser_backed_graph_input_ready": bool(graph_readiness.get("parser_backed_graph_input_ready")),
            "node_inspector_contract_ready": bool(graph_readiness.get("node_inspector_contract_ready")),
            "deterministic_layout_ready": view_ready,
            "typed_graph_trust_overlays_ready": visual_ready,
            "node_visual_renderer_ready": visual_ready,
            "edge_layer_renderer_ready": visual_ready,
            "trust_overlay_renderer_ready": visual_ready,
            "generated_canonical_distinction_ready": bool((visual_overlays.get("summary") or {}).get("generated_vs_canonical_ready")),
            "all_14_node_families_available": bool((visual_overlays.get("coverage") or {}).get("all_14_node_families_available")),
            "all_4_edge_layers_available": bool((visual_overlays.get("coverage") or {}).get("all_4_edge_layers_available")),
            "all_8_trust_states_available": bool((visual_overlays.get("coverage") or {}).get("all_8_trust_states_available")),
            "static_graph_renderer_ready": static_graph_renderer_built,
            "browser_visual_qa_ready": static_graph_browser_qa_built,
            "graph_view_ui_ready": False,
            "persisted_graph_storage_status_ready": bool(persisted_readiness.get("persisted_graph_storage_status_ready")),
            "persisted_graph_index_ready": persisted_graph_index_ready,
            "current_persisted_snapshot_id": persisted_summary.get("current_snapshot_id"),
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "graph_view_truth": {
            "markdown_scan_contract_built": True,
            "graph_scanner_parser_built": True,
            "parser_backed_graph_input_built": bool(graph_readiness.get("parser_backed_graph_input_ready")),
            "graph_index_contract_built": True,
            "node_inspector_contract_built": bool(graph_readiness.get("node_inspector_contract_ready")),
            "graph_view_contract_built": True,
            "deterministic_layout_contract_built": True,
            "typed_node_family_registry_built": True,
            "typed_graph_trust_overlays_built": visual_ready,
            "edge_layer_visual_model_built": visual_ready,
            "trust_state_overlay_model_built": visual_ready,
            "generated_canonical_distinction_built": visual_ready,
            "graph_view_ui_built": False,
            "static_graph_renderer_built": static_graph_renderer_built,
            "static_graph_browser_qa_built": static_graph_browser_qa_built,
            "persistent_graph_snapshot_built": persisted_graph_index_ready,
            "node_id_writer_built": False,
            "node_editing_built": False,
            "service_layer_write_path_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "renders_ui": False,
            "renders_static_artifact": False,
            "starts_servers": False,
            "bounded_file_count": (graph.get("source_scan") or {}).get("scan_limits", {}).get("max_files"),
            "bounded_bytes_per_file": (graph.get("source_scan") or {}).get("scan_limits", {}).get("max_bytes_per_file"),
            "bounded_node_count": (graph.get("graph_limits") or {}).get("max_nodes"),
            "bounded_edge_count": (graph.get("graph_limits") or {}).get("max_edges"),
            "bounded_layout_node_count": layout_limit,
            "bounded_content_excerpt_bytes": excerpt_limit,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "writes_snapshot": False,
            "reads_persisted_graph_snapshot": persisted_graph_index_ready,
            "node_editing_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-graph-view-contract", "inspect-persisted-graph-storage-status"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-graph-view-readonly-contract.md",
        ],
    }
