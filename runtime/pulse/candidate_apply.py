"""Pulse Candidate Apply — applies Hermes-reviewed decisions to runtime memory.

This is the only Pulse module where candidate_apply_allowed = True.

It reads review decisions with decision_type in the "apply" family
(approve_for_future_apply, accept_for_future_ranking), cross-references the
source candidate, and writes to non-canonical runtime memory targets.

Write targets (all under runtime/memory/ — NOT canonical vault notes):
  - feedback  + accept_for_future_ranking:
      runtime/memory/feedback-rules/accepted-signals.jsonl
  - personal_map + approve_for_future_apply:
      runtime/memory/personal-map/graph.json  (upsert node or edge)
  - execution_repair + approve_for_future_apply:
      runtime/memory/repair/<runtime_id>.json  (via growth.record_repair_pattern)

Apply registry:
  07_LOGS/Pulse-Decks/apply-registry/applied-decisions.json
  Prevents double-apply across runs.

Governance:
  candidate_apply_allowed = True        — unique to this module
  canonical_writeback_allowed = False   — no vault note mutation
  mutates_canonical_state = False
  dry_run=True                          — default; must opt-in to live writes
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.agents.repair_candidate_store import (
    ExecutionRepairMemoryCandidate,
    load_execution_repair_memory_candidates,
)
from runtime.memory import growth as _growth
from runtime.memory.candidate_store import PersonalMapCandidate, load_personal_map_candidates
from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback import PulseFeedbackCandidate, load_feedback_candidates
from runtime.pulse.review_decision_log import (
    PulseCandidateReviewDecision,
    load_review_decisions,
)


# ── Decision types that trigger an apply action ──────────────────────────────

_APPLY_DECISION_TYPES = {"approve_for_future_apply", "accept_for_future_ranking"}

# ── Runtime memory write paths ────────────────────────────────────────────────

def _feedback_signals_path(vault: Path) -> Path:
    return vault / "runtime" / "memory" / "feedback-rules" / "accepted-signals.jsonl"


def _personal_map_graph_path(vault: Path) -> Path:
    return vault / "runtime" / "memory" / "personal-map" / "graph.json"


APPLY_REGISTRY_ROOT = Path("07_LOGS") / "Pulse-Decks" / "apply-registry"
_APPLY_REGISTRY_FILENAME = "applied-decisions.json"


# ── Apply registry ────────────────────────────────────────────────────────────

def _apply_registry_path(vault: Path) -> Path:
    return (vault / APPLY_REGISTRY_ROOT / _APPLY_REGISTRY_FILENAME).resolve()


def _load_apply_registry(vault: Path) -> set[str]:
    """Load set of already-applied decision_ids. Fail-open (empty on any error)."""
    path = _apply_registry_path(vault)
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("applied_decision_ids") or [])
    except Exception:
        return set()


def _save_apply_registry(vault: Path, applied: set[str]) -> None:
    path = _apply_registry_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"applied_decision_ids": sorted(applied)},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


# ── Candidate index builders ──────────────────────────────────────────────────

def _build_feedback_index(vault: Path) -> dict[str, PulseFeedbackCandidate]:
    return {c.candidate_id: c for c in load_feedback_candidates(vault)}


def _build_personal_map_index(vault: Path) -> dict[str, PersonalMapCandidate]:
    return {c.candidate_id: c for c in load_personal_map_candidates(vault)}


def _build_repair_index(vault: Path) -> dict[str, ExecutionRepairMemoryCandidate]:
    return {c.candidate_id: c for c in load_execution_repair_memory_candidates(vault)}


# ── Apply handlers ────────────────────────────────────────────────────────────

def _apply_feedback_ranking_signal(
    vault: Path,
    decision: PulseCandidateReviewDecision,
    candidate: PulseFeedbackCandidate,
) -> str:
    """Append an accepted ranking signal to the feedback-rules JSONL."""
    path = _feedback_signals_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "feedback_type": candidate.feedback_type,
        "card_id": candidate.card_id,
        "candidate_id": candidate.candidate_id,
        "decision_id": decision.decision_id,
        "source_deck_path": candidate.source_deck_path,
        "operator_note": decision.operator_note or "",
        "recorded_at": now_utc(),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True))
        handle.write("\n")
    return str(path.relative_to(vault))


def _apply_personal_map_candidate(
    vault: Path,
    decision: PulseCandidateReviewDecision,
    candidate: PersonalMapCandidate,
) -> str:
    """Upsert approved node or edge into the personal map graph JSON."""
    path = _personal_map_graph_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            graph = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(graph, dict):
                graph = {}
        except Exception:
            graph = {}
    else:
        graph = {}

    if "nodes" not in graph:
        graph["nodes"] = {}
    if "edges" not in graph:
        graph["edges"] = {}
    if "updated_at" not in graph:
        graph["updated_at"] = now_utc()

    if candidate.candidate_type == "node" and candidate.node is not None:
        node_dict = asdict(candidate.node)
        node_dict["approved_by_decision"] = decision.decision_id
        node_dict["applied_at"] = now_utc()
        graph["nodes"][candidate.node.node_id] = node_dict

    elif candidate.candidate_type == "edge" and candidate.edge is not None:
        edge_dict = asdict(candidate.edge)
        edge_dict["approved_by_decision"] = decision.decision_id
        edge_dict["applied_at"] = now_utc()
        graph["edges"][candidate.edge.edge_id] = edge_dict

    graph["updated_at"] = now_utc()
    path.write_text(json.dumps(graph, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return str(path.relative_to(vault))


def _apply_execution_repair_candidate(
    vault: Path,
    decision: PulseCandidateReviewDecision,
    candidate: ExecutionRepairMemoryCandidate,
) -> str:
    """Write the repair entry to runtime memory via growth.record_repair_pattern."""
    entry = candidate.entry
    _growth.record_repair_pattern(
        runtime_id=candidate.runtime_id,
        vault_root=vault,
        workflow_id=entry.workflow_id,
        failure_context=entry.failure_summary,
        repair_action=entry.resolution_summary,
        resolved=True,
        notes=(
            f"Applied from Pulse candidate {candidate.candidate_id} "
            f"via decision {decision.decision_id}. {candidate.reason}"
        ),
    )
    repair_path = vault / "runtime" / "memory" / "repair" / f"{candidate.runtime_id}.json"
    try:
        return str(repair_path.relative_to(vault))
    except ValueError:
        return str(repair_path)


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class PulseCandidateApplyItem:
    """One successfully applied candidate."""

    decision_id: str
    candidate_id: str
    candidate_kind: str
    decision_type: str
    write_target: str
    applied_at: str


@dataclass
class PulseCandidateApplyResult:
    """Summary result for one apply run."""

    run_at: str
    applied_count: int
    skipped_already_applied: int
    skipped_no_candidate: int
    skipped_no_apply_decision: int
    error_count: int
    items: list[PulseCandidateApplyItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Governance flags — candidate_apply_allowed is True only in this module.
    candidate_apply_allowed: bool = True
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    creates_vault_notes: bool = False
    expands_permissions: bool = False
    calls_provider_or_connector: bool = False
    schedule_activation_allowed: bool = False
    second_datastore_write_allowed: bool = False

    def validate(self) -> None:
        if not self.candidate_apply_allowed:
            raise ValueError("apply result must have candidate_apply_allowed=True")
        if self.canonical_writeback_allowed:
            raise ValueError("apply result cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("apply result cannot mutate canonical state")
        if self.creates_vault_notes:
            raise ValueError("apply result cannot create vault notes")
        if self.expands_permissions:
            raise ValueError("apply result cannot expand permissions")
        if self.calls_provider_or_connector:
            raise ValueError("apply result cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("apply result cannot activate schedules")
        if self.second_datastore_write_allowed:
            raise ValueError("apply result cannot write a second datastore")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


# ── Core apply function ───────────────────────────────────────────────────────

def apply_reviewed_candidates(
    vault_root: str | Path,
    *,
    dry_run: bool = True,
    candidate_kind: str | None = None,
    run_at: str | None = None,
) -> PulseCandidateApplyResult:
    """Apply Hermes-reviewed Pulse candidates to non-canonical runtime memory.

    Reads review decisions with decision_type in {approve_for_future_apply,
    accept_for_future_ranking} and applies the underlying candidate to its
    runtime memory target.

    Args:
        vault_root: ChaseOS vault root path.
        dry_run: If True (default), reads all state and reports what would be
            applied but writes nothing (no apply registry update, no memory writes).
        candidate_kind: Optional filter — apply only "feedback", "personal_map",
            or "execution_repair" candidates.
        run_at: ISO timestamp override (for testing).

    Returns:
        PulseCandidateApplyResult with governance flags and per-item details.
    """
    vault = Path(vault_root).resolve()
    ts = run_at or now_utc()

    # Load all decisions; track non-apply types without iterating.
    all_decisions: list[PulseCandidateReviewDecision] = load_review_decisions(vault)

    # Count decisions skipped because their type isn't in the apply family.
    # These go into skipped_no_apply_decision before we filter to the apply set.
    _non_apply = [d for d in all_decisions if d.decision_type not in _APPLY_DECISION_TYPES]
    apply_decisions = [d for d in all_decisions if d.decision_type in _APPLY_DECISION_TYPES]

    # Filter by kind if requested.
    if candidate_kind is not None:
        _non_apply += [d for d in apply_decisions if d.candidate_kind != candidate_kind]
        apply_decisions = [d for d in apply_decisions if d.candidate_kind == candidate_kind]

    # Load apply registry.
    applied_ids = _load_apply_registry(vault)

    # Build candidate indexes (lazy — loaded once).
    _feedback_index: dict[str, PulseFeedbackCandidate] | None = None
    _pm_index: dict[str, PersonalMapCandidate] | None = None
    _repair_index: dict[str, ExecutionRepairMemoryCandidate] | None = None

    applied_count = 0
    skipped_already = 0
    skipped_no_candidate = 0
    skipped_no_apply = len(_non_apply)
    error_count = 0
    items: list[PulseCandidateApplyItem] = []
    errors: list[str] = []
    newly_applied: set[str] = set()

    for decision in apply_decisions:
        if decision.decision_id in applied_ids:
            skipped_already += 1
            continue

        try:
            write_target: str | None = None

            if decision.candidate_kind == "feedback":
                if _feedback_index is None:
                    _feedback_index = _build_feedback_index(vault)
                candidate = _feedback_index.get(decision.candidate_id)
                if candidate is None:
                    skipped_no_candidate += 1
                    continue
                if not dry_run:
                    write_target = _apply_feedback_ranking_signal(vault, decision, candidate)
                else:
                    write_target = str(_feedback_signals_path(vault).relative_to(vault))

            elif decision.candidate_kind == "personal_map":
                if _pm_index is None:
                    _pm_index = _build_personal_map_index(vault)
                candidate = _pm_index.get(decision.candidate_id)
                if candidate is None:
                    skipped_no_candidate += 1
                    continue
                if not dry_run:
                    write_target = _apply_personal_map_candidate(vault, decision, candidate)
                else:
                    write_target = str(_personal_map_graph_path(vault).relative_to(vault))

            elif decision.candidate_kind == "execution_repair":
                if _repair_index is None:
                    _repair_index = _build_repair_index(vault)
                candidate = _repair_index.get(decision.candidate_id)
                if candidate is None:
                    skipped_no_candidate += 1
                    continue
                if not dry_run:
                    write_target = _apply_execution_repair_candidate(vault, decision, candidate)
                else:
                    rp = candidate.runtime_id
                    write_target = f"runtime/memory/repair/{rp}.json"

            else:
                skipped_no_apply += 1
                continue

            if write_target is not None:
                newly_applied.add(decision.decision_id)
                items.append(PulseCandidateApplyItem(
                    decision_id=decision.decision_id,
                    candidate_id=decision.candidate_id,
                    candidate_kind=decision.candidate_kind,
                    decision_type=decision.decision_type,
                    write_target=write_target,
                    applied_at=ts,
                ))
                applied_count += 1

        except Exception as exc:
            errors.append(f"decision {decision.decision_id}: {exc}")
            error_count += 1

    if not dry_run and newly_applied:
        _save_apply_registry(vault, applied_ids | newly_applied)

    result = PulseCandidateApplyResult(
        run_at=ts,
        applied_count=applied_count,
        skipped_already_applied=skipped_already,
        skipped_no_candidate=skipped_no_candidate,
        skipped_no_apply_decision=skipped_no_apply,
        error_count=error_count,
        items=items,
        errors=errors,
    )
    result.validate()
    return result
