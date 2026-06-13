---
title: ChaseOS V1 Public-User Beta Acceptance Checklist
created: 2026-05-30
updated: 2026-06-12
runtime: hermes-optimus
type: release-acceptance-checklist
status: DRAFT / V1-A1 PM HANDOFF
scope: V1 public-user beta release gate, cutline, acceptance checklist
links:
  - [[ChaseOS-V1-Release-Cutline]]
  - [[chaseos_v1_release_readiness_matrix]]
  - [[Feature-Register]]
  - [[Chaser-Forge]]
  - [[HERMES]]
  - [[Hermes-Runtime-Profile]]
---

# ChaseOS V1 Public-User Beta Acceptance Checklist

> V1-A1 PM handoff. This turns the release cutline and readiness matrix into a final public-user beta acceptance checklist without expanding scope.

## 1. Product naming boundary

Use this product identity consistently in public-user beta copy, Studio UI, docs, and release notes:

| Name | V1 role | Acceptance rule |
|---|---|---|
| ChaseOS | Platform/product: local-first AI operating system and agent control plane. | Public product name. Do not reduce it to a chatbot, vault, or template pack. |
| ChaseOS Studio | Standalone app / graphical control panel for ChaseOS. | Main V1 user-facing app. |
| Chaser Forge | Governed marketplace / extension and workflow-pack distribution layer. | V1 preview/partial path unless public domain/index is live. |
| Chaser Agent | Future first-party always-on runtime / managed agent family. | Upcoming/Post-V1. Must not block beta. |
| Hermes / OpenClaw | Existing bounded runtime-instance lanes under ChaseOS governance. | Internal/proof/runtime-compatibility lanes, not product brand. |

## 2. Release gate verdict

Current PM verdict: **not beta-ready until Ship and Ship-Minimum gates below are verified**.

The beta may still show Preview, Upcoming, and Blocked features if they are clearly labeled, safe, and non-deceptive. V1 public-user beta must not imply that external delivery, payments, broad browser automation, marketplace purchase flows, Chaser Agent, or uncontrolled runtime execution are live unless separately proven and approved.

## 3. Ship gates — must work for first public users

| Gate | Acceptance checklist | Evidence needed |
|---|---|---|
| Standalone ChaseOS Studio launch | App opens from a public-user path; user can select or detect a vault/root; no `No vault root found`; no hardcoded `C:\\Users\\chaseos`, `<WSL_HOME>`, or private machine assumptions in public flow. | Launch smoke result plus path/leak scan. |
| Home / Command Center | First screen explains ChaseOS in under 60 seconds; shows current capability, readiness, first useful action, and preview/upcoming states without internal-only jargon. | Route/page audit and screenshot or static render proof. |
| Settings / privacy / providers | User can see local data location, provider/API-key status, runtime status, privacy/data controls, open-folder/export/reset/help, and legal/privacy links. | Settings smoke plus privacy/legal page existence. |
| Privacy / terms / AI warnings | Privacy notice, terms/disclaimer, AI limitations warning, personal-data warning, external-send/upload/credential/payment warnings. | Linked docs/pages included in app and README. |
| Public repo/package hygiene | No secrets, private paths, private IDs, or internal-only claims in public repo/package; README matches actual beta capability. | Secret/path/personal-context scan and README audit. |
| Release smoke suite | Repeatable command set validates launch/routes/settings/catalog/static product states and leak scans. | One recorded successful smoke run. |

## 4. Ship-Minimum gates — may be thin, but cannot be absent

