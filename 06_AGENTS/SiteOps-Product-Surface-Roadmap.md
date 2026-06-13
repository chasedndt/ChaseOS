---
title: SiteOps Product Surface Roadmap
status: PLANNED
date: 2026-04-30
---

# SiteOps Product Surface Roadmap

The current product surface is CLI-only. The future user-facing tab is **Site Skills**.

## Current CLI Surface

- catalog list/show
- tenants list
- skills install/list/enable/disable
- workflows list/show/validate/dry-run
- runs list/show/dry-run
- approvals list/show/approve/reject
- credentials list/check
- browser-profiles list/check
- budgets list/check

## Future UI

The future Site Skills tab should support:
- browse installed skills by site/provider
- configure workflow inputs
- dry-run plan review
- approval queue, routed through [[ChaseOS-Approval-Center]] for cross-feature approval-center semantics
- run progress
- artifact review
- run/audit replay
- workflow scorecards
- provider performance scorecards

Marketplace and community catalog behavior remain future work. The backend scaffold preserves templates versus tenant installs so those surfaces are not blocked.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
