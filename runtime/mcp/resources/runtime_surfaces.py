"""Curated read-only ARSL Runtime MCP resource."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope
from runtime.runtime_surfaces import (
    RuntimeSurfaceError,
    build_capability_policy_index,
    load_runtime_surface_registry,
    normalize_browser_skill_memory,
    read_route_decision_records,
)


def runtime_surfaces(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    """Return a curated ARSL summary without raw manifests or execution."""

    payload = build_runtime_surfaces_summary(config.vault_root)
    return HandlerResult(
        True,
        payload,
        audit_metadata={"resource": "runtime.surfaces"},
        files_read=_files_read(payload),
        files_written=[],
    )


def chaseos_runtime_surfaces_summary(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    """ChaseOS-named JSON-RPC-safe alias for the ARSL summary resource."""

    result = runtime_surfaces(params, config, envelope)
    result.audit_metadata["resource"] = "chaseos.runtime_surfaces_summary"
    return result


def build_runtime_surfaces_summary(vault_root: Any) -> dict[str, Any]:
    """Build the resource payload using sanitized ARSL views only."""

    try:
        registry = load_runtime_surface_registry(vault_root=vault_root, require_files=True)
        policy_index = build_capability_policy_index(registry)
        registry_status = "available"
        registry_error = None
        surfaces = [_surface_summary(surface) for surface in registry.list_surfaces()]
        capabilities = [
            _capability_summary(record)
            for capability_id in sorted(policy_index)
            for record in policy_index[capability_id]
        ]
    except RuntimeSurfaceError as exc:
        registry_status = "blocked"
        registry_error = str(exc)
        surfaces = []
        capabilities = []

    browser_skill_inventory = normalize_browser_skill_memory(vault_root)
    route_decisions = read_route_decision_records(vault_root=vault_root)

    return {
        "schema_version": 1,
        "resource": "runtime.surfaces",
        "feature_name": "Adaptive Runtime Surface Layer",
        "feature_status": "PARTIAL",
        "registry_status": registry_status,
        "registry_error": registry_error,
        "exposure_policy": {
            "curated_summary_only": True,
            "raw_manifest_exposed": False,
            "route_preview_exposed": False,
            "mcp_tools_exposed": False,
            "execution_performed": False,
            "ledger_written": False,
            "provider_calls_performed": False,
            "browser_control_performed": False,
            "credential_values_visible": False,
            "cookies_visible": False,
            "browser_profile_visible": False,
            "raw_browser_skill_content_visible": False,
        },
        "registry": {
            "surface_count": len(surfaces),
            "capability_count": len({item["capability_id"] for item in capabilities}),
            "policy_record_count": len(capabilities),
            "surfaces": surfaces,
        },
        "capability_policy": {
            "records": capabilities,
        },
        "browser_skill_memory": browser_skill_inventory.summary(),
        "routing_audit": {
            "route_decision_count": len(route_decisions),
            "latest_decisions": [_route_decision_summary(record) for record in route_decisions[-5:]],
        },
    }


def _surface_summary(surface: Any) -> dict[str, Any]:
    return {
        "surface_id": surface.surface_id,
        "display_name": surface.display_name,
        "surface_family": surface.surface_family,
        "surface_type": surface.surface_type,
        "owner_layer": surface.owner_layer,
        "status": surface.status,
        "trust_ceiling": surface.trust_ceiling,
        "capability_count": len(surface.capabilities),
        "summary_exposed": surface.mcp_exposure_policy.get("expose_summary") is True,
        "raw_manifest_exposed": False,
    }


def _capability_summary(record: Any) -> dict[str, Any]:
    return {
        "capability_id": record.capability_id,
        "surface_id": record.surface_id,
        "risk_class": record.risk_class,
        "risk_severity": record.risk_severity,
        "risk_category": record.risk_category,
        "policy_decision": record.policy_decision,
        "approval_required": record.approval_required,
        "approval_floor": record.approval_floor,
        "audit_required": record.audit_required,
        "gate_required": record.gate_required,
        "trust_ceiling": record.trust_ceiling,
        "authority_layer": record.authority_layer,
        "source_status": record.source_status,
    }


def _route_decision_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": record.get("decision_id"),
        "created_at": record.get("created_at"),
        "requested_capability": record.get("requested_capability"),
        "requested_surface_id": record.get("requested_surface_id"),
        "candidate_surfaces": list(record.get("candidate_surfaces") or []),
        "selected_surface": record.get("selected_surface"),
        "decision": record.get("decision"),
        "risk_class": record.get("risk_class"),
        "approval_required": record.get("approval_required"),
        "audit_required": record.get("audit_required"),
        "gate_required": record.get("gate_required"),
        "execution_performed": False,
    }


def _files_read(payload: dict[str, Any]) -> list[str]:
    if payload.get("registry_status") == "available":
        return ["runtime/runtime_surfaces/manifests/", "runtime/runtime_surfaces/state/routing_decisions.jsonl"]
    return ["runtime/runtime_surfaces/manifests/"]
