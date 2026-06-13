from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.agents.agent_hub import AgentHub, create_runtime_profile
from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern


def test_execution_repair_memory_entry_is_runtime_memory_only() -> None:
    entry = ExecutionRepairMemoryEntry(
        repair_id="erm-openflow-1",
        runtime_id="openflow",
        workflow_id="shopify_product_upload",
        failure_surface="browser",
        failure_type="missing_required_asset",
        failure_summary="Shopify upload could not continue because product images were missing.",
        resolution_summary="Runtime should stop, request manual assets, and avoid publishing.",
        repair_pattern=RepairPattern(
            trigger="Product upload workflow lacks image assets",
            workaround="Create Manual Input Needed card and defer upload.",
            recommended_response=[
                "stop upload before creating incomplete draft",
                "create manual input card",
            ],
            future_prevention=["add product image preflight check"],
        ),
        source_logs=["07_LOGS/Agent-Activity/openflow/shopify-upload.md"],
        related_projects=["BusinessOS"],
    )

    payload = entry.to_dict()
    assert payload["promotion_status"] == "runtime_memory_only"
    assert payload["canonical_writeback_enabled"] is False


def test_execution_repair_memory_can_emit_agent_pulse_card_candidate() -> None:
    entry = ExecutionRepairMemoryEntry(
        repair_id="erm-repo-1",
        runtime_id="codex",
        workflow_id="pulse_reconciliation",
        failure_surface="repo",
        failure_type="schema_gap",
        failure_summary="Pulse card schema lacked master-context source links.",
        resolution_summary="Add source link schema fields without enabling canonical writeback.",
        repair_pattern=RepairPattern(
            trigger="Master context requires source links",
            workaround="Add SourceLinkRef and tests.",
        ),
        source_logs=["07_LOGS/Build-Logs/example.md"],
    )

    card = entry.to_agent_pulse_card(deck_id="agent-pulse")
    payload = card.to_dict()
    assert payload["audience"] == "agent"
    assert payload["card_class"] == "Execution Repair Pattern"
    assert payload["deck_id"] == "agent-pulse"
    assert payload["canonical_writeback_enabled"] is False


def test_runtime_brain_tracks_master_context_learning_fields() -> None:
    profile = create_runtime_profile(
        "codex",
        provider="OpenAI",
        execution_surface="Codex development harness",
        access_mode="repo-aware coding agent",
        trust_tier="Tier 2 ceiling",
        status="registered",
    )
    hub = AgentHub()
    hub.register_profile(profile)
    brain = hub.get_brain("codex")
    assert brain is not None
    brain.known_strengths.append("schema-first reconciliation")
    brain.known_weaknesses.append("requires repo-truth preflight before edits")
    brain.repeated_blockers.append("stale docs after scaffold passes")
    brain.successful_repair_patterns.append("patch docs and schema together")
    brain.workflow_preferences.append("targeted tests before broad tests")
    brain.permission_issues.append("R&D workbook requires explicit approval")
    brain.drift_signals.append("overclaim risk if UI is called complete too early")
    brain.next_improvement_candidates.append("persist review decisions after approval")
    brain.runtime_navigation_map_refs.append("runtime/memory/nav/codex/nav-map.json")
    brain.agent_identity_ledger_refs.append("runtime/memory/adapters/codex/identity-ledger.json")
    brain.execution_repair_memory_refs.append("runtime/memory/repair/codex.json")
    brain.runtime_pulse_history_refs.append("07_LOGS/Pulse-Decks/agents/codex/example.md")

    payload = brain.to_dict()
    assert payload["known_strengths"] == ["schema-first reconciliation"]
    assert payload["execution_repair_memory_refs"] == ["runtime/memory/repair/codex.json"]
    assert payload["self_upgrade_active"] is False
