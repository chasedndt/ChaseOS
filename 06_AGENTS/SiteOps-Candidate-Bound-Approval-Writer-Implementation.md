---
title: SiteOps Candidate Bound Approval Writer Implementation
type: architecture-note
status: COMPLETE / VERIFIED TARGETED / BOUNDED WRITER
created: 2026-05-01
updated: 2026-05-01
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Bound Approval Writer Implementation

This note records the first bounded writer for SiteOps Browser Skill candidate
legacy-approval supersession.

The command:

```powershell
chaseos siteops candidates bound-approval-writer-implementation CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --actor USER_ID [--write-replacement-approval] --json
```

implements only the replacement approval request writer. It does not implement
the trusted artifact executor.

## Current Behavior

`candidate_promotion_bound_approval_writer_implementation(...)` reruns:

1. `bound-approval-writer-implementation-approval`
2. `bound-approval-writer-preflight`

inside the writer call before any write is attempted.

Without `--write-replacement-approval`, the command returns a dry-run writer
plan only. With `--write-replacement-approval`, it may write only when the
implementation approval and preflight are ready.

When ready and explicitly requested, it writes:

- pending replacement `ApprovalRequest`
- scoped `SiteOpsRun`
- scoped append-only `SiteOpsAuditEvent`
- idempotency marker
- recovery marker

The replacement approval remains `status: pending` and requires a separate
approval decision path before any future executor can consume it.

## Write Boundary

Allowed write lanes for this implementation:

- `07_LOGS/SiteOps-Approvals/<tenant>/<workspace>/<approval_id>.json`
- `07_LOGS/SiteOps-Runs/<tenant>/<workspace>/<run_id>.json`
- `07_LOGS/SiteOps-Audits/<tenant>/<workspace>/<run_id>.jsonl`
- `07_LOGS/SiteOps-Approvals/<tenant>/<workspace>/_idempotency/<approval_id>.json`
- `07_LOGS/SiteOps-Approvals/<tenant>/<workspace>/_recovery/<approval_id>.json`

Everything else remains denied.

## Security Boundary

This pass still denies:

- mutating or consuming the superseded legacy approval
- writing approval decisions
- writing trusted Browser Skill artifacts
- writing SiteOps Skill Card artifacts
- editing `runtime/policy/gateway_allowlists.json`
- adding `apply_trusted_candidate_artifacts`
- launching or controlling a browser
- enqueueing Agent Bus work
- calling provider APIs
- activating skills
- writing canonical ChaseOS memory/state

The writer uses create-new file semantics for the replacement approval and
markers. Existing targets, idempotency markers, or recovery markers block
through preflight before writing.

## Live Local Candidate Status

The live local candidate still does not receive a replacement approval because
its source approval is pending and legacy-unbound:

```text
approval_siteops_candidate_20260430_063855_candidate-browser-runtime-20260430-022607-example-com_browser_skill_candidate_promote
```

The live smoke with `--write-replacement-approval` returned blocked/no-write.

## Test Evidence

- Focused SiteOps candidate tests: `83 passed`
- CLI command/json contract tests: `8 passed`
- Browser Skill candidate + SiteOps adjacent regression: `136 passed`
- Generated CLI reference check: passed

## Next Required Pass

`siteops-candidate-replacement-approval-decision-consumption`: define and
implement the decision/consumption policy for new bound replacement approval
requests. That pass must still avoid trusted artifact writes unless a later
Gate-controlled trusted executor pass is separately approved.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[SiteOps-Candidate-Bound-Approval-Writer-Implementation-Approval]] - [[SiteOps-Candidate-Bound-Approval-Writer-Preflight]] - [[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
