---
title: SiteOps Candidate Activation Executor Implementation Approval
type: runtime-contract
status: COMPLETE TARGETED / NO-WRITE IMPLEMENTATION APPROVAL
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9
feature_family: SiteOps Browser Skill activation
---

# SiteOps Candidate Activation Executor Implementation Approval

`siteops candidates activation-executor-implementation-approval` returns a
no-write approve/reject packet for a future guarded activation executor
implementation pass.

It composes the activation executor implementation request and records only:

- the operator decision: `approve` or `reject`
- the actor and reason
- the candidate and proposed skill IDs
- source and activation approval IDs
- the implementation request ID
- the future `--activate-trusted-artifact` flag
- the future activation write set
- record-schema and no-secret/no-session-state boundaries

## Boundary

This pass does not:

- write an implementation approval artifact
- write or mutate an approval decision
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
python -m runtime.cli.main siteops candidates activation-executor-implementation-approval CANDIDATE_ID `
  --source-approval-id SOURCE_APPROVAL_ID `
  --activation-approval-id ACTIVATION_APPROVAL_ID `
  --decision approve `
  --tenant TENANT --workspace WORKSPACE --user USER --actor ACTOR --json
```

## Status

The implementation approval packet is verified as no-write. SiteOps activation
is still not built. The next recommended pass is
`siteops-candidate-activation-executor-implementation`, which may introduce the
guarded activation executor but must still use an explicit activation flag and
stop before browser/CDP execution, Agent Bus/provider calls, Gate mutation, and
canonical writeback.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
