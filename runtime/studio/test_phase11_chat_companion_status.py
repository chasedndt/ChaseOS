"""Tests for Phase 11 Chat companion-status read-only contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_companion_status import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_chat_companion_status,
)


def _seed_runtime_profile(root: Path, runtime_id: str = "hermes") -> Path:
    path = root / "06_AGENTS" / f"{runtime_id.title()}-Runtime-Profile.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"title: {runtime_id.title()} Runtime Profile",
                "type: runtime-profile",
                "status: active bounded test lane",
                "version: 0.1",
                "created: 2026-05-11",
                "updated: 2026-05-11",
                f"runtime: {runtime_id}",
                "owner: Optimus",
                "---",
                "",
                f"# {runtime_id.title()} Runtime Profile",
                "",
                "This runtime is a bounded companion candidate.",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _seed_role_card(root: Path) -> Path:
    path = root / "06_AGENTS" / "role-cards" / "hermes-operator-shadow.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "id: hermes-operator-shadow",
                "name: Hermes Operator Shadow Role Card",
                "description: Shadow-only Hermes role card.",
                "allowed_actions:",
                "  - read_declared_context_files",
                "  - generate_markdown_output",
                "forbidden_actions:",
                "  - execute_external_commands",
                "  - promote_to_canonical_state",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_companion_status_reads_profiles_and_role_cards_without_writes(tmp_path: Path) -> None:
    profile = _seed_runtime_profile(tmp_path)
    role = _seed_role_card(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    payload = build_phase11_chat_companion_status(tmp_path, requested_runtime="hermes")

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    card = payload["selected_companion"]

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-chat-companion-status-readonly"
    assert payload["summary"]["selected_runtime_id"] == "hermes"
    assert payload["summary"]["companion_cards_visible"] is True
    assert payload["summary"]["profile_writes_performed"] is False
    assert payload["summary"]["role_card_writes_performed"] is False
    assert card["runtime_id"] == "hermes"
    assert card["display_name"] == "Hermes"
    assert card["runtime_profile_path"] == profile.relative_to(tmp_path).as_posix()
    assert role.relative_to(tmp_path).as_posix() in card["connected_role_card_paths"]
    assert card["authority_ceiling"] == "read_only_status_only"
    assert card["actions_allowed_now"] == []
    assert payload["authority"]["runtime_control_allowed"] is False
    assert payload["authority"]["identity_ledger_mutation_allowed"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert before == after


def test_companion_status_falls_back_to_planned_builtin_cards(tmp_path: Path) -> None:
    payload = build_phase11_chat_companion_status(tmp_path)

    assert payload["ok"] is True
    assert payload["summary"]["registered_companion_count"] >= 3
    assert {card["runtime_id"] for card in payload["companion_cards"]}.issuperset({"hermes", "openclaw", "claude-code"})
    assert payload["summary"]["profile_writes_performed"] is False
    assert "runtime_profile_missing_using_planned_builtin_card" in payload["companion_cards"][0]["status_notes"]


def test_unknown_requested_companion_blocks_cleanly(tmp_path: Path) -> None:
    payload = build_phase11_chat_companion_status(tmp_path, requested_runtime="unknown-runtime")

    assert payload["ok"] is False
    assert payload["summary"]["selected_runtime_id"] == "unknown-runtime"
    assert "requested_companion_runtime_not_registered" in payload["blocked_reasons"]
    assert payload["authority"]["runtime_control_allowed"] is False


def test_companion_status_is_json_safe_and_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _seed_runtime_profile(tmp_path, "openclaw")

    payload = build_phase11_chat_companion_status(tmp_path, requested_runtime="openclaw")
    encoded = json.dumps(payload, sort_keys=True)

    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()


def test_claude_code_companion_resolves_profile_via_config(tmp_path: Path) -> None:
    """claude-code card must show non-empty runtime_profile_path when companion_config.json maps it."""
    profile = tmp_path / "06_AGENTS" / "Archon-Runtime-Profile.md"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(
        "---\nruntime_label: \"Archon / Claude Code Engineering Runtime\"\nstatus: active\n---\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".chaseos" / "companion_config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(
        '{"_schema": "chaseos.companion_config.v1", "companion_profiles": {"claude-code": "06_AGENTS/Archon-Runtime-Profile.md"}}',
        encoding="utf-8",
    )

    payload = build_phase11_chat_companion_status(tmp_path, requested_runtime="claude-code")

    card = payload["selected_companion"]
    assert card["runtime_id"] == "claude-code"
    assert card["runtime_profile_path"] != ""
    assert card["runtime_profile_path"] == "06_AGENTS/Archon-Runtime-Profile.md"
    assert card["runtime_profile_status"] != "missing"


def test_shell_api_and_registry_expose_companion_status(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_chat_companion_status("hermes")
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_chat_companion_status_readonly"
    assert (api_status["data"].get("summary") or {}).get("selected_runtime_id") == "hermes"
    assert "get_phase11_chat_companion_status" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_chat_companion_status_readonly_ready"] is True
    assert readiness["phase11_chat_companion_status_authority_neutral"] is True
    assert readiness["phase11_chat_companion_runtime_control_blocked"] is True
