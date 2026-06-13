---
title: ChaseOS AI Website Launch Spec
created: 2026-05-31
runtime: hermes-optimus
status: DRAFT / HERMES PLANNING SPEC FOR CODEX IMPLEMENTATION
type: website-spec
links:
  - [[ChaseOS-AI-Domain-Override-Handover-2026-05-31]]
  - [[Hermes-Runtime-Profile]]
  - [[HERMES]]
  - [[Agent-Activity-Index]]
---

# ChaseOS AI Website Launch Spec

## Primary domain

`https://chaseos.ai`

## Required product line

**ChaseOS is the local-first AI operating system for builders running real projects with agents.**

Expanded: ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

## Route map

| Route | Purpose |
|---|---|
| `/` | Homepage: product identity, hero, CTA to waitlist and Studio. |
| `/waitlist` | Early-access signup. |
| `/studio` | ChaseOS Studio app/interface page. |
| `/forge` | Chaser Forge preview and creator ecosystem. |
| `/forge/index.json` | Static public Forge index artifact. |
| `/standards` | Public ChaseOS standards overview. |
| `/open-core` | Open-core/source-available/commercial posture. |
| `/pricing` | Pricing placeholder and future paid layers. |
| `/docs` | Public-safe docs hub. |
| `/download` | Download/early access instructions. |
| `/privacy` | Local-first privacy baseline. |
| `/security` | Security posture and disclosure contact. |
| `/roadmap` | Current/preview/future/blocked roadmap. |
| `/support` | Support/contact. |
| `/terms` | Early access terms. |
| `/creators` | Forge creator overview. |
| `/submit-pack` | Pack creator interest/submission form. |
| `/admin` | Protected internal waitlist/admin view; not public nav. |

## Hero copy

Human intent. Agentic execution. Private control.

ChaseOS is the local-first AI operating system for builders running real projects with agents. Turn scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

Primary CTA: `Join Studio Early Access`  
Secondary CTA: `Explore Chaser Forge`

## Feature sections

1. Local-first memory and project continuity.
2. Governed knowledge graph over sources, projects, decisions, approvals, and outputs.
3. ChaseOS Studio as the app/interface and command surface.
4. Agent/runtime awareness with bounded authority.
5. Approval Center visibility before action.
6. Workflow/mission packs for repeatable operating kits.
7. Chaser Forge preview for packs and creators.
8. Standards for portable manifests, approvals, graph objects, outcomes, and Forge index entries.

## Current/future claims

Current safe posture: ChaseOS Studio Early Access / Developer Preview.  
Future/upcoming: paid marketplace, managed agents, runtime credits, arbitrary browser automation, CRM/payment mutation, live external posting, and enterprise readiness.

## Waitlist form fields

Email, name, persona, current tools, biggest AI-workflow pain, use case, interest type, operating system, willingness to pay, consent to contact, source/UTM.

## Admin requirements

Protected `/admin`; admin auth/allowlist; view/filter/export signups; mark qualified/invited; view submit-pack entries; add notes. Must not expose user vaults, private graphs, provider keys, local runtime logs, or private project memory.

## Forge preview requirements

- `/forge` overview page.
- `/forge/index.json` static JSON preview.
- Example packs with digest/manifest metadata.
- Creator interest / submit-pack route.
- No live paid checkout.
- No untrusted third-party auto-install without validation.
- 9% future take-rate may be stated only as strategy, not current functionality.

## Standards page requirements

Expose high-level standards plus example schemas: `chaseos.pack.json`, `chaseos.forge-index.json`, `chaseos.approval.json`, `chaseos.graph.json`, `chaseos.outcome.json`.

## Privacy/security/open-core copy

Private graph stays local unless user explicitly exports/uploads/opts in. Use accurate terms: open-source, source-available, commercial source, proprietary paid layer. Do not call commercially restricted code open-source.

## Pricing placeholder

Free/local starter, Pro target, Teams, Forge creator/commercial packs, managed agents/runtime credits, enterprise/private deployment. Mark all billing/payments as planned until implemented and tested.

## SEO/social metadata suggestions

Title: `ChaseOS — Local-first AI operating system for builders`  
Description: `ChaseOS turns AI chats, docs, repos, runtimes, approvals, and outputs into one governed knowledge graph. Join ChaseOS Studio Early Access.`  
Open Graph image: Studio + graph + approval + Forge visual, no private data.

## No-overclaim rules

Do not claim: public beta complete, live marketplace payments, managed agents, runtime credits, arbitrary browser control, live email/social posting, CRM/payment mutation, enterprise compliance, or autonomous company operator capability.
