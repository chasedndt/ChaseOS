---
type: standard
title: Domain Playbook Standard
status: DOCS + SCHEMA CONTRACT
updated: 2026-05-10
runtime: Codex
---

# Domain Playbook Standard

A VentureOps domain playbook describes how a domain becomes workflow-pack candidates without hard-coding a specific user's life.

## Required Fields

- `domain_id`
- `name`
- `target_users`
- `evidence_sources`
- `workflow_opportunities`
- `approval_boundaries`
- `proof_artifacts`
- `monetization_paths`
- `risks`

## Portability Rules

- Domain playbooks must separate seed-instance examples from universal rules.
- Personal rankings are labeled `personal-seed`, not default global priority.
- Missing evidence produces discovery questions.
- Domain-specific risky actions must declare approval boundaries.
- Crypto/trading, ecommerce/payments, job submissions, and external contact workflows default to draft/proof mode.

## Implementation Status

The schema-like contract exists at `runtime/workflows/registry/templates/domain_playbook_schema.yaml`; the reusable template exists at `05_TEMPLATES/Domain-Playbook-Template.md`.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
