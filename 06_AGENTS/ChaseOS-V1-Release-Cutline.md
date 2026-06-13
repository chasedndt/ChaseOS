---
title: ChaseOS V1 Release Cutline
created: 2026-05-30
updated: 2026-05-30
latest_decision: open-local-first with paid hosted/marketplace/managed-runtime layers
runtime: hermes-optimus
type: release-control
status: DRAFT / TRACK A STARTED / PRODUCTIZATION CUTLINE
scope: V1 public-user beta readiness, product positioning, monetization framing, domain/marketplace linkage
links:
  - [[Feature-Register]]
  - [[Feature-Fit-Register]]
  - [[chaseos_v1_public_beta_acceptance_checklist]]
  - [[chaseos_not_built_backlog]]
  - [[Chaser-Forge]]
  - [[Artifact-Intelligence-Submission-Operator]]
  - [[HERMES]]
  - [[Hermes-Runtime-Profile]]
---

# ChaseOS V1 Release Cutline

> Track A release-control document for resuming ChaseOS development without falling into the infinite-feature loop.

## 1. Decision

ChaseOS should now move from feature expansion into a **V1 productization and release-readiness program**.

The next development phase is not “build every planned feature.” The next phase is:

```text
make ChaseOS installable, explainable, safe, product-facing, privacy-aware, monetizable, and truthful for first public users.
```

A feature may be visible in V1 without being fully implemented if it is clearly labeled as preview, upcoming, blocked, or local-only.

## 2. Product identity stack

Use these names consistently:

| Name | Role | V1 framing |
|---|---|---|
| **ChaseOS** | The product/platform: a local-first AI operating system and agent control plane. | Public product name. |
| **ChaseOS Studio** | The standalone app / graphical control panel for ChaseOS. | Main user-facing app. |
| **Chaser Forge** | The governed marketplace / extension and workflow-pack distribution layer. | V1 preview/partial marketplace lane; domain-linked once public index exists. |
| **Chaser Agent** | Future first-party 24/7 agent harness/runtime developed by ChaseOS. | Post-V1 / upcoming runtime family; do not block V1. |
| **Hermes / OpenClaw** | Existing bounded runtime-instance lanes integrated under ChaseOS governance. | Internal/proof/runtime compatibility lanes; not the product brand. |

Boundary: do not let “Chaser Agent” confuse V1. V1 ships ChaseOS Studio plus a governed local-first control plane. Chaser Agent can become a future premium/runtime layer once the product shell and marketplace path are stable.

## 3. Domain strategy

Operator decision update (2026-05-31): the selected primary public launch domain is:

```text
https://chaseos.ai
```

`chaseos.ai` is the selected public launch domain. The prior `chaseos.systems` lane is superseded as primary and may only be treated as an optional secondary/alias lane if separately purchased and configured.

V1 should use path-based pages first:

```text
chaseos.ai/
chaseos.ai/studio
chaseos.ai/forge
chaseos.ai/standards
chaseos.ai/pricing
chaseos.ai/docs
chaseos.ai/open-core
chaseos.ai/download
chaseos.ai/privacy
chaseos.ai/security
chaseos.ai/waitlist
chaseos.ai/roadmap
chaseos.ai/support
chaseos.ai/terms
```

`chaseos.ai` is the selected primary public launch domain. `chaseos.systems` is superseded as primary and may later be a secondary redirect, standards/ecosystem alias, or defensive domain if purchased. Do not use get/try/use-prefixed domains, `chaseos.dev`, or `chaseos.app` as the public product domain.

Keep **ChaseOS** as the product/platform and **ChaseOS Studio** as the app. This preserves the operating-system thesis.

## 4. Monetization model

ChaseOS can be open-source or source-available while still monetizing through hosted services, marketplace distribution, premium runtime orchestration, team/company features, and paid agent credits.

### Recommended V1 monetization thesis

```text
Local-first core + paid cloud/account layer + marketplace + premium agent/runtime services.
```

### Revenue layers

| Layer | What users pay for | V1 posture |
|---|---|---|
| Personal Pro subscription | ChaseOS Studio features, account/license, updates, premium templates/workflows, advanced local control panel. | Plan now; implement license/account later if needed. |
| Agent/runtime credits | Optional managed agent minutes, hosted model calls, long-running remote workers, premium orchestrator lanes. | Future; do not block local V1. |
| Chaser Forge marketplace | Paid workflow packs, templates, agent presets, extensions, and domain-specific operating kits. | Chaser Forge already maps here; public domain/index is needed. |
| Team / Founder workspace | Multi-project/team control plane, collaboration, approval logs, shared runtime policies. | Post-V1 business tier. |
| Managed 24/7 agency / Chaser Agent | Done-for-you or always-on operator harness for founders/businesses. | Post-V1 high-ticket / agency wedge. |
| Enterprise/private deployment | Local/private install, security review, custom runtime adapters, governance controls. | Later B2B path. |

