---
title: ChaseOS Pulse Runtime Brain Dashboard Contract
type: implementation-note
status: complete-targeted
created: 2026-05-02
updated: 2026-05-03
runtime: Codex
feature: ChaseOS Pulse
phase: Phase 10 Studio contract over Phase 9 Pulse memory/runtime substrate
---

# ChaseOS Pulse Runtime Brain Dashboard Contract

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

## Status

`runtime/studio/runtime_brain_dashboard.py` and:

```text
chaseos studio runtime-brain-dashboard --json
chaseos studio runtime-brain-dashboard --runtime <runtime_id> --json
```

provide a read-only Studio contract for the future Runtime Brain dashboard.

This is not the full visual dashboard. It is the backend/UI contract that lets
Studio render current AgentHub and Runtime Brain posture without taking
authority over runtime memory.

## Pulse Visual Surface Addendum

As of 2026-05-03, `runtime/pulse/runtime_brain_visualization.py` and:

```text
chaseos pulse runtime-brain-visualization --write --json
```

render this contract into a static local Pulse HTML artifact under
`07_LOGS/Pulse-Decks/runtime-brains/`.

The Studio contract remains the source model. The Pulse visual surface does not
add apply buttons, runtime memory mutation, Agent Bus writes, permission
expansion, provider calls, schedule activation, or canonical writeback.

## What It Reads

The contract composes:

- `runtime.pulse.memory_runtime_readiness`
- runtime profiles from `runtime/memory/adapters/*/profile.json`
- Agent Identity Ledgers from `runtime/memory/adapters/*/identity-ledger.json`
- Runtime Navigation Maps from `runtime/memory/nav/*/nav-map.json`
- Execution Repair Memory from `runtime/memory/repair/*.json`
- runtime scorecards from `runtime/memory/scorecards/*.json`

It reports runtime cards for the available runtime memory families and can be
filtered to one runtime with `--runtime`.

## Dashboard Model

The model includes:

- source Pulse memory/runtime readiness summary
- runtime counts and ready/partial posture
- missing runtime-memory family counts
- drift signal counts
- execution repair incident candidate counts
- per-runtime profile summary
- per-runtime identity ledger posture
- per-runtime navigation map counts
- per-runtime execution repair memory counts
- scorecard aggregates
- non-executing action hints for operator review

## Authority Boundary

The contract is read-only and local-only.

It does not:

- update Runtime Brains
- update Runtime Navigation Maps
- update Agent Identity Ledgers
- apply Execution Repair Memory candidates
- apply feedback rules
- mutate the Personal Map
- expand runtime permissions
- activate self-upgrade
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- write canonical state
- update the R&D workbook

## Current Repo Evidence

As of this pass, the live repo smoke reports the Runtime Brain dashboard
contract as partial because the runtime memory substrate is intentionally
incremental:

- Hermes: ready
- OpenClaw: ready
- Archon: partial, missing repair memory
- Claude: partial, missing navigation and repair memory

This is useful product signal, not a failure. The dashboard contract exposes
the current truth without inventing missing runtime brain state.

## Phase Boundary

This pass belongs to the Phase 10 Studio contract lane, but it depends on the
Phase 9 Pulse/AgentHub memory substrate.

The follow-on Phase 10 product work should focus on:

```text
approval queue UI
applied Personal Map review/apply surface
broader Pulse/Studio integration
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
