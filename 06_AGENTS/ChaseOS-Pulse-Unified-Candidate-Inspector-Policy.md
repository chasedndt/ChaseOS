# ChaseOS Pulse Unified Candidate Inspector Policy

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** PARTIAL - read-only inspector scaffold  
**Created:** 2026-04-30  
**Runtime scaffold:** `runtime/pulse/candidate_inspector.py`

## Purpose

The Pulse Unified Candidate Inspector gives ChaseOS one read-only view over the
existing Pulse candidate and review-decision lanes.

It aggregates:

- feedback candidates
- Personal Map candidates
- execution repair memory candidates
- persisted review-decision records

The inspector is an observability layer only. It is not an approval UI, not an
apply engine, not a second datastore, not a memory writer, and not canonical
truth.

The adjacent Agent Bus review request contract may consume inspector items to
build REVIEW task previews. That contract is also non-mutating: it does not
enqueue tasks or dispatch runtimes.

## Source Lanes

The inspector reads existing JSONL log artifacts only:

```text
07_LOGS/Pulse-Decks/feedback-candidates/YYYY-MM-DD-feedback-candidates.jsonl
07_LOGS/Pulse-Decks/memory-candidates/personal-map/YYYY-MM-DD-personal-map-candidates.jsonl
07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/<runtime_id>/YYYY-MM-DD-repair-candidates.jsonl
07_LOGS/Pulse-Decks/review-decisions/YYYY-MM-DD-review-decisions.jsonl
```

Empty reads do not create folders. Snapshot construction returns an in-memory
object only.

## Inspector Contract

The runtime helper can:

- discover existing source log paths
- normalize candidate and review-decision records into inspector items
- filter by item kind, candidate kind, or candidate ID
- expose counts by item kind
- expose review-decision counts by candidate ID
- preserve source log paths, source deck/card refs, runtime refs, target refs,
  and follow-up signals

Every snapshot and item declares:

- `inspector_status: read_only`
- `writes: []`
- `canonical_writeback_allowed: false`
- `applies_effects: false`
- `second_datastore_write_allowed: false`
- blocked effects for candidate application, source-deck mutation, memory
  approval, task/SOP creation, Personal Map/runtime memory mutation, Runtime
  Navigation Map and Agent Identity Ledger updates, permission expansion,
  provider/connector calls, schedule activation, knowledge promotion, canonical
  writeback, and second datastore writes

## Boundary

This pass does not implement:

- candidate apply workflows
- feedback application to source decks
- Personal Map mutation
- runtime repair memory mutation
- memory approval
- task or SOP creation
- Runtime Navigation Map updates
- Agent Identity Ledger updates
- permission expansion
- provider or connector calls
- schedule activation
- Agent Bus task creation
- live runtime dispatch
- full Studio/Pulse approval UI
- canonical project or knowledge writeback
- R&D workbook sync

## Next Boundary

The governed review/apply UI boundary now lives in
[[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]. The inspector remains the
read-only source of candidate/review rows for that surface; the UI may display
dry-run apply previews and exact backend effect boundaries, but it must not
execute apply, approve memory, enqueue Agent Bus tasks, or mutate canonical truth
without a separate approved backend lane.

Any real Agent Bus enqueue or live apply workflow remains a separate
operator-approved pass.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[Pulse-Feedback-Policy]] - [[ChaseOS-Pulse-Candidate-Store-Policy]] - [[ChaseOS-Pulse-Review-Decision-Log-Policy]] - [[ChaseOS-Pulse-Agent-Bus-Review-Request-Contract]] - [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
