"""Read-only routing proposal helpers for ARSL runtime surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from runtime.runtime_surfaces.models import RuntimeSurfaceManifest
from runtime.runtime_surfaces.policy import CapabilityPolicyRecord, build_capability_policy_index
from runtime.runtime_surfaces.registry import RuntimeSurfaceRegistry, load_runtime_surface_registry


RouteDecision = Literal["proposed", "approval_required", "blocked", "deny_unknown"]


@dataclass(frozen=True)
class RuntimeSurfaceRouteCandidate:
    """Read-only route candidate derived from a manifest capability policy record."""

    surface_id: str
    capability_id: str
    policy_decision: str
    authority_layer: str
    risk_class: str
    risk_severity: int
    approval_required: str
    audit_required: bool
    gate_required: bool
    trust_ceiling: str
    source_status: str

    @classmethod
    def from_policy_record(cls, record: CapabilityPolicyRecord) -> "RuntimeSurfaceRouteCandidate":
        return cls(
            surface_id=record.surface_id,
            capability_id=record.capability_id,
            policy_decision=record.policy_decision,
            authority_layer=record.authority_layer,
            risk_class=record.risk_class,
            risk_severity=record.risk_severity,
            approval_required=record.approval_required,
            audit_required=record.audit_required,
            gate_required=record.gate_required,
            trust_ceiling=record.trust_ceiling,
            source_status=record.source_status,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "surface_id": self.surface_id,
            "capability_id": self.capability_id,
            "policy_decision": self.policy_decision,
            "authority_layer": self.authority_layer,
            "risk_class": self.risk_class,
            "risk_severity": self.risk_severity,
            "approval_required": self.approval_required,
            "audit_required": self.audit_required,
            "gate_required": self.gate_required,
            "trust_ceiling": self.trust_ceiling,
            "source_status": self.source_status,
        }


@dataclass(frozen=True)
class RuntimeSurfaceRouteDecision:
    """Read-only ARSL routing proposal.

    Phase 3 decisions are metadata only. They do not execute work and do not
    write the Phase 5 routing ledger.
    """

    schema_version: int
    requested_capability: str
    requested_surface_id: str | None
    decision: RouteDecision
    candidate_surfaces: tuple[str, ...]
    selected_surface: str | None
    authority_layer: str | None
    risk_class: str | None
    risk_severity: int | None
    approval_required: str | None
    audit_required: bool
    gate_required: bool
    trust_ceiling: str | None
    policy_refs: tuple[str, ...]
    denial_reasons: tuple[str, ...]
    candidates: tuple[RuntimeSurfaceRouteCandidate, ...]
    execution_performed: bool = False
    ledger_written: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "requested_capability": self.requested_capability,
            "requested_surface_id": self.requested_surface_id,
            "decision": self.decision,
            "candidate_surfaces": list(self.candidate_surfaces),
            "selected_surface": self.selected_surface,
            "authority_layer": self.authority_layer,
            "risk_class": self.risk_class,
            "risk_severity": self.risk_severity,
            "approval_required": self.approval_required,
            "audit_required": self.audit_required,
            "gate_required": self.gate_required,
            "trust_ceiling": self.trust_ceiling,
            "policy_refs": list(self.policy_refs),
            "denial_reasons": list(self.denial_reasons),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "execution_performed": self.execution_performed,
            "ledger_written": self.ledger_written,
        }


def propose_route(
    requested_capability: str,
    *,
    registry: RuntimeSurfaceRegistry | None = None,
    vault_root: str | None = None,
    requested_surface_id: str | None = None,
) -> RuntimeSurfaceRouteDecision:
    """Return a read-only routing proposal for a requested capability.

    Unknown capabilities and mismatched surface filters deny closed instead of
    falling back to weaker or ambient surfaces.
    """

    resolved_registry = registry or load_runtime_surface_registry(vault_root)
    requested = str(requested_capability or "").strip()
    if not requested:
        return _deny(
            requested_capability=requested,
            requested_surface_id=requested_surface_id,
            reason="requested_capability is required",
        )

    records = build_capability_policy_index(resolved_registry).get(requested, [])
    if requested_surface_id is not None:
        records = [record for record in records if record.surface_id == requested_surface_id]
    if not records:
        reason = (
            f"No ARSL route candidates found for {requested_surface_id}.{requested}"
            if requested_surface_id
            else f"No ARSL route candidates found for {requested}"
        )
        return _deny(
            requested_capability=requested,
            requested_surface_id=requested_surface_id,
            reason=reason,
        )

    candidates = tuple(RuntimeSurfaceRouteCandidate.from_policy_record(record) for record in records)
    selected = _select_candidate(candidates)
    if selected.policy_decision == "blocked":
        return _from_selected(
            requested_capability=requested,
            requested_surface_id=requested_surface_id,
            decision="blocked",
            selected=selected,
            candidates=candidates,
            policy_refs=_policy_refs_for(resolved_registry, selected.surface_id),
            denial_reasons=(f"{selected.surface_id}.{selected.capability_id} is blocked by ARSL policy",),
        )
    if selected.policy_decision == "approval_required":
        return _from_selected(
            requested_capability=requested,
            requested_surface_id=requested_surface_id,
            decision="approval_required",
            selected=selected,
            candidates=candidates,
            policy_refs=_policy_refs_for(resolved_registry, selected.surface_id),
            denial_reasons=(f"{selected.approval_required} approval required before execution authority",),
        )
    return _from_selected(
        requested_capability=requested,
        requested_surface_id=requested_surface_id,
        decision="proposed",
        selected=selected,
        candidates=candidates,
        policy_refs=_policy_refs_for(resolved_registry, selected.surface_id),
        denial_reasons=(),
    )


def _select_candidate(candidates: tuple[RuntimeSurfaceRouteCandidate, ...]) -> RuntimeSurfaceRouteCandidate:
    decision_rank = {"allow": 0, "approval_required": 1, "blocked": 2}
    return sorted(
        candidates,
        key=lambda candidate: (
            decision_rank.get(candidate.policy_decision, 99),
            candidate.risk_severity,
            candidate.surface_id,
        ),
    )[0]


def _policy_refs_for(registry: RuntimeSurfaceRegistry, surface_id: str) -> tuple[str, ...]:
    manifest: RuntimeSurfaceManifest = registry.get_surface(surface_id)
    refs = [
        "06_AGENTS/Agent-Control-Plane.md",
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/Trust-Tiers.md",
        *manifest.permission_model_refs,
        *manifest.docs_refs,
    ]
    return tuple(dict.fromkeys(refs))


def _from_selected(
    *,
    requested_capability: str,
    requested_surface_id: str | None,
    decision: RouteDecision,
    selected: RuntimeSurfaceRouteCandidate,
    candidates: tuple[RuntimeSurfaceRouteCandidate, ...],
    policy_refs: tuple[str, ...],
    denial_reasons: tuple[str, ...],
) -> RuntimeSurfaceRouteDecision:
    return RuntimeSurfaceRouteDecision(
        schema_version=1,
        requested_capability=requested_capability,
        requested_surface_id=requested_surface_id,
        decision=decision,
        candidate_surfaces=tuple(candidate.surface_id for candidate in candidates),
        selected_surface=selected.surface_id,
        authority_layer=selected.authority_layer,
        risk_class=selected.risk_class,
        risk_severity=selected.risk_severity,
        approval_required=selected.approval_required,
        audit_required=selected.audit_required,
        gate_required=selected.gate_required,
        trust_ceiling=selected.trust_ceiling,
        policy_refs=policy_refs,
        denial_reasons=denial_reasons,
        candidates=candidates,
    )


def _deny(
    *,
    requested_capability: str,
    requested_surface_id: str | None,
    reason: str,
) -> RuntimeSurfaceRouteDecision:
    return RuntimeSurfaceRouteDecision(
        schema_version=1,
        requested_capability=requested_capability,
        requested_surface_id=requested_surface_id,
        decision="deny_unknown",
        candidate_surfaces=(),
        selected_surface=None,
        authority_layer=None,
        risk_class=None,
        risk_severity=None,
        approval_required=None,
        audit_required=True,
        gate_required=True,
        trust_ceiling=None,
        policy_refs=(
            "06_AGENTS/Agent-Control-Plane.md",
            "06_AGENTS/Permission-Matrix.md",
            "06_AGENTS/Trust-Tiers.md",
        ),
        denial_reasons=(reason,),
        candidates=(),
    )
