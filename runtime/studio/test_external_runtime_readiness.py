"""Tests for Studio external runtime readiness gate."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from runtime.studio.external_runtime_readiness import (
    RECORD_TYPE,
    STATUS_BLOCKED,
    STATUS_READY_BOTH,
    STATUS_READY_BROWSER_USE,
    build_studio_external_runtime_readiness,
    main as readiness_main,
    write_studio_external_runtime_readiness_evidence,
)


def _browser_use_ready() -> dict[str, object]:
    return {
        "status": "ready_for_operator_authorized_live_validation_no_execution",
        "blockers": ["browser_use_cli_live_validation_not_run"],
        "ready_for_future_live_validation": True,
        "browser_launch_attempted": False,
        "browser_use_cli_live_run_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "canonical_writeback_attempted": False,
    }


def _browser_use_blocked() -> dict[str, object]:
    return {
        "status": "blocked_browser_use_cli_unavailable",
        "blockers": ["browser_use_cli_executable_not_found"],
        "ready_for_future_live_validation": False,
    }


def _target_pending() -> dict[str, object]:
    return {
        "status": "excalidraw_target_response_resolution_pending_external_runtime",
        "target_url": "",
        "blockers": [],
    }


def _target_accepted() -> dict[str, object]:
    return {
        "status": "excalidraw_target_response_resolution_accepted_no_probe",
        "target_url": "http://127.0.0.1:3210/",
        "blockers": [],
    }


def _chain_blocked() -> dict[str, object]:
    return {
        "status": "blocked_excalidraw_live_chain_readiness_target_response_not_accepted",
        "blockers": [
            "target_response_not_accepted:excalidraw_target_response_resolution_pending_external_runtime"
        ],
        "browser_launch_attempted": False,
        "mcp_invocation_attempted": False,
        "canonical_writeback_attempted": False,
    }


def _write_browser_runtime_fixture(vault_root: Path) -> None:
    adapter = vault_root / "runtime/browser_runtime/adapters/browser_use_cli.py"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text("# test wrapper\n", encoding="utf-8")
    config = vault_root / "runtime/browser_runtime/config.yaml"
    config.write_text(
        "\n".join(
            [
                "browser_profile_policy: throwaway_only",
                "allow_real_profile: false",
                "allow_credentials: false",
                "allow_shell_execution: false",
                "allow_cookie_export: false",
                "allow_browser_profile_sync: false",
                "allow_public_tunnel: false",
                "canonical_writeback: false",
                "automatic_skill_activation: false",
                "skill_generation: draft_only",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_readiness_blocks_when_both_external_inputs_are_missing(tmp_path: Path) -> None:
    report = build_studio_external_runtime_readiness(
        tmp_path,
        generated_at="2026-05-05T01:00:00Z",
        browser_use_status=_browser_use_blocked(),
        excalidraw_target_response=_target_pending(),
        excalidraw_live_chain=_chain_blocked(),
    )
    payload = report.to_dict()

    assert payload["record_type"] == RECORD_TYPE
    assert payload["status"] == STATUS_BLOCKED
    assert payload["browser_use_branch_ready"] is False
    assert payload["excalidraw_branch_ready"] is False
    assert "browser_use:browser_use_cli_executable_not_found" in payload["blockers"]
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["browser_use_cli_live_run_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_readiness_allows_browser_use_branch_when_only_cli_preflight_is_ready(tmp_path: Path) -> None:
    report = build_studio_external_runtime_readiness(
        tmp_path,
        generated_at="2026-05-05T01:05:00Z",
        browser_use_status=_browser_use_ready(),
        excalidraw_target_response=_target_pending(),
        excalidraw_live_chain=_chain_blocked(),
    )

    assert report.status == STATUS_READY_BROWSER_USE
    assert report.browser_use_branch_ready is True
    assert report.excalidraw_branch_ready is False
    assert report.next_recommended_pass == "browser-use-cli-external-runtime-validation"


def test_readiness_uses_browser_use_cli_env_without_live_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_browser_runtime_fixture(tmp_path)
    monkeypatch.setenv("CHASEOS_BROWSER_USE_CLI", sys.executable)

    report = build_studio_external_runtime_readiness(
        tmp_path,
        generated_at="2026-05-05T01:07:00Z",
        excalidraw_target_response=_target_pending(),
        excalidraw_live_chain=_chain_blocked(),
    )
    payload = report.to_dict()

    assert payload["status"] == STATUS_READY_BROWSER_USE
    assert payload["browser_use_branch_ready"] is True
    assert payload["browser_use"]["executable"] == sys.executable
    assert payload["browser_use"]["executable_found"] is True
    assert payload["browser_use"]["browser_use_cli_live_run_attempted"] is False
    assert payload["browser_use"]["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_readiness_allows_both_branches_when_inputs_are_ready(tmp_path: Path) -> None:
    report = build_studio_external_runtime_readiness(
        tmp_path,
        generated_at="2026-05-05T01:10:00Z",
        browser_use_status=_browser_use_ready(),
        excalidraw_target_response=_target_accepted(),
        excalidraw_live_chain={"status": "excalidraw_live_chain_readiness_ready_no_execution", "blockers": []},
    )

    assert report.status == STATUS_READY_BOTH
    assert report.browser_use_branch_ready is True
    assert report.excalidraw_branch_ready is True
    assert report.blockers == ()


def test_evidence_write_is_explicit_and_vault_relative(tmp_path: Path) -> None:
    report = build_studio_external_runtime_readiness(
        tmp_path,
        generated_at="2026-05-05T01:15:00Z",
        browser_use_status=_browser_use_blocked(),
        excalidraw_target_response=_target_pending(),
        excalidraw_live_chain=_chain_blocked(),
    )
    evidence = write_studio_external_runtime_readiness_evidence(
        tmp_path,
        report,
        evidence_slug="external-runtime-readiness-test",
    )

    assert evidence["written"] is True
    assert Path(evidence["json_path"]).exists()
    assert Path(evidence["markdown_path"]).exists()


def test_cli_prints_json_without_implicit_writes() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = readiness_main(["--vault-root", ".", "--json"])
    payload = json.loads(output.getvalue())

    assert exit_code in {0, 1}
    assert payload["record_type"] == RECORD_TYPE
    assert payload["read_only"] is True
    assert payload["writes_evidence"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["browser_use_cli_live_run_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
