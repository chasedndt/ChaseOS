---
title: Chaser Forge Workflows Index
status: public-core-template-hub
created: 2026-06-13
owner: ChaseOS Core
open_core_template_status: included-template-hub
---

# Chaser Forge Workflows Index

Chaser Forge is the governed self-extension workflow family for ChaseOS Core. It lets a user or operator describe a new module, validate it as an extension manifest, review its permissions, preview/sandbox it, and only then install it through approved extension points.

This Core node is intentionally public-safe. It describes the transferable workflow pattern; it does not include private run logs, local operator receipts, credentials, generated fixture state, or live marketplace execution.

## OpenCore transfer posture

Chaser Forge should ship in OpenCore as a **templateable governance and workflow-pack system**, not as an automatic remote marketplace.

Included here:

- workflow-node map;
- template lifecycle;
- required approval boundaries;
- extension-point guardrails;
- public proof taxonomy;
- reusable template files under `templates/forge/`.

Not included here:

- live hosted marketplace fetch;
- network upload;
- paid checkout or entitlement enforcement;
- seller accounts, payouts, refunds, or disputes;
- untrusted third-party install;
- approval consumption or runtime execution.

## Workflow node map

| Workflow ID | Purpose | Template status | Execution boundary |
|---|---|---|---|
| `forge.manifest.validate` | Validate extension identity, version, target paths, extension points, permissions, and rollback posture. | Included as template pattern. | Local validation only. |
| `forge.extension.preview` | Render a non-destructive preview of declared UI/workflow/agent surfaces. | Included as template pattern. | No production writes. |
| `forge.sandbox.request` | Create an approval-request packet for extension-owned sandbox writes. | Included as approval packet template. | Request only; no install. |
| `forge.decision.handoff` | Record an operator approve/reject decision with exact digest and statement gates. | Included as workflow-node template. | Decision metadata only; no consumption. |
| `forge.sandbox.consume` | Consume an approved sandbox packet exactly once to create sandbox-scoped extension files. | Design pattern only. | Requires explicit local executor implementation and approval. |
| `forge.live-install.request` | Request promotion from sandbox to active. | Templateable. | Request only. |
| `forge.live-install.consume` | Consume a live-install approval exactly once. | Design pattern only. | Approval-gated local executor only. |
| `forge.rollback.request` | Request rollback/disable for active extension. | Templateable. | Request only. |
| `forge.rollback.consume` | Consume rollback approval exactly once and preserve audit trail. | Design pattern only. | Approval-gated local executor only. |
| `forge.marketplace.package` | Package a local extension template with digest metadata. | Included as template pattern. | Local artifact only. |
| `forge.marketplace.catalog` | Build or inspect a local catalog/index of available packs. | Included as template/index pattern. | No remote exchange. |
| `forge.marketplace.import-review` | Request review before importing a package into sandbox. | Templateable. | Request only. |
| `forge.marketplace.import-bridge` | Convert approved marketplace-import review into a sandbox request. | Design pattern only. | No install by itself. |
| `forge.static.index` | Publish static metadata for packs in a public-safe index format. | Included as example index. | Static metadata only. |
| `forge.remote.fetch` | Fetch or verify a remote index. | Excluded from default OpenCore. | Requires explicit future approval and network gate. |

## Graph routing pattern

Every Forge workflow should route through this graph shape:

```text
Forge workflow index
  -> workflow-node spec/template
  -> extension manifest or pack manifest
  -> approval request template when writes are possible
  -> proof taxonomy / evidence class
  -> explicit blocked authority labels
```

## Required fields for workflow nodes

Use `templates/forge/forge-workflow-node.template.md` as the authoring base. Minimum fields:

- `workflow_id`
- `status`
- `open_core_template_status`
- `allowed_inputs`
- `allowed_writes`
- `blocked_authority`
- `approval_required_before_execution`
- `proof_artifacts`
- `runtime_paths`
- `studio_surfaces`
- `obsidian_links`

## Extension-point rule

Forge extensions may add functionality only through declared extension points. Generated extensions must not rewrite ChaseOS Core itself.

Approved extension-point families for templates:

- `sidebar.nav.item`
- `workspace.page`
- `dashboard.widget`
- `agent.preset`
- `workflow.template`
- `form.schema`
- `command.palette.action`
- `report.template`
- `notification.template`
- `connector.usage`
- `marketplace.template`

## Template files

- `templates/forge/forge-workflow-node.template.md`
- `templates/forge/extension-manifest.example.json`
- `templates/forge/approval-request.template.json`
- `templates/forge/forge-index.example.json`

## Related Core docs

- `docs/forge/chaser_forge_workflow_proofs_index.md`
- `docs/forge/chaser_forge_opencore_transfer_plan.md`
- `docs/standards/chaseos-forge-workflow-node-v1.md`
- `docs/standards/chaseos-forge-index-v1.md`
- `docs/audits/2026-06-13_chaser_forge_opencore_transfer_audit.md`
