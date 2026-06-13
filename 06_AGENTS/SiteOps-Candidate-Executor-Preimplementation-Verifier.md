---
title: SiteOps Candidate Executor Preimplementation Verifier
type: architecture
status: partial / read-only verifier
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Preimplementation Verifier

This note documents the read-only verifier that aggregates all current guards
before any Browser Skill candidate trusted artifact executor patch is proposed.

It does not implement the executor.

The follow-on
`[[SiteOps-Candidate-Executor-Implementation-Design-Review]]` command now
composes this verifier into a review-only future patch-plan packet. That
follow-on command also does not implement the executor.

## Current Surface

Command:

```powershell
chaseos siteops candidates preimplementation-verifier CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_preimplementation_verifier(...)
```

The verifier composes `executor-review-checklist` and adds live guard checks.

## Verifier Checks

The verifier currently checks:

- Gate operation remains denied for
  `siteops.browser_skill_candidate.apply_trusted_artifacts`,
- `apply_trusted_candidate_artifacts` remains absent from
  `runtime.siteops.candidate_promotions`,
- future trusted Browser Skill and SiteOps Skill Card target files are absent,
- executor guard tests are present,
- CLI contract surface for `executor-review-checklist` exists.

When the upstream checklist is ready and all live guards pass, the verifier may
return:

```text
verifier_verdict: ready_for_patch_proposal
verifier_pass: true
```

This means only that a future executor patch may be proposed for review. It is
not approval to implement, merge, allowlist, write artifacts, activate skills,
or run a browser.

## Blocked States

The verifier remains blocked when:

- approval is pending, rejected, missing, unbound, or mismatched,
- candidate validation is not ready,
- Gate is already allowlisted unexpectedly,
- the executor entrypoint already exists unexpectedly,
- trusted target artifacts already exist unexpectedly,
- guard tests or CLI contract markers are missing.

## Hardening - 2026-04-30

Codex added focused negative tests for the verifier:

- pre-existing trusted artifact targets keep the verifier blocked,
- an unexpected `apply_trusted_candidate_artifacts` entrypoint keeps the
  verifier blocked,
- a missing CLI contract marker keeps the verifier blocked.

The tests use temp fixtures and monkeypatched module state only. They do not
write real trusted artifacts, implement the executor, edit Gate policy, launch
a browser, enqueue Agent Bus work, call providers, activate skills, or write
canonical state.

## Denied Effects

The verifier performs no:

- executor implementation,
- Gate allowlist mutation,
- trusted Browser Skill write,
- SiteOps Skill Card write,
- browser/CDP/Browser Use/Browser Harness execution,
- authenticated session handling,
- Agent Bus enqueue,
- provider/API call,
- skill activation,
- canonical ChaseOS writeback.

## Current Verdict

`preimplementation-verifier` is the terminal no-write inspection pass before a
future executor patch proposal. It keeps the lane in Phase 9 runtime/operator
infrastructure and does not move trusted promotion or Site Skills UI into
Phase 10.

The implementation design-review command may be run after this verifier to
shape a future patch proposal, but it keeps all executor, Gate, trusted write,
browser, provider, Agent Bus, activation, and canonical writeback authority
disabled.

## Validation - 2026-04-30

Codex validated the verifier against the current live local candidate approval:

- upstream `executor-review-checklist` stayed blocked because the approval is
  pending and legacy-unbound,
- Gate denial, executor-entrypoint absence, target artifact absence, guard-test
  presence, and CLI contract presence all passed as live guards,
- the final verifier verdict remained blocked until the approval/checklist
  layer becomes ready,
- no executor implementation, Gate allowlist mutation, trusted artifact write,
  browser execution, Agent Bus enqueue, provider call, activation, or canonical
  writeback occurred.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[SiteOps-Candidate-Executor-Implementation-Design-Review]] - [[SiteOps-Candidate-Executor-Guard-Tests]] - [[SiteOps-Candidate-Trusted-Executor-Design]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[SiteOps-Candidate-Gate-Executor-Spec]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Skill-Memory]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
