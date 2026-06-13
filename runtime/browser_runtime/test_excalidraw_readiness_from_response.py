"""Tests for no-execution Excalidraw readiness bridge from target response."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_readiness_from_response as bridge_module
from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_readiness_from_response import (
    EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING,
    EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
    build_excalidraw_readiness_from_response,
    main as bridge_main,
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
        generated_at="2026-05-03T21:00:00Z",
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


def test_module_does_not_import_or_execute_live_browser_mcp_surfaces() -> None:
    source = inspect.getsource(bridge_module)
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
        "write_draft_site_skill",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_pending_response_blocks_without_writes(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    packet = build_excalidraw_readiness_from_response(
        tmp_path,
        generated_at="2026-05-03T21:05:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING
    assert payload["source_response_status"] == "excalidraw_local_target_response_pending_external_runtime"
    assert payload["target_url"] == ""
    assert payload["bridge_artifact_written"] is False
    assert "excalidraw_target_response_pending_external_runtime" in payload["blockers"]
    assert payload["browser_launch_attempted"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_accepted_response_can_build_ready_live_readiness_without_writes(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    _seed_accepted_response(tmp_path)
    packet = build_excalidraw_readiness_from_response(
        tmp_path,
        generated_at="2026-05-03T21:10:00Z",
        controller_readiness=_controller_ready(),
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_READY
    assert payload["target_url"] == "http://127.0.0.1:9230/"
    assert payload["live_readiness_status"] == "excalidraw_local_browser_mcp_live_readiness_ready_no_execution"
    assert payload["bridge_artifact_written"] is False
    assert payload["live_readiness_would_write"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False
    assert payload["target_navigation_attempted"] is False
    assert payload["next_recommended_pass"] == "excalidraw-local-browser-mcp-proof-execution-approval"


def test_latest_resolver_finds_newer_dated_accepted_response(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    path = tmp_path / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260504_accepted.json"
    _write_json(
        path,
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "generated_at": "2026-05-04T08:10:00Z",
            "status": "excalidraw_local_target_response_accepted_no_probe",
            "response_artifact_written": True,
            "target_url": "http://127.0.0.1:9232/",
            "target_host": "127.0.0.1",
        },
    )

    packet = build_excalidraw_readiness_from_response(
        tmp_path,
        generated_at="2026-05-04T08:15:00Z",
        controller_readiness=_controller_ready(),
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_READY
    assert payload["source_response_path"] == path.resolve().as_posix()
    assert payload["target_url"] == "http://127.0.0.1:9232/"
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_write_bridge_writes_only_browser_run_bridge_evidence(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    packet = build_excalidraw_readiness_from_response(
        tmp_path,
        generated_at="2026-05-03T21:15:00Z",
        write_bridge=True,
    )
    artifact = Path(packet.bridge_artifact_path)
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert artifact.is_file()
    assert artifact.name == "excalidraw_readiness_from_target_response_20260503_blocked_pending.json"
    assert payload["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING
    assert payload["bridge_artifact_written"] is True
    assert payload["network_probe_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_is_no_write_without_write_flag(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = bridge_main(["--vault-root", str(tmp_path), "--json"])

    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 1
    assert before == after
    assert payload["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING
    assert payload["bridge_artifact_written"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
