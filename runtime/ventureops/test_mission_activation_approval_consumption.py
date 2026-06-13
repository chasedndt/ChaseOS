from __future__ import annotations

import json
import shutil
from pathlib import Path

import runtime.cli.main as cli
from runtime.ventureops.mission_activation_approval_consumption import (
    build_mission_activation_approval_artifact,
    consume_mission_activation_approval,
    load_mission_activation_approval_consumption_state,
    validate_mission_activation_approval_artifact,
)
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


def _copy_workspace(vault_root: Path) -> Path:
    mission_workspace = vault_root / "missions" / "dry-run"
    mission_workspace.mkdir(parents=True, exist_ok=True)
    source = _dry_run_workspace()
    for filename in _WORKSPACE_FIXTURE_FILES:
        shutil.copy2(source / filename, mission_workspace / filename)
    for filename in (
        "activation-approval-approved.json",
        "activation-approval-consumption.json",
        "mission-manifest-promotion-workflow-evolution-review-approved.json",
        "mission-manifest-promotion-workflow-evolution-review-consumption.json",
        "mission-agent-bus-enqueue-approval-approved.json",
        "mission-agent-bus-enqueue-consumption.json",
        "mission-runtime-claim-result-approval-approved.json",
        "mission-runtime-result.json",
        "mission-runtime-claim-result-consumption.json",
        "mission-activation-execution-approved.json",
        "mission-activation-execution-consumption.json",
    ):
        target = mission_workspace / filename
        if target.exists():
            target.unlink()
    manifest_path = mission_workspace / "mission-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "draft"
    manifest["version"] = "0.1-dry-run"
    manifest["updated"] = "2026-05-13"
    manifest.pop("activation_state", None)
    manifest["notes"] = "Test fixture reset before activation approval consumption."
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    boundary_path = mission_workspace / "run-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary.update(
        {
            "agent_bus_task_written": False,
            "agent_bus_task_claimed": False,
            "aor_dispatch_performed": False,
            "runtime_result_ingested": False,
            "mission_activation_performed": False,
            "workflow_mutation_performed": False,
            "workflow_evolution_applied": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "external_send_performed": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "protected_file_edit_performed": False,
            "credential_or_secret_read_performed": False,
            "canonical_promotion_performed": False,
        }
    )
    for key in list(boundary):
        if (
            key.startswith("agent_bus_enqueue_")
            or key.startswith("agent_bus_task_claim_result_")
            or key.startswith("mission_activation_")
            or key in {"agent_bus_task_status", "runtime_result_path", "aor_workflow_dispatched_from_claim_result"}
        ):
            boundary.pop(key)
    boundary["mission_activation_performed"] = False
    boundary_path.write_text(json.dumps(boundary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return mission_workspace


def test_mission_activation_approval_artifact_validates_for_exact_gate(tmp_path: Path) -> None:
    mission_workspace = _copy_workspace(tmp_path)

    artifact = build_mission_activation_approval_artifact(
        tmp_path,
        mission_workspace=mission_workspace,
        approval_id="approval-test",
        approved_by="operator",
        operator_approval_statement="Approve exact-once Mission Mode activation gate consumption only.",
    )
    validation = validate_mission_activation_approval_artifact(
        artifact,
        vault_root=tmp_path,
        mission_workspace=mission_workspace,
    )

    assert artifact["approval_status"] == "approved"
    assert artifact["approved_next_step"] == "mission_activation_gate_only"
    assert artifact["activation_authority_granted"] is True
    assert artifact["mission_activation_execution_authorized"] is False
    assert artifact["aor_dispatch_authorized"] is False
    assert artifact["agent_bus_task_write_authorized"] is False
    assert validation["ok"] is True


def test_mission_activation_approval_consumes_once_and_blocks_duplicate(tmp_path: Path) -> None:
    mission_workspace = _copy_workspace(tmp_path)

    first = consume_mission_activation_approval(
        tmp_path,
        mission_workspace=mission_workspace,
        approval_id="approval-once",
        approved_by="operator",
        operator_approval_statement="Approve exact-once Mission Mode activation gate consumption only.",
        write_approval=True,
        consume=True,
    )
    marker_path = tmp_path / first["consumption_marker_path"]
    marker_bytes = marker_path.read_bytes()

    duplicate = consume_mission_activation_approval(
        tmp_path,
        mission_workspace=mission_workspace,
        approval_id="approval-once",
        approved_by="operator",
        operator_approval_statement="Approve exact-once Mission Mode activation gate consumption only.",
        write_approval=True,
        consume=True,
    )

    assert first["ok"] is True
    assert first["approval_artifact_written"] is True
    assert first["approval_consumed"] is True
    assert first["exact_once_marker_written"] is True
    assert first["authority_boundary"]["mission_activation_performed"] is False
    assert "mission_activation_approval_missing" not in first["readiness_after_consumption"]["blockers"]
    assert "mission_manifest_is_draft" in first["readiness_after_consumption"]["blockers"]
    assert duplicate["ok"] is False
    assert duplicate["duplicate_blocked_before_activation"] is True
    assert duplicate["approval_consumed"] is False
    assert "exact_once_marker_already_present" in duplicate["blockers"]
    assert marker_path.read_bytes() == marker_bytes


def test_consumed_approval_clears_readiness_approval_blocker_only(tmp_path: Path) -> None:
    mission_workspace = _copy_workspace(tmp_path)

    consume_mission_activation_approval(
        tmp_path,
        mission_workspace=mission_workspace,
        approval_id="approval-readiness",
        approved_by="operator",
        operator_approval_statement="Approve exact-once Mission Mode activation gate consumption only.",
        write_approval=True,
        consume=True,
    )
    state = load_mission_activation_approval_consumption_state(
        tmp_path,
        mission_workspace=mission_workspace,
    )
    readiness = build_mission_activation_readiness(tmp_path, mission_workspace=mission_workspace)

    assert state["approval_consumed"] is True
    assert readiness["approved_for_activation"] is True
    assert readiness["approval_consumed"] is True
    assert readiness["activation_approval_artifact_present"] is True
    assert readiness["activation_approval_consumption_marker_present"] is True
    assert "mission_activation_approval_missing" not in readiness["blockers"]
    assert "mission_manifest_is_draft" in readiness["blockers"]
    assert "workflow_evolution_proposal_pending_review" in readiness["blockers"]
    assert readiness["ready_for_activation"] is False
    assert readiness["authority_boundary"]["agent_bus_task_written"] is False


def test_mission_activation_approval_consume_cli_writes_and_blocks_duplicate(tmp_path: Path, capsys) -> None:
    mission_workspace = _copy_workspace(tmp_path)
    argv = [
        "ventureops",
        "mission-activation-approval-consume",
        "--mission-workspace",
        str(mission_workspace),
        "--vault-root",
        str(tmp_path),
        "--approval-id",
        "approval-cli",
        "--approved-by",
        "operator",
        "--operator-approval-statement",
        "Approve exact-once Mission Mode activation gate consumption only.",
        "--write-approval",
        "--consume",
        "--json",
    ]

    first_exit = cli.main(argv)
    first_payload = json.loads(capsys.readouterr().out)["result"]
    second_exit = cli.main(argv)
    second_payload = json.loads(capsys.readouterr().out)["result"]

    assert first_exit == 0
    assert first_payload["ok"] is True
    assert first_payload["approval_artifact_written"] is True
    assert first_payload["approval_consumed"] is True
    assert first_payload["exact_once_marker_written"] is True
    assert second_exit == 0
    assert second_payload["ok"] is False
    assert "exact_once_marker_already_present" in second_payload["blockers"]
    assert second_payload["authority_boundary"]["external_send_performed"] is False
