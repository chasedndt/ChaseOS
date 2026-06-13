"""Read-only Studio typed graph and trust overlay contract."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_contract import build_graph_view_contract
from runtime.studio.graph_visual_model import (
    NEXT_RECOMMENDED_PASS,
    build_graph_visual_model,
    visual_model_ready,
)


MODEL_VERSION = "studio.graph_visual_overlays.v1"
SURFACE_ID = "studio_graph_visual_overlays"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_graph_visual_overlays(
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
    """Return the Phase 10Y visual overlay contract without writes."""

    contract = build_graph_view_contract(
        vault_root,
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
    view = contract.get("view_model") or {}
    nodes = view.get("nodes") or []
    edges = view.get("edges") or []
    source_graph = contract.get("source_graph") or {}
    graph_summary = source_graph.get("graph_summary") or {}
    visual_model = view.get("visual_overlays") or build_graph_visual_model(
        nodes,
        edges,
        graph_summary=graph_summary,
    )
    contract_readiness = contract.get("readiness") or {}
    blockers = list(contract_readiness.get("blockers") or [])
    warnings = list(contract_readiness.get("warnings") or [])
    overlay_ready = visual_model_ready(
        visual_model,
        graph_ready=bool(contract_readiness.get("graph_view_contract_ready")),
        blockers=blockers,
    )
    coverage = visual_model.get("coverage") or {}
    visual_summary = visual_model.get("summary") or {}
    return {
        "ok": overlay_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Typed Graph Trust Overlays",
        "phase": "Phase 10Y - Typed Graph / Trust Overlays",
        "status": (
            "COMPLETE / READ-ONLY TYPED GRAPH TRUST OVERLAYS BUILT"
            if overlay_ready
            else "BLOCKED / TYPED GRAPH TRUST OVERLAYS SOURCE CONTRACT NOT READY"
        ),
        "vault_root": contract.get("vault_root"),
        "target": contract.get("target"),
        "source_contract": {
            "surface": contract.get("surface"),
            "model_version": contract.get("model_version"),
            "ok": contract.get("ok"),
            "readiness": contract_readiness,
        },
        "visual_summary": visual_summary,
        "visual_model": visual_model,
        "readiness": {
            "typed_graph_trust_overlays_ready": overlay_ready,
            "graph_view_contract_ready": bool(contract_readiness.get("graph_view_contract_ready")),
            "parser_backed_graph_input_ready": bool(contract_readiness.get("parser_backed_graph_input_ready")),
            "node_visual_renderer_ready": overlay_ready,
            "edge_layer_renderer_ready": overlay_ready,
            "trust_overlay_renderer_ready": overlay_ready,
            "generated_canonical_distinction_ready": bool(
                visual_summary.get("generated_vs_canonical_ready")
            ),
            "all_14_node_families_available": bool(coverage.get("all_14_node_families_available")),
            "all_4_edge_layers_available": bool(coverage.get("all_4_edge_layers_available")),
            "all_8_trust_states_available": bool(coverage.get("all_8_trust_states_available")),
            "runtime_action_layer_available": bool(coverage.get("runtime_action_layer_available")),
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if overlay_ready else contract_readiness.get("next_recommended_pass"),
        },
        "graph_visual_truth": {
            "markdown_scan_contract_built": True,
            "graph_scanner_parser_built": True,
            "graph_view_contract_built": True,
            "typed_node_family_registry_built": True,
            "typed_node_visual_model_built": overlay_ready,
            "edge_layer_visual_model_built": overlay_ready,
            "trust_state_overlay_model_built": overlay_ready,
            "generated_canonical_distinction_built": overlay_ready,
            "semantic_suggestion_acceptance_built": False,
            "canonical_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "renders_ui": False,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_graph_index": False,
            "writes_node_ids": False,
            "writes_trust_state": False,
            "accepts_suggestions": False,
            "promotes_nodes": False,
            "node_editing_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-typed-graph-trust-overlays"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/Phase10-Graph-Write-Structural-Gap-Plan.md",
        ],
    }
