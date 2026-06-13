from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path

import runtime.cli.main as cli
from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _dry_run_workspace() -> Path:
    return (
        _repo_root()
        / "07_LOGS"
        / "VentureOps-Missions"
        / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
    )


_WORKSPACE_FIXTURE_FILES = (
    "activation-approval-packet-draft.json",
    "artifact-index.json",
    "domain-goal-profile.json",
    "mission-manifest.json",
    "mission-review.json",
    "mission-state-ledger.json",
    "proof-card.json",
    "README.md",
    "run-boundary.json",
    "scorecard.json",
    "site-profile-candidate.json",
    "sub-agent-plan.json",
    "workflow-evolution-proposal.json",
)


def _copy_workspace_fixture(target: Path) -> None:
    source = _dry_run_workspace()
    target.mkdir(parents=True, exist_ok=True)
    for filename in _WORKSPACE_FIXTURE_FILES:
        shutil.copy2(source / filename, target / filename)


def test_mission_activation_readiness_and_enqueue_gate_import_without_cycle() -> None:
    readiness = importlib.import_module("runtime.ventureops.mission_activation_readiness")
    enqueue_gate = importlib.import_module("runtime.ventureops.mission_agent_bus_enqueue_gate")

    assert hasattr(readiness, "build_mission_activation_readiness")
    assert hasattr(enqueue_gate, "load_mission_agent_bus_enqueue_state")


def test_mvp_current_state_cli_survives_ventureops_import_graph(capsys) -> None:
    exit_code = cli.main(["mvp", "current-state", "--json"])

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.current-state"
    assert result["surface"] == "chaseos_mvp_current_state_map"
    assert result["pass_status_count"] == 10
    assert result["safe_to_call_update_goal_complete"] is True  # all 10 MVP checklist items now covered


def test_mission_activation_readiness_ready_after_consumed_review_gates() -> None:
    result = build_mission_activation_readiness(_repo_root(), mission_workspace=_dry_run_workspace())

    assert result["ok"] is True
    assert result["artifact_validation_ok"] is True
    assert result["approved_for_activation"] is True
    assert result["approval_consumed"] is True
    assert result["effective_mission_manifest_status"] in {"approved", "active"}
    assert result["effective_workflow_evolution_status"] == "reviewed_deferred_no_apply"
    assert result["activation_approval_artifact_present"] is True
    assert result["activation_approval_consumption_marker_present"] is True
    assert result["manifest_promotion_review_artifact_present"] is True
    assert result["manifest_promotion_review_marker_present"] is True
    assert result["manifest_promotion_review_consumed"] is True
    assert result["mission_manifest_promoted_for_activation"] is True
    assert result["workflow_evolution_reviewed_for_activation"] is True
    assert result["agent_bus_mission_enqueue_artifact_present"] is True
    assert result["agent_bus_mission_enqueue_artifact_valid"] is True
    assert result["agent_bus_mission_enqueue_marker_present"] is True
    assert result["agent_bus_mission_enqueue_marker_valid"] is True
    assert result["agent_bus_mission_enqueue_consumed"] is True
    assert result["agent_bus_mission_task_written"] is True
    assert result["agent_bus_mission_task_recipient"] == "Codex"
    assert result["agent_bus_mission_task_priority"] == "normal"
    assert result["base_aor_workflow_manifest_present"] is True
    assert result["base_aor_workflow_handler_present"] is True
    assert result["workflow_alias_declared"] is True
    assert result["aor_mission_handler_present"] is True
    assert result["agent_bus_mission_dispatch_contract_present"] is True
    assert result["blockers"] == []
    assert "mission_manifest_is_draft" not in result["blockers"]
    assert "workflow_evolution_proposal_pending_review" not in result["blockers"]
    assert "mission_activation_approval_missing" not in result["blockers"]
    assert "run_boundary_flag_not_false:agent_bus_task_written" not in result["blockers"]
    assert "aor_mission_handler_missing" not in result["blockers"]
    assert "agent_bus_mission_dispatch_contract_missing" not in result["blockers"]
    assert result["authority_boundary"]["agent_bus_task_written"] is True
    assert result["authority_boundary"]["workflow_evolution_applied"] is False

    if result["mission_active"]:
        assert result["readiness_status"] == "mission_active_local"
        assert result["ready_for_activation"] is False
        assert result["ready_for_aor_dispatch"] is False
        assert result["runtime_claim_result_consumed"] is True
        assert result["runtime_task_closed"] is True
        assert result["mission_result_ingested"] is True
        assert result["mission_activation_gate_consumed"] is True
        assert result["authority_boundary"]["mission_activation_performed"] is True
        assert result["authority_boundary"]["aor_dispatch_performed"] is True
    elif result["runtime_claim_result_consumed"]:
        assert result["readiness_status"] == "ready_for_activation"
        assert result["ready_for_activation"] is True
        assert result["ready_for_aor_dispatch"] is True
        assert result["agent_bus_mission_task_claimed"] is True
        assert result["agent_bus_mission_workflow_dispatched"] is True
        assert result["runtime_task_closed"] is True
        assert result["mission_result_ingested"] is True
        assert result["authority_boundary"]["mission_activation_performed"] is False
        assert result["authority_boundary"]["aor_dispatch_performed"] is True
    else:
        assert result["readiness_status"] == "ready_for_activation"
        assert result["ready_for_activation"] is True
        assert result["ready_for_aor_dispatch"] is True
        assert result["agent_bus_mission_task_claimed"] is False
        assert result["agent_bus_mission_workflow_dispatched"] is False
        assert result["authority_boundary"]["mission_activation_performed"] is False
        assert result["authority_boundary"]["aor_dispatch_performed"] is False


