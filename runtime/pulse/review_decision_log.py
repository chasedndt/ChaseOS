"""Persisted, non-applying review decisions for ChaseOS Pulse candidates.

The decision log records operator review intent under the Pulse log tree. It
does not apply feedback, mutate Personal Map nodes, update runtime repair
memory, create tasks/SOPs, expand permissions, or promote canonical knowledge.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.agents.repair_candidate_store import ExecutionRepairMemoryCandidate
from runtime.memory.candidate_store import PersonalMapCandidate
from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback import PulseFeedbackCandidate


REVIEW_DECISION_ROOT = Path("07_LOGS") / "Pulse-Decks" / "review-decisions"
DECISION_RECORDED = "recorded"
REVIEW_DECISION_STATUSES = {DECISION_RECORDED}
CANDIDATE_KINDS = {"feedback", "personal_map", "execution_repair"}

REVIEW_DECISION_TYPES_BY_KIND = {
    "feedback": {
        "accept_for_future_ranking",
        "reject_candidate",
        "defer_candidate",
        "request_more_context",
        "mark_duplicate",
        "request_revision",
    },
    "personal_map": {
        "approve_for_future_apply",
        "reject_candidate",
        "defer_candidate",
        "request_more_context",
        "mark_duplicate",
        "request_revision",
    },
    "execution_repair": {
        "approve_for_future_apply",
        "reject_candidate",
        "defer_candidate",
        "request_more_context",
        "mark_duplicate",
        "request_revision",
    },
}
REVIEW_DECISION_TYPES = set().union(*REVIEW_DECISION_TYPES_BY_KIND.values())

REVIEW_DECISION_BLOCKED_EFFECTS = (
    "source_deck_mutation",
    "feedback_application",
    "personal_map_mutation",
    "runtime_memory_mutation",
    "memory_approval",
    "task_creation",
    "sop_creation",
    "runtime_navigation_map_update",
    "agent_identity_ledger_update",
    "permission_expansion",
    "project_file_mutation",
    "knowledge_promotion",
    "canonical_writeback",
    "schedule_activation",
    "provider_call",
    "connector_call",
    "second_datastore_write",
)

DECISION_FOLLOWUP_SIGNALS = {
    "accept_for_future_ranking": ("future_ranking_signal",),
    "approve_for_future_apply": ("future_apply_review_signal",),
    "reject_candidate": ("candidate_rejection_signal",),
    "defer_candidate": ("deferred_review_signal",),
    "request_more_context": ("more_context_requested_signal",),
    "mark_duplicate": ("duplicate_candidate_signal",),
    "request_revision": ("candidate_revision_requested_signal",),
}


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


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    if not slug or slug in {".", ".."} or ".." in slug:
        raise ValueError("review decision slug is invalid")
    return slug


def _date_slug(created_at: str) -> str:
    candidate = (created_at or now_utc())[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return now_utc()[:10]
    return candidate


def _id(prefix: str, *parts: str) -> str:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _candidate_kind(candidate: Any) -> str:
    if isinstance(candidate, PulseFeedbackCandidate):
        return "feedback"
    if isinstance(candidate, PersonalMapCandidate):
        return "personal_map"
    if isinstance(candidate, ExecutionRepairMemoryCandidate):
        return "execution_repair"
    raise TypeError("unsupported Pulse candidate type")


def _candidate_metadata(candidate: Any) -> dict[str, str | None]:
    if isinstance(candidate, PulseFeedbackCandidate):
        return {
            "source_card_id": candidate.card_id,
            "source_deck_path": candidate.source_deck_path,
            "runtime_id": None,
            "target_ref": candidate.card_id,
        }
    if isinstance(candidate, PersonalMapCandidate):
        target_ref = None
        if candidate.node is not None:
            target_ref = candidate.node.node_id
        if candidate.edge is not None:
            target_ref = candidate.edge.edge_id
        return {
            "source_card_id": candidate.source_card_id,
            "source_deck_path": candidate.source_deck_path,
            "runtime_id": None,
            "target_ref": target_ref,
        }
    if isinstance(candidate, ExecutionRepairMemoryCandidate):
        return {
            "source_card_id": candidate.source_card_id,
            "source_deck_path": candidate.source_deck_path,
            "runtime_id": candidate.runtime_id,
            "target_ref": candidate.entry.repair_id,
        }
    raise TypeError("unsupported Pulse candidate type")


@dataclass
class PulseCandidateReviewDecision:
    """A persisted review decision that does not apply candidate effects."""

    decision_id: str
    candidate_id: str
    candidate_kind: str
    decision_type: str
    reviewer: str = "operator"
    operator_note: str = ""
    created_at: str = field(default_factory=now_utc)
    source_candidate_log_path: str | None = None
    source_card_id: str | None = None
    source_deck_path: str | None = None
    runtime_id: str | None = None
    target_ref: str | None = None
    status: str = DECISION_RECORDED
    decision_record_only: bool = True
    persisted_decision: bool = True
    canonical_writeback_allowed: bool = False
    applies_feedback_to_source_deck: bool = False
    applies_personal_map_update: bool = False
    applies_runtime_repair_memory: bool = False
    approves_memory: bool = False
    creates_task: bool = False
    creates_sop: bool = False
    updates_runtime_navigation_map: bool = False
    updates_agent_identity_ledger: bool = False
    expands_permissions: bool = False
    mutates_canonical_state: bool = False
    calls_provider_or_connector: bool = False
    second_datastore_write_allowed: bool = False
    followup_signals: tuple[str, ...] = field(default_factory=tuple)
    blocked_effects: tuple[str, ...] = REVIEW_DECISION_BLOCKED_EFFECTS

    def validate(self) -> None:
        if not self.decision_id:
            raise ValueError("decision_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if self.candidate_kind not in CANDIDATE_KINDS:
            raise ValueError(f"candidate_kind must be one of {sorted(CANDIDATE_KINDS)}")
        if self.decision_type not in REVIEW_DECISION_TYPES_BY_KIND[self.candidate_kind]:
            allowed = sorted(REVIEW_DECISION_TYPES_BY_KIND[self.candidate_kind])
            raise ValueError(
                f"decision_type {self.decision_type!r} is not valid for "
                f"{self.candidate_kind!r}. Allowed: {allowed}"
            )
        if not self.reviewer:
            raise ValueError("reviewer is required")
        if self.status not in REVIEW_DECISION_STATUSES:
            raise ValueError(f"status must be one of {sorted(REVIEW_DECISION_STATUSES)}")
        if not self.decision_record_only:
            raise ValueError("Pulse review decisions must remain record-only")
        if not self.persisted_decision:
            raise ValueError("Pulse review decisions in this lane are persisted records")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse review decisions cannot allow canonical writeback")
        if self.applies_feedback_to_source_deck:
            raise ValueError("Pulse review decisions cannot apply feedback")
        if self.applies_personal_map_update:
            raise ValueError("Pulse review decisions cannot apply Personal Map updates")
        if self.applies_runtime_repair_memory:
            raise ValueError("Pulse review decisions cannot apply runtime repair memory")
        if self.approves_memory:
            raise ValueError("Pulse review decisions cannot approve memory")
        if self.creates_task:
            raise ValueError("Pulse review decisions cannot create tasks")
        if self.creates_sop:
            raise ValueError("Pulse review decisions cannot create SOPs")
        if self.updates_runtime_navigation_map:
            raise ValueError("Pulse review decisions cannot update runtime navigation maps")
        if self.updates_agent_identity_ledger:
            raise ValueError("Pulse review decisions cannot update Agent Identity Ledgers")
        if self.expands_permissions:
            raise ValueError("Pulse review decisions cannot expand permissions")
        if self.mutates_canonical_state:
            raise ValueError("Pulse review decisions cannot mutate canonical state")
        if self.calls_provider_or_connector:
            raise ValueError("Pulse review decisions cannot call providers or connectors")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse review decisions cannot write a second datastore")
        if set(self.blocked_effects) != set(REVIEW_DECISION_BLOCKED_EFFECTS):
            raise ValueError("Pulse review decisions must declare blocked effects")
        expected_signals = set(DECISION_FOLLOWUP_SIGNALS[self.decision_type])
        if set(self.followup_signals) != expected_signals:
            raise ValueError("Pulse review decisions must declare expected followup signals")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PulseCandidateReviewDecision":
        decision = cls(
            decision_id=str(data.get("decision_id") or ""),
            candidate_id=str(data.get("candidate_id") or ""),
            candidate_kind=str(data.get("candidate_kind") or ""),
            decision_type=str(data.get("decision_type") or ""),
            reviewer=str(data.get("reviewer") or "operator"),
            operator_note=str(data.get("operator_note") or ""),
            created_at=str(data.get("created_at") or now_utc()),
            source_candidate_log_path=data.get("source_candidate_log_path"),
            source_card_id=data.get("source_card_id"),
            source_deck_path=data.get("source_deck_path"),
            runtime_id=data.get("runtime_id"),
            target_ref=data.get("target_ref"),
            status=str(data.get("status") or DECISION_RECORDED),
            decision_record_only=bool(data.get("decision_record_only", True)),
            persisted_decision=bool(data.get("persisted_decision", True)),
            canonical_writeback_allowed=bool(data.get("canonical_writeback_allowed", False)),
            applies_feedback_to_source_deck=bool(
                data.get("applies_feedback_to_source_deck", False)
            ),
            applies_personal_map_update=bool(data.get("applies_personal_map_update", False)),
            applies_runtime_repair_memory=bool(
                data.get("applies_runtime_repair_memory", False)
            ),
            approves_memory=bool(data.get("approves_memory", False)),
            creates_task=bool(data.get("creates_task", False)),
            creates_sop=bool(data.get("creates_sop", False)),
            updates_runtime_navigation_map=bool(
                data.get("updates_runtime_navigation_map", False)
            ),
            updates_agent_identity_ledger=bool(
                data.get("updates_agent_identity_ledger", False)
            ),
            expands_permissions=bool(data.get("expands_permissions", False)),
            mutates_canonical_state=bool(data.get("mutates_canonical_state", False)),
            calls_provider_or_connector=bool(data.get("calls_provider_or_connector", False)),
            second_datastore_write_allowed=bool(
                data.get("second_datastore_write_allowed", False)
            ),
            followup_signals=tuple(data.get("followup_signals", ())),
            blocked_effects=tuple(data.get("blocked_effects", REVIEW_DECISION_BLOCKED_EFFECTS)),
        )
        decision.validate()
        return decision


@dataclass
class PulseCandidateReviewDecisionArtifact:
    path: str
    decision_id: str
    candidate_id: str
    candidate_kind: str
    decision_type: str
    status: str = DECISION_RECORDED
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False

    def validate(self) -> None:
        if not self.path:
            raise ValueError("review decision artifact path is required")
        if not self.decision_id:
            raise ValueError("decision_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if self.candidate_kind not in CANDIDATE_KINDS:
            raise ValueError(f"candidate_kind must be one of {sorted(CANDIDATE_KINDS)}")
        if self.decision_type not in REVIEW_DECISION_TYPES:
            raise ValueError(f"decision_type must be one of {sorted(REVIEW_DECISION_TYPES)}")
        if self.status != DECISION_RECORDED:
            raise ValueError("review decision artifacts must be recorded decisions")
        if self.canonical_writeback_allowed:
            raise ValueError("review decision artifacts cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("review decision artifacts cannot write a second datastore")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class PulseCandidateReviewDecisionLedger:
    generated_at: str = field(default_factory=now_utc)
    items: list[PulseCandidateReviewDecision] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    ledger_status: str = "read_only"
    writes: list[str] = field(default_factory=list)
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False
    blocked_effects: tuple[str, ...] = REVIEW_DECISION_BLOCKED_EFFECTS

    @property
    def item_count(self) -> int:
        return len(self.items)

    def validate(self) -> None:
        if self.ledger_status != "read_only":
            raise ValueError("review decision ledger snapshots are read-only")
        if self.writes:
            raise ValueError("review decision ledger snapshots cannot declare writes")
        if self.canonical_writeback_allowed:
            raise ValueError("review decision ledgers cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("review decision ledgers cannot write a second datastore")
        if set(self.blocked_effects) != set(REVIEW_DECISION_BLOCKED_EFFECTS):
            raise ValueError("review decision ledgers must declare blocked effects")
        for item in self.items:
            item.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "ledger_status": self.ledger_status,
            "item_count": self.item_count,
            "source_log_paths": list(self.source_log_paths),
            "writes": list(self.writes),
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "blocked_effects": list(self.blocked_effects),
            "items": [item.to_dict() for item in self.items],
        }


def build_review_decision(
    candidate: PulseFeedbackCandidate | PersonalMapCandidate | ExecutionRepairMemoryCandidate,
    *,
    decision_type: str,
    reviewer: str = "operator",
    operator_note: str = "",
    source_candidate_log_path: str | None = None,
    created_at: str | None = None,
) -> PulseCandidateReviewDecision:
    candidate.validate()
    kind = _candidate_kind(candidate)
    if decision_type not in REVIEW_DECISION_TYPES:
        raise ValueError(f"decision_type must be one of {sorted(REVIEW_DECISION_TYPES)}")
    metadata = _candidate_metadata(candidate)
    timestamp = created_at or now_utc()
    decision = PulseCandidateReviewDecision(
        decision_id=_id(
            "pulse-review-decision",
            kind,
            candidate.candidate_id,
            decision_type,
            reviewer,
            operator_note,
            timestamp,
        ),
        candidate_id=candidate.candidate_id,
        candidate_kind=kind,
        decision_type=decision_type,
        reviewer=reviewer,
        operator_note=operator_note,
        created_at=timestamp,
        source_candidate_log_path=source_candidate_log_path,
        source_card_id=metadata["source_card_id"],
        source_deck_path=metadata["source_deck_path"],
        runtime_id=metadata["runtime_id"],
        target_ref=metadata["target_ref"],
        followup_signals=DECISION_FOLLOWUP_SIGNALS[decision_type],
    )
    decision.validate()
    return decision


def review_decision_log_path(
    vault_root: str | Path,
    *,
    created_at: str | None = None,
) -> Path:
    vault = _vault_path(vault_root)
    root = (vault / REVIEW_DECISION_ROOT).resolve()
    path = root / f"{_date_slug(created_at or now_utc())}-review-decisions.jsonl"
    _assert_inside(path, root, "Pulse review decision logs must stay inside review-decisions/")
    return path


def persist_review_decision(
    vault_root: str | Path,
    decision: PulseCandidateReviewDecision,
) -> PulseCandidateReviewDecisionArtifact:
    decision.validate()
    vault = _vault_path(vault_root)
    path = review_decision_log_path(vault, created_at=decision.created_at)
    root = (vault / REVIEW_DECISION_ROOT).resolve()
    _assert_inside(path, root, "Pulse review decision logs must stay inside review-decisions/")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision.to_dict(), sort_keys=True))
        handle.write("\n")

    artifact = PulseCandidateReviewDecisionArtifact(
        path=_relative_to_vault(vault, path),
        decision_id=decision.decision_id,
        candidate_id=decision.candidate_id,
        candidate_kind=decision.candidate_kind,
        decision_type=decision.decision_type,
        status=decision.status,
        canonical_writeback_allowed=False,
        second_datastore_write_allowed=False,
    )
    artifact.validate()
    return artifact


def load_review_decisions(
    vault_root: str | Path,
    *,
    log_path: str | Path | None = None,
    candidate_kind: str | None = None,
    candidate_id: str | None = None,
) -> list[PulseCandidateReviewDecision]:
    vault = _vault_path(vault_root)
    root = (vault / REVIEW_DECISION_ROOT).resolve()
    if candidate_kind is not None and candidate_kind not in CANDIDATE_KINDS:
        raise ValueError(f"candidate_kind must be one of {sorted(CANDIDATE_KINDS)}")
    if log_path is None:
        paths = sorted(root.glob("*-review-decisions.jsonl")) if root.exists() else []
    else:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        _assert_inside(target, root, "Pulse review decision logs must stay inside review-decisions/")
        paths = [target]

    decisions: list[PulseCandidateReviewDecision] = []
    for path in paths:
        if not path.exists():
            continue
        _assert_inside(path, root, "Pulse review decision logs must stay inside review-decisions/")
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            decision = PulseCandidateReviewDecision.from_dict(json.loads(line))
            if candidate_kind is not None and decision.candidate_kind != candidate_kind:
                continue
            if candidate_id is not None and decision.candidate_id != candidate_id:
                continue
            decisions.append(decision)
    return decisions


def _source_log_paths(vault: Path, log_path: str | Path | None) -> list[str]:
    root = (vault / REVIEW_DECISION_ROOT).resolve()
    if log_path is not None:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        return [_relative_to_vault(vault, target)]
    if not root.exists():
        return []
    return [_relative_to_vault(vault, path) for path in sorted(root.glob("*-review-decisions.jsonl"))]


def build_review_decision_ledger(
    vault_root: str | Path,
    *,
    log_path: str | Path | None = None,
    candidate_kind: str | None = None,
    candidate_id: str | None = None,
) -> PulseCandidateReviewDecisionLedger:
    vault = _vault_path(vault_root)
    ledger = PulseCandidateReviewDecisionLedger(
        items=load_review_decisions(
            vault,
            log_path=log_path,
            candidate_kind=candidate_kind,
            candidate_id=candidate_id,
        ),
        source_log_paths=_source_log_paths(vault, log_path),
    )
    ledger.validate()
    return ledger
