---
type: framework-standard
title: Mission Review Standard
status: PARTIAL / STANDARD AND VALIDATOR IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Mission Review Standard

Mission reviews are periodic structured artifacts that convert repeated mission runs into evidence-backed decisions.

## Review Questions

- What was the mission objective?
- What workflows ran?
- What proof artifacts were produced?
- What changed since last review?
- What worked?
- What failed?
- What repeated pattern appeared?
- What evidence supports the pattern?
- What should be tested next?
- What workflow change is proposed?
- What requires human approval?
- What remains blocked?
- What is the next safe pass?

## Boundary

Mission reviews do not apply workflow changes. Proposed changes require workflow evolution proposals and approvals.

Schema: `runtime/ventureops/templates/mission_review_schema.yaml`

Validator: `runtime.ventureops.validation.validate_mission_review`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
