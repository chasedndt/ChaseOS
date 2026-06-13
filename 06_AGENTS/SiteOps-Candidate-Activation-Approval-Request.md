---
title: SiteOps Candidate Activation Approval Request
type: runtime-contract
status: BUILT / PENDING APPROVAL REQUEST PATH / NO ACTIVATION
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Request

`siteops candidates activation-approval-request` is the bounded approval-request
surface for future SiteOps Browser Skill candidate activation.

It sits after `activation-boundary-readiness` and before any future activation
consumer/executor. Its job is to turn a ready activation boundary into a
first-class SiteOps `ApprovalRequest`, not to activate anything.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-request <candidate_id> --approval-id <source_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

Preview mode is read-only.

Explicit write mode:

```powershell
python -m runtime.cli.main siteops candidates activation-approval-request <candidate_id> --approval-id <source_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --write-approval-request --json
```

When ready, write mode creates only:

- a pending SiteOps `ApprovalRequest`
- a scoped `SiteOpsRun`
- a scoped `SiteOpsAuditEvent`

## Required Preconditions

- tenant, workspace, and user scope must be present
- source candidate promotion approval must already be approved
- activation-boundary readiness must report `activation_boundary_ready_no_authority`
- inactive artifact validator and collision policy must be ready
- activation remains separated behind `siteops.browser_skill_candidate.activate_trusted_artifact`

## Forbidden Effects

The command does not:

- consume approvals
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- activate skills
- launch or control browsers
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Current Status

This is a scaffold for governed activation approval only. The activation
decision preflight, consumer design, consumer write guard, consumer writer
design, consumer writer implementation request, consumer writer implementation
approval, guarded marker-only consumer writer, and read-only live readiness
checker are now built. The writer is dry-run by default and can write only
scoped marker/run/audit evidence behind `--consume-activation-approval`; it
does not mutate the ApprovalRequest status or activate anything. The live local
candidate currently lacks a real approved source/activation approval pair, so
live consumption was not run. The activation executor, browser
execution/replay, Agent Bus integration, provider integration, and canonical
writeback remain future work.

Hermes remains bounded reviewer/shadow only. This contract does not make Hermes
the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