| Gate | Minimum acceptable beta shape | Evidence needed |
|---|---|---|
| First-run onboarding | Simple page/modal explains local-first setup, data location, optional provider setup, what works now, and what is preview/upcoming. | Onboarding route/page proof. |
| Feature Catalog / Workflow Packs | Cards for major features with consistent Live/Partial/Upcoming/Blocked labels; no empty dead pages. | Catalog route audit. |
| Docs / Inspector | User can browse/search local docs or at minimum open the public docs/help path; broken paths handled gracefully. | Docs route/search/open-folder proof. |
| Source Intelligence Core | Represented clearly as an existing/local capability or documented workflow; no promise of live external acquisition unless proven. | Feature card and docs copy. |
| Workspace Mode Layer | Settings/status explain workspace/vault path and local-first model. | Settings/onboarding copy proof. |
| Public website/landing | Domain or landing path selected; page explains product, download/waitlist/contact, privacy stance, and current beta limitations. | Landing page/domain decision. |
| Provider/runtime/browser execution posture | Either live executor path works and is bounded, or UI explicitly marks it deferred/preview. No fake provider calls. | Readiness output or explicit deferral copy. |
| Workspace upgrade/migration posture | Either safe upgrade flow works with approval, or UI explicitly marks migration as deferred/preview. | Deferral copy or approval-gated proof. |

## 5. Preview / Partial — allowed in beta if honest and bounded

| Area | Beta posture | Acceptance rule |
|---|---|---|
| Chat / Agent Control Panel | Preview/Partial. | Show runtime readiness and safe buttons/commands only; unknown or dangerous actions must be preview-only, disabled, or approval-gated. |
| Graph / Memory visibility | Preview/Partial. | Read-only graph/memory/status is acceptable; writes/promotions must be gated/disabled. |
| Chaser Forge | Preview/Partial. | Local marketplace proof and static/public index path may be visible; live hosted fetch waits for domain/public `index.json`. |
| Capture / Acquisition + Normalization | Preview/Partial. | Local/import readiness only; do not overclaim live connectors. |
| AOR/runtime adapter authority | Preview/Partial. | Show bounded workflow status and NB-035 governed-by-design labels: `Live / local` mission artifacts, `Preview / governed` Agent Bus/reviewer-gate lanes, and `Blocked / approval required` ambient/provider/browser/external/canonical authority. No uncontrolled execution. |
| ChaseOS Pulse | Preview/Partial. | Show schedule/readiness/status honestly; full proactive intelligence is not required for beta. |
| Browser Runtime / SiteOps | Preview/Partial. | Readiness/proof/status only unless live bounded executor is separately verified. |
| VentureOps / Mission Mode | Preview/Partial. | Founder/business positioning is allowed; external revenue/client delivery remains blocked unless approved. |
| MCP | Preview. | Developer/advanced integration mention only; V1 server/hub readiness can be shown, broader expansion not required. |
| Agent role cards / memory architecture / runtime maps | Preview/Partial. | Useful governance surfaces; not a beta blocker unless the app claims they are live product features. |
| Voice Mode | Preview/Partial. | Mounted page/local browser-native surface may be shown; live microphone/provider/runtime handoff must be labeled gated unless proven. |
| Companion Surface | Preview/Partial. | Studio companion/roster/readiness may be shown; mobile/tablet/memory-write/execution-routing expansions remain gated. |
| Phase 11 Chat live dispatch lanes | Preview/Partial / Decision. | Runtime-dispatch foundation may be shown; provider/browser/target-mutation/result-writeback lanes must be proven or deferred. |
| Live Operator Shell / Agent Operating Console | Ship-Minimum / Preview. | A governed visual control surface may be shown if it uses action envelopes and no fake shell/provider/browser authority. |
| Visual Capture Markdown Ingestion | Preview/Partial. | Governed local capture/source-pack readiness can be shown; downstream writeback/promotion stays gated. |
| Sub-Agent Presets | Preview/Partial. | Presets can shape bounded task packets; they must not imply uncontrolled dispatch. |
| Product Workflow Packs / Missions | Ship-Minimum/Preview. | Product navigation should expose packs/missions as their own feature-family row. Local Studio cards/run records/proof artifacts may be shown as preview-live; external delivery, payment, hosted publication, remote install, and approval consumption stay blocked unless separately proven and approved. |
| Creator Engine | Preview/Partial. | Product preview allowed; live generation/posting/provider execution must be labeled gated. |
| Adaptive Runtime Surface Layer | Preview/Partial. | Read-only runtime-surface trust/routing labels allowed; execution/authority grant remains blocked. |
| Chaser Forge extension install/import contract | Preview/Decision. | Local import-intent, package/manifest validation, permission disclosure, and review handoff may be shown; live remote install, hosted publication, payment/license checkout, seller accounts, network fetch/upload, and approval consumption require a separate release decision. |

