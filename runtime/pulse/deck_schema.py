"""Deck artifact metadata for ChaseOS Pulse.

The main deck shape lives in card_schema.PulseDeck. This module describes the
filesystem artifacts produced by the backend renderer/writeback scaffold.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from runtime.pulse.card_schema import CARD_AUDIENCES, now_utc


@dataclass
class PulseDeckArtifact:
    deck_id: str
    audience: str
    markdown_path: str
    json_path: str
    generated_at: str = field(default_factory=now_utc)
    canonical_writeback_enabled: bool = False

    def validate(self) -> None:
        if not self.deck_id:
            raise ValueError("deck_id is required")
        if self.audience not in CARD_AUDIENCES:
            raise ValueError(f"audience must be one of {sorted(CARD_AUDIENCES)}")
        if not self.markdown_path:
            raise ValueError("markdown_path is required")
        if not self.json_path:
            raise ValueError("json_path is required")
        if self.canonical_writeback_enabled:
            raise ValueError("Pulse deck artifacts cannot enable canonical writeback")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
