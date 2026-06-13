from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.connector_source_scanner_live_execution_proof import (
    PulseConnectorSourceScannerExecutionResult,
    build_pulse_connector_source_scanner_live_execution_proof,
    write_pulse_connector_source_scanner_live_execution_proof,
)
from runtime.pulse.connector_source_scanner_live_proof import REQUIRED_EVIDENCE_SLOTS


SECRET_TEXT = "SECRET-LIKE SOURCE CONTENT SHOULD NOT APPEAR"


def _write(vault: Path, rel_path: str, text: str = SECRET_TEXT) -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write(vault, "runtime/acquisition/adapters/rss_live_adapter.py")
    _write(vault, "07_LOGS/Build-Logs/build.md")
    _write(vault, "07_LOGS/Agent-Activity/activity.md")
    _write(vault, "07_LOGS/Pulse-Decks/users/user.json")


def _refs() -> dict[str, str]:
    return {slot: f"approval-{slot}-2026-05-03" for slot in REQUIRED_EVIDENCE_SLOTS}


def test_live_execution_proof_dry_run_blocks_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    proof = build_pulse_connector_source_scanner_live_execution_proof(
        vault,
        generated_at="2026-05-03T21:00:00+00:00",
        connector_id="acquisition_rss_live",
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["execution_status"] == "blocked_missing_operator_permission_envelope"
    assert set(payload["missing_evidence_slots"]) == set(REQUIRED_EVIDENCE_SLOTS)
    assert payload["execute_requested"] is False
    assert payload["write_executed"] is False
    assert payload["connector_runner_bound"] is False
    assert payload["live_connector_execution_executed"] is False
    assert payload["provider_or_connector_call_executed"] is False
    assert payload["source_content_read"] is False
    assert payload["credential_or_secret_read_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert SECRET_TEXT not in json.dumps(payload)


def test_live_execution_proof_ready_refs_still_do_not_execute(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    proof = build_pulse_connector_source_scanner_live_execution_proof(
        vault,
        generated_at="2026-05-03T21:05:00+00:00",
        connector_id="acquisition_rss_live",
        evidence_refs=_refs(),
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["execution_status"] == "ready_for_live_connector_execution"
    assert payload["missing_evidence_slots"] == []
    assert payload["execute_requested"] is False
    assert payload["live_connector_execution_executed"] is False
    assert payload["provider_or_connector_call_executed"] is False


def test_live_execution_proof_write_without_execute_is_artifact_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    proof = write_pulse_connector_source_scanner_live_execution_proof(
        vault,
        generated_at="2026-05-03T21:10:00+00:00",
        connector_id="acquisition_rss_live",
        evidence_refs=_refs(),
    )
    payload = proof.to_dict()

    assert payload["execution_status"] == "ready_for_live_connector_execution"
    assert payload["write_executed"] is True
    assert payload["live_connector_execution_executed"] is False
    assert payload["provider_or_connector_call_executed"] is False
    assert len(payload["writes"]) == 1
    written = payload["writes"][0]
    assert written.startswith("07_LOGS/Pulse-Decks/source-scanner-live-executions/")
    written_payload = json.loads((vault / written).read_text(encoding="utf-8"))
    assert written_payload["live_connector_execution_executed"] is False
    assert written_payload["canonical_writeback_allowed"] is False


def test_live_execution_rejects_execute_without_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="all evidence refs are ready"):
        write_pulse_connector_source_scanner_live_execution_proof(
            vault,
            generated_at="2026-05-03T21:15:00+00:00",
            connector_id="acquisition_rss_live",
            execute_live_scan=True,
        )


def test_live_execution_with_evidence_but_no_runner_blocks_and_writes_proof(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    proof = write_pulse_connector_source_scanner_live_execution_proof(
        vault,
        generated_at="2026-05-03T21:20:00+00:00",
        connector_id="acquisition_rss_live",
        evidence_refs=_refs(),
        execute_live_scan=True,
    )
    payload = proof.to_dict()

    assert payload["execution_status"] == "blocked_missing_live_connector_runner"
    assert payload["execute_requested"] is True
    assert payload["connector_runner_bound"] is False
    assert payload["live_connector_execution_executed"] is False
    assert payload["provider_or_connector_call_executed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_live_execution_with_injected_runner_records_result_without_canonical_writeback(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    def runner(_target) -> PulseConnectorSourceScannerExecutionResult:
        return PulseConnectorSourceScannerExecutionResult(
            connector_id="acquisition_rss_live",
            result_status="simulated_connector_result_recorded",
            result_ref="07_LOGS/Pulse-Decks/source-scanner-live-executions/simulated-result.json",
            item_count=3,
        )

    proof = write_pulse_connector_source_scanner_live_execution_proof(
        vault,
        generated_at="2026-05-03T21:25:00+00:00",
        connector_id="acquisition_rss_live",
        evidence_refs=_refs(),
        execute_live_scan=True,
        connector_runner=runner,
    )
    payload = proof.to_dict()

    assert payload["execution_status"] == "live_connector_execution_recorded"
    assert payload["connector_runner_bound"] is True
    assert payload["live_connector_execution_executed"] is True
    assert payload["provider_or_connector_call_executed"] is True
    assert payload["execution_result_count"] == 1
    assert payload["source_content_read"] is False
    assert payload["credential_or_secret_read_allowed"] is False
    assert payload["source_promotion_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert SECRET_TEXT not in json.dumps(payload)


def test_live_execution_rejects_all_connector_execution(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="one explicit connector_id"):
        write_pulse_connector_source_scanner_live_execution_proof(
            vault,
            generated_at="2026-05-03T21:30:00+00:00",
            connector_id="all",
            evidence_refs=_refs(),
            execute_live_scan=True,
        )


def test_live_execution_write_guard_rejects_outside_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="must be written under"):
        write_pulse_connector_source_scanner_live_execution_proof(
            vault,
            connector_id="acquisition_rss_live",
            evidence_refs=_refs(),
            output_path="07_LOGS/not-source-execution.json",
        )


def test_current_repo_live_execution_proof_has_no_live_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    proof = build_pulse_connector_source_scanner_live_execution_proof(
        vault,
        connector_id="acquisition_rss_live",
    )
    payload = proof.to_dict()

    assert payload["execution_status"] == "blocked_missing_operator_permission_envelope"
    assert payload["target_count"] == 1
    assert payload["execute_requested"] is False
    assert payload["write_executed"] is False
    assert payload["connector_runner_bound"] is False
    assert payload["live_connector_execution_executed"] is False
    assert payload["provider_or_connector_call_executed"] is False
    assert payload["source_content_read"] is False
    assert payload["unrestricted_web_scan_allowed"] is False
    assert payload["browser_history_ingest_allowed"] is False
    assert payload["credential_or_secret_read_allowed"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["source_promotion_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
