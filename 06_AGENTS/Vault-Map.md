---
type: agent-knowledge
title: Vault Map — Full Navigation Guide
updated: 2026-05-16
audience: AI agents, Claude Code, OpenClaw, any operator of this vault
---

# 🗺️ Vault Map — Agent Navigation Guide

> This is the navigation reference for agents operating in the ChaseOS Obsidian vault.
> Use it to locate files and understand folder conventions. Load it when the task involves vault structure or file routing — not as a mandatory default preload.

---

## Who Operates This Vault

**Owner:** Chase  
**Identity:** Sovereign Technō — builder, trader, founder, lifelong learner  
**Operating rules for agents:** See `00_HOME/Assistant-Contract.md`  
**Identity and soul of this vault:** See `SOUL.md` (vault root)  
**Full personal operating system:** See `00_HOME/Operating-System.md`  
**Current sprint priorities:** See `00_HOME/Now.md` ← **read this on every session start**

---

## Vault Root (`/`)

| File                    | Purpose                                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `SOUL.md`               | Agent identity file — who Chase is, how agents should think and behave                                                           |
| `CLAUDE.md`             | Anthropic Agent Harness execution adapter — routing anchor for Claude Code                                                       |
| `OPENAI.md`             | OpenAI execution adapter — covers Chat UI (Tier 3), Codex bus worker when bound / advisory when unbound, Agent Harness (planned) |
| `LOCAL-OSS.md`          | Local/Open-Source execution adapter — Claude Code+Ollama, Cline, OpenHands paths                                                 |
| `N8N.md`                | n8n workflow runtime execution adapter — workflow-scoped access, planned                                                         |
| `README.md`             | Public front door — project overview and reading guide                                                                           |
| `KNOWLEDGE-INDEX.md`    | Root Knowledge Index routing shim only; canonical knowledge taxonomy lives in `02_KNOWLEDGE/Knowledge-Index.md`                  |
| `PROJECT_FOUNDATION.md` | Internal architecture truth — framework model, agent layer, design decisions                                                     |
| `ROADMAP.md`            | Development phases — current phase, outputs, definitions of done                                                                 |
| `FORKING.md`            | Framework forking guidance — Core/Personal split                                                                                 |
| `Welcome.md`            | Obsidian default — ignore                                                                                                        |
| `Untitled.canvas`       | Obsidian default — ignore                                                                                                        |

---

## 00_HOME — Control Tower

| File | Purpose | Agent Priority |
|------|---------|----------------|
| `Personal-Operator-Index.md` | Personal-instance context hub linking identity, doctrine, A-R domains, project OS files, knowledge roots, Personal Map surfaces, and update templates | High - read for personal operator / real-world use prep |
| `Now.md` | Current sprint focus, active priorities | 🔴 High — read every session |
| `Assistant-Contract.md` | Rules governing agent behaviour | 🔴 High — binding on all agents |
| `Principles.md` | Doctrine, identity, decision rules | 🟡 Medium — read for decisions |
| `Dashboard.md` | Master hub, domain links, system status | 🟢 Low — navigation aid only, not required for most tasks |
| `Operating-System.md` | Full 18-domain OS (A–R), project tiers, rules | 🟢 Low — read only when the task is about the OS itself |

**When to read 00_HOME:**
- When updating the personal instance for real-world use, read `Personal-Operator-Index.md`, then the relevant identity/domain/project files it links.
- At the start of any session → read `Now.md` + relevant `Project-OS.md`
- When making a decision that affects priorities → read `Principles.md`
- When unsure how to behave → read `Assistant-Contract.md`
- `Dashboard.md` and `Operating-System.md` are **not** default context — load them only when explicitly needed

---

## 01_PROJECTS — Active Projects

Each subfolder is a domain/project with a named OS file (e.g., `ChaseOS-OS.md`, `TradeSync-OS.md`).

| Folder | File | Domain | Status |
|--------|------|--------|--------|
| `ChaseOS/` | `ChaseOS-OS.md` | A — System Infrastructure | Active |
| `TradingSystems/` | `TradingSystems-OS.md` | B — Trading Systems / Market Ops | Active |
| ↳ `TradingSystems/` | `DEXPerps-OS.md` | B — Perps overview (parent) | Active |
| ↳ `TradingSystems/` | `CryptoPerps-OS.md` | B — Crypto perps subdomain | Active |
| ↳ `TradingSystems/` | `TradFiPerps-OS.md` | B — TradFi perps subdomain | Active |
| `StrikeZone/` | `StrikeZone-Crypto-OS.md` | C — StrikeZone Crypto | Live |
| `IndicatorRnD/` | `IndicatorRnD-OS.md` | D — Indicator R&D / Pine Script | Active |
| `TradeSync/` | `TradeSync-OS.md` | E — TradeSync AI | Building |
| `GeoMacro/` | `GeoMacro-OS.md` | F — Macro Intelligence | Building |
| `FullStackWeb2Web3/` | `FullStackWeb2Web3-OS.md` | H — Full-Stack / Software Engineering | Active |
| `HypeList/` | `HypeList-OS.md` | H — Full-Stack Portfolio | Building |
| `Cybersecurity/` | `Cybersecurity-OS.md` | I — Bug Bounty / Security | Active |
| `GreyTheory/` | `GreyTheory-OS.md` | I — Autonomous Bug Bounty Hunter | Concept |
| `University/` | `Degree-OS.md` | J — Academic Ops | Active |
| `University/Modules/` | `Modules.md` | J — Academic Ops | Module child tree / coursework bridge |
| `CareerOps/` | `CareerOps-OS.md` | K — Career / Freelance | Active |
| `ContentEngine/` | `ContentCreation-OS.md` | L — Content / Brands | Active |
| ↳ `ContentEngine/` | `ChaseInTech-OS.md` | L — Builder / AI / Dev persona | Active |
| ↳ `ContentEngine/` | `ChaserSol-OS.md` | L — Crypto / Trading persona | Active |
| `Language-Mobility/` | `Mandarin.md` | R - Language Learning / Global Mobility | Source-derived / review required |
| `Businesses/` | `Businesses-OS.md` | M — Ventures Registry | Mixed |
| ↳ `Businesses/` | `EcommerceReselling-OS.md` | M — E-commerce / reselling parent | Active |
| ↳ `Businesses/` | `Marketplaces.md` | M — Platform reference (eBay, StockX, etc.) | Reference |

**When to read a Project-OS:**
- Before doing ANY work on that project
- When asked to update status, goals, or open loops
- Structure: Mission → Key Components → Current Status → 30/60/90 Goals → Open Loops → Resources

---

## 02_KNOWLEDGE — Domain Knowledge Base

Each subfolder has a named knowledge index file defining the domain. Notes are added inside each folder over time. Master index: `[[Knowledge-Index]]`.

| Folder               | Domain                            | Notes Location                                                  |
| -------------------- | --------------------------------- | --------------------------------------------------------------- |
| `AI-Agents/`         | AI / Agent Engineering (Domain G) | `AI-Agents/AI-Agent-Engineering.md` + notes inside              |
| `Computer-Science/`  | CS fundamentals (Domain J)        | `Computer-Science/Computer-Science.md` + notes inside           |
| `Trading/`           | Trading & Markets (Domain B)      | `Trading-Systems/Trading-Systems-Engineering.md` + notes inside |
| `Full-Stack/`        | Full-Stack Engineering (Domain H) | `Full-Stack/Full-Stack-Engineering.md` + notes inside           |
| `Cybersecurity/`     | Security knowledge (Domain I)     | `Cybersecurity/Cybersecurity.md` + notes inside                 |
| `Mathematics/`       | Mathematics (Domain J)            | `Mathematics/Mathematics.md` + notes inside                     |
| `Hardware/`          | Hardware / Robotics (Domain N)    | `Hardware/Hardware-Robotics.md` + notes inside                  |
| `Doctrine/`          | Philosophy / Identity (Domain O)  | `Doctrine/Doctrine-Philosophy.md` + notes inside                |
| `Fitness/`           | Physical Discipline (Domain P)    | `Fitness/Fitness-Physical.md` + notes inside                    |
| `Networking-Social/` | Social Capital (Domain Q)         | `Networking-Social/Networking-Social-Capital.md` + notes inside |
| `Language/`          | Language Learning (Domain R)      | `Language/Language-Learning.md` + `Language/Mandarin-HSK1.md`   |
| `Runtime-Ops/`       | Runtime Ops / Linux / Infrastructure | `Runtime-Ops/Runtime-Ops.md` + nodes for Linux/WSL, WSL2 Ubuntu setup, Linux commands, Hermes, OpenClaw |
| `Platform-Strategy/` | Platform Strategy / Sovereign Playbook | `Platform-Strategy/Platform-Strategy.md` + platform/portfolio/action nodes |
| `Content-Distribution/` | Content / Brand / Distribution | `Content-Distribution/Content-Distribution.md` + digest/CTA nodes |

**Agent rule:** When adding a new concept note, it goes inside the matching domain folder and gets linked in that domain's knowledge index file (e.g., `AI-Agent-Engineering.md`, `Trading-Systems-Engineering.md`).

**Knowledge taxonomy:** Every durable note in `02_KNOWLEDGE/` must declare `knowledge_class` in frontmatter. Classes: `user-origin`, `source-derived`, `synthesized`, `generated-ideas`, `system-operational`, `canonical-state`. See `[[Knowledge-Taxonomy]]` for the full schema and generated-ideas rules.

---

## 03_INPUTS — Raw Inbound Material

Quarantine zone for all external content. Tier 4 by default. Do not treat as knowledge. Process through the five-stage flow: `[[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]]` · `[[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]]` · `[[Ingestion-Architecture]]`.

| File / Subfolder | What Goes Here |
|------------------|----------------|
| `03_INPUTS-Folder-Guide.md` | Front door — subfolders, naming convention, queue states, input methods, governing SOPs |
| `Digests/` | Perplexity / Grok / newsletter digests / web research summaries |
| `NotebookLM/` | NotebookLM document synthesis outputs |
| `Transcript-Raw/` | Raw verbatim transcripts — YouTube, lecture, meeting, podcast |
| `YouTube-Notes/` | Pre-curated structured notes from YouTube videos (lighter transcript variant) |
| `Sources/` | Articles, PDFs, imported documents, course materials — catch-all |
| `Clipboard/` | Copied text fragments, prompt outputs, short external clips |
| `Personal-Context-Intake/` | Raw personal context exports, review maps, final node coverage audits, and candidate promotion queues for the personal ChaseOS instance; Studio import contract is `06_AGENTS/Personal-Context-Import-Feature.md` |

**Naming convention:** `YYYY-MM-DD_[source]-[topic-slug].md`
**Processing SOPs:** `04_SOPS/Research-Ingest-SOP.md` · `04_SOPS/Untrusted-Input-Handling-SOP.md`
**Architecture:** `06_AGENTS/Ingestion-Architecture.md`

