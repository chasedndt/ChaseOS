"""Tests for no-execution Excalidraw browser/MCP live readiness."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_mcp_live_readiness as readiness_module
from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_mcp_live_readiness import (
    EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET,
    EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_NONLOCAL_TARGET,
    EXCALIDRAW_MCP_LIVE_READINESS_READY,
    build_excalidraw_mcp_live_readiness,
    main as readiness_main,
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


def _controller_ready() -> BrowserControllerSetupReadiness:
    return BrowserControllerSetupReadiness(
        record_type="browser_controller_setup_readiness",
        version="browser.controller_setup_readiness.v1",
        generated_at="2026-05-03T13:00:00Z",
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
        next_step="rerun_safe_local_workflow_replay_execution_proof",
    )


def _controller_blocked() -> BrowserControllerSetupReadiness:
    return BrowserControllerSetupReadiness(
        record_type="browser_controller_setup_readiness",
        version="browser.controller_setup_readiness.v1",
        generated_at="2026-05-03T13:00:00Z",
        status="blocked_browser_controller_setup",
        env_var_name="CHASEOS_BROWSER_CDP_EXECUTABLE",
        env_var_value_present=False,
        selected_executable="",
        selected_source="",
        blockers=["chromium_compatible_executable_not_found"],
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
        next_step="install_or_locate_chromium_and_set_chaseos_browser_cdp_executable",
    )


def test_module_does_not_import_live_browser_mcp_or_external_workflow_surfaces() -> None:
    source = inspect.getsource(readiness_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "import browser_use",
        "from browser_use",
        "import workflow_use",
        "from workflow_use",
        "playwright",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
        "write_draft_site_skill",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_missing_local_target_blocks_without_writes(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    before = _snapshot(tmp_path)
    packet = build_excalidraw_mcp_live_readiness(
        tmp_path,
        generated_at="2026-05-03T13:05:00Z",
        controller_readiness=_controller_ready(),
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET
    assert payload["prep_evidence_ready"] is True
    assert payload["browser_controller_ready"] is True
    assert payload["readiness_artifact_written"] is False
    assert "local_excalidraw_target_url_not_provided" in payload["blockers"]
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_server_invoked"] is False
    assert payload["network_navigation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_nonlocal_target_is_blocked(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    packet = build_excalidraw_mcp_live_readiness(
        tmp_path,
        local_target_url="https://excalidraw.com/",
        generated_at="2026-05-03T13:10:00Z",
        controller_readiness=_controller_ready(),
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_NONLOCAL_TARGET
    assert payload["local_target_host"] == "excalidraw.com"
    assert "local_excalidraw_target_url_must_be_loopback" in payload["blockers"]
    assert payload["public_tunnel_attempted"] is False
    assert payload["network_navigation_attempted"] is False


def test_local_target_can_be_ready_without_execution(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    packet = build_excalidraw_mcp_live_readiness(
        tmp_path,
        local_target_url="http://127.0.0.1:9230/excalidraw",
        generated_at="2026-05-03T13:15:00Z",
        controller_readiness=_controller_ready(),
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_MCP_LIVE_READINESS_READY
    assert payload["blockers"] == []
    assert payload["local_target_host"] == "127.0.0.1"
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False
    assert payload["mcp_tool_call_attempted"] is False
    assert payload["next_recommended_pass"] == "excalidraw-local-browser-mcp-proof-execution-approval"


def test_controller_blocker_stops_before_target_readiness(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    packet = build_excalidraw_mcp_live_readiness(
        tmp_path,
        local_target_url="http://localhost:9230/",
        generated_at="2026-05-03T13:20:00Z",
        controller_readiness=_controller_blocked(),
    )
    payload = packet.to_dict()

    assert payload["status"] == "blocked_excalidraw_live_readiness_browser_controller_unavailable"
    assert payload["browser_controller_ready"] is False
    assert "browser_controller_setup_not_ready" in payload["blockers"]
    assert payload["browser_launch_attempted"] is False


def test_write_readiness_writes_only_browser_run_evidence(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    packet = build_excalidraw_mcp_live_readiness(
        tmp_path,
        generated_at="2026-05-03T13:25:00Z",
        write_readiness=True,
        controller_readiness=_controller_ready(),
    )
    artifact = Path(packet.readiness_artifact_path)
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert artifact.is_file()
    assert artifact.name == "excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
    assert payload["status"] == EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET
    assert payload["readiness_artifact_written"] is True
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_server_invoked"] is False
    assert payload["trusted_skill_write_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_is_no_write_without_write_flag(tmp_path: Path, monkeypatch) -> None:
    _seed_safe_prep(tmp_path)
    monkeypatch.setattr(readiness_module, "evaluate_browser_controller_setup_readiness", lambda: _controller_ready())
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = readiness_main(
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
    assert payload["status"] == EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET
    assert payload["readiness_artifact_written"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_tool_call_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
