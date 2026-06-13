---
title: SiteOps Candidate Executor Approval Rebind Spec
type: architecture
status: PARTIAL / VERIFIED TARGETED / NO-WRITE
created: 2026-04-30
updated: 2026-04-30
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Approval Rebind Spec

`chaseos siteops candidates approval-rebind-spec` is a no-write SiteOps
candidate promotion contract for legacy or unbound approval artifacts.

It does not create, mutate, approve, reject, consume, or supersede approval
artifacts.

## Current Surface

Command:

```powershell
chaseos siteops candidates approval-rebind-spec CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_approval_rebind_spec(...)
```

The command checks current approval provenance and returns the future
supersession/rebind policy required before a trusted executor may consume an
approval.

## Status Outputs

```text
approval_rebind_not_required_bound_match
```

The approval already binds to the current candidate and proposed skill.

```text
approval_rebind_spec_required_no_write_authority
```

The approval is legacy/unbound. A future separate approval request must be
created with explicit `candidate_id` and `proposed_skill_id` metadata.

```text
blocked_bound_mismatch_requires_new_approval
```

The approval binds to a different candidate or proposed skill and must not be
reused.

```text
blocked_approval_not_approved
```

Pending or rejected approvals cannot be consumed by a future executor.

## Rebind Policy

Current policy:

- default: fail closed
- legacy unbound approval: do not mutate in place
- bound mismatch: reject existing approval for this candidate path
- replacement approval: future separate request with candidate and skill metadata
- legacy artifact retention: preserve as historical audit record
- executor dependency: future executor requires `bound_match`

## Future Replacement Requirements

A future replacement approval must:

- be newly created through `request-promotion`
- bind `candidate_id`
- bind `proposed_skill_id`
- preserve trusted target metadata
- be separately approved by an authorized operator
- supersede by reference, not by mutating the legacy artifact

That behavior is not implemented in this pass.

## Explicit Denials

This surface performs no:

- legacy approval mutation
- replacement approval request write
- approval decision write
- audit event write
- inactive trusted artifact write
- executor implementation
- Gate allowlist mutation
- Browser Skill write
- SiteOps Skill Card write
- browser/CDP/Browser Use execution
- Agent Bus enqueue
- provider/API call
- skill activation
- canonical ChaseOS writeback

Hermes remains reviewer/shadow only and does not own this runtime path.

## Status

Current status: PARTIAL / VERIFIED TARGETED / NO-WRITE.

This is a prerequisite contract before any future trusted artifact executor is
allowed to consume approval evidence.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Collision-Policy-Spec]] - [[SiteOps-Candidate-Inactive-Artifact-Validator]] - [[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
