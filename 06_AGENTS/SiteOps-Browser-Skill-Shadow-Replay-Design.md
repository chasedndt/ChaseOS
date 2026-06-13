---
title: SiteOps Browser Skill Shadow Replay Design
type: implementation-evidence
status: COMPLETE TARGETED / NO-EXECUTION DESIGN READY
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Replay Design

This pass completes the no-execution Browser Skill shadow replay design surface
for the SiteOps candidate pipeline.

It does not run a browser.

## Command

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-replay-design <candidate_id> --source-approval-id <id> --activation-approval-id <id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## Live Local Result

For `candidate_browser_runtime_20260430_022607_example-com`, the command now
returns:

```text
browser_skill_shadow_replay_design_status: browser_skill_shadow_replay_design_ready_no_execution
backend_activation_ready: true
remaining_backend_activation_blockers: []
remaining_feature_blockers: [browser_replay_shadow_mode]
review_decision: ready_for_shadow_replay_implementation_request_next_pass
```

## Design Requirements

- Shadow mode must come before any live browser write/action mode.
- Initial replay must use a local or operator-allowlisted target.
- Authenticated browser sessions require separate explicit approval.
- Initial replay should use an isolated or throwaway browser profile.
- Browser skills must not contain secrets, cookies, tokens, or personal account
  state.
- Browser observations remain untrusted until human review.
- Browser tasks must emit scoped Browser Run and Agent Activity evidence before
  any future trusted replay claim.
- Replay outputs are candidate evidence, not canonical truth.
- No DOM mutation, form submission, or external write is allowed in this design
  pass.

## Boundary

This pass did not:

- activate trusted artifacts
- set `activation_allowed=true`
- write activation records or activation audits
- write Browser Run logs
- mutate Browser Skill or SiteOps Skill Card artifacts
- launch browser/CDP automation
- inspect authenticated sessions
- read cookies, tokens, or secrets
- enqueue Agent Bus work
- call providers or paid APIs
- mutate Gate policy
- grant Hermes SiteOps runtime authority
- write canonical ChaseOS memory/state

Hermes remains a bounded reviewer/shadow evaluator only.

## Current Status

Backend activation no-write readiness is complete, and shadow replay design is
ready. Browser replay implementation/proof remains future work.

Next recommended pass:

```text
siteops-browser-skill-shadow-replay-implementation-request
```

Optional pre-replay pass:

```text
siteops-candidate-explicit-activation-write
```



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
