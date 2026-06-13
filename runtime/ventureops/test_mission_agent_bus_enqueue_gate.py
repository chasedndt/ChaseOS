from __future__ import annotations

import json
import shutil
from pathlib import Path

import runtime.cli.main as cli
from runtime.agent_bus.bus import list_tasks
from runtime.ventureops.mission_activation_approval_consumption import consume_mission_activation_approval
from runtime.ventureops.mission_agent_bus_enqueue_gate import (
    consume_mission_agent_bus_enqueue_gate,
    load_mission_agent_bus_enqueue_state,
)
from runtime.ventureops.mission_manifest_promotion_review_gate import (
    consume_mission_manifest_promotion_review_gate,
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


def _copy_workspace_fixture(workspace: Path) -> None:
    source = _source_workspace()
    workspace.mkdir(parents=True, exist_ok=True)
    for filename in _WORKSPACE_FIXTURE_FILES:
        shutil.copy2(source / filename, workspace / filename)


def _prepare_vault(tmp_path: Path) -> tuple[Path, Path]:
    vault_root = tmp_path / "vault"
    workspace = (
        vault_root
        / "07_LOGS"
        / "VentureOps-Missions"
        / "m"
    )
    _copy_workspace_fixture(workspace)

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

    manifest_path = workspace / "mission-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "draft"
    manifest["version"] = "0.1-dry-run"
    manifest["updated"] = "2026-05-13"
    manifest.pop("activation_state", None)
    manifest["notes"] = "Test fixture reset before exact-once Agent Bus enqueue gate."
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    boundary_path = workspace / "run-boundary.json"
    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["agent_bus_task_written"] = False
    boundary["agent_bus_task_claimed"] = False
    boundary["aor_dispatch_performed"] = False
    boundary["runtime_result_ingested"] = False
    boundary["mission_activation_performed"] = False
    boundary["notes"] = "Test fixture reset before exact-once Agent Bus enqueue gate."
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

    required_paths = {
        "runtime/workflows/registry/agent_runtime_governance_audit.yaml": "workflow_id: agent_runtime_governance_audit\n",
        "runtime/workflows/agent_runtime_governance_audit.py": "# test fixture\n",
        "runtime/workflows/registry/use_case_registry.yaml": "agent_runtime_governance_audit: {}\nventureops_ai_runtime_security_audit: {}\n",
        "runtime/workflows/missions/mission_chase_ai_runtime_governance_kit.py": "# test fixture\n",
        "runtime/agent_bus/mission_tasks.py": "# test fixture\n",
        "runtime/agent_bus/schemas/mission_task_packet.schema.json": "{}\n",
    }
    for relative, text in required_paths.items():
        target = vault_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

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

    boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    boundary["agent_bus_task_written"] = False
    boundary["agent_bus_task_claimed"] = False
    boundary["aor_dispatch_performed"] = False
    boundary["runtime_result_ingested"] = False
    boundary["mission_activation_performed"] = False
    boundary["notes"] = "Test fixture reset before exact-once Agent Bus enqueue gate."
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
    return vault_root, workspace


def test_mission_agent_bus_enqueue_gate_writes_one_unclaimed_task(tmp_path: Path) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)

    result = consume_mission_agent_bus_enqueue_gate(
        vault_root,
        mission_workspace=workspace,
        enqueue_id="test-mission-agent-bus-enqueue",
        approved_by="test-operator",
        operator_approval_statement="Approve exactly one local Agent Bus mission dry-review task.",
        write_approval=True,
        consume=True,
        enqueue_task=True,
    )

    assert result["ok"] is True, result["blockers"]
    assert result["approval_artifact_written"] is True
    assert result["enqueue_consumed"] is True
    assert result["exact_once_marker_written"] is True
    assert result["agent_bus_task_written"] is True
    assert result["runtime_task_claimed"] is False
    assert result["workflow_dispatched"] is False
    assert result["aor_dispatch_performed"] is False
    assert result["mission_activation_performed"] is False

    state = load_mission_agent_bus_enqueue_state(vault_root, mission_workspace=workspace)
    assert state["ok"] is True, state["errors"]
    assert state["enqueue_consumed"] is True
    assert state["agent_bus_task_written"] is True
    assert state["runtime_task_claimed"] is False
    assert state["workflow_dispatched"] is False

    tasks = [
        task for task in list_tasks(vault_root, recipient="Codex")
        if task.get("task_id") == result["agent_bus_task_id"]
    ]
    assert len(tasks) == 1
    assert tasks[0]["status"] == "open"
    assert "task_type: mission.run_dry_review" in str(tasks[0].get("notes") or "")

    duplicate = consume_mission_agent_bus_enqueue_gate(
        vault_root,
        mission_workspace=workspace,
        enqueue_id="test-mission-agent-bus-enqueue",
        approved_by="test-operator",
        operator_approval_statement="Approve exactly one local Agent Bus mission dry-review task.",
        write_approval=True,
        consume=True,
        enqueue_task=True,
    )
    assert duplicate["ok"] is False
    assert duplicate["duplicate_blocked_before_task_write"] is True
    assert "exact_once_marker_already_present" in duplicate["blockers"]


def test_mission_agent_bus_enqueue_gate_blocks_consume_without_task_write(tmp_path: Path) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)

    result = consume_mission_agent_bus_enqueue_gate(
        vault_root,
        mission_workspace=workspace,
        enqueue_id="test-consume-without-task",
        approved_by="test-operator",
        operator_approval_statement="Approve exactly one local Agent Bus mission dry-review task.",
        write_approval=True,
        consume=True,
        enqueue_task=False,
    )

    assert result["ok"] is False
    assert "consume_requires_enqueue_task" in result["blockers"]
    assert (workspace / "mission-agent-bus-enqueue-consumption.json").exists() is False


def test_mission_agent_bus_enqueue_gate_cli_preview_is_read_only(tmp_path: Path, capsys) -> None:
    vault_root, workspace = _prepare_vault(tmp_path)

    exit_code = cli.main(
        [
            "ventureops",
            "mission-agent-bus-enqueue-gate",
            "--vault-root",
            str(vault_root),
            "--mission-workspace",
            str(workspace),
            "--approval-id",
            "test-cli-preview",
            "--operator-approval-statement",
            "Approve exactly one local Agent Bus mission dry-review task.",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "ventureops.mission-agent-bus-enqueue-gate"
    assert result["status"] == "preview_ready"
    assert result["preview_only"] is True
    assert result["agent_bus_task_written"] is False
    assert (workspace / "mission-agent-bus-enqueue-approval-approved.json").exists() is False
    assert (workspace / "mission-agent-bus-enqueue-consumption.json").exists() is False
