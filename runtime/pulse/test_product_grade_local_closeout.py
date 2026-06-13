from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.product_grade_local_closeout import (
    BLOCKED_EFFECTS,
    CLOSEOUT_ARTIFACT_ROOT,
    EXTERNAL_LANES,
    STATUS_LOCAL_V1_READY,
    build_pulse_product_grade_local_closeout,
)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_product_grade_local_closeout_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    closeout = build_pulse_product_grade_local_closeout(
        vault,
        generated_at="2026-05-04T00:50:00+01:00",
    )

    assert _snapshot(vault) == before
    assert closeout.local_v1_product_grade_ready is False
    assert closeout.current_v1_local_lane_complete is False
    assert closeout.full_product_grade_complete is False
    assert closeout.closeout_artifact_written is False
    assert closeout.writes_audit_artifact is False
    assert closeout.read_only is True
    assert closeout.provider_or_connector_call_allowed is False
    assert closeout.schedule_activation_allowed is False
    assert closeout.canonical_writeback_allowed is False
    assert closeout.rd_workbook_update_allowed is False
    assert set(closeout.blocked_effects) == set(BLOCKED_EFFECTS)


def test_product_grade_local_closeout_current_repo_closes_local_v1_only() -> None:
    vault = Path(__file__).resolve().parents[2]

    closeout = build_pulse_product_grade_local_closeout(vault)
    payload = closeout.to_dict()

    assert payload["closeout_status"] == STATUS_LOCAL_V1_READY
    assert payload["local_v1_product_grade_ready"] is True
    assert payload["current_v1_local_lane_complete"] is True
    assert payload["full_product_grade_complete"] is False
    assert payload["next_recommended_pass"] == "pulse-explicit-next-feature-lane-selection"
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["source_content_read"] is False
    assert payload["unrestricted_web_scan_allowed"] is False
    assert payload["browser_history_ingest_allowed"] is False
    assert payload["schedule_activation_allowed"] is False
    assert payload["approval_execution_allowed"] is False
    assert payload["agent_bus_task_write_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False
    assert payload["rd_workbook_update_allowed"] is False

    deferred = {lane["lane_id"]: lane for lane in payload["deferred_external_lanes"]}
    assert set(EXTERNAL_LANES) == set(deferred)
    assert "bounded_connector_runner" in deferred["live_connector_source_scanner_execution"]["required_to_unblock"]
    assert payload["evidence"]["rd_workbook_final_sync_complete"] is True
    assert payload["evidence"]["rd_workbook_final_sync_doc"] == "06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Final-Sync.md"


def test_product_grade_local_closeout_write_artifact_is_scoped(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    closeout = build_pulse_product_grade_local_closeout(
        vault,
        write_closeout=True,
        generated_at="2026-05-04T00:55:00+01:00",
    )

    assert closeout.closeout_artifact_written is True
    assert closeout.writes_audit_artifact is True
    assert closeout.closeout_artifact_path
    artifact = vault / closeout.closeout_artifact_path
    assert CLOSEOUT_ARTIFACT_ROOT.as_posix() in closeout.closeout_artifact_path
    assert artifact.exists()

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["closeout_artifact_written"] is True
    assert payload["provider_or_connector_call_allowed"] is False
    assert payload["canonical_writeback_allowed"] is False


def test_product_grade_local_closeout_rejects_output_outside_closeout_root(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError, match="product closeout artifacts"):
        build_pulse_product_grade_local_closeout(
            vault,
            write_closeout=True,
            output_path=vault / "07_LOGS" / "Pulse-Decks" / "bad.json",
        )
