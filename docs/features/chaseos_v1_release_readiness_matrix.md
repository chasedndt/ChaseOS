---
title: ChaseOS V1 Release Readiness Matrix
created: 2026-05-30
updated: 2026-06-12
runtime: hermes-optimus
type: release-readiness-matrix
status: DRAFT / TRACK A STARTED / RELEASE MATRIX SURFACED
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

2026-06-12 Optimus Release Matrix surface: the native Studio shell now includes a read-only `Release Matrix` panel/API/catalog entry over `docs/features/chaseos_not_built_backlog.md`. The parser-backed output currently reports 43 NB rows, 17 implemented-or-preview, 26 blocked-or-gated, 0 needs-review, and 43 Studio-wired-or-mapped rows. UI/UX proof is recorded at `07_LOGS/Visual-QA/2026-06-12-nb001-043-release-matrix-closeout/index.html` with screenshot `release-matrix-closeout.png` and sidecar `summary.json`. This is an inspection surface only: no provider call, runtime dispatch, browser control, approval consumption, Agent Bus task creation, host mutation, external delivery, or canonical promotion is performed.

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
| NB-005 | Phase 9 second-wave features | Preview / Partial | No longer blanket-deferred: show the readiness/proof surfaces that exist, but keep execution/score application gated. |
| NB-006 | Agent Memory Architecture file structure | Preview / Partial | Show memory status; do not block on full Layers C/D. |
| NB-007 | Agent Identity Ledger implementation | Post-V1 / Preview | Can show planned identity ledger. |
| NB-008 | Runtime Navigation Map accumulation | Preview / Partial | Useful for agents; not user-facing blocker. |
| NB-009 | Multi-Repo / Multi-Directory policy enforcement | Preview / Partial | Public user can start single workspace; multi-repo can be later. |
| NB-010 | Layer C durable generated artifacts | Post-V1 | Promotion path can remain future. |
| NB-011 | Persisted Studio graph storage | Preview / Partial | Read-only/cache status is enough for V1; full refresh/write later. |
| NB-012 | Real target-folder/file workspace upgrade execution | Post-V1 / Blocked | Risky migration executor; not V1 blocker. |
| NB-013 | Runtime action execution | Preview / Partial | Show action envelopes plus any approval-gated executor proof; no uncontrolled execution. |
| NB-014 | Runtime/adapter activation | Preview / Partial | Runtime/gateway/daemon controls may show operator-confirmed activation posture; broad ambient activation no. |
| NB-015 | Core export target restoration/revalidation | Ship-Minimum / Approval-gated | 2026-06-12 recovery proves scanner-clean local export readiness: 145 candidates/previews, 0 scanner blockers, manual review artifact present, target absent, and approval request ready. Actual local export still needs operator approval ref + `--confirm`; Git/publication remain separate gates. |
| NB-016 | Public Core repo gates | Ship / Decision / Approval-gated | 2026-06-12 decision packet and UI proof now expose the repo-gate status without performing publication: current workspace Git/remote facts are known, no license file is present, public Core `.gitignore` policy and sanitized target/repo binding still need operator approval, and no export/Git init/commit/push/publication/canonical promotion occurred. |
| NB-017 | Broader Gate coverage beyond Anthropic lane | Preview / Partial | 2026-06-12 bounded proof exposes a read-only Gate side-effect coverage matrix for gateway, Studio/operator, lifecycle/host, and browser-action lanes across Approvals, Settings, and Browser Runtime. Gate policy/allowlist mutation, approval consumption, provider/browser/runtime execution, Agent Bus writes, host mutation, external delivery, and canonical promotion remain blocked/gated. |
| NB-018 | Live browser acquisition and connector/API acquisition expansion | Post-V1 / Preview | Useful but not needed for first public users; 2026-06-12 bounded proof shows staged Sources connector readiness and Browser Runtime acquisition boundaries are inspectable, while live connector/API calls, arbitrary browser acquisition, credential/session access, approval consumption, Agent Bus writes, external delivery, and canonical promotion remain gated. |
| NB-019 | Memory candidates / action-ready packets / delivery-ready packets | Preview / Partial | Read-only packet-readiness proof now surfaces the review-center contract across Context Import, Review Queue, and Missions; live memory apply, approval consumption, Agent Bus writes, runtime dispatch, external delivery, and canonical promotion remain gated. |
| NB-020 | Outcome scoring and scheduler integration | Post-V1 | Not first-user blocker. |
| NB-021 | SBP consumer wiring | Preview / Partial | Briefings can be partial/upcoming. |
| NB-022 | Full standalone governed Studio product experience | Ship | Central V1 blocker; recovery proof now shows mounted route/status/catalog/legal-source evidence, so this is not empty/deferred. It still must pass launch, copy, legal/privacy, package, leak/smoke, and release verdict proof before beta-ready. |
| NB-023 | Branded installer/logo/icon packaging | Ship-Minimum / Decision | Need at least credible branding and download packaging; signing can be staged. |
| NB-024 | Signing/startup/release/host mutation follow-through | Blocked / Decision | Signing/startup may be post-beta; release packaging must be explicit. |
| NB-025 | Real provider/runtime/browser execution or explicit deferral | Ship-Minimum | 2026-06-12 recovery proof splits this into ready runtime-dispatch posture plus explicit provider/browser/external-runtime deferrals. Studio Chat production operator dispatch and Agent Bus/canonical-writeback readiness are wired; live provider/model calls, browser-runtime production closeout, and external-runtime setup must remain labeled blocked/gated unless separately approved. |
| NB-026 | Real target workspace upgrade/migration or explicit deferral | Ship-Minimum | Must explicitly defer if not built. |
| NB-027 | Live client run / live external delivery / live revenue workflow authority | Post-V1 / Blocked with proof | 2026-06-12 bounded proof shows VentureOps local readiness and live-client proof posture are inspectable, but real-world delivery/revenue remains blocked: `real_world_delivery_revenue_complete=false`, `safe_to_mark_real_world_delivery_revenue_complete=false`, live revenue workflow proof/final bundle validation are missing, and no external send, CRM/payment mutation, provider/browser action, revenue claim, marketplace/publication action, or canonical promotion occurred. |
| NB-028 | MCP surface expansion | Post-V1 / Preview | MCP V1 exists; expansion later. |
| NB-029 | Companion surface | Preview / Partial | Studio `#/companion-surface` is mounted as a read-only companion status desk; mobile/tablet, autonomous routing, approval consumption, Agent Bus writes, and memory-write expansions remain gated. |
| NB-030 | Voice Mode | Preview / Partial | Studio `#/voice-mode` is mounted as a read-only companion-first voice page; live mic, transcription/synthesis, provider/model, browser-control, memory-write, and runtime handoff remain blocked if labeled honestly. |
| NB-031 | AISO | Local Dev Complete / Real-Test Closeout Ready | Bounded prepare/rename/package proof path is implemented: declared-root locator, dry-run evidence, email/portal preview screenshots, Studio Media Rename Review, explicit rename approval, explicit zip package approval, exact-once proof records, and closeout readiness reporting. Not a public beta blocker unless marketed as live submission; live provider/email/browser/upload authority remains gated. |
| NB-032 | Live Operator Shell | Ship-Minimum / Preview | Expected product surface is no longer a generic deferred/zero-built item: Runtime Shell, runtime controls, Agent Bus status, and Action Center preview/readiness contracts support a governed operator-shell posture. V1 still needs product-grade UX labels and must not imply raw terminal, provider, browser, approval, host, or canonical authority. |
| NB-033 | Visual shell / Agent Operating Console | Preview / Partial | Visual-shell substrate is present across Studio/Chat/Companion/Voice/Runtime/Browser/App Launcher surfaces, but dedicated `#/agent-operating-console` is not mounted yet; reconcile into a bounded mission-control product lane, not broad desktop control. |
| NB-034 | Phase 11 Chat live provider/runtime/browser dispatch | Ship-Minimum / Decision | Recovered split truth: Chat/Agent Bus dispatch readiness is production-ready in live CLI output, while provider execution is approval-preview-only, browser-runtime production closeout is blocked on internal panel evidence, and external runtime readiness is blocked on setup. V1 can ship only if these distinctions are visible in Chat/Action Center UI. |
| NB-035 | Broad automated agent execution | Preview / Partial | Bounded autonomy is intended and now has an explicit product label contract: `Live / local` mission outputs, `Preview / governed` Agent Bus/reviewer-gate lanes, and `Blocked / approval required` ambient/provider/browser/external/canonical authority. Public beta may show this governed status slice; it must not market broad autonomy. |
| NB-036 | Public beta acceptance gate | Ship | Release blocker until Ship and Ship-Minimum evidence is verified; 2026-06-12 proof artifact turns the gate into concrete evidence rows but preserves NO-GO until package/domain/leak/smoke/legal gates are green. |
| NB-037 | Core/Personal structural separation | Ship-Minimum / Approval-gated | Active structural split now has manifest/templates plus scanner-clean dry-run/readiness proof. V1 can truthfully expose the split/export posture if it labels local export approval, Git init, public repo, license, push/publication, and canonical promotion as separate blocked gates. |
| NB-038 | Visual Capture Markdown Ingestion | Preview / Partial | Capture-to-source-pack lanes may be visible if labeled governed/local; downstream promotion/writeback remains gated. |
| NB-039 | Sub-Agent Presets | Preview / Partial | Useful operator/product UX; live dispatch must be allowlisted and bounded. |
| NB-040 | Product Workflow Packs / Missions | Ship-Minimum / Preview | Workflow-pack cards are central product UX and should appear as their own feature-family row. Preview-live scope is local Missions/Workflow Packs cards, run records, approval/resume evidence, proof cards, and clickthrough evidence; paid marketplace, hosted publication, external delivery, remote install, and approval consumption remain blocked. |
| NB-041 | ChaseOS Creator Engine | Preview / Partial | Roadmap/product preview; media/provider generation and posting are not beta blockers unless marketed live. |
| NB-042 | Adaptive Runtime Surface Layer | Preview / Partial | Read-only runtime-surface registry/routing inspection supports trust labels; execution/authority grants remain gated. |
| NB-043 | Chaser Forge extension install/import contract | Preview / Decision | Local import-intent, manifest/package validation, permission disclosure, and sandbox/import review handoff can be beta-visible. Live remote install, payment/license checkout, hosted publication, network fetch/upload, seller accounts, and approval consumption require an explicit future release decision. |

