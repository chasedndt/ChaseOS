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
    PulseFeedbackRecord,
    persist_feedback_candidate,
)
from runtime.pulse.feedback_review_queue import (
    BLOCKED_REVIEW_EFFECTS,
    CONTRACT_ONLY,
    PulseFeedbackReviewDecision,
    build_apply_contract,
    build_feedback_review_queue,
    build_review_apply_contract,
    build_review_decision,
)
from runtime.pulse.local_surface import USER_DECK_DIR
from runtime.pulse.renderer_json import render_deck_json


_TMP_ROOT = Path("runtime/pulse/_tmp_feedback_review_queue")


def _make_vault() -> Path:
    root = (_TMP_ROOT / f"vault-{uuid4().hex}").resolve()
    (root / USER_DECK_DIR).mkdir(parents=True, exist_ok=True)
    return root


def _cleanup(root: Path) -> None:
    base = _TMP_ROOT.resolve()
    target = root.resolve()
    if target == base or base in target.parents:
        shutil.rmtree(target, ignore_errors=True)


def _deck(deck_id: str = "pulse-user-review") -> PulseDeck:
    return PulseDeck(
        deck_id=deck_id,
        audience="user",
        generated_at="2026-04-30T07:30:00+01:00",
        cards=[
            PulseCard(
                card_id=f"{deck_id}-01",
                audience="user",
                card_class="Memory Update",
                title="Review pending Pulse feedback",
                summary="Pending feedback candidates must be inspectable without being applied.",
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


def _persist_candidate(vault: Path, *, feedback_type: str = "accepted") -> tuple[Path, str]:
    deck = _deck()
    deck_path = _write_deck(vault, "2026-04-30-user-pulse", deck)
    record = PulseFeedbackRecord(
        feedback_id=f"candidate-feedback-{feedback_type}",
        card_id=deck.cards[0].card_id,
        feedback_type=feedback_type,
        operator_note="Review only.",
        created_at="2026-04-30T07:31:00+00:00",
    )
    artifact = persist_feedback_candidate(vault, record, source_deck_path=deck_path)
    return deck_path, artifact.path


def test_review_queue_loads_pending_candidates_without_writes() -> None:
    vault = _make_vault()
    try:
        deck_path, log_path = _persist_candidate(vault, feedback_type="memory_candidate")
        before = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*") if path.is_file())

        queue = build_feedback_review_queue(vault, log_path=log_path)
        after = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*") if path.is_file())

        assert queue.queue_status == "read_only"
        assert queue.item_count == 1
        assert queue.pending_count == 1
        assert queue.writes == []
        assert before == after
        item = queue.items[0]
        assert item.source_deck_path == deck_path.relative_to(vault).as_posix()
        assert item.status == "pending_review"
        assert item.review_required is True
        assert item.candidate_only is True
        assert item.creates_memory_candidate is True
        assert item.canonical_writeback_allowed is False
        assert item.applied_to_source_deck is False
        assert item.approves_memory is False
        assert item.creates_task is False
        assert "canonical_writeback" in item.blocked_effects
    finally:
        _cleanup(vault)


def test_review_queue_empty_vault_does_not_create_candidate_directory() -> None:
    vault = _make_vault()
    try:
        candidate_dir = vault / FEEDBACK_CANDIDATE_ROOT
        assert not candidate_dir.exists()

        queue = build_feedback_review_queue(vault)

        assert queue.item_count == 0
        assert queue.pending_count == 0
        assert queue.source_log_paths == []
        assert queue.to_dict()["writes"] == []
        assert not candidate_dir.exists()
    finally:
        _cleanup(vault)


def test_review_queue_rejects_log_paths_outside_feedback_candidate_root() -> None:
    vault = _make_vault()
    try:
        _persist_candidate(vault)
        outside = vault / USER_DECK_DIR / "not-a-review-log.jsonl"
        outside.write_text("{}", encoding="utf-8")

        with pytest.raises(ValueError, match="feedback-candidates"):
            build_feedback_review_queue(vault, log_path=outside)
    finally:
        _cleanup(vault)


def test_review_decision_and_apply_contract_are_non_executing() -> None:
    vault = _make_vault()
    try:
        _, log_path = _persist_candidate(vault)
        item = build_feedback_review_queue(vault, log_path=log_path).items[0]

        decision, contract = build_review_apply_contract(
            item,
            decision_type="accept_for_future_ranking",
            reviewer="operator",
            operator_note="Use as future ranking signal only.",
            created_at="2026-04-30T08:00:00+00:00",
        )

        assert decision.status == CONTRACT_ONLY
        assert decision.canonical_writeback_allowed is False
        assert decision.applies_feedback_to_source_deck is False
        assert decision.approves_memory is False
        assert decision.creates_task is False
        assert decision.persists_decision is False
        assert contract.status == CONTRACT_ONLY
        assert contract.allowed_effects == ("future_ranking_signal_candidate",)
        assert contract.blocked_effects == BLOCKED_REVIEW_EFFECTS
        assert contract.writes == []
        assert contract.canonical_writeback_allowed is False
        assert contract.approves_memory is False
        assert contract.creates_task is False
    finally:
        _cleanup(vault)


def test_review_decision_rejects_canonical_flags_and_candidate_mismatch() -> None:
    vault = _make_vault()
    try:
        _, log_path = _persist_candidate(vault)
        item = build_feedback_review_queue(vault, log_path=log_path).items[0]

        bad_decision = PulseFeedbackReviewDecision(
            decision_id="bad",
            candidate_id=item.candidate_id,
            decision_type="reject_candidate",
            canonical_writeback_allowed=True,
        )
        with pytest.raises(ValueError, match="canonical writeback"):
            bad_decision.validate()

        decision = build_review_decision(item, decision_type="reject_candidate")
        mismatched = PulseFeedbackReviewDecision(
            decision_id=decision.decision_id,
            candidate_id="different-candidate",
            decision_type=decision.decision_type,
        )
        with pytest.raises(ValueError, match="candidate_id"):
            build_apply_contract(item, mismatched)
    finally:
        _cleanup(vault)
