---
date: 2026-05-21
runtime: Codex
session_descriptor: studio-product-ui-feature-family-normalization
type: feature-family-normalization
status: COMPLETE / OPERATOR CONFIRMATION REQUIRED BEFORE NAVBAR IMPLEMENTATION
scope: ChaseOS Studio product UI panels, canonical feature families, feature-fit surfaces, wiki node coverage
authority: docs/register normalization only; no app code or runtime authority changed
---

# Studio Product UI Feature-Family Normalization

## Result

Pass 0 is complete as a documentation/register normalization pass.

This file names every canonical feature family currently registered in `06_AGENTS/Feature-Register.md`, verifies wiki-node coverage, maps every current Studio registry panel to a canonical family or governed product sub-surface, and separates product page labels from real feature families.

Expanded subfeature and mini-feature truth now lives in `[[ChaseOS-Feature-Family-and-Subfeature-Inventory]]`. The corrected evidence matrix is `[[docs/audits/2026-05-21_feature_family_deep_reconciliation]]`. Use both before the next confirmation pass so features such as Visual Capture Markdown Ingestion, Sub-Agent Presets, Product Workflow Packs, Creator Engine, Personal Context Import, Phase 11 Chat, Pulse, SiteOps/Browser Runtime, and runtime bus/daemon lanes are not hidden under broad family labels.

Navbar and Dashboard/Home implementation remain blocked until the operator confirms this mapping.

## Audit Scope

Audited surfaces:

- `06_AGENTS/Feature-Register.md`
- `06_AGENTS/Feature-Fit-Register.md`
- `docs/features/-Upcoming-Features-Index.md`
- `docs/features/*.md`
- `06_AGENTS/Finalize-ChaseOS-Studio-Product-UI-Handover.md`
- `06_AGENTS/ChaseOS-Studio-Product-Nav-Model.md`
- `06_AGENTS/ChaseOS-Studio-Full-Desktop-Card-UI-Closure-Criteria.md`
- `runtime/studio/shell/panel_registry.py`
- live `build_native_shell_panel_registry('.')` output

Current registry count verified: 39 declared panels, 38 mounted panels, 1 readiness-only panel.

## Normalization Rules

- Do not create a new feature family for a page label.
- Do not promote implementation group names such as `Advanced`, `Orientation`, `QA / Proof`, or `Runtime Operations` into feature families.
- Every visible product page must map to one canonical family, a documented cross-cutting feature node, or a governed audit/advanced surface.
- Feature families live in `06_AGENTS/Feature-Register.md`; feature-fit and implementation lanes live in `06_AGENTS/Feature-Fit-Register.md`.
- Proposed or reference features in `docs/features/-Upcoming-Features-Index.md` remain planning seeds until promoted through the register.

## Canonical Feature Families And Wiki Nodes

