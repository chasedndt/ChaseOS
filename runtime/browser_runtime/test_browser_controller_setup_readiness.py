from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from runtime.browser_runtime.browser_controller_setup_readiness import (
    ENV_VAR_NAME,
    evaluate_browser_controller_setup_readiness,
    main,
    resolve_browser_executable,
)


def test_blocks_without_browser_executable() -> None:
    result = evaluate_browser_controller_setup_readiness(
        env={},
        which=lambda _: None,
        known_paths=[],
        generated_at="2026-05-03T09:00:00Z",
    )

    assert result.status == "blocked_browser_controller_setup"
    assert result.blockers == ["chromium_compatible_executable_not_found"]
    assert result.selected_executable == ""
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.real_profile_access_attempted is False
    assert result.credential_or_cookie_read_attempted is False
    assert result.browser_harness_used is False
    assert result.canonical_writeback_attempted is False


def test_env_path_candidate_is_ready_without_launch(tmp_path: Path) -> None:
    fake_browser = tmp_path / "chrome.exe"
    fake_browser.write_text("not actually executed", encoding="utf-8")

    result = evaluate_browser_controller_setup_readiness(
        env={ENV_VAR_NAME: str(fake_browser)},
        which=lambda _: None,
        known_paths=[],
        generated_at="2026-05-03T09:05:00Z",
    )

    assert result.status == "browser_controller_setup_ready_no_launch"
    assert result.selected_executable == str(fake_browser)
    assert result.selected_source == "env"
    assert result.next_step == "rerun_safe_local_workflow_replay_execution_proof"
    assert result.operator_handoff["session_env_powershell"].endswith(f"'{fake_browser}'")
    assert result.browser_launch_attempted is False


def test_path_candidate_is_ready_without_env() -> None:
    result = evaluate_browser_controller_setup_readiness(
        env={},
        which=lambda command: "C:/Browsers/msedge.exe" if command == "msedge" else None,
        known_paths=[],
        generated_at="2026-05-03T09:10:00Z",
    )

    assert result.status == "browser_controller_setup_ready_no_launch"
    assert result.selected_executable == "C:/Browsers/msedge.exe"
    assert result.selected_source == "path"
    assert result.env_var_value_present is False


def test_invalid_env_can_fall_back_to_path_candidate(tmp_path: Path) -> None:
    missing = tmp_path / "missing.exe"

    result = evaluate_browser_controller_setup_readiness(
        env={ENV_VAR_NAME: str(missing)},
        which=lambda command: "C:/Browsers/chrome.exe" if command == "chrome" else None,
        known_paths=[],
        generated_at="2026-05-03T09:15:00Z",
    )

    assert result.status == "browser_controller_setup_ready_no_launch"
    assert result.selected_executable == "C:/Browsers/chrome.exe"
    assert result.candidates[0].source == "env"
    assert result.candidates[0].reason == "env_path_not_found"


def test_cli_json_emits_parseable_blocked_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "runtime.browser_runtime.browser_controller_setup_readiness.evaluate_browser_controller_setup_readiness",
        lambda: evaluate_browser_controller_setup_readiness(
            env={},
            which=lambda _: None,
            known_paths=[],
            generated_at="2026-05-03T09:20:00Z",
        ),
    )
    stream = io.StringIO()
    with redirect_stdout(stream):
        code = main(["--json"])

    payload = json.loads(stream.getvalue())
    assert code == 1
    assert payload["status"] == "blocked_browser_controller_setup"
    assert payload["browser_launch_attempted"] is False
    assert payload["operator_handoff"]["safe_replay_command"].startswith(
        "python -m runtime.browser_runtime.workflow_replay_execution_proof"
    )


def test_cdp_live_uses_setup_readiness_resolver(monkeypatch, tmp_path: Path) -> None:
    fake_browser = tmp_path / "chrome.exe"
    fake_browser.write_text("not actually executed", encoding="utf-8")
    monkeypatch.setenv(ENV_VAR_NAME, str(fake_browser))

    assert resolve_browser_executable() == str(fake_browser)


def test_cdp_live_profile_root_prefers_writable_env(monkeypatch, tmp_path: Path) -> None:
    from runtime.browser_runtime.cdp_live import _profile_temp_root

    profile_root = tmp_path / "profiles"
    monkeypatch.setenv("CHASEOS_BROWSER_CDP_PROFILE_ROOT", str(profile_root))

    assert _profile_temp_root() == profile_root
