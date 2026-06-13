# ChaseOS Pulse Agent Bus Enqueue Design

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** PARTIAL - design-only enqueue preflight scaffold  
**Date:** 2026-04-30  
**Runtime:** Codex  
**Runtime scaffold:** `runtime/pulse/bus_enqueue_design.py`

## Purpose

This pass defines the approval boundary between Pulse Agent Bus review queue
previews and any future live Agent Bus task handoff.

It does not enqueue tasks. It does not persist approval requests. It does not
dispatch Hermes, OpenClaw, Codex, or any other runtime. It does not apply Pulse
candidates or ingest review responses.

## Repo Truth Baseline

Current Pulse bus layers are:

1. `candidate_inspector.py` - read-only candidate and review-decision snapshot.
2. `bus_review_contract.py` - in-memory Agent Bus REVIEW task previews.
3. `bus_review_queue.py` - read-only in-memory queue preview over review
   contracts.
4. `test_bus_review_queue_audit.py` - audit guards proving the queue preview
   is non-enqueueing and non-applying.

This pass adds only the next design object:

5. `bus_enqueue_design.py` - denied-by-default preflight contracts for a future
   operator-approved enqueue surface.

## Adopted Boundary

Pulse may describe a future Agent Bus REVIEW handoff only when these fields are
present:

- source review contract ID
- candidate ID and candidate kind
- sender, recipient, intent, priority
- request and expected output
- source log, deck, card, target, and runtime refs where known
- work fingerprint for duplicate review
- required approvals
- blocked effects
- task payload preview

The preflight status is:

```text
ready_for_operator_approval
```

That status is not permission. It means the object is reviewable by the
operator and still non-executing.

## Required Approvals

Every future enqueue must require:

- `operator_enqueue_approval`
- `gate_policy_defined`
- `external_sender_allowance`
- `duplicate_work_fingerprint_review`

The current scaffold does not persist those approvals. It only records that
they are required.

## Review Recipients

The design-only default review recipients are:

- Hermes
- OpenClaw

Codex is registered on the Agent Bus for bounded code/repo tasks, but this pass
does not make Codex a default Pulse REVIEW recipient. Adding Codex as a Pulse
review recipient would require a separate role/profile and routing pass.

## Non-Goals

This pass does not implement:

- live Agent Bus task handoff
- approval queue persistence
- review-response ingestion
- candidate apply effects
- feedback application
- memory approval
- Personal Map mutation
- runtime brain mutation
- Runtime Navigation Map updates
- Agent Identity Ledger writes
- task or SOP creation
- schedule activation
- provider or connector calls
- canonical writeback
- second datastore writes
- R&D workbook sync

## Runtime Objects

### `PulseAgentBusEnqueueDesign`

Static denied-by-default policy object for the future enqueue surface.

Key fields:

- `design_status: design_only`
- `allowed: false`
- `approval_required: true`
- `live_enqueue_allowed: false`
- `agent_bus_write_allowed: false`
- `approval_request_write_allowed: false`
- `candidate_apply_allowed: false`
- `review_response_ingest_allowed: false`

### `PulseAgentBusEnqueuePreflight`

One-contract preflight built from a `PulseAgentBusReviewRequestContract`.

Key fields:

- `preflight_status: ready_for_operator_approval`
- `enqueue_allowed: false`
- `agent_bus_task_written: false`
- `approval_request_written: false`
- `duplicate_check_performed: false`
- `work_fingerprint: required`

### `PulseAgentBusEnqueuePlan`

Read-only aggregate over enqueue preflights from a queue preview.

Key fields:

- `plan_status: read_only`
- `preflight_count`
- `counts_by_recipient`
- `task_payload_previews`
- `writes: []`
- `agent_bus_tasks_written: false`

## Verification

Focused tests assert:

- the module does not import the live Agent Bus writer/backend
- no bus state or `.chaseos` state is created by candidate preflight reads
- preflights are ready for operator approval but non-enqueueing
- queue-derived plans remain read-only and in-memory
- Codex is not silently promoted to a default Pulse REVIEW recipient
- forbidden write/apply/runtime-dispatch flags are rejected

## Next Pass

The next safe pass is an approval-request design for enqueue intent, still
without live task handoff. A live enqueue command should only be added after a
Gate policy, duplicate-review behavior, operator approval artifact, and review
response intake path are defined and tested.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Audit]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Preview]] - [[ChaseOS-Pulse-Agent-Bus-Review-Request-Contract]] - [[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
