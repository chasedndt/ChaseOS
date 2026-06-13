"""Tests for read-only Studio Runtime Support Loops packets."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.runtime_support_loops import (
    build_proactive_suggestion_packet,
    build_qa_verification_packet,
    build_repair_candidate_packet,
    build_runtime_support_loops_panel,
    build_support_loop_contract,
    build_usage_metrics_packet,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_support_loop_evidence(vault: Path) -> None:
    _write_json(
        vault / "runtime/memory/scorecards/hermes.json",
        {
            "runtime_id": "hermes",
            "scorecard_version": "1.0",
            "status": "seeded",
            "workflow_id": "hermes_operator_today_shadow",
            "runs": [
                {"status": "success", "operator_acceptance_signal": True},
                {"status": "blocked", "approval_requested": True},
                {"status": "success"},
            ],
        },
    )
    _write_json(
        vault / "runtime/memory/repair/hermes.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "execution_repair",
            "runtime_id": "hermes",
            "status": "seeded",
            "repair_patterns": [
                {
                    "id": "repeat-missing-evidence",
                    "failure_pattern": "Repeated QA discrepancy: missing proof artifact reference",
                    "evidence_refs": ["07_LOGS/Agent-Activity/2026-05-12-hermes-proof.md"],
                    "proposed_repair_text": "Ask reviewer to confirm required proof links before closing.",
                    "risk_level": "low",
                }
            ],
        },
    )
    _write_json(
        vault / "runtime/osril/run/run-1.events.jsonl",
        {"event_type": "task_complete", "workflow_id": "hermes_operator_today_shadow"},
    )


def _file_snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _assert_advisory_authority(authority: dict) -> None:
    assert authority["advisory_only"] is True
    assert authority["read_only"] is True
    assert authority["operator_approval_required_for_action"] is True
    assert authority["writes_memory"] is False
    assert authority["writes_agent_bus_tasks"] is False
    assert authority["executes_workflows"] is False
    assert authority["dispatches_runtimes"] is False
    assert authority["consumes_approvals"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["connector_calls_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False


def test_support_loop_contract_exposes_four_read_only_loop_families(tmp_path: Path) -> None:
    contract = build_support_loop_contract(tmp_path)

    assert contract["surface"] == "studio_runtime_support_loops_contract"
    assert contract["possible_writes"] == []
    assert contract["allowed_actions"] == ["inspect-runtime-support-loops-panel"]
    _assert_advisory_authority(contract["authority"])
    assert set(contract["loop_families"]) == {
        "qa_verification",
        "proactive_suggestion",
        "usage_tracking",
        "execution_repair",
    }
    assert "create_agent_bus_task" in contract["blocked_authority"]
    assert "dispatch_runtime" in contract["blocked_authority"]
    assert "canonical_writeback" in contract["blocked_authority"]
    json.dumps(contract)


def test_runtime_support_loop_packets_match_contract_and_do_not_mutate_sources(tmp_path: Path) -> None:
    _seed_support_loop_evidence(tmp_path)
    before = _file_snapshot(tmp_path)

    qa = build_qa_verification_packet(
        tmp_path,
        source_ref="07_LOGS/Agent-Activity/2026-05-12-hermes-proof.md",
        declared_success_criteria=["focused tests pass", "no-write boundary proven"],
        observed_evidence_refs=["runtime/studio/test_runtime_support_loops.py"],
    )
    suggestion = build_proactive_suggestion_packet(
        tmp_path,
        source_ref="runtime/memory/scorecards/hermes.json",
        recommendation_text="Review the missing proof-link pattern before the next Studio closeout.",
    )
    usage = build_usage_metrics_packet(tmp_path, runtime_id="hermes", window="2026-05-12")
    repair = build_repair_candidate_packet(tmp_path, runtime_id="hermes")
    panel = build_runtime_support_loops_panel(tmp_path)

    after = _file_snapshot(tmp_path)
    assert after == before

    assert qa["loop_family"] == "qa_verification"
    assert qa["source_run_ref"] == "07_LOGS/Agent-Activity/2026-05-12-hermes-proof.md"
    assert qa["declared_success_criteria"] == ["focused tests pass", "no-write boundary proven"]
    assert qa["observed_evidence_refs"] == ["runtime/studio/test_runtime_support_loops.py"]
    assert qa["allowed_next_actions"] == ["operator_review"]
    _assert_advisory_authority(qa["authority"])

    assert suggestion["suggestion_id"].startswith("suggestion-")
    assert suggestion["approval_required"] is True
    assert suggestion["suggested_route"] == "operator_review"
    assert "create_agent_bus_task" in suggestion["blocked_authority"]
    _assert_advisory_authority(suggestion["authority"])

    assert usage["metrics_id"].startswith("metrics-")
    assert usage["runtime_id"] == "hermes"
    assert usage["time_window"] == "2026-05-12"
    assert usage["run_count"] == 3
    assert usage["success_count"] == 2
    assert usage["blocked_count"] == 1
    assert usage["approval_requested_count"] == 1
    assert usage["operator_acceptance_signal_count"] == 1
    assert usage["scorecard_refs"] == ["runtime/memory/scorecards/hermes.json"]
    _assert_advisory_authority(usage["authority"])

    assert repair["repair_candidate_id"] == "repeat-missing-evidence"
    assert repair["runtime_id"] == "hermes"
    assert repair["review_required"] is True
    assert repair["apply_allowed"] is False
    assert "apply_repair_memory" in repair["blocked_authority"]
    _assert_advisory_authority(repair["authority"])

    assert panel["surface"] == "studio_runtime_support_loops_panel"
    assert panel["native_panel"]["panel_id"] == "runtime-support-loops"
    assert panel["native_panel"]["read_only"] is True
    assert panel["possible_writes"] == []
    assert panel["allowed_actions"] == ["inspect-runtime-support-loops-panel"]
    assert set(panel["packets"]) == {
        "qa_verification_packet",
        "proactive_suggestion_packet",
        "usage_metrics_packet",
        "repair_candidate_packet",
    }
    assert panel["packets"]["proactive_suggestion_packet"]["approval_required"] is True
    assert panel["packets"]["repair_candidate_packet"]["apply_allowed"] is False
    assert panel["readiness"]["no_memory_mutation"] is True
    assert panel["readiness"]["no_agent_bus_task_write"] is True
    assert panel["readiness"]["no_runtime_dispatch"] is True
    assert panel["readiness"]["no_approval_consumption"] is True
    assert panel["readiness"]["no_provider_or_connector_call"] is True
    assert panel["readiness"]["no_canonical_writeback"] is True
    json.dumps(panel)
