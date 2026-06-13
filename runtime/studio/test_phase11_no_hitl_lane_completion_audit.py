"""Tests for the Phase 11 no-HITL lane completion audit."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_no_hitl_lane_completion_audit import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    build_phase11_no_hitl_lane_completion_audit,
    format_phase11_no_hitl_lane_completion_audit,
)


COMPLETED_PASS_SLUGS = [
    "phase11-readonly-slash-command-responses",
    "phase11-readonly-slash-command-response-ui",
    "phase11-readonly-card-visual-qa",
    "phase11-no-hitl-feature-family-selection-audit",
    "phase11-readonly-slash-command-catalog-audit",
    "phase11-readonly-operator-dashboard-aggregate-audit",
]


def _seed_completion_vault(vault: Path) -> None:
    (vault / "README.md").write_text("# Test Vault\n", encoding="utf-8")
    build_index = vault / "07_LOGS" / "Build-Logs" / "Build-Logs-Index.md"
    history_index = vault / "99_ARCHIVE" / "Documentation-History" / "Documentation-History-Index.md"
    daily = vault / "07_LOGS" / "Daily" / "2026-05-12.md"
    daily_index = vault / "07_LOGS" / "Daily" / "Daily-Index.md"
    activity_index = vault / "07_LOGS" / "Agent-Activity" / "Agent-Activity-Index.md"
    for path in [build_index, history_index, daily, daily_index, activity_index]:
        path.parent.mkdir(parents=True, exist_ok=True)

    build_lines: list[str] = []
    history_lines: list[str] = []
    daily_lines: list[str] = []
    daily_index_lines: list[str] = []
    activity_index_lines: list[str] = []
    for slug in COMPLETED_PASS_SLUGS:
        build_name = f"2026-05-12-ChaseOS-{slug}"
        history_name = f"2026-05-12_{slug}"
        activity_name = f"2026-05-12-codex-{slug}"
        (vault / "07_LOGS" / "Build-Logs" / f"{build_name}.md").write_text(
            "# Build Log\n\n## Tests Run\n\n- Red-first cluster failed as expected.\n\n## Test Results\n\n- passed.\n",
            encoding="utf-8",
        )
        (vault / "99_ARCHIVE" / "Documentation-History" / f"{history_name}.md").write_text(
            "# Documentation History\n\nStatus: COMPLETE.\n",
            encoding="utf-8",
        )
        (vault / "07_LOGS" / "Agent-Activity" / f"{activity_name}.md").write_text(
            "# Agent Activity\n\nBoundaries respected.\n",
            encoding="utf-8",
        )
        build_lines.append(f"[[{build_name}]]")
        history_lines.append(f"[[{history_name}]]")
        daily_lines.extend([f"[[{build_name}]]", f"[[{history_name}]]", f"[[{activity_name}]]"])
        daily_index_lines.extend([f"[[{build_name}]]", f"[[{history_name}]]", f"[[{activity_name}]]"])
        activity_index_lines.append(f"[[{activity_name}]]")

    build_index.write_text("\n".join(build_lines), encoding="utf-8")
    history_index.write_text("\n".join(history_lines), encoding="utf-8")
    daily.write_text("\n".join(daily_lines), encoding="utf-8")
    daily_index.write_text("\n".join(daily_index_lines), encoding="utf-8")
    activity_index.write_text("\n".join(activity_index_lines), encoding="utf-8")

    evidence_roots = {
        "phase11-readonly-card-visual-qa": "phase11-readonly-card-visual-qa",
        "phase11-no-hitl-feature-family-selection-audit": "phase11-no-hitl-feature-family-selection-audits",
        "phase11-readonly-slash-command-catalog-audit": "phase11-readonly-slash-command-catalog-audits",
        "phase11-readonly-operator-dashboard-aggregate-audit": "phase11-dashboard-aggregate-audits",
    }
    for slug, folder in evidence_roots.items():
        evidence_dir = vault / "07_LOGS" / "Studio-Graph-Views" / folder
        evidence_dir.mkdir(parents=True, exist_ok=True)
        (evidence_dir / f"2026-05-12-{slug}.json").write_text(
            json.dumps({"ok": True, "pass": slug}),
            encoding="utf-8",
        )
        (evidence_dir / f"2026-05-12-{slug}.md").write_text("# Evidence\n", encoding="utf-8")


def test_no_hitl_lane_completion_audit_closes_lane_and_maps_objective(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    audit = build_phase11_no_hitl_lane_completion_audit(tmp_path)
    summary = audit["summary"]
    checklist = {item["id"]: item for item in audit["prompt_to_artifact_checklist"]}

    assert audit["ok"] is True
    assert audit["surface"] == "phase11_no_hitl_lane_completion_audit"
    assert audit["pass"] == PASS_ID
    assert audit["status"] == "COMPLETE / READ-ONLY / VERIFIED / NO-HITL LANE COMPLETION AUDIT"
    assert summary["completion_audit_ready"] is True
    assert summary["no_hitl_lane_complete"] is True
    assert summary["eligible_no_hitl_remaining_count"] == 0
    assert summary["can_continue_without_human_in_loop"] is False
    assert summary["human_or_operator_gate_required_for_next_work"] is True
    assert summary["selected_next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert NEXT_RECOMMENDED_PASS == "operator-selected-governed-executor-or-deferred-closeout"
    assert audit["lane_result"]["status"] == "NO_HITL_LANE_COMPLETE / EXECUTOR_LANES_DEFERRED"

    for key in [
        "phase11_feature_family_development_started",
        "only_no_hitl_features_developed",
        "test_driven_development_observed",
        "handovers_and_documentation_maintained",
        "daily_build_history_indexes_connected",
        "completion_audit_performed_against_current_state",
    ]:
        assert checklist[key]["satisfied"] is True


def test_no_hitl_lane_completion_audit_verifies_artifacts_and_deferred_lanes(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    audit = build_phase11_no_hitl_lane_completion_audit(tmp_path)
    artifact_audits = {item["pass_slug"]: item for item in audit["completed_no_hitl_artifacts"]}
    deferred = {item["lane_id"]: item for item in audit["deferred_lanes"]}
    retired = {item["lane_id"]: item for item in audit.get("retired_lanes", [])}

    assert set(COMPLETED_PASS_SLUGS).issubset(set(artifact_audits))
    assert all(item["all_required_artifacts_present"] is True for item in artifact_audits.values())
    assert all(item["index_coverage_complete"] is True for item in artifact_audits.values())
    assert all(item["tdd_evidence_present"] is True for item in artifact_audits.values())
    assert "companion_selection_approval_consumption_executor" not in deferred
    assert "runtime_dispatch_executor" not in deferred
    # live_provider_model_execution is retired (architecture violation), not deferred
    assert "live_provider_model_execution" not in deferred
    assert "live_provider_model_execution" in retired
    assert retired["live_provider_model_execution"]["retired"] is True
    assert "architecture_violation" in retired["live_provider_model_execution"]["retired_reason"]
    assert retired["live_provider_model_execution"]["requires_provider_or_external_call"] is True
    assert deferred["browser_dispatch_executor"]["requires_browser_control"] is True
    assert deferred["approval_target_mutation_executor"]["requires_target_mutation"] is True
    assert all(item["eligible_for_no_hitl"] is False for item in deferred.values())
    assert audit["summary"]["deferred_lane_count"] == 3
    assert audit["summary"]["retired_lane_count"] == 1


def test_no_hitl_lane_completion_audit_authority_is_bounded_and_formatted(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    audit = build_phase11_no_hitl_lane_completion_audit(tmp_path)
    authority = audit["authority"]
    text = format_phase11_no_hitl_lane_completion_audit(audit)

    assert authority["read_only"] is True
    assert authority["completion_audit_only"] is True
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["vault_writes_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "NO_HITL_LANE_COMPLETE" in text
    assert "operator-selected-governed-executor-or-deferred-closeout" in text
    assert "Boundary: completion audit only" in text


def test_no_hitl_lane_completion_audit_writes_bounded_json_and_markdown_evidence(tmp_path: Path) -> None:
    _seed_completion_vault(tmp_path)

    audit = build_phase11_no_hitl_lane_completion_audit(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-no-hitl-lane-completion-audit",
    )

    assert audit["ok"] is True
    assert audit["evidence"]["written"] is True
    assert audit["evidence"]["json_path"].endswith("test-phase11-no-hitl-lane-completion-audit.json")
    assert audit["evidence"]["markdown_path"].endswith("test-phase11-no-hitl-lane-completion-audit.md")
    json_path = tmp_path / audit["evidence"]["json_path"]
    markdown_path = tmp_path / audit["evidence"]["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["surface"] == "phase11_no_hitl_lane_completion_audit"
    assert payload["summary"]["no_hitl_lane_complete"] is True
    assert "Phase 11 No-HITL Lane Completion Audit" in markdown_path.read_text(encoding="utf-8")
