"""Tests for read-only Browser Runtime production closeout."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from runtime.browser_runtime.completion_estimate import build_browser_runtime_completion_estimate
from runtime.browser_runtime.completion_status import (
    BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED,
    BrowserRuntimeCompletionStatus,
)
from runtime.browser_runtime.production_closeout import (
    BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_RECORD_TYPE,
    BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS,
    BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_EXTERNAL_DEFERRED,
    build_browser_runtime_production_closeout,
    main as closeout_main,
    write_production_closeout_evidence,
)


def _status(*, production_done: bool = False) -> BrowserRuntimeCompletionStatus:
    return BrowserRuntimeCompletionStatus(
        generated_at="2026-05-04T12:00:00Z",
        overall_status=(
            "complete" if production_done else BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED
        ),
        bounded_mvp_done=True,
        production_feature_done=production_done,
        next_recommended_pass=(
            "browser-runtime-production-complete"
            if production_done
            else "excalidraw-local-browser-mcp-live-readiness-with-target"
        ),
        blocked_reasons=(
            ()
            if production_done
            else (
                "browser_use_cli_live_validation_blocked_unavailable",
                "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target",
                "excalidraw_live_browser_mcp_proof_not_run",
            )
        ),
        items=(),
    )


def _seed_native_panel_evidence(root: Path) -> None:
    for relative in (
        "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-native-shell-panel-static-qa.md",
        "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-qa-runner-static-qa.md",
        "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-browser-qa.md",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("evidence", encoding="utf-8")


def test_closeout_report_marks_internal_lane_complete_without_forbidden_effects(tmp_path: Path) -> None:
    _seed_native_panel_evidence(tmp_path)
    status = _status()
    estimate = build_browser_runtime_completion_estimate(
        tmp_path,
        generated_at="2026-05-04T12:01:00Z",
        completion_status=status,
    )

    report = build_browser_runtime_production_closeout(
        tmp_path,
        generated_at="2026-05-04T12:02:00Z",
        completion_status=status,
        completion_estimate=estimate,
    )
    payload = report.to_dict()

    assert payload["record_type"] == BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_RECORD_TYPE
    assert payload["status"] == BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_EXTERNAL_DEFERRED
    assert payload["bounded_mvp_done"] is True
    assert payload["production_feature_done"] is False
    assert payload["internal_studio_panel_lane_complete"] is True
    assert payload["remaining_internal_passes"] == []
    assert payload["external_deferred_lanes"] == [
        "browser-use-cli-live-validation",
        "excalidraw-target-and-readiness",
        "excalidraw-live-browser-mcp-proof",
    ]
    assert payload["remaining_major_passes_min"] == 3
    assert payload["remaining_major_passes_max"] == 6
    assert payload["browser_launch_attempted"] is False
    assert payload["browser_use_cli_live_used"] is False
    assert payload["excalidraw_live_proof_attempted"] is False
    assert payload["approval_execution_attempted"] is False
    assert payload["agent_bus_enqueue_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_closeout_report_marks_production_complete_when_all_lanes_are_done(tmp_path: Path) -> None:
    _seed_native_panel_evidence(tmp_path)
    status = _status(production_done=True)
    estimate = build_browser_runtime_completion_estimate(
        tmp_path,
        generated_at="2026-05-04T12:03:00Z",
        completion_status=status,
    )

    report = build_browser_runtime_production_closeout(
        tmp_path,
        generated_at="2026-05-04T12:04:00Z",
        completion_status=status,
        completion_estimate=estimate,
    )
    payload = report.to_dict()

    assert payload["status"] == BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS
    assert payload["production_feature_done"] is True
    assert payload["external_runtime_lanes_deferred"] is False
    assert payload["remaining_internal_passes"] == []
    assert payload["external_deferred_lanes"] == []
    assert payload["remaining_major_passes_min"] == 0
    assert payload["remaining_major_passes_max"] == 0
    assert payload["blocked_reasons"] == []


def test_closeout_blocks_when_native_panel_evidence_is_missing(tmp_path: Path) -> None:
    status = _status()
    estimate = build_browser_runtime_completion_estimate(
        tmp_path,
        generated_at="2026-05-04T12:05:00Z",
        completion_status=status,
    )

    with pytest.raises(ValueError):
        build_browser_runtime_production_closeout(
            tmp_path,
            generated_at="2026-05-04T12:06:00Z",
            completion_status=status,
            completion_estimate=estimate,
        )


def test_write_closeout_evidence_is_explicit_and_vault_relative(tmp_path: Path) -> None:
    _seed_native_panel_evidence(tmp_path)
    status = _status()
    estimate = build_browser_runtime_completion_estimate(
        tmp_path,
        generated_at="2026-05-04T12:10:00Z",
        completion_status=status,
    )
    report = build_browser_runtime_production_closeout(
        tmp_path,
        generated_at="2026-05-04T12:11:00Z",
        completion_status=status,
        completion_estimate=estimate,
    )

    evidence = write_production_closeout_evidence(
        tmp_path,
        report,
        evidence_slug="closeout-test",
    )

    assert evidence["written"] is True
    assert Path(evidence["json_path"]).exists()
    assert Path(evidence["markdown_path"]).exists()
    payload = json.loads(Path(evidence["json_path"]).read_text(encoding="utf-8"))
    assert payload["internal_studio_panel_lane_complete"] is True


def test_cli_prints_json_without_implicit_evidence_writes() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = closeout_main(["--vault-root", ".", "--json"])
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["record_type"] == BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_RECORD_TYPE
    assert payload["read_only"] is True
    assert payload["writes_evidence"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["browser_use_cli_live_used"] is False
    assert payload["excalidraw_live_proof_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
