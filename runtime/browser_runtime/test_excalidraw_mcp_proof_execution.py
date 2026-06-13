"""Tests for fail-closed Excalidraw browser/MCP proof execution shell."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_mcp_proof_execution as execution_module
from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_mcp_proof_execution import (
    EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL,
    EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_EXECUTOR_DISABLED,
    EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_MARKER_EXISTS,
    EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION,
    ExcalidrawMCPProofExecutionRequest,
    build_excalidraw_mcp_proof_execution_shell,
    main as execution_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_pending_response(root: Path) -> None:
    _write_json(
        root / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json",
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "status": "excalidraw_local_target_response_pending_external_runtime",
            "response_artifact_written": True,
            "target_url": "",
            "target_host": "",
        },
    )


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


def _seed_ready_response(root: Path) -> Path:
    path = root / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_accepted.json"
    _write_json(
        path,
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "status": "excalidraw_local_target_response_accepted_no_probe",
            "target_url": "http://127.0.0.1:9230/",
            "target_host": "127.0.0.1",
        },
    )
    return path


def _controller_ready() -> BrowserControllerSetupReadiness:
    return BrowserControllerSetupReadiness(
        record_type="browser_controller_setup_readiness",
        version="browser.controller_setup_readiness.v1",
        generated_at="2026-05-03T22:00:00Z",
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


def test_module_does_not_import_live_or_external_runtime_surfaces() -> None:
    source = inspect.getsource(execution_module)
    forbidden = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "playwright",
        "import browser_use",
        "from browser_use",
        "import browser_harness",
        "from browser_harness",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
    )
    for token in forbidden:
        assert token not in source


def test_pending_target_blocks_without_writes(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    result = build_excalidraw_mcp_proof_execution_shell(
        tmp_path,
        generated_at="2026-05-03T22:00:00Z",
    )
    after = _snapshot(tmp_path)

    assert before == after
    assert result.status == EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL
    assert result.approval_request_written is False
    assert result.idempotency_marker_written is False
    assert result.execution_attempted is False
    assert result.browser_launch_attempted is False
    assert result.mcp_invocation_attempted is False
    assert result.canonical_writeback_attempted is False
    assert result.next_step == "external-runtime-provide-excalidraw-target-url"


def test_ready_approval_without_execute_flag_is_ready_no_execution_and_no_writes(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    source = _seed_ready_response(tmp_path)
    before = _snapshot(tmp_path)
    result = build_excalidraw_mcp_proof_execution_shell(
        tmp_path,
        ExcalidrawMCPProofExecutionRequest(response_path=source.as_posix()),
        generated_at="2026-05-03T22:05:00Z",
        controller_readiness=_controller_ready(),
    )
    after = _snapshot(tmp_path)

    assert before == after
    assert result.status == EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION
    assert result.target_url == "http://127.0.0.1:9230/"
    assert result.target_domain == "127.0.0.1"
    assert result.approval_request_written is False
    assert result.idempotency_marker_written is False
    assert result.execution_attempted is False
    assert result.future_artifact_plan["browser_run_log"].endswith("_success.json")
    assert result.execution_contract["browser_profile_policy"] == "throwaway_only"
    assert result.execution_contract["trusted_skill_activation_allowed"] is False
    assert result.next_step == "operator-review-before-excalidraw-live-canvas-execution"


def test_execute_flag_still_blocks_when_live_executor_disabled(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    source = _seed_ready_response(tmp_path)
    result = build_excalidraw_mcp_proof_execution_shell(
        tmp_path,
        ExcalidrawMCPProofExecutionRequest(
            response_path=source.as_posix(),
            execute_local_canvas_proof=True,
            live_executor_enabled=False,
        ),
        generated_at="2026-05-03T22:10:00Z",
        controller_readiness=_controller_ready(),
    )

    assert result.status == EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_EXECUTOR_DISABLED
    assert "live_executor_enabled" in result.blockers
    assert result.execution_attempted is False
    assert result.browser_launch_attempted is False
    assert result.mcp_tool_call_attempted is False


def test_existing_marker_blocks_before_execution(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    source = _seed_ready_response(tmp_path)
    first = build_excalidraw_mcp_proof_execution_shell(
        tmp_path,
        ExcalidrawMCPProofExecutionRequest(response_path=source.as_posix()),
        controller_readiness=_controller_ready(),
    )
    marker = Path(first.idempotency_marker_path)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"status":"reserved"}\n', encoding="utf-8")

    second = build_excalidraw_mcp_proof_execution_shell(
        tmp_path,
        ExcalidrawMCPProofExecutionRequest(response_path=source.as_posix(), execute_local_canvas_proof=True),
        controller_readiness=_controller_ready(),
    )

    assert second.status == EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_MARKER_EXISTS
    assert second.idempotency_marker_exists is True
    assert second.idempotency_marker_written is False
    assert second.browser_launch_attempted is False


def test_validate_rejects_any_execution_or_write_authority(tmp_path: Path) -> None:
    result = build_excalidraw_mcp_proof_execution_shell(tmp_path)

    for field in (
        "approval_request_written",
        "idempotency_marker_written",
        "execution_attempted",
        "browser_launch_attempted",
        "mcp_invocation_attempted",
        "trusted_skill_write_attempted",
        "canonical_writeback_attempted",
    ):
        payload = result.as_dict()
        payload["request"] = result.request
        payload[field] = True
        try:
            type(result)(**payload).validate()
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"{field} should be rejected")


def test_cli_json_is_no_write(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = execution_main(["--vault-root", str(tmp_path), "--json"])
    after = _snapshot(tmp_path)
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL
    assert payload["approval_request_written"] is False
    assert payload["idempotency_marker_written"] is False
    assert payload["execution_attempted"] is False
