# ChaseOS Pulse Interactive Governed Controls

Status: COMPLETE TARGETED / CANDIDATE-ONLY CONTROLS BUILT / EXECUTION AND APPLY STILL BLOCKED

Date: 2026-05-03

## Purpose

This pass broadens the local Pulse control surface so the operator can submit every supported Pulse feedback/action type as a pending-review candidate.

This is not approval execution, memory approval, task creation, runtime dispatch, schedule activation, or canonical writeback.

## Implemented Control Boundary

Host surface:

- `runtime/studio/pulse_deck_app.py`
- `runtime/pulse/local_surface.py`

Candidate sink:

- `07_LOGS/Pulse-Decks/feedback-candidates/`

The controls append review-required candidate rows only. They do not apply effects to the source deck and do not mutate canonical ChaseOS truth.

## Covered Feedback / Action Types

- `accepted`
- `dismissed`
- `snoozed`
- `corrected`
- `needs_more_evidence`
- `memory_candidate`
- `thumbs_up`
- `thumbs_down`
- `show_more_like_this`
- `show_less_like_this`
- `never_show_this`
- `save`
- `delegate`
- `turn_into_task`
- `promote_to_memory`
- `link_to_project`
- `link_to_personal_map`
- `link_to_agent_brain`
- `dismiss`

## Authority Boundary

The controls may:

- render the latest user Pulse deck
- render all governed feedback/action candidate controls for each card
- accept explicit local operator form submissions
- append pending-review feedback candidate JSONL rows

The controls must not:

- write review decisions
- apply candidates
- approve memory
- create tasks directly
- grant approvals
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers
- call connectors
- mutate `00_HOME/Now.md`
- mutate Project-OS files
- promote anything into `02_KNOWLEDGE/`
- update the R&D workbook

## Current Truth

This closes the first interactive governed-controls gap for Pulse: visible controls exist and can create review candidates. Full product-grade Pulse remains partial because the candidate review/apply lanes, Personal Map live apply proof, schedule runner activation proof, and optional connector/source scanner expansion remain separate governed work.

## Verification Targets

- `runtime/studio/test_pulse_deck_app.py`
- `runtime/pulse/test_final_product_readiness_audit.py`

## Next Pass

Recommended next pass: browser-QA or service-layer hardening for the governed controls surface, then Personal Map live apply proof or native schedule runner activation proof depending on operator priority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
