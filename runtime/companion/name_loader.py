"""Companion display name loader — reads from runtime profile .md frontmatter.

Fail-open: returns a sensible default if the profile file is missing,
unparseable, or the companion ID is unknown.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


_DEFAULT_PROFILE_PATHS: dict[str, str] = {
    "hermes":      "06_AGENTS/Hermes-Runtime-Profile.md",
    "openclaw":    "06_AGENTS/OpenClaw-Runtime-Profile.md",
    "claude-code": "06_AGENTS/Claude-Code-Runtime-Profile.md",  # new deployments fallback
    "chaser":      "06_AGENTS/ChaserAgent-Runtime-Profile.md",
}

_COMPANION_CONFIG_PATH = ".chaseos/companion_config.json"

_HARDCODED_DEFAULTS: dict[str, str] = {
    "hermes":     "Hermes",
    "openclaw":   "OpenClaw",
    "claude-code": "Claude Code",
    "chaser":     "Chaser Agent",
}


def load_companion_display_name(companion_id: str, vault_root: str | Path) -> str:
    """Read display name from a runtime profile file.

    Priority order for profile path:
      1. companion_profiles[companion_id] in .chaseos/companion_config.json
      2. _DEFAULT_PROFILE_PATHS fallback
      3. 06_AGENTS/<TitleCase>-Runtime-Profile.md guess

    Priority order for the name inside the file:
      runtime_label → title → runtime_id → runtime → default
    """
    vault = Path(vault_root)
    profile_path = _resolve_profile_path(companion_id, vault)

    if not profile_path.exists():
        return _default_display_name(companion_id)

    try:
        text = profile_path.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)

        label = (
            frontmatter.get("runtime_label")
            or frontmatter.get("title", "")
            or frontmatter.get("runtime_id")
            or frontmatter.get("runtime")
            or ""
        )
        name = re.sub(r"\s*Runtime Profile$", "", str(label), flags=re.IGNORECASE).strip()
        if "/" in name:
            name = name.split("/")[0].strip()
        return name or _default_display_name(companion_id)
    except Exception:
        return _default_display_name(companion_id)


def resolve_companion_profile_path(companion_id: str, vault_root: str | Path) -> Path | None:
    """Return the resolved .md profile path for a companion. None if file not found on disk."""
    path = _resolve_profile_path(companion_id, Path(vault_root))
    return path if path.exists() else None


def _resolve_profile_path(companion_id: str, vault_root: Path) -> Path:
    """Return the profile .md path for a companion, checking vault config first."""
    config_path = vault_root / _COMPANION_CONFIG_PATH
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            profiles = cfg.get("companion_profiles") or {}
            override = profiles.get(companion_id)
            if override:
                return vault_root / override
        except Exception:
            pass

    default = _DEFAULT_PROFILE_PATHS.get(companion_id)
    if default:
        return vault_root / default

    # Best-effort guess for future/custom runtimes
    title_cased = "-".join(part.title() for part in companion_id.split("-"))
    return vault_root / f"06_AGENTS/{title_cased}-Runtime-Profile.md"


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter key-value pairs (string values only, no PyYAML dep)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fm_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)

    result: dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            result[key] = val
    return result


def _default_display_name(companion_id: str) -> str:
    if companion_id in _HARDCODED_DEFAULTS:
        return _HARDCODED_DEFAULTS[companion_id]
    return companion_id.replace("-", " ").title()
