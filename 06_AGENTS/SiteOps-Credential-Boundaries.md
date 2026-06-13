---
title: SiteOps Credential Boundaries
status: PARTIAL
date: 2026-04-30
---

# SiteOps Credential Boundaries

SiteOps stores opaque credential references only.

## Built Now

CredentialRef objects include:
- `credential_ref_id`
- `tenant_id`
- optional `user_id`
- `provider_id`
- `credential_type`
- `secret_store_ref`
- `status`
- `last_verified_at`

CLI credential checks return configured/missing status and never print secret values or the secret store value.

## Secret Scanner

Validation rejects raw secret-like fields such as:
- `api_key`
- `password`
- `token`
- `cookie`
- `session_key`
- `private_key`
- `seed_phrase`

Opaque reference fields such as `credential_ref_id` and `secret_store_ref` are allowed.

## Not Built

No secure secret store integration is implemented in this pass. Adapters may use approved credential capabilities later, but agents must not receive raw credential values.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