## 4. Feature-family V1 classification

| Feature family | V1 class | V1 requirement |
|---|---|---|
| Source Intelligence Core | Ship-Minimum | Existing capability should be represented clearly; first-user docs explain what source intake means. |
| Capture / Acquisition + Normalization | Preview / Partial | Local/import readiness plus NB-018 staged connector/browser-readiness proof may be shown; no overclaiming live connectors or arbitrary browser acquisition. |
| AOR | Preview / Partial | Show bounded workflow status and the NB-035 governed-by-design labels; avoid claiming unrestricted automation. |
| Workspace Mode Layer | Ship-Minimum | Product-facing explanation and settings/status integration. |
| Interface / Experience Layer / Studio | Ship | Main V1 blocker. |
| ChaseOS Pulse | Preview / Partial | Status/page/card; not required as fully live proactive system. |
| Chaser Forge | Preview / Partial | Marketplace direction visible; domain/live index pending. |
| Browser Runtime / SiteOps | Preview / Partial | Readiness/proof/status only unless live bounded executor is separately verified. |
| MCP | Preview | Mention advanced/developer integration; not first user required. |
| VentureOps / Mission Mode | Preview / Partial | Good founder/business wedge; external revenue delivery remains blocked. |
| AISO | Upcoming | Roadmap/mission preview only. |
| Chaser Agent | Upcoming / Post-V1 | Future first-party runtime/agency harness. |
| Live Operator Shell | Ship-Minimum / Preview | Show the governed shell/control posture backed by runtime controls, Agent Bus status, and preview/readiness evidence; no raw terminal or broad authority. |
| Agent Operating Console / visual shell | Preview / Partial | Productize existing Studio/runtime/companion/voice/browser visibility as an action-envelope console; dedicated Agent Operating Console route still needs bounded mount proof and must not become desktop control. |
| Public beta acceptance gate | Ship | Explicit gate across standalone launch, labels, docs/legal/privacy, repo hygiene, and smoke proof. |
| Core/Personal structural separation | Ship-Minimum / Approval-gated | Public-safe core/export posture is now backed by scanner-clean local-export readiness proof; full export execution, public repo, Git, license, push/publication, and canonical promotion remain gated and must be labeled clearly. |
| Visual Capture Markdown Ingestion | Preview / Partial | Show governed local capture/readiness where present; keep downstream promotion/writeback gated. |
| Sub-Agent Presets | Preview / Partial | Productize as bounded preset selection/task-shaping, not uncontrolled autonomous dispatch. |
| Product Workflow Packs / Missions | Ship-Minimum / Preview | Major product navigation lane with live/preview/blocked distinctions: local Missions UI and proof artifacts may be visible; payment, external delivery, hosted publication, remote install, and approval consumption must remain disabled or future-labeled. |
| ChaseOS Creator Engine | Preview / Partial | Roadmap/preview product lane; live media generation/posting/provider execution must be gated. |
| Adaptive Runtime Surface Layer | Preview / Partial | Read-only runtime surface trust/routing labels support safer UI; no execution/authority grant. |
| Chaser Forge extension install/import contract | Preview / Decision | Local import-intent and permission preview can be beta-visible; remote install/payment/hosted publication/approval consumption need a separate release decision. |

