"""Tests for no-write workflow replay execution approval/idempotency contract."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_execution_approval as approval_module
from runtime.browser_runtime.workflow_replay_execution_approval import (
    WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED,
    WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS,
    WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY,
    WorkflowReplayExecutionApprovalRequest,
    build_workflow_replay_execution_approval,
    main as approval_main,
)


def _write_cache_metadata(root: Path, workflow_id: str, entry_path: Path) -> None:
    metadata_path = root / "runtime" / "browser_workflows" / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "record_type": "browser_workflow_cache_metadata",
                "schema_version": "browser.workflow_cache.v1",
                "status": "inactive_review_cache",
                "activation_allowed": False,
                "replay_allowed": False,
                "trusted_write_allowed": False,
                "external_code_copied": False,
                "workflows": [
                    {
                        "workflow_id": workflow_id,
                        "domain": "127.0.0.1",
                        "status": "reviewed_for_trial",
                        "path": entry_path.as_posix(),
                        "activation_allowed": False,
                        "replay_allowed": True,
                        "trusted_write_allowed": False,
                        "external_code_copied": False,
                        "trial_candidate": True,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_reviewed_local_entry(root: Path, *, workflow_id: str = "wf_local_trial") -> Path:
    entry_path = root / "runtime" / "browser_workflows" / "workflows" / f"{workflow_id}.workflow.json"
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "record_type": "browser_workflow_cache_entry",
        "schema_version": "browser.workflow_cache.v1",
        "workflow_id": workflow_id,
        "domain": "127.0.0.1",
        "intent": "local safe workflow trial",
        "source_run_id": "safe-run",
        "source_run_log_path": "07_LOGS/Browser-Runs/safe-run.json",
        "status": "reviewed_for_trial",
        "allowed_domains": ["127.0.0.1"],
        "source_url": "http://127.0.0.1:8770/",
        "steps": [
            {
                "step_id": "step_01_open",
                "action_type": "open",
                "target": "http://127.0.0.1:8770/",
                "status": "succeeded",
                "source_action_index": 0,
            },
            {
                "step_id": "step_02_read_state",
                "action_type": "read_state",
                "target": "document",
                "status": "succeeded",
                "source_action_index": 1,
            },
        ],
        "review_required": True,
        "activation_allowed": False,
        "replay_allowed": True,
        "trusted_write_allowed": False,
        "external_code_copied": False,
    }
    entry_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    _write_cache_metadata(root, workflow_id, entry_path)
    return entry_path


def test_module_does_not_import_browser_or_external_workflow_surfaces() -> None:
    source = inspect.getsource(approval_module)
    forbidden_tokens = (
        "import workflow_use",
        "from workflow_use",
        "import browser_use",
        "from browser_use",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "playwright",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_missing_readiness_blocks_without_writes(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    result = build_workflow_replay_execution_approval(
        tmp_path,
        WorkflowReplayExecutionApprovalRequest(
            workflow_id="wf_missing",
            target_url="http://127.0.0.1:8770/",
            allowed_domains=["127.0.0.1"],
        ),
        generated_at="2026-05-02T21:00:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED
    assert "readiness_ready_no_execution" in result.blockers
    assert result.approval_request_written is False
    assert result.idempotency_marker_written is False
    assert result.workflow_replay_attempted is False
    assert result.browser_launch_attempted is False


def test_selected_local_workflow_builds_ready_contract_without_writes(tmp_path: Path) -> None:
    _write_reviewed_local_entry(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    result = build_workflow_replay_execution_approval(
        tmp_path,
        WorkflowReplayExecutionApprovalRequest(
            workflow_id="wf_local_trial",
            target_url="http://127.0.0.1:8770/",
            allowed_domains=["127.0.0.1"],
            requested_by="Codex",
            operator_id="operator-review",
        ),
        generated_at="2026-05-02T21:05:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY
    assert result.readiness_status == "workflow_replay_execution_readiness_ready_no_execution"
    assert result.executor_status == "workflow_replay_executor_ready_no_execution"
    assert result.approval_request_preview["status"] == "pending_preview_not_written"
    assert result.approval_request_preview["operator_id"] == "operator-review"
    assert result.idempotency_marker_contract["marker_written"] is False
    assert result.execution_allowed is False
    assert result.workflow_replay_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.real_profile_access_attempted is False
    assert result.credential_or_cookie_read_attempted is False
    assert result.trusted_skill_write_attempted is False
    assert result.canonical_writeback_attempted is False


def test_contract_is_stable_for_same_workflow_target_and_requester(tmp_path: Path) -> None:
    _write_reviewed_local_entry(tmp_path)
    request = WorkflowReplayExecutionApprovalRequest(
        workflow_id="wf_local_trial",
        target_url="http://127.0.0.1:8770/",
        allowed_domains=["127.0.0.1"],
        requested_by="Codex",
    )

    first = build_workflow_replay_execution_approval(
        tmp_path,
        request,
        generated_at="2026-05-02T21:10:00Z",
    )
    second = build_workflow_replay_execution_approval(
        tmp_path,
        request,
        generated_at="2026-05-02T21:11:00Z",
    )

    assert first.approval_request_id == second.approval_request_id
    assert first.request_digest_sha256 == second.request_digest_sha256
    assert first.idempotency_marker_path == second.idempotency_marker_path


def test_nonlocal_target_is_blocked(tmp_path: Path) -> None:
    _write_reviewed_local_entry(tmp_path)

    result = build_workflow_replay_execution_approval(
        tmp_path,
        WorkflowReplayExecutionApprovalRequest(
            workflow_id="wf_local_trial",
            target_url="https://example.com/",
            allowed_domains=["example.com"],
        ),
        generated_at="2026-05-02T21:15:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED
    assert "target_domain_local_only" in result.blockers
    assert result.execution_allowed is False
    assert result.workflow_replay_attempted is False


def test_existing_idempotency_marker_blocks_duplicate_attempt(tmp_path: Path) -> None:
    _write_reviewed_local_entry(tmp_path)
    request = WorkflowReplayExecutionApprovalRequest(
        workflow_id="wf_local_trial",
        target_url="http://127.0.0.1:8770/",
        allowed_domains=["127.0.0.1"],
    )
    first = build_workflow_replay_execution_approval(
        tmp_path,
        request,
        generated_at="2026-05-02T21:20:00Z",
    )
    marker = Path(first.idempotency_marker_path)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"reserved": true}\n', encoding="utf-8")

    second = build_workflow_replay_execution_approval(
        tmp_path,
        request,
        generated_at="2026-05-02T21:21:00Z",
    )

    assert second.status == WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS
    assert second.idempotency_marker_exists is True
    assert "idempotency_marker_absent" in second.blockers
    assert second.idempotency_marker_written is False
    assert second.workflow_replay_attempted is False


def test_validate_rejects_write_execution_or_marker_authority(tmp_path: Path) -> None:
    _write_reviewed_local_entry(tmp_path)
    result = build_workflow_replay_execution_approval(
        tmp_path,
        WorkflowReplayExecutionApprovalRequest(
            workflow_id="wf_local_trial",
            target_url="http://127.0.0.1:8770/",
            allowed_domains=["127.0.0.1"],
        ),
    )

    payload = result.as_dict()
    payload["request"] = result.request
    payload["approval_request_written"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "approval_request_written" in str(exc)
    else:
        raise AssertionError("approval request write should be rejected")

    payload = result.as_dict()
    payload["request"] = result.request
    payload["idempotency_marker_written"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "idempotency_marker_written" in str(exc)
    else:
        raise AssertionError("idempotency marker write should be rejected")

    payload = result.as_dict()
    payload["request"] = result.request
    payload["workflow_replay_attempted"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "workflow_replay_attempted" in str(exc)
    else:
        raise AssertionError("workflow replay attempt should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _write_reviewed_local_entry(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = approval_main(
            [
                "--vault-root",
                str(tmp_path),
                "--workflow-id",
                "wf_local_trial",
                "--target-url",
                "http://127.0.0.1:8770/",
                "--allowed-domain",
                "127.0.0.1",
                "--json",
            ]
        )

    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY
    assert payload["approval_request_written"] is False
    assert payload["idempotency_marker_written"] is False
    assert payload["execution_allowed"] is False
    assert payload["workflow_replay_attempted"] is False
    assert payload["browser_launch_attempted"] is False
