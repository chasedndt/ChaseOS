from __future__ import annotations

from pathlib import Path

import pytest

from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck, RecommendedAction
from runtime.pulse.product_shell import (
    build_pulse_product_shell,
    render_pulse_product_shell_html,
    write_pulse_product_shell_html,
)
from runtime.pulse.renderer_json import render_deck_json


def _write_user_deck(vault: Path) -> Path:
    deck_dir = vault / "07_LOGS" / "Pulse-Decks" / "users"
    deck_dir.mkdir(parents=True, exist_ok=True)
    deck = PulseDeck(
        deck_id="pulse-product-shell-test",
        audience="user",
        generated_at="2026-05-03T11:20:00+01:00",
        cards=[
            PulseCard(
                card_id="pulse-product-shell-card-001",
                audience="user",
                card_class="Today’s Operating Brief",
                title="Inspect integrated Pulse shell",
                summary="A valid product shell test card.",
                generated_at="2026-05-03T11:20:00+01:00",
                evidence=[
                    EvidenceRef(
                        source_path="06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md",
                        source_type="repo_doc",
                        summary="Completion tracker exists.",
                        trust_label="repo-observed",
                    )
                ],
                recommended_actions=[
                    RecommendedAction(
                        action_id="inspect",
                        label="Inspect shell",
                        action_type="review",
                        requires_operator_approval=False,
                    )
                ],
                urgency=4,
                confidence=0.9,
            )
        ],
    )
    path = deck_dir / "2026-05-03-user-pulse.json"
    path.write_text(render_deck_json(deck), encoding="utf-8")
    return path


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_product_shell_build_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)
    before = _snapshot(vault)

    model = build_pulse_product_shell(
        vault,
        deck_path=deck_path,
        generated_at="2026-05-03T11:25:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_product_shell"
    assert model["summary"]["panel_count"] == 6
    assert model["summary"]["card_count"] == 1
    assert model["authority"]["candidate_apply_allowed"] is False
    assert model["authority"]["canonical_writeback_allowed"] is False
    assert model["authority"]["schedule_activation_allowed"] is False


def test_product_shell_composes_expected_panels(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    model = build_pulse_product_shell(vault, deck_path=deck_path)

    assert set(model["panels"]) == {
        "visual_shell",
        "personal_map",
        "personal_map_review_apply",
        "personal_map_live_apply_proof",
        "runtime_brain",
        "approval_queue",
    }
    assert len(model["surface_statuses"]) == 7
    assert model["panels"]["personal_map_review_apply"]["authority"]["runs_apply_command"] is False
    assert model["panels"]["personal_map_live_apply_proof"]["authority"]["runs_live_apply"] is False


def test_product_shell_render_contains_product_regions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    model = build_pulse_product_shell(vault, deck_path=deck_path)
    html = render_pulse_product_shell_html(model)

    assert "<!doctype html>" in html
    assert "ChaseOS Pulse" in html
    assert "Surface Status" in html
    assert "Personal Map" in html
    assert "Runtime And Approval" in html
    assert "Pulse Cards" in html
    assert "Blocked Authority" in html


def test_product_shell_write_stays_inside_product_shell_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    model = write_pulse_product_shell_html(
        vault,
        deck_path=deck_path,
        generated_at="2026-05-03T11:30:00+01:00",
    )
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-pulse-product-shell.html"
    assert output.parent == vault / "07_LOGS" / "Pulse-Decks" / "product-shell"


def test_product_shell_rejects_output_outside_product_shell_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)

    with pytest.raises(ValueError):
        write_pulse_product_shell_html(
            vault,
            deck_path=deck_path,
            output_path=vault / "07_LOGS" / "bad-product-shell.html",
        )
