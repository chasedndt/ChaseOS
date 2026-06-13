"""Tests for no-execution Excalidraw target-response resolver."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.excalidraw_target_response_resolver as resolver_module
from runtime.browser_runtime.excalidraw_target_response_resolver import (
    EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED,
    EXCALIDRAW_TARGET_RESPONSE_RESOLVER_INVALID,
    EXCALIDRAW_TARGET_RESPONSE_RESOLVER_MISSING,
    EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING,
    main as resolver_main,
    resolve_excalidraw_target_response,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _pending_path(root: Path, name: str) -> Path:
    return root / "03_INPUTS/Browser-Target-Responses/_pending" / name


def _response_payload(
    *,
    status: str,
    generated_at: str,
    target_url: str = "",
) -> dict[str, object]:
    return {
        "record_type": "excalidraw_local_target_response",
        "schema_version": "browser.excalidraw_target_response.v1",
        "generated_at": generated_at,
        "status": status,
        "response_artifact_written": True,
        "target_url": target_url,
        "target_host": "127.0.0.1" if target_url else "",
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
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "canonical_writeback_attempted": False,
    }


def test_module_does_not_import_or_execute_live_browser_surfaces() -> None:
    source = inspect.getsource(resolver_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "playwright",
        "import browser_use",
        "from browser_use",
        "import mcp_excalidraw",
        "from mcp_excalidraw",
        "write_text(",
        "open(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_missing_pending_folder_blocks_without_writes(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)
    packet = resolve_excalidraw_target_response(
        tmp_path,
        generated_at="2026-05-04T08:00:00Z",
    )
    after = _snapshot(tmp_path)
    payload = packet.to_dict()

    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_MISSING
    assert payload["selected_response_path"] == ""
    assert "excalidraw_target_response_artifact_missing" in payload["blockers"]
    assert payload["network_probe_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["mcp_invocation_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_prefers_latest_accepted_over_pending(tmp_path: Path) -> None:
    _write_json(
        _pending_path(tmp_path, "excalidraw_local_target_response_20260504_pending.json"),
        _response_payload(
            status="excalidraw_local_target_response_pending_external_runtime",
            generated_at="2026-05-04T08:10:00Z",
        ),
    )
    accepted_path = _pending_path(tmp_path, "excalidraw_local_target_response_20260504_accepted.json")
    _write_json(
        accepted_path,
        _response_payload(
            status="excalidraw_local_target_response_accepted_no_probe",
            generated_at="2026-05-04T08:05:00Z",
            target_url="http://127.0.0.1:9230/",
        ),
    )

    packet = resolve_excalidraw_target_response(tmp_path, generated_at="2026-05-04T08:12:00Z")
    payload = packet.to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED
    assert payload["selected_response_path"] == accepted_path.resolve().as_posix()
    assert payload["selected_response_status"] == "excalidraw_local_target_response_accepted_no_probe"
    assert payload["target_url"] == "http://127.0.0.1:9230/"
    assert payload["next_recommended_pass"] == "excalidraw-local-browser-mcp-live-readiness-with-target"


def test_selects_latest_accepted_by_generated_at(tmp_path: Path) -> None:
    older_path = _pending_path(tmp_path, "excalidraw_local_target_response_20260504_accepted_old.json")
    newer_path = _pending_path(tmp_path, "excalidraw_local_target_response_20260504_accepted_new.json")
    _write_json(
        older_path,
        _response_payload(
            status="excalidraw_local_target_response_accepted_no_probe",
            generated_at="2026-05-04T08:05:00Z",
            target_url="http://127.0.0.1:9230/",
        ),
    )
    _write_json(
        newer_path,
        _response_payload(
            status="excalidraw_local_target_response_accepted_no_probe",
            generated_at="2026-05-04T08:20:00Z",
            target_url="http://localhost:9231/",
        ),
    )

    payload = resolve_excalidraw_target_response(tmp_path).to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED
    assert payload["selected_response_path"] == newer_path.resolve().as_posix()
    assert payload["target_url"] == "http://localhost:9231/"


def test_selects_pending_when_no_accepted_response_exists(tmp_path: Path) -> None:
    pending_path = _pending_path(tmp_path, "excalidraw_local_target_response_20260504_pending.json")
    _write_json(
        pending_path,
        _response_payload(
            status="excalidraw_local_target_response_pending_external_runtime",
            generated_at="2026-05-04T08:30:00Z",
        ),
    )

    payload = resolve_excalidraw_target_response(tmp_path).to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING
    assert payload["selected_response_path"] == pending_path.resolve().as_posix()
    assert payload["target_url"] == ""
    assert payload["next_recommended_pass"] == "external-runtime-provide-excalidraw-target-url"


def test_invalid_files_are_reported_and_not_selected(tmp_path: Path) -> None:
    invalid_path = _pending_path(tmp_path, "excalidraw_local_target_response_20260504_invalid.json")
    invalid_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_path.write_text("{not-json", encoding="utf-8")

    payload = resolve_excalidraw_target_response(tmp_path).to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_INVALID
    assert payload["selected_response_path"] == ""
    assert "no_accepted_or_pending_excalidraw_target_response_found" in payload["blockers"]
    assert payload["candidates_inspected"][0]["candidate_blocker"].startswith("unreadable_or_invalid_json")


def test_explicit_response_path_must_stay_under_pending_inputs(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    _write_json(
        outside,
        _response_payload(
            status="excalidraw_local_target_response_accepted_no_probe",
            generated_at="2026-05-04T08:40:00Z",
            target_url="http://127.0.0.1:9230/",
        ),
    )

    payload = resolve_excalidraw_target_response(tmp_path, response_path=outside).to_dict()

    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_MISSING
    assert payload["selected_response_path"] == ""
    assert any("escapes pending inputs" in blocker for blocker in payload["blockers"])


def test_cli_json_is_read_only_without_writes(tmp_path: Path) -> None:
    pending_path = _pending_path(tmp_path, "excalidraw_local_target_response_20260504_pending.json")
    _write_json(
        pending_path,
        _response_payload(
            status="excalidraw_local_target_response_pending_external_runtime",
            generated_at="2026-05-04T08:50:00Z",
        ),
    )
    before = _snapshot(tmp_path)
    stdout = io.StringIO()

    with redirect_stdout(stdout):
        exit_code = resolver_main(["--vault-root", str(tmp_path), "--json"])

    after = _snapshot(tmp_path)
    payload = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert before == after
    assert payload["status"] == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING
    assert payload["selected_response_path"] == pending_path.resolve().as_posix()
    assert payload["read_only"] is True
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
