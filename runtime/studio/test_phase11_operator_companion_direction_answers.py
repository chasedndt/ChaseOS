"""Tests for approved Phase 11 operator companion direction answers."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_operator_companion_direction_answers import (
    NEXT_RECOMMENDED_PASS,
    OPERATOR_DIRECTION_RELATIVE_PATH,
    build_phase11_operator_companion_direction_answers,
)
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry


def _seed_direction(root: Path) -> None:
    source = Path(__file__).resolve().parent / "chat" / "companions" / "operator-direction.v0.1.json"
    target = root / OPERATOR_DIRECTION_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def test_operator_companion_direction_answers_validate_approved_policy_without_writes(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_operator_companion_direction_answers(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "operator-answer-companion-direction-questions"
    assert payload["summary"]["operator_approved_with_amendments"] is True
    assert payload["summary"]["operator_decision_unanswered_count"] == 0
    assert payload["summary"]["ready_for_roster_ui_preview"] is True
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert payload["readiness"]["provider_calls_blocked"] is True
    assert payload["readiness"]["runtime_dispatch_blocked"] is True
    assert payload["summary"]["separate_companion_memory_allowed"] is True
    assert payload["readiness"]["memory_boundary_contract_defined"] is True
    assert payload["readiness"]["memory_write_executor_required_before_companion_memory_writes"] is True
    assert payload["authority"]["routing_granted"] is False
    assert payload["authority"]["tool_access_granted"] is False
    assert payload["authority"]["memory_access_granted"] is False
    assert payload["authority"]["write_authority_granted"] is False
    assert before == after


def test_operator_companion_direction_answers_block_authority_expansion(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)
    path = tmp_path / OPERATOR_DIRECTION_RELATIVE_PATH
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["authority"]["routing_granted"] = True
    path.write_text(json.dumps(policy), encoding="utf-8")

    payload = build_phase11_operator_companion_direction_answers(tmp_path)

    assert payload["ok"] is False
    assert "operator_direction_authority_expansion_detected" in payload["blocked_reasons"]
    assert payload["summary"]["ready_for_roster_ui_preview"] is False


def test_shell_api_and_registry_expose_operator_companion_direction_answers(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_operator_companion_direction_answers()
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_operator_companion_direction_answers"
    assert "get_phase11_operator_companion_direction_answers" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_operator_companion_direction_answers_ready"] is True
    assert readiness["phase11_operator_companion_roster_ui_preview_unblocked_by_direction"] is True
