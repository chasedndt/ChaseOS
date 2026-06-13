---
title: Agent Bus Visual Inspection
type: runtime-inspection-guide
status: active
created: 2026-04-30
updated: 2026-04-30
runtime_surface: agent-bus
---

# Agent Bus Visual Inspection

This note is the Obsidian-openable inspection surface for the ChaseOS Agent Bus.
It does not replace the live SQLite bus state or the CLI; it gives the operator
a stable visual entry point with the exact commands and expected runtime nodes.

## Current Visual Options

| Surface | Status | Use |
|---|---|---|
| Obsidian note graph | Active | Open this note, [[Runtime-InterAgent-Coordination-Bus]], [[Agent-Registry]], [[Backends-Supported]], and runtime profiles to inspect the bus as linked nodes. |
| CLI JSON | Active | Use the commands below for live liveness, route, heartbeat, and queue state. |
| Markdown snapshots | Active | Use dated snapshots under `07_LOGS/Agent-Activity/` for readable point-in-time bus state. |
| ChaseOS Studio Runtime Cockpit | Planned / backend foothold only | The future visual runtime cockpit belongs to Phase 10 Studio. It is not a full GUI runtime inspector yet. |

## Runtime Nodes

| Runtime | Runtime Profile | Bus Role | Current Registration |
|---|---|---|---|
| Codex | [[Codex-Runtime-Profile]] | Bounded code/repo/test worker | Active bus worker `Codex`; retained instance name `Axiom-Codex`. |
| Hermes | [[Hermes-Runtime-Profile]] | Review/planning/shadow-audit runtime | Active runtime for `review`, `planning`, `shadow-audit`, and related coordination work. |
| OpenClaw | [[OpenClaw-Runtime-Profile]] | Operator synthesis / AOR runtime | Active runtime for operator briefing, scheduled briefing, source-pack builder, graph hygiene, and related coordination work. |

## Live Inspection Commands

Run from the repo root:

```powershell
cd <VAULT_ROOT>
python -m chaseos agent-bus status --json
python -m chaseos agent-bus runtimes --json
python -m chaseos agent-bus heartbeats --runtime Codex --json
python -m chaseos agent-bus heartbeats --runtime Hermes --json
python -m chaseos agent-bus heartbeats --runtime OpenClaw --json
python -m chaseos agent-bus route --task-type code.patch --json
python -m chaseos agent-bus route --task-type review --json
```

Refresh Codex before inspecting if you want it to show live without starting a
long-running worker:

```powershell
python -m chaseos agent-bus codex-daemon --once --executor mock --json
```

## What "Codex Added To The Bus" Means

Codex is considered added to the bus when all of these hold:

- `runtime/codex/capabilities.yaml` registers bus name `Codex`.
- `runtime/policy/adapters/codex.yaml` validates.
- [[Codex-Runtime-Profile]] exists and is linked from runtime hub surfaces.
- `python -m chaseos agent-bus runtimes --json` lists `Codex`.
- `python -m chaseos agent-bus route --task-type code.patch --json` recommends `Codex`.
- `python -m chaseos agent-bus heartbeats --runtime Codex --json` shows `Codex:Axiom-Codex` after a refresh.
- Codex remains bounded to `code.review`, `code.patch`, `repo.inspect`, and `test.run`.

## Current Boundary

This is an inspection surface, not a control surface. Do not edit SQLite state
or governed runtime state by hand. Use Agent Bus CLI commands and governed
runtime workflows for state changes.

## Latest Snapshot

- [[2026-04-30-agent-bus-runtime-inspection-snapshot]]

## Links

- [[Runtime-InterAgent-Coordination-Bus]]
- [[Agent-Registry]]
- [[Backends-Supported]]
- [[Codex-Runtime-Profile]]
- [[Hermes-Runtime-Profile]]
- [[OpenClaw-Runtime-Profile]]
