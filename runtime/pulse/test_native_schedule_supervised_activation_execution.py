from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.native_schedule_activation_gate import REQUIRED_EVIDENCE_SLOTS
from runtime.pulse.native_schedule_supervised_activation_execution import (
    build_pulse_native_schedule_supervised_activation_execution,
    write_pulse_native_schedule_supervised_activation_execution_proof,
)
from runtime.pulse.test_native_schedule_runner_proof import _write_manifest


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write_manifest(vault, "chaseos_pulse_daily")
    _write_manifest(vault, "hermes_runtime_pulse")


def _refs() -> dict[str, str]:
    return {slot: f"approval-{slot}-2026-05-03" for slot in REQUIRED_EVIDENCE_SLOTS}


def test_supervised_activation_execution_dry_run_blocks_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    proof = build_pulse_native_schedule_supervised_activation_execution(
        vault,
        generated_at="2026-05-03T20:10:00+00:00",
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["execution_status"] == "blocked_activation_gate_not_ready"
    assert set(payload["missing_evidence_slots"]) == set(REQUIRED_EVIDENCE_SLOTS)
    assert payload["execute_requested"] is False
    assert payload["write_executed"] is False
    assert payload["schedule_manifest_write_executed"] is False
    assert payload["schedule_activation_executed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["real_run_queue_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_supervised_activation_execution_ready_refs_still_require_execute_flag(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    proof = build_pulse_native_schedule_supervised_activation_execution(
        vault,
        generated_at="2026-05-03T20:15:00+00:00",
        evidence_refs=_refs(),
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["execution_status"] == "ready_for_supervised_activation_execution"
    assert payload["missing_evidence_slots"] == []
    assert payload["execute_requested"] is False
    assert payload["schedule_manifest_write_executed"] is False
    assert payload["schedule_activation_executed"] is False


def test_supervised_activation_execution_write_proof_is_artifact_only_without_execute(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    proof = write_pulse_native_schedule_supervised_activation_execution_proof(
        vault,
        generated_at="2026-05-03T20:20:00+00:00",
        evidence_refs=_refs(),
    )
    payload = proof.to_dict()

    assert payload["execution_status"] == "ready_for_supervised_activation_execution"
    assert payload["write_executed"] is True
    assert payload["schedule_manifest_write_executed"] is False
    assert payload["schedule_activation_executed"] is False
    assert len(payload["writes"]) == 1
    rel_path = payload["writes"][0]
    assert rel_path.startswith("07_LOGS/Pulse-Decks/native-schedule-activation-executions/")
    written = json.loads((vault / rel_path).read_text(encoding="utf-8"))
    assert written["schedule_manifest_write_executed"] is False
    assert written["workflow_execution_allowed"] is False


def test_supervised_activation_execution_rejects_execute_without_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="activation gate is ready"):
        write_pulse_native_schedule_supervised_activation_execution_proof(
            vault,
            generated_at="2026-05-03T20:25:00+00:00",
            execute_activation=True,
        )


def test_supervised_activation_execution_can_patch_temp_manifests_with_all_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    proof = write_pulse_native_schedule_supervised_activation_execution_proof(
        vault,
        generated_at="2026-05-03T20:30:00+00:00",
        evidence_refs=_refs(),
        execute_activation=True,
    )
    payload = proof.to_dict()

    assert payload["execution_status"] == "supervised_activation_execution_recorded"
    assert payload["schedule_manifest_write_executed"] is True
    assert payload["schedule_activation_executed"] is True
    assert payload["schedule_daemon_started"] is False
    assert payload["real_run_queue_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert payload["manifest_patch_count"] == 2
    for schedule_id in ("chaseos_pulse_daily", "hermes_runtime_pulse"):
        text = (
            vault
            / "runtime"
            / "schedules"
            / "manifests"
            / f"{schedule_id}.yaml"
        ).read_text(encoding="utf-8")
        assert "status: active" in text
        assert "enabled: true" in text
        assert "activation_state: active_supervised" in text
        assert "workflow_execution_started: false" in text
        assert "agent_bus_task_written: false" in text
        assert "canonical_writeback_enabled: false" in text


def test_supervised_activation_execution_write_guard_rejects_outside_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)

    with pytest.raises(ValueError, match="must be written under"):
        write_pulse_native_schedule_supervised_activation_execution_proof(
            vault,
            generated_at="2026-05-03T20:35:00+00:00",
            evidence_refs=_refs(),
            output_path="07_LOGS/not-pulse-activation-execution.json",
        )


def test_current_repo_supervised_activation_execution_has_no_execution_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    proof = build_pulse_native_schedule_supervised_activation_execution(vault)
    payload = proof.to_dict()

    assert payload["execution_status"] == "blocked_activation_gate_not_ready"
    assert payload["schedule_count"] >= 2
    assert payload["execute_requested"] is False
    assert payload["schedule_manifest_write_executed"] is False
    assert payload["schedule_activation_executed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["real_run_queue_written"] is False
    assert payload["real_audit_event_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["external_scheduler_install_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
