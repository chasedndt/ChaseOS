"""Tests for Studio external runtime setup request handoff."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from runtime.studio.external_runtime_setup_request import (
    BRANCH_BROWSER_USE,
    BRANCH_EXCALIDRAW,
    RECORD_TYPE,
    STATUS_NO_REQUEST_NEEDED,
    STATUS_REQUEST_READY,
    build_studio_external_runtime_setup_request,
    main as setup_request_main,
    write_studio_external_runtime_setup_request_evidence,
)


def _readiness_blocked() -> dict[str, object]:
    return {
        "status": "blocked_external_runtime_setup_missing",
        "browser_use_branch_ready": False,
        "excalidraw_branch_ready": False,
        "blockers": [
            "browser_use:browser_use_cli_executable_not_found",
            "excalidraw_target_response:excalidraw_target_response_resolution_pending_external_runtime",
        ],
    }


def _readiness_browser_use_ready() -> dict[str, object]:
    return {
        "status": "ready_for_browser_use_cli_validation",
        "browser_use_branch_ready": True,
        "excalidraw_branch_ready": False,
        "blockers": [
            "excalidraw_target_response:excalidraw_target_response_resolution_pending_external_runtime"
        ],
    }


def _readiness_both_ready() -> dict[str, object]:
    return {
        "status": "ready_for_external_runtime_branches",
        "browser_use_branch_ready": True,
        "excalidraw_branch_ready": True,
        "blockers": [],
    }


def test_auto_request_includes_both_blocked_branches(tmp_path: Path) -> None:
    packet = build_studio_external_runtime_setup_request(
        tmp_path,
        generated_at="2026-05-05T02:00:00Z",
        readiness=_readiness_blocked(),
    )
    payload = packet.to_dict()

    assert payload["record_type"] == RECORD_TYPE
    assert payload["status"] == STATUS_REQUEST_READY
    assert payload["requested_branches"] == [BRANCH_BROWSER_USE, BRANCH_EXCALIDRAW]
    assert len(payload["setup_requests"]) == 2
    assert payload["dependency_install_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
    assert payload["proposal_packet_only"] is True
    assert payload["governed_proposal_packet"]["packet_type"] == "external_runtime_setup_request"
    assert payload["governed_proposal_packet"]["studio_executes_request"] is False
    assert payload["governed_proposal_packet"]["approval_consumed"] is False


def test_auto_request_only_requests_remaining_blocked_branch(tmp_path: Path) -> None:
    packet = build_studio_external_runtime_setup_request(
        tmp_path,
        generated_at="2026-05-05T02:05:00Z",
        readiness=_readiness_browser_use_ready(),
    )

    assert packet.status == STATUS_REQUEST_READY
    assert packet.requested_branches == (BRANCH_EXCALIDRAW,)
    assert packet.setup_requests[0]["branch"] == BRANCH_EXCALIDRAW


def test_no_request_needed_when_both_external_branches_ready(tmp_path: Path) -> None:
    packet = build_studio_external_runtime_setup_request(
        tmp_path,
        generated_at="2026-05-05T02:10:00Z",
        readiness=_readiness_both_ready(),
    )

    assert packet.status == STATUS_NO_REQUEST_NEEDED
    assert packet.requested_branches == ()
    assert packet.setup_requests == ()


def test_explicit_excalidraw_request_contains_target_response_command(tmp_path: Path) -> None:
    packet = build_studio_external_runtime_setup_request(
        tmp_path,
        branch=BRANCH_EXCALIDRAW,
        generated_at="2026-05-05T02:15:00Z",
        readiness=_readiness_blocked(),
    )
    request = packet.setup_requests[0]

    assert request["branch"] == BRANCH_EXCALIDRAW
    assert request["accepted_response_shape"]["target_url"] == "http://127.0.0.1:<port>/"
    assert "excalidraw_target_response" in request["handoff_commands"][0]
    assert "no accounts" in " ".join(request["external_operator_actions"])


def test_evidence_write_is_explicit_and_vault_relative(tmp_path: Path) -> None:
    packet = build_studio_external_runtime_setup_request(
        tmp_path,
        generated_at="2026-05-05T02:20:00Z",
        readiness=_readiness_blocked(),
    )
    evidence = write_studio_external_runtime_setup_request_evidence(
        tmp_path,
        packet,
        evidence_slug="external-runtime-setup-request-test",
    )

    assert evidence["written"] is True
    assert Path(evidence["json_path"]).exists()
    assert Path(evidence["markdown_path"]).exists()


def test_cli_prints_json_without_implicit_writes() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = setup_request_main(["--vault-root", ".", "--json"])
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["record_type"] == RECORD_TYPE
    assert payload["read_only"] is True
    assert payload["writes_evidence"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["browser_use_cli_live_run_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
