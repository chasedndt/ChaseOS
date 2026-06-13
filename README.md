# ChaseOS

**Human intent. Agentic execution. Private control.**

ChaseOS is the local-first AI operating system for builders running real projects with agents. It turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

The core brand idea is simple: human intent and permissioned agent runtimes operating inside a private, evolving control plane.

## Website

ChaseOS public launch domain:

https://chaseos.ai

The public site will host ChaseOS Studio Early Access, Chaser Forge marketplace preview, standards and pack manifests, documentation, open-core/commercial philosophy, waitlist, privacy/security notes, support, and creator submission paths.

Status: ChaseOS Studio Early Access / Developer Preview. `chaseos.systems` is superseded as the primary launch domain and may remain a future secondary redirect, standards alias, ecosystem alias, or defensive domain if purchased later.

---

## What is ChaseOS?

ChaseOS is a local-first, privacy-first command layer for human-agent work. It connects source intelligence, structured memory, knowledge graph relationships, SOPs, workflow automation, runtime profiles, permission matrices, approvals, and bounded execution into one governed system.

The current implementation uses an Obsidian-first markdown vault plus Python runtime packages. That is the substrate, not the identity. The product identity is ChaseOS: a private operating layer where human intent, agent runtimes, memory, workflows, and execution history stay under user control.

## Why ChaseOS exists

Modern AI work is fragmented. People think in one AI chat, store context in another notes system, run code in terminals, manage automations elsewhere, keep files in scattered folders, and hand off tasks to agents that do not share a durable operating memory.

That creates repeated re-briefing, lost project context, unclear agent authority, disconnected workflows, and automation that cannot be trusted without visible provenance and permission boundaries.

ChaseOS exists to make that operating context durable, inspectable, and executable without giving up private control.

## The problem: agentic chaos

ChaseOS is built against agentic chaos: disconnected tools, forgetful chats, shallow AI wrappers, ungoverned automation, and agent systems that execute without enough user doctrine, memory, or permission structure.

The problem is not that AI tools cannot answer questions. The problem is that most AI tools do not operate inside one trusted system of record.

## The solution: a private command layer

ChaseOS gives the operator one private command layer where:

- files, notes, sources, projects, workflows, SOPs, and outputs have durable homes;
- knowledge graph memory links sources, decisions, work products, approvals, and runtime activity;
- AI agents act as bounded runtimes, not uncontrolled authorities;
- automations and workflows run through visible gates, logs, and permission boundaries;
- generated ideas stay separate from verified facts and canonical project state.

The human stays in control. Agents gain useful context. The system compounds over time.

## Core capabilities

- Secure memory and writeback: local-first markdown, runtime artifacts, logs, provenance, and canonical state separation.
- Knowledge graph memory: relationships across sources, projects, workflows, decisions, approvals, and outputs.
- Source intelligence: governed ingestion, source packages, workspaces, retrieval, and structured outputs.
- Permissioned agent runtimes: explicit trust tiers, permission matrices, runtime profiles, Agent Bus boundaries, and approval-gated execution.
- Automation, SOP, and workflow execution: bounded AOR workflows, schedule intent, workflow packs, mission modes, and audit trails where implemented.
- Human-agent collaboration: agents assist, propose, route, execute within approved scopes, and write back evidence without replacing operator authority.
- Privacy-first positioning: user data, source archives, project memory, and generated outputs stay in the user's system unless a specific connector/runtime path is approved.

## Who ChaseOS is for

The first audience is AI-native operators: technical founders, AI engineers, developers, high-agency creators, entrepreneurs, researchers, and builders who already feel the cost of scattered chats, repos, notes, files, workflows, and agents.

Longer term, ChaseOS can support students, creators, knowledge workers, operators, small businesses, and everyday users who want a private AI operating system for goals, study, work, planning, and execution.

## How ChaseOS is different

ChaseOS is not a generic AI chat, a second-brain template, a productivity app, or an automation wrapper.

It is different because it combines:

- private local-first memory;
- knowledge graph relationships;
- explicit permission and trust boundaries;
- governed source ingestion;
- runtime and agent profiles;
- approval-gated execution;
- SOP/workflow automation;
- durable logs, proof artifacts, and documentation history.

Most AI tools answer in the moment. ChaseOS remembers the system.

## Brand and design foundation

The current brand foundation lives in [docs/brand/](docs/brand/).

- Canonical name: `ChaseOS`
- Primary tagline direction: `Human intent. Agentic execution. Private control.`
- Visual essence: `Human core. Agent network. Private boundary. Controlled execution.`
- Design status: `DOCS-ONLY / BRAND FOUNDATION ADOPTED / LOGO AND UI REDESIGN NOT COMPLETE`

Use [docs/brand/Brand_Copy_Bank.md](docs/brand/Brand_Copy_Bank.md) for reusable definitions, taglines, and copy. Use [docs/brand/Design_Tokens_Preliminary.md](docs/brand/Design_Tokens_Preliminary.md) for preliminary visual tokens before any future UI redesign.

## Project status

ChaseOS is an active open-core personal operating system / agent control-plane framework. This repository is a public Core export: it includes the framework docs, governance contracts, runtime surfaces, templates, and Studio-facing architecture needed to understand and extend the system without publishing private operator data.

---

## Technical architecture detail

ChaseOS is a privacy-first agentic operating system and local-first control plane. It is the environment in which a person and permissioned agent runtimes work together: ingesting sources, reasoning over structured workspaces, executing bounded tasks, writing back to canonical state, and generating ideas that stay visibly separate from verified truth.

It is not a note-taking setup. It is not a productivity method. It is not a second brain.

It is an operating system: a set of conventions, routing rules, memory structures, operating files, agent contracts, and enforcement hooks that let a person — and the AI tools they work with — operate coherently across a large, complex, multi-domain life.

**ChaseOS ages with the user.** Most AI tools are useful in the moment. ChaseOS is designed to get more useful over time — because the value lives in the system, not in any single session. As the user keeps learning, building, operating, and writing back into ChaseOS, the system compounds:

- The source archive gets deeper — more material for retrieval-backed reasoning
- The doctrine gets sharper — better decisions with less re-briefing
- The project state stays continuous — agents re-orient in seconds, not minutes
- The operator memory improves — runtimes learn from their own behavioral history
- Cross-domain associations become possible — the graph connects ideas across domains
- Recurring workflow patterns become reusable — what you did manually becomes something the system can support or automate
- Failure-handling patterns accumulate — the system learns from its own mistakes

