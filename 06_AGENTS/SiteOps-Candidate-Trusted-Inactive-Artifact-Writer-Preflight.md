---
title: SiteOps Candidate Trusted Inactive Artifact Writer Preflight
type: architecture
status: VERIFIED / NO-WRITE PREFLIGHT
created: 2026-05-02
updated: 2026-05-02
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Trusted Inactive Artifact Writer Preflight

`chaseos siteops candidates trusted-inactive-artifact-writer-preflight` is the no-write preflight before any future trusted inactive Browser Skill or SiteOps Skill Card writer can exist.

It composes:

- approved bound replacement approval validation
- replacement approval decision/consumption readiness
- inactive Browser Skill and SiteOps Skill Card payload validation
- trusted target path confinement and collision posture
- Gate operation denial posture for `siteops.browser_skill_candidate.apply_trusted_artifacts`
- activation-disabled and no-browser/no-provider/no-Agent-Bus boundaries

## Command

```powershell
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-preflight CANDIDATE_ID `
  --replacement-approval-id REPLACEMENT_APPROVAL_ID `
  --tenant local `
  --workspace default `
  --user local-user `
  --json
```

## Boundary

This command is allowed to read candidate, approval, target-path, and Gate posture. It is not allowed to:

- consume replacement approvals
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- write audit events
- mutate Gate allowlists
- launch or control browsers
- enqueue Agent Bus tasks
- call providers
- activate skills
- write canonical ChaseOS state

## Verification Status

Focused tests verify the ready path from an approved bound replacement approval and CLI no-write behavior. Live repo smoke remains blocked because the current local candidate has no approved bound replacement approval available for consumption.

## Next Step

The follow-on surface is `trusted-inactive-artifact-writer-implementation-request`, which packages this preflight evidence for operator review without writing artifacts or implementing the writer.

## Graph Links

[[ChaseOS-SiteOps]] - [[Browser-Operator-Skill-Layer]] - [[SiteOps-Candidate-Replacement-Approval-Decision-Consumption]] - [[SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Implementation-Request]] - [[SiteOps-Candidate-Executor-Feature-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
