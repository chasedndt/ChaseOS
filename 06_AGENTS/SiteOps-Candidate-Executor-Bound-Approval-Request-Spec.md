---
title: SiteOps Candidate Executor Bound Approval Request Spec
type: architecture
status: PARTIAL / VERIFIED TARGETED / NO-WRITE
created: 2026-05-01
updated: 2026-05-01
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Bound Approval Request Spec

`chaseos siteops candidates bound-approval-request-spec` is a no-write SiteOps
candidate promotion contract for the future replacement approval artifact that
may supersede a legacy-unbound approval.

It does not create, persist, approve, reject, consume, supersede, or mutate
approval artifacts.

## Current Surface

Command:

```powershell
chaseos siteops candidates bound-approval-request-spec CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_bound_approval_request_spec(...)
```

The command composes `approval-rebind-spec`, builds the proposed replacement
approval request payload in memory, validates required binding metadata, and
returns the future writer requirements.

## Status Outputs

```text
bound_approval_request_spec_ready_no_write
```

The legacy approval is unbound, the replacement approval payload contains the
required candidate, skill, scope, action, and supersession metadata, and a
future writer may be designed in a separate pass.

```text
blocked_before_bound_approval_request_spec
```

The rebind spec is not ready, the existing approval is not the expected
legacy-unbound case, or the proposed replacement payload failed validation.

## Replacement Artifact Contract

The in-memory artifact must include:

- new `approval_id`
- `tenant_id`
- `workspace_id`
- `user_id`
- new `run_id`
- `workflow_id: browser_skill_candidate.promotion`
- `action: browser_skill_candidate.promote`
- `status: pending`
- `required_approver_role: tenant_admin`
- `supersedes_approval_id`
- `supersession_policy`
- metadata binding:
  - `approval_binding_version`
  - `candidate_id`
  - `proposed_skill_id`
  - `trusted_skill_path`
  - `siteops_skill_card_path`
  - `promotion_action`
  - `legacy_approval_provenance_status`
  - `replacement_reason`

## Validation Checks

The no-write spec validates:

- candidate metadata is bound,
- tenant/workspace/user scope is bound,
- legacy approval remains immutable,
- separate operator review is required,
- approval action matches the promotion action.

## Explicit Denials

This surface performs no:

- bound approval request write
- legacy approval mutation
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

This is a prerequisite contract before any future approval writer can create a
new bound approval request for a legacy-unbound candidate promotion approval.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Approval-Rebind-Spec]] - [[SiteOps-Candidate-Executor-Collision-Policy-Spec]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
