---
title: ChaseOS V1 Landing Pricing Privacy and Terms Requirements
created: 2026-05-30
updated: 2026-05-30
runtime: hermes-optimus
type: productization-requirements
status: DRAFT / TRACK A / V1-A4
scope: public landing structure, pricing hypothesis copy, privacy requirements, terms/disclaimer requirements, AI safety warnings, Chaser Forge positioning
links:
  - [[ChaseOS-V1-Release-Cutline]]
  - [[Chaser-Forge]]
  - [[HERMES]]
  - [[Hermes-Runtime-Profile]]
  - [[Agent-Activity-Index]]
---

# ChaseOS V1 Landing Pricing Privacy and Terms Requirements

> V1-A4 draft requirements for product-facing ChaseOS copy and public-user trust surfaces. Source of truth: `06_AGENTS/ChaseOS-V1-Release-Cutline.md`.

## 1. Purpose

This document turns the V1 release cutline into product-facing landing-page, pricing, privacy, terms/disclaimer, and marketplace-positioning requirements.

The goal is not to imply that all commercial infrastructure is implemented. The goal is to make ChaseOS explainable, safe, truthful, privacy-aware, and monetizable for first public users.

V1 copy must follow these boundaries:

- ChaseOS is the product/platform: a local-first AI operating system and agent control plane.
- ChaseOS Studio is the standalone app / graphical control panel.
- Chaser Forge is the governed marketplace / extension and workflow-pack distribution layer.
- Hermes and OpenClaw are existing bounded runtime-instance lanes under ChaseOS governance, not the public product brand.
- Chaser Agent is one of the ChaseOS 24/7 harness/runtime lanes; public product/agency authority remains gated and must not be framed as a V1 blocker.
- Billing, credits, paid marketplace purchases, hosted provider calls, and account/license enforcement must not be described as implemented unless separately verified.

## 2. Product-facing landing-page structure

### 2.1 Required landing sections

The V1 landing page should include these sections in this order:

1. Hero
2. Problem / why ChaseOS exists
3. What ChaseOS is
4. ChaseOS Studio product preview
5. Local-first privacy and control
6. Runtime and agent governance
7. Chaser Forge marketplace preview
8. Pricing / plan hypothesis
9. Safety, limitations, and external-action warnings
10. Download / waitlist / contact call to action
11. Privacy and terms links

### 2.2 Hero requirements

The hero must communicate the OS thesis in the first screen.

Suggested headline options:

- `The local-first AI operating system for builders who run projects with agents.`
- `Run your AI work from a private control plane — not scattered chats, scripts, and tabs.`
- `ChaseOS gives builders a governed home for memory, workflows, runtime activity, and agent coordination.`

Suggested subheadline:

`ChaseOS Studio is a local-first command center for inspecting your project system, coordinating AI runtime lanes, managing workflow packs, and keeping agent actions approval-aware.`

Required hero claims:

- local-first
- AI operating system / control plane
- project/workflow/agent coordination
- Studio as the user-facing app
- approval-aware runtime behavior

Forbidden hero claims unless implemented and verified:

- autonomous work without approval
- live hosted agents
- built-in billing or credits
- guaranteed income/revenue outcomes
- fully automated browser/site operation
- automatic publication, trading, payments, emailing, or external delivery

### 2.3 Problem section requirements

The landing page should describe the current pain clearly:

- AI work is fragmented across chats, terminals, docs, tools, providers, and agents.
- Builders need visibility into what agents can do, what they changed, and what still requires approval.
- Local project memory and runtime state should be inspectable instead of hidden inside opaque SaaS systems.
- External actions need explicit boundaries, especially when they touch files, credentials, uploads, payments, messages, trades, or public publication.

Suggested copy:

`AI work is becoming multi-agent, tool-heavy, and hard to supervise. ChaseOS gives your projects a local control plane: a place to inspect memory, workflows, runtime status, approval gates, and extension packs before agents act.`

### 2.4 What ChaseOS is section requirements

This section should explain the product without internal-only language.

