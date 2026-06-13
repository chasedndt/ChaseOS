"""Adapter contracts for Creator Engine source intake."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable


@dataclass
class RecordingCandidate:
    source_ref: str
    adapter_id: str
    media_kind: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterValidationResult:
    ok: bool
    normalized_source: RecordingCandidate | None = None
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


@runtime_checkable
class RecordingIntakeAdapter(Protocol):
    adapter_id: str

    def discover(self, source: str | Path) -> Iterable[RecordingCandidate]:
        """Return candidate recordings from a declared local source."""

    def validate(self, candidate: RecordingCandidate) -> AdapterValidationResult:
        """Validate one candidate without reading secrets, publishing, or mutating canon."""
