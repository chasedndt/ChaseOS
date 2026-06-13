---
title: SiteOps Candidate Bound Approval Writer Implementation Request
type: architecture-note
status: COMPLETE / VERIFIED TARGETED / NO-WRITE
created: 2026-05-01
updated: 2026-05-01
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Bound Approval Writer Implementation Request

This note records the no-write implementation-request packet for the future
SiteOps Browser Skill candidate bound approval writer.

The command:

```powershell
chaseos siteops candidates bound-approval-writer-implementation-request CANDIDATE_ID --approval-id APPROVAL_ID --tenant TENANT_ID --workspace WORKSPACE_ID --user USER_ID --json
```

composes `bound-approval-writer-preflight` and returns an operator review packet
for a later pass that may implement the first real replacement approval writer.
It does not write that packet to disk and does not authorize the writer.

## Current Behavior

`candidate_promotion_bound_approval_writer_implementation_request(...)` returns:

- the candidate, proposed skill, tenant, workspace, user, and superseded approval
  binding
- the preflight status inherited from `bound-approval-writer-preflight`
- a review-only `implementation_request_artifact`
- readiness checks proving the request is scope-bound and still no-write
- future implementation requirements for an explicitly approved writer pass
- all write, executor, browser, Agent Bus, provider, activation, and canonical
  writeback flags set false

If the preflight is blocked, the request reports
`blocked_bound_approval_writer_preflight: ...` and
`blocked_before_implementation_request`.

If the preflight is ready, the request reports
`bound_approval_writer_implementation_request_ready_no_write` and remains
review-only.

## Security Boundary

This pass intentionally keeps all of the following denied:

- writing an implementation request artifact
- implementing or running the bound approval writer
- writing a replacement approval request
- mutating or consuming the legacy approval
- writing audit, idempotency, preflight, or recovery markers
- writing trusted Browser Skill or SiteOps Skill Card artifacts
- editing `runtime/policy/gateway_allowlists.json`
- launching or controlling a browser
- enqueueing Agent Bus tasks
- calling provider APIs
- activating skills
- writing canonical ChaseOS memory/state

No secrets, cookies, tokens, API keys, credentials, browser session data, raw
candidate content, or personal account state may be written into the request.

## Verification

Focused tests cover:

- ready no-write implementation-request packets
- blocked pending/legacy-unbound approval posture
- CLI non-mutating behavior

The 2026-05-01 verification pass ran the focused SiteOps candidate promotion
suite, adjacent CLI/contract regression, generated CLI docs check, live blocked
preflight smoke, live blocked implementation-request smoke, and absence checks
for replacement approval artifacts, markers, trusted target files, executor
symbol, and Gate allowlist entry.

## Follow-On Pass

The follow-on pass is
`[[SiteOps-Candidate-Bound-Approval-Writer-Implementation-Approval]]`, which
turns this request packet into a no-write approve/reject decision packet. The
actual writer implementation remains separate and must rerun
`bound-approval-writer-preflight` immediately before any write.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[SiteOps-Candidate-Bound-Approval-Writer-Implementation-Approval]] - [[SiteOps-Candidate-Bound-Approval-Writer-Preflight]] - [[SiteOps-Candidate-Executor-Bound-Approval-Writer-Design]] - [[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
