# ChaseOS Pulse Approval Readiness Summary

**Status:** PARTIAL - read-only approval readiness surface  
**Created:** 2026-05-01  
**Runtime label:** Codex  
**Scope:** Pulse Agent Bus approval handoff readiness

## Purpose

The approval readiness summary gives operators and runtimes a compact answer to:

```text
Can the current Pulse candidate be manually enqueued for runtime review yet?
```

It sits above the existing request, evidence, handoff preflight, operator/Gate
contract, and supervised rehearsal surfaces. It does not replace them; it
summarizes them.

## Runtime Surface

Module:

```text
runtime/pulse/approval_readiness_summary.py
```

CLI:

```text
chaseos pulse approval-readiness [REQUEST_ID] [--evidence-id EVIDENCE_ID] [--json]
```

Focused test:

```text
runtime/pulse/test_approval_readiness_summary.py
```

## Current Live Status

The current live Pulse request remains blocked:

```text
readiness_status: blocked_missing_required_evidence
request_id: pulse-bus-enqueue-approval-f59f16c29a9a
evidence_id: pulse-bus-enqueue-evidence-20318b971e53
```

Missing evidence:

- `operator_enqueue_approval`
- `gate_policy_defined`
- `external_sender_allowance`
- `duplicate_work_fingerprint_review`

Read-only live checks also show:

- no active duplicate work fingerprint for the current request
- Agent Bus target snapshot is readable
- no supervised live command preview is exposed while evidence is missing
- structured `approval_evidence_slots` are now emitted for the four required evidence items, each with `approval_key`, `satisfied`, `required_ref`, current `ref`, and its bounded capture command

## Structured Evidence Slots

`approval-readiness --json` now exposes machine-readable approval slots for:

| Slot | Required ref | Purpose |
|---|---|---|
| `operator_enqueue_approval` | `operator-approval-ref` | explicit operator authorization for the future live review enqueue |
| `gate_policy_defined` | `gate-policy-ref` | Gate policy reference proving the handoff policy is defined before enqueue |
| `external_sender_allowance` | `allowance-ref` | allowance reference for the non-runtime `Operator` sender seam |
| `duplicate_work_fingerprint_review` | `duplicate-review-ref` | duplicate review reference for the Pulse review work fingerprint |

The slots are visibility only. They do not write evidence, grant approval, enqueue the task, or expose the live command preview while any required slot is unsatisfied.

As of the Hermes/Optimus 2026-05-02 continuation pass, any evidence slot marked satisfied must carry its corresponding explicit reference at evidence-record construction time. Generic rehearsal notes cannot satisfy or surface as operator approval refs unless `--operator-approved` is also present, and the Gate policy, external sender allowance, and duplicate work-fingerprint slots require their dedicated ref fields. This keeps future live enqueue readiness tied to auditable approval evidence rather than ambiguous notes.

As of the Hermes/Optimus 2026-05-02 placeholder-hardening continuation, the evidence record layer also rejects literal CLI placeholders such as `<operator-approval-ref>`, `<gate-policy-ref>`, `<allowance-ref>`, and `<duplicate-review-ref>`. The capture commands remain operator-facing templates only; future evidence capture must replace them with real approval/policy/allowance/duplicate-review references before any slot can become satisfied.

As of the Hermes/Optimus 2026-05-02 slot-metadata continuation, each structured evidence slot also exposes `ref_placeholder`, `requires_real_ref: true`, and `placeholder_ref_rejected: true`. This lets the future Phase 10/operator UI distinguish a safe command template from an acceptable evidence value without parsing the shell command string.

As of the Hermes/Optimus 2026-05-02 authority-metadata continuation, each evidence slot also exposes `authority_class` and `runtime_self_satisfiable`. The remaining operator approval, Gate policy, and external sender allowance slots are explicitly not runtime-self-satisfiable; bounded queue inspection such as duplicate work_fingerprint review is runtime-self-satisfiable because it is factual read-only evidence rather than an approval or policy grant.

As of the Codex 2026-05-02 CLI metadata sync, the canonical CLI command contract also declares those nested `approval_evidence_slots` fields for `pulse_approval_readiness_summary` and `pulse_operator_gate_approval_ui_contract`. This is schema metadata only; it does not grant approval or execute handoff.

As of the Codex 2026-05-02 final evidence-gate continuation, the CLI also
exposes:

```text
chaseos pulse final-evidence-gate [REQUEST_ID] [--evidence-id EVIDENCE_ID] [--json]
```

This combines approval readiness and completion status into a final read-only
operator packet. It names remaining non-runtime-self-satisfiable slots,
distinguishes runtime-self-satisfiable evidence gaps from operator/Gate/external
sender authority gaps, and keeps the supervised live enqueue command hidden
until every required evidence slot is satisfied by a real ref.

## Boundary

This surface is read-only. It does not:

- write evidence
- grant approval
- execute live enqueue
- write Agent Bus tasks
- dispatch runtimes
- ingest review responses
- apply candidates
- mutate memory, Personal Map, Now, Project-OS, or `02_KNOWLEDGE/`
- call providers or connectors
- activate schedules
- update the R&D workbook

The final evidence gate shares this boundary.

## Completion Role

This pass improves operator/runtime visibility only. ChaseOS Pulse remains
`backend_proof_pending` until a separately approved live enqueue, review ingest,
candidate apply, truth-state audit, and R&D update occur.

Graph links: [[ChaseOS-Pulse-Completion-Status]] - [[ChaseOS-Pulse-Completion-Tracker]] - [[ChaseOS-Pulse-Supervised-Live-Enqueue-Rehearsal]] - [[ChaseOS-Pulse-Final-Evidence-Gate]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
