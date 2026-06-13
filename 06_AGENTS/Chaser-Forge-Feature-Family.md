---
title: Chaser Forge Feature Family
type: feature-family-node
status: COMPLETE / GOVERNED MARKETPLACE, LOCAL LIVE-INDEX INPUT PREFILL BUILT, NO-DOMAIN CLOSEOUT VERIFIED, DOMAIN SELECTED / PUBLIC STATIC INDEX UPLOAD PENDING / LIVE FETCH APPROVAL-GATED
created: 2026-05-21
updated: 2026-05-25
canonical_parent: [[Feature-Register]]
---

# Chaser Forge Feature Family

Chaser Forge is the governed self-extension feature family for ChaseOS. It lets the local product shell review, install, inspect, and govern extension-like packages without turning extension installation into ambient code execution.

This node gives Chaser Forge a wiki-addressable feature-family home. Runtime implementation truth remains in `runtime/forge/`; the marketplace proof deck and completion audit remain the evidence surfaces.

Workflow routing for transfer/OpenCore packaging now lives in [[chaser_forge_workflows_index]], with Forge-specific proof routing in [[Chaser-Forge-Workflow-Proofs-Index]].

## What It Is

Chaser Forge covers:

- local governed extension lifecycle;
- local package review;
- ChaseOS-owned local public catalog publish;
- read-only Local Marketplace Library inspection;
- digest-bound remote distribution index artifacts;
- verified remote listing ingest into the local catalog;
- digest-gated hosted export bundles for manual static-host mirroring;
- digest-gated static-host publication proof directories with upload-ready static files;
- digest-gated static-host upload handoff artifacts for operator manual upload;
- digest-gated static-host upload receipt artifacts for operator proof after manual upload;
- digest-gated published static index registration artifacts for operator-declared public index URLs;
- digest-gated local live `index.json` input prefill artifacts with official domain selected and static upload/fetch approval pending;
- read-only live `index.json` input readiness for the future domain-hosted verification packet;
- deterministic no-domain closeout audit proving Studio wiring, packet prefill, coming-soon UI source state, static publication files, and domain-owned blockers;
- approved extension-point policy;
- sandboxed package/import review;
- marketplace-import-to-sandbox approval bridge;
- governed marketplace install execution;
- Studio panel exposure;
- product-facing Extensions operating context, readiness, capability coverage, object cards, and right-inspector selection;
- proof deck and completion audit evidence.

## Current Status

COMPLETE / GOVERNED CHASER FORGE MARKETPLACE, LOCAL LIVE-INDEX INPUT PREFILL BUILT, NO-DOMAIN CLOSEOUT VERIFIED, DOMAIN SELECTED / PUBLIC STATIC INDEX UPLOAD PENDING / LIVE FETCH APPROVAL-GATED.

The governed local extension lifecycle, local catalog publish path, read-only Local Marketplace Library, approved marketplace install path, digest-bound remote index artifact path, verified remote listing ingest path, digest-gated hosted export bundle path, digest-gated static-host publication proof path, digest-gated static-host upload handoff path, digest-gated static-host upload receipt path, digest-gated published static index registration path, local live index input prefill path, read-only live index input readiness, no-domain closeout audit, Studio UI wiring, operator-use Studio button flow, and source-rendered product-facing Extensions UI are complete for the local MVP. The hosted marketplace area in Studio presents the domain-dependent public lane as `Coming soon` and keeps live registration/fetch authority blocked. `runtime.studio.chaser_forge_no_domain_closeout_audit` reports zero code-owned no-domain blockers against current repo evidence; the only remaining live-hosted path is operator-owned static upload, packet finalization, and one future approved bounded fetch. Live hosted fetch verification is deferred until `https://chaseos.ai/forge/index.json` is uploaded, digest-verified, and a final approval packet is supplied. Ambient remote network marketplace calls, network upload, live network fetch verification of operator-provided hosted URLs, untrusted third-party package exchange, payment/license mutation, public publication to an external hosted registry, and external registry mutation remain blocked by design unless a future explicitly approved authority lane adds them.

## Canonical Evidence

