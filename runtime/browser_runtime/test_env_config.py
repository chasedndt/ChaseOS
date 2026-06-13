"""Tests for non-secret Browser Runtime env resolution."""

from __future__ import annotations

import runtime.browser_runtime.env_config as env_config


def test_browser_use_cli_env_prefers_process_env(monkeypatch) -> None:
    monkeypatch.setattr(env_config, "_read_windows_user_env", lambda name: "user-value")
    executable, source = env_config.browser_use_cli_executable_from_env(
        env={env_config.BROWSER_USE_CLI_ENV: "process-value"}
    )

    assert executable == "process-value"
    assert source == "process"


def test_browser_use_cli_env_falls_back_to_windows_user_env(monkeypatch) -> None:
    monkeypatch.setattr(env_config, "_read_windows_user_env", lambda name: "user-value")
    executable, source = env_config.browser_use_cli_executable_from_env(env={})

    assert executable == "user-value"
    assert source == "windows_user"


def test_browser_use_cli_env_uses_default_when_unset(monkeypatch) -> None:
    monkeypatch.setattr(env_config, "_read_windows_user_env", lambda name: "")
    executable, source = env_config.browser_use_cli_executable_from_env(env={})

    assert executable == "browser-use"
    assert source == "default"

