---
title: SiteOps Candidate Executor Bound Approval Writer Design
type: architecture
status: PARTIAL / VERIFIED TARGETED / NO-WRITE DESIGN
created: 2026-05-01
updated: 2026-05-01
phase: Phase 9 - Browser Runtime Skill Memory / SiteOps candidate promotion guardrails
runtime: Codex
knowledge_class: system-operational
---

# SiteOps Candidate Executor Bound Approval Writer Design

This note records the no-write design surface for a future bound approval request writer.

The runtime helper is `candidate_promotion_bound_approval_writer_design(...)` and the CLI surface is:

```bash
chaseos siteops candidates bound-approval-writer-design CANDIDATE_ID \
  --approval-id APPROVAL_ID \
  --tenant TENANT_ID \
  --workspace WORKSPACE_ID \
  --user USER_ID \
  --json
```

## Current Behavior

The command composes `bound-approval-request-spec`, computes a future scoped approval artifact path under `07_LOGS/SiteOps-Approvals/<tenant>/<workspace>/`, validates path confinement and target absence, and returns a writer sequence, audit event contract, idempotency policy, and rollback policy.

It writes nothing.

Ready status:

- `bound_approval_writer_design_ready_no_write`

Blocked statuses include:

- `blocked_bound_approval_request_spec: <status>`
- `blocked_existing_bound_approval_request_target`
- `blocked_bound_approval_writer_path_boundary`

## Boundary

This pass does not:

- build or run the approval writer
- write a replacement approval request
- mutate or consume the legacy approval
- decide approvals
- write audit events or idempotency markers
- write Browser Skill or SiteOps Skill Card artifacts
- implement `apply_trusted_candidate_artifacts`
- edit Gate allowlists
- launch or control browsers
- enqueue Agent Bus work
- call providers
- activate skills
- write canonical ChaseOS state

## Security Requirements

A future writer must:

- recompute the bound approval request spec immediately before writing
- write only a new pending approval artifact
- preserve the legacy approval unchanged as historical audit evidence
- validate candidate, proposed skill, tenant, workspace, user, action, and supersession metadata
- confine the target path to the scoped SiteOps approvals lane
- fail closed on target collision unless exact idempotency is separately reviewed
- emit scoped audit without raw candidate content, secrets, cookies, tokens, credentials, or session state
- leave the trusted artifact executor locked until a later approved executor/Gate pass

## Placement

This remains Phase 9 runtime/operator infrastructure. The Phase 10 Site Skills UI can later inspect candidate status, replacement approval requests, and promotion readiness, but it must not silently promote skills or write approval artifacts.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Skill-Memory]] - [[SiteOps-Candidate-Executor-Bound-Approval-Request-Spec]] - [[SiteOps-Candidate-Executor-Collision-Policy-Spec]] - [[Permission-Matrix]] - [[Trust-Tiers]]
