"""Read-only operator review contract for ARSL route posture."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from runtime.runtime_surfaces.models import RuntimeSurfaceError
from runtime.runtime_surfaces.policy import build_capability_policy_index
from runtime.runtime_surfaces.registry import load_runtime_surface_registry
from runtime.runtime_surfaces.router import propose_route


class RuntimeSurfaceRouteReviewError(ValueError):
    """Raised when an ARSL route review contract cannot be built safely."""


SAFETY_FLAGS: dict[str, bool] = {
    "read_only": True,
    "route_review_built": True,
    "execution_performed": False,
    "runtime_dispatch_performed": False,
    "route_proposal_committed": False,
    "ledger_written": False,
    "approval_granted": False,
    "gate_mutated": False,
    "provider_calls_performed": False,
    "browser_control_performed": False,
    "raw_manifest_exposed": False,
    "mcp_tools_exposed": False,
    "credential_values_visible": False,
    "browser_profile_visible": False,
    "canonical_writeback_performed": False,
}


def build_route_review_contract(
    vault_root: str | Path | None = None,
    *,
    capability: str | None = None,
    surface_id: str | None = None,
) -> dict[str, Any]:
    """Build a read-only ARSL operator review contract.

    The contract can either summarize all known capability policy records or
    preview the route posture for one requested capability. It never appends the
    route ledger and never invokes the selected authority layer.
    """

    requested_capability = str(capability or "").strip() or None
    requested_surface_id = str(surface_id or "").strip() or None
    try:
        registry = load_runtime_surface_registry(vault_root)
        if requested_surface_id:
            registry.get_surface(requested_surface_id)
        policy_index = build_capability_policy_index(registry)
        records = [
            record
            for records_for_capability in policy_index.values()
            for record in records_for_capability
            if requested_capability is None or record.capability_id == requested_capability
            if requested_surface_id is None or record.surface_id == requested_surface_id
        ]
        route_preview = (
            propose_route(
                requested_capability,
                registry=registry,
                requested_surface_id=requested_surface_id,
            ).to_dict()
            if requested_capability
            else None
        )
    except (RuntimeSurfaceError, ValueError, FileNotFoundError) as exc:
        raise RuntimeSurfaceRouteReviewError(str(exc)) from exc

    records = sorted(records, key=lambda record: (record.capability_id, record.surface_id))
    decision_counts = Counter(record.policy_decision for record in records)
    risk_counts = Counter(record.risk_class for record in records)
    approval_counts = Counter(record.approval_required for record in records)

    return {
        "ok": True,
        "schema_version": 1,
        "feature": "Adaptive Runtime Surface Layer",
        "contract": "runtime_surface_route_review",
        "requested_capability": requested_capability,
        "requested_surface_id": requested_surface_id,
        "review_row_count": len(records),
        "route_preview": route_preview,
        "review_rows": [_review_row(record) for record in records],
        "summary": {
            "surface_count": len({record.surface_id for record in records}),
            "capability_count": len({record.capability_id for record in records}),
            "policy_decision_count": dict(sorted(decision_counts.items())),
            "risk_class_count": dict(sorted(risk_counts.items())),
            "approval_required_count": dict(sorted(approval_counts.items())),
            "explicit_or_conditional_approval_rows": sum(
                1 for record in records if record.approval_required in {"explicit", "conditional"}
            ),
            "gate_required_rows": sum(1 for record in records if record.gate_required),
            "audit_required_rows": sum(1 for record in records if record.audit_required),
        },
        "operator_review": {
            "review_surface_ready": True,
            "can_compare_candidate_surfaces": requested_capability is not None,
            "can_show_policy_refs": route_preview is not None,
            "can_grant_approval": False,
            "can_execute_route": False,
            "can_write_ledger": False,
            "next_required_authority": _next_required_authority(route_preview),
        },
        "safety": dict(SAFETY_FLAGS),
        "boundary": _boundary_text(),
    }


def format_route_review_contract(payload: dict[str, Any]) -> str:
    """Format an ARSL route review contract for human CLI output."""

    lines = [
        "Adaptive Runtime Surface Layer Route Review",
        f"  ok: {payload.get('ok')}",
        f"  rows: {payload.get('review_row_count')}",
    ]
    if payload.get("requested_capability"):
        lines.append(f"  capability: {payload.get('requested_capability')}")
    if payload.get("requested_surface_id"):
        lines.append(f"  surface: {payload.get('requested_surface_id')}")
    preview = payload.get("route_preview") or {}
    if preview:
        lines.extend(
            [
                f"  preview_decision: {preview.get('decision')}",
                f"  selected_surface: {preview.get('selected_surface') or 'none'}",
                f"  authority_layer: {preview.get('authority_layer') or 'none'}",
                f"  approval_required: {preview.get('approval_required') or 'none'}",
                f"  gate_required: {preview.get('gate_required')}",
                f"  ledger_written: {preview.get('ledger_written')}",
            ]
        )
    summary = payload.get("summary") or {}
    lines.extend(
        [
            f"  policy_decisions: {_format_counts(summary.get('policy_decision_count'))}",
            f"  risk_classes: {_format_counts(summary.get('risk_class_count'))}",
            f"  approval_required: {_format_counts(summary.get('approval_required_count'))}",
            "  review_rows:",
        ]
    )
    for row in payload.get("review_rows", [])[:40]:
        lines.append(
            "    - "
            f"{row.get('surface_id')}.{row.get('capability_id')} "
            f"decision={row.get('policy_decision')} "
            f"risk={row.get('risk_class')} "
            f"approval={row.get('approval_required')} "
            f"gate={row.get('gate_required')} "
            f"authority={row.get('authority_layer')}"
        )
    if len(payload.get("review_rows", [])) > 40:
        lines.append(f"    ... {len(payload.get('review_rows', [])) - 40} more rows omitted")
    lines.append(f"  boundary: {payload.get('boundary')}")
    return "\n".join(lines)


def _review_row(record: Any) -> dict[str, Any]:
    return {
        "surface_id": record.surface_id,
        "capability_id": record.capability_id,
        "maps_to": record.maps_to,
        "policy_decision": record.policy_decision,
        "risk_class": record.risk_class,
        "risk_severity": record.risk_severity,
        "risk_category": record.risk_category,
        "approval_required": record.approval_required,
        "approval_floor": record.approval_floor,
        "audit_required": record.audit_required,
        "gate_required": record.gate_required,
        "trust_ceiling": record.trust_ceiling,
        "authority_layer": record.authority_layer,
        "source_status": record.source_status,
        "reasons": list(record.reasons),
    }


def _next_required_authority(route_preview: dict[str, Any] | None) -> str:
    if not route_preview:
        return "operator_review_only"
    decision = route_preview.get("decision")
    if decision == "proposed":
        return str(route_preview.get("authority_layer") or "operator_review")
    if decision == "approval_required":
        return "approval_gate_then_" + str(route_preview.get("authority_layer") or "authority_layer")
    if decision == "blocked":
        return "blocked_by_arsl_policy"
    return "deny_unknown"


def _format_counts(counts: Any) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(dict(counts).items()))


def _boundary_text() -> str:
    return (
        "read-only route review only; no route execution, runtime dispatch, browser control, "
        "provider call, credential access, approval grant, Gate mutation, raw manifest exposure, "
        "MCP tool exposure, routing ledger write, or canonical writeback"
    )