---

## 04_SOPS — Standard Operating Procedures

Binding process documents. Agents must follow these.

| File | When to Use |
|------|-------------|
| `Feature-Filter-SOP.md` | **Phase 9** — 6-question gate before adopting any new feature into the roadmap |
| `Build-Log-SOP.md` | Every coding / build / infra session |
| `Research-Ingest-SOP.md` | Every time raw input needs processing into knowledge |
| `Untrusted-Input-Handling-SOP.md` | Quarantine, triage, sanitize, route, and promote all external content |
| `Credential-Boundaries-SOP.md` | Any session touching API keys, secrets, or external credentials |
| `Discord-Control-Plane-Setup-SOP.md` | Binding a local Discord control-plane instance through `.chaseos/discord_instance_bindings.yaml` and `.env` without publishing IDs/secrets |
| `Agent-Failure-Ambiguity-SOP.md` | Stop/escalate behavior for all agent failure and ambiguity modes |
| `Morning-Thesis-Workflow.md` | Pre-market session — produces thesis output in `07_LOGS/Morning-Thesis/` |
| `Weekly-Trading-Review-Workflow.md` | End of trading week — produces review in `07_LOGS/Trading-Weekly/` |

---

## 05_TEMPLATES — Reusable Templates

Copy these when creating new notes of these types.

| Template | Use For |
|----------|---------|
| `Decision-Ledger-Entry-Template.md` | **Phase 9** — new immutable decision entry in `07_LOGS/Decision-Ledger/` |
| `Pivot-Log-Entry-Template.md` | **Phase 9** — new immutable pivot entry in `07_LOGS/Pivot-Log/` |
| `Feature-Filter-Template.md` | **Phase 9** — 6-question feature filter pass (run before adopting any new feature) |
| `Workspace-Mode-Profile-Template.md` | Copyable WML profile contract for `workspace-mode.yaml` or Project-OS frontmatter |
| `Daily-Note-Template.md` | New daily note in `07_LOGS/Daily/` |
| `Project-OS-Template.md` | New project operating file |
| `Decision-Log-Template.md` | Any significant decision |
| `Experiment-Template.md` | Any structured experiment or test |
| `Source-Note-Template.md` | Any processed single-source research note |
| `Synthesis-Note-Template.md` | Multi-source synthesis, digest output, or platform synthesis (NotebookLM, Perplexity multi-topic) |
| `Adapter-Compliance-Checklist.md` | Checklist for activating, auditing, or upgrading an execution adapter — 5 compliance tiers |
| `Trade-Journal-Entry-Template.md` | New trade journal entry in `07_LOGS/Trade-Journal/` |
| `Agent-Session-Log-Template.md` | Current base template for dated records in `07_LOGS/Agent-Activity/`; use under the reconciled runtime/audit doctrine, not as a second build-log lane |
| `Agent-Activity-Log-Template.md` | Agent activity log — security/audit-focused; elevated actions, hook blocks, automated workflows |
| `Agent-Audit-Log-Template.md` | Formal agent audit log for permission review sessions |
| `Morning-Thesis-Output-Template.md` | Morning thesis output in `07_LOGS/Morning-Thesis/` |
| `Session-Prompt-Patterns.md` | Reusable session patterns — 6 types with read order, scope, and close-out requirements |

**Agent rule:** Never create project, decision, or source notes from scratch. Always use the template.

---

## 06_AGENTS — Agent Configuration