This is accumulated operating context, not chat memory. The architecture is designed so that useful context is never lost between sessions, never conflated across content types, and never allowed to override governance rules.

The Source Intelligence Core is now complete. ChaseOS already owns local source packages, workspaces, retrieval, and structured outputs rather than delegating that architecture to external platforms. The current major layer is Phase 9/10 hardening and productization: runtime buses, schedules, MCP, scorecards, acquisition/normalization, Studio shell/panel surfaces, parser-backed graph input, and the security posture required before broader governed Studio write/action flows.

**Local-first principle:** User sources and knowledge remain in the user's system. Source packages, indexes, workspace objects, and generated outputs are stored locally. The model provider (Claude, OpenAI, local runtime) is pluggable — it supplies generation and embeddings. It does not own the workspace architecture or the knowledge model. ChaseOS does.

ChaseOS separates four distinct categories that most systems conflate:

- **Raw inputs** — unverified external content held in quarantine until processed
- **Processed knowledge** — source-derived notes and multi-source syntheses with explicit trust labeling
- **Generated ideas** — AI-generated or human+AI hypotheses, theses, and proposals kept visibly separate from verified facts
- **Canonical state** — active project truth, sprint priorities, and operating status

ChaseOS provides:

- **Structured memory** — canonical knowledge, project state, and operating principles stored in a navigable, machine-readable format
- **Knowledge taxonomy** — explicit classification of every knowledge note by origin, trust tier, and verification status
- **Project governance** — each active project has an operating file defining its mission, status, goals, and open loops
- **Context routing** — agents are directed to read specific files rather than loading everything; narrow context, not full context
- **Governed ingestion** — a five-stage pipeline (Quarantine → Triage → Sanitize → Route → Promote) for processing external content
- **Operating discipline** — SOPs, build logs, decision logs, and review cadences that create writeback accountability
- **Agent behavior contracts** — explicit rules governing what AI tools can and cannot do inside the system
- **Mechanical enforcement** — hook scripts, adapter manifests, and runtime policy files enforce the agent contracts at the tool-call level (not just as instructions)
- **Domain operating layers** — 18 named domains, each with its own knowledge base and project structure

---

## What ChaseOS Is Not

- Not an Obsidian plugin or Obsidian-specific product
- Not a generic PKM template
- Not a journaling framework
- Not a productivity methodology
- Not a finished product — it is a living, evolving framework
- Not a replacement for domain expertise — it routes and structures it

---

## Why Obsidian Right Now

Obsidian is currently the default memory backend and visualization layer for ChaseOS.

It was chosen because:
- Files are plain markdown — portable, not locked in
- Vault structure maps cleanly to ChaseOS folder conventions
- Graph view and backlinks support navigation between related context
- Local-first architecture fits the sovereignty requirements of the system
- The plugin ecosystem allows rapid customization without building custom tooling yet

**Obsidian is not the product identity.** ChaseOS is the framework. Obsidian is one implementation of it.

The product identity is **ChaseOS Studio** - a standalone desktop, graph-first operating surface for ChaseOS (Phase 10). The native shell, read-only panel lane, parser-backed graph input, typed graph/trust overlay model, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposal flow, and approval-gated Runtime Cockpit action-readiness request surface are built; general markdown / Obsidian-compatible onboarding previews are built through bootstrap preview; proof-temp workspace upgrade approval/execution is built; persisted graph storage, real target-folder/file upgrade execution, and runtime action execution remain future work. The framework conventions are designed to survive the transition away from Obsidian as the primary interface.

---

## System Layers

```
┌─────────────────────────────────────────────────────────┐
│  ChaseOS Framework                                       │
│  ─────────────────────────────────────────────────────  │
│  Memory Layer      → structured notes, project OS files  │
│  Governance Layer  → SOPs, templates, decision logs      │
│  Context Layer     → Vault Map, routing rules, registry  │
│  Agent Layer       → contracts, permissions, trust levels│
│  Gate Layer        → adapter manifests, hook enforcement │
│  Identity Layer    → SOUL, principles, operating doctrine│
│  Log Layer         → build logs, daily, weekly reviews   │
│  Archive Layer     → history, snapshots, handovers       │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Feature Families (subsystems + capability layers)       │
│  ─────────────────────────────────────────────────────  │
│  Source Intelligence Core    (Phase 7 — COMPLETE)         │
│    Source Package Layer  → normalized source objects     │
│    Workspace Layer       → grouped source sets           │
│    Retrieval Layer       → evidence-grounded reasoning   │
│    Output Layer          → summary, FAQ, synthesis draft │
│    Provider Adapter      → pluggable model backend       │
│                                                          │
│  Autonomous Operator Runtime (Phase 9 — partial)         │
│    Workflow Registry → manifest-based execution          │
│    Bounded Autonomy  → explicit permission ceilings      │
│    Multi-Repo Policy → declared directory scope          │
│    Audit Trails      → every action logged               │
│    Runtime Navigation Map → evolving per-runtime         │
│      navigational overlay (routes, zones, escalations)   │
│                                                          │
│  Scheduled Briefing Pipelines (Phase 9 — planned)        │
│    Trigger Schedule  → cron or event-based               │
│    Input Adapters    → SIC workspaces, vault, APIs       │
│    Delivery Adapters → Discord, email, dashboard         │
│    Guardrail Profile → fail-closed, audit-required       │
│                                                          │
│  Operator Surface + Runtime Interaction (Phase 9/10)     │
│    Phase 9: Runtime Interaction Contract → event bus     │
│             Action Dispatch Visibility → live view       │
│             Runtime Session Model → resumable sessions   │
│             Approval-Linked Execution → gated confirms   │
│    Phase 10: Operator Shell → browser shell + approvals  │
│              Voice I/O → STT/TTS provider-neutral        │
│              Companion Surface → mobile/tablet access    │
│                                                          │
│  ChaseOS Studio (Phase 10 - active)                      │
│    Native shell + read-only panels through 10W           │
│    Parser-backed graph input complete in 10X             │
│    Typed graph/trust overlays complete in 10Y            │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Current Implementation: Obsidian Vault                  │
│  (default memory backend + visualization interface)      │
└─────────────────────────────────────────────────────────┘
```

