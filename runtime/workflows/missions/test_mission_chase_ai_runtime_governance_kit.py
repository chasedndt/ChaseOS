from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from runtime.aor.engine import run_workflow
from runtime.aor.registry import load_manifest
from runtime.aor.role_cards import load_card
from runtime.aor.task_router import classify
from runtime.workflows.missions.mission_chase_ai_runtime_governance_kit import (
    WORKFLOW_ID,
    WorkflowExecutionError,
    build_mission_chase_ai_runtime_governance_kit,
)


_REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKSPACE_REL = (
    Path("07_LOGS")
    / "VentureOps-Missions"
    / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
)
_WORKSPACE = _REPO_ROOT / _WORKSPACE_REL
_APPROVAL_PACKET_REL = _WORKSPACE_REL / "activation-approval-packet-draft.json"
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
    destination = vault / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_REPO_ROOT / relative, destination)


def _copy_workspace_fixture(vault: Path) -> None:
    workspace = vault / _WORKSPACE_REL
    workspace.mkdir(parents=True, exist_ok=True)
    for filename in _WORKSPACE_FIXTURE_FILES:
        shutil.copy2(_WORKSPACE / filename, workspace / filename)
    _reset_workspace_to_draft(workspace)


def _reset_workspace_to_draft(workspace: Path) -> None:
    manifest_path = workspace / "mission-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "draft"
    manifest["version"] = "0.1-dry-run"
    manifest["updated"] = "2026-05-13"
    manifest.pop("activation_state", None)
    manifest["notes"] = "Test fixture reset for local AOR dry-review."
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


def _make_temp_vault() -> Path:
    scratch = Path("C:/tmp/chaseos-mission-aor-tests")
    scratch.mkdir(parents=True, exist_ok=True)
    vault = scratch / f"mission-aor-dry-review-{uuid.uuid4().hex}"
    vault.mkdir(parents=True, exist_ok=False)
    (vault / "CLAUDE.md").write_text("# test vault\n", encoding="utf-8")
    (vault / "00_HOME").mkdir(parents=True, exist_ok=True)
    (vault / "00_HOME" / "Now.md").write_text("# Now\n\nMission AOR dry-review test.\n", encoding="utf-8")
    _copy_workspace_fixture(vault)
    for relative in (
        "runtime/workflows/registry/mission_chase_ai_runtime_governance_kit.yaml",
        "06_AGENTS/role-cards/ventureops_mission_dry_reviewer.yaml",
        "runtime/workflows/missions/mission_chase_ai_runtime_governance_kit.py",
        "runtime/agent_bus/mission_tasks.py",
        "runtime/agent_bus/schemas/mission_task_packet.schema.json",
    ):
        _copy_repo_file(vault, relative)
    return vault


def test_mission_handler_builds_writebacks_without_writing_files() -> None:
    vault = _make_temp_vault()
    try:
        result = build_mission_chase_ai_runtime_governance_kit(
            inputs={
                "date": "2026-05-13",
                "run_id": "unit-dry-review",
                "mission_workspace_path": str(_WORKSPACE_REL),
                "activation_approval_packet_path": str(_APPROVAL_PACKET_REL),
            },
            vault_root=vault,
        )

        assert result["workflow_id"] == WORKFLOW_ID
        assert result["artifact_validation_ok"] is True
        assert result["mission_task_packet_valid"] is True
        assert result["authority_boundary"]["mission_activation_performed"] is False
        assert result["authority_boundary"]["agent_bus_task_written"] is False
        assert result["authority_boundary"]["workflow_evolution_applied"] is False
        assert len(result["writebacks"]) == 4
        assert not (vault / result["proof_path"]).exists()
    finally:
        shutil.rmtree(vault, ignore_errors=True)


def test_mission_handler_rejects_non_dry_review_execution_mode() -> None:
    vault = _make_temp_vault()
    try:
        with pytest.raises(WorkflowExecutionError, match="execution_mode must be dry_review"):
            build_mission_chase_ai_runtime_governance_kit(
                inputs={
                    "execution_mode": "activate",
                    "mission_workspace_path": str(_WORKSPACE_REL),
                    "activation_approval_packet_path": str(_APPROVAL_PACKET_REL),
                },
                vault_root=vault,
            )
    finally:
        shutil.rmtree(vault, ignore_errors=True)


def test_mission_aor_workflow_writes_only_declared_review_artifacts() -> None:
    vault = _make_temp_vault()
    try:
        result = run_workflow(
            WORKFLOW_ID,
            inputs={
                "date": "2026-05-13",
                "run_id": "aor-dry-review-test",
                "mission_workspace_path": str(_WORKSPACE_REL),
                "activation_approval_packet_path": str(_APPROVAL_PACKET_REL),
            },
            vault_root=vault,
        )

        assert result.status == "success"
        files_written = result.outputs["writeback"]["files_written"]
        assert len(files_written) == 4
        assert all(
            path.startswith(
                (
                    "07_LOGS/VentureOps-Missions/",
                    "07_LOGS/Mission-Reviews/",
                    "07_LOGS/Workflow-Proofs/",
                    "07_LOGS/Runtime-Audits/",
                )
            )
            for path in files_written
        )
        for path in files_written:
            assert (vault / path).exists()

        proof_path = next(path for path in files_written if path.startswith("07_LOGS/Workflow-Proofs/"))
        proof = json.loads((vault / proof_path).read_text(encoding="utf-8"))
        assert proof["mission_task_packet_valid"] is True
        assert proof["authority_boundary"]["aor_dispatch_performed"] is True
        assert proof["authority_boundary"]["mission_activation_performed"] is False
        assert proof["authority_boundary"]["agent_bus_task_written"] is False

        manifest = json.loads((vault / _WORKSPACE_REL / "mission-manifest.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "draft"
        assert not (vault / "runtime" / "agent_bus" / "agent_bus.sqlite").exists()
    finally:
        shutil.rmtree(vault, ignore_errors=True)


def test_live_manifest_task_type_and_role_card_validate() -> None:
    task_type = classify("ventureops-mission-dry-review")
    manifest = load_manifest(WORKFLOW_ID, vault_root=_REPO_ROOT)
    role_card = load_card("ventureops_mission_dry_reviewer", vault_root=_REPO_ROOT)

    assert task_type["id"] == "ventureops-mission-dry-review"
    assert manifest is not None
    assert manifest["task_type"] == "ventureops-mission-dry-review"
    assert manifest["status"] == "active"
    assert "07_LOGS/Mission-Reviews/" in manifest["writeback_targets"]
    assert role_card is not None
    assert "07_LOGS/Mission-Reviews/" in role_card["write_scope"]
