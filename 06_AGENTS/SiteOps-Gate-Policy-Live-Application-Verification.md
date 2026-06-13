---
title: SiteOps Gate Policy Live Application Verification
type: agent-runtime-verification
status: VERIFIED / DOCS-ONLY RUNBOOK
created: 2026-05-03
updated: 2026-05-03
phase: Phase 9 runtime/operator infrastructure
runtime: Codex
---

# SiteOps Gate Policy Live Application Verification

This document defines the verification boundary for applying the SiteOps trusted
inactive artifact writer Gate policy patch.

It is a runbook and evidence contract only. It does not authorize Gate mutation,
approval consumption, trusted artifact writes, activation, browser/CDP
execution, Agent Bus work, provider calls, or canonical memory/state writeback.

## Feature Family

Recommended feature-family name:

`SiteOps Trusted Inactive Artifact Writer Gate Policy Application`

This belongs to Phase 9 runtime/operator infrastructure. It unlocks the narrow
trusted-inactive artifact writer path after operator review. Browser skill
inspection UI, skill browsing, and promotion review surfaces remain Phase 10.

## Current Repo Truth

- The guarded patch writer exists behind `--apply-gate-policy-patch`.
- The no-write live readiness command exists.
- The live Gate operation is still not applied unless a future pass has run the
  guarded writer with real approval IDs.
- The trusted executor entrypoint is built, but remains Gate-blocked until the
  policy patch is applied.
- Trusted inactive artifacts, activation, browser replay/control, Agent Bus
  integration, provider calls, and canonical memory writeback remain out of
  scope.

## Required Pre-Apply Evidence

Before any live application pass, collect and preserve:

| Evidence | Requirement |
| --- | --- |
| Replacement approval ID | Real operator-reviewed replacement approval; no legacy unbound approval |
| Gate approval ID | Real operator-reviewed approval for this Gate policy application |
| Readiness result | `gate_policy_live_application_ready_no_write` |
| Gate operation posture | Target operation absent before first apply, or already-applied state explicitly reported |
| Gateway category posture | Required inactive-review categories absent before first apply, or already-applied state explicitly reported |
| Current digests | Current normalized digest for `runtime/chaseos_gate.py` and `runtime/policy/gateway_allowlists.json` |
| Future apply command | Exact command preview from the readiness packet |
| Operator scope check | Confirms this pass applies only Gate policy, not trusted artifacts or activation |

Readiness command:

```powershell
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-gate-policy-live-application-readiness <candidate_id> --replacement-approval-id <replacement_approval_id> --gate-approval-id <gate_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## Live Apply Command

The future live application pass may run only after the readiness command reports
ready with real approval IDs:

```powershell
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation <candidate_id> --replacement-approval-id <replacement_approval_id> --gate-approval-id <gate_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --apply-gate-policy-patch --json
```

The command must patch exactly two files:

- `runtime/chaseos_gate.py`
- `runtime/policy/gateway_allowlists.json`

## Expected Post-Apply Evidence

The post-apply result must show:

- `gate_policy_patch_writer_implementation_status` equals
  `gate_policy_patch_writer_implementation_applied`.
- The runtime operation entry is present exactly once:
  `siteops.browser_skill_candidate.apply_trusted_artifacts`.
- The gateway allowlist contains the exact inactive-review categories:

```json
{
  "browser_skills_inactive_review": [
    "runtime/browser_skills/skills/*.yaml"
  ],
  "siteops_skill_cards_inactive_review": [
    "runtime/siteops/registry/skill_cards/*.json"
  ]
}
```

- Backup artifacts exist under the writer-reported
  `07_LOGS/SiteOps-Gate-Policy-Patches/<tenant>/<workspace>/<run_id>/` path.
- Rollback audit evidence exists and reports:
  - rollback was not performed during a successful apply
  - target files were backed up before replacement
  - no secrets, cookies, tokens, credentials, browser session state, or personal
    account state were written into artifacts
- Post-apply verification compiled the Gate file and parsed gateway JSON.
- Re-running live readiness reports already-applied or apply-ready posture.
- Re-running the trusted inactive writer readiness shows the Gate boundary has
  moved from policy-missing to approval/write-readiness posture.

## Mandatory Post-Apply Commands

Run these after the future live apply:

```powershell
python -m py_compile runtime/chaseos_gate.py
python -m json.tool runtime/policy/gateway_allowlists.json
python -m runtime.cli.main siteops candidates trusted-inactive-artifact-writer-gate-policy-live-application-readiness <candidate_id> --replacement-approval-id <replacement_approval_id> --gate-approval-id <gate_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
python -m runtime.cli.main siteops candidates apply-trusted-candidate-artifacts <candidate_id> --replacement-approval-id <replacement_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

The last command should be run first without `--write-inactive-artifacts` unless
the operator explicitly starts the separate trusted artifact write pass.

## Rollback Boundary

If post-apply verification fails:

1. Stop the pass and do not run trusted artifact writes.
2. Preserve the writer output, backup paths, digests, and failing command output.
3. Restore only from the writer-created backup artifacts for the two target
   files, after operator confirmation.
4. Re-run `py_compile`, `json.tool`, and the no-write readiness command.
5. Write rollback evidence to the build log and Agent Activity log.

Manual broad edits to Gate policy are not part of this runbook.

## Security Boundaries

- No live browser control is granted by this patch.
- No authenticated browser session may be used without explicit user approval.
- Browser observations and candidate artifacts remain untrusted until reviewed.
- No secrets, cookies, tokens, credentials, browser profile data, or personal
  account state may be written into skills, skill cards, backups, rollback
  audits, or logs.
- Domain skills and SiteOps Skill Cards must be proposed, reviewed, and promoted;
  they are not silently canonical truth.
- Any future live browser write/action mode must begin in shadow mode.
- Every future browser or SiteOps task must produce Agent Activity evidence.

## Completion Boundary

This verification doc is complete when it exists, is linked from the SiteOps
tracker, and a no-write readiness smoke confirms the live Gate policy remains
unchanged in this pass.

The SiteOps trusted inactive artifact writer feature is not complete until a
future pass applies the Gate policy with real approval IDs, verifies the exact
patch, then performs a separately approved trusted inactive artifact write and
postwrite verification.

## Graph Links

[[SiteOps-Candidate-Executor-Feature-Completion-Tracker]] -
[[Browser-Operator-Skill-Layer]] -
[[SiteOps-Gate-Policy-Live-Application-Runbook]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