| # | Registered feature family | Normalized wiki node | Status | Studio coverage |
|---|---|---|---|---|
| 1 | Source Intelligence Core (SIC) | [[Source-Intelligence-Core]] + [[SIC-Architecture]] | COMPLETE | `sic`, `acquisition`, `provenance-explorer` |
| 2 | Scheduled Briefing Pipelines (SBP) | [[Scheduled-Briefing-Pipelines]] | PARTIAL / generic substrate live | `schedules`, `pulse-schedule-proof` |
| 3 | Autonomous Operator Runtime (AOR) | [[Autonomous-Operator-Runtime]] | PARTIAL LIVE | `runtime-cockpit`, `aor`, `bus`, `workflow-registry`, `role-cards`, `schedules` |
| 3a | ChaseOS VentureOps | [[VentureOps-Architecture]] | PARTIAL / local implementation lane complete; real-world evidence blocked | `workflow-packs`, `project-workspace` |
| 4 | Multi-Repo / Multi-Directory Access Policy | [[Multi-Repo-Multi-Directory-Access-Policy]] | DEFERRED / policy defined | advanced runtime/governance only |
| 5 | Agent Memory Architecture | [[Agent-Memory-Architecture]] | PARTIAL / Layer A/B active; product surfaces partial | `context-import`, `memory-ledger`, `runtime-memory-inspector`, `agent-identity`, `companion-surface` |
| 6 | Runtime Navigation Map | [[Runtime-Navigation-Map]] | SEEDED | `runtime-navigation` |
| 7 | Interface / Experience Layer | [[ChaseOS-Studio-Architecture]] | PARTIAL / native shell active | `dashboard`, `app-launcher`, `workspace-entry`, `settings`, `graph`, `node-inspector`, `project-workspace` |
| 8 | Operator Surface + Runtime Interaction Layer (OSRIL) | [[Operator-Surface-Runtime-Interaction]] | Phase 9 runtime-side COMPLETE; Phase 10+ surfaces partial | `runtime-support-loops`, `runtime-cockpit`, `chat` |
| 9 | Developer Co-Development Mode | [[Developer-Co-Development-Mode]] | COMPLETE / parked | no default MVP panel; audit/dev surface only |
| 10 | Acquisition + Normalization Layer | [[Acquisition-Normalization-Layer]] | Pass 1A substrate active | `intake`, `capture-markdown`, `acquisition`, `sic` |
| 11 | Full-System Operator Surface (FSOS) | [[Full-System-Operator-Surface]] | architecture/adapter contracts complete; live surfaces partial | `browser-runtime`, `siteops`, `chat` dispatch surfaces |
| 12 | Model Context Protocol (MCP) Integration | [[ChaseOS-MCP-Server]] + [[ChaseOS-MCP-Module-Design]] | V1 stdio scaffold active | no primary page; runtime/settings/audit only |
| 13 | ChaseOS Pulse | [[ChaseOS-Pulse-Architecture]] | current v1 local lane complete; broader product partial | `pulse-schedule-proof`, `pulse-enqueue` |
| 14 | ChaseOS SiteOps / Browser Runtime Skill Memory | [[ChaseOS-SiteOps]] + [[Browser-Runtime-Skill-Memory]] | PARTIAL / bounded MVP + safe-local proofs | `siteops`, `browser-runtime` |
| 15 | Chaser Forge | [[Chaser-Forge-Feature-Family]] | COMPLETE / local governed MVP verified; public marketplace deferred | `chaser-forge` |

## Cross-Cutting Feature Nodes Observed

These are real feature/product nodes in current repo truth, but they are not all separate top-level Feature Register families.

| Feature node | Normalized parent | Status | Studio relevance |
|---|---|---|---|
| [[Workspace-Mode-Layer-Feature-Family]] | Interface / Experience Layer + AOR + VentureOps | COMPLETE | `project-workspace`, `workspace-entry`, Chat deeplinks |
| [[ChaseOS-Phase11-Architecture]] | Interface / Experience Layer + OSRIL + Agent Memory | PARTIAL / many read-only and governed executor proofs | `chat`, `companion-surface`, runtime/browser dispatch surfaces |
| [[Personal-Context-Import-Feature]] | Agent Memory Architecture | PARTIAL / approved chains exist; product surface needs cleanup | `context-import` |
| [[Graph-Substrate-Architecture]] | Interface / Experience Layer + AOR graph workflows | PARTIAL / graph substrate live; persisted graph storage deferred | `graph`, `node-inspector`, `graph-hygiene`, `provenance-explorer` |
| [[ChaseOS-Approval-Center]] | Governance / Interface Layer | PARTIAL / read-only aggregator mounted | `approval-center` |
| [[Provider-Agnostic-Routing-Architecture]] | AOR + Phase 11 Chat + Runtime | COMPLETE as architecture rule | `chat`, `runtime-cockpit`, `agent-identity` |
| [[docs/features/chaseos_product_facing_workflow_packs_spec.md]] | VentureOps + WML | LOCAL LANE COMPLETE / external execution deferred; includes Automation Audit, Creative Studio, Research Intelligence, Agent Governance Kit, approval review, marker reservation, approved local resume, and local UI resume | `workflow-packs` |
| [[docs/features/chaseos_visual_capture_markdown_ingestion_rule]] | Capture + Acquisition + SIC | PARTIAL / Pass 14 approved source-pack write executor verified; AOR dispatch readiness is code-observed/log-evidence-required only | `capture-markdown` |
| [[docs/features/CHASE_OS_SUB_AGENT_PRESETS]] | Runtime / Governance / Chaser Forge-adjacent | PARTIAL / contract lanes | no primary MVP panel yet |
| [[docs/features/chase-os-creator-engine-spec]] | VentureOps / Content / future product lane | PARTIAL / passes 1-10 verified; product execution blocked | no primary MVP panel yet |
| [[ChaseOS-Feature-Family-and-Subfeature-Inventory]] | Register supplement across all families | OPERATOR CONFIRMATION REQUIRED | source for README/Foundation/guides/navbar cleanup |
| [[docs/audits/2026-05-21_feature_family_deep_reconciliation]] | Evidence matrix across all families | READ-ONLY AUDIT COMPLETE | source for inventory/register corrections |

