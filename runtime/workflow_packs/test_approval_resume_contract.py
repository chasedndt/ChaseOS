from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runtime.workflow_packs.agent_governance import create_agent_governance_run
from runtime.workflow_packs.approval_resume_contract import build_approval_resume_contract
from runtime.workflow_packs.store import WorkflowPackStore


def test_approval_resume_contract_previews_gate_without_mutation(tmp_path: Path) -> None:
    result = create_agent_governance_run(
        tmp_path,
        title="Approval resume design",
        user_goal="Design safe resume contract before live execution",
        agent_name="Codex",
        runtime="agent bus worker",
        tools="repo.inspect\ncode.patch\ntest.run",
        external_actions="send_email\nruntime_execution",
        permission_surfaces="approval queue\nruntime execution",
        workflow_manifest="steps:\n  - send_email\n  - execute runtime task\napproval: required",
    )
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    before = _snapshot(tmp_path)

    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)

    assert _snapshot(tmp_path) == before
    assert contract["status"] == "ready_for_operator_approval_review_only"
    assert contract["summary"]["contract_preview_ready"] is True
    assert contract["summary"]["approval_consumption_built"] is True
    assert contract["summary"]["resume_executor_built"] is True
    assert contract["summary"]["approval_decision_consumed"] is False
    assert contract["summary"]["external_actions_performed"] is False
    assert contract["checks"]["execution_allowed_now"] is False
    assert contract["selected_gate"]["id"] == gate_id
    assert contract["selected_gate"]["status"] == "pending"
    assert contract["selected_preview_artifacts"]
    assert contract["future_resume_packet_preview"]["approval_packet_id"].startswith("wfpr-")
    assert contract["future_resume_packet_preview"]["request_digest"] == contract["summary"]["request_digest"]
    assert "approval_scope: one_workflow_pack_gate_only" in contract["future_resume_packet_preview"]["required_future_approval_fields"]
    assert contract["future_resume_packet_preview"]["exact_match_requirements"]["approval_decision_consumed"] is False
    assert contract["safety"]["mutates_approval_gate"] is False
    assert contract["safety"]["consumes_approval_decision"] is False
    assert contract["safety"]["executes_resume"] is False


def test_approval_resume_contract_fails_closed_without_run_id(tmp_path: Path) -> None:
    create_agent_governance_run(tmp_path, title="Queued gate")

    contract = build_approval_resume_contract(tmp_path)

    assert contract["status"] == "blocked_missing_run_id"
    assert contract["summary"]["contract_preview_ready"] is False
    assert contract["summary"]["approval_consumption_performed"] is False
    assert contract["summary"]["resume_execution_performed"] is False
    assert contract["pending_gate_queue"]
    assert contract["future_resume_packet_preview"] is None


def test_approved_gate_still_requires_future_consumption_executor(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Approved but not consumable")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    store = WorkflowPackStore(tmp_path)
    gate_path = store.run_dir(run_id) / "approvals" / f"{gate_id}.json"
    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    gate_data["status"] = "approved"
    gate_data["approved_by"] = "operator-test"
    gate_data["approved_at"] = "2026-05-20T00:00:00Z"
    gate_path.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)

    assert contract["status"] == "approved_gate_present_local_resume_consumed_or_duplicate_blocked"
    assert contract["summary"]["approved_gate_count"] >= 1
    assert contract["checks"]["gate_pending_or_approved"] is True
    assert contract["checks"]["approval_consumption_available"] is True
    assert contract["checks"]["resume_executor_available"] is True
    assert contract["summary"]["approval_execution_allowed"] is False
    assert contract["summary"]["approval_decision_consumed"] is False
    assert "duplicate local resume is blocked" in " ".join(contract["blockers"])


def test_approval_resume_contract_digest_is_deterministic(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Stable packet")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]

    first = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    second = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)

    assert first["summary"]["request_digest"] == second["summary"]["request_digest"]
    assert first["future_resume_packet_preview"]["approval_packet_id"] == second["future_resume_packet_preview"]["approval_packet_id"]


def _snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        snapshot[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot
