from __future__ import annotations

from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    build_personal_map_edge_candidate,
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapEdge, PersonalMapNode
from runtime.pulse.personal_map_visualization import (
    build_personal_map_visualization_contract,
    render_personal_map_visualization_html,
    write_personal_map_visualization_html,
)


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_personal_map_visualization_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    model = build_personal_map_visualization_contract(
        vault,
        generated_at="2026-05-03T06:00:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_personal_map_visualization_contract"
    assert model["summary"]["declared_lane_count"] >= 10
    assert model["summary"]["accepted_node_count"] == 0
    assert model["summary"]["applied_graph_present"] is False
    assert model["authority"]["mutates_personal_map"] is False
    assert model["authority"]["canonical_writeback_allowed"] is False


def test_personal_map_visualization_reads_pending_candidates(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    node = PersonalMapNode(
        node_id="personal_domain_business_test",
        node_type="business_os",
        label="Business Test",
        summary="Candidate business lane.",
        updated_at="2026-05-03T06:00:00+01:00",
    )
    candidate = build_personal_map_node_candidate(
        node,
        reason="test visualization candidate",
        created_at="2026-05-03T06:00:00+01:00",
    )
    persist_personal_map_candidate(vault, candidate)

    model = build_personal_map_visualization_contract(vault)

    assert model["summary"]["candidate_node_count"] == 1
    assert any(item["node_id"] == "personal_domain_business_test" for item in model["nodes"])
    assert model["candidate_queue"]["item_count"] == 1
    assert model["writes"] == []


def test_personal_map_visualization_reports_disconnected_candidate_edges(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    edge = PersonalMapEdge(
        edge_id="edge_missing_nodes",
        source_node_id="missing_source",
        target_node_id="missing_target",
        relation="supports",
        confidence=0.5,
    )
    candidate = build_personal_map_edge_candidate(
        edge,
        reason="test disconnected edge",
        created_at="2026-05-03T06:00:00+01:00",
    )
    persist_personal_map_candidate(vault, candidate)

    model = build_personal_map_visualization_contract(vault)

    assert model["summary"]["candidate_edge_count"] == 1
    assert model["summary"]["disconnected_edge_count"] == 1
    assert model["disconnected_edges"][0]["edge_id"] == "edge_missing_nodes"


def test_personal_map_visualization_render_contains_core_regions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    model = build_personal_map_visualization_contract(vault)
    html = render_personal_map_visualization_html(model)

    assert "<!doctype html>" in html
    assert "ChaseOS Pulse Personal Map" in html
    assert "Map Nodes" in html
    assert "Candidate Edges" in html
    assert "Blocked Authority" in html


def test_personal_map_visualization_write_stays_inside_pulse_personal_map_dir(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    model = write_personal_map_visualization_html(
        vault,
        generated_at="2026-05-03T06:00:00+01:00",
    )
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-personal-map-visualization.html"
    assert output.parent == vault / "07_LOGS" / "Pulse-Decks" / "personal-map"
    assert model["writes"] == ["07_LOGS/Pulse-Decks/personal-map/2026-05-03-personal-map-visualization.html"]


def test_personal_map_visualization_rejects_output_outside_pulse_personal_map_dir(
    tmp_path: Path,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError):
        write_personal_map_visualization_html(
            vault,
            output_path=vault / "07_LOGS" / "bad-personal-map.html",
        )
