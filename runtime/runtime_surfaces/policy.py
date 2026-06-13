"""Policy helpers for ARSL capability risk classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from runtime.runtime_surfaces.models import (
    RuntimeSurfaceCapability,
    RuntimeSurfaceError,
    RuntimeSurfaceManifest,
)
from runtime.runtime_surfaces.registry import RuntimeSurfaceRegistry
from runtime.runtime_surfaces.risk import (
    RiskClassDefinition,
    approval_satisfies_floor,
    get_risk_class,
    normalize_approval_required,
)


PolicyDecision = Literal["allow", "approval_required", "blocked"]


@dataclass(frozen=True)
class CapabilityPolicyRecord:
    """Normalized policy view for one manifest capability."""

    surface_id: str
    capability_id: str
    maps_to: str
    risk_class: str
    risk_severity: int
    risk_category: str
    approval_required: str
    approval_floor: str
    policy_decision: PolicyDecision
    audit_required: bool
    gate_required: bool
    trust_ceiling: str
    authority_layer: str
    source_status: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "surface_id": self.surface_id,
            "capability_id": self.capability_id,
            "maps_to": self.maps_to,
            "risk_class": self.risk_class,
            "risk_severity": self.risk_severity,
            "risk_category": self.risk_category,
            "approval_required": self.approval_required,
            "approval_floor": self.approval_floor,
            "policy_decision": self.policy_decision,
            "audit_required": self.audit_required,
            "gate_required": self.gate_required,
            "trust_ceiling": self.trust_ceiling,
            "authority_layer": self.authority_layer,
            "source_status": self.source_status,
            "reasons": list(self.reasons),
        }


def classify_manifest_capabilities(manifest: RuntimeSurfaceManifest) -> list[CapabilityPolicyRecord]:
    """Return normalized policy records for every capability in a manifest."""

    return [
        classify_capability(manifest, capability)
        for capability in manifest.capabilities
    ]


def classify_capability(
    manifest: RuntimeSurfaceManifest,
    capability: RuntimeSurfaceCapability,
) -> CapabilityPolicyRecord:
    """Classify a manifest capability and fail closed on unsafe approval declarations."""

    risk = get_risk_class(capability.risk_class)
    approval_required = normalize_approval_required(capability.approval_required)
    if not risk.blocks_routing and not approval_satisfies_floor(capability.approval_required, risk.approval_floor):
        raise RuntimeSurfaceError(
            f"{manifest.surface_id}.{capability.capability_id} approval_required={approval_required!r} "
            f"does not satisfy {risk.risk_class} floor {risk.approval_floor!r}"
        )

    decision, reasons = _decision_for(risk=risk, approval_required=approval_required)
    return CapabilityPolicyRecord(
        surface_id=manifest.surface_id,
        capability_id=capability.capability_id,
        maps_to=capability.maps_to,
        risk_class=risk.risk_class,
        risk_severity=risk.severity,
        risk_category=risk.category,
        approval_required=approval_required,
        approval_floor=risk.approval_floor,
        policy_decision=decision,
        audit_required=risk.audit_required,
        gate_required=risk.gate_required,
        trust_ceiling=manifest.trust_ceiling,
        authority_layer=str(manifest.routing_policy.get("authority_layer") or ""),
        source_status=manifest.status,
        reasons=reasons,
    )


def build_capability_policy_index(registry: RuntimeSurfaceRegistry) -> dict[str, list[CapabilityPolicyRecord]]:
    """Build a capability-to-policy-record index from validated surface manifests."""

    index: dict[str, list[CapabilityPolicyRecord]] = {}
    for manifest in registry.list_surfaces():
        for record in classify_manifest_capabilities(manifest):
            index.setdefault(record.capability_id, []).append(record)
    return {capability_id: sorted(records, key=lambda record: record.surface_id) for capability_id, records in index.items()}


def capability_policy_records(
    registry: RuntimeSurfaceRegistry,
    capability_id: str,
    *,
    surface_id: str | None = None,
) -> list[CapabilityPolicyRecord]:
    """Return policy records for a requested capability or fail closed."""

    records = build_capability_policy_index(registry).get(capability_id, [])
    if surface_id is not None:
        records = [record for record in records if record.surface_id == surface_id]
    if not records:
        label = f"{surface_id}.{capability_id}" if surface_id else capability_id
        raise RuntimeSurfaceError(f"No ARSL capability policy records found for {label}")
    return records


def assert_registry_policy_safe(registry: RuntimeSurfaceRegistry) -> None:
    """Validate all manifests against the Phase 2 risk policy floor."""

    build_capability_policy_index(registry)


def _decision_for(*, risk: RiskClassDefinition, approval_required: str) -> tuple[PolicyDecision, tuple[str, ...]]:
    if risk.blocks_routing:
        return "blocked", (f"{risk.risk_class} is blocked by ARSL Phase 2 policy",)
    if approval_required in {"conditional", "explicit"}:
        return "approval_required", (f"{approval_required} approval is required before execution authority",)
    if risk.audit_required:
        return "allow", ("allowed only as classified metadata; audit is required if routed by a later phase",)
    return "allow", ("allowed as classified metadata",)
