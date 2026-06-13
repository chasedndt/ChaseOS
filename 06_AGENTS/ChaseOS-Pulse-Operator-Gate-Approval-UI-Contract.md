# ChaseOS Pulse Operator/Gate Approval UI Contract

**Status:** PARTIAL - contract-only runtime surface  
**Created:** 2026-04-30  
**Runtime label:** Codex  
**Scope:** Pulse Agent Bus handoff approval contract

## Purpose

The Pulse operator/Gate approval UI contract is the bridge between a non-live
handoff preflight and a future human approval surface.

It does not build the visual UI. It produces a structured packet that a future
Studio or operator surface can render without inventing approval semantics.

## Contract Flow

1. Load a persisted Pulse Agent Bus approval request.
2. Load the specified or latest enqueue evidence record.
3. Re-run handoff preflight against approval validation, duplicate posture, and
   Agent Bus target posture.
4. Emit visible evidence fields for operator/Gate review.
5. Expose decision controls.
6. Expose a supervised live enqueue command preview only when the preflight is
   ready.

## Supported Decisions

- `approve_supervised_live_enqueue`
- `reject_handoff`
- `request_more_evidence`
- `refresh_handoff_preflight`

Enabled approval controls still require explicit operator confirmation. A ready
contract is not itself an approval grant.

## Visible Evidence Fields

- `request_id`
- `evidence_id`
- `handoff_status`
- `validation_status`
- `satisfied_approvals`
- `missing_approvals`
- `approval_evidence_slots`
- `duplicate_found`
- `active_duplicate_task_ids`
- `target_recipient`
- `target_active_task_count`
- `blocked_reasons`

## Runtime Surface

Runtime module:

```text
runtime/pulse/operator_gate_approval_contract.py
```

CLI:

```text
chaseos pulse operator-gate-contract REQUEST_ID [--evidence-id EVIDENCE_ID]
```

The command reads approval-request and enqueue-evidence artifacts, inspects
Agent Bus target posture, and prints the contract. It does not persist a
contract artifact.

As of the Hermes/Optimus 2026-05-01 continuation pass, the operator/Gate
contract also mirrors the read-only approval readiness surface by exposing
`approval_evidence_slots`. These slots enumerate the four required approval
evidence items, whether each slot is satisfied, any recorded ref/note, and the
bounded `chaseos pulse enqueue-evidence ...` capture command to use after the
operator supplies explicit evidence. This makes the future Phase 10 surface
able to show what remains blocked without fabricating approval or executing a
live handoff.

As of the Hermes/Optimus 2026-05-02 evidence-ref hardening pass, the contract
only surfaces a slot `ref` when that slot is satisfied by its explicit evidence
flag. Generic notes on an unsatisfied evidence record remain visible only as
record notes elsewhere; they do not become operator approval refs. Satisfied
slots now require the matching auditable reference (`--note` for operator
approval, and dedicated Gate policy / sender allowance / duplicate review refs
for the other slots) before the evidence record can validate.

As of the Hermes/Optimus 2026-05-02 slot-metadata pass, each contract evidence
slot also carries `ref_placeholder`, `requires_real_ref: true`, and
`placeholder_ref_rejected: true`. Phase 10/operator UI code can therefore render
safe capture templates while treating literal placeholder strings as invalid
evidence values.

As of the Hermes/Optimus 2026-05-02 authority-metadata pass, each contract
evidence slot also carries `authority_class` and `runtime_self_satisfiable`.
The operator approval, Gate policy, and external sender allowance slots are
marked non-self-satisfiable by a runtime instance; only bounded queue-inspection
evidence such as duplicate work_fingerprint review is marked runtime-self-
satisfiable. This gives the future operator UI a machine-readable split between
runtime-preparable evidence and decisions/policies that still require explicit
operator/Gate authority.

As of the Codex 2026-05-02 CLI metadata sync, the generated CLI command contract
also declares those nested slot metadata fields for the operator/Gate contract
JSON shape. The metadata is descriptive only and does not persist a contract,
grant approval, or write an Agent Bus task.

The next dry-run procedure layer is:

```text
chaseos pulse supervised-enqueue-rehearsal REQUEST_ID [--evidence-id EVIDENCE_ID]
```

That command rehearses the operator procedure and exposes the manual
`enqueue-candidate` command preview when ready, but still does not execute it.

## Blocked Effects

The contract must keep these false:

- visual UI built
- persisted contract
- approval granted
- approval executed
- Gate policy mutated
- live Agent Bus handoff allowed
- Agent Bus task written
- runtime dispatch allowed
- review-response ingest allowed
- candidate apply allowed
- canonical writeback allowed
- second datastore write allowed
- provider or connector call allowed
- schedule activation allowed

## Current Boundary

This is Phase 9 backend/control-plane scaffolding. Phase 10 may render this
contract inside Studio, but the visual surface must consume these contract
fields rather than granting new authority.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[Pulse-Feedback-Policy]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Approval-Validation]] - [[ChaseOS-Pulse-Agent-Bus-Handoff-Preflight]]

*Graph links: [[OpenClaw-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
