"""Tests for no-execution Excalidraw local target response intake."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_target_response as target_response_module
from runtime.browser_runtime.excalidraw_target_response import (
    EXCALIDRAW_TARGET_RESPONSE_ACCEPTED,
    EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_FILE,
    EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_SHAPE,
    EXCALIDRAW_TARGET_RESPONSE_BLOCKED_NONLOCAL,
    EXCALIDRAW_TARGET_RESPONSE_PENDING,
    build_excalidraw_target_response,
    main as response_main,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_module_does_not_import_or_execute_live_browser_mcp_surfaces() -> None:
    source = inspect.getsource(target_response_module)
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


def test_pending_response_without_target_or_writes(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    packet = build_excalidraw_target_response(
        tmp_path,
        generated_at="2026-05-03T20:05:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_PENDING
    assert payload["target_url"] == ""
    assert payload["response_artifact_written"] is False
    assert payload["external_runtime_handoff"]["safe_to_run_next"] is False
    assert payload["server_start_attempted"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_loopback_target_is_accepted_without_probe(tmp_path: Path) -> None:
    packet = build_excalidraw_target_response(
        tmp_path,
        target_url="http://localhost:9230/",
        generated_at="2026-05-03T20:10:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
    assert payload["target_host"] == "localhost"
    assert payload["blocked_reasons"] == []
    assert payload["external_runtime_handoff"]["safe_to_run_next"] is True
    assert payload["network_probe_attempted"] is False
    assert payload["next_recommended_pass"] == "excalidraw-local-browser-mcp-live-readiness-with-target"


def test_response_file_target_is_accepted_without_probe(tmp_path: Path) -> None:
    response_file = tmp_path / "external_response.json"
    response_file.write_text(
        json.dumps({"target_url": "http://127.0.0.1:9230/excalidraw"}),
        encoding="utf-8",
    )
    packet = build_excalidraw_target_response(
        tmp_path,
        response_file=response_file,
        generated_at="2026-05-03T20:15:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
    assert payload["target_url"] == "http://127.0.0.1:9230/excalidraw"
    assert payload["source_response_payload"]["target_url"] == "http://127.0.0.1:9230/excalidraw"
    assert payload["network_probe_attempted"] is False


def test_nonlocal_target_is_blocked_without_probe(tmp_path: Path) -> None:
    packet = build_excalidraw_target_response(
        tmp_path,
        target_url="https://excalidraw.com/",
        generated_at="2026-05-03T20:20:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_BLOCKED_NONLOCAL
    assert "target_url_must_use_loopback_host" in payload["blocked_reasons"]
    assert payload["target_host"] == "excalidraw.com"
    assert payload["public_tunnel_attempted"] is False
    assert payload["network_probe_attempted"] is False


def test_bad_target_shape_is_blocked_without_probe(tmp_path: Path) -> None:
    packet = build_excalidraw_target_response(
        tmp_path,
        target_url="127.0.0.1:9230",
        generated_at="2026-05-03T20:25:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_SHAPE
    assert "target_url_must_be_http_or_https" in payload["blocked_reasons"]
    assert payload["network_probe_attempted"] is False


def test_bad_response_file_is_blocked_without_probe(tmp_path: Path) -> None:
    response_file = tmp_path / "external_response.json"
    response_file.write_text("{not-json", encoding="utf-8")
    packet = build_excalidraw_target_response(
        tmp_path,
        response_file=response_file,
        generated_at="2026-05-03T20:30:00Z",
    )
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_FILE
    assert payload["blocked_reasons"][0].startswith("response_file_unreadable_or_invalid_json")
    assert payload["network_probe_attempted"] is False


def test_write_response_writes_only_pending_input_evidence(tmp_path: Path) -> None:
    packet = build_excalidraw_target_response(
        tmp_path,
        generated_at="2026-05-03T20:35:00Z",
        write_response=True,
    )
    artifact = Path(packet.response_artifact_path)
    payload = json.loads(artifact.read_text(encoding="utf-8"))

    assert artifact.is_file()
    assert "03_INPUTS/Browser-Target-Responses/_pending" in artifact.as_posix()
    assert artifact.name == "excalidraw_local_target_response_20260503_pending.json"
    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_PENDING
    assert payload["response_artifact_written"] is True
    assert payload["server_start_attempted"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_cli_json_is_no_write_without_write_flag(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = response_main(["--vault-root", str(tmp_path), "--json"])

    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_PENDING
    assert payload["response_artifact_written"] is False
    assert payload["network_probe_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