## 5. Monetization-readiness classification

| Monetization component | V1 class | Required now | Deferred |
|---|---|---|---|
| Landing page/domain | Ship-Minimum | Domain selected; landing copy; waitlist/download/contact. | Full webapp account system. |
| Subscription plans | Preview / Decision | Pricing hypothesis and plan labels. | Billing implementation. |
| License/account gate | Post-V1 / Decision | Decide open-core/source-available boundary. | Stripe/license server. |
| Credits | Post-V1 | Define credit concept only if managed agents/provider calls exist. | Credit accounting and enforcement. |
| Marketplace paid packs | Preview / Partial | Chaser Forge static/public index path; free/demo packs. | Payments, seller accounts, revenue share. |
| Managed Chaser Agent / agency | Post-V1 | Position as premium future lane. | 24/7 hosted runtime product. |
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

2026-06-12 NB-022/NB-036 recovery proof: `07_LOGS/Visual-QA/2026-06-12-nb022-nb036-studio-beta-acceptance/2026-06-12-nb022-nb036-studio-beta-acceptance.html` and JSON sidecar record the product-facing status slice. Current proof state: 12/12 required Studio routes mounted, 12/12 required routes catalog-labeled after adding the Studio Status label, privacy/terms/beta-warning source docs present, public beta verdict still NO-GO pending packaging, smoke/leak, domain/package, and final acceptance proof.

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


*Graph links: [[Visual-QA-Index]] · [[Agent-Activity-Index]] · [[Build-Logs-Index]] · [[Workflow-Proofs-Index]] · [[Hermes-Runtime-Profile]] · [[HERMES]]*
