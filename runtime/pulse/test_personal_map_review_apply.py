from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.personal_map_review_apply import (
    PERSONAL_MAP_GRAPH_PATH,
    build_personal_map_review_apply_surface,
    render_personal_map_review_apply_html,
    write_personal_map_review_apply_html,
)
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _candidate(vault: Path):
    node = PersonalMapNode(
        node_id="personal_domain_business_test",
        node_type="business_os",
        label="Business Test",
        summary="Candidate Personal Map node.",
        updated_at="2026-05-03T09:00:00+01:00",
    )
    candidate = build_personal_map_node_candidate(
        node,
        reason="operator reviewed business domain signal",
        created_at="2026-05-03T09:00:00+01:00",
    )
    persist_personal_map_candidate(vault, candidate)
    return candidate


def test_review_apply_surface_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    model = build_personal_map_review_apply_surface(
        vault,
        generated_at="2026-05-03T09:05:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_personal_map_review_apply_surface"
    assert model["summary"]["candidate_count"] == 0
    assert model["summary"]["dry_run_apply_count"] == 0
    assert model["summary"]["applied_graph_present"] is False
    assert model["authority"]["applies_personal_map_candidates"] is False
    assert model["authority"]["canonical_writeback_allowed"] is False


def test_review_apply_surface_previews_approved_personal_map_candidate(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    candidate = _candidate(vault)
    decision = build_review_decision(
        candidate,
        decision_type="approve_for_future_apply",
        reviewer="operator",
        created_at="2026-05-03T09:06:00+01:00",
    )
    persist_review_decision(vault, decision)
    before_graph = vault / PERSONAL_MAP_GRAPH_PATH

    model = build_personal_map_review_apply_surface(vault)

    assert model["summary"]["candidate_count"] == 1
    assert model["summary"]["approved_candidate_count"] == 1
    assert model["summary"]["dry_run_apply_count"] == 1
    assert model["candidate_rows"][0]["decision_id"] == decision.decision_id
    assert model["candidate_rows"][0]["approved_for_future_apply"] is True
    assert not before_graph.exists()


def test_review_apply_surface_reads_existing_runtime_graph(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    graph_path = vault / PERSONAL_MAP_GRAPH_PATH
    graph_path.parent.mkdir(parents=True)
    graph_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-05-03T09:10:00+01:00",
                "nodes": {"node-a": {"label": "A"}},
                "edges": {"edge-a": {"relation": "supports"}},
            }
        ),
        encoding="utf-8",
    )

    model = build_personal_map_review_apply_surface(vault)

    assert model["graph_summary"]["graph_present"] is True
    assert model["graph_summary"]["node_count"] == 1
    assert model["graph_summary"]["edge_count"] == 1


def test_review_apply_surface_render_contains_review_regions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    model = build_personal_map_review_apply_surface(vault)
    html = render_personal_map_review_apply_html(model)

    assert "<!doctype html>" in html
    assert "ChaseOS Pulse Personal Map Review" in html
    assert "Governed Apply Command" in html
    assert "Applied Runtime Graph" in html
    assert "Blocked Authority" in html


def test_review_apply_surface_write_stays_inside_pulse_review_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    model = write_personal_map_review_apply_html(
        vault,
        generated_at="2026-05-03T09:15:00+01:00",
    )
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-personal-map-review-apply.html"
    assert output.parent == vault / "07_LOGS" / "Pulse-Decks" / "personal-map-review"


def test_review_apply_surface_rejects_output_outside_pulse_review_dir(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError):
        write_personal_map_review_apply_html(
            vault,
            output_path=vault / "07_LOGS" / "bad-personal-map-review.html",
        )
