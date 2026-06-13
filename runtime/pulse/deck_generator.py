"""Minimal deck generation for ChaseOS Pulse."""

from __future__ import annotations

from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck, now_utc
from runtime.pulse.ranker import rank_cards
from runtime.pulse.signal_collector import PulseSignal
from runtime.pulse.topic_selector import PulseTopic, select_topics


DEFAULT_CARD_CLASS = {
    "user": "Today's Operating Brief",
    "agent": "Runtime Reflection",
    "shared": "Multi-Agent Coordination",
    "shared_coordination": "Multi-Agent Coordination",
}


def card_from_topic(topic: PulseTopic, *, audience: str | None = None) -> PulseCard:
    target_audience = audience or topic.audience
    if target_audience not in DEFAULT_CARD_CLASS:
        target_audience = "shared"
    evidence: list[EvidenceRef] = []
    for signal in topic.signals:
        evidence.extend(signal.evidence)
        if signal.source_path:
            evidence.append(
                EvidenceRef(
                    source_path=signal.source_path,
                    source_type=signal.source_type,
                    summary=signal.summary,
                    trust_label="repo-observed",
                    observed_at=signal.observed_at,
                )
            )
    summary = "; ".join(signal.summary for signal in topic.signals[:3])
    return PulseCard(
        card_id=f"pulse-{topic.topic_id}",
        audience=target_audience,
        card_class=DEFAULT_CARD_CLASS[target_audience],
        title=topic.label,
        summary=summary or topic.label,
        evidence=evidence,
        urgency=min(topic.priority, 5),
        confidence=0.5 if evidence else 0.2,
    )


def generate_deck(
    signals: list[PulseSignal],
    *,
    audience: str = "user",
    deck_id: str | None = None,
    schedule_ref: str | None = None,
    max_cards: int = 10,
) -> PulseDeck:
    topics = select_topics(signals, max_topics=max_cards)
    cards = [
        card_from_topic(topic, audience=audience)
        for topic in topics
        if topic.audience in {audience, "shared", "shared_coordination"}
        or audience in {"shared", "shared_coordination"}
    ]
    deck = PulseDeck(
        deck_id=deck_id or f"pulse-{audience}-{now_utc()[:10]}",
        audience=audience,
        cards=rank_cards(cards, limit=max_cards),
        source_summary=sorted({signal.source_type for signal in signals}),
        schedule_ref=schedule_ref,
    )
    deck.validate()
    return deck