| File | Purpose |
|------|---------|
| `Agent-Control-Plane.md` | **Phase 4 canonical control doc** — what agents can do, trust model, permissions, failure policy |
| `Permission-Matrix.md` | Explicit permission table by agent type, action, and target — canonical protected-file source |
| `Trust-Tiers.md` | Trust tier definitions (Tier 1–4) with operational rules |
| `Handoff-Protocol.md` | Session start/close and context handoff protocol |
| `Backends-Supported.md` | Provider/execution-surface/access-mode matrix — all surfaces with execution adapter references |
| `ChaseOS-Discord-Control-Plane.md` | Discord as current operator/control transport; local binding, no-secret validation, and Studio status boundary for runtime lanes |
| `Personal-Context-Import-Feature.md` | Personal Context Import feature contract; Studio import planner, digest-gated preview writer, approved-preview artifact executor, temp-only fixture harness, runtime reference readiness, canonical-promotion approval preview, and approved canonical route writer for raw intake, parent/child node routing, Knowledge Index resolution, secure storage, WML `personal_os`, and Personal Map candidate boundaries |
| `Use-Case-Mode-Architecture.md` | **Workspace Mode Layer** — mode-aware operating context for personal, study/research, founder/venture, business ops, runtime/agent ops, and unknown workspaces |
| `Workspace-Mode-Layer-Feature-Family.md` | **Workspace Mode Layer** — canonical WML feature-family node linking runtime, profile, AOR gate, Studio panel, Chat selector, visual QA, handoff, and closeout evidence |
| `Workspace-Mode-Profile-Standard.md` | **Workspace Mode Layer** — machine-readable profile contract, required fields, inference behavior, fail-closed unknown mode, route preview, review-only rollout planning, validated draft packets, profile-write approval requests, guarded profile writer, no-execution dispatch gate, WML-gated AOR dry-run executor, live-execution approval request gate, exact-once live executor, and first approved runtime foundation profiles |
| `Adaptive-Runtime-Surface-Layer.md` | **Runtime governance** — canonical ARSL doc for runtime surface registry, capability classification, routing proposal, MCP summary exposure, and audit boundaries |
| `Runtime-Surface-Manifest-Standard.md` | **Runtime governance** — manifest schema/field standard for registering ARSL runtime surfaces without granting execution authority |
| `Execution-Adapter-Standard.md` | **Phase 5 standard** — defines execution adapter concept, 4 classes, 11 required sections |
| `Claude-Memory-System.md` | Claude Code memory system (`~/.claude/`) — what belongs there, stale-memory risks, update protocol |
| `Hook-Patterns.md` | Session-open/close hook patterns for Claude Code; PreToolUse/PostToolUse guards; protected-file backstop |
| `Subagent-Patterns.md` | When and how to use subagents; permission inheritance rules; multi-adapter handoff patterns |
| `Ingestion-Architecture.md` | **Phase 6A** — five-layer ingestion pipeline; content type vocabulary; trust assignments; advisory vs harness roles; automation boundaries; cadence model |
| `SIC-Architecture.md` | **Phase 7** — Source Intelligence Core architecture; five SIC layers; SIC output classes → ChaseOS vault routing table; what SIC is/is not |
| `ChaseOS-Gate.md` | **Phase 6 preflight** — execution control layer above all adapters; enforcement layers; hook scripts; adapter manifests; what is enforced vs documented only |
| `Adapter-Manifest-Standard.md` | **Phase 6 preflight** — schema and required fields for adapter manifests; manifest lifecycle; manifest vs markdown doc |
| `Agent-Registry.md` | All AI agents — trust tier, permission scope, capabilities, execution adapter, status |
| `Agent-Security-Model.md` | Framework-level threat model — 8 attack classes, fail-closed principles, surface-specific notes |
| `Agent-Output-Conventions.md` | Output rules for ALL agent backends (Claude, OpenAI, n8n, etc.) |
| `Vault-Map.md` | **This file** — full navigation guide for agents |
| `Tool-Map.md` | Every tool and platform in the ChaseOS stack |
| `Agent-Memory-Architecture.md` | **Cross-phase** — formal five-layer memory model (Shared System Doctrine, User-Specific, Runtime-Specific + Agent Identity Ledger + Execution Repair Memory, Workspace-Local, Execution-History); architecture for how ChaseOS memory grows with the user |
| `Claude-Identity-Ledger.md` | **Phase 9 seeded** — first human-readable Agent Identity Ledger for the Claude / Anthropic Agent Harness lane; advisory Layer C memory, not an authority source |
| `Feature-Register.md` | **Cross-phase** — canonical register of all ChaseOS feature families with status, phase, and canonical doc references |
| `Scheduled-Briefing-Pipelines.md` | **Phase 9 planned** — six-component pipeline schema (trigger, input adapters, execution adapter, writeback targets, delivery adapters, guardrail profile); what problem SBP solves; StrikeZone Market Digest Publisher as first implementation |
| `Autonomous-Operator-Runtime.md` | **Phase 9** — OS-level execution infrastructure; bounded autonomy; repo-aware operation; multi-repo policy; audit trails; Execution Repair Memory integration; OpenClaw-style operator support |
| `ChaseOS-Vault-Maintenance.md` | **Phase 9** — Operating system graph maintenance sweep; documents the `vault.maintain` MCP tool and `chaseos maintain` capabilities for agents and humans |
| `Runtime-Navigation-Map.md` | **Phase 9 planned** — per-runtime evolving overlay map of preferred vault routes, trusted zones, failure points, safe writeback paths, and escalation boundaries; navigational dimension of Layer C; distinct from Vault Map (static system ref), Layer C behavioral profile, Agent Identity Ledger, and Execution Repair Memory |
| `Hermes-Runtime-Profile.md` | **Phase 9 seeded** — human-readable Hermes navigation/runtime overlay; connects bounded Hermes lane, Vault Map routing, markdown indexes, and future standalone representation |
| `Phase9-Adopted-Feature-Specification.md` | **Phase 9** — canonical spec for all 17 adopted Phase 9 features (10 first-wave + 6 second-wave + Paperclip candidate); authoritative over ROADMAP summaries |
| `ChaseOS-Hardening-Passover.md` | **All-phase hardening** — complete passover document for all agents and runtimes covering Phase 1–9; 31 open items classified as AUTONOMOUS vs REQUIRES-OPERATOR-INPUT; 19 autonomous items in 3 sprints; Gate hook + connector/capture + Phase 9 runtime hardening; supersedes `Phase9-Hardening-Passover.md` |
| `Phase9-Hardening-Passover.md` | **SUPERSEDED** — see `ChaseOS-Hardening-Passover.md` |
| `OpenClaw-Adapter-Spec.md` | **Phase 9 active** — runtime contract for OpenClaw as the active experimental bounded operator adapter lane; permission envelope, injected file governance, activation checklist, trust tier progression; replaces Hermes as active lane |
| `OpenClaw-Runtime-Profile.md` | **Phase 9 seeded** — human-readable OpenClaw navigation/runtime overlay; connects active execution lane, Vault Map routing, markdown indexes, schedules, and future standalone representation |
| `OpenHuman-Runtime-Profile.md` | **Reference-only / retired runtime candidate** — records why OpenHuman was unwired from active ChaseOS runtime integration and retained only as a product/feature study source |
| `OpenHuman-Adapter-Spec.md` | **Retired reference adapter note** — documents the closed OpenHuman adapter lane, API-key credential mismatch, removed watchdog, and reopen criteria |
| `Runtime-Instance-Provenance-Promotion-Caller-Alignment.md` | **Phase 9 seeded / Phase 10 relevant** — runtime-instance caller-alignment doctrine for future provenance-aware promotion paths; keeps OpenClaw/Hermes aligned to the same centralized Gate seam without premature authority expansion |
| `Runtime-Instance-Authority-Parity.md` | **Phase 9 seeded** — standing constitutional ruling that Hermes and OpenClaw are peer runtime instances with equal authority ceilings under AOR/Gate governance |
| `OpenClaw-First-Bounded-Promotion-Path.md` | **Phase 9 seeded** — OpenClaw bounded promotion-path contract for future AOR/Gate-mediated canonical promotion without live authority expansion |
| `Hermes-First-Bounded-Promotion-Path.md` | **Phase 9 seeded** — Hermes bounded promotion-path contract for future AOR/Gate-mediated canonical promotion with explicit control-plane/approval posture |
| `Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md` | **Phase 9 seeded** — pair-level draft contract spec for OpenClaw/Hermes promotion workflow + role-card shapes, including canonical helper comparison for pre-activation failure posture and the shared validation surface those contracts now depend on |
| `OpenClaw-Promotion-Activation-Readiness-Gate.md` | **Phase 9 seeded** — OpenClaw runtime-specific readiness gate for bounded promotion activation review; documents fail-closed blockers and canonical helper routing |
| `Hermes-Promotion-Activation-Readiness-Gate.md` | **Phase 9 seeded** — Hermes runtime-specific readiness gate for bounded promotion activation review; documents control-plane posture, fail-closed blockers, and canonical helper routing |
| `Portable-Runtime-Identity-and-User-Binding.md` | **Phase 9 seeded / Phase 10 relevant** — cross-runtime architecture for separating constitutional runtime governance, portable runtime identity, machine-local bindings, and detachable personal user attachment |
| `ChaseOS-Runtime-State-and-Gateway-Design.md` | **Phase 9 seeded / Phase 10 relevant** — runtime-state resolver architecture, fail-closed startup posture, and local-first gateway/interface direction |
| `Browser-Autonomy-Policy.md` | **Phase 9 seeded** — governance layer for bounded browser-based autonomous work; defines allowed task classes, approval boundaries, forbidden actions, and markdown/standalone routing continuity |
| `Browser-Task-Patterns.md` | **Phase 9 seeded** — reusable bounded browser task classes; bridges browser execution patterns, registry entries, audit surfaces, and future standalone mapping |
| `Core-Personal-Split-Implementation-Plan.md` | **Phase 9 seeded** — concrete implementation plan for turning the conceptual Core/Personal split into a structural one while preserving markdown indexes, Vault Map routing, and standalone portability |
| `Core-Export-Git-Safe-Extraction-Development-Plan.md` | **Phase 9/10 active plan** — runtime-handoff-ready implementation plan for expanding the minimal Core export into a proper Git-safe Core repository candidate through inventory, templates, manifest expansion, dry-run verification, manual review, approved export update, and later separate Git-init Gate |
| `Core-Export-Sync-Procedure.md` | **Phase 9 seeded** — priority and sync doctrine: live repo remains primary development surface; Core export and sibling repo work are long-term support lanes governed by deliberate reviewed sync |
| `Markdown-to-Standalone-Bridge.md` | **Phase 9 seeded** — explicit bridge layer mapping markdown docs, index-note surfaces, and machine-readable runtime scaffolds forward into future standalone ChaseOS representations |
| `Phase10-Desktop-Shell-Engineering-Plan.md` | **Phase 10 ACTIVE** — canonical engineering plan for ChaseOS Studio desktop shell; framework decision (PyWebView selected, Tauri migration path documented); full architecture (StudioAPI bridge, Cytoscape.js graph, subphase specs 10A–10F, IPC contract, graph data contract, packaging plan, runtime handover instructions) |
| `ChaseOS-Studio-Freeform-Canvas-Graph-Linking.md` | **Phase 10E SPEC SEEDED / NOT BUILT** — product/technical spec for workspace-local Studio Canvas/Whiteboard drafts linked to graph nodes; defines canvas JSON objects, pointer-only graph-node references, read-only provenance behavior, no-canonical-until-Gate boundary, and implementation task split |
| `Companion-Surface-Mobile-Tablet-Architecture.md` | **Phase 10 seeded / not live** — mobile/tablet/browser companion-surface architecture for brief viewing, approval inboxes, capture-trigger previews, runtime status cards, gateway/mobile delivery posture, and strict Gate/AOR/StudioService authority ceiling |
| `Live-Visual-Shell-Contract.md` | **Phase 10 seeded / not implemented** — read-only visual-state contract mapping AOR/OSRIL/runtime lifecycle/approval posture into Studio shell animation/status states; defines source classes, precedence, packet shape, QA proof, and explicit no-execution/no-approval/no-write authority boundary |
| `Runtime-Navigation-and-Browser-Governance-Standalone-Application.md` | **Phase 9 seeded** — first worked bridge application mapping runtime navigation plus browser governance into future standalone operational inspector surfaces |
| `Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application.md` | **Phase 9 seeded / Phase 10 relevant** — browser monitoring/evidence summary-context application for watchlists, change summaries, evidence posture, extraction summaries, and quarantine-aware browser outputs |
| `Runtime-State-and-Bootstrap-Standalone-Application.md` | **Phase 9 seeded** — second worked bridge application mapping runtime state resolution plus bootstrap/user attachment into future standalone posture and startup inspectors |
| `Standalone-Summary-Context-Layer.md` | **Phase 10 seeded on Phase 9 substrate** — feature layer for treating summaries as typed operating artifacts with runtime, authority, source, routing, and promotion posture |
| `Summary-Context-Taxonomy-and-Object-Model.md` | **Phase 9 seeded / Phase 10 relevant** — canonical summary-family and summary-class taxonomy plus shared object-model direction for unifying summary handling across runtime-state, workflow, coordination, and operator-shell surfaces |
| `Workflow-Registry-and-Role-Cards-Standalone-Application.md` | **Phase 9 seeded** — third worked bridge application mapping workflow manifests plus role-card permission envelopes into future standalone execution-contract and approval-aware surfaces |
| `Runtime-Agent-Bus-and-Coordination-Standalone-Application.md` | **Phase 9 seeded** — fourth worked bridge application mapping the dual-runtime coordination substrate into future standalone coordination inspectors, blocker/review views, and runtime liveness surfaces |
| `Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md` | **Phase 9 seeded** — fifth worked bridge application mapping runtime shell doctrine, OSRIL approval/session visibility, and runtime-browser surfaces into future standalone operator control surfaces |
| `Live-Operator-Shell-Browser-Surface.md` | **Phase 10 browser shell scope seeded / no live authority** — scoped Live Operator Shell browser lane defining panels, visible-control UX, no-action/readiness states, dependency routing, rollout stages, and lower-phase approval/backend blockers |
| `Control-Plane-Ingress-and-Bus-Translation.md` | **Phase 9 seeded / Phase 10 relevant** — canonical rule that actionable control-surface input must translate into structured ChaseOS state rather than being coordinated in transport-local chat or panel state |
| `Voice-IO-Architecture.md` | **Phase 10 seeded / OSRIL relevant** — provider-neutral voice ingress/egress architecture for Studio/OSRIL; defines voice sessions, STT/TTS adapter boundary, transcript/audit retention, trust-tier handling, and no-dispatch/no-canonical-mutation proof requirements |
| `Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping Core-vs-Personal repo mode, export safety, template staging, and support-lane posture into future standalone operator views |
| `Project-Cockpit-and-Workspace-Browser-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping Project-OS files and SIC workspaces into future standalone project cockpits, workspace browsers, and typed project/workspace cross-link surfaces |
| `Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md` | **Phase 9 seeded** — worked bridge application mapping provenance contracts, build/runtime chronology, and approval traceability into future standalone provenance explorer and chronology browser surfaces |
| `Provenance-Schema-and-Trace-Idea-Implementation-Plan.md` | **Phase 9 seeded** — implementation plan for the first real provenance substrate: runtime provenance schema, validator, `trace_idea` workflow, trace-report routing, and Gate-adjacent minimum checks |
| `Phase9-Implementation-Closure-Plan.md` | **Phase 9 active** — ordered implementation program for clearing the highest-impact remaining Phase 9 substrate in dependency order before further downstream feature-R&D execution/design |
| `Consolidated-Operator-Cockpit-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — consolidated application mapping runtime, workflow, coordination, project, workspace, approval, chronology, and repo-mode visibility into one future operator cockpit surface while preserving subsystem authority boundaries |
| `Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping `02_KNOWLEDGE/` indexes, classified knowledge notes, and knowledge provenance/promotion posture into future standalone knowledge navigator and domain browser surfaces |
| `Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping runtime-shell doctrine, model bindings, config-store concepts, lifecycle/readiness posture, and scaffold/onboarding concepts into future standalone settings and product-shell setup surfaces |
| `Governed-Promotion-and-Review-Center-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping approvals, review-needed items, graduation proposals, provenance-linked promotion checks, and governance context into future standalone review-center surfaces |
| `Cross-Panel-Object-Model-Consolidation.md` | **Phase 9 seeded / Phase 10 relevant** — consolidation pass defining shared higher-level cross-panel object families so cockpit, knowledge, settings, project/workspace, runtime, provenance, and review surfaces can compose lower-level truth coherently |
| `Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping scorecard doctrine, runtime-quality posture, compliance/overreach history, and evidence-backed runtime performance visibility into future standalone quality surfaces |
| `Runtime-Support-Loops-Contract.md` | **Phase 10 seeded / Phase 9-governed** — advisory-only contract for QA verification, proactive suggestions, usage tracking, and repair candidates over existing runtime-memory, Pulse, Studio, and AOR evidence; no approval execution, memory mutation, runtime dispatch, Agent Bus write, provider/connector call, self-upgrade, or canonical writeback |
| `ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI.md` | **Phase 10 seeded / Phase 9-governed** — governed Pulse feedback review/apply UX contract over existing candidate inspector, review-decision log, Approval Center, and `candidate_apply.py` dry-run/non-canonical runtime-memory apply lanes; no new apply backend, memory approval, Agent Bus write, schedule activation, provider/connector call, canonical Personal Map mutation, `02_KNOWLEDGE/` writeback, or hidden Studio mutation authority |
| `Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping execution-repair doctrine, fail-closed runtime-state posture, recovery contracts, and repair-memory visibility into future standalone resilience surfaces |
| `Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping layered memory architecture, runtime-memory stores, navigation memory, learned-memory families, and memory-evidence visibility into future standalone memory-inspector surfaces |
| `Agent-Identity-Ledger-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping behavioral evolution, drift, doctrine adherence, correction history, and identity-evidence visibility into future standalone runtime identity-ledger surfaces |
| `Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping graph substrate node/edge/topology semantics into future standalone graph-native consolidation surfaces |
| `Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md` | **Architecture-ready / implementation-deferred** — Phase 9/backend dependency contract for explicit graph-store roots, durable node identity, migration proof, stale-source rejection, and Gate-covered graph-store writes; does not activate Studio graph persistence or canonical graph mutation |
| `Memory-Editing-and-Curation-Surfaces-Standalone-Application.md` | **Phase 9 seeded / Phase 10 relevant** — worked bridge application mapping memory-maintenance rules, layer-specific editability, and evidence-backed memory lifecycle work into future standalone memory curation surfaces |
| `Feature-Fit-Register.md` | **Cross-phase** — canonical phase/layer triage register for all ChaseOS feature families; Phase 8 complete; Phase 9 first-wave and second-wave classified; Cross-Cutting section added (2026-04-08) |
| `Security-Research-Workflow-Layer.md` | **Cross-Cutting** — domain workflow specialization for security research; intake paths, SIC workspace conventions, trust state separation, promotion rules, auditability requirements; uses Phase 7+8 infrastructure; automation is Phase 9 |
| `ChaseOS-Studio-Architecture.md` | **Phase 10** — canonical product architecture for ChaseOS Studio; standalone desktop graph-first operating surface; 18 sections: product identity, why Studio exists, ChaseOS vs Studio distinction, operating modes (native/markdown-compatible), entry points, graph prerequisites (node_id, schemas, builder/indexer/watcher), node ontology, edge ontology, trust/provenance model, service layer (traffic controller), action model, interface views, implementation subphases 10A–10F, product identity + forkable surface, guardrails, phase dependencies |
| `role-cards/` | **Phase 9 Pass 1** — AOR runtime permission envelopes; `operator-briefing.yaml`, `vault-maintenance.yaml`; schema in `_schema.yaml` |

---

## 07_LOGS — Session Records

All time-stamped output. Never delete from here.

| Subfolder | Contents | Naming Convention | Index |
|-----------|----------|-------------------|-------|
| `Build-Logs/` | Build session records | `YYYY-MM-DD-[Project]-[descriptor].md` | `[[Build-Logs-Index]]` |
| `Daily/` | Daily notes | `YYYY-MM-DD.md` | `[[Daily-Index]]` |
| `Trading-Weekly/` | Weekly trading reviews | `YYYY-Wxx-Trading-Review.md` | `[[Trading-Weekly-Index]]` |
| `Trade-Journal/` | Trade journal entries | `YYYY-MM-DD-[ASSET]-[DIRECTION].md` | `[[Trade-Journal-Index]]` |
| `Morning-Thesis/` | Pre-market thesis outputs | `YYYY-MM-DD-thesis.md` | `[[Morning-Thesis-Index]]` |
| `Agent-Activity/` | Runtime activity logs, automation traces, operational binds, and AOR audit records | `YYYY-MM-DD-[agent]-[descriptor].md` (logs) · `YYYYMMDD-HHMMSS__[workflow]__[audit_id].json` (AOR) | `[[Agent-Activity-Index]]` |
| `Decision-Ledger/` | **Phase 9 Pass 1** — immutable decision records; append-only | `YYYY-MM-DD_[slug].md` | `Index.md` |
| `Pivot-Log/` | **Phase 9 Pass 1** — immutable scope/direction pivot records; append-only | `YYYY-MM-DD_[slug].md` | `Index.md` |
| `Operator-Briefs/` | AI-generated operator morning/close-day briefs (OpenClaw runtime output) | `YYYY-MM-DD-operator-today.md` / `YYYY-MM-DD-operator-close-day.md` | `[[Operator-Briefs-Index]]` |
| `SBP-Runs/` | Scheduled Briefing Pipeline execution records | `YYYY-MM-DD-sbp_[pipeline]-run.md` | `[[SBP-Runs-Index]]` |
| `Graph-Reports/` | Graph substrate analysis reports | `YYYY-MM-DD-graph-[descriptor].md` | `[[Graph-Reports-Index]]` |
| `Graph-Snapshots/` | Graph snapshot artifacts | — | — |
| `Hygiene-Reports/` | Vault hygiene scan/fix reports | `YYYY-MM-DD-vault-hygiene-report.md` | `[[Hygiene-Reports-Index]]` |
| `Trace-Reports/` | Read-only derivative lineage tracing outputs | `YYYY-MM-DD-trace-[slug].md` | `[[TRACE-REPORTS-Folder-Guide]]` |
| `Promotion-Records/` | Canonical graduation records and promotion artifacts | `YYYY-MM-DD-\[Target\]-promotion.md` | `[[PROMOTION-RECORDS-Folder-Guide]]` |
| `Graduation-Proposals/` | Knowledge graduation proposals from generated-ideas | — | — |
| `Schedule-State/` | Schedule state change log (JSONL) | — | — |

---

## 99_ARCHIVE — Reference & Archive

Non-operational. Agents do not route here for live context.

| Folder / File | Purpose | Index |
|---------------|---------|-------|
| `Documentation-History/` | Dated archive notes for major passes | `[[Documentation-History-Index]]` |
| `Imported-Context/` | Pre-vault historical session files (2026-03-18) | `[[Imported-Context-Index]]` |
| `Audits/` | Formal audit reports — Project-OS coverage, domain gap analysis | `[[Audits-Index]]` |
| `Reporting/` | R&D update reports, canonical deep audits | `[[Reporting-Index]]` |

---

## Agent Context Routing — Quick Reference

| If asked about...                                                                                                                                                           | Read first                                                                                                                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Current priorities / what to work on                                                                                                                                        | `00_HOME/Now.md`                                                                                                                                                                                  |
| Any specific project                                                                                                                                                        | `01_PROJECTS/[Project]/[Project]-OS.md`                                                                                                                                                           |
| How to behave / what's allowed                                                                                                                                              | `00_HOME/Assistant-Contract.md` + `06_AGENTS/Agent-Control-Plane.md`                                                                                                                              |
| Agent permissions and trust                                                                                                                                                 | `06_AGENTS/Permission-Matrix.md` + `06_AGENTS/Trust-Tiers.md`                                                                                                                                     |
| Agent output rules (all backends)                                                                                                                                           | `06_AGENTS/Agent-Output-Conventions.md`                                                                                                                                                           |
| Runtime/audit activity routing                                                                                                                                              | `07_LOGS/Agent-Activity/Agent-Activity-Folder-Guide.md` + `07_LOGS/Agent-Activity/Agent-Activity-Index.md`                                                                                        |
| Session start/close and handoff                                                                                                                                             | `06_AGENTS/Handoff-Protocol.md`                                                                                                                                                                   |
| Failure, ambiguity, or injection                                                                                                                                            | `04_SOPS/Agent-Failure-Ambiguity-SOP.md`                                                                                                                                                          |
| Untrusted or external content                                                                                                                                               | `04_SOPS/Untrusted-Input-Handling-SOP.md`                                                                                                                                                         |
| Credentials or API keys                                                                                                                                                     | `04_SOPS/Credential-Boundaries-SOP.md`                                                                                                                                                            |
| Security architecture and threats                                                                                                                                           | `06_AGENTS/Agent-Security-Model.md`                                                                                                                                                               |
| Security research operating model (intake, workspaces, promotion)                                                                                                           | `06_AGENTS/Security-Research-Workflow-Layer.md`                                                                                                                                                   |
| Which runtime surfaces exist                                                                                                                                                | `06_AGENTS/Backends-Supported.md`                                                                                                                                                                 |
| Workspace mode / use-case-aware routing                                                                                                                                     | `06_AGENTS/Workspace-Mode-Layer-Feature-Family.md` + `06_AGENTS/Use-Case-Mode-Architecture.md` + `06_AGENTS/Workspace-Mode-Profile-Standard.md` + `runtime/workspace_modes/` + `runtime/studio/workspace_mode_panel.py` + `runtime/studio/phase11_chat_panel_contract.py`                                                                           |
| Workspace mode AOR route preview                                                                                                                                            | Canonical CLI: `chaseos runtime workspace-mode route-preview`; helper module: `runtime/workspace_modes/aor_routing_preview.py`                                                                     |
| Workspace mode first-profile rollout plan                                                                                                                                   | Canonical CLI: `chaseos runtime workspace-mode rollout-plan`; helper module: `runtime/workspace_modes/profile_rollout_plan.py`                                                                     |
| Workspace mode profile draft packet                                                                                                                                          | Canonical CLI: `chaseos runtime workspace-mode draft-packet`; helper module: `runtime/workspace_modes/profile_draft_packet.py`                                                                     |
| Workspace mode profile-write approval request and guarded writer                                                                                                             | Canonical CLI: `chaseos runtime workspace-mode write-approval-request` and `chaseos runtime workspace-mode write-profiles`; helper modules: `runtime/workspace_modes/profile_write_approval_request.py` and `runtime/workspace_modes/profile_guarded_writer.py` |
| Workspace mode AOR dispatch gate                                                                                                                                            | Canonical CLI: `chaseos runtime workspace-mode dispatch-gate`; helper module: `runtime/workspace_modes/aor_dispatch_gate.py`                                                                    |
| Workspace mode AOR dry-run executor                                                                                                                                         | Canonical CLI: `chaseos runtime workspace-mode dispatch-dry-run`; helper module: `runtime/workspace_modes/aor_dispatch_dry_run_executor.py`                                                    |
| Workspace mode AOR live-execution approval gate                                                                                                                             | Canonical CLI: `chaseos runtime workspace-mode live-execution-approval-gate`; helper module: `runtime/workspace_modes/aor_live_execution_approval_gate.py`                                      |
| Workspace mode AOR exact-once live executor                                                                                                                                 | Canonical CLI: `chaseos runtime workspace-mode live-executor`; helper module: `runtime/workspace_modes/aor_live_executor.py`                                                                    |
| Which runtime surfaces are registered and capability-classified                                                                                                             | `06_AGENTS/Adaptive-Runtime-Surface-Layer.md`                                                                                                                                                     |
| How to register an ARSL runtime surface manifest                                                                                                                            | `06_AGENTS/Runtime-Surface-Manifest-Standard.md`                                                                                                                                                  |
| Execution adapter for a specific harness                                                                                                                                    | `CLAUDE.md` / `OPENAI.md` / `LOCAL-OSS.md` / `N8N.md`                                                                                                                                             |
| How to write a new execution adapter                                                                                                                                        | `06_AGENTS/Execution-Adapter-Standard.md`                                                                                                                                                         |
| What session pattern to use                                                                                                                                                 | `05_TEMPLATES/Session-Prompt-Patterns.md`                                                                                                                                                         |
| Claude Code memory system rules                                                                                                                                             | `06_AGENTS/Claude-Memory-System.md`                                                                                                                                                               |
| Hook configuration and patterns                                                                                                                                             | `06_AGENTS/Hook-Patterns.md`                                                                                                                                                                      |
| Subagent and multi-agent patterns                                                                                                                                           | `06_AGENTS/Subagent-Patterns.md`                                                                                                                                                                  |
| Chase's identity / decisions / values                                                                                                                                       | `00_HOME/Principles.md` + `SOUL.md`                                                                                                                                                               |
| Full system overview (only when needed)                                                                                                                                     | `00_HOME/Operating-System.md`                                                                                                                                                                     |
| Knowledge in a domain                                                                                                                                                       | `02_KNOWLEDGE/[Domain]/[Domain-Name].md`                                                                                                                                                          |
| How to run a build session                                                                                                                                                  | `04_SOPS/Build-Log-SOP.md`                                                                                                                                                                        |
| How to process research                                                                                                                                                     | `04_SOPS/Research-Ingest-SOP.md`                                                                                                                                                                  |
| Ingestion pipeline architecture                                                                                                                                             | `06_AGENTS/Ingestion-Architecture.md`                                                                                                                                                             |
| 03_INPUTS/ structure and input methods                                                                                                                                      | `03_INPUTS/03_INPUTS-Folder-Guide.md`                                                                                                                                                             |
| Which note type to create from a raw input                                                                                                                                  | `06_AGENTS/Ingestion-Architecture.md` Section 3                                                                                                                                                   |
| Gate enforcement layer (how policy is enforced)                                                                                                                             | `06_AGENTS/ChaseOS-Gate.md`                                                                                                                                                                       |
| Adapter manifest schema and required fields                                                                                                                                 | `06_AGENTS/Adapter-Manifest-Standard.md`                                                                                                                                                          |
| Adapter compliance verification checklist                                                                                                                                   | `05_TEMPLATES/Adapter-Compliance-Checklist.md`                                                                                                                                                    |
| Hook scripts and settings.json                                                                                                                                              | `.claude/hooks/` · `.claude/settings.json`                                                                                                                                                        |
| Machine-readable policy files                                                                                                                                               | `runtime/policy/`                                                                                                                                                                                 |
| AOR execution engine                                                                                                                                                        | `runtime/aor/engine.py` + `runtime/aor/`                                                                                                                                                          |
| AOR workflow registry                                                                                                                                                       | `runtime/workflows/registry/`                                                                                                                                                                     |
| AOR role cards                                                                                                                                                              | `06_AGENTS/role-cards/`                                                                                                                                                                           |
| Runtime profiles, identity ledgers, and preferred routes                                                                                                                    | [[Runtime-Navigation-Map]] + [[Hermes-Runtime-Profile]] / [[OpenClaw-Runtime-Profile]] / [[Codex-Runtime-Profile]] / `06_AGENTS/Claude-Identity-Ledger.md` + `runtime/memory/adapters/` + `runtime/memory/nav/`                |
| Discord runtime control-plane bindings and Studio status                                                                                                                   | [[ChaseOS-Discord-Control-Plane]] + [[Discord-Control-Plane-Setup-SOP]] + `runtime/discord_bindings.py` + `runtime/bindings/discord_instance_bindings.example.yaml` + Studio `discord_control_plane_panel`                 |
| Native Studio Chat projects, folders, threads, runtime lanes, proposals, native target state, route state, drafts, runtime board handoff approval requests, schedule proposal packets, staged schedule proposal consumption, approved schedule-intent writes, schedule activation-readiness packets, approved schedule activation execution, schedule adapter export-readiness packets, approved local adapter export packet writes, and schedule UI action controls/readback | [[ChaseOS-Phase11-Architecture]] + [[ChaseOS-Studio-Architecture]] + [[ChaseOS-Discord-Control-Plane]] + [[Scheduling-Intent-Architecture]] + `runtime/studio/phase11_chat_workspaces_foundation.py` + `runtime/studio/phase11_chat_native_state.py` + `runtime/studio/phase11_chat_workspace_proposal_writer.py` + `runtime/studio/phase11_chat_workspace_proposal_consumption_executor.py` + `runtime/studio/phase11_chat_workspace_target_state_executor.py` + `runtime/studio/phase11_chat_route_state_and_message_drafts.py` + `runtime/studio/phase11_chat_runtime_board_handoff_proposal.py` + `runtime/studio/phase11_chat_schedule_proposal_packet.py` + `runtime/studio/phase11_chat_schedule_proposal_consumption_executor.py` + `runtime/studio/phase11_chat_approved_schedule_intent_writer.py` + `runtime/studio/phase11_chat_schedule_intent_activation_readiness.py` + `runtime/studio/phase11_chat_approved_schedule_activation_executor.py` + `runtime/studio/phase11_chat_schedule_adapter_export_readiness.py` + `runtime/studio/phase11_chat_approved_schedule_adapter_export_packet_writer.py` + `runtime/studio/phase11_chat_schedule_ui_action_controls_and_readback.py` + Studio `#panel-chat` |
| Portable runtime identity vs detachable personal binding                                                                                                                    | `06_AGENTS/Portable-Runtime-Identity-and-User-Binding.md`                                                                                                                                         |
| Runtime state resolution and future local gateway direction                                                                                                                 | `06_AGENTS/ChaseOS-Runtime-State-and-Gateway-Design.md` + `runtime/state/`                                                                                                                        |
| Runtime command contract and inspection surface                                                                                                                             | `06_AGENTS/ChaseOS-Runtime-Command-Contract.md` + `runtime/state/runtime_cli.py` + `runtime/state/CLI-README.md`                                                                                  |
| Dual-runtime machine coordination contract                                                                                                                                  | `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md` + `runtime/agent_bus/` + `runtime/hermes/` + `runtime/openclaw/coordination_bridge.md`                                                         |
| Browser autonomy governance                                                                                                                                                 | `06_AGENTS/Browser-Autonomy-Policy.md` + `06_AGENTS/Browser-Task-Patterns.md` + `runtime/browser_registry/`                                                                                       |
| Runtime bootstrap and detachable user attachment                                                                                                                            | `06_AGENTS/Portable-Runtime-Identity-and-User-Binding.md` + `runtime/bindings/`                                                                                                                   |
| Core/personal split implementation                                                                                                                                          | `06_AGENTS/Core-Personal-Split-Implementation-Plan.md` + `CORE_MANIFEST.md` + `core_templates/`                                                                                                   |
| Core export Git-safe extraction development                                                                                                                                 | `06_AGENTS/Core-Export-Git-Safe-Extraction-Development-Plan.md` + `core_export/export_manifest.yaml` + `core_export/reports/latest/runtime-handoff-core-export-git-safe-extraction-2026-04-30.md` |
| Core export priority + sync doctrine                                                                                                                                        | `06_AGENTS/Core-Export-Sync-Procedure.md`                                                                                                                                                         |
| Markdown -> standalone bridge                                                                                                                                               | `06_AGENTS/Markdown-to-Standalone-Bridge.md`                                                                                                                                                      |
| Control-panel ingress -> structured ChaseOS state rule                                                                                                                      | `06_AGENTS/Control-Plane-Ingress-and-Bus-Translation.md`                                                                                                                                          |
| Summary-context use case for typed summaries in future standalone surfaces                                                                                                  | `06_AGENTS/Standalone-Summary-Context-Layer.md`                                                                                                                                                   |
| Summary-context taxonomy + shared object-model direction                                                                                                                    | `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`                                                                                                                                          |
| Browser watchlists + evidence-flow summary-context application                                                                                                              | `06_AGENTS/Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application.md`                                                                                                                   |
| First worked standalone bridge slice (runtime nav + browser governance)                                                                                                     | `06_AGENTS/Runtime-Navigation-and-Browser-Governance-Standalone-Application.md`                                                                                                                   |
| Second worked standalone bridge slice (runtime state + bootstrap)                                                                                                           | `06_AGENTS/Runtime-State-and-Bootstrap-Standalone-Application.md`                                                                                                                                 |
| Third worked standalone bridge slice (workflow registry + role cards)                                                                                                       | `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`                                                                                                                            |
| Fourth worked standalone bridge slice (agent bus + coordination)                                                                                                            | `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md`                                                                                                                          |
| Core-vs-Personal operator views and export-safety surfaces                                                                                                                  | `06_AGENTS/Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application.md`                                                                                                            |
| Fifth worked standalone bridge slice (runtime shell + approval center + runtime browser)                                                                                    | `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`                                                                                                           |
| Canonical cross-feature Approval Center                                                                                                                                    | [[ChaseOS-Approval-Center]]                                                                                                                                                                      |
| Project cockpit and workspace browser surfaces                                                                                                                              | `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md`                                                                                                                       |
| Sixth worked standalone bridge slice (provenance explorer + chronology browser)                                                                                             | `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`                                                                                                                  |
| Consolidated operator cockpit surface                                                                                                                                       | `06_AGENTS/Consolidated-Operator-Cockpit-Standalone-Application.md`                                                                                                                               |
| Knowledge navigator and domain browser surfaces                                                                                                                             | `06_AGENTS/Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md`                                                                                                                      |
| Settings, provider-config, and scaffold surfaces                                                                                                                            | `06_AGENTS/Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application.md`                                                                                                              |
| Governed promotion and review center surfaces                                                                                                                               | `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md`                                                                                                                        |
| Cross-panel object-model consolidation                                                                                                                                      | `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md`                                                                                                                                             |
| Agent scorecards and runtime quality surfaces                                                                                                                               | `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md`                                                                                                               |
| Runtime support loops contract and proven read-only Studio panel                                                                                                            | `06_AGENTS/Runtime-Support-Loops-Contract.md`; `runtime/studio/runtime_support_loops.py`; `runtime/studio/shell/panel_registry.py`                                                               |
| Execution repair and failure recovery surfaces                                                                                                                              | `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md`                                                                                                              |
| Memory inspector and runtime-memory surfaces                                                                                                                                | `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md`                                                                                                                |
| Agent identity ledger surfaces                                                                                                                                              | `06_AGENTS/Agent-Identity-Ledger-Surfaces-Standalone-Application.md`                                                                                                                              |
| Graph-native node and edge consolidation surfaces                                                                                                                           | `06_AGENTS/Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application.md`                                                                                                           |
| Persisted graph engine and durable node-ID layer                                                                                                                            | `06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md`                                                                                                                                   |
| Memory editing and curation surfaces                                                                                                                                        | `06_AGENTS/Memory-Editing-and-Curation-Surfaces-Standalone-Application.md`                                                                                                                        |
| Provenance schema + trace_idea implementation plan                                                                                                                          | `06_AGENTS/Provenance-Schema-and-Trace-Idea-Implementation-Plan.md`                                                                                                                               |
| Runtime-instance provenance caller alignment (Claude hook lane -> OpenClaw/Hermes future alignment)                                                                         | `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`                                                                                                                             |
| Runtime-instance authority parity ruling                                                                                                                                    | `06_AGENTS/Runtime-Instance-Authority-Parity.md`                                                                                                                                                  |
| OpenClaw-first bounded promotion path contract                                                                                                                              | `06_AGENTS/OpenClaw-First-Bounded-Promotion-Path.md`                                                                                                                                              |
| Hermes-first bounded promotion path contract                                                                                                                                | `06_AGENTS/Hermes-First-Bounded-Promotion-Path.md`                                                                                                                                                |
| Runtime-instance promotion workflow + role-card pair specifications (plus shared validation surface for helper dimensions, write-scope parity, and writeback-target parity) | `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`                                                                                                              |
| OpenClaw promotion activation-readiness gate                                                                                                                                | `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`                                                                                                                                       |
| Hermes promotion activation-readiness gate                                                                                                                                  | `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`                                                                                                                                         |
| Canonical pre-activation helper inspection surface (shared module)                                                                                                          | `runtime/aor/promotion_readiness.py`                                                                                                                                                              |
| Canonical OpenClaw pre-activation helper surface                                                                                                                            | `runtime/aor/promotion_readiness.py::collect_openclaw_preactivation_failure_signals(...)` + `runtime/aor/test_openclaw_promotion_preactivation_failures.py`                                       |
| Canonical Hermes pre-activation helper surface                                                                                                                              | `runtime/aor/promotion_readiness.py::collect_hermes_preactivation_failure_signals(...)` + `runtime/aor/test_hermes_promotion_preactivation_failures.py`                                           |
| OpenClaw draft promotion workflow substrate                                                                                                                                 | `runtime/workflows/registry/openclaw_promote_note.yaml`                                                                                                                                           |
| OpenClaw draft promotion role card                                                                                                                                          | `06_AGENTS/role-cards/openclaw-promotion-review.yaml`                                                                                                                                             |
| Hermes draft promotion workflow substrate                                                                                                                                   | `runtime/workflows/registry/hermes_promote_note.yaml`                                                                                                                                             |
| Hermes draft promotion role card                                                                                                                                            | `06_AGENTS/role-cards/hermes-promotion-review.yaml`                                                                                                                                               |
| Shared promotion-review task type substrate                                                                                                                                 | `runtime/aor/task_type_table.yaml`                                                                                                                                                                |
| Promotion-record review-history lane                                                                                                                                        | `07_LOGS/Promotion-Records/`                                                                                                                                                                      |
| Trace report lane for read-only lineage outputs                                                                                                                             | `07_LOGS/Trace-Reports/`                                                                                                                                                                          |
| Provenance migration posture for historical artifacts                                                                                                                       | `runtime/schemas/provenance_migration_notes.md`                                                                                                                                                   |
| AOR decision ledger                                                                                                                                                         | `07_LOGS/Decision-Ledger/`                                                                                                                                                                        |
| Schedule intent store                                                                                                                                                       | `runtime/schedules/` (loader.py, index.yaml, sch-*.yaml seed files)                                                                                                                               |
| Schedule state change log                                                                                                                                                   | `07_LOGS/Schedule-State/schedule_state_log.jsonl`                                                                                                                                                 |
| AOR pivot log                                                                                                                                                               | `07_LOGS/Pivot-Log/`                                                                                                                                                                              |
| Feature filter gate                                                                                                                                                         | `04_SOPS/Feature-Filter-SOP.md` + `05_TEMPLATES/Feature-Filter-Template.md`                                                                                                                       |
| Graph substrate architecture                                                                                                                                                | `06_AGENTS/Graph-Substrate-Architecture.md`                                                                                                                                                       |
| Graph substrate implementation                                                                                                                                              | `runtime/graph/` (artifact, index, extractor, topology, reporter, query, builder)                                                                                                                 |
| Deferred graph-store / durable node-ID contract                                                                                                                             | `06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md` (future `runtime/graph/store/` roots remain implementation-deferred and Gate-governed)                                           |
| Graph snapshots (operator artifacts)                                                                                                                                        | `07_LOGS/Graph-Snapshots/`                                                                                                                                                                        |
| Graph analysis reports (operator artifacts)                                                                                                                                 | `07_LOGS/Graph-Reports/`                                                                                                                                                                          |
| Full-System Operator Surface (FSOS) parent                                                                                                                                  | `06_AGENTS/Full-System-Operator-Surface.md`                                                                                                                                                       |
| FSOS adapter spec                                                                                                                                                           | `06_AGENTS/Operator-Surface-Adapter-Spec.md`                                                                                                                                                      |
| Browser Operator Surface (first child)                                                                                                                                      | `06_AGENTS/Browser-Operator-Surface.md`                                                                                                                                                           |
| Operator Overlay UX Spec                                                                                                                                                    | `06_AGENTS/Operator-Overlay-UX-Spec.md`                                                                                                                                                           |
| FSOS Safety SOP                                                                                                                                                             | `04_SOPS/Full-System-Operator-Safety-SOP.md`                                                                                                                                                      |
| FSOS runtime foothold                                                                                                                                                       | `runtime/operator_surface/` (12 modules: contracts, capabilities, scopes, events, approvals, audit, session, recovery, planner, executor, adapter_registry)                                       |
| FSOS surface adapters                                                                                                                                                       | `runtime/operator_surface/adapters/` (base, browser-partial, terminal/desktop/filesystem-stubs)                                                                                                   |
| Browser subpackage                                                                                                                                                          | `runtime/operator_surface/browser/` (perception, actions, grounding, replay)                                                                                                                      |
| Source Intelligence Core (SIC) architecture                                                                                                                                 | `06_AGENTS/SIC-Architecture.md`                                                                                                                                                                   |
| SIC runtime store (workspaces, schemas, indexes)                                                                                                                            | `runtime/source_intelligence/`                                                                                                                                                                    |
| Source Package schema                                                                                                                                                       | `runtime/source_intelligence/schemas/source_package_schema.md`                                                                                                                                    |
| Workspace schema                                                                                                                                                            | `runtime/source_intelligence/schemas/workspace_schema.md`                                                                                                                                         |
| SIC provider adapter boundary                                                                                                                                               | `runtime/source_intelligence/SIC-Provider-Adapter-Standard.md`                                                                                                                                    |
| Agent activity audit log                                                                                                                                                    | `07_LOGS/Agent-Activity/Agent-Activity-Folder-Guide.md`                                                                                                                                           |
| How to run the pre-market thesis                                                                                                                                            | `04_SOPS/Morning-Thesis-Workflow.md`                                                                                                                                                              |
| What tools are available                                                                                                                                                    | `06_AGENTS/Tool-Map.md`                                                                                                                                                                           |
| What other agents exist                                                                                                                                                     | `06_AGENTS/Agent-Registry.md`                                                                                                                                                                     |

