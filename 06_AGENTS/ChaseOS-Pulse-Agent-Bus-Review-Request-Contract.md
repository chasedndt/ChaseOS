# ChaseOS Pulse Agent Bus Review Request Contract

**Status:** PARTIAL - non-mutating review request contract scaffold  
**Created:** 2026-04-30  
**Runtime scaffold:** `runtime/pulse/bus_review_contract.py`

## Purpose

This contract is the first bridge between the Pulse candidate inspector and the
ChaseOS Agent Bus.

It converts one read-only Pulse candidate inspector item into a REVIEW task
preview for a registered runtime such as Hermes or OpenClaw. It does not create
the Agent Bus task.

## Why This Pass Exists

Pulse now has multiple pending-review candidate lanes:

- feedback candidates
- Personal Map candidates
- execution repair memory candidates
- persisted review-decision records

The unified candidate inspector can read those lanes together, but other
ChaseOS runtimes are also developing against the Agent Bus. The safe next
boundary is therefore a contract-only bridge: a deterministic packet shape that
can be reviewed and tested before any live bus enqueue or candidate apply
exists.

## Current Contract

`runtime/pulse/bus_review_contract.py` can:

- build a `PulseAgentBusReviewRequestContract` from a
  `PulseCandidateInspectorItem`
- build the same contract by loading a candidate ID through the read-only
  inspector
- preserve source log, deck, card, runtime, and target refs
- generate a future Agent Bus REVIEW task preview
- default the recipient to `Hermes`, the primary review runtime
- allow explicit recipient override, for example `OpenClaw` for runtime-adjacent
  repair review
- keep the bus sender as `Operator`, because current Agent Bus validation only
  allows registered runtimes or approved control-surface senders

## Boundary

This pass does not:

- import or call the Agent Bus task writer
- initialize Agent Bus storage
- enqueue review tasks
- persist approval requests
- apply Pulse candidates
- apply feedback to source decks
- approve memory
- mutate the Personal Map
- mutate runtime memory
- create tasks or SOPs
- update Runtime Navigation Maps
- update Agent Identity Ledgers
- expand runtime permissions
- call providers or connectors
- activate schedules
- write to `02_KNOWLEDGE/`
- mutate `00_HOME/Now.md`, Dashboard, or Project-OS files as a Pulse effect
- create a second datastore
- update the R&D workbook

## Contract Fields

The contract declares:

- `contract_id`
- `candidate_id`
- `source_item_id`
- `source_item_kind`
- `candidate_kind`
- `sender`
- `recipient`
- `intent`
- `priority`
- `request`
- `expected_output`
- `work_fingerprint`
- source artifact refs
- runtime and target refs
- `approval_required: true`
- `bus_task_creation_allowed: false`
- `bus_task_written: false`
- `writes_performed: false`
- `candidate_apply_allowed: false`
- `canonical_writeback_allowed: false`
- `second_datastore_write_allowed: false`
- provider, connector, schedule, and runtime-dispatch blocks

## Review Preview Semantics

The generated preview is suitable for later human or Gate-governed review. It
is not itself an instruction to create a live Agent Bus task.

Expected output from a future runtime review packet:

- recommendation
- rationale
- evidence refs
- blockers
- required operator approvals
- overlap or coordination risks
- explicit blocked effects

## Runtime Coordination Rule

Other runtimes may read this contract and use it to understand the intended
shape of a Pulse review request. They must not treat it as permission to create,
claim, or execute Agent Bus tasks unless a later approved pass adds an enqueue
surface.

## Next Boundary

The read-only queue preview now exists in
`runtime/pulse/bus_review_queue.py`. The next safe pass is either an audit of
the contract/queue boundary or an operator-approved enqueue surface that
converts one contract into an Agent Bus task.

Any enqueue pass must preserve candidate-only behavior unless explicit approval
and Gate policy are added.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Unified-Candidate-Inspector-Policy]] - [[Pulse-Feedback-Policy]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Preview]] - [[Agent-Control-Plane]]
