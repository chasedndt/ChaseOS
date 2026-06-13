---
title: SiteOps Candidate Bound Approval Writer Implementation Approval
type: architecture-note
status: COMPLETE / VERIFIED TARGETED / NO-WRITE
created: 2026-05-01
updated: 2026-05-01
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Bound Approval Writer Implementation Approval

This note records the no-write approval/rejection packet for a future SiteOps
Browser Skill candidate bound approval writer implementation pass.

The command:

```powershell
chaseos siteops candidates bound-approval-writer-implementation-approval CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --actor USER_ID --decision approve|reject --json
```

composes `bound-approval-writer-implementation-request` and returns an
operator decision packet. It does not write that packet, implement the writer,
or authorize replacement approval persistence in the same pass.

## Current Behavior

`candidate_promotion_bound_approval_writer_implementation_approval(...)`
returns:

- candidate, proposed skill, tenant, workspace, user, actor, and decision
- the inherited implementation-request/preflight status
- a review-only `implementation_approval_record`
- checks proving the record is still no-write and the writer is still disabled
- `implementation_patch_allowed_next_pass=true` only when the underlying
  implementation request is ready and the decision is `approve`
- all replacement approval, audit, marker, trusted write, browser, provider,
  Agent Bus, activation, Gate, and canonical writeback flags false

If the implementation request is blocked, the approval packet is also blocked.
The live local candidate currently remains blocked because the source approval
is pending and legacy-unbound.

## ID Hardening

This pass also made the future replacement approval preview ID stable for the
same tenant/workspace/user/candidate/source-approval tuple. That makes repeated
preflight/idempotency/recovery checks deterministic and avoids same-second
preview drift.

## Security Boundary

This pass intentionally keeps all of the following denied:

- writing the implementation approval record
- implementing or running the bound approval writer
- writing a replacement approval request
- mutating or consuming the legacy approval
- recording approval decisions
- writing audit, idempotency, preflight, or recovery markers
- writing trusted Browser Skill or SiteOps Skill Card artifacts
- editing `runtime/policy/gateway_allowlists.json`
- launching or controlling a browser
- enqueueing Agent Bus tasks
- calling provider APIs
- activating skills
- writing canonical ChaseOS memory/state

## Next Required Pass

The first real bound approval writer implementation now exists in
`[[SiteOps-Candidate-Bound-Approval-Writer-Implementation]]`. It reruns
implementation-approval and preflight inside the writer call, dry-runs by
default, and with `--write-replacement-approval` may write only a new pending
bound replacement approval plus scoped run/audit/idempotency/recovery evidence.
It still must not consume approvals or write trusted Browser Skill / SiteOps
Skill Card artifacts.

The next required pass is replacement approval decision/consumption policy.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[SiteOps-Candidate-Bound-Approval-Writer-Implementation-Request]] - [[SiteOps-Candidate-Bound-Approval-Writer-Preflight]] - [[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
