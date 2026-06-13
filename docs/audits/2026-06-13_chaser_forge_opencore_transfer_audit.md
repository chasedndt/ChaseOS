---
title: Chaser Forge OpenCore Transfer Audit
status: applied-core-template-slice
created: 2026-06-13
owner: ChaseOS Core
scope: Chaser Forge workflow hub, OpenCore/template transfer, public-safe repo packaging
---

# Chaser Forge OpenCore Transfer Audit

## Why this audit exists

Chaser Forge is not just a feature page. It is a reusable workflow-pack and extension-governance pattern that belongs in ChaseOS Core as a templateable system surface. If ChaseOS Core is going to be an OpenCore / template download, Forge needs graph-routed workflow nodes, standards, and templates — not only local personal-vault proof logs.

## Repositories inspected

- Source/private development vault: private ChaseOS development vault (path intentionally omitted from public Core docs)
- Public/Core candidate repo: ChaseOS Core repository

## Source-side findings

The source vault already contains a large Forge implementation/proof surface:

- Feature family: `06_AGENTS/Chaser-Forge-Feature-Family.md`
- Public preview spec: `06_AGENTS/Chaser-Forge-V1-Public-Preview-Spec.md`
- Feature specs:
  - `docs/features/chaser_forge_mvp_extension_install_contract.md`
  - `docs/features/chase_forge_approved_extension_points_spec.md`
- Standards:
  - `docs/standards/chaseos-forge-index-v1.md`
  - `docs/standards/examples/chaseos.forge-index.json`
- General proof hub:
  - `07_LOGS/Workflow-Proofs/Workflow-Proofs-Index.md`
- Forge proof decks/audits under `07_LOGS/Workflow-Proofs/`
- Runtime implementation in the private/dev source under `runtime/forge/` and Studio bridge code

A Forge-specific workflow hub was missing before this pass. The source vault now has `docs/forge/chaser_forge_workflows_index.md` and `07_LOGS/Workflow-Proofs/Chaser-Forge-Workflow-Proofs-Index.md`, but those files are still private-vault oriented. Core needs a public-safe equivalent.

## Target repo findings before this pass

`chaseos_core` is connected to Git at `git@github.com:chasedndt/ChaseOS.git` on `main`. The tracked public surface was still intentionally minimal:

- `README.md`
- `CORE_MANIFEST.md`
- `.gitignore`
- `chaseos.py`
- `pyproject.toml`
- `runtime/cli/__init__.py`
- `runtime/cli/main.py`

Many docs/templates existed locally under ignored paths, but they were not part of the tracked production-safe public repo. That meant Chaser Forge was present as local material but not actually packaged for OpenCore transfer.

## Gap classification

| Gap | Severity | Finding | Applied in this pass |
|---|---:|---|---|
| Forge workflow hub absent from tracked Core | High | No tracked graph-routed Forge workflow index suitable for public template use. | Added `docs/forge/chaser_forge_workflows_index.md`. |
| Forge proof/log routing not public-safe | High | Source proof logs are useful but should not be copied wholesale into public Core. | Added `docs/forge/chaser_forge_workflow_proofs_index.md` as a public proof taxonomy. |
| OpenCore transfer contract missing | High | No explicit rule for what Forge pieces become templates vs blocked authority. | Added `docs/forge/chaser_forge_opencore_transfer_plan.md`. |
| Workflow-node schema missing | Medium | Core had pack standards but no Forge workflow-node standard. | Added `docs/standards/chaseos-forge-workflow-node-v1.md`. |
| Template payload missing | Medium | No tracked starter templates for Forge workflow nodes/manifests/approval packets/index entries. | Added `templates/forge/*`. |
| Git ignore still blocked curated docs | Medium | `docs/` was ignored globally, making public-safe docs easy to forget. | Narrowed `.gitignore` exceptions for selected curated docs/templates. |
| README / manifest understated scope | Medium | Core README/manifest still said only minimal CLI. | Updated root docs to include governed template/docs surfaces. |

## Transfer rule

For OpenCore, Chaser Forge should ship as:

1. public-safe workflow/index standards;
2. manifest and approval templates;
3. extension-point and protected-core policy examples;
4. graph-routed docs that explain the lifecycle; and
5. explicit blockers for live marketplace/network/payment/remote install authority.

It should not ship as:

- private proof logs;
- local operator receipt artifacts;
- generated fixture outputs;
- live marketplace credentials or URLs requiring trust;
- payment/licensing/payout logic;
- automatic remote install authority; or
- broad runtime execution.

## Applied Core slice

This pass applies a first tracked Forge/OpenCore template slice to the Core repo:

- `docs/forge/chaser_forge_workflows_index.md`
- `docs/forge/chaser_forge_workflow_proofs_index.md`
- `docs/forge/chaser_forge_opencore_transfer_plan.md`
- `docs/standards/chaseos-forge-workflow-node-v1.md`
- `templates/forge/forge-workflow-node.template.md`
- `templates/forge/extension-manifest.example.json`
- `templates/forge/approval-request.template.json`
- `templates/forge/forge-index.example.json`

## Authority boundaries preserved

This pass does not add:

- live hosted fetch;
- network upload;
- external registry mutation;
- paid checkout;
- licensing entitlement enforcement;
- seller accounts or creator payouts;
- untrusted third-party package execution;
- approval consumption;
- Agent Bus task writes;
- provider/model calls;
- browser control;
- host mutation; or
- canonical promotion.

## Recommended next pass

1. Add a small validation CLI for Forge templates only, e.g. `chaseos forge validate-template`, without install or network authority.
2. Add tests for the example templates and standards links.
3. Decide whether selected source-side Forge runtime code should enter Core later; keep that as a separate code-inclusion audit, not part of this docs/template pass.
4. Keep proof decks private unless converted into synthetic example proof templates.
