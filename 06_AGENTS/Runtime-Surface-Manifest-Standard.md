---
type: framework-control
title: Runtime Surface Manifest Standard - ChaseOS
status: PARTIAL
created: 2026-05-04
updated: 2026-05-04
scope: runtime-governance
---

# Runtime Surface Manifest Standard

> Runtime surface manifests are the machine-readable registration records for the Adaptive Runtime Surface Layer. They describe a runtime surface and its capabilities; they do not grant execution authority.

---

## 1. Manifest Location

Runtime surface manifests live in:

- `runtime/runtime_surfaces/manifests/`

Schema:

- `runtime/runtime_surfaces/schemas/runtime_surface_manifest.schema.json`

Loader and validator:

- `runtime/runtime_surfaces/models.py`
- `runtime/runtime_surfaces/registry.py`

## 2. Required Fields

Every manifest must define:

```yaml
schema_version: 1
surface_id: agent.codex.bus
display_name: Codex Agent Bus Worker
surface_family: agent_runtime
surface_type: agent
owner_layer: runtime/agent_bus
status: PARTIAL
implementation_refs: []
docs_refs: []
trust_ceiling: tier-2
permission_model_refs: []
gate_operations: []
capabilities: []
credential_policy:
  credentials_allowed: false
  cookies_allowed: false
  real_profile_allowed: false
fallback_policy:
  sticky_fallback_allowed: false
writeback_surfaces: []
audit_targets: []
routing_policy:
  default: deny_unknown
  authority_layer: runtime/agent_bus
mcp_exposure_policy:
  expose_summary: true
  expose_raw_manifest: false
```

## 3. Allowed Surface Families

Current allowed families:

- `provider_model_runtime`
- `agent_runtime`
- `browser_operator`
- `siteops_skill_runtime`
- `runtime_mcp`
- `client_embedded_runtime`
- `filesystem_surface`
- `terminal_surface`
- `desktop_surface`

Unknown surface family fails closed.

## 4. Allowed Surface Types

Current allowed types:

- `provider_model`
- `agent`
- `browser`
- `siteops_skill`
- `mcp`
- `client_embedded`
- `filesystem`
- `terminal`
- `desktop`

Unknown surface type fails closed.

## 5. Status Labels

Manifest `status` must use ChaseOS status labels:

- `COMPLETE`
- `PARTIAL`
- `PLANNED`
- `NOT BUILT`
- `DOCS-ONLY`
- `VERIFIED`
- `CONFIGURED BUT UNVERIFIED`
- `BLOCKED`
- `DEFERRED`

Status is descriptive. It does not grant authority.

## 6. Trust Ceiling

Allowed trust ceilings:

- `tier-1`
- `tier-2`
- `tier-3`
- `tier-4`

Trust ceiling is a maximum, not a permission grant. Actual authority still comes from `06_AGENTS/Trust-Tiers.md`, `06_AGENTS/Permission-Matrix.md`, the active execution surface, and operator approval.

## 7. Capability Fields

Each capability must define:

```yaml
capability_id: browser.read_state
maps_to: browser_read_state
risk_class: read_untrusted_external
approval_required: false
```

`approval_required` may be:

- `false`
- `true`
- `conditional`

The risk policy layer may normalize `true` to explicit approval. Unsupported values fail closed.

## 8. Risk Classes

Current risk classes:

- `read_local_scoped`
- `read_untrusted_external`
- `draft_only`
- `proposal_write`
- `quarantine_write`
- `canonical_write`
- `external_ui_read`
- `external_ui_mutation`
- `external_network_call`
- `credential_sensitive`
- `browser_profile_sensitive`
- `provider_fallback`
- `runtime_config_change`
- `security_policy_change`
- `destructive_action`
- `blocked`

Unknown risk class fails closed.

Blocked by default:

- `credential_sensitive`
- `browser_profile_sensitive`
- `destructive_action`
- `blocked`

## 9. Required Safety Policies

Credential policy must not grant secrets or browser profiles:

```yaml
credential_policy:
  credentials_allowed: false
  cookies_allowed: false
  real_profile_allowed: false
```

Fallback policy must not allow sticky fallback:

```yaml
fallback_policy:
  sticky_fallback_allowed: false
```

MCP exposure must not expose raw manifests:

```yaml
mcp_exposure_policy:
  expose_summary: true
  expose_raw_manifest: false
```

Routing policy must deny unknown work:

```yaml
routing_policy:
  default: deny_unknown
```

## 10. Path Rules

Manifest path references must be repo-relative.

The following fields are path-validated:

- `implementation_refs`
- `docs_refs`
- `permission_model_refs`
- `writeback_surfaces`
- `audit_targets`

Absolute paths, drive-qualified paths, and `..` path escapes are invalid.

## 11. Add or Change Procedure

To add a runtime surface:

1. Create or update a manifest under `runtime/runtime_surfaces/manifests/`.
2. Reference the real owner layer, implementation files, docs, and permission model.
3. Assign the lowest accurate trust ceiling.
4. Assign risk classes for every capability.
5. Keep credentials, cookies, real browser profile access, sticky fallback, and raw MCP manifest exposure disabled.
6. Add or update focused tests under `runtime/runtime_surfaces/tests/`.
7. Run the ARSL registry/policy test suite.
8. Update docs/logs without claiming execution support unless execution tests prove it.

## 12. Non-Goals

Manifests must not:

- grant runtime authority;
- bypass Gate;
- bypass the Permission Matrix;
- bypass Trust Tiers;
- bypass Agent Control Plane rules;
- create browser automation permission;
- create provider fallback permission;
- expose secrets;
- make weak fallback models sticky;
- make candidate browser skills trusted.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
