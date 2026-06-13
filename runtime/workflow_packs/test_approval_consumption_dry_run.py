from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import runtime.workflow_packs.store as store_module
from runtime.workflow_packs.agent_governance import create_agent_governance_run
from runtime.workflow_packs.approval_consumption_dry_run import (
    BLOCKED_STATUS,
    READY_STATUS,
    REJECTION_READY_STATUS,
    build_approval_consumption_dry_run,
)
from runtime.workflow_packs.approval_resume_contract import build_approval_resume_contract
from runtime.workflow_packs.approval_review_artifact import (
    build_approval_review_artifact,
    required_operator_statement,
)
from runtime.workflow_packs.store import WorkflowPackStore


@pytest.fixture(autouse=True)
def _short_workflow_pack_state_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store_module, "STATE_ROOT", Path("wfp_state"))


def test_approval_consumption_dry_run_blocks_missing_artifact_without_writing(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path, title="Consumption dry-run missing artifact")
    run_id = result["run"]["id"]
    gate_id = result["approval_gates"][0]["id"]
    contract = build_approval_resume_contract(tmp_path, run_id=run_id, gate_id=gate_id)
    before = _snapshot(tmp_path)

    report = build_approval_consumption_dry_run(
        tmp_path,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=contract["summary"]["request_digest"],
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "Workflow Pack approval review artifact is missing." in report["blockers"]
    assert report["summary"]["approval_consumption_performed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["writes_performed"] is False


def test_approval_consumption_dry_run_validates_approved_artifact_without_marker_or_resume(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    before = _snapshot(tmp_path)
    store = WorkflowPackStore(tmp_path)
    run_before = store.run_path(setup["run_id"]).read_text(encoding="utf-8")
    gate_path = store.run_dir(setup["run_id"]) / "approvals" / f"{setup['gate_id']}.json"
    gate_before = gate_path.read_text(encoding="utf-8")

    report = build_approval_consumption_dry_run(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        generated_at="2026-05-20T00:00:00Z",
    )

    marker_path = tmp_path / report["exact_once_marker_contract"]["path"]
    assert _snapshot(tmp_path) == before
    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["approval_consumption_dry_run_ready"] is True
    assert report["summary"]["future_single_workflow_pack_gate_approved"] is True
    assert report["summary"]["future_single_workflow_pack_gate_rejected"] is False
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["approval_consumption_performed"] is False
    assert report["summary"]["exact_once_marker_absent"] is True
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["summary"]["agent_bus_dispatch_performed"] is False
    assert report["marker_reservation_dry_run"]["first_reservation_allowed"] is True
    assert report["marker_reservation_dry_run"]["duplicate_reservation_blocked"] is True
    assert report["marker_reservation_dry_run"]["real_marker_written"] is False
    assert report["authority"]["consumes_approval_decision"] is False
    assert report["authority"]["writes_exact_once_marker"] is False
    assert report["authority"]["executes_resume"] is False
    assert marker_path.exists() is False
    assert store.run_path(setup["run_id"]).read_text(encoding="utf-8") == run_before
    assert gate_path.read_text(encoding="utf-8") == gate_before


def test_approval_consumption_dry_run_blocks_existing_marker_without_mutation(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    marker_path = tmp_path / setup["marker_path"]
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(json.dumps({"record_type": "future_marker_fixture"}), encoding="utf-8")
    before = _snapshot(tmp_path)

    report = build_approval_consumption_dry_run(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "real_exact_once_marker_absent" in report["blockers"]
    assert "marker_reservation_proof_passed" in report["blockers"]
    assert report["exact_once_marker_contract"]["exists"] is True
    assert report["marker_reservation_dry_run"]["first_reservation_allowed"] is False
    assert report["writes_performed"] is False


def test_approval_consumption_dry_run_blocks_tampered_artifact_scope(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    artifact_path = tmp_path / setup["approval_artifact_path"]
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["approval_scope"] = "all_workflow_pack_gates"
    artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    before = _snapshot(tmp_path)

    report = build_approval_consumption_dry_run(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "approval_scope_one_gate" in report["blockers"]
    assert report["summary"]["approval_consumption_performed"] is False
    assert report["summary"]["resume_execution_performed"] is False


def test_approval_consumption_dry_run_blocks_artifact_path_mismatch(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    wrong_path = (
        Path("runtime")
        / "workflow_packs"
        / "state"
        / "runs"
        / setup["run_id"]
        / "approval_reviews"
        / "wrong-packet.json"
    )
    before = _snapshot(tmp_path)

    report = build_approval_consumption_dry_run(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=wrong_path.as_posix(),
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert "approval_artifact_path must match" in " ".join(report["blockers"])
    assert report["writes_performed"] is False


def test_approval_consumption_dry_run_validates_rejection_without_execution(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="rejected")
    before = _snapshot(tmp_path)

    report = build_approval_consumption_dry_run(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="rejected",
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is True
    assert report["status"] == REJECTION_READY_STATUS
    assert report["summary"]["future_single_workflow_pack_gate_approved"] is False
    assert report["summary"]["future_single_workflow_pack_gate_rejected"] is True
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["summary"]["resume_execution_performed"] is False


def _write_review_artifact(tmp_path: Path, *, decision: str) -> dict[str, str]:
    result = create_agent_governance_run(tmp_path, title=f"Consumption dry-run {decision}")
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
        generated_at="2026-05-20T00:00:00Z",
    )
    return {
        "run_id": run_id,
        "gate_id": gate_id,
        "approval_packet_id": packet_id,
        "request_digest": digest,
        "approval_artifact_path": review["approval_artifact"]["path"],
        "marker_path": review["exact_once_marker_contract"]["path"],
    }


def _snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        snapshot[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot
