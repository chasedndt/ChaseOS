# ChaseOS Pulse Personal Map Visualization Contract

**Status:** COMPLETE TARGETED / READ-ONLY VISUALIZATION CONTRACT  
**Date:** 2026-05-03  
**Runtime:** Codex  
**Phase:** Phase 10 Pulse Personal Map surface foothold  
**Scope:** First local-only visualization contract for Personal Map lanes and pending candidates.

## Purpose

This pass gives ChaseOS Pulse a first Personal Map visualization surface without
turning the Personal Map into an automatic profile writer.

The contract renders:

- declared Personal Map lanes from `06_AGENTS/Personal-Map-Architecture.md`
- pending Personal Map node and edge candidates from the existing candidate
  store
- candidate queue posture
- disconnected candidate-edge warnings
- memory/runtime readiness status
- explicit blocked authority

It is a visualization contract, not applied Personal Map state.

## Runtime Surface

Runtime module:

```text
runtime/pulse/personal_map_visualization.py
```

CLI:

```powershell
python -m chaseos pulse personal-map-visualization --json
python -m chaseos pulse personal-map-visualization --write --json
```

Default write target:

```text
07_LOGS/Pulse-Decks/personal-map/YYYY-MM-DD-personal-map-visualization.html
```

The command is dry-run by default. `--write` writes only the static HTML
visualization artifact under the Pulse log tree.

## Current Repo Evidence

The live contract currently reports:

- declared Personal Map lanes: 11
- accepted Personal Map nodes: 0
- accepted Personal Map edges: 0
- applied Personal Map graph present: false
- pending Personal Map candidates: 0
- memory/runtime readiness: partial

This is correct for the current repo state. The Personal Map schema and
candidate store exist, but applied profile graph persistence and interactive
review UI are not built.

## Governance Boundary

The visualization contract does not:

- apply Personal Map candidates
- mutate Personal Map state
- approve memory
- create tasks
- edit `00_HOME/Now.md`
- edit Project-OS files
- update Runtime Brains
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- write canonical knowledge
- update the R&D workbook

## Relationship To Other Maps

This surface preserves the existing map separation:

| Map | Role |
|---|---|
| Vault Map | where ChaseOS files, logs, docs, and runtime surfaces live |
| Personal Map | who the user is, what domains matter, what goals/projects/cadences exist |
| Runtime Navigation Map | how a specific runtime has learned to navigate ChaseOS safely |

The visualization may link to Vault Map paths as evidence, but it does not
replace Vault Map or grant runtime navigation authority.

## Remaining Work

This pass does not complete the full Personal Map product surface.

Remaining work:

- accepted Personal Map graph persistence after review
- operator review UI for Personal Map candidates
- graph layout inside the future Pulse/Studio product shell
- node inspector and evidence drilldown
- governed apply path for approved profile updates
- conflict/drift visualization between Personal Map, Now, and project truth

Graph links:
[[Personal-Map-Architecture]] -
[[ChaseOS-Pulse-Visual-Card-Deck-Shell]] -
[[ChaseOS-Pulse-Final-Product-Readiness-Audit]] -
[[ChaseOS-Pulse-Completion-Tracker]] -
[[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
