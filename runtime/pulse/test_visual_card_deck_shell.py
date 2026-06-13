from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck, RecommendedAction
from runtime.pulse.renderer_json import render_deck_json
from runtime.pulse.visual_card_deck_shell import (
    build_pulse_visual_card_deck_shell,
    render_pulse_visual_card_deck_shell_html,
    write_pulse_visual_card_deck_shell_html,
)


def _write_user_deck(vault: Path) -> Path:
    deck_dir = vault / "07_LOGS" / "Pulse-Decks" / "users"
    deck_dir.mkdir(parents=True, exist_ok=True)
    deck = PulseDeck(
        deck_id="pulse-visual-shell-test",
        audience="user",
        generated_at="2026-05-03T05:00:00+01:00",
        cards=[
            PulseCard(
                card_id="pulse-visual-shell-card-001",
                audience="user",
                card_class="Today's Operating Brief",
                title="Review Pulse product shell",
                summary="A valid visual shell test card.",
                generated_at="2026-05-03T05:00:00+01:00",
                evidence=[
                    EvidenceRef(
                        source_path="06_AGENTS/ChaseOS-Pulse-Final-Product-Readiness-Audit.md",
                        source_type="audit",
                        summary="Final audit exists.",
                        trust_label="repo-observed",
                    )
                ],
                recommended_actions=[
                    RecommendedAction(
                        action_id="inspect",
                        label="Inspect Pulse UI",
                        action_type="review",
                        requires_operator_approval=False,
                    )
                ],
                urgency=3,
                confidence=0.91,
            )
        ],
    )
    path = deck_dir / "2026-05-03-user-pulse.json"
    path.write_text(render_deck_json(deck), encoding="utf-8")
    return path


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_visual_shell_build_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)
    before = _snapshot(vault)

    model = build_pulse_visual_card_deck_shell(vault, deck_path=deck_path)

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_visual_card_deck_shell"
    assert model["authority"]["canonical_writeback_allowed"] is False
    assert model["authority"]["schedule_activation_allowed"] is False
    assert model["authority"]["provider_or_connector_call_allowed"] is False
    assert model["deck_card_summary"]["card_count"] == 1


def test_visual_shell_render_contains_core_regions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    model = build_pulse_visual_card_deck_shell(vault, deck_path=deck_path)
    html = render_pulse_visual_card_deck_shell_html(model)

    assert "<!doctype html>" in html
    assert "Approval Center" in html
    assert "Memory And Runtime" in html
    assert "Runtime Brain" in html
    assert "Pulse Cards" in html
    assert "canonical writeback" in html.lower()


def test_visual_shell_write_stays_inside_user_deck_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    model = write_pulse_visual_card_deck_shell_html(vault, deck_path=deck_path)
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-user-pulse.visual-shell.html"
    assert output.parent == vault / "07_LOGS" / "Pulse-Decks" / "users"
    assert model["writes"] == ["07_LOGS/Pulse-Decks/users/2026-05-03-user-pulse.visual-shell.html"]


def test_visual_shell_rejects_output_outside_user_deck_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    with pytest.raises(Exception):
        write_pulse_visual_card_deck_shell_html(
            vault,
            deck_path=deck_path,
            output_path=vault / "07_LOGS" / "bad.html",
        )