---

## File Creation Rules (for Agents)

| Type of file | Where it goes |
|--------------|---------------|
| New project | `01_PROJECTS/[ProjectName]/[ProjectName]-OS.md` |
| New knowledge note | `02_KNOWLEDGE/[Domain]/[topic].md` |
| New decision | `07_LOGS/Decision-Ledger/YYYY-MM-DD_[slug].md` (via template) |
| New pivot record | `07_LOGS/Pivot-Log/YYYY-MM-DD_[slug].md` (via template) |
| AOR audit record | `07_LOGS/Agent-Activity/YYYYMMDD-HHMMSS__[workflow]__[id].json` (written by engine) |
| New build log | `07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md` |
| New daily note | `07_LOGS/Daily/YYYY-MM-DD.md` |
| New trade journal entry | `07_LOGS/Trade-Journal/YYYY-MM-DD-[ASSET]-[DIRECTION].md` |
| New morning thesis | `07_LOGS/Morning-Thesis/YYYY-MM-DD-thesis.md` |
| New agent session log | `07_LOGS/Agent-Activity/YYYY-MM-DD-[agent]-[descriptor].md` |
| New source note | `02_KNOWLEDGE/[Domain]/[source-slug].md` |
| Raw input (unprocessed) | `03_INPUTS/[appropriate subfolder]/` |
| Workspace mode profile | `01_PROJECTS/[Project]/workspace-mode.yaml`, Project-OS frontmatter, or `.workspace-mode.yaml` for a bounded workspace root |
| Template | `05_TEMPLATES/` |
| Archived / reference | `99_ARCHIVE/` |

