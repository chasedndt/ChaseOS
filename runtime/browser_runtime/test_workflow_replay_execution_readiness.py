"""Tests for read-only workflow replay execution readiness preflight."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_execution_readiness as readiness_module
from runtime.browser_runtime.workflow_replay_execution_readiness import (
    WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED,
    WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_AVAILABLE,
    WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_SELECTED,
    WORKFLOW_REPLAY_EXECUTION_READINESS_READY,
    WorkflowReplayExecutionReadinessRequest,
    build_workflow_replay_execution_readiness,
    main as readiness_main,
)


def _write_cache_metadata(root: Path, workflows: list[dict[str, object]] | None = None) -> None:
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
                "workflows": workflows or [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_reviewed_replay_entry(root: Path, *, workflow_id: str = "wf_example_trial") -> Path:
    entry_path = root / "runtime" / "browser_workflows" / "workflows" / f"{workflow_id}.workflow.json"
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "record_type": "browser_workflow_cache_entry",
        "schema_version": "browser.workflow_cache.v1",
        "workflow_id": workflow_id,
        "domain": "example.com",
        "intent": "inspect demo page",
        "source_run_id": "safe-run",
        "source_run_log_path": "07_LOGS/Browser-Runs/safe-run.json",
        "status": "reviewed_for_trial",
        "allowed_domains": ["example.com"],
        "source_url": "https://example.com/demo",
        "steps": [
            {
                "step_id": "step_01_open",
                "action_type": "open",
                "target": "https://example.com/demo",
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
        "activation_allowed": False,
        "replay_allowed": True,
        "trusted_write_allowed": False,
        "external_code_copied": False,
    }
    entry_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    _write_cache_metadata(
        root,
        workflows=[
            {
                "workflow_id": workflow_id,
                "domain": "example.com",
                "status": "reviewed_for_trial",
                "path": entry_path.as_posix(),
                "activation_allowed": False,
                "replay_allowed": True,
            }
        ],
    )
    return entry_path


def test_module_does_not_import_browser_or_external_workflow_surfaces() -> None:
    source = inspect.getsource(readiness_module)
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


def test_missing_cache_blocks_without_writes(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    result = build_workflow_replay_execution_readiness(
        tmp_path,
        generated_at="2026-05-02T17:00:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED
    assert "cache_foundation_ready" in result.blockers
    assert result.workflow_replay_attempted is False
    assert result.browser_launch_attempted is False


def test_empty_cache_reports_no_reviewed_workflow_available(tmp_path: Path) -> None:
    _write_cache_metadata(tmp_path)

    result = build_workflow_replay_execution_readiness(
        tmp_path,
        generated_at="2026-05-02T17:05:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_AVAILABLE
    assert result.workflow_count == 0
    assert result.reviewed_replay_workflow_ids == []
    assert result.next_step == "create_reviewed_local_workflow_trial_candidate"
    assert result.execution_allowed is False


def test_reviewed_workflow_available_still_requires_selection(tmp_path: Path) -> None:
    _write_reviewed_replay_entry(tmp_path)

    result = build_workflow_replay_execution_readiness(
        tmp_path,
        generated_at="2026-05-02T17:10:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_SELECTED
    assert result.reviewed_replay_workflow_ids == ["wf_example_trial"]
    assert "workflow_selected" in result.blockers
    assert result.workflow_replay_attempted is False


def test_selected_reviewed_workflow_is_ready_no_execution(tmp_path: Path) -> None:
    _write_reviewed_replay_entry(tmp_path)

    result = build_workflow_replay_execution_readiness(
        tmp_path,
        WorkflowReplayExecutionReadinessRequest(
            workflow_id="wf_example_trial",
            target_url="https://example.com/demo",
            allowed_domains=["example.com"],
        ),
        generated_at="2026-05-02T17:15:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_READINESS_READY
    assert result.executor_status == "workflow_replay_executor_ready_no_execution"
    assert result.execution_allowed is False
    assert result.workflow_replay_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.next_step == "request_separate_live_workflow_replay_execution_approval"


def test_live_replay_request_remains_blocked(tmp_path: Path) -> None:
    _write_reviewed_replay_entry(tmp_path)

    result = build_workflow_replay_execution_readiness(
        tmp_path,
        WorkflowReplayExecutionReadinessRequest(
            workflow_id="wf_example_trial",
            target_url="https://example.com/demo",
            allowed_domains=["example.com"],
            request_live_replay=True,
        ),
        generated_at="2026-05-02T17:20:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED
    assert "live_replay_not_requested" in result.blockers
    assert result.execution_allowed is False
    assert result.workflow_replay_attempted is False


def test_validate_rejects_side_effect_flags(tmp_path: Path) -> None:
    _write_reviewed_replay_entry(tmp_path)
    result = build_workflow_replay_execution_readiness(
        tmp_path,
        WorkflowReplayExecutionReadinessRequest(
            workflow_id="wf_example_trial",
            target_url="https://example.com/demo",
            allowed_domains=["example.com"],
        ),
    )
    payload = result.as_dict()
    payload["request"] = result.request
    payload["browser_launch_attempted"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "browser_launch_attempted" in str(exc)
    else:
        raise AssertionError("browser side effect should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _write_cache_metadata(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = readiness_main(["--vault-root", str(tmp_path), "--json"])

    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_AVAILABLE
    assert payload["workflow_replay_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["execution_allowed"] is False
