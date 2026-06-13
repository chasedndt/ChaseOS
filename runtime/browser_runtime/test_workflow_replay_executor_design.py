"""Tests for Browser Workflow replay executor design preflight."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_executor_design as design_module
from runtime.browser_runtime.workflow_replay_executor_design import (
    WORKFLOW_REPLAY_EXECUTOR_STATUS_BLOCKED,
    WORKFLOW_REPLAY_EXECUTOR_STATUS_READY,
    build_workflow_replay_executor_design,
    main as design_main,
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


def test_module_does_not_import_external_replay_or_browser_surfaces() -> None:
    source = inspect.getsource(design_module)
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


def test_design_blocks_when_cache_foundation_missing_without_writes(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    design = build_workflow_replay_executor_design(tmp_path, generated_at="2026-05-02T11:20:00Z")
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert design.status == WORKFLOW_REPLAY_EXECUTOR_STATUS_BLOCKED
    assert design.external_code_copied is False
    assert design.workflow_use_reference_only is True
    assert design.forbidden_effects["workflow_replay_attempted"] is False
    assert design.forbidden_effects["browser_launch_attempted"] is False


def test_design_ready_when_cache_foundation_exists_but_replay_stays_forbidden(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)

    design = build_workflow_replay_executor_design(tmp_path, generated_at="2026-05-02T11:21:00Z")

    assert design.status == WORKFLOW_REPLAY_EXECUTOR_STATUS_READY
    assert design.implementation_strategy == "chaseos_native_aor_siteops_executor_no_external_code_copy"
    assert "start_isolated_browser_context_only_after_explicit_approval" in design.future_executor_sequence
    assert "workflow_entry_not_reviewed_or_not_selected" in design.stop_conditions
    assert all(value is False for value in design.forbidden_effects.values())


def test_validate_rejects_authority_flags(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)
    design = build_workflow_replay_executor_design(tmp_path)
    payload = design.as_dict()
    payload["forbidden_effects"]["workflow_replay_attempted"] = True

    try:
        type(design)(**payload).validate()
    except ValueError as exc:
        assert "workflow_replay_attempted" in str(exc)
    else:
        raise AssertionError("authority flag should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _seed_cache_foundation(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = design_main(["--vault-root", str(tmp_path), "--json"])

    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_EXECUTOR_STATUS_READY
    assert payload["external_code_copied"] is False
    assert payload["workflow_use_reference_only"] is True
    assert payload["forbidden_effects"]["canonical_writeback_attempted"] is False
