"""Tests for unified Phase 11 Chat authority-tier controls."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_chat_authority_tier_controls import (
    build_phase11_chat_authority_tier_controls,
    format_phase11_chat_authority_tier_controls,
)
from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
from runtime.studio.shell.api import StudioAPI


def test_authority_tier_controls_surface_groups_all_high_authority_lanes(tmp_path: Path) -> None:
    payload = build_phase11_chat_authority_tier_controls(tmp_path)

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_chat_authority_tier_controls"
    assert payload["summary"]["lane_count"] == 6
    assert payload["summary"]["provider_lane_present"] is True
    assert payload["summary"]["credential_lane_present"] is True
    assert payload["summary"]["runtime_dispatch_lane_present"] is True
    assert payload["summary"]["agent_bus_lane_present"] is True
    assert payload["summary"]["discord_lane_present"] is True
    assert payload["summary"]["external_cron_apply_lane_present"] is True


def test_authority_tier_controls_do_not_grant_live_authority(tmp_path: Path) -> None:
    payload = build_phase11_chat_authority_tier_controls(tmp_path)
    authority = payload["authority"]

    assert authority["direct_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["credential_values_visible"] is False
    assert authority["secret_value_read"] is False
    assert authority["discord_api_calls_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["workflow_dispatch_allowed"] is False
    assert authority["external_scheduler_mutation_allowed"] is False
    assert authority["openclaw_cron_mutation_allowed"] is False
    assert authority["hermes_cron_mutation_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert all(lane["execute_button"]["enabled"] is False for lane in payload["lanes"])


def test_authority_tier_controls_are_embedded_in_chat_panel_contract(tmp_path: Path) -> None:
    contract = build_phase11_chat_panel_contract(tmp_path, message="run this with openclaw and openai")

    controls = contract["chat_authority_tier_controls"]
    assert controls["surface"] == "phase11_chat_authority_tier_controls"
    assert contract["chat_authority_tier_controls_posture"]["authority_tier_controls_visible"] is True
    assert contract["readiness"]["studio_chat_authority_tier_controls_ready"] is True
    assert contract["readiness"]["studio_chat_authority_tier_direct_execution_blocked"] is True
    assert "get_phase11_chat_authority_tier_controls" in contract["api_methods"]


def test_authority_tier_controls_api_method_returns_wrapped_payload(tmp_path: Path) -> None:
    response = StudioAPI(tmp_path).get_phase11_chat_authority_tier_controls("dispatch to hermes", "runtime-task")

    assert response["ok"] is True
    assert response["data"]["surface"] == "phase11_chat_authority_tier_controls"
    assert response["data"]["summary"]["lane_count"] == 6


def test_authority_tier_controls_format_names_lanes(tmp_path: Path) -> None:
    formatted = format_phase11_chat_authority_tier_controls(
        build_phase11_chat_authority_tier_controls(tmp_path)
    )

    assert "Provider Calls" in formatted
    assert "Runtime Dispatch" in formatted
    assert "External Cron Apply" in formatted
