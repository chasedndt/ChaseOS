"""Tests for the Phase 11 operator companion direction packet."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_operator_companion_direction import (
    DECISION_FIELDS,
    NEXT_RECOMMENDED_PASS_WHEN_READY,
    NEXT_RECOMMENDED_PASS_WHEN_UNANSWERED,
    build_phase11_operator_companion_direction,
)


def _files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


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
        "evidence": {"source": "test registry", "profile_digest_required": True},
    }


def _seed_registry(root: Path) -> None:
    path = root / "runtime" / "studio" / "chat" / "companions" / "registry.example.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "registry_id": "studio-companion-registry-example-v1",
                "status": "EXAMPLE / PLANNED / NOT LOADED BY RUNTIME",
                "companions": [
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
        ),
        encoding="utf-8",
    )
    (path.parent / "companion-profile.schema.json").write_text(json.dumps({"type": "object"}), encoding="utf-8")


def test_operator_companion_direction_packet_lists_unanswered_decisions_without_writes(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_operator_companion_direction(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "operator-companion-direction-before-roster-ui"
    assert payload["summary"]["registry_companion_count"] == 3
    assert payload["summary"]["operator_decision_unanswered_count"] == len(DECISION_FIELDS)
    assert payload["summary"]["ready_for_roster_ui_preview"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS_WHEN_UNANSWERED
    assert {"hermes", "openclaw", "claude-code"} == {item["runtime_id"] for item in payload["companion_options"]}
    assert payload["authority"]["companion_roster_ui_mutation_allowed"] is False
    assert payload["authority"]["companion_selection_write_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert before == after


def test_operator_companion_direction_packet_reports_ready_only_when_all_answers_supplied(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    decisions = {field: f"answer-{field}" for field in DECISION_FIELDS}

    payload = build_phase11_operator_companion_direction(tmp_path, operator_decisions=decisions)

    assert payload["summary"]["operator_decision_answered_count"] == len(DECISION_FIELDS)
    assert payload["summary"]["ready_for_roster_ui_preview"] is True
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS_WHEN_READY
    assert payload["readiness"]["selection_target_write_blocked"] is True
    assert payload["authority"]["approval_execution_allowed"] is False


def test_shell_api_and_registry_expose_operator_companion_direction(tmp_path: Path) -> None:
    _seed_registry(tmp_path)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_operator_companion_direction()
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_operator_companion_direction"
    assert "get_phase11_operator_companion_direction" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_operator_companion_direction_packet_ready"] is True
    assert readiness["phase11_operator_companion_roster_ui_blocked_until_direction"] is True
