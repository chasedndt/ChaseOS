---
title: SiteOps Approval Policy
status: PARTIAL
date: 2026-04-30
---

# SiteOps Approval Policy

Approval is a first-class object, not a prompt string.

## Built Now

When a dry-run hits an approval-required decision, SiteOps:
- returns run status `approval_needed`
- creates an `ApprovalRequest`
- writes the approval under `07_LOGS/SiteOps-Approvals/<tenant_id>/<workspace_id>/`
- records the approval ID in the run audit stream
- stops before execution because live execution is not built

Approval decisions require the configured approver role or `tenant_admin`. Approval/rejection updates the approval object and appends an audit event.

## Approval-Required Actions

- `export_file`
- `external_share`
- `publish_publicly`
- `purchase`
- `billing_action`
- `destructive_action`
- `account_mutation`
- `broker_connection`
- `live_trade`
- `invite_users`
- `credential_scope_expansion`
- paid provider cost above threshold

## Current Limitation

Resume is dry-run simulation only. No live browser/API execution resumes from an approval in this pass.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
