"""Tests for the fail-closed Studio external runtime branch gate."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from runtime.browser_runtime.excalidraw_live_chain_readiness import (
    EXCALIDRAW_LIVE_CHAIN_READINESS_READY,
)
from runtime.studio.external_runtime_branch_gate import (
    BRANCH_BROWSER_USE,
    BRANCH_EXCALIDRAW_PROOF,
    BRANCH_EXCALIDRAW_TARGET,
    RECORD_TYPE,
    STATUS_BLOCKED,
    STATUS_READY,
    build_studio_external_runtime_branch_gate,
    main as branch_gate_main,
    write_studio_external_runtime_branch_gate_evidence,
)


def _readiness_blocked() -> dict[str, object]:
    return {
        "status": "blocked_external_runtime_setup_missing",
        "browser_use_branch_ready": False,
        "excalidraw_branch_ready": False,
        "blockers": [
            "browser_use:browser_use_cli_executable_not_found",
            "excalidraw_target_response:excalidraw_target_response_resolution_pending_external_runtime",
            "excalidraw_live_chain:target_response_not_accepted:excalidraw_target_response_resolution_pending_external_runtime",
        ],
        "excalidraw_live_chain": {
            "status": "blocked_excalidraw_live_chain_readiness_target_response_not_accepted",
            "blockers": [
                "target_response_not_accepted:excalidraw_target_response_resolution_pending_external_runtime"
            ],
        },
    }


def _readiness_browser_ready() -> dict[str, object]:
    return {
        "status": "ready_for_browser_use_cli_validation",
        "browser_use_branch_ready": True,
        "excalidraw_branch_ready": False,
        "blockers": [
            "excalidraw_target_response:excalidraw_target_response_resolution_pending_external_runtime"
        ],
        "excalidraw_live_chain": {
            "status": "blocked_excalidraw_live_chain_readiness_target_response_not_accepted",
            "blockers": ["target_response_not_accepted"],
        },
    }


def _readiness_excalidraw_target_ready() -> dict[str, object]:
    return {
        "status": "ready_for_excalidraw_target_or_live_proof",
        "browser_use_branch_ready": False,
        "excalidraw_branch_ready": True,
        "blockers": ["browser_use:browser_use_cli_executable_not_found"],
        "excalidraw_live_chain": {
            "status": "blocked_excalidraw_mcp_execution_approval",
            "blockers": ["execution_approval_contract_not_ready"],
        },
    }


def _readiness_excalidraw_proof_ready() -> dict[str, object]:
    return {
        "status": "ready_for_excalidraw_target_or_live_proof",
        "browser_use_branch_ready": False,
        "excalidraw_branch_ready": True,
        "blockers": ["browser_use:browser_use_cli_executable_not_found"],
        "excalidraw_live_chain": {
            "status": EXCALIDRAW_LIVE_CHAIN_READINESS_READY,
            "blockers": [],
        },
    }


def test_browser_use_branch_blocks_when_preflight_not_ready(tmp_path: Path) -> None:
    gate = build_studio_external_runtime_branch_gate(
        tmp_path,
        branch=BRANCH_BROWSER_USE,
        generated_at="2026-05-05T03:00:00Z",
        readiness=_readiness_blocked(),
    )
    payload = gate.to_dict()

    assert payload["record_type"] == RECORD_TYPE
    assert payload["status"] == STATUS_BLOCKED
    assert payload["can_start_branch"] is False
    assert "browser_use:browser_use_cli_executable_not_found" in payload["blockers"]
    assert payload["browser_launch_attempted"] is False
    assert payload["browser_use_cli_live_run_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_browser_use_branch_can_start_when_readiness_allows_it(tmp_path: Path) -> None:
    gate = build_studio_external_runtime_branch_gate(
        tmp_path,
        branch=BRANCH_BROWSER_USE,
        generated_at="2026-05-05T03:05:00Z",
        readiness=_readiness_browser_ready(),
    )

    assert gate.status == STATUS_READY
    assert gate.can_start_branch is True
    assert gate.next_allowed_step == BRANCH_BROWSER_USE


def test_excalidraw_target_branch_can_start_on_excalidraw_branch_ready(tmp_path: Path) -> None:
    gate = build_studio_external_runtime_branch_gate(
        tmp_path,
        branch=BRANCH_EXCALIDRAW_TARGET,
        generated_at="2026-05-05T03:10:00Z",
        readiness=_readiness_excalidraw_target_ready(),
    )

    assert gate.status == STATUS_READY
    assert gate.can_start_branch is True
    assert "no live browser/MCP proof starts" in " ".join(gate.required_preconditions)


def test_excalidraw_live_proof_requires_live_chain_ready(tmp_path: Path) -> None:
    gate = build_studio_external_runtime_branch_gate(
        tmp_path,
        branch=BRANCH_EXCALIDRAW_PROOF,
        generated_at="2026-05-05T03:15:00Z",
        readiness=_readiness_excalidraw_target_ready(),
    )

    assert gate.status == STATUS_BLOCKED
    assert gate.can_start_branch is False
    assert "excalidraw_live_chain:execution_approval_contract_not_ready" in gate.blockers


def test_excalidraw_live_proof_can_start_when_live_chain_ready(tmp_path: Path) -> None:
    gate = build_studio_external_runtime_branch_gate(
        tmp_path,
        branch=BRANCH_EXCALIDRAW_PROOF,
        generated_at="2026-05-05T03:20:00Z",
        readiness=_readiness_excalidraw_proof_ready(),
    )

    assert gate.status == STATUS_READY
    assert gate.can_start_branch is True
    assert gate.next_allowed_step == BRANCH_EXCALIDRAW_PROOF


def test_evidence_write_is_explicit_and_vault_relative(tmp_path: Path) -> None:
    gate = build_studio_external_runtime_branch_gate(
        tmp_path,
        branch=BRANCH_EXCALIDRAW_TARGET,
        generated_at="2026-05-05T03:25:00Z",
        readiness=_readiness_blocked(),
    )
    evidence = write_studio_external_runtime_branch_gate_evidence(
        tmp_path,
        gate,
        evidence_slug="external-runtime-branch-gate-test",
    )

    assert evidence["written"] is True
    assert Path(evidence["json_path"]).exists()
    assert Path(evidence["markdown_path"]).exists()


def test_cli_prints_json_without_implicit_writes() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = branch_gate_main(
            [
                "--vault-root",
                ".",
                "--branch",
                BRANCH_EXCALIDRAW_TARGET,
                "--json",
            ]
        )
    payload = json.loads(output.getvalue())

    assert exit_code in {0, 1}
    assert payload["record_type"] == RECORD_TYPE
    assert payload["read_only"] is True
    assert payload["writes_evidence"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
