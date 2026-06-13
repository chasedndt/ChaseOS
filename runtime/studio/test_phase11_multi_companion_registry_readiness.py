"""Tests for Phase 11 multi-companion registry readiness."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_multi_companion_registry_readiness import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_multi_companion_registry_readiness,
)


def _files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _seed_schema(root: Path) -> Path:
    path = root / "runtime" / "studio" / "chat" / "companions" / "companion-profile.schema.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"type": "object"}), encoding="utf-8")
    return path


def _companion(runtime_id: str, display_name: str) -> dict:
    return {
        "companion_id": f"{runtime_id}-companion",
        "display_name": display_name,
        "runtime_id": runtime_id,
        "status": "available_builtin",
        "avatar": {"kind": "runtime_mark", "asset_path": ""},
        "tone_tags": ["test"],
        "supported_surfaces": ["chat_panel", "dashboard", "runtime_status", "slash_pet", "companion_roster"],
        "authority": {
            "personality_grants_authority": False,
            "runtime_control_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "selection": {
            "can_be_selected": True,
            "selection_requires_approval_executor": True,
            "target_path": "runtime/studio/chat/companion-selection.json",
        },
        "evidence": {
            "source": "test registry",
            "profile_digest_required": True,
        },
    }


def _seed_registry(root: Path, companions: list[dict] | None = None) -> Path:
    path = root / "runtime" / "studio" / "chat" / "companions" / "registry.example.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "registry_id": "studio-companion-registry-example-v1",
        "status": "EXAMPLE / PLANNED / NOT LOADED BY RUNTIME",
        "companions": companions
        if companions is not None
        else [
            _companion("hermes", "Hermes"),
            _companion("openclaw", "OpenClaw"),
            _companion("claude-code", "Claude Code"),
        ],
        "blocked_authority": {
            "runtime_loader_implemented": False,
            "selection_target_written": False,
            "approval_consumed": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
        },
        "next_recommended_pass": "phase11-multi-companion-registry-readiness",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_multi_companion_registry_readiness_validates_registry_without_writes(tmp_path: Path) -> None:
    registry = _seed_registry(tmp_path)
    schema = _seed_schema(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_multi_companion_registry_readiness(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-multi-companion-registry-readiness"
    assert payload["summary"]["registry_path"] == registry.relative_to(tmp_path).as_posix()
    assert payload["summary"]["profile_schema_path"] == schema.relative_to(tmp_path).as_posix()
    assert payload["summary"]["registry_companion_count"] == 3
    assert payload["summary"]["registry_covers_builtin_companions"] is True
    assert payload["summary"]["registry_runtime_ids_have_status_cards"] is True
    assert payload["summary"]["registry_loaded_for_selection"] is False
    assert payload["summary"]["selection_target_written"] is False
    assert payload["summary"]["provider_call_performed"] is False
    assert payload["summary"]["runtime_dispatched"] is False
    assert payload["summary"]["agent_bus_task_written"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert payload["files"]["selection_target_written_now"] is False
    assert payload["readiness"]["multi_companion_registry_readiness_ready"] is True
    assert payload["authority"]["registry_loader_activated"] is False
    assert payload["authority"]["companion_selection_write_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert before == after


def test_multi_companion_registry_readiness_blocks_missing_builtin_runtime(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    _seed_registry(tmp_path, companions=[_companion("hermes", "Hermes"), _companion("openclaw", "OpenClaw")])

    payload = build_phase11_multi_companion_registry_readiness(tmp_path)

    assert payload["ok"] is False
    assert "registry_missing_builtin_runtime_ids:claude-code" in payload["blocked_reasons"]
    assert payload["authority"]["companion_selection_write_allowed"] is False


def test_multi_companion_registry_readiness_blocks_authority_expansion(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    bad = _companion("claude-code", "Claude Code")
    bad["authority"]["provider_calls_allowed"] = True
    _seed_registry(tmp_path, companions=[_companion("hermes", "Hermes"), _companion("openclaw", "OpenClaw"), bad])

    payload = build_phase11_multi_companion_registry_readiness(tmp_path)

    assert payload["ok"] is False
    assert "companions[2].authority.provider_calls_allowed:must_be_false" in payload["blocked_reasons"]
    assert payload["summary"]["provider_call_performed"] is False


def test_multi_companion_registry_readiness_blocks_unknown_runtime_until_status_card_exists(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    _seed_registry(
        tmp_path,
        companions=[
            _companion("hermes", "Hermes"),
            _companion("openclaw", "OpenClaw"),
            _companion("claude-code", "Claude Code"),
            _companion("custom", "Custom"),
        ],
    )

    payload = build_phase11_multi_companion_registry_readiness(tmp_path)

    assert payload["ok"] is False
    assert "registry_runtime_ids_without_status_cards:custom" in payload["blocked_reasons"]
    assert payload["comparison"]["registry_runtime_ids"] == ["claude-code", "custom", "hermes", "openclaw"]


def test_shell_api_and_registry_expose_multi_companion_registry_readiness(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    _seed_registry(tmp_path)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_multi_companion_registry_readiness()
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_multi_companion_registry_readiness"
    assert (api_status["data"].get("summary") or {}).get("registry_companion_count") == 3
    assert "get_phase11_multi_companion_registry_readiness" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_multi_companion_registry_readiness_ready"] is True
    assert readiness["phase11_multi_companion_registry_loader_blocked"] is True
    assert readiness["phase11_multi_companion_registry_selection_write_blocked"] is True
