from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.native_schedule_activation_gate import REQUIRED_EVIDENCE_SLOTS
from runtime.pulse.native_schedule_run_queue_audit_proof import (
    build_pulse_native_schedule_run_queue_audit_proof,
    write_pulse_native_schedule_run_queue_audit_proof,
)
from runtime.pulse.test_native_schedule_runner_proof import _write_manifest


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write_manifest(vault, "chaseos_pulse_daily")
    _write_manifest(vault, "hermes_runtime_pulse")


def _refs() -> dict[str, str]:
    return {slot: f"evidence-{slot}-2026-05-03" for slot in REQUIRED_EVIDENCE_SLOTS}


def test_run_queue_audit_proof_blocks_without_gate_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    proof = build_pulse_native_schedule_run_queue_audit_proof(
        vault,
        generated_at="2026-05-03T20:20:00+00:00",
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["proof_status"] == "blocked_activation_gate_not_ready"
    assert payload["gate_status"] == "blocked_missing_activation_evidence"
    assert set(payload["missing_evidence_slots"]) == set(REQUIRED_EVIDENCE_SLOTS)
    assert payload["proof_queue_entry_count"] == 0
    assert payload["proof_audit_event_count"] == 0
    assert payload["real_run_queue_written"] is False
    assert payload["real_audit_event_written"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_run_queue_audit_proof_builds_proof_only_shapes_when_gate_ready(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    proof = build_pulse_native_schedule_run_queue_audit_proof(
        vault,
        generated_at="2026-05-03T20:25:00+00:00",
        evidence_refs=_refs(),
    )
    payload = proof.to_dict()

    assert payload["proof_status"] == "run_queue_audit_proof_ready"
    assert payload["missing_evidence_slots"] == []
    assert payload["proof_queue_entry_count"] == 2
    assert payload["proof_audit_event_count"] == 2
    assert {entry["queue_status"] for entry in payload["run_queue_entries"]} == {
        "proof_only_not_enqueued"
    }
    assert {event["audit_status"] for event in payload["audit_events"]} == {
        "proof_only_not_enqueued"
    }
    assert payload["real_run_queue_written"] is False
    assert payload["real_audit_event_written"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False


def test_run_queue_audit_write_is_artifact_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    proof = write_pulse_native_schedule_run_queue_audit_proof(
        vault,
        generated_at="2026-05-03T20:30:00+00:00",
        evidence_refs=_refs(),
    )
    payload = proof.to_dict()

    assert payload["write_executed"] is True
    assert payload["writes_artifacts"] is True
    assert len(payload["writes"]) == 1
    rel_path = payload["writes"][0]
    assert rel_path.startswith("07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/")
    written = json.loads((vault / rel_path).read_text(encoding="utf-8"))
    assert written["proof_status"] == "run_queue_audit_proof_ready"
    assert written["real_run_queue_written"] is False
    assert written["real_audit_event_written"] is False
    assert written["schedule_activation_allowed"] is False
    assert written["workflow_execution_allowed"] is False


def test_run_queue_audit_write_guard_rejects_outside_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="must be written under"):
        write_pulse_native_schedule_run_queue_audit_proof(
            vault,
            output_path="07_LOGS/not-run-queue-proof.json",
            evidence_refs=_refs(),
        )


def test_current_repo_run_queue_audit_proof_has_no_execution_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    proof = build_pulse_native_schedule_run_queue_audit_proof(vault)
    payload = proof.to_dict()

    assert payload["proof_status"] == "blocked_activation_gate_not_ready"
    assert payload["schedule_count"] >= 2
    assert payload["real_run_queue_written"] is False
    assert payload["real_audit_event_written"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["schedule_manifest_write_allowed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["external_scheduler_install_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
