"""Tests for no-execution Excalidraw browser/MCP live-chain readiness."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_live_chain_readiness as chain_module
from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_live_chain_readiness import (
    EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET,
    EXCALIDRAW_LIVE_CHAIN_READINESS_READY,
    build_excalidraw_live_chain_readiness,
    main as chain_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_safe_prep(root: Path) -> None:
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json",
        {
            "record_type": "excalidraw_local_browser_mcp_proof_prep",
            "schema_version": "browser.excalidraw_mcp_proof_prep.v1",
            "status": "excalidraw_local_browser_mcp_proof_prep_ready_no_execution",
            "prep_artifact_written": True,
            "run_slug": "excalidraw-local-browser-mcp-proof-20260503",
            "live_proof_allowed_in_this_pass": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "mcp_server_invoked": False,
            "mcp_tool_call_attempted": False,
            "network_navigation_attempted": False,
            "real_profile_access_attempted": False,
            "credential_or_cookie_read_attempted": False,
            "cookie_export_attempted": False,
            "browser_profile_sync_attempted": False,
            "public_tunnel_attempted": False,
            "browser_harness_used": False,
            "browser_use_cli_live_used": False,
            "workflow_use_code_copied": False,
            "trusted_skill_write_attempted": False,
            "skill_activation_attempted": False,
            "agent_bus_enqueue_attempted": False,
            "provider_call_attempted": False,
            "gate_mutation_attempted": False,
            "canonical_writeback_attempted": False,
        },
    )


def _seed_pending_response(root: Path) -> Path:
    path = root / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json"
    _write_json(
        path,
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "status": "excalidraw_local_target_response_pending_external_runtime",
            "response_artifact_written": True,
            "target_url": "",
            "target_host": "",
        },
    )
    return path


def _seed_accepted_response(root: Path) -> Path:
    path = root / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_accepted.json"
    _write_json(
        path,
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "status": "excalidraw_local_target_response_accepted_no_probe",
            "response_artifact_written": True,
            "target_url": "http://127.0.0.1:9230/",
            "target_host": "127.0.0.1",
        },
    )
    return path


def _controller_ready() -> BrowserControllerSetupReadiness:
    return BrowserControllerSetupReadiness(
        record_type="browser_controller_setup_readiness",
        version="browser.controller_setup_readiness.v1",
        generated_at="2026-05-04T10:00:00Z",
        status="browser_controller_setup_ready_no_launch",
        env_var_name="CHASEOS_BROWSER_CDP_EXECUTABLE",
        env_var_value_present=False,
        selected_executable=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        selected_source="well_known_path",
        blockers=[],
        candidates=[],
        operator_handoff={},
        browser_launch_attempted=False,
        cdp_connection_attempted=False,
        real_profile_access_attempted=False,
        credential_or_cookie_read_attempted=False,
        browser_profile_sync_attempted=False,
        browser_use_cli_invoked=False,
        browser_harness_used=False,
        gate_mutation_attempted=False,
        canonical_writeback_attempted=False,
        next_step="excalidraw-local-browser-mcp-live-readiness-with-target",
    )


def test_module_does_not_import_or_execute_live_surfaces() -> None:
    source = inspect.getsource(chain_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "playwright",
        "import browser_use",
        "from browser_use",
        "import workflow_use",
        "from workflow_use",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
        "write_text(",
        "mkdir(",
        "open(",
        "write_draft_site_skill",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_pending_response_blocks_target_chain_without_writes(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    packet = build_excalidraw_live_chain_readiness(
        tmp_path,
        generated_at="2026-05-04T10:05:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET
    assert payload["selected_response_status"] == "excalidraw_local_target_response_pending_external_runtime"
    assert payload["target_url"] == ""
    assert "target_response_not_accepted:excalidraw_target_response_resolution_pending_external_runtime" in payload[
        "blockers"
    ]
    assert payload["chain_steps"][0]["ready"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["browser_run_log_written"] is False
    assert payload["draft_skill_written"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_accepted_response_reports_ready_chain_without_execution_or_writes(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    response = _seed_accepted_response(tmp_path)
    before = _snapshot(tmp_path)
    packet = build_excalidraw_live_chain_readiness(
        tmp_path,
        response_path=response,
        generated_at="2026-05-04T10:10:00Z",
        controller_readiness=_controller_ready(),
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_LIVE_CHAIN_READINESS_READY
    assert payload["target_url"] == "http://127.0.0.1:9230/"
    assert payload["readiness_status"] == "excalidraw_readiness_from_target_response_ready_no_execution"
    assert payload["approval_status"] == "excalidraw_mcp_execution_approval_ready_no_execution"
    assert payload["proof_shell_status"] == "excalidraw_mcp_proof_execution_shell_ready_no_execution"
    assert [step["ready"] for step in payload["chain_steps"]] == [True, True, True, True]
    assert payload["next_recommended_pass"] == "operator-review-before-excalidraw-live-canvas-execution"
    assert payload["execution_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["target_navigation_attempted"] is False
    assert payload["screenshot_attempted"] is False
    assert payload["skill_activation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_explicit_response_path_outside_pending_blocks_without_writes(tmp_path: Path) -> None:
    outside = tmp_path / "outside_response.json"
    _write_json(
        outside,
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "status": "excalidraw_local_target_response_accepted_no_probe",
            "target_url": "http://127.0.0.1:9230/",
            "target_host": "127.0.0.1",
        },
    )
    before = _snapshot(tmp_path)
    packet = build_excalidraw_live_chain_readiness(
        tmp_path,
        response_path=outside,
        generated_at="2026-05-04T10:15:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET
    assert payload["selected_response_path"] == ""
    assert payload["target_url"] == ""
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_reports_blocked_status_for_pending_response_without_writes(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        exit_code = chain_main(
            [
                "--vault-root",
                str(tmp_path),
                "--json",
            ]
        )
    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert before == after
    assert payload["status"] == EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_tool_call_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
