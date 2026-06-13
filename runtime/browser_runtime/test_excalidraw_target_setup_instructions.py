"""Tests for no-execution Excalidraw local-target setup instructions."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_target_setup_instructions as target_setup_module
from runtime.browser_runtime.excalidraw_target_setup_instructions import (
    EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS,
    EXCALIDRAW_TARGET_SETUP_READY,
    build_excalidraw_target_setup_instructions,
    main as setup_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_safe_blocked_readiness(root: Path, *, unsafe: bool = False) -> None:
    payload: dict[str, object] = {
        "record_type": "excalidraw_local_browser_mcp_live_readiness",
        "schema_version": "browser.excalidraw_mcp_live_readiness.v1",
        "status": "blocked_excalidraw_live_readiness_missing_local_target",
        "readiness_artifact_written": True,
        "prep_evidence_ready": True,
        "browser_controller_ready": True,
        "local_target_url": "",
        "blockers": ["local_excalidraw_target_url_not_provided"],
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_server_invoked": False,
        "mcp_tool_call_attempted": False,
        "network_navigation_attempted": False,
        "dependency_install_attempted": False,
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
    }
    if unsafe:
        payload["browser_launch_attempted"] = True
    _write_json(
        root
        / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json",
        payload,
    )


def test_module_does_not_import_or_execute_live_browser_mcp_surfaces() -> None:
    source = inspect.getsource(target_setup_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
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


def test_builds_setup_instructions_without_writes(tmp_path: Path) -> None:
    _seed_safe_blocked_readiness(tmp_path)
    before = _snapshot(tmp_path)
    packet = build_excalidraw_target_setup_instructions(
        tmp_path,
        generated_at="2026-05-03T19:20:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_SETUP_READY
    assert payload["previous_readiness_safe"] is True
    assert payload["setup_artifact_written"] is False
    assert payload["allowed_target_hosts"] == ["127.0.0.1", "::1", "localhost"]
    assert payload["runtime_handoff"]["chaseos_does_not_install_or_start_target"] is True
    assert payload["live_proof_command_not_authorized"]
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_server_start_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_missing_previous_readiness_blocks_instructions(tmp_path: Path) -> None:
    packet = build_excalidraw_target_setup_instructions(
        tmp_path,
        generated_at="2026-05-03T19:25:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS
    assert payload["previous_readiness_safe"] is False
    assert "previous_excalidraw_live_readiness_missing_or_unsafe" in payload["blockers"]
    assert payload["dependency_install_attempted"] is False
    assert payload["browser_launch_attempted"] is False


def test_unsafe_previous_readiness_blocks_instructions(tmp_path: Path) -> None:
    _seed_safe_blocked_readiness(tmp_path, unsafe=True)
    packet = build_excalidraw_target_setup_instructions(tmp_path)
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS
    assert payload["previous_readiness_safe"] is False
    assert "previous_excalidraw_live_readiness_missing_or_unsafe" in payload["blockers"]
    assert payload["mcp_tool_call_attempted"] is False


def test_write_instructions_writes_only_browser_run_evidence(tmp_path: Path) -> None:
    _seed_safe_blocked_readiness(tmp_path)
    packet = build_excalidraw_target_setup_instructions(
        tmp_path,
        generated_at="2026-05-03T19:30:00Z",
        write_instructions=True,
    )
    artifact = Path(packet.setup_artifact_path)
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert artifact.is_file()
    assert artifact.name == "excalidraw_local_target_setup_instructions_20260503_ready.json"
    assert payload["status"] == EXCALIDRAW_TARGET_SETUP_READY
    assert payload["setup_artifact_written"] is True
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_server_start_attempted"] is False
    assert payload["trusted_skill_write_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_is_no_write_without_write_flag(tmp_path: Path) -> None:
    _seed_safe_blocked_readiness(tmp_path)
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = setup_main(["--vault-root", str(tmp_path), "--json"])

    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_SETUP_READY
    assert payload["setup_artifact_written"] is False
    assert payload["dependency_install_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
