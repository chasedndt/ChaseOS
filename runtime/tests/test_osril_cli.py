from __future__ import annotations

import json
from pathlib import Path

from runtime.cli import main as cli
from runtime.osril.contract import OSRILEvent, OSRILEventType
from runtime.osril.session import append_event, create_session, read_session_events


def test_osril_sessions_cli_lists_session_json(capsys, tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="hermes",
        workflow_id="operator_today",
        timestamp="2026-04-26T12:00:00Z",
        session_id="sess-cli",
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="hermes",
            workflow_id="operator_today",
            event_type=OSRILEventType.STATUS,
            timestamp="2026-04-26T12:00:01Z",
            state="working",
            payload={"stage": "test"},
        ),
    )

    exit_code = cli.main([
        "osril",
        "sessions",
        "--runtime",
        "hermes",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "osril.sessions"
    assert payload["result"]["count"] == 1
    assert payload["result"]["sessions"][0]["session_id"] == "sess-cli"


def test_osril_events_cli_filters_by_event_type(capsys, tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="openclaw",
        workflow_id="review",
        timestamp="2026-04-26T12:00:00Z",
        session_id="sess-events",
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="openclaw",
            workflow_id="review",
            event_type=OSRILEventType.TASK_COMPLETE,
            timestamp="2026-04-26T12:00:01Z",
            state="complete",
            payload={"terminal_status": "success"},
        ),
    )

    exit_code = cli.main([
        "osril",
        "events",
        "--session",
        "sess-events",
        "--type",
        "task_complete",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "osril.events"
    assert payload["result"]["count"] == 1
    assert payload["result"]["events"][0]["event_type"] == "task_complete"


def test_osril_approvals_cli_lists_pending_and_records_response(capsys, tmp_path: Path) -> None:
    session = create_session(
        vault_root=tmp_path,
        run_id="run-1",
        runtime_id="openclaw",
        workflow_id="review",
        timestamp="2026-04-26T12:00:00Z",
        session_id="sess-approval-cli",
    )
    append_event(
        vault_root=tmp_path,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="openclaw",
            workflow_id="review",
            event_type=OSRILEventType.APPROVAL_REQUIRED,
            timestamp="2026-04-26T12:00:01Z",
            state="waiting_approval",
            payload={"approval_id": "appr-cli"},
        ),
    )

    exit_code = cli.main([
        "osril",
        "approvals",
        "--runtime",
        "openclaw",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "osril.approvals"
    assert payload["result"]["pending_count"] == 1
    assert payload["result"]["pending"][0]["approval_id"] == "appr-cli"

    exit_code = cli.main([
        "osril",
        "respond",
        "appr-cli",
        "--decision",
        "approve",
        "--operator",
        "chase",
        "--runtime",
        "openclaw",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "osril.respond"
    assert payload["result"]["decision"] == "APPROVE"
    assert payload["result"]["operator_id"] == "chase"
    assert payload["result"]["applied_to_execution"] is True
    assert payload["result"]["application_status"] == "recorded_in_osril_session"
    assert payload["result"]["resume_executed"] is False
    events = read_session_events(tmp_path, "sess-approval-cli")
    assert [item.event_type.value for item in events] == ["approval_required", "approval_response"]

    exit_code = cli.main([
        "osril",
        "respond",
        "appr-cli",
        "--decision",
        "deny",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "already exists" in payload["errors"][0]
