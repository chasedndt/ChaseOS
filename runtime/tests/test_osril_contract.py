from __future__ import annotations

import json
from pathlib import Path

from runtime.osril.contract import OSRILEvent, OSRILEventType
from runtime.osril.approvals import (
    ApprovalResponseError,
    find_pending_approvals,
    record_approval_response,
    read_approval_application,
    read_approval_response,
)
from runtime.osril.inspector import get_session_detail, list_events, list_sessions
from runtime.osril.session import append_event, create_session, read_session, read_session_events


def test_osril_event_validates_known_event_families() -> None:
    event = OSRILEvent(
        session_id="sess-1",
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        event_type=OSRILEventType.TASK_STARTED,
        timestamp="2026-04-26T12:00:00Z",
        state="working",
        payload={"permission_ceiling": "tier-2"},
    )

    assert event.validate() == []
    assert event.to_dict()["event_type"] == "task_started"


def test_osril_event_rejects_invalid_approval_required_shape() -> None:
    event = OSRILEvent(
        session_id="sess-1",
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        event_type=OSRILEventType.APPROVAL_REQUIRED,
        timestamp="2026-04-26T12:00:00Z",
        state="waiting_approval",
        payload={},
    )

    errors = event.validate()
    assert any("approval_id" in err for err in errors)


def test_osril_event_validates_approval_response_shape() -> None:
    event = OSRILEvent(
        session_id="sess-1",
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        event_type=OSRILEventType.APPROVAL_RESPONSE,
        timestamp="2026-04-26T12:00:00Z",
        state="working",
        payload={
            "approval_id": "appr-1",
            "response_id": "resp-1",
            "decision": "APPROVE",
        },
    )

    assert event.validate() == []
    assert event.to_dict()["event_type"] == "approval_response"


def test_osril_session_store_persists_snapshot_and_events(tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
    )

    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.STATUS,
            timestamp="2026-04-26T12:00:00Z",
            state="working",
            payload={"stage": "workflow_lookup"},
        ),
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.TASK_COMPLETE,
            timestamp="2026-04-26T12:00:01Z",
            state="complete",
            payload={"terminal_status": "success"},
        ),
    )

    snapshot = read_session(tmp_path, session.session_id)
    assert snapshot is not None
    assert snapshot.latest_event_type == "task_complete"
    assert snapshot.event_count == 2
    assert snapshot.status == "complete"

    events = read_session_events(tmp_path, session.session_id)
    assert [item.event_type.value for item in events] == ["status", "task_complete"]

    session_path = tmp_path / "runtime" / "osril" / "run" / f"{session.session_id}.session.json"
    stored = json.loads(session_path.read_text(encoding="utf-8"))
    assert stored["runtime_id"] == "hermes"


def test_osril_inspector_lists_sessions_and_events(tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        timestamp="2026-04-26T12:00:00Z",
        session_id="sess-1",
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.TASK_STARTED,
            timestamp="2026-04-26T12:00:01Z",
            state="working",
            permission_ceiling="tier-2",
            payload={},
        ),
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.APPROVAL_REQUIRED,
            timestamp="2026-04-26T12:00:02Z",
            state="waiting_approval",
            payload={"approval_id": "appr-1"},
        ),
    )

    sessions = list_sessions(tmp_path, runtime_id="hermes")
    assert sessions["count"] == 1
    assert sessions["sessions"][0]["session_id"] == "sess-1"
    assert sessions["sessions"][0]["status"] == "waiting_approval"

    detail = get_session_detail(tmp_path, "sess-1")
    assert detail["session"]["workflow_id"] == "operator_today"
    assert detail["event_count"] == 2

    events = list_events(tmp_path, session_id="sess-1", event_type="approval_required")
    assert events["count"] == 1
    assert events["events"][0]["payload"]["approval_id"] == "appr-1"


def test_osril_inspector_missing_session_fails_closed(tmp_path: Path) -> None:
    try:
        get_session_detail(tmp_path, "missing-session")
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("missing OSRIL session should fail closed")


def test_osril_approval_response_records_are_immutable_and_remove_pending(tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        timestamp="2026-04-26T12:00:00Z",
        session_id="sess-approval",
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.APPROVAL_REQUIRED,
            timestamp="2026-04-26T12:00:01Z",
            state="waiting_approval",
            payload={"approval_id": "appr-1", "reason": "test approval"},
        ),
    )

    pending = find_pending_approvals(tmp_path)
    assert [item["approval_id"] for item in pending] == ["appr-1"]

    response = record_approval_response(
        tmp_path,
        approval_id="appr-1",
        decision="approve",
        operator_id="chase",
        operator_note="approved in test",
    )

    assert response["decision"] == "APPROVE"
    assert response["operator_id"] == "chase"
    assert response["applied_to_execution"] is True
    assert response["application_status"] == "recorded_in_osril_session"
    assert response["resume_executed"] is False
    assert read_approval_response(tmp_path, "appr-1")["response_id"] == response["response_id"]
    assert read_approval_response(tmp_path, "appr-1")["applied_to_execution"] is True
    raw_response = json.loads(
        (tmp_path / "runtime" / "osril" / "approvals" / "appr-1.response.json").read_text(
            encoding="utf-8"
        )
    )
    assert raw_response["applied_to_execution"] is False
    application = read_approval_application(tmp_path, "appr-1")
    assert application is not None
    assert application["applied_event_id"] == response["applied_event_id"]
    assert find_pending_approvals(tmp_path) == []
    snapshot = read_session(tmp_path, "sess-approval")
    assert snapshot is not None
    assert snapshot.latest_event_type == "approval_response"
    assert snapshot.status == "active"
    events = read_session_events(tmp_path, "sess-approval")
    assert [item.event_type.value for item in events] == ["approval_required", "approval_response"]
    assert events[-1].payload["resume_executed"] is False

    try:
        record_approval_response(
            tmp_path,
            approval_id="appr-1",
            decision="deny",
            operator_id="chase",
        )
    except ApprovalResponseError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate approval response should fail closed")


def test_osril_approval_response_denial_halts_session(tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        timestamp="2026-04-26T12:00:00Z",
        session_id="sess-denial",
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.APPROVAL_REQUIRED,
            timestamp="2026-04-26T12:00:01Z",
            state="waiting_approval",
            payload={"approval_id": "appr-deny"},
        ),
    )

    response = record_approval_response(
        tmp_path,
        approval_id="appr-deny",
        decision="deny",
        operator_id="chase",
    )

    assert response["decision"] == "DENY"
    assert response["applied_to_execution"] is True
    snapshot = read_session(tmp_path, "sess-denial")
    assert snapshot is not None
    assert snapshot.latest_event_type == "approval_response"
    assert snapshot.status == "halted"


def test_osril_approval_response_rejects_orphan_and_unsafe_ids(tmp_path: Path) -> None:
    try:
        record_approval_response(
            tmp_path,
            approval_id="missing",
            decision="approve",
            operator_id="chase",
        )
    except ApprovalResponseError as exc:
        assert "no matching pending" in str(exc)
    else:
        raise AssertionError("orphan approval response should fail closed")

    try:
        record_approval_response(
            tmp_path,
            approval_id="../unsafe",
            decision="approve",
            operator_id="chase",
        )
    except ApprovalResponseError as exc:
        assert "may only contain" in str(exc)
    else:
        raise AssertionError("unsafe approval_id should fail closed")