---

## Major Domains

ChaseOS currently operates across 18 named domains (A–R):

| ID | Domain | Description |
|----|--------|-------------|
| A | ChaseOS / System Infrastructure | The operating system itself |
| B | Market Operations | Trading, market research, and risk-review workflows |
| C | Community / Signal Products | Audience, membership, and distribution workflows |
| D | Indicator R&D / Technical Tooling | Custom indicators, strategy research, and tool prototypes |
| E | Autonomous Trading Systems | Agent-assisted trading research and governed execution design |
| F | Macro Intelligence | Cross-market macro intelligence and dashboard workflows |
| G | AI / Agent Engineering | Agent architecture, tooling, systems |
| H | Full-Stack / Software Engineering | Web2, Web3, and product engineering workflows |
| I | Security Research | Offensive security, blockchain security, and vulnerability workflows |
| J | Learning / Credential Ops | Structured study, credential, and education workflows |
| K | Career / Client Ops | Internship, freelance, and client-service positioning |
| L | Content Engine | Research-to-content and distribution workflows |
| M | Businesses / Ventures | Active, paused, and legacy venture operations |
| N | Hardware / Robotics / Future Systems | GPU, embedded, robotics, and future system tracks |
| O | Doctrine / Philosophy / Identity | Operating principles and identity templates |
| P | Physical Discipline | Training, health, and performance standards |
| Q | Network / Relationship Ops | Relationship and professional-network workflows |
| R | Language / Mobility Ops | Language learning and international optionality workflows |

---

## Core vs Personal

ChaseOS now treats Core/Personal as an active structural separation lane, not only a concept.

### ChaseOS Core
The public, forkable, reusable framework.

Contains: folder conventions, note type definitions, routing rules, operating principles, agent behavior contracts, templates, boilerplate structure, and forking guidance.

This layer is meant to be standardized, version-controlled, and usable by anyone willing to populate it with their own context. The current Core extraction lane is controlled by `CORE_MANIFEST.md`, `core_export/export_manifest.yaml`, `core_export/core_candidate_inventory.yaml`, scanner/sanitizer policy, curated templates under `core_export/templates/`, and rendered review artifacts under `core_export/reports/latest/`.

### ChaseOS Personal
The private, populated instance.

Contains: real projects, real priorities, personal doctrine, private operating history, personal logs, individualized knowledge, and private workflows.

This layer is specific to each operator or organization and is not intended to be shared publicly as-is. It follows the Core conventions while being populated with private operational context.

The active development workspace is the source workspace for validating ChaseOS Core/Personal separation. Guarded Core export targets are inspection/export-candidate outputs only; they are not public, not authoritative, and not Git repositories unless a later explicit Git-init gate approves that step. The latest Core export tracker records 57 manifest candidates/previews, 0 scanner blockers, a guarded local export update, a recorded verify-export pass, and Git/commit/remote/push/publication still unapproved; the latest revalidation found the export target and manual review artifact missing, so current verify-export is blocked until restored through the guarded export lane.

See [FORKING.md](FORKING.md) for how to create your own instance.

---

## Where This Project Is

ChaseOS is currently in **Phase 9 — Operator Runtime (AOR + SBP) — active implementation**. Phases 1–8 are complete. Phase 7 (Source Intelligence Core) and Phase 8 (Connector / Capture Automation) are fully operational.

Phase 6 built the governed ingestion architecture, ChaseOS Gate (ACTIVE VERIFIED), knowledge taxonomy (six classes), and operational SOPs. Phase 7 delivered the full SIC stack. Phase 8 delivered the capture and connector automation layer. A Phase 9 planning pass was completed 2026-03-31, producing `06_AGENTS/Phase9-Adopted-Feature-Specification.md` — full specification for 17 adopted Phase 9 features across governance infrastructure, AOR workflows, and data governance layers.

**Phase 7 engineering progress (SIC — COMPLETE 2026-03-26):**
- Pass 1: Architecture kickoff — SIC-Architecture.md, schemas, runtime/source_intelligence/ structure ✅
- Pass 2: Source Package Builder MVP ✅
- Pass 3: Workspace Management ✅
- Pass 4: Index Contract + Embedding State ✅
- Pass 5: Local Retrieval Contract + Evidence Query Layer ✅
- Pass 6: Output Generation Layer (StubGenerationAdapter + AnthropicGenerationAdapter, 7 output types) ✅
- Pass 6B: Output Persistence + Contract Alignment (output_store.py, generate_and_persist) ✅
- Pass 7: Embedding Backend Abstraction + Benchmark (LocalWordEmbedder, OpenAIEmbedder, backend_registry) ✅

**What is already built and operational:**
- Full 18-domain folder hierarchy and naming conventions
- `CLAUDE.md` routing anchor for Claude Code (v2.0)
- `SOUL.md` identity layer
- `00_HOME/` control files (Now.md, Operating-System.md, Dashboard.md, Principles.md, Assistant-Contract.md)
- Project OS files for all major active domains
- Knowledge index files across all active domains
- SOPs: Build-Log-SOP, Research-Ingest-SOP v2.1, Promotion-Session-SOP v1.0, Ingestion-Cadence v1.0
- Templates: Project-OS, Decision-Log, Experiment, Source-Note, Synthesis-Note, Generated-Idea, Daily-Note, Trade-Journal-Entry
- Agent control plane in `06_AGENTS/`: registry, vault map, tool map, permission matrix, trust tiers, handoff protocol, backends matrix
- Knowledge taxonomy — six knowledge classes, mandatory frontmatter schema, generated-ideas layer
- Active five-stage ingestion pipeline (`03_INPUTS/` → triage → sanitize → route → `02_KNOWLEDGE/`)
- ChaseOS Gate — Anthropic lane ACTIVE VERIFIED: hook scripts enforcing protected-file writes and ingestion promotion guard
- Claude persistent memory seeded: project state, writeback discipline, user profile
- Active build log discipline in `07_LOGS/Build-Logs/`