## Normalized Studio Panel Matrix

| Panel id | Current registry group | Normalized product feature | Canonical parent node | Target product area | Productization status |
|---|---|---|---|---|---|
| `dashboard` | Orientation | Home | [[ChaseOS-Studio-Architecture]] | Main -> Home | needs UI rewrite; current copy is implementation/release status |
| `chat` | Advanced | Chat | [[ChaseOS-Phase11-Architecture]] | Main -> Chat | rename from Phase 11 Chat; hide pass language |
| `project-workspace` | Advanced | Project Workspace | [[Workspace-Mode-Layer-Feature-Family]] | Main -> Project Workspace | product surface; reduce implementation scaffolding |
| `workflow-packs` | Workflow Packs | Missions / Workflow Packs | [[VentureOps-Architecture]] + [[Workflow-Pack-Standard]] | Main -> Missions | product surface; hide local resume internals by default |
| `chaser-forge` | Builder Studio | Extensions / Chaser Forge | [[Chaser-Forge-Feature-Family]] | Main -> Extensions | local MVP complete; public marketplace deferred |
| `graph` | Knowledge Graph | Graph View | [[Graph-Substrate-Architecture]] + [[ChaseOS-Studio-Architecture]] | Knowledge Graph -> Graph View | primary graph surface |
| `node-inspector` | Knowledge Graph | Node Inspector | [[Graph-Substrate-Architecture]] + [[ChaseOS-Studio-Architecture]] | Knowledge Graph -> Node Inspector | primary graph/detail surface |
| `graph-hygiene` | Knowledge Graph | Graph Hygiene | [[Autonomous-Operator-Runtime]] + [[Graph-Substrate-Architecture]] | Knowledge Graph -> Graph Hygiene | user-actionable maintenance surface |
| `provenance-explorer` | Advanced | Provenance | [[Acquisition-Normalization-Layer]] + [[Graph-Substrate-Architecture]] | Knowledge Graph -> Provenance | rename to user-facing Provenance |
| `intake` | Acquisition | Intake | [[Acquisition-Normalization-Layer]] | Content -> Intake | primary review/quarantine surface |
| `capture-markdown` | Acquisition | Capture | [[Connector-Capture-Architecture]] + [[Acquisition-Normalization-Layer]] | Content -> Capture | rename from implementation phrase |
| `acquisition` | Acquisition | Sources | [[Acquisition-Normalization-Layer]] | Content -> Sources | product label should be source pipeline |
| `sic` | Acquisition | Research Collections | [[Source-Intelligence-Core]] + [[SIC-Architecture]] | Content -> Research Collections | rename away from acronym if needed |
| `runtime-cockpit` | Runtime Operations | AI Agents | [[Autonomous-Operator-Runtime]] + [[Operator-Surface-Runtime-Interaction]] | Runtime -> AI Agents | primary runtime/operator surface |
| `bus` | Advanced | Agent Bus | [[Runtime-InterAgent-Coordination-Bus]] | Runtime -> Agent Bus | primary diagnostics/status surface |
| `schedules` | Advanced | Schedules | [[Scheduled-Briefing-Pipelines]] + [[Autonomous-Operator-Runtime]] | Runtime -> Schedules | product schedule view |
| `aor` | QA / Proof | Task History | [[Autonomous-Operator-Runtime]] | Runtime -> Task History | rename from AOR Executions for users |
| `browser-runtime` | Advanced | Browser Runtime | [[Browser-Runtime-Skill-Memory]] | Runtime -> Browser Runtime | likely advanced until live product-ready |
| `siteops` | Advanced | Site Skills | [[ChaseOS-SiteOps]] | Runtime -> Site Skills / Advanced | decide visibility after operator confirmation |
| `context-import` | Personal Memory Manager | Context Import | [[Personal-Context-Import-Feature]] + [[Agent-Memory-Architecture]] | Personal Memory -> Context Import | keep explicit approval posture |
| `memory-ledger` | Personal Memory Manager | Memory Ledger | [[Agent-Memory-Architecture]] | Personal Memory -> Memory Ledger | hide JSONL internals |
| `runtime-memory-inspector` | Personal Memory Manager | Runtime Memory | [[Agent-Memory-Architecture]] | Personal Memory -> Runtime Memory / Advanced | decide primary vs advanced |
| `pulse-schedule-proof` | ChaseOS Pulse | Proactive Briefings | [[ChaseOS-Pulse-Architecture]] | Personal Memory -> Proactive Briefings | remove proof wording from default UI |
| `pulse-enqueue` | ChaseOS Pulse | Review Queue | [[ChaseOS-Pulse-Architecture]] | Personal Memory -> Review Queue | remove Agent Bus enqueue wording from default UI |
| `companion-surface` | Planned / Blocked | Companion Surface | [[ChaseOS-Phase11-Architecture]] + [[Agent-Memory-Architecture]] | Hidden / Personal Memory Advanced | readiness-only; not primary product page |
| `approval-center` | Governance | Approvals | [[ChaseOS-Approval-Center]] | Governance -> Approvals | central governance page |
| `settings` | Governance | Settings | [[ChaseOS-Studio-Architecture]] | Governance -> Settings | keep read-only/config-safe posture |
| `qa-proof` | Advanced | QA / Proof | [[Feature-Fit-Register]] | Governance -> QA / Proof | audit/dev evidence surface |
| `build-logs` | QA / Proof | Logs / Audit | [[Build-Logs-and-Operator-Briefs-Summary-Context-Application]] | Governance -> Logs / Audit | audit surface |
| `decision-ledger` | Advanced | Decisions | [[Autonomous-Operator-Runtime]] | Governance -> Decisions | product-readable decision history |
| `pivot-log` | Advanced | Pivot Log | [[Autonomous-Operator-Runtime]] | Governance -> Decisions / Advanced | merge under Decisions unless needed |
| `feature-filter` | Advanced | Feature Audit | [[Feature-Register]] + [[Feature-Fit-Register]] | Governance -> Feature Audit | useful for this cleanup; likely advanced later |
| `workflow-registry` | QA / Proof | Workflow Registry | [[Autonomous-Operator-Runtime]] + [[Workflow-Pack-Standard]] | Governance -> Workflow Registry / Advanced | registry/debug surface, not Missions |
| `role-cards` | Advanced | Role Cards | [[Autonomous-Operator-Runtime]] | Governance -> Role Cards / Advanced | permission inspection surface |
| `agent-identity` | Advanced | Agent Identity | [[Agent-Memory-Architecture]] | Runtime or Governance -> Agents | decide placement |
| `runtime-navigation` | Advanced | Runtime Navigation | [[Runtime-Navigation-Map]] | Runtime -> Navigation / Advanced | seeded; keep advanced until readable |
| `runtime-support-loops` | Advanced | Runtime Support Loops | [[Runtime-Support-Loops-Contract]] | Runtime -> Support Loops / Advanced | OSRIL support surface |
| `app-launcher` | Advanced | App Launcher | [[ChaseOS-Studio-Architecture]] | Hidden / Governance -> Advanced | hide unless launcher becomes product feature |
| `workspace-entry` | Orientation | Workspace Setup | [[ChaseOS-Studio-Architecture]] + [[Workspace-Mode-Layer-Feature-Family]] | Main -> Workspace Setup / Settings | onboarding/setup path, not duplicate Home |

