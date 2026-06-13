from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import runtime.workflow_packs.store as store_module
from runtime.workflow_packs.agent_governance import create_agent_governance_run
from runtime.workflow_packs.approval_marker_reservation import build_approval_marker_reservation
from runtime.workflow_packs.approval_resume_contract import build_approval_resume_contract
from runtime.workflow_packs.approval_review_artifact import (
    build_approval_review_artifact,
    required_operator_statement,
)
from runtime.workflow_packs.approved_local_resume_executor import (
    BLOCKED_STATUS,
    EXECUTED_STATUS,
    READY_STATUS,
    REJECTED_STATUS,
    build_approved_local_resume_executor,
)
from runtime.workflow_packs.store import WorkflowPackStore


@pytest.fixture(autouse=True)
def _short_workflow_pack_state_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store_module, "STATE_ROOT", Path("wfp_state"))


def test_approved_local_resume_previews_without_mutation(tmp_path: Path) -> None:
    setup = _write_review_artifact_and_marker(tmp_path, decision="approved")
    before = _snapshot(tmp_path)

    report = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="approved",
        execute_resume=False,
        generated_at="2026-05-21T00:00:00Z",
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["approval_consumption_built"] is True
    assert report["summary"]["resume_executor_built"] is True
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["approval_consumption_performed"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["summary"]["external_actions_performed"] is False
    assert report["local_resume_evidence"]["required_operator_statement"].startswith(
        "CONSUME WORKFLOW PACK LOCAL DECISION ONLY:"
    )
    assert report["writes_performed"] is False


def test_approved_local_resume_consumes_approval_and_updates_only_local_state(tmp_path: Path) -> None:
    setup = _write_review_artifact_and_marker(tmp_path, decision="approved")
    preview = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="approved",
    )
    store = WorkflowPackStore(tmp_path)
    gate_path = store.approval_gate_path(setup["run_id"], setup["gate_id"])
    artifact_path = tmp_path / setup["approval_artifact_path"]
    marker_path = tmp_path / setup["marker_path"]
    artifact_before = artifact_path.read_text(encoding="utf-8")
    marker_before = marker_path.read_text(encoding="utf-8")

    report = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="approved",
        execute_resume=True,
        operator_statement=preview["local_resume_evidence"]["required_operator_statement"],
        executed_by="operator-test",
        generated_at="2026-05-21T00:00:00Z",
    )

    evidence_path = tmp_path / report["local_resume_evidence"]["path"]
    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    loaded_run = store.get_run(setup["run_id"])
    loaded_gate = _gate_by_id(store, setup["run_id"], setup["gate_id"])

    assert report["ok"] is True
    assert report["status"] == EXECUTED_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["approval_decision_consumed"] is True
    assert report["summary"]["approval_consumption_performed"] is True
    assert report["summary"]["resume_execution_performed"] is True
    assert report["summary"]["state_mutations_performed"] is True
    assert report["summary"]["run_status_before"] == "review_required"
    assert report["summary"]["gate_status_before"] == "pending"
    assert report["summary"]["run_status_after"] == "approved"
    assert report["summary"]["gate_status_after"] == "approved"
    assert report["summary"]["external_actions_performed"] is False
    assert report["summary"]["provider_calls_performed"] is False
    assert report["summary"]["browser_actions_performed"] is False
    assert report["summary"]["agent_bus_dispatch_performed"] is False
    assert report["summary"]["canonical_promotion_performed"] is False
    assert report["summary"]["policy_mutation_performed"] is False
    assert evidence_payload["record_type"] == "workflow_pack_approved_local_resume_execution"
    assert evidence_payload["approval_packet_id"] == setup["approval_packet_id"]
    assert evidence_payload["request_digest"] == setup["request_digest"]
    assert evidence_payload["operator_decision"] == "approved"
    assert evidence_payload["approval_decision_consumed"] is True
    assert evidence_payload["approval_consumption_performed"] is True
    assert evidence_payload["exact_once_marker_reserved"] is True
    assert evidence_payload["resume_execution_performed"] is True
    assert evidence_payload["external_actions_performed"] is False
    assert evidence_payload["provider_calls_performed"] is False
    assert evidence_payload["browser_actions_performed"] is False
    assert evidence_payload["agent_bus_dispatch_performed"] is False
    assert evidence_payload["canonical_promotion_performed"] is False
    assert loaded_run.status == "approved"
    assert loaded_run.approval_refs[0].status == "approved"
    assert loaded_gate.status == "approved"
    assert loaded_gate.approved_by == "operator-test"
    assert gate_path.exists()
    assert artifact_path.read_text(encoding="utf-8") == artifact_before
    assert marker_path.read_text(encoding="utf-8") == marker_before


