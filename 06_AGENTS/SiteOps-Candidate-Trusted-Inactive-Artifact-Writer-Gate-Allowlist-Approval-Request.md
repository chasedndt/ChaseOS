---
title: SiteOps Candidate Trusted Inactive Artifact Writer Gate Allowlist Approval Request
type: architecture
status: VERIFIED / PENDING APPROVAL REQUEST PATH
created: 2026-05-02
updated: 2026-05-02
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Trusted Inactive Artifact Writer Gate Allowlist Approval Request

`chaseos siteops candidates trusted-inactive-artifact-writer-gate-allowlist-approval-request`
previews or writes a pending SiteOps approval request for a future Gate policy
patch for `siteops.browser_skill_candidate.apply_trusted_artifacts`.

This command does not apply the Gate patch. Optional writes are limited to a
pending SiteOps `ApprovalRequest` plus a scoped SiteOps audit event.

## Command

Preview only:

```powershell
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-gate-allowlist-approval-request CANDIDATE_ID `
  --replacement-approval-id REPLACEMENT_APPROVAL_ID `
  --tenant local `
  --workspace default `
  --user local-user `
  --actor local-user `
  --json
```

Write pending approval request:

```powershell
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-gate-allowlist-approval-request CANDIDATE_ID `
  --replacement-approval-id REPLACEMENT_APPROVAL_ID `
  --tenant local `
  --workspace default `
  --user local-user `
  --actor local-user `
  --requested-by local-user `
  --write-approval-request `
  --json
```

## Preconditions

The command composes `trusted-inactive-artifact-writer-live-gate-readiness`.
Approval request writing is ready only when:

- trusted inactive writer implementation approval is ready
- immediate trusted inactive writer preflight is ready
- target paths are available
- current Gate posture denies the live write operation
- proposed Gate patch is previewable for operator review

## Written Artifact

With `--write-approval-request`, the command writes a pending SiteOps approval
request under `07_LOGS/SiteOps-Approvals/<tenant>/<workspace>/`.

The approval metadata includes:

- candidate id
- proposed skill id
- replacement approval id
- Gate operation
- target paths and write targets
- preview-only Gate patch shape
- request digest
- explicit booleans showing no secrets/session state, Gate mutation, or artifact
  write occurred

## Denied Effects

This approval-request command does not:

- edit `runtime/chaseos_gate.py`
- edit `runtime/policy/gateway_allowlists.json`
- write Browser Skill artifacts
- write SiteOps Skill Card artifacts
- consume replacement approvals
- consume the new Gate approval request
- activate promoted skills
- launch or control browsers
- enqueue Agent Bus work
- call provider APIs
- write canonical ChaseOS memory or state

## Next Boundary

The no-mutation Gate allowlist approval-decision preflight now exists as
`trusted-inactive-artifact-writer-gate-allowlist-decision-preflight`. It
validates the pending/decided approval request, operator decision status, target
patch digest, and fail-closed smoke requirements before any Gate policy patch is
considered.

The follow-on no-write patch-plan command now exists as
`trusted-inactive-artifact-writer-gate-policy-patch-plan`; it previews exact
future Gate policy and gateway allowlist edits without applying them.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Live-Gate-Readiness]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Allowlist-Decision-Preflight]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Plan]] - [[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