Required framing:

`ChaseOS is a local-first AI operating system and agent control plane. ChaseOS Studio is the app that makes it usable: a command center for project state, feature readiness, workflow packs, runtime lanes, and approval-aware AI work.`

Feature bullets may include:

- Local-first workspace and project visibility
- ChaseOS Studio command center
- Feature catalog and workflow pack readiness labels
- Provider/API-key configuration visibility
- Runtime status and capability boundaries
- Docs, graph, and memory inspection
- ChaseOS Pulse proactive-intelligence previews where available
- Chaser Forge marketplace path for governed workflow packs and extensions

Avoid saying every listed feature is fully live. Use status labels: `Live`, `Partial`, `Preview`, `Upcoming`, `Blocked`, or `Post-V1`.

### 2.5 ChaseOS Studio section requirements

The Studio section should position Studio as the public-user app, not an internal dashboard.

Required copy concepts:

- `ChaseOS Studio is the graphical control panel for ChaseOS.`
- `It helps users understand what is installed, what is configured, what is safe to run, and what still needs setup.`
- `V1 should distinguish live, preview, upcoming, and blocked features clearly.`

Suggested module list:

- Home / Command Center
- Settings / Privacy / Providers
- Feature Catalog / Workflow Packs
- Chat / Agent Control Panel
- Docs / Graph / Memory Inspector
- Runtime Status
- Chaser Forge preview

### 2.6 Local-first trust section requirements

This section should be short, prominent, and repeated in privacy/terms surfaces.

Required claims:

- ChaseOS is designed around local-first project control.
- Users should be able to see where their local data lives.
- Provider/API-key setup is user-controlled.
- External actions require clear approval gates.
- Readiness/status labels must be honest.

Suggested copy:

`Your workspace should be visible to you first. ChaseOS is designed as a local-first control plane: it shows where your data lives, which providers are configured, what runtime lanes are active, and which actions require approval before anything leaves your machine or changes an external system.`

Do not imply:

- that no data can ever leave the machine,
- that all providers are private by default,
- that every runtime or connector is sandboxed unless verified,
- that all external side effects are technically impossible.

Instead, say local-first control plus explicit provider/external-action warnings.

## 3. Pricing hypothesis copy

### 3.1 Pricing posture

The pricing section should be framed as a hypothesis / early access model until billing and account infrastructure exist.

Required warning:

`Pricing and plan names are planning hypotheses for V1 productization. Billing, credits, license enforcement, paid marketplace purchases, and account services should not be presented as implemented until verified.`

### 3.2 Suggested public pricing section copy

Heading:

`Start local. Grow into managed workflows when you need them.`

Intro:

`ChaseOS is being built around a local-first core with optional paid layers for premium workflow packs, hosted/account services, managed runtime lanes, teams, and support.`

Plan hypothesis table:

| Plan | Public framing | What it may include | V1 truth label |
|---|---|---|---|
| Free / Local Starter | Try ChaseOS locally. | ChaseOS Studio, local docs/graph/status, sample workflows, basic feature catalog. | V1 candidate; must match actual download. |
| Pro | For AI-native builders and founders. | Advanced Studio surfaces, premium templates/workflows, provider/runtime convenience, optional updates/support. | Pricing hypothesis; billing not implemented unless verified. |
| Forge+ | For power users and teams extending ChaseOS. | Workflow packs, private catalogs, premium extensions, Chaser Forge distribution. | Marketplace preview; paid pack purchase flow not implemented unless verified. |
| Managed Agent / Agency | For founders/businesses that want outcomes. | Chaser Agent / always-on operator / done-for-you workflows. | Runtime identity exists; public managed-agent product lane remains gated/Post-V1. |
| Team / Business | For teams with shared governance needs. | Shared projects, approval logs, team policies, collaboration, private deployment support. | Post-V1. |

### 3.3 Required pricing disclaimers

Include these requirements near the pricing area or FAQ:

