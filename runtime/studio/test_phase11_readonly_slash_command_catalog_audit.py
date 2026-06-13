"""Tests for the Phase 11 read-only slash command catalog audit."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_readonly_slash_command_catalog_audit import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_readonly_slash_command_catalog_audit,
    format_phase11_readonly_slash_command_catalog_audit,
)


EXPECTED_SUPPORTED_COMMANDS = {
    "/dashboard",
    "/map",
    "/vault",
    "/runtime status",
    "/models",
    "/provider",
    "/log",
    "/memory show",
    "/pet",
}


def _seed_vault(vault: Path) -> None:
    (vault / "README.md").write_text("# Test Vault\n\nSee [[Project Alpha]].\n", encoding="utf-8")
    notes = vault / "notes"
    notes.mkdir()
    (notes / "Project Alpha.md").write_text("# Project Alpha\n\nLinked from [[README]].\n", encoding="utf-8")
    profile = vault / "06_AGENTS" / "Hermes-Runtime-Profile.md"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "---\ntitle: Hermes Runtime Profile\nruntime: hermes\nstatus: active test lane\n---\n# Hermes\n",
        encoding="utf-8",
    )


def test_catalog_audit_covers_supported_readonly_commands_without_execution(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_slash_command_catalog_audit(tmp_path)

    summary = audit["summary"]
    supported = {item["command"]: item for item in audit["supported_readonly_commands"]}

    assert audit["ok"] is True
    assert audit["surface"] == "phase11_readonly_slash_command_catalog_audit"
    assert audit["pass"] == "phase11-chat-readonly-slash-command-catalog-audit"
    assert audit["status"] == "COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT"
    assert summary["catalog_audit_ready"] is True
    assert summary["supported_readonly_commands_covered"] is True
    assert summary["supported_readonly_command_count"] >= len(EXPECTED_SUPPORTED_COMMANDS)
    assert EXPECTED_SUPPORTED_COMMANDS.issubset(set(supported))
    assert summary["selected_next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert NEXT_RECOMMENDED_PASS == "phase11-chat-readonly-operator-dashboard-aggregate-audit"

    for command in EXPECTED_SUPPORTED_COMMANDS:
        item = supported[command]
        assert item["read_only_response_ready"] is True, command
        assert item["response_surface_ok"] is True, command
        assert item["response_card_count"] >= 1, command
        assert item["command_execution_performed"] is False
        assert item["approval_action_performed"] is False
        assert item["provider_call_performed"] is False
        assert item["model_call_performed"] is False
        assert item["runtime_dispatch_performed"] is False
        assert item["browser_action_performed"] is False
        assert item["vault_write_performed"] is False
        assert item["agent_bus_task_written"] is False
        assert item["canonical_mutation_performed"] is False


def test_catalog_audit_blocks_write_execution_and_unknown_commands(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_slash_command_catalog_audit(tmp_path)
    blocked = {item["command"]: item for item in audit["blocked_or_unknown_commands"]}

    assert audit["summary"]["write_and_execution_commands_blocked"] is True
    assert audit["summary"]["unknown_commands_help_only"] is True
    assert audit["summary"]["blocked_or_unknown_command_count"] >= 8
    assert {
        "/approve",
        "/reject",
        "/run",
        "/browser",
        "/memory save",
        "/rnd",
        "/new-project",
        "/unknown",
    }.issubset(set(blocked))

    for item in blocked.values():
        assert item["response_surface_ok"] is False
        assert item["read_only_response_ready"] is False
        assert item["response_card_count"] == 0
        assert item["command_execution_performed"] is False
        assert item["approval_action_performed"] is False
        assert item["provider_call_performed"] is False
        assert item["runtime_dispatch_performed"] is False
        assert item["vault_write_performed"] is False
        assert item["agent_bus_task_written"] is False
        assert item["canonical_mutation_performed"] is False

    assert blocked["/approve"]["help_card_id"] == "slash-command-boundary"
    assert blocked["/unknown"]["help_card_id"] == "slash-command-help"
    assert "unknown_slash_command" in blocked["/unknown"]["blocked_reasons"]


def test_catalog_audit_authority_is_bounded_and_format_mentions_boundary(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_slash_command_catalog_audit(tmp_path)
    authority = audit["authority"]
    text = format_phase11_readonly_slash_command_catalog_audit(audit)

    assert authority["read_only"] is True
    assert authority["catalog_audit_only"] is True
    assert authority["command_execution_allowed"] is False
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["model_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["vault_writes_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "Boundary: catalog audit only" in text


def test_catalog_audit_writes_bounded_json_and_markdown_evidence(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_slash_command_catalog_audit(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-readonly-slash-command-catalog-audit",
    )
    evidence = audit["evidence"]

    assert evidence["written"] is True
    assert evidence["json_path"].endswith("test-phase11-readonly-slash-command-catalog-audit.json")
    assert evidence["markdown_path"].endswith("test-phase11-readonly-slash-command-catalog-audit.md")
    json_path = tmp_path / evidence["json_path"]
    markdown_path = tmp_path / evidence["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["surface"] == "phase11_readonly_slash_command_catalog_audit"
    assert "Phase 11 Read-Only Slash Command Catalog Audit" in markdown_path.read_text(encoding="utf-8")
