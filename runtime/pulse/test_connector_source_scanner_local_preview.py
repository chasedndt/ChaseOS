from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.connector_source_scanner_local_preview import (
    build_pulse_connector_source_scanner_local_preview,
    write_pulse_connector_source_scanner_local_preview,
)


def _write(vault: Path, rel_path: str, text: str = "SECRET-LIKE CONTENT SHOULD NOT APPEAR") -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write(vault, "07_LOGS/Pulse-Decks/users/2026-05-03-user.json")
    _write(vault, "runtime/source_intelligence/output/source.json")
    _write(vault, "03_INPUTS/00_QUARANTINE/source.md")
    _write(vault, "07_LOGS/Build-Logs/build.md")
    _write(vault, "07_LOGS/Agent-Activity/activity.md")
    _write(vault, "runtime/acquisition/packs/pack.json")
    _write(vault, "runtime/capture/capture.py")
    _write(vault, "runtime/capture/connectors/rss_connector.py")
    _write(vault, "runtime/acquisition/adapters/rss_live_adapter.py")


def test_local_preview_is_read_only_and_metadata_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    preview = build_pulse_connector_source_scanner_local_preview(
        vault,
        generated_at="2026-05-03T15:00:00+01:00",
        limit=10,
    )
    payload = preview.to_dict()

    assert _snapshot(vault) == before
    assert payload["preview_status"] == "ready"
    assert payload["candidate_count"] > 0
    assert payload["read_only"] is True
    assert payload["source_content_read"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["browser_history_ingest_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert "SECRET-LIKE CONTENT" not in json.dumps(payload)


def test_local_preview_write_stays_under_pulse_preview_logs(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    preview = write_pulse_connector_source_scanner_local_preview(
        vault,
        generated_at="2026-05-03T15:05:00+01:00",
        limit=5,
    )
    payload = preview.to_dict()

    assert payload["read_only"] is False
    assert payload["writes_artifacts"] is True
    assert payload["writes"] == [
        "07_LOGS/Pulse-Decks/source-scanner-preview/2026-05-03-source-scanner-local-preview.json"
    ]
    assert (vault / payload["writes"][0]).exists()


def test_local_preview_rejects_output_outside_preview_logs(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError):
        write_pulse_connector_source_scanner_local_preview(
            vault,
            output_path="07_LOGS/Pulse-Decks/bad.json",
        )


def test_current_repo_local_preview_has_no_live_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    preview = build_pulse_connector_source_scanner_local_preview(vault, limit=12)
    payload = preview.to_dict()

    assert payload["candidate_count"] > 0
    assert payload["source_content_read"] is False
    assert payload["live_connector_execution_enabled"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["unrestricted_web_scan_allowed"] is False
    assert payload["credential_or_secret_read_allowed"] is False
