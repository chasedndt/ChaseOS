"""Read-only feedback review queue contracts for ChaseOS Pulse."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback import (
    FEEDBACK_CANDIDATE_ROOT,
    PENDING_REVIEW,
    PulseFeedbackCandidate,
    load_feedback_candidates,
)


REVIEW_DECISION_TYPES = {
    "accept_for_future_ranking",
    "reject_candidate",
    "defer_candidate",
    "request_more_context",
}

CONTRACT_ONLY = "contract_only"
REVIEW_ITEM_STATUS = {PENDING_REVIEW}

BLOCKED_REVIEW_EFFECTS = (
    "source_deck_mutation",
    "source_card_feedback_application",
    "memory_approval",
    "memory_atom_write",
    "task_creation",
    "project_file_mutation",
    "knowledge_promotion",
    "canonical_writeback",
    "schedule_activation",
    "provider_call",
    "connector_call",
    "second_datastore_write",
)

DECISION_ALLOWED_EFFECTS = {
    "accept_for_future_ranking": ("future_ranking_signal_candidate",),
    "reject_candidate": ("candidate_rejection_signal",),
    "defer_candidate": ("defer_for_later_review_signal",),
    "request_more_context": ("request_more_context_signal",),
}


@dataclass
class PulseFeedbackReviewItem:
    """Operator-review projection of a persisted feedback candidate."""

    candidate_id: str
    feedback_id: str
    card_id: str
    feedback_type: str
    source_deck_path: str
    operator_note: str = ""
    created_at: str = field(default_factory=now_utc)
    source_surface_path: str | None = None
    status: str = PENDING_REVIEW
    review_required: bool = True
    candidate_only: bool = True
    creates_memory_candidate: bool = False
    canonical_writeback_allowed: bool = False
    applied_to_source_deck: bool = False
    approves_memory: bool = False
    creates_task: bool = False
    allowed_review_decisions: tuple[str, ...] = field(
        default_factory=lambda: tuple(sorted(REVIEW_DECISION_TYPES))
    )
    blocked_effects: tuple[str, ...] = BLOCKED_REVIEW_EFFECTS

    def validate(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.feedback_id:
            raise ValueError("feedback_id is required")
        if not self.card_id:
            raise ValueError("card_id is required")
        if not self.feedback_type:
            raise ValueError("feedback_type is required")
        if not self.source_deck_path:
            raise ValueError("source_deck_path is required")
        if self.status not in REVIEW_ITEM_STATUS:
            raise ValueError(f"review item status must be one of {sorted(REVIEW_ITEM_STATUS)}")
        if not self.review_required:
            raise ValueError("feedback review items require review")
        if not self.candidate_only:
            raise ValueError("feedback review items must remain candidate-only")
        if self.canonical_writeback_allowed:
            raise ValueError("feedback review items cannot allow canonical writeback")
        if self.applied_to_source_deck:
            raise ValueError("feedback review items cannot be applied to source decks")
        if self.approves_memory:
            raise ValueError("feedback review items cannot approve memory")
        if self.creates_task:
            raise ValueError("feedback review items cannot create tasks directly")
        if "canonical_writeback" not in self.blocked_effects:
            raise ValueError("feedback review items must block canonical writeback")
        missing = REVIEW_DECISION_TYPES.difference(self.allowed_review_decisions)
        if missing:
            raise ValueError(f"review item is missing decisions: {sorted(missing)}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_candidate(cls, candidate: PulseFeedbackCandidate) -> "PulseFeedbackReviewItem":
        candidate.validate()
        item = cls(
            candidate_id=candidate.candidate_id,
            feedback_id=candidate.feedback_id,
            card_id=candidate.card_id,
            feedback_type=candidate.feedback_type,
            source_deck_path=candidate.source_deck_path,
            operator_note=candidate.operator_note,
            created_at=candidate.created_at,
            source_surface_path=candidate.source_surface_path,
            status=candidate.status,
            review_required=candidate.review_required,
            candidate_only=candidate.candidate_only,
            creates_memory_candidate=candidate.creates_memory_candidate,
            canonical_writeback_allowed=candidate.canonical_writeback_allowed,
            applied_to_source_deck=candidate.applied_to_source_deck,
            approves_memory=candidate.approves_memory,
            creates_task=candidate.creates_task,
        )
        item.validate()
        return item


@dataclass
class PulseFeedbackReviewQueue:
    """Read-only queue snapshot over pending Pulse feedback candidates."""

    generated_at: str = field(default_factory=now_utc)
    items: list[PulseFeedbackReviewItem] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    queue_status: str = "read_only"
    canonical_writeback_allowed: bool = False
    writes: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.queue_status != "read_only":
            raise ValueError("feedback review queue is read-only")
        if self.canonical_writeback_allowed:
            raise ValueError("feedback review queue cannot allow canonical writeback")
        if self.writes:
            raise ValueError("feedback review queue cannot declare writes")
        for item in self.items:
            item.validate()

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def pending_count(self) -> int:
        return sum(1 for item in self.items if item.status == PENDING_REVIEW)

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "queue_status": self.queue_status,
            "item_count": self.item_count,
            "pending_count": self.pending_count,
            "source_log_paths": list(self.source_log_paths),
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "writes": list(self.writes),
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class PulseFeedbackReviewDecision:
    """In-memory operator decision contract for a feedback candidate."""

    decision_id: str
    candidate_id: str
    decision_type: str
    reviewer: str = "operator"
    operator_note: str = ""
    created_at: str = field(default_factory=now_utc)
    status: str = CONTRACT_ONLY
    review_required: bool = True
    canonical_writeback_allowed: bool = False
    applies_feedback_to_source_deck: bool = False
    approves_memory: bool = False
    creates_task: bool = False
    mutates_canonical_state: bool = False
    persists_decision: bool = False

    def validate(self) -> None:
        if not self.decision_id:
            raise ValueError("decision_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if self.decision_type not in REVIEW_DECISION_TYPES:
            raise ValueError(f"decision_type must be one of {sorted(REVIEW_DECISION_TYPES)}")
        if not self.reviewer:
            raise ValueError("reviewer is required")
        if self.status != CONTRACT_ONLY:
            raise ValueError("feedback review decisions are contract-only in this pass")
        if not self.review_required:
            raise ValueError("feedback review decisions require review context")
        if self.canonical_writeback_allowed:
            raise ValueError("feedback review decisions cannot allow canonical writeback")
        if self.applies_feedback_to_source_deck:
            raise ValueError("feedback review decisions cannot apply feedback to source decks")
        if self.approves_memory:
            raise ValueError("feedback review decisions cannot approve memory")
        if self.creates_task:
            raise ValueError("feedback review decisions cannot create tasks")
        if self.mutates_canonical_state:
            raise ValueError("feedback review decisions cannot mutate canonical state")
        if self.persists_decision:
            raise ValueError("feedback review decisions are not persisted in this pass")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class PulseFeedbackApplyContract:
    """Non-executing application contract for a reviewed feedback candidate."""

    contract_id: str
    candidate_id: str
    decision_id: str
    decision_type: str
    status: str = CONTRACT_ONLY
    allowed_effects: tuple[str, ...] = field(default_factory=tuple)
    blocked_effects: tuple[str, ...] = BLOCKED_REVIEW_EFFECTS
    writes: list[str] = field(default_factory=list)
    canonical_writeback_allowed: bool = False
    applies_feedback_to_source_deck: bool = False
    approves_memory: bool = False
    creates_task: bool = False
    mutates_canonical_state: bool = False
    requires_separate_approval_for: tuple[str, ...] = (
        "memory_approval",
        "task_creation",
        "project_file_mutation",
        "knowledge_promotion",
        "schedule_activation",
        "provider_call",
        "connector_call",
    )

    def validate(self) -> None:
        if not self.contract_id:
            raise ValueError("contract_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.decision_id:
            raise ValueError("decision_id is required")
        if self.decision_type not in REVIEW_DECISION_TYPES:
            raise ValueError(f"decision_type must be one of {sorted(REVIEW_DECISION_TYPES)}")
        if self.status != CONTRACT_ONLY:
            raise ValueError("feedback apply contracts are contract-only in this pass")
        if self.writes:
            raise ValueError("feedback apply contracts cannot declare writes")
        if self.canonical_writeback_allowed:
            raise ValueError("feedback apply contracts cannot allow canonical writeback")
        if self.applies_feedback_to_source_deck:
            raise ValueError("feedback apply contracts cannot apply feedback to source decks")
        if self.approves_memory:
            raise ValueError("feedback apply contracts cannot approve memory")
        if self.creates_task:
            raise ValueError("feedback apply contracts cannot create tasks")
        if self.mutates_canonical_state:
            raise ValueError("feedback apply contracts cannot mutate canonical state")
        if "canonical_writeback" not in self.blocked_effects:
            raise ValueError("feedback apply contracts must block canonical writeback")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _source_log_paths(vault: Path, log_path: str | Path | None) -> list[str]:
    root = (vault / FEEDBACK_CANDIDATE_ROOT).resolve()
    if log_path is not None:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        return [_relative_to_vault(vault, target)]
    if not root.exists():
        return []
    return [_relative_to_vault(vault, path) for path in sorted(root.glob("*-feedback-candidates.jsonl"))]


def _id(prefix: str, *parts: str) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def build_feedback_review_queue(
    vault_root: str | Path,
    *,
    log_path: str | Path | None = None,
) -> PulseFeedbackReviewQueue:
    """Build a read-only pending feedback candidate queue snapshot."""
    vault = _vault_path(vault_root)
    candidates = load_feedback_candidates(vault, log_path=log_path)
    items = [
        PulseFeedbackReviewItem.from_candidate(candidate)
        for candidate in candidates
        if candidate.status == PENDING_REVIEW
    ]
    queue = PulseFeedbackReviewQueue(
        items=items,
        source_log_paths=_source_log_paths(vault, log_path),
    )
    queue.validate()
    return queue


def build_review_decision(
    candidate: PulseFeedbackCandidate | PulseFeedbackReviewItem,
    *,
    decision_type: str,
    reviewer: str = "operator",
    operator_note: str = "",
    created_at: str | None = None,
) -> PulseFeedbackReviewDecision:
    """Create an in-memory review decision without persisting or applying it."""
    candidate.validate()
    timestamp = created_at or now_utc()
    decision = PulseFeedbackReviewDecision(
        decision_id=_id(
            "pulse-feedback-review",
            candidate.candidate_id,
            decision_type,
            reviewer,
            operator_note,
            timestamp,
        ),
        candidate_id=candidate.candidate_id,
        decision_type=decision_type,
        reviewer=reviewer,
        operator_note=operator_note,
        created_at=timestamp,
    )
    decision.validate()
    return decision


def build_apply_contract(
    candidate: PulseFeedbackCandidate | PulseFeedbackReviewItem,
    decision: PulseFeedbackReviewDecision,
) -> PulseFeedbackApplyContract:
    """Create a non-executing apply contract for a review decision."""
    candidate.validate()
    decision.validate()
    if decision.candidate_id != candidate.candidate_id:
        raise ValueError("decision candidate_id does not match feedback candidate")
    contract = PulseFeedbackApplyContract(
        contract_id=_id(
            "pulse-feedback-apply-contract",
            candidate.candidate_id,
            decision.decision_id,
            decision.decision_type,
        ),
        candidate_id=candidate.candidate_id,
        decision_id=decision.decision_id,
        decision_type=decision.decision_type,
        allowed_effects=DECISION_ALLOWED_EFFECTS[decision.decision_type],
    )
    contract.validate()
    return contract


def build_review_apply_contract(
    candidate: PulseFeedbackCandidate | PulseFeedbackReviewItem,
    *,
    decision_type: str,
    reviewer: str = "operator",
    operator_note: str = "",
    created_at: str | None = None,
) -> tuple[PulseFeedbackReviewDecision, PulseFeedbackApplyContract]:
    """Convenience helper for a decision plus its non-executing apply contract."""
    decision = build_review_decision(
        candidate,
        decision_type=decision_type,
        reviewer=reviewer,
        operator_note=operator_note,
        created_at=created_at,
    )
    return decision, build_apply_contract(candidate, decision)