**Never create operational files in:** `00_HOME/` (reserved for core OS docs), `06_AGENTS/` (reserved for agent config), or the vault root.

---

*Graph links: [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Handoff-Protocol]] · [[04_SOPS/Agent-Failure-Ambiguity-SOP|Agent-Failure-Ambiguity-SOP]] · [[Agent-Security-Model]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[Execution-Adapter-Standard]] · [[Agent-Output-Conventions]] · [[Agent-Registry]] · [[Backends-Supported]] · [[CLAUDE]] · [[OPENAI]] · [[LOCAL-OSS]] · [[N8N]] · [[Session-Prompt-Patterns]] · [[Ingestion-Architecture]] · [[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]] · [[05_TEMPLATES/Source-Note-Template|Source-Note-Template]] · [[05_TEMPLATES/Synthesis-Note-Template|Synthesis-Note-Template]] · [[ChaseOS-Gate]] · [[Adapter-Manifest-Standard]] · [[05_TEMPLATES/Adapter-Compliance-Checklist|Adapter-Compliance-Checklist]] · [[Agent-Activity-Index]] · [[Morning-Thesis-Index]] · [[Trade-Journal-Index]] · [[Build-Logs-Index]] · [[Daily-Index]] · [[Trading-Weekly-Index]] · [[Knowledge-Index]] · [[Documentation-History-Index]] · [[Imported-Context-Index]] · [[Audits-Index]] · [[SOUL]] · [[Operator-Briefs-Index]] · [[SBP-Runs-Index]] · [[Graph-Reports-Index]] · [[Reporting-Index]] · [[Hermes-Runtime-Profile]] · [[OpenClaw-Runtime-Profile]] · [[ROADMAP]] · [[PROJECT_FOUNDATION]] · [[OPENCLAW]] · [[HERMES]] · [[FORKING]] · [[CORE_MANIFEST]]*

