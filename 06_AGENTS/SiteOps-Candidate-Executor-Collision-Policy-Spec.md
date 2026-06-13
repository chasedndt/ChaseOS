---
title: SiteOps Candidate Executor Collision Policy Spec
type: architecture
status: PARTIAL / VERIFIED TARGETED / NO-WRITE
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Collision Policy Spec

This note documents the no-write collision, overwrite, idempotency, and
rollback policy packet for future Browser Skill candidate trusted artifact
writes.

It does not implement the executor.

## Current Surface

Command:

```powershell
chaseos siteops candidates collision-policy-spec CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_collision_policy_spec(...)
```

The command composes the inactive-artifact validator and checks future trusted
Browser Skill / SiteOps Skill Card target paths without writing anything.

## Policy

Current collision policy:

- default: fail closed,
- pre-existing trusted target: block,
- overwrite: forbidden without separate operator approval and collision review,
- idempotent no-op: future-only after exact provenance and payload match,
- partial write: future executor must roll back or mark recovery required,
- activation after write: forbidden,
- canonical writeback after write: forbidden.

## Target Checks

The packet reports, per target:

- artifact kind,
- target path,
- path confinement,
- disk existence,
- collision status,
- overwrite allowance,
- idempotent no-op allowance,
- manual review requirement,
- write allowance in this pass.

All write allowance values remain false.

## Denied Effects

The collision policy spec performs no:

- inactive trusted artifact write,
- overwrite,
- idempotent apply marker,
- audit event write,
- executor implementation,
- Gate allowlist mutation,
- browser/CDP/Browser Use/Browser Harness execution,
- Agent Bus enqueue,
- provider/API call,
- activation,
- canonical ChaseOS writeback.

## Current Verdict

`collision-policy-spec` is a no-write policy contract. A future executor must
fail closed on any target collision unless a separate operator-approved
collision review exists. This pass only makes that rule testable and visible.

Hermes remains reviewer/shadow only and does not own this runtime path.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]] - [[SiteOps-Candidate-Executor-Preimplementation-Verifier]] - [[SiteOps-Candidate-Executor-Implementation-Design-Review]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Skill-Memory]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
