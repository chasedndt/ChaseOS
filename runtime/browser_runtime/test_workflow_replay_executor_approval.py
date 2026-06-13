"""Tests for no-write workflow replay executor implementation approval."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_executor_approval as approval_module
from runtime.browser_runtime.workflow_replay_executor_approval import (
    WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_BLOCKED,
    WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_READY,
    WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_REJECTED,
    build_workflow_replay_executor_implementation_approval,
    main as approval_main,
)


def _seed_cache_foundation(root: Path) -> None:
    path = root / "runtime" / "browser_workflows" / "metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "record_type": "browser_workflow_cache_metadata",
                "schema_version": "browser.workflow_cache.v1",
                "status": "empty_initialized",
                "activation_allowed": False,
                "replay_allowed": False,
                "trusted_write_allowed": False,
                "external_code_copied": False,
                "workflows": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_module_does_not_import_external_executor_or_browser_surfaces() -> None:
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


def test_approval_blocks_when_request_is_not_ready_without_writes(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    approval = build_workflow_replay_executor_implementation_approval(
        tmp_path,
        decision="approve",
        generated_at="2026-05-02T12:10:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert approval.status == WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_BLOCKED
    assert approval.implementation_request_ready_no_write is False
    assert approval.implementation_approved_for_future_patch is False
    assert approval.implementation_allowed_in_this_pass is False
    assert approval.approval_artifact_written is False
    assert approval.replay_execution_allowed is False


def test_approval_ready_when_request_ready_but_implementation_stays_disabled(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)

    approval = build_workflow_replay_executor_implementation_approval(
        tmp_path,
        decision="approve",
        operator_id="operator-review",
        generated_at="2026-05-02T12:11:00Z",
    )

    assert approval.status == WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_READY
    assert approval.operator_id == "operator-review"
    assert approval.implementation_request_ready_no_write is True
    assert approval.implementation_approved_for_future_patch is True
    assert approval.implementation_allowed_in_this_pass is False
    assert approval.approval_artifact_written is False
    assert approval.replay_execution_allowed is False
    assert "runtime/browser_runtime/workflow_replay_executor.py" in approval.approved_patch_scope
    assert "--write-replay-implementation-approval" in approval.future_write_flags_required
    assert all(value is False for value in approval.denied_effects.values())


def test_reject_decision_does_not_approve_patch_scope(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)

    approval = build_workflow_replay_executor_implementation_approval(
        tmp_path,
        decision="reject",
        generated_at="2026-05-02T12:12:00Z",
    )

    assert approval.status == WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_REJECTED
    assert approval.implementation_request_ready_no_write is True
    assert approval.implementation_approved_for_future_patch is False
    assert approval.approved_patch_scope == []
    assert approval.implementation_allowed_in_this_pass is False
    assert approval.replay_execution_allowed is False


def test_validate_rejects_write_execution_or_replay_authority(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)
    approval = build_workflow_replay_executor_implementation_approval(tmp_path)

    payload = approval.as_dict()
    payload["approval_artifact_written"] = True
    try:
        type(approval)(**payload).validate()
    except ValueError as exc:
        assert "approval_artifact_written" in str(exc)
    else:
        raise AssertionError("approval artifact write should be rejected")

    payload = approval.as_dict()
    payload["implementation_allowed_in_this_pass"] = True
    try:
        type(approval)(**payload).validate()
    except ValueError as exc:
        assert "implementation_allowed_in_this_pass" in str(exc)
    else:
        raise AssertionError("implementation authority should be rejected")

    payload = approval.as_dict()
    payload["denied_effects"]["workflow_replay_attempted"] = True
    try:
        type(approval)(**payload).validate()
    except ValueError as exc:
        assert "workflow_replay_attempted" in str(exc)
    else:
        raise AssertionError("replay side effect should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = approval_main(["--vault-root", str(tmp_path), "--decision", "approve", "--json"])

    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_READY
    assert payload["implementation_approved_for_future_patch"] is True
    assert payload["implementation_allowed_in_this_pass"] is False
    assert payload["approval_artifact_written"] is False
    assert payload["replay_execution_allowed"] is False
    assert payload["denied_effects"]["canonical_writeback_attempted"] is False