## 6. Upcoming / Post-V1 — must not block beta

| Area | Beta label | Rule |
|---|---|---|
| Chaser Agent | Upcoming / Post-V1 | Future first-party runtime or managed-agent layer; do not present as required for Studio beta. |
| AISO | Upcoming / active `/goal` | Roadmap/mission preview plus local dry-run proof chain; do not claim live submission/send/upload. |

| Full Phase 9 second-wave features | Post-V1 | Do not let second-wave automation delay Studio beta. |
| Layer C durable generated artifacts | Post-V1 | Promotion path can remain future. |
| Outcome scoring and scheduler integration | Post-V1 | Not first-user beta critical. |
| Credits, license server, paid marketplace packs, seller accounts | Post-V1 / Decision | Define direction; implementation can wait. |
| Team/business/enterprise collaboration | Post-V1 | Mention high-level only. |
| Managed Chaser Agent / agency | Post-V1 | Premium future/agency wedge. |
| Broad automated agent execution | Post-V1 / Governed-by-design | Do not unblock as ambient autonomy; beta can show the bounded mission/workflow/Agent Bus/reviewer-gate status slice only, with provider/browser/account mutation, external delivery, approval consumption, host mutation, and canonical promotion labeled blocked unless separately approved. |
| Core/Personal full public export | Post-V1 / Decision | Active split can be documented; full public export/repo publication remains gated until scanner-clean proof. |

## 7. Blocked / Decision — beta gate only when trust/install depends on it

| Decision/blocker | Beta impact | Required decision or proof |
|---|---|---|
| Public repo/license/open-core boundary | Blocks public release packaging if unresolved. | Choose public/open-core/source-available posture and update README/license messaging. |
| Domain/landing path | Blocks public distribution trust if absent. | Select domain or interim landing/waitlist path; decide where Forge public index will live. |
| Chaser Forge live public index | Does not block beta if labeled preview; blocks live marketplace claim. | Domain/public `index.json` packet before claiming live hosted marketplace. |
| Signing/startup/release packaging | Blocks installer trust if no credible distribution story exists. | Decide beta packaging minimum: unsigned local beta, signed installer later, or hosted download path. |
| External delivery / CRM / payments / marketplace publication | Does not block local beta; blocks monetized/live external workflows. | Explicit approval gates, credentials, service setup, and legal/payment decisions. |
| Provider/API-key/live browser execution | Blocks only if UI claims live execution. | Either verify bounded execution or clearly defer/preview it. |
| Hardcoded path / secret / private-context leakage | Blocks public beta. | Complete scan and fix or document zero findings. |

## 8. Minimum beta acceptance runbook

Before public-user beta can be called ready, complete and record these checks:

1. Studio launch smoke from a non-personal/public-user path.
2. Route/page audit: Home, onboarding, Settings, Feature Catalog, Docs/Inspector, Chat/Agent Control, Forge preview, legal/privacy.
3. Copy audit: README, Foundation/product copy, app UI text, release notes, marketplace wording.
4. Leak audit: secrets, private IDs, hardcoded personal paths, private machine names, internal-only Discord/Hermes/OpenClaw claims in public surfaces.
5. Release-class audit: every visible feature card has exactly one public status label: Ship/Live, Ship-Minimum/Available, Preview/Partial, Upcoming, or Blocked/Decision.
6. Safety audit: dangerous actions disabled, preview-only, or approval-gated; no fake provider/runtime/browser execution.
7. Domain/package audit: landing/download/waitlist path selected; Forge public-index path named even if preview.
8. Smoke evidence recorded in build log or release-readiness note.

## 8A. 2026-06-12 NB-022/NB-036 recovery evidence slice

