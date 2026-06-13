---
title: SiteOps Candidate Inactive Artifact Validator
type: architecture
status: partial / no-write inactive artifact validation
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Inactive Artifact Validator

This note documents the no-write validator for future inactive Browser Skill
and SiteOps Skill Card payloads.

It does not implement the trusted artifact executor and it does not write
trusted artifacts.

## Current Surface

Command:

```powershell
chaseos siteops candidates inactive-artifact-validator CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

Runtime helper:

```python
runtime.siteops.candidate_promotions.candidate_promotion_inactive_artifact_validator(...)
```

The command composes `executor-prewrite-audit-spec`, builds proposed inactive
artifact payloads in memory, and validates their shape against the no-write
contracts.

## Validation Contract

The validator currently checks:

- required identity fields are present,
- `status` is `inactive_review`,
- `activation_allowed` is `false`,
- forbidden fields such as cookies, tokens, API keys, passwords, secrets,
  sessions, private keys, and seed phrases are absent,
- validation remains in memory only.

The proposed payloads are not written.

## Current Output States

Ready, with all upstream guards passing:

```text
inactive_artifact_validator_status: inactive_artifact_validator_ready_no_authority
validation_pass: true
review_decision: validator_contract_only_do_not_write_in_this_pass
```

Blocked, when upstream prewrite audit spec is not ready:

```text
inactive_artifact_validator_status: blocked_prewrite_audit_spec: <status>
validation_pass: false
review_decision: blocked_before_inactive_artifact_validation
```

## Denied Effects

The command performs no:

- inactive trusted artifact write,
- audit event write,
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

`inactive-artifact-validator` is the next no-write contract layer before any
future executor implementation. It proves the future inactive artifact payload
shape can be checked without granting write, Gate, browser, provider,
activation, or canonical writeback authority.

The follow-on `[[SiteOps-Candidate-Executor-Collision-Policy-Spec]]` layer
defines target collision, overwrite, idempotency, and rollback rules before any
future inactive artifact write can be considered.

## Graph Links

[[ChaseOS-SiteOps]] - [[SiteOps-Candidate-Executor-Collision-Policy-Spec]] - [[SiteOps-Candidate-Executor-Prewrite-Audit-Spec]] - [[SiteOps-Candidate-Executor-Implementation-Design-Review]] - [[SiteOps-Candidate-Executor-Preimplementation-Verifier]] - [[Browser-Operator-Skill-Layer]] - [[Agent-Control-Plane]] - [[Permission-Matrix]]
