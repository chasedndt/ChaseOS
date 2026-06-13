# ChaseOS Pulse Agent Bus Enqueue Approval Request

**Status:** PARTIAL - persisted approval-request record scaffold  
**Date:** 2026-04-30  
**Runtime:** Codex  
**Runtime scaffold:** `runtime/pulse/bus_enqueue_approval_request.py`

## Purpose

This pass adds an append-only approval-request lane for Pulse Agent Bus enqueue
intent.

It records that a Pulse enqueue preflight is ready for operator/Gate review. It
does not grant approval, write Agent Bus tasks, dispatch runtimes, ingest review
responses, apply candidates, or mutate canonical ChaseOS state.

## Artifact Path

Approval-request records are stored under the existing Pulse log tree:

```text
07_LOGS/Pulse-Decks/agent-bus-approval-requests/YYYY-MM-DD-agent-bus-approval-requests.jsonl
```

This is a Pulse log artifact lane, not a second datastore and not Agent Bus task
state.

## Request Shape

Each approval request preserves:

- request ID
- preflight ID
- review contract ID
- candidate ID and candidate kind
- operation: `pulse.agent_bus.enqueue_review`
- sender, recipient, intent, and priority
- request text and expected output
- work fingerprint for duplicate review
- task payload preview
- source log, deck, card, target, and runtime refs where known
- required approvals
- blocked effects

The request status is:

```text
approval_requested
```

That status is not approval. It is a pending review record only.

## Required Approvals

The request preserves the same required approvals as the preflight:

- `operator_enqueue_approval`
- `gate_policy_defined`
- `external_sender_allowance`
- `duplicate_work_fingerprint_review`

The current scaffold records those requirements but does not satisfy them.

## Guardrails

The approval-request lane enforces:

- `approval_granted: false`
- `gate_policy_defined: false`
- `duplicate_check_performed: false`
- `live_agent_bus_handoff_allowed: false`
- `agent_bus_task_written: false`
- `approval_executed: false`
- `review_response_ingest_allowed: false`
- `candidate_apply_allowed: false`
- `canonical_writeback_allowed: false`
- `second_datastore_write_allowed: false`

## Non-Goals

This pass does not implement:

- live Agent Bus task handoff
- approval execution
- Gate approval validation
- duplicate suppression against live bus task history
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
- R&D workbook sync

## Verification

Focused tests assert:

- the module does not import the live Agent Bus writer/backend
- build-only request creation is read-only until persistence is explicitly
  called
- persistence writes only under the Pulse approval-request log lane
- ledger reads are read-only and create no folders on empty reads
- forbidden approval, enqueue, apply, provider, schedule, datastore, and
  canonical-writeback flags are rejected

## Next Pass

The next safe pass is a Gate/operator approval validation design. It should
define how an approval request is reviewed, denied, or marked ready without
creating a live task. Live Agent Bus handoff should remain separate from request
creation and approval validation.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Design]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Audit]] - [[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
