---
title: SiteOps Candidate Trusted Inactive Artifact Writer Implementation
type: architecture
status: BUILT / GATE-CHECKED / EXPLICIT WRITE FLAG
created: 2026-05-02
updated: 2026-05-02
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Trusted Inactive Artifact Writer Implementation

`chaseos siteops candidates trusted-inactive-artifact-writer-implementation` is the bounded writer for inactive-review Browser Skill and SiteOps Skill Card artifacts.

The writer is implemented, but it is not an unrestricted executor. It writes only when all of these are true:

- the trusted inactive writer implementation approval packet is ready
- the trusted inactive writer preflight passes immediately before the write
- target paths are confined and collision-free
- the Gate operation allows `siteops.browser_skill_candidate.apply_trusted_artifacts`
- the operator supplies `--write-inactive-artifacts`

In the live repo, the Gate operation is still not allowlisted, so the command fails closed and writes nothing.

## Command

```powershell
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-implementation CANDIDATE_ID `
  --replacement-approval-id REPLACEMENT_APPROVAL_ID `
  --tenant local `
  --workspace default `
  --user local-user `
  --actor local-user `
  --reason "write inactive review artifacts" `
  --write-inactive-artifacts `
  --json
```

Omit `--write-inactive-artifacts` for dry-run/preview behavior.

## Allowed Writes

Only when every gate passes and `--write-inactive-artifacts` is supplied:

- inactive Browser Skill artifact under `runtime/browser_skills/skills/`
- inactive SiteOps Skill Card artifact under `runtime/siteops/registry/skill_cards/`
- scoped SiteOps run record
- scoped SiteOps audit events

All artifact writes use create-new semantics and refuse target collisions.

## Still Forbidden

- replacement approval consumption
- legacy approval mutation
- Gate allowlist mutation
- activation
- browser/CDP/browser-use execution
- Agent Bus enqueue
- provider API calls
- canonical ChaseOS memory/state writeback

## Verification

2026-05-02 targeted verification:

- `runtime/siteops/tests/test_candidate_promotions.py` passed with `100 passed`
- CLI command/JSON contract suite passed with `8 passed`
- generated CLI docs check passed
- live missing-approval smoke failed closed

Unit verification includes a mocked Gate-approved collaborator path that writes inactive artifacts in a temp vault. Live repo verification remains blocked by Gate and missing bound replacement approval evidence.

## Current Status

The writer is **BUILT / GATE-CHECKED / EXPLICIT WRITE FLAG**. The broader SiteOps candidate executor remains partial because live Gate allowlist, activation, browser replay, Agent Bus/provider integration, and canonical writeback remain unimplemented.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Implementation-Approval]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Implementation-Request]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Preflight]] - [[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
