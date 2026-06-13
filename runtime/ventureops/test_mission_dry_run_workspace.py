from __future__ import annotations

import json
import shutil
from pathlib import Path

from runtime.ventureops.mission_dry_runs import validate_mission_dry_run_workspace


def _dry_run_workspace() -> Path:
    return (
        Path(__file__).resolve().parents[2]
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


def test_local_mission_dry_run_workspace_validates() -> None:
    result = validate_mission_dry_run_workspace(_dry_run_workspace())

    assert result["ok"], result["errors"]
    assert result["mission_id"] == "mission-chase-ai-runtime-governance-kit"
    assert "mission-manifest.json" in result["files_checked"]
    assert "run-boundary.json" in result["files_checked"]


def test_local_mission_dry_run_keeps_activation_and_external_actions_blocked() -> None:
    root = _dry_run_workspace()
    manifest = json.loads((root / "mission-manifest.json").read_text(encoding="utf-8"))
    proposal = json.loads((root / "workflow-evolution-proposal.json").read_text(encoding="utf-8"))
    boundary = json.loads((root / "run-boundary.json").read_text(encoding="utf-8"))

    if boundary.get("mission_activation_performed") is True:
        assert manifest["status"] == "active"
        assert boundary["runtime_result_ingested"] is True
        assert boundary["agent_bus_task_claimed"] is True
        assert boundary["aor_dispatch_performed"] is True
    elif boundary.get("runtime_result_ingested") is True:
        assert manifest["status"] == "draft"
        assert boundary["agent_bus_task_claimed"] is True
        assert boundary["aor_dispatch_performed"] is True
        assert boundary["mission_activation_performed"] is False
    else:
        assert manifest["status"] == "draft"
        assert boundary["aor_dispatch_performed"] is False
        assert boundary["agent_bus_task_claimed"] is False
        assert boundary["mission_activation_performed"] is False
    assert manifest["mission_mode"]["auto_apply_evolution"] is False
    assert manifest["evolution_policy"]["allow_auto_apply"] is False
    assert proposal["auto_apply_allowed"] is False
    assert proposal["authority_boundary"]["applies_workflow_change"] is False
    assert boundary["approval_consumed"] is True
    assert boundary["approved_for_activation"] is True
    assert boundary["manifest_promotion_review_consumed"] is True
    assert boundary["workflow_evolution_reviewed_for_activation"] is True
    assert boundary["agent_bus_task_written"] is True
    assert boundary["agent_bus_enqueue_gate_consumed"] is True
    assert boundary["external_send_performed"] is False
    assert boundary["provider_call_performed"] is False
    assert boundary["browser_action_performed"] is False
    assert boundary["credential_or_secret_read_performed"] is False
    assert boundary["workflow_mutation_performed"] is False


def test_local_mission_dry_run_validator_blocks_external_action_drift(tmp_path: Path) -> None:
    target = tmp_path / "dry-run"
    _copy_workspace_fixture(target)
    boundary_path = target / "run-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["external_send_performed"] = True
    boundary["credential_or_secret_read_performed"] = True
    boundary_path.write_text(json.dumps(boundary, indent=2) + "\n", encoding="utf-8")

    result = validate_mission_dry_run_workspace(target)

    assert result["ok"] is False
    assert any("external_send_performed must be false" in error for error in result["errors"])
    assert any("credential_or_secret_read_performed must be false" in error for error in result["errors"])
