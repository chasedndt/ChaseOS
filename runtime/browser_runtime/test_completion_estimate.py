"""Tests for read-only Browser Runtime completion estimates."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.completion_estimate as estimate_module
from runtime.browser_runtime.completion_estimate import (
    BROWSER_RUNTIME_COMPLETION_ESTIMATE_BLOCKED,
    BROWSER_RUNTIME_COMPLETION_ESTIMATE_COMPLETE,
    BrowserRuntimeCompletionEstimate,
    build_browser_runtime_completion_estimate,
    main as estimate_main,
)
from runtime.browser_runtime.completion_status import (
    BROWSER_RUNTIME_OVERALL_COMPLETE,
    BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED,
    BrowserRuntimeCompletionStatus,
)


def _status(*, blockers: tuple[str, ...], production_done: bool = False) -> BrowserRuntimeCompletionStatus:
    return BrowserRuntimeCompletionStatus(
        generated_at="2026-05-04T01:00:00Z",
        overall_status=(
            BROWSER_RUNTIME_OVERALL_COMPLETE
            if production_done
            else BROWSER_RUNTIME_OVERALL_MVP_DONE_PRODUCTION_BLOCKED
        ),
        bounded_mvp_done=True,
        production_feature_done=production_done,
        next_recommended_pass=(
            "complete"
            if production_done
            else "external-runtime-provide-excalidraw-target-url"
        ),
        blocked_reasons=blockers,
        items=(),
    )


def test_module_does_not_import_browser_or_writer_surfaces() -> None:
    source = inspect.getsource(estimate_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "playwright",
        "import browser_use",
        "from browser_use",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
        "write_text(",
        "mkdir(",
        "open(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_current_blocker_shape_estimates_remaining_major_passes_without_effects() -> None:
    estimate = build_browser_runtime_completion_estimate(
        ".",
        generated_at="2026-05-04T01:05:00Z",
        completion_status=_status(
            blockers=(
                "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target",
                "browser_use_cli_live_validation_blocked_unavailable",
                "excalidraw_live_browser_mcp_proof_not_run",
                "studio_operator_ui_not_built",
            )
        ),
    )
    payload = estimate.to_dict()

    assert payload["status"] == BROWSER_RUNTIME_COMPLETION_ESTIMATE_BLOCKED
    assert payload["total_remaining_major_passes_min"] == 5
    assert payload["total_remaining_major_passes_max"] == 9
    assert payload["critical_path"] == [
        "browser-use-cli-live-validation",
        "excalidraw-target-and-readiness",
        "excalidraw-live-browser-mcp-proof",
        "studio-operator-browser-runtime-ui",
    ]
    assert payload["external_dependencies"] == [
        "browser-use-cli-live-validation",
        "excalidraw-target-and-readiness",
        "excalidraw-live-browser-mcp-proof",
    ]
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["browser_run_log_written"] is False
    assert payload["trusted_skill_write_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_current_external_only_blocker_shape_estimates_without_studio_ui_pass() -> None:
    estimate = build_browser_runtime_completion_estimate(
        ".",
        generated_at="2026-05-04T01:06:00Z",
        completion_status=_status(
            blockers=(
                "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target",
                "browser_use_cli_live_validation_blocked_unavailable",
                "excalidraw_live_browser_mcp_proof_not_run",
            )
        ),
    )
    payload = estimate.to_dict()

    assert payload["status"] == BROWSER_RUNTIME_COMPLETION_ESTIMATE_BLOCKED
    assert payload["total_remaining_major_passes_min"] == 3
    assert payload["total_remaining_major_passes_max"] == 6
    assert payload["critical_path"] == [
        "browser-use-cli-live-validation",
        "excalidraw-target-and-readiness",
        "excalidraw-live-browser-mcp-proof",
    ]
    assert payload["external_dependencies"] == payload["critical_path"]


def test_studio_ui_estimate_keeps_wider_range_without_readiness_contract(tmp_path: Path) -> None:
    estimate = build_browser_runtime_completion_estimate(
        tmp_path,
        generated_at="2026-05-04T01:07:00Z",
        completion_status=_status(blockers=("studio_operator_ui_not_built",)),
    )
    payload = estimate.to_dict()

    assert payload["total_remaining_major_passes_min"] == 2
    assert payload["total_remaining_major_passes_max"] == 4
    assert payload["remaining_passes"][0]["pass_id"] == "studio-operator-browser-runtime-ui"


def test_complete_status_reports_zero_remaining_passes() -> None:
    estimate = build_browser_runtime_completion_estimate(
        ".",
        generated_at="2026-05-04T01:10:00Z",
        completion_status=_status(blockers=(), production_done=True),
    )
    payload = estimate.to_dict()

    assert payload["status"] == BROWSER_RUNTIME_COMPLETION_ESTIMATE_COMPLETE
    assert payload["production_feature_done"] is True
    assert payload["total_remaining_major_passes_min"] == 0
    assert payload["total_remaining_major_passes_max"] == 0
    assert payload["remaining_passes"] == []


def test_unknown_blockers_are_counted_as_unclassified_followup() -> None:
    estimate = build_browser_runtime_completion_estimate(
        ".",
        generated_at="2026-05-04T01:15:00Z",
        completion_status=_status(blockers=("new_unclassified_blocker",)),
    )
    payload = estimate.to_dict()

    assert payload["total_remaining_major_passes_min"] == 1
    assert payload["total_remaining_major_passes_max"] == 2
    assert payload["remaining_passes"][0]["pass_id"] == "unclassified-browser-runtime-blockers"
    assert payload["remaining_passes"][0]["blocker_reasons"] == ["new_unclassified_blocker"]


def test_rejects_forbidden_effect_flags() -> None:
    estimate = build_browser_runtime_completion_estimate(
        ".",
        generated_at="2026-05-04T01:20:00Z",
        completion_status=_status(blockers=("studio_operator_ui_not_built",)),
    )
    for flag in (
        "writes_estimate_artifact",
        "dependency_install_attempted",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_invocation_attempted",
        "browser_run_log_written",
        "trusted_skill_write_attempted",
        "skill_activation_attempted",
        "real_profile_access_attempted",
        "credential_or_cookie_read_attempted",
        "browser_harness_used",
        "browser_use_cli_live_used",
        "agent_bus_enqueue_attempted",
        "provider_call_attempted",
        "gate_mutation_attempted",
        "canonical_writeback_attempted",
    ):
        with pytest_raises(ValueError):
            BrowserRuntimeCompletionEstimate(
                record_type=estimate.record_type,
                schema_version=estimate.schema_version,
                generated_at=estimate.generated_at,
                status=estimate.status,
                overall_status=estimate.overall_status,
                bounded_mvp_done=estimate.bounded_mvp_done,
                production_feature_done=estimate.production_feature_done,
                source_next_recommended_pass=estimate.source_next_recommended_pass,
                blocker_count=estimate.blocker_count,
                item_count=estimate.item_count,
                total_remaining_major_passes_min=estimate.total_remaining_major_passes_min,
                total_remaining_major_passes_max=estimate.total_remaining_major_passes_max,
                remaining_passes=estimate.remaining_passes,
                critical_path=estimate.critical_path,
                external_dependencies=estimate.external_dependencies,
                estimate_assumptions=estimate.estimate_assumptions,
                **{flag: True},
            ).validate()


def test_cli_prints_json_without_writes() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = estimate_main(["--vault-root", ".", "--json"])
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["record_type"] == "browser_runtime_completion_estimate"
    assert payload["read_only"] is True
    assert payload["writes_estimate_artifact"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


class pytest_raises:
    def __init__(self, expected: type[BaseException]):
        self.expected = expected

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            raise AssertionError(f"expected {self.expected.__name__}")
        if not issubclass(exc_type, self.expected):
            return False
        return True
