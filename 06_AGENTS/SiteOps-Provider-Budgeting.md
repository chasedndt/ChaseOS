---
title: SiteOps Provider Budgeting
status: PARTIAL
date: 2026-04-30
---

# SiteOps Provider Budgeting

Paid provider workflows are routed through BudgetPolicy checks before execution.

## Built Now

Provider templates expose:
- `cost_mode`
- `estimated_cost_per_run`
- `supports_dry_run`
- `supports_stub`
- `requires_paid_credits`
- provider account requirements

BudgetPolicy checks return:
- `allow`
- `approval_required`
- `deny`

Dry-runs estimate cost and never charge or call providers. Gemini image edit currently exceeds the local approval threshold and creates an approval request; Perplexity research capture is below the local threshold.

## Future

Production should track actual usage, daily/monthly budget windows, provider reliability, output quality, and workflow/provider scorecards.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
