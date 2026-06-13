---
title: ChaseOS AI Web Page Functionality Matrix
created: 2026-06-06
status: DRAFT / PUBLIC WEB IA / STATIC IMPLEMENTATION INPUT
type: website-plan
primary_domain: https://chaseos.ai
session: 2026-06-06_chaseros-web-page-architecture
---

# ChaseOS AI Web Page Functionality Matrix

This matrix maps the public `chaseos.ai` route set to current repo truth. It is an implementation guide for the static public site and a planning guide for future dynamic pages.

## Repo-Truth Baseline

- ChaseOS is the product/platform: local-first AI operating system and agent control plane.
- ChaseOS Studio is the desktop command surface and primary V1 app.
- Chaser Forge is a static preview catalog and future marketplace path.
- Standards are preview examples, not stable public APIs.
- Studio public posture is `Early Access / Developer Preview`.
- Billing, paid marketplace checkout, managed agents, runtime credits, external delivery, and enterprise readiness are not live public features.

## Page Matrix

| Route | Page role | Feature families that matter | Current implementation posture | Required page behavior |
|---|---|---|---|---|
| `/` | Public front door | Studio, SIC, Capture/Acquisition, AOR, approval visibility, Forge, Standards | Static implemented | Explain ChaseOS in under 60 seconds; route to waitlist, Forge, docs; keep future claims blocked. |
| `/studio` | Product page for the app | Studio, Graph/Memory, Workflow Packs, Runtime/Agent status, approvals, Settings/privacy | Static implemented | Show Studio modules and authority boundaries; do not imply release-grade public installer until download gate clears. |
| `/forge` | Marketplace preview | Chaser Forge, Product Workflow Packs, Creator Engine, approval packets, standards | Static implemented | Render preview packs and `/forge/index.json`; no paid marketplace, creator payouts, entitlement, or auto-install claims. |
| `/standards` | Public contracts hub | Pack manifest, Forge index, Approval, Graph, Source, Outcome, Entitlement, Managed Job, Agent | Static implemented | Link example JSON files and mark preview/no stable API. |
| `/waitlist` | Demand capture placeholder | Studio, Forge, creators, teams/private deployment | Static implemented | Browser-only validation until an approved backend/storage/admin policy exists. |
| `/open-core` | Product/business posture | Core export, license, standards, Forge packs, commercial layers | Static implemented | Separate open/inspectable trust surfaces from commercial/service surfaces. |
| `/pricing` | Pricing hypothesis | Local Starter, Pro, Forge+, Managed Agents, Team/Business | Static implemented | Mark pricing planned; no live billing, credits, managed agents, or marketplace purchases. |
| `/download` | Release gate | Studio packaging, signing, release smoke, public repo hygiene | Static implemented | Route to waitlist until public package, signing, smoke, and operator approval are complete. |
| `/roadmap` | Feature status map | SIC, Capture/Acquisition, AOR, WML, Studio, Pulse, Forge, Browser Runtime/SiteOps, MCP, VentureOps, Product Workflow Packs / Missions, AISO, Chaser Agent | Static implemented, expanded 2026-06-12 for NB-040 | Classify as ready/preview, partial/gated, future; include Product Workflow Packs / Missions as its own feature-family row with local preview-live proof and blocked marketplace/payment/external-delivery/approval-consumption lanes. |
| `/status` | Public status posture | Studio, Forge, Standards, website static status | Static implemented 2026-06-06 | Report early-access state without reading private runtime logs or customer systems. |
| `/changelog` | Public-safe release notes | Website, standards, Forge, Studio public gates | Static implemented 2026-06-06 | Keep internal build logs out; summarize only public-safe changes. |
| `/docs` | Public docs hub | Standards, Forge, security, roadmap, Studio | Static implemented | Link public-safe docs; exclude private paths, ledgers, and secrets. |
| `/privacy` | Privacy posture | Local-first storage, provider setup, logs/audits, telemetry, external actions | Static implemented | Explain local-first default and provider/action caveats honestly. |
| `/security` | Security posture | Permission Matrix, Trust Tiers, approvals, Gate, provenance, audit logs | Static implemented | Explain boundaries; no enterprise/compliance claims. |
| `/terms` | Early access terms | AI output risk, external action responsibility, preview software | Static implemented | Mark draft/not lawyer-reviewed. |
| `/license` | License/open-core boundary | Core export, open-core, source-available/commercial split, Forge examples | Static implemented 2026-06-06 | Do not call commercial-restricted code open-source until final license exists. |
| `/companions` | Companion/runtime posture | Hermes, OpenClaw, Claude Code/Archon, Chaser Agent, Agent Bus | Static implemented 2026-06-06 | Position companions as bounded lanes; Chaser Agent remains future public managed lane. |
| `/support` | Support/contact route | Early access support, security contact, creator support | Static implemented | Keep support desk as early access until backend/staffing exists. |
| `/creators` | Creator landing | Chaser Forge, Product Workflow Packs, Creator Engine, standards | Static implemented | Recruit pack creators; paid/certified/payout lanes remain future. |
| `/submit-pack` | Creator interest form | Forge, standards, approval/external action declaration | Static implemented | Browser-only validation; no submission storage in static build. |
| `/marketplace-terms` | Draft creator/buyer terms | Forge marketplace, entitlements, payouts, certification, refunds | Static implemented 2026-06-06 | Mark draft because marketplace is preview-only. |
| `/admin` | Protected internal stub | Waitlist/admin future backend | Static implemented, noindex | Excluded from sitemap; no PII/private vault/runtime/admin APIs. |

