---
title: ChaseOS Forge Workflow Node v1
status: draft-standard
created: 2026-06-13
schema_name: chaseos.forge-workflow-node.v1
owner: ChaseOS Core
---

# ChaseOS Forge Workflow Node v1

`chaseos.forge-workflow-node.v1` defines the minimum public-safe metadata for a Chaser Forge workflow node.

A workflow node is not an executor. It is a graph-routed contract that explains what a Forge workflow may read, what it may write, what approval is required, and what authority remains blocked.

## Required fields

| Field | Type | Purpose |
|---|---|---|
| `workflow_id` | string | Stable identifier such as `forge.manifest.validate`. |
| `title` | string | Human-readable workflow title. |
| `status` | string | `draft`, `template`, `implemented-local`, `blocked`, or `deprecated`. |
| `open_core_template_status` | string | Whether this workflow is included, pattern-only, or excluded from OpenCore. |
| `allowed_inputs` | array | Declared files/objects the workflow may read. |
| `allowed_writes` | array | Declared files/objects the workflow may write, if any. |
| `blocked_authority` | array | Explicitly denied powers. |
| `approval_required_before_execution` | boolean | Whether a human/Gate approval is required before writes. |
| `approval_packet_schema` | string/null | Approval packet schema if writes are possible. |
| `proof_artifacts` | array | Evidence classes the workflow should produce. |
| `runtime_paths` | array | Optional implementation paths. |
| `studio_surfaces` | array | Optional UI surfaces. |
| `obsidian_links` | array | Graph links to related docs. |

## Minimum blocked-authority set

Unless a separate gate grants more authority, every Forge workflow should block:

- `network_fetch`
- `network_upload`
- `external_registry_mutation`
- `payment_or_license_mutation`
- `untrusted_remote_install`
- `provider_model_call`
- `browser_control`
- `agent_bus_write`
- `host_mutation`
- `canonical_promotion`

## Example YAML frontmatter

```yaml
---
workflow_id: forge.manifest.validate
title: Forge Manifest Validation
status: template
open_core_template_status: included
allowed_inputs:
  - extension-manifest.json
allowed_writes: []
blocked_authority:
  - network_fetch
  - network_upload
  - external_registry_mutation
  - payment_or_license_mutation
  - untrusted_remote_install
approval_required_before_execution: false
approval_packet_schema: null
proof_artifacts:
  - manifest-validation-report
runtime_paths: []
studio_surfaces:
  - Chaser Forge
obsidian_links:
  - docs/forge/chaser_forge_workflows_index.md
---
```

## Validation expectations

A validator for this standard should fail closed when:

- `workflow_id` is missing or unstable;
- writes are declared but approval is not required;
- blocked-authority labels are missing;
- network/payment/remote-install authority appears in OpenCore templates;
- proof artifacts imply execution that the workflow cannot perform;
- local/private proof paths are used as public template payload.

## Related files

- `docs/forge/chaser_forge_workflows_index.md`
- `docs/forge/chaser_forge_workflow_proofs_index.md`
- `templates/forge/forge-workflow-node.template.md`