*Vault-Map.md — Updated: 2026-03-20 (Phase 6A — ingestion architecture); Updated: 2026-03-20 (Phase 6 preflight — ChaseOS-Gate.md, Adapter-Manifest-Standard.md, Adapter-Compliance-Checklist.md added; Gate routing rows added; runtime/ and .claude/ references added); Updated: 2026-03-21 (Phase 7 SIC architecture kickoff — SIC-Architecture.md, runtime/source_intelligence/ structure added to routing table); Updated: 2026-04-07 (contradiction-cleanup pass — Phase 9 Pass 1 content was already present in body; footer date corrected); Updated: 2026-05-13 (Workspace Mode Layer docs, template, runtime package, route preview, profile rollout planner, profile draft packet, profile-write approval request, guarded profile writer, first approved runtime foundation profiles, canonical CLI commands, and routing rows added); Updated: 2026-05-14 (Workspace Mode no-execution AOR dispatch gate, WML-gated AOR dry-run executor, live-execution approval request gate, and exact-once live executor added); Updated: 2026-05-14 (WML feature-family node, Studio panel, and Chat deeplink selector routing added); Updated: 2026-05-16 (Personal Context Intake and University module child-tree routing added)*

*Additional update: 2026-05-16 (Studio Chat approved schedule adapter export packet writer routing added).*


