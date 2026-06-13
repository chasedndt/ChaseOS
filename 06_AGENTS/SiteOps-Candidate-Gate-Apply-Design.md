---
title: SiteOps Candidate Gate Apply Design
type: architecture
status: partial / denied-by-default design preflight
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Gate Apply Design

This note defines the first safe Gate apply design surface for Browser Skill
candidate promotion.

It does not implement trusted writes.

## Current Surface

Read-only approval queue/provenance inspection (operator-facing approval aggregation routes through [[ChaseOS-Approval-Center]]):

```powershell
chaseos siteops candidates approvals --tenant TENANT_ID --workspace WORKSPACE_ID --json
```

This list surface reads scoped Browser Skill candidate promotion `ApprovalRequest`
artifacts and reports each approval's `approval_provenance` status and
`apply_contract_status` without making approval decisions, writing trusted
artifacts, activating skills, or invoking browser execution.

Command:

```powershell
chaseos siteops candidates gate-apply-design CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_gate_apply_design(...)
```

The command composes the existing scoped `apply-contract`, reads the matching
`ApprovalRequest`, verifies approval provenance binding when the approval carries
candidate metadata (`candidate_id` and `proposed_skill_id`), reports a read-only
`approval_provenance` inspector (`bound_match`, `legacy_unbound`, or rejected
`bound_mismatch`), previews future target paths, and checks the future Gate
operation id:

```text
siteops.browser_skill_candidate.apply_trusted_artifacts
```

That Gate operation is intentionally not allowlisted. Current result:

```text
gate_operation_allowed: false
gate_apply_design_status: blocked_gate_operation_not_allowlisted
writes_performed: false
```

If the approval is still pending, the design status remains
`blocked_pending_approval`.

The target write preview includes a `path_confined` flag for each future target
so reviewers can see that trusted Browser Skill YAML and SiteOps Skill Card JSON
would remain inside their governed homes before any later executor is built.

The follow-on command `chaseos siteops candidates gate-executor-spec` now
describes the future executor preconditions and write plan. That command is also
non-mutating and keeps the executor `NOT BUILT`. Its preflight packet now
includes a read-only `secret_session_exclusion_recheck` derived from candidate
validation, so operator review can see whether secret/cookie/token/session
exclusion was rechecked without exposing raw candidate content.

## Allowed

- Read a redacted Browser Skill candidate.
- Read a scoped SiteOps `ApprovalRequest`.
- Compute future target paths for:
  - trusted Browser Skill YAML,
  - SiteOps Skill Card JSON.
- Report whether each future target path is confined to its governed home.
- Report a read-only secret/cookie/token/session exclusion recheck derived from candidate validation.
- Report required future checks.
- Report approval provenance inspection status without mutating approval state.
- Report denied effects.
- Confirm that the future Gate operation is not currently allowlisted.

## Denied

- No trusted Browser Skill write.
- No SiteOps Skill Card write.
- No browser execution.
- No CDP daemon.
- No authenticated browser session.
- No cookie, token, credential, or browser profile access.
- No activation marker.
- No canonical ChaseOS writeback.
- No Gate allowlist change.

## Future Apply Requirements

A later implementation may only add a real apply executor after:

- the operator explicitly approves the feature pass,
- a named Gate operation is added and tested,
- target writes are path-confined to trusted Browser Skill and SiteOps Skill Card homes,
- candidate validation is rerun immediately before write,
- secret/session exclusion is rerun immediately before write,
- approval provenance binding reports `bound_match` for newly bound approvals before trusted writes are even considered,
- approval scope matches tenant/workspace/user,
- approval provenance binding matches the same candidate and proposed skill target,
- an Agent Activity log and SiteOps audit record are written by the executor,
- execution starts in dry-run/shadow mode.
- the fail-closed executor spec remains satisfied immediately before any future
  executor implementation is enabled.

## Current Verdict

`gate-apply-design` is a Phase 9 safety foothold. It makes the future apply
contract inspectable while preserving deny-by-default behavior.

Full trusted promotion and the Phase 10 Site Skills inspection UI remain future
work.

The current next boundary is not trusted writes. `gate-executor-spec` now
provides the disabled executor preflight/review surface, and any real writer
still requires a separately approved Gate allowlist/executor pass.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Gate-Executor-Spec]] - [[Browser-Skill-Memory]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Harness-Boundaries]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
