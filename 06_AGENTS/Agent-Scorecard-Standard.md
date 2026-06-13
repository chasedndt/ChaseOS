---
type: framework-standard
title: Agent Scorecard Standard
status: DOCS-ONLY
created: 2026-05-10
updated: 2026-05-10
---

# Agent Scorecard Standard

> VentureOps scorecards evaluate a workflow run, runtime contribution, or workflow pack against evidence, governance, usefulness, and commercial repeatability.

## Scorecard Scope

A scorecard can apply to:

- a single workflow run
- a workflow pack over multiple runs
- a runtime adapter contribution
- a client-facing service delivery

## Core Dimensions

| Dimension | Question |
|---|---|
| Governance fit | Did the run stay inside declared manifest, Gate, and approval boundaries? |
| Evidence quality | Are sources, inputs, outputs, and proof artifacts inspectable? |
| Output usefulness | Did the workflow produce a usable artifact or decision support? |
| Repeatability | Can the run be repeated with the same manifest and inputs class? |
| Monetization fit | Does this map to an offer, report, subscription, or workflow pack? |
| Runtime reliability | Did the selected runtime finish, fail gracefully, or escalate correctly? |
| Operator burden | Did the workflow reduce manual load without hiding risk? |

## Rating Scale

Use 0-5 for each dimension:

- 0: Not evaluated or absent.
- 1: Failed.
- 2: Weak / partial.
- 3: Acceptable for internal use.
- 4: Strong / external draft quality.
- 5: Verified, repeatable, and customer-ready.

## Required Evidence

Every scorecard must link to:

- workflow manifest
- proof artifact
- audit log or Agent Activity log
- output artifact
- tests or dry-run evidence
- unresolved risks



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