- `runtime/forge/README.md`
- `docs/features/chaser_forge_mvp_extension_install_contract.md`
- `docs/features/chase_forge_approved_extension_points_spec.md`
- `07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-proof-deck.md`
- `07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-completion-audit.md`
- `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-operator-use-studio-proof/chaser-forge-marketplace-operator-use-visual-qa-report.json`
- `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-marketplace-operator-use-closeout-smoke/chaser-forge-marketplace-operator-use-visual-qa-report.json`
- `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-local-marketplace-library-studio-use-smoke/chaser-forge-local-marketplace-library-studio-use-smoke-result.json`
- `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-remote-distribution-foundation-smoke/chaser-forge-remote-distribution-foundation-smoke-result.json`
- `07_LOGS/Studio-Visual-QA/2026-05-22-chaser-forge-hosted-marketplace-export-bundle-smoke/chaser-forge-hosted-marketplace-export-bundle-smoke-result.json`
- `07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-host-publication-proof-smoke/chaser-forge-static-host-publication-proof-smoke-result.json`
- `07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-upload-handoff-smoke/chaser-forge-static-upload-handoff-smoke-result.json`
- `07_LOGS/Studio-Visual-QA/2026-05-23-chaser-forge-static-upload-receipt-smoke/chaser-forge-static-upload-receipt-smoke-result.json`
- `07_LOGS/Studio-Visual-QA/2026-05-24-chaser-forge-published-static-index-registration-smoke/chaser-forge-published-static-index-registration-smoke-result.json`
- `07_LOGS/Operator-Briefs/2026-05-24-chaser-forge-live-index-json-input-handover.md`
- `07_LOGS/Operator-Briefs/2026-05-24-chaser-forge-live-index-json-input-packet-template.json`
- `07_LOGS/Operator-Briefs/Chaser-Forge-Live-Index-Input-Prefills/live-index-input-prefill-8db3a8749899.json`
- `07_LOGS/Operator-Briefs/Chaser-Forge-Live-Index-Input-Prefills/live-index-input-prefill-8db3a8749899.md`
- `runtime/studio/chaser_forge_no_domain_closeout_audit.py`
- `runtime/studio/test_chaser_forge_no_domain_closeout_audit.py`
- `07_LOGS/Build-Logs/2026-05-25-ChaseOS-chaser-forge-no-domain-closeout-audit.md`
- `docs/forge/chaser_forge_workflows_index.md`
- `docs/forge/chaser_forge_web_design_agency_workflow.md`
- `07_LOGS/Workflow-Proofs/Chaser-Forge-Workflow-Proofs-Index.md`
- `07_LOGS/Visual-QA/2026-05-24-studio-ui-chaser-forge-extensions-product-polish/final-productization-visual-qa.json`
- `07_LOGS/Visual-QA/2026-05-24-studio-ui-chaser-forge-extensions-product-polish/desktop-chaser-forge.png`
- `07_LOGS/Visual-QA/2026-05-24-studio-ui-chaser-forge-extensions-product-polish/mobile-chaser-forge.png`

## Studio Mapping

Normalized product surface:

- Current panel: `chaser-forge`
- User-facing label: Extensions / Chaser Forge
- Target navbar area: Main -> Extensions
- Canonical family: [[Chaser-Forge-Feature-Family]]
- Source UI status: COMPLETE / SOURCE UI VERIFIED / HOSTED MARKETPLACE COMING SOON / NO NEW LIVE AUTHORITY as of 2026-05-25.

## Boundaries

Chaser Forge does not grant:

- ambient remote third-party marketplace exchange;
- network upload, live network fetch verification, or external hosted registry mutation until a real domain-hosted packet is supplied and explicitly approved;
- untrusted remote extension trust;
- payment/license mutation;
- package execution beyond governed local approval flows;
- provider/model calls;
- browser control;
- Agent Bus task writes;
- payment/CRM mutation;
- canonical promotion without approval.

## Graph Links

[[Feature-Register]] [[Feature-Fit-Register]] [[Finalize-ChaseOS-Studio-Product-UI-Handover]] [[ChaseOS-Studio-Architecture]] [[chaser_forge_workflows_index]] [[Chaser-Forge-Workflow-Proofs-Index]]


## 2026-05-31 domain-selected update

Primary public domain selected: `https://chaseos.ai`. Chaser Forge public static index target: `https://chaseos.ai/forge/index.json`. This confirms the product planning status as domain-selected/static-index-upload-pending; it does not enable live hosted fetch, network upload, payment/license mutation, untrusted third-party exchange, automatic remote install, or external registry mutation. Live hosted fetch remains approval-gated until the static index is uploaded, URL verified, digest matched to the local artifact, and a final approval packet exists.
