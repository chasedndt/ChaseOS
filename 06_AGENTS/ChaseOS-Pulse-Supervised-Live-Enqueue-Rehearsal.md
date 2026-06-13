# ChaseOS Pulse Supervised Live-Enqueue Rehearsal

**Status:** PARTIAL - dry-run procedure packet  
**Created:** 2026-05-01  
**Runtime label:** Codex  
**Scope:** Pulse Agent Bus handoff rehearsal

## Purpose

The supervised live-enqueue rehearsal is the final dry-run checkpoint before an
operator manually runs the guarded Pulse Agent Bus enqueue command.

It exists because a ready operator/Gate contract is still not approval
execution. The rehearsal makes the operator procedure explicit without creating
Agent Bus tasks.

## Runtime Surface

Runtime module:

```text
runtime/pulse/supervised_live_enqueue_rehearsal.py
```

CLI:

```text
chaseos pulse supervised-enqueue-rehearsal REQUEST_ID [--evidence-id EVIDENCE_ID]
```

## Procedure

1. Load the operator/Gate approval UI contract.
2. Verify the contract is ready.
3. Confirm duplicate-work posture is still clear.
4. Expose the manual `enqueue-candidate` command preview only when ready.
5. List required operator steps for the actual supervised enqueue.

If the operator/Gate contract is blocked, the rehearsal hides the command
preview and reports blocked reasons.

## Boundary

This surface does not:

- persist rehearsal artifacts
- execute live enqueue
- grant or execute approval
- mutate Gate policy
- write Agent Bus tasks
- dispatch runtimes
- ingest review responses
- apply candidates
- call providers/connectors
- activate schedules
- mutate canonical state

The actual live handoff remains the existing guarded command:

```text
chaseos pulse enqueue-candidate REQUEST_ID --evidence-id EVIDENCE_ID
```

That command should be run only after the operator reviews the rehearsal
output and explicitly chooses to proceed.

## Current Repo State

As of 2026-05-01, the live vault now has a real Pulse feedback candidate,
approval-request artifact, and enqueue-evidence artifact from the real approval
artifact rehearsal pass:

- candidate: `feedback-candidate-pulse-user-2026-04-29-01-show_more_like_this-6623cb04ce4a`
- request: `pulse-bus-enqueue-approval-f59f16c29a9a`
- evidence: `pulse-bus-enqueue-evidence-20318b971e53`

The supervised rehearsal remains blocked because the evidence record does not
claim operator approval, Gate policy definition, external-sender allowance, or
duplicate-work-fingerprint review. No Agent Bus task or enqueue result exists.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Operator-Gate-Approval-UI-Contract]] - [[Pulse-Feedback-Policy]] - [[ChaseOS-Pulse-Real-Approval-Artifact-Rehearsal]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
