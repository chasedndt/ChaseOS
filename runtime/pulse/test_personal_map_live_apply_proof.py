from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.memory.candidate_store import (
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.candidate_apply import _personal_map_graph_path
from runtime.pulse.personal_map_live_apply_proof import (
    build_personal_map_live_apply_proof,
    render_personal_map_live_apply_proof_html,
    write_personal_map_live_apply_proof_html,
)
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    return vault


def _persist_approved_personal_map_candidate(vault: Path) -> str:
    node = PersonalMapNode(
        node_id="node-live-proof-goal",
        node_type="goal",
        label="Complete Personal Map proof",
        summary="Use approved candidates to prove the runtime-memory apply lane.",
    )
    candidate = build_personal_map_node_candidate(
        node,
        reason="Synthetic test proof candidate",
        source_card_id="card-live-proof-001",
    )
    persist_personal_map_candidate(vault, candidate)
    decision = build_review_decision(
        candidate,
        decision_type="approve_for_future_apply",
        reviewer="Codex",
        operator_note="Approved in isolated test fixture.",
    )
    persist_review_decision(vault, decision)
    return candidate.candidate_id


def test_live_apply_proof_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    before = _snapshot(vault)

    model = build_personal_map_live_apply_proof(
        vault,
        generated_at="2026-05-03T13:45:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_personal_map_live_apply_proof"
    assert model["summary"]["candidate_count"] == 0
    assert model["summary"]["ready_for_live_apply_count"] == 0
    assert model["authority"]["runs_live_apply"] is False
    assert model["authority"]["writes_runtime_memory_graph"] is False
    assert model["authority"]["canonical_writeback_allowed"] is False


def test_live_apply_proof_reports_ready_candidate_without_graph_write(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    candidate_id = _persist_approved_personal_map_candidate(vault)
    before = _snapshot(vault)

    model = build_personal_map_live_apply_proof(vault)

    assert _snapshot(vault) == before
    assert model["summary"]["candidate_count"] == 1
    assert model["summary"]["approved_candidate_count"] == 1
    assert model["summary"]["ready_for_live_apply_count"] == 1
    assert model["summary"]["dry_run_apply_count"] == 1
    assert model["summary"]["live_apply_ready"] is True
    assert model["ready_candidate_rows"][0]["candidate_id"] == candidate_id
    assert not _personal_map_graph_path(vault).exists()


def test_live_apply_proof_detects_already_applied_candidate(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    _persist_approved_personal_map_candidate(vault)
    from runtime.pulse.candidate_apply import apply_reviewed_candidates

    result = apply_reviewed_candidates(vault, dry_run=False, candidate_kind="personal_map")
    result.validate()
    assert _personal_map_graph_path(vault).exists()

    model = build_personal_map_live_apply_proof(vault)

    assert model["summary"]["already_applied_count"] == 1
    assert model["summary"]["ready_for_live_apply_count"] == 0
    assert model["summary"]["graph_present"] is True
    graph = json.loads(_personal_map_graph_path(vault).read_text(encoding="utf-8"))
    assert "node-live-proof-goal" in graph["nodes"]


def test_live_apply_proof_render_contains_expected_regions(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    _persist_approved_personal_map_candidate(vault)

    html = render_personal_map_live_apply_proof_html(
        build_personal_map_live_apply_proof(vault)
    )

    assert "<!doctype html>" in html
    assert "ChaseOS Pulse Personal Map Live Apply Proof" in html
    assert "Operator Commands" in html
    assert "Candidate Proof Rows" in html
    assert "Blocked Authority" in html
    assert "chaseos pulse apply-decisions --kind personal_map --live" in html


def test_live_apply_proof_write_stays_inside_proof_dir(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    _persist_approved_personal_map_candidate(vault)

    model = write_personal_map_live_apply_proof_html(
        vault,
        generated_at="2026-05-03T13:50:00+01:00",
    )
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-personal-map-live-apply-proof.html"
    assert output.parent == (
        vault
        / "07_LOGS"
        / "Pulse-Decks"
        / "personal-map-live-apply-proof"
    )


def test_live_apply_proof_rejects_output_outside_proof_dir(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    with pytest.raises(ValueError):
        write_personal_map_live_apply_proof_html(
            vault,
            output_path=vault / "07_LOGS" / "bad-personal-map-live-proof.html",
        )
