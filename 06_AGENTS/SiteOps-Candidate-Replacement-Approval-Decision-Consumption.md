---
title: SiteOps Candidate Replacement Approval Decision Consumption
type: architecture
status: COMPLETE / VERIFIED TARGETED / DECISION-WRITE ONLY
created: 2026-05-01
updated: 2026-05-01
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Replacement Approval Decision Consumption

This pass adds the bounded decision path for SiteOps Browser Skill candidate
replacement approvals.

It exists because legacy unbound promotion approvals cannot be consumed for
trusted Browser Skill or SiteOps Skill Card writes. The bounded approval writer
can create a new pending replacement approval with candidate/skill/scope
metadata. This decision-consumption path can then approve or reject only that
bound replacement approval.

## Command

```powershell
chaseos siteops candidates replacement-approval-decision-consumption `
  <candidate_id> `
  --replacement-approval-id <approval_id> `
  --tenant local `
  --workspace default `
  --user local-user `
  --actor local-user `
  --decision approve `
  --write-approval-decision `
  --json
```

Without `--write-approval-decision`, the command performs a non-mutating
readiness check.

## Scope Rules

The helper fails closed unless `tenant_id`, `workspace_id`, and `user_id` are
all present. It only searches approval records inside the requested tenant.

The target approval must:

- match the requested tenant/workspace/user scope
- be for `browser_skill_candidate.promote`
- carry `approval_binding_version: browser_skill_candidate.v1`
- bind the requested `candidate_id`
- bind the candidate's proposed skill id
- include `supersedes_approval_id`
- require `tenant_admin` approval

Already-approved bound replacement approvals report
`replacement_approval_consumption_ready_no_trusted_write`.

## What It Can Write

Only when `--write-approval-decision` is supplied and the replacement approval
is still pending, it can write the normal `ApprovalRequest` decision update and
the corresponding scoped `approval_decision` audit event. If `--reason` is
supplied, the reason is persisted in the approval record and audit metadata.

It does not write a consumption marker.

## Explicitly Not Added

This pass does not:

- consume the replacement approval
- mutate the superseded legacy approval
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- implement `apply_trusted_candidate_artifacts`
- edit Gate allowlists
- launch browsers
- enqueue Agent Bus work
- call provider APIs
- activate promoted skills
- write canonical ChaseOS memory/state

## Verification

Focused SiteOps candidate tests passed: `88 passed`.

Focused tests cover:

- approval decision writes only the bound replacement approval
- dry-run decision checks do not mutate approval artifacts
- already-approved replacement approvals become consumption-ready without
  trusted writes
- decision reasons persist to the approval record and scoped audit event
- missing scope fails closed
- CLI JSON path for decision-write only

The live local candidate remains blocked because the source legacy approval is
pending/unbound, so no live replacement approval exists in the real workspace.

## Next Pass

The next pass should define the trusted inactive Browser Skill and SiteOps Skill
Card writer or its immediate preflight. That pass must still require the bound
replacement approval to be approved and must stay behind the Gate operation
`siteops.browser_skill_candidate.apply_trusted_artifacts`.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] -
[[SiteOps-Candidate-Bound-Approval-Writer-Implementation]] -
[[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
