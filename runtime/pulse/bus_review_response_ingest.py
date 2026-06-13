"""Pulse Agent Bus review response ingest.

Reads completed REVIEW tasks from the Agent Bus that were enqueued by Pulse,
maps Hermes review verdicts to review decisions, and persists them to the
Pulse review decision log.

This is the only Pulse module where review_response_ingest_allowed = True.
All other governance flags remain False.

Ingest flow:
  1. Load all "enqueued" Pulse enqueue results (have task_id)
  2. Skip task_ids already in the ingest-tracking registry
  3. For each unprocessed task_id:
     a. Call bus.get_task() — if not status=="done", skip (not ready)
     b. Call bus.list_events() — find the result_attached event message
     c. Parse Hermes verdict (PASS / CONDITIONAL PASS / FLAGGED / unreadable)
     d. Map verdict + candidate_kind → decision_type
     e. Build and persist a PulseCandidateReviewDecision
     f. Record task_id in the ingest-tracking registry
  4. Return PulseReviewResponseIngestResult

Governance:
  - Reads bus tasks and events (read-only bus access)
  - Reads Pulse enqueue result JSONL (read-only)
  - Writes to 07_LOGS/Pulse-Decks/review-decisions/ (append-only JSONL)
  - Writes ingest-tracking JSON (processed task registry)
  - Does NOT apply candidates, mutate memory, activate schedules,
    call providers/connectors, or perform canonical writeback
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.agent_bus import bus as _bus
from runtime.pulse.bus_enqueue import (
    PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
    PULSE_BUS_ENQUEUE_RESULTS_ROOT,
    load_enqueue_results,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.review_decision_log import (
    DECISION_FOLLOWUP_SIGNALS,
    REVIEW_DECISION_BLOCKED_EFFECTS,
    REVIEW_DECISION_TYPES_BY_KIND,
    PulseCandidateReviewDecision,
    persist_review_decision,
)


# Registry of already-ingested task_ids (prevents double-processing).
INGEST_REGISTRY_FILENAME = "ingested-task-ids.json"

# Candidate kinds supported by ingest (subset of CANDIDATE_KINDS).
_INGESTABLE_KINDS = {"feedback", "personal_map", "execution_repair"}

# Hermes verdict → decision_type for each candidate kind.
# "pass" maps to accept/approve; anything else maps to defer or request_more_context.
_VERDICT_MAP: dict[str, dict[str, str]] = {
    "feedback": {
        "pass": "accept_for_future_ranking",
        "conditional_pass": "defer_candidate",
        "flagged": "defer_candidate",
        "unreadable": "request_more_context",
    },
    "personal_map": {
        "pass": "approve_for_future_apply",
        "conditional_pass": "defer_candidate",
        "flagged": "defer_candidate",
        "unreadable": "request_more_context",
    },
    "execution_repair": {
        "pass": "approve_for_future_apply",
        "conditional_pass": "defer_candidate",
        "flagged": "defer_candidate",
        "unreadable": "request_more_context",
    },
}

# Hermes writes verdict in two canonical locations:
#   "**Verdict:** PASS/CONDITIONAL PASS/FLAGGED ..."
#   "## Hermes Review — PASS/CONDITIONAL PASS/FLAGGED"
# We match these anchored contexts before falling back to bare word search.
_VERDICT_LINE_PATTERN = re.compile(
    r"(?:\*\*Verdict:\*\*|##\s+Hermes Review\s+[—-]+)\s*(CONDITIONAL\s+PASS|FLAGGED|PASS)",
    re.IGNORECASE,
)
_VERDICT_BARE_PATTERNS = [
    (re.compile(r"CONDITIONAL\s+PASS", re.IGNORECASE), "conditional_pass"),
    (re.compile(r"\bFLAGGED\b", re.IGNORECASE), "flagged"),
    (re.compile(r"\bPASS\b", re.IGNORECASE), "pass"),
]
_VERDICT_KEY_MAP = {
    "conditional pass": "conditional_pass",
    "flagged": "flagged",
    "pass": "pass",
}


def _parse_verdict(message: str) -> str:
    """Extract Hermes review verdict key from a result_attached event message.

    Prefers anchored verdict lines (**Verdict:** or ## Hermes Review —) before
    falling back to bare word search. The anchored approach prevents "flagged"
    count text ("0 flagged") from overriding the primary verdict.
    """
    m = _VERDICT_LINE_PATTERN.search(message)
    if m:
        raw = m.group(1).strip().lower()
        return _VERDICT_KEY_MAP.get(raw, "unreadable")
    # Fall back to bare word search in the full message.
    for pattern, key in _VERDICT_BARE_PATTERNS:
        if pattern.search(message):
            return key
    return "unreadable"


def _decision_type_for(candidate_kind: str, verdict: str) -> str:
    """Map (candidate_kind, verdict) → decision_type string."""
    kind_map = _VERDICT_MAP.get(candidate_kind, _VERDICT_MAP["feedback"])
    return kind_map.get(verdict, "request_more_context")


def _decision_id(task_id: str, candidate_id: str, decision_type: str) -> str:
    seed = f"pulse-ingest|{task_id}|{candidate_id}|{decision_type}"
    return "pulse-ingest-decision-" + hashlib.sha256(seed.encode()).hexdigest()[:12]


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _ingest_registry_path(vault: Path) -> Path:
    return (vault / PULSE_BUS_ENQUEUE_RESULTS_ROOT / INGEST_REGISTRY_FILENAME).resolve()


def _load_ingest_registry(vault: Path) -> set[str]:
    """Load the set of already-ingested task_ids. Fail-open (empty set on any error)."""
    path = _ingest_registry_path(vault)
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("ingested_task_ids") or [])
    except Exception:
        return set()


def _save_ingest_registry(vault: Path, ingested: set[str]) -> None:
    """Persist the set of ingested task_ids."""
    path = _ingest_registry_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"ingested_task_ids": sorted(ingested)}, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _parse_notes_field(notes: str) -> dict[str, str]:
    """Parse key=value pairs from a bus task notes field."""
    result: dict[str, str] = {}
    for part in (notes or "").split():
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip()
    return result


def _find_result_attached_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the last result_attached event, or None."""
    for evt in reversed(events):
        if evt.get("event_type") == "result_attached":
            return evt
    return None


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class PulseReviewIngestItem:
    """One successfully ingested review response."""

    task_id: str
    candidate_id: str
    candidate_kind: str
    verdict: str
    decision_type: str
    decision_id: str
    reviewer: str


@dataclass
class PulseReviewResponseIngestResult:
    """Summary result for one ingest run."""

    run_at: str
    ingested_count: int
    skipped_already_ingested: int
    skipped_not_done: int
    skipped_no_event: int
    error_count: int
    items: list[PulseReviewIngestItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Governance flags — this module is the ONLY Pulse module with
    # review_response_ingest_allowed = True.
    review_response_ingest_allowed: bool = True
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False

    def validate(self) -> None:
        if not self.review_response_ingest_allowed:
            raise ValueError("ingest result must have review_response_ingest_allowed=True")
        if self.candidate_apply_allowed:
            raise ValueError("ingest result cannot allow candidate apply")
        if self.canonical_writeback_allowed:
            raise ValueError("ingest result cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("ingest result cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("ingest result cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("ingest result cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("ingest result cannot activate schedules")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


# ── Core ingest function ──────────────────────────────────────────────────────

def ingest_pulse_review_responses(
    vault_root: str | Path,
    *,
    dry_run: bool = True,
    run_at: str | None = None,
) -> PulseReviewResponseIngestResult:
    """Ingest completed Hermes review results back into the Pulse review decision log.

    Args:
        vault_root: ChaseOS vault root path.
        dry_run: If True (default), reads bus state and reports what would be
            ingested but writes nothing. Set False to persist review decisions.
        run_at: ISO timestamp override (for testing).
    """
    vault = _vault_path(vault_root)
    ts = run_at or now_utc()

    ingested_ids = _load_ingest_registry(vault)
    enqueue_results = load_enqueue_results(
        vault_root, result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED
    )

    ingested_count = 0
    skipped_already = 0
    skipped_not_done = 0
    skipped_no_event = 0
    error_count = 0
    items: list[PulseReviewIngestItem] = []
    errors: list[str] = []
    newly_ingested: set[str] = set()

    for enqueue_result in enqueue_results:
        task_id = enqueue_result.task_id
        if not task_id:
            continue

        # Skip already-ingested.
        if task_id in ingested_ids:
            skipped_already += 1
            continue

        try:
            task = _bus.get_task(vault, task_id)
            if task is None or task.get("status") != "done":
                skipped_not_done += 1
                continue

            events = _bus.list_events(vault, task_id)
            result_evt = _find_result_attached_event(events)
            if result_evt is None:
                skipped_no_event += 1
                continue

            message = result_evt.get("message") or ""
            event_ts = result_evt.get("created_at") or ts

            # Parse candidate metadata — prefer task notes, fall back to enqueue result.
            notes_parsed = _parse_notes_field(task.get("notes") or "")
            candidate_id = (
                notes_parsed.get("pulse_candidate_id")
                or enqueue_result.candidate_id
            )
            candidate_kind = (
                notes_parsed.get("pulse_candidate_kind")
                or enqueue_result.candidate_kind
            )

            if candidate_kind not in _INGESTABLE_KINDS:
                errors.append(
                    f"task {task_id}: unsupported candidate_kind {candidate_kind!r}"
                )
                error_count += 1
                continue

            verdict = _parse_verdict(message)
            decision_type = _decision_type_for(candidate_kind, verdict)

            decision = PulseCandidateReviewDecision(
                decision_id=_decision_id(task_id, candidate_id, decision_type),
                candidate_id=candidate_id,
                candidate_kind=candidate_kind,
                decision_type=decision_type,
                reviewer="Hermes",
                operator_note=message[:400] if message else "",
                created_at=event_ts,
                followup_signals=DECISION_FOLLOWUP_SIGNALS[decision_type],
                blocked_effects=REVIEW_DECISION_BLOCKED_EFFECTS,
            )
            decision.validate()

            if not dry_run:
                persist_review_decision(vault, decision)
                newly_ingested.add(task_id)

            items.append(PulseReviewIngestItem(
                task_id=task_id,
                candidate_id=candidate_id,
                candidate_kind=candidate_kind,
                verdict=verdict,
                decision_type=decision_type,
                decision_id=decision.decision_id,
                reviewer="Hermes",
            ))
            ingested_count += 1

        except Exception as exc:
            errors.append(f"task {task_id}: {exc}")
            error_count += 1

    if not dry_run and newly_ingested:
        _save_ingest_registry(vault, ingested_ids | newly_ingested)

    result = PulseReviewResponseIngestResult(
        run_at=ts,
        ingested_count=ingested_count,
        skipped_already_ingested=skipped_already,
        skipped_not_done=skipped_not_done,
        skipped_no_event=skipped_no_event,
        error_count=error_count,
        items=items,
        errors=errors,
    )
    result.validate()
    return result
