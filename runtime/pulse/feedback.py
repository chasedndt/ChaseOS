"""Feedback policy primitives for ChaseOS Pulse."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import FEEDBACK_TYPES, PulseCard, PulseFeedback, now_utc


FEEDBACK_CANDIDATE_ROOT = Path("07_LOGS") / "Pulse-Decks" / "feedback-candidates"
USER_DECK_ROOT = Path("07_LOGS") / "Pulse-Decks" / "users"
PENDING_REVIEW = "pending_review"
FEEDBACK_CANDIDATE_STATUSES = {PENDING_REVIEW}


@dataclass
class PulseFeedbackRecord:
    feedback_id: str
    card_id: str
    feedback_type: str
    operator_note: str = ""
    created_at: str = field(default_factory=now_utc)
    creates_memory_candidate: bool = False
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.feedback_id:
            raise ValueError("feedback_id is required")
        if not self.card_id:
            raise ValueError("card_id is required")
        if self.feedback_type not in FEEDBACK_TYPES:
            raise ValueError(f"feedback_type must be one of {sorted(FEEDBACK_TYPES)}")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse feedback cannot allow canonical writeback directly")
        if self.feedback_type == "memory_candidate":
            self.creates_memory_candidate = True

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def apply_feedback(card: PulseCard, record: PulseFeedbackRecord) -> PulseCard:
    card.validate()
    record.validate()
    if card.card_id != record.card_id:
        raise ValueError("feedback card_id does not match card.card_id")
    card.feedback.append(
        PulseFeedback(
            feedback_type=record.feedback_type,
            operator_note=record.operator_note,
            created_at=record.created_at,
        )
    )
    card.validate()
    return card


@dataclass
class PulseFeedbackCandidate:
    """Durable feedback candidate row.

    A candidate is an append-only review object. It is not applied to the
    source deck, not an approved memory, and not a task/canonical write.
    """

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
    mutates_canonical_state: bool = False
    approves_memory: bool = False
    creates_task: bool = False

    def validate(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.feedback_id:
            raise ValueError("feedback_id is required")
        if not self.card_id:
            raise ValueError("card_id is required")
        if self.feedback_type not in FEEDBACK_TYPES:
            raise ValueError(f"feedback_type must be one of {sorted(FEEDBACK_TYPES)}")
        if not self.source_deck_path:
            raise ValueError("source_deck_path is required")
        if self.status not in FEEDBACK_CANDIDATE_STATUSES:
            raise ValueError(f"status must be one of {sorted(FEEDBACK_CANDIDATE_STATUSES)}")
        if self.feedback_type == "memory_candidate":
            self.creates_memory_candidate = True
        if not self.review_required:
            raise ValueError("feedback candidates require review")
        if not self.candidate_only:
            raise ValueError("feedback candidates must remain candidate-only")
        if self.canonical_writeback_allowed:
            raise ValueError("feedback candidates cannot allow canonical writeback")
        if self.applied_to_source_deck:
            raise ValueError("feedback candidates cannot be applied to the source deck")
        if self.mutates_canonical_state:
            raise ValueError("feedback candidates cannot mutate canonical state")
        if self.approves_memory:
            raise ValueError("feedback candidates cannot approve memory")
        if self.creates_task:
            raise ValueError("feedback candidates cannot create tasks directly")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PulseFeedbackCandidate":
        candidate = cls(
            candidate_id=str(data.get("candidate_id") or ""),
            feedback_id=str(data.get("feedback_id") or ""),
            card_id=str(data.get("card_id") or ""),
            feedback_type=str(data.get("feedback_type") or ""),
            source_deck_path=str(data.get("source_deck_path") or ""),
            operator_note=str(data.get("operator_note") or ""),
            created_at=str(data.get("created_at") or now_utc()),
            source_surface_path=data.get("source_surface_path"),
            status=str(data.get("status") or PENDING_REVIEW),
            review_required=bool(data.get("review_required", True)),
            candidate_only=bool(data.get("candidate_only", True)),
            creates_memory_candidate=bool(data.get("creates_memory_candidate", False)),
            canonical_writeback_allowed=bool(data.get("canonical_writeback_allowed", False)),
            applied_to_source_deck=bool(data.get("applied_to_source_deck", False)),
            mutates_canonical_state=bool(data.get("mutates_canonical_state", False)),
            approves_memory=bool(data.get("approves_memory", False)),
            creates_task=bool(data.get("creates_task", False)),
        )
        candidate.validate()
        return candidate


@dataclass
class PulseFeedbackCandidateArtifact:
    path: str
    candidate_id: str
    card_id: str
    feedback_type: str
    status: str = PENDING_REVIEW
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.path:
            raise ValueError("feedback candidate artifact path is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.card_id:
            raise ValueError("card_id is required")
        if self.feedback_type not in FEEDBACK_TYPES:
            raise ValueError(f"feedback_type must be one of {sorted(FEEDBACK_TYPES)}")
        if self.status != PENDING_REVIEW:
            raise ValueError("feedback candidate artifacts are pending review only")
        if self.canonical_writeback_allowed:
            raise ValueError("feedback candidate artifact cannot allow canonical writeback")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


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
        raise ValueError("feedback candidate slug is invalid")
    return slug


def _candidate_id(record: PulseFeedbackRecord, source_deck_path: str) -> str:
    seed = f"{record.feedback_id}|{record.created_at}|{source_deck_path}|{record.operator_note}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"feedback-candidate-{_safe_slug(record.card_id)}-{_safe_slug(record.feedback_type)}-{digest}"


def _date_slug(created_at: str) -> str:
    candidate = (created_at or now_utc())[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return now_utc()[:10]
    return candidate


def feedback_candidate_log_path(vault_root: str | Path, *, created_at: str | None = None) -> Path:
    vault = _vault_path(vault_root)
    root = (vault / FEEDBACK_CANDIDATE_ROOT).resolve()
    date_slug = _date_slug(created_at or now_utc())
    path = root / f"{date_slug}-feedback-candidates.jsonl"
    _assert_inside(path, root, "Pulse feedback candidate logs must stay inside feedback-candidates/")
    return path


def build_feedback_candidate_record(
    record: PulseFeedbackRecord,
    *,
    source_deck_path: str,
    source_surface_path: str | None = None,
) -> PulseFeedbackCandidate:
    record.validate()
    candidate = PulseFeedbackCandidate(
        candidate_id=_candidate_id(record, source_deck_path),
        feedback_id=record.feedback_id,
        card_id=record.card_id,
        feedback_type=record.feedback_type,
        source_deck_path=source_deck_path,
        operator_note=record.operator_note,
        created_at=record.created_at,
        source_surface_path=source_surface_path,
        creates_memory_candidate=record.creates_memory_candidate,
        canonical_writeback_allowed=False,
    )
    candidate.validate()
    return candidate


def persist_feedback_candidate(
    vault_root: str | Path,
    record: PulseFeedbackRecord,
    *,
    source_deck_path: str | Path,
    source_surface_path: str | Path | None = None,
) -> PulseFeedbackCandidateArtifact:
    """Append a governed feedback candidate to the Pulse log tree.

    This writes only an append-only JSONL row under
    `07_LOGS/Pulse-Decks/feedback-candidates/`. It does not apply feedback to
    cards, approve memory, create tasks, or mutate canonical ChaseOS state.
    """
    vault = _vault_path(vault_root)
    source_deck = Path(source_deck_path)
    source_deck = source_deck if source_deck.is_absolute() else vault / source_deck
    _assert_inside(
        source_deck,
        vault / USER_DECK_ROOT,
        "feedback candidate source deck must stay inside 07_LOGS/Pulse-Decks/users/",
    )
    if not source_deck.exists() or not source_deck.is_file():
        raise ValueError("feedback candidate source deck does not exist")

    source_surface: str | None = None
    if source_surface_path is not None:
        surface = Path(source_surface_path)
        surface = surface if surface.is_absolute() else vault / surface
        _assert_inside(
            surface,
            vault / USER_DECK_ROOT,
            "feedback candidate source surface must stay inside 07_LOGS/Pulse-Decks/users/",
        )
        source_surface = _relative_to_vault(vault, surface)

    source_deck_ref = _relative_to_vault(vault, source_deck)
    candidate = build_feedback_candidate_record(
        record,
        source_deck_path=source_deck_ref,
        source_surface_path=source_surface,
    )
    path = feedback_candidate_log_path(vault, created_at=candidate.created_at)
    root = (vault / FEEDBACK_CANDIDATE_ROOT).resolve()
    _assert_inside(path, root, "Pulse feedback candidate logs must stay inside feedback-candidates/")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(candidate.to_dict(), sort_keys=True))
        handle.write("\n")

    artifact = PulseFeedbackCandidateArtifact(
        path=_relative_to_vault(vault, path),
        candidate_id=candidate.candidate_id,
        card_id=candidate.card_id,
        feedback_type=candidate.feedback_type,
        status=candidate.status,
        canonical_writeback_allowed=False,
    )
    artifact.validate()
    return artifact


def load_feedback_candidates(
    vault_root: str | Path,
    *,
    log_path: str | Path | None = None,
) -> list[PulseFeedbackCandidate]:
    """Load persisted feedback candidate rows from the governed Pulse log tree."""
    vault = _vault_path(vault_root)
    root = (vault / FEEDBACK_CANDIDATE_ROOT).resolve()
    if log_path is None:
        paths = sorted(root.glob("*-feedback-candidates.jsonl")) if root.exists() else []
    else:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        _assert_inside(target, root, "Pulse feedback candidate logs must stay inside feedback-candidates/")
        paths = [target]

    candidates: list[PulseFeedbackCandidate] = []
    for path in paths:
        if not path.exists():
            continue
        _assert_inside(path, root, "Pulse feedback candidate logs must stay inside feedback-candidates/")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                candidates.append(PulseFeedbackCandidate.from_dict(json.loads(line)))
    return candidates
