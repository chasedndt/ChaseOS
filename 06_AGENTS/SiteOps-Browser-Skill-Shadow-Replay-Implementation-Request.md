---
title: SiteOps Browser Skill Shadow Replay Implementation Request
type: implementation-evidence
status: COMPLETE TARGETED / IMPLEMENTATION REQUEST READY / NO-WRITE
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Replay Implementation Request

This pass adds the no-write implementation-request surface for the future
Browser Skill shadow replay runner.

It does not implement or run browser replay.

## Command

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-replay-implementation-request <candidate_id> --source-approval-id <id> --activation-approval-id <id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## Live Local Result

For `candidate_browser_runtime_20260430_022607_example-com`, the command now
returns:

```text
browser_skill_shadow_replay_implementation_request_status: browser_skill_shadow_replay_implementation_request_ready_no_write
review_decision: ready_for_shadow_replay_implementation_approval_next_pass
backend_activation_ready: true
browser_replay_ready: false
browser_replay_built: false
```

## Request Packet

The command packages a future implementation request with:

- `request_type`: `siteops_browser_skill_shadow_replay_implementation_request`
- `requested_action`: `implement_browser_skill_shadow_replay_runner`
- `required_operator_decision`: `approve_future_shadow_replay_implementation_pass`
- `future_command_name`: `browser-skill-shadow-replay`
- `future_required_mode`: `shadow`
- `future_required_flags`: `--shadow-mode`, `--write-browser-run-log`

The future write set is declared but not written:

- `07_LOGS/Browser-Runs/siteops-shadow-replay-<candidate>.json`
- `07_LOGS/Agent-Activity/<YYYY-MM-DD>-siteops-shadow-replay-<candidate>.md`
- `03_INPUTS/Browser-Skill-Candidates/<domain>/shadow-replay-<candidate>.md`
- scoped activation record path reference
- Browser Skill artifact reference
- SiteOps Skill Card artifact reference

## Record Schema Boundary

The request schema requires tenant/workspace/user/candidate/approval scoping and
forbids secret or browser-session material.

Forbidden fields include:

- `cookie`
- `token`
- `secret`
- `password`
- `browser_session_state`
- `personal_account_state`
- `api_key`
- `oauth`

## Boundary

This pass did not:

- write the implementation request artifact
- write Browser Run logs
- write Agent Activity evidence for a replay run
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

Backend activation no-write readiness is complete. The shadow replay design and
implementation-request surfaces are ready. The remaining replay lane needs an
operator approval/pass before any shadow replay runner implementation is added.

Next recommended pass:

```text
siteops-browser-skill-shadow-replay-implementation-approval
```

Optional pre-replay pass:

```text
siteops-candidate-explicit-activation-write
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
