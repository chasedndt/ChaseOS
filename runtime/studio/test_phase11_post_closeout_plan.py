"""Tests for the Phase 11 post-closeout planning contract."""

from __future__ import annotations

import json

from runtime.studio.phase11_post_closeout_planning import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_post_closeout_planning,
)


def test_post_closeout_plan_is_read_only_and_selection_gated(tmp_path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path)

    assert plan["ok"] is True
    assert plan["surface"] == "phase11_post_closeout_planning"
    assert plan["read_only"] is True
    assert plan["summary"]["remaining_pass_count"] >= 1
    assert plan["summary"]["writes_allowed_now"] is False
    assert plan["summary"]["live_execution_allowed_now"] is False
    assert plan["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert plan["next_pass"]["pass_id"] == NEXT_RECOMMENDED_PASS


def test_post_closeout_plan_tracks_all_deferred_authority_lanes(tmp_path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path)
    passes = {item["pass_id"]: item for item in plan["remaining_passes"]}

    assert {"operator-action-required-no-autonomous-phase11-pass"}.issubset(set(passes))
    completed = {item["pass_id"]: item for item in plan["completed_foundation"]}
    assert completed["phase11-chat-no-hitl-lane-completion-audit"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / NO-HITL LANE COMPLETION AUDIT"
    )
    assert completed["operator-selected-governed-executor-or-deferred-closeout"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / OPERATOR HANDOFF READY"
    )
    assert completed["phase11-chat-readonly-operator-dashboard-aggregate-audit"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT"
    )
    assert completed["phase11-chat-readonly-slash-command-catalog-audit"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT"
    )
    assert completed["phase11-chat-no-hitl-feature-family-selection-audit"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / NO-HITL SELECTION AUDIT"
    )
    assert completed["phase11-chat-conversation-persistence-approval-contract"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / CONVERSATION WRITES BLOCKED"
    )
    assert completed["phase11-chat-approval-queue-write-execution-proof"]["status"] == (
        "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / EXECUTION BLOCKED"
    )
    assert completed["phase11-chat-live-provider-execution-approval-preview"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / PROVIDER CALLS BLOCKED"
    )
    assert completed["phase11-chat-runtime-dispatch-readiness-contract"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / RUNTIME DISPATCH BLOCKED"
    )
    assert completed["phase11-chat-browser-dispatch-readiness-contract"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / BROWSER DISPATCH BLOCKED"
    )
    assert completed["phase11-chat-approval-consumption-readiness-contract"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / APPROVAL CONSUMPTION BLOCKED"
    )
    assert completed["phase11-chat-companion-status-readonly"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / AUTHORITY NEUTRAL"
    )
    assert completed["phase11-chat-companion-status-ui-shell"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED"
    )
    assert completed["phase11-chat-companion-selection-approval-preview"]["status"] == (
        "COMPLETE / APPROVAL-PREVIEW ONLY / VERIFIED / SELECTION WRITES BLOCKED"
    )
    assert completed["phase11-chat-companion-selection-queue-write-readiness"]["status"] == (
        "COMPLETE / APPROVAL-QUEUE WRITE READINESS / VERIFIED / SELECTION WRITES BLOCKED"
    )
    assert completed["phase11-chat-readonly-slash-command-responses"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / NO COMMAND EXECUTION"
    )
    assert completed["phase11-chat-readonly-slash-command-response-ui"]["status"] == (
        "COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED"
    )
    assert completed["phase11-chat-readonly-card-visual-qa"]["status"] == (
        "COMPLETE / VISUAL QA VERIFIED / NO COMMAND EXECUTION"
    )
    assert "operator-selected-governed-executor-or-deferred-closeout" in passes[
        "operator-action-required-no-autonomous-phase11-pass"
    ]["depends_on"]
    assert "requires operator decision before executor/live/target-mutation work" in passes[
        "operator-action-required-no-autonomous-phase11-pass"
    ]["tests"]


def test_post_closeout_plan_denies_mutating_and_live_authority(tmp_path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path)
    authority = plan["authority"]

    assert authority["planning_only"] is True
    assert authority["conversation_persistence_allowed"] is False
    assert authority["approval_queue_write_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "approval_grant_or_execution" in plan["blocked_authority"]
    assert "agent_bus_task_write" in plan["blocked_authority"]


def test_post_closeout_plan_consumes_queue_handoff_contract(tmp_path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path, message="Create a new project")
    source = plan["source_contracts"]["approval_handoff_queue_contract"]

    assert source["surface"] == "phase11_chat_approval_handoff_queue_contract"
    assert source["queue_write_allowed_now"] is False
    assert source["next_recommended_pass"] == "phase11-conversational-command-center-post-closeout-planning"


def test_post_closeout_plan_is_json_safe(tmp_path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path)

    encoded = json.dumps(plan, sort_keys=True)
    assert "sk-" not in encoded
    assert "API_KEY_VALUE" not in encoded.upper()

