"""Read-only source/graph context bridge for the ChaseOS MVP gate.

The bridge proves a narrow claim: a real workflow can reference existing source
workspace/source-package metadata and derived graph context as navigation input
without promoting sources, mutating the graph, writing canonical knowledge,
calling providers, or controlling browsers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.studio.graph_index_contract import build_graph_index_contract


MODEL_VERSION = "chaseos.mvp_source_context_bridge.v1"
SURFACE_ID = "chaseos_mvp_source_context_bridge"
DEFAULT_WORKFLOW_ID = "ventureops_ai_runtime_security_audit"
DEFAULT_SOURCE_WORKSPACE = "phase7-test"
MAX_CONTEXT_REFS = 5


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _rel(root: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    raw = str(path).strip()
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        return raw.replace("\\", "/").lstrip("./")
    try:
        return candidate.resolve().relative_to(root).as_posix()
    except (OSError, ValueError):
        return None


def _path_exists(root: Path, path: str | Path | None) -> bool:
    rel = _rel(root, path)
    if not rel:
        return False
    return (root / rel).exists()


def _extract_manifest_list(text: str, key: str) -> list[str]:
    values: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == f"{key}:":
            in_section = True
            continue
        if in_section:
            if not line.startswith((" ", "\t", "-")) and not stripped.startswith("-"):
                break
            if stripped.startswith("-"):
                value = stripped[1:].strip().strip("\"'")
                if value:
                    values.append(value)
    return values


def _source_context_refs(root: Path, workspace: dict[str, Any]) -> list[dict[str, Any]]:
    refs = workspace.get("source_refs") if isinstance(workspace.get("source_refs"), dict) else {}
    items: list[dict[str, Any]] = []
    for source_id, ref in sorted(refs.items()):
        if not isinstance(ref, dict):
            continue
        package_path = _rel(root, ref.get("source_package_path"))
        origin_path = _rel(root, ref.get("origin_path"))
        items.append(
            {
                "source_package_id": str(ref.get("source_package_id") or source_id),
                "title": ref.get("title"),
                "source_type": ref.get("source_type"),
                "source_package_path": package_path,
                "source_package_exists": _path_exists(root, package_path),
                "origin_path": origin_path,
                "origin_path_inside_repo": origin_path is not None,
                "extraction_status": ref.get("extraction_status"),
                "embedding_status": ref.get("embedding_status"),
                "user_trust_level": ref.get("user_trust_level"),
                "context_use": "read-only-reference",
                "promotion_allowed": False,
                "canonical_write_allowed": False,
            }
        )
        if len(items) >= MAX_CONTEXT_REFS:
            break
    return items


def _graph_context_refs(root: Path, workflow_required_reads: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    graph = build_graph_index_contract(
        str(root),
        folder_path="06_AGENTS",
        max_files=1000,
        max_bytes_per_file=262144,
        max_nodes=1200,
        max_edges=1800,
    )
    nodes = ((graph.get("graph") or {}).get("nodes") or []) if isinstance(graph, dict) else []
    by_path: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
        path = str(props.get("path") or "").replace("\\", "/").lstrip("./")
        if path:
            by_path[path] = node
            by_path[f"06_AGENTS/{path}"] = node

    refs: list[dict[str, Any]] = []
    for read_path in workflow_required_reads:
        if not read_path.startswith("06_AGENTS/"):
            continue
        node = by_path.get(read_path) or by_path.get(read_path.removeprefix("06_AGENTS/"))
        refs.append(
            {
                "required_read_path": read_path,
                "graph_node_resolved": node is not None,
                "node_id": node.get("id") if isinstance(node, dict) else None,
                "node_type": node.get("node_type") if isinstance(node, dict) else None,
                "node_family": node.get("node_family") if isinstance(node, dict) else None,
                "context_use": "read-only-navigation",
                "graph_write_allowed": False,
                "canonical_write_allowed": False,
            }
        )
    return graph, refs


def build_mvp_source_context_bridge(
    vault_root: str | Path = ".",
    *,
    workflow_id: str = DEFAULT_WORKFLOW_ID,
    workspace_slug: str = DEFAULT_SOURCE_WORKSPACE,
) -> dict[str, Any]:
    """Build a no-write proof packet for MVP graph/source context use."""

    root = Path(vault_root).resolve()
    workflow_manifest_path = root / "runtime" / "workflows" / "registry" / f"{workflow_id}.yaml"
    workflow_manifest = _read_text(workflow_manifest_path)
    workflow_required_reads = _extract_manifest_list(workflow_manifest, "required_reads")

    workspace_path = root / "runtime" / "source_intelligence" / "workspaces" / workspace_slug / "workspace.json"
    workspace = _read_json(workspace_path, {})
    if not isinstance(workspace, dict):
        workspace = {}

    source_refs = _source_context_refs(root, workspace)
    graph_contract, graph_refs = _graph_context_refs(root, workflow_required_reads)

    source_available = bool(source_refs)
    graph_available = bool(graph_refs) and all(ref.get("graph_node_resolved") for ref in graph_refs)
    workflow_present = bool(workflow_manifest)
    mutation_blocked = True

    blockers: list[str] = []
    if not workflow_present:
        blockers.append("workflow_manifest_missing")
    if not source_available:
        blockers.append("source_workspace_refs_missing")
    if not graph_available:
        blockers.append("graph_context_refs_unresolved")

    status = "ready_for_read_only_workflow_context_reference" if not blockers else "partial_or_blocked"

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "workflow": {
            "workflow_id": workflow_id,
            "manifest_path": _rel(root, workflow_manifest_path),
            "manifest_present": workflow_present,
            "required_reads": workflow_required_reads,
            "required_read_count": len(workflow_required_reads),
        },
        "source_context": {
            "workspace_slug": workspace_slug,
            "workspace_path": _rel(root, workspace_path),
            "workspace_present": bool(workspace),
            "workspace_status": workspace.get("status"),
            "source_count": workspace.get("source_count"),
            "index_status": workspace.get("index_status"),
            "query_scope": workspace.get("query_scope"),
            "references": source_refs,
            "reference_count": len(source_refs),
            "source_context_available": source_available,
        },
        "graph_context": {
            "graph_contract_surface": graph_contract.get("surface"),
            "graph_contract_status": graph_contract.get("status"),
            "graph_contract_read_only": bool((graph_contract.get("authority") or {}).get("read_only")),
            "bounded_node_count": len(((graph_contract.get("graph") or {}).get("nodes") or [])),
            "bounded_edge_count": len(((graph_contract.get("graph") or {}).get("edges") or [])),
            "references": graph_refs,
            "reference_count": len(graph_refs),
            "resolved_reference_count": sum(1 for ref in graph_refs if ref.get("graph_node_resolved")),
            "graph_context_available": graph_available,
        },
        "workflow_context": {
            "workflow_can_reference_source_context": workflow_present and source_available,
            "workflow_can_reference_graph_context": workflow_present and graph_available,
            "workflow_can_reference_context_without_mutation": workflow_present
            and source_available
            and graph_available
            and mutation_blocked,
        },
        "authority": {
            "read_only": True,
            "source_package_promotion_allowed": False,
            "canonical_source_write_allowed": False,
            "graph_mutation_allowed": False,
            "graph_index_write_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": blockers,
        "evidence_refs": [
            ref
            for ref in [
                _rel(root, workflow_manifest_path),
                _rel(root, workspace_path),
                "runtime/studio/graph_index_contract.py",
                "runtime/source_intelligence/workspaces/workspace_manager.py",
            ]
            if ref
        ],
    }
