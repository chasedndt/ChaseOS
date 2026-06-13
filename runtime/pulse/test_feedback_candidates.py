from __future__ import annotations

import os
import shutil
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck
from runtime.pulse.feedback import (
    FEEDBACK_CANDIDATE_ROOT,
    PulseFeedbackCandidate,
    PulseFeedbackRecord,
    load_feedback_candidates,
    persist_feedback_candidate,
)
from runtime.pulse.local_surface import USER_DECK_DIR, build_feedback_candidate, persist_surface_feedback_candidate
from runtime.pulse.renderer_json import render_deck_json


_TMP_ROOT = Path("runtime/pulse/_tmp_feedback_candidates")


def _make_vault() -> Path:
    root = (_TMP_ROOT / f"vault-{uuid4().hex}").resolve()
    (root / USER_DECK_DIR).mkdir(parents=True, exist_ok=True)
    return root


def _cleanup(root: Path) -> None:
    base = _TMP_ROOT.resolve()
    target = root.resolve()
    if target == base or base in target.parents:
        shutil.rmtree(target, ignore_errors=True)


def _deck(deck_id: str = "pulse-user-feedback") -> PulseDeck:
    return PulseDeck(
        deck_id=deck_id,
        audience="user",
        generated_at="2026-04-30T07:30:00+01:00",
        cards=[
            PulseCard(
                card_id=f"{deck_id}-01",
                audience="user",
                card_class="Memory Update",
                title="Review candidate feedback",
                summary="Feedback should persist as a review-required candidate only.",
                generated_at="2026-04-30T07:30:00+01:00",
                evidence=[
                    EvidenceRef(
                        source_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
                        source_type="test_deck",
                        summary="Test source deck.",
                        trust_label="repo-observed",
                    )
                ],
                urgency=2,
                confidence=0.7,
            )
        ],
        source_summary=["test"],
    )


def _write_deck(vault: Path, slug: str, deck: PulseDeck, *, mtime: int = 100) -> Path:
    path = vault / USER_DECK_DIR / f"{slug}.json"
    path.write_text(render_deck_json(deck), encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_persist_feedback_candidate_appends_pending_jsonl_only() -> None:
    vault = _make_vault()
    try:
        deck = _deck()
        deck_path = _write_deck(vault, "2026-04-30-user-pulse", deck)
        record = PulseFeedbackRecord(
            feedback_id="candidate-feedback-001",
            card_id=deck.cards[0].card_id,
            feedback_type="memory_candidate",
            operator_note="Save as a candidate, not approved memory.",
            created_at="2026-04-30T07:31:00+00:00",
        )

        artifact = persist_feedback_candidate(vault, record, source_deck_path=deck_path)

        assert artifact.path == (FEEDBACK_CANDIDATE_ROOT / "2026-04-30-feedback-candidates.jsonl").as_posix()
        assert artifact.status == "pending_review"
        assert artifact.canonical_writeback_allowed is False

        loaded = load_feedback_candidates(vault, log_path=artifact.path)
        assert len(loaded) == 1
        candidate = loaded[0]
        assert candidate.feedback_id == "candidate-feedback-001"
        assert candidate.feedback_type == "memory_candidate"
        assert candidate.creates_memory_candidate is True
        assert candidate.review_required is True
        assert candidate.candidate_only is True
        assert candidate.applied_to_source_deck is False
        assert candidate.approves_memory is False
        assert candidate.creates_task is False
        assert deck.cards[0].feedback == []
    finally:
        _cleanup(vault)


def test_feedback_candidate_rejects_canonical_mutation_flags() -> None:
    candidate = PulseFeedbackCandidate(
        candidate_id="bad",
        feedback_id="bad-feedback",
        card_id="card",
        feedback_type="accepted",
        source_deck_path="07_LOGS/Pulse-Decks/users/deck.json",
        canonical_writeback_allowed=True,
    )

    with pytest.raises(ValueError, match="canonical writeback"):
        candidate.validate()


def test_feedback_candidate_persistence_rejects_paths_outside_governed_roots() -> None:
    vault = _make_vault()
    try:
        outside = vault / "runtime/pulse/deck.json"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text(render_deck_json(_deck("pulse-outside")), encoding="utf-8")
        record = PulseFeedbackRecord(
            feedback_id="candidate-feedback-002",
            card_id="pulse-outside-01",
            feedback_type="accepted",
        )

        with pytest.raises(ValueError, match="source deck"):
            persist_feedback_candidate(vault, record, source_deck_path=outside)

        with pytest.raises(ValueError, match="feedback-candidates"):
            load_feedback_candidates(vault, log_path=vault / "07_LOGS/Pulse-Decks/users/not-a-log.jsonl")
    finally:
        _cleanup(vault)


def test_surface_can_persist_feedback_candidate_without_mutating_deck() -> None:
    vault = _make_vault()
    try:
        deck = _deck("pulse-user-surface-feedback")
        _write_deck(vault, "2026-04-30-user-pulse", deck)

        artifact = persist_surface_feedback_candidate(
            vault,
            card_id=deck.cards[0].card_id,
            feedback_type="needs_more_evidence",
            operator_note="Keep this pending.",
        )

        loaded = load_feedback_candidates(vault, log_path=artifact.path)
        assert len(loaded) == 1
        assert loaded[0].card_id == deck.cards[0].card_id
        assert loaded[0].feedback_type == "needs_more_evidence"
        assert loaded[0].status == "pending_review"
        assert deck.cards[0].feedback == []
    finally:
        _cleanup(vault)


def test_surface_feedback_candidate_builder_still_stays_in_memory_until_persisted() -> None:
    card = _deck("pulse-user-in-memory").cards[0]
    record = build_feedback_candidate(card, "accepted", operator_note="Candidate only")

    assert record.card_id == card.card_id
    assert record.feedback_type == "accepted"
    assert record.canonical_writeback_allowed is False
    assert card.feedback == []
