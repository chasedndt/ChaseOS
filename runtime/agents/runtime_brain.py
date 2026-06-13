"""Agent Runtime Brain schema.

Runtime brains are advisory Layer C surfaces. They do not self-upgrade,
self-authorize, or expand runtime permissions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from runtime.agents.runtime_profile import RuntimeProfile
from runtime.pulse.card_schema import EvidenceRef, PulseCard, now_utc


@dataclass
class RuntimeReflection:
    reflection_id: str
    summary: str
    evidence: list[EvidenceRef] = field(default_factory=list)
    created_at: str = field(default_factory=now_utc)
    creates_self_upgrade_proposal: bool = False
    requires_operator_review: bool = True

    def validate(self) -> None:
        if not self.reflection_id:
            raise ValueError("reflection_id is required")
        if not self.summary:
            raise ValueError("summary is required")
        if self.creates_self_upgrade_proposal and not self.requires_operator_review:
            raise ValueError("self-upgrade proposals require operator review")
        for item in self.evidence:
            item.validate()


@dataclass
class AgentRuntimeBrain:
    runtime_id: str
    profile: RuntimeProfile
    reflections: list[RuntimeReflection] = field(default_factory=list)
    pulse_deck_refs: list[str] = field(default_factory=list)
    runtime_pulse_history_refs: list[str] = field(default_factory=list)
    known_strengths: list[str] = field(default_factory=list)
    known_weaknesses: list[str] = field(default_factory=list)
    repeated_blockers: list[str] = field(default_factory=list)
    successful_repair_patterns: list[str] = field(default_factory=list)
    skill_gap_notes: list[str] = field(default_factory=list)
    workflow_preferences: list[str] = field(default_factory=list)
    permission_requests: list[str] = field(default_factory=list)
    permission_issues: list[str] = field(default_factory=list)
    drift_signals: list[str] = field(default_factory=list)
    next_improvement_candidates: list[str] = field(default_factory=list)
    runtime_navigation_map_refs: list[str] = field(default_factory=list)
    agent_identity_ledger_refs: list[str] = field(default_factory=list)
    execution_repair_memory_refs: list[str] = field(default_factory=list)
    self_upgrade_active: bool = False

    def validate(self) -> None:
        self.profile.validate()
        if self.runtime_id != self.profile.runtime_id:
            raise ValueError("brain runtime_id must match profile runtime_id")
        if self.self_upgrade_active:
            raise ValueError("agent self-upgrade is not active in this scaffold")
        for reflection in self.reflections:
            reflection.validate()

    def add_reflection(self, reflection: RuntimeReflection) -> None:
        reflection.validate()
        self.reflections.append(reflection)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    def latest_reflection_card(self) -> PulseCard | None:
        self.validate()
        if not self.reflections:
            return None
        reflection = self.reflections[-1]
        return PulseCard(
            card_id=f"{self.runtime_id}-{reflection.reflection_id}",
            audience="agent",
            card_class="Runtime Reflection",
            title=f"{self.runtime_id} reflection",
            summary=reflection.summary,
            evidence=reflection.evidence,
            urgency=1,
            confidence=0.5,
        )
