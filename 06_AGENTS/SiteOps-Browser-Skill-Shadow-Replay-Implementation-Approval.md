---
title: SiteOps Browser Skill Shadow Replay Implementation Approval
type: implementation-evidence
status: COMPLETE TARGETED / IMPLEMENTATION APPROVAL READY / NO-WRITE
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Replay Implementation Approval

This pass adds the no-write approve/reject intent surface for future Browser
Skill shadow replay implementation.

It does not implement or run browser replay.

## Command

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-replay-implementation-approval <candidate_id> --source-approval-id <id> --activation-approval-id <id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --decision approve --json
```

`--decision` is restricted to `approve` or `reject`.

## Live Local Result

For `candidate_browser_runtime_20260430_022607_example-com`, the approve smoke
returns:

```text
browser_skill_shadow_replay_implementation_approval_status: shadow_replay_implementation_approved_for_next_pass_no_write
review_decision: operator_intent_approve_shadow_replay_implementation_next_pass
ready_for_shadow_replay_implementation_next_pass: true
backend_activation_ready: true
browser_replay_built: false
```

## Approval Packet

The command returns a review-only packet with:

- `record_type`: `siteops_browser_skill_shadow_replay_implementation_approval`
- scoped `tenant_id`, `workspace_id`, and `user_id`
- actor and approve/reject decision
- source and activation approval references
- implementation-request reference
- future command name `browser-skill-shadow-replay`
- required mode `shadow`
- required flags `--shadow-mode` and `--write-browser-run-log`
- future Browser Run, Agent Activity, and candidate evidence paths

The approval packet is not written to disk in this pass.

## ID Safety Fix

The initial live smoke exposed that long candidate IDs could make the generated
request ID and approval ID collide after slug truncation. This pass fixed the
approval ID prefix so approval IDs remain distinct from request IDs, and added a
focused regression assertion.

## Boundary

This pass did not:

- write an implementation approval artifact
- write the implementation request artifact
- implement the shadow replay runner
- write Browser Run logs
- write Agent Activity replay evidence
- activate trusted artifacts
- write activation records or activation audits
- mutate Browser Skill or SiteOps Skill Card artifacts
- launch browser/CDP automation
- inspect authenticated sessions
- read cookies, tokens, secrets, or account state
- mutate DOM or submit forms
- enqueue Agent Bus work
- call providers or paid APIs
- mutate Gate policy
- grant Hermes SiteOps runtime authority
- write canonical ChaseOS memory/state

Hermes remains a bounded reviewer/shadow evaluator only.

## Current Status

Backend activation no-write readiness is complete. Shadow replay design,
implementation-request, and implementation-approval surfaces are ready. The
remaining replay lane is the guarded shadow replay runner/proof path.

Next recommended pass:

```text
siteops-browser-skill-shadow-replay-runner-write-guard
```

Optional pre-replay pass:

```text
siteops-candidate-explicit-activation-write
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
