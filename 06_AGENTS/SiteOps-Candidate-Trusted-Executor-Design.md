---
title: SiteOps Candidate Trusted Executor Design
type: architecture
status: partial / design-only fail-closed
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Trusted Executor Design

This note defines the design-only trusted artifact executor packet for Browser
Skill candidate promotion.

It does not implement the executor.

## Current Surface

Command:

```powershell
chaseos siteops candidates trusted-executor-design CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_trusted_executor_design(...)
```

The command composes redacted candidate inspection, scoped approval lookup,
approval provenance binding inspection, the non-mutating apply contract,
denied-by-default Gate apply design, fail-closed executor spec, review-only Gate
allowlist review, and the trusted executor design packet.

## Current Result

With an approved, provenance-bound request and the Gate operation still not
allowlisted, the expected design status is:

```text
trusted_executor_design_status: trusted_executor_design_ready_but_not_implemented
allowlist_review_status: blocked_executor_not_implemented
operation_currently_allowlisted: false
executor_implemented: false
executor_enabled: false
writes_performed: false
```

For pending, unbound, invalid, or unconfined requests, the design inherits the
earliest fail-closed blocker.

## Design Components

The packet describes future components only:

- `scope_loader`
- `candidate_revalidator`
- `secret_session_guard`
- `gate_operation_checker`
- `artifact_writer`
- `audit_writer`
- `activation_boundary`

Each component currently reports `implemented: false`.

## Audit Sequence

The future executor must define and test an audit sequence before any trusted
write exists:

1. `trusted_executor_preflight_started`
2. `trusted_executor_prewrite_validated`
3. `trusted_artifact_write_attempted`
4. `trusted_artifact_write_result`
5. `trusted_executor_postwrite_closed`

All sequence entries are design-only in the current pass.

## Rollback Boundary

The design requires future rollback handling for failure before any artifact
write, failure after partial artifact write, and postwrite validation failure.
Partial artifacts must remain inactive review artifacts and require manual
review. Activation remains a separate future workflow.

## Denied

- No executor function is implemented.
- No Gate policy file is edited.
- No trusted Browser Skill write is performed.
- No SiteOps Skill Card write is performed.
- No browser execution occurs.
- No Agent Bus task is enqueued.
- No provider/API call occurs.
- No activation marker is written.
- No canonical ChaseOS writeback occurs.

## Current Verdict

`trusted-executor-design` is a Phase 9 design packet. It makes the future
executor implementation checklist, failure modes, audit sequence, rollback plan,
and acceptance tests inspectable while preserving deny-by-default behavior.

The trusted artifact executor remains NOT BUILT and disabled.

## Follow-On Guard Tests

The follow-on `[[SiteOps-Candidate-Executor-Guard-Tests]]` pass added
regression tests that assert the executor entrypoint remains absent, the future
Gate operation remains denied, design/write-plan steps remain unimplemented,
and trusted artifact targets remain unwritten.

Those tests are guard coverage only. They still do not implement the executor,
edit Gate policy, write trusted artifacts, activate skills, launch a browser, or
perform canonical writeback.

## Follow-On Implementation Checklist

The follow-on `[[SiteOps-Candidate-Executor-Implementation-Checklist]]` pass
defines the review gate for any future executor implementation and now exposes
it as `chaseos siteops candidates executor-review-checklist`. It records the
required preconditions, execution order, tests, audit events, rollback boundary,
and denied effects before `apply_trusted_candidate_artifacts` can exist.

That checklist is still no-write. It does not implement the executor,
allowlist the Gate operation, write trusted artifacts, activate skills, launch
a browser, enqueue Agent Bus tasks, call providers, or perform canonical
writeback.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Gate-Allowlist-Review]] - [[SiteOps-Candidate-Gate-Executor-Spec]] - [[SiteOps-Candidate-Apply-Executor-Preflight]] - [[SiteOps-Candidate-Executor-Guard-Tests]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[Browser-Skill-Memory]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