### Open-source vs commercial recommendation

For V1, prefer:

```text
open-core / source-available product strategy
```

Meaning:

- Public GitHub repo for trust, developer adoption, issue tracking, docs, and community.
- Keep local-first core inspectable.
- Monetize hosted account services, managed runtime lanes, marketplace distribution, premium packs, teams, and support.
- Avoid committing too early to a license that prevents future commercial packaging.

Do not make the marketplace, licensing/account backend, premium runtime orchestration, paid extension distribution, or hosted agent infrastructure fully unrestricted if the business model depends on them.

### Open-source / paid product split

Operator decision context: `https://chaseos.ai` is the selected primary public launch domain. `chaseos.ai` is the selected primary public launch domain; `chaseos.systems` is optional future secondary/alias only. Availability, purchase, RDAP, DNS, and legal/mark status must still be verified outside this document before public claims beyond domain selection/purchase.

Recommended split:

| Surface | Recommended openness | Why | Monetization boundary |
|---|---|---|---|
| **ChaseOS Core** | Open-source or source-available core repository. | Trust, auditability, local-first adoption, developer community, and compatibility with the current agent-market trend. | Paid convenience, support, managed services, and team/cloud layers sit around it. |
| **ChaseOS Studio desktop app** | Source-available/open-core client with public issues/docs. | Studio is the local GUI/control plane users need to trust on their machine. | Pro gates can apply to convenience features, cloud sync/account, premium workflow packs, team governance, and managed runtimes — not basic local control. |
| **Chaser Agent** | Open-source or source-available runtime harness. | Runtime agents are trending open and need auditability like Hermes/OpenClaw; closed black-box local agents reduce trust. | Monetize managed hosting, hosted workers, support, templates, SLA, team deployment, and done-for-you agency operation rather than the base harness alone. |
| **Workflow packs / mission packs** | Mixed: free core packs plus paid premium packs. | Marketplace needs useful free examples and paid domain expertise. | Chaser Forge can sell certified/premium packs, private catalogs, updates, and support. |
| **Chaser Forge catalog/client protocol** | Open/local install protocol plus public free index. | Developers need to publish/install packs without lock-in. | Paid distribution, license checks for premium packs, private team registries, revenue share, and certification remain commercial. |
| **Hosted account / license / sync / update services** | Commercial SaaS service. | This is the cleanest subscription boundary. | Pro subscription, team seats, marketplace purchases, managed runtime credits. |
| **Cloud or managed agent runtime** | Commercial service built around open runtimes. | Users can self-host, but many will pay for reliability, uptime, queues, dashboards, logs, and support. | Runtime credits, monthly managed plans, agency tier, enterprise/private deployments. |
| **Enterprise/private deployment** | Commercial contracts; code visibility can be negotiated. | Businesses pay for governance, security, custom adapters, and support. | Annual contracts, onboarding, compliance, custom integrations. |

Plain-language positioning:

```text
ChaseOS is open/local-first where trust matters. Users can inspect and run the core themselves.
ChaseOS charges for convenience, hosted infrastructure, premium workflow packs, managed agents, teams, and support.
```

Do not frame the subscription as “pay to use your local AI OS.” Frame it as:

```text
Free: run ChaseOS locally.
Pro: get the best maintained Studio experience, premium workflow packs, cloud/account conveniences, marketplace access, and managed agent options.
```

## 5. V1 release classes

| Class | Definition | Blocks V1? |
|---|---|---|
| **Ship** | Must work for first public users. | Yes. |
| **Preview / Partial** | Product-facing, visible, honest limitations, no fake authority. | No, unless broken/confusing. |
| **Upcoming** | Roadmap/feature card/page only. | No. |
| **Blocked / Needs decision** | Requires domain, provider, secret, legal, signing, external service, or operator decision. | Only if it affects install, safety, or user trust. |
| **Post-V1** | Valuable but not necessary for first users. | No. |

## 6. V1 must-ship scope

These are the real V1 blockers:

1. **Standalone launch and onboarding**
   - ChaseOS Studio opens reliably.
   - Fresh instance/vault path is resolved or selected.
   - No hardcoded `<WINDOWS_USER_HOME>` / `<WSL_HOME>` assumptions in public paths.
   - First-run explains local-first setup.

2. **Product-facing Home / Command Center**
   - User understands what ChaseOS is in the first 60 seconds.
   - Shows live, partial, upcoming, and blocked status without internal-only jargon.
   - Gives a first useful action.

