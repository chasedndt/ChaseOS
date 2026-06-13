"""JSON renderer for ChaseOS Pulse decks."""

from __future__ import annotations

import json

from runtime.pulse.card_schema import PulseCard, PulseDeck


def render_card_json(card: PulseCard, *, indent: int = 2) -> str:
    return json.dumps(card.to_dict(), indent=indent, sort_keys=True)


def render_deck_json(deck: PulseDeck, *, indent: int = 2) -> str:
    return json.dumps(deck.to_dict(), indent=indent, sort_keys=True)
