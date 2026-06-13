from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.agents.execution_repair_memory import (
    ExecutionRepairMemoryEntry,
    RepairPattern,
)
from runtime.memory.feedback_rules import FeedbackRule, evaluate_feedback
from runtime.pulse.card_schema import (
    CARD_AUDIENCES,
    FEEDBACK_TYPES,
    SHARED_CARD_CLASSES,
    USER_CARD_CLASSES,
    EvidenceRef,
    PulseCard,
    PulseDeck,
    RecommendedAction,
    SourceLinkRef,
)


ROOT = Path(__file__).resolve().parents[2]


def test_reconciled_card_schema_keeps_master_audiences_and_fields() -> None:
    assert {"user", "agent", "shared_coordination"}.issubset(CARD_AUDIENCES)
    assert "shared" in CARD_AUDIENCES
    assert "Schedule Catch-Up" in USER_CARD_CLASSES
    assert "Truth-State Warning" in SHARED_CARD_CLASSES
    assert "promote_to_memory" in FEEDBACK_TYPES
    assert "link_to_agent_brain" in FEEDBACK_TYPES

    deck = PulseDeck(
        deck_id="audit-shared-coordination",
        audience="shared_coordination",
        cards=[
            PulseCard(
                card_id="truth-warning-1",
                deck_id="audit-shared-coordination",
                audience="shared_coordination",
                card_class="Truth-State Warning",
                title="Pulse reconciliation needs audit",
                summary="The schema pass needs a guard that keeps it proposal-only.",
                why_it_matters="Pulse must remain future-facing intelligence, not canonical mutation.",
                evidence=[
                    EvidenceRef(
                        source_path="06_AGENTS/ChaseOS-Pulse-Master-Context-Gap-Audit.md",
                        source_type="audit_doc",
                        summary="Master-context reconciliation gap audit exists.",
                        trust_label="internal_doc",
                    )
                ],
                source_links=[
                    SourceLinkRef(
                        label="Reconciliation audit",
                        path="06_AGENTS/ChaseOS-Pulse-Master-Context-Gap-Audit.md",
                    )
                ],
                recommended_actions=[
                    RecommendedAction(
                        action_id="run-truth-audit",
                        label="Run truth-state audit",
                        action_type="run_truth_audit",
                        requires_operator_approval=False,
                        mutates_canonical_state=False,
                    )
                ],
                confidence=0.8,
            )
        ],
    )

    payload = deck.to_dict()
    card = payload["cards"][0]
    assert payload["canonical_writeback_enabled"] is False
    assert card["type"] == "truth_state_warning"
    assert card["source_links"][0]["path"].endswith("Gap-Audit.md")
    assert card["writeback_status"] == "draft_only"
    assert card["promotion_status"] == "not_promoted"


def test_recommended_actions_cannot_hide_canonical_mutation() -> None:
    action = RecommendedAction(
        action_id="bad-action",
        label="Mutate without approval",
        action_type="create_task",
        requires_operator_approval=False,
        mutates_canonical_state=True,
    )

    try:
        action.validate()
    except ValueError as exc:
        assert "canonical mutations require operator approval" in str(exc)
    else:
        raise AssertionError("canonical mutation without approval should fail")


def test_feedback_rules_remain_durable_candidates_only() -> None:
    result = evaluate_feedback("turn_into_task")
    rule = FeedbackRule(
        rule_id="audit-feedback-rule",
        rule_type="link_agent_brain_context",
        target_type="runtime_id",
        target="hermes",
        source_card_id="truth-warning-1",
        reason="Feedback can create a candidate link, not mutate AgentHub.",
    )

    payload = rule.to_dict()
    assert result.requires_operator_review is True
    assert result.canonical_writeback_allowed is False
    assert payload["status"] == "candidate"
    assert payload["canonical_writeback_allowed"] is False


def test_execution_repair_memory_stays_runtime_memory_only() -> None:
    entry = ExecutionRepairMemoryEntry(
        repair_id="audit-repair-1",
        runtime_id="openflow-placeholder",
        workflow_id="business_os_upload",
        failure_surface="browser",
        failure_type="missing_required_asset",
        failure_summary="A browser workflow cannot continue without product images.",
        resolution_summary="Stop the workflow and create a manual input card.",
        repair_pattern=RepairPattern(
            trigger="Product image batch is missing",
            workaround="Defer upload and request manual input.",
            recommended_response=["create Manual Input Needed card"],
            future_prevention=["add product asset preflight check"],
        ),
        source_logs=["07_LOGS/Agent-Activity/openflow-placeholder/example.md"],
    )

    card = entry.to_agent_pulse_card(deck_id="agent-audit")
    assert entry.to_dict()["canonical_writeback_enabled"] is False
    assert card.to_dict()["card_class"] == "Execution Repair Pattern"
    assert card.to_dict()["canonical_writeback_enabled"] is False


def test_pulse_schedule_manifests_are_chaseos_owned_inactive_intent() -> None:
    manifests = [
        ROOT / "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
        ROOT / "runtime/schedules/manifests/hermes_runtime_pulse.yaml",
    ]
    for path in manifests:
        text = path.read_text(encoding="utf-8")
        assert "owner: chaseos" in text
        assert "enabled: false" in text
        assert "schedule_owner: chaseos" in text
        assert "openclaw_cron_owner: false" in text
        assert "executor_is_adapter_only: true" in text
        assert "if_machine_off: catch_up_once" in text
        assert "if_server_down: queue_pending" in text
        assert "if_runtime_unavailable: defer_to_review" in text
        assert "if_approval_timeout: create_review_card" in text

    assert not (
        ROOT / "runtime/schedules/manifests/openflow_runtime_pulse.yaml"
    ).exists()
