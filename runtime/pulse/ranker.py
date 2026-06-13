"""Ranking helpers for ChaseOS Pulse cards."""

from __future__ import annotations

from runtime.pulse.card_schema import PulseCard


def score_card(card: PulseCard) -> float:
    card.validate()
    evidence_score = min(len(card.evidence), 5) * 0.5
    action_score = 0.5 if card.recommended_actions else 0.0
    feedback_penalty = 0.5 if any(f.feedback_type == "dismissed" for f in card.feedback) else 0.0
    return card.urgency + card.confidence + evidence_score + action_score - feedback_penalty


def rank_cards(cards: list[PulseCard], *, limit: int | None = None) -> list[PulseCard]:
    ranked = sorted(cards, key=lambda card: (-score_card(card), card.card_id))
    return ranked if limit is None else ranked[:limit]
