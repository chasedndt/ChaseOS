from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from runtime.agent_bus.bus import list_tasks, update_task_status
from runtime.ventureops.mission_activation_approval_consumption import consume_mission_activation_approval
from runtime.ventureops.mission_activation_gate import (
    build_mission_activation_gate_approval,
    consume_mission_activation_gate,
    load_mission_activation_gate_state,
    validate_mission_activation_gate_approval,
)
from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness
from runtime.ventureops.mission_agent_bus_enqueue_gate import consume_mission_agent_bus_enqueue_gate
from runtime.ventureops.mission_manifest_promotion_review_gate import (
    consume_mission_manifest_promotion_review_gate,
)
from runtime.ventureops.mission_runtime_claim_result_gate import (
    consume_mission_runtime_claim_result_gate,
    load_mission_runtime_claim_result_state,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _source_workspace() -> Path:
    return (
        _repo_root()
        / "07_LOGS"
        / "VentureOps-Missions"
        / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
    )


_WORKSPACE_REL = Path("07_LOGS") / "VentureOps-Missions" / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
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


def _copy_repo_file(vault: Path, relative: str) -> None:
    target = vault / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_repo_root() / relative, target)


def _copy_workspace_fixture(workspace: Path) -> None:
    source = _source_workspace()
    workspace.mkdir(parents=True, exist_ok=True)
    for filename in _WORKSPACE_FIXTURE_FILES:
        shutil.copy2(source / filename, workspace / filename)


def _reset_workspace_to_pre_enqueue(workspace: Path) -> None:
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
        target = workspace / filename
        if target.exists():
            target.unlink()
    for target in workspace.glob("aor-dry-review-*.json"):
        target.unlink()

    manifest_path = workspace / "mission-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "draft"
    manifest["version"] = "0.1-dry-run"
    manifest["updated"] = "2026-05-13"
    manifest.pop("activation_state", None)
    manifest["notes"] = "Test fixture reset to pre-enqueue Mission Mode state."
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    boundary_path = workspace / "run-boundary.json"
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
            "notes": "Test fixture reset before Mission Mode runtime claim/result and activation gates.",
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

    state_path = workspace / "mission-state-ledger.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["current_status"] = "blocked"
    state["current_phase"] = "fixture_pre_enqueue_reset"
    state["last_run_id"] = "fixture-pre-enqueue-reset"
    state["last_review_date"] = "2026-05-13"
    state["progress_summary"] = "Test fixture reset to pre-enqueue Mission Mode state."
    state["active_blockers"] = [
        "real_client_scope_not_supplied",
        "mission_activation_approval_not_consumed",
        "workflow_evolution_proposal_pending_review",
        "agent_bus_mission_task_not_written",
    ]
    state["pending_approvals"] = [
        "mission_activation_approval_consumption",
        "manifest_promotion_workflow_evolution_review_gate",
        "agent_bus_mission_enqueue_gate",
    ]
    state["next_recommended_pass"] = "fixture-agent-bus-enqueue"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    review_path = workspace / "mission-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["next_pass"] = "fixture-agent-bus-enqueue"
    review["approvals_needed"] = ["mission_activation_approval_consumption", "manifest_promotion_workflow_evolution_review_gate", "agent_bus_mission_enqueue_gate"]
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    artifact_path = workspace / "artifact-index.json"
    index = json.loads(artifact_path.read_text(encoding="utf-8"))
    index["status"] = "fixture_pre_enqueue_reset"
    index["mission_activation_status"] = "not_activated"
    for key in (
        "runtime_claim_result_approval_artifact",
        "mission_runtime_result",
        "runtime_claim_result_marker",
        "mission_activation_execution_approval",
        "mission_activation_execution_marker",
    ):
        if isinstance(index.get("artifacts"), dict):
            index["artifacts"].pop(key, None)
        if isinstance(index.get("linked_notes"), dict):
            index["linked_notes"].pop(key, None)
    artifact_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prepare_vault(tmp_path: Path) -> tuple[Path, Path]:
    scratch = Path("C:/tmp/chaseos-mission-runtime-gate-tests")
    scratch.mkdir(parents=True, exist_ok=True)
    vault_root = scratch / f"vault-{uuid.uuid4().hex[:12]}"
    workspace = vault_root / _WORKSPACE_REL
    _copy_workspace_fixture(workspace)
    _reset_workspace_to_pre_enqueue(workspace)
    (vault_root / "CLAUDE.md").write_text("# test vault\n", encoding="utf-8")
    (vault_root / "00_HOME").mkdir(parents=True, exist_ok=True)
    (vault_root / "00_HOME" / "Now.md").write_text("# Now\n\nMission runtime gate test.\n", encoding="utf-8")
    for relative in (
        "runtime/aor/task_type_table.yaml",
        "runtime/workflows/registry/agent_runtime_governance_audit.yaml",
        "runtime/workflows/registry/mission_chase_ai_runtime_governance_kit.yaml",
        "runtime/workflows/registry/use_case_registry.yaml",
        "runtime/workflows/agent_runtime_governance_audit.py",
        "runtime/workflows/missions/mission_chase_ai_runtime_governance_kit.py",
        "runtime/agent_bus/mission_tasks.py",
        "runtime/agent_bus/schemas/mission_task_packet.schema.json",
        "06_AGENTS/role-cards/ventureops_mission_dry_reviewer.yaml",
    ):
        _copy_repo_file(vault_root, relative)

    activation = consume_mission_activation_approval(
        vault_root,
        mission_workspace=workspace,
        approval_id="fixture-activation-approval",
        approved_by="test-operator",
        operator_approval_statement="Approve fixture activation readiness gate only.",
        write_approval=True,
        consume=True,
    )
    assert activation["ok"], activation["blockers"]
    review = consume_mission_manifest_promotion_review_gate(
        vault_root,
        mission_workspace=workspace,
        review_id="fixture-manifest-review",
        approved_by="test-operator",
        operator_approval_statement="Approve fixture manifest review gate only.",
        write_review=True,
        consume=True,
    )
    assert review["ok"], review["blockers"]
    enqueue = consume_mission_agent_bus_enqueue_gate(
        vault_root,
        mission_workspace=workspace,
        enqueue_id="fixture-agent-bus-enqueue",
        approved_by="test-operator",
        operator_approval_statement="Approve exactly one local Agent Bus mission dry-review task.",
        write_approval=True,
        consume=True,
        enqueue_task=True,
    )
    assert enqueue["ok"], enqueue["blockers"]
    return vault_root, workspace


