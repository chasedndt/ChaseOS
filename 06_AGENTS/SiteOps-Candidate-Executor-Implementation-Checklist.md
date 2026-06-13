---
title: SiteOps Candidate Executor Implementation Checklist
type: architecture
status: partial / no-write implementation checklist and CLI packet
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Implementation Checklist

This note defines the review checklist for a future
`apply_trusted_candidate_artifacts` implementation.

It does not implement the executor.

## Current Boundary

The current Browser Skill candidate promotion lane is still non-mutating:

1. redacted candidate inspection,
2. candidate preflight,
3. scoped approval request,
4. non-mutating apply contract,
5. denied-by-default Gate apply design,
6. fail-closed executor spec,
7. review-only Gate allowlist packet,
8. design-only trusted executor packet,
9. executor guard tests,
10. machine-readable executor implementation review checklist,
11. read-only preimplementation verifier.
12. review-only executor implementation design review.
13. no-write executor prewrite audit spec.
14. no-write inactive artifact validator.
15. no-write collision policy spec.
16. no-write approval rebind spec.

The executor entrypoint is absent, the future Gate operation is not
allowlisted, and trusted artifact targets are not written.

## Current Machine Surface

Command:

```powershell
chaseos siteops candidates executor-review-checklist CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_executor_review_checklist(...)
```

The command composes the design-only trusted executor packet and returns:

- `executor_review_status`,
- `required_review_gates`,
- `implementation_review_steps`,
- `replacement_test_requirements`,
- `blocked_actions`,
- no-write/no-execution flags.

With an approved, provenance-bound request and the Gate operation still
not allowlisted, the expected review status is:

```text
executor_review_status: executor_review_checklist_ready_no_write_authority
review_decision: do_not_implement_in_this_pass
operation_currently_allowlisted: false
writes_performed: false
executor_implemented: false
executor_enabled: false
```

Pending, rejected, unbound, invalid, or unconfined requests inherit the
earliest trusted-executor-design blocker.

## Required Preconditions Before Code Exists

A future executor implementation pass must not begin until the operator has
explicitly approved all of the following:

- implementation of `runtime.siteops.candidate_promotions.apply_trusted_candidate_artifacts`,
- exact write targets under `runtime/browser_skills/skills/` and
  `runtime/siteops/registry/skill_cards/`,
- Gate policy review for
  `siteops.browser_skill_candidate.apply_trusted_artifacts`,
- scoped SiteOps approval semantics for the candidate and proposed skill,
- inactive-artifact behavior after any successful write,
- rollback/audit behavior for partial writes.

Approval to implement the executor is not approval to allowlist it. Approval to
allowlist it is not approval to activate written skills. Those remain separate
decisions.

## Required Executor Order

The future executor must run in this order and fail closed before the first
write:

1. load tenant/workspace/user scope,
2. load the approval request by explicit `approval_id`,
3. verify approval status is `approved`,
4. verify approval provenance is bound to the same `candidate_id` and
   `proposed_skill_id`,
5. rerun candidate preflight from the current candidate file,
6. rerun secret/session exclusion checks,
7. compute target paths from validated candidate metadata only,
8. verify target paths are confined to governed trusted homes,
9. call ChaseOS Gate for
   `siteops.browser_skill_candidate.apply_trusted_artifacts`,
10. write a scoped prewrite audit event,
11. write trusted artifacts as inactive review artifacts,
12. validate written artifact shape,
13. write per-artifact result events,
14. write a scoped postwrite audit event,
15. return a structured result with activation still false.

## Required Tests Before Enablement

The implementation pass must add tests before it can be considered for Gate
allowlisting:

- missing approval blocks before Gate,
- pending approval blocks before Gate,
- rejected approval blocks before Gate,
- legacy-unbound approval blocks before Gate,
- candidate/proposed-skill approval mismatch blocks before Gate,
- stale or invalid candidate preflight blocks before write,
- secret/cookie/token/session-like content blocks before write,
- path traversal or malformed skill IDs block before write,
- Gate denial blocks before write,
- write collision behavior is explicit and audited,
- partial write leaves artifacts inactive and audit-visible,
- successful future write still leaves activation false,
- no browser execution, provider/API call, Agent Bus enqueue, or canonical
  writeback occurs.

## Required Audit Events

Future implementation must emit scoped SiteOps audit events for:

