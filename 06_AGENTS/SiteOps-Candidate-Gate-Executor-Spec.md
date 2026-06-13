---
title: SiteOps Candidate Gate Executor Spec
type: architecture
status: partial / spec-only fail-closed
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Gate Executor Spec

This note defines the fail-closed future executor specification for Browser
Skill candidate promotion.

It does not implement an executor.

## Current Surface

Command:

```powershell
chaseos siteops candidates gate-executor-spec CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_gate_executor_spec(...)
```

The command composes:

1. redacted candidate inspection,
2. scoped approval request lookup,
3. approval provenance binding inspection,
4. non-mutating apply contract,
5. denied-by-default Gate apply design,
6. future executor precondition and write-plan specification.

The future write operation is still:

```text
siteops.browser_skill_candidate.apply_trusted_artifacts
```

That Gate operation remains intentionally not allowlisted.

## Current Result

Current executor spec output reports:

```text
executor_implemented: false
executor_enabled: false
writes_performed: false
trusted_skill_write_allowed: false
siteops_skill_card_write_allowed: false
browser_execution_allowed: false
agent_bus_enqueue_allowed: false
provider_api_call_allowed: false
activation_allowed: false
canonical_writeback_allowed: false
```

When the approval is approved but Gate remains unallowlisted, status is:

```text
executor_spec_status: blocked_gate_operation_not_allowlisted
```

When the approval is still pending, the spec inherits:

```text
executor_spec_status: blocked_pending_approval
```

The spec now also returns `executor_preflight_checks`:

- `candidate_preflight_ready`
- `apply_contract_ready`
- `approval_provenance_bound_match`
- `target_paths_confined`
- `gate_operation_allowlisted`
- `executor_implemented`
- `writes_disabled`

Legacy unbound approvals block before Gate status:

```text
executor_spec_status: blocked_approval_provenance_not_bound
```

## Future Executor Contract

A later executor may only be considered after a separate approved pass defines
and tests the actual writer. At minimum, it must:

- rerun candidate validation immediately before write,
- rerun secret/cookie/token/session exclusion immediately before write,
- require approval provenance `bound_match`,
- require tenant/workspace/user scope to match candidate, approval, run, and
  audit artifacts,
- require the Gate operation to be explicitly allowlisted,
- require target paths to stay inside governed trusted artifact homes,
- write scoped prewrite and postwrite audit events,
- keep trusted artifacts inactive until a separate activation path exists,
- fail closed before any browser execution, Agent Bus enqueue, provider call,
  or canonical writeback.

## Future Write Plan

The spec describes the future write order but does not perform it:

1. revalidate candidate,
2. recheck secret/session exclusion,
3. write prewrite SiteOps audit event,
4. write trusted Browser Skill YAML,
5. write SiteOps Skill Card JSON,
6. write postwrite SiteOps audit event.

All future trusted artifact write steps currently report `write_allowed: false`.

## Denied

- No trusted Browser Skill write.
- No SiteOps Skill Card write.
- No browser execution.
- No Agent Bus task enqueue.
- No provider/API call.
- No activation marker.
- No canonical ChaseOS writeback.
- No Gate allowlist change.

## Current Verdict

`gate-executor-spec` is a Phase 9 safety contract. It makes the next executor
boundary machine-inspectable while preserving deny-by-default behavior.

The real executor remains NOT BUILT.

The operator-facing preflight alias is documented in
`[[SiteOps-Candidate-Apply-Executor-Preflight]]`; the implemented command
surface remains `gate-executor-spec`.

The follow-on allowlist review surface is documented in
`[[SiteOps-Candidate-Gate-Allowlist-Review]]`. It evaluates the future Gate
allowlist question but does not edit `runtime/policy/gateway_allowlists.json`.

The follow-on design surface is documented in
`[[SiteOps-Candidate-Trusted-Executor-Design]]`. It defines executor components,
audit sequencing, rollback behavior, and failure modes without implementing the
executor.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Gate-Apply-Design]] - [[SiteOps-Candidate-Apply-Executor-Preflight]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[SiteOps-Candidate-Trusted-Executor-Design]] - [[Browser-Skill-Memory]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