**Phase 8 engineering (COMPLETE 2026-03-31):**
- Passes 1–10: capture pipeline, operator CLI, quarantine boundary, sidecar v8.3, semantic breadcrumbs, RSS/Atom connector, SHA-256 dedup registry, browser/HTML connector, Perplexity API connector, watched-folder automation, Grok/xAI API connector ✅
- 485 tests, 0 failures; `06_AGENTS/Feature-Fit-Register.md` created ✅

**What is not yet built (honest boundaries):**
- Autonomous Operator Runtime — first-wave bounded workflows are live (Passes 1–4, 2026-04-09); Graph Substrate subsystem built (Passes 1+2, 2026-04-10); native schedule intent is built in `runtime/schedules/` (2026-04-15); Operator Briefing V2 handlers are live (2026-04-17); Runtime MCP V1 scaffold is built in `runtime/mcp/` (2026-04-20), with `workflow.invoke_bounded` active V2 for `operator_today`/`operator_close_day` as of 2026-04-21; event-triggered workflow infrastructure now has bounded queue/rule/schedule readiness surfaces, but broad event-triggered execution remains gated.
- Scheduled Briefing Pipelines — `operator_today` and `operator_close_day` are live; broader SBP consumer wiring and briefing-family expansion remain partial/gated and are tracked as NB-002/NB-021 in `docs/features/chaseos_not_built_backlog.md`.
- What's-missing Release Matrix — Studio now has a read-only `Release Matrix` panel/API/catalog entry for NB-001 through NB-043 posture, with UI/UX proof at `07_LOGS/Visual-QA/2026-06-12-nb001-043-release-matrix-closeout/`. Current parsed matrix: 43 rows total, 17 implemented-or-preview, 26 blocked-or-gated, 0 needs-review, and 43 Studio-wired-or-mapped; public beta remains **NO-GO** until Ship/Ship-Minimum gates are verified.
- Phase 9 first-wave governance infrastructure — BUILT/PARTIAL by lane: Workflow Registry has a read-only completion inspector; Agent Role Cards have registry/readiness surfaces but still need coverage refresh; Task-Type Router, Decision Ledger, Feature Filter, and Project Pivot Log are implemented.
- Phase 9 first-wave workflow handlers — BUILT in bounded form: `operator_today` and `operator_close_day` write operator briefs; `graph_hygiene` writes hygiene reports only; `graduate_ideas` writes graduation proposals only.
- Phase 9 second-wave features (Provenance Schema, Context Governance Layer, Agent Scorecards, Meeting Ingest Linker, trace_idea, drift_scan) — no longer blanket-deferred: several readiness/proof/status surfaces exist, but integrated execution and score application remain gated.
- Agent Memory Architecture — Layers C and D are formalized; read-only memory/identity inspection exists, and `chaseos memory structure` now proves the Layer C/D file-structure homes are present with missing_paths `[]`. Memory mutation, runtime dispatch, approval consumption, and canonical promotion remain gated.
- Agent Identity Ledger — seeded operationally under `runtime/memory/adapters/` with read-only inspection; automated drift scoring and mutation workflows remain deferred.
- Runtime Navigation Map — architecture defined (2026-03-25); implementation foothold seeded 2026-04-24 via `runtime/memory/nav/` + runtime profile docs; Studio now surfaces accumulated route-pattern evidence read-only, while curation/writeback remains Phase 9 governed work.
- Multi-Repo / Multi-Directory Policy enforcement — schema defined; enforcement is Phase 9
- Layer C durable generated artifacts (`02_KNOWLEDGE/[Domain]/Generated-Ideas/`) — architecture defined; directories created lazily on first promotion
- ChaseOS Studio (Phase 10) - native shell and read-only panels are implemented through Pass 10W, parser-backed graph input is complete in Pass 10X, typed graph/trust overlays are complete in Pass 10Y, read-only graph provenance inspection is complete in Pass 10Z, approval-gated node create/edit is complete in Pass 10AA, approval-gated visual link proposals are complete in Pass 10AB, Runtime Cockpit action readiness is complete in Pass 10AC, ChaseOS bootstrap wizard preview is complete in Pass 10F4, and proof-temp workspace upgrade approval/execution is complete in Pass 10F5/10F6; persisted graph storage, real target-folder/file upgrade execution, runtime action execution, and runtime/adapter activation remain future work
- Core/Personal structural separation — ACTIVE / PARTIAL: implementation plan, `CORE_MANIFEST.md`, `core_export/` allowlist machinery, candidate inventory, scanner-clean dry-run previews/reports, templates, and evidence for a guarded local Core export candidate exist; the current tracked packet is 57 manifest candidates/previews with 0 scanner blockers and a last recorded verify-export pass. The latest revalidation found the guarded export target and manual review artifact missing, so current verification is blocked until restored through the guarded export lane. Git initialization, public repository setup, license choice, public `.gitignore`, remote creation, push/publication, and canonical promotion remain separate approval gates.
- Gate enforcement beyond the Anthropic lane - runtime operation policy foothold is active for agent-bus mutation paths plus bounded setup/config/schedule/scaffold draft/browser read-screenshot paths; broader gateway/Studio/lifecycle/browser-action side-effect coverage remains Phase 9 hardening


---

## Knowledge Classification

ChaseOS classifies every piece of knowledge in the vault by its origin and trust level. This prevents raw research, verified facts, AI-generated ideas, and active project state from being conflated.

| Class | What it is | Default trust |
|-------|-----------|---------------|
| `user-origin` | Directly authored or explicitly endorsed by the user | High |
| `source-derived` | Processed from a single outside source | Tier 3 — verify before citing |
| `synthesized` | Combined from multiple sources or platform synthesis | Tier 3 — flag unverified claims |
| `generated-ideas` | AI-generated or human+AI hypotheses, theses, proposals | Tier 3 — not canonical without endorsement |
| `system-operational` | Framework SOPs, policies, templates, runtime logic | Tier 2 — framework authority |
| `canonical-state` | Active, verified project/system truth and current priorities | High — current authoritative truth |

Every promoted knowledge note in `02_KNOWLEDGE/` carries `knowledge_class` in frontmatter.
The full taxonomy, frontmatter schema, and generated-ideas rules: `06_AGENTS/Knowledge-Taxonomy.md`

---

## How to Read ChaseOS — Key Terms

A short vocabulary for working with the system. These terms have precise meanings here — conflating them is the main source of confusion about trust levels and content types.