def test_runtime_claim_result_gate_dispatches_aor_ingests_and_closes_task(tmp_path: Path) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)
    try:
        result = consume_mission_runtime_claim_result_gate(
            vault_root,
            mission_workspace=workspace,
            approval_id="fixture-runtime-claim-result",
            approved_by="test-operator",
            operator_approval_statement=(
                "Approve exactly one local runtime claim, AOR dry-review dispatch, "
                "mission result ingestion, and Agent Bus task closeout."
            ),
            write_approval=True,
            consume=True,
            claim_task_flag=True,
            dispatch_aor=True,
            ingest_result=True,
            close_task=True,
        )

        assert result["ok"] is True, result["blockers"]
        assert result["runtime_task_claimed"] is True
        assert result["aor_dispatch_performed"] is True
        assert result["mission_result_ingested"] is True
        assert result["agent_bus_task_closed"] is True
        assert result["mission_activation_performed"] is False
        assert (workspace / "mission-runtime-result.json").exists()
        assert (workspace / "mission-runtime-claim-result-consumption.json").exists()

        state = load_mission_runtime_claim_result_state(vault_root, mission_workspace=workspace)
        assert state["ok"] is True, state["errors"]
        assert state["claim_result_consumed"] is True
        assert state["stored_task_status"] == "done"

        tasks = [
            task for task in list_tasks(vault_root, recipient="Codex")
            if task["task_id"] == result["agent_bus_task_id"]
        ]
        assert tasks[0]["status"] == "done"

        readiness = build_mission_activation_readiness(vault_root, mission_workspace=workspace)
        assert readiness["ready_for_activation"] is True
        assert readiness["runtime_claim_result_consumed"] is True
        assert readiness["runtime_task_closed"] is True
        assert readiness["mission_result_ingested"] is True
        assert readiness["mission_activation_gate_consumed"] is False

        duplicate = consume_mission_runtime_claim_result_gate(
            vault_root,
            mission_workspace=workspace,
            approval_id="fixture-runtime-claim-result",
            approved_by="test-operator",
            operator_approval_statement=(
                "Approve exactly one local runtime claim, AOR dry-review dispatch, "
                "mission result ingestion, and Agent Bus task closeout."
            ),
            write_approval=True,
            consume=True,
            claim_task_flag=True,
            dispatch_aor=True,
            ingest_result=True,
            close_task=True,
        )
        assert duplicate["ok"] is False
        assert "exact_once_marker_already_present" in duplicate["blockers"]
    finally:
        shutil.rmtree(vault_root, ignore_errors=True)


def test_runtime_claim_result_state_blocks_closed_task_drift(tmp_path: Path) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)
    try:
        result = consume_mission_runtime_claim_result_gate(
            vault_root,
            mission_workspace=workspace,
            approval_id="fixture-runtime-claim-result",
            approved_by="test-operator",
            operator_approval_statement=(
                "Approve exactly one local runtime claim, AOR dry-review dispatch, "
                "mission result ingestion, and Agent Bus task closeout."
            ),
            write_approval=True,
            consume=True,
            claim_task_flag=True,
            dispatch_aor=True,
            ingest_result=True,
            close_task=True,
        )
        assert result["ok"], result["blockers"]

        drift = update_task_status(
            vault_root,
            task_id=str(result["agent_bus_task_id"]),
            runtime="Codex",
            status="blocked",
            event_type="blocked",
            message="Test-only drift after mission claim/result marker consumption.",
            artifacts=[],
        )
        assert drift["updated"] is True

        state = load_mission_runtime_claim_result_state(vault_root, mission_workspace=workspace)

        assert state["ok"] is False
        assert "claim_result_marker_task_not_closed:blocked" in state["errors"]
    finally:
        shutil.rmtree(vault_root, ignore_errors=True)


