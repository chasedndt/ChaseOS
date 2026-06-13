---
type: framework-standard
title: Mission State Ledger
status: PARTIAL / STANDARD AND VALIDATOR IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Mission State Ledger

A Mission State Ledger preserves mission-local operational state across days or weeks.

## Purpose

The ledger tracks:

- current status and phase
- active workflow versions
- latest run and review
- progress summary
- score trends
- hypotheses
- blockers
- pending approvals
- approved and rejected evolutions
- next recommended pass
- evidence, proof-card, and audit links

## Boundary

The ledger does not replace canonical project truth, roadmap truth, proof artifacts, or audit logs. It points to those artifacts.

## Runtime Contract

Schema: `runtime/ventureops/templates/mission_state_schema.yaml`

Validator: `runtime.ventureops.validation.validate_mission_state`

Helper: `runtime.ventureops.mission_state.build_initial_mission_state`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
