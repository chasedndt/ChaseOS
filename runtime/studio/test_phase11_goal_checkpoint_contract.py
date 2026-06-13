"""Tests for the Phase 11 long-running /goal checkpoint contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_goal_checkpoint_contract import (
    DEPENDENCY_REPORT_FIELDS,
    NO_WRITE_PROOF_FIELDS,
    build_phase11_goal_checkpoint_contract,
)


def test_goal_checkpoint_contract_exposes_expected_checkpoint_shape(tmp_path: Path) -> None:
    contract = build_phase11_goal_checkpoint_contract(
        tmp_path,
        surface="Phase 11 Chat / runtime dispatch preview",
        artifacts=["07_LOGS/Agent-Activity/2026-05-11-hermes-optimus-example.md"],
        tests_or_smokes=["PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_phase11_goal_checkpoint_contract.py -q"],
    )
    checkpoint = contract["checkpoint"]

    assert contract["ok"] is True
    assert contract["read_only"] is True
    assert contract["surface"] == "phase11_goal_checkpoint_contract"
    assert checkpoint["heading"] == "## Checkpoint — <UTC timestamp>"
    assert checkpoint["surface"] == "Phase 11 Chat / runtime dispatch preview"
    assert checkpoint["artifacts"] == ["07_LOGS/Agent-Activity/2026-05-11-hermes-optimus-example.md"]
    assert checkpoint["tests_or_smokes"] == [
        "PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_phase11_goal_checkpoint_contract.py -q"
    ]
    assert checkpoint["authority_posture"].startswith("Phase 11 Chat/Studio operator surface only")
    assert checkpoint["next_safe_action"]


def test_goal_checkpoint_no_write_proof_covers_required_denials(tmp_path: Path) -> None:
    contract = build_phase11_goal_checkpoint_contract(tmp_path)
    proof = contract["checkpoint"]["no_write_proof"]
    authority = contract["authority"]

    assert list(proof) == NO_WRITE_PROOF_FIELDS
    assert proof == {
        "provider_call": False,
        "browser_launch": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "runtime_dispatched": False,
        "credential_config_mutated": False,
        "protected_file_written": False,
        "canonical_writeback": False,
    }
    assert authority["provider_calls_allowed"] is False
    assert authority["browser_launch_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["credential_config_mutation_allowed"] is False
    assert authority["protected_file_write_allowed"] is False
    assert authority["canonical_writeback_allowed"] is False


def test_goal_checkpoint_dependency_examples_use_required_handover_fields(tmp_path: Path) -> None:
    contract = build_phase11_goal_checkpoint_contract(tmp_path)
    reports = contract["checkpoint"]["dependency_reports"]

    assert contract["dependency_report_required_fields"] == DEPENDENCY_REPORT_FIELDS
    assert len(reports) >= 3
    for report in reports:
        for field in DEPENDENCY_REPORT_FIELDS:
            assert report[field]
        assert report["complete"] is True

    keys = {report["dependency_key"] for report in reports}
    assert "agent_bus_runtime_dispatch" in keys
    assert "provider_execution" in keys
    assert "protected_or_canonical_writeback" in keys


def test_goal_checkpoint_marks_incomplete_custom_dependency_reports(tmp_path: Path) -> None:
    contract = build_phase11_goal_checkpoint_contract(
        tmp_path,
        dependency_reports=[
            {
                "dependency_key": "browser_policy",
                "missing_contract": "browser launch governance",
                "affected_phase10_or_phase11_surface": "Phase 11 browser preview",
                "lower_phase_owner_or_surface": "browser runtime policy",
                "minimum_proof_needed": "approved bounded launch contract",
                # blocked_action_reason intentionally omitted to prove fixture validation.
            }
        ],
    )
    report = contract["checkpoint"]["dependency_reports"][0]

    assert report["dependency_key"] == "browser_policy"
    assert report["blocked_action_reason"] == ""
    assert report["complete"] is False


def test_goal_checkpoint_template_is_markdown_json_safe_and_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")

    contract = build_phase11_goal_checkpoint_contract(tmp_path)
    encoded = json.dumps(contract, sort_keys=True)
    template = contract["template_markdown"]

    assert "## Checkpoint — <UTC timestamp>" in template
    assert "provider_call=false" in template
    assert "browser_launch=false" in template
    assert "agent_bus_task_written=false" in template
    assert "approval_consumed=false" in template
    assert "runtime_dispatched=false" in template
    assert "credential_config_mutated=false" in template
    assert "protected_file_written=false" in template
    assert "canonical_writeback=false" in template
    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()


def test_goal_checkpoint_builder_does_not_write_artifacts_or_queue_files(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    contract = build_phase11_goal_checkpoint_contract(tmp_path)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    assert contract["ok"] is True
    assert before == after
