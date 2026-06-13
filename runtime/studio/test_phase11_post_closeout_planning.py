"""Tests for the Phase 11 post-closeout implementation planning contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_post_closeout_planning import (
    NEXT_RECOMMENDED_PASS,
    OPERATOR_ACTION_REQUIRED_NO_AUTONOMOUS_PASS,
    OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS,
    build_phase11_post_closeout_planning,
)


def test_post_closeout_planning_declares_operator_action_required_next_pass(tmp_path: Path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path, message="Create a new project")

    assert plan["ok"] is True
    assert plan["surface"] == "phase11_post_closeout_planning"
    assert plan["pass"] == "phase11-conversational-command-center-post-closeout-planning"
    assert plan["summary"]["foundation_closed"] is True
    assert plan["summary"]["queue_handoff_contract_closed"] is True
    assert plan["summary"]["conversation_persistence_contract_ready"] is True
    assert plan["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert plan["next_pass"]["pass_id"] == NEXT_RECOMMENDED_PASS
    assert NEXT_RECOMMENDED_PASS == OPERATOR_ACTION_REQUIRED_NO_AUTONOMOUS_PASS
    assert plan["next_pass"]["depends_on"] == [OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS]
    assert plan["summary"]["companion_status_readonly_contract_ready"] is True
    assert plan["summary"]["companion_status_ui_shell_ready"] is True
    assert plan["summary"]["can_start_next_pass_now"] is False


def test_post_closeout_planning_orders_dependencies_before_live_execution(tmp_path: Path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path)
    passes = {item["pass_id"]: item for item in plan["remaining_passes"]}
    completed = {item["pass_id"]: item for item in plan["completed_foundation"]}

    assert NEXT_RECOMMENDED_PASS in passes
    assert "phase11-chat-approval-queue-write-execution-proof" in completed
    assert "phase11-chat-live-provider-execution-approval-preview" in completed
    assert "phase11-chat-runtime-dispatch-readiness-contract" in completed
    assert "phase11-chat-browser-dispatch-readiness-contract" in completed
    assert "phase11-chat-approval-consumption-readiness-contract" in completed
    assert passes[NEXT_RECOMMENDED_PASS]["depends_on"] == [OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS]
    assert OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS in completed
    assert "phase11-chat-companion-selection-approval-preview" in completed
    assert "phase11-chat-readonly-slash-command-response-ui" in completed
    assert "Conversation persistence approval contract precedes live provider execution." in plan["dependency_rules"]
    assert len(plan["remaining_passes"]) >= 1


def test_post_closeout_planning_is_read_only_and_blocks_all_authority(tmp_path: Path) -> None:
    plan = build_phase11_post_closeout_planning(tmp_path)
    authority = plan["authority"]

    assert plan["read_only"] is True
    assert authority["planning_only"] is True
    assert authority["conversation_persistence_allowed"] is False
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["vault_writes_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "provider_api_call" in plan["denied_by_this_surface"]


def test_post_closeout_planning_is_json_safe_and_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    plan = build_phase11_post_closeout_planning(tmp_path, message="Use OpenAI")
    encoded = json.dumps(plan, sort_keys=True)

    assert "fixture-secret-not-returned" not in encoded
    assert "API_KEY" not in encoded.upper()


def test_post_closeout_planning_does_not_write_markdown_or_approvals(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    plan = build_phase11_post_closeout_planning(tmp_path)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    assert plan["ok"] is True
    assert before == after
