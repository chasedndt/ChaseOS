---
title: SiteOps Candidate Activation Executor Design
type: runtime-contract
status: BUILT / DESIGN ONLY / ACTIVATION STILL NOT BUILT
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Executor Design

`siteops candidates activation-executor-design` is the no-mutation design
surface for the future SiteOps Browser Skill activation executor.

It sits after marker-only activation approval consumption. It checks whether
there is consumed marker evidence plus inactive trusted Browser Skill and
SiteOps Skill Card artifacts, then previews the future state transition. It
does not activate anything.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-executor-design <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## What It Checks

- candidate resolves under supplied tenant/workspace/user scope
- activation-consumption marker exists under
  `07_LOGS/SiteOps-Activation-Consumers/<tenant>/<workspace>/`
- marker matches candidate, proposed skill, source approval, and activation
  approval
- trusted Browser Skill artifact exists under `runtime/browser_skills/skills/`
- SiteOps Skill Card exists under `runtime/siteops/registry/skill_cards/`
- both trusted artifacts are `inactive_review`
- both trusted artifacts have `activation_allowed: false`
- future activation record path is scoped under
  `07_LOGS/SiteOps-Activations/<tenant>/<workspace>/`

## Future State Transition Preview

The future executor is expected to require an explicit
`--activate-trusted-artifact` flag. The previewed state transition is:

- Browser Skill: `inactive_review` -> `active_approved`
- SiteOps Skill Card: `inactive_review` -> `active_approved`
- `activation_allowed`: `false` -> `true`
- activation record: create-new-only under scoped activation logs

Activation alone still does not launch a browser, enqueue Agent Bus work, call
providers, or write canonical ChaseOS memory/state.

## Forbidden Effects

The command does not:

- activate promoted skills
- set `activation_allowed=true`
- write activation records
- mutate trusted Browser Skill artifacts
- mutate SiteOps Skill Card artifacts
- append activation audit events
- launch or control browsers/CDP
- enqueue Agent Bus work
- call providers
- mutate Gate policy
- write canonical ChaseOS memory/state

## Live Result From This Pass

The live local example candidate
`candidate_browser_runtime_20260430_022607_example-com` was smoke-tested with
missing approval IDs and correctly returned
`blocked_activation_consumption_marker_missing`.

No activation marker, activation record, trusted artifact mutation, browser
action, Agent Bus task, provider call, Gate mutation, or canonical writeback was
performed.

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
- browser replay/execution from trusted skills
- Agent Bus/provider integration
- canonical writeback integration

Hermes remains bounded reviewer/shadow only. This design does not make Hermes
the SiteOps owner/runtime and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
