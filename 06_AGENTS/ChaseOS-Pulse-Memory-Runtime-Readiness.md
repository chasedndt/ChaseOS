---
title: ChaseOS Pulse Memory Runtime Readiness
status: COMPLETE TARGETED / READ-ONLY
created: 2026-05-02
runtime: Codex
---

# ChaseOS Pulse Memory Runtime Readiness

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

This pass adds a read-only Pulse readiness contract for the Context Memory Core
and AgentHub runtime memory substrate.

It is not a memory writer, approval executor, runtime dispatcher, or schedule
activation surface.

## Purpose

`runtime/pulse/memory_runtime_readiness.py` answers one bounded question:

> Are the current Pulse memory, feedback, Personal Map candidate, runtime
> profile, identity ledger, runtime navigation, execution repair, and runtime
> brain evidence surfaces visible enough for the next product-grade Pulse
> passes?

The surface composes existing repo-local evidence only:

- `runtime/memory/inspector.py`
- `runtime/memory/adapters/*/profile.json`
- `runtime/memory/adapters/*/identity-ledger.json`
- `runtime/memory/nav/*/nav-map.json`
- `runtime/memory/repair/*.json`
- `runtime/memory/scorecards/*.json`
- `runtime/memory/feedback-rules/accepted-signals.jsonl`
- `07_LOGS/Pulse-Decks/memory-candidates/personal-map/*.jsonl`
- `07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/*/*.jsonl`
- `runtime/agents/runtime_brain.py`
- `runtime/agents/agent_hub.py`
- `runtime/agents/execution_repair_memory.py`

## CLI

```powershell
chaseos pulse memory-runtime-readiness --json
```

The command returns a local readiness packet with:

- `readiness_status`
- memory posture
- lane counts
- runtime cards
- runtime family counts
- feedback rule counts
- Personal Map candidate counts
- execution repair candidate counts
- validation error counts
- blocked authority flags

## Lanes

The readiness contract exposes all of these lanes:

| Lane | Meaning |
|---|---|
| `context_memory_core` | Layer C/D memory summary and validation posture |
| `personal_map_candidates` | Pending Personal Map candidates surfaced by Pulse |
| `feedback_rules` | Accepted feedback signal records |
| `runtime_profiles` | Runtime profile files |
| `runtime_identity_ledgers` | Agent identity ledger files |
| `runtime_navigation_maps` | Runtime navigation map files |
| `execution_repair_memory` | Existing repair memory plus pending repair candidates |
| `runtime_brain_readiness` | Per-runtime brain substrate completeness |

## Boundaries

This surface explicitly blocks:

- memory mutation
- feedback rule application
- Personal Map candidate application
- execution repair candidate application
- runtime brain updates
- permission grants
- Agent Bus task writes
- runtime dispatch
- provider or connector calls
- schedule activation
- memory approval
- canonical writeback
- second datastore creation
- R&D workbook updates

## Current Status

This is complete for the targeted read-only readiness contract.

It does not complete the runtime brain dashboard, Personal Map visualization,
approval queue UI, automatic runtime repair application, schedule activation,
or autonomous memory approval.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
