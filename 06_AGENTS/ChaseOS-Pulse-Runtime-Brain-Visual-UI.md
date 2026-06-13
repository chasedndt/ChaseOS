---
title: ChaseOS Pulse Runtime Brain Visual UI
type: implementation-note
status: complete-targeted
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
feature: ChaseOS Pulse
phase: Phase 10 local visual surface
---

# ChaseOS Pulse Runtime Brain Visual UI

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

## Status

`runtime/pulse/runtime_brain_visualization.py` and:

```text
chaseos pulse runtime-brain-visualization --json
chaseos pulse runtime-brain-visualization --runtime <runtime_id> --json
chaseos pulse runtime-brain-visualization --write --json
```

provide the first local-only static Runtime Brain visualization surface for
ChaseOS Pulse.

This is not the full interactive Runtime Brain dashboard. It is a static HTML
artifact over the existing read-only Studio Runtime Brain dashboard contract.

## What It Reads

The surface composes `runtime/studio/runtime_brain_dashboard.py`, which already
reads:

- Pulse memory/runtime readiness
- runtime profiles
- Agent Identity Ledgers
- Runtime Navigation Maps
- Execution Repair Memory
- runtime scorecards

The Pulse visualizer does not introduce a second datastore. It only converts
that contract into a visualization packet and optional HTML artifact.

## What It Renders

The generated model and HTML show:

- dashboard status
- runtime card count
- missing runtime-memory family count
- drift signal count
- execution repair candidate count
- non-executing action hint count
- per-runtime profile role
- strengths and known weaknesses
- runtime navigation counts
- scorecard compliance summary
- blocked authority

The artifact path is:

```text
07_LOGS/Pulse-Decks/runtime-brains/YYYY-MM-DD-runtime-brain-visualization.html
07_LOGS/Pulse-Decks/runtime-brains/YYYY-MM-DD-runtime-brain-<runtime_id>.html
```

Artifacts are written only when `--write` is passed.

## Authority Boundary

This surface is read-only and local-only.

It does not:

- update Runtime Brains
- update Runtime Navigation Maps
- update Agent Identity Ledgers
- apply Execution Repair Memory
- apply feedback rules
- apply Personal Map candidates
- grant permissions
- activate self-upgrade
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- write canonical state
- update the R&D workbook

## Product Boundary

This pass moves Pulse closer to Phase 10 product-grade visibility by giving the
operator a concrete local Runtime Brain surface. It remains a static proof
surface, not a full dashboard with review, apply, repair, permission, or
approval flows.

Full product-grade Pulse still needs the approval queue UI, applied Personal
Map review/apply surface, native schedule runner activation proof if separately
approved, and broader Pulse/Studio integration.

## Graph Links

[[ChaseOS-Pulse-Architecture]] - [[ChaseOS-Pulse-Runtime-Brain-Dashboard-Contract]] - [[ChaseOS-Pulse-Memory-Runtime-Readiness]] - [[ChaseOS-Pulse-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
