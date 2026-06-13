from __future__ import annotations

import json
import shutil
from pathlib import Path

from runtime.studio.runtime_brain_dashboard import build_runtime_brain_dashboard_contract


def _temp_vault(name: str) -> Path:
    base = (Path(__file__).resolve().parent / "_tmp_runtime_brain_dashboard").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if base.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {base}")
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _cleanup_temp_vault(vault: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_runtime_brain_dashboard").resolve()
    if vault.resolve().parent != base:
        raise RuntimeError(f"Refusing unsafe test cleanup: {vault}")
    if vault.exists():
        shutil.rmtree(vault)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_runtime(vault: Path, runtime_id: str = "hermes", *, complete: bool = True) -> None:
    _write_json(
        vault / f"runtime/memory/adapters/{runtime_id}/profile.json",
        {
            "runtime_id": runtime_id,
            "status": "seeded",
            "behavioral_profile": {
                "primary_role": "bounded runtime reviewer",
                "strengths": ["reviews Pulse candidates"],
                "known_failure_modes": [
                    {"id": "missing-denial-proof", "description": "Denial paths need proof."}
                ],
                "routing_guidance": ["read role card first"],
                "confidence_signals": ["scorecard clean"],
            },
        },
    )
    _write_json(
        vault / f"runtime/memory/adapters/{runtime_id}/identity-ledger.json",
        {
            "runtime_id": runtime_id,
            "status": "seeded",
            "identity_summary": {"current_actor_posture": "bounded runtime"},
            "behavioral_tendencies": [{"summary": "stays in review lane"}],
            "drift_signals": [{"summary": "watch approval evidence drift"}],
            "governance_boundary": "identity is evidence, not authority",
        },
    )
    _write_json(
        vault / f"runtime/memory/scorecards/{runtime_id}.json",
        {
            "runtime_id": runtime_id,
            "aggregate_stats": {
                "total_executions": 3,
                "success_count": 3,
                "escalated_count": 0,
                "failed_count": 0,
                "reliability_rate": 1.0,
                "overreach_rate": 0.0,
                "compliance_rate": 1.0,
            },
            "last_updated": "2026-05-02T20:50:00Z",
        },
    )
    if complete:
        _write_json(
            vault / f"runtime/memory/nav/{runtime_id}/nav-map.json",
            {
                "runtime_id": runtime_id,
                "status": "active",
                "preferred_read_routes": [{"task_class": "pulse", "route": ["README.md"]}],
                "trusted_zones": ["07_LOGS/"],
                "safe_write_paths": ["07_LOGS/Agent-Activity/"],
                "risk_zones": ["02_KNOWLEDGE/"],
                "escalation_points": ["canonical mutation"],
            },
        )
        _write_json(
            vault / f"runtime/memory/repair/{runtime_id}.json",
            {
                "runtime_id": runtime_id,
                "status": "active",
                "repair_patterns": [],
                "incident_candidates": [{"id": "candidate-1", "state": "candidate"}],
                "governance_boundary": "repair memory is not auto-applied",
            },
        )


def test_runtime_brain_dashboard_contract_is_read_only_and_detailed() -> None:
    vault = _temp_vault("ready")
    try:
        _seed_runtime(vault)
        before = _snapshot(vault)

        model = build_runtime_brain_dashboard_contract(vault)

        assert _snapshot(vault) == before
        assert model["ok"] is True
        assert model["surface"] == "studio_runtime_brain_dashboard_contract"
        assert model["status"] == "runtime_brain_dashboard_contract_ready"
        assert model["metrics"]["runtime_card_count"] == 1
        assert model["metrics"]["ready_runtime_count"] == 1
        assert model["metrics"]["drift_signal_count"] == 1
        assert model["metrics"]["repair_incident_candidate_count"] == 1
        card = model["cards"][0]
        assert card["runtime_id"] == "hermes"
        assert card["profile"]["primary_role"] == "bounded runtime reviewer"
        assert card["identity_ledger"]["current_actor_posture"] == "bounded runtime"
        assert card["runtime_navigation"]["preferred_route_count"] == 1
        assert card["scorecard"]["compliance_rate"] == 1.0
        assert card["authority"]["self_upgrade_active"] is False
        assert model["authority"]["read_only"] is True
        assert model["authority"]["updates_runtime_brains"] is False
        assert model["authority"]["canonical_writeback_allowed"] is False
    finally:
        _cleanup_temp_vault(vault)


def test_runtime_brain_dashboard_filters_runtime() -> None:
    vault = _temp_vault("filter")
    try:
        _seed_runtime(vault, "hermes")
        _seed_runtime(vault, "openclaw")

        model = build_runtime_brain_dashboard_contract(vault, runtime_id="openclaw")

        assert model["runtime_filter"] == "openclaw"
        assert model["metrics"]["runtime_card_count"] == 1
        assert model["cards"][0]["runtime_id"] == "openclaw"
    finally:
        _cleanup_temp_vault(vault)


def test_runtime_brain_dashboard_marks_partial_runtime_without_writes() -> None:
    vault = _temp_vault("partial")
    try:
        _seed_runtime(vault, "claude", complete=False)
        before = _snapshot(vault)

        model = build_runtime_brain_dashboard_contract(vault)

        assert _snapshot(vault) == before
        assert model["status"] == "runtime_brain_dashboard_contract_partial"
        assert model["metrics"]["partial_runtime_count"] == 1
        assert model["metrics"]["missing_family_count"] == 2
        assert "navigation" in model["cards"][0]["missing_families"]
        assert "repair_memory" in model["cards"][0]["missing_families"]
        assert model["authority"]["mutates_memory"] is False
    finally:
        _cleanup_temp_vault(vault)


def test_runtime_brain_dashboard_empty_contract() -> None:
    vault = _temp_vault("empty")
    try:
        model = build_runtime_brain_dashboard_contract(vault)

        assert model["status"] == "runtime_brain_dashboard_contract_empty"
        assert model["metrics"]["runtime_card_count"] == 0
        assert model["authority"]["agent_bus_task_write_allowed"] is False
        assert model["authority"]["rd_workbook_update_allowed"] is False
    finally:
        _cleanup_temp_vault(vault)
