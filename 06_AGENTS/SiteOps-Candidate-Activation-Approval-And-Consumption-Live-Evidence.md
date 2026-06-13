---
title: SiteOps Candidate Activation Approval And Consumption Live Evidence
type: implementation-evidence
status: PARTIAL / BACKEND ACTIVATION CHAIN ADVANCED / BROWSER REPLAY NOT BUILT
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval And Consumption Live Evidence

This note records the 2026-05-03 live evidence pass for the local SiteOps
Browser Skill candidate:

```text
candidate_browser_runtime_20260430_022607_example-com
```

## What Changed

This pass advanced the real-vault activation evidence chain beyond the previous
source-approval blocker.

The pass:

- created and approved a scoped activation ApprovalRequest
- confirmed the activation approval had an exact-once consumption marker
- applied the guarded Gate policy patch for
  `siteops.browser_skill_candidate.apply_trusted_artifacts`
- wrote the inactive trusted Browser Skill artifact
- wrote the inactive SiteOps Skill Card artifact
- updated the post-Gate verifier so an operator-reviewed allowlist state is
  acceptable evidence instead of a stale failure
- reran live activation evidence closeout

No browser/CDP replay, provider call, Agent Bus enqueue, activation record,
canonical ChaseOS writeback, public posting, credential access, cookie/session
inspection, or Hermes authority expansion occurred.

## Key Live Evidence

Approved bound source approval:

```text
approval_siteops_candidate_bound_replacement_candidate-browser-runtime-20260430-022607-exampl_976914bf1181_browser_skill_candidate_promote
```

Activation approval:

```text
approval_siteops_activation_approval_20260503_202025_cbde7fb93c_siteops_browser_skill_candidate_activate_trusted_artifact
```

Activation-consumption marker:

```text
07_LOGS/SiteOps-Activation-Consumers/local/default/activation_consumer_candidate-browser-runtime-20260430-022607-exampl_141ecb2d12be.json
```

Gate allowlist approval:

```text
approval_siteops_gate_allowlist_20260503_202536_aea0c83e99_browser_skill_candidate_gate_allowlist_approval_request
```

Applied Gate operation:

```text
siteops.browser_skill_candidate.apply_trusted_artifacts
```

Inactive trusted Browser Skill artifact:

```text
runtime/browser_skills/skills/example-com.observed_shadow_flow.yaml
```

Inactive SiteOps Skill Card artifact:

```text
runtime/siteops/registry/skill_cards/example-com.observed_shadow_flow.json
```

## Current Closeout Result

`live-activation-evidence-closeout` now reports the live chain as still blocked,
but the remaining blockers are narrower:

- `activation_gate_allowance`: the activation Gate operation
  `siteops.browser_skill_candidate.activate_trusted_artifact` is not allowlisted
- `activation_executor_dry_run`: currently blocked by the activation Gate denial
- `browser_replay_shadow_mode`: trusted browser replay remains not built

## Status

Backend activation proof before browser replay now has an estimated **1 major
pass** remaining: activation Gate allowance plus activation executor dry-run or
activation-record evidence, if the operator approves that Gate path.

Full Browser Skill promotion pipeline still has an estimated **5-7 major
passes** remaining if browser replay/shadow execution, browser-run provenance,
trusted replay evidence, UI/operator review, and production hardening are in
scope.

The separate SiteOps Browser Skill promotion pipeline chat should assume **4-6
major passes** remain unless it has already produced repo-backed browser replay
evidence not visible in this pass.

## Hermes Boundary

Hermes remains a bounded reviewer/shadow evaluator only. This pass did not give
Hermes SiteOps runtime ownership, canonical writeback authority, browser
execution authority, secret access, Gate bypass authority, or approval
authority.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
