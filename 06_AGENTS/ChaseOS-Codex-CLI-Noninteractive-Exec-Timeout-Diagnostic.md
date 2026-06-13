---
title: ChaseOS Codex CLI Noninteractive Exec Timeout Diagnostic
type: runtime-proof
status: COMPLETE / LIVE READ-ONLY CODEX BUS OUTPUT VERIFIED
created: 2026-05-13
updated: 2026-05-13
runtime: Codex
session_descriptor: codex-cli-noninteractive-exec-timeout-diagnostic
---

# ChaseOS Codex CLI Noninteractive Exec Timeout Diagnostic

## Summary

The previous Agent Bus lifecycle proof showed bus mechanics were working, but the live Codex CLI task `task-1562dc3450f3` blocked after `codex exec --skip-git-repo-check --ephemeral --sandbox read-only -` timed out.

This pass narrowed and cleared that blocker for simple read-only bus tasks.

## Diagnosis

Direct Codex CLI smoke tests showed the CLI itself was functional when run outside the filesystem sandbox:

- `codex exec --skip-git-repo-check --ephemeral --sandbox read-only "Return exactly READY."` returned `READY`.
- `Write-Output "Return exactly READY." | codex exec --skip-git-repo-check --ephemeral --sandbox read-only -` returned `READY`.

The sandboxed direct run failed with `.codex` temp/app-server access errors, confirming live Codex CLI probes need an elevated/local runtime boundary.

The daemon-specific issue was prompt shape: the daemon wrote `codex-task-packet.json` and told nested Codex to read that file, while the prompt also discouraged shell commands. For no-write read-only tasks, nested Codex could be forced to use a shell command just to discover the request.

## Change

`runtime/adapters/codex/daemon.py` now embeds the bounded task packet JSON directly in the stdin prompt and still writes the packet artifact to `codex-task-packet.json`.

The prompt now states:

- use the embedded packet as source of truth,
- run shell commands only when allowed and needed for bounded read-only inspection or requested tests,
- do not edit files unless the task asks for edits and declares allowed write paths,
- keep empty `allowed_write_paths` as a hard no-write packet.

## Live Proof

Fresh Agent Bus task:

- Task id: `task-e417a38df4d0`
- Run id: `run-1685f32c`
- Work fingerprint: `codex-cli-noninteractive-postfix-proof-20260513`
- Final status: `done`
- Owner: `Codex`
- Owner instance: `Axiom-Codex`
- Adapter event type: `proposal`

Live daemon command:

```powershell
python -m chaseos agent-bus codex-daemon --once --executor codex --timeout-seconds 180 --json
```

Live output artifact:

- `runtime/adapters/codex/runs/20260513T104717Z-task-e417a38df4d0/codex-stdout.md`

The nested Codex output confirmed it received the inline bounded packet, made no file edits, ran no shell commands, and returned a text-only result.

## Verification

Targeted adapter tests:

```powershell
python -m pytest runtime\adapters\codex\test_codex_daemon_command.py runtime\adapters\codex\test_codex_daemon.py -q --basetemp C:\tmp\chaseos-codex-daemon-pytest-temp\basetemp -p no:cacheprovider
```

Result: `21 passed`.

Agent Bus status after live proof:

- `task_count=291`
- `open_count=42`
- `claimed_count=0`
- `in_progress_count=0`
- `blocked_count=2`
- `done_count=16`
- `expired_count=113`

## Boundary Result

No provider setup was changed. No secret values were read or written. No browser action, system-control action, workflow dispatch, VentureOps run, Pulse memory mutation, Personal Map mutation, R&D truth-state mutation, Gate/Git/host/release/payment/CRM/marketplace mutation, or canonical ChaseOS mutation occurred.

## Current MVP Interpretation

The Codex Agent Bus live read-only path is now:

`COMPLETE FOR SIMPLE LIVE READ-ONLY OUTPUT`

The earlier blocked task `task-1562dc3450f3` remains blocked as historical timeout evidence. The original Chat runtime-dispatch task `chat-runtime-dispatch-ec40d576ce3940c3b3d2` remains correctly policy-blocked because its task packet explicitly set `allow_live_subprocess=false`.

The next MVP blocker is no longer this timeout. The next practical P0 pass is:

`credential-readiness-repair`

That pass should repair/validate provider secret references without exposing secret values.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
