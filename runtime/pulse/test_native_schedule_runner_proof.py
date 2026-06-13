from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.native_schedule_runner_proof import (
    build_pulse_native_schedule_runner_proof,
)


def _write_manifest(vault: Path, schedule_id: str, *, external: bool = False) -> None:
    target = vault / "runtime" / "schedules" / "manifests" / f"{schedule_id}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    audience = "agent" if schedule_id == "hermes_runtime_pulse" else "user"
    runtime_target = "\n  runtime_target: hermes" if schedule_id == "hermes_runtime_pulse" else ""
    target.write_text(
        f"""manifest_id: {schedule_id}
schedule_id: {schedule_id}
feature: chaseos_pulse
owner: chaseos
status: scaffolded
enabled: false
activation_state: planned
cadence:
  type: daily
  local_time: "07:15"
  timezone: Europe/London
execution:
  schedule_owner: chaseos{runtime_target}
  executor_adapter: native_chaseos_scheduler_planned
  workflow_id: {schedule_id}_generate
  openclaw_cron_owner: false
  windows_task_scheduler_owner: false
delivery:
  target: local_pulse_deck_archive
  output_root: "07_LOGS/Pulse-Decks/users/"
missed_run_policy:
  if_machine_off: catch_up_once
  if_server_down: queue_pending
  if_runtime_unavailable: defer_to_review
  if_approval_timeout: create_review_card
deck:
  audience: {audience}
  canonical_writeback_enabled: false
source_policy:
  external_connectors_enabled: {str(external).lower()}
  unrestricted_browsing_enabled: false
audit_identity:
  schedule_id: {schedule_id}
  trigger_source: native_chaseos_schedule_intent
  owner: chaseos
  executor_is_adapter_only: true
""",
        encoding="utf-8",
    )


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_runner_proof_dry_run_reads_manifests_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_manifest(vault, "chaseos_pulse_daily")
    _write_manifest(vault, "hermes_runtime_pulse")
    before = _snapshot(vault)

    proof = build_pulse_native_schedule_runner_proof(
        vault,
        generated_at="2026-05-03T18:30:00+00:00",
        simulate_missed_run=True,
    )
    payload = proof.to_dict()

    assert _snapshot(vault) == before
    assert payload["runner_status"] == "runner_ready_activation_blocked"
    assert payload["schedule_count"] == 2
    assert payload["enabled_schedule_count"] == 0
    assert payload["simulated_missed_run"] is True
    assert payload["write_executed"] is False
    assert payload["schedule_daemon_started"] is False
    assert payload["schedule_manifest_written"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["run_queue_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert {item["catchup_decision"] for item in payload["schedules"]} == {"would_create_review_card"}


def test_runner_proof_write_stays_under_pulse_logs(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_manifest(vault, "chaseos_pulse_daily")
    _write_manifest(vault, "hermes_runtime_pulse")

    proof = build_pulse_native_schedule_runner_proof(
        vault,
        generated_at="2026-05-03T18:35:00+00:00",
        simulate_missed_run=True,
        write=True,
    )
    payload = proof.to_dict()

    assert payload["write_executed"] is True
    assert payload["writes_artifacts"] is True
    assert len(payload["writes"]) == 1
    rel_path = payload["writes"][0]
    assert rel_path.startswith("07_LOGS/Pulse-Decks/native-schedule-runner-proof/")
    written = json.loads((vault / rel_path).read_text(encoding="utf-8"))
    assert written["schedule_daemon_started"] is False
    assert written["schedule_activation_allowed"] is False
    assert written["run_queue_written"] is False


def test_runner_proof_fails_closed_if_external_connectors_enabled(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_manifest(vault, "chaseos_pulse_daily", external=True)
    _write_manifest(vault, "hermes_runtime_pulse")

    with pytest.raises(ValueError, match="external sources disabled"):
        build_pulse_native_schedule_runner_proof(vault)


def test_current_repo_runner_proof_has_no_execution_authority() -> None:
    vault = Path(__file__).resolve().parents[2]

    proof = build_pulse_native_schedule_runner_proof(vault, simulate_missed_run=True)
    payload = proof.to_dict()

    assert payload["runner_status"] == "runner_ready_activation_blocked"
    assert payload["schedule_count"] >= 2
    assert payload["schedule_daemon_started"] is False
    assert payload["schedule_manifest_written"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["run_queue_written"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["runtime_dispatch_allowed"] is False
    assert payload["workflow_execution_allowed"] is False
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
