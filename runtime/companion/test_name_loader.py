"""Tests for runtime/companion/name_loader.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.companion.name_loader import (
    load_companion_display_name,
    resolve_companion_profile_path,
    _default_display_name,
    _parse_frontmatter,
    _resolve_profile_path,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_profile(path: Path, frontmatter: str, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")


def _write_config(vault: Path, profiles: dict) -> None:
    cfg_path = vault / ".chaseos" / "companion_config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        json.dumps({"_schema": "chaseos.companion_config.v1", "companion_profiles": profiles}),
        encoding="utf-8",
    )


# ── _parse_frontmatter ────────────────────────────────────────────────────────

def test_parse_frontmatter_basic() -> None:
    text = "---\ntitle: Hermes Runtime Profile\nruntime: hermes\n---\n\n# Body"
    result = _parse_frontmatter(text)
    assert result["title"] == "Hermes Runtime Profile"
    assert result["runtime"] == "hermes"


def test_parse_frontmatter_no_fence() -> None:
    result = _parse_frontmatter("# No frontmatter here")
    assert result == {}


def test_parse_frontmatter_quoted_value() -> None:
    text = '---\nruntime_label: "Archon / Claude Code Engineering Runtime"\n---\n'
    result = _parse_frontmatter(text)
    assert result["runtime_label"] == "Archon / Claude Code Engineering Runtime"


def test_parse_frontmatter_single_quoted() -> None:
    text = "---\nruntime: 'hermes'\n---\n"
    result = _parse_frontmatter(text)
    assert result["runtime"] == "hermes"


# ── _default_display_name ─────────────────────────────────────────────────────

def test_default_display_name_known_ids() -> None:
    assert _default_display_name("hermes") == "Hermes"
    assert _default_display_name("openclaw") == "OpenClaw"
    assert _default_display_name("claude-code") == "Claude Code"
    assert _default_display_name("chaser") == "Chaser Agent"


def test_default_display_name_unknown_id() -> None:
    assert _default_display_name("my-custom-runtime") == "My Custom Runtime"


# ── load_companion_display_name — no profile file ─────────────────────────────

def test_returns_default_when_profile_missing(tmp_path: Path) -> None:
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "Hermes"


def test_returns_default_when_claude_code_profile_missing(tmp_path: Path) -> None:
    name = load_companion_display_name("claude-code", tmp_path)
    assert name == "Claude Code"


def test_returns_default_when_chaser_profile_missing(tmp_path: Path) -> None:
    name = load_companion_display_name("chaser", tmp_path)
    assert name == "Chaser Agent"


# ── load_companion_display_name — from profile file ───────────────────────────

def test_reads_hermes_name_from_title_field(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md",
        "title: Hermes Runtime Profile\nruntime: hermes",
    )
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "Hermes"


def test_reads_openclaw_name_from_title_field(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "OpenClaw-Runtime-Profile.md",
        "title: OpenClaw Runtime Profile\nruntime: openclaw",
    )
    name = load_companion_display_name("openclaw", tmp_path)
    assert name == "OpenClaw"


def test_reads_archon_name_from_runtime_label(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Archon-Runtime-Profile.md",
        'runtime_label: "Archon / Claude Code Engineering Runtime"\nruntime_id: archon',
    )
    _write_config(tmp_path, {"claude-code": "06_AGENTS/Archon-Runtime-Profile.md"})
    name = load_companion_display_name("claude-code", tmp_path)
    assert name == "Archon"


def test_strips_runtime_profile_suffix(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md",
        "title: Hermes Runtime Profile",
    )
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "Hermes"


def test_slash_separator_takes_first_segment(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Archon-Runtime-Profile.md",
        'runtime_label: "Archon / Claude Code Engineering Runtime"',
    )
    _write_config(tmp_path, {"claude-code": "06_AGENTS/Archon-Runtime-Profile.md"})
    name = load_companion_display_name("claude-code", tmp_path)
    assert name == "Archon"


def test_falls_back_to_runtime_field_when_no_title(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md",
        "runtime: hermes",
    )
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "hermes"


# ── companion_config.json override ───────────────────────────────────────────

def test_companion_config_overrides_profile_path(tmp_path: Path) -> None:
    custom_path = tmp_path / "06_AGENTS" / "MyCustomArchon.md"
    _write_profile(custom_path, 'runtime_label: "MyArchon / Engineering Runtime"')
    _write_config(tmp_path, {"claude-code": "06_AGENTS/MyCustomArchon.md"})
    name = load_companion_display_name("claude-code", tmp_path)
    assert name == "MyArchon"


def test_companion_config_maps_hermes(tmp_path: Path) -> None:
    custom = tmp_path / "06_AGENTS" / "CustomHermes.md"
    _write_profile(custom, "title: CustomHermes Runtime Profile")
    _write_config(tmp_path, {"hermes": "06_AGENTS/CustomHermes.md"})
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "CustomHermes"


def test_companion_config_maps_openclaw(tmp_path: Path) -> None:
    custom = tmp_path / "06_AGENTS" / "CustomClaw.md"
    _write_profile(custom, "title: CustomClaw Runtime Profile")
    _write_config(tmp_path, {"openclaw": "06_AGENTS/CustomClaw.md"})
    name = load_companion_display_name("openclaw", tmp_path)
    assert name == "CustomClaw"


def test_corrupt_companion_config_falls_back_to_default(tmp_path: Path) -> None:
    cfg_path = tmp_path / ".chaseos" / "companion_config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("{invalid json", encoding="utf-8")
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "Hermes"


# ── Future/custom runtime extension ──────────────────────────────────────────

def test_future_runtime_returns_title_case_default(tmp_path: Path) -> None:
    name = load_companion_display_name("my-new-runtime", tmp_path)
    assert name == "My New Runtime"


def test_future_runtime_reads_profile_when_registered(tmp_path: Path) -> None:
    custom = tmp_path / "06_AGENTS" / "My-New-Runtime-Runtime-Profile.md"
    _write_profile(custom, "title: My New Runtime Runtime Profile")
    name = load_companion_display_name("my-new-runtime", tmp_path)
    assert name == "My New Runtime"


def test_corrupt_profile_falls_back_to_default(tmp_path: Path) -> None:
    profile = tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_bytes(b"\xff\xfe\x00")  # non-UTF-8
    name = load_companion_display_name("hermes", tmp_path)
    assert name == "Hermes"


# ── resolve_companion_profile_path ───────────────────────────────────────────

def test_resolve_companion_profile_path_returns_path_when_exists(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md",
        "title: Hermes Runtime Profile",
    )
    path = resolve_companion_profile_path("hermes", tmp_path)
    assert path is not None
    assert path.exists()
    assert path.name == "Hermes-Runtime-Profile.md"


def test_resolve_companion_profile_path_returns_none_when_missing(tmp_path: Path) -> None:
    path = resolve_companion_profile_path("hermes", tmp_path)
    assert path is None


def test_resolve_companion_profile_path_claude_code_via_config(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Archon-Runtime-Profile.md",
        'runtime_label: "Archon / Claude Code Engineering Runtime"',
    )
    _write_config(tmp_path, {"claude-code": "06_AGENTS/Archon-Runtime-Profile.md"})
    path = resolve_companion_profile_path("claude-code", tmp_path)
    assert path is not None
    assert path.name == "Archon-Runtime-Profile.md"


def test_resolve_companion_profile_path_claude_code_no_config(tmp_path: Path) -> None:
    path = resolve_companion_profile_path("claude-code", tmp_path)
    assert path is None


def test_resolve_companion_profile_path_accepts_str_vault_root(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md",
        "title: Hermes Runtime Profile",
    )
    path = resolve_companion_profile_path("hermes", str(tmp_path))
    assert path is not None
    assert path.exists()
