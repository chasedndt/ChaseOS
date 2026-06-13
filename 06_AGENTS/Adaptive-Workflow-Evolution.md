---
type: framework-standard
title: Adaptive Workflow Evolution
status: PARTIAL / PROPOSAL-FIRST STANDARD IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Adaptive Workflow Evolution

Adaptive Workflow Evolution is the Mission Mode rule for improving workflow packs over repeated runs.

## Rule

Workflow logic may be observed, scored, simulated, dry-run, and proposed. It must not be silently changed.

## Lifecycle

1. A mission run produces proof artifacts and scorecards.
2. A mission review identifies repeated patterns.
3. A workflow evolution proposal records the proposed change, evidence, risk review, dry-run plan, and approval need.
4. A human approves or rejects the proposal.
5. An approved change becomes a versioned workflow update through the normal ChaseOS implementation and writeback path.

## Required Evidence

Evidence-backed proposals require:

- proof cards
- scorecards
- run logs or audit links
- source files when relevant
- risk review
- dry-run plan

## Safety Boundary

`auto_apply_allowed` defaults to false. Weak-provider fallback cannot approve or perform high-authority evolution review. Financial logic, browser skills, external actions, protected-file edits, and runtime/provider routing changes require human approval.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
