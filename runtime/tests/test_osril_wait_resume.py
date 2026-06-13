from __future__ import annotations

import json
import uuid
from pathlib import Path

from runtime.cli import main as cli
from runtime.aor.engine import AORRunResult
from runtime.osril.approvals import mark_approval_resume, record_approval_response
from runtime.osril.contract import OSRILEvent, OSRILEventType
import runtime.osril.resume_ready as resume_ready
from runtime.osril.session import append_event, create_session
from runtime.osril.wait_resume import build_wait_resume_state, wait_for_resume_state


ROOT = Path(__file__).resolve().parents[2]
SCRATCH_ROOT = ROOT / "runtime" / "osril" / "_tmp_wait_resume_tests"


def _vault_root() -> Path:
    path = SCRATCH_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _seed_pending(vault_root: Path, approval_id: str = "appr-wait") -> None:
    session = create_session(
        vault_root=vault_root,
        run_id="run-1",
        runtime_id="openclaw",
        workflow_id="review",
        timestamp="2026-04-28T10:00:00Z",
        session_id=f"sess-{approval_id}",
    )
    append_event(
        vault_root=vault_root,
        event=OSRILEvent(
            session_id=session.session_id,
            run_id="run-1",
            runtime_id="openclaw",
            workflow_id="review",
            event_type=OSRILEventType.APPROVAL_REQUIRED,
            timestamp="2026-04-28T10:00:01Z",
            state="waiting_approval",
            payload={"approval_id": approval_id},
        ),
    )


def test_wait_resume_state_tracks_pending_ready_and_resumed() -> None:
    vault_root = _vault_root()
    _seed_pending(vault_root)

    pending = build_wait_resume_state(vault_root)
    assert pending["waiting_count"] == 1
    assert pending["items"][0]["wait_status"] == "waiting_response"
    assert pending["items"][0]["response_command_hint"] == "chaseos osril respond appr-wait --decision approve"

    waiting_for_ready = wait_for_resume_state(
        vault_root,
        approval_id="appr-wait",
        wait_status="ready_to_resume",
        timeout_seconds=0.01,
        poll_interval_seconds=0.01,
    )
    assert waiting_for_ready["timed_out"] is True
    assert waiting_for_ready["count"] == 0
    assert waiting_for_ready["filters"]["wait_status"] == "ready_to_resume"

    record_approval_response(
        vault_root,
        approval_id="appr-wait",
        decision="approve",
        operator_id="chase",
    )
    ready = wait_for_resume_state(vault_root, approval_id="appr-wait", timeout_seconds=0)
    assert ready["item"]["wait_status"] == "ready_to_resume"
    assert ready["item"]["resume_command_hint"] == "chaseos run review --input operator_approval_ref=appr-wait"
    assert ready["ready_count"] == 1

    mark_approval_resume(
        vault_root,
        approval_id="appr-wait",
        resumed_session_id="sess-resumed",
        resumed_run_id="run-2",
        workflow_id="review",
        runtime_id="openclaw",
    )
    resumed = build_wait_resume_state(vault_root, approval_id="appr-wait")
    assert resumed["item"]["wait_status"] == "resumed"
    assert resumed["item"]["terminal"] is True
    assert resumed["resumed_count"] == 1


def test_wait_resume_state_tracks_denial_and_missing_approval() -> None:
    vault_root = _vault_root()
    _seed_pending(vault_root, approval_id="appr-deny")
    record_approval_response(
        vault_root,
        approval_id="appr-deny",
        decision="deny",
        operator_id="chase",
    )

    denied = build_wait_resume_state(vault_root, approval_id="appr-deny")
    assert denied["item"]["wait_status"] == "denied"
    assert denied["item"]["terminal"] is True
    assert denied["item"]["resume_command_hint"] is None

    missing = build_wait_resume_state(vault_root, approval_id="missing-approval")
    assert missing["item"]["wait_status"] == "not_found"
    assert missing["not_found_count"] == 1


def test_osril_wait_resume_cli_lists_ready_response(capsys) -> None:
    vault_root = _vault_root()
    _seed_pending(vault_root, approval_id="appr-cli-ready")
    record_approval_response(
        vault_root,
        approval_id="appr-cli-ready",
        decision="approve",
        operator_id="chase",
    )

    exit_code = cli.main([
        "osril",
        "wait-resume",
        "--status",
        "ready_to_resume",
        "--vault-root",
        str(vault_root),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "osril.wait-resume"
    assert payload["result"]["ready_count"] == 1
    assert payload["result"]["items"][0]["approval_id"] == "appr-cli-ready"

    exit_code = cli.main([
        "osril",
        "wait-resume",
        "appr-cli-ready",
        "--decision",
        "deny",
        "--vault-root",
        str(vault_root),
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"]["count"] == 0
    assert payload["result"]["filters"]["decision"] == "deny"


def test_resume_ready_approvals_runs_ready_items_once(monkeypatch) -> None:
    vault_root = _vault_root()
    _seed_pending(vault_root, approval_id="appr-resume")
    record_approval_response(
        vault_root,
        approval_id="appr-resume",
        decision="approve",
        operator_id="chase",
    )
    calls = []

    def fake_run_workflow(workflow_id, inputs, vault_root, runtime_id):
        calls.append(
            {
                "workflow_id": workflow_id,
                "inputs": inputs,
                "runtime_id": runtime_id,
            }
        )
        resume = mark_approval_resume(
            vault_root,
            approval_id=inputs["operator_approval_ref"],
            resumed_session_id="sess-resumed",
            resumed_run_id="run-resumed",
            workflow_id=workflow_id,
            runtime_id=runtime_id,
        )
        return AORRunResult(
            workflow_id=workflow_id,
            status="success",
            audit_id="run-resumed",
            stage_reached="writeback",
            outputs={
                "approval_gate": {
                    "approval_id": inputs["operator_approval_ref"],
                    "resume_executed": True,
                    "resume_id": resume["resume_id"],
                    "resume_path": resume["resume_path"],
                }
            },
        )

    monkeypatch.setattr(resume_ready, "run_workflow", fake_run_workflow)

    payload = resume_ready.resume_ready_approvals(vault_root)

    assert payload["ready_count"] == 1
    assert payload["attempted_count"] == 1
    assert payload["resumed_count"] == 1
    assert payload["failed_count"] == 0
    assert calls == [
        {
            "workflow_id": "review",
            "inputs": {"operator_approval_ref": "appr-resume"},
            "runtime_id": "openclaw",
        }
    ]
    resumed = build_wait_resume_state(vault_root, approval_id="appr-resume")
    assert resumed["item"]["wait_status"] == "resumed"


def test_osril_resume_ready_cli_dry_run_reports_planned_without_resume(capsys) -> None:
    vault_root = _vault_root()
    _seed_pending(vault_root, approval_id="appr-cli-plan")
    record_approval_response(
        vault_root,
        approval_id="appr-cli-plan",
        decision="approve",
        operator_id="chase",
    )

    exit_code = cli.main([
        "osril",
        "resume-ready",
        "--vault-root",
        str(vault_root),
        "--dry-run",
        "--json",
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "osril.resume-ready"
    assert payload["result"]["ready_count"] == 1
    assert payload["result"]["planned_count"] == 1
    assert payload["result"]["results"][0]["status"] == "planned"
    assert "operator_approval_ref=appr-cli-plan" in payload["result"]["results"][0]["command_hint"]
    ready = build_wait_resume_state(vault_root, approval_id="appr-cli-plan")
    assert ready["item"]["wait_status"] == "ready_to_resume"
