from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.connector_source_scanner_live_proof import (
    build_pulse_connector_source_scanner_live_proof,
    write_pulse_connector_source_scanner_live_proof_request,
)


SECRET_TEXT = "SECRET-LIKE SOURCE CONTENT SHOULD NOT APPEAR"


def _write(vault: Path, rel_path: str, text: str = SECRET_TEXT) -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write(vault, "runtime/capture/connectors/rss_connector.py")
    _write(vault, "runtime/acquisition/adapters/rss_live_adapter.py")
    _write(vault, "07_LOGS/Build-Logs/build.md")
    _write(vault, "07_LOGS/Agent-Activity/activity.md")
    _write(vault, "07_LOGS/Pulse-Decks/users/user.json")


def test_live_proof_is_dry_run_and_fail_closed(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    model = build_pulse_connector_source_scanner_live_proof(
        vault,
        generated_at="2026-05-03T16:40:00+00:00",
        connector_id="all",
    )
    payload = model.to_dict()

    assert _snapshot(vault) == before
    assert payload["status"] == "blocked_missing_operator_permission_envelope"
    assert payload["target_count"] >= 1
    assert payload["write_executed"] is False
    assert payload["source_content_read"] is False
    assert payload["live_connector_execution_enabled"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["source_promotion_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert SECRET_TEXT not in json.dumps(payload)


def test_live_proof_write_creates_pending_request_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    model = write_pulse_connector_source_scanner_live_proof_request(
        vault,
        generated_at="2026-05-03T16:45:00+00:00",
        connector_id="acquisition_rss_live",
    )
    payload = model.to_dict()

    assert payload["write_executed"] is True
    assert payload["writes_artifacts"] is True
    assert len(payload["writes"]) == 1
    written = payload["writes"][0]
    assert written.startswith("07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/")
    written_payload = json.loads((vault / written).read_text(encoding="utf-8"))
    assert written_payload["status"] == "pending_operator_review"
    assert written_payload["approval_granted"] is False
    assert written_payload["execution_allowed"] is False
    assert written_payload["connector_id"] == "acquisition_rss_live"
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert SECRET_TEXT not in json.dumps(payload)


def test_live_proof_rejects_unknown_or_non_live_connector(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="unknown or non-live connector_id"):
        build_pulse_connector_source_scanner_live_proof(vault, connector_id="capture_file")


def test_live_proof_write_guard_rejects_outside_pulse_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="must be written under"):
        write_pulse_connector_source_scanner_live_proof_request(
            vault,
            connector_id="acquisition_rss_live",
            output_path="07_LOGS/not-pulse-request.json",
        )


def test_current_repo_live_proof_has_no_live_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    model = build_pulse_connector_source_scanner_live_proof(vault, connector_id="all")
    payload = model.to_dict()

    assert payload["status"] == "blocked_missing_operator_permission_envelope"
    assert payload["target_count"] > 0
    assert payload["source_content_read"] is False
    assert payload["live_connector_execution_enabled"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["unrestricted_web_scan_allowed"] is False
    assert payload["browser_history_ingest_allowed"] is False
    assert payload["credential_or_secret_read_allowed"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["source_promotion_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
