"""Tests for the Phase 11 companion memory boundary contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_companion_memory_boundary_contract import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_boundary_contract,
)
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


def test_companion_memory_boundary_contract_is_readonly_and_declares_namespaces(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_boundary_contract(tmp_path)
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-companion-memory-boundary-contract"
    assert payload["summary"]["separate_companion_memory_enabled_by_operator"] is True
    assert payload["summary"]["separate_memory_namespace_declared"] is True
    assert payload["summary"]["memory_namespace_count"] == 3
    assert payload["summary"]["memory_writes_allowed_now"] is False
    assert payload["summary"]["approval_required_for_memory_write"] is True
    assert payload["summary"]["memory_files_written_by_this_surface"] is False
    assert payload["summary"]["sample_allowed_candidate_valid"] is True
    assert payload["summary"]["sample_allowed_candidate_write_allowed"] is False
    assert payload["summary"]["sample_denied_candidates_blocked"] is True
    assert payload["authority"]["memory_write_authority_granted"] is False
    assert payload["authority"]["approval_queue_write_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert payload["readiness"]["companion_memory_boundary_contract_ready"] is True
    assert payload["readiness"]["companion_memory_writes_blocked"] is True
    assert payload["future_approval_contract"]["next_pass"] == NEXT_RECOMMENDED_PASS
    assert before == after


def test_companion_memory_boundary_blocks_without_direction_policy(tmp_path: Path) -> None:
    _seed_registry(tmp_path)

    payload = build_phase11_companion_memory_boundary_contract(tmp_path)

    assert payload["ok"] is False
    assert "operator_companion_direction_policy_not_ready" in payload["blocked_reasons"]
    assert payload["readiness"]["companion_memory_boundary_contract_ready"] is False


def test_shell_api_registry_and_chat_panel_embed_memory_boundary(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _seed_direction(tmp_path)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_boundary_contract()
    panel = StudioAPI(tmp_path).get_phase11_chat_panel_contract("/pet hermes", "chat-answer")
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((item for item in registry.get("panels", []) if item.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_boundary_contract"
    assert (api_status["data"]["summary"])["separate_memory_namespace_declared"] is True
    assert "get_phase11_companion_memory_boundary_contract" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_boundary_contract_ready"] is True
    assert readiness["phase11_companion_memory_writes_blocked"] is True
    assert panel["data"]["companion_memory_boundary_contract"]["surface"] == "phase11_companion_memory_boundary_contract"
    assert panel["data"]["companion_memory_boundary_posture"]["memory_writes_allowed_now"] is False
