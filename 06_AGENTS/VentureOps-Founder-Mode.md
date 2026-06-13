---
title: VentureOps Founder Mode
type: ventureops-mode-spec
status: DOCS-LEVEL SPEC / SUBSTRATE-PARTIAL / NO-LIVE-AUTONOMY
created: 2026-05-18
updated: 2026-05-18
source_context: 06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
---

# VentureOps Founder Mode

## Decision

Founder Mode did not previously exist as a dedicated VentureOps mode document. The repo already had the important substrate — WML `founder_venture`, VentureOps workflow packs, Mission Mode, SIC, AOR, SiteOps, Approval Center, Studio, and graph infrastructure — so this pass chooses outcome **B: partial substrate exists but no mission pack**.

This document specifies Founder Mode at the documentation/product-architecture level only. It does not implement a runtime, executor, provider call, browser action, external send, payment/CRM mutation, or canonical graph/writeback mutation.

## Definition

**Founder Mode** is a ChaseOS operating mode for AI-native founders and builders turning scattered ideas, research, docs, agents, launch assets, and workflows into governed mission packs.

It is not the whole product. It is a mode/use-case layer inside ChaseOS.

## Reused substrate

Founder Mode reuses:

- Workspace Mode Layer `founder_venture` for context classification and routing posture;
- VentureOps workflow-pack standards for repeatable business/application workflows;
- VentureOps Mission Mode for long-running objectives, mission state, proof cards, scorecards, reviews, and proposal-only workflow evolution;
- SIC for pain research, competitor research, source-backed briefs, and evidence packets;
- Graph substrate for project/source/workflow/output/approval/decision relationships;
- AOR for bounded manifest-driven dispatch, writeback, and audit;
- SiteOps for landing-page/site workflow planning and dry-run packages;
- Approval Center for approval review visibility;
- Gate, Permission Matrix, Trust Tiers, and Agent Control Plane for authority boundaries.

## User jobs

Founder Mode should help a builder:

- convert a rough idea into a structured project graph;
- run venture gates and research briefs;
- produce launch assets without losing provenance;
- prepare landing page and form specs;
- draft distribution and interview plans;
- review approval packets before any external action;
- record metrics, decisions, and runtime evidence;
- turn repeated work into reusable workflow packs.

## Initial mission family

Initial mission cards:

- Startup Validation & Launch;
- Research Briefing;
- Site / Landing Page Build;
- Content Distribution Pack;
- Company Brain Setup;
- Runtime Security Audit;
- Ecommerce / Reselling Ops Pack;
- Agent Workflow Governance.

## Authority posture

Founder Mode is proposal-first:

- drafts and local reports are allowed within declared write scopes;
- external sends, posting, scraping, deployment, CRM/payment mutation, and live browser/account actions require source-specific executors and explicit approval;
- Approval Center can display/review approval posture but does not become a generic executor;
- SiteOps is dry-run/planning and bounded proofs unless a later executor pass is approved;
- WML narrows context and posture but does not grant authority.

## Studio implication

Founder Mode should appear under `Missions`, with `founder_venture` WML context available and graph/Knowledge Box links visible. It should not replace Home, Graph, Sources, Projects, Runtimes, Site Skills, Approvals, Logs/Audit, or Settings.

## Related files

- [[ChaseOS-Product-Identity-and-Wedge]]
- [[VentureOps-Startup-Validation-Launch-Mission]]
- [[Startup-Validation-Launch-Mission-SOP]]
- [[Startup-Validation-Launch-Report-Template]]
- [[Workspace-Mode-Layer-Feature-Family]]
- [[VentureOps-Architecture]]
- [[VentureOps-Mission-Mode]]
- [[ChaseOS-Founder-Mode-Capability-Readiness-Audit]]