## Recommended Navigation Model

Top navigation should stay compact:

- Home
- Studio
- Forge
- Roadmap
- Status
- Docs
- Waitlist

The full route family belongs in grouped footer navigation:

- Product: Open Core, Pricing, Download, Roadmap, Status, Changelog.
- Trust, Docs & Legal: Standards, Docs, Privacy, Security, Terms, License.
- Forge & Support: Forge, Companions, Support, Creators, Submit Pack, Marketplace Terms.

## Feature Families To Surface On Roadmap/Status Pages

- Source Intelligence Core: `COMPLETE` for core subsystem; public copy should explain source packages/workspaces/retrieval without overclaiming provider execution.
- Connector / Capture / Acquisition: `COMPLETE` for Phase 8 capture core and `PARTIAL` for newer acquisition/live connector lanes.
- Autonomous Operator Runtime: `PARTIAL LIVE`; first-wave and bounded paths exist, broad autonomy does not.
- Workspace Mode Layer: `COMPLETE` as scoped runtime/operator product feature; broad autonomy remains approval-gated.
- Studio / Interface Layer: central V1 app; release-grade public distribution remains gated.
- Pulse: `PREVIEW / PARTIAL`; do not imply live proactive external execution.
- Chaser Forge: `COMPLETE LOCAL / STATIC PREVIEW`; remote marketplace/payment/entitlement paths are future.
- Browser Runtime / SiteOps: `PREVIEW / PARTIAL`; broad authenticated browser automation remains blocked/future.
- MCP / Agent Bus / Runtime adapters: developer/runtime surfaces; only exact bounded lanes should be called live.
- VentureOps / Mission Mode: strong product wedge; real-world delivery/revenue remains blocked unless supplied by evidence.
- Creator Engine / Product Workflow Packs / Sub-Agent Presets / Personal Context Import / Phase 11 Chat: include as feature families or roadmap cards with their exact authority labels. Product Workflow Packs / Missions must not be hidden under VentureOps or Forge; mark local Missions UI/proof as preview-live and marketplace payment, hosted publication, remote install, external delivery, and approval consumption as blocked.
- AISO and Chaser Agent: upcoming/post-V1 unless a later implementation pass proves otherwise.

## Non-Claims

The web surface must not claim:

- public beta readiness;
- live billing, credits, or account services;
- live paid marketplace purchases, licensing, creator payouts, or refunds;
- managed agents available now;
- broad external delivery, browser automation, CRM/payment mutation, or posting;
- enterprise/compliance readiness;
- private vault/runtime/customer status readback from static pages.

## Graph Links

[[Feature-Register]] [[Feature-Fit-Register]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]] [[chaseos_v1_release_readiness_matrix]] [[chaseos_systems_site_map]]
