# ChaseOS Pulse Agent Bus Review Queue Preview

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** PARTIAL - read-only in-memory queue preview  
**Created:** 2026-04-30  
**Runtime scaffold:** `runtime/pulse/bus_review_queue.py`

## Purpose

The Pulse Agent Bus Review Queue Preview aggregates existing Pulse candidate
lanes into non-mutating Agent Bus `REVIEW` request contracts.

It is a coordination preview for the operator and bounded runtimes. It is not a
live Agent Bus queue, not an approval queue, not an apply engine, and not
canonical truth.

## Source

The queue preview reads through the existing unified candidate inspector:

- feedback candidates
- Personal Map candidates
- execution repair memory candidates
- review-decision records for context

Review-decision records are not converted into new review contracts by default.
The preview builds contracts only for candidate items.

## Current Runtime Contract

`runtime/pulse/bus_review_queue.py` can:

- build an in-memory queue preview over current Pulse candidates
- filter by candidate kind or candidate ID
- limit the number of contracts returned
- preserve discovered source log paths
- create Agent Bus `REVIEW` task previews for each candidate
- count contracts by candidate kind
- count contracts by recipient
- route all candidates to Hermes by default
- optionally route a candidate kind to a different recipient, such as OpenClaw
  for execution repair review

## Boundary

This pass does not:

- persist a derived Pulse queue
- persist an approval queue
- create Agent Bus tasks
- initialize or mutate Agent Bus storage
- dispatch Hermes, OpenClaw, Codex, or any runtime
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

## Why It Is Separate From Enqueue

Other ChaseOS runtimes are actively developing against the Agent Bus. A queue
preview lets Pulse expose a deterministic review shape without causing live bus
side effects or racing another runtime's work.

The future enqueue surface must be a separate approval-gated pass.

## Next Boundary

The queue-preview audit now exists at
`06_AGENTS/ChaseOS-Pulse-Agent-Bus-Review-Queue-Audit.md` and passes for the
current boundary. The next safe pass is a narrow operator-approved enqueue
design. A real enqueue implementation must decide:

- who may approve enqueue
- whether the sender remains `Operator`
- which runtime receives each candidate kind
- how work fingerprints prevent duplicates
- how review responses are recorded
- why no candidate apply happens from the enqueue step

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Agent-Bus-Review-Request-Contract]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Audit]] - [[ChaseOS-Pulse-Unified-Candidate-Inspector-Policy]] - [[Pulse-Feedback-Policy]] - [[Agent-Control-Plane]]
