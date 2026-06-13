from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from runtime.pulse.native_schedule_activation_proof import (
    NATIVE_SCHEDULE_ACTIVATION_PROOF_PATH,
    PULSE_NATIVE_SCHEDULE_MANIFEST_PATH,
    build_native_schedule_activation_catchup_proof,
)

_TMP_ROOT = Path("runtime/pulse/_tmp_native_schedule_activation_proof")


def _make_vault() -> Path:
    root = (_TMP_ROOT / f"vault-{uuid4().hex}").resolve()
    (root / "runtime" / "schedules" / "manifests").mkdir(parents=True, exist_ok=True)
    (root / "00_HOME").mkdir(parents=True, exist_ok=True)
    (root / "07_LOGS" / "Daily").mkdir(parents=True, exist_ok=True)
    (root / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)
    (root / "07_LOGS" / "Build-Logs").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "memory").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "source_intelligence").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "workflows" / "registry").mkdir(parents=True, exist_ok=True)
    (root / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    (root / "07_LOGS" / "Daily" / "2026-05-02.md").write_text("# Daily\n", encoding="utf-8")
    (root / PULSE_NATIVE_SCHEDULE_MANIFEST_PATH).write_text(
        """manifest_id: chaseos_pulse_daily
schedule_id: chaseos_pulse_daily
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
  workflow_id: chaseos_pulse_generate
delivery:
  output_root: "07_LOGS/Pulse-Decks/users/"
missed_run_policy:
  if_machine_off: catch_up_once
  if_server_down: queue_pending
deck:
  audience: user
  canonical_writeback_enabled: false
source_policy:
  external_connectors_enabled: false
  unrestricted_browsing_enabled: false
audit_identity:
  schedule_id: chaseos_pulse_daily
  trigger_source: native_chaseos_schedule_intent
""",
        encoding="utf-8",
    )
    return root


def _cleanup(root: Path) -> None:
    base = _TMP_ROOT.resolve()
    target = root.resolve()
    if target == base or base in target.parents:
        shutil.rmtree(target, ignore_errors=True)


def test_dry_run_previews_native_schedule_catchup_without_writes() -> None:
    vault = _make_vault()
    try:
        result = build_native_schedule_activation_catchup_proof(
            vault,
            generated_at="2026-05-02T12:45:00+01:00",
            live=False,
        )

        assert result.proof_status == "ready"
        assert result.dry_run is True
        assert result.schedule_id == "chaseos_pulse_daily"
        assert result.catchup_policy == "catch_up_once"
        assert result.catchup_deck_written is False
        assert result.writes == []
        assert result.schedule_manifest_written is False
        assert result.schedule_activation_allowed is False
        assert result.provider_or_connector_call_allowed is False
        assert not (vault / NATIVE_SCHEDULE_ACTIVATION_PROOF_PATH).exists()
    finally:
        _cleanup(vault)


def test_live_writes_catchup_deck_and_proof_without_daemon_activation() -> None:
    vault = _make_vault()
    try:
        result = build_native_schedule_activation_catchup_proof(
            vault,
            generated_at="2026-05-02T12:45:00+01:00",
            live=True,
        )

        assert result.proof_status == "complete"
        assert result.dry_run is False
        assert result.catchup_deck_written is True
        assert result.proof_written is True
        assert result.schedule_manifest_written is False
        assert result.schedule_daemon_started is False
        assert result.schedule_activation_allowed is False
        assert result.canonical_writeback_allowed is False
        assert result.provider_or_connector_call_allowed is False
        assert result.schedule_manifest_enabled is False
        assert result.deck_artifact is not None
        assert result.deck_artifact["json_path"].endswith("2026-05-02-native-schedule-catchup-pulse.json")
        assert (vault / result.deck_artifact["json_path"]).exists()
        assert (vault / result.deck_artifact["markdown_path"]).exists()
        proof_path = vault / NATIVE_SCHEDULE_ACTIVATION_PROOF_PATH
        assert proof_path.exists()
        proof_text = proof_path.read_text(encoding="utf-8")
        assert "Status: PASS" in proof_text
        assert "chaseos_pulse_daily" in proof_text
        assert "No schedule daemon was started" in proof_text
    finally:
        _cleanup(vault)
