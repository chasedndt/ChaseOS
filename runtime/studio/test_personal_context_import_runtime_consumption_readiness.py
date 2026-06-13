"""Tests for Personal Context Import runtime-consumption readiness."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.personal_context_import_runtime_consumption_readiness import (
    NEXT_RECOMMENDED_PASS,
    SURFACE_ID,
    build_personal_context_import_runtime_consumption_readiness,
    format_personal_context_import_runtime_consumption_readiness,
)
from runtime.studio.test_personal_context_import import _seed_import_ready_vault


def _files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_runtime_consumption_readiness_builds_refs_only_packet_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    before = _files(vault)

    payload = build_personal_context_import_runtime_consumption_readiness(vault)
    after = _files(vault)

    assert payload["ok"] is True
    assert payload["surface"] == SURFACE_ID
    assert payload["pass"] == "personal-context-import-runtime-consumption-readiness"
    assert payload["status"] == "COMPLETE / READ-ONLY / RUNTIME CONSUMPTION READINESS / LIVE DISPATCH BLOCKED"
    assert payload["summary"]["runtime_reference_packet_ready"] is True
    assert payload["summary"]["context_ref_count"] > 0
    assert payload["summary"]["raw_context_body_included"] is False
    assert payload["summary"]["raw_full_memory_injection_allowed"] is False
    assert payload["summary"]["source_text_returned"] is False
    assert payload["summary"]["provider_call_performed"] is False
    assert payload["summary"]["agent_bus_task_written"] is False
    assert payload["summary"]["runtime_dispatch_performed"] is False
    assert payload["summary"]["runtime_memory_mutation_performed"] is False
    assert payload["summary"]["personal_map_apply_performed"] is False
    assert payload["summary"]["canonical_mutation_performed"] is False
    assert payload["summary"]["artifact_snapshot_unchanged"] is True
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS

    packet = payload["runtime_reference_packet_preview"]
    assert packet["schema_version"] == "personal_context_runtime_reference_packet.v1"
    assert packet["context_scope"] == "personal_os"
    assert packet["context_refs_only"] is True
    assert packet["raw_context_body_included"] is False
    assert packet["raw_full_memory_injection_allowed"] is False
    assert packet["ready_for_agent_bus_task_creation"] is False
    assert packet["agent_bus_task_created"] is False
    assert packet["provider_execution_allowed"] is False
    assert packet["runtime_dispatch_allowed"] is False
    assert packet["packet_digest"] == payload["digest_proof"]["runtime_reference_packet_digest"]
    assert packet["context_refs"][0]["content_included"] is False
    assert packet["context_refs"][0]["raw_source_text_included"] is False

    assert payload["workspace_mode"]["declares_personal_os"] is True
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert payload["authority"]["runtime_memory_mutation_allowed"] is False
    assert payload["authority"]["personal_map_apply_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert before == after


def test_runtime_consumption_readiness_never_echoes_raw_source_text(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    raw_text = "Sensitive source body that should not be echoed into runtime packets."
    source_path = vault / "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-source-digest.md"
    source_path.write_text(raw_text, encoding="utf-8")

    payload = build_personal_context_import_runtime_consumption_readiness(vault)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["ok"] is True
    assert raw_text not in encoded
    assert "Sensitive source body" not in encoded
    assert payload["runtime_reference_packet_preview"]["raw_context_body_included"] is False
    assert all(item["content_included"] is False for item in payload["runtime_reference_packet_preview"]["context_refs"])


def test_runtime_consumption_readiness_blocks_without_personal_os_workspace_mode(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    (vault / "00_HOME/.workspace-mode.yaml").unlink()

    payload = build_personal_context_import_runtime_consumption_readiness(vault)

    assert payload["ok"] is False
    assert payload["status"] == "BLOCKED / PERSONAL CONTEXT REFERENCES UNAVAILABLE / LIVE DISPATCH BLOCKED"
    assert "workspace_mode_personal_os_not_declared" in payload["blocked_reasons"]
    assert payload["readiness"]["personal_context_import_provider_calls_blocked"] is True
    assert payload["readiness"]["personal_context_import_agent_bus_dispatch_blocked"] is True
    assert payload["readiness"]["personal_context_import_raw_full_memory_injection_blocked"] is True
    assert payload["authority"]["canonical_mutation_allowed"] is False


def test_api_and_registry_expose_runtime_consumption_readiness(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_result = StudioAPI(vault).get_personal_context_import_runtime_consumption_readiness()
    registry = build_native_shell_panel_registry(vault)
    context_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "context-import"), {})

    assert api_result["ok"] is True
    assert api_result["surface"] == "personal_context_import_runtime_consumption_readiness"
    assert api_result["data"]["readiness"]["personal_context_import_runtime_consumption_readiness_ready"] is True
    assert "get_personal_context_import_runtime_consumption_readiness" in (context_panel.get("api_methods") or [])
    assert registry["readiness"]["personal_context_import_runtime_consumption_readiness_ready"] is True
    assert registry["readiness"]["personal_context_import_raw_full_memory_injection_blocked"] is True
    assert registry["readiness"]["personal_context_import_runtime_dispatch_blocked"] is True


def test_format_runtime_consumption_readiness_summarizes_blocked_live_effects(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_import_ready_vault(vault)
    payload = build_personal_context_import_runtime_consumption_readiness(vault)

    text = format_personal_context_import_runtime_consumption_readiness(payload)

    assert "Personal Context Import Runtime Consumption Readiness" in text
    assert "Reference packet ready: True" in text
    assert "Raw full-memory injection allowed: False" in text
    assert "Provider execution allowed: False" in text
    assert "Runtime dispatch allowed: False" in text
