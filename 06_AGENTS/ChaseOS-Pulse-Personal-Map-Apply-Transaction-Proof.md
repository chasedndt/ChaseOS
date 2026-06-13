# ChaseOS Pulse Personal Map Apply Transaction Proof

**Status:** COMPLETE TARGETED / PROOF-ONLY TRANSACTION PACKET  
**Date:** 2026-05-03  
**Runtime:** Codex  
**Feature lane:** ChaseOS Pulse Phase 10 Personal Map apply depth

## Purpose

This pass adds an auditable transaction packet around the existing governed
Personal Map apply lane. The prior surface showed whether approved Personal Map
candidates were ready. This surface packages the exact ready decisions,
planned runtime-memory write target, graph before-state counts/hash, and
idempotency keys before any operator-approved live apply.

Command:

```text
chaseos pulse personal-map-apply-transaction-proof --json
chaseos pulse personal-map-apply-transaction-proof --write-proof --json
```

Implementation:

```text
runtime/pulse/personal_map_apply_transaction_proof.py
runtime/pulse/test_personal_map_apply_transaction_proof.py
```

Optional proof artifact:

```text
07_LOGS/Pulse-Decks/personal-map-apply-transactions/
```

## Evidence Read

The transaction proof reads:

- Personal Map candidate logs
- Pulse review decision logs
- the existing Personal Map live-apply proof surface
- the dry-run apply preview from `runtime/pulse/candidate_apply.py`
- `runtime/memory/personal-map/graph.json` metadata/hash when present
- the Pulse apply registry

## What It Proves

For each ready Personal Map candidate, the packet records:

- `transaction_entry_id`
- `decision_id`
- `candidate_id`
- candidate/target type
- planned write target
- idempotency key
- whether the decision is already applied

The current workspace can therefore review the exact transaction shape before
running the separate live apply command.

## Authority Boundary

This surface does not:

- run live apply
- mutate `runtime/memory/personal-map/graph.json`
- approve memory
- execute approvals
- edit `00_HOME/Now.md`
- edit Project-OS files
- write `02_KNOWLEDGE/`
- update Runtime Brains
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- update the R&D workbook

`--write-proof` writes only a proof JSON artifact under the Pulse Decks log
tree.

## Status Truth

This closes the missing transaction-proof layer for Personal Map apply. It does
not claim that a live Personal Map apply happened in the current workspace.
Live apply remains a separate explicit operator action through:

```text
chaseos pulse apply-decisions --kind personal_map --live
```

Current remaining Personal Map product work is either:

- an operator-approved live apply using real repo-local approved candidates, or
- explicit deferral if no real Personal Map candidate should be applied yet.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
