# ChaseOS Pulse Candidate Store Policy

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** PARTIAL - append-only candidate-store scaffold plus read-only unified inspection  
**Created:** 2026-04-30  
**Runtime scaffold:** `runtime/memory/candidate_store.py`, `runtime/agents/repair_candidate_store.py`, `runtime/pulse/review_decision_log.py`, `runtime/pulse/candidate_inspector.py`

## Purpose

Pulse candidate stores persist reviewable memory candidates without applying
them. They are ChaseOS Pulse log artifacts, not a second datastore and not
canonical memory.

This pass adds candidate stores for:

- Personal Map node and edge candidates
- Execution Repair Memory candidates

## Storage Paths

Candidate artifacts live under the existing Pulse deck/log tree:

- `07_LOGS/Pulse-Decks/memory-candidates/personal-map/YYYY-MM-DD-personal-map-candidates.jsonl`
- `07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/<runtime_id>/YYYY-MM-DD-repair-candidates.jsonl`

These paths are append-only JSONL logs. Queue builders read them in read-only
mode and do not create folders when no candidates exist.

## Candidate Semantics

Every candidate is:

- `pending_review`
- `candidate_only`
- review-required
- blocked from canonical writeback
- blocked from second-datastore writes

The candidate stores may record evidence and source references, but they do not
approve the candidate or mutate any target system.

## Review Decision Records

Pulse can now persist operator review intent for feedback, Personal Map, and
execution repair candidates under:

- `07_LOGS/Pulse-Decks/review-decisions/YYYY-MM-DD-review-decisions.jsonl`

These records are not apply records. They can say that a candidate was accepted
for future ranking, approved for a later apply review, rejected, deferred,
marked duplicate, or sent back for more context/revision. They still block all
target-system effects.

## Unified Candidate Inspection

`runtime/pulse/candidate_inspector.py` now reads the feedback candidate,
Personal Map candidate, execution repair candidate, and review-decision lanes
into one read-only in-memory snapshot.

The inspector:

- discovers existing JSONL source logs without creating folders on empty reads
- normalizes candidate and review-decision rows into inspector items
- preserves source log paths, source deck/card refs, runtime refs, target refs,
  follow-up signals, and decision counts by candidate ID
- declares no writes, no apply effects, no canonical writeback, and no second
  datastore writes

The inspector does not approve or apply candidates. It is an observability
surface only.

## Personal Map Candidate Boundary

Personal Map candidates can represent proposed nodes or edges. The store blocks:

- Personal Map mutation
- memory approval
- task creation
- Project-OS mutation
- `02_KNOWLEDGE/` promotion
- canonical writeback
- second datastore writes

An operator review/apply lane is still NOT BUILT.

## Execution Repair Candidate Boundary

Execution Repair Memory candidates can represent reusable failure/workaround
patterns from browser, repo, connector, runtime, or autonomous workflow work.
The store blocks:

- runtime memory mutation
- Runtime Navigation Map updates
- Agent Identity Ledger updates
- SOP creation
- tool or connector grants
- permission expansion
- `02_KNOWLEDGE/` promotion
- canonical writeback
- second datastore writes

Execution repair candidates can feed Agent Pulse review cards, but they do not
change a runtime brain by themselves.

## Not Implemented

- automatic Personal Map apply
- automatic runtime repair memory apply
- automatic SOP/task creation
- automatic Runtime Navigation Map update
- automatic Agent Identity Ledger update
- live connectors or web scanning
- full UI or dashboard approval queue
- candidate inspector apply effects
- canonical project or knowledge writeback

Graph links: [[ChaseOS-Pulse-Architecture]] - [[Context-Memory-Core]] - [[Personal-Map-Architecture]] - [[AgentHub-Spec]] - [[Agent-Runtime-Brain-Architecture]] - [[ChaseOS-Pulse-Unified-Candidate-Inspector-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
