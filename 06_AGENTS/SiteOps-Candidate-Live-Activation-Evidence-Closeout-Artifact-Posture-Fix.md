---
title: SiteOps Candidate Live Activation Evidence Closeout Artifact Posture Fix
type: feature-note
status: COMPLETE TARGETED / READINESS BUG FIX / NO ACTIVATION
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Live Activation Evidence Closeout Artifact Posture Fix

This pass corrected the live activation evidence closeout so inactive trusted
artifact evidence is satisfied only when the activation executor dry-run proves
the Browser Skill and SiteOps Skill Card are present, parseable,
`inactive_review`, `activation_allowed=false`, and secret-free.

## Repo-Truth Delta

Parallel SiteOps work had already advanced the live local candidate past source
approval, activation approval, and marker-only activation approval consumption.
It also appears to have applied the trusted inactive artifact writer Gate
allowance for `siteops.browser_skill_candidate.apply_trusted_artifacts`.

The live activation closeout previously treated computed target paths as
artifact satisfaction. That was incorrect: the real candidate still does not
have:

- `runtime/browser_skills/skills/example-com.observed_shadow_flow.yaml`
- `runtime/siteops/registry/skill_cards/example-com.observed_shadow_flow.json`

## What Changed

- `activation-executor-live-readiness` now exposes the guarded executor's
  internal `activation_executor_checks`.
- `live-activation-evidence-closeout` now uses
  `activation_executor_artifacts_still_inactive_and_secret_free` before marking
  inactive Browser Skill or SiteOps Skill Card evidence as satisfied.
- Missing or invalid inactive artifacts now remain backend blockers even when
  target paths are known.

## Live Evidence After Fix

Live local closeout for
`candidate_browser_runtime_20260430_022607_example-com` now reports:

- source approval: satisfied
- activation approval: satisfied
- activation consumption marker: satisfied
- inactive trusted Browser Skill: `missing_or_invalid`
- inactive SiteOps Skill Card: `missing_or_invalid`
- activation Gate allowance: missing/denied
- activation executor dry-run: blocked
- browser replay shadow mode: not built

## Boundaries

This pass did not write inactive trusted artifacts, activate skills, mutate Gate
policy, consume approvals, mutate approval status, launch or control a browser,
enqueue Agent Bus work, call providers, or write canonical ChaseOS state.

## Next Pass

`siteops-candidate-trusted-inactive-artifact-live-write`: use the now-allowlisted
trusted inactive artifact writer path to create the missing inactive Browser
Skill and SiteOps Skill Card artifacts, then rerun live activation evidence
closeout. Do not activate and do not start browser replay.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
