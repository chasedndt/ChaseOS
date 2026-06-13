"""Tests for no-execution Excalidraw local target contract."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_target_contract as target_contract_module
from runtime.browser_runtime.excalidraw_target_contract import (
    EXCALIDRAW_TARGET_CONTRACT_BLOCKED_BAD_SHAPE,
    EXCALIDRAW_TARGET_CONTRACT_BLOCKED_NONLOCAL,
    EXCALIDRAW_TARGET_CONTRACT_READY,
    EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY,
    build_excalidraw_target_contract,
    main as contract_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_module_does_not_import_or_execute_live_browser_mcp_surfaces() -> None:
    source = inspect.getsource(target_contract_module)
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


def test_builds_request_packet_without_target_or_writes(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    packet = build_excalidraw_target_contract(
        tmp_path,
        generated_at="2026-05-03T19:35:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY
    assert payload["target_url"] == ""
    assert payload["external_runtime_request"]["target_url_required"] is True
    assert payload["contract_artifact_written"] is False
    assert payload["server_start_attempted"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_local_target_url_is_contract_ready_without_probe(tmp_path: Path) -> None:
    packet = build_excalidraw_target_contract(
        tmp_path,
        target_url="http://127.0.0.1:9230/excalidraw",
        generated_at="2026-05-03T19:40:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_CONTRACT_READY
    assert payload["target_host"] == "127.0.0.1"
    assert payload["blocked_reasons"] == []
    assert payload["network_probe_attempted"] is False
    assert payload["next_recommended_pass"] == "excalidraw-local-browser-mcp-live-readiness-with-target"


def test_nonlocal_target_is_blocked_without_probe(tmp_path: Path) -> None:
    packet = build_excalidraw_target_contract(
        tmp_path,
        target_url="https://excalidraw.com/",
        generated_at="2026-05-03T19:45:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_CONTRACT_BLOCKED_NONLOCAL
    assert "target_url_must_use_loopback_host" in payload["blocked_reasons"]
    assert payload["target_host"] == "excalidraw.com"
    assert payload["network_probe_attempted"] is False


def test_bad_url_shape_is_blocked_without_probe(tmp_path: Path) -> None:
    packet = build_excalidraw_target_contract(
        tmp_path,
        target_url="127.0.0.1:9230",
        generated_at="2026-05-03T19:50:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_CONTRACT_BLOCKED_BAD_SHAPE
    assert "target_url_must_be_http_or_https" in payload["blocked_reasons"]
    assert payload["network_probe_attempted"] is False


def test_write_contract_writes_only_browser_run_evidence(tmp_path: Path) -> None:
    packet = build_excalidraw_target_contract(
        tmp_path,
        generated_at="2026-05-03T19:55:00Z",
        write_contract=True,
    )
    artifact = Path(packet.contract_artifact_path)
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert artifact.is_file()
    assert artifact.name == "excalidraw_local_target_contract_request_20260503_ready.json"
    assert payload["status"] == EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY
    assert payload["contract_artifact_written"] is True
    assert payload["server_start_attempted"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_is_no_write_without_write_flag(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = contract_main(["--vault-root", str(tmp_path), "--json"])

    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY
    assert payload["contract_artifact_written"] is False
    assert payload["server_start_attempted"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