def test_activation_gate_moves_local_mission_active_after_result_ingestion(tmp_path: Path) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)
    try:
        claim = consume_mission_runtime_claim_result_gate(
            vault_root,
            mission_workspace=workspace,
            approval_id="fixture-runtime-claim-result",
            approved_by="test-operator",
            operator_approval_statement=(
                "Approve exactly one local runtime claim, AOR dry-review dispatch, "
                "mission result ingestion, and Agent Bus task closeout."
            ),
            write_approval=True,
            consume=True,
            claim_task_flag=True,
            dispatch_aor=True,
            ingest_result=True,
            close_task=True,
        )
        assert claim["ok"], claim["blockers"]

        activation = consume_mission_activation_gate(
            vault_root,
            mission_workspace=workspace,
            activation_id="fixture-local-activation",
            approved_by="test-operator",
            operator_approval_statement="Approve exact-once local mission activation after runtime result ingestion.",
            write_approval=True,
            consume=True,
            activate=True,
        )

        assert activation["ok"] is True, activation["blockers"]
        assert activation["mission_activation_performed"] is True
        assert activation["authority_boundary"]["external_send_performed"] is False
        assert (workspace / "mission-activation-execution-consumption.json").exists()

        manifest = json.loads((workspace / "mission-manifest.json").read_text(encoding="utf-8"))
        state = json.loads((workspace / "mission-state-ledger.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "active"
        assert state["current_status"] == "active"
        assert state["current_phase"] == "mission_active_local"

        gate_state = load_mission_activation_gate_state(vault_root, mission_workspace=workspace)
        assert gate_state["ok"] is True, gate_state["errors"]
        assert gate_state["activation_consumed"] is True

        readiness = build_mission_activation_readiness(vault_root, mission_workspace=workspace)
        assert readiness["readiness_status"] == "mission_active_local"
        assert readiness["mission_active"] is True
        assert readiness["ready_for_activation"] is False
        assert readiness["authority_boundary"]["mission_activation_performed"] is True
        assert readiness["authority_boundary"]["external_send_performed"] is False

        duplicate = consume_mission_activation_gate(
            vault_root,
            mission_workspace=workspace,
            activation_id="fixture-local-activation",
            approved_by="test-operator",
            operator_approval_statement="Approve exact-once local mission activation after runtime result ingestion.",
            write_approval=True,
            consume=True,
            activate=True,
        )
        assert duplicate["ok"] is False
        assert "exact_once_marker_already_present" in duplicate["blockers"]
    finally:
        shutil.rmtree(vault_root, ignore_errors=True)


def test_activation_gate_approval_is_bound_to_requested_workspace(tmp_path: Path) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)
    try:
        claim = consume_mission_runtime_claim_result_gate(
            vault_root,
            mission_workspace=workspace,
            approval_id="fixture-runtime-claim-result",
            approved_by="test-operator",
            operator_approval_statement=(
                "Approve exactly one local runtime claim, AOR dry-review dispatch, "
                "mission result ingestion, and Agent Bus task closeout."
            ),
            write_approval=True,
            consume=True,
            claim_task_flag=True,
            dispatch_aor=True,
            ingest_result=True,
            close_task=True,
        )
        assert claim["ok"], claim["blockers"]
        approval = build_mission_activation_gate_approval(
            vault_root,
            mission_workspace=workspace,
            activation_id="fixture-local-activation",
            approved_by="test-operator",
            operator_approval_statement="Approve exact-once local mission activation after runtime result ingestion.",
        )
        approval["mission_workspace_path"] = "07_LOGS/VentureOps-Missions/not-the-requested-workspace"

        validation = validate_mission_activation_gate_approval(
            approval,
            vault_root=vault_root,
            mission_workspace=workspace,
        )

        assert validation["ok"] is False
        assert "approval mission_workspace_path does not match requested mission workspace" in validation["errors"]
    finally:
        shutil.rmtree(vault_root, ignore_errors=True)


def test_mission_gate_schema_templates_include_hardening_boundaries() -> None:
    template_root = _repo_root() / "runtime" / "ventureops" / "templates"
    claim_schema = (template_root / "mission_runtime_claim_result_gate_schema.yaml").read_text(encoding="utf-8")
    activation_schema = (template_root / "mission_activation_gate_schema.yaml").read_text(encoding="utf-8")

    assert "credential_or_secret_read_authorized" in claim_schema
    assert "credential_or_secret_read_performed" in claim_schema
    assert "claim_dispatch_ingest_close_mission_dry_review_task" in claim_schema
    assert "credential_or_secret_read_authorized" in activation_schema
    assert "credential_or_secret_read_performed" in activation_schema
    assert "move_local_mission_state_to_active" in activation_schema
