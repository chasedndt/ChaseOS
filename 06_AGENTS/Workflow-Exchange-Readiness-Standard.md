---
type: standard
title: Workflow Exchange Readiness Standard
status: DOCS + SCHEMA CONTRACT / MARKETPLACE NOT BUILT
updated: 2026-05-10
runtime: Codex
---

# Workflow Exchange Readiness Standard

The future ChaseOS Workflow Exchange can only list workflow packs that are portable, governed, auditable, and safe to fork. This pass does not build a marketplace UI or payment system.

## Exchange-Ready Requirements

A workflow pack can be exchange-ready only when:

- manifest exists
- schema validates
- runtime requirements are declared
- permission model exists
- approval policy exists
- proof card exists
- scorecard exists
- failure modes are documented
- no secrets are included
- safe dry-run mode exists
- installation/onboarding instructions exist
- fork attribution and versioning are declared

## Listing Requirements

Listings must include:

- workflow ID and version
- target user/customer
- compatible workspace modes
- runtime requirements
- permissions requested
- proof-card links
- scorecard summary
- redaction posture
- install/fork steps
- known limitations

## Non-Goals

- No marketplace UI in this pass.
- No payments.
- No public publishing.
- No automatic workflow installation.
- No trust claim from author reputation alone.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