| Term | What it means |
|------|---------------|
| **Raw input** | Unprocessed external content in `03_INPUTS/` — untrusted by default until triaged |
| **Source note** | A processed note from a single external source — article, video, lecture, or transcript |
| **Synthesis note** | A note combining multiple sources or a platform synthesis output (NotebookLM, Perplexity digest) |
| **Idea Generation** | An AI-generated or human+AI hypothesis, thesis, or proposal — not a verified fact; kept visibly separate from processed knowledge |
| **Canonical state** | Active, verified project truth — project OS files and current state notes — what the system currently believes is true |
| **Knowledge class** | A tag on every knowledge note classifying its origin and trust level: how it was made, how much to trust it |
| **Promotion** | Moving content from `03_INPUTS/` quarantine into `02_KNOWLEDGE/` after passing a four-condition gate; always human-approved |
| **Trust tier** | An authority ceiling — Tier 4 = untrusted external input, Tier 3 = research starting point, Tier 2 = operational framework |
| **The Gate** | The enforcement control layer: hook scripts and adapter manifests that block policy violations at the tool-call level |
| **Domain** | One of ChaseOS's 18 named knowledge areas — each has a knowledge index file and a project OS file |

**One example pass:** You find a useful YouTube lecture. Drop the transcript in `03_INPUTS/Transcript-Raw/`. In an ingestion session: triage it (source identified, no injection detected), sanitize it (unverified claims labeled), promote it to `02_KNOWLEDGE/Trading-Systems/` as a source note with `knowledge_class: source-derived`. The domain index gets updated. Action items surface to you for routing. The raw file keeps a PROCESSED banner as an audit trail.

---

## Why ChaseOS Is More Than AI Memory

Most AI memory tools store what you've told them and surface it later. ChaseOS is a different category.

**Local-first sovereignty.** User sources, knowledge, indexes, and workspace objects stay on the user's machine. Model providers (Claude, OpenAI, local runtimes) supply generation and embeddings — they do not own the data, define the workspace, or set governance rules. The knowledge is not delegated to a platform.

**Governed writeback.** Information that exists only in a chat window does not exist in ChaseOS. Every output from every session must be written to the vault. The Gate enforces this mechanically — hook scripts block unintended writes and require promotion approval for knowledge promotion. Discipline is structural, not volitional.

**Explicit content separation.** ChaseOS separates raw inputs, processed knowledge, AI-generated ideas, and canonical project state. These categories are never conflated. An AI-generated hypothesis is not treated as a verified fact until the user explicitly endorses it. Raw research is not the same as promoted knowledge. This separation makes the system trustworthy.

**Inspectable provenance.** Every output should eventually trace back to its inputs — the source packages, doctrine notes, memory clusters, workspace context, and prior outputs that produced it. ChaseOS is building toward a system where nothing is a black box. You can ask what the system used to derive something.

**Multi-runtime control plane.** ChaseOS is not built for one model or one provider. The same governance layer, Gate enforcement, taxonomy, and writeback discipline applies regardless of whether Claude, OpenAI, or a local model is the active runtime. The control plane is provider-agnostic.

**Ingress surfaces vs coordination substrate.** Discord is the current shared control/visibility transport, but it is not intended to remain the permanent control-field identity. ChaseOS is moving toward a model where many ingress surfaces may exist (Discord, CLI/runtime shell, future Studio/operator panels, future companion surfaces), while actionable coordination-sensitive work is translated into ChaseOS-owned structured state such as `runtime/agent_bus/` rather than being tracked in chat threads or transport-local state.

**Default coordination rule.** When one runtime participates through multiple ingress lanes (for example `hermes-chat`, a thread under `hermes-chat`, and shared `chaseos-ops`), runtime-only arbitration is not enough. By default, ChaseOS coordination-sensitive work should be represented with ingress/work-item context — channel, thread/topic, conversation identity, and work fingerprint — so present and future runtimes can deconflict work on the real unit of coordination.

**Personalization that compounds.** The system gets more useful as source archives deepen, doctrine sharpens, operator memory accumulates, and recurring workflows become patterns. This is not about better prompts. It is about accumulated operating context that the system can use across all future sessions.

**Runtime behavior that is inspectable and improvable.** Through the Agent Identity Ledger (planned), every runtime accumulates a behavioral record — what it does well, where it fails, what corrections have been applied. A system you can inspect is a system you can improve.

---

## Getting started

Start by reading the brand foundation, current repo truth, and the current operating state before changing code or docs:

- [docs/brand/README.md](docs/brand/README.md)
- [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md)
- [00_HOME/Now.md](00_HOME/Now.md)
- [06_AGENTS/Vault-Map.md](06_AGENTS/Vault-Map.md)

For local CLI setup and package entrypoints, keep using the existing install/setup docs in this repository, including [CLI-INSTALL-README.md](CLI-INSTALL-README.md), [SETUP-INSTRUCTIONS.md](SETUP-INSTRUCTIONS.md), and the command surfaces below.

## Development

### ChaseOS Shell Commands and Runtime Command Surfaces

This section is split deliberately so the README stays honest.
Some command surfaces are directly evidenced in this repository today, while others are documented as part of the broader ChaseOS implementation history and architecture.

### Proven / directly inspectable from this repo

Canonical command spine: `runtime.cli.main:main` (installed as `chaseos` and `chase`). Direct shims `python chaseos.py ...` and `python runtime\\cli.py ...` route to the same parser.

Canonical `--json` output uses the ChaseOS envelope `ok`, `action`, `result`, `errors`, `warnings`, and `audit_id`; detailed command payloads live under `result`.

Machine-readable parser truth now lives at `runtime/cli/command_contract.json`; `runtime/tests/test_cli_command_contract.py` verifies it against the canonical parser so command-path, alias, argument, JSON-shape, side-effect, and maturity drift is deliberate. The generated command reference lives at `06_AGENTS/ChaseOS-CLI-Command-Reference.md`; regenerate with `python -m runtime.cli.generate_docs --write` and check drift with `python -m runtime.cli.generate_docs --check`. Routine local CLI preflight is `python -m runtime.cli.main doctor cli --json`; the full contract/docs/action/smoke ratchet is `python -m runtime.cli.main doctor cli --contract-ratchet-smoke --json` or `python -m runtime.cli.main test cli-contract --json`.

