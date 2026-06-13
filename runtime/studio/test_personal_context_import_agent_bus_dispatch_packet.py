"""Tests for Personal Context Import Agent Bus dispatch packet surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.personal_context_import_agent_bus_dispatch_packet import (
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    _DISPATCH_RECIPIENTS,
    _EXCLUDED_FIELDS,
    _REFERENCE_FIELDS,
    build_personal_context_import_agent_bus_dispatch_packet,
    format_personal_context_import_agent_bus_dispatch_packet,
)


def _write_json(vault: Path, rel: str, obj: dict) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


# --- Basic contract ---

def test_dispatch_packet_ok(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert result["ok"] is True
    assert result["surface"] == SURFACE_ID
    assert result["model_version"] == MODEL_VERSION
    assert result["pass"] == PASS_ID


def test_dispatch_packet_no_task_written(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert result["agent_bus_task_written"] is False
    task_preview = result["task_preview"]
    assert task_preview["agent_bus_task_written"] is False


def test_dispatch_packet_default_recipient_hermes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert result["target_recipient"] == "Hermes"


def test_dispatch_packet_recipient_archon(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault, target_recipient="Archon")
    assert result["target_recipient"] == "Archon"


def test_dispatch_packet_invalid_recipient_defaults_to_hermes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault, target_recipient="unknown")
    assert result["target_recipient"] == "Hermes"


def test_dispatch_packet_excluded_fields_declared(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    excluded = result["excluded_fields"]
    assert "raw_source_text" in excluded
    assert "full_memory_dump" in excluded
    assert "credential_values" in excluded


def test_dispatch_packet_reference_fields_declared(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    reference_fields = result["reference_fields"]
    assert "personal_operator_index_path" in reference_fields
    assert "personal_domains_index_path" in reference_fields


def test_dispatch_packet_no_source_text_in_reference_packet(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    ref = result["reference_packet"]
    assert ref["source_text_included"] is False
    assert ref["full_memory_dump_included"] is False


def test_dispatch_packet_authority_no_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    auth = result["authority"]
    assert auth["agent_bus_task_write_allowed"] is False
    assert auth["runtime_dispatch_allowed"] is False
    assert auth["canonical_writeback_allowed"] is False
    assert auth["secret_values_read"] is False


def test_dispatch_packet_gate_requirements_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    reqs = result["dispatch_gate_requirements"]
    assert any("approval_id" in r for r in reqs)
    assert any("execute=True" in r for r in reqs)


def test_dispatch_packet_next_pass(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_dispatch_packet_digest_is_sha256(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    digest = result["packet_digest"]
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_dispatch_packet_stable_digest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    r1 = build_personal_context_import_agent_bus_dispatch_packet(vault)
    r2 = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert r1["packet_digest"] == r2["packet_digest"]


def test_dispatch_packet_bus_state_reported(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    bus_state = result["bus_state"]
    assert "bus_config_present" in bus_state
    assert "bus_db_present" in bus_state


def test_dispatch_packet_bus_db_present_when_db_exists(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    db_path = vault / "runtime/agent_bus/bus.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"")
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert result["bus_state"]["bus_db_present"] is True
    assert "bus_not_verified" not in result["status"]


def test_dispatch_packet_task_preview_boundary_flags(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    boundary = result["task_preview"]["boundary"]
    assert boundary["raw_source_text_excluded"] is True
    assert boundary["full_memory_dump_excluded"] is True
    assert boundary["credential_read_excluded"] is True


def test_dispatch_packet_recipients_list(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    assert set(result["dispatch_recipients"]) == set(_DISPATCH_RECIPIENTS)


def test_dispatch_packet_runtime_delivery_rules_present(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    rules = result["reference_packet"]["runtime_delivery_rules"]
    assert len(rules) > 0


# --- Format ---

def test_format_output(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    result = build_personal_context_import_agent_bus_dispatch_packet(vault)
    text = format_personal_context_import_agent_bus_dispatch_packet(result)
    assert "Status:" in text
    assert "Packet digest:" in text
    assert "Target recipient:" in text
    assert "Agent Bus task written:" in text
    assert "Next recommended pass:" in text
