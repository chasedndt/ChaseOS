from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_no_hitl_feature_family_selection_audit import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    build_phase11_no_hitl_feature_family_selection_audit,
    format_phase11_no_hitl_feature_family_selection_audit,
)


def test_no_hitl_feature_family_selection_audit_selects_readonly_catalog_candidate(
    tmp_path: Path,
) -> None:
    report = build_phase11_no_hitl_feature_family_selection_audit(tmp_path)

    assert report["ok"] is True
    assert report["surface"] == "phase11_no_hitl_feature_family_selection_audit"
    assert report["pass"] == PASS_ID
    assert report["summary"]["no_human_in_loop_required"] is False
    assert report["summary"]["operator_selection_required"] is False
    assert report["summary"]["eligible_candidate_count"] >= 1
    assert report["summary"]["deferred_candidate_count"] >= 4
    assert report["summary"]["selected_next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert report["selected_candidate"]["pass_id"] == NEXT_RECOMMENDED_PASS
    assert report["selected_candidate"]["authority_class"] == "read_only"
    assert report["selected_candidate"]["requires_human_in_loop"] is False
    assert report["selected_candidate"]["can_develop_without_human_in_loop"] is True
    assert report["selected_candidate"]["tdd_ready"] is True
    assert report["selected_candidate"]["writes_allowed"] == ["evidence_json", "evidence_markdown"]
    assert "phase11-chat-readonly-card-visual-qa" in report["selected_candidate"]["depends_on"]

    rejected = {item["pass_id"]: item for item in report["deferred_candidates"]}
    assert rejected["phase11-chat-companion-selection-approval-consumption-executor"][
        "requires_human_in_loop"
    ] is True
    assert rejected["phase11-chat-live-provider-execution"][
        "requires_external_or_provider"
    ] is True
    assert rejected["phase11-chat-runtime-dispatch-executor"][
        "requires_runtime_dispatch"
    ] is True
    assert rejected["phase11-chat-browser-dispatch-executor"][
        "requires_browser_control"
    ] is True
    assert rejected["phase11-chat-approval-target-mutation-executor"][
        "requires_target_mutation"
    ] is True


def test_no_hitl_feature_family_selection_audit_maps_prompt_objective_and_authority(
    tmp_path: Path,
) -> None:
    report = build_phase11_no_hitl_feature_family_selection_audit(tmp_path)
    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    authority = report["authority"]

    assert checklist["only_no_human_in_loop_features"]["satisfied"] is True
    assert checklist["test_driven_development"]["satisfied"] is True
    assert checklist["handover_documentation_indexes"]["satisfied"] is True
    assert checklist["complete_feature_pass"]["satisfied"] is True
    assert authority["read_only"] is True
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["model_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["vault_writes_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False


def test_no_hitl_feature_family_selection_audit_write_evidence_is_log_only(
    tmp_path: Path,
) -> None:
    report = build_phase11_no_hitl_feature_family_selection_audit(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-no-hitl-feature-family-selection-audit",
    )

    assert report["ok"] is True
    assert report["evidence"]["written"] is True
    assert report["evidence"]["json_path"].endswith(".json")
    assert report["evidence"]["markdown_path"].endswith(".md")
    assert "07_LOGS/Studio-Graph-Views/phase11-no-hitl-feature-family-selection-audits" in report[
        "evidence"
    ]["json_path"]
    json_path = tmp_path / report["evidence"]["json_path"]
    markdown_path = tmp_path / report["evidence"]["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["selected_candidate"]["pass_id"] == NEXT_RECOMMENDED_PASS
    assert "No-HITL Feature-Family Selection Audit" in markdown_path.read_text(encoding="utf-8")


def test_no_hitl_feature_family_selection_audit_text_output_states_deferred_live_paths(
    tmp_path: Path,
) -> None:
    report = build_phase11_no_hitl_feature_family_selection_audit(tmp_path)
    output = format_phase11_no_hitl_feature_family_selection_audit(report)

    assert "Phase 11 No-HITL Feature-Family Selection Audit" in output
    assert f"selected_next: {NEXT_RECOMMENDED_PASS}" in output
    assert "approval_consumption_allowed: False" in output
    assert "provider_calls_allowed: False" in output
    assert "runtime_dispatch_allowed: False" in output
    assert "Boundary: selection audit only" in output
