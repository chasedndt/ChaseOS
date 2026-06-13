"""Read-only unified inspector for ChaseOS Pulse candidate lanes.

The inspector aggregates existing Pulse feedback candidates, Personal Map
candidates, execution repair candidates, and persisted review decisions into a
single in-memory snapshot. It does not apply decisions, mutate source logs,
write derived artifacts, call providers/connectors, or create a second
datastore.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.agents.repair_candidate_store import (
    REPAIR_BLOCKED_EFFECTS,
    REPAIR_CANDIDATE_ROOT,
    ExecutionRepairMemoryCandidate,
    load_execution_repair_memory_candidates,
)
from runtime.memory.candidate_store import (
    PERSONAL_MAP_BLOCKED_EFFECTS,
    PERSONAL_MAP_CANDIDATE_ROOT,
    PersonalMapCandidate,
    load_personal_map_candidates,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback import (
    FEEDBACK_CANDIDATE_ROOT,
    PulseFeedbackCandidate,
    load_feedback_candidates,
)
from runtime.pulse.review_decision_log import (
    REVIEW_DECISION_BLOCKED_EFFECTS,
    REVIEW_DECISION_ROOT,
    PulseCandidateReviewDecision,
    load_review_decisions,
)


INSPECTOR_ITEM_KINDS = {
    "feedback_candidate",
    "personal_map_candidate",
    "execution_repair_candidate",
    "review_decision",
}

INSPECTOR_CANDIDATE_KINDS = {
    "feedback",
    "personal_map",
    "execution_repair",
}

INSPECTOR_BLOCKED_EFFECTS = tuple(
    sorted(
        set(REVIEW_DECISION_BLOCKED_EFFECTS)
        | set(PERSONAL_MAP_BLOCKED_EFFECTS)
        | set(REPAIR_BLOCKED_EFFECTS)
        | {
            "source_deck_mutation",
            "feedback_application",
            "schedule_activation",
            "provider_call",
            "connector_call",
        }
    )
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _existing_jsonl_paths(vault: Path, root: Path, pattern: str) -> list[Path]:
    absolute_root = (vault / root).resolve()
    if not absolute_root.exists():
        return []
    paths = sorted(absolute_root.glob(pattern))
    for path in paths:
        _assert_inside(path, absolute_root, "Pulse inspector source logs must stay in lane root")
    return paths


@dataclass
class PulseCandidateInspectorItem:
    """Normalized read-only row for one candidate or review-decision record."""

    item_id: str
    item_kind: str
    record_id: str
    status: str
    title: str
    summary: str = ""
    candidate_kind: str | None = None
    candidate_id: str | None = None
    related_candidate_id: str | None = None
    record_type: str | None = None
    source_log_path: str | None = None
    source_card_id: str | None = None
    source_deck_path: str | None = None
    source_surface_path: str | None = None
    runtime_id: str | None = None
    target_ref: str | None = None
    decision_type: str | None = None
    created_at: str | None = None
    followup_signals: tuple[str, ...] = field(default_factory=tuple)
    inspector_read_only: bool = True
    applies_effects: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    blocked_effects: tuple[str, ...] = INSPECTOR_BLOCKED_EFFECTS

    def validate(self) -> None:
        if not self.item_id:
            raise ValueError("inspector item_id is required")
        if self.item_kind not in INSPECTOR_ITEM_KINDS:
            raise ValueError(f"item_kind must be one of {sorted(INSPECTOR_ITEM_KINDS)}")
        if not self.record_id:
            raise ValueError("inspector record_id is required")
        if not self.status:
            raise ValueError("inspector item status is required")
        if not self.title:
            raise ValueError("inspector item title is required")
        if self.candidate_kind is not None and self.candidate_kind not in INSPECTOR_CANDIDATE_KINDS:
            raise ValueError(
                f"candidate_kind must be one of {sorted(INSPECTOR_CANDIDATE_KINDS)}"
            )
        if not self.inspector_read_only:
            raise ValueError("Pulse candidate inspector items must remain read-only")
        if self.applies_effects:
            raise ValueError("Pulse candidate inspector items cannot apply effects")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse candidate inspector items cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse candidate inspector items cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse candidate inspector items cannot write a second datastore")
        if set(self.blocked_effects) != set(INSPECTOR_BLOCKED_EFFECTS):
            raise ValueError("Pulse candidate inspector items must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_feedback_candidate(
        cls,
        candidate: PulseFeedbackCandidate,
        *,
        source_log_path: str | None = None,
    ) -> "PulseCandidateInspectorItem":
        candidate.validate()
        item = cls(
            item_id=candidate.candidate_id,
            item_kind="feedback_candidate",
            record_id=candidate.candidate_id,
            status=candidate.status,
            title=f"Feedback candidate: {candidate.feedback_type}",
            summary=candidate.operator_note or f"Feedback candidate for card {candidate.card_id}.",
            candidate_kind="feedback",
            candidate_id=candidate.candidate_id,
            record_type=candidate.feedback_type,
            source_log_path=source_log_path,
            source_card_id=candidate.card_id,
            source_deck_path=candidate.source_deck_path,
            source_surface_path=candidate.source_surface_path,
            target_ref=candidate.card_id,
            created_at=candidate.created_at,
        )
        item.validate()
        return item

    @classmethod
    def from_personal_map_candidate(
        cls,
        candidate: PersonalMapCandidate,
        *,
        source_log_path: str | None = None,
    ) -> "PulseCandidateInspectorItem":
        candidate.validate()
        target_ref = None
        title_target = candidate.candidate_type
        if candidate.node is not None:
            target_ref = candidate.node.node_id
            title_target = candidate.node.label
        if candidate.edge is not None:
            target_ref = candidate.edge.edge_id
            title_target = candidate.edge.relation
        item = cls(
            item_id=candidate.candidate_id,
            item_kind="personal_map_candidate",
            record_id=candidate.candidate_id,
            status=candidate.status,
            title=f"Personal Map candidate: {title_target}",
            summary=candidate.reason,
            candidate_kind="personal_map",
            candidate_id=candidate.candidate_id,
            record_type=candidate.candidate_type,
            source_log_path=source_log_path,
            source_card_id=candidate.source_card_id,
            source_deck_path=candidate.source_deck_path,
            target_ref=target_ref,
            created_at=candidate.created_at,
        )
        item.validate()
        return item

    @classmethod
    def from_execution_repair_candidate(
        cls,
        candidate: ExecutionRepairMemoryCandidate,
        *,
        source_log_path: str | None = None,
    ) -> "PulseCandidateInspectorItem":
        candidate.validate()
        item = cls(
            item_id=candidate.candidate_id,
            item_kind="execution_repair_candidate",
            record_id=candidate.candidate_id,
            status=candidate.status,
            title=f"Execution repair candidate: {candidate.entry.failure_type}",
            summary=candidate.reason,
            candidate_kind="execution_repair",
            candidate_id=candidate.candidate_id,
            record_type=candidate.entry.failure_surface,
            source_log_path=source_log_path,
            source_card_id=candidate.source_card_id,
            source_deck_path=candidate.source_deck_path,
            runtime_id=candidate.runtime_id,
            target_ref=candidate.entry.repair_id,
            created_at=candidate.created_at,
        )
        item.validate()
        return item

    @classmethod
    def from_review_decision(
        cls,
        decision: PulseCandidateReviewDecision,
        *,
        source_log_path: str | None = None,
    ) -> "PulseCandidateInspectorItem":
        decision.validate()
        item = cls(
            item_id=decision.decision_id,
            item_kind="review_decision",
            record_id=decision.decision_id,
            status=decision.status,
            title=f"Review decision: {decision.decision_type}",
            summary=decision.operator_note,
            candidate_kind=decision.candidate_kind,
            related_candidate_id=decision.candidate_id,
            record_type=decision.decision_type,
            source_log_path=source_log_path,
            source_card_id=decision.source_card_id,
            source_deck_path=decision.source_deck_path,
            runtime_id=decision.runtime_id,
            target_ref=decision.target_ref,
            decision_type=decision.decision_type,
            created_at=decision.created_at,
            followup_signals=decision.followup_signals,
        )
        item.validate()
        return item


@dataclass
class PulseCandidateInspectorSnapshot:
    """Read-only aggregate view over Pulse candidate and review-decision lanes."""

    generated_at: str = field(default_factory=now_utc)
    items: list[PulseCandidateInspectorItem] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    inspector_status: str = "read_only"
    writes: list[str] = field(default_factory=list)
    canonical_writeback_allowed: bool = False
    applies_effects: bool = False
    second_datastore_write_allowed: bool = False
    blocked_effects: tuple[str, ...] = INSPECTOR_BLOCKED_EFFECTS

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def counts_by_kind(self) -> dict[str, int]:
        counts = {kind: 0 for kind in sorted(INSPECTOR_ITEM_KINDS)}
        for item in self.items:
            counts[item.item_kind] += 1
        return counts

    @property
    def decision_counts_by_candidate_id(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            if item.item_kind != "review_decision" or not item.related_candidate_id:
                continue
            counts[item.related_candidate_id] = counts.get(item.related_candidate_id, 0) + 1
        return counts

    def validate(self) -> None:
        if self.inspector_status != "read_only":
            raise ValueError("Pulse candidate inspector snapshots are read-only")
        if self.writes:
            raise ValueError("Pulse candidate inspector snapshots cannot declare writes")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse candidate inspector snapshots cannot allow canonical writeback")
        if self.applies_effects:
            raise ValueError("Pulse candidate inspector snapshots cannot apply effects")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse candidate inspector snapshots cannot write a second datastore")
        if set(self.blocked_effects) != set(INSPECTOR_BLOCKED_EFFECTS):
            raise ValueError("Pulse candidate inspector snapshots must declare blocked effects")
        for item in self.items:
            item.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "inspector_status": self.inspector_status,
            "item_count": self.item_count,
            "counts_by_kind": self.counts_by_kind,
            "decision_counts_by_candidate_id": self.decision_counts_by_candidate_id,
            "source_log_paths": list(self.source_log_paths),
            "writes": list(self.writes),
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "applies_effects": self.applies_effects,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "blocked_effects": list(self.blocked_effects),
            "items": [item.to_dict() for item in self.items],
        }


def discover_candidate_inspector_sources(vault_root: str | Path) -> list[str]:
    """Return existing candidate/review JSONL source paths without creating folders."""
    vault = _vault_path(vault_root)
    paths: list[Path] = []
    paths.extend(_existing_jsonl_paths(vault, FEEDBACK_CANDIDATE_ROOT, "*-feedback-candidates.jsonl"))
    paths.extend(
        _existing_jsonl_paths(
            vault,
            PERSONAL_MAP_CANDIDATE_ROOT,
            "*-personal-map-candidates.jsonl",
        )
    )
    paths.extend(
        _existing_jsonl_paths(
            vault,
            REPAIR_CANDIDATE_ROOT,
            "*/*-repair-candidates.jsonl",
        )
    )
    paths.extend(_existing_jsonl_paths(vault, REVIEW_DECISION_ROOT, "*-review-decisions.jsonl"))
    return [_relative_to_vault(vault, path) for path in sorted(paths)]


def _include_item(
    item: PulseCandidateInspectorItem,
    *,
    item_kinds: set[str] | None,
    candidate_kinds: set[str] | None,
    candidate_id: str | None,
) -> bool:
    if item_kinds is not None and item.item_kind not in item_kinds:
        return False
    if candidate_kinds is not None and item.candidate_kind not in candidate_kinds:
        return False
    if candidate_id is None:
        return True
    return item.candidate_id == candidate_id or item.related_candidate_id == candidate_id


def build_candidate_inspector_snapshot(
    vault_root: str | Path,
    *,
    item_kinds: set[str] | None = None,
    candidate_kinds: set[str] | None = None,
    candidate_id: str | None = None,
) -> PulseCandidateInspectorSnapshot:
    """Build a read-only in-memory aggregate over existing Pulse candidate lanes."""
    if item_kinds is not None and not item_kinds.issubset(INSPECTOR_ITEM_KINDS):
        raise ValueError(f"item_kinds must be a subset of {sorted(INSPECTOR_ITEM_KINDS)}")
    if candidate_kinds is not None and not candidate_kinds.issubset(INSPECTOR_CANDIDATE_KINDS):
        raise ValueError(
            f"candidate_kinds must be a subset of {sorted(INSPECTOR_CANDIDATE_KINDS)}"
        )

    vault = _vault_path(vault_root)
    items: list[PulseCandidateInspectorItem] = []

    for path in _existing_jsonl_paths(vault, FEEDBACK_CANDIDATE_ROOT, "*-feedback-candidates.jsonl"):
        source_ref = _relative_to_vault(vault, path)
        for candidate in load_feedback_candidates(vault, log_path=path):
            items.append(
                PulseCandidateInspectorItem.from_feedback_candidate(
                    candidate,
                    source_log_path=source_ref,
                )
            )

    for path in _existing_jsonl_paths(
        vault,
        PERSONAL_MAP_CANDIDATE_ROOT,
        "*-personal-map-candidates.jsonl",
    ):
        source_ref = _relative_to_vault(vault, path)
        for candidate in load_personal_map_candidates(vault, log_path=path):
            items.append(
                PulseCandidateInspectorItem.from_personal_map_candidate(
                    candidate,
                    source_log_path=source_ref,
                )
            )

    for path in _existing_jsonl_paths(vault, REPAIR_CANDIDATE_ROOT, "*/*-repair-candidates.jsonl"):
        source_ref = _relative_to_vault(vault, path)
        for candidate in load_execution_repair_memory_candidates(vault, log_path=path):
            items.append(
                PulseCandidateInspectorItem.from_execution_repair_candidate(
                    candidate,
                    source_log_path=source_ref,
                )
            )

    for path in _existing_jsonl_paths(vault, REVIEW_DECISION_ROOT, "*-review-decisions.jsonl"):
        source_ref = _relative_to_vault(vault, path)
        for decision in load_review_decisions(vault, log_path=path):
            items.append(
                PulseCandidateInspectorItem.from_review_decision(
                    decision,
                    source_log_path=source_ref,
                )
            )

    filtered = [
        item
        for item in sorted(items, key=lambda value: (value.created_at or "", value.item_kind, value.item_id))
        if _include_item(
            item,
            item_kinds=item_kinds,
            candidate_kinds=candidate_kinds,
            candidate_id=candidate_id,
        )
    ]
    snapshot = PulseCandidateInspectorSnapshot(
        items=filtered,
        source_log_paths=discover_candidate_inspector_sources(vault),
    )
    snapshot.validate()
    return snapshot
