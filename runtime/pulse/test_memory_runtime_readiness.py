from __future__ import annotations

from dataclasses import replace
import json
import shutil
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.memory_runtime_readiness import (
    MEMORY_RUNTIME_READINESS_LANES,
    build_pulse_memory_runtime_readiness,
)


def _temp_vault(name: str) -> Path:
    base = (Path(__file__).resolve().parent / "_tmp_memory_runtime_readiness").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if base.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {base}")
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _cleanup_temp_vault(vault: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_memory_runtime_readiness").resolve()
    if vault.resolve().parent != base:
        raise RuntimeError(f"Refusing unsafe test cleanup: {vault}")
    if vault.exists():
        shutil.rmtree(vault)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_complete_runtime(vault: Path, runtime_id: str = "hermes") -> None:
    _write_json(vault / f"runtime/memory/adapters/{runtime_id}/profile.json", {"runtime_id": runtime_id})
    _write_json(
        vault / f"runtime/memory/adapters/{runtime_id}/identity-ledger.json",
        {"runtime_id": runtime_id, "memory_family": "agent_identity_ledger"},
    )
    _write_json(vault / f"runtime/memory/nav/{runtime_id}/nav-map.json", {"runtime_id": runtime_id})
    _write_json(vault / f"runtime/memory/repair/{runtime_id}.json", {"runtime_id": runtime_id})
    _write_json(vault / f"runtime/memory/scorecards/{runtime_id}.json", {"runtime_id": runtime_id})


def _seed_personal_map_candidate(vault: Path) -> None:
    node = PersonalMapNode(
        node_id="personal_domain_business_os",
        node_type="business_os",
        label="Business OS",
        summary="Business operating domain.",
    )
    candidate = build_personal_map_node_candidate(
        node,
        reason="Pulse surfaced a Business OS map candidate.",
        source_card_id="pulse-card-readiness-001",
        created_at="2026-05-02T20:30:00+01:00",
    )
    persist_personal_map_candidate(vault, candidate)


def _seed_feedback_rules(vault: Path, *, invalid: bool = False) -> None:
    path = vault / "runtime/memory/feedback-rules/accepted-signals.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "rule_id": "feedback-rule-001",
                "rule_type": "boost_card_type",
                "target_type": "card_type",
                "target": "runtime_blocker",
                "scope": "user",
                "status": "active",
            }
        )
    ]
    if invalid:
        lines.append("{invalid-json")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_memory_runtime_readiness_empty_is_read_only() -> None:
    vault = _temp_vault("empty")
    try:
        before = _snapshot(vault)

        surface = build_pulse_memory_runtime_readiness(
            vault,
            generated_at="2026-05-02T20:30:00+00:00",
        )

        assert _snapshot(vault) == before
        assert surface.readiness_status == "empty"
        assert {lane.lane_id for lane in surface.lanes} == MEMORY_RUNTIME_READINESS_LANES
        assert surface.read_only is True
        assert surface.mutates_memory is False
        assert surface.canonical_writeback_allowed is False
        assert surface.rd_workbook_update_allowed is False
    finally:
        _cleanup_temp_vault(vault)


def test_memory_runtime_readiness_summarizes_runtime_candidates_and_rules_without_writes() -> None:
    vault = _temp_vault("ready")
    try:
        _seed_complete_runtime(vault)
        _seed_personal_map_candidate(vault)
        _seed_feedback_rules(vault)
        before = _snapshot(vault)

        surface = build_pulse_memory_runtime_readiness(
            vault,
            generated_at="2026-05-02T20:35:00+00:00",
        )

        assert _snapshot(vault) == before
        assert surface.readiness_status == "ready"
        assert surface.runtime_count == 1
        assert surface.runtime_card_count == 1
        assert surface.runtime_cards[0].runtime_id == "hermes"
        assert surface.runtime_cards[0].status == "ready"
        assert surface.family_counts["profile"] == 1
        assert surface.family_counts["identity_ledger"] == 1
        assert surface.family_counts["navigation"] == 1
        assert surface.family_counts["repair_memory"] == 1
        assert surface.personal_map_candidate_count == 1
        assert surface.feedback_rule_count == 1
        assert surface.applies_personal_map_candidates is False
        assert surface.applies_feedback_rules is False
    finally:
        _cleanup_temp_vault(vault)


def test_memory_runtime_readiness_marks_incomplete_runtime_partial() -> None:
    vault = _temp_vault("partial")
    try:
        _write_json(vault / "runtime/memory/adapters/openclaw/profile.json", {"runtime_id": "openclaw"})

        surface = build_pulse_memory_runtime_readiness(
            vault,
            generated_at="2026-05-02T20:40:00+00:00",
        )

        assert surface.readiness_status == "partial"
        assert surface.runtime_cards[0].runtime_id == "openclaw"
        assert surface.runtime_cards[0].status == "partial"
        assert "identity_ledger" in surface.runtime_cards[0].missing_families
        assert "navigation" in surface.runtime_cards[0].missing_families
    finally:
        _cleanup_temp_vault(vault)


def test_memory_runtime_readiness_blocks_invalid_feedback_rule_json() -> None:
    vault = _temp_vault("blocked")
    try:
        _seed_complete_runtime(vault)
        _seed_feedback_rules(vault, invalid=True)

        surface = build_pulse_memory_runtime_readiness(
            vault,
            generated_at="2026-05-02T20:45:00+00:00",
        )

        assert surface.readiness_status == "blocked"
        assert surface.feedback_rule_count == 1
        assert surface.feedback_rule_error_count == 1
        feedback_lane = next(lane for lane in surface.lanes if lane.lane_id == "feedback_rules")
        assert feedback_lane.status == "blocked"
    finally:
        _cleanup_temp_vault(vault)


def test_memory_runtime_readiness_rejects_authority_flags() -> None:
    vault = _temp_vault("authority")
    try:
        surface = build_pulse_memory_runtime_readiness(vault)

        for flag in (
            "mutates_memory",
            "applies_feedback_rules",
            "applies_personal_map_candidates",
            "applies_execution_repair_candidates",
            "updates_runtime_brains",
            "grants_permissions",
            "agent_bus_task_write_allowed",
            "runtime_dispatch_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
            "memory_approval_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_created",
            "rd_workbook_update_allowed",
        ):
            with pytest.raises(ValueError):
                replace(surface, **{flag: True}).validate()
    finally:
        _cleanup_temp_vault(vault)