| Command Surface | Status | How to inspect or run |
|----------------|--------|------------------------|
| `chaseos runtime inventory --json` | Live in repo | Lists discovered runtime lifecycle records from canonical CLI |
| `chaseos runtime status --runtime all --json` | Live in repo | Resolves bounded runtime state through canonical CLI |
| `chaseos runtime provider-status --runtime all --json` | Live in repo | Reports runtime provider/fallback governance, provider-state ledger posture, queue/stuck/no-chunk posture, and adapter health without mutating runtime state |
| `chaseos runtime workspace-mode route-preview --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --json` | Live in repo | Shows read-only WML/AOR routing posture without workflow dispatch, Agent Bus task write, approval consumption, external action, or canonical writeback |
| `chaseos runtime workspace-mode rollout-plan --json` | Live in repo | Shows a review-only first-profile rollout plan with proposed profile paths and draft payloads; writes no profile file and enables no dispatch |
| `chaseos runtime workspace-mode draft-packet --json` | Live in repo | Shows validated draft YAML for selected WML profiles with no profile file write, overwrite, approval consumption, or dispatch |
| `chaseos runtime workspace-mode write-approval-request --json` | Live in repo | Shows a pending profile-write approval request packet for selected WML profiles with no profile file write, dispatch, approval consumption, or canonical writeback |
| `chaseos runtime workspace-mode write-profiles --gate-approval-id ID --confirm --json` | Live in repo | Create-only guarded writer for approved WML profiles; duplicate writes block and no AOR dispatch, Agent Bus task, approval consumption, provider/model call, browser/external action, or canonical writeback occurs |
| `chaseos runtime workspace-mode dispatch-gate --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --confirm --json` | Live in repo | Clears or blocks a WML/AOR dispatch request without calling `run_workflow`, executing a workflow, writing workflow output, writing Agent Bus tasks, consuming approvals, or performing external/canonical action |
| `chaseos runtime workspace-mode dispatch-dry-run --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --confirm --json` | Live in repo | Re-runs the WML dispatch gate and calls AOR only with `dry_run=True`; writes AOR dry-run audit evidence but does not execute handlers, write workflow output, write Agent Bus tasks, consume approvals, or perform external/canonical action |
| `chaseos runtime workspace-mode live-execution-approval-gate --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --confirm --json` | Live in repo | Shows or writes a pending exact-scope WML live AOR execution approval request; does not call live `run_workflow`, execute handlers, write workflow output, consume approvals, write Agent Bus tasks, or perform external/canonical action |
| `chaseos runtime workspace-mode live-executor --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --gate-approval-id ID --decision approved --write-approval-decision --write-approval-consumption --write-consumption-marker --confirm --json` | Live in repo | Consumes an exact-scope approved WML live AOR execution packet once, re-runs the dispatch gate, binds fresh AOR dry-run evidence, reserves an exact-once marker, then calls live AOR for the approved workflow only; duplicate execution blocks before `run_workflow` |
| `chaseos runtime health --runtime <id> --json` | Live in repo | Runs runtime lifecycle health probe through canonical CLI |
| `chaseos setup provider list --json` | Live in repo | Lists setup provider records through canonical CLI |
| `chaseos config set default_provider openai --json` | Live in repo | Bounded config mutation now passes deny-by-default runtime operation policy |
| `chaseos schedule enable sch-operator-today-0700 --json` | Live in repo | Schedule state mutation now passes deny-by-default runtime operation policy |
| `chaseos scaffold project "Alpha Core" --json` | Live in repo | Draft scaffold generation now passes deny-by-default runtime operation policy before writing under `runtime/scaffold/generated/` |
| `chaseos operate browser screenshot https://example.com --json` | Live in repo | Bounded browser artifact writes now pass deny-by-default runtime operation policy |
| `chaseos gate validate --json` | Live in repo | Validates adapter manifests through canonical CLI |
| `chaseos gate check-operation <operation> --json` | Live in repo | Deny-by-default runtime operation policy smoke check |
| `chaseos doctor cli --json` | Live in repo | Fast CLI preflight for installed `chaseos` / `chase`, pyproject scripts, and compatibility shims; use `--contract-ratchet-smoke` for full parser/contract/docs/action/smoke alignment |
| `python runtime\\chaseos_gate.py validate` | Live in repo | Validates adapter manifests |
| `python runtime\\chaseos_gate.py list` | Live in repo | Lists registered adapter manifests |
| `python runtime\\chaseos_gate.py show <adapter-id>` | Live in repo | Shows a manifest |
| `python runtime\\chaseos_gate.py check-write <adapter-id> <file-path>` | Live in repo | Checks write permission |
| `python runtime\\chaseos_gate.py check-task <adapter-id> <task-type>` | Live in repo | Checks task-type permission |
| `python runtime\\state\\resolver.py` | Live in repo | Resolves and writes `runtime/state/current_state.json` |
| `python runtime\\state\\runtime_cli.py resolve` | Live in repo | Resolves runtime state |
| `python runtime\\state\\runtime_cli.py status` | Live in repo | Shows runtime status summary |
| `python runtime\\state\\runtime_cli.py status --refresh --json` | Live in repo | Refreshes and prints full runtime state JSON |
| `python runtime\\cli.py runtime health --runtime <id> --json` | Compatibility shim | Routes to canonical `runtime.cli.main` parser |
| `python runtime\\cli.py runtime health-debug --runtime <id> --json` | Compatibility shim | Routes to canonical `runtime.cli.main` parser |
| `python chaseos.py runtime health --runtime <id> --json` | Compatibility shim | Routes to canonical `runtime.cli.main` parser |

### Documented / broader ChaseOS command surfaces

These are referenced in the framework docs and README history, but should be treated as broader ChaseOS command surfaces whose exact availability depends on the active implementation environment:

- `chaseos capture file`
- `chaseos capture stdin`
- `chaseos capture rss URL [--limit N]`
- `chaseos capture browser file PATH`
- `chaseos capture perplexity --query "..."`
- `chaseos capture grok --query "..."`
- `chaseos watch add PATH --class CLASS`
- `chaseos watch run --once`
- `chaseos intake ls`
- `chaseos intake inspect`
- `chaseos intake dedup-stats`
- `chaseos doctor`
- `chaseos test capture`
- `chaseos run <workflow>`
- runtime command contract: `chaseos runtime resolve`, `chaseos runtime status`, `chaseos runtime health`

