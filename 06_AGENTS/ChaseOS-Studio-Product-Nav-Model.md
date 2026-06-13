---
title: ChaseOS Studio Product Nav Model
type: product-nav-model
status: PROPOSED / FAMILY-NORMALIZED / OPERATOR CONFIRMATION REQUIRED BEFORE IMPLEMENTATION
created: 2026-05-18
updated: 2026-05-21
source_context: 06_AGENTS/ChaseOS-Product-Positioning-and-Founder-Mode-Context.md
---

# ChaseOS Studio Product Nav Model

## Principle

2026-05-21 correction: this file remains a broad proposed product-nav model, not the implemented Studio navbar. Use `06_AGENTS/Studio-Product-UI-Feature-Family-Normalization.md` as the current feature-family mapping and `06_AGENTS/Finalize-ChaseOS-Studio-Product-UI-Handover.md` as the work-order control document. Navbar implementation is still pending operator confirmation.

Studio navigation should present ChaseOS as a broad privacy-first agentic operating system, not as only Founder Mode or Startup Validation.

Recommended top-level nav:

```text
Home
Graph
Knowledge Boxes
Sources
Projects
Missions
Runtimes
Site Skills
Approvals
Logs / Audit
Settings
```

If the current shell needs a narrower first release, use:

```text
Home
Projects
Graph
Missions
Runtimes
Approvals
Sources
Settings
```

Do **not** create a top-level nav item called only “Startup Validation”. Startup Validation & Launch belongs under Missions.

## Top-level areas

- **Home** — current-state dashboard, blockers, operator handoffs, safe next actions, recent mission/proof activity.
- **Graph** — graph-first view over files, workflows, sources, approvals, outputs, decisions, and runtime evidence.
- **Knowledge Boxes** — user-friendly graph containers for a project, domain, mission, customer, workflow family, or runtime lane.
- **Sources** — SIC and Capture entry point: source packages, workspaces, evidence, provenance, and promotion posture.
- **Projects** — project state, goals, decisions, and linked graph/source/workflow artifacts.
- **Missions** — mission/workflow-pack launcher and review surface.
- **Runtimes** — OpenClaw, Hermes, Codex/Claude, MCP, Agent Bus, AOR, readiness, role cards, adapter ceilings, handoff state, and audit trails.
- **Site Skills** — SiteOps / browser workflow planning, site profiles, workflow manifests, dry-runs, approvals, and browser-run evidence.
- **Approvals** — Approval Center aggregator for pending/approved/rejected/blocked/consumed items.
- **Logs / Audit** — build logs, documentation history, workflow proofs, runtime audits, SiteOps runs, browser runs, decision ledger, and provenance reports.
- **Settings** — provider refs, local paths, runtime adapters, WML profiles, Gate/Permission Matrix references, scheduler/export posture, and safe local configuration.

## Mission cards

Initial mission cards should include:

- Founder Mode / AI Builder Mode;
- Startup Validation & Launch;
- Research Briefing;
- Site / Landing Page Build;
- Content Distribution Pack;
- Company Brain Setup;
- Runtime Security Audit;
- Ecommerce / Reselling Ops Pack;
- Agent Workflow Governance.

## Founder Mode placement

Founder Mode should be represented as a mode-aware workspace under Missions and Workspace Mode Layer, not as the whole product.

Suggested Founder Mode surface:

```text
Missions
└── Founder Mode / AI Builder Mode
    ├── Idea Intake
    ├── Project Graph / Knowledge Box
    ├── Venture Gate
    ├── Research Brief
    ├── Launch Assets
    ├── Landing Page Preview
    ├── Distribution Pack
    ├── Interview / Feedback Pipeline
    ├── Metrics Tracker
    ├── Approval Packets
    ├── Decision Room
    └── Writeback / Audit
```

## Current implementation mapping

| Nav area | Existing substrate | Current posture |
|---|---|---|
| Home | `runtime/studio/dashboard.py`, product status panels | PARTIAL / read-only + governed controls |
| Graph | `runtime/graph/`, `runtime/studio/graph_view.py` | PARTIAL / graph view exists |
| Knowledge Boxes | graph/project/source substrate | FUTURE UI abstraction; docs-level now |
| Sources | `runtime/source_intelligence/`, SIC docs | READY substrate |
| Projects | vault/project OS files, WML project/domain cards | PARTIAL |
| Missions | VentureOps Mission Mode substrate | PARTIAL; mission nav missing |
| Runtimes | AOR, Agent Bus, runtime governance, OpenClaw/Hermes/Codex lanes | PARTIAL |
| Site Skills | SiteOps registry/dry-run/proof lanes | PARTIAL |
| Approvals | `runtime/studio/approval_center_panel.py` | PARTIAL / read-only aggregator |
| Logs / Audit | `07_LOGS/` indexes and proof artifacts | READY/PARTIAL |
| Settings | setup/config/runtime docs | PARTIAL |

## Boundaries

- Nav does not grant authority.
- Mission cards do not execute until a bounded manifest/handler exists.
- Approval visibility does not equal approval execution.
- Site Skills does not imply arbitrary authenticated browser control.
- Knowledge Boxes must not mutate canonical graph/knowledge state outside approved paths.
