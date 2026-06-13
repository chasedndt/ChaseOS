# ChaseOS Pulse Real Approval Artifact Rehearsal

**Status:** PARTIAL - governed artifact-chain rehearsal  
**Created:** 2026-05-01  
**Runtime label:** Codex  
**Scope:** Pulse candidate -> approval request -> evidence -> supervised rehearsal

## Purpose

This pass creates a real, repo-local Pulse approval artifact chain from the
existing user Pulse deck without performing live Agent Bus enqueue.

It closes the gap identified by the supervised live-enqueue rehearsal pass:
the repo previously had the code path, but no live Pulse candidate, approval
request, or evidence artifact to inspect.

## Runtime Surface

Runtime module:

```text
runtime/pulse/real_approval_artifact_rehearsal.py
```

Focused tests:

```text
runtime/pulse/test_real_approval_artifact_rehearsal.py
```

## Artifact Chain Created

The live rehearsal run created:

- feedback candidate:
  `07_LOGS/Pulse-Decks/feedback-candidates/2026-05-01-feedback-candidates.jsonl`
- Agent Bus approval request:
  `07_LOGS/Pulse-Decks/agent-bus-approval-requests/2026-05-01-agent-bus-approval-requests.jsonl`
- enqueue evidence record:
  `07_LOGS/Pulse-Decks/agent-bus-enqueue-evidence/2026-05-01-agent-bus-enqueue-evidence.jsonl`

Live record IDs:

- candidate: `feedback-candidate-pulse-user-2026-04-29-01-show_more_like_this-6623cb04ce4a`
- request: `pulse-bus-enqueue-approval-f59f16c29a9a`
- evidence: `pulse-bus-enqueue-evidence-20318b971e53`

## Rehearsal Result

The supervised rehearsal correctly remained blocked:

```text
status: blocked_pending_operator_gate_approval
ready_for_manual_enqueue: false
```

Missing evidence:

- `operator_enqueue_approval`
- `gate_policy_defined`
- `external_sender_allowance`
- `duplicate_work_fingerprint_review`

This is intentional. Codex did not claim operator approval or Gate approval.

## Boundary

This surface does not:

- grant or execute approval
- mutate Gate policy
- write Agent Bus tasks
- dispatch Hermes, OpenClaw, Codex, or other runtimes
- ingest review responses
- apply candidates
- approve memory
- mutate Personal Map
- mutate runtime memory
- call providers or connectors
- activate schedules
- write canonical project or knowledge state
- update the R&D workbook

## Next Step

The next pass should be operator-approved live Agent Bus REVIEW enqueue using
the existing guarded command only if the operator supplies the missing approval
evidence:

```text
chaseos pulse enqueue-candidate pulse-bus-enqueue-approval-f59f16c29a9a --evidence-id pulse-bus-enqueue-evidence-20318b971e53
```

That command must not be run until the missing evidence is explicitly supplied
and the supervised rehearsal returns `ready_for_manual_enqueue: true`.

Graph links: [[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Supervised-Live-Enqueue-Rehearsal]] - [[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
