from __future__ import annotations

import json
from pathlib import Path

import runtime.cli.main as cli
from runtime.ventureops.mission_activation_approval_packet import (
    build_mission_activation_approval_packet,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _dry_run_workspace() -> Path:
    return (
        _repo_root()
        / "07_LOGS"
        / "VentureOps-Missions"
        / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
    )


def test_mission_activation_approval_packet_reports_ready_after_consumed_review_gates() -> None:
    result = build_mission_activation_approval_packet(_repo_root(), mission_workspace=_dry_run_workspace())
    packet = result["packet"]

    assert result["ok"] is True
    assert result["ready_for_operator_review"] is True
    assert packet["operator_approved"] is True
    assert packet["approval_consumed"] is True
    assert packet["manifest_promotion_review_consumed"] is True
    assert packet["agent_bus_mission_enqueue_consumed"] is True
    assert packet["agent_bus_mission_task_recipient"] == "Codex"
    assert packet["agent_bus_task_written"] is True
    assert packet["workflow_evolution_applied"] is False
    assert packet["readiness_blockers"] == []
    assert "mission_activation_approval_missing" not in packet["readiness_blockers"]
    assert "mission_manifest_is_draft" not in packet["readiness_blockers"]
    assert "workflow_evolution_proposal_pending_review" not in packet["readiness_blockers"]
    assert packet["approval_packet_template"]["activation_authority_granted"] is False
    assert packet["aor_handler_design"]["status"] == "IMPLEMENTED_LOCAL_DRY_REVIEW"
    assert packet["agent_bus_contract_design"]["status"] == "IMPLEMENTED_PREVIEW_CONTRACT"
    assert packet["agent_bus_contract_design"]["live_enqueue_implemented"] is True
    assert packet["authority_boundary"]["approval_packet_draft_only"] is False
    assert packet["authority_boundary"]["operator_approval_consumed"] is True

    if packet["mission_active"]:
        assert result["packet_status"] == "mission_active_local"
        assert result["ready_for_activation"] is False
        assert result["ready_for_aor_dispatch"] is False
        assert packet["activation_performed"] is True
        assert packet["aor_dispatch_performed"] is True
        assert packet["agent_bus_mission_task_claimed"] is True
        assert packet["next_required_action"] == (
            "mission is active locally; external/client action requires separate operator-approved evidence"
        )
        assert "final hardening is complete for local Mission Mode gates" in packet["safe_followup_plan"]
    elif packet["runtime_claim_result_consumed"]:
        assert result["packet_status"] == "runtime_claim_result_ingested_pending_activation_gate"
        assert result["ready_for_activation"] is True
        assert result["ready_for_aor_dispatch"] is True
        assert packet["activation_performed"] is False
        assert packet["aor_dispatch_performed"] is True
        assert packet["agent_bus_mission_task_claimed"] is True
    else:
        assert result["packet_status"] == "agent_bus_mission_task_enqueued_pending_runtime_claim_or_result"
        assert result["ready_for_activation"] is True
        assert result["ready_for_aor_dispatch"] is True
        assert packet["activation_performed"] is False
        assert packet["aor_dispatch_performed"] is False
        assert packet["agent_bus_mission_task_claimed"] is False


def test_mission_activation_approval_packet_blocks_when_workspace_missing(tmp_path: Path) -> None:
    missing_workspace = tmp_path / "missing-dry-run"

    result = build_mission_activation_approval_packet(_repo_root(), mission_workspace=missing_workspace)
    packet = result["packet"]

    assert result["ok"] is True
    assert result["packet_status"] == "blocked_missing_valid_dry_run_workspace"
    assert result["ready_for_operator_review"] is False
    assert packet["artifact_validation_ok"] is False
    assert "mission_dry_run_workspace_missing" in packet["readiness_blockers"]
    assert packet["ready_for_activation"] is False
    assert packet["ready_for_aor_dispatch"] is False


def test_mission_activation_approval_packet_cli_json_is_no_write_by_default(capsys) -> None:
    exit_code = cli.main(
        [
            "ventureops",
            "mission-activation-approval-packet",
            "--mission-workspace",
            str(_dry_run_workspace()),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    packet = result["packet"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "ventureops.mission-activation-approval-packet"
    assert result["packet_written"] is False
    assert result["ready_for_activation"] is (not packet["mission_active"])
    assert packet["aor_handler_design"]["activation_performed"] is False
    assert packet["agent_bus_contract_design"]["agent_bus_task_written"] is False


def test_mission_activation_approval_packet_cli_write_packet_is_create_only(tmp_path: Path, capsys) -> None:
    vault_root = tmp_path / "vault"
    mission_workspace = vault_root / "missing-dry-run"
    packet_path = vault_root / "packets" / "activation-packet.json"
    argv = [
        "ventureops",
        "mission-activation-approval-packet",
        "--mission-workspace",
        str(mission_workspace),
        "--vault-root",
        str(vault_root),
        "--write-packet",
        "--output",
        str(packet_path),
        "--json",
    ]

    first_exit = cli.main(argv)
    first_payload = json.loads(capsys.readouterr().out)
    second_exit = cli.main(argv)
    second_payload = json.loads(capsys.readouterr().out)

    assert first_exit == 0
    assert first_payload["result"]["packet_written"] is True
    assert packet_path.exists()
    assert second_exit == 0
    assert second_payload["result"]["packet_written"] is False
    assert second_payload["result"]["packet_write_blocked"] is True
    assert second_payload["result"]["authority_boundary"]["mission_activation_performed"] is False
