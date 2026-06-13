from __future__ import annotations

import json
import shutil
from pathlib import Path

import runtime.cli.main as cli
from runtime.ventureops.mission_activation_approval_consumption import consume_mission_activation_approval
from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness
from runtime.ventureops.mission_manifest_promotion_review_gate import (
    REVIEW_ARTIFACT_FILENAME,
    REVIEW_MARKER_FILENAME,
    build_mission_manifest_promotion_review_artifact,
    consume_mission_manifest_promotion_review_gate,
    load_mission_manifest_promotion_review_state,
    validate_mission_manifest_promotion_review_artifact,
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
        REVIEW_ARTIFACT_FILENAME,
        REVIEW_MARKER_FILENAME,
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
    manifest["notes"] = "Test fixture reset before manifest-promotion review gate."
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


def _seed_activation(vault_root: Path, mission_workspace: Path) -> None:
    result = consume_mission_activation_approval(
        vault_root,
        mission_workspace=mission_workspace,
        approval_id="activation-before-review",
        approved_by="operator",
        operator_approval_statement="Approve exact-once Mission Mode activation gate consumption only.",
        write_approval=True,
        consume=True,
    )
    assert result["ok"] is True


def _seed_runtime_contracts(vault_root: Path) -> None:
    mission_handler = vault_root / "runtime" / "workflows" / "missions" / "mission_chase_ai_runtime_governance_kit.py"
    mission_handler.parent.mkdir(parents=True, exist_ok=True)
    mission_handler.write_text("# fixture mission handler\n", encoding="utf-8")
    agent_bus_schema = vault_root / "runtime" / "agent_bus" / "schemas" / "mission_task_packet.schema.json"
    agent_bus_schema.parent.mkdir(parents=True, exist_ok=True)
    agent_bus_schema.write_text("{}\n", encoding="utf-8")
    registry = vault_root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        "workflows:\n"
        "  - workflow_id: agent_runtime_governance_audit\n"
        "  - workflow_id: ventureops_ai_runtime_security_audit\n",
        encoding="utf-8",
    )


def test_manifest_promotion_review_artifact_validates_after_activation_approval(tmp_path: Path) -> None:
    mission_workspace = _copy_workspace(tmp_path)
    _seed_activation(tmp_path, mission_workspace)

    artifact = build_mission_manifest_promotion_review_artifact(
        tmp_path,
        mission_workspace=mission_workspace,
        review_id="review-test",
        approved_by="operator",
        operator_approval_statement="Approve manifest promotion readiness and review workflow evolution without applying it.",
    )
    validation = validate_mission_manifest_promotion_review_artifact(
        artifact,
        vault_root=tmp_path,
        mission_workspace=mission_workspace,
    )

    assert artifact["approval_status"] == "approved"
    assert artifact["approved_next_step"] == "activation_readiness_gate_only"
    assert artifact["manifest_promotion_decision"] == "approved_for_activation_readiness_only"
    assert artifact["workflow_evolution_review_decision"] == "reviewed_deferred_no_apply"
    assert artifact["mission_manifest_file_mutation_authorized"] is False
    assert artifact["workflow_evolution_apply_authorized"] is False
    assert validation["ok"] is True


def test_manifest_promotion_review_consumes_once_and_clears_readiness_blockers(tmp_path: Path) -> None:
    mission_workspace = _copy_workspace(tmp_path)
    _seed_activation(tmp_path, mission_workspace)
    _seed_runtime_contracts(tmp_path)

    first = consume_mission_manifest_promotion_review_gate(
        tmp_path,
        mission_workspace=mission_workspace,
        review_id="review-once",
        approved_by="operator",
        operator_approval_statement="Approve manifest promotion readiness and review workflow evolution without applying it.",
        write_review=True,
        consume=True,
    )
    marker_path = tmp_path / first["review_marker_path"]
    marker_bytes = marker_path.read_bytes()

    duplicate = consume_mission_manifest_promotion_review_gate(
        tmp_path,
        mission_workspace=mission_workspace,
        review_id="review-once",
        approved_by="operator",
        operator_approval_statement="Approve manifest promotion readiness and review workflow evolution without applying it.",
        write_review=True,
        consume=True,
    )
    readiness = build_mission_activation_readiness(tmp_path, mission_workspace=mission_workspace)

    assert first["ok"] is True
    assert first["review_artifact_written"] is True
    assert first["review_consumed"] is True
    assert first["exact_once_marker_written"] is True
    assert first["authority_boundary"]["mission_manifest_file_mutation_performed"] is False
    assert "mission_manifest_is_draft" not in readiness["blockers"]
    assert "workflow_evolution_proposal_pending_review" not in readiness["blockers"]
    assert readiness["manifest_promotion_review_consumed"] is True
    assert readiness["ready_for_activation"] is True
    assert readiness["ready_for_aor_dispatch"] is True
    assert duplicate["ok"] is False
    assert duplicate["duplicate_blocked_before_activation"] is True
    assert "exact_once_marker_already_present" in duplicate["blockers"]
    assert marker_path.read_bytes() == marker_bytes


def test_manifest_promotion_review_blocks_without_consumed_activation_approval(tmp_path: Path) -> None:
    mission_workspace = _copy_workspace(tmp_path)

    result = consume_mission_manifest_promotion_review_gate(
        tmp_path,
        mission_workspace=mission_workspace,
        review_id="review-without-activation",
        approved_by="operator",
        operator_approval_statement="Approve manifest promotion readiness and review workflow evolution without applying it.",
        write_review=True,
        consume=True,
    )
    state = load_mission_manifest_promotion_review_state(tmp_path, mission_workspace=mission_workspace)

    assert result["ok"] is False
    assert "activation approval must be consumed before manifest promotion review" in result["blockers"]
    assert result["review_consumed"] is False
    assert state["review_consumed"] is False


def test_mission_manifest_promotion_review_gate_cli_writes_and_blocks_duplicate(tmp_path: Path, capsys) -> None:
    mission_workspace = _copy_workspace(tmp_path)
    _seed_activation(tmp_path, mission_workspace)
    argv = [
        "ventureops",
        "mission-manifest-promotion-review-gate",
        "--mission-workspace",
        str(mission_workspace),
        "--vault-root",
        str(tmp_path),
        "--review-id",
        "review-cli",
        "--approved-by",
        "operator",
        "--operator-approval-statement",
        "Approve manifest promotion readiness and review workflow evolution without applying it.",
        "--write-review",
        "--consume",
        "--json",
    ]

    first_exit = cli.main(argv)
    first_payload = json.loads(capsys.readouterr().out)["result"]
    second_exit = cli.main(argv)
    second_payload = json.loads(capsys.readouterr().out)["result"]

    assert first_exit == 0
    assert first_payload["ok"] is True
    assert first_payload["review_artifact_written"] is True
    assert first_payload["review_consumed"] is True
    assert first_payload["exact_once_marker_written"] is True
    assert second_exit == 0
    assert second_payload["ok"] is False
    assert "exact_once_marker_already_present" in second_payload["blockers"]
    assert second_payload["authority_boundary"]["external_send_performed"] is False
