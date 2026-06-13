from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.native_schedule_activation_gate import REQUIRED_EVIDENCE_SLOTS
from runtime.pulse.native_schedule_live_runner import write_pulse_native_schedule_live_runner_records
from runtime.pulse.native_schedule_runtime_dispatch_proof import (
    build_pulse_native_schedule_runtime_dispatch_proof,
    write_pulse_native_schedule_runtime_dispatch_proof,
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


def _write_workflow_registry(vault: Path, workflow_id: str, *, status: str = "active") -> None:
    root = vault / "runtime" / "workflows" / "registry"
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{workflow_id}.yaml").write_text(
        f"---\nid: {workflow_id}\nstatus: {status}\nowner: chaseos\n",
        encoding="utf-8",
    )


def _queue(vault: Path) -> None:
    write_pulse_native_schedule_live_runner_records(
        vault,
        generated_at="2026-05-07T09:10:00+00:00",
        force_due=True,
        execute=True,
    )


def test_runtime_dispatch_proof_blocks_without_queue_or_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    before = _snapshot(vault)

    proof = build_pulse_native_schedule_runtime_dispatch_proof(
        vault,
        generated_at="2026-05-07T09:30:00+00:00",
    ).to_dict()

    assert _snapshot(vault) == before
    assert proof["dispatch_status"] == "blocked_no_queued_native_schedule_runs"
    assert proof["queue_file_exists"] is False
    assert proof["queue_entry_count"] == 0
    assert proof["ready_dispatch_target_count"] == 0
    assert proof["write_executed"] is False
    assert proof["runtime_dispatch_allowed"] is False
    assert proof["runtime_dispatch_started"] is False
    assert proof["workflow_execution_allowed"] is False
    assert proof["workflow_execution_started"] is False
    assert proof["run_queue_status_write_executed"] is False
    assert proof["canonical_writeback_allowed"] is False


def test_runtime_dispatch_proof_blocks_queued_runs_without_workflow_registry(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)
    _queue(vault)

    proof = build_pulse_native_schedule_runtime_dispatch_proof(
        vault,
        generated_at="2026-05-07T09:35:00+00:00",
    ).to_dict()

    assert proof["dispatch_status"] == "blocked_pending_runs_not_dispatch_ready"
    assert proof["queue_file_exists"] is True
    assert proof["queue_entry_count"] == 2
    assert proof["pending_entry_count"] == 2
    assert proof["ready_dispatch_target_count"] == 0
    assert proof["missing_workflow_count"] == 2
    assert all("workflow_registry_missing" in target["blockers"] for target in proof["dispatch_targets"])
    assert proof["runtime_dispatch_started"] is False
    assert proof["workflow_execution_started"] is False


def test_runtime_dispatch_proof_ready_for_registered_queued_runs_without_dispatch(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)
    _write_workflow_registry(vault, "chaseos_pulse_daily_generate")
    _write_workflow_registry(vault, "hermes_runtime_pulse_generate")
    _queue(vault)
    before = _snapshot(vault)

    proof = build_pulse_native_schedule_runtime_dispatch_proof(
        vault,
        generated_at="2026-05-07T09:40:00+00:00",
    ).to_dict()

    assert _snapshot(vault) == before
    assert proof["dispatch_status"] == "runtime_dispatch_proof_ready"
    assert proof["dispatch_target_count"] == 2
    assert proof["ready_dispatch_target_count"] == 2
    assert proof["blocked_dispatch_target_count"] == 0
    assert proof["proof_events"][0]["proof_artifact_written"] is False
    assert all(target["dispatch_ready"] is True for target in proof["dispatch_targets"])
    assert all(target["command_preview"].startswith("chaseos run ") for target in proof["dispatch_targets"])
    assert all(target["runtime_dispatch_allowed"] is False for target in proof["dispatch_targets"])
    assert all(target["workflow_execution_allowed"] is False for target in proof["dispatch_targets"])
    assert proof["execute_dispatch_action_exposed"] is False
    assert proof["runtime_dispatch_started"] is False
    assert proof["workflow_execution_started"] is False
    assert proof["run_queue_status_write_executed"] is False


def test_runtime_dispatch_proof_write_writes_artifact_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)
    _write_workflow_registry(vault, "chaseos_pulse_daily_generate")
    _write_workflow_registry(vault, "hermes_runtime_pulse_generate")
    _queue(vault)

    proof = write_pulse_native_schedule_runtime_dispatch_proof(
        vault,
        generated_at="2026-05-07T09:45:00+00:00",
    ).to_dict()

    assert proof["dispatch_status"] == "runtime_dispatch_proof_written"
    assert proof["write_executed"] is True
    assert proof["proof_artifact_write_executed"] is True
    assert len(proof["writes"]) == 1
    assert proof["writes"][0].startswith("07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/")
    assert proof["writes"][0].endswith(".json")
    written = vault / proof["writes"][0]
    assert written.is_file()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["dispatch_status"] == "runtime_dispatch_proof_written"
    assert all(event["proof_artifact_written"] is True for event in payload["proof_events"])
    assert payload["runtime_dispatch_started"] is False
    assert payload["workflow_execution_started"] is False
    assert payload["run_queue_status_write_executed"] is False


def test_runtime_dispatch_proof_blocks_non_active_workflow_registry(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)
    _write_workflow_registry(vault, "chaseos_pulse_daily_generate", status="draft")
    _write_workflow_registry(vault, "hermes_runtime_pulse_generate")
    _queue(vault)

    proof = build_pulse_native_schedule_runtime_dispatch_proof(
        vault,
        generated_at="2026-05-07T09:50:00+00:00",
    ).to_dict()

    assert proof["dispatch_status"] == "runtime_dispatch_proof_ready"
    blocked = [target for target in proof["dispatch_targets"] if not target["dispatch_ready"]]
    assert len(blocked) == 1
    assert blocked[0]["workflow_registry_status"] == "draft"
    assert "workflow_registry_not_active" in blocked[0]["blockers"]


def test_runtime_dispatch_proof_write_guard_rejects_outside_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed(vault)
    _activate(vault)
    _write_workflow_registry(vault, "chaseos_pulse_daily_generate")
    _write_workflow_registry(vault, "hermes_runtime_pulse_generate")
    _queue(vault)

    with pytest.raises(ValueError, match="native-schedule-runtime-dispatch-proof"):
        write_pulse_native_schedule_runtime_dispatch_proof(
            vault,
            generated_at="2026-05-07T09:55:00+00:00",
            output_path="07_LOGS/not-dispatch-proof.json",
        )


def test_current_repo_runtime_dispatch_proof_has_no_dispatch_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    proof = build_pulse_native_schedule_runtime_dispatch_proof(vault).to_dict()

    assert proof["dispatch_status"] == "blocked_no_queued_native_schedule_runs"
    assert proof["queue_entry_count"] == 0
    assert proof["ready_dispatch_target_count"] == 0
    assert proof["write_executed"] is False
    assert proof["execute_dispatch_action_exposed"] is False
    assert proof["schedule_daemon_started"] is False
    assert proof["run_queue_status_write_executed"] is False
    assert proof["runtime_dispatch_allowed"] is False
    assert proof["runtime_dispatch_started"] is False
    assert proof["workflow_execution_allowed"] is False
    assert proof["workflow_execution_started"] is False
    assert proof["provider_or_connector_call_allowed"] is False
    assert proof["canonical_writeback_allowed"] is False
