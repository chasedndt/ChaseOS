"""Log-only Pulse deck artifact writer.

This module writes rendered Pulse decks to 07_LOGS/Pulse-Decks only. It does
not write to Now.md, Project-OS files, governance docs, or 02_KNOWLEDGE/.
"""

from __future__ import annotations

import re
from pathlib import Path

from runtime.pulse.card_schema import PulseDeck
from runtime.pulse.deck_schema import PulseDeckArtifact
from runtime.pulse.renderer_json import render_deck_json
from runtime.pulse.renderer_markdown import render_deck_markdown


PULSE_DECK_ROOT = Path("07_LOGS") / "Pulse-Decks"
AUDIENCE_DIRS = {
    "user": "users",
    "agent": "agents",
    "shared": "shared",
    "shared_coordination": "shared",
}


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    if not slug or slug in {".", ".."} or ".." in slug:
        raise ValueError("deck artifact slug is invalid")
    return slug


def _assert_inside(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    try:
        child_resolved.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError("Pulse deck artifacts must stay inside 07_LOGS/Pulse-Decks") from exc


def deck_output_dir(vault_root: Path, audience: str) -> Path:
    if audience not in AUDIENCE_DIRS:
        raise ValueError(f"audience must be one of {sorted(AUDIENCE_DIRS)}")
    return vault_root / PULSE_DECK_ROOT / AUDIENCE_DIRS[audience]


def deck_artifact_paths(
    vault_root: Path,
    deck: PulseDeck,
    *,
    slug: str | None = None,
) -> tuple[Path, Path]:
    deck.validate()
    root = (vault_root / PULSE_DECK_ROOT).resolve()
    output_dir = deck_output_dir(vault_root, deck.audience)
    artifact_slug = _safe_slug(slug or deck.deck_id)
    markdown_path = output_dir / f"{artifact_slug}.md"
    json_path = output_dir / f"{artifact_slug}.json"
    _assert_inside(markdown_path, root)
    _assert_inside(json_path, root)
    return markdown_path, json_path


def write_deck_artifacts(
    vault_root: Path,
    deck: PulseDeck,
    *,
    slug: str | None = None,
) -> PulseDeckArtifact:
    deck.validate()
    if deck.canonical_writeback_enabled:
        raise ValueError("Pulse deck writer cannot write canonical deck output")
    markdown_path, json_path = deck_artifact_paths(vault_root, deck, slug=slug)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_deck_markdown(deck), encoding="utf-8")
    json_path.write_text(render_deck_json(deck), encoding="utf-8")
    artifact = PulseDeckArtifact(
        deck_id=deck.deck_id,
        audience=deck.audience,
        markdown_path=str(markdown_path.relative_to(vault_root)),
        json_path=str(json_path.relative_to(vault_root)),
        generated_at=deck.generated_at,
    )
    artifact.validate()
    return artifact
