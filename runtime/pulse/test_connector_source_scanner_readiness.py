from __future__ import annotations

from pathlib import Path

from runtime.pulse.connector_source_scanner_readiness import (
    BLOCKED_EFFECTS,
    build_pulse_connector_source_scanner_readiness,
)


def _write(vault: Path, rel_path: str, text: str = "x") -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_connector_source_scanner_readiness_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _write(vault, "runtime/capture/capture.py")
    _write(vault, "runtime/capture/connectors/rss_connector.py")
    _write(vault, "runtime/acquisition/adapters/rss_live_adapter.py")
    _write(vault, "runtime/source_intelligence/output/example.json")
    _write(vault, "03_INPUTS/00_QUARANTINE/example.md")
    _write(vault, "07_LOGS/Pulse-Decks/users/example.json")
    before = _snapshot(vault)

    readiness = build_pulse_connector_source_scanner_readiness(
        vault,
        generated_at="2026-05-03T14:35:00+01:00",
    )
    payload = readiness.to_dict()

    assert _snapshot(vault) == before
    assert payload["read_only"] is True
    assert payload["local_inventory_only"] is True
    assert payload["reads_source_content"] is False
    assert payload["writes_artifacts"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["unrestricted_web_scan_allowed"] is False
    assert payload["browser_history_ingest_allowed"] is False
    assert payload["credential_or_secret_read_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert set(payload["blocked_effects"]) == set(BLOCKED_EFFECTS)


def test_external_connectors_are_available_but_not_live_enabled(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _write(vault, "runtime/capture/connectors/perplexity_connector.py")
    _write(vault, "runtime/capture/connectors/grok_connector.py")
    _write(vault, "runtime/acquisition/adapters/email_adapter.py")
    _write(vault, "runtime/acquisition/adapters/google_adapter.py")

    readiness = build_pulse_connector_source_scanner_readiness(vault)
    external = [
        connector
        for connector in readiness.connector_contracts
        if connector.external_call
    ]

    assert external
    assert all(connector.approval_required_for_live for connector in external)
    assert all(connector.live_execution_enabled is False for connector in external)
    assert all(connector.secrets_read is False for connector in external)


def test_current_repo_connector_source_scanner_readiness_contract() -> None:
    vault = Path(__file__).resolve().parents[2]

    readiness = build_pulse_connector_source_scanner_readiness(vault)
    payload = readiness.to_dict()

    assert payload["readiness_status"] in {
        "contract_ready_live_execution_blocked",
        "partial",
    }
    assert payload["source_surface_count"] >= 4
    assert payload["connector_count"] >= 5
    assert payload["live_enabled_connector_count"] == 0
    assert payload["provider_or_connector_call_allowed"] is False
    assert "browser_history" in payload["denied_source_classes"]
    assert "local_file" in payload["allowed_source_classes"]