- `trusted_executor_preflight_started`,
- `trusted_executor_prewrite_validated`,
- `trusted_artifact_write_attempted`,
- `trusted_artifact_write_result`,
- `trusted_executor_postwrite_closed`,
- `trusted_executor_blocked`,
- `trusted_executor_rollback_required`.

Audit records must not include raw candidate content, cookies, tokens, browser
session state, profile paths, passwords, API key values, or personal account
state.

## Still Out Of Scope

The executor implementation checklist does not authorize:

- live browser or CDP control,
- authenticated browser session use,
- Browser Use / Browser Harness daemon control,
- provider or paid API calls,
- Agent Bus enqueue,
- automatic skill activation,
- canonical ChaseOS memory writeback,
- Gate policy mutation,
- unrestricted workflow replay.

The `executor-review-checklist` command also does not authorize direct trusted
Browser Skill writes, SiteOps Skill Card writes, browser execution, Agent Bus
enqueue, provider/API calls, activation, or canonical writeback.

The follow-on `[[SiteOps-Candidate-Executor-Preimplementation-Verifier]]`
command aggregates the checklist with live guards for Gate denial, executor
entrypoint absence, target artifact absence, guard-test presence, and CLI
contract presence. It is also read-only and does not authorize implementation.

The follow-on
`[[SiteOps-Candidate-Executor-Implementation-Design-Review]]` command composes
the verifier into a future patch-plan packet. It is also review-only and marks
every future patch-plan item as `allowed_in_this_pass=false`.

The follow-on `[[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]]` command
defines exact future audit event and inactive-artifact contracts without
writing audit events or trusted artifacts.

The follow-on `[[SiteOps-Candidate-Inactive-Artifact-Validator]]` command
validates proposed inactive Browser Skill and SiteOps Skill Card payloads in
memory only.

The follow-on `[[SiteOps-Candidate-Executor-Collision-Policy-Spec]]` command defines
fail-closed target collision, overwrite, idempotency, and rollback policy
without writing artifacts.

The follow-on `[[SiteOps-Candidate-Executor-Approval-Rebind-Spec]]` command
defines the future replacement approval requirements for legacy-unbound
approval artifacts without mutating legacy approvals.

The follow-on `[[SiteOps-Candidate-Executor-Bound-Approval-Request-Spec]]`
command defines and validates the future replacement approval request artifact
shape in memory only. It does not write the replacement request, mutate legacy
approval records, decide approvals, write audit events, or authorize executor
implementation.

The follow-on `[[SiteOps-Candidate-Executor-Bound-Approval-Writer-Design]]`
command defines the future replacement approval writer path, audit event,
idempotency, and rollback contract without writing approval artifacts.

## Current Verdict

The current step is review-only but now machine-readable. ChaseOS can inspect
future executor gates and replacement tests through CLI/runtime output, but
must keep the executor absent and Gate-denied until a separate operator
approval explicitly allows implementation.

## Validation - 2026-04-30

Codex validated the checklist and preimplementation verifier as no-write
surfaces:

- candidate promotion focused tests passed with checklist/verifier coverage,
- adjacent SiteOps / Browser Skill / CLI contract tests passed,
- generated CLI reference was current,
- live `executor-review-checklist` returned
  `executor_review_status=blocked_pending_approval` for the existing pending
  legacy-unbound approval,
- live `preimplementation-verifier` returned
  `verifier_verdict=blocked_checklist_not_ready: blocked_pending_approval`,
- trusted Browser Skill and SiteOps Skill Card target files remained absent,
- the Gate allowlist remained unchanged,
- `apply_trusted_candidate_artifacts` remained absent.

No executor implementation, Gate allowlist mutation, trusted artifact write,
browser execution, Agent Bus enqueue, provider call, activation, or canonical
writeback was added.

## Verifier Hardening - 2026-04-30

Follow-on verifier hardening added negative tests for the final no-write
inspection layer:

- a pre-existing trusted artifact target blocks readiness,
- an unexpected executor entrypoint blocks readiness,
- a missing CLI contract marker blocks readiness.

This hardening keeps the checklist and verifier as review-only surfaces. It
does not implement or enable the executor.

## Implementation Design Review - 2026-04-30

Codex added a review-only `executor-implementation-design-review` surface after
the verifier. It names the future files, order, stop conditions, and tests a
future executor implementation would need, but performs no executor
implementation, Gate allowlist mutation, trusted artifact write, browser
execution, Agent Bus enqueue, provider call, activation, or canonical
writeback.

## Prewrite Audit Spec - 2026-04-30

