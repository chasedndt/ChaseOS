# ChaseOS Pulse Visual Card Deck Shell

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** COMPLETE TARGETED / LOCAL STATIC SHELL  
**Date:** 2026-05-03  
**Runtime:** Codex  
**Phase:** Phase 10 Pulse visual UI foothold  
**Scope:** First local-only visual Pulse card/deck shell over existing Pulse backend contracts.

## Product Boundary

The visual card deck shell is the first Phase 10 ChaseOS Pulse surface. It is
not the full ChaseOS Studio desktop, not a live provider surface, not a
schedule runner, and not an approval executor.

It renders existing repo-local Pulse evidence into one static HTML artifact:

- latest user Pulse deck from `07_LOGS/Pulse-Decks/users/`
- final product-readiness audit summary
- approval-center readiness summary
- Context Memory Core / AgentHub readiness summary
- Runtime Brain dashboard contract summary
- current Pulse cards, evidence, recommended actions, and blocked authority

The shell is separate from the broader ChaseOS Studio development lane. It can
be mounted or absorbed by Studio later, but this pass keeps the Pulse UI surface
local and standalone.

## Runtime Surface

Runtime module:

```text
runtime/pulse/visual_card_deck_shell.py
```

CLI:

```powershell
python -m chaseos pulse visual-card-deck-shell --json
python -m chaseos pulse visual-card-deck-shell --write --json
```

Default write target:

```text
07_LOGS/Pulse-Decks/users/<source-deck-stem>.visual-shell.html
```

The command is dry-run by default. `--write` writes only the static HTML shell
inside the user Pulse deck archive.

## Governance Boundary

The shell is read-only except for the explicit HTML artifact write. It does
not:

- submit feedback
- apply feedback candidates
- approve memory
- mutate Context Memory Core state
- mutate the Personal Map
- update Runtime Brains
- grant permissions
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- create a second datastore
- write canonical knowledge
- update the R&D workbook

Candidate-only feedback remains in the existing Pulse local app and review
pipeline. This shell only visualizes current cards and governance posture.

## Adopted UI Shape

The first shell is static HTML rather than a full app. It provides:

- deck metrics
- current product-readiness status
- remaining Phase 10 product lanes
- approval-center readiness cards
- memory/runtime readiness metrics
- Runtime Brain summary cards
- Pulse card rendering with evidence and recommended actions
- blocked-authority summary

This gives Pulse a visual product foothold while keeping all mutation paths
behind existing governed review and approval lanes.

## Live Verification

Live command:

```powershell
python -m chaseos pulse visual-card-deck-shell --write --json
```

Observed output artifact:

```text
07_LOGS/Pulse-Decks/users/2026-05-02-pass1-signal-user-pulse-signal.visual-shell.html
```

Focused tests:

```powershell
python -m pytest runtime/pulse/test_visual_card_deck_shell.py runtime/pulse/test_final_product_readiness_audit.py runtime/pulse/test_post_completion_hardening.py runtime/pulse/test_completion_status.py runtime/studio/test_runtime_brain_dashboard.py runtime/pulse/test_memory_runtime_readiness.py runtime/tests/test_cli_command_contract.py -q
```

Result:

```text
42 passed, 18 subtests passed
```

## Remaining Phase 10 Pulse Lanes

This pass reduces the remaining visual card deck/product shell gap, but full
product-grade ChaseOS Pulse remains partial.

Remaining major lanes:

- Personal Map visualization
- visual Runtime Brain dashboard UI
- Approval queue UI
- native schedule runner activation and missed-run proof
- optional connector/source scanner expansion

Graph links:
[[ChaseOS-Pulse-Final-Product-Readiness-Audit]] -
[[ChaseOS-Pulse-Completion-Tracker]] -
[[ChaseOS-Pulse-Phase10-UI-Proof]] -
[[ChaseOS-Pulse-Runtime-Brain-Dashboard-Contract]] -
[[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
