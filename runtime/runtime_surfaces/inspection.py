"""Read-only CLI inspection helpers for Adaptive Runtime Surface Layer."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from runtime.runtime_surfaces.audit import read_route_decision_records
from runtime.runtime_surfaces.browser_skill_memory import normalize_browser_skill_memory
from runtime.runtime_surfaces.models import RuntimeSurfaceError, RuntimeSurfaceManifest
from runtime.runtime_surfaces.policy import build_capability_policy_index
from runtime.runtime_surfaces.registry import load_runtime_surface_registry


class RuntimeSurfaceInspectionError(ValueError):
    """Raised when read-only ARSL inspection cannot be completed safely."""


SAFETY_FLAGS: dict[str, bool] = {
    "read_only": True,
    "execution_performed": False,
    "route_proposal_performed": False,
    "ledger_written": False,
    "provider_calls_performed": False,
    "browser_control_performed": False,
    "raw_manifest_exposed": False,
    "mcp_tools_exposed": False,
    "credential_values_visible": False,
    "browser_profile_visible": False,
}


def build_runtime_surface_summary(
    vault_root: str | Path | None = None,
    *,
    surface_id: str | None = None,
) -> dict[str, Any]:
    """Build a sanitized registry summary without routing or execution."""

    try:
        registry = load_runtime_surface_registry(vault_root)
        surfaces = registry.list_surfaces()
        if surface_id:
            surfaces = [registry.get_surface(surface_id)]
        policy_index = build_capability_policy_index(registry)
        policy_records = [
            record
            for records in policy_index.values()
            for record in records
            if surface_id is None or record.surface_id == surface_id
        ]
        browser_skill_memory = normalize_browser_skill_memory(vault_root).summary()
        route_decisions = read_route_decision_records(vault_root=vault_root)
    except (RuntimeSurfaceError, ValueError, FileNotFoundError) as exc:
        raise RuntimeSurfaceInspectionError(str(exc)) from exc

    return {
        "ok": True,
        "schema_version": 1,
        "feature": "Adaptive Runtime Surface Layer",
        "surface_filter": surface_id,
        "surface_count": len(surfaces),
        "capability_count": sum(len(surface.capabilities) for surface in surfaces),
        "policy_record_count": len(policy_records),
        "risk_class_count": dict(sorted(Counter(record.risk_class for record in policy_records).items())),
        "policy_decision_count": dict(
            sorted(Counter(record.policy_decision for record in policy_records).items())
        ),
        "surfaces": [_surface_summary(surface) for surface in surfaces],
        "browser_skill_memory": browser_skill_memory,
        "routing_audit": _routing_audit_summary(route_decisions, surface_id=surface_id),
        "safety": dict(SAFETY_FLAGS),
        "boundary": _boundary_text(),
    }


def build_runtime_surface_capability_summary(
    vault_root: str | Path | None = None,
    *,
    surface_id: str | None = None,
) -> dict[str, Any]:
    """Build a sanitized capability-policy summary without routing or execution."""

    try:
        registry = load_runtime_surface_registry(vault_root)
        if surface_id:
            registry.get_surface(surface_id)
        records = [
            record
            for records in build_capability_policy_index(registry).values()
            for record in records
            if surface_id is None or record.surface_id == surface_id
        ]
    except (RuntimeSurfaceError, ValueError, FileNotFoundError) as exc:
        raise RuntimeSurfaceInspectionError(str(exc)) from exc

    records = sorted(records, key=lambda record: (record.surface_id, record.capability_id))
    return {
        "ok": True,
        "schema_version": 1,
        "feature": "Adaptive Runtime Surface Layer",
        "surface_filter": surface_id,
        "capability_policy_record_count": len(records),
        "risk_class_count": dict(sorted(Counter(record.risk_class for record in records).items())),
        "policy_decision_count": dict(sorted(Counter(record.policy_decision for record in records).items())),
        "capabilities": [_capability_summary(record) for record in records],
        "safety": dict(SAFETY_FLAGS),
        "boundary": _boundary_text(),
    }


def format_runtime_surface_summary(payload: dict[str, Any]) -> str:
    """Format an ARSL registry summary for human CLI output."""

    lines = [
        "Adaptive Runtime Surface Layer",
        f"  ok: {payload.get('ok')}",
        f"  surfaces: {payload.get('surface_count')}",
        f"  capabilities: {payload.get('capability_count')}",
        f"  policy_records: {payload.get('policy_record_count')}",
        f"  risk_classes: {_format_counts(payload.get('risk_class_count'))}",
        f"  policy_decisions: {_format_counts(payload.get('policy_decision_count'))}",
    ]
    if payload.get("surface_filter"):
        lines.append(f"  filter: {payload.get('surface_filter')}")
    lines.append("  registry:")
    for surface in payload.get("surfaces", []):
        lines.append(
            "    - "
            f"{surface.get('surface_id')} "
            f"family={surface.get('surface_family')} "
            f"type={surface.get('surface_type')} "
            f"status={surface.get('status')} "
            f"trust_ceiling={surface.get('trust_ceiling')} "
            f"capabilities={surface.get('capability_count')}"
        )
    memory = payload.get("browser_skill_memory") or {}
    lines.append(
        "  browser_skill_memory: "
        f"records={memory.get('record_count')} "
        f"writes={memory.get('writes_performed')} "
        f"execution={memory.get('browser_execution_performed')} "
        f"promotion={memory.get('promotion_performed')}"
    )
    audit = payload.get("routing_audit") or {}
    lines.append(
        "  routing_audit: "
        f"records={audit.get('record_count')} "
        f"latest={audit.get('latest_created_at') or 'none'}"
    )
    lines.append(f"  boundary: {payload.get('boundary')}")
    return "\n".join(lines)


def format_runtime_surface_capability_summary(payload: dict[str, Any]) -> str:
    """Format ARSL capability policy summary for human CLI output."""

    lines = [
        "Adaptive Runtime Surface Layer Capability Policy",
        f"  ok: {payload.get('ok')}",
        f"  records: {payload.get('capability_policy_record_count')}",
        f"  risk_classes: {_format_counts(payload.get('risk_class_count'))}",
        f"  policy_decisions: {_format_counts(payload.get('policy_decision_count'))}",
    ]
    if payload.get("surface_filter"):
        lines.append(f"  filter: {payload.get('surface_filter')}")
    lines.append("  capabilities:")
    for record in payload.get("capabilities", []):
        lines.append(
            "    - "
            f"{record.get('surface_id')}.{record.get('capability_id')} "
            f"risk={record.get('risk_class')} "
            f"decision={record.get('policy_decision')} "
            f"approval={record.get('approval_required')} "
            f"gate={record.get('gate_required')} "
            f"audit={record.get('audit_required')}"
        )
    lines.append(f"  boundary: {payload.get('boundary')}")
    return "\n".join(lines)


def _surface_summary(surface: RuntimeSurfaceManifest) -> dict[str, Any]:
    return {
        "surface_id": surface.surface_id,
        "display_name": surface.display_name,
        "surface_family": surface.surface_family,
        "surface_type": surface.surface_type,
        "owner_layer": surface.owner_layer,
        "status": surface.status,
        "trust_ceiling": surface.trust_ceiling,
        "capability_count": len(surface.capabilities),
        "authority_layer": str(surface.routing_policy.get("authority_layer") or ""),
        "summary_exposed": bool(surface.mcp_exposure_policy.get("expose_summary")),
        "raw_manifest_exposed": False,
    }


def _capability_summary(record: Any) -> dict[str, Any]:
    return {
        "surface_id": record.surface_id,
        "capability_id": record.capability_id,
        "maps_to": record.maps_to,
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
        "reasons": list(record.reasons),
    }


def _routing_audit_summary(records: list[dict[str, Any]], *, surface_id: str | None) -> dict[str, Any]:
    if surface_id:
        records = [
            record
            for record in records
            if record.get("selected_surface") == surface_id or surface_id in (record.get("candidate_surfaces") or [])
        ]
    latest = records[-1] if records else {}
    return {
        "record_count": len(records),
        "latest_decision_id": latest.get("decision_id"),
        "latest_created_at": latest.get("created_at"),
        "latest_decision": latest.get("decision"),
        "execution_performed": False,
        "ledger_written": False,
    }


def _format_counts(counts: Any) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(dict(counts).items()))


def _boundary_text() -> str:
    return (
        "read-only inspection only; no route proposal, runtime dispatch, browser control, "
        "provider call, credential access, raw manifest exposure, MCP tool exposure, "
        "ledger write, approval grant, or canonical writeback"
    )