Codex added a no-write `executor-prewrite-audit-spec` surface. It defines the
future executor audit event sequence, inactive Browser Skill and SiteOps Skill
Card contracts, validation checks, and forbidden metadata fields. It performs
no audit write, executor implementation, Gate allowlist mutation, trusted
artifact write, browser execution, Agent Bus enqueue, provider call,
activation, or canonical writeback.

## Inactive Artifact Validator - 2026-04-30

Codex added a no-write `inactive-artifact-validator` surface. It builds the
future inactive Browser Skill and SiteOps Skill Card payload shapes in memory
and validates required fields, `inactive_review` status, `activation_allowed:
false`, and forbidden secret/session fields. It performs no trusted artifact
write, audit write, executor implementation, Gate mutation, browser execution,
Agent Bus enqueue, provider call, activation, or canonical writeback.

## Collision Policy Spec - 2026-04-30

Codex added a no-write `collision-policy-spec` surface. It composes the
inactive artifact validator and target path inspection to define fail-closed
collision, overwrite, idempotency, and rollback policy for future inactive
trusted artifact writes. Existing trusted targets block by default. It performs
no overwrite, idempotent apply marker, trusted artifact write, audit write,
executor implementation, Gate mutation, browser execution, Agent Bus enqueue,
provider call, activation, or canonical writeback.

## Approval Rebind Spec - 2026-04-30

Codex validated the existing no-write `approval-rebind-spec` surface and added
the missing architecture documentation. The command reports whether an approval
is already `bound_match`, requires a future replacement approval because it is
`legacy_unbound`, or is blocked because it binds to a mismatched candidate or
skill. It performs no legacy approval mutation, replacement approval write,
approval decision, audit write, executor implementation, Gate mutation,
trusted artifact write, browser execution, Agent Bus enqueue, provider call,
activation, or canonical writeback.

## Bound Approval Request Spec - 2026-05-01

Codex validated and wired the no-write `bound-approval-request-spec` command
surface. It composes `approval-rebind-spec`, builds a proposed replacement
approval request artifact in memory, validates candidate/skill/scope/action
binding, and keeps all write/execution authority false. It performs no bound
approval request write, legacy approval mutation, approval decision, audit
write, executor implementation, Gate mutation, trusted artifact write, browser
execution, Agent Bus enqueue, provider call, activation, or canonical
writeback.

## Bound Approval Writer Design - 2026-05-01

Codex added the no-write `bound-approval-writer-design` surface. It composes
the bound approval request spec, previews the future scoped approval artifact
path, validates target confinement/collision status, and defines writer steps,
audit event metadata, idempotency policy, and rollback policy. A same-second
approval ID collision bug in the replacement preview was fixed by giving
replacement previews a distinct run-id namespace. The pass performs no bound
approval request write, audit event write, idempotency marker write, legacy
approval mutation, approval decision, executor implementation, Gate mutation,
trusted artifact write, browser execution, Agent Bus enqueue, provider call,
activation, or canonical writeback.

## Bound Approval Writer Preflight - 2026-05-01

Codex added the no-write `bound-approval-writer-preflight` surface. It composes
the writer design and validates a specific future writer invocation for design
readiness, scoped target absence, pending replacement artifact shape, scope
binding, secret-like field exclusion, audit contract exclusions,
idempotency/recovery marker absence, and trusted apply Gate posture. The live
local candidate remains blocked because the source approval is pending and
legacy-unbound. The pass performs no replacement approval request write,
preflight marker write, idempotency marker write, recovery marker write, audit
event write, legacy approval mutation, approval decision, executor
implementation, Gate mutation, trusted artifact write, browser execution,
Agent Bus enqueue, provider call, activation, or canonical writeback.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Preimplementation-Verifier]] - [[SiteOps-Candidate-Executor-Implementation-Design-Review]] - [[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]] - [[SiteOps-Candidate-Inactive-Artifact-Validator]] - [[SiteOps-Candidate-Executor-Collision-Policy-Spec]] - [[SiteOps-Candidate-Executor-Approval-Rebind-Spec]] - [[SiteOps-Candidate-Executor-Bound-Approval-Request-Spec]] - [[SiteOps-Candidate-Executor-Bound-Approval-Writer-Design]] - [[SiteOps-Candidate-Bound-Approval-Writer-Preflight]] - [[SiteOps-Candidate-Executor-Guard-Tests]] - [[SiteOps-Candidate-Trusted-Executor-Design]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[SiteOps-Candidate-Gate-Executor-Spec]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Skill-Memory]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