## Normalized Feature Names For Operator Confirmation

This is the current feature set that should be used for product UI discussion.

### Main

- Home
- Chat
- Project Workspace
- Missions / Workflow Packs
- Extensions / Chaser Forge

### Knowledge Graph

- Graph View
- Node Inspector
- Knowledge Boxes (planned product abstraction; not a built feature family)
- Graph Hygiene
- Provenance

### Content

- Intake
- Capture
- Sources
- Research Collections

### Runtime

- AI Agents
- Agent Bus
- Schedules
- Task History
- Browser Runtime
- Site Skills

### Personal Memory

- Context Import
- Memory Ledger
- Runtime Memory
- Proactive Briefings
- Review Queue
- Companion Surface (advanced/readiness-only until promoted)

### Governance

- Approvals
- Settings
- Logs / Audit
- Decisions
- QA / Proof
- Feature Audit
- Workflow Registry
- Role Cards
- Advanced

## Feature Family Decisions

Accepted normalization decisions for this pass:

- Home is not a feature family. It is the Interface / Experience landing surface.
- Missions is not a new family yet. It is the product page for VentureOps, Workflow Packs, WML mission mode, and Founder Mode surfaces.
- Extensions is not a new family yet. Current implementation maps to Chaser Forge.
- Knowledge Boxes is not complete and should remain planned/product abstraction until implemented.
- Personal Memory is a navbar/product grouping, not a single canonical family. It maps to Agent Memory, Pulse, Personal Context Import, companion memory, and runtime memory surfaces.
- Logs / Audit, QA / Proof, Feature Audit, Workflow Registry, Role Cards, Pivot Log, and App Launcher are governance/operator/dev surfaces, not user-facing feature families.
- Site Skills remains under SiteOps / Browser Runtime Skill Memory; it should not imply unrestricted browser control.
- Browser Runtime remains partial and authority-gated; it should not be positioned as production browser automation.
- Chaser Forge has a dedicated wiki node now and remains complete for the local governed MVP only.
- Multi-Repo Policy has a dedicated wiki node now and remains policy/deferred, not a first-class MVP page.

