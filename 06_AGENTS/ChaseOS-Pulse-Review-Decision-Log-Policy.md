# ChaseOS Pulse Review Decision Log Policy

**Status:** PARTIAL - persisted review intent only; read-only unified inspection available  
**Created:** 2026-04-30  
**Runtime scaffold:** `runtime/pulse/review_decision_log.py`, `runtime/pulse/candidate_inspector.py`

## Purpose

The Pulse Review Decision Log records operator review intent for existing Pulse
candidates without applying those candidates.

It covers:

- feedback candidates
- Personal Map candidates
- execution repair memory candidates

The log is not a UI, not an apply engine, not a second datastore, and not
canonical memory.

## Storage Path

Review decisions append to:

```text
07_LOGS/Pulse-Decks/review-decisions/YYYY-MM-DD-review-decisions.jsonl
```

The loader and ledger snapshot are read-only. Empty ledger reads do not create
folders.

## Decision Types

Feedback candidates may record:

- `accept_for_future_ranking`
- `reject_candidate`
- `defer_candidate`
- `request_more_context`
- `mark_duplicate`
- `request_revision`

Personal Map and execution repair candidates may record:

- `approve_for_future_apply`
- `reject_candidate`
- `defer_candidate`
- `request_more_context`
- `mark_duplicate`
- `request_revision`

These names are intentionally conservative. `approve_for_future_apply` records
operator intent only; it does not apply the candidate.

## Blocked Effects

Every review decision blocks:

- source deck mutation
- feedback application
- Personal Map mutation
- runtime memory mutation
- memory approval
- task creation
- SOP creation
- Runtime Navigation Map update
- Agent Identity Ledger update
- permission expansion
- Project-OS mutation
- `02_KNOWLEDGE/` promotion
- canonical writeback
- schedule activation
- provider calls
- connector calls
- second datastore writes

## Next Boundary

The read-only unified inspector now exists in
`runtime/pulse/candidate_inspector.py` and displays candidates and review
decisions together without persisting a derived queue or applying effects.

The next safe Phase 10 layer is now specified in
[[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]. That spec keeps review
decisions record-only, uses the existing `candidate_apply.py` backend only for
dry-run previews or explicitly approved non-canonical runtime-memory apply, and
continues to block Personal Map canonical mutation, memory approval, Agent Bus
task writes, schedule activation, provider/connector calls, and canonical
writeback.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[Pulse-Feedback-Policy]] - [[ChaseOS-Pulse-Candidate-Store-Policy]] - [[ChaseOS-Pulse-Unified-Candidate-Inspector-Policy]] - [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
