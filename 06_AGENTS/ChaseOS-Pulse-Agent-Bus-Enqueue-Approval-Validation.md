# ChaseOS Pulse Agent Bus Enqueue Approval Validation

**Status:** PARTIAL - non-executing approval validation scaffold  
**Date:** 2026-04-30  
**Runtime:** Codex  
**Runtime scaffold:** `runtime/pulse/bus_enqueue_approval_validation.py`

## Purpose

This pass adds an in-memory validation layer for Pulse Agent Bus enqueue
approval-request records.

It checks whether a request has the evidence needed for final handoff review.
It does not grant approval, execute approval, mutate Gate policy, query live
Agent Bus duplicates, write Agent Bus tasks, dispatch runtimes, ingest review
responses, apply candidates, or mutate canonical ChaseOS state.

## Inputs

Validation consumes:

- persisted approval-request records from
  `07_LOGS/Pulse-Decks/agent-bus-approval-requests/`
- explicit validation evidence supplied by a caller/reviewer

It does not inspect the live Agent Bus task database for duplicate suppression
in this pass.

## Evidence Shape

`PulseAgentBusApprovalValidationEvidence` records whether these required
approval conditions are present:

- `operator_enqueue_approval_present`
- `gate_policy_defined`
- `external_sender_allowance_present`
- `duplicate_work_fingerprint_reviewed`

These booleans are evidence inputs, not authority grants. The persisted enqueue evidence record layer now additionally requires every satisfied boolean to carry its explicit auditable reference and rejects literal template placeholders such as `<operator-approval-ref>`, `<gate-policy-ref>`, `<allowance-ref>`, and `<duplicate-review-ref>`; capture-command placeholders must be replaced with real refs before readiness can advance.

## Validation Statuses

Validation returns one of:

- `blocked_missing_required_evidence`
- `ready_for_final_handoff_review`

`ready_for_final_handoff_review` is still not live handoff permission. It only
means the request can move to a separate final operator/Gate review surface.

## Guardrails

The validation result enforces:

- `validation_record_only: true`
- `persisted_validation: false`
- `approval_granted: false`
- `approval_executed: false`
- `gate_policy_mutated: false`
- `duplicate_query_performed: false`
- `live_agent_bus_handoff_allowed: false`
- `agent_bus_task_written: false`
- `review_response_ingest_allowed: false`
- `candidate_apply_allowed: false`
- `canonical_writeback_allowed: false`
- `second_datastore_write_allowed: false`

## Non-Goals

This pass does not implement:

- persisted validation records
- approval grants
- Gate policy mutation
- duplicate querying against live Agent Bus history
- live Agent Bus handoff
- runtime dispatch
- review-response ingestion
- candidate apply effects
- canonical writeback
- R&D workbook sync

## Verification

Focused tests assert:

- the module does not import the live Agent Bus writer/backend
- default validation blocks all missing evidence
- partial validation lists remaining missing approvals
- full evidence returns `ready_for_final_handoff_review` while still
  non-executable
- validation by request ID reads existing request logs without writing
- validation ledgers are read-only and create no folders on empty reads
- forbidden approval, execution, runtime, provider, schedule, datastore, and
  canonical-writeback flags are rejected

## Next Pass

The next safe pass is a final handoff review design. It should remain
non-executing until the operator explicitly approves live Agent Bus handoff and
the duplicate-review mechanism is defined.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Approval-Request]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Design]] - [[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
