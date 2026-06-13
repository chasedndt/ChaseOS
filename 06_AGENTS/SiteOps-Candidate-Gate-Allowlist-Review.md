---
title: SiteOps Candidate Gate Allowlist Review
type: architecture
status: partial / review-only fail-closed
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Gate Allowlist Review

This note defines the review-only Gate allowlist surface for Browser Skill
candidate promotion.

It does not edit Gate policy.

## Current Surface

Command:

```powershell
chaseos siteops candidates gate-allowlist-review CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_gate_allowlist_review(...)
```

The command composes:

1. redacted candidate inspection,
2. scoped approval request lookup,
3. approval provenance binding inspection,
4. non-mutating apply contract,
5. denied-by-default Gate apply design,
6. fail-closed executor spec,
7. allowlist eligibility/risk review.

## Gate Operation

The future trusted artifact operation remains:

```text
siteops.browser_skill_candidate.apply_trusted_artifacts
```

That operation is still intentionally not allowlisted in
`runtime/policy/gateway_allowlists.json`.

## Current Result

With an approved and provenance-bound request, the current expected status is:

```text
allowlist_review_status: blocked_executor_not_implemented
operation_currently_allowlisted: false
allowlist_change_allowed: false
allowlist_change_performed: false
policy_file_write_allowed: false
writes_performed: false
executor_enabled: false
trusted_skill_write_allowed: false
siteops_skill_card_write_allowed: false
```

If the approval is pending or unbound, the review inherits the earlier
fail-closed blocker before considering allowlist eligibility.

## Review Checks

The command returns `allowlist_review_checks`:

- `executor_spec_available`
- `candidate_preflight_ready`
- `apply_contract_ready`
- `approval_provenance_bound_match`
- `target_paths_confined`
- `executor_implemented`
- `operation_currently_allowlisted`
- `allowlist_policy_write_disabled`

`operation_currently_allowlisted` is informational. The desired current state is
false because the executor is not built.

## Minimum Future Conditions

A later allowlist pass may only be considered after:

- an approved and provenance-bound SiteOps ApprovalRequest exists,
- candidate validation and secret/session exclusion rerun immediately before
  write,
- the trusted artifact executor exists and has focused tests,
- target path confinement is enforced by the executor,
- scoped prewrite and postwrite audit events are emitted,
- rollback and partial-write behavior is defined,
- trusted artifacts remain inactive until a separate activation path exists.

## Denied

- No edit to `runtime/policy/gateway_allowlists.json`.
- No trusted Browser Skill write.
- No SiteOps Skill Card write.
- No browser execution.
- No Agent Bus task enqueue.
- No provider/API call.
- No activation marker.
- No canonical ChaseOS writeback.

## Current Verdict

`gate-allowlist-review` is a policy-review packet, not a policy mutation path.
It makes the allowlist decision inspectable while preserving deny-by-default
behavior.

The trusted artifact executor remains NOT BUILT.

The follow-on design-only executor packet is documented in
`[[SiteOps-Candidate-Trusted-Executor-Design]]`. It defines the future executor
components, audit sequence, rollback plan, and failure modes without
implementing the executor.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Gate-Executor-Spec]] - [[SiteOps-Candidate-Gate-Apply-Design]] - [[SiteOps-Candidate-Trusted-Executor-Design]] - [[SiteOps-Candidate-Apply-Executor-Preflight]] - [[Browser-Skill-Memory]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
