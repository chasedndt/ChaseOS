---
type: framework-standard
title: Workflow Pack Standard
status: PARTIAL / SCHEMA + PACK EXAMPLES VERIFIED
created: 2026-05-10
updated: 2026-05-10
---

# Workflow Pack Standard

> A workflow pack is the VentureOps unit of productization: a governed, repeatable workflow with manifest, role card, tool contracts, proof artifacts, audit path, and monetization surface.

## Required Components

Every workflow pack must define:

1. `workflow_id`
2. Workflow family and priority
3. Intended user/customer
4. Trigger types
5. Task packet shape
6. Workflow manifest path
7. Role card path
8. Required inputs
9. Required context
10. Allowed tools
11. Blocked tools
12. Runtime adapter candidates
13. Approval requirements
14. Writeback targets
15. Proof artifact shape
16. Audit log target
17. Scorecard metrics
18. Failure behavior
19. Monetization / follow-up path
20. Status and verification evidence

## Production Equation

Generic production agent:

`model + prompts + tools + schemas + retries + fallbacks + memory + routing + permissions + audit logs + evaluation + runtime state + human approval = production agent`

ChaseOS VentureOps equivalent:

`workflow manifest + role card + runtime adapter + tool contract + Gate check + provider governance + proof artifact + audit log + scorecard = monetizable governed workflow`

## Minimum Gates

Before a workflow pack can move from DOCS-ONLY to PARTIAL:

- Manifest draft exists.
- Required reads and writes are declared.
- Approval requirements are declared.
- Proof artifact contract exists.
- Audit target exists.
- Secret boundary is stated.

Before a workflow pack can move from PARTIAL to VERIFIED:

- It has a bounded dry-run, unit test, or live safe proof.
- Proof artifact is written.
- Agent Activity or runtime audit log is written.
- Scorecard can be produced or explicitly deferred with reason.

Before a workflow pack can move from VERIFIED to COMPLETE:

- Repeatable run path exists.
- Failure behavior is exercised or explicitly tested.
- Human approval boundaries are proven.
- Client/internal-facing output is reviewable.
- Registry and docs truth are updated.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
