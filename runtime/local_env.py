"""Local ChaseOS environment-file support.

ChaseOS keeps secret values out of tracked Markdown and JSON truth files, but a
local install may still own a gitignored `.env` file at the vault root. This
module loads that file into process environment variables without printing
values and without overriding variables that were already provided by the OS.
"""

from __future__ import annotations

import os
from pathlib import Path


def find_vault_root(start: Path | None = None) -> Path:
    """Find the nearest ChaseOS vault root from ``start`` or the current cwd."""
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        if (candidate / "runtime").is_dir() and (candidate / ".env.example").exists():
            return candidate
    return current


def _strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
    return value.strip()


def _unquote(value: str) -> str:
    value = _strip_inline_comment(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
        if value and value[0] != "'":
            value = value.replace("\\n", "\n").replace("\\r", "\r")
    return value


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a simple dotenv file without expanding variables or logging values."""
    parsed: dict[str, str] = {}
    if not path.exists():
        return parsed
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
            continue
        parsed[key] = _unquote(value.strip())
    return parsed


def _looks_like_placeholder(value: str) -> bool:
    normalized = value.strip()
    upper = normalized.upper()
    if not normalized:
        return False
    return (
        "YOUR_" in upper
        or "PASTE-" in upper
        or "PASTE_" in upper
        or upper.startswith("SET_")
        or (normalized.startswith("<") and normalized.endswith(">"))
        or upper in {"REPLACE_ME", "TODO", "CHANGEME"}
    )


def load_chaseos_env(start: Path | None = None, *, override: bool = False) -> dict[str, object]:
    """Load root `.env` values into ``os.environ`` and return safe metadata only."""
    vault_root = find_vault_root(start)
    env_path = vault_root / ".env"
    values = parse_env_file(env_path)
    loaded_names: list[str] = []
    skipped_existing: list[str] = []
    skipped_empty: list[str] = []
    skipped_placeholder: list[str] = []
    for key, value in values.items():
        if value == "":
            skipped_empty.append(key)
            continue
        if _looks_like_placeholder(value):
            skipped_placeholder.append(key)
            continue
        if not override and os.environ.get(key):
            skipped_existing.append(key)
            continue
        os.environ[key] = value
        loaded_names.append(key)
    return {
        "env_path": str(env_path),
        "env_file_exists": env_path.exists(),
        "loaded_names": sorted(loaded_names),
        "skipped_existing_names": sorted(skipped_existing),
        "skipped_empty_names": sorted(skipped_empty),
        "skipped_placeholder_names": sorted(skipped_placeholder),
        "secret_values_visible": False,
    }
