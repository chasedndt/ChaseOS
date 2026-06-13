"""Execution Repair Memory schema for AgentHub runtime brains.

Execution repair memory records reusable failure/workaround patterns from
browser, repo, connector, or autonomous workflow execution. It is advisory
runtime memory only; it does not grant permissions or mutate canonical truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from runtime.pulse.card_schema import EvidenceRef, PulseCard, RecommendedAction, now_utc


FAILURE_SURFACES = {"browser", "repo", "connector", "autonomous_workflow", "runtime"}
REPAIR_PROMOTION_STATUSES = {
    "runtime_memory_only",
    "candidate_for_sop",
    "candidate_for_runtime_navigation_map",
    "rejected",
}


@dataclass
class RepairPattern:
    trigger: str
    workaround: str
    recommended_response: list[str] = field(default_factory=list)
    future_prevention: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.trigger:
            raise ValueError("repair trigger is required")
        if not self.workaround:
            raise ValueError("repair workaround is required")
        for item in self.recommended_response + self.future_prevention:
            if not item:
                raise ValueError("repair pattern items cannot be empty")


@dataclass
class ExecutionRepairMemoryEntry:
    repair_id: str
    runtime_id: str
    workflow_id: str
    failure_surface: str
    failure_type: str
    failure_summary: str
    resolution_summary: str
    repair_pattern: RepairPattern
    detected_at: str = field(default_factory=now_utc)
    source_logs: list[str] = field(default_factory=list)
    related_projects: list[str] = field(default_factory=list)
    promotion_status: str = "runtime_memory_only"
    requires_user_review: bool = False
    canonical_writeback_enabled: bool = False

    def validate(self) -> None:
        if not self.repair_id:
            raise ValueError("repair_id is required")
        if not self.runtime_id:
            raise ValueError("runtime_id is required")
        if not self.workflow_id:
            raise ValueError("workflow_id is required")
        if self.failure_surface not in FAILURE_SURFACES:
            raise ValueError(f"failure_surface must be one of {sorted(FAILURE_SURFACES)}")
        if not self.failure_type:
            raise ValueError("failure_type is required")
        if not self.failure_summary:
            raise ValueError("failure_summary is required")
        if not self.resolution_summary:
            raise ValueError("resolution_summary is required")
        self.repair_pattern.validate()
        if self.promotion_status not in REPAIR_PROMOTION_STATUSES:
            raise ValueError(
                f"promotion_status must be one of {sorted(REPAIR_PROMOTION_STATUSES)}"
            )
        if self.canonical_writeback_enabled:
            raise ValueError("execution repair memory cannot enable canonical writeback")
        for item in self.source_logs + self.related_projects:
            if not item:
                raise ValueError("execution repair references cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    def to_agent_pulse_card(self, *, deck_id: str | None = None) -> PulseCard:
        """Represent the repair pattern as an agent Pulse card candidate."""
        self.validate()
        return PulseCard(
            card_id=f"repair-{self.repair_id}",
            deck_id=deck_id,
            audience="agent",
            card_class="Execution Repair Pattern",
            title=f"{self.runtime_id} repair pattern: {self.failure_type}",
            summary=self.failure_summary,
            why_it_matters=self.resolution_summary,
            evidence=[
                EvidenceRef(
                    source_path=path,
                    source_type="execution_repair_memory_source_log",
                    summary=f"Source log for repair pattern {self.repair_id}",
                    trust_label="internal_log",
                )
                for path in self.source_logs
            ],
            recommended_actions=[
                RecommendedAction(
                    action_id=f"{self.repair_id}-runtime-navigation-update",
                    label="Review repair for runtime navigation map update",
                    action_type="update_runtime_navigation_map",
                    requires_operator_approval=True,
                    mutates_canonical_state=False,
                )
            ],
            urgency=3,
            confidence=0.7,
            promotion_status="candidate",
            writeback_status="draft_only",
            canonical_writeback_enabled=False,
        )
