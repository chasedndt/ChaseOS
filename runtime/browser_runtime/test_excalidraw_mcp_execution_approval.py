"""Tests for no-write Excalidraw browser/MCP execution approval contract."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_mcp_execution_approval as approval_module
from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_mcp_execution_approval import (
    EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED,
    EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS,
    EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY,
    ExcalidrawMCPExecutionApprovalRequest,
    build_excalidraw_mcp_execution_approval,
    main as approval_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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


def _seed_ready_bridge(root: Path) -> Path:
    source = root / "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_accepted.json"
    live = root / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_ready.json"
    path = root / "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_ready.json"
    _write_json(
        source,
        {
            "record_type": "excalidraw_local_target_response",
            "schema_version": "browser.excalidraw_target_response.v1",
            "status": "excalidraw_local_target_response_accepted_no_probe",
            "target_url": "http://127.0.0.1:9230/",
            "target_host": "127.0.0.1",
        },
    )
    _write_json(
        live,
        {
            "record_type": "excalidraw_local_browser_mcp_live_readiness",
            "schema_version": "browser.excalidraw_mcp_live_readiness.v1",
            "status": "excalidraw_local_browser_mcp_live_readiness_ready_no_execution",
            "readiness_artifact_written": True,
        },
    )
    _write_json(
        path,
        {
            "record_type": "excalidraw_readiness_from_target_response",
            "schema_version": "browser.excalidraw_readiness_from_response.v1",
            "status": "excalidraw_readiness_from_target_response_ready_no_execution",
            "bridge_artifact_written": True,
            "source_response_path": source.as_posix(),
            "source_response_status": "excalidraw_local_target_response_accepted_no_probe",
            "target_url": "http://127.0.0.1:9230/",
            "target_host": "127.0.0.1",
            "live_readiness_status": "excalidraw_local_browser_mcp_live_readiness_ready_no_execution",
            "live_readiness_artifact_path": live.as_posix(),
            "blockers": [],
            "dependency_install_attempted": False,
            "server_start_attempted": False,
            "network_probe_attempted": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "mcp_invocation_attempted": False,
            "mcp_tool_call_attempted": False,
            "target_navigation_attempted": False,
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
    return source


def _controller_ready() -> BrowserControllerSetupReadiness:
    return BrowserControllerSetupReadiness(
        record_type="browser_controller_setup_readiness",
        version="browser.controller_setup_readiness.v1",
        generated_at="2026-05-03T21:30:00Z",
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
    source = inspect.getsource(approval_module)
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
    )
    for token in forbidden_tokens:
        assert token not in source


def test_pending_target_response_blocks_without_writes(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    result = build_excalidraw_mcp_execution_approval(
        tmp_path,
        generated_at="2026-05-03T21:30:00Z",
    )
    after = _snapshot(tmp_path)

    assert before == after
    assert result.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED
    assert "readiness_from_response_ready_no_execution" in result.blockers
    assert result.target_url == ""
    assert result.approval_request_written is False
    assert result.idempotency_marker_written is False
    assert result.execution_allowed is False
    assert result.browser_launch_attempted is False
    assert result.mcp_invocation_attempted is False
    assert result.canonical_writeback_attempted is False
    assert result.next_step == "external-runtime-provide-excalidraw-target-url"


def test_ready_bridge_builds_approval_contract_without_writes(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    source = _seed_ready_bridge(tmp_path)
    before = _snapshot(tmp_path)
    result = build_excalidraw_mcp_execution_approval(
        tmp_path,
        ExcalidrawMCPExecutionApprovalRequest(
            response_path=source.as_posix(),
            requested_by="Codex",
            operator_id="operator-review",
        ),
        generated_at="2026-05-03T21:35:00Z",
        controller_readiness=_controller_ready(),
    )
    after = _snapshot(tmp_path)

    assert before == after
    assert result.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY
    assert result.target_url == "http://127.0.0.1:9230/"
    assert result.target_domain == "127.0.0.1"
    assert result.approval_request_preview["status"] == "pending_preview_not_written"
    assert result.approval_request_preview["operator_id"] == "operator-review"
    assert result.idempotency_marker_contract["marker_written"] is False
    assert result.execution_allowed is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.mcp_invocation_attempted is False
    assert result.real_profile_access_attempted is False
    assert result.credential_or_cookie_read_attempted is False
    assert result.trusted_skill_write_attempted is False
    assert result.canonical_writeback_attempted is False
    assert result.next_step == "excalidraw-local-browser-mcp-proof-execution"


def test_contract_identity_is_stable(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    source = _seed_ready_bridge(tmp_path)
    request = ExcalidrawMCPExecutionApprovalRequest(response_path=source.as_posix())

    first = build_excalidraw_mcp_execution_approval(
        tmp_path,
        request,
        generated_at="2026-05-03T21:40:00Z",
        controller_readiness=_controller_ready(),
    )
    second = build_excalidraw_mcp_execution_approval(
        tmp_path,
        request,
        generated_at="2026-05-03T21:41:00Z",
        controller_readiness=_controller_ready(),
    )

    assert first.approval_request_id == second.approval_request_id
    assert first.request_digest_sha256 == second.request_digest_sha256
    assert first.idempotency_marker_path == second.idempotency_marker_path


def test_existing_idempotency_marker_blocks_duplicate_attempt(tmp_path: Path) -> None:
    _seed_safe_prep(tmp_path)
    source = _seed_ready_bridge(tmp_path)
    request = ExcalidrawMCPExecutionApprovalRequest(response_path=source.as_posix())
    first = build_excalidraw_mcp_execution_approval(tmp_path, request, controller_readiness=_controller_ready())
    marker = Path(first.idempotency_marker_path)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"reserved": true}\n', encoding="utf-8")

    second = build_excalidraw_mcp_execution_approval(tmp_path, request, controller_readiness=_controller_ready())

    assert second.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS
    assert second.idempotency_marker_exists is True
    assert "idempotency_marker_absent" in second.blockers
    assert second.idempotency_marker_written is False
    assert second.browser_launch_attempted is False


def test_validate_rejects_write_execution_or_marker_authority(tmp_path: Path) -> None:
    result = build_excalidraw_mcp_execution_approval(tmp_path)

    payload = result.as_dict()
    payload["request"] = result.request
    payload["approval_request_written"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "approval_request_written" in str(exc)
    else:
        raise AssertionError("approval request write should be rejected")

    payload = result.as_dict()
    payload["request"] = result.request
    payload["idempotency_marker_written"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "idempotency_marker_written" in str(exc)
    else:
        raise AssertionError("idempotency marker write should be rejected")

    payload = result.as_dict()
    payload["request"] = result.request
    payload["mcp_invocation_attempted"] = True
    try:
        type(result)(**payload).validate()
    except ValueError as exc:
        assert "mcp_invocation_attempted" in str(exc)
    else:
        raise AssertionError("MCP invocation should be rejected")


def test_cli_json_is_read_only(tmp_path: Path) -> None:
    _seed_pending_response(tmp_path)
    before = _snapshot(tmp_path)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = approval_main(["--vault-root", str(tmp_path), "--json"])

    after = _snapshot(tmp_path)
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED
    assert payload["approval_request_written"] is False
    assert payload["idempotency_marker_written"] is False
    assert payload["execution_allowed"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
