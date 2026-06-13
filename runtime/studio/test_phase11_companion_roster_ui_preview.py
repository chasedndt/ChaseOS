"""Tests for the Phase 11 companion roster UI preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_companion_roster_ui_preview import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_roster_ui_preview,
)
from runtime.studio.phase11_operator_companion_direction_answers import OPERATOR_DIRECTION_RELATIVE_PATH
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


def test_companion_roster_ui_preview_builds_readonly_cards_without_writes(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_roster_ui_preview(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-companion-roster-ui-preview"
    assert payload["summary"]["operator_direction_captured"] is True
    assert payload["summary"]["roster_ui_preview_ready"] is True
    assert payload["summary"]["roster_card_count"] == 3
    assert payload["summary"]["active_companion_first"] is True
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert [card["runtime_id"] for card in payload["roster_cards"]] == ["hermes", "openclaw", "claude-code"]
    assert all(card["abstract_visual"]["kind"] == "runtime_mark" for card in payload["roster_cards"])
    assert all(card["descriptive_metadata"]["metadata_changes_capability"] is False for card in payload["roster_cards"])
    assert payload["authority"]["companion_selection_write_allowed_by_this_surface"] is False
    assert payload["authority"]["routing_granted"] is False
    assert payload["authority"]["tool_access_granted"] is False
    assert payload["authority"]["memory_access_granted"] is False
    assert payload["authority"]["separate_memory_namespace_declared"] is True
    assert payload["authority"]["memory_write_authority_granted"] is False
    assert payload["authority"]["write_authority_granted"] is False
    assert payload["readiness"]["memory_boundary_defined_for_companion_memory"] is True
    assert payload["readiness"]["memory_boundary_contract_required_before_companion_memory_writes"] is True
    assert payload["readiness"]["separate_companion_memory_namespace_declared"] is True
    assert payload["readiness"]["companion_memory_writes_blocked"] is True
    assert before == after


def test_companion_roster_ui_preview_blocks_without_operator_direction(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    path = tmp_path / OPERATOR_DIRECTION_RELATIVE_PATH
    if path.exists():
        path.unlink()

    payload = build_phase11_companion_roster_ui_preview(tmp_path)

    assert payload["ok"] is False
    assert "operator_direction_answers_not_ready" in payload["blocked_reasons"]
    assert payload["summary"]["roster_ui_preview_ready"] is False


def test_shell_api_and_registry_expose_companion_roster_ui_preview(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_roster_ui_preview()
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_roster_ui_preview"
    assert "get_phase11_companion_roster_ui_preview" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_roster_ui_preview_ready"] is True
    assert readiness["phase11_companion_roster_ui_preview_selection_write_blocked"] is True