- Billing is not active unless an account/billing provider is actually configured.
- Credits are not active unless managed agent/runtime accounting exists.
- Users may need their own API keys for third-party AI providers.
- Provider costs are separate from ChaseOS unless a managed hosted plan explicitly says otherwise.
- Marketplace paid packs require payment, license, and seller/account infrastructure before being sold.
- Pricing may change during beta.

### 3.4 Pricing copy that must be avoided

Do not use:

- `Unlimited agents`
- `Autonomous revenue machine`
- `Fully managed AI workforce included`
- `Credits included` unless credit accounting exists
- `Marketplace purchases live` unless payments/licensing are implemented
- `No API keys needed` unless hosted provider routing is live
- `Private by default across all providers` unless provider-specific data flow is documented

## 4. Privacy notice requirements

### 4.1 Privacy page purpose

The privacy notice must help first public users answer:

- What data does ChaseOS store locally?
- Where is the local workspace/vault/data folder?
- What data may be sent to third-party providers?
- What happens when the user configures API keys?
- What runtime logs or audit records may be created?
- What external actions require approval?
- What is not yet built?

### 4.2 Required privacy sections

The privacy notice should include:

1. Local-first design
2. Local data location and user control
3. Provider/API-key data flow
4. Runtime, audit, and log data
5. Chaser Forge marketplace/extension data
6. External actions and approvals
7. Telemetry status
8. Data export/reset/open-folder controls
9. Beta limitations
10. Contact/support path

### 4.3 Required privacy statements

Suggested copy blocks:

`ChaseOS is designed as a local-first control plane. Your project files, workspace state, local docs, and runtime records may live on your device or in a folder you choose. The app should show this location in Settings.`

`If you connect third-party AI providers or other services, prompts, context, files, metadata, or action requests may be sent to those providers according to your configuration and their policies. ChaseOS should show provider/API-key readiness before provider-backed actions run.`

`ChaseOS may create local logs, audit records, workflow outputs, or runtime status records so you can inspect what happened. These records are part of the control-plane model and should remain visible to the user.`

`External actions such as uploads, emails, browser actions, payments, trading, CRM mutation, publication, or connector/API mutations must be clearly labeled and approval-gated unless a specific workflow explicitly proves safe execution.`

`Telemetry should be off, absent, or explicitly opt-in unless a verified telemetry system and privacy policy exist.`

### 4.4 Local-data warning requirements

The UI must warn users that:

- ChaseOS may read from the selected local workspace/vault.
- Local project files can contain sensitive personal, business, credential, or client data.
- Users should choose a workspace intentionally.
- Export/reset/open-folder controls should be visible in Settings.
- Deleting local data may not delete data already sent to external providers.

Suggested warning:

`Choose your ChaseOS workspace carefully. Local files may include private project notes, credentials, client details, or business data. ChaseOS should make the active data location visible and provide clear open-folder, export, and reset paths.`

### 4.5 Provider/API-key warning requirements

The UI must warn users that:

- Third-party API keys are user-managed unless ChaseOS offers a hosted account layer.
- Provider calls may send prompts, context, files, metadata, and outputs to the provider.
- Provider billing, rate limits, retention, and privacy policies are controlled by the provider unless ChaseOS manages the account.
- Users should not paste secrets into prompts or documents unless they understand the provider flow.
- API-key storage must be disclosed and should not be shown in plaintext after entry.

Suggested warning:

`Provider/API-key setup is user-controlled. When you connect an AI provider or external service, relevant prompts, files, context, and metadata may be sent to that provider. Provider costs, retention, and privacy terms may apply separately.`

## 5. Terms and disclaimer requirements

### 5.1 Terms/disclaimer page purpose

The terms/disclaimer page should protect user trust and avoid overclaiming. It should make clear that ChaseOS is a tool for local-first AI coordination, not a guarantee of accuracy, safety, legal compliance, revenue, or autonomous outcome delivery.

### 5.2 Required terms/disclaimer sections

The page should include:

