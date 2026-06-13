from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.runtime_brain_visualization import (
    build_runtime_brain_visualization,
    render_runtime_brain_visualization_html,
    write_runtime_brain_visualization_html,
)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_runtime(vault: Path, runtime_id: str = "hermes") -> None:
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
            "last_updated": "2026-05-03T06:20:00Z",
        },
    )


def test_runtime_brain_visualization_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    model = build_runtime_brain_visualization(
        vault,
        generated_at="2026-05-03T06:20:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_runtime_brain_visualization"
    assert model["summary"]["runtime_card_count"] == 0
    assert model["authority"]["updates_runtime_brains"] is False
    assert model["authority"]["agent_bus_task_write_allowed"] is False
    assert model["authority"]["canonical_writeback_allowed"] is False
    assert model["writes"] == []


def test_runtime_brain_visualization_builds_over_studio_contract(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_runtime(vault)

    model = build_runtime_brain_visualization(vault, runtime_id="hermes")

    assert model["runtime_filter"] == "hermes"
    assert model["summary"]["runtime_card_count"] == 1
    assert model["summary"]["drift_signal_count"] == 1
    assert model["summary"]["repair_incident_candidate_count"] == 1
    assert model["runtime_summaries"][0]["runtime_id"] == "hermes"
    assert model["runtime_summaries"][0]["primary_role"] == "bounded runtime reviewer"
    assert model["dashboard_contract"]["surface"] == "studio_runtime_brain_dashboard_contract"


def test_runtime_brain_visualization_render_contains_core_regions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_runtime(vault)

    html = render_runtime_brain_visualization_html(build_runtime_brain_visualization(vault))

    assert "<!doctype html>" in html
    assert "ChaseOS Pulse Runtime Brain" in html
    assert "Runtime Cards" in html
    assert "Blocked Authority" in html
    assert "bounded runtime reviewer" in html


def test_runtime_brain_visualization_write_stays_inside_runtime_brains_dir(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    _seed_runtime(vault)

    model = write_runtime_brain_visualization_html(
        vault,
        runtime_id="hermes",
        generated_at="2026-05-03T06:20:00+01:00",
    )
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-runtime-brain-hermes.html"
    assert output.parent == vault / "07_LOGS" / "Pulse-Decks" / "runtime-brains"
    assert model["writes"] == [
        "07_LOGS/Pulse-Decks/runtime-brains/2026-05-03-runtime-brain-hermes.html"
    ]


def test_runtime_brain_visualization_rejects_output_outside_runtime_brains_dir(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError):
        write_runtime_brain_visualization_html(
            vault,
            output_path=vault / "07_LOGS" / "bad-runtime-brain.html",
        )
