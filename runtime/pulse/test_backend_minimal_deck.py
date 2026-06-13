from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck
from runtime.pulse.minimal_deck import (
    DEFAULT_MINIMAL_AGENT_CLASSES,
    DEFAULT_MINIMAL_SHARED_CLASSES,
    DEFAULT_MINIMAL_USER_CLASSES,
    build_minimal_agent_deck,
    build_minimal_shared_coordination_deck,
    build_minimal_user_deck,
    generate_and_write_minimal_agent_deck,
    generate_and_write_minimal_shared_coordination_deck,
)
from runtime.pulse.writeback import deck_artifact_paths, write_deck_artifacts


def _temp_vault(name: str) -> Path:
    base = (Path(__file__).resolve().parent / "_tmp_backend_minimal_deck").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if base.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {base}")
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _cleanup_temp_vault(vault: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_backend_minimal_deck").resolve()
    if vault.resolve().parent != base:
        raise RuntimeError(f"Refusing unsafe test cleanup: {vault}")
    if vault.exists():
        shutil.rmtree(vault)


def _seed_minimal_vault(vault: Path) -> None:
    for rel_path in [
        "00_HOME/Now.md",
        "00_HOME/Dashboard.md",
        "06_AGENTS/ChaseOS-Pulse-Architecture.md",
        "06_AGENTS/Context-Memory-Core.md",
        "06_AGENTS/Pulse-Truth-State-Audit-Checklist.md",
        "runtime/pulse/signal_collector.py",
        "runtime/memory/README.md",
        "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
        "runtime/schedules/manifests/hermes_runtime_pulse.yaml",
        "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-architecture-scaffolding.md",
        "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-scaffold-audit.md",
        "07_LOGS/Agent-Activity/example.md",
    ]:
        path = vault / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test\n", encoding="utf-8")


def test_minimal_user_deck_has_phase_b_card_set() -> None:
    vault = _temp_vault("phase_b_card_set")
    try:
        _seed_minimal_vault(vault)
        deck = build_minimal_user_deck(
            vault,
            deck_id="pulse-user-test",
            generated_at="2026-04-29T07:30:00+00:00",
        )

        assert deck.audience == "user"
        assert deck.schedule_ref == "runtime/schedules/manifests/chaseos_pulse_daily.yaml"
        assert deck.canonical_writeback_enabled is False
        assert [card.card_class for card in deck.cards] == DEFAULT_MINIMAL_USER_CLASSES
        assert len(deck.cards) == 8
        assert all(card.evidence for card in deck.cards)
        assert all(card.related_nodes for card in deck.cards)
        assert all(card.recommended_actions for card in deck.cards)
    finally:
        _cleanup_temp_vault(vault)


def test_minimal_agent_and_shared_decks_are_feature_only_non_visual_outputs() -> None:
    vault = _temp_vault("agent_shared_decks")
    try:
        _seed_minimal_vault(vault)
        agent_deck = build_minimal_agent_deck(
            vault,
            deck_id="pulse-agent-test",
            generated_at="2026-05-02T16:00:00+00:00",
        )
        shared_deck = build_minimal_shared_coordination_deck(
            vault,
            deck_id="pulse-shared-test",
            generated_at="2026-05-02T16:00:00+00:00",
        )

        assert agent_deck.audience == "agent"
        assert shared_deck.audience == "shared_coordination"
        assert [card.card_class for card in agent_deck.cards] == DEFAULT_MINIMAL_AGENT_CLASSES
        assert [card.card_class for card in shared_deck.cards] == DEFAULT_MINIMAL_SHARED_CLASSES
        assert all(card.audience == "agent" for card in agent_deck.cards)
        assert all(card.audience == "shared_coordination" for card in shared_deck.cards)
        assert agent_deck.canonical_writeback_enabled is False
        assert shared_deck.canonical_writeback_enabled is False
        assert all(action.requires_operator_approval is False for card in agent_deck.cards for action in card.recommended_actions)
        assert all(action.requires_operator_approval is False for card in shared_deck.cards for action in card.recommended_actions)
    finally:
        _cleanup_temp_vault(vault)


def test_agent_and_shared_deck_writers_stay_under_pulse_logs() -> None:
    vault = _temp_vault("agent_shared_writer_outputs")
    try:
        _seed_minimal_vault(vault)
        agent_artifact = generate_and_write_minimal_agent_deck(
            vault,
            deck_id="pulse-agent-test",
            slug="2026-05-02-agent-pulse",
            generated_at="2026-05-02T16:00:00+00:00",
        )
        shared_artifact = generate_and_write_minimal_shared_coordination_deck(
            vault,
            deck_id="pulse-shared-test",
            slug="2026-05-02-shared-pulse",
            generated_at="2026-05-02T16:00:00+00:00",
        )

        assert agent_artifact.markdown_path in {
            "07_LOGS\\Pulse-Decks\\agents\\2026-05-02-agent-pulse.md",
            "07_LOGS/Pulse-Decks/agents/2026-05-02-agent-pulse.md",
        }
        assert shared_artifact.markdown_path in {
            "07_LOGS\\Pulse-Decks\\shared\\2026-05-02-shared-pulse.md",
            "07_LOGS/Pulse-Decks/shared/2026-05-02-shared-pulse.md",
        }
        assert agent_artifact.canonical_writeback_enabled is False
        assert shared_artifact.canonical_writeback_enabled is False
        assert (vault / agent_artifact.json_path).exists()
        assert (vault / shared_artifact.json_path).exists()
    finally:
        _cleanup_temp_vault(vault)


def test_deck_writer_outputs_markdown_and_json_under_pulse_logs() -> None:
    vault = _temp_vault("writer_outputs")
    try:
        _seed_minimal_vault(vault)
        deck = build_minimal_user_deck(
            vault,
            deck_id="pulse-user-test",
            generated_at="2026-04-29T07:30:00+00:00",
        )
        artifact = write_deck_artifacts(vault, deck, slug="2026-04-29-user-pulse")

        markdown_path = vault / artifact.markdown_path
        json_path = vault / artifact.json_path
        assert artifact.canonical_writeback_enabled is False
        assert artifact.markdown_path in {
            "07_LOGS\\Pulse-Decks\\users\\2026-04-29-user-pulse.md",
            "07_LOGS/Pulse-Decks/users/2026-04-29-user-pulse.md",
        }
        assert markdown_path.exists()
        assert json_path.exists()
        assert "ChaseOS Pulse Deck" in markdown_path.read_text(encoding="utf-8")
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["deck_id"] == "pulse-user-test"
        assert payload["cards"][0]["feedback"] == []
    finally:
        _cleanup_temp_vault(vault)


def test_deck_writer_rejects_path_traversal_slug() -> None:
    vault = _temp_vault("path_traversal")
    try:
        deck = PulseDeck(deck_id="safe", audience="user")

        try:
            deck_artifact_paths(vault, deck, slug="../bad")
        except ValueError as exc:
            assert "slug" in str(exc)
        else:
            raise AssertionError("path traversal slug should fail")
    finally:
        _cleanup_temp_vault(vault)


def test_deck_writer_rejects_canonical_writeback() -> None:
    vault = _temp_vault("canonical_writeback")
    try:
        deck = PulseDeck(deck_id="unsafe", audience="user", canonical_writeback_enabled=True)

        try:
            write_deck_artifacts(vault, deck)
        except ValueError as exc:
            assert "canonical writeback" in str(exc)
        else:
            raise AssertionError("canonical deck output should fail")
    finally:
        _cleanup_temp_vault(vault)


def test_card_schema_accepts_source_urls_and_expanded_classes() -> None:
    card = PulseCard(
        card_id="research-watch",
        audience="user",
        card_class="Research Watch",
        title="Research stays opt-in",
        summary="External links can be represented without enabling external scanning.",
        evidence=[
            EvidenceRef(
                source_path="03_INPUTS/example.md",
                source_type="source_intelligence",
                summary="Imported source reference.",
                source_url="https://example.invalid/source",
            )
        ],
    )

    payload = card.to_dict()
    assert payload["evidence"][0]["source_url"] == "https://example.invalid/source"
