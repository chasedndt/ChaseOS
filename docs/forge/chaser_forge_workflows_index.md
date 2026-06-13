---
title: Chaser Forge Workflows Index
status: active-transfer-index
created: 2026-06-13
updated: 2026-06-13
owner: ChaseOS
canonical_parent: [[Chaser-Forge-Feature-Family]]
transfer_target: ChaseOS OpenCore template
---

# Chaser Forge Workflows Index

This is the graph-routed Obsidian wiki hub for Chaser Forge workflows. It exists so the Chaser Forge implementation can be transferred into a future ChaseOS OpenCore download as templated, inspectable workflow nodes rather than as an unstructured pile of runtime files.

Chaser Forge workflow truth is split intentionally:

- Product/feature family home: [[Chaser-Forge-Feature-Family]]
- Public preview spec: [[Chaser-Forge-V1-Public-Preview-Spec]]
- Proof/log hub: [[Chaser-Forge-Workflow-Proofs-Index]]
- General proof hub: [[Workflow-Proofs-Index]]
- Not-built / partial backlog row: [[chaseos_not_built_backlog]] NB-043
- Runtime implementation: `runtime/forge/` and Studio API/frontend surfaces

## Transfer posture for OpenCore

For the ChaseOS OpenCore template, Chaser Forge should ship as a **governed workflow-pack template**, not as a live paid marketplace or ambient remote installer.

### Include in OpenCore template

- Extension manifest schema and validation pattern.
- Approved extension-point policy.
- Protected-core path guard pattern.
- Sandbox approval request workflow.
- Source-specific operator decision handoff workflow.
- Decision-bound approval-consumption preflight pattern.
- Exact-once marker pattern for install/rollback executors.
- Local marketplace package/export/catalog preview pattern.
- Local library inspection pattern.
- Static Forge index format and digest verification pattern.
- Public `/forge/index.json` template artifacts.
- Studio/Obsidian graph nodes that explain status, boundaries, evidence, and next gates.

### Exclude from OpenCore template unless separately approved

- Hosted marketplace network fetch execution.
- Network upload or external registry mutation.
- Paid checkout, licensing entitlement enforcement, seller accounts, creator payouts, refunds, or marketplace disputes.
- Untrusted third-party install without validation and explicit approval.
- Provider/model calls, browser control, Agent Bus writes, credential reads, host mutation, or canonical promotion.

## Workflow node map

