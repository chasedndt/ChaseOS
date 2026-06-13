---
title: SiteOps Tenancy And Isolation
status: PARTIAL
date: 2026-04-30
---

# SiteOps Tenancy And Isolation

SiteOps production objects are scoped. Objects that affect user data must fail closed when required scope is absent or mismatched.

Required local defaults:
- `tenant_id: local`
- `workspace_id: default`
- `user_id: local-user`

## Enforced Now

- `run_siteops_dry_run` requires tenant, workspace, and user.
- tenant fixture loading rejects tenant ID mismatch.
- workflow installations are tenant/workspace scoped.
- workflow runs write under `07_LOGS/SiteOps-Runs/<tenant_id>/<workspace_id>/`.
- audit events write under `07_LOGS/SiteOps-Audits/<tenant_id>/<workspace_id>/`.
- approval objects write under `07_LOGS/SiteOps-Approvals/<tenant_id>/<workspace_id>/`.
- users without permitted roles or explicit workflow access are denied.
- missing tenant files fail closed.

## Future Production Storage

The current backing store is YAML/JSON fixtures. The model is intended to map to SQLite for local dev, Postgres for production metadata, object storage for artifacts, secure secret stores for credentials, and isolated browser session stores for profile refs.

## Not Allowed

- cross-tenant workflow access
- cross-user browser profile reuse by default
- shared provider credentials without tenant policy
- output paths outside scoped tenant/workspace lanes
- automatic promotion into canonical ChaseOS knowledge


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
