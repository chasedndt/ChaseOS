from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runtime.workflow_packs.agent_governance import create_agent_governance_run
from runtime.workflow_packs.approval_resume_contract import build_approval_resume_contract
from runtime.workflow_packs.approval_review_artifact import (
    BLOCKED_STATUS,
    EXISTING_STATUS,
    READY_STATUS,
    WRITTEN_STATUS,
    build_approval_review_artifact,
    required_operator_statement,
)
from runtime.workflow_packs.store import WorkflowPackStore


def test_approval_review_artifact_previews_without_writing_or_mutation(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Approval review preview")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    digest = contract["summary"]["request_digest"]
    before = _snapshot(tmp_path)

    report = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=digest,
        write_approval=False,
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["approval_artifact_ready"] is True
    assert report["summary"]["approval_artifact_written"] is False
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["writes_performed"] is False
    assert report["approval_artifact"]["required_operator_statement"].startswith("APPROVE WORKFLOW PACK GATE ONLY:")
    assert report["checks"]["no_execution_in_this_pass"] is True


def test_approval_review_artifact_blocks_mismatched_digest_without_writing(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Approval review mismatch")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    before = _snapshot(tmp_path)

    report = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest="0" * 64,
        operator_statement="APPROVE WORKFLOW PACK GATE ONLY: wrong wrong",
        write_approval=True,
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert report["writes_performed"] is False
    assert "request_digest does not match" in " ".join(report["blockers"])
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["resume_execution_performed"] is False


def test_approval_review_artifact_writes_only_scoped_approval_artifact(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Approval review write")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    packet_id = contract["summary"]["approval_packet_id"]
    digest = contract["summary"]["request_digest"]
    statement = required_operator_statement(
        decision="approved",
        approval_packet_id=packet_id,
        request_digest=digest,
    )
    store = WorkflowPackStore(tmp_path)
    run_before = store.run_path(run_id).read_text(encoding="utf-8")
    gate_path = store.run_dir(run_id) / "approvals" / f"{gate_id}.json"
    gate_before = gate_path.read_text(encoding="utf-8")

    report = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=digest,
        reviewer_id="operator-test",
        operator_statement=statement,
        write_approval=True,
        generated_at="2026-05-20T00:00:00Z",
    )

    artifact_path = tmp_path / report["approval_artifact"]["path"]
    marker_path = tmp_path / report["exact_once_marker_contract"]["path"]
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["approval_artifact_written"] is True
    assert report["summary"]["approval_artifact_write_status"] == "approval_artifact_written"
    assert payload["record_type"] == "workflow_pack_approval_resume_artifact"
    assert payload["approval_packet_id"] == packet_id
    assert payload["request_digest"] == digest
    assert payload["operator_decision"] == "approved"
    assert payload["approval_scope"] == "one_workflow_pack_gate_only"
    assert payload["approval_decision_consumed"] is False
    assert payload["exact_once_marker_reserved"] is False
    assert payload["resume_execution_performed"] is False
    assert payload["external_actions_performed"] is False
    assert payload["provider_calls_performed"] is False
    assert payload["browser_actions_performed"] is False
    assert payload["agent_bus_dispatch_performed"] is False
    assert payload["canonical_promotion_performed"] is False
    assert marker_path.exists() is False
    assert store.run_path(run_id).read_text(encoding="utf-8") == run_before
    assert gate_path.read_text(encoding="utf-8") == gate_before


def test_approval_review_artifact_reuses_existing_matching_artifact(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Approval review reuse")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    packet_id = contract["summary"]["approval_packet_id"]
    digest = contract["summary"]["request_digest"]
    statement = required_operator_statement(
        decision="approved",
        approval_packet_id=packet_id,
        request_digest=digest,
    )

    first = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=digest,
        operator_statement=statement,
        write_approval=True,
        generated_at="2026-05-20T00:00:00Z",
    )
    second = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=digest,
        operator_statement=statement,
        write_approval=True,
        generated_at="2026-05-20T00:01:00Z",
    )

    artifact_dir = tmp_path / "runtime" / "workflow_packs" / "state" / "runs" / run_id / "approval_reviews"
    assert first["status"] == WRITTEN_STATUS
    assert second["status"] == EXISTING_STATUS
    assert second["summary"]["approval_artifact_write_status"] == "existing_matching_approval_present"
    assert second["writes_performed"] is False
    assert len(list(artifact_dir.glob("*.json"))) == 1


def test_approval_review_artifact_can_record_rejection_without_execution(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Approval review reject")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    packet_id = contract["summary"]["approval_packet_id"]
    digest = contract["summary"]["request_digest"]
    statement = required_operator_statement(
        decision="rejected",
        approval_packet_id=packet_id,
        request_digest=digest,
    )

    report = build_approval_review_artifact(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=digest,
        reviewer_id="operator-test",
        operator_statement=statement,
        decision="rejected",
        write_approval=True,
    )
    payload = json.loads((tmp_path / report["approval_artifact"]["path"]).read_text(encoding="utf-8"))

    assert report["status"] == WRITTEN_STATUS
    assert report["summary"]["future_single_workflow_pack_gate_approved"] is False
    assert report["summary"]["future_single_workflow_pack_gate_rejected"] is True
    assert payload["operator_decision"] == "rejected"
    assert payload["future_single_workflow_pack_gate_approved"] is False
    assert payload["approval_decision_consumed"] is False
    assert payload["resume_execution_performed"] is False


def _snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        snapshot[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot
