"""Topic selection for ChaseOS Pulse decks."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.pulse.signal_collector import PulseSignal


@dataclass
class PulseTopic:
    topic_id: str
    label: str
    audience: str
    signals: list[PulseSignal] = field(default_factory=list)
    priority: int = 0


def _topic_key(signal: PulseSignal) -> str:
    if signal.tags:
        return signal.tags[0]
    return signal.source_type


def select_topics(signals: list[PulseSignal], *, max_topics: int = 10) -> list[PulseTopic]:
    grouped: dict[str, PulseTopic] = {}
    for signal in signals:
        signal.validate(external_sources_enabled=True)
        key = _topic_key(signal)
        topic = grouped.setdefault(
            key,
            PulseTopic(
                topic_id=key.replace(" ", "-").lower(),
                label=key.replace("_", " ").title(),
                audience=signal.audience_hint,
            ),
        )
        topic.signals.append(signal)
        topic.priority = max(topic.priority, signal.priority)
        if topic.audience != signal.audience_hint:
            topic.audience = "shared_coordination"
    return sorted(grouped.values(), key=lambda item: (-item.priority, item.topic_id))[:max_topics]