This recovery pass converts the standalone governed Studio and public beta acceptance rows from stale Deferred/Partial wording into an explicit Ship / Ship-Minimum evidence checklist. Product-facing proof artifact: `07_LOGS/Visual-QA/2026-06-12-nb022-nb036-studio-beta-acceptance/2026-06-12-nb022-nb036-studio-beta-acceptance.html`; machine-readable sidecar: `07_LOGS/Visual-QA/2026-06-12-nb022-nb036-studio-beta-acceptance/2026-06-12-nb022-nb036-studio-beta-acceptance.json`.

| Evidence row | Current proof | Beta verdict impact |
|---|---|---|
| Standalone Studio route surface | 12/12 required product routes are mounted in `runtime/studio/shell/frontend/index.html`. | Supports NB-022 Ship evidence; not final launch/package proof. |
| Feature/status labeling | 12/12 required routes are present in the fallback feature catalog with Live/Local/Inspect/Approval-gated labels after adding the `studio-status` / Studio Status catalog entry. | Supports Ship-Minimum labeling; still requires full route/copy smoke before beta-ready. |
| Legal/privacy/trust source docs | Site map, privacy/security/terms baseline, and public launch checklist all exist and include privacy/terms/beta-warning posture. | Trust copy source exists; public app/README/legal-link wiring still needs final smoke. |
| Public beta gate | NB-036 remains Ship and NO-GO until Ship and Ship-Minimum gates are verified. | Prevents overclaiming public beta readiness. |
| Packaging/release smoke | JSON-shape crash hardening landed for Visual-QA report scanners and focused tests pass; latest fix-forward smoke reports packaging readiness `status=ready_for_local_packaging_proof` with `icon_configured=true`, and `mvp-closure-gate --json` returns inside the WSL smoke budget with `closed=false`. Current blockers are `decision_packet_missing_or_invalid` and `pass10b_installer_zip_proof_not_complete`. | Blocks final beta-ready verdict until decision-packet and installer/package proof close; route remaining release proof to packaging/release lanes instead of deferring NB-022/NB-036 generically. |

Authority preserved: this slice did not perform provider calls, browser/account mutation, host mutation, external delivery, approval consumption, canonical promotion, or release/package writes.

## 9. Proposed follow-on Track A gates

These are PM/reviewer gates, not implementation scope for V1-A1:

| Gate | Owner lane | Purpose |
|---|---|---|
| V1-A2 Studio route/page audit | analyst | Map every Studio route/page to Ship/Preview/Upcoming/Blocked and identify empty/broken pages. |
| V1-A3 public-doc/copy/leak audit | analyst | Audit README, project foundation, app copy, and public docs for public-user language and private leakage. |
| V1-A4 landing/legal/pricing copy | writer | Draft landing page, pricing hypothesis, privacy/TOS warnings, and beta limitation copy. |
| V1-A5 launch/path/secret smoke | ops | Run hardcoded path, secret, private context, and launch-smoke checks. |
| V1-A6 final release-gate review | reviewer | Convert checklist evidence into final V1 blocker verdict. |

## 10. Proposed doc patches

1. `06_AGENTS/ChaseOS-V1-Release-Cutline.md`: add this acceptance checklist as Track A output 5 and mark V1-A1 checklist handoff available.
2. `docs/features/chaseos_v1_release_readiness_matrix.md`: link this checklist near the blocker list and clarify that the matrix is now source material for the final checklist, not the final release verdict.
3. Public README/product copy later: use the naming boundary in Section 1 so ChaseOS, ChaseOS Studio, Chaser Forge, and Chaser Agent do not collapse into one unclear brand.

## 11. PM handoff summary

V1 public-user beta should be cut around a truthful ChaseOS Studio product shell, local-first setup, settings/privacy/provider visibility, feature catalog status labeling, docs/inspector access, public repo hygiene, and a repeatable smoke/leak suite. Chaser Forge can ship as preview/partial, Chaser Agent and AISO remain upcoming, and live external delivery/payments/browser/runtime authority must stay blocked or preview-only unless separately proven. The next release decision should be evidence-driven: the beta is ready only after Ship and Ship-Minimum gates have recorded proof and no public-trust blocker remains.

## 12. Graph links

[[ChaseOS-V1-Release-Cutline]] · [[chaseos_v1_release_readiness_matrix]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[Chaser-Forge]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Agent-Activity-Index]]