def test_mission_activation_readiness_reports_boundary_drift(tmp_path: Path) -> None:
    target = tmp_path / "dry-run"
    _copy_workspace_fixture(target)
    boundary_path = target / "run-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["provider_call_performed"] = True
    boundary["credential_or_secret_read_performed"] = True
    boundary_path.write_text(json.dumps(boundary, indent=2) + "\n", encoding="utf-8")

    result = build_mission_activation_readiness(_repo_root(), mission_workspace=target)

    assert result["artifact_validation_ok"] is False
    assert "mission_dry_run_artifact_validation_failed" in result["blockers"]
    assert "run_boundary_flag_not_false:provider_call_performed" in result["blockers"]
    assert "run_boundary_flag_not_false:credential_or_secret_read_performed" in result["blockers"]
    assert any("provider_call_performed must be false" in error for error in result["artifact_validation_errors"])
    assert any("credential_or_secret_read_performed must be false" in error for error in result["artifact_validation_errors"])


def test_mission_activation_readiness_cli_json_is_read_only(capsys) -> None:
    exit_code = cli.main(
        [
            "ventureops",
            "mission-activation-readiness",
            "--mission-workspace",
            str(_dry_run_workspace()),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "ventureops.mission-activation-readiness"
    assert result["readiness_status"] in {"ready_for_activation", "mission_active_local"}
    if result["mission_active"]:
        assert result["ready_for_activation"] is False
        assert result["ready_for_aor_dispatch"] is False
        assert result["next_required_action"] == (
            "mission is active locally; external/client action requires separate operator-approved evidence"
        )
        assert "final hardening is complete for local Mission Mode gates" in result["safe_followup_plan"]
    else:
        assert result["ready_for_activation"] is True
        assert result["ready_for_aor_dispatch"] is True
    assert result["authority_boundary"]["external_send_performed"] is False
    assert result["authority_boundary"]["credential_or_secret_read_performed"] is False
    assert result["report_written"] is False


def test_mission_activation_readiness_cli_write_report_is_create_only(tmp_path: Path, capsys) -> None:
    vault_root = tmp_path / "vault"
    mission_workspace = vault_root / "missions" / "dry-run"
    _copy_workspace_fixture(mission_workspace)
    report_path = vault_root / "reports" / "mission-readiness.json"
    first_exit = cli.main(
        [
            "ventureops",
            "mission-activation-readiness",
            "--mission-workspace",
            str(mission_workspace),
            "--vault-root",
            str(vault_root),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ]
    )
    first_payload = json.loads(capsys.readouterr().out)

    second_exit = cli.main(
        [
            "ventureops",
            "mission-activation-readiness",
            "--mission-workspace",
            str(mission_workspace),
            "--vault-root",
            str(vault_root),
            "--write-report",
            "--report-path",
            str(report_path),
            "--json",
        ]
    )
    second_payload = json.loads(capsys.readouterr().out)

    assert first_exit == 0
    assert first_payload["result"]["report_written"] is True
    assert report_path.exists()
    assert second_exit == 0
    assert second_payload["result"]["report_written"] is False
    assert second_payload["result"]["report_write_blocked"] is True
    assert second_payload["result"]["authority_boundary"]["external_send_performed"] is False