*Graph links auto-wired by vault_hygiene (2026-04-24): [[Acquisition-Surface-Map]] . [[Architecture-Workbook-2026-04-07]] . [[ChaseOS-MCP-Operator-Runbook]] . [[ChaseOS-MCP-Smoke-Test-Guide]] . [[ChaseOS-MCP-Usage]] . [[ChaseOS-Runtime-State-and-Gateway-Design]] . [[05_TEMPLATES/Decision-Ledger-Entry-Template|Decision-Ledger-Entry-Template]] . [[05_TEMPLATES/Experiment-Template|Experiment-Template]] . [[Feature-Filter-SOP]] . [[05_TEMPLATES/Feature-Filter-Template|Feature-Filter-Template]] . [[Hermes-Operations-Runbook]] . [[Layer-Catalog]] . [[Normalization-Provenance-Contract]] . [[OpenClaw-Activation-Runbook]] . [[OpenClaw-Discord-Activation-Preflight]] . [[05_TEMPLATES/Operator-Run-Audit-Template|Operator-Run-Audit-Template]] . [[Pivot-Log-Entry-Template]] . [[05_TEMPLATES/Project-OS-Template|Project-OS-Template]] . [[Runtime-Acquisition-Responsibility-Matrix]] . [[StrikeZone-Acquisition-Normalization-Pilot]]*

--- 
## Vault Folder Guides
[[03_INPUTS-Folder-Guide]] 
 [[QUARANTINE-Folder-Guide]] 
 [[Agent-Activity-Folder-Guide]] 
 [[Core-Templates-Folder-Guide]] 
 [[HOME-Templates-Guide]] 
 [[PROJECTS-Templates-Guide]] 
 [[KNOWLEDGE-Templates-Guide]] 
 [[AGENTS-Templates-Guide]] 
 [[LOGS-Templates-Guide]] 
 [[Runtime-Templates-Guide]] 
 [[Runtime-Layer-Guide]] 
 [[runtime/agent_bus/Agent-Bus-Folder-Guide|Agent-Bus-Folder-Guide]] 
 [[Runtime-Bindings-Folder-Guide]] 
 [[Browser-Watchlists-Folder-Guide]] 
 [[Runtime-Navigation-Folder-Guide]] 
 [[Operator-Surface-Folder-Guide]] 
 [[Source-Intelligence-Folder-Guide]]



*Graph links auto-wired by vault_hygiene (2026-04-24): [[ChaseOS-Runtime-Command-Contract]] . [[Control-Plane-Ingress-and-Bus-Translation]] . [[Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application]] . [[Workflow-Registry-and-Role-Cards-Summary-Context-Application]]*


*Graph links auto-wired by vault_hygiene (2026-04-25): [[Acquisition-and-Source-Pack-Summary-Context-Application]] . [[Build-Logs-and-Operator-Briefs-Summary-Context-Application]] . [[ChaseOS-Top-Level-Command-Promotion]] . [[ChaseOS-Vault-Maintenance]] . [[OpenClaw-Promotion-Activation-Readiness-Gate]] . [[Runtime-Navigation-Overlay-Summary-Context-Application]]*


*Graph links auto-wired by vault_hygiene (2026-04-25): [[CHASEOS-COMMAND-README]] . [[ChaseOS-CLI-Surfaces]] . [[Hermes-Promotion-Activation-Readiness-Gate]]*


*Graph links auto-wired by vault_hygiene (2026-04-26): [[ChaseOS-Provider-and-Integration-Setup-CLI-Plan]] . [[Phase9-Implementation-Closure-Plan]]*


*Graph links auto-wired by vault_hygiene (2026-04-26): [[ChaseOS-Setup-Init-Scaffold-Spec]] . [[Immediate-Next-Steps-Execution-Plan]]*


*Graph links auto-wired by vault_hygiene (2026-04-27): [[Agent-Bus-Backend-Architecture]] . [[ChaseOS-CLI-Command-Reference]] . [[ChaseOS-CLI-Consolidation-Refactor]] . [[ChaseOS-CLI-JSON-Output-Contract]] . [[ChaseOS-Deny-Default-Runtime-Policy]] . [[Discord-Channel-Aware-Coordination-Arbitration-Implementation-Plan]] . [[Scorecard-Cron-Integration]]*


*Graph links auto-wired by vault_hygiene (2026-05-01): [[Browser-Domain-Skill-Template]] . [[Browser-Run-Log-Template]] . [[Browser-Skill-Candidate-Template]] . [[Browser-Skill-Template]] . [[Pulse-Card-Template]] . [[Site-Memory-Ledger]] . [[SiteOps-Approval-Policy]] . [[SiteOps-Approval-Request-Template]] . [[SiteOps-Browser-Session-Boundaries]] . [[SiteOps-Browser-Session-SOP]] . [[SiteOps-Credential-Boundaries]] . [[SiteOps-Credential-Handling-SOP]] . [[SiteOps-Product-Surface-Roadmap]] . [[SiteOps-Provider-Budgeting]] . [[SiteOps-Run-Audit-Template]] . [[SiteOps-Skill-Template]] . [[SiteOps-Tenancy-And-Isolation]] . [[SiteOps-Tenant-Admin-SOP]] . [[SiteOps-Workflow-Approval-SOP]] . [[SiteOps-Workflow-Template]] . [[draft-browser-runtime-20260430-015628-example-com]] . [[draft-browser-runtime-20260430-015655-example-com]] . [[draft-browser-runtime-20260430-022443-example-com]] . [[draft-browser-runtime-20260430-022607-example-com]] . [[draft-vincisos-inapp-browser-20260430]] . [[replay-vincisos-draft-skill-20260501]]*


*Graph links auto-wired by vault_hygiene (2026-05-02): [[ChaseOS-Cross-Runtime-Handoff]] . [[ChaseOS-Pulse-Approval-Center-Readiness]] . [[Other-Runtime-Continuation-Handoff]] . [[draft-vincisos-product-ui-browser-proof-20260502]] . [[vincisos-full-ui-product-target-20260502]]*


*Graph links auto-wired by vault_hygiene (2026-05-04): [[05_TEMPLATES/Agent-Runtime-Profile-Template|Agent-Runtime-Profile-Template]] . [[ChaseOS-Pulse-Personal-Map-Apply-Transaction-Proof]] . [[05_TEMPLATES/Personal-Map-Node-Template|Personal-Map-Node-Template]] . [[SiteOps-Browser-Skill-Shadow-Execution-Proof-Consumption-Guard]] . [[SiteOps-Browser-Skill-Shadow-Execution-Proof-Live-Consumption-Write]] . [[SiteOps-Browser-Skill-Shadow-Replay-Evidence-Review-Closeout]] . [[SiteOps-Browser-Skill-Shadow-Replay-Runner-Write-Pass]] . [[SiteOps-Candidate-Activation-Approval-And-Consumption-Live-Evidence]] . [[SiteOps-Candidate-Activation-Gate-Live-Readiness]] . [[SiteOps-Candidate-Source-Approval-Rebind-Live-Readiness]] . [[SiteOps-Candidate-Trusted-Inactive-Artifact-Live-Write-Verification]] . [[draft-safe-local-workflow-replay-execution-proof-20260503]]*


*Graph links auto-wired by vault_hygiene (2026-05-04): [[Browser-Runs-Index]] . [[Browser-Skill-Candidates-Index]] . [[Changes-Index]] . [[-Upcoming-Features-Index]] . [[Index]] . [[Promotion-Records-Index]] . [[Pulse-Decks-Index]] . [[Studio-ARSL-Route-Review-Index]] . [[Studio-Graph-Views-Index]] . [[Trace-Reports-Index]] . [[Web-Clips]]*


*Graph links auto-wired by vault_hygiene (2026-05-05): [[05_TEMPLATES/Generated-Idea-Template|Generated-Idea-Template]]*


*Graph links auto-wired by vault_hygiene (2026-05-05): [[06_AGENTS/Adapter-Manifest-Standard|Adapter-Manifest-Standard.core]] . [[05_TEMPLATES/Agent-Audit-Log-Template|Agent-Audit-Log-Template]] . [[05_TEMPLATES/Agent-Audit-Log-Template|Agent-Audit-Log-Template.core]] . [[runtime/agent_bus/Agent-Bus-Folder-Guide|Agent-Bus-Folder-Guide.core]] . [[Agent-Bus-Task-Packet.example]] . [[Agent-Bus-Task-Packet.example]] . [[06_AGENTS/Agent-Output-Conventions|Agent-Output-Conventions.core]] . [[06_AGENTS/Agent-Security-Model|Agent-Security-Model.core]] . [[Build-Logs-Index.example]] . [[Build-Logs-Index.example]] . [[Build-Logs-Index.example]] . [[CORE_MANIFEST|CORE_MANIFEST.core]] . [[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate.core]] . [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP.core]] . [[05_TEMPLATES/Daily-Note-Template|Daily-Note-Template]] . [[05_TEMPLATES/Daily-Note-Template|Daily-Note-Template.core]] . [[Dashboard.example]] . [[Dashboard.example]] . [[05_TEMPLATES/Decision-Log-Template|Decision-Log-Template]] . [[Example-Project-OS]] . [[Example-Project-OS]] . [[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard.core]] . [[05_TEMPLATES/Experiment-Template|Experiment-Template.core]] . [[05_TEMPLATES/Feature-Filter-Template|Feature-Filter-Template.core]] . [[05_TEMPLATES/Generated-Idea-Template|Generated-Idea-Template.core]] . [[IMPLEMENTATION-NOTES]] . [[IMPLEMENTATION-NOTES]] . [[06_AGENTS/Ingestion-Architecture|Ingestion-Architecture.core]] . [[Knowledge-Index.example]] . [[Knowledge-Index.example]] . [[Knowledge-Index.example]] . [[06_AGENTS/Knowledge-Taxonomy|Knowledge-Taxonomy.core]] . [[New-Runtime-Registration-Checklist.core]] . [[Now.example]] . [[Now.example]] . [[Operating-System.example]] . [[Operating-System.example]] . [[05_TEMPLATES/Personal-Map-Node-Template|Personal-Map-Node-Template.core]] . [[Principles.example]] . [[Principles.example]] . [[README.core]] . [[Runtime-InterAgent-Coordination-Bus]] . [[06_AGENTS/Runtime-InterAgent-Coordination-Bus|Runtime-InterAgent-Coordination-Bus.core]] . [[Runtime-Profile.example]] . [[Runtime-Profile.example]] . [[SIC-Architecture]] . [[06_AGENTS/SIC-Architecture|SIC-Architecture.core]] . [[Source-Note.example]] . [[Source-Note.example]] . [[Synthesis-Note.example]] . [[Synthesis-Note.example]] . [[codex-stdout]] . [[codex-stdout]] . [[codex-stdout]] . [[codex-stdout]] . [[grok_digest.template]] . [[perplexity_digest.template]] . [[youtube_summary.template]]*


