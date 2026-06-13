"""Read-only graph-node provenance inspector for ChaseOS Studio."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_index_contract import build_graph_index_contract
from runtime.studio.provenance import inspect_provenance


MODEL_VERSION = "studio.graph_provenance_inspector.v1"
SURFACE_ID = "studio_graph_provenance_inspector"
NEXT_RECOMMENDED_PASS = "phase10aa-controlled-node-create-edit"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_rel(path: str | Path | None) -> str:
    if path is None:
        return ""
    value = str(path).strip().replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    return value


def _relative_to_vault(vault: Path, path: Path | str | None) -> str | None:
    if path is None:
        return None
    try:
        resolved = Path(path).resolve()
        return resolved.relative_to(vault.resolve()).as_posix()
    except (OSError, ValueError):
        return str(path)


def _resolve_node_path(
    vault: Path,
    selected_node: dict[str, Any],
    *,
    target_root: Path | None = None,
) -> tuple[Path | None, str | None]:
    props = selected_node.get("properties") or {}
    raw_path = props.get("path") or selected_node.get("path") or selected_node.get("file_path")
    if not raw_path:
        stable_key = selected_node.get("stable_key")
        if stable_key and not str(stable_key).startswith(("http://", "https://")):
            raw_path = str(stable_key).split("#", 1)[0]
    if not raw_path:
        return None, "graph-node-has-no-file-path"

    target = Path(str(raw_path))
    if not target.is_absolute():
        vault_candidate = vault / target
        target_candidate = (target_root / target) if target_root is not None else vault_candidate
        target = vault_candidate if vault_candidate.exists() or target_root is None else target_candidate
    try:
        resolved = target.resolve()
        resolved.relative_to(vault.resolve())
    except (OSError, ValueError):
        return None, "graph-node-path-outside-vault"
    return resolved, None


def _find_node(
    nodes: list[dict[str, Any]],
    *,
    node_id: str | None,
    path: str | Path | None,
) -> dict[str, Any] | None:
    wanted_id = str(node_id).strip() if node_id else ""
    wanted_path = _normalize_rel(path)
    for node in nodes:
        props = node.get("properties") or {}
        stable_key = _normalize_rel(node.get("stable_key"))
        node_path = _normalize_rel(props.get("path") or node.get("path") or node.get("file_path"))
        if wanted_id and node.get("id") == wanted_id:
            return node
        if wanted_path and (
            wanted_path in {node_path, stable_key}
            or (node_path and wanted_path.endswith("/" + node_path))
            or (stable_key and wanted_path.endswith("/" + stable_key))
            or (wanted_path and node_path.endswith("/" + wanted_path))
            or (wanted_path and stable_key.endswith("/" + wanted_path))
        ):
            return node
    if not wanted_id and not wanted_path:
        for node in nodes:
            props = node.get("properties") or {}
            if props.get("path") or node.get("path") or node.get("file_path"):
                return node
    return None


def _chain_value(chain: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = chain.get(key)
        if value not in (None, ""):
            return value
    return None


def _section_status(values: dict[str, Any]) -> str:
    return "present" if any(value not in (None, "", [], {}) for value in values.values()) else "missing"


def _build_sections(
    *,
    vault: Path,
    selected_node: dict[str, Any],
    target_path: Path | None,
    provenance: dict[str, Any],
    provenance_status: str,
) -> dict[str, Any]:
    props = selected_node.get("properties") or {}
    chain = provenance.get("chain") or {}
    graph = {
        "status": "resolved",
        "node_id": selected_node.get("id"),
        "label": selected_node.get("label") or selected_node.get("title"),
        "node_type": selected_node.get("node_type"),
        "node_family": selected_node.get("node_family"),
        "stable_key": selected_node.get("stable_key"),
        "source": selected_node.get("source"),
        "confidence": selected_node.get("confidence"),
        "path": _relative_to_vault(vault, target_path) if target_path else _normalize_rel(props.get("path")),
        "trust_state": props.get("trust_state") or selected_node.get("trust_state") or provenance.get("trust_state"),
        "domain": props.get("domain") or selected_node.get("domain"),
        "project": props.get("project") or selected_node.get("project"),
    }
    capture = {
        "status": provenance_status if provenance_status != "present" else "present",
        "capture_id": _chain_value(chain, "capture_id"),
        "captured_at": _chain_value(chain, "captured_at"),
        "capture_method": _chain_value(chain, "capture_method"),
        "source_platform": _chain_value(chain, "source_platform"),
        "source_url": _chain_value(chain, "source_url"),
        "author": _chain_value(chain, "author"),
        "title": _chain_value(chain, "title"),
        "content_sha256": _chain_value(chain, "content_sha256"),
    }
    if provenance_status == "present":
        capture["status"] = _section_status(capture)

    quarantine = {
        "status": provenance_status if provenance_status != "present" else "present",
        "input_class": _chain_value(chain, "input_class"),
        "quarantine_status": _chain_value(chain, "quarantine_status"),
        "injection_scan": provenance.get("injection_scan") or _chain_value(chain, "injection_scan"),
        "original_name": _chain_value(chain, "original_name"),
        "original_path_or_uri": _chain_value(chain, "original_path_or_uri"),
        "detected_mime": _chain_value(chain, "detected_mime"),
        "route_reason": _chain_value(chain, "route_reason"),
    }
    if provenance_status == "present":
        quarantine["status"] = _section_status(quarantine)

    promotion = {
        "status": provenance_status if provenance_status != "present" else "present",
        "promotion_status": provenance.get("promotion_status") or _chain_value(chain, "promotion_status"),
        "knowledge_class": _chain_value(chain, "knowledge_class"),
        "source_package_status": _chain_value(chain, "source_package_status"),
        "domain_hint": _chain_value(chain, "domain_hint"),
        "project_hint": _chain_value(chain, "project_hint"),
        "topic_hint": _chain_value(chain, "topic_hint"),
        "workspace_hint": _chain_value(chain, "workspace_hint"),
        "desired_output_kind": _chain_value(chain, "desired_output_kind"),
    }
    if provenance_status == "present":
        promotion["status"] = _section_status(promotion)

    content_state = {
        "status": "resolved",
        "graph_trust_state": graph.get("trust_state"),
        "provenance_trust_state": provenance.get("trust_state"),
        "generated": bool(props.get("generated") or str(graph.get("trust_state")) == "generated"),
        "canonical": bool(props.get("canonical") or str(graph.get("trust_state")) == "canonical"),
        "generated_canonical_distinction": (
            "generated"
            if bool(props.get("generated") or str(graph.get("trust_state")) == "generated")
            else "canonical"
            if bool(props.get("canonical") or str(graph.get("trust_state")) == "canonical")
            else "neither"
        ),
    }
    dedup = {
        "status": "present" if provenance.get("dedup_status") not in (None, "", "unknown") else "missing",
        "dedup_status": provenance.get("dedup_status"),
        "dedup_entry": provenance.get("dedup_entry"),
    }
    audit = {
        "status": provenance_status,
        "file_path": _relative_to_vault(vault, target_path) if target_path else None,
        "sidecar_path": _relative_to_vault(vault, provenance.get("sidecar_path")),
        "schema_version": provenance.get("schema_version") or _chain_value(chain, "schema_version"),
        "extra_metadata": provenance.get("extra_metadata") or {},
        "error": provenance.get("error"),
    }
    return {
        "graph": graph,
        "capture": capture,
        "quarantine": quarantine,
        "promotion": promotion,
        "content_state": content_state,
        "dedup": dedup,
        "audit": audit,
    }


def _chain_steps(sections: dict[str, Any], provenance_status: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "graph-node",
            "label": "Graph node",
            "state": sections["graph"].get("status", "resolved"),
            "summary": sections["graph"].get("label") or sections["graph"].get("node_id"),
        },
        {
            "id": "sidecar",
            "label": "Sidecar provenance",
            "state": provenance_status,
            "summary": sections["audit"].get("sidecar_path") or sections["audit"].get("error") or "no sidecar",
        },
        {
            "id": "capture",
            "label": "Capture",
            "state": sections["capture"].get("status", "missing"),
            "summary": sections["capture"].get("capture_id") or sections["capture"].get("source_platform"),
        },
        {
            "id": "quarantine",
            "label": "Quarantine",
            "state": sections["quarantine"].get("status", "missing"),
            "summary": sections["quarantine"].get("input_class") or sections["quarantine"].get("injection_scan"),
        },
        {
            "id": "promotion",
            "label": "Promotion",
            "state": sections["promotion"].get("status", "missing"),
            "summary": sections["promotion"].get("promotion_status") or sections["promotion"].get("knowledge_class"),
        },
        {
            "id": "content-state",
            "label": "Generated/canonical",
            "state": sections["content_state"].get("generated_canonical_distinction", "neither"),
            "summary": sections["content_state"].get("graph_trust_state"),
        },
        {
            "id": "dedup-audit",
            "label": "Dedup/audit",
            "state": sections["dedup"].get("dedup_status") or sections["dedup"].get("status", "missing"),
            "summary": sections["audit"].get("schema_version") or sections["audit"].get("file_path"),
        },
    ]


def _status_from_provenance(provenance: dict[str, Any]) -> str:
    if provenance.get("ok") is True:
        return "present"
    error = str(provenance.get("error") or "").lower()
    if "no sidecar found" in error:
        return "missing"
    if "failed to read sidecar" in error:
        return "malformed"
    if "file not found" in error:
        return "file_missing"
    return "missing"


def build_graph_provenance_inspector(
    vault_root: str | Path,
    *,
    node_id: str | None = None,
    path: str | Path | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
) -> dict[str, Any]:
    """Return graph-selected provenance detail without mutating any source."""

    vault = Path(vault_root).resolve()
    graph = build_graph_index_contract(
        vault,
        folder_path=str(folder_path) if folder_path is not None else None,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
    )
    graph_readiness = graph.get("readiness") or {}
    warnings = list(graph_readiness.get("warnings") or [])
    blockers = list(graph_readiness.get("blockers") or [])
    nodes = ((graph.get("graph") or {}).get("nodes") or [])
    selected_node = _find_node(nodes, node_id=node_id, path=path)
    selector = {
        "node_id": node_id,
        "path": _normalize_rel(path),
        "defaulted_to_first_file_node": not bool(node_id or path) and selected_node is not None,
    }

    if not graph.get("ok"):
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "title": "ChaseOS Studio Graph Provenance Inspector",
            "phase": "Phase 10Z - Graph Provenance Inspector",
            "status": "BLOCKED / GRAPH SOURCE CONTRACT NOT READY",
            "vault_root": str(vault),
            "target": graph.get("target"),
            "selector": selector,
            "selected_node": None,
            "provenance_status": "graph_unavailable",
            "chain_sections": {},
            "chain_steps": [],
            "source_contract": {
                "surface": graph.get("surface"),
                "model_version": graph.get("model_version"),
                "ok": graph.get("ok"),
                "readiness": graph_readiness,
            },
            "readiness": {
                "graph_provenance_inspector_ready": False,
                "graph_index_contract_ready": False,
                "graph_node_resolved": False,
                "node_file_path_resolved": False,
                "sidecar_provenance_present": False,
                "missing_provenance_tolerated": False,
                "malformed_sidecar_tolerated": False,
                "blockers": blockers,
                "warnings": warnings,
                "next_recommended_pass": graph_readiness.get("next_recommended_pass"),
            },
            "authority": _authority(),
            "possible_writes": [],
            "allowed_actions": ["inspect-graph-node-provenance"],
        }

    if selected_node is None:
        blockers.append("graph-node-not-found")
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "title": "ChaseOS Studio Graph Provenance Inspector",
            "phase": "Phase 10Z - Graph Provenance Inspector",
            "status": "BLOCKED / GRAPH NODE NOT FOUND",
            "vault_root": str(vault),
            "target": graph.get("target"),
            "selector": selector,
            "selected_node": None,
            "provenance_status": "node_missing",
            "chain_sections": {},
            "chain_steps": [],
            "source_contract": {
                "surface": graph.get("surface"),
                "model_version": graph.get("model_version"),
                "ok": graph.get("ok"),
                "readiness": graph_readiness,
            },
            "readiness": {
                "graph_provenance_inspector_ready": False,
                "graph_index_contract_ready": True,
                "graph_node_resolved": False,
                "node_file_path_resolved": False,
                "sidecar_provenance_present": False,
                "missing_provenance_tolerated": False,
                "malformed_sidecar_tolerated": False,
                "blockers": blockers,
                "warnings": warnings,
                "next_recommended_pass": "select-existing-graph-node",
            },
            "authority": _authority(),
            "possible_writes": [],
            "allowed_actions": ["inspect-graph-node-provenance"],
        }

    target_root_value = ((graph.get("target") or {}).get("resolved_path"))
    target_root = Path(str(target_root_value)).resolve() if target_root_value else vault
    target_path, path_error = _resolve_node_path(vault, selected_node, target_root=target_root)
    if path_error:
        warnings.append(path_error)
        provenance = {"ok": False, "error": path_error}
        provenance_status = "not_applicable"
    else:
        provenance = inspect_provenance(vault, target_path)
        provenance_status = _status_from_provenance(provenance)
        if provenance_status == "missing":
            warnings.append("sidecar-provenance-missing")
        if provenance_status == "malformed":
            warnings.append("sidecar-provenance-malformed")
        if provenance_status == "file_missing":
            warnings.append("target-file-missing")

    sections = _build_sections(
        vault=vault,
        selected_node=selected_node,
        target_path=target_path,
        provenance=provenance,
        provenance_status=provenance_status,
    )
    ready = True
    return {
        "ok": ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Graph Provenance Inspector",
        "phase": "Phase 10Z - Graph Provenance Inspector",
        "status": "COMPLETE / READ-ONLY GRAPH PROVENANCE INSPECTOR BUILT",
        "vault_root": str(vault),
        "target": graph.get("target"),
        "selector": selector,
        "selected_node": selected_node,
        "node_identity": {
            "id": selected_node.get("id"),
            "label": selected_node.get("label"),
            "node_type": selected_node.get("node_type"),
            "node_family": selected_node.get("node_family"),
            "stable_key": selected_node.get("stable_key"),
            "path": _relative_to_vault(vault, target_path) if target_path else None,
        },
        "provenance_status": provenance_status,
        "provenance": provenance,
        "chain_sections": sections,
        "chain_steps": _chain_steps(sections, provenance_status),
        "source_contract": {
            "surface": graph.get("surface"),
            "model_version": graph.get("model_version"),
            "ok": graph.get("ok"),
            "readiness": graph_readiness,
        },
        "readiness": {
            "graph_provenance_inspector_ready": ready,
            "graph_index_contract_ready": bool(graph_readiness.get("graph_index_contract_ready")),
            "parser_backed_graph_input_ready": bool(graph_readiness.get("parser_backed_graph_input_ready")),
            "graph_node_resolved": True,
            "node_file_path_resolved": target_path is not None,
            "sidecar_provenance_present": provenance_status == "present",
            "missing_provenance_tolerated": provenance_status in {"missing", "not_applicable"},
            "malformed_sidecar_tolerated": provenance_status == "malformed",
            "generated_canonical_distinction_available": True,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "graph_provenance_truth": {
            "graph_node_selection_built": True,
            "file_path_resolution_built": True,
            "sidecar_provenance_chain_built": True,
            "missing_provenance_state_built": True,
            "malformed_sidecar_tolerance_built": True,
            "generated_canonical_distinction_built": True,
            "semantic_suggestion_acceptance_built": False,
            "provenance_writeback_built": False,
            "canonical_writeback_built": False,
        },
        "authority": _authority(),
        "possible_writes": [],
        "allowed_actions": ["inspect-graph-node-provenance"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/Phase10-Graph-Write-Structural-Gap-Plan.md",
        ],
    }


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "reads_file_contents": True,
        "reads_sidecar": True,
        "reads_dedup_registry": True,
        "derives_graph_in_memory": True,
        "writes_opened_folder": False,
        "writes_vault": False,
        "writes_sidecar": False,
        "writes_graph_index": False,
        "writes_node_ids": False,
        "writes_trust_state": False,
        "edits_metadata": False,
        "accepts_suggestions": False,
        "promotes_nodes": False,
        "workflow_execution_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_mutation_allowed": False,
    }
