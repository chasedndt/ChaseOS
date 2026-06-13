# ChaseOS Pulse Product Shell Integration

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** COMPLETE TARGETED / INTEGRATED STATIC PRODUCT SHELL  
**Date:** 2026-05-03  
**Runtime:** Codex  
**Phase:** Phase 10 Pulse product-surface integration  
**Scope:** First integrated local Pulse shell over the existing Phase 10 Pulse surfaces.

## Purpose

This pass gives ChaseOS Pulse one local product entry surface instead of a set
of separate static artifacts.

The shell composes:

- latest user Pulse deck
- visual card/deck shell model
- Personal Map visualization contract
- Personal Map review/apply surface
- Runtime Brain visualization contract
- Approval Queue UI model
- final product-readiness audit

It is still local and static. It does not become ChaseOS Studio, start a
server, open a browser, or execute actions.

## Runtime Surface

Runtime module:

```text
runtime/pulse/product_shell.py
```

CLI:

```powershell
python -m chaseos pulse product-shell --json
python -m chaseos pulse product-shell --write --json
```

Default artifact:

```text
07_LOGS/Pulse-Decks/product-shell/YYYY-MM-DD-pulse-product-shell.html
```

## Current Product Role

This surface is the first local Pulse product shell. It is useful as an
operator-facing artifact because it shows, in one place:

- whether the current v1 local lane is complete
- why full product-grade Pulse is still partial
- current deck card count and source deck
- Personal Map candidate/review/apply posture
- Runtime Brain and repair/drift posture
- approval lane posture
- blocked authority

## Governance Boundary

The product shell does not:

- start a server
- open a browser
- submit feedback
- grant or execute approvals
- apply candidates
- approve memory
- mutate Personal Map state
- update Runtime Brains
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- write canonical ChaseOS state
- update the R&D workbook

`--write` writes only the static HTML artifact under the Pulse deck log tree.

## Relationship To Studio

This is not the full ChaseOS Studio desktop shell. It is a static artifact that
the future Studio shell can mount or replace.

The next Studio/Pulse integration work should add:

- shell-panel mount inside the local Studio desktop shell
- route/navigation model between Pulse panels
- optional operator confirmation controls that still call governed backend
  commands instead of mutating state directly

2026-05-03 update: targeted browser visual QA for this artifact is now recorded
under `07_LOGS/Pulse-Decks/product-shell/2026-05-03-pulse-product-shell-browser-qa.md`.
The read-only Studio panel contract now lives in
`runtime/studio/pulse_product_shell_panel.py`. Actual Studio mounting is still
not built.

## Remaining Work

Full product-grade Pulse remains partial until:

- Personal Map live candidate review/apply proof exists
- the Pulse shell is mounted or reproduced inside Studio
- approval execution remains governed but becomes operator-usable
- Runtime Brain dashboard moves from static visualization to interactive
  inspect-only UI
- native schedule runner activation proof is explicitly approved and verified,
  if that lane is selected

Graph links:
[[ChaseOS-Pulse-Visual-Card-Deck-Shell]] -
[[ChaseOS-Pulse-Personal-Map-Visualization-Contract]] -
[[ChaseOS-Pulse-Personal-Map-Review-Apply-Surface]] -
[[ChaseOS-Pulse-Runtime-Brain-Visual-UI]] -
[[ChaseOS-Pulse-Approval-Queue-UI]] -
[[ChaseOS-Pulse-Final-Product-Readiness-Audit]] -
[[ChaseOS-Pulse-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