| Node | Workflow | Current posture | Primary implementation / proof |
|---|---|---|---|
| `forge.manifest.validate` | Validate extension manifests, allowed points, permissions, and protected-core boundaries. | Local/governed foundation. | `runtime/forge/`; [[chaser_forge_mvp_extension_install_contract]]; [[chase_forge_approved_extension_points_spec]] |
| `forge.sandbox.request` | Create a pending sandbox approval artifact for extension-owned sandbox writes. | Approval request only; no install. | `_forge_sandbox_approvals/`; proof deck entries in [[Chaser-Forge-Workflow-Proofs-Index]] |
| `forge.decision.handoff` | Record approve/reject metadata for a Forge approval artifact with exact digest/statement gates. | Source-specific decision writer; no approval consumption. | `runtime.forge.approval_decision`; Approval Center decision handoff proof |
| `forge.sandbox.consume` | Consume an approved sandbox artifact exactly once and write sandbox registry/extension-owned files. | Governed local executor; exact-once gated. | `runtime.forge` sandbox registry writer; 2026-05-20/21 proof decks |
| `forge.live-install.request` | Create a live-install approval request after sandbox proof. | Approval request only. | `_forge_live_install_approvals/`; lifecycle proof deck |
| `forge.live-install.consume` | Promote sandbox registry entry to active after approval, lifecycle proof, and exact-once validation. | Governed local executor; not ambient. | Marketplace/local MVP proof decks |
| `forge.rollback.request` | Create rollback approval request for active extension state. | Approval request only. | `_forge_rollback_approvals/`; lifecycle proof deck |
| `forge.rollback.consume` | Consume rollback approval exactly once and move active extension back to sandbox/disabled posture. | Governed local executor; no protected-core mutation. | Marketplace/local MVP proof decks |
| `forge.marketplace.package` | Build digest-bound local marketplace package previews and write package artifacts when the exact digest is supplied. | Local package/export preview. | `Forge-Marketplace-Packages/`; 2026-05-20/21 marketplace proof |
| `forge.marketplace.catalog` | Publish ChaseOS-owned local public catalog entries and inspect Local Marketplace Library. | Local catalog/library complete; no remote exchange. | 2026-05-21/22 proof deck and Studio-use smoke |
| `forge.marketplace.import-review` | Create marketplace-import approval artifact for local package-to-sandbox review. | Approval request only. | `_forge_marketplace_import_approvals/`; marketplace import bridge proof |
| `forge.marketplace.import-bridge` | Convert approved marketplace-import review into a pending sandbox request without installing. | Approval bridge only; no install. | `build_forge_marketplace_import_sandbox_request`; visual QA proof |
| `forge.marketplace.install` | Governed marketplace install execution after approved import and sandbox gates. | Local/governed install verified; exact-once gated. | 2026-05-21 marketplace proof deck and completion audit |
| `forge.remote.index` | Build digest-bound remote distribution index artifacts and ingest trusted remote listings into local catalog. | Foundation verified; no ambient live fetch. | 2026-05-22 remote distribution smoke |
| `forge.hosted.bundle` | Build hosted export bundle for manual static-host mirroring. | Local artifact write; no network upload. | 2026-05-22 hosted bundle smoke |
| `forge.static.publication` | Build upload-ready static host files including `index.json`, checksums, and publication manifest. | Local publication proof; operator upload pending. | 2026-05-23 static-host publication proof |
| `forge.static.upload-handoff` | Create operator upload handoff artifacts after checksums match. | Local handoff only. | 2026-05-23 static upload handoff smoke |
| `forge.static.upload-receipt` | Record operator-provided upload receipt statement/digest after manual upload. | Local receipt only; no network verification. | 2026-05-23 static upload receipt smoke |
| `forge.published-index.registration` | Register operator-declared public static index URL after receipt and digest gates. | Local registration artifact; live fetch still gated. | 2026-05-24 published index registration smoke |
| `forge.live-index.prefill` | Prefill the future live-index packet for `https://chaseos.ai/forge/index.json`. | Domain selected; static upload/fetch approval pending. | `07_LOGS/Operator-Briefs/Chaser-Forge-Live-Index-Input-Prefills/` |
| `forge.live-index.readiness` | Inspect future live-index input readiness without fetching. | Read-only readiness only. | 2026-05-25 live input readiness/no-domain closeout |
| `forge.public.preview` | Public `/forge`, `/forge/index.json`, `/submit-pack`, `/creators`, standards docs. | Static preview; no paid marketplace claim. | `website/forge/`; `docs/standards/`; [[Chaser-Forge-V1-Public-Preview-Spec]] |
| `forge.web_agency.site_build` | Reusable web design agency workflow seeded from the ChaseOS-Web / `https://chaseos.ai` build: intake, truth audit, IA/route map, copy, design, preview implementation, visual QA, approval packet, launch verification, and maintenance. | Draft workflow definition; template-transfer candidate; no automatic deploy/DNS/payment/CRM authority. | [[chaser_forge_web_design_agency_workflow]]; ChaseOS-Web docs under `<CHASEOS_WEB_REPO>/docs/website/` |

## OpenCore graph routing contract

Every Forge workflow node that ships in OpenCore should route through this pattern:

```text
Feature family node
  -> workflow index node
  -> workflow proof/log node
  -> runtime implementation path
  -> approval/gate boundary
  -> not-built/backlog row when incomplete
```

Minimum fields for each transferable node:

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

## Open loops / next gates

1. Keep NB-043 as the backlog row for Chaser Forge extension install/import until public/open-core packaging is actually exported and verified.
2. Add individual workflow-node files only when a workflow needs its own operator-facing specification beyond this index.
3. Before any OpenCore download claim, create a sanitized template package and prove it excludes secrets, private runtime state, personal vault paths, paid marketplace claims, and automatic remote install authority.
4. Public `https://chaseos.ai/forge/index.json` remains static-upload/fetch approval gated until the uploaded file exists, checksum matches, and a bounded fetch packet is explicitly approved.

## Graph links

[[Chaser-Forge-Feature-Family]] · [[Chaser-Forge-V1-Public-Preview-Spec]] · [[Chaser-Forge-Workflow-Proofs-Index]] · [[Workflow-Proofs-Index]] · [[chaser_forge_mvp_extension_install_contract]] · [[chase_forge_approved_extension_points_spec]] · [[chaseos_not_built_backlog]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[Hermes-Runtime-Profile]] · [[HERMES]]
