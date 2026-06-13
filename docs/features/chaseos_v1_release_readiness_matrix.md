---
title: ChaseOS V1 Release Readiness Matrix
created: 2026-05-30
updated: 2026-05-30
runtime: hermes-optimus
type: release-readiness-matrix
status: DRAFT / TRACK A STARTED
scope: feature cutline, V1 blockers, preview/upcoming classification, monetization/domain implications
links:
  - [[ChaseOS-V1-Release-Cutline]]
  - [[chaseos_v1_public_beta_acceptance_checklist]]
  - [[chaseos_not_built_backlog]]
  - [[Feature-Register]]
  - [[Chaser-Forge]]
---

# ChaseOS V1 Release Readiness Matrix

> Track A matrix for deciding what blocks first public users versus what can ship as preview/upcoming.

Final V1-A1 PM handoff: `docs/features/chaseos_v1_public_beta_acceptance_checklist.md` turns this matrix into the public-user beta acceptance checklist. Treat this matrix as source classification input; treat the checklist plus follow-on evidence as the release-gate basis.

## 1. Legend

| Release class | Meaning | Blocks V1? |
|---|---|---|
| **Ship** | Must work for first public users. | Yes. |
| **Ship-Minimum** | Must exist, but may be thin/read-only/simple. | Yes if absent. |
| **Preview / Partial** | Visible but honest about limitations. | No if safe and truthful. |
| **Upcoming** | Roadmap card/page only. | No. |
| **Blocked / Decision** | Needs domain, provider, secret, signing, legal, external service, or operator input. | Only if needed for public trust/install. |
| **Post-V1** | Strategic later feature. | No. |

## 2. V1 product-critical capabilities

| Area | Release class | V1 acceptance | Notes |
|---|---|---|---|
| Standalone ChaseOS Studio launch | Ship | App opens, vault/root selected or detected, no `No vault root found`, no hardcoded personal path. | Highest priority. |
| First-run onboarding | Ship-Minimum | Explains local-first system, setup path, data location, provider setup optionality. | Can be simple page/modal. |
| Home / Command Center | Ship | Clear product-facing page with current capability, next actions, readiness, and upcoming features. | Must not feel like raw internal dashboard. |
| Settings | Ship | Vault path, provider/runtime status, privacy/data controls, app info, links to terms/privacy. | Should be first-class, not hidden. |
| Privacy / Terms / AI warnings | Ship | Privacy notice, terms/disclaimer, personal data warning, external-side-effect warning. | Required for public users. |
| Feature Catalog / Workflow Packs | Ship-Minimum | Cards for major features with Live/Partial/Upcoming/Blocked statuses. | Prevents empty-page confusion. |
| Chat / Agent Control Panel | Preview / Partial | Runtime readiness and safe commands/buttons work; unknown commands do not fake execution. | Can ship if honest and bounded. |
| Docs / Inspector | Ship-Minimum | User can browse/search local docs; broken paths handled. | Valuable immediately. |
| Graph / Memory visibility | Preview / Partial | Read-only graph/memory status visible; writes/promotions gated/disabled. | Do not block on full graph writeback. |
| Chaser Forge / marketplace | Preview / Partial | Local marketplace proof and public-domain coming-soon state visible. | Domain needed for live index. |
| Public website/landing | Ship-Minimum | Domain/landing path selected; page explains product, download/waitlist, privacy stance. | Can start as static landing page. |
| Public repo hygiene | Ship | No secrets/private context; README matches actual capability. | Blocker. |
| Release smoke tests | Ship | One repeatable command set validates launch/routes/settings/static product states. | Blocker. |

## 3. Not-built backlog classification

