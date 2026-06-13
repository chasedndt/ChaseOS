---
title: SiteOps Candidate Activation Executor Implementation
type: runtime-contract
status: COMPLETE TARGETED / GUARDED LOCAL ACTIVATION WRITER
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9
feature_family: SiteOps Browser Skill activation
---

# SiteOps Candidate Activation Executor Implementation

`siteops candidates activation-executor-implementation` is the guarded local
activation executor for reviewed Browser Skill candidate artifacts.

The command is dry-run by default. It can activate only when all of these are
true:

- source promotion ApprovalRequest is approved
- activation ApprovalRequest is approved
- activation-consumption marker exists and matches tenant/workspace/user,
  candidate, source approval, and activation approval
- trusted Browser Skill artifact exists under the trusted skill root
- SiteOps Skill Card artifact exists under the skill-card registry root
- both trusted artifacts are `inactive_review`
- both trusted artifacts have `activation_allowed: false`
- no secret-like keys are present in marker or artifacts
- activation record path is scoped and absent
- ChaseOS Gate allows `siteops.browser_skill_candidate.activate_trusted_artifact`
- caller supplies `--activate-trusted-artifact`

When all checks pass and the explicit flag is present, the executor writes only:

- scoped `SiteOpsRun` evidence
- scoped append-only activation audit events
- one create-new activation record under `07_LOGS/SiteOps-Activations/<tenant>/<workspace>/`
- activation-field updates to the reviewed trusted Browser Skill artifact
- activation-field updates to the reviewed SiteOps Skill Card artifact

## Boundary

This pass does not:

- mutate source or activation ApprovalRequest status
- consume approvals
- mutate Gate policy
- launch or control a browser/CDP session
- enqueue Agent Bus work
- call provider APIs
- publish, share, buy, trade, connect accounts, or mutate external services
- write canonical ChaseOS memory/state
- invoke Hermes/OpenClaw or broaden runtime authority

Activation is local artifact activation only. Runtime execution from the trusted
skill remains future governed work.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-executor-implementation CANDIDATE_ID `
  --source-approval-id SOURCE_APPROVAL_ID `
  --activation-approval-id ACTIVATION_APPROVAL_ID `
  --tenant TENANT --workspace WORKSPACE --user USER --actor ACTOR `
  --activate-trusted-artifact --json
```

Omitting `--activate-trusted-artifact` returns
`activation_executor_ready_dry_run_no_write` when all non-write checks pass.

## Verification

Verified in this pass:

- Python compile passed.
- Focused activation executor tests passed.
- Full SiteOps candidate suite passed: `186 passed`.
- CLI command/JSON contract suite passed: `10 passed`.
- Generated CLI docs check passed.
- Live fake-candidate smoke failed closed with structured candidate-not-found
  JSON.
- Gate file hashes stayed unchanged.

## Status

The guarded activation executor is built and tested against temp-vault mocked
Gate approval. The real vault did not activate anything in this pass. Live
activation remains blocked until a real scoped candidate, approved approval
chain, consumed marker evidence, inactive trusted artifacts, and operator
reviewed Gate allowance are present.

The next recommended pass is
`siteops-candidate-activation-executor-live-readiness`.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
