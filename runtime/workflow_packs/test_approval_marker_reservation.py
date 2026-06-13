from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import runtime.workflow_packs.store as store_module
from runtime.workflow_packs.agent_governance import create_agent_governance_run
from runtime.workflow_packs.approval_marker_reservation import (
    BLOCKED_STATUS,
    READY_STATUS,
    WRITTEN_STATUS,
    build_approval_marker_reservation,
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


def test_approval_marker_reservation_previews_without_writing_or_resume(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    before = _snapshot(tmp_path)

    report = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        reserve_marker=False,
        generated_at="2026-05-20T00:00:00Z",
    )

    marker_path = tmp_path / report["exact_once_marker"]["path"]
    assert _snapshot(tmp_path) == before
    assert report["ok"] is True
    assert report["status"] == READY_STATUS
    assert report["summary"]["approval_marker_reservation_ready"] is True
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["approval_consumption_performed"] is False
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["exact_once_marker"]["required_operator_statement"].startswith(
        "RESERVE WORKFLOW PACK EXACT-ONCE MARKER ONLY:"
    )
    assert report["writes_performed"] is False
    assert marker_path.exists() is False


def test_approval_marker_reservation_writes_only_scoped_marker(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    preview = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
    )
    before = _snapshot(tmp_path)
    store = WorkflowPackStore(tmp_path)
    run_before = store.run_path(setup["run_id"]).read_text(encoding="utf-8")
    gate_path = store.run_dir(setup["run_id"]) / "approvals" / f"{setup['gate_id']}.json"
    gate_before = gate_path.read_text(encoding="utf-8")
    artifact_path = tmp_path / setup["approval_artifact_path"]
    artifact_before = artifact_path.read_text(encoding="utf-8")

    report = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        reserve_marker=True,
        operator_statement=preview["exact_once_marker"]["required_operator_statement"],
        reserved_by="operator-test",
        generated_at="2026-05-20T00:00:00Z",
    )

    after = _snapshot(tmp_path)
    marker_path = tmp_path / report["exact_once_marker"]["path"]
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    new_files = sorted(set(after) - set(before))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["writes_performed"] is True
    assert report["summary"]["exact_once_marker_reserved"] is True
    assert report["summary"]["exact_once_marker_written"] is True
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["approval_consumption_performed"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert report["summary"]["agent_bus_dispatch_performed"] is False
    assert report["authority"]["writes_exact_once_marker"] is True
    assert marker_payload["record_type"] == "workflow_pack_approval_consumption_exact_once_marker"
    assert marker_payload["approval_packet_id"] == setup["approval_packet_id"]
    assert marker_payload["request_digest"] == setup["request_digest"]
    assert marker_payload["operator_decision"] == "approved"
    assert marker_payload["marker_scope"] == "one_workflow_pack_gate_only"
    assert marker_payload["approval_decision_consumed"] is False
    assert marker_payload["approval_consumption_performed"] is False
    assert marker_payload["exact_once_marker_reserved"] is True
    assert marker_payload["resume_execution_performed"] is False
    assert marker_payload["external_actions_performed"] is False
    assert marker_payload["provider_calls_performed"] is False
    assert marker_payload["browser_actions_performed"] is False
    assert marker_payload["agent_bus_dispatch_performed"] is False
    assert marker_payload["canonical_promotion_performed"] is False
    assert new_files == [report["exact_once_marker"]["path"]]
    assert store.run_path(setup["run_id"]).read_text(encoding="utf-8") == run_before
    assert gate_path.read_text(encoding="utf-8") == gate_before
    assert artifact_path.read_text(encoding="utf-8") == artifact_before


def test_approval_marker_reservation_blocks_mismatched_statement_without_writing(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    before = _snapshot(tmp_path)

    report = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        reserve_marker=True,
        operator_statement="RESERVE WORKFLOW PACK EXACT-ONCE MARKER ONLY: wrong wrong",
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "operator_statement must exactly match" in " ".join(report["blockers"])
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["writes_performed"] is False


def test_approval_marker_reservation_blocks_duplicate_marker_without_mutation(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    preview = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
    )
    statement = preview["exact_once_marker"]["required_operator_statement"]
    first = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        reserve_marker=True,
        operator_statement=statement,
        reserved_by="operator-test",
    )
    before_second = _snapshot(tmp_path)

    second = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="approved",
        reserve_marker=True,
        operator_statement=statement,
        reserved_by="operator-test",
    )

    assert first["status"] == WRITTEN_STATUS
    assert _snapshot(tmp_path) == before_second
    assert second["ok"] is False
    assert second["status"] == BLOCKED_STATUS
    assert "real_exact_once_marker_absent" in second["blockers"]
    assert "Workflow Pack exact-once marker already exists." in second["blockers"]
    assert second["writes_performed"] is False


def test_approval_marker_reservation_blocks_tampered_artifact_without_marker(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="approved")
    artifact_path = tmp_path / setup["approval_artifact_path"]
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["approval_scope"] = "all_workflow_pack_gates"
    artifact_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    before = _snapshot(tmp_path)

    report = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        reserve_marker=True,
        operator_statement="RESERVE WORKFLOW PACK EXACT-ONCE MARKER ONLY: wrong wrong",
    )

    assert _snapshot(tmp_path) == before
    assert report["ok"] is False
    assert report["status"] == BLOCKED_STATUS
    assert "approval_scope_one_gate" in report["blockers"]
    assert report["summary"]["exact_once_marker_reserved"] is False
    assert report["writes_performed"] is False


def test_approval_marker_reservation_can_reserve_rejection_marker_without_resume(tmp_path: Path) -> None:
    setup = _write_review_artifact(tmp_path, decision="rejected")
    preview = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="rejected",
    )

    report = build_approval_marker_reservation(
        tmp_path,
        run_id=setup["run_id"],
        gate_id=setup["gate_id"],
        request_digest=setup["request_digest"],
        approval_artifact_path=setup["approval_artifact_path"],
        expected_decision="rejected",
        reserve_marker=True,
        operator_statement=preview["exact_once_marker"]["required_operator_statement"],
        reserved_by="operator-test",
    )
    marker_payload = json.loads((tmp_path / report["exact_once_marker"]["path"]).read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["status"] == WRITTEN_STATUS
    assert report["summary"]["future_single_workflow_pack_gate_approved"] is False
    assert report["summary"]["future_single_workflow_pack_gate_rejected"] is True
    assert report["summary"]["approval_decision_consumed"] is False
    assert report["summary"]["resume_execution_performed"] is False
    assert marker_payload["operator_decision"] == "rejected"
    assert marker_payload["exact_once_marker_reserved"] is True
    assert marker_payload["resume_execution_performed"] is False


def _write_review_artifact(tmp_path: Path, *, decision: str) -> dict[str, str]:
    result = create_agent_governance_run(tmp_path, title=f"Marker reservation {decision}")
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
