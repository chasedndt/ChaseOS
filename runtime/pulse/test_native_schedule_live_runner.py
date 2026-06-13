from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.native_schedule_activation_gate import REQUIRED_EVIDENCE_SLOTS
from runtime.pulse.native_schedule_live_runner import (
    build_pulse_native_schedule_live_runner,
    write_pulse_native_schedule_live_runner_records,
)
from runtime.pulse.native_schedule_supervised_activation_execution import (
    write_pulse_native_schedule_supervised_activation_execution_proof,
)
from runtime.pulse.test_native_schedule_runner_proof import _write_manifest


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _seed(vault: Path) -> None:
    _write_manifest(vault, "chaseos_pulse_daily")
    _write_manifest(vault, "hermes_runtime_pulse")


def _refs() -> dict[str, str]:
    return {slot: f"approval-{slot}-2026-05-07" for slot in REQUIRED_EVIDENCE_SLOTS}


def _activate(vault: Path) -> None:
    write_pulse_native_schedule_supervised_activation_execution_proof(
        vault,
        generated_at="2026-05-07T08:00:00+00:00",
        evidence_refs=_refs(),
        execute_activation=True,
    )


def test_live_runner_blocks_inactive_manifests_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    runner = build_pulse_native_schedule_live_runner(
        vault,
        generated_at="2026-05-07T09:00:00+00:00",
        force_due=True,
    )
    payload = runner.to_dict()

    assert _snapshot(vault) == before
    assert payload["runner_status"] == "blocked_no_supervised_active_schedules"
    assert payload["active_schedule_count"] == 0
    assert payload["queue_entry_count"] == 0
    assert payload["write_executed"] is False
    assert payload["run_queue_write_executed"] is False
    assert payload["audit_event_write_executed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["schedule_manifest_write_executed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_live_runner_dry_run_prepares_due_supervised_schedules_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)
    before = _snapshot(vault)

    runner = build_pulse_native_schedule_live_runner(
        vault,
        generated_at="2026-05-07T09:05:00+00:00",
        force_due=True,
    )
    payload = runner.to_dict()

    assert _snapshot(vault) == before
    assert payload["runner_status"] == "ready_for_live_run_queue_write"
    assert payload["active_schedule_count"] == 2
    assert payload["due_schedule_count"] == 2
    assert payload["queue_entry_count"] == 2
    assert payload["audit_event_count"] == 2
    assert payload["execute_requested"] is False
    assert payload["write_executed"] is False
    assert payload["run_queue_entries"][0]["queue_status"] == "queued_pending_runtime_dispatch"
    assert payload["run_queue_entries"][0]["runtime_dispatch_allowed"] is False
    assert payload["audit_events"][0]["real_audit_event_written"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["workflow_execution_allowed"] is False


def test_live_runner_execute_writes_queue_audit_and_run_record_once(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)

    runner = write_pulse_native_schedule_live_runner_records(
        vault,
        generated_at="2026-05-07T09:10:00+00:00",
        force_due=True,
        execute=True,
    )
    payload = runner.to_dict()

    assert payload["runner_status"] == "live_run_queue_audit_written"
    assert payload["write_executed"] is True
    assert payload["run_queue_write_executed"] is True
    assert payload["audit_event_write_executed"] is True
    assert payload["queue_entry_count"] == 2
    assert payload["audit_event_count"] == 2
    assert len(payload["writes"]) == 3
    queue_path, audit_path, record_path = [vault / path for path in payload["writes"]]
    assert queue_path.is_file()
    assert audit_path.is_file()
    assert record_path.is_file()
    queue_lines = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]
    audit_lines = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert len(queue_lines) == 2
    assert len(audit_lines) == 2
    assert {line["schedule_id"] for line in queue_lines} == {"chaseos_pulse_daily", "hermes_runtime_pulse"}
    assert all(line["workflow_execution_allowed"] is False for line in queue_lines)
    assert all(line["real_audit_event_written"] is True for line in audit_lines)
    assert json.loads(record_path.read_text(encoding="utf-8"))["runner_status"] == "live_run_queue_audit_written"

    duplicate = write_pulse_native_schedule_live_runner_records(
        vault,
        generated_at="2026-05-07T09:15:00+00:00",
        force_due=True,
        execute=True,
    ).to_dict()

    assert duplicate["runner_status"] == "duplicate_run_already_queued"
    assert duplicate["duplicate_count"] == 2
    assert duplicate["queue_entry_count"] == 0
    assert duplicate["write_executed"] is False
    assert len(queue_path.read_text(encoding="utf-8").splitlines()) == 2
    assert len(audit_path.read_text(encoding="utf-8").splitlines()) == 2


def test_live_runner_blocks_not_due_without_force(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)

    runner = build_pulse_native_schedule_live_runner(
        vault,
        generated_at="2026-05-07T00:30:00+00:00",
        force_due=False,
    ).to_dict()

    assert runner["runner_status"] == "blocked_no_due_schedules"
    assert runner["active_schedule_count"] == 2
    assert runner["due_schedule_count"] == 0
    assert runner["queue_entry_count"] == 0
    assert runner["write_executed"] is False


def test_live_runner_write_guard_rejects_outside_record_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)

    with pytest.raises(ValueError, match="native-schedule-runs"):
        write_pulse_native_schedule_live_runner_records(
            vault,
            generated_at="2026-05-07T09:20:00+00:00",
            force_due=True,
            execute=True,
            output_path="07_LOGS/not-pulse-live-runner.json",
        )


def test_current_repo_live_runner_has_no_live_write_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    runner = build_pulse_native_schedule_live_runner(vault, force_due=True).to_dict()

    assert runner["runner_status"] == "blocked_no_supervised_active_schedules"
    assert runner["schedule_count"] >= 2
    assert runner["active_schedule_count"] == 0
    assert runner["write_executed"] is False
    assert runner["run_queue_write_executed"] is False
    assert runner["audit_event_write_executed"] is False
    assert runner["schedule_daemon_started"] is False
    assert runner["schedule_manifest_write_executed"] is False
    assert runner["schedule_activation_executed"] is False
    assert runner["agent_bus_task_write_allowed"] is False
    assert runner["runtime_dispatch_allowed"] is False
    assert runner["workflow_execution_allowed"] is False
    assert runner["provider_or_connector_call_allowed"] is False
    assert runner["external_scheduler_install_allowed"] is False
    assert runner["canonical_writeback_allowed"] is False