1. Beta / early-access status
2. AI output limitations
3. User responsibility for review and approval
4. External action warning
5. Provider/API-key responsibility
6. Local data and backup responsibility
7. Marketplace/extension disclaimer
8. No professional advice disclaimer
9. No guaranteed outcomes disclaimer
10. Acceptable use / safety boundary
11. Changes to product/pricing/features

### 5.3 AI limitations warnings

Required copy concepts:

- AI outputs can be wrong, incomplete, unsafe, outdated, or misleading.
- Agent/tool actions may fail or have unintended effects.
- Users must review important outputs before relying on them.
- ChaseOS status labels should distinguish live, preview, upcoming, and blocked capabilities.
- ChaseOS does not replace professional judgment.

Suggested warning:

`AI-generated outputs and agent recommendations may be inaccurate, incomplete, unsafe, or outdated. Review important outputs before using them for business, legal, financial, medical, security, or operational decisions.`

### 5.4 External action approval warnings

Required copy concepts:

External actions include, but are not limited to:

- sending emails or messages,
- uploading files,
- publishing content,
- making payments,
- trading or financial operations,
- browser actions on third-party sites,
- CRM/customer data mutation,
- repository or production-system mutation,
- marketplace publication,
- credential or account changes.

Suggested warning:

`External actions can affect real accounts, money, customers, files, repositories, websites, or public content. ChaseOS should preview and approval-gate these actions unless a specific live workflow proves otherwise. Do not assume a button or agent suggestion has executed an external action unless the UI shows verified execution evidence.`

### 5.5 Local-data and backup disclaimers

Required copy concepts:

- Users are responsible for backups of local workspaces.
- Local-first does not mean immune to accidental deletion or local machine failure.
- Reset/migration features should be preview-only or approval-gated unless verified.
- Workspace upgrades/migrations must not be framed as safe automatic mutation unless implemented and tested.

Suggested warning:

`Because ChaseOS is local-first, you remain responsible for backups, local storage, and workspace selection. Use caution with reset, migration, upgrade, or writeback actions, especially during beta.`

### 5.6 Marketplace/extension disclaimer requirements

Required copy concepts:

- Chaser Forge is a governed marketplace / workflow-pack distribution layer.
- In V1 it should be framed as preview/partial unless the public domain/index exists.
- Paid packs, payment, seller accounts, revenue share, licensing, and remote install flows are not implemented unless verified.
- Extension/workflow packs may request permissions or provider access; users should review them before installing/running.

Suggested warning:

`Chaser Forge is the planned marketplace and workflow-pack layer for ChaseOS. V1 may show local/demo packs or a preview catalog. Paid purchases, seller accounts, revenue share, licensing, and live hosted marketplace fetches require separate implementation and should not be implied until verified.`

## 6. Chaser Forge marketplace positioning

### 6.1 Public positioning

Chaser Forge should be positioned as the extension and workflow-pack ecosystem around ChaseOS, not as a completed payment marketplace in V1.

Suggested headline:

`Chaser Forge: governed workflow packs for the ChaseOS ecosystem.`

Suggested copy:

`Chaser Forge is the path for distributing templates, workflow packs, agent presets, extensions, and domain-specific operating kits for ChaseOS. V1 can show local/demo packs and the marketplace direction while the public domain, index, payments, licensing, and seller flows mature.`

### 6.2 V1 truth labels for Forge

Use these labels:

- `Local proof available` for local catalog/install proof.
- `Static/public index pending` for the official domain and `index.json` publication path.
- `Payments blocked` for paid packs, license mutation, seller accounts, and revenue share.
- `Preview` for public product pages that explain Forge before live purchase infrastructure exists.

### 6.3 Required Forge boundaries

Do not claim:

- live public hosted marketplace fetch,
- paid purchases,
- seller payout/revenue share,
- license enforcement,
- one-click remote install from a public index,
- automatic publication,
- safety-vetted third-party ecosystem,

unless each is separately implemented, tested, and approved.

### 6.4 Forge domain linkage

The landing/domain structure should reserve:

