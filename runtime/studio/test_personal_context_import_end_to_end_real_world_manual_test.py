"""Tests for Personal Context Import end-to-end real-world manual test orchestrator."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.studio.personal_context_import_end_to_end_real_world_manual_test import (
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    format_personal_context_import_end_to_end_manual_test,
    run_personal_context_import_end_to_end_manual_test,
)


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


def _write(vault: Path, rel: str, text: str) -> None:
    p = vault / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _seed_minimal_vault(vault: Path) -> None:
    _write(vault, "00_HOME/Now.md", "# Now\n- Sprint focus\n")
    _write(vault, "00_HOME/Personal-Operator-Index.md", "# Personal Operator Index\n")
    _write(vault, "00_HOME/Personal-Domains/Personal-Domains-Index.md", "# Personal Domains Index\n")
    _write(vault, "02_KNOWLEDGE/Knowledge-Index.md", "# Knowledge Index\n")
    _write(vault, "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md", "# Context Intake\n")


# --- Basic contract ---

def test_orchestrator_returns_ok(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    assert isinstance(result["ok"], bool)
    assert result["surface"] == SURFACE_ID
    assert result["model_version"] == MODEL_VERSION
    assert result["pass"] == PASS_ID


def test_orchestrator_covers_all_lanes(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    lane_ids = {r["lane_id"] for r in result["lane_results"]}
    expected_lanes = {
        "personal_context_import",
        "personal_map_apply_readiness",
        "personal_map_approved_apply_executor",
        "runtime_memory_mutation_readiness",
        "runtime_memory_approved_mutation_executor",
        "agent_bus_dispatch_packet",
        "provider_credential_readiness",
        "provider_execution_proof",
    }
    assert lane_ids == expected_lanes


def test_orchestrator_no_writes_performed(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    authority = result["authority"]
    assert authority["provider_call_executed"] is False
    assert authority["file_write_executed"] is False
    assert authority["canonical_writeback_executed"] is False
    assert authority["personal_map_apply_executed"] is False
    assert authority["agent_bus_task_written"] is False
    assert authority["secret_values_read"] is False


def test_orchestrator_next_pass(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    assert result["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_orchestrator_overall_status_present(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    assert result["overall_status"]


def test_orchestrator_lanes_count(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    assert result["lanes_total"] == 8
    assert 0 <= result["lanes_ok"] <= 8


def test_orchestrator_provider_blocker_classified_as_operator_owned(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    with patch.dict(os.environ, {}, clear=True):
        result = run_personal_context_import_end_to_end_manual_test(vault)
    # OPENAI_API_KEY missing → should show as operator_owned_blocker
    op_blockers = result["operator_owned_blockers"]
    assert any("openai" in b.lower() or "credential" in b.lower() for b in op_blockers)


def test_orchestrator_all_lanes_importable(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    code_blockers = result["code_blockers"]
    # No code-level import errors should be present
    import_errors = [b for b in code_blockers if "import_error" in b]
    assert import_errors == [], f"Import errors found: {import_errors}"


def test_orchestrator_has_manual_test_instructions(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    instructions = result["manual_test_instructions"]
    assert "step_1_planner" in instructions
    assert "step_8_provider" in instructions


def test_orchestrator_started_and_finished_timestamps(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    assert result["started_at"]
    assert result["finished_at"]
    assert result["started_at"] <= result["finished_at"]


def test_orchestrator_lane_result_structure(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    for lane in result["lane_results"]:
        assert "lane_id" in lane
        assert "ok" in lane
        assert "status" in lane
        assert "surface" in lane
        assert "blockers" in lane


def test_orchestrator_status_all_green_when_no_code_errors(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    # With no key but no code errors, status should be READY_FOR_OPERATOR_INPUT
    with patch.dict(os.environ, {}, clear=True):
        result = run_personal_context_import_end_to_end_manual_test(vault)
    if not result["code_blockers"]:
        assert "OPERATOR_INPUT" in result["overall_status"] or "ALL_LANES_GREEN" in result["overall_status"]


# --- Format ---

def test_format_output(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    text = format_personal_context_import_end_to_end_manual_test(result)
    assert "Overall status:" in text
    assert "Lanes OK:" in text
    assert "Next recommended pass:" in text


def test_format_shows_lane_statuses(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _seed_minimal_vault(vault)
    result = run_personal_context_import_end_to_end_manual_test(vault)
    text = format_personal_context_import_end_to_end_manual_test(result)
    assert "personal_context_import" in text
    assert "agent_bus_dispatch_packet" in text
    assert "provider_credential_readiness" in text
