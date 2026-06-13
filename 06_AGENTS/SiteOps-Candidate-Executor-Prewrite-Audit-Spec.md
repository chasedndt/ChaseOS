---
title: SiteOps Candidate Executor Prewrite Audit Spec
type: architecture
status: partial / no-write audit and inactive-artifact contract
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Executor Prewrite Audit Spec

This note documents the no-write audit event and inactive-artifact contract for
a future `apply_trusted_candidate_artifacts` executor.

It does not implement the executor and it does not write audit events.

## Current Surface

Command:

```powershell
chaseos siteops candidates executor-prewrite-audit-spec CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_executor_prewrite_audit_spec(...)
```

The command composes `executor-implementation-design-review` and returns a
machine-readable contract for future audit events, inactive trusted artifacts,
validation checks, and forbidden metadata fields.

The follow-on `[[SiteOps-Candidate-Inactive-Artifact-Validator]]` command uses
this contract to validate proposed inactive Browser Skill and SiteOps Skill
Card payloads in memory only.

## Audit Event Contract

Future executor implementation must preserve this sequence:

- `trusted_executor_preflight_started`
- `trusted_executor_prewrite_validated`
- `trusted_artifact_write_attempted`
- `trusted_artifact_write_result`
- `trusted_executor_postwrite_closed`
- `trusted_executor_blocked`
- `trusted_executor_rollback_required`

Each event requires tenant/workspace/user/candidate/approval/run identity fields
and forbids raw candidate content, cookies, tokens, API keys, passwords,
secrets, session state, browser profile paths, credential values, private keys,
and seed phrases.

## Inactive Artifact Contract

Future trusted Browser Skill and SiteOps Skill Card artifacts must be written
only as inactive review artifacts:

```text
required_status: inactive_review
activation_allowed: false
```

Promotion is not activation. Any activation remains a separate future approval
and Gate-controlled workflow.

## Current Output States

Ready, with an approved bound approval and all upstream guards passing:

```text
prewrite_audit_spec_status: prewrite_audit_spec_ready_no_authority
review_decision: audit_contract_only_do_not_write_in_this_pass
```

Blocked, when upstream design review is not ready:

```text
prewrite_audit_spec_status: blocked_implementation_design_review: <status>
review_decision: blocked_before_audit_contract
```

## Denied Effects

The command performs no:

- audit event write,
- inactive trusted artifact write,
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

`executor-prewrite-audit-spec` is a review-only contract layer. It makes the
future executor's audit and inactive-artifact obligations testable without
granting any implementation, write, Gate, browser, provider, activation, or
canonical writeback authority.

It is now followed by the no-write inactive artifact validator, which still
does not write trusted artifacts or implement the executor.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Inactive-Artifact-Validator]] - [[SiteOps-Candidate-Executor-Implementation-Design-Review]] - [[SiteOps-Candidate-Executor-Preimplementation-Verifier]] - [[SiteOps-Candidate-Executor-Implementation-Checklist]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
