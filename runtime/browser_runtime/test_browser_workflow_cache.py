"""Tests for the ChaseOS-native browser workflow cache foundation."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflows as workflow_module
from runtime.browser_runtime.models import (
    BrowserActionRecord,
    BrowserRunResult,
    BrowserRuntimeProvider,
)
from runtime.browser_runtime.workflows import (
    WORKFLOW_CACHE_SCHEMA_VERSION,
    build_empty_workflow_cache_metadata,
    main as workflow_cache_main,
    summarize_workflow_cache,
    validate_workflow_cache_entry,
    workflow_entry_from_run,
    write_workflow_cache_entry,
)


def _safe_result() -> BrowserRunResult:
    return BrowserRunResult(
        run_id="workflow_cache_safe_run",
        status="succeeded",
        provider=BrowserRuntimeProvider.SHADOW,
        mode="shadow",
        url="https://example.com/demo",
        task="inspect demo page",
        browser_run_log_path="07_LOGS/Browser-Runs/workflow_cache_safe_run.json",
        actions=[
            BrowserActionRecord(action_type="open", target="https://example.com/demo", status="succeeded"),
            BrowserActionRecord(action_type="read_state", target="document", status="succeeded"),
            BrowserActionRecord(action_type="form_submit", target="#danger", status="blocked"),
        ],
        security_flags={
            "real_profile_used": False,
            "credentials_used": False,
            "cookies_exported": False,
            "canonical_writeback": False,
            "browser_harness_used": False,
            "browser_use_cli_used": False,
        },
    )


def test_module_does_not_import_external_workflow_or_browser_surfaces() -> None:
    source = inspect.getsource(workflow_module)
    forbidden_tokens = (
        "import workflow_use",
        "from workflow_use",
        "import browser_use",
        "from browser_use",
        "workflow_use",
        "browser-harness",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "playwright",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_empty_metadata_shape_is_inactive() -> None:
    metadata = build_empty_workflow_cache_metadata(generated_at="2026-05-02T10:00:00Z")

    assert metadata["schema_version"] == WORKFLOW_CACHE_SCHEMA_VERSION
    assert metadata["activation_allowed"] is False
    assert metadata["replay_allowed"] is False
    assert metadata["trusted_write_allowed"] is False
    assert metadata["external_code_copied"] is False
    assert metadata["workflows"] == []


def test_summary_is_read_only_when_metadata_missing(tmp_path: Path) -> None:
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    summary = summarize_workflow_cache(tmp_path)
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert summary["status"] == "cache_metadata_missing"
    assert summary["workflow_count"] == 0
    assert summary["browser_launch_attempted"] is False
    assert summary["canonical_writeback_attempted"] is False


def test_workflow_entry_from_run_filters_forbidden_actions_and_stays_inactive() -> None:
    result = _safe_result()
    entry = workflow_entry_from_run(result)
    validation = validate_workflow_cache_entry(entry, source_security_flags=result.security_flags)

    assert validation.ok is True
    assert entry.domain == "example.com"
    assert entry.activation_allowed is False
    assert entry.replay_allowed is False
    assert entry.external_code_copied is False
    assert [step.action_type for step in entry.steps] == ["open", "read_state"]


def test_validation_blocks_unsafe_source_security_flags() -> None:
    result = _safe_result()
    entry = workflow_entry_from_run(result)
    validation = validate_workflow_cache_entry(entry, source_security_flags={"real_profile_used": True})

    assert validation.ok is False
    assert "forbidden_source_security_flag:real_profile_used" in validation.errors


def test_write_workflow_cache_entry_writes_inactive_entry_and_metadata(tmp_path: Path) -> None:
    result = _safe_result()
    entry = workflow_entry_from_run(result)

    entry_path, metadata_path = write_workflow_cache_entry(
        entry,
        root=tmp_path,
        source_security_flags=result.security_flags,
    )

    entry_record = json.loads(Path(entry_path).read_text(encoding="utf-8"))
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))

    assert entry_record["record_type"] == "browser_workflow_cache_entry"
    assert entry_record["activation_allowed"] is False
    assert entry_record["replay_allowed"] is False
    assert metadata["status"] == "inactive_review_cache"
    assert metadata["workflows"][0]["workflow_id"] == entry.workflow_id
    assert metadata["workflows"][0]["activation_allowed"] is False
    assert metadata["workflows"][0]["replay_allowed"] is False


def test_cli_summary_json_is_read_only(tmp_path: Path) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = workflow_cache_main(["--vault-root", str(tmp_path), "--json"])

    payload = json.loads(buffer.getvalue())

    assert exit_code == 0
    assert payload["record_type"] == "browser_workflow_cache_status"
    assert payload["activation_allowed"] is False
    assert payload["replay_allowed"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["provider_call_attempted"] is False
