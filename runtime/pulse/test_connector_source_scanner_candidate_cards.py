from __future__ import annotations

import json
from pathlib import Path

from runtime.pulse.connector_source_scanner_candidate_cards import (
    build_pulse_connector_source_scanner_candidate_cards,
    build_pulse_connector_source_scanner_candidate_decks,
)


SECRET_TEXT = "SECRET-LIKE SOURCE CONTENT SHOULD NOT APPEAR"


def _write(vault: Path, rel_path: str, text: str = SECRET_TEXT) -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write(vault, "07_LOGS/Pulse-Decks/users/2026-05-03-user-pulse.json")
    _write(vault, "runtime/source_intelligence/workspaces/demo/workspace.json")
    _write(vault, "03_INPUTS/00_QUARANTINE/source.md")
    _write(vault, "07_LOGS/Build-Logs/build.md")
    _write(vault, "07_LOGS/Agent-Activity/activity.md")
    _write(vault, "runtime/acquisition/packs/pack.json")
    _write(vault, "runtime/capture/connectors/rss_connector.py")
    _write(vault, "runtime/acquisition/adapters/rss_live_adapter.py")


def test_candidate_cards_are_dry_run_metadata_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    model = build_pulse_connector_source_scanner_candidate_cards(
        vault,
        generated_at="2026-05-03T16:00:00+00:00",
        limit=12,
    )
    payload = model.to_dict()

    assert _snapshot(vault) == before
    assert payload["status"] == "ready"
    assert payload["deck_count"] == 3
    assert payload["card_count"] > 0
    assert payload["read_only"] is True
    assert payload["write_executed"] is False
    assert payload["source_content_read"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["unrestricted_web_scan_allowed"] is False
    assert payload["browser_history_ingest_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert SECRET_TEXT not in json.dumps(payload)


def test_candidate_decks_validate_core_card_requirements(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    decks = build_pulse_connector_source_scanner_candidate_decks(
        vault,
        generated_at="2026-05-03T16:05:00+00:00",
        limit=12,
    )

    assert {deck.audience for deck in decks} == {"user", "agent", "shared_coordination"}
    for deck in decks:
        deck.validate()
        assert deck.canonical_writeback_enabled is False
        for card in deck.cards:
            assert card.evidence
            assert card.source_links
            assert card.related_nodes
            assert card.recommended_actions
            assert card.thumbnails
            assert card.writeback_status == "card_generated"
            assert card.promotion_status == "not_promoted"
            assert card.canonical_writeback_enabled is False
            assert SECRET_TEXT not in json.dumps(card.to_dict())


def test_candidate_card_write_stays_under_pulse_decks(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    model = build_pulse_connector_source_scanner_candidate_cards(
        vault,
        generated_at="2026-05-03T16:10:00+00:00",
        limit=12,
        slug_prefix="2026-05-03-test",
        write=True,
    )
    payload = model.to_dict()

    assert payload["read_only"] is False
    assert payload["write_executed"] is True
    assert payload["writes_artifacts"] is True
    assert len(payload["writes"]) == 6
    for rel_path in payload["writes"]:
        assert rel_path.replace("\\", "/").startswith("07_LOGS/Pulse-Decks/")
        assert (vault / rel_path).exists()
    assert SECRET_TEXT not in json.dumps(payload)


def test_current_repo_candidate_cards_have_no_live_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    model = build_pulse_connector_source_scanner_candidate_cards(vault, limit=12)
    payload = model.to_dict()

    assert payload["status"] == "ready"
    assert payload["card_count"] > 0
    assert payload["source_content_read"] is False
    assert payload["live_connector_execution_enabled"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["credential_or_secret_read_allowed"] is False
    assert payload["source_promotion_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
