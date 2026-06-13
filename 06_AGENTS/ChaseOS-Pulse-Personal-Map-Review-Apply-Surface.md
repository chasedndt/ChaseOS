# ChaseOS Pulse Personal Map Review Apply Surface

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** COMPLETE TARGETED / STATIC REVIEW-APPLY SURFACE  
**Date:** 2026-05-03  
**Runtime:** Codex  
**Phase:** Phase 10 Pulse Personal Map surface foothold  
**Scope:** Local-only Personal Map candidate review/apply visibility over the existing governed apply lane.

## Purpose

This pass adds a focused Personal Map surface between the first visualization
contract and the existing `candidate_apply` runtime-memory writer.

It shows:

- pending Personal Map candidates
- latest persisted Personal Map review decisions
- dry-run apply preview for `personal_map` candidates
- current runtime-memory Personal Map graph status
- the separate governed live apply command
- explicit blocked authority

This is not a new apply mechanism. It is a UI/runtime surface over the existing
governed apply lane.

## Runtime Surface

Runtime module:

```text
runtime/pulse/personal_map_review_apply.py
```

CLI:

```powershell
python -m chaseos pulse personal-map-review-apply --json
python -m chaseos pulse personal-map-review-apply --write --json
```

Default artifact:

```text
07_LOGS/Pulse-Decks/personal-map-review/YYYY-MM-DD-personal-map-review-apply.html
```

The command is dry-run by default. `--write` writes only the static HTML surface
under the Pulse log tree.

## Apply Boundary

The surface may display this governed command:

```powershell
python -m chaseos pulse apply-decisions --kind personal_map --live
```

The surface does not execute it. Live apply remains explicit and separate.
When used, the existing apply lane writes approved Personal Map candidates only
to:

```text
runtime/memory/personal-map/graph.json
```

That graph is runtime memory, not canonical knowledge or a mutation of
`00_HOME/Personal-Map.md`.

## Current Repo Evidence

Current live repo state at this pass:

- Personal Map candidate logs: none present
- Personal Map review decisions: none present
- applied Personal Map runtime graph: not present
- feedback apply registry exists for the prior Hermes feedback decision only

This is expected. The surface is now ready to show and preview Personal Map
candidate application when approved Personal Map candidates exist.

## Governance Boundary

The review/apply surface does not:

- run live apply
- apply Personal Map candidates
- approve memory
- create tasks
- edit `00_HOME/Now.md`
- edit Project-OS files
- write `02_KNOWLEDGE/`
- update Runtime Brains
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- mutate canonical state
- update the R&D workbook

## Relationship To Existing Surfaces

| Surface | Role |
|---|---|
| `personal-map-visualization` | visualizes declared lanes and pending candidates |
| `candidate_apply` | guarded runtime-memory writer for approved candidate decisions |
| `personal-map-review-apply` | static review/apply visibility surface over the Personal Map lane |
| Approval Queue UI | broader queue for all candidate/review lanes |
| [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]] | Phase 10 UI contract that generalizes review/apply preview and gated non-canonical apply boundaries across feedback, Personal Map, and execution repair candidates |

## Remaining Work

This pass does not complete the full Personal Map product surface.

Remaining work:

- real approved Personal Map candidate proof from live runtime review
- optional operator confirmation UI around the separate live apply command
- implementation of the broader governed feedback review/apply panel specified
  in [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]
- graph layout inside the future Pulse/Studio shell
- node inspector and evidence drilldown for applied runtime graph nodes
- conflict/drift visualization between Personal Map, Now, and project truth

Graph links:
[[Personal-Map-Architecture]] -
[[ChaseOS-Pulse-Personal-Map-Visualization-Contract]] -
[[ChaseOS-Pulse-Approval-Queue-UI]] -
[[ChaseOS-Pulse-Final-Product-Readiness-Audit]] -
[[ChaseOS-Pulse-Completion-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
