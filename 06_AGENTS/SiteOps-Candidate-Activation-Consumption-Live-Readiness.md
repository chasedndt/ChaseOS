---
title: SiteOps Candidate Activation Consumption Live Readiness
type: runtime-contract
status: BUILT / READ-ONLY LIVE READINESS / ACTIVATION STILL NOT BUILT
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Consumption Live Readiness

`siteops candidates activation-consumption-live-readiness` is the read-only
readiness surface before the guarded marker-only activation approval consumer
writer is run with real approval IDs.

It is not an activation executor. It does not consume approvals. It checks
whether the live vault has a scoped approved source-promotion approval and a
matching scoped approved activation approval, then runs the marker-only writer
in dry-run mode when both IDs are available.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-consumption-live-readiness <candidate_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

Optional explicit ID validation:

```powershell
python -m runtime.cli.main siteops candidates activation-consumption-live-readiness <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## What It Checks

- candidate resolves under the supplied tenant/workspace/user scope
- source promotion approval exists, is scoped, and is approved
- activation approval exists, is scoped, is approved, and binds back to the
  selected source approval
- marker-only consumer writer dry-run is ready
- the explicit consume command preview can be generated for operator review

## Outputs

The readiness payload includes:

- selected `source_approval_id` and `activation_approval_id` when found
- source and activation approval candidate summaries
- readiness status and check list
- marker-only writer dry-run status or error
- explicit `--consume-activation-approval` command preview
- no-write/no-activation guard flags

## Forbidden Effects

The command does not:

- consume activation approvals
- write activation consumer markers
- append activation consumer audit events
- mutate `ApprovalRequest` status
- write trusted Browser Skill or SiteOps Skill Card artifacts
- mutate Gate policy
- activate skills
- launch or control browsers/CDP
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Live Result From This Pass

The live local example candidate
`candidate_browser_runtime_20260430_022607_example-com` returned
`blocked_missing_source_promotion_approval_id`. No approved source/activation
approval pair is currently discoverable for that candidate in the live vault.

This means the readiness surface is built and verified, but live activation
consumption remains blocked until real scoped approvals exist and an operator
explicitly runs the marker-only writer.

## Current Status

SiteOps candidate activation is still **PARTIAL**.

Built:

- activation approval request
- activation approval decision preflight
- activation consumer design/write guard/writer design
- activation consumer writer request/approval
- guarded marker-only consumer writer
- live readiness checker for real approval IDs
- activation executor design

Still future:

- activation executor preflight
- activation executor write guard
- activation executor implementation request/approval
- guarded activation executor implementation
- activation record/artifact state transition
- browser replay/execution from trusted skills
- Agent Bus/provider integration
- canonical writeback integration

Hermes remains bounded reviewer/shadow only. This readiness surface does not
make Hermes the SiteOps owner/runtime and does not grant Hermes activation
authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
