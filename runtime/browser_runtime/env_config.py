"""Non-secret Browser Runtime environment resolution helpers.

This module is intentionally narrow: it only resolves ChaseOS browser runtime
environment values that are expected to be non-secret paths/config selectors.
It must not be used for API keys, credentials, tokens, or cookies.
"""

from __future__ import annotations

import os
from collections.abc import Mapping


BROWSER_USE_CLI_ENV = "CHASEOS_BROWSER_USE_CLI"


def _read_windows_user_env(name: str) -> str:
    if os.name != "nt":
        return ""
    try:
        import winreg  # type: ignore[import-not-found]

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
        ) as key:
            value, _value_type = winreg.QueryValueEx(key, name)
    except (OSError, ImportError):
        return ""
    return str(value or "").strip()


def read_nonsecret_env_value(
    name: str,
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    """Read a non-secret ChaseOS env value from process env or Windows user env."""

    env_map = os.environ if env is None else env
    process_value = str(env_map.get(name, "") or "").strip()
    if process_value:
        return process_value, "process"

    user_value = _read_windows_user_env(name)
    if user_value:
        return user_value, "windows_user"

    return "", "unset"


def browser_use_cli_executable_from_env(
    *,
    default: str = "browser-use",
    env: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    value, source = read_nonsecret_env_value(BROWSER_USE_CLI_ENV, env=env)
    if value:
        return value, source
    return default, "default"

