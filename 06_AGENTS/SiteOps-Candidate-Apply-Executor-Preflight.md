---
title: SiteOps Candidate Apply Executor Preflight
type: architecture
status: partial / disabled preflight only
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Apply Executor Preflight

This note defines the disabled future-executor preflight for Browser Skill
candidate promotion. The canonical architecture note is
`[[SiteOps-Candidate-Gate-Executor-Spec]]`; this note records why the next pass
maps to the existing `gate-executor-spec` command rather than adding a duplicate
command.

It does not implement the executor.

## Current Surface

Command:

```powershell
chaseos siteops candidates gate-executor-spec CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_gate_executor_spec(...)
```

The command composes candidate promotion preflight, scoped approval inspection,
approval provenance binding inspection, the non-mutating apply contract,
denied-by-default Gate apply design, and a future write-plan preview. The
approval queue view can also include this disabled preflight per listed approval; operator-facing aggregation routes through [[ChaseOS-Approval-Center]]
without requiring the operator to know each approval ID first:

```powershell
chaseos siteops candidates approvals --tenant TENANT_ID --workspace WORKSPACE_ID --include-executor-preflight --json
```

The same queue view can optionally include activation-boundary readiness for each
listed approval, preserving a single queue/provenance inspection workflow before
operators drill into a specific candidate:

```powershell
chaseos siteops candidates approvals --tenant TENANT_ID --workspace WORKSPACE_ID --include-activation-boundary --json
```

Operators can also project the no-write bound replacement approval-request spec
for each listed approval. This is especially useful for legacy-unbound approvals:
it shows whether a separate future writer could create a new bound approval
request, while preserving the historical approval artifact unchanged.

```powershell
chaseos siteops candidates approvals --tenant TENANT_ID --workspace WORKSPACE_ID --include-bound-approval-request-spec --json
```

Operators can add a read-only summary layer to aggregate the queue posture without
changing approval state or crossing the activation boundary:

```powershell
chaseos siteops candidates approvals --tenant TENANT_ID --workspace WORKSPACE_ID --include-executor-preflight --include-activation-boundary --include-bound-approval-request-spec --include-readiness-summary --json
```

The summary reports approval/provenance/apply-contract counts, plus executor,
activation-boundary, and bound-approval-request-spec counts when those optional
projections are included.

A separate activation-boundary readiness surface now inspects the post-write
activation boundary without writing trusted artifacts or activating skills:

```powershell
chaseos siteops candidates activation-boundary-readiness CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

This surface composes the already disabled/non-mutating preflight layers
(inactive artifact validation, collision policy, prewrite audit spec,
implementation design review, preimplementation verifier, checklist, and apply
contract) into one explicit readiness packet. It reports whether a future apply
executor would still be blocked before any activation boundary could be crossed.

## Machine Preflight Checks

The command returns `executor_preflight_checks` with:

- `candidate_preflight_ready`
- `apply_contract_ready`
- `approval_provenance_bound_match`
- `target_paths_confined`
- `gate_operation_allowlisted`
- `executor_implemented`
- `writes_disabled`

Current expected posture:

```text
executor_spec_status: blocked_gate_operation_not_allowlisted
executor_preflight_status: blocked_gate_operation_not_allowlisted
gate_operation_allowed: false
executor_implemented: false
executor_enabled: false
writes_performed: false
```

For legacy unbound approvals, the preflight blocks earlier with:

```text
executor_spec_status: blocked_approval_provenance_not_bound
```

## Activation Boundary Readiness Checks

The `activation-boundary-readiness` command returns:

- `activation_boundary_status`
- `review_decision`
- `activation_boundary_checks`
- `activation_boundary_inputs`
- authority booleans proving `writes_performed`, `activation_allowed`,
  `activation_performed`, `trusted_skill_write_allowed`,
  `siteops_skill_card_write_allowed`, `browser_execution_allowed`, and
  `canonical_writeback_allowed` are all false.

Current expected live posture for pending/legacy approval material is blocked
before activation, for example:

```text
activation_boundary_status: blocked_collision_policy: blocked_inactive_artifact_validator: blocked_implementation_design_review: blocked_checklist_not_ready: blocked_pending_approval
review_decision: blocked_before_activation_boundary
writes_performed: false
activation_allowed: false
activation_performed: false
```

This command is an inspection/readiness projection only. It does not make an
approval decision, does not run an apply executor, and does not create or enable
an activation path.

## Denied

- No trusted Browser Skill write.
- No SiteOps Skill Card write.
- No browser execution.
- No Agent Bus enqueue.
- No provider API call.
- No skill activation.
- No canonical ChaseOS writeback.
- No Gate allowlist change.

## Future Executor Requirements

A later executor pass must be separate and must prove:

- the candidate still validates immediately before write,
- the approval is approved, scoped, and provenance-bound,
- target paths remain confined,
- secret/cookie/token/session exclusion reruns immediately before write,
- the Gate operation is explicitly allowlisted,
- prewrite and postwrite SiteOps audit events are emitted,
- trusted artifacts remain inactive until a separate activation path exists.

## 2026-04-30 Continuation Validation

Codex revalidated this pass as a continuation after the fail-closed
`gate-executor-spec` surface already existed. The correct next-pass mapping is
to validate and use `gate-executor-spec` as the disabled apply-executor preflight
surface, not to add another command.

Validation confirmed:

- focused candidate/SiteOps/CLI tests pass,
- generated CLI docs are current,
- Gate still denies `siteops.browser_skill_candidate.apply_trusted_artifacts`,
- a live `gate-executor-spec` smoke reports the existing pending approval as
  blocked,
- `executor_implemented` and `executor_enabled` remain false,
- future trusted Browser Skill and SiteOps Skill Card target files remain
  absent.

Follow-on note: `[[SiteOps-Candidate-Gate-Allowlist-Review]]` now records the
separate review-only allowlist surface. It reports allowlist eligibility and
risks without editing Gate policy or enabling the executor.

## Current Verdict

This is a Phase 9 safety preflight. It makes the future executor requirements
machine-readable while keeping promotion authority blocked.

## Graph Links

[[SiteOps-Candidate-Gate-Apply-Design]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Skill-Memory]] - [[Agent-Control-Plane]] - [[ChaseOS-Gate]]
