"""Tests for prep-only Excalidraw browser/MCP proof contract."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_mcp_proof_prep as prep_module
from runtime.browser_runtime.excalidraw_mcp_proof_prep import (
    EXCALIDRAW_MCP_PROOF_PREP_READY,
    ExcalidrawMCPProofPrepRequest,
    build_excalidraw_mcp_proof_prep,
    main as prep_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_module_does_not_import_live_browser_mcp_or_external_workflow_surfaces() -> None:
    source = inspect.getsource(prep_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "import browser_use",
        "from browser_use",
        "import workflow_use",
        "from workflow_use",
        "playwright",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_build_prep_packet_is_no_write_by_default(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    packet = build_excalidraw_mcp_proof_prep(
        tmp_path,
        ExcalidrawMCPProofPrepRequest(run_date="20260503"),
        generated_at="2026-05-03T10:00:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_MCP_PROOF_PREP_READY
    assert payload["run_slug"] == "excalidraw-local-browser-mcp-proof-20260503"
    assert payload["prep_artifact_written"] is False
    assert payload["live_proof_allowed_in_this_pass"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False
    assert payload["mcp_server_invoked"] is False
    assert payload["mcp_tool_call_attempted"] is False
    assert payload["network_navigation_attempted"] is False
    assert payload["real_profile_access_attempted"] is False
    assert payload["credential_or_cookie_read_attempted"] is False
    assert payload["trusted_skill_write_attempted"] is False
    assert payload["skill_activation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_prep_packet_declares_local_first_and_public_fallback_boundaries(tmp_path: Path) -> None:
    packet = build_excalidraw_mcp_proof_prep(
        tmp_path,
        ExcalidrawMCPProofPrepRequest(run_date="20260503"),
        generated_at="2026-05-03T10:05:00Z",
    )
    payload = packet.to_dict()
    targets = {target["mode"]: target for target in payload["target_options"]}

    assert targets["local_mcp_or_local_canvas_first"]["allowed_hosts"] == ["127.0.0.1", "localhost"]
    assert targets["local_mcp_or_local_canvas_first"]["requires_public_network"] is False
    assert targets["public_excalidraw_fallback"]["requires_explicit_operator_approval"] is True
    assert targets["public_excalidraw_fallback"]["requires_throwaway_profile"] is True
    assert targets["public_excalidraw_fallback"]["requires_account_login"] is False
    assert "07_LOGS/Browser-Runs/excalidraw-local-browser-mcp-proof-20260503_success.json" in payload[
        "expected_future_artifacts"
    ]["browser_run_log"]


def test_write_prep_persists_only_prep_evidence(tmp_path: Path) -> None:
    packet = build_excalidraw_mcp_proof_prep(
        tmp_path,
        ExcalidrawMCPProofPrepRequest(run_date="20260503"),
        generated_at="2026-05-03T10:10:00Z",
        write_prep=True,
    )
    artifact = Path(packet.prep_artifact_path)
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert artifact.is_file()
    assert artifact.name == "excalidraw_local_browser_mcp_proof_prep_20260503_ready.json"
    assert payload["status"] == EXCALIDRAW_MCP_PROOF_PREP_READY
    assert payload["prep_artifact_written"] is True
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_server_invoked"] is False
    assert payload["trusted_skill_write_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_is_no_write_without_write_flag(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = prep_main(
            [
                "--vault-root",
                str(tmp_path),
                "--run-date",
                "20260503",
                "--json",
            ]
        )

    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_MCP_PROOF_PREP_READY
    assert payload["prep_artifact_written"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_tool_call_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