*Graph links auto-wired by vault_hygiene (2026-05-05): [[03_INPUTS/Browser-Skill-Candidates/vincisos-local/vincisos-full-ui-product-target-20260502|vincisos-full-ui-product-target-20260502]] . [[05_TEMPLATES/Agent-Runtime-Profile-Template|Agent-Runtime-Profile-Template]] . [[05_TEMPLATES/Decision-Ledger-Entry-Template|Decision-Ledger-Entry-Template]] . [[05_TEMPLATES/Feature-Filter-Template|Feature-Filter-Template]] . [[05_TEMPLATES/Generated-Idea-Template|Generated-Idea-Template]] . [[05_TEMPLATES/Operator-Run-Audit-Template|Operator-Run-Audit-Template]] . [[05_TEMPLATES/Personal-Map-Node-Template|Personal-Map-Node-Template]] . [[05_TEMPLATES/Source-Note-Template|Source-Note-Template]] . [[05_TEMPLATES/Synthesis-Note-Template|Synthesis-Note-Template]] . [[06_AGENTS/Browser-Skills/_drafts/vincisos-full-ui-product-target-20260502|vincisos-full-ui-product-target-20260502]]*


*Graph links auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/ChaseOS-Studio-Launch-Instructions|ChaseOS-Studio-Launch-Instructions]]*


*Graph links auto-wired by vault_hygiene (2026-05-11): [[07_LOGS/Workflow-Proofs/Workflow-Proofs-Index|Workflow-Proofs-Index]] . [[05_TEMPLATES/Agent-Scorecard-Template|Agent-Scorecard-Template]] . [[05_TEMPLATES/Customer-Offer-Canvas|Customer-Offer-Canvas]] . [[05_TEMPLATES/Domain-Playbook-Template|Domain-Playbook-Template]] . [[05_TEMPLATES/Live-Revenue-Evidence-Template|Live-Revenue-Evidence-Template]] . [[05_TEMPLATES/Proof-of-Run-Template|Proof-of-Run-Template]] . [[05_TEMPLATES/Real-Client-Scope-Approval-Template|Real-Client-Scope-Approval-Template]] . [[05_TEMPLATES/Real-Client-Scope-Evidence-Template|Real-Client-Scope-Evidence-Template]] . [[05_TEMPLATES/Runtime-Adapter-Checklist|Runtime-Adapter-Checklist]] . [[05_TEMPLATES/Workflow-Exchange-Listing-Template|Workflow-Exchange-Listing-Template]] . [[05_TEMPLATES/Workflow-Monetization-Canvas|Workflow-Monetization-Canvas]] . [[05_TEMPLATES/Workflow-Pack-Template|Workflow-Pack-Template]] . [[05_TEMPLATES/Workflow-Recommendation-Card|Workflow-Recommendation-Card]] . [[06_AGENTS/Agent-Scorecard-Standard|Agent-Scorecard-Standard]] . [[06_AGENTS/ChaseOS-Hardening-Passover|ChaseOS-Hardening-Passover]] . [[06_AGENTS/Customer-Proof-Artifact-Standard|Customer-Proof-Artifact-Standard]] . [[06_AGENTS/Domain-Playbook-Standard|Domain-Playbook-Standard]] . [[06_AGENTS/Phase9-Hardening-Passover|Phase9-Hardening-Passover]] . [[06_AGENTS/Runtime-Adapter-Use-Case-Matrix|Runtime-Adapter-Use-Case-Matrix]] . [[06_AGENTS/Workflow-Exchange-Readiness-Standard|Workflow-Exchange-Readiness-Standard]] . [[docs/goal|goal]]*


*Graph links auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Operator-Handover-2026-05-12|Operator-Handover-2026-05-12]] . [[06_AGENTS/Operator-Setup-Checklist|Operator-Setup-Checklist]] . [[06_AGENTS/Workflow-Pack-Standard|Workflow-Pack-Standard]] . [[06_AGENTS/Workflow-Recommendation-Engine|Workflow-Recommendation-Engine]] . [[07_LOGS/Workflow-Proofs/2026-05-10_agent_runtime_governance_audit_real-chaseos-client-report-scorecard|2026-05-10_agent_runtime_governance_audit_real-chaseos-client-report-scorecard]] . 


*Graph links auto-wired by vault_hygiene (2026-05-15): [[05_TEMPLATES/Domain-Goal-Profile-Template|Domain-Goal-Profile-Template]] . [[05_TEMPLATES/Experiment-Hypothesis-Template|Experiment-Hypothesis-Template]] . [[05_TEMPLATES/Mission-Manifest-Template|Mission-Manifest-Template]] . [[05_TEMPLATES/Mission-Recommendation-Card|Mission-Recommendation-Card]] . [[05_TEMPLATES/Mission-Review-Template|Mission-Review-Template]] . [[05_TEMPLATES/Mission-State-Ledger-Template|Mission-State-Ledger-Template]] . [[05_TEMPLATES/Site-Profile-Template|Site-Profile-Template]] . [[05_TEMPLATES/Sub-Agent-Plan-Template|Sub-Agent-Plan-Template]] . [[05_TEMPLATES/Workflow-Evolution-Proposal-Template|Workflow-Evolution-Proposal-Template]] . [[06_AGENTS/Adaptive-Workflow-Evolution|Adaptive-Workflow-Evolution]] . [[07_LOGS/Mission-Reviews/2026-05-13_mission-chase-ai-runtime-governance-kit_2026-05-13-ventureops-aor-mission-dry-review|2026-05-13_mission-chase-ai-runtime-governance-kit_2026-05-13-ventureops-aor-mission-dry-review]] . [[07_LOGS/Mission-Reviews/2026-05-13_mission-chase-ai-runtime-governance-kit_dry-run-review|2026-05-13_mission-chase-ai-runtime-governance-kit_dry-run-review]] . [[07_LOGS/Mission-Reviews/2026-05-14_mission-chase-ai-runtime-governance-kit_2026-05-14-ventureops-mission-runtime-claim-result-aor-dry-review|2026-05-14_mission-chase-ai-runtime-governance-kit_2026-05-14-ventureops-mission-runtime-claim-result-aor-dry-review]] . [[07_LOGS/Runtime-Audits/2026-05-13-operator-provide-real-client-scope-inputs|2026-05-13-operator-provide-real-client-scope-inputs]] . [[07_LOGS/Runtime-Audits/2026-05-13-operator-real-client-scope-handover|2026-05-13-operator-real-client-scope-handover]] . [[07_LOGS/Runtime-Audits/2026-05-13-operator-submit-real-client-scope-inputs|2026-05-13-operator-submit-real-client-scope-inputs]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-actual-tested-workflow-explainer|2026-05-13-ventureops-actual-tested-workflow-explainer]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-ai-runtime-security-audit|2026-05-13-ventureops-ai-runtime-security-audit]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-internal-workflow-proof-closeout|2026-05-13-ventureops-internal-workflow-proof-closeout]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-live-client-scope-proof-blocked|2026-05-13-ventureops-live-client-scope-proof-blocked]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-live-client-workflow-proof-execution|2026-05-13-ventureops-live-client-workflow-proof-execution]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-live-revenue-evidence-packet-handoff|2026-05-13-ventureops-live-revenue-evidence-packet-handoff]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-operator-approved-internal-scope-packets|2026-05-13-ventureops-operator-approved-internal-scope-packets]] . [[07_LOGS/Runtime-Audits/2026-05-13-ventureops-real-client-input-packet|2026-05-13-ventureops-real-client-input-packet]] . [[07_LOGS/Runtime-Audits/2026-05-14_mission_chase_ai_runtime_governance_kit_2026-05-14-ventureops-mission-runtime-claim-result-aor-dry-review|2026-05-14_mission_chase_ai_runtime_governance_kit_2026-05-14-ventureops-mission-runtime-claim-result-aor-dry-review]] . [[07_LOGS/Workflow-Evolution-Proposals/2026-05-13_mission-chase-ai-runtime-governance-kit_evo-001-required-approval-evidence|2026-05-13_mission-chase-ai-runtime-governance-kit_evo-001-required-approval-evidence]] . [[07_LOGS/Workflow-Proofs/2026-05-10_agent_runtime_governance_audit_real-chaseos-client-report-scorecard_client-report|2026-05-10_agent_runtime_governance_audit_real-chaseos-client-report-scorecard_client-report]] . [[07_LOGS/Workflow-Proofs/2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_client-scope|2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_client-scope]] . [[07_LOGS/Workflow-Proofs/2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_delivery-approval-contract|2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_delivery-approval-contract]] . [[07_LOGS/Workflow-Proofs/2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_delivery-packet-preview|2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_delivery-packet-preview]] . [[07_LOGS/Workflow-Proofs/2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_offer-packet|2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_offer-packet]] . [[07_LOGS/Workflow-Proofs/2026-05-13_mission-chase-ai-runtime-governance-kit_dry-run-proof|2026-05-13_mission-chase-ai-runtime-governance-kit_dry-run-proof]] . [[07_LOGS/Workflow-Proofs/2026-05-13_ventureops-real-client-input-packet|2026-05-13_ventureops-real-client-input-packet]] . [[07_LOGS/Workflow-Proofs/2026-05-13_ventureops_ai_runtime_security_audit_session-closeout-v2|2026-05-13_ventureops_ai_runtime_security_audit_session-closeout-v2]] . [[07_LOGS/Workflow-Proofs/2026-05-13_ventureops_ai_runtime_security_audit_session-closeout-v2_client-report|2026-05-13_ventureops_ai_runtime_security_audit_session-closeout-v2_client-report]] . [[07_LOGS/Workflow-Proofs/2026-05-13_ventureops_ai_runtime_security_audit_session-closeout|2026-05-13_ventureops_ai_runtime_security_audit_session-closeout]] . [[07_LOGS/Workflow-Proofs/2026-05-13_ventureops_ai_runtime_security_audit_session-closeout_client-report|2026-05-13_ventureops_ai_runtime_security_audit_session-closeout_client-report]] . [[07_LOGS/Workflow-Proofs/2026-05-14_ventureops-mega-pass-after-evidence-prep-closeout|2026-05-14_ventureops-mega-pass-after-evidence-prep-closeout]] . [[07_LOGS/Workflow-Proofs/2026-05-15_ventureops-governed-completion-pass-closeout|2026-05-15_ventureops-governed-completion-pass-closeout]] . [[07_LOGS/Workflow-Proofs/2026-05-15_ventureops-real-operator-evidence-ingestion-packet|2026-05-15_ventureops-real-operator-evidence-ingestion-packet]] . [[docs/VentureOps_goal|VentureOps_goal]] . [[docs/slash-go|slash-go]]*
