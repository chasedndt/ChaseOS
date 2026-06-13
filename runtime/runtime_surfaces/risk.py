"""Risk taxonomy for Adaptive Runtime Surface Layer capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


APPROVAL_LEVELS: tuple[str, ...] = ("none", "conditional", "explicit", "blocked")


@dataclass(frozen=True)
class RiskClassDefinition:
    """Canonical risk definition for one ARSL capability risk class."""

    risk_class: str
    category: str
    severity: int
    approval_floor: str
    audit_required: bool
    gate_required: bool
    external_side_effect: bool
    sensitive_access: bool
    description: str

    @property
    def blocks_routing(self) -> bool:
        return self.approval_floor == "blocked"


class RuntimeSurfaceRiskError(ValueError):
    """Raised when an ARSL risk class or approval value fails closed."""


RISK_CLASS_DEFINITIONS: dict[str, RiskClassDefinition] = {
    "read_local_scoped": RiskClassDefinition(
        risk_class="read_local_scoped",
        category="read",
        severity=1,
        approval_floor="none",
        audit_required=False,
        gate_required=False,
        external_side_effect=False,
        sensitive_access=False,
        description="Scoped local read of already permitted repo/vault content.",
    ),
    "read_untrusted_external": RiskClassDefinition(
        risk_class="read_untrusted_external",
        category="read",
        severity=2,
        approval_floor="none",
        audit_required=True,
        gate_required=False,
        external_side_effect=False,
        sensitive_access=False,
        description="Read of untrusted external input treated as data, not instructions.",
    ),
    "draft_only": RiskClassDefinition(
        risk_class="draft_only",
        category="write",
        severity=1,
        approval_floor="none",
        audit_required=True,
        gate_required=False,
        external_side_effect=False,
        sensitive_access=False,
        description="Draft/proposal output that cannot mutate canonical state.",
    ),
    "proposal_write": RiskClassDefinition(
        risk_class="proposal_write",
        category="write",
        severity=2,
        approval_floor="conditional",
        audit_required=True,
        gate_required=False,
        external_side_effect=False,
        sensitive_access=False,
        description="Proposal or patch write that requires review conditions before trust.",
    ),
    "quarantine_write": RiskClassDefinition(
        risk_class="quarantine_write",
        category="write",
        severity=2,
        approval_floor="conditional",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=False,
        description="Write into quarantine or other untrusted holding area.",
    ),
    "canonical_write": RiskClassDefinition(
        risk_class="canonical_write",
        category="write",
        severity=4,
        approval_floor="explicit",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=False,
        description="Mutation of canonical ChaseOS state.",
    ),
    "external_ui_read": RiskClassDefinition(
        risk_class="external_ui_read",
        category="browser",
        severity=2,
        approval_floor="none",
        audit_required=True,
        gate_required=False,
        external_side_effect=False,
        sensitive_access=False,
        description="Inspection or screenshot of an external UI surface without mutation.",
    ),
    "external_ui_mutation": RiskClassDefinition(
        risk_class="external_ui_mutation",
        category="browser",
        severity=3,
        approval_floor="conditional",
        audit_required=True,
        gate_required=True,
        external_side_effect=True,
        sensitive_access=False,
        description="Click, keyboard, tab, or workflow action on an external UI.",
    ),
    "external_network_call": RiskClassDefinition(
        risk_class="external_network_call",
        category="network",
        severity=3,
        approval_floor="explicit",
        audit_required=True,
        gate_required=True,
        external_side_effect=True,
        sensitive_access=False,
        description="Network operation that may contact an external system.",
    ),
    "credential_sensitive": RiskClassDefinition(
        risk_class="credential_sensitive",
        category="secret",
        severity=5,
        approval_floor="blocked",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=True,
        description="Credential or secret handling. ARSL Phase 2 does not route this.",
    ),
    "browser_profile_sensitive": RiskClassDefinition(
        risk_class="browser_profile_sensitive",
        category="secret",
        severity=5,
        approval_floor="blocked",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=True,
        description="Real browser profile, cookies, or logged-in session handling. ARSL Phase 2 blocks this.",
    ),
    "provider_fallback": RiskClassDefinition(
        risk_class="provider_fallback",
        category="provider",
        severity=3,
        approval_floor="conditional",
        audit_required=True,
        gate_required=False,
        external_side_effect=False,
        sensitive_access=False,
        description="Provider/model fallback decision. Weak fallback must never become sticky silently.",
    ),
    "runtime_config_change": RiskClassDefinition(
        risk_class="runtime_config_change",
        category="runtime_config",
        severity=4,
        approval_floor="explicit",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=False,
        description="Change to runtime/provider/surface configuration.",
    ),
    "security_policy_change": RiskClassDefinition(
        risk_class="security_policy_change",
        category="security_policy",
        severity=5,
        approval_floor="explicit",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=False,
        description="Change to Gate, Trust Tier, Permission Matrix, or Agent Control Plane policy.",
    ),
    "destructive_action": RiskClassDefinition(
        risk_class="destructive_action",
        category="destructive",
        severity=5,
        approval_floor="blocked",
        audit_required=True,
        gate_required=True,
        external_side_effect=True,
        sensitive_access=False,
        description="Deletion, irreversible mutation, or destructive external action. ARSL does not route this.",
    ),
    "blocked": RiskClassDefinition(
        risk_class="blocked",
        category="blocked",
        severity=5,
        approval_floor="blocked",
        audit_required=True,
        gate_required=True,
        external_side_effect=False,
        sensitive_access=False,
        description="Capability intentionally unavailable through ARSL.",
    ),
}

VALID_RISK_CLASSES: set[str] = set(RISK_CLASS_DEFINITIONS)


def get_risk_class(risk_class: str) -> RiskClassDefinition:
    """Return a risk definition or fail closed on unknown risk classes."""

    try:
        return RISK_CLASS_DEFINITIONS[risk_class]
    except KeyError as exc:
        raise RuntimeSurfaceRiskError(f"Unknown ARSL risk class: {risk_class}") from exc


def list_risk_classes() -> list[RiskClassDefinition]:
    """Return risk definitions in stable severity/name order."""

    return sorted(RISK_CLASS_DEFINITIONS.values(), key=lambda definition: (definition.severity, definition.risk_class))


def normalize_approval_required(value: Any) -> str:
    """Normalize manifest approval values into ARSL policy levels."""

    if value is False:
        return "none"
    if value is True:
        return "explicit"
    if value == "conditional":
        return "conditional"
    if value == "blocked":
        return "blocked"
    raise RuntimeSurfaceRiskError("approval_required must be true, false, conditional, or blocked")


def approval_rank(level: str) -> int:
    if level not in APPROVAL_LEVELS:
        raise RuntimeSurfaceRiskError(f"Unknown approval level: {level}")
    return APPROVAL_LEVELS.index(level)


def approval_satisfies_floor(declared: Any, floor: str) -> bool:
    """Return whether a manifest approval declaration satisfies a risk floor."""

    normalized = normalize_approval_required(declared)
    if floor == "blocked":
        return normalized == "blocked"
    return approval_rank(normalized) >= approval_rank(floor) and normalized != "blocked"


def highest_risk(risk_classes: list[str] | tuple[str, ...]) -> RiskClassDefinition:
    if not risk_classes:
        raise RuntimeSurfaceRiskError("At least one risk class is required")
    definitions = [get_risk_class(risk_class) for risk_class in risk_classes]
    return sorted(definitions, key=lambda definition: (definition.severity, definition.risk_class))[-1]
