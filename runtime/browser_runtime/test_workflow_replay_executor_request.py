"""Tests for no-write workflow replay executor implementation request."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_executor_request as request_module
from runtime.browser_runtime.workflow_replay_executor_request import (
    WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_BLOCKED,
    WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY,
    build_workflow_replay_executor_implementation_request,
    main as request_main,
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
    source = inspect.getsource(request_module)
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


def test_request_blocks_when_design_preflight_is_not_ready_without_writes(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    request = build_workflow_replay_executor_implementation_request(
        tmp_path,
        generated_at="2026-05-02T11:45:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert request.status == WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_BLOCKED
    assert request.request_ready_no_write is False
    assert request.implementation_allowed_in_this_pass is False
    assert request.implementation_request_artifact_written is False
    assert request.denied_effects["workflow_replay_attempted"] is False


def test_request_ready_when_design_ready_but_implementation_stays_disabled(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)

    request = build_workflow_replay_executor_implementation_request(
        tmp_path,
        generated_at="2026-05-02T11:46:00Z",
    )

    assert request.status == WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY
    assert request.request_ready_no_write is True
    assert request.implementation_allowed_in_this_pass is False
    assert request.external_code_copied is False
    assert request.workflow_use_reference_only is True
    assert "runtime/browser_runtime/workflow_replay_executor.py" in request.proposed_patch_scope
    assert "--run-approved-workflow-replay" in request.future_write_flags_required
    assert all(value is False for value in request.denied_effects.values())


def test_validate_rejects_implementation_or_replay_authority(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)
    request = build_workflow_replay_executor_implementation_request(tmp_path)
    payload = request.as_dict()
    payload["implementation_allowed_in_this_pass"] = True

    try:
        type(request)(**payload).validate()
    except ValueError as exc:
        assert "implementation_allowed_in_this_pass" in str(exc)
    else:
        raise AssertionError("implementation authority should be rejected")

    payload = request.as_dict()
    payload["denied_effects"]["workflow_replay_attempted"] = True
    try:
        type(request)(**payload).validate()
    except ValueError as exc:
        assert "workflow_replay_attempted" in str(exc)
    else:
        raise AssertionError("replay authority should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = request_main(["--vault-root", str(tmp_path), "--json"])

    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY
    assert payload["implementation_allowed_in_this_pass"] is False
    assert payload["implementation_request_artifact_written"] is False
    assert payload["denied_effects"]["canonical_writeback_attempted"] is False
