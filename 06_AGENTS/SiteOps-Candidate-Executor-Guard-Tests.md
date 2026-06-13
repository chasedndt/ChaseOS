---
title: SiteOps Candidate Executor Guard Tests
type: architecture
status: verified targeted / guard tests only
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Guard Tests

This note records the regression boundary around the future Browser Skill
candidate trusted artifact executor.

It does not implement the executor.

## Purpose

The guard tests make the current fail-closed state executable:

- the future executor entrypoint remains absent,
- `siteops.browser_skill_candidate.apply_trusted_artifacts` remains denied by
  Gate,
- pending approvals still block trusted-executor design even when provenance is
  bound,
- legacy/unbound approvals still block trusted-executor design before any write
  consideration,
- future write-plan steps remain `implemented: false`,
- future write-plan artifact writes remain `write_allowed: false`,
- design-only executor components, audit sequence, and rollback plan remain
  unimplemented,
- trusted Browser Skill and SiteOps Skill Card targets remain absent.

## Test Surface

File:

```text
runtime/siteops/tests/test_candidate_promotions.py
```

New guard tests:

- `test_candidate_executor_guard_entrypoint_remains_absent`
- `test_candidate_executor_guard_gate_operation_remains_denied_by_default`
- `test_candidate_executor_guard_design_never_marks_future_steps_implemented`
- `test_candidate_trusted_executor_design_blocks_pending_approval`
- `test_candidate_trusted_executor_design_blocks_legacy_unbound_approval`

## Verified Boundary

The guard tests cover the current design path only:

```text
candidate -> approval request -> apply contract -> Gate apply design ->
executor spec -> allowlist review -> trusted executor design
```

They do not grant approval, edit Gate policy, create trusted artifacts, launch a
browser, enqueue Agent Bus work, call providers, activate skills, or mutate
canonical ChaseOS state.

## Future Implication

Any later pass that implements `apply_trusted_candidate_artifacts` or allowlists
`siteops.browser_skill_candidate.apply_trusted_artifacts` must first satisfy
the review checklist in
`[[SiteOps-Candidate-Executor-Implementation-Checklist]]` and intentionally
replace these guard expectations with executor tests that prove:

- approval is approved and provenance-bound,
- candidate validation reruns immediately before write,
- secret/session exclusion reruns immediately before write,
- target paths remain confined,
- Gate operation is explicitly allowlisted,
- prewrite and postwrite audit events are emitted,
- successful writes remain inactive until a separate activation path approves
  reuse.

## Current Verdict

The trusted artifact executor remains NOT BUILT and disabled. The new tests
turn that boundary into regression coverage.

Continuation validation also confirmed the live CLI path returns the structured
fail-closed design payload for pending/legacy-unbound approval state. A
concurrent function-order drift that caused `trusted-executor-design` to fall
through to `None` was repaired without adding executor authority.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[SiteOps-Candidate-Trusted-Executor-Design]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[SiteOps-Candidate-Gate-Executor-Spec]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Skill-Memory]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
