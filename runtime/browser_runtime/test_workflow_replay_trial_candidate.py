"""Tests for local workflow replay trial-candidate selection."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_trial_candidate as trial_module
from runtime.browser_runtime.workflow_replay_execution_readiness import (
    WORKFLOW_REPLAY_EXECUTION_READINESS_READY,
    WorkflowReplayExecutionReadinessRequest,
    build_workflow_replay_execution_readiness,
)
from runtime.browser_runtime.workflow_replay_trial_candidate import (
    DEFAULT_WORKFLOW_ID,
    WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED,
    WORKFLOW_REPLAY_TRIAL_CANDIDATE_PREVIEW_READY,
    WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTED_EXISTING,
    WORKFLOW_REPLAY_TRIAL_CANDIDATE_WRITTEN,
    main as trial_main,
    select_or_write_trial_candidate,
)


def _safe_source_record() -> dict[str, object]:
    return {
        "record_type": "browser_run_log",
        "schema_version": "browser.run.v1",
        "run_id": "vincisos_product_ui_browser_proof_20260502_success",
        "status": "succeeded",
        "target": {
            "name": "ChaseOS Studio Product UI Test Target",
            "url": "http://127.0.0.1:8770/",
            "domain": "127.0.0.1",
            "contract": "vincisos.full_ui_target.v1",
            "target_kind": "product_ui",
            "mode": "shadow",
            "safe_mode_asserted": True,
        },
        "provider": "codex-in-app-browser",
        "provider_backend": "iab",
        "url": "http://127.0.0.1:8770/",
        "browser_state": {
            "post_action_status": "Panel inspected in safe mode.",
            "selector_counts": {
                "root": 1,
                "safe_mode_banner": 1,
                "panel_overview": 1,
                "panel_approvals": 1,
                "panel_workflow": 1,
                "tab_overview": 1,
                "tab_approvals": 1,
                "tab_workflow": 1,
                "task_table": 1,
                "approval_table": 1,
                "action_status": 1,
                "harmless_action": 1,
                "task_rows": 3,
                "approval_rows": 2,
            },
        },
        "provider_details": {
            "surface": "Codex in-app browser",
            "backend": "iab",
            "real_browser_profile_used": False,
            "browser_use_cli_used": False,
            "browser_harness_used": False,
            "cdp_used": False,
        },
        "actions": [
            {
                "index": 1,
                "action": "open",
                "target": "http://127.0.0.1:8770/",
                "result": "loaded",
                "evidence": "title: ChaseOS Studio Product UI Test Target",
            },
            {
                "index": 2,
                "action": "read_state",
                "target": "initial DOM snapshot",
                "result": "success",
                "evidence": "Runtime overview visible",
            },
            {
                "index": 3,
                "action": "harmless_click",
                "target": "Approvals tab",
                "result": "success",
                "evidence": "Approvals tab active",
            },
            {
                "index": 4,
                "action": "harmless_click",
                "target": "Workflow tab",
                "result": "success",
                "evidence": "Workflow tab active",
            },
            {
                "index": 5,
                "action": "harmless_click",
                "target": "Mark panel inspected button",
                "result": "success",
                "evidence": "Action status changed to Panel inspected in safe mode.",
            },
            {
                "index": 6,
                "action": "capture_screenshot",
                "target": "visible viewport",
                "result": "success",
                "evidence": "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png",
            },
        ],
        "artifacts": [
            {
                "artifact_type": "screenshot",
                "path": "07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png",
            }
        ],
        "governance": {
            "canonical_writeback": False,
            "skill_activation": False,
            "trusted_skill_write": False,
            "siteops_skill_card_write": False,
            "draft_skill_written": True,
            "untrusted_candidate_written": True,
            "real_profile_allowed": False,
            "real_profile_used": False,
            "credentials_allowed": False,
            "credentials_used": False,
            "cookies_exported": False,
            "browser_history_imported": False,
            "cdp_connection_used": False,
            "browser_harness_used": False,
            "browser_use_cli_used": False,
            "public_tunnel_used": False,
            "agent_bus_enqueue": False,
            "provider_call": False,
            "gate_policy_mutation": False,
        },
    }


def _write_source(root: Path, record: dict[str, object] | None = None) -> Path:
    path = root / "07_LOGS" / "Browser-Runs" / "safe_source.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record or _safe_source_record(), indent=2), encoding="utf-8")
    return path


def test_module_does_not_import_external_browser_or_workflow_surfaces() -> None:
    source = inspect.getsource(trial_module)
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


def test_preview_is_read_only(tmp_path: Path) -> None:
    source_path = _write_source(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    result = select_or_write_trial_candidate(
        tmp_path,
        source_run_log_path=source_path.as_posix(),
        generated_at="2026-05-02T20:15:00Z",
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_TRIAL_CANDIDATE_PREVIEW_READY
    assert result.workflow_id == DEFAULT_WORKFLOW_ID
    assert result.write_requested is False
    assert result.wrote_workflow_entry is False
    assert result.wrote_metadata is False
    assert result.workflow_replay_attempted is False
    assert result.browser_launch_attempted is False


def test_blocks_unsafe_source_governance(tmp_path: Path) -> None:
    record = _safe_source_record()
    governance = record["governance"]
    assert isinstance(governance, dict)
    governance["real_profile_used"] = True
    source_path = _write_source(tmp_path, record)

    result = select_or_write_trial_candidate(
        tmp_path,
        source_run_log_path=source_path.as_posix(),
        write_trial_candidate=True,
        generated_at="2026-05-02T20:16:00Z",
    )

    assert result.status == WORKFLOW_REPLAY_TRIAL_CANDIDATE_BLOCKED
    assert "forbidden_governance_flag:real_profile_used" in result.validation_errors
    assert result.wrote_workflow_entry is False
    assert result.wrote_metadata is False
    assert result.real_profile_access_attempted is False
    assert result.credential_or_cookie_read_attempted is False


def test_write_creates_reviewed_trial_candidate_and_metadata(tmp_path: Path) -> None:
    source_path = _write_source(tmp_path)

    result = select_or_write_trial_candidate(
        tmp_path,
        source_run_log_path=source_path.as_posix(),
        write_trial_candidate=True,
        generated_at="2026-05-02T20:17:00Z",
    )

    entry = json.loads((tmp_path / result.workflow_entry_path).read_text(encoding="utf-8"))
    metadata = json.loads((tmp_path / result.metadata_path).read_text(encoding="utf-8"))

    assert result.status == WORKFLOW_REPLAY_TRIAL_CANDIDATE_WRITTEN
    assert entry["record_type"] == "browser_workflow_cache_entry"
    assert entry["schema_version"] == "browser.workflow_cache.v1"
    assert entry["status"] == "reviewed_for_trial"
    assert entry["replay_allowed"] is True
    assert entry["activation_allowed"] is False
    assert entry["trusted_write_allowed"] is False
    assert entry["external_code_copied"] is False
    assert entry["allowed_domains"] == ["127.0.0.1"]
    assert [step["action_type"] for step in entry["steps"]] == [
        "open",
        "read_state",
        "harmless_click",
        "harmless_click",
        "harmless_click",
        "capture_screenshot",
    ]
    assert metadata["replay_allowed"] is False
    assert metadata["activation_allowed"] is False
    assert metadata["trusted_write_allowed"] is False
    assert metadata["workflows"][0]["replay_allowed"] is True
    assert metadata["workflows"][0]["trial_candidate"] is True


def test_write_is_idempotent_for_existing_valid_entry(tmp_path: Path) -> None:
    source_path = _write_source(tmp_path)
    first = select_or_write_trial_candidate(
        tmp_path,
        source_run_log_path=source_path.as_posix(),
        write_trial_candidate=True,
        generated_at="2026-05-02T20:18:00Z",
    )
    second = select_or_write_trial_candidate(
        tmp_path,
        source_run_log_path=source_path.as_posix(),
        write_trial_candidate=True,
        generated_at="2026-05-02T20:19:00Z",
    )

    assert first.status == WORKFLOW_REPLAY_TRIAL_CANDIDATE_WRITTEN
    assert second.status == WORKFLOW_REPLAY_TRIAL_CANDIDATE_SELECTED_EXISTING
    assert second.wrote_workflow_entry is False
    assert second.wrote_metadata is True
    assert second.selected_existing is True


def test_written_candidate_makes_readiness_ready_only_when_selected(tmp_path: Path) -> None:
    source_path = _write_source(tmp_path)
    result = select_or_write_trial_candidate(
        tmp_path,
        source_run_log_path=source_path.as_posix(),
        write_trial_candidate=True,
        generated_at="2026-05-02T20:20:00Z",
    )

    readiness = build_workflow_replay_execution_readiness(
        tmp_path,
        WorkflowReplayExecutionReadinessRequest(
            workflow_id=result.workflow_id,
            target_url="http://127.0.0.1:8770/",
            allowed_domains=["127.0.0.1"],
        ),
        generated_at="2026-05-02T20:21:00Z",
    )

    assert readiness.status == WORKFLOW_REPLAY_EXECUTION_READINESS_READY
    assert readiness.execution_allowed is False
    assert readiness.workflow_replay_attempted is False
    assert readiness.browser_launch_attempted is False
    assert readiness.reviewed_replay_workflow_ids == [DEFAULT_WORKFLOW_ID]


def test_cli_write_outputs_json_and_writes_candidate(tmp_path: Path) -> None:
    source_path = _write_source(tmp_path)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = trial_main(
            [
                "--vault-root",
                str(tmp_path),
                "--source-run-log",
                source_path.as_posix(),
                "--write-trial-candidate",
                "--json",
            ]
        )
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["status"] == WORKFLOW_REPLAY_TRIAL_CANDIDATE_WRITTEN
    assert (tmp_path / payload["workflow_entry_path"]).is_file()
    assert payload["workflow_replay_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
