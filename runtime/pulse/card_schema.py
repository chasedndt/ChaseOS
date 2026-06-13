"""Schema primitives for ChaseOS Pulse cards and decks.

Pulse cards are proposal and briefing artifacts. They are not canonical
knowledge, do not mutate Now.md or Project-OS files, and do not promote content
to 02_KNOWLEDGE/ without a separate Gate-governed workflow.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


CARD_AUDIENCES = {"user", "agent", "shared", "shared_coordination"}

USER_CARD_CLASSES = {
    "Today's Operating Brief",
    "Future Prep",
    "Project Momentum",
    "Business OS Opportunity",
    "Learning / University Focus",
    "Content / Brand Edge",
    "Trading / Market Watch",
    "Research Watch",
    "Memory Update",
    "Personal Map Update",
    "Manual Input Needed",
    "Decision Needed",
    "Risk / Blocker",
    "Runtime Blocker",
    "Carry-Forward",
    "Schedule Catch-Up",
    "Suggested Delegation",
}

AGENT_CARD_CLASSES = {
    "Runtime Reflection",
    "Error Cluster",
    "Skill Gap",
    "Permission Request",
    "Workflow Improvement",
    "SOP Needed",
    "Tool Needed",
    "Connector Needed",
    "Self-Upgrade Proposal",
    "Memory Drift Warning",
    "Execution Repair Pattern",
    "Runtime Navigation Update",
    "Capability Gap",
    "Autonomy Envelope Suggestion",
}

SHARED_CARD_CLASSES = {
    "Agent Handoff",
    "AOR Pending Decision",
    "Multi-Agent Coordination",
    "Governance Risk",
    "Source Conflict",
    "Review Queue",
    "Cross-Runtime Blocker",
    "Schedule / Delivery Failure",
    "Promotion Candidate",
    "Truth-State Warning",
}

CARD_CLASSES_BY_AUDIENCE = {
    "user": USER_CARD_CLASSES,
    "agent": AGENT_CARD_CLASSES,
    "shared": SHARED_CARD_CLASSES,
    "shared_coordination": SHARED_CARD_CLASSES,
}

ACTION_TYPES = {
    "review",
    "decide",
    "snooze",
    "add_context",
    "open_source",
    "create_task",
    "request_permission",
    "propose_memory_candidate",
    "request_manual_input",
    "run_catchup_pulse",
    "delegate",
    "save",
    "turn_into_task",
    "promote_to_memory",
    "link_to_project",
    "link_to_personal_map",
    "link_to_agent_brain",
    "create_sop_draft",
    "propose_sop",
    "create_manual_input_card_template",
    "create_feature_candidate",
    "update_runtime_navigation_map",
    "approve_memory",
    "edit_memory",
    "reject_memory",
    "run_truth_audit",
    "write_log_artifact",
    "skip",
}

FEEDBACK_TYPES = {
    "accepted",
    "dismissed",
    "snoozed",
    "corrected",
    "needs_more_evidence",
    "memory_candidate",
    "thumbs_up",
    "thumbs_down",
    "show_more_like_this",
    "show_less_like_this",
    "never_show_this",
    "save",
    "delegate",
    "turn_into_task",
    "promote_to_memory",
    "link_to_project",
    "link_to_personal_map",
    "link_to_agent_brain",
    "dismiss",
}

PROMOTION_STATUSES = {
    "not_promoted",
    "candidate",
    "pending_review",
    "approved_memory",
    "approved_project_update",
    "approved_knowledge_promotion",
    "rejected",
    "archived",
}

WRITEBACK_STATUSES = {
    "draft_only",
    "card_generated",
    "card_saved",
    "card_archived",
    "task_candidate",
    "memory_candidate",
    "memory_approved",
    "project_update_approved",
    "knowledge_promotion_approved",
    "blocked",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_card_class(card_class: str) -> str:
    """Normalize common punctuation variants while keeping display text stable."""
    return card_class.replace("\u2019", "'").replace("â€™", "'").strip()


def card_class_to_type(card_class: str) -> str:
    """Return the stable machine-style card type for a display card class."""
    normalized = normalize_card_class(card_class).lower().replace("/", " ")
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def validate_card_class(audience: str, card_class: str) -> None:
    if audience not in CARD_AUDIENCES:
        raise ValueError(f"audience must be one of {sorted(CARD_AUDIENCES)}")
    normalized = normalize_card_class(card_class)
    if normalized not in CARD_CLASSES_BY_AUDIENCE[audience]:
        allowed = sorted(CARD_CLASSES_BY_AUDIENCE[audience])
        raise ValueError(
            f"card_class {card_class!r} is not valid for audience {audience!r}. "
            f"Allowed: {allowed}"
        )


@dataclass
class EvidenceRef:
    source_path: str
    source_type: str
    summary: str
    trust_label: str = "unverified"
    observed_at: str | None = None
    quote: str | None = None
    source_url: str | None = None

    def validate(self) -> None:
        if not self.source_path:
            raise ValueError("evidence.source_path is required")
        if not self.source_type:
            raise ValueError("evidence.source_type is required")
        if not self.summary:
            raise ValueError("evidence.summary is required")


@dataclass
class SourceLinkRef:
    label: str
    path: str | None = None
    url: str | None = None
    source_type: str = "local"

    def validate(self) -> None:
        if not self.label:
            raise ValueError("source link label is required")
        if not self.path and not self.url:
            raise ValueError("source links require a path or url")


@dataclass
class PulseCardScope:
    user_id: str | None = None
    agent_id: str | None = None
    project_ids: list[str] = field(default_factory=list)
    coordination_ids: list[str] = field(default_factory=list)

    def validate(self) -> None:
        for value in self.project_ids + self.coordination_ids:
            if not value:
                raise ValueError("scope ids cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class RelatedNodeRef:
    node_id: str
    node_type: str
    relation: str
    label: str = ""

    def validate(self) -> None:
        if not self.node_id:
            raise ValueError("related node_id is required")
        if not self.node_type:
            raise ValueError("related node_type is required")
        if not self.relation:
            raise ValueError("related relation is required")


@dataclass
class ThumbnailRef:
    path: str
    alt: str
    source_type: str = "local"

    def validate(self) -> None:
        if not self.path:
            raise ValueError("thumbnail.path is required")
        if not self.alt:
            raise ValueError("thumbnail.alt is required")


@dataclass
class RecommendedAction:
    action_id: str
    label: str
    action_type: str
    target_ref: str | None = None
    requires_operator_approval: bool = True
    mutates_canonical_state: bool = False

    def validate(self) -> None:
        if not self.action_id:
            raise ValueError("recommended action_id is required")
        if not self.label:
            raise ValueError("recommended action label is required")
        if self.action_type not in ACTION_TYPES:
            raise ValueError(f"action_type must be one of {sorted(ACTION_TYPES)}")
        if self.mutates_canonical_state and not self.requires_operator_approval:
            raise ValueError("canonical mutations require operator approval")


@dataclass
class PulseFeedback:
    feedback_type: str
    operator_note: str = ""
    created_at: str = field(default_factory=now_utc)
    reviewed_by: str = "operator"

    def validate(self) -> None:
        if self.feedback_type not in FEEDBACK_TYPES:
            raise ValueError(f"feedback_type must be one of {sorted(FEEDBACK_TYPES)}")


@dataclass
class PulseCard:
    card_id: str
    audience: str
    card_class: str
    title: str
    summary: str
    deck_id: str | None = None
    created_at: str | None = None
    scope: PulseCardScope = field(default_factory=PulseCardScope)
    type: str | None = None
    why_it_matters: str = ""
    generated_at: str = field(default_factory=now_utc)
    evidence: list[EvidenceRef] = field(default_factory=list)
    source_links: list[SourceLinkRef] = field(default_factory=list)
    related_nodes: list[RelatedNodeRef] = field(default_factory=list)
    thumbnails: list[ThumbnailRef] = field(default_factory=list)
    recommended_actions: list[RecommendedAction] = field(default_factory=list)
    feedback: list[PulseFeedback] = field(default_factory=list)
    urgency: int = 0
    confidence: float = 0.0
    promotion_status: str = "not_promoted"
    writeback_status: str = "draft_only"
    governance_state: str = "proposal"
    canonical_writeback_enabled: bool = False

    def validate(self) -> None:
        if not self.card_id:
            raise ValueError("card_id is required")
        validate_card_class(self.audience, self.card_class)
        self.card_class = normalize_card_class(self.card_class)
        if not self.title:
            raise ValueError("title is required")
        if not self.summary:
            raise ValueError("summary is required")
        if self.created_at is None:
            self.created_at = self.generated_at
        if self.type is None:
            self.type = card_class_to_type(self.card_class)
        if not self.type:
            raise ValueError("card type is required")
        if self.scope is None:
            self.scope = PulseCardScope()
        self.scope.validate()
        if not 0 <= self.urgency <= 5:
            raise ValueError("urgency must be between 0 and 5")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.promotion_status not in PROMOTION_STATUSES:
            raise ValueError(f"promotion_status must be one of {sorted(PROMOTION_STATUSES)}")
        if self.writeback_status not in WRITEBACK_STATUSES:
            raise ValueError(f"writeback_status must be one of {sorted(WRITEBACK_STATUSES)}")
        if self.canonical_writeback_enabled:
            raise ValueError("Pulse cards cannot enable canonical writeback by default")
        for item in self.evidence:
            item.validate()
        for link in self.source_links:
            link.validate()
        for node in self.related_nodes:
            node.validate()
        for thumbnail in self.thumbnails:
            thumbnail.validate()
        for action in self.recommended_actions:
            action.validate()
        for item in self.feedback:
            item.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PulseCard":
        card = cls(
            card_id=str(data.get("card_id") or ""),
            audience=str(data.get("audience") or ""),
            card_class=str(data.get("card_class") or ""),
            title=str(data.get("title") or ""),
            summary=str(data.get("summary") or ""),
            deck_id=data.get("deck_id"),
            created_at=data.get("created_at"),
            scope=PulseCardScope(**(data.get("scope") or {})),
            type=data.get("type"),
            why_it_matters=str(data.get("why_it_matters") or ""),
            generated_at=str(data.get("generated_at") or now_utc()),
            evidence=[EvidenceRef(**item) for item in data.get("evidence", [])],
            source_links=[SourceLinkRef(**item) for item in data.get("source_links", [])],
            related_nodes=[RelatedNodeRef(**item) for item in data.get("related_nodes", [])],
            thumbnails=[ThumbnailRef(**item) for item in data.get("thumbnails", [])],
            recommended_actions=[
                RecommendedAction(**item) for item in data.get("recommended_actions", [])
            ],
            feedback=[PulseFeedback(**item) for item in data.get("feedback", [])],
            urgency=int(data.get("urgency", 0)),
            confidence=float(data.get("confidence", 0.0)),
            promotion_status=str(data.get("promotion_status") or "not_promoted"),
            writeback_status=str(data.get("writeback_status") or "draft_only"),
            governance_state=str(data.get("governance_state") or "proposal"),
            canonical_writeback_enabled=bool(data.get("canonical_writeback_enabled", False)),
        )
        card.validate()
        return card


@dataclass
class PulseDeck:
    deck_id: str
    audience: str
    generated_at: str = field(default_factory=now_utc)
    cards: list[PulseCard] = field(default_factory=list)
    source_summary: list[str] = field(default_factory=list)
    schedule_ref: str | None = None
    feedback_policy_ref: str = "06_AGENTS/Pulse-Feedback-Policy.md"
    canonical_writeback_enabled: bool = False

    def validate(self) -> None:
        if not self.deck_id:
            raise ValueError("deck_id is required")
        if self.audience not in CARD_AUDIENCES:
            raise ValueError(f"audience must be one of {sorted(CARD_AUDIENCES)}")
        if self.canonical_writeback_enabled:
            raise ValueError("Pulse decks cannot enable canonical writeback by default")
        for card in self.cards:
            if card.deck_id is None:
                card.deck_id = self.deck_id
            card.validate()
            if card.audience != self.audience:
                raise ValueError("all cards in a deck must match the deck audience")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PulseDeck":
        deck = cls(
            deck_id=str(data.get("deck_id") or ""),
            audience=str(data.get("audience") or ""),
            generated_at=str(data.get("generated_at") or now_utc()),
            cards=[PulseCard.from_dict(item) for item in data.get("cards", [])],
            source_summary=[str(item) for item in data.get("source_summary", [])],
            schedule_ref=data.get("schedule_ref"),
            feedback_policy_ref=str(
                data.get("feedback_policy_ref") or "06_AGENTS/Pulse-Feedback-Policy.md"
            ),
            canonical_writeback_enabled=bool(data.get("canonical_writeback_enabled", False)),
        )
        deck.validate()
        return deck