## Required Register Updates Completed In This Pass

- `06_AGENTS/Feature-Register.md` now links SIC to [[Source-Intelligence-Core]], Multi-Repo Policy to [[Multi-Repo-Multi-Directory-Access-Policy]], and Chaser Forge to [[Chaser-Forge-Feature-Family]].
- `06_AGENTS/Feature-Fit-Register.md` records this normalization pass and keeps UI implementation deferred.
- `06_AGENTS/ChaseOS-Feature-Family-and-Subfeature-Inventory.md` now records expanded feature/subfeature truth for downstream product documentation and UI architecture confirmation.
- `docs/audits/2026-05-21_feature_family_deep_reconciliation.md` records the evidence matrix behind the corrected inventory.
- Dedicated feature nodes now exist for [[Visual-Capture-Markdown-Ingestion-Feature]], [[Sub-Agent-Presets-Feature]], [[Product-Workflow-Packs-Feature]], and [[ChaseOS-Creator-Engine-Feature]].
- `06_AGENTS/Finalize-ChaseOS-Studio-Product-UI-Handover.md` now treats Pass 0 audit/register sync as complete pending operator confirmation.
- `06_AGENTS/ChaseOS-Studio-Product-Nav-Model.md` now points to this normalization document before navbar implementation.
- `docs/features/-Upcoming-Features-Index.md` links this normalization surface as a planning/control artifact.

## Non-Claims

This pass does not claim:

- navbar implementation is done;
- Dashboard/Home implementation is done;
- page cleanup is done;
- packaged `.exe` UI was visually verified;
- Knowledge Boxes is built;
- Personal Memory Manager is a single canonical feature family;
- browser/runtime/provider/live action authority changed;
- any approval, graph, memory, Agent Bus, host, release, or canonical write action occurred.

## Next Gate

Operator confirmation is required on:

- whether the 16 canonical families are correct;
- whether the 39 panel mappings are correct;
- whether `Site Skills`, `Browser Runtime`, and `Runtime Memory` should be visible in the first MVP sidebar or remain advanced;
- whether `Knowledge Boxes` should become a near-term build target or stay planned;
- whether `Home`, `Missions`, and `Extensions` are the accepted Main labels.

Only after that confirmation should Pass 1 begin: final navbar IA implementation.

## Graph Links

[[Feature-Register]] [[Feature-Fit-Register]] [[Finalize-ChaseOS-Studio-Product-UI-Handover]] [[ChaseOS-Studio-Product-Nav-Model]] [[ChaseOS-Studio-Architecture]]
[[ChaseOS-Feature-Family-and-Subfeature-Inventory]] [[Visual-Capture-Markdown-Ingestion-Feature]] [[Sub-Agent-Presets-Feature]] [[Product-Workflow-Packs-Feature]] [[ChaseOS-Creator-Engine-Feature]]
