"""Tests for the disabled-by-default workflow replay executor."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_executor as executor_module
from runtime.browser_runtime.workflow_replay_executor import (
    WORKFLOW_REPLAY_EXECUTOR_BLOCKED,
    WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_EXECUTION,
    WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_WORKFLOW,
    WORKFLOW_REPLAY_EXECUTOR_EXECUTION_DEFERRED,
    WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION,
    WorkflowReplayExecutorRequest,
    build_workflow_replay_executor_result,
    main as executor_main,
)


def _write_entry(root: Path, *, workflow_id: str = "wf_example_reviewed", **overrides: object) -> None:
    entry = {
        "record_type": "browser_workflow_cache_entry",
        "schema_version": "browser.workflow_cache.v1",
        "workflow_id": workflow_id,
        "domain": "example.com",
        "intent": "inspect demo page",
        "source_run_id": "safe-run",
        "source_run_log_path": "07_LOGS/Browser-Runs/safe-run.json",
        "status": "reviewed_inactive",
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
    entry.update(overrides)
    entry_path = root / "runtime" / "browser_workflows" / "workflows" / f"{workflow_id}.workflow.json"
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")

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
                        "domain": "example.com",
                        "status": entry["status"],
                        "path": entry_path.as_posix(),
                        "activation_allowed": False,
                        "replay_allowed": entry["replay_allowed"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_module_does_not_import_external_executor_or_browser_surfaces() -> None:
    source = inspect.getsource(executor_module)
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


def test_executor_without_workflow_is_disabled_and_read_only(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(),
        generated_at="2026-05-02T12:30:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_WORKFLOW
    assert result.workflow_replay_attempted is False
    assert result.execution_allowed is False
    assert result.replay_artifacts_written is False


def test_executor_blocks_missing_workflow_without_writes(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(workflow_id="missing"),
        generated_at="2026-05-02T12:31:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTOR_BLOCKED
    assert "workflow_entry_found" in result.stop_reasons
    assert result.workflow_replay_attempted is False


def test_executor_blocks_unreviewed_or_inactive_entry(tmp_path: Path) -> None:
    _write_entry(tmp_path, workflow_id="wf_example_draft", status="draft_review_only", replay_allowed=False)

    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(workflow_id="wf_example_draft", target_url="https://example.com/demo"),
        generated_at="2026-05-02T12:32:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTOR_BLOCKED
    assert "workflow_entry_reviewed" in result.stop_reasons
    assert "workflow_entry_replay_allowed" in result.stop_reasons
    assert result.execution_allowed is False


def test_executor_blocks_allowed_domain_mismatch(tmp_path: Path) -> None:
    _write_entry(tmp_path)

    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(workflow_id="wf_example_reviewed", target_url="https://blocked.example/demo"),
        generated_at="2026-05-02T12:33:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTOR_BLOCKED
    assert "target_domain_allowed" in result.stop_reasons
    assert result.target_domain == "blocked.example"


def test_executor_validates_reviewed_entry_but_stays_disabled_by_default(tmp_path: Path) -> None:
    _write_entry(tmp_path)

    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(workflow_id="wf_example_reviewed", target_url="https://example.com/demo"),
        generated_at="2026-05-02T12:34:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_EXECUTION
    assert result.planned_steps[0].status == "planned_not_executed"
    assert result.executor_enabled is False
    assert result.workflow_replay_attempted is False
    assert all(value is False for value in result.denied_effects.values())


def test_executor_ready_no_execution_when_explicitly_enabled_without_run_flag(tmp_path: Path) -> None:
    _write_entry(tmp_path)

    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(
            workflow_id="wf_example_reviewed",
            target_url="https://example.com/demo",
            enable_replay_executor=True,
        ),
        generated_at="2026-05-02T12:35:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION
    assert result.execution_requested is False
    assert result.execution_allowed is False
    assert result.workflow_replay_attempted is False


def test_executor_blocks_live_run_flag_even_when_ready(tmp_path: Path) -> None:
    _write_entry(tmp_path)

    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(
            workflow_id="wf_example_reviewed",
            target_url="https://example.com/demo",
            enable_replay_executor=True,
            run_approved_workflow_replay=True,
        ),
        generated_at="2026-05-02T12:36:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTOR_EXECUTION_DEFERRED
    assert result.execution_requested is True
    assert result.execution_allowed is False
    assert result.workflow_replay_attempted is False
    assert "live_execution_deferred" in result.stop_reasons


def test_validate_rejects_side_effect_flags(tmp_path: Path) -> None:
    _write_entry(tmp_path)
    result = build_workflow_replay_executor_result(
        tmp_path,
        WorkflowReplayExecutorRequest(workflow_id="wf_example_reviewed", target_url="https://example.com/demo"),
    )

    payload = result.as_dict()
    payload["request"] = result.request
    payload["planned_steps"] = result.planned_steps
    payload["workflow_replay_attempted"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "workflow_replay_attempted" in str(exc)
    else:
        raise AssertionError("replay side effect should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _write_entry(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = executor_main(
            [
                "--vault-root",
                str(tmp_path),
                "--workflow-id",
                "wf_example_reviewed",
                "--target-url",
                "https://example.com/demo",
                "--json",
            ]
        )

    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_EXECUTION
    assert payload["workflow_replay_attempted"] is False
    assert payload["execution_allowed"] is False
    assert payload["replay_artifacts_written"] is False
