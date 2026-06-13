"""Multi-audience ChaseOS Pulse deck generation and inventory.

This module operationalizes the deterministic backend deck builders for user,
agent, and shared-coordination audiences. It is local and log-only: deck writes
stay under 07_LOGS/Pulse-Decks/ and do not activate schedules, dispatch
runtimes, call providers/connectors, approve memory, or mutate canonical state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from runtime.pulse.card_schema import PulseDeck, now_utc
from runtime.pulse.deck_schema import PulseDeckArtifact
from runtime.pulse.minimal_deck import (
    build_minimal_agent_deck,
    build_minimal_shared_coordination_deck,
    build_minimal_user_deck,
)
from runtime.pulse.writeback import AUDIENCE_DIRS, PULSE_DECK_ROOT, write_deck_artifacts


DEFAULT_MULTI_AUDIENCE_DECKS = ("user", "agent", "shared_coordination")
SUPPORTED_MULTI_AUDIENCE_DECKS = DEFAULT_MULTI_AUDIENCE_DECKS
_BUILDERS: dict[str, Callable[[Path, str | None, str | None], PulseDeck]] = {
    "user": lambda vault, deck_id, generated_at: build_minimal_user_deck(
        vault, deck_id=deck_id, generated_at=generated_at
    ),
    "agent": lambda vault, deck_id, generated_at: build_minimal_agent_deck(
        vault, deck_id=deck_id, generated_at=generated_at
    ),
    "shared_coordination": lambda vault, deck_id, generated_at: build_minimal_shared_coordination_deck(
        vault, deck_id=deck_id, generated_at=generated_at
    ),
}


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _normalize_audiences(audiences: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    raw = tuple(audiences or DEFAULT_MULTI_AUDIENCE_DECKS)
    if not raw:
        raise ValueError("at least one Pulse deck audience is required")
    invalid = tuple(audience for audience in raw if audience not in SUPPORTED_MULTI_AUDIENCE_DECKS)
    if invalid:
        raise ValueError(
            f"unsupported Pulse deck audiences: {sorted(invalid)}; "
            f"allowed={sorted(SUPPORTED_MULTI_AUDIENCE_DECKS)}"
        )
    seen: set[str] = set()
    ordered: list[str] = []
    for audience in raw:
        if audience not in seen:
            seen.add(audience)
            ordered.append(audience)
    return tuple(ordered)


def _deck_slug(audience: str, generated_at: str, slug_prefix: str | None) -> str:
    prefix = slug_prefix or generated_at[:10]
    label = "shared" if audience == "shared_coordination" else audience
    return f"{prefix}-{label}-pulse-expanded"


def _deck_id(audience: str, generated_at: str) -> str:
    label = "shared" if audience == "shared_coordination" else audience
    return f"pulse-{label}-{generated_at[:10]}-expanded"


def _latest_json(path: Path) -> Path | None:
    if not path.exists():
        return None
    candidates = [item for item in path.glob("*.json") if item.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.stat().st_mtime, item.name))


def _relative(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _card_count(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    cards = payload.get("cards") if isinstance(payload, dict) else None
    return len(cards) if isinstance(cards, list) else 0


@dataclass(frozen=True)
class PulseAudienceDeckResult:
    audience: str
    deck_id: str
    card_count: int
    schedule_ref: str | None
    canonical_writeback_enabled: bool
    write_requested: bool
    artifact_written: bool = False
    markdown_path: str | None = None
    json_path: str | None = None

    def validate(self) -> None:
        if self.audience not in SUPPORTED_MULTI_AUDIENCE_DECKS:
            raise ValueError("invalid Pulse audience deck result audience")
        if not self.deck_id:
            raise ValueError("deck_id is required")
        if self.card_count < 0:
            raise ValueError("card_count cannot be negative")
        if self.canonical_writeback_enabled:
            raise ValueError("multi-audience Pulse decks cannot enable canonical writeback")
        if self.artifact_written and (not self.markdown_path or not self.json_path):
            raise ValueError("written deck artifacts require markdown and json paths")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseDeckInventoryItem:
    audience: str
    output_dir: str
    latest_json_path: str | None
    latest_markdown_path: str | None
    card_count: int

    def validate(self) -> None:
        if self.audience not in SUPPORTED_MULTI_AUDIENCE_DECKS:
            raise ValueError("invalid Pulse deck inventory audience")
        if not self.output_dir:
            raise ValueError("output_dir is required")
        if self.card_count < 0:
            raise ValueError("card_count cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseMultiAudienceDeckResult:
    generated_at: str
    audiences: tuple[str, ...]
    write_requested: bool
    write_executed: bool
    decks: tuple[PulseAudienceDeckResult, ...]
    inventory: tuple[PulseDeckInventoryItem, ...]
    writes: tuple[str, ...] = ()
    read_only: bool = True
    log_only: bool = True
    canonical_writeback_allowed: bool = False
    memory_approval_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    schedule_activation_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    second_datastore_created: bool = False
    allowed_write_root: str = "07_LOGS/Pulse-Decks/"
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Dry-run by default; --write creates markdown/json deck artifacts only under 07_LOGS/Pulse-Decks/.",
            "This command does not activate schedules, dispatch runtimes, call providers/connectors, approve memory, or mutate canonical state.",
        )
    )

    @property
    def deck_count(self) -> int:
        return len(self.decks)

    def validate(self) -> None:
        _normalize_audiences(self.audiences)
        for deck in self.decks:
            deck.validate()
        for item in self.inventory:
            item.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("write_executed cannot be read_only")
        if self.write_requested and self.write_executed and not self.writes:
            raise ValueError("write execution must report written paths")
        if not self.log_only:
            raise ValueError("Pulse multi-audience decks must remain log-only")
        if self.canonical_writeback_allowed:
            raise ValueError("canonical writeback cannot be allowed")
        if self.memory_approval_allowed:
            raise ValueError("memory approval cannot be allowed")
        if self.provider_or_connector_call_allowed:
            raise ValueError("provider/connector calls cannot be allowed")
        if self.runtime_dispatch_allowed:
            raise ValueError("runtime dispatch cannot be allowed")
        if self.schedule_activation_allowed:
            raise ValueError("schedule activation cannot be allowed")
        if self.agent_bus_task_write_allowed:
            raise ValueError("Agent Bus task writes cannot be allowed")
        if self.second_datastore_created:
            raise ValueError("multi-audience decks cannot create a second datastore")
        for written in self.writes:
            normalized = written.replace("\\", "/")
            if not normalized.startswith(self.allowed_write_root):
                raise ValueError("Pulse multi-audience deck writes must stay under 07_LOGS/Pulse-Decks/")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "audiences": list(self.audiences),
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "deck_count": self.deck_count,
            "decks": [deck.to_dict() for deck in self.decks],
            "inventory": [item.to_dict() for item in self.inventory],
            "writes": list(self.writes),
            "read_only": self.read_only,
            "log_only": self.log_only,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "second_datastore_created": self.second_datastore_created,
            "allowed_write_root": self.allowed_write_root,
            "notes": list(self.notes),
        }


def build_pulse_deck_inventory(
    vault_root: str | Path,
    *,
    audiences: list[str] | tuple[str, ...] | None = None,
) -> tuple[PulseDeckInventoryItem, ...]:
    """Return latest local Pulse deck artifacts by audience without writing."""

    vault = _vault_path(vault_root)
    items: list[PulseDeckInventoryItem] = []
    for audience in _normalize_audiences(audiences):
        output_dir = vault / PULSE_DECK_ROOT / AUDIENCE_DIRS[audience]
        latest_json = _latest_json(output_dir)
        latest_markdown = latest_json.with_suffix(".md") if latest_json is not None else None
        if latest_markdown is not None and not latest_markdown.exists():
            latest_markdown = None
        item = PulseDeckInventoryItem(
            audience=audience,
            output_dir=(PULSE_DECK_ROOT / AUDIENCE_DIRS[audience]).as_posix(),
            latest_json_path=_relative(vault, latest_json),
            latest_markdown_path=_relative(vault, latest_markdown),
            card_count=_card_count(latest_json),
        )
        item.validate()
        items.append(item)
    return tuple(items)


def build_pulse_multi_audience_decks(
    vault_root: str | Path,
    *,
    audiences: list[str] | tuple[str, ...] | None = None,
    generated_at: str | None = None,
    slug_prefix: str | None = None,
    write: bool = False,
) -> PulseMultiAudienceDeckResult:
    """Build or write deterministic Pulse decks for multiple audiences."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    target_audiences = _normalize_audiences(audiences)
    deck_results: list[PulseAudienceDeckResult] = []
    writes: list[str] = []

    for audience in target_audiences:
        deck = _BUILDERS[audience](vault, _deck_id(audience, generated), generated)
        artifact: PulseDeckArtifact | None = None
        if write:
            artifact = write_deck_artifacts(
                vault,
                deck,
                slug=_deck_slug(audience, generated, slug_prefix),
            )
            writes.extend([artifact.markdown_path, artifact.json_path])
        deck_result = PulseAudienceDeckResult(
            audience=audience,
            deck_id=deck.deck_id,
            card_count=len(deck.cards),
            schedule_ref=deck.schedule_ref,
            canonical_writeback_enabled=deck.canonical_writeback_enabled,
            write_requested=write,
            artifact_written=artifact is not None,
            markdown_path=artifact.markdown_path if artifact is not None else None,
            json_path=artifact.json_path if artifact is not None else None,
        )
        deck_result.validate()
        deck_results.append(deck_result)

    result = PulseMultiAudienceDeckResult(
        generated_at=generated,
        audiences=target_audiences,
        write_requested=write,
        write_executed=write,
        decks=tuple(deck_results),
        inventory=build_pulse_deck_inventory(vault, audiences=target_audiences),
        writes=tuple(writes),
        read_only=not write,
    )
    result.validate()
    return result
