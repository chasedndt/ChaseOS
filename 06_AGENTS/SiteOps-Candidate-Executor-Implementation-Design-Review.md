---
title: SiteOps Candidate Executor Implementation Design Review
type: architecture
status: partial / review-only patch plan
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Implementation Design Review

This note documents the review-only design packet for a future
`apply_trusted_candidate_artifacts` implementation.

It does not implement the executor.

## Current Surface

Command:

```powershell
chaseos siteops candidates executor-implementation-design-review CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_executor_implementation_design_review(...)
```

The command composes `preimplementation-verifier` and returns a structured
future patch plan only.

The follow-on `[[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]]` command
uses this design review as its upstream guard and defines no-write audit event
and inactive-artifact contracts for the same future executor.

## Output Contract

When the upstream verifier is ready, the command returns:

```text
implementation_design_status: implementation_design_review_ready_no_authority
review_decision: patch_plan_only_do_not_implement_in_this_pass
executor_implemented: false
executor_enabled: false
writes_performed: false
```

If the verifier is blocked, this command stays blocked with:

```text
implementation_design_status: blocked_preimplementation_verifier: <verdict>
review_decision: blocked_before_patch_plan
```

## Patch Plan Shape

The review packet names the future files and order that would need separate
approval:

- `runtime/siteops/candidate_promotions.py` for a future executor symbol,
- `runtime/siteops/tests/test_candidate_promotions.py` for fail-closed executor
  tests,
- `runtime/cli/main.py` and `runtime/cli/siteops_commands.py` for a future CLI
  apply surface,
- `runtime/policy/gateway_allowlists.json` for a separate Gate policy review.

Every patch-plan item is marked `allowed_in_this_pass: false`.

## Denied Effects

The design-review packet performs no:

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

This command is the first implementation-shape review after the
preimplementation verifier. It makes the next patch easier to review without
granting any implementation, Gate, write, browser, provider, activation, or
canonical writeback authority.

It is now followed by the no-write prewrite audit spec, which still does not
implement or enable the executor.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]] - [[SiteOps-Candidate-Executor-Preimplementation-Verifier]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[SiteOps-Candidate-Trusted-Executor-Design]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
