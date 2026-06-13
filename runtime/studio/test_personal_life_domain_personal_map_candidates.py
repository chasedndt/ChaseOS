"""Tests for the personal life-domain Personal Map candidate generator."""

from __future__ import annotations

from pathlib import Path

from runtime.memory.candidate_store import build_personal_map_candidate_queue
from runtime.studio.personal_life_domain_personal_map_candidates import (
    REVIEW_DECK_PATH,
    build_personal_life_domain_personal_map_candidates,
    write_personal_life_domain_personal_map_candidates,
)


def test_builds_candidate_only_nodes_and_edges() -> None:
    candidates = build_personal_life_domain_personal_map_candidates()

    assert len(candidates) == 28
    assert sum(1 for candidate in candidates if candidate.candidate_type == "node") == 15
    assert sum(1 for candidate in candidates if candidate.candidate_type == "edge") == 13
    assert all(candidate.status == "pending_review" for candidate in candidates)
    assert all(candidate.candidate_only is True for candidate in candidates)
    assert all(candidate.review_required is True for candidate in candidates)
    assert all(candidate.canonical_writeback_allowed is False for candidate in candidates)
    assert all(candidate.applied_to_personal_map is False for candidate in candidates)
    assert all(candidate.mutates_canonical_state is False for candidate in candidates)
    assert all(candidate.second_datastore_write_allowed is False for candidate in candidates)
    assert {
        candidate.node.node_id
        for candidate in candidates
        if candidate.node is not None
    } >= {
        "domain.fitness_combat_physical_discipline",
        "domain.interests_knowledge_domains",
        "domain.language_learning_global_mobility",
        "domain.networking_social_capital",
        "domain.hardware_systems_future_robotics",
        "preference.interest.piano",
        "preference.interest.geopolitics",
        "preference.interest.history",
        "content_map.youtube_monetization",
    }


def test_write_generates_review_deck_and_read_only_queue(tmp_path: Path) -> None:
    result = write_personal_life_domain_personal_map_candidates(tmp_path)

    assert result["ok"] is True
    assert result["candidate_count"] == 28
    assert result["node_candidate_count"] == 15
    assert result["edge_candidate_count"] == 13
    assert result["written_candidate_count"] == 28
    assert result["canonical_writeback_allowed"] is False
    assert result["personal_map_apply_performed"] is False
    assert (tmp_path / result["candidate_log_path"]).exists()
    assert (tmp_path / REVIEW_DECK_PATH).exists()

    queue = build_personal_map_candidate_queue(tmp_path)
    assert queue.item_count == 28
    assert queue.pending_count == 28
    assert queue.canonical_writeback_allowed is False
    assert queue.second_datastore_write_allowed is False

    rerun = write_personal_life_domain_personal_map_candidates(tmp_path)
    assert rerun["written_candidate_count"] == 0
    assert rerun["skipped_existing_candidate_count"] == 28
