"""Tests for read-only Studio Runtime Intelligence panels."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.runtime_intelligence_panels import (
    build_agent_identity_panel,
    build_memory_ledger_panel,
    build_provenance_explorer_panel,
    build_runtime_intelligence_panels,
    build_runtime_navigation_map_panel,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_runtime_memory(vault: Path) -> None:
    _write_json(
        vault / "runtime/memory/adapters/codex/profile.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "runtime_id": "codex",
            "status": "active",
            "behavioral_profile": {"summary": "bounded repo-aware coding agent"},
        },
    )
    _write_json(
        vault / "runtime/memory/adapters/codex/identity-ledger.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "agent_identity_ledger",
            "runtime_id": "codex",
            "status": "seeded",
            "updated_at": "2026-05-04T00:00:00Z",
            "identity_summary": {
                "current_actor_posture": "bounded developer",
                "identity_confidence": "configured",
            },
            "behavioral_tendencies": [{"id": "repo_grounded", "summary": "Reads repo truth before editing"}],
            "correction_history": [{"id": "qa_bound", "summary": "Use bounded QA runner"}],
            "drift_signals": [{"id": "overrun", "summary": "Avoid long-lived foreground server QA"}],
            "doctrine_adherence": {"gate_bypass": False},
            "governance_boundary": "Identity ledger is advisory and grants no authority.",
        },
    )
    _write_json(
        vault / "runtime/memory/nav/codex/nav-map.json",
        {
            "runtime_id": "codex",
            "status": "seeded",
            "updated": "2026-05-04",
            "preferred_read_routes": [{"task_class": "code.patch", "route": ["README.md", "runtime"]}],
            "trusted_zones": ["runtime/studio"],
            "safe_write_paths": ["runtime/studio"],
            "risk_zones": ["runtime/policy"],
            "escalation_points": ["Gate"],
            "governance_boundary": "Navigation is advisory and grants no write path.",
        },
    )
    _write_json(
        vault / "runtime/memory/repair/codex.json",
        {
            "schema_version": "1.0",
            "layer": "C",
            "memory_family": "execution_repair",
            "runtime_id": "codex",
            "status": "seeded",
            "repair_patterns": [],
            "incident_candidates": [],
        },
    )
    _write_json(
        vault / "runtime/memory/scorecards/codex.json",
        {
            "runtime_id": "codex",
            "scorecard_version": "1.0",
            "status": "seeded",
            "scores": {},
        },
    )
    _write_json(
        vault / "runtime/tasks/active/task-1.json",
        {
            "task_id": "task-1",
            "runtime_id": "codex",
            "status": "active",
            "objective": "verify runtime intelligence panels",
        },
    )


def _assert_panel_read_only(panel: dict, panel_id: str, allowed_action: str) -> None:
    assert panel["ok"] is True
    assert panel["native_panel"]["mounted"] is True
    assert panel["native_panel"]["panel_id"] == panel_id
    assert panel["native_panel"]["read_only"] is True
    assert panel["authority"]["read_only"] is True
    assert panel["authority"]["writes_memory"] is False
    assert panel["authority"]["writes_provenance"] is False
    assert panel["authority"]["writes_identity_ledger"] is False
    assert panel["authority"]["writes_runtime_navigation_map"] is False
    assert panel["authority"]["writes_agent_bus_tasks"] is False
    assert panel["authority"]["updates_trust_tiers"] is False
    assert panel["authority"]["updates_permission_matrix"] is False
    assert panel["authority"]["approves_memory"] is False
    assert panel["authority"]["provider_calls_allowed"] is False
    assert panel["authority"]["connector_calls_allowed"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
    assert panel["possible_writes"] == []
    assert panel["allowed_actions"] == [allowed_action]


def test_runtime_intelligence_panels_are_read_only_and_json_serializable(tmp_path: Path) -> None:
    _seed_runtime_memory(tmp_path)

    provenance = build_provenance_explorer_panel(tmp_path)
    memory = build_memory_ledger_panel(tmp_path)
    identity = build_agent_identity_panel(tmp_path)
    navigation = build_runtime_navigation_map_panel(tmp_path)
    combined = build_runtime_intelligence_panels(tmp_path)

    _assert_panel_read_only(provenance, "provenance-explorer", "inspect-provenance-explorer-panel")
    _assert_panel_read_only(memory, "memory-ledger", "inspect-memory-ledger-panel")
    _assert_panel_read_only(identity, "agent-identity", "inspect-agent-identity-panel")
    _assert_panel_read_only(navigation, "runtime-navigation", "inspect-runtime-navigation-map-panel")

    assert provenance["readiness"]["no_content_body_read"] is True
    assert memory["readiness"]["memory_approval_allowed"] is False
    assert identity["readiness"]["trust_tier_mutation_allowed"] is False
    assert navigation["readiness"]["runtime_navigation_writeback_allowed"] is False
    assert memory["summary"]["runtime_count"] == 1
    assert memory["summary"]["active_task_context_count"] == 1
    assert identity["summary"]["runtime_count"] == 1
    assert identity["summary"]["drift_signal_count"] == 1
    assert navigation["summary"]["navigation_map_count"] == 1
    assert combined["ok"] is True
    assert combined["readiness"]["runtime_intelligence_panels_mounted"] is True
    assert combined["readiness"]["no_memory_writeback"] is True
    assert combined["readiness"]["no_runtime_navigation_writeback"] is True
    json.dumps(combined)
