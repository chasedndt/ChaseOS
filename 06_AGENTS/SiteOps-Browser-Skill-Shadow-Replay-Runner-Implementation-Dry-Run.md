---
title: SiteOps Browser Skill Shadow Replay Runner Implementation Dry Run
type: feature-evidence
status: COMPLETE TARGETED / DRY-RUN SHELL READY / NO BROWSER EXECUTION
phase: 9
date: 2026-05-04
runtime: Codex
---

# SiteOps Browser Skill Shadow Replay Runner Implementation Dry Run

This pass adds the dry-run shell for the future SiteOps Browser Skill shadow
replay runner.

## Current Result

`runtime/siteops/candidate_promotions.py` exposes
`candidate_promotion_browser_skill_shadow_replay_runner_implementation_dry_run`,
and the CLI exposes:

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-replay-runner-implementation-dry-run <candidate_id> --source-approval-id <id> --activation-approval-id <id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --target-url <url> --shadow-mode --json
```

Live local smoke for
`candidate_browser_runtime_20260430_022607_example-com` returned:

```text
browser_skill_shadow_replay_runner_dry_run_status: shadow_replay_runner_dry_run_ready_no_browser
ready_for_shadow_replay_runner_write_pass_next: true
target_policy_reason: local_loopback_target
runner_dry_run_shell_built: true
browser_replay_built: false
browser_run_log_written: false
runner_dry_run_artifact_written: false
browser_execution_allowed: false
cdp_connection_allowed: false
authenticated_session_allowed: false
canonical_writeback_allowed: false
```

## Dry-Run Contract

The dry-run shell validates:

- scoped tenant/workspace/user inputs
- source approval and activation approval evidence through the existing guard chain
- the runner write-guard contract
- `--shadow-mode`
- `--target-url`
- local loopback or operator-allowlisted domain posture
- secret-like URL marker rejection
- max-step bounds

It produces a Browser Run record preview and policy-decision plan, but writes no
artifacts.

## Boundary

This pass does not launch a browser, connect CDP, use authenticated sessions,
read profile state, read cookies/tokens/secrets/localStorage/sessionStorage,
mutate DOM, submit forms, write Browser Run logs, write Agent Activity replay
evidence, mutate trusted Browser Skill artifacts, mutate SiteOps Skill Cards,
activate skills, enqueue Agent Bus work, call providers, mutate Gate policy,
expand Hermes authority, or write canonical ChaseOS memory/state.

`--write-browser-run-log` is accepted by the parser only so the dry-run shell can
reject it explicitly with
`blocked_write_browser_run_log_not_supported_in_dry_run`.

## Next Pass

`siteops-browser-skill-shadow-replay-runner-write-pass`

That pass should add the separately guarded explicit Browser Run evidence writer
for the already-planned dry-run record. It should still avoid browser/CDP and
authenticated session execution unless a later operator-approved execution pass
exists.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