def test_approved_local_resume_blocks_duplicate_without_mutation(tmp_path: Path) -> None:
    setup = _write_review_artifact_and_marker(tmp_path, decision="approved")
    preview = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="approved",
    )
    first = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="approved",
        execute_resume=True,
        operator_statement=preview["local_resume_evidence"]["required_operator_statement"],
        executed_by="operator-test",
    )
    before_second = _snapshot(tmp_path)

    second = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="approved",
        execute_resume=True,
        operator_statement=preview["local_resume_evidence"]["required_operator_statement"],
        executed_by="operator-test",
    )

    assert first["status"] == EXECUTED_STATUS
    assert _snapshot(tmp_path) == before_second
    assert second["ok"] is False
    assert second["status"] == BLOCKED_STATUS
    assert "Workflow Pack local resume evidence already exists." in second["blockers"]
    assert "current_gate_still_pending" in second["blockers"]
    assert second["writes_performed"] is False


def test_approved_local_resume_blocks_missing_marker_without_mutation(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    before = _snapshot(tmp_path)

    report = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        execute_resume=True,
        operator_statement="CONSUME WORKFLOW PACK LOCAL DECISION ONLY: wrong wrong",
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "Workflow Pack exact-once marker is missing." in report["blockers"]
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["writes_performed"] is False


def test_approved_local_resume_consumes_rejection_and_cancels_local_run(tmp_path: Path) -> None:
    setup = _write_review_artifact_and_marker(tmp_path, decision="rejected")
    preview = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="rejected",
    )

    report = build_approved_local_resume_executor(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        exact_once_marker_path=setup["marker_path"],
        expected_decision="rejected",
        execute_resume=True,
        operator_statement=preview["local_resume_evidence"]["required_operator_statement"],
        executed_by="operator-test",
    )
    store = WorkflowPackStore(tmp_path)
    loaded_run = store.get_run(setup["run_id"])
    loaded_gate = _gate_by_id(store, setup["run_id"], setup["gate_id"])
    evidence_payload = json.loads((tmp_path / report["local_resume_evidence"]["path"]).read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == REJECTED_STATUS
    assert report["summary"]["operator_decision"] == "rejected"
    assert report["summary"]["approval_decision_consumed"] is True
    assert report["summary"]["resume_execution_performed"] is True
    assert report["summary"]["run_status_after"] == "cancelled"
    assert report["summary"]["gate_status_after"] == "rejected"
    assert report["summary"]["external_actions_performed"] is False
    assert loaded_run.status == "cancelled"
    assert loaded_run.approval_refs[0].status == "rejected"
    assert loaded_gate.status == "rejected"
    assert evidence_payload["operator_decision"] == "rejected"
    assert evidence_payload["after_state"]["run_status"] == "cancelled"
    assert evidence_payload["external_actions_performed"] is False


def _write_review_artifact_and_marker(tmp_path: Path, *, decision: str) -> dict[str, str]:
    setup = _write_review_artifact(tmp_path, decision=decision)
    preview = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision=decision,
    )
    marker = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision=decision,
        reserve_marker=True,
        operator_statement=preview["exact_once_marker"]["required_operator_statement"],
        reserved_by="operator-test",
        generated_at="2026-05-21T00:00:00Z",
    )
    return setup | {"marker_path": marker["exact_once_marker"]["path"]}


def _write_review_artifact(tmp_path: Path, *, decision: str) -> dict[str, str]:
    result = create_agent_governance_run(tmp_path, title=f"Approved local resume {decision}")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    packet_id = contract["summary"]["approval_packet_id"]
    digest = contract["summary"]["request_digest"]
    statement = required_operator_statement(
        decision=decision,
        approval_packet_id=packet_id,
        request_digest=digest,
    )
    review = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=digest,
        reviewer_id="operator-test",
        operator_statement=statement,
        decision=decision,
        write_approval=True,
        generated_at="2026-05-21T00:00:00Z",
    )
    return {
        "run_id": run_id,
        "gate_id": gate_id,
        "approval_packet_id": packet_id,
        "request_digest": digest,
        "approval_artifact_path": review["approval_artifact"]["path"],
    }


def _snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        snapshot[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def _gate_by_id(store: WorkflowPackStore, run_id: str, gate_id: str):
    return next(gate for gate in store.list_approval_gates(run_id) if gate.id == gate_id)
