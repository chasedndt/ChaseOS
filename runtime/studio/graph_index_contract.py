"""Read-only Studio graph index contract.

This module derives a bounded, rebuildable graph model from the markdown scan
contract. It provides deterministic node and edge identities for future Studio
graph and node-inspector work, but it does not persist a graph index, write node
IDs into files, mutate opened folders, execute workflows, call providers, or
write canonical state.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from runtime.studio.graph_view_browser_qa import (
    STATIC_GRAPH_BROWSER_QA_PASS,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)
from runtime.graph.store.identity import (
    annotate_studio_graph_nodes,
    identity_annotation_summary,
    load_node_identity_registry,
)
from runtime.studio.graph_scanner_parser import build_graph_scanner_parser


MODEL_VERSION = "studio.graph_index_contract.v1"
SURFACE_ID = "studio_graph_index_contract"

DEFAULT_MAX_NODES = 500
DEFAULT_MAX_EDGES = 1000
MAX_SAMPLE_ITEMS = 12


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_positive_int(value: int | None, default: int) -> int:
    if value is None:
        return default
    return max(1, int(value))


def _digest(*parts: object, length: int = 18) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def _node_id(node_type: str, stable_key: str) -> str:
    return f"studio:{node_type}:{_digest(node_type, stable_key)}"


def _edge_id(relation: str, source_id: str, target_id: str, stable_key: str) -> str:
    return f"studio:edge:{_digest(relation, source_id, target_id, stable_key)}"


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _normalize_link_target(target: str) -> str:
    stripped = target.split("|", 1)[0].split("#", 1)[0].strip()
    return unquote(stripped).replace("\\", "/").lstrip("./")


def _file_label(path: str) -> str:
    name = PurePosixPath(path).name
    return name[:-3] if name.lower().endswith(".md") else name


def _file_node_type(path: str, open_folder_mode: str | None) -> str:
    normalized = _normalize_path(path)
    if normalized.startswith("07_LOGS/Build-Logs/"):
        return "build_log"
    if normalized.startswith("99_ARCHIVE/Documentation-History/"):
        return "documentation_history_note"
    if normalized.startswith("07_LOGS/Daily/"):
        return "daily_note"
    if normalized.startswith("06_AGENTS/"):
        return "agent_control_doc"
    if normalized.startswith("00_HOME/"):
        return "home_doc"
    if normalized.startswith("01_PROJECTS/"):
        return "project_doc"
    if normalized.startswith("02_KNOWLEDGE/"):
        return "knowledge_doc"
    if normalized in {"README.md", "PROJECT_FOUNDATION.md", "ROADMAP.md"}:
        return "system_root_doc"
    if open_folder_mode == "chaseos_native_detected":
        return "chaseos_markdown_doc"
    return "markdown_note"


def _is_external_target(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme and re.match(r"^[A-Za-z][A-Za-z0-9+.-]*$", parsed.scheme))


def _local_link_candidates(source_path: str, target: str) -> list[str]:
    normalized_target = _normalize_link_target(target)
    if not normalized_target:
        return []
    candidates = [normalized_target]
    source_parent = PurePosixPath(_normalize_path(source_path)).parent
    if str(source_parent) != ".":
        candidates.append((source_parent / normalized_target).as_posix())
    if not normalized_target.lower().endswith(".md"):
        candidates.append(f"{normalized_target}.md")
        if str(source_parent) != ".":
            candidates.append((source_parent / f"{normalized_target}.md").as_posix())
    deduped: list[str] = []
    for candidate in candidates:
        clean = _normalize_path(candidate)
        if clean not in deduped:
            deduped.append(clean)
    return deduped


def _make_node(
    *,
    node_type: str,
    stable_key: str,
    label: str,
    confidence: str,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": _node_id(node_type, stable_key),
        "node_type": node_type,
        "label": label[:180],
        "stable_key": stable_key,
        "confidence": confidence,
        "source": "derived_from_markdown_scan_contract",
        "properties": properties or {},
    }


def _make_edge(
    *,
    relation: str,
    source_id: str,
    target_id: str,
    stable_key: str,
    confidence: str,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": _edge_id(relation, source_id, target_id, stable_key),
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "stable_key": stable_key,
        "confidence": confidence,
        "source_contract": "studio_markdown_scan_contract",
        "properties": properties or {},
    }


def _add_node(
    nodes_by_id: dict[str, dict[str, Any]],
    node: dict[str, Any],
    *,
    max_nodes: int,
    warnings: list[str],
) -> bool:
    if node["id"] in nodes_by_id:
        return True
    if len(nodes_by_id) >= max_nodes:
        if "graph-node-output-limit-reached" not in warnings:
            warnings.append("graph-node-output-limit-reached")
        return False
    nodes_by_id[node["id"]] = node
    return True


def _add_edge(
    edges_by_id: dict[str, dict[str, Any]],
    edge: dict[str, Any],
    *,
    max_edges: int,
    warnings: list[str],
) -> bool:
    if edge["id"] in edges_by_id:
        return True
    if len(edges_by_id) >= max_edges:
        if "graph-edge-output-limit-reached" not in warnings:
            warnings.append("graph-edge-output-limit-reached")
        return False
    edges_by_id[edge["id"]] = edge
    return True


def _build_file_nodes(
    file_records: list[dict[str, Any]],
    open_folder_mode: str | None,
    *,
    max_nodes: int,
    warnings: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, str]]:
    nodes_by_id: dict[str, dict[str, Any]] = {}
    file_node_by_path: dict[str, str] = {}
    file_node_by_stem: dict[str, str] = {}

    for record in file_records:
        path = _normalize_path(str(record.get("path", "")))
        if not path:
            continue
        label = _file_label(path)
        node_type = _file_node_type(path, open_folder_mode)
        node = _make_node(
            node_type=node_type,
            stable_key=path,
            label=label,
            confidence="direct_file_scan",
            properties={
                "path": path,
                "size_bytes": record.get("size_bytes"),
                "bytes_read": record.get("bytes_read"),
                "truncated": bool(record.get("truncated")),
                "read_error": record.get("read_error"),
            },
        )
        if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
            file_node_by_path[path.lower()] = node["id"]
            stem = PurePosixPath(path).stem.lower()
            file_node_by_stem.setdefault(stem, node["id"])

    return nodes_by_id, file_node_by_path, file_node_by_stem


def _resolve_wikilink_target(
    target: str,
    file_node_by_path: dict[str, str],
    file_node_by_stem: dict[str, str],
) -> str | None:
    normalized = _normalize_link_target(target)
    if not normalized:
        return None
    candidates = [normalized.lower()]
    if not normalized.lower().endswith(".md"):
        candidates.append(f"{normalized.lower()}.md")
    for candidate in candidates:
        if candidate in file_node_by_path:
            return file_node_by_path[candidate]
    return file_node_by_stem.get(PurePosixPath(normalized).stem.lower())


def _resolve_markdown_link_target(
    source_path: str,
    target: str,
    file_node_by_path: dict[str, str],
    file_node_by_stem: dict[str, str],
) -> str | None:
    for candidate in _local_link_candidates(source_path, target):
        lower = candidate.lower()
        if lower in file_node_by_path:
            return file_node_by_path[lower]
        stem_match = file_node_by_stem.get(PurePosixPath(candidate).stem.lower())
        if stem_match:
            return stem_match
    return None


def _derive_graph(
    file_records: list[dict[str, Any]],
    open_folder_mode: str | None,
    *,
    max_nodes: int,
    max_edges: int,
) -> dict[str, Any]:
    warnings: list[str] = []
    nodes_by_id, file_node_by_path, file_node_by_stem = _build_file_nodes(
        file_records,
        open_folder_mode,
        max_nodes=max_nodes,
        warnings=warnings,
    )
    edges_by_id: dict[str, dict[str, Any]] = {}
    unresolved_references: list[dict[str, Any]] = []

    for record in file_records:
        source_path = _normalize_path(str(record.get("path", "")))
        source_id = file_node_by_path.get(source_path.lower())
        if not source_id:
            continue
        signals = record.get("signals") or {}

        for heading in (signals.get("headings") or {}).get("sample", []):
            line = heading.get("line")
            text = str(heading.get("text", ""))
            level = heading.get("level")
            stable_key = f"{source_path}#heading:{line}:{text}"
            node = _make_node(
                node_type="markdown_heading",
                stable_key=stable_key,
                label=text or f"Heading {line}",
                confidence="derived_heading",
                properties={"path": source_path, "line": line, "level": level},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="contains_heading",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=stable_key,
                        confidence="direct_markdown_structure",
                        properties={"line": line, "level": level},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for tag in (signals.get("tags") or {}).get("sample", []):
            tag_text = str(tag)
            stable_key = tag_text.lower()
            node = _make_node(
                node_type="markdown_tag",
                stable_key=stable_key,
                label=f"#{tag_text}",
                confidence="derived_tag",
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="has_tag",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=f"{source_path}#tag:{stable_key}",
                        confidence="direct_markdown_structure",
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        blocks = signals.get("block_candidates") or {}
        for ordinal, task in enumerate(blocks.get("task_sample", []), start=1):
            task_text = str(task)
            stable_key = f"{source_path}#task:{ordinal}:{task_text}"
            node = _make_node(
                node_type="markdown_task",
                stable_key=stable_key,
                label=task_text,
                confidence="derived_task_candidate",
                properties={"path": source_path, "ordinal": ordinal},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="contains_task",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=stable_key,
                        confidence="direct_markdown_structure",
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for block_id in blocks.get("block_id_sample", []):
            block_text = str(block_id)
            stable_key = f"{source_path}#block:{block_text}"
            node = _make_node(
                node_type="obsidian_block_marker",
                stable_key=stable_key,
                label=block_text,
                confidence="derived_block_marker",
                properties={"path": source_path},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="contains_block_marker",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=stable_key,
                        confidence="direct_markdown_structure",
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )

        for target in (signals.get("wikilinks") or {}).get("sample", []):
            target_text = str(target)
            resolved_target_id = _resolve_wikilink_target(
                target_text,
                file_node_by_path,
                file_node_by_stem,
            )
            if resolved_target_id:
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="links_to_note",
                        source_id=source_id,
                        target_id=resolved_target_id,
                        stable_key=f"{source_path}#wikilink:{target_text}",
                        confidence="resolved_wikilink",
                        properties={"raw_target": target_text, "resolved": True},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )
                continue

            normalized = _normalize_link_target(target_text)
            node = _make_node(
                node_type="unresolved_wikilink",
                stable_key=normalized.lower(),
                label=normalized or target_text,
                confidence="unresolved_reference",
                properties={"raw_target": target_text},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="links_to_unresolved_wikilink",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=f"{source_path}#wikilink:{target_text}",
                        confidence="unresolved_wikilink",
                        properties={"raw_target": target_text, "resolved": False},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )
            if len(unresolved_references) < MAX_SAMPLE_ITEMS:
                unresolved_references.append(
                    {"source_path": source_path, "target": target_text, "kind": "wikilink"}
                )

        for link in (signals.get("markdown_links") or {}).get("sample", []):
            target = str(link.get("target", ""))
            link_text = str(link.get("text", ""))
            if _is_external_target(target) or bool(link.get("external")):
                node = _make_node(
                    node_type="external_resource",
                    stable_key=target,
                    label=link_text or target,
                    confidence="external_markdown_link",
                    properties={"target": target},
                )
                if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                    _add_edge(
                        edges_by_id,
                        _make_edge(
                            relation="links_to_external_resource",
                            source_id=source_id,
                            target_id=node["id"],
                            stable_key=f"{source_path}#markdown-link:{target}",
                            confidence="direct_markdown_link",
                            properties={"text": link_text, "target": target},
                        ),
                        max_edges=max_edges,
                        warnings=warnings,
                    )
                continue

            resolved_target_id = _resolve_markdown_link_target(
                source_path,
                target,
                file_node_by_path,
                file_node_by_stem,
            )
            if resolved_target_id:
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="links_to_file",
                        source_id=source_id,
                        target_id=resolved_target_id,
                        stable_key=f"{source_path}#markdown-link:{target}",
                        confidence="resolved_markdown_link",
                        properties={"text": link_text, "raw_target": target, "resolved": True},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )
                continue

            normalized = _normalize_link_target(target)
            node = _make_node(
                node_type="unresolved_markdown_link",
                stable_key=normalized.lower(),
                label=link_text or normalized,
                confidence="unresolved_reference",
                properties={"raw_target": target},
            )
            if _add_node(nodes_by_id, node, max_nodes=max_nodes, warnings=warnings):
                _add_edge(
                    edges_by_id,
                    _make_edge(
                        relation="links_to_unresolved_markdown_link",
                        source_id=source_id,
                        target_id=node["id"],
                        stable_key=f"{source_path}#markdown-link:{target}",
                        confidence="unresolved_markdown_link",
                        properties={"text": link_text, "raw_target": target, "resolved": False},
                    ),
                    max_edges=max_edges,
                    warnings=warnings,
                )
            if len(unresolved_references) < MAX_SAMPLE_ITEMS:
                unresolved_references.append(
                    {"source_path": source_path, "target": target, "kind": "markdown_link"}
                )

    nodes = list(nodes_by_id.values())
    edges = list(edges_by_id.values())
    node_type_counts: dict[str, int] = {}
    relation_counts: dict[str, int] = {}
    for node in nodes:
        node_type = str(node.get("node_type"))
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
    for edge in edges:
        relation = str(edge.get("relation"))
        relation_counts[relation] = relation_counts.get(relation, 0) + 1

    return {
        "nodes": nodes,
        "edges": edges,
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "relation_counts": dict(sorted(relation_counts.items())),
        "unresolved_references": unresolved_references,
        "warnings": warnings,
    }


def build_graph_index_contract(
    vault_root: str,
    folder_path: str | None = None,
    *,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    identity_registry_path: str | Path | None = None,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Return the read-only Phase 10A derived graph index contract."""

    node_limit = _as_positive_int(max_nodes, DEFAULT_MAX_NODES)
    edge_limit = _as_positive_int(max_edges, DEFAULT_MAX_EDGES)
    scan = build_graph_scanner_parser(
        vault_root,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=node_limit,
        max_edges=edge_limit,
    )
    scan_readiness = scan.get("readiness") or {}
    scan_summary = scan.get("parser_summary") or {}
    target = scan.get("target") or {}
    blockers = list(scan_readiness.get("blockers", []))
    warnings = list(scan_readiness.get("warnings", []))
    graph_payload = scan.get("graph_input") or {}
    graph_summary_payload = scan.get("graph_summary") or {}
    graph = {
        "nodes": graph_payload.get("nodes") or [],
        "edges": graph_payload.get("edges") or [],
        "node_type_counts": graph_summary_payload.get("node_type_counts") or {},
        "relation_counts": graph_summary_payload.get("relation_counts") or {},
        "unresolved_references": (scan.get("samples") or {}).get("unresolved_references") or [],
    }
    if "graph-parser-node-output-limit-reached" in warnings and "graph-node-output-limit-reached" not in warnings:
        warnings.append("graph-node-output-limit-reached")
    if "graph-parser-edge-output-limit-reached" in warnings and "graph-edge-output-limit-reached" not in warnings:
        warnings.append("graph-edge-output-limit-reached")
    registry = None
    if identity_registry_path:
        registry_file = Path(identity_registry_path)
        if registry_file.exists():
            registry = load_node_identity_registry(registry_file)
        else:
            warnings.append("identity-registry-path-missing")
    graph["nodes"] = annotate_studio_graph_nodes(
        list(graph["nodes"]),
        registry,
        snapshot_id=snapshot_id,
    )
    identity_registry_summary = identity_annotation_summary(graph["nodes"], registry)
    node_count = len(graph["nodes"])
    edge_count = len(graph["edges"])
    graph_ready = (
        not blockers
        and bool(scan_readiness.get("parser_backed_graph_input_ready"))
        and node_count > 0
    )
    node_inspector_contract_built = (
        Path(str(scan.get("vault_root", ""))) / "runtime/studio/node_inspector_contract.py"
    ).exists()
    graph_view_contract_built = (
        Path(str(scan.get("vault_root", ""))) / "runtime/studio/graph_view_contract.py"
    ).exists()
    static_graph_renderer_built = (
        Path(str(scan.get("vault_root", ""))) / "runtime/studio/graph_view_static_renderer.py"
    ).exists()
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(scan.get("vault_root"))
    next_pass = (
        "phase10aa-controlled-node-create-edit"
        if graph_ready
        else scan_readiness.get("next_recommended_pass")
    )

    return {
        "ok": graph_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Graph Index Contract",
        "phase": "Phase 10A - Studio Core Shell",
        "status": "COMPLETE / READ-ONLY PARSER-BACKED GRAPH INDEX INPUT BUILT / PERSISTED GRAPH ENGINE NOT BUILT",
        "vault_root": scan.get("vault_root"),
        "target": target,
        "source_parser": {
            "surface": scan.get("surface"),
            "model_version": scan.get("model_version"),
            "ok": scan.get("ok"),
            "parser_summary": scan_summary,
            "graph_summary": graph_summary_payload,
        },
        "source_scan": {
            "surface": scan.get("surface"),
            "model_version": scan.get("model_version"),
            "ok": scan.get("ok"),
            "scan_limits": scan.get("scan_limits"),
            "scan_summary": scan_summary,
            "open_folder_readiness": scan.get("open_folder_readiness"),
        },
        "graph_limits": {
            "max_nodes": node_limit,
            "max_edges": edge_limit,
            "sample_limit": MAX_SAMPLE_ITEMS,
        },
        "graph_summary": {
            "node_count": node_count,
            "edge_count": edge_count,
            "file_node_count": sum(
                1 for node in graph["nodes"] if str(node.get("node_type", "")).endswith("_doc") or node.get("node_type") in {"markdown_note", "system_root_doc"}
            ),
            "unresolved_reference_count": int(graph_summary_payload.get("unresolved_reference_count", len(graph["unresolved_references"])) or 0),
            "node_output_truncated": "graph-node-output-limit-reached" in warnings,
            "edge_output_truncated": "graph-edge-output-limit-reached" in warnings,
            "node_type_counts": graph["node_type_counts"],
            "node_family_counts": graph_summary_payload.get("node_family_counts") or {},
            "trust_state_counts": graph_summary_payload.get("trust_state_counts") or {},
            "relation_counts": graph["relation_counts"],
            "edge_layer_counts": graph_summary_payload.get("edge_layer_counts") or {},
        },
        "samples": {
            "nodes": graph["nodes"][:MAX_SAMPLE_ITEMS],
            "edges": graph["edges"][:MAX_SAMPLE_ITEMS],
            "unresolved_references": graph["unresolved_references"][:MAX_SAMPLE_ITEMS],
        },
        "graph": {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
        },
        "identity_registry": identity_registry_summary,
        "readiness": {
            "graph_index_contract_ready": graph_ready,
            "markdown_scan_contract_ready": True,
            "graph_scanner_parser_ready": bool(scan_readiness.get("graph_scanner_parser_ready")),
            "parser_backed_graph_input_ready": bool(scan_readiness.get("parser_backed_graph_input_ready")),
            "derived_node_identity_ready": graph_ready,
            "derived_edge_identity_ready": graph_ready,
            "persisted_graph_index_ready": False,
            "node_inspector_contract_ready": node_inspector_contract_built,
            "graph_view_contract_ready": graph_view_contract_built,
            "static_graph_renderer_ready": static_graph_renderer_built,
            "browser_visual_qa_ready": static_graph_browser_qa_built,
            "node_inspector_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "graph_truth": {
            "markdown_scan_contract_built": True,
            "graph_scanner_parser_built": True,
            "parser_backed_graph_input_built": True,
            "derived_graph_index_contract_built": True,
            "deterministic_node_identity_built": graph_ready,
            "deterministic_edge_identity_built": graph_ready,
            "persistent_graph_snapshot_built": False,
            "node_id_writer_built": False,
            "node_inspector_contract_built": node_inspector_contract_built,
            "graph_view_contract_built": graph_view_contract_built,
            "static_graph_renderer_built": static_graph_renderer_built,
            "static_graph_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_built": False,
            "node_inspector_built": False,
            "service_layer_write_path_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "bounded_file_count": (scan.get("scan_limits") or {}).get("max_files"),
            "bounded_bytes_per_file": (scan.get("scan_limits") or {}).get("max_bytes_per_file"),
            "bounded_node_count": node_limit,
            "bounded_edge_count": edge_limit,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "writes_snapshot": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-graph-index-contract"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-graph-index-contract.md",
        ],
    }
