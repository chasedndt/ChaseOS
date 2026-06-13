# ChaseOS Pulse Final Evidence Gate

**Status:** PARTIAL / READ-ONLY  
**Created:** 2026-05-02  
**Runtime label:** Codex  
**Purpose:** Provide a final operator-facing evidence gate before any ChaseOS Pulse Agent Bus live enqueue.

## Summary

The final evidence gate is a read-only Pulse control-plane surface. It combines
the Pulse approval-readiness summary with the Pulse completion-status tracker and
answers:

- which Pulse Agent Bus approval request is current
- which evidence record is being evaluated
- which approval slots are satisfied
- which approval slots remain missing
- whether remaining slots require operator/Gate/external-sender authority
- whether any remaining slot is runtime-self-satisfiable
- whether a supervised live enqueue command may be shown
- which feature blockers still prevent calling Pulse complete

It is not an approval grant and does not execute handoff.

## CLI Surface

```text
chaseos pulse final-evidence-gate [REQUEST_ID] [--evidence-id EVIDENCE_ID] [--json]
```

The command may use the latest Pulse Agent Bus approval request when
`REQUEST_ID` is omitted.

## Adopted Schema

The runtime module is:

```text
runtime/pulse/final_evidence_gate.py
```

The output schema is `PulseFinalEvidenceGateStatus` and includes:

- `gate_status`
- `request_id`
- `evidence_id`
- `candidate_id`
- `candidate_kind`
- `recipient`
- `work_fingerprint`
- `completion_status`
- `feature_done`
- `backend_control_plane_done`
- `readiness_status`
- `ready_for_operator_gate_decision`
- `ready_for_manual_enqueue`
- `ready_for_live_enqueue`
- `operator_action_required`
- `can_runtime_self_satisfy_remaining`
- `closure_status`
- `closure_authority_classes`
- `closure_runtime_action_keys`
- `satisfied_approvals`
- `missing_approvals`
- `missing_operator_action_slots`
- `missing_authority_action_slots`
- `missing_runtime_self_satisfiable_slots`
- `approval_evidence_slots`
- `evidence_capture_command_hints`
- `next_required_actions`
- `final_feature_blockers`
- `supervised_live_command_preview`

## Authority Boundary

As of the Hermes/Optimus 2026-05-02 slot-partition continuation, the final gate
separates missing evidence into two machine-readable partitions:

- `missing_authority_action_slots`: missing slots that require explicit operator,
  Gate, or external-sender policy authority and cannot be completed by a runtime
  instance.
- `missing_runtime_self_satisfiable_slots`: missing slots that a runtime instance
  may satisfy through bounded factual inspection, such as duplicate
  work_fingerprint review.

`operator_action_required` is true when the authority partition is non-empty.
`can_runtime_self_satisfy_remaining` is true only when every remaining missing
slot is in the runtime-self-satisfiable partition. The companion closure fields
make the final state directly consumable by operator UI and runtime-instance
lanes:

- `closure_status` is one of:
  - `blocked_by_external_authority`
  - `runtime_self_satisfiable_evidence_missing`
  - `blocked_by_active_duplicate`
  - `ready_for_supervised_live_enqueue`
- `closure_authority_classes` lists the authority classes still blocking closure.
- `closure_runtime_action_keys` lists bounded runtime-preparable evidence slots
  still missing or active queue-hygiene blockers such as
  `active_duplicate_work_fingerprint`.

This keeps the final gate's next-action routing explicit for Phase 10 UI and
runtime-instance lanes without granting approval or enqueue authority.

The final evidence gate is read-only. It explicitly does not:

- write evidence
- grant approval
- execute live enqueue
- write Agent Bus tasks
- dispatch runtimes
- ingest review responses
- apply candidates
- mutate memory, Personal Map, Now, Project-OS, governance docs, or `02_KNOWLEDGE/`
- call providers or connectors
- activate schedules
- update the R&D workbook

## Current Live Interpretation

As of this pass, the current Pulse approval chain may have all evidence refs
satisfied but still remain blocked if an active Agent Bus task already exists for
the same `work_fingerprint`. In that case, the final gate reports:

```text
closure_status=blocked_by_active_duplicate
closure_runtime_action_keys=["active_duplicate_work_fingerprint"]
```

The final gate must not expose another live enqueue command while the duplicate
is active. If no duplicate exists and all refs are recorded, the gate may report
`ready_for_supervised_live_enqueue`; candidate application still remains a later,
separate governed step.

## Completion Role

This pass narrows the remaining backend-control-plane work. ChaseOS Pulse is
still not feature-complete. Remaining work still includes explicit operator/Gate
approval evidence, live REVIEW enqueue, real review-response ingest, governed
candidate apply, truth-state audit, Phase 10 UI completion, and R&D workbook
update only after approval.

Graph links: [[ChaseOS-Pulse-Approval-Readiness-Summary]] - [[ChaseOS-Pulse-Completion-Status]] - [[ChaseOS-Pulse-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