- `/forge` or `forge.chaseos.<tld>` for marketplace index and extension catalog,
- `/docs` for install/use docs,
- `/account` later for subscriptions, licenses, and credits,
- `/api` later for licensing, accounts, updates, marketplace, and opt-in telemetry endpoints if built.

## 7. FAQ requirements

The landing page should include a short FAQ that prevents overclaiming.

Recommended FAQ entries:

### Is ChaseOS a chatbot?

`No. ChaseOS is a local-first AI operating system and control plane. Chat may be one surface, but the product is about project memory, workflow visibility, runtime governance, and approval-aware agent coordination.`

### Does ChaseOS run fully autonomous agents?

`V1 should show runtime readiness and bounded workflow status honestly. External actions and dangerous commands require explicit approvals or verified workflow boundaries. Future managed runtime lanes may expand this.`

### Do I need my own API keys?

`For provider-backed AI calls, yes unless a hosted ChaseOS account/provider layer is explicitly offered. Provider billing and data policies may apply separately.`

### Is my data local?

`ChaseOS is designed local-first and should show the active workspace/data location. Data may leave the device if you connect providers, run external integrations, upload files, or approve external actions.`

### Is Chaser Forge live?

`Chaser Forge is the marketplace/workflow-pack path. V1 may include local/demo packs or preview catalog pages. Paid purchases and public hosted marketplace infrastructure should not be treated as live until implemented.`

### Are billing and credits implemented?

`Do not claim billing, credits, license enforcement, or paid marketplace purchases are implemented unless the product has verified account, payment, and accounting infrastructure.`

## 8. UI requirement checklist

### 8.1 Landing page checklist

- [ ] Hero says local-first AI operating system/control plane.
- [ ] ChaseOS Studio is named as the app/control panel.
- [ ] Product copy explains first-user value in under 60 seconds.
- [ ] Status labels distinguish live/partial/preview/upcoming/blocked/post-V1.
- [ ] Chaser Forge is visible but honestly labeled as preview/partial where applicable.
- [ ] Download/waitlist/contact CTA exists.
- [ ] Privacy and terms links are visible.
- [ ] No hardcoded personal paths appear in public copy.
- [ ] No billing/credits/paid marketplace claim appears unless implemented.

### 8.2 Pricing checklist

- [ ] Pricing framed as hypothesis/early-access if billing is absent.
- [ ] Provider/API-key costs called out separately.
- [ ] Credits not advertised as active unless accounting exists.
- [ ] Marketplace paid packs not advertised as buyable unless payments/licensing exist.
- [ ] Pro/Forge+/Managed/Team lanes framed as roadmap or early-access as appropriate.

### 8.3 Privacy checklist

- [ ] Local data location visible or required in Settings.
- [ ] Provider/API-key data flow explained.
- [ ] External-action approvals explained.
- [ ] Logs/audit records explained.
- [ ] Telemetry status explicitly off/absent/opt-in unless verified otherwise.
- [ ] Export/reset/open-folder controls documented.

### 8.4 Terms/disclaimer checklist

- [ ] Beta/early-access status stated.
- [ ] AI limitation warning included.
- [ ] External action warning included.
- [ ] Provider/API-key responsibility included.
- [ ] Local backup responsibility included.
- [ ] Marketplace/extension limitations included.
- [ ] No guaranteed outcomes/revenue statement included.

## 9. Implementation acceptance criteria for V1-A4

This draft is ready for reviewer/product implementation when:

- Product copy uses ChaseOS / ChaseOS Studio / Chaser Forge names consistently.
- Pricing copy is useful but does not claim billing or credits are implemented.
- Privacy requirements clearly warn about local data, providers, API keys, and external actions.
- Terms/disclaimer requirements clearly warn about AI limitations and user responsibility.
- Chaser Forge is positioned as the marketplace path without implying paid marketplace infrastructure is live.
- The requirements align with the V1 release cutline's must-ship safety/legal baseline.

## 10. Graph links

[[ChaseOS-V1-Release-Cutline]] · [[Chaser-Forge]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Agent-Activity-Index]]
