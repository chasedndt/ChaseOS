"""Phase 10F3 read-only general Markdown inference preview.

This surface composes the 10F1 Open Folder compatibility scan, the 10F2
Obsidian detector, and the 10X parser-backed graph input into a preview-only
model for non-canonical workspace onboarding. It infers candidate node/edge
shape, source domains, trust defaults, and migration warnings without writing
sidecar hints, graph indexes, approval artifacts, node IDs, or source files.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_scanner_parser import build_graph_scanner_parser
from runtime.studio.obsidian_vault_detection import build_obsidian_vault_detection
from runtime.studio.open_folder_compatibility_readiness import (
    build_open_folder_compatibility_readiness,
)


MODEL_VERSION = "studio.general_markdown_inference_preview.v1"
SURFACE_ID = "studio_general_markdown_inference_preview"
PASS_ID = "phase10f3-general-markdown-inference-preview"
NEXT_RECOMMENDED_PASS = "phase10f5-upgrade-plan-approval-packet"

DEFAULT_MAX_FILES = 10000
DEFAULT_MAX_NODES = 20000
DEFAULT_MAX_EDGES = 50000
SAMPLE_LIMIT = 50

KNOWN_FRONTMATTER_KEYS = {
    "aliases",
    "alias",
    "created",
    "date",
    "domain",
    "id",
    "project",
    "source",
    "status",
    "summary",
    "tags",
    "title",
    "type",
    "updated",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_target(vault_root: str | Path, folder_path: str | Path | None = None) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    if folder_path is None or str(folder_path).strip() == "":
        return vault, vault
    candidate = Path(folder_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    return vault, candidate.resolve()


def _positive_int(value: int | None, default: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _sample_mapping(mapping: dict[str, int], limit: int = SAMPLE_LIMIT) -> dict[str, int]:
    return dict(sorted(mapping.items(), key=lambda item: (-int(item[1]), item[0]))[:limit])


def _preview_node(node: dict[str, Any]) -> dict[str, Any]:
    props = node.get("properties") or {}
    return {
        "id": node.get("id"),
        "label": node.get("label"),
        "node_type": node.get("node_type"),
        "node_family": node.get("node_family"),
        "confidence": node.get("confidence"),
        "trust_state_default": props.get("trust_state") or "raw",
        "source_domain": props.get("domain") or "unassigned",
        "path": props.get("path"),
        "preview_state": "non_canonical",
    }


def _preview_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": edge.get("id"),
        "source": edge.get("source"),
        "target": edge.get("target"),
        "relation": edge.get("relation"),
        "edge_layer": edge.get("edge_layer"),
        "confidence": edge.get("confidence"),
        "preview_state": "non_canonical",
    }


def _domain_counts(nodes: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for node in nodes:
        props = node.get("properties") or {}
        domain = str(props.get("domain") or "unassigned")
        counts[domain] += 1
    return dict(sorted(counts.items()))


def _trust_defaults_by_type(nodes: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for node in nodes:
        node_type = str(node.get("node_type") or "unknown")
        trust = str((node.get("properties") or {}).get("trust_state") or "raw")
        grouped[node_type][trust] += 1
    return {node_type: dict(sorted(counter.items())) for node_type, counter in sorted(grouped.items())}


def _frontmatter_warnings(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    unknown_key_counts: Counter[str] = Counter()
    malformed_paths: list[str] = []
    for record in files:
        parsed = record.get("parsed") or {}
        frontmatter = parsed.get("frontmatter") or {}
        path = str(record.get("path") or "")
        if frontmatter.get("present") and not frontmatter.get("closed"):
            malformed_paths.append(path)
        for key in frontmatter.get("keys") or []:
            if str(key) not in KNOWN_FRONTMATTER_KEYS:
                unknown_key_counts[str(key)] += 1
    if malformed_paths:
        warnings.append(
            {
                "level": "warn",
                "code": "malformed-frontmatter-preview-only",
                "message": "Some Markdown files have unclosed frontmatter; migration must block or request manual review before writes.",
                "sample": malformed_paths[:SAMPLE_LIMIT],
                "count": len(malformed_paths),
            }
        )
    if unknown_key_counts:
        warnings.append(
            {
                "level": "info",
                "code": "unknown-frontmatter-keys-detected",
                "message": "Unknown frontmatter keys were found and are previewed only; no sidecar hints or canonical metadata are written.",
                "keys": _sample_mapping(dict(unknown_key_counts)),
            }
        )
    return warnings


def _migration_warnings(
    compatibility: dict[str, Any],
    obsidian: dict[str, Any],
    graph: dict[str, Any],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    compatibility_summary = compatibility.get("summary") or {}
    obsidian_summary = obsidian.get("summary") or {}
    graph_summary = graph.get("graph_summary") or {}
    parser_summary = graph.get("parser_summary") or {}
    graph_readiness = graph.get("readiness") or {}

    for blocker in (compatibility.get("readiness") or {}).get("blockers") or []:
        warnings.append(
            {
                "level": "block",
                "code": str(blocker),
                "message": "The selected folder is not ready for general Markdown inference.",
            }
        )
    if compatibility_summary.get("truncated") or parser_summary.get("file_scan_truncated"):
        warnings.append(
            {
                "level": "warn",
                "code": "bounded-scan-truncated",
                "message": "Counts may be partial because a bounded scan limit was reached.",
            }
        )
    if graph_summary.get("unresolved_reference_count"):
        warnings.append(
            {
                "level": "warn",
                "code": "unresolved-markdown-references",
                "message": "Some links could not be resolved to files and remain suggested-only.",
                "count": graph_summary.get("unresolved_reference_count"),
            }
        )
    if obsidian_summary.get("enabled_plugin_count") or obsidian_summary.get("plugin_dir_count"):
        warnings.append(
            {
                "level": "info",
                "code": "obsidian-plugin-state-preview-only",
                "message": "Obsidian plugin state is visible for review only; Studio will not activate, install, or edit plugins.",
            }
        )
    if obsidian_summary.get("canvas_file_count"):
        warnings.append(
            {
                "level": "info",
                "code": "canvas-files-not-canonical",
                "message": "Canvas files are detected as compatibility signals only; canvas import remains deferred.",
                "count": obsidian_summary.get("canvas_file_count"),
            }
        )
    if not graph_readiness.get("parser_backed_graph_input_ready"):
        warnings.append(
            {
                "level": "block" if graph_readiness.get("blockers") else "warn",
                "code": "parser-backed-graph-input-not-ready",
                "message": "Parser-backed graph input is not ready, so inference cannot become a usable migration preview.",
            }
        )
    warnings.extend(_frontmatter_warnings(graph.get("files") or []))

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for warning in warnings:
        key = str(warning.get("code") or warning)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)
    return deduped


def build_general_markdown_inference_preview(
    vault_root: str | Path,
    folder_path: str | Path | None = None,
    *,
    max_files: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
) -> dict[str, Any]:
    """Return a read-only preview of inferred Markdown graph/import shape."""

    file_limit = _positive_int(max_files, DEFAULT_MAX_FILES)
    node_limit = _positive_int(max_nodes, DEFAULT_MAX_NODES)
    edge_limit = _positive_int(max_edges, DEFAULT_MAX_EDGES)
    vault, target = _resolve_target(vault_root, folder_path)

    compatibility = build_open_folder_compatibility_readiness(vault, folder_path=target)
    obsidian = build_obsidian_vault_detection(vault, folder_path=target)
    graph = build_graph_scanner_parser(
        vault,
        folder_path=target,
        max_files=file_limit,
        max_nodes=node_limit,
        max_edges=edge_limit,
    )

    graph_input = graph.get("graph_input") or {}
    nodes = list(graph_input.get("nodes") or [])
    edges = list(graph_input.get("edges") or [])
    graph_summary = graph.get("graph_summary") or {}
    parser_summary = graph.get("parser_summary") or {}
    migration_warnings = _migration_warnings(compatibility, obsidian, graph)
    blockers = [str(item.get("code")) for item in migration_warnings if item.get("level") == "block"]
    preview_ready = not blockers and bool(nodes) and bool((graph.get("readiness") or {}).get("parser_backed_graph_input_ready"))
    compatibility_summary = compatibility.get("summary") or {}
    obsidian_summary = obsidian.get("summary") or {}

    candidate_node_types = dict(sorted((graph_summary.get("node_type_counts") or {}).items()))
    candidate_node_families = dict(sorted((graph_summary.get("node_family_counts") or {}).items()))
    candidate_edge_types = dict(sorted((graph_summary.get("relation_counts") or {}).items()))
    candidate_edge_layers = dict(sorted((graph_summary.get("edge_layer_counts") or {}).items()))
    source_domains = _domain_counts(nodes)
    trust_defaults = _trust_defaults_by_type(nodes)

    return {
        "ok": preview_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "COMPLETE / READ-ONLY / VERIFIED" if preview_ready else "BLOCKED / READ-ONLY PREVIEW NOT READY",
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio General Markdown Inference Preview",
        "vault_root": str(vault),
        "target": {
            "requested_path": str(folder_path) if folder_path is not None else None,
            "resolved_path": str(target),
            "exists": target.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
            "compatibility_mode": compatibility_summary.get("mode"),
            "obsidian_classification": obsidian_summary.get("classification"),
        },
        "summary": {
            "preview_ready": preview_ready,
            "preview_only": True,
            "non_canonical": True,
            "markdown_file_count": parser_summary.get("scanned_file_count") or compatibility_summary.get("markdown_file_count", 0),
            "candidate_node_count": len(nodes),
            "candidate_edge_count": len(edges),
            "candidate_node_type_count": len(candidate_node_types),
            "candidate_node_family_count": len(candidate_node_families),
            "candidate_edge_type_count": len(candidate_edge_types),
            "candidate_edge_layer_count": len(candidate_edge_layers),
            "source_domain_count": len(source_domains),
            "migration_warning_count": len(migration_warnings),
            "bounded_scan_truncated": bool(
                compatibility_summary.get("truncated")
                or parser_summary.get("file_scan_truncated")
                or graph_summary.get("node_output_truncated")
                or graph_summary.get("edge_output_truncated")
            ),
        },
        "candidate_model": {
            "candidate_node_type_counts": candidate_node_types,
            "candidate_node_family_counts": candidate_node_families,
            "candidate_edge_type_counts": candidate_edge_types,
            "candidate_edge_layer_counts": candidate_edge_layers,
            "source_domain_counts": source_domains,
            "trust_state_defaults_by_node_type": trust_defaults,
            "trust_state_counts": dict(sorted((graph_summary.get("trust_state_counts") or {}).items())),
        },
        "preview_graph": {
            "schema_version": "studio.general_markdown_inference_preview.v1",
            "preview_only": True,
            "non_canonical": True,
            "nodes": [_preview_node(node) for node in nodes[:SAMPLE_LIMIT]],
            "edges": [_preview_edge(edge) for edge in edges[:SAMPLE_LIMIT]],
            "unresolved_references": (graph.get("samples") or {}).get("unresolved_references") or [],
        },
        "migration_warnings": migration_warnings,
        "component_surfaces": {
            "open_folder_compatibility_readiness": {
                "ok": compatibility.get("ok"),
                "surface": compatibility.get("surface"),
                "mode": compatibility_summary.get("mode"),
            },
            "obsidian_vault_detection": {
                "ok": obsidian.get("ok"),
                "surface": obsidian.get("surface"),
                "classification": obsidian_summary.get("classification"),
            },
            "graph_scanner_parser": {
                "ok": graph.get("ok"),
                "surface": graph.get("surface"),
                "parser_backed_graph_input_ready": (graph.get("readiness") or {}).get("parser_backed_graph_input_ready"),
            },
        },
        "readiness": {
            "ok": preview_ready,
            "general_markdown_inference_preview_ready": preview_ready,
            "parser_backed_graph_input_ready": bool((graph.get("readiness") or {}).get("parser_backed_graph_input_ready")),
            "preview_non_canonical": True,
            "sidecar_hint_writer_built": False,
            "migration_approval_packet_required": True,
            "upgrade_execution_available": False,
            "blockers": blockers,
            "warnings": [str(item.get("code")) for item in migration_warnings if item.get("level") != "block"],
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if preview_ready else PASS_ID,
        },
        "performance_contract": {
            "bounded_scan": True,
            "uses_parser_backed_graph_input": True,
            "persists_graph_index": False,
            "writes_preview_cache": False,
            "returns_counts_and_samples": True,
            "max_files": file_limit,
            "max_nodes": node_limit,
            "max_edges": edge_limit,
            "sample_limit": SAMPLE_LIMIT,
        },
        "authority_boundary": {
            "read_only": True,
            "preview_only": True,
            "non_canonical": True,
            "writes_selected_folder": False,
            "writes_vault": False,
            "writes_vault_source_files": False,
            "writes_sidecar_hints": False,
            "writes_graph_index": False,
            "writes_node_ids": False,
            "writes_approval_artifacts": False,
            "migration_writer_built": False,
            "upgrade_executor_built": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "workflow_execution_allowed": False,
            "agent_bus_writes_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "allowed_actions": ["inspect-general-markdown-inference-preview"],
        "possible_writes": [],
        "future_passes": [
            "10F5-upgrade-plan-approval-packet",
            "10F6-approved-upgrade-execution-proof",
        ],
    }
