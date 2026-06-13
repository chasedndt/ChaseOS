---
title: SiteOps Candidate Activation Executor Implementation Request
type: runtime-contract
status: COMPLETE TARGETED / NO-WRITE IMPLEMENTATION REQUEST
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9
feature_family: SiteOps Browser Skill activation
---

# SiteOps Candidate Activation Executor Implementation Request

`siteops candidates activation-executor-implementation-request` packages the
activation executor preflight evidence for operator review without writing an
approval artifact or implementing activation.

The request packet includes:

- activation executor preflight status and checks
- consumed activation marker evidence posture
- inactive trusted Browser Skill and SiteOps Skill Card posture
- future create-new activation record path
- future explicit `--activate-trusted-artifact` flag
- future trusted artifact state transition preview
- record schema and forbidden secret/session-state fields
- required operator decision for the next approval pass

## Boundary

This pass does not:

- write an implementation request artifact
- implement the activation executor
- accept or execute `--activate-trusted-artifact`
- activate promoted skills
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
python -m runtime.cli.main siteops candidates activation-executor-implementation-request CANDIDATE_ID `
  --source-approval-id SOURCE_APPROVAL_ID `
  --activation-approval-id ACTIVATION_APPROVAL_ID `
  --tenant TENANT --workspace WORKSPACE --user USER --actor ACTOR --json
```

## Status

The implementation request is verified as a no-write packet. SiteOps activation
is still not built. The next recommended pass is
`siteops-candidate-activation-executor-implementation-approval`.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
