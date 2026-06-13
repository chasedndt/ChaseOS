"""Tests for runtime/pulse/candidate_apply.py — Pulse Candidate Apply."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    ExecutionRepairMemoryCandidate,
    REPAIR_CANDIDATE_ROOT,
    persist_execution_repair_memory_candidate,
)
from runtime.memory.candidate_store import (
    PERSONAL_MAP_CANDIDATE_ROOT,
    PersonalMapCandidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.candidate_apply import (
    APPLY_REGISTRY_ROOT,
    PulseCandidateApplyItem,
    PulseCandidateApplyResult,
    _APPLY_DECISION_TYPES,
    _apply_registry_path,
    _feedback_signals_path,
    _load_apply_registry,
    _personal_map_graph_path,
    _save_apply_registry,
    apply_reviewed_candidates,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback import (
    FEEDBACK_CANDIDATE_ROOT,
    PulseFeedbackCandidate,
    PulseFeedbackRecord,
    persist_feedback_candidate,
)
from runtime.pulse.review_decision_log import (
    REVIEW_DECISION_BLOCKED_EFFECTS,
    DECISION_FOLLOWUP_SIGNALS,
    PulseCandidateReviewDecision,
    persist_review_decision,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_vault() -> Path:
    """Create a minimal vault structure in a temp dir."""
    tmp = tempfile.mkdtemp()
    vault = Path(tmp)
    for subdir in [
        "07_LOGS/Pulse-Decks/review-decisions",
        "07_LOGS/Pulse-Decks/feedback-candidates",
        "07_LOGS/Pulse-Decks/memory-candidates/personal-map",
        "07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/hermes",
        "07_LOGS/Pulse-Decks/apply-registry",
        "07_LOGS/Operator-Briefs",
        "00_HOME",
    ]:
        (vault / subdir).mkdir(parents=True, exist_ok=True)
    # Minimal Now.md so boot doesn't fail
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    return vault


def _make_feedback_candidate(vault: Path) -> PulseFeedbackCandidate:
    """Persist a feedback candidate and return it."""
    deck_dir = vault / "07_LOGS" / "Pulse-Decks" / "users"
    deck_dir.mkdir(parents=True, exist_ok=True)
    deck_path = deck_dir / "test-deck.json"
    deck_path.write_text(json.dumps({"cards": []}), encoding="utf-8")

    record = PulseFeedbackRecord(
        feedback_id="fb-001",
        card_id="card-abc",
        feedback_type="thumbs_up",
        operator_note="useful card",
        created_at=now_utc(),
    )
    persist_feedback_candidate(
        vault,
        record,
        source_deck_path=deck_path,
    )
    from runtime.pulse.feedback import load_feedback_candidates
    candidates = load_feedback_candidates(vault)
    return candidates[-1]


def _make_personal_map_candidate(vault: Path) -> PersonalMapCandidate:
    node = PersonalMapNode(
        node_id="node-chase-goal",
        node_type="goal",
        label="Build ChaseOS",
        summary="Deliver Phase 9 Operator Runtime",
    )
    from runtime.memory.candidate_store import build_personal_map_node_candidate
    candidate = build_personal_map_node_candidate(
        node,
        reason="Observed from Pulse deck signal",
        source_card_id="card-goal-001",
    )
    persist_personal_map_candidate(vault, candidate)
    return candidate


def _make_repair_candidate(vault: Path, runtime_id: str = "hermes") -> ExecutionRepairMemoryCandidate:
    entry = ExecutionRepairMemoryEntry(
        repair_id="repair-001",
        runtime_id=runtime_id,
        workflow_id="operator_today",
        failure_surface="autonomous_workflow",
        failure_type="timeout",
        failure_summary="Now.md read timed out",
        resolution_summary="Re-read after short delay",
        repair_pattern=RepairPattern(
            trigger="slow filesystem",
            workaround="retry read",
        ),
    )
    from runtime.agents.repair_candidate_store import build_execution_repair_memory_candidate
    candidate = build_execution_repair_memory_candidate(
        entry,
        reason="Recurring timeout pattern observed",
        source_card_id="card-repair-001",
    )
    persist_execution_repair_memory_candidate(vault, candidate)
    return candidate


def _make_review_decision(
    vault: Path,
    candidate: object,
    decision_type: str,
) -> PulseCandidateReviewDecision:
    """Build and persist a review decision for a candidate."""
    from runtime.pulse.review_decision_log import build_review_decision
    decision = build_review_decision(
        candidate,
        decision_type=decision_type,
        reviewer="Hermes",
        operator_note="Reviewed and approved.",
    )
    persist_review_decision(vault, decision)
    return decision


# ── TestResultDataclass ───────────────────────────────────────────────────────

class TestResultDataclass:
    def test_governance_flags_immutable(self):
        r = PulseCandidateApplyResult(
            run_at=now_utc(),
            applied_count=0,
            skipped_already_applied=0,
            skipped_no_candidate=0,
            skipped_no_apply_decision=0,
            error_count=0,
        )
        r.validate()

    def test_canonical_writeback_rejected(self):
        r = PulseCandidateApplyResult(
            run_at=now_utc(),
            applied_count=0,
            skipped_already_applied=0,
            skipped_no_candidate=0,
            skipped_no_apply_decision=0,
            error_count=0,
            canonical_writeback_allowed=True,
        )
        with pytest.raises(ValueError, match="canonical writeback"):
            r.validate()

    def test_mutates_canonical_state_rejected(self):
        r = PulseCandidateApplyResult(
            run_at=now_utc(),
            applied_count=0,
            skipped_already_applied=0,
            skipped_no_candidate=0,
            skipped_no_apply_decision=0,
            error_count=0,
            mutates_canonical_state=True,
        )
        with pytest.raises(ValueError, match="canonical state"):
            r.validate()

    def test_creates_vault_notes_rejected(self):
        r = PulseCandidateApplyResult(
            run_at=now_utc(),
            applied_count=0,
            skipped_already_applied=0,
            skipped_no_candidate=0,
            skipped_no_apply_decision=0,
            error_count=0,
            creates_vault_notes=True,
        )
        with pytest.raises(ValueError, match="vault notes"):
            r.validate()

    def test_to_dict_includes_governance(self):
        r = PulseCandidateApplyResult(
            run_at="2026-04-30T00:00:00Z",
            applied_count=1,
            skipped_already_applied=0,
            skipped_no_candidate=0,
            skipped_no_apply_decision=0,
            error_count=0,
        )
        d = r.to_dict()
        assert d["candidate_apply_allowed"] is True
        assert d["canonical_writeback_allowed"] is False
        assert d["mutates_canonical_state"] is False


# ── TestApplyRegistry ─────────────────────────────────────────────────────────

class TestApplyRegistry:
    def test_empty_on_missing(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        assert _load_apply_registry(vault) == set()

    def test_roundtrip(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / APPLY_REGISTRY_ROOT).mkdir(parents=True, exist_ok=True)
        ids = {"dec-aaa", "dec-bbb"}
        _save_apply_registry(vault, ids)
        loaded = _load_apply_registry(vault)
        assert loaded == ids

    def test_fail_open_on_corrupt(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        path = _apply_registry_path(vault)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not json", encoding="utf-8")
        result = _load_apply_registry(vault)
        assert result == set()

    def test_sorted_on_save(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        _save_apply_registry(vault, {"zzz", "aaa", "mmm"})
        data = json.loads(_apply_registry_path(vault).read_text(encoding="utf-8"))
        assert data["applied_decision_ids"] == ["aaa", "mmm", "zzz"]


# ── TestDryRun ────────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_no_writes(self):
        vault = _make_vault()
        result = apply_reviewed_candidates(vault, dry_run=True)
        result.validate()
        assert result.applied_count == 0
        assert not _apply_registry_path(vault).exists()

    def test_dry_run_with_feedback_decision(self):
        vault = _make_vault()
        candidate = _make_feedback_candidate(vault)
        _make_review_decision(vault, candidate, "accept_for_future_ranking")

        result = apply_reviewed_candidates(vault, dry_run=True)
        result.validate()
        assert result.applied_count == 1
        assert result.items[0].candidate_kind == "feedback"
        # No actual file written
        assert not _feedback_signals_path(vault).exists()
        # Registry NOT updated in dry_run
        assert not _apply_registry_path(vault).exists()

    def test_dry_run_with_personal_map_decision(self):
        vault = _make_vault()
        candidate = _make_personal_map_candidate(vault)
        _make_review_decision(vault, candidate, "approve_for_future_apply")

        result = apply_reviewed_candidates(vault, dry_run=True)
        result.validate()
        assert result.applied_count == 1
        assert result.items[0].candidate_kind == "personal_map"
        assert not _personal_map_graph_path(vault).exists()

    def test_dry_run_with_repair_decision(self):
        vault = _make_vault()
        candidate = _make_repair_candidate(vault)
        _make_review_decision(vault, candidate, "approve_for_future_apply")

        result = apply_reviewed_candidates(vault, dry_run=True)
        result.validate()
        assert result.applied_count == 1
        assert result.items[0].candidate_kind == "execution_repair"


# ── TestLiveMode ──────────────────────────────────────────────────────────────

class TestLiveMode:
    def test_feedback_writes_signal(self):
        vault = _make_vault()
        candidate = _make_feedback_candidate(vault)
        decision = _make_review_decision(vault, candidate, "accept_for_future_ranking")

        result = apply_reviewed_candidates(vault, dry_run=False)
        result.validate()
        assert result.applied_count == 1

        # Signal file written
        sig_path = _feedback_signals_path(vault)
        assert sig_path.exists()
        lines = [l for l in sig_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["candidate_id"] == candidate.candidate_id
        assert entry["decision_id"] == decision.decision_id
        assert entry["feedback_type"] == "thumbs_up"

    def test_feedback_registry_updated(self):
        vault = _make_vault()
        candidate = _make_feedback_candidate(vault)
        decision = _make_review_decision(vault, candidate, "accept_for_future_ranking")

        apply_reviewed_candidates(vault, dry_run=False)
        applied = _load_apply_registry(vault)
        assert decision.decision_id in applied

    def test_feedback_skip_already_applied(self):
        vault = _make_vault()
        candidate = _make_feedback_candidate(vault)
        decision = _make_review_decision(vault, candidate, "accept_for_future_ranking")

        apply_reviewed_candidates(vault, dry_run=False)
        result2 = apply_reviewed_candidates(vault, dry_run=False)
        result2.validate()
        assert result2.applied_count == 0
        assert result2.skipped_already_applied == 1

    def test_personal_map_writes_graph(self):
        vault = _make_vault()
        candidate = _make_personal_map_candidate(vault)
        _make_review_decision(vault, candidate, "approve_for_future_apply")

        apply_reviewed_candidates(vault, dry_run=False)
        graph_path = _personal_map_graph_path(vault)
        assert graph_path.exists()
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        assert "nodes" in graph
        assert "node-chase-goal" in graph["nodes"]
        node = graph["nodes"]["node-chase-goal"]
        assert node["label"] == "Build ChaseOS"

    def test_personal_map_upserts_on_second_apply(self):
        vault = _make_vault()
        candidate = _make_personal_map_candidate(vault)
        _make_review_decision(vault, candidate, "approve_for_future_apply")

        # First apply
        apply_reviewed_candidates(vault, dry_run=False)
        graph = json.loads(_personal_map_graph_path(vault).read_text(encoding="utf-8"))
        assert len(graph["nodes"]) == 1

        # Second candidate with different node
        from runtime.memory.personal_map import PersonalMapNode
        from runtime.memory.candidate_store import build_personal_map_node_candidate
        node2 = PersonalMapNode(node_id="node-2", node_type="skill", label="Python")
        c2 = build_personal_map_node_candidate(node2, reason="skill signal")
        persist_personal_map_candidate(vault, c2)
        _make_review_decision(vault, c2, "approve_for_future_apply")

        apply_reviewed_candidates(vault, dry_run=False)
        graph2 = json.loads(_personal_map_graph_path(vault).read_text(encoding="utf-8"))
        assert len(graph2["nodes"]) == 2

    def test_repair_writes_to_growth(self):
        vault = _make_vault()
        candidate = _make_repair_candidate(vault, runtime_id="hermes")
        _make_review_decision(vault, candidate, "approve_for_future_apply")

        apply_reviewed_candidates(vault, dry_run=False)
        repair_path = vault / "runtime" / "memory" / "repair" / "hermes.json"
        assert repair_path.exists()
        data = json.loads(repair_path.read_text(encoding="utf-8"))
        patterns = data.get("repair_patterns", [])
        assert len(patterns) == 1
        assert "Now.md read timed out" in patterns[0]["failure_context"]

    def test_defer_decision_skipped(self):
        vault = _make_vault()
        candidate = _make_feedback_candidate(vault)
        _make_review_decision(vault, candidate, "defer_candidate")

        result = apply_reviewed_candidates(vault, dry_run=False)
        result.validate()
        assert result.applied_count == 0
        assert result.skipped_no_apply_decision == 1


# ── TestKindFilter ────────────────────────────────────────────────────────────

class TestKindFilter:
    def test_filter_feedback_only(self):
        vault = _make_vault()
        fb = _make_feedback_candidate(vault)
        pm = _make_personal_map_candidate(vault)
        _make_review_decision(vault, fb, "accept_for_future_ranking")
        _make_review_decision(vault, pm, "approve_for_future_apply")

        result = apply_reviewed_candidates(vault, dry_run=False, candidate_kind="feedback")
        result.validate()
        assert result.applied_count == 1
        assert all(item.candidate_kind == "feedback" for item in result.items)

    def test_filter_personal_map_only(self):
        vault = _make_vault()
        fb = _make_feedback_candidate(vault)
        pm = _make_personal_map_candidate(vault)
        _make_review_decision(vault, fb, "accept_for_future_ranking")
        _make_review_decision(vault, pm, "approve_for_future_apply")

        result = apply_reviewed_candidates(vault, dry_run=False, candidate_kind="personal_map")
        result.validate()
        assert result.applied_count == 1
        assert all(item.candidate_kind == "personal_map" for item in result.items)

    def test_no_kind_applies_all(self):
        vault = _make_vault()
        fb = _make_feedback_candidate(vault)
        pm = _make_personal_map_candidate(vault)
        repair = _make_repair_candidate(vault)
        _make_review_decision(vault, fb, "accept_for_future_ranking")
        _make_review_decision(vault, pm, "approve_for_future_apply")
        _make_review_decision(vault, repair, "approve_for_future_apply")

        result = apply_reviewed_candidates(vault, dry_run=True)
        result.validate()
        assert result.applied_count == 3


# ── TestMissingCandidates ─────────────────────────────────────────────────────

class TestMissingCandidates:
    def test_skips_when_candidate_missing(self):
        vault = _make_vault()
        # Create a decision that references a non-existent candidate
        decision = PulseCandidateReviewDecision(
            decision_id="dec-missing-001",
            candidate_id="feedback-candidate-ghost-relevant-000000000000",
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
            blocked_effects=REVIEW_DECISION_BLOCKED_EFFECTS,
        )
        decision.validate()
        persist_review_decision(vault, decision)

        result = apply_reviewed_candidates(vault, dry_run=False)
        result.validate()
        assert result.applied_count == 0
        assert result.skipped_no_candidate == 1


# ── TestErrorIsolation ────────────────────────────────────────────────────────

class TestErrorIsolation:
    def test_one_error_does_not_block_others(self):
        vault = _make_vault()

        # Valid feedback candidate
        fb = _make_feedback_candidate(vault)
        _make_review_decision(vault, fb, "accept_for_future_ranking")

        # Decision referencing missing candidate (will be skipped, not an error)
        decision = PulseCandidateReviewDecision(
            decision_id="dec-ghost",
            candidate_id="repair-memory-candidate-hermes-000000000000",
            candidate_kind="execution_repair",
            decision_type="approve_for_future_apply",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["approve_for_future_apply"],
            blocked_effects=REVIEW_DECISION_BLOCKED_EFFECTS,
        )
        decision.validate()
        persist_review_decision(vault, decision)

        result = apply_reviewed_candidates(vault, dry_run=False)
        result.validate()
        # Feedback was applied
        assert result.applied_count == 1
        # Ghost repair was skipped (no candidate)
        assert result.skipped_no_candidate == 1

    def test_empty_vault_returns_zero_counts(self):
        vault = _make_vault()
        result = apply_reviewed_candidates(vault, dry_run=False)
        result.validate()
        assert result.applied_count == 0
        assert result.error_count == 0


# ── TestApplyDecisionTypes ────────────────────────────────────────────────────

class TestApplyDecisionTypes:
    def test_apply_decision_types_set(self):
        assert "approve_for_future_apply" in _APPLY_DECISION_TYPES
        assert "accept_for_future_ranking" in _APPLY_DECISION_TYPES
        assert "defer_candidate" not in _APPLY_DECISION_TYPES
        assert "reject_candidate" not in _APPLY_DECISION_TYPES

    def test_only_apply_types_trigger_write(self):
        vault = _make_vault()
        candidate = _make_feedback_candidate(vault)
        _make_review_decision(vault, candidate, "mark_duplicate")

        result = apply_reviewed_candidates(vault, dry_run=False)
        result.validate()
        assert result.applied_count == 0
        assert result.skipped_no_apply_decision == 1
