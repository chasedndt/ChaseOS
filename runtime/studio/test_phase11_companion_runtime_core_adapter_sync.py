"""Tests for Phase 11 companion runtime-core adapter sync."""

from __future__ import annotations

from pathlib import Path

from runtime.companion.policy import SELECTION_TARGET_PATH
from runtime.companion.roster import get_companion
from runtime.studio.phase11_chat_companion_selection_preview import (
    build_phase11_chat_companion_selection_preview,
)
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status
from runtime.studio.phase11_companion_roster_ui_preview import build_phase11_companion_roster_ui_preview
from runtime.studio.phase11_companion_runtime_core_adapter_sync import (
    build_phase11_companion_runtime_core_adapter_sync,
)
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


def test_status_surface_reads_runtime_companion_core_profiles(tmp_path: Path) -> None:
    hermes = get_companion("hermes")

    payload = build_phase11_chat_companion_status(tmp_path, requested_runtime="hermes")
    card = payload["selected_companion"]

    assert payload["ok"] is True
    assert payload["summary"]["core_companion_package_used"] is True
    assert payload["summary"]["core_roster_valid"] is True
    assert card["core_companion_package_used"] is True
    assert card["core_profile_valid"] is True
    assert card["display_name"] == hermes["display_name"]
    assert card["runtime_role"] == hermes["role_summary"]
    assert payload["authority"]["runtime_control_allowed"] is False
    assert payload["authority"]["companion_identity_is_runtime_authority"] is False


def test_roster_preview_uses_core_visuals_and_descriptive_stats_without_writes(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)
    before = _files(tmp_path)
    openclaw = get_companion("openclaw")

    payload = build_phase11_companion_roster_ui_preview(tmp_path, requested_runtime="openclaw")
    after = _files(tmp_path)
    active = payload["active_card"]

    assert payload["ok"] is True
    assert payload["summary"]["core_companion_package_used"] is True
    assert payload["summary"]["core_roster_valid"] is True
    assert active["runtime_id"] == "openclaw"
    assert active["core_companion_package_used"] is True
    assert active["abstract_visual"]["runtime_mark"] == openclaw["visual_mark"]["token"]
    assert active["abstract_visual"]["border_preset"] == openclaw["border_style"]
    assert active["descriptive_metadata"]["stats_are_cosmetic"] is True
    assert active["descriptive_metadata"]["metadata_changes_capability"] is False
    assert payload["authority"]["memory_access_granted"] is False
    assert payload["authority"]["separate_memory_namespace_declared"] is True
    assert payload["authority"]["memory_write_authority_granted"] is False
    assert before == after


def test_selection_preview_uses_core_selection_target_and_registered_ids(tmp_path: Path) -> None:
    payload = build_phase11_chat_companion_selection_preview(
        tmp_path,
        requested_runtime="claude-code",
        current_runtime="hermes",
        message="select Claude Code companion",
    )

    assert payload["ok"] is True
    assert payload["summary"]["core_companion_package_used"] is True
    assert payload["summary"]["registered_companion_ids"] == ["claude-code", "hermes", "openclaw"]
    assert payload["digest_proof"]["digest_material"]["target_path"] == SELECTION_TARGET_PATH.as_posix()
    assert payload["authority"]["companion_selection_write_allowed"] is False
    assert payload["readiness"]["runtime_companion_core_adapter_synced"] is True


def test_runtime_core_adapter_sync_audit_is_readonly_and_authority_neutral(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_runtime_core_adapter_sync(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-companion-runtime-core-adapter-sync"
    assert payload["summary"]["studio_status_synced"] is True
    assert payload["summary"]["studio_registry_synced"] is True
    assert payload["summary"]["studio_roster_synced"] is True
    assert payload["summary"]["selection_preview_synced"] is True
    assert payload["summary"]["selection_target_written"] is False
    assert payload["summary"]["memory_changed"] is False
    assert payload["summary"]["separate_companion_memory_namespace_declared"] is True
    assert payload["summary"]["routing_changed"] is False
    assert payload["summary"]["permissions_changed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["readiness"]["runtime_companion_core_is_source_of_truth"] is True
    assert all(check["ok"] for check in payload["checks"])
    assert before == after