3. **Settings / Privacy / Providers**
   - Local data location.
   - Provider/API-key configuration status.
   - Runtime status.
   - Privacy/data warnings.
   - Export/reset/open-folder/help surfaces.

4. **Feature Catalog / Workflow Packs**
   - Major features appear as cards with status labels.
   - Upcoming features are not dead empty pages.
   - Chaser Forge / marketplace path is visible but honest.

5. **Chat / Agent Control Panel**
   - Honest runtime readiness.
   - Capability/readiness commands or buttons.
   - No fake provider calls.
   - Dangerous commands are preview-only unless executor exists.

6. **Docs / Graph / Memory visibility**
   - User can inspect their system.
   - Read-only graph/docs/search surfaces are stable.
   - Write/promote/mutate buttons are disabled, preview-only, or approval-gated.

7. **Safety and legal baseline**
   - Privacy notice.
   - Terms/disclaimer page.
   - AI limitations warning.
   - External-send/upload/trading/payment/credential warnings.
   - Clear statement that user controls local data and provider choices.

8. **Release smoke suite**
   - Launch smoke.
   - Route smoke.
   - Settings smoke.
   - Feature catalog smoke.
   - No secret/path leak scan.
   - README/setup validation.

## 7. V1 preview / partial scope

These can appear in V1 if honest:

- Chaser Forge marketplace / extension system: local proof and static-host handoff exist; `https://chaseos.ai/forge/index.json` is the selected public static-index target, but live hosted fetch remains approval-gated until upload, digest verification, and final approval packet exist.
- AISO: upcoming feature family; show as roadmap/mission preview only.
- Voice Mode: page/status preview if no microphone/provider integration exists.
- Browser Runtime / SiteOps: preview/local proof/readiness only unless live executor path is proven.
- Pulse / Scheduled Briefings: partial/proactive intelligence; show schedule/readiness state honestly.
- Runtime activation / adapter authority: show status and boundaries, not uncontrolled execution.
- Workspace migration/upgrades: preview/approval-gated only.
- External delivery / CRM / payments / marketplace publication: blocked until explicit live service setup and approval gates exist.

## 8. Product-facing marketplace path

The feature that links most directly to the domain and marketplace decision is **Chaser Forge**.

Current Chaser Forge truth from `docs/features/chaser_forge_mvp_extension_install_contract.md` and `Feature-Register.md`:

- local marketplace catalog and install proof exist,
- static-host publication files and upload handoff proof exist,
- published static index registration flow exists,
- live hosted fetch is deferred until official domain and public `index.json` packet exist,
- payment/license mutation remains blocked.

Therefore the domain should serve at least two things:

```text
/chaseos landing + download
/forge or forge.<domain> public marketplace index
/docs install/use docs
/account later for subscriptions/licenses/credits
```

## 9. Startup / valuation strategy

For startup positioning, ChaseOS should be framed as:

```text
The local-first AI operating system for builders who run projects with agents.
```

Not merely:

- an Obsidian vault,
- a chatbot,
- a workflow template,
- a second brain,
- a generic automation wrapper.

The investable thesis:

1. AI work is becoming multi-agent and fragmented.
2. Users need a private control plane for memory, permissions, workflows, and runtime activity.
3. ChaseOS owns the local-first operating substrate and product-facing Studio.
4. Chaser Forge creates an extension/workflow marketplace around that substrate.
5. Chaser Agent can become the managed always-on runtime/agency layer.
6. Monetization expands from Pro users to marketplace, teams, credits, managed agents, and enterprise/private deployments.

## 10. Non-negotiable anti-scope-creep rule

For V1:

> A feature may be important to the company without being allowed to block first-user release.

AISO, Chaser Agent, full browser automation, payments, live external delivery, marketplace payments, voice capture, CRM mutation, and full provider abstraction are strategic — but they are not allowed to block V1 unless the V1 user journey explicitly depends on them.

## 11. Immediate Track A outputs

Track A must produce:

1. This release cutline.
2. `docs/features/chaseos_v1_release_readiness_matrix.md`.
3. `docs/features/chaseos_v1_public_beta_acceptance_checklist.md`.
4. A Kanban/task batch for V1 productization implementation.
5. A reviewer gate that converts the matrix/checklist evidence into the true V1 blocker list.

## 12. Graph links

[[Feature-Register]] · [[Feature-Fit-Register]] · [[chaseos_v1_public_beta_acceptance_checklist]] · [[chaseos_not_built_backlog]] · [[Chaser-Forge]] · [[Artifact-Intelligence-Submission-Operator]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Agent-Activity-Index]]
