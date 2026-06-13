from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.native_schedule_activation_gate import (
    REQUIRED_EVIDENCE_SLOTS,
    build_pulse_native_schedule_activation_gate,
    write_pulse_native_schedule_activation_request,
)
from runtime.pulse.test_native_schedule_runner_proof import _write_manifest


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write_manifest(vault, "chaseos_pulse_daily")
    _write_manifest(vault, "hermes_runtime_pulse")


def _refs() -> dict[str, str]:
    return {slot: f"approval-{slot}-2026-05-03" for slot in REQUIRED_EVIDENCE_SLOTS}


def test_activation_gate_dry_run_is_blocked_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    gate = build_pulse_native_schedule_activation_gate(
        vault,
        generated_at="2026-05-03T19:00:00+00:00",
    )
    payload = gate.to_dict()

    assert _snapshot(vault) == before
    assert payload["gate_status"] == "blocked_missing_activation_evidence"
    assert payload["schedule_count"] == 2
    assert payload["enabled_schedule_count"] == 0
    assert set(payload["missing_evidence_slots"]) == set(REQUIRED_EVIDENCE_SLOTS)
    assert payload["write_executed"] is False
    assert payload["approval_granted"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["schedule_manifest_write_allowed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["run_queue_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_activation_gate_ready_refs_still_do_not_execute(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    gate = build_pulse_native_schedule_activation_gate(
        vault,
        generated_at="2026-05-03T19:05:00+00:00",
        evidence_refs=_refs(),
    )
    payload = gate.to_dict()

    assert payload["gate_status"] == "ready_for_operator_supervised_activation"
    assert payload["missing_evidence_slots"] == []
    assert payload["schedule_activation_allowed"] is False
    assert payload["run_queue_written"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_activation_request_write_is_artifact_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    gate = write_pulse_native_schedule_activation_request(
        vault,
        generated_at="2026-05-03T19:10:00+00:00",
    )
    payload = gate.to_dict()

    assert payload["write_executed"] is True
    assert payload["writes_artifacts"] is True
    assert len(payload["writes"]) == 1
    rel_path = payload["writes"][0]
    assert rel_path.startswith("07_LOGS/Pulse-Decks/native-schedule-activation-requests/")
    written = json.loads((vault / rel_path).read_text(encoding="utf-8"))
    assert written["status"] == "pending_operator_review"
    assert written["approval_granted"] is False
    assert written["execution_allowed"] is False
    assert set(written["missing_evidence_slots"]) == set(REQUIRED_EVIDENCE_SLOTS)
    assert payload["schedule_activation_allowed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["run_queue_written"] is False


def test_activation_request_write_guard_rejects_outside_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="must be written under"):
        write_pulse_native_schedule_activation_request(
            vault,
            output_path="07_LOGS/not-pulse-activation-request.json",
        )


def test_current_repo_activation_gate_has_no_execution_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    gate = build_pulse_native_schedule_activation_gate(vault)
    payload = gate.to_dict()

    assert payload["gate_status"] == "blocked_missing_activation_evidence"
    assert payload["schedule_count"] >= 2
    assert payload["enabled_schedule_count"] == 0
    assert payload["approval_granted"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["schedule_manifest_write_allowed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["run_queue_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["external_scheduler_install_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