For the new runtime-state command family, read:
- `runtime/state/CLI-README.md`
- `runtime/state/COMMAND-CONTRACT-README.md`
- `06_AGENTS/ChaseOS-Runtime-Command-Contract.md`

For the broader command inventory, read:
- `runtime/COMMANDS.md`
- `CLI-SURFACES.md`
- `runtime/COMMANDS-README.md`
- `runtime/CLI-README.md`
- `runtime/LIFECYCLE-README.md`
- `runtime/lifecycle/README.md`
- `CHASEOS-COMMAND-README.md`

## Documentation

### What to Read First

| If you want to understand... | Read |
|------------------------------|------|
| The full framework philosophy | [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md) |
| How to fork this for yourself | [FORKING.md](FORKING.md) |
| Agent identity template | [SOUL.template.md](SOUL.template.md) |
| How to navigate the vault | `06_AGENTS/Vault-Map.md` |
| Workspace modes and mode-aware routing | `06_AGENTS/Use-Case-Mode-Architecture.md`, `06_AGENTS/Workspace-Mode-Profile-Standard.md`, `runtime/workspace_modes/` |
| Agent behavior rules | `00_HOME/Assistant-Contract.md` |
| Agent output conventions (all backends) | `06_AGENTS/Agent-Output-Conventions.md` |
| Which AI backends/surfaces are supported | `06_AGENTS/Backends-Supported.md` |
| Knowledge taxonomy and note classification | `06_AGENTS/Knowledge-Taxonomy.md` |
| Current sprint priorities | `00_HOME/Now.md` |
| Full domain operating system | `00_HOME/Operating-System.md` |
| Feature families and their status | `06_AGENTS/Feature-Register.md` |
| Phase 9 adopted feature specification (all 17 features) | `06_AGENTS/Phase9-Adopted-Feature-Specification.md` |
| Operator Surface + Runtime Interaction Layer architecture | `06_AGENTS/Operator-Surface-Runtime-Interaction.md` |
| Phase/layer triage register | `06_AGENTS/Feature-Fit-Register.md` |
| Multi-layer memory architecture | `06_AGENTS/Agent-Memory-Architecture.md` |
| Scheduled Briefing Pipelines architecture | `06_AGENTS/Scheduled-Briefing-Pipelines.md` |
| Autonomous Operator Runtime architecture | `06_AGENTS/Autonomous-Operator-Runtime.md` |
| Operator Briefing v2 architecture | `06_AGENTS/Operator-Briefing-Architecture.md` |
| Native Scheduling Intent architecture | `06_AGENTS/Scheduling-Intent-Architecture.md` |
| Runtime commands and shell surfaces | `runtime/COMMANDS.md`, `CLI-SURFACES.md`, `runtime/COMMANDS-README.md`, `runtime/CLI-README.md`, `runtime/LIFECYCLE-README.md`, `runtime/state/CLI-README.md`, `CHASEOS-COMMAND-README.md` |
| ChaseOS MCP Server architecture + V1 stdio scaffold | `06_AGENTS/ChaseOS-MCP-Server.md`, `runtime/mcp/` |
| Graph Substrate architecture | `06_AGENTS/Graph-Substrate-Architecture.md` |
| Runtime Navigation Map architecture | `06_AGENTS/Runtime-Navigation-Map.md` |
| Runtime profile + nav scaffolds | [[Hermes-Runtime-Profile]], [[OpenClaw-Runtime-Profile]], [[Codex-Runtime-Profile]], `runtime/memory/nav/` |
| Browser autonomy governance | `06_AGENTS/Browser-Autonomy-Policy.md`, `06_AGENTS/Browser-Task-Patterns.md`, `runtime/browser_registry/` |
| Dual-runtime coordination substrate | `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`, `runtime/agent_bus/`, `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md` |
| How control-panel input should translate into structured ChaseOS state | `06_AGENTS/Control-Plane-Ingress-and-Bus-Translation.md`, `runtime/agent_bus/README.md` |
| Core/Personal split implementation | `06_AGENTS/Core-Personal-Split-Implementation-Plan.md`, `CORE_MANIFEST.md`, `core_templates/` |
| Core-vs-Personal operator views and export surfaces | `06_AGENTS/Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application.md` |
| Project cockpit + workspace browser surfaces | `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md` |
| Consolidated operator cockpit surface | `06_AGENTS/Consolidated-Operator-Cockpit-Standalone-Application.md` |
| Knowledge navigator + domain browser surfaces | `06_AGENTS/Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md` |
| Settings / provider-config / scaffold surfaces | `06_AGENTS/Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application.md` |
| Governed promotion / review center surfaces | `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md` |
| Cross-panel object-model consolidation | `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md` |
| Agent scorecards / runtime quality surfaces | `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md` |
| Execution repair / failure recovery surfaces | `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md` |
| Memory inspector / runtime-memory surfaces | `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md` |
| Agent identity ledger surfaces | `06_AGENTS/Agent-Identity-Ledger-Surfaces-Standalone-Application.md` |
| Graph-native node and edge consolidation surfaces | `06_AGENTS/Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application.md` |
| Memory editing / curation surfaces | `06_AGENTS/Memory-Editing-and-Curation-Surfaces-Standalone-Application.md` |
| Core export sync doctrine | `06_AGENTS/Core-Export-Sync-Procedure.md` |
| Markdown -> standalone bridge | `06_AGENTS/Markdown-to-Standalone-Bridge.md` |
| Source Intelligence Core architecture | `06_AGENTS/SIC-Architecture.md` |
| ChaseOS VentureOps business/application layer | `06_AGENTS/VentureOps-Architecture.md`, `06_AGENTS/VentureOps-Instance-Intelligence.md`, `06_AGENTS/Workflow-Recommendation-Engine.md`, `06_AGENTS/Revenue-Workflow-Registry.md`, `06_AGENTS/Workflow-Pack-Standard.md` |

---

## 2026-04-27 Adapter Foundation Truth

