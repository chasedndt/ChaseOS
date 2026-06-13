---
title: SiteOps Candidate Activation Approval Decision Consumer Writer Implementation
type: runtime-contract
status: BUILT / GUARDED MARKER-ONLY WRITER / NO ACTIVATION
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Decision Consumer Writer Implementation

`siteops candidates activation-approval-decision-consumer-writer-implementation`
is the guarded writer for consuming an approved SiteOps Browser Skill candidate
activation approval.

It is dry-run by default. It writes only when `--consume-activation-approval`
is supplied and the activation approval request, decision preflight, consumer
design, write guard, writer design, implementation request, and implementation
approval chain still pass.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-writer-implementation <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

Explicit marker/audit write mode:

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-writer-implementation <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --consume-activation-approval --json
```

## Allowed Write Set

When ready and explicitly requested, the writer may create:

- one exact-once activation-consumption marker under
  `07_LOGS/SiteOps-Activation-Consumers/<tenant_id>/<workspace_id>/`
- one scoped SiteOps run record under
  `07_LOGS/SiteOps-Runs/<tenant_id>/<workspace_id>/`
- append-only SiteOps audit events under
  `07_LOGS/SiteOps-Audits/<tenant_id>/<workspace_id>/`

The marker is create-new only. If it already exists, the writer fails closed.

## Forbidden Effects

The writer does not:

- mutate the `ApprovalRequest` status
- decide approvals
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- activate skills
- mutate Gate policy
- launch or control browsers
- enqueue Agent Bus work
- call providers
- expose secrets, cookies, tokens, or browser session state
- write canonical ChaseOS memory/state

## Current Status

This is BUILT / GUARDED MARKER-ONLY WRITER / NO ACTIVATION.

The activation executor, browser replay/execution, Agent Bus/provider
integration, trusted skill activation, and canonical writeback remain future
work.

Hermes remains bounded reviewer/shadow only. This writer does not make Hermes
the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