| ID | Feature / gap | V1 class | Why |
|---|---|---|---|
| NB-001 | Event-triggered AOR workflows | Post-V1 / Preview | Strategic automation; V1 can show upcoming/status. |
| NB-002 | Scheduled Briefing Pipelines expansion | Preview / Partial | Useful differentiator; broad expansion not required. |
| NB-003 | Workflow Registry completion | Ship-Minimum | Feature catalog/workflow pages need truthful registry/status; completion can be partial. |
| NB-004 | Agent Role Cards completion | Preview / Partial | Needed for deeper runtime governance, but not full public-user blocker. |
| NB-005 | Phase 9 second-wave features | Post-V1 | Not first-user critical. |
| NB-006 | Agent Memory Architecture file structure | Preview / Partial | Show memory status; do not block on full Layers C/D. |
| NB-007 | Agent Identity Ledger implementation | Post-V1 / Preview | Can show planned identity ledger. |
| NB-008 | Runtime Navigation Map accumulation | Preview / Partial | Useful for agents; not user-facing blocker. |
| NB-009 | Multi-Repo / Multi-Directory policy enforcement | Preview / Partial | Public user can start single workspace; multi-repo can be later. |
| NB-010 | Layer C durable generated artifacts | Post-V1 | Promotion path can remain future. |
| NB-011 | Persisted Studio graph storage | Preview / Partial | Read-only/cache status is enough for V1; full refresh/write later. |
| NB-012 | Real target-folder/file workspace upgrade execution | Post-V1 / Blocked | Risky migration executor; not V1 blocker. |
| NB-013 | Runtime action execution | Preview / Partial | Show action envelopes/readiness; no uncontrolled execution. |
| NB-014 | Runtime/adapter activation | Preview / Partial | Status/config pages yes; broad activation no. |
| NB-015 | Core export target restoration/revalidation | Blocked / Decision | Public repo/export hygiene matters; exact export target may be a release gate if packaging depends on it. |
| NB-016 | Public Core repo gates | Ship / Decision | License, .gitignore, repo, publication strategy directly affect V1. |
| NB-017 | Broader Gate coverage beyond Anthropic lane | Preview / Partial | Must not overclaim; enough safety gates for surfaced actions. |
| NB-018 | Live browser acquisition and connector/API acquisition expansion | Post-V1 / Preview | Useful but not needed for first public users. |
| NB-019 | Memory candidates / action-ready packets / delivery-ready packets | Preview / Partial | Can surface as upcoming/review center later. |
| NB-020 | Outcome scoring and scheduler integration | Post-V1 | Not first-user blocker. |
| NB-021 | SBP consumer wiring | Preview / Partial | Briefings can be partial/upcoming. |
| NB-022 | Full standalone governed Studio product experience | Ship | This is the central V1 blocker. |
| NB-023 | Branded installer/logo/icon packaging | Ship-Minimum / Decision | Need at least credible branding and download packaging; signing can be staged. |
| NB-024 | Signing/startup/release/host mutation follow-through | Blocked / Decision | Signing/startup may be post-beta; release packaging must be explicit. |
| NB-025 | Real provider/runtime/browser execution or explicit deferral | Ship-Minimum | Must either work or be explicitly deferred in UI. |
| NB-026 | Real target workspace upgrade/migration or explicit deferral | Ship-Minimum | Must explicitly defer if not built. |
| NB-027 | Live client run / live external delivery / live revenue workflow authority | Post-V1 / Blocked | Monetization strategy matters, but live external delivery is not V1 public-user blocker. |
| NB-028 | MCP surface expansion | Post-V1 / Preview | MCP V1 exists; expansion later. |
| NB-029 | Companion surface | Upcoming | Not V1 blocker. |
| NB-030 | Voice Mode | Upcoming / Preview | Show page/status; no microphone/provider capture required for V1. |
| NB-031 | AISO | Upcoming | High-value future mission; not a V1 blocker. |

## 4. Feature-family V1 classification

| Feature family | V1 class | V1 requirement |
|---|---|---|
| Source Intelligence Core | Ship-Minimum | Existing capability should be represented clearly; first-user docs explain what source intake means. |
| Capture / Acquisition + Normalization | Preview / Partial | Local/import readiness only; no overclaiming live connectors. |
| AOR | Preview / Partial | Show bounded workflow status; avoid claiming unrestricted automation. |
| Workspace Mode Layer | Ship-Minimum | Product-facing explanation and settings/status integration. |
| Interface / Experience Layer / Studio | Ship | Main V1 blocker. |
| ChaseOS Pulse | Preview / Partial | Status/page/card; not required as fully live proactive system. |
| Chaser Forge | Preview / Partial | Marketplace direction visible; domain/live index pending. |
| Browser Runtime / SiteOps | Preview / Partial | Readiness/proof/status only unless live bounded executor is separately verified. |
| MCP | Preview | Mention advanced/developer integration; not first user required. |
| VentureOps / Mission Mode | Preview / Partial | Good founder/business wedge; external revenue delivery remains blocked. |
| AISO | Upcoming | Roadmap/mission preview only. |
| Chaser Agent | Runtime identity exists / product authority gated | First-party 24/7 runtime/harness lane; managed-agent product authority remains gated. |

