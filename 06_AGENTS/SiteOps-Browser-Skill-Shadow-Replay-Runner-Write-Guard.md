---
title: SiteOps Browser Skill Shadow Replay Runner Write Guard
type: feature-evidence
status: COMPLETE TARGETED / WRITE GUARD READY / NO BROWSER EXECUTION
phase: 9
date: 2026-05-04
runtime: Codex
---

# SiteOps Browser Skill Shadow Replay Runner Write Guard

This pass completes the no-execution write-guard contract for the future
SiteOps Browser Skill shadow replay runner.

## Current Result

`runtime/siteops/candidate_promotions.py` exposes
`candidate_promotion_browser_skill_shadow_replay_runner_write_guard`, and the
CLI exposes:

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-replay-runner-write-guard <candidate_id> --source-approval-id <id> --activation-approval-id <id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

Live local smoke for
`candidate_browser_runtime_20260430_022607_example-com` returned:

```text
browser_skill_shadow_replay_runner_write_guard_status: shadow_replay_runner_write_guard_ready_no_write
ready_for_shadow_replay_runner_implementation_next_pass: true
backend_activation_ready: true
browser_replay_built: false
runner_write_guard_artifact_written: false
browser_run_log_written: false
browser_launch_allowed: false
cdp_connection_allowed: false
authenticated_session_allowed: false
canonical_writeback_allowed: false
```

## Guard Contract

Future runner implementation must fail closed unless it has:

- an approved no-write implementation approval intent
- `--shadow-mode`
- `--write-browser-run-log`
- `--target-url`
- scoped Browser Run evidence path
- scoped Agent Activity path
- scoped candidate evidence path
- local or operator-allowlisted target posture

Future allowed write roots are limited to:

- `07_LOGS/Browser-Runs/<tenant>/<workspace>/`
- `07_LOGS/Agent-Activity/<tenant>/<workspace>/`
- `03_INPUTS/Browser-Skill-Candidates/`

Future forbidden write targets include:

- `runtime/chaseos_gate.py`
- `runtime/policy/gateway_allowlists.json`
- `runtime/browser_skills/skills/**`
- `runtime/siteops/registry/skill_cards/**`
- protected current-state docs
- canonical memory/state
- cookies, tokens, secrets, credentials, and browser session state

## Boundary

This pass did not implement or run the replay runner. It did not write Browser
Run logs, Agent Activity replay evidence, activation records/audits, trusted
artifacts, approval decisions, Gate policy, or canonical ChaseOS state. It did
not launch browser/CDP, use authenticated sessions, read profile state, mutate
DOM, submit forms, enqueue Agent Bus work, or call providers.

## Next Pass

`siteops-browser-skill-shadow-replay-runner-implementation-dry-run`

That pass should implement a dry-run runner shell that still rejects
`--write-browser-run-log` until a separately guarded write pass is approved.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