- OpenAI adapter foundation added as a shadow/dry-run surface: `openai_operator_research_shadow`, OpenAI policy/config, role card, and Responses API MCP payload builder exist; no live OpenAI API call is enabled.
- ChaseOS Runtime MCP now exposes additional ChaseOS-named safe resources/tools/prompts for adapter use, a unit-tested JSON-RPC stdio wrapper for core MCP methods, and a local subprocess stdio client smoke proof; it remains internal infrastructure, not a public MCP deployment.
- n8n MCP hub policy, workflow exposure registry, connection readiness harness, approval-aware dry-run call governance, and redacted proof artifact runner exist; the current workspace proof blocks live probing because no n8n instance/access token is configured. Governed n8n call drafts are audit-only; no production workflow or live Discord/Telegram send is configured.
- ChatGPT Apps SDK remains a future UI layer; no ChatGPT app is built or deployed.

## Current Limitations

- The framework is still Obsidian-backed in its current implementation, but ChaseOS Studio now has a native shell/read-only panel lane, parser-backed graph input, typed graph/trust overlays, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposals, and approval-gated Runtime Cockpit action-readiness requests, and read-only ChaseOS bootstrap preview. The full standalone governed product experience is still incomplete.
- Agent workflows are defined contractually but not yet automated — agents operate on instruction, not on schedule
- Context routing is partly formalized by the Workspace Mode Layer (`runtime/workspace_modes/`), safe path inference, route preview, profile rollout/draft/write gates, WML/AOR dispatch gate, dry-run executor, live-execution approval request gate, and the exact-once WML live executor (`chaseos runtime workspace-mode live-executor`). The first three approved runtime foundation profiles now exist at `runtime/.workspace-mode.yaml`, `06_AGENTS/.workspace-mode.yaml`, and `01_PROJECTS/ChaseOS/workspace-mode.yaml`; approved packet `wml-aor-live-exec-appr-58147fa104e8514d` was consumed once for `operator_today`, producing live AOR audit `96064d06-81fc-4939-9061-3c6fd958149e` and `07_LOGS/Operator-Briefs/2026-05-14-operator-today.md`. This is exact-scope proof only, not broad live runtime autonomy.
- Input capture is partially automated — the Phase 8 connector stack (`chaseos capture`, `watch_folders.py`, RSS/browser/API connectors) automates content intake into quarantine; full autonomous operator workflows (scheduled SIC ingestion, idea graduation, vault maintenance) are Phase 9
- The Core/Personal split is no longer merely conceptual: structural separation is an active development lane with `core_export/` machinery, scanner-clean preview/report artifacts, Core templates, and 2026-05-01 evidence for a guarded local `chaseos-core` export candidate. Remaining limitations are export-state reconciliation plus governance/publication gates: restore/revalidate the guarded local export target and manual review artifact through the approved export lane, then address license decision, public ignore policy, Git-init approval, public repo setup, and canonical promotion.
- The markdown -> standalone mapping layer is now explicitly documented in `06_AGENTS/Markdown-to-Standalone-Bridge.md`, but the standalone surface itself remains unbuilt

---

---

*Graph links: [[PROJECT_FOUNDATION]] · [[CLAUDE]] · [[FORKING]] · [[06_AGENTS/Agent-Output-Conventions|Agent-Output-Conventions]] · [[06_AGENTS/Knowledge-Taxonomy|Knowledge-Taxonomy]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[Phase9-Adopted-Feature-Specification]] · [[Agent-Memory-Architecture]] · [[Scheduled-Briefing-Pipelines]] · [[06_AGENTS/Autonomous-Operator-Runtime|Autonomous-Operator-Runtime]] · [[Runtime-Navigation-Map]] · [[06_AGENTS/SIC-Architecture|SIC-Architecture]] · [[ChaseOS-OS]] · [[TradingSystems-OS]] · [[FullStackWeb2Web3-OS]]*

*ChaseOS - Framework version: 0.9 | Phases 1-8 complete | Phase 9 active: AOR first-wave live + Graph Substrate (87 tests) + Operator Briefing V2 live + Native Schedule Layer live + ChaseOS-MCP-Server v1.0 architecture | Phase 10: Studio native shell/read-only panel lane through 10W + parser-backed graph input in 10X + typed graph/trust overlays in 10Y + graph provenance inspection in 10Z + approval-gated node create/edit in 10AA + approval-gated visual link proposals in 10AB + Runtime Cockpit action readiness in 10AC + bootstrap wizard preview in 10F4 + proof-temp workspace upgrade approval/execution in 10F5/10F6 | chaseos CLI v0.10.0 | sidecar schema v8.3 | 485 capture tests + 87 graph substrate tests passing*


*Graph links auto-wired by vault_hygiene (2026-05-04): [[AGENTS]] . [[CLI-INSTALL-README]] . [[KNOWLEDGE-INDEX]] . [[NEXT-STEPS]] . [[OPERATOR-BRIEF-INDEX]] . [[RUNTIME-REGISTRY]] . [[SETUP-INSTRUCTIONS]] . [[STRIKEZONE-DISCORD-SETUP]] . [[SYSTEM-STATUS]]*

## 2026-06-02 Terminal Workbench + ChaserAgent Expansion Addendum

The Hermes-inspired Terminal Workbench / ChaserAgent / Studio expansion has been scoped from the canonical handoff at `06_AGENTS/ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2.md`. New canonical planning docs now live at `06_AGENTS/Terminal-ChaserAgent-Feature-Matrix.md`, `06_AGENTS/ChaserAgent-Architecture.md`, `06_AGENTS/Terminal-Workbench-Architecture.md`, and `06_AGENTS/Session-Export-and-Artifacts-Architecture.md`.

Implementation truth: the only code foothold added in this pass is `runtime/operator_surface/adapters/terminal_adapter.py`, now PARTIAL for bounded read-only subprocess execution. It blocks destructive/write/network/elevated/unknown commands, validates cwd scope, captures/redacts/truncates output, and labels terminal output as Tier 4 untrusted. Targeted verification passed with `PYTHONPATH=. uvx --with pyyaml pytest runtime/operator_surface/tests/test_terminal_adapter.py -q` (`6 passed`). ChaserAgent, `runtime/chaser/`, `board.py`, Terminal Workbench UI, `chaseos operate terminal`, session export backend, artifact hub, voice, mobile remote control, billing, and autonomous terminal execution remain PLANNED / DOCS-ONLY / DEFERRED as labeled in the feature matrix.