## 5. Monetization-readiness classification

| Monetization component | V1 class | Required now | Deferred |
|---|---|---|---|
| Landing page/domain | Ship-Minimum | Domain selected; landing copy; waitlist/download/contact. | Full webapp account system. |
| Subscription plans | Preview / Decision | Pricing hypothesis and plan labels. | Billing implementation. |
| License/account gate | Post-V1 / Decision | Decide open-core/source-available boundary. | Stripe/license server. |
| Credits | Post-V1 | Define credit concept only if managed agents/provider calls exist. | Credit accounting and enforcement. |
| Marketplace paid packs | Preview / Partial | Chaser Forge static/public index path; free/demo packs. | Payments, seller accounts, revenue share. |
| Managed Chaser Agent / agency | Post-V1 | Position as gated premium lane. | 24/7 hosted runtime product. |
| Enterprise/private deployment | Post-V1 | Mention high-level. | Sales/legal/security process. |

## 6. Recommended package/pricing hypothesis

Do not hard-code pricing in-product yet. Use as planning hypothesis:

| Plan | Buyer | Value | Notes |
|---|---|---|---|
| Free / Local Starter | Developers/builders trying ChaseOS locally. | Local Studio, docs, basic graph/status, sample workflows. | Drives adoption. |
| Pro | AI-native builders/founders. | Advanced Studio, workflow packs, provider/runtime convenience, premium templates, optional updates. | First MRR lane. |
| Forge+ | Power users/teams buying workflow packs/extensions. | Marketplace purchases, private catalogs, premium packs. | Chaser Forge monetization. |
| Managed Agent / Agency | Founders/businesses wanting outcomes. | Chaser Agent / always-on operator / done-for-you workflows. | High-ticket service-to-SaaS bridge. |
| Team / Business | Teams with shared projects/approvals. | Multi-user governance, logs, shared runtime policy. | Later B2B. |

## 7. Immediate V1 blocker list draft

Current likely blockers:

1. Standalone app product-facing audit not complete.
2. Settings/privacy/legal pages not complete enough for public users.
3. Public repo/license/open-core decision not finalized.
4. Domain/landing path not selected.
5. Chaser Forge live public index blocked until domain exists.
6. Hardcoded personal path/context/secret leak audit not complete.
7. README/Foundation/app copy may still contain internal/personal/status-heavy language for public users.
8. Release smoke suite not defined and run.
9. Feature catalog/readiness labeling must be consistent so preview/upcoming features do not look broken.

See `docs/features/chaseos_v1_public_beta_acceptance_checklist.md` for the final V1-A1 acceptance gates and evidence requirements.

## 8. Recommended Track A Kanban batch

Create these cards next:

| Card | Assignee | Goal |
|---|---|---|
| V1-A1 | pm | Turn this matrix into final V1 release cutline and acceptance checklist. |
| V1-A2 | analyst | Audit Studio routes/pages and map each to Ship/Preview/Upcoming/Blocked. |
| V1-A3 | analyst | Audit README/PROJECT_FOUNDATION/public docs for public-user language and personal leakage. |
| V1-A4 | writer | Draft landing-page positioning, pricing hypothesis, privacy/TOS warning copy. |
| V1-A5 | ops | Run hardcoded path, secret, personal context, and launch-smoke audit. |
| V1-A6 | reviewer | Produce final V1 blocker list and release-gate verdict. |

## 9. Graph links

[[ChaseOS-V1-Release-Cutline]] · [[chaseos_not_built_backlog]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[Chaser-Forge]] · [[Artifact-Intelligence-Submission-Operator]]
