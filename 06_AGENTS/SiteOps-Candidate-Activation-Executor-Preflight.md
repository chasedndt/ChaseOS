---
title: SiteOps Candidate Activation Executor Preflight
type: runtime-contract
status: COMPLETE TARGETED / NO-WRITE PREFLIGHT
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9
feature_family: SiteOps Browser Skill activation
---

# SiteOps Candidate Activation Executor Preflight

`siteops candidates activation-executor-preflight` is the strict no-write
preflight before any future guarded activation executor.

It composes the activation executor design and verifies:

- scoped source and activation approval IDs
- consumed activation marker evidence exists, parses, is scoped, and matches the candidate/source/activation approval tuple
- trusted Browser Skill and SiteOps Skill Card artifacts exist under trusted roots
- trusted artifacts remain `inactive_review` with `activation_allowed=false`
- no secret-like keys are present in marker or artifact payloads
- the future activation record path is scoped under `07_LOGS/SiteOps-Activations/<tenant>/<workspace>/`
- the future activation record is create-new-only and absent before any future write
- `--activate-trusted-artifact` remains a future flag and is unsupported in this pass

## Boundary

This pass does not:

- activate promoted skills
- set `activation_allowed=true`
- write activation records
- append activation audit events
- mutate trusted Browser Skill artifacts
- mutate SiteOps Skill Card artifacts
- launch or control a browser/CDP session
- enqueue Agent Bus work
- call provider APIs
- mutate Gate policy
- write canonical ChaseOS memory or state

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-executor-preflight CANDIDATE_ID `
  --source-approval-id SOURCE_APPROVAL_ID `
  --activation-approval-id ACTIVATION_APPROVAL_ID `
  --tenant TENANT --workspace WORKSPACE --user USER --actor ACTOR --json
```

## Status

The implementation is verified as a no-write preflight. SiteOps activation is
still not built. The next recommended pass is
`siteops-candidate-activation-executor-implementation-request`, which should
package this preflight evidence for operator review while still avoiding live
activation.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
