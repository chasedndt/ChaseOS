# PROJECT_FOUNDATION.md
## ChaseOS â€” Internal Architecture and Identity Document

> This document is the internal truth record for ChaseOS. It goes deeper than the README. It defines what the project is, what it is becoming, what the hard design decisions are, and where the boundaries lie. It is a living document and should be updated when the architecture evolves.
---

## 1. Project Identity

**ChaseOS** is a privacy-first agentic operating system where humans and AI agents work together through secure memory, knowledge graphs, automations, and permissioned execution.

Internally, ChaseOS remains a local-first human-agent control plane for source intelligence, structured memory, project governance, runtime orchestration, permissioned agent execution, and workflow productization.

It is a framework â€” not a vault, not a plugin, not a productivity method. The framework defines:

- how memory is structured and navigated
- how projects are governed and tracked
- how workspace purpose is resolved before agent read/write/workflow behavior
- how sources are ingested, normalized, grouped, and reasoned over
- how context is routed to agents and tools
- how authority and permissions are bounded
- how outputs get written back into the system
- how a person and permissioned agent runtimes operate together coherently

ChaseOS owns the orchestration and data model. Model providers (Claude, OpenAI, local runtimes) are pluggable adapters that supply generation and embeddings â€” they do not define the workspace architecture, knowledge model, or governance rules.

**User data stays in the user's system.** Source files, source packages, indexes, workspaces, and generated outputs remain local-first. The provider is swappable. The knowledge is not.

The current implementation is an Obsidian vault. This is the substrate, not the identity.

The product identity is the framework.

**Brand foundation (2026-05-22):** Current public positioning, copy guardrails, visual thesis, and preliminary design-token direction live in `docs/brand/`. This is documentation-only brand adoption; final logo assets, UI redesign, and branded installer assets remain planned until separate verified implementation passes complete them.

**Domain override alignment (2026-05-31):** The selected primary public launch domain is `https://chaseos.ai`. ChaseOS remains the product/platform, ChaseOS Studio remains the app/control panel, Chaser Forge remains the marketplace/ecosystem layer, and Managed Agents / Chaser Agent remains future/post-V1. `chaseos.systems` is superseded as primary and may become a future secondary redirect, standards/ecosystem alias, or defensive domain. Domain selection does not mark public beta, live Forge fetch, billing, managed agents, or marketplace payments as complete.

**Why the scope expanded (2026-03-21):** Phase 6 proved that the governed ingestion core works â€” the manual pipeline from raw inputs to promoted knowledge notes is solid and disciplined. What Phase 6 revealed is that the intelligence layer is entirely missing: the part that reasons over grouped sources, retrieves evidence, and generates structured outputs. External advisory tools (NotebookLM, Perplexity) were bridging that gap. The Source Intelligence Core (Phase 7) is the direct consequence â€” ChaseOS will own that layer rather than delegating it to platform dependencies.

---

## 2. Philosophical Framing

ChaseOS is built on a small set of hard beliefs:

**Canonical truth beats scattered notes.**
Information has one authoritative home. Everything else is a pointer to it or a derivation from it. There is no "well I think it's in one of these three places." There is the file, or there is nothing.

**Context should be loaded minimally and intentionally.**
Agents should not read everything every time. Large context dumps are architectural failure. The right context for a task is narrow, specific, and pre-identified. ChaseOS is designed so that a small number of files can orient any agent to any task without loading the full system.

**Writeback matters.**
If a build session produced something real, it must go into the vault. Outputs that exist only in an ephemeral chat window do not exist. The system only knows what it has on record.

**Assistants must not become the source of truth.**
AI tools assist. They read, reason, and generate. They do not hold authoritative state. The vault holds authoritative state. If an agent generates an insight, that insight becomes real when it is written to the vault, not when it is spoken in chat.

**Systems over heroics.**
The system must run on low-energy days. SOPs, templates, and agent contracts exist so that the operating system does not depend on willpower or exceptional effort. Good architecture is good on a bad day.

**Sovereignty over convenience.**
No dependency on systems that are not understood. No black boxes in the critical path. If a tool is used, it is used with awareness of what it does and what it costs. This applies to AI tools as much as infrastructure.

---

## 3. Current Implementation Truth

The current ChaseOS implementation is an Obsidian vault with the following structure:

```
00_HOME/          Control tower â€” master OS, principles, dashboard, sprint focus
01_PROJECTS/      Active project operating files, one per domain/project
02_KNOWLEDGE/     Domain knowledge bases, 11 folders
03_INPUTS/        Raw unprocessed input material
04_SOPS/          Standard operating procedures â€” build, research ingest
05_TEMPLATES/     Reusable templates for notes and logs
06_AGENTS/        Agent configuration â€” registry, vault map, tool map
07_LOGS/          Time-stamped records â€” build logs, daily, weekly
99_ARCHIVE/       Historical record â€” snapshots, handovers, session summaries
```

### Current System State

2026-05-15 MVP continuation status: the current operating sector is `MVP Integration / Operator Workflow Activation`. The one-clean current-state command is `python -m runtime.cli.main mvp current-state --json`, and the stop/continue gate is `python -m runtime.cli.main mvp operator-action-required --json`. Live gate truth remains `safe_to_call_update_goal_complete=false` with only P0 `openai_secret_reference` still operator-owned; the unresolved placeholder target is `SET_OPENAI_SECRET_REF`. The previously pending tracked Chat approval `5849a53f-10e0-46af-a89a-7de06150f7f8` is approved, consumed exactly once, target-written, marker-present, and no longer a current P1 decision. `mvp current-state` and `mvp completion-audit` now discover latest MVP writeback evidence, including the 2026-05-15 setup-scope and latest-record passes. Canonical handoff: `07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md`. This note does not authorize secret reads, provider calls, setup metadata writes, new approval consumption, Agent Bus writes, browser/host control, or canonical mutation.

Phases 1–8 complete. Active phase: 9 (Operator Runtime / AOR) — Pass 4 COMPLETE 2026-04-09; bounded first-wave workflow set live (`chaseos run operator_today`, `operator_close_day`, `graph_hygiene`, `graduate_ideas`); all run through manifest → role card → task router → Stage 6 dispatch → Stage 7 bounded writeback → audit; `graph_hygiene` and `graduate_ideas` are proposal-only. Graph Substrate Passes 1+2 COMPLETE 2026-04-10 (`runtime/graph/`, 87 tests). Architecture Pass COMPLETE 2026-04-14 (Operator-Briefing-Architecture.md, Scheduling-Intent-Architecture.md, ChaseOS-MCP-Server.md). Runtime MCP V1 stdio scaffold COMPLETE 2026-04-20; Pass 6B `workflow.invoke_bounded` active V2 COMPLETE 2026-04-21; Pass 6C operator smoke + duplicate-output hardening COMPLETE 2026-04-21 (`runtime/mcp/`, 67 MCP tests). **OpenClaw LIVE 2026-04-15** — OpenClaw installed and operational; Discord transport operational; `operator_today`, `operator_close_day`, `graph_hygiene` executed through the OpenClaw → `chaseos run` → AOR path; scheduled execution proven through OpenClaw cron/control plane; Discord delivery operational; AOR writeback and audit verified. Discord is now specified as a shared control-plane transport in `06_AGENTS/ChaseOS-Discord-Control-Plane.md`; the spec does not grant Hermes, MCP, Home Assistant, or new connector authority. Native ChaseOS schedule intent (`runtime/schedules/`) is built and validated; OpenClaw remains the external execution lane. Operator Briefing V2 is live for `operator_today` and `operator_close_day`. Hermes bounded shadow activation is proven, but Hermes remains shadow-only and draft/audit-only. Runtime-instance bounded promotion substrate for OpenClaw and Hermes is now also present as activation-blocked evaluation truth: draft manifests and role cards exist, readiness-gate docs exist, canonical helper surfaces exist, `07_LOGS/Promotion-Records/` is seeded, and pair-level validation machine-checks approval/escalation/readiness/writeback structure while `status: draft` and adapter fail-closed posture keep canonical promotion blocked. Phase 7 COMPLETE 2026-03-26. Phase 8 COMPLETE 2026-03-31; 485 tests. Anthropic lane hook enforcement live and verified.

Acquisition + Normalization is now a named Phase 9 feature family with a Pass 1A generic implementation substrate. It defines how governed runtimes gather real-world operating inputs and convert them into inspectable source packs, evidence bundles, briefing-ready input sets, action-ready runtime packets, and memory candidates before AOR/SBP/SIC/delivery consume them. The current implementation produces only `source_packet`, `normalized_source_pack`, and `briefing_ready_input_set` artifacts from declared local inputs. It does not add MCP authority, canonical writeback, ambient vault/browser access, delivery, action packets, memory candidates, outcome scoring, or a native ChaseOS cron runner.

Workspace Mode Layer (WML) is now the mode-aware context contract for ChaseOS workspaces. It distinguishes `personal_os`, `study_research`, `founder_venture`, `business_ops`, `runtime_agent_ops`, and `unknown` contexts, preserving the existing six knowledge classes and AI-generated output bridge while exposing read order, output classes, allowed workflows, adapter ceilings, approval rules, graph rules, protected paths, write targets, fail-closed unknown-mode behavior, read-only AOR route previews through `chaseos runtime workspace-mode route-preview`, review-only rollout planning through `chaseos runtime workspace-mode rollout-plan`, validated draft YAML packets through `chaseos runtime workspace-mode draft-packet`, pending profile-write approval request packets through `chaseos runtime workspace-mode write-approval-request` and `write-approval-request-full`, create-only guarded profile creation through `chaseos runtime workspace-mode write-profiles` and `write-profiles-full`, no-execution WML/AOR dispatch gate checks through `chaseos runtime workspace-mode dispatch-gate`, WML-gated AOR dry-run execution through `chaseos runtime workspace-mode dispatch-dry-run`, pending live AOR execution approval requests through `chaseos runtime workspace-mode live-execution-approval-gate`, exact-scope approved live AOR execution through `chaseos runtime workspace-mode live-executor`, and product status/ledger inspection through `chaseos runtime workspace-mode product-status` and `approval-ledger`. The full approved profile set now exists at `runtime/.workspace-mode.yaml`, `06_AGENTS/.workspace-mode.yaml`, `01_PROJECTS/ChaseOS/workspace-mode.yaml`, `04_SOPS/.workspace-mode.yaml`, `01_PROJECTS/University/workspace-mode.yaml`, and `00_HOME/.workspace-mode.yaml`; WML approval packet `wml-aor-live-exec-appr-58147fa104e8514d` has been consumed once for `operator_today`, with decision/marker/consumption artifacts under `07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_*`, fresh dry-run audit `f5f131c7-3581-41f0-a9cd-1b75dd791fe6`, live AOR audit `96064d06-81fc-4939-9061-3c6fd958149e`, and operator brief `07_LOGS/Operator-Briefs/2026-05-14-operator-today.md`. `product-status` reports the WML runtime/operator product feature `COMPLETE` from repo evidence. WML is not RBAC/SSO, team accounts, broad runtime autonomy, Agent Bus task execution, provider/model execution, browser control, canonical promotion, or a requirement for a native Studio visual panel.

### What Is Live Now

What is already operational:
- Folder hierarchy and naming conventions
- 18-domain operating system (Operating-System.md)
- Project OS files for all major active projects
- Domain knowledge index files
- Agent behavior contracts (Assistant-Contract.md)
- Identity and doctrine (SOUL.md, Principles.md)
- Vault navigation guide (Vault-Map.md)
- Agent registry (Agent-Registry.md)
- Tool map (Tool-Map.md)
- SOPs for build sessions and research ingestion
- Templates for projects, decisions, experiments, source notes
- Dashboard and sprint focus file (Now.md)
- ChaseOS Gate â€” Anthropic lane ACTIVE VERIFIED; all 4 hooks live (protected_write_guard, ingestion_promotion_guard, session_start_context, session_end_audit)
- Knowledge taxonomy â€” six knowledge classes, frontmatter schema, generated-ideas layer
- Workspace Mode Layer — COMPLETE for runtime/operator product feature: docs, profile standard/template, safe path inference, profile validation, fail-closed unknown mode, read-only AOR route preview under `runtime/workspace_modes/`, canonical CLI contract `chaseos runtime workspace-mode route-preview`, profile rollout planner, validated draft packets, profile-write approval request commands, create-only guarded profile writers including `write-profiles-full`, no-execution WML/AOR dispatch gate, WML-gated AOR dry-run executor, live AOR execution approval gate, exact-once live executor, read-only product status and approval ledger, six valid workspace profiles, and one approved `operator_today` WML live execution proof with live audit `96064d06-81fc-4939-9061-3c6fd958149e`
- Five-stage ingestion pipeline proven with real inputs
- Source Intelligence Core â€” all 7 passes complete (2026-03-26):
  - `ingest_source()` MVP â€” 4 source types (Pass 2)
  - `workspace_manager.py` â€” create/load/add/remove/list workspaces (Pass 3)
  - `embedder.py` + `index_manager.py` â€” embedding state + index contract (Pass 4)
  - `similarity.py` + `retriever.py` â€” cosine similarity retrieval, 17-field evidence packets (Pass 5)
  - `output/prompt_builder.py` + `generator.py` â€” structured output generation, 9 output types, Anthropic + stub adapters (Pass 6)
  - `output_store.py` â€” workspace-local output persistence, generate_and_persist() (Pass 6B)
  - `LocalWordEmbedder` + `OpenAIEmbedder` + `backend_registry.py` + `benchmark.py` â€” real embedding backends, list-backends CLI (Pass 7)
  - `runtime/source_intelligence/` directory structure with schemas
- Architecture doctrine docs: `Agent-Memory-Architecture.md`, `Feature-Register.md`, `Scheduled-Briefing-Pipelines.md`, `Autonomous-Operator-Runtime.md`
- Connector/Capture Automation â€” Phase 8 COMPLETE â€” all 10 passes done 2026-03-31; 485 tests:
  - `ContentPacket` + `router.py` + `intake_writer.py` + `capture.py` â€” capture pipeline with type-first org, sidecar v8.3 (Passes 1â€“3)
  - `chaseos` / `chase` operator CLI â€” `capture file/stdin/rss/browser/perplexity/grok`, `watch add/remove/list/enable/disable/run`, `intake ls`, `intake inspect`, `intake dedup-stats`, `doctor`, test-capture (Pass 2â€“3+5+6+7+8+9+10)
  - Physical quarantine boundary: `03_INPUTS/00_QUARANTINE/[class]/`; `00_` sorts first (Pass 2)
  - Sidecar v8.3: 6 semantic breadcrumb hint fields + vocabulary constants (Pass 3)
  - AI-Generated-Output-Bridge architecture: 4-layer Aâ†’Bâ†’Câ†’D flow documented (Pass 3)
  - SIC-Architecture.md v1.1: Layer B bridge rules formally wired (Pass 4)
  - `runtime/capture/connectors/rss_connector.py` â€” RSS 2.0 + Atom 1.0 connector, stdlib-only; per-item event_date_hint; feed provenance in extra_metadata; `chaseos capture rss URL [--limit N]` (Pass 5)
  - `dedup_registry.py` â€” SHA-256 dedup registry; fail-open; first-capture-wins; `chaseos intake dedup-stats` (Pass 6)
  - `runtime/capture/connectors/browser_connector.py` â€” stdlib html.parser HTMLâ†’markdown; title auto-extraction (cli>html_title>h1>filename); `chaseos capture browser file PATH` (Pass 7)
  - `runtime/capture/connectors/perplexity_connector.py` â€” Perplexity API connector; stdlib urllib.request; `PERPLEXITY_API_KEY` env var only; default input_class=digest; citations extraction; `chaseos capture perplexity --query "..."` (Pass 8)
  - `watch_folders.py` â€” watched-folder automation; `.chaseos/watch_folders.json` config; `.chaseos/watch_processed.json` processed-file registry (path+mtime+size); two dedup layers; .txt/.md/.html routing; `chaseos watch add/remove/list/enable/disable/run --once/--interval N`; fail-safe per-file (Pass 9)
  - `runtime/capture/connectors/grok_connector.py` â€” Grok/xAI API connector; stdlib urllib.request; `XAI_API_KEY` env var only; OpenAI-compat endpoint; default input_class=digest; finish_reason in extra_metadata; `chaseos capture grok --query "..."` (Pass 10)
- `06_AGENTS/Feature-Fit-Register.md` â€” canonical feature/layer triage register; Phase 8/7/9/10 scope table; triage rules for new feature requests (Pass 10); Cross-Cutting section added (2026-04-08)
- `06_AGENTS/Security-Research-Workflow-Layer.md` â€” domain workflow specialization for security research: intake path, SIC workspace conventions, trust state separation (raw â†’ workspace-local â†’ knowledge note â†’ doctrine), promotion rules, auditability requirements (2026-04-08)
- `06_AGENTS/Execution-Adapter-Standard.md` â€” Sections 4.1 Evaluation Dimensions + 4.2 Security-Sensitive Workflow Adapter criteria added (2026-04-08)
- `06_AGENTS/Backends-Supported.md` â€” Enforcement Status table added; docs-vs-enforcement gap made explicit per lane (2026-04-08)
- `06_AGENTS/Developer-Co-Development-Mode.md` â canonical feature definition for Developer Co-Development Mode; ChaseOS-owned, adapter-capable; five subfeatures (Repo Truth Explainer, Contradiction/Drift Scan, Doc Refresh Proposal Generator, Implementation Brief Generator, Diagram Draft Generator); AOR/OSRIL/Studio/adapter relationship; safety posture and non-goals (created 2026-04-22; artifact contract updated 2026-04-23)
- `runtime/aor/developer_shadow.py` â `developer_repo_explain_shadow` AOR handler; reads narrow declared context; produces draft developer brief, contradiction scan, doc refresh proposal, implementation brief, diagram proposal, audit, build log, and archive note; shadow-mode only; forbidden: shell, git, network, credential reads, broad traversal, canonical writes; 30 tests pass (2026-04-23)
- `runtime/acquisition/` — Acquisition + Normalization Pass 1A substrate; `plan.py`, `models.py`, `validators.py`, `adapters/local.py`, `builder.py`, and `source_pack_builder.py` validate acquisition plans, read declared local inputs only, produce `source_packet`, `normalized_source_pack`, and `briefing_ready_input_set`, preserve provenance/trust/freshness/transformation chain fields, and write only runtime pack artifacts; 24 focused acquisition tests pass (2026-04-23)

### What Is Planned / Not Yet Built

What is not yet operational:
- Broad automated agent execution beyond bounded AOR workflows (first-wave AOR and OpenClaw schedule execution are live; other adapter lanes remain documented or shadow-only)
- Broad fully automated context routing without approvals remains unbuilt. WML itself is complete as a bounded runtime/operator product feature with validation, inference, six profiles, route preview, profile approval/write gates, dispatch gate, AOR dry-run execution, exact-scope live execution, product status, and approval ledger; broad live autonomy still requires separate exact-scope approvals.
- Broader Acquisition + Normalization implementation — Pass 1A generic source-pack substrate is active, but live browser acquisition, connector/API acquisition, memory candidates, action-ready packets, delivery-ready packets, outcome scoring, scheduler integration, and SBP consumer wiring remain future
- Additional broad scheduled/event-triggered workflow families beyond the currently declared bounded schedules remain gated; invalid StrikeZone future schedule intents were reset to disabled/shadow and registry-backed during the 2026-06-12 V1 audit.
- Agent Identity Ledger and Execution Repair Memory are no longer merely architectural: identity ledgers are seeded under `runtime/memory/adapters/`, the read-only memory inspector surfaces them, and execution-repair/candidate-store modules are implemented under `runtime/agents/` with focused tests. Automated drift scoring and broad UI workflows remain future.
- Runtime Navigation Map — architecture defined (2026-03-25); implementation foothold seeded 2026-04-24 via `runtime/memory/nav/` and runtime profile docs; evidence-driven accumulation remains Phase 9; per-runtime evolving navigational overlay distinct from Vault Map, Layer C behavioral memory, and Agent Identity Ledger
- Scheduled Briefing Pipelines beyond the current operator_today/operator_close_day schedule path
- MCP server V1 is LIVE (`runtime/mcp/`); active V2 `workflow.invoke_bounded` is LIVE; further MCP surface expansion is deferred per design-freeze
- Full standalone governed Studio product experience — Phase 10 native shell/read-only panels, parser-backed graph input, typed graph/trust overlays, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposals, approval-gated Runtime Cockpit action-readiness requests, read-only Open Folder compatibility readiness, read-only Obsidian vault detection, read-only general Markdown inference preview, and the NB-001..043 Release Matrix panel/API/catalog entry with proof under `07_LOGS/Visual-QA/2026-06-12-nb001-043-release-matrix-closeout/` exist. The Release Matrix currently parses 43 rows with 13 implemented-or-preview, 25 blocked-or-gated, 5 needs-review, and 43 Studio-wired-or-mapped. Public beta is still NO-GO until launch/package, legal/privacy, public repo hygiene, leak/smoke proof, final release acceptance, migration/setup execution, runtime action execution, and runtime/adapter activation gates are verified.
- Formal Core/Personal structural separation is ACTIVE / PARTIAL: implementation-plan + manifest + `core_templates/` staging were seeded 2026-04-24, and the 2026-05-01 Core export lane now has `core_export/` allowlist machinery, candidate inventory, scanner-clean dry-run previews/reports, and evidence for a guarded local `chaseos-core` export candidate. 2026-05-11 revalidation found the local target absent and the manual review artifact missing, so current verify-export is blocked until restored through the guarded export lane. Git initialization, public repository setup, license choice, remote creation, push/publication, and canonical promotion remain separate approval gates.

---

## 4. Future Standalone Direction

ChaseOS is designed to evolve beyond its current Obsidian implementation.

### Source Intelligence Core (Phase 7 â€” COMPLETE, 2026-03-26)

The next major layer. ChaseOS will build its own self-hosted, local-first intelligence layer:

**Source Package Layer** â€” every source becomes a normalized internal object: source ID, type, title, origin, raw extracted text, chunked representation, metadata, trust/provenance, workspace assignment.

**Workspace / Notebook Layer** â€” groups source packages around a topic, project, course, or research question. The self-built equivalent of a NotebookLM notebook â€” owned locally, not platform-dependent.

**Retrieval / Evidence Layer** â€” chunks source packages, embeds them, retrieves relevant passages, and attaches evidence citations to outputs. Grounds outputs in specific source content, not generic summarization.

**Output Generation Layer** â€” structured outputs over workspaces: source summary, FAQ, briefing, timeline, study guide, comparison note, Idea Generation note, synthesis draft.

**Provider Adapter Layer** â€” pluggable model provider for generation and embeddings. Claude/Anthropic, OpenAI/Codex, local models (Ollama or equivalent). The provider supplies generation; it does not own workspace logic or source data.

External tools (NotebookLM, Perplexity) may remain as optional inbound connectors (Phase 8), but they are not the intelligence core. ChaseOS is.

### Additional future layers

**Connector / Capture Automation (Phase 8 â€” COMPLETE 2026-03-31)** â€” All 10 passes done. Pass 10: `grok_connector.py` (Grok/xAI API, `XAI_API_KEY` env var, default model grok-3, `chaseos capture grok --query`). Pass 9: `watch_folders.py` (watched-folder automation, `chaseos watch` family, Phase 8 DoD met). Pass 8: `perplexity_connector.py` (Perplexity API, citations, `chaseos capture perplexity --query`). Pass 7: `browser_connector.py` (stdlib html.parser, HTMLâ†’markdown). Pass 6: `dedup_registry.py` (SHA-256 dedup). Pass 5: `rss_connector.py`. Passes 1â€“4: capture pipeline, operator CLI, quarantine boundary, sidecar v8.3. 485 tests, 0 failures. `06_AGENTS/Feature-Fit-Register.md` created. Phase 9 (Operator Runtime / AOR) is next.

**Operator Runtime (Phase 9 â€” ACTIVE) â€” Autonomous Operator Runtime + Acquisition/Normalization + Runtime Shell + OSRIL + Scheduled Briefing Pipelines + Adopted Feature Set**

Phase 9 delivers six layers running on the same infrastructure. Full feature specification: `06_AGENTS/Phase9-Adopted-Feature-Specification.md`. Pass 1 (AOR Foundation) COMPLETE 2026-03-31; Passes 2–4 completed the bounded first-wave workflow set on 2026-04-09. Acquisition + Normalization architecture and Pass 1A generic source-pack substrate completed 2026-04-23. Scheduled/event-triggered wiring and broader runtime-shell work remain next.

**Autonomous Operator Runtime (AOR)** â€” the OS-level execution infrastructure. The layer that binds chosen runtimes, models, and tools to ChaseOS memory, repos, execution rules, writeback targets, and audit requirements. AOR enables bounded autonomous operation under explicit policy. It provides:
- Workflow registry and manifest-based execution
- Explicit permission ceilings per workflow (no ambient vault access)
- Repo-aware operation (reads current vault state before acting)
- Prompt-injection hardening for automated inputs
- Mandatory audit trails for every autonomous action
- Multi-repo targeting under declared policy
- Long-running runtime support beyond session-based execution
- Support for OpenClaw-style and custom operator registration
- Draft runtime-instance promotion/readiness substrate for OpenClaw and Hermes — manifests, role cards, helper-backed readiness inspection, promotion-record routing, and pair-level validation now exist while activation remains blocked by draft/fail-closed policy
- **Hermes Agent** as a formally registered Phase 9 bounded operator runtime adapter (governance complete 2026-04-08; bounded shadow activation proven 2026-04-09; non-canonical shadow lane only)
- Runtime Navigation Map — per-runtime evolving navigational overlay consulted before each autonomous workflow run

Canonical doc: `06_AGENTS/Autonomous-Operator-Runtime.md`
Hermes governance docs: `HERMES.md`, `06_AGENTS/Hermes-Adapter-Spec.md`, `06_AGENTS/Hermes-Workflow-Boundaries.md`, `06_AGENTS/Hermes-Memory-Boundary.md`

**Runtime Navigation Map** â€” a per-runtime, evolving navigational overlay built from operational history. Records which vault routes a specific runtime prefers, which zones it trusts, which paths have led to failures, and which decision points require escalation. Makes runtimes more efficient within their already-defined permission scope â€” does not expand permissions or override governance rules.

Canonical doc: `06_AGENTS/Runtime-Navigation-Map.md`
Seeded implementation foothold: `runtime/memory/nav/_schema.json`, `runtime/memory/nav/hermes/nav-map.json`, `runtime/memory/nav/openclaw/nav-map.json`, `06_AGENTS/Hermes-Runtime-Profile.md`, `06_AGENTS/OpenClaw-Runtime-Profile.md`
Bridge doc: `06_AGENTS/Markdown-to-Standalone-Bridge.md`

**Acquisition + Normalization Layer** — the governed input-preparation bridge between capture/source availability and workflows, briefings, actions, memory, and delivery. It defines acquisition scope, source surfaces, acquisition methods, runtime responsibility, normalized artifact types, provenance fields, trust/freshness/actionability rules, and outcome-feedback separation. Pass 1A implements the first generic substrate under `runtime/acquisition/`: acquisition plan validation, first-wave artifact validators, local declared-source acquisition, source-pack building, and a StrikeZone fixture. It complements Phase 8 Capture and Phase 7 SIC: Capture moves material into quarantine/sidecar form, SIC indexes and retrieves source packages, while Acquisition + Normalization decides what to gather for a task and how it becomes a workflow-ready operating packet.

Canonical docs: `06_AGENTS/Acquisition-Normalization-Layer.md`, `06_AGENTS/Acquisition-Surface-Map.md`, `06_AGENTS/Normalization-Provenance-Contract.md`, `06_AGENTS/Runtime-Acquisition-Responsibility-Matrix.md`, `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md`
Standalone bridge/application doc: `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`

**Scheduled Briefing Pipelines** â€” a reusable pipeline pattern for producing structured, scheduled, guardrailed briefings from governed data sources. Each pipeline is defined by: trigger schedule, input adapters, execution adapter, writeback targets, delivery adapters, and guardrail profile. Generic SBP substrate built in Pass 1A (2026-04-22): SBPConfig manifest contract, SBPGuardrailProfile, InputAdapter/DeliveryAdapter ABCs, SBPBaseHandler base class, generic pipeline runner. Instance pipelines build on this substrate — first named instance: StrikeZone Market Digest Publisher (daily morning market briefing â†’ Discord + Whop). Pipelines run on top of AOR infrastructure and route all outputs through the standard ChaseOS Gate.

**ChaseOS VentureOps** — the governed runtime/product layer that converts ChaseOS capabilities into repeatable, auditable, monetizable workflows for Chase-owned ventures and client-facing services. VentureOps sits above AOR, SIC, MCP, Studio, Gate, Hermes, OpenClaw, Codex, and future adapters as the business/application layer. Current status as of 2026-05-11: PARTIAL / LIVE CLIENT SCOPE CONTRACT VERIFIED / REAL CLIENT INPUT REQUIRED / NO LIVE CLIENT RUN / NO LIVE EXTERNAL DELIVERY. Canonical docs and scaffolds now exist, including `06_AGENTS/VentureOps-Architecture.md`, `06_AGENTS/VentureOps-Instance-Intelligence.md`, `06_AGENTS/Workflow-Recommendation-Engine.md`, `06_AGENTS/Revenue-Workflow-Registry.md`, `06_AGENTS/Workflow-Pack-Standard.md`, `06_AGENTS/Customer-Proof-Artifact-Standard.md`, `06_AGENTS/Agent-Scorecard-Standard.md`, `06_AGENTS/Runtime-Adapter-Use-Case-Matrix.md`, `06_AGENTS/Workflow-Exchange-Readiness-Standard.md`, workflow-pack templates, proof templates, scorecard templates, `runtime/workflows/registry/use_case_registry.yaml`, schema templates, pack examples under `runtime/workflows/registry/packs/`, read-only helpers under `runtime/ventureops/`, and a bounded AOR workflow manifest/handler for `agent_runtime_governance_audit`. The latest synthetic client-style internal run ingested declared fixture runtime/governance files and wrote an internal proof, client-safe draft report, standalone scorecard, offer packet, client-scope record, blocked delivery approval contract, no-send delivery packet preview, pending approval request artifact, approval consumption proof, exact-once delivery gate proof, delivery gate marker, external-send dry-run proof, approved external-send local proof-sink artifact, CRM draft, payment/invoice draft, Workflow Exchange publication preview, and live client scope contract under `07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-scope-contract*`. No live client run, live client data ingestion, marketplace publication, payment mutation, CRM mutation, browser action, provider call, live external client delivery, live client workflow, or live revenue workflow is implemented yet.

2026-05-13 current-status correction: the MVP readiness gate now discovers the approved internal ChaseOS scope packet and guarded scoped local live-client workflow proof under `07_LOGS/Workflow-Proofs/`. VentureOps pass 7 is complete for one scoped local workflow proof. Broader VentureOps remains partial because live revenue proof, external delivery, CRM/payment mutation, provider/browser execution, marketplace publication, and canonical promotion are still unverified and gated.

2026-05-13 closeout update: the operator accepted this VentureOps instance as closed for the internal workflow proof objective. Payment evidence is not required for this closeout. The future real-world use-case lane remains separate: when ChaseOS/VentureOps is run against a real system, real scope, delivery, and payment evidence can be supplied and validated through the guarded revenue proof chain.

Canonical doc: `06_AGENTS/Scheduled-Briefing-Pipelines.md`

**Adopted Feature Set â€” 10 first-wave + 6 second-wave features** â€” identified during Phase 8 as architecturally necessary for AOR to function correctly. The first-wave features are governance infrastructure that AOR workflows depend on; the second-wave features extend AOR once the foundation is stable.

First-wave governance infrastructure (must be built before AOR runs in production):
- Workflow Registry â€” canonical manifest store for all authorized AOR workflows; no workflow runs without a registry entry
- Agent Role Cards â€” bounded runtime-role definitions (NOT personas); consumed by AOR at workflow initialization; defines allowed/forbidden actions, required reads, write scope, escalation rules
- Task-Type Router â€” canonical classification for all task types; maps task type â†’ required reads, runtime class, permission set, writeback expectations; unclassified tasks escalate rather than run
- Decision Ledger â€” immutable record for operational and architectural decisions; captures rationale, alternatives rejected, consequences; required for AOR autonomous decision audit
- Feature Filter â€” formal 6-question filter for all feature proposals; formalized as `04_SOPS/Feature-Filter-SOP.md`; governs additions to Feature-Fit-Register.md
- Project Pivot Log â€” structured record of major direction changes; immutable entries; captures what changed, what is killed, what is unlocked

First-wave AOR workflows (the first live demonstrations of AOR in operation):
- operator_today â€” first live AOR workflow; runs on demand via `chaseos run operator_today`; reads Now.md, Project-OS files, intake queue, and recent logs; writes structured brief to `07_LOGS/Operator-Briefs/`; read-only vault access
- operator_close_day — end-of-session close-out workflow; reads today's outputs; checks session-close checklist completeness; pairs with operator_today; live through the governed AOR path
- graph_hygiene â€” weekly vault maintenance scan; identifies broken links, orphaned notes, stale frontmatter, index drift, aging quarantine items; outputs maintenance proposal (no automated vault edits)
- graduate_ideas â€” idea lifecycle workflow; surfaces graduation candidates from quarantine and generated-ideas layer; outputs graduation proposal for operator review; no autonomous promotion to canonical destinations

Second-wave features (dependent on first-wave; built once foundation is stable):
- Provenance Schema â€” machine-readable lineage model extending SIC source packages + Phase 8 sidecar v8.3; prerequisite for Context Governance Layer and trace_idea
- Context Governance Layer â€” makes notes action-governing; AOR and SIC consult CGL metadata (trust level, sensitivity, promotion stage) before using a note as context input
- Agent Scorecards â€” runtime-performance memory (Layer C); tracks reliability, overreach, CGL compliance per runtime; feeds Agent Identity Ledger behavioral evolution
- Meeting Ingest Linker â€” post-capture enrichment for transcripts; maps entities to vault structure; outputs link proposals for operator review
- trace_idea â€” on-demand lineage traversal; traces an idea from first capture through promotion to current canonical state; read-only vault traversal
- drift_scan â€” weekly doctrine-vs-behavior comparison; flags neglected domains, priority drift, persistent open loops; read-only vault access

**Later candidate (not Phase 9 scope):**
- Paperclip â€” orchestration surface above ChaseOS; executive dashboard, cross-system triggers, external system integration; MUST NOT bypass Gate or write canonically without AORâ†’Gate chain; reserved for post-Phase-10 design

**Runtime Shell / Command Surface (Phase 9 subset)** â€” the operator-command and configuration surface above AOR. The Runtime Shell routes operator commands in to execution (the input-flow side). OSRIL routes AOR events out to the operator (the output-flow side). Both are Phase 9 infrastructure; both are needed. Key features: provider/model registry, shell command router (`chaseos workflow`, `chaseos run`, `chaseos models`, `chaseos scaffold`, `chaseos config`), workflow launcher, environment/config store, brain/workspace scaffold generator, expanded doctor/health commands.

Canonical doc: `06_AGENTS/ChaseOS-Runtime-Shell.md`

**Operator Surface + Runtime Interaction Layer / OSRIL (Phase 9 subset)** â€” the event-visibility and session layer. AOR execution events (task started, approval required, task complete) route through the Runtime Interaction Contract to any consuming operator surface. Operator-facing features: action dispatch visibility, runtime session model with resumable sessions, harness-agnostic operator execution, approval-linked execution flow.

Canonical doc: `06_AGENTS/Operator-Surface-Runtime-Interaction.md`

**ChaseOS Studio (Phase 10)** â€” the standalone desktop, graph-first, mouse-first visual operating surface for ChaseOS. Studio is the product shell that wraps SIC (Phase 7), Capture (Phase 8), and AOR (Phase 9) and surfaces them through a governed write surface with full trust-state and provenance visibility. Current repo truth: the native PyWebView shell/read-only panel lane is implemented through Pass 10W, Pass 10X adds read-only parser-backed graph input, Pass 10Y adds read-only typed graph/trust overlays, Pass 10Z adds read-only graph-node provenance chain inspection, Pass 10AA adds approval-gated node create/edit, Pass 10AB adds approval-gated visual link proposals with bounded pending-edge overlays, Pass 10AC adds approval-gated Runtime Cockpit action-readiness requests, Pass 10F1 adds read-only Open Folder compatibility readiness, Pass 10F2 adds bounded read-only Obsidian vault detection, and Pass 10F3 adds read-only general Markdown inference preview over parser-backed candidate nodes, edges, domains, trust defaults, and migration warnings. Studio has two target modes: ChaseOS-native (full governance, trust states, AOR runtime visibility) and general markdown / Obsidian-compatible (best-effort graph exploration, migration path). Remaining major work includes runtime action execution, import/setup onboarding, runtime/adapter activation, persisted graph storage, and deferred Canvas/whiteboard. Architecture formalized 2026-04-08.

Canonical docs: `06_AGENTS/ChaseOS-Studio-Architecture.md` (Studio product architecture), `06_AGENTS/ChaseOS-Runtime-Shell.md` (Runtime Shell / command surface), `06_AGENTS/Operator-Surface-Runtime-Interaction.md` (OSRIL surfaces)

**Automated routing engine** â€” a routing layer that resolves which files are relevant for a task and loads only those, replacing manual agent direction.

Phase 7 is complete: all 7 passes done 2026-03-26. Phase 8 is complete: all 10 passes done 2026-03-31 — 485 tests, 9 capture subcommands, SHA-256 dedup registry, quarantine-first doctrine, sidecar v8.3, semantic breadcrumbs. Phase 9 Passes 2–4 COMPLETE 2026-04-09: `operator_today`, `operator_close_day`, `graph_hygiene`, and `graduate_ideas` are live through the governed AOR path; Stage 6 dispatch and Stage 7 bounded writeback are real; `graph_hygiene` and `graduate_ideas` remain proposal-only; audit records write to `07_LOGS/Agent-Activity/`. Phase 10 is active/incremental: native Studio shell/read-only panels, parser-backed graph input, typed graph/trust overlays, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposals, approval-gated Runtime Cockpit action-readiness requests, read-only Open Folder compatibility readiness, read-only Obsidian vault detection, and read-only general Markdown inference preview exist, while the full governed Studio product experience remains incomplete.

---

## 5. Core vs Personal Split

ChaseOS is designed to support two distinct layers:

### ChaseOS Core

The public, forkable, reusable framework layer.

Core contains:
- Folder hierarchy conventions
- Note type definitions and naming conventions
- Routing rules and context discipline
- Agent behavior contracts (generic templates)
- Operating principles (the philosophy, not personal doctrine)
- Reusable templates (project OS, decision log, experiment, source note, daily note)
- Boilerplate structure that any user can populate
- SOUL.template.md (identity layer template, not personal)
- Guidance for forking, customization, and population

Core does **not** contain:
- Personal identity, doctrine, or values
- Actual project details or private working state
- Real project OS files with private information
- Personal logs, build records, or operating history
- Credentials, private keys, or sensitive external references

### ChaseOS Personal

The private, populated instance layer.

Personal contains implementation-specific material that must stay out of public Core exports:
- Actual project OS files and private project details
- Populated sprint priorities and current working state
- Instance-specific doctrine and identity notes
- Private build logs, daily records, open loops, decisions, and project history
- Domain knowledge populated with private research
- Agent/runtime registries that include credentials, account details, or tool-access information
- Tool maps or connector notes containing account-specific information

This workspace is the active source workspace used to develop and validate ChaseOS. It follows Core conventions and may contain populated implementation context, so public-facing exports must be produced only through the guarded Core extraction lane and reviewed for private-context leakage.

The structural separation lane is now active rather than purely conceptual. `CORE_MANIFEST.md`, `core_export/export_manifest.yaml`, `core_export/core_candidate_inventory.yaml`, `core_export/templates/`, and `core_export/reports/latest/` define the current machine-checkable Core extraction path. The latest tracker records 57 manifest candidates/previews, 0 scanner blockers, a guarded local export update, and a recorded verify-export pass for a guarded local Core export inspection target. The latest revalidation found that export target absent in this environment and `core_export/reports/latest/manual-preview-review-pass2.md` missing, so both must be restored/revalidated through the guarded export lane before any Git/publication step. That target remains generated output for inspection only, not a public repository or canonical source.

The architectural gap to close: Core boilerplate should eventually be versioned separately (as a template repository or git submodule) so that a forking user can pull Core updates without overwriting their Personal context. The next safe slice is export-state reconciliation plus public-readiness cleanup: restore/revalidate the export target and manual review artifact through approved lanes, inspect the current 57-file candidate, decide license/public `.gitignore`, close any scanner/public-readiness gaps, then request a separate Git-init approval only after review is clean. Remote creation, push/publication, and canonical promotion remain later gates.

---

## 6. Role of Obsidian

Obsidian is currently serving three roles in ChaseOS:

1. **Memory backend** â€” the file system with structured markdown notes is the data store
2. **Visualization layer** â€” graph view, backlinks, and search make the memory navigable
3. **Editing interface** â€” notes are created and updated in Obsidian's editor

Obsidian is a strong default because:
- Files are plain markdown â€” not locked to Obsidian, portable to any future backend
- Local-first â€” no cloud dependency in the critical path
- Plugin ecosystem â€” extensible without custom code
- Graph view â€” structural navigation for a complex system

Obsidian is not the right long-term answer because:
- No native agent interface â€” there is no programmatic API for agents to read/write the vault
- GUI-bound â€” terminal-first or CLI workflows require workarounds
- Plugin dependency risk â€” the ecosystem is external and can change
- Visualization is generic â€” custom dashboards and domain views are not possible in vanilla Obsidian

The plan is to keep Obsidian as one valid interface while building framework layers that are not Obsidian-dependent.

---

## 7. Role of Agents

The agent layer is governed by a three-layer model:

```
Provider  â‰   Execution Surface  â‰   Granted Permission Scope
```

**Provider** â€” who makes the underlying model (Anthropic, OpenAI, Google, xAI, open-source)
**Execution surface** â€” how the model connects to tools and vault files (agent harness, chat UI, workflow runtime, research platform)
**Permission scope** â€” what the owner explicitly grants this instance

Trust tiers are **authority ceilings**, not capability bundles. The same Anthropic model running as Claude Code (agent harness) can write the vault directly. The same model running on claude.ai (chat surface) is advisory-only. Provider identity does not determine access â€” execution surface and granted permissions do.

Agent instances currently operating in ChaseOS:

| Surface                               | Provider   | Access                             | Trust Tier                     | Status  |
| ------------------------------------- | ---------- | ---------------------------------- | ------------------------------ | ------- |
| Anthropic Agent Harness (Claude Code) | Anthropic  | Direct vault read/write            | Tier 2 â€” High Trust          | Active  |
| Anthropic Chat Surface (claude.ai)    | Anthropic  | Advisory only â€” no vault access  | Tier 3 â€” Advisory            | Active  |
| NotebookLM                            | Google     | Upload-mediated read only          | Tier 3 â€” Research            | Active  |
| Perplexity AI                         | Perplexity | External web â€” no vault access   | Tier 3 â€” Research            | Active  |
| Grok / xAI                            | xAI        | External web/X â€” no vault access | Tier 3 â€” Research            | Active  |
| n8n self-hosted                       | n8n        | Workflow-scoped vault access       | Tier 2 ceiling â€” conditional | Planned |
| OpenAI Agent Harness (SDK/MCP)        | OpenAI     | MCP-mediated vault access          | Tier 2 ceiling â€” conditional | Planned |
| Local/Open-Source Harness             | Various    | Direct local filesystem            | Tier 2 ceiling â€” conditional | Active  |

Full registry: `06_AGENTS/Agent-Registry.md`
Backend/surface details: `06_AGENTS/Backends-Supported.md`

**Agent philosophy:**
- Agents are tools, not authorities
- Agents read context; they do not hold it
- Agents write back to the vault; they do not store state in themselves
- Agents operate within permission contracts; they do not self-authorize
- No agent should be able to modify core identity or operating files without explicit user approval
- The framework is model-agnostic â€” execution surface and permission scope matter, not which provider's model is running

**Output conventions for all agent backends:** `06_AGENTS/Agent-Output-Conventions.md`
This file defines the writeback rules, output types, and template requirements that apply regardless of which agent (Claude Code, OpenAI, n8n, etc.) is producing output.

---

## 8. Context Routing Philosophy

The context routing model in ChaseOS is:

**Narrow context, not full context.**

When an agent is assigned a task, it should load:
1. The sprint focus file (`Now.md`) â€” what is in scope
2. The relevant project OS file â€” current state of the specific project
3. Any domain knowledge files directly relevant to the task

It should NOT load:
- The full operating system document unless the task is about the OS itself
- All project OS files simultaneously
- The full knowledge base for a domain when only one concept is needed
- Identity and doctrine files unless the task involves decisions or principles

This model keeps tokens low, keeps reasoning tight, and prevents agents from conflating context across domains.

The Vault Map (`06_AGENTS/Vault-Map.md`) is the routing guide. It tells agents where to look for any given type of task.

Future direction: a formal context routing engine that resolves the relevant file set for a task before invocation, rather than relying on agents to self-direct.

---

## 9. Memory and Writeback Philosophy

**Memory is in the vault. Not in chat.**

When a session produces something real â€” a decision, a build output, an updated project status, a new piece of knowledge â€” it must be written to the vault before the session ends.

The writeback discipline includes:
- Build logs for every engineering session (`07_LOGS/Build-Logs/`)
- Project OS file updates when status or goals change
- Knowledge notes when new domain knowledge is developed
- Decision logs when significant choices are made
- Archive notes when important snapshots need to be preserved

**Writeback is not optional.** An undocumented session did not happen in terms of system state.

The assistant close protocol (defined in `SOUL.md` and `00_HOME/Assistant-Contract.md`) enforces this at the session level: Claude Code writes build logs directly at session end â€” agent-assisted writeback is the default. The user is prompted only when the write target is ambiguous or the session produced no meaningful output. Flagging open loops and confirming vault updates are always required.

**Formal memory architecture:**
ChaseOS defines a five-layer memory model that specifies how different types of memory are separated, stored, scoped, and used:
- **Layer A â€” Shared System Doctrine:** Global rules (Gate, taxonomy, permissions) that apply to all runtimes and tasks
- **Layer B â€” User-Specific Operating Memory:** What the system has learned about this user's goals, preferences, and recurring patterns
- **Layer C â€” Agent/Runtime-Specific Memory:** Per-adapter behavioral profiles; the Agent Identity Ledger (planned) tracks behavioral evolution of each runtime
- **Layer D â€” Workspace/Task-Local Memory:** Ephemeral context scoped to one SIC workspace or run; does not propagate to other layers without explicit promotion
- **Layer E â€” Execution-History/Audit Memory:** Permanent append-only record of all sessions, runs, and outcomes

Full architecture: `06_AGENTS/Agent-Memory-Architecture.md`

---

## 9a. Provenance and Output Traceability

ChaseOS is designed so that every output generated by the system is increasingly attributable â€” traceable back to the specific inputs, context, and memory that produced it.

**The provenance principle:**
Anything ChaseOS generates should eventually be able to trace back to combinations of:
- Source packages used (which sources were loaded into the workspace)
- Workspace context (what the workspace was for, what questions it was answering)
- Doctrine notes consulted (which principles or operating rules were in context)
- Project notes consulted (which project OS files or sprint priorities shaped the output)
- Memory clusters active (which user-specific or runtime-specific memory was applied)
- Prior generated ideas that were referenced or built upon
- User-origin knowledge explicitly endorsed and loaded
- Runtime/agent context (which adapter executed, at what trust tier)
- Execution history (whether this follows a pattern from prior runs)

**Why this matters:**
- Every output should know where it came from
- The user should be able to understand what the system used to derive something
- Future outputs should build on the provenance graph, not ignore it
- Links between outputs and their sources are not decorative â€” they are accountability and inspectability
- The graph structure should improve over time as more outputs accumulate their provenance records
- Future interfaces should expose provenance clearly so users can audit what produced any output

**Current state:** Provenance is partially captured through knowledge taxonomy frontmatter fields (`source_ref`, `source_refs`, `linked_index`), build log records, and workspace object state. Full output-level provenance graph tracking is a future system capability (Phase 10 interface layer).

---

## 9b. Workspace-Local vs Durable Outputs

Not everything produced by ChaseOS should become a permanent vault note. ChaseOS defines a clear hierarchy of output states, each with a different interpretation and different governance rules.

**The five output states:**

**1. SIC Runtime Artifacts (workspace-local, ephemeral)**
These exist only inside a SIC workspace during a run: retrieved evidence passages, intermediate reasoning traces, draft FAQ entries, working hypotheses. They are useful for the current task but are not promoted automatically.
- Lives in: `runtime/source_intelligence/workspaces/[workspace]/`
- Durability: Session-scoped or workspace-scoped
- Gate requirement: None â€” this is pre-promotion workspace state
- User action needed: Review and decide whether to promote

**2. Workspace-Local Intermediate Outputs (structured, retained)**
Outputs that are kept in workspace state for future reference but are not yet vault notes. Workspace output history, draft briefings, query results stored in workspace.json.
- Lives in: Workspace object output history
- Durability: Workspace-scoped (survives workspace sessions but not promoted)
- Gate requirement: None
- User action needed: Explicit promotion decision

**3. Durable Markdown Artifacts (vault notes, taxonomy-governed)**
Promoted notes written to `02_KNOWLEDGE/` or `01_PROJECTS/`. These carry knowledge class frontmatter, trust tier, and domain indexing. They are the outputs that ChaseOS treats as durable knowledge.
- Lives in: `02_KNOWLEDGE/[Domain]/` or `01_PROJECTS/[Project]/`
- Durability: Permanent (vault note with writeback discipline)
- Gate requirement: Promotion gate (human approval required)
- User action needed: Explicit promotion via Promotion-Session-SOP

**4. Promoted Knowledge (canonical, taxonomy-classed)**
Notes that have passed the four-condition promotion gate, carry a declared knowledge class, and are linked in the domain index. These are the system's processed knowledge layer.
- Knowledge class: one of six (`user-origin`, `source-derived`, `synthesized`, `generated-ideas`, `system-operational`, `canonical-state`)
- Lives in: `02_KNOWLEDGE/[Domain]/`
- Durability: Permanent, authoritative for its knowledge class

**5. Canonical State (active truth)**
The system's current, authoritative operating truth: `Now.md`, project OS files, `ROADMAP.md`, `CLAUDE.md`. These define what the system currently believes is true about its own state, projects, and priorities.
- Lives in: `00_HOME/`, `01_PROJECTS/`, root-level docs
- Durability: Permanent, updated as state changes
- Gate requirement: Protected file rules apply

**Why not everything should become a vault note:**
Workspace reasoning artifacts are useful for a run but are not worth the governance overhead of promotion. Promoting everything creates vault noise and dilutes the signal-to-noise ratio of `02_KNOWLEDGE/`. The promotion step is a filter â€” not a formality.

**How a user should interpret these states:**
- If it is in a workspace but not promoted: it is draft intelligence, not operational knowledge
- If it is a vault note with knowledge class: it is processed knowledge at a known trust tier
- If it is in `01_PROJECTS/` or `00_HOME/`: it is canonical operating state
- If it is in `07_LOGS/`: it is historical record, not current truth

---

## 10. Trust Boundaries

ChaseOS defines explicit trust and permission levels:

| Action | Level |
|--------|-------|
| Read any vault file | Always permitted |
| Create new notes | Permitted |
| Edit existing notes | Permitted with user direction |
| Modify core OS documents | Requires explicit user approval |
| Delete files | Never without explicit instruction |
| Execute code or scripts | Requires user approval |
| Make external network requests | Requires user awareness |
| Modify identity files (Principles, SOUL, Operating-System) | Explicit approval only |

**Trust must be earned per-action, not assumed per-session.**

Prompt injection is a real risk. Untrusted external text â€” web clips, ingested digests, transcript content â€” must be treated as potentially hostile. The ingest SOP (`04_SOPS/Research-Ingest-SOP.md`) should account for this. Agents should never execute instructions embedded in raw input material.

---

## 11. Model-Agnostic Design Goals

ChaseOS should work regardless of which AI model or provider is used.

Design rules:
- Vault structure should be readable by any text-capable AI
- SOPs should be written as instructions to "the assistant," not to a specific model
- Templates should produce notes that any model can parse
- Agent contracts should define behavior, not model-specific syntax
- The framework should not be permanently coupled to Claude Code or any Anthropic product

The current implementation leans on Claude Code for engineering sessions and Claude Chat for research. This is practical, not architectural. The underlying conventions should survive a change of providers.

---

## 12. What Should Remain Framework-Level

These belong in ChaseOS Core â€” framework-level, not personal:

- Folder numbering conventions (00â€“99)
- Note type definitions (Project-OS, Knowledge-Index, SOP, Template, Log, Archive)
- Routing rules (how agents should navigate)
- Agent permission model (read/write/modify/delete boundaries)
- Writeback discipline (the principle that outputs must go to the vault)
- Context loading philosophy (narrow, not full)
- Trust boundaries and prompt injection awareness
- Template files (Project-OS-Template, Decision-Log-Template, etc.)
- SOUL.template.md (identity layer pattern, not personal content)
- Forking guidance and Core/Personal split documentation

---

## 13. What Should Remain Personal-Instance-Level

These belong in ChaseOS Personal â€” not shareable as framework:

- SOUL.md (personal identity, values, doctrine)
- Principles.md (personal decision rules)
- Operating-System.md (personal 18-domain definition)
- Now.md (personal sprint priorities)
- All Project-OS.md files with real project details
- All knowledge notes with researched content
- All build logs and daily records
- Agent-Registry.md with real tool access references
- Tool-Map.md with personal accounts and API references
- Dashboard.md with personal status

---

## 14. What Not To Do Yet

**Phase 7 COMPLETE â€” all 7 passes done (2026-03-26). Do not re-implement:**
- Source package builder â€” `ingest_source()` MVP live (Pass 2)
- Workspace management â€” `workspace_manager.py` live (Pass 3)
- Index contract + embedding state â€” `embedder.py` + `index_manager.py` live (Pass 4)
- Local retrieval â€” `similarity.py` + `retriever.py` + cosine similarity + evidence packets (Pass 5)
- Output generation â€” `prompt_builder.py` + `generator.py` + 9 output types + Anthropic adapter (Pass 6)
- Output persistence â€” `output_store.py` + `generate_and_persist()` + workspace-local storage (Pass 6B)
- Real embedding backends â€” `LocalWordEmbedder` + `OpenAIEmbedder` + `backend_registry.py` + `benchmark.py` (Pass 7)
- Architecture doctrine docs â€” `Agent-Memory-Architecture.md`, `Feature-Register.md`, `Scheduled-Briefing-Pipelines.md`, `Autonomous-Operator-Runtime.md`

**Phase 8 complete components (do not re-implement):**
- Capture pipeline â€” `ContentPacket` + `router.py` + `intake_writer.py` + `capture.py` (Pass 1)
- Operator CLI â€” `chaseos` / `chase` console scripts + `runtime/cli/main.py` (Pass 2)
- Physical quarantine boundary â€” `03_INPUTS/00_QUARANTINE/[class]/` (Pass 2)
- Sidecar v8.3 â€” 6 semantic breadcrumb hint fields + vocabulary constants (Pass 3)
- `chaseos intake inspect PATH` command (Pass 3)
- AI-Generated-Output-Bridge 4-layer architecture documented (Pass 3)
- SIC-Architecture.md v1.1 â€” Layer B bridge rules wired (Pass 4)
- Lazy Generated-Ideas scaffolding policy confirmed (Pass 4)
- Semantic hint vocabulary confirmed advisory-only (Pass 4)
- RSS/Atom feed connector â€” `rss_connector.py`; stdlib-only; `chaseos capture rss URL [--limit N]`; RSS 2.0 + Atom 1.0; per-item provenance (Pass 5)
- SHA-256 dedup registry â€” `dedup_registry.py`; `.chaseos/dedup_registry.json`; connector-agnostic; fail-open; `chaseos intake dedup-stats` (Pass 6)
- Browser/HTML connector â€” `browser_connector.py`; stdlib html.parser; HTMLâ†’markdown; title auto-extraction; `chaseos capture browser file PATH` (Pass 7)
- Perplexity API connector â€” `perplexity_connector.py`; stdlib urllib.request; env-var-only creds; default input_class=digest; citations; `chaseos capture perplexity --query "..."` (Pass 8)
- Watched-folder automation â€” `watch_folders.py`; `.chaseos/watch_folders.json` + `.chaseos/watch_processed.json`; polling-based; .txt/.md/.html routing; `chaseos watch add/remove/list/enable/disable/run`; fail-safe per-file; Phase 8 DoD met (Pass 9)
- Grok/xAI API connector â€” `grok_connector.py`; stdlib urllib.request; `XAI_API_KEY` env var only; OpenAI-compat endpoint; default input_class=digest; `chaseos capture grok --query "..."` (Pass 10)
- Feature-Fit Triage Register â€” `06_AGENTS/Feature-Fit-Register.md`; canonical phase/layer triage table; triage rules for all future feature requests (Pass 10)

**Phase 8 complete. All 10 passes done 2026-03-31.**

**Not in scope until Phase 9:**
- Autonomous Operator Runtime implementation (architecture defined â€” do not build yet)
- Scheduled Briefing Pipelines implementation (architecture defined â€” do not build yet)
- Agent Identity Ledger implementation
- Execution Repair Memory implementation
- Runtime Navigation Map implementation
- AOR wiring of semantic hint vocabulary

**Phase 10 (ChaseOS Studio) remaining scope:**
- Full governed Studio product experience beyond the current native shell/read-only panels, parser-backed graph input, visual overlays, provenance inspection, and approval-gated create/edit/link proposal flows
- Custom visualization layer
- Building custom Obsidian plugins

**Ongoing gated decisions (not time-critical):**
- License decision for any public/forkable Core repository
- Public ignore policy / scanner-safe `.gitignore` pass
- Git-init approval for the guarded local `chaseos-core` export candidate
- Public repository setup, remote creation, push/publication, and release process
- Canonical promotion of any Core/Public truth beyond the guarded local export lane

**What IS complete through Phase 8 Pass 10 (all 7 SIC passes + 10 Phase 8 passes):**
- ChaseOS Gate â€” Anthropic lane ACTIVE VERIFIED
- Five-layer ingestion pipeline proven with real inputs
- Knowledge taxonomy â€” six knowledge classes, frontmatter schema, generated-ideas layer
- Promotion-Session-SOP and Ingestion-Cadence â€” operational session conventions
- Claude persistent memory seeded (project state, writeback discipline, user profile)
- Full SIC runtime: source packages, workspace management, local embedding + retrieval, output generation + persistence, real embedding backends
- Operator CLI: `chaseos` and `chase` installed and verified; 9 capture subcommands (file, stdin, rss, browser, perplexity, grok); watch family; intake family
- Capture runtime: ContentPacket â†’ quarantine pipeline with semantic breadcrumb hints, SHA-256 dedup, 485 tests
- AI-Generated-Output-Bridge: 4-layer Aâ†’Bâ†’Câ†’D architecture documented and wired into SIC doctrine
- Feature-Fit Triage Register: canonical phase/layer feature classification for Phase 8 through Phase 10
- Five-layer memory architecture defined; AOR + SBP + Agent Identity Ledger + Execution Repair Memory defined as planned features

**Phase 8 COMPLETE (2026-03-31).** Phase 9 (Autonomous Operator Runtime) is next.

---

## 15. Design Tensions and Risks

**Tension: Obsidian-first vs framework-first**
The current implementation is deeply Obsidian-native (wikilinks, Obsidian-specific syntax, plugin reliance). This creates friction for future portability. Mitigation: keep markdown conventional, avoid over-reliance on Obsidian-specific features, document where Obsidian-specific syntax is used.

**Tension: Personal context vs forkable framework**
The live repository remains a populated personal implementation that mixes framework structure with personal operating truth, but extraction is no longer only conceptual. Mitigation now runs through the active Core/Personal structural lane: `CORE_MANIFEST.md`, `core_export/` allowlist machinery, scanner-clean previews/reports, template rewrites, and 2026-05-01 evidence for the guarded local `chaseos-core` export candidate. Current target presence must be revalidated through the guarded export lane before any Git/publication step. Remaining work is approval-gated publication readiness, not blind structural copying: license decision, public ignore policy, Git-init approval, public repo setup, and canonical promotion remain separate gates.

**Tension: Manual agent operation vs future automation**
Agents currently operate on explicit instruction. Future automation requires defined permissions, writeback targets, and failure modes. Mitigation: define agent contracts carefully now so they extend naturally to automated contexts later.

**Risk: Vault complexity growing faster than governance**
As the vault grows, without discipline it becomes harder to navigate. Mitigation: enforce routing rules, Vault Map maintenance, and archive discipline rigorously.

**Risk: Context rot in Project-OS files**
If project OS files are not updated regularly, they become false context. An agent reading a stale Project-OS will reason incorrectly about a project's state. Mitigation: build OS file update into session close protocol; make stale files obvious.

**Risk: Prompt injection via raw input**
Ingested web content, digests, and transcripts may contain adversarial instructions. An agent processing raw input without awareness could execute injected instructions. Mitigation: treat all raw input as untrusted; agents should not act on instructions embedded in input material.

---

## 16. Current Architecture Status (Phase 8 COMPLETE â€” Pass 10 Complete 2026-03-31)

Phases 1â€“8 complete. Phase 8 (Connector / Capture Automation) COMPLETE â€” all 10 passes done 2026-03-31. Phase 7 (Source Intelligence Core) COMPLETE â€” all 7 passes done 2026-03-26. Architecture doctrine and roadmap expansion pass completed 2026-03-23: Agent Memory Architecture, Scheduled Briefing Pipelines, and Autonomous Operator Runtime formally documented as canonical feature families. Phase 9 (Operator Runtime / AOR + SBP) is the next active engineering phase. See Section 4 for the full future direction, Section 9/9a/9b for memory architecture and output clarity, and Section 19 for the SIC architecture.

Phase 4 control plane canonical docs:
- `06_AGENTS/Agent-Control-Plane.md` v1.1 â€” framework control architecture anchor
- `06_AGENTS/Permission-Matrix.md` â€” canonical permission source
- `06_AGENTS/Trust-Tiers.md` v1.1 â€” authority ceiling definitions
- `06_AGENTS/Handoff-Protocol.md` â€” session start/close and context handoff
- `06_AGENTS/Agent-Security-Model.md` â€” framework-level threat model
- `00_HOME/Assistant-Contract.md` v2.0 â€” Phase 4 aligned

Phase 5 execution adapter layer canonical docs:
- `06_AGENTS/Execution-Adapter-Standard.md` v1.0 â€” 4 adapter classes, 11 required sections
- `CLAUDE.md` v1.6 â€” Anthropic harness execution adapter (reference implementation)
- `OPENAI.md`, `LOCAL-OSS.md`, `N8N.md` v1.0 â€” other adapter bindings (documented conformance only)
- `06_AGENTS/Claude-Memory-System.md`, `Hook-Patterns.md`, `Subagent-Patterns.md` â€” Phase 5B

Phase 6 additions â€” ACTIVE:
- `06_AGENTS/ChaseOS-Gate.md` v1.1 â€” enforcement control layer; Anthropic lane ACTIVE VERIFIED 2026-03-21
- `runtime/policy/adapters/claude.yaml` â€” all 4 hooks verified; `.venv/Scripts/python.exe` confirmed interpreter
- `.claude/hooks/` + `.claude/settings.json` â€” hook scripts verified in live tests
- `06_AGENTS/Ingestion-Architecture.md` v1.0 â€” five-stage pipeline architecture
- `06_AGENTS/Knowledge-Taxonomy.md` v1.0 â€” six knowledge classes, frontmatter schema, generated-ideas layer (Phase 6C)
- `05_TEMPLATES/Generated-Idea-Template.md` â€” template for AI-generated/human+AI ideas (Phase 6C)
- Ingestion pipeline proven with real inputs: Digest + NotebookLM + Transcript â†’ Source/Synthesis notes (Phase 6B)

Note: `SOUL.md` naming is correct â€” single extension confirmed.

---

## 17. Knowledge Taxonomy

ChaseOS classifies all knowledge in the vault by origin, trust tier, and verification status. This prevents raw research inputs, verified facts, AI-generated ideas, and canonical project state from being conflated.

**The six knowledge classes:**

| Class | Meaning | Trust |
|-------|---------|-------|
| `user-origin` | Authored or explicitly endorsed by the user | High |
| `source-derived` | Processed from a single outside source | Tier 3 |
| `synthesized` | Combined from multiple sources or platform synthesis | Tier 3 |
| `generated-ideas` | AI-generated or human+AI hypotheses, theses, proposals | Tier 3 â€” not canonical without endorsement |
| `system-operational` | Framework SOPs, policies, templates, runtime logic | Tier 2 |
| `canonical-state` | Active project truth, sprint focus, roadmap state | High |

**Generated ideas layer:** AI-generated ideas are captured in `02_KNOWLEDGE/[Domain]/` using the Generated-Idea-Template. They carry `endorsement_status: unendorsed` by default and must not be treated as verified facts or cited in project state files until explicitly endorsed by the user.

**Canonical reference:** `06_AGENTS/Knowledge-Taxonomy.md` v1.0

---

## 18. ChaseOS Vocabulary

Core terms for working with the system. These have precise meanings in ChaseOS â€” conflating them is the main source of confusion about trust levels and content types.

| Term | Architectural meaning |
|------|-----------------------|
| **Raw input** | Unprocessed external content in `03_INPUTS/`; Tier 4 by default; not trusted until triaged and sanitized |
| **Source note** | Structured note processed from a single external source; `knowledge_class: source-derived`; Tier 3 |
| **Synthesis note** | Structured note combining multiple sources or platform synthesis output; `knowledge_class: synthesized`; Tier 3 |
| **Idea Generation** | AI-generated or human+AI hypothesis, thesis, or proposal; `knowledge_class: generated-ideas`; not canonical until explicitly endorsed by the user |
| **Canonical state** | Active, verified project truth: `Now.md`, project OS files, `ROADMAP.md`; authoritative for current sprint; `knowledge_class: canonical-state` |
| **Knowledge class** | Frontmatter field on every knowledge note classifying origin, trust, and verification status |
| **Promotion** | Moving content through the ingestion gate from `03_INPUTS/` into `02_KNOWLEDGE/`; requires four gate conditions; always human-approved |
| **Trust tier** | Authority ceiling for a content source or agent surface: Tier 4 = untrusted external, Tier 3 = research input, Tier 2 = execution harness, Tier 1 = owner |
| **The Gate** | ChaseOS enforcement control layer: hook scripts + adapter manifests + runtime policy files; enforces permission rules at tool-call level, independent of instruction-following |
| **Domain** | One of ChaseOS's 18 named knowledge areas; each has a knowledge index file in `02_KNOWLEDGE/[Domain]/` and a corresponding project OS file in `01_PROJECTS/` |

Full taxonomy, frontmatter schema, and generated-ideas rules: `06_AGENTS/Knowledge-Taxonomy.md`

---

## 19. Source Intelligence Core â€” Architecture

*All 7 passes complete (2026-03-26): source packages, workspace management, index contract + embedding state, local retrieval + evidence packets, output generation (9 types, Anthropic adapter), output persistence (workspace-local), and real embedding backends (LocalWordEmbedder, OpenAIEmbedder, registry, benchmark). All five layers are architecturally defined and implemented.*

The Source Intelligence Core (SIC) is ChaseOS's self-hosted intelligence layer. It replaces the dependency on external platforms (NotebookLM, Perplexity) as primary intelligence surfaces.

### Design principle: local-first and provider-pluggable

User data stays in the user's system:
- Source files stay local
- Source packages stay local
- Indexes and embeddings stay local
- Workspace objects stay local
- Generated outputs write to the local vault
- Model execution goes through a user-supplied provider connection or local runtime

ChaseOS owns the orchestration and data model. The provider adapter supplies generation and embeddings only.

### Five layers

**1. Source Package Layer**
Universal intake object for any source type:
- `source_id`, `source_type`, `title`, `origin` (URL, file path, platform)
- `raw_text` â€” full extracted content
- `chunks` â€” sectioned/chunked representation for retrieval
- `metadata` â€” timestamps, page refs, author, speaker
- `trust` â€” tier + `verified_status`
- `workspace_id` â€” workspace assignment

Source types in scope: PDF, webpage, transcript, pasted text, audio transcript, local doc, exported note, digest, API response.

**2. Workspace / Notebook Layer**
A workspace groups source packages around a coherent topic, project, course, research question, or investigation. Each workspace has:
- A name, topic, and description
- An ordered or tagged set of source packages
- A context note (what is this workspace for, what questions to answer)
- Output history (previous generated outputs from this workspace)

Workspace operations: summarize, extract key concepts, generate FAQ, compare sources, propose ideas, build study guide, create thesis, open-ended Q&A with retrieval.

**3. Retrieval / Evidence Layer**
The evidence engine. Prevents generic summarization; produces grounded outputs:
- Chunk source packages at section or paragraph level
- Embed chunks (using provider adapter embeddings)
- Store index locally
- For any workspace query: retrieve relevant chunks â†’ attach as evidence â†’ generate output with citations

**4. Output Generation Layer**
Structured outputs generated over a workspace with evidence grounding:
- Source summary (per source or per workspace)
- FAQ (question + sourced answer)
- Briefing document (structured executive summary)
- Timeline (chronological synthesis)
- Study guide (organized learning material)
- Comparison note (structured differences across sources)
- Idea Generation note (hypothesis/thesis; carries `knowledge_class: generated-ideas`)
- Synthesis note draft (multi-source synthesis ready for taxonomy-governed promotion)

**5. Provider Adapter Layer**
Pluggable model backend. Adapters:
- Claude / Anthropic (default for current Anthropic lane)
- OpenAI / Codex
- Local model (Ollama or equivalent)
- Future: others

Each adapter provides: generation, embeddings, optional transcription, optional tool access. The adapter does NOT define workspace logic, source schema, or writeback rules. Those belong to ChaseOS.

### Connection to existing Gate and taxonomy

SIC outputs are not canonical until processed through the standard ingestion gate:
- Source summaries â†’ `02_KNOWLEDGE/` as source notes (`knowledge_class: source-derived`)
- Multi-source synthesis outputs â†’ synthesis notes (`knowledge_class: synthesized`)
- Idea Generation notes â†’ `knowledge_class: generated-ideas`; endorsement required before promotion to canonical state
- All writeback through `ingestion_promotion_guard` â€” standard Gate rules apply

---

*Graph links: [[README]] Â· [[ROADMAP]] Â· [[CLAUDE]] Â· [[Operating-System]] Â· [[Assistant-Contract]] Â· [[06_AGENTS/Agent-Output-Conventions|Agent-Output-Conventions]] Â· [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] Â· [[06_AGENTS/Backends-Supported|Backends-Supported]] Â· [[06_AGENTS/Knowledge-Taxonomy|Knowledge-Taxonomy]] Â· [[Agent-Memory-Architecture]] Â· [[Feature-Register]] Â· [[Scheduled-Briefing-Pipelines]] Â· [[06_AGENTS/Autonomous-Operator-Runtime|Autonomous-Operator-Runtime]] Â· [[06_AGENTS/SIC-Architecture|SIC-Architecture]] Â· [[Markdown-to-Standalone-Bridge]] Â· [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] Â· [[ChaseOS-Approval-Center]]*

*2026-04-23 update: Acquisition + Normalization Layer added as named Phase 9 architecture family; canonical packet lives in `06_AGENTS/Acquisition-Normalization-Layer.md` and companion docs; Pass 1A generic substrate active under `runtime/acquisition/` with a StrikeZone fixture and 24 focused tests passing.*

*2026-04-27 update: OpenAI / Responses API / Runtime MCP / n8n adapter foundation added as Phase 9 shadow/dry-run infrastructure. `openai_operator_research_shadow` runs through AOR in tests and writes draft/audit artifacts only; Responses MCP payload and n8n call builders are dry-run only; Runtime MCP gained ChaseOS-named safe aliases; no live OpenAI, remote MCP, n8n, Discord, trading, wallet/exchange, or canonical writeback authority was enabled.*

*2026-05-07 update: Phase 10Y typed graph/trust overlays are complete/read-only/verified. `runtime/studio/graph_visual_model.py`, `runtime/studio/graph_visual_overlays.py`, graph-view/static-renderer/shell/API wiring, `chaseos studio graph-visual-overlays`, QA runner coverage, CLI contract/docs, and focused/broad shell tests now expose 14 node families, 4 edge layers, 8 trust states, generated/canonical distinction, filter/legend data, and read-only overlay summaries. Phase 10Z later completed read-only graph provenance inspection. Controlled graph writes, persisted graph engine/node-ID writes, import/setup, runtime/adapter activation, provider/connector calls, Gate/Agent Bus/Git/workflow mutation, and canonical writeback remain unbuilt or deferred.*

*2026-05-07 update: Phase 10Z graph provenance inspector is complete/read-only/verified. `runtime/studio/graph_provenance_inspector.py`, StudioAPI `get_graph_node_provenance`, the Node Inspector provenance tab, CLI `chaseos studio graph-provenance-inspector`, QA runner surface `graph-provenance-inspector`, CLI contract/docs, focused graph tests, static QA, product-hardening QA, generated docs check, and full shell suite now expose graph-node to sidecar/capture/quarantine/promotion/generated-canonical/dedup/audit chain inspection. Missing and malformed sidecars are tolerated as explicit states. Controlled graph writes, provenance writeback, trust promotion, persisted graph engine/node-ID writes, import/setup, runtime/adapter activation, provider/connector calls, Gate/Agent Bus/Git/workflow mutation, host/release mutation, and canonical writeback remain unbuilt or deferred. Next marker: `phase10aa-controlled-node-create-edit`.*

*2026-05-07 update: Phase 10AB visual link approval flow is complete/approval-gated/verified. `runtime/studio/visual_link_approval.py`, StudioAPI `preview_visual_link`, approval-gated `create_link`, `get_visual_link_overlay`, graph context-menu/Shift-drag proposal UX, bounded non-canonical pending edge overlays, CLI `chaseos studio visual-link-approval-flow`, QA runner surface `visual-link-approval-flow`, focused tests, static QA, and split broad verification now expose visual link proposals without duplicating or persisting the full graph payload. Link writes can occur only after `StudioService` approval execution; persisted graph engine/node-ID writes, provenance writeback, trust promotion, import/setup, runtime/adapter activation, provider/connector calls, Gate/Agent Bus/Git/workflow mutation, host/release mutation, and canonical graph/trust writeback remain unbuilt or deferred. It historically advanced to `phase10ac-runtime-cockpit-action-readiness`, which is now complete.*

*2026-05-07 update: Phase 10AC Runtime Cockpit action readiness is complete/approval-gated/verified. `runtime/studio/runtime_cockpit_action_readiness.py`, Runtime Cockpit panel/API/registry/frontend wiring, CLI `chaseos studio runtime-cockpit-action-readiness`, QA runner surface `runtime-cockpit-action-readiness`, focused tests, static no-write QA, and split broad Studio/CLI/runtime verification now expose requestable startup-surface readiness and blocked runtime/provider/Agent Bus action posture. Requestable actions queue approval packets only; start/stop/restart, lifecycle execution, host mutation, provider/connector calls, Agent Bus task writes, workflow execution, Gate mutation, release mutation, and canonical writeback remain unbuilt or deferred. Next marker: `phase10f1-open-folder-compatibility-readiness`.*

*2026-05-08 update: Phase 10F2 Obsidian vault detection is complete/read-only/verified. `runtime/studio/obsidian_vault_detection.py`, StudioAPI `get_obsidian_vault_detection`, Workspace Entry and Open Folder scan embedding, CLI `chaseos studio obsidian-vault-detection`, QA runner surface `obsidian-vault-detection`, CLI contract/docs, focused tests, and broad Studio/CLI/runtime verification now expose bounded `.obsidian` config, plugin, canvas, attachment, alias, wikilink, embed, malformed-frontmatter, truncation, and migration-risk detection. The pass writes no `.obsidian` config, activates no plugins, builds/persists no graph, creates no approval artifacts, and performs no migration/upgrade execution, provider/connector call, Agent Bus task write, Gate/Git/workflow/host/release mutation, or canonical writeback. Next marker: `phase10f3-general-markdown-inference-preview`.*

*2026-05-08 update: Phase 10F3 general Markdown inference preview is complete/read-only/verified. `runtime/studio/general_markdown_inference_preview.py`, StudioAPI `get_general_markdown_inference_preview`, Workspace Entry and Open Folder scan embedding, CLI `chaseos studio general-markdown-inference-preview`, QA runner surface `general-markdown-inference-preview`, CLI contract/docs, focused tests, and broad Studio/CLI/runtime verification now compose 10F1 readiness, 10F2 Obsidian detection, and 10X parser-backed graph input into non-canonical candidate node/edge/domain/trust-default summaries plus migration warnings. The pass writes no selected folder/vault/source files, sidecar hints, graph index, node IDs, approval artifacts, migration/upgrade executor output, provider/connector calls, Agent Bus tasks, Gate/Git/workflow/host/release mutation, or canonical writeback. Next marker: `phase10f4-chaseos-bootstrap-wizard-preview`.*

*2026-05-08 update: Phase 10F4 ChaseOS bootstrap wizard preview is complete/read-only/verified. `runtime/studio/chaseos_bootstrap_wizard_preview.py`, StudioAPI `get_chaseos_bootstrap_wizard_preview`, Workspace Entry and Open Folder scan embedding, CLI `chaseos studio chaseos-bootstrap-wizard-preview`, QA runner surface `chaseos-bootstrap-wizard-preview`, CLI contract/docs, focused tests, and broad Studio/CLI/runtime verification now preview target folders/files, bootstrap steps, scaffold brain draft posture, and future approval/execution requirements. Bounded draft-only `chaseos scaffold brain` is registered for scaffold artifacts, but Studio preview does not invoke it. The pass writes no target folders/files, scaffold artifacts from preview, approval artifacts, migration/upgrade executor output, provider/connector calls, Agent Bus tasks, Gate/Git/workflow/host/release mutation, or canonical writeback. Next marker: `phase10f5-upgrade-plan-approval-packet`.*

*2026-05-08 update: Phase 10F5/10F6 workspace upgrade approval and proof chain is complete/proof-temp verified. `runtime/studio/upgrade_plan_approval_packet.py`, `runtime/studio/approved_upgrade_execution_proof.py`, StudioAPI/Workspace Entry/[[ChaseOS-Approval-Center|Approval Center]] wiring, CLI `chaseos studio upgrade-plan-approval-packet`, CLI `chaseos studio approved-upgrade-execution-proof`, QA runner surfaces, CLI contract/docs, focused tests, mounted shell tests, and broad Studio/CLI/runtime verification now produce an explicit approval packet for the current workspace upgrade plan and consume it exactly once in proof-temp execution. Approval packet `workspace-upgrade-appr-383c66ea3196193a` was written and consumed; the exact-once marker was reserved before proof outputs; duplicate execution blocks before writes. The pass writes no real target folders/files, executes no scaffold against the live vault, performs no Git/Gate/Agent Bus/provider/connector/host/release/workflow mutation, and does not promote canonical state. Next marker: `phase11-chat-approval-handoff-queue-contract`.*

*2026-05-11 update, amended 2026-05-12: Studio MVP closure is PARTIAL / NOT FULLY CLOSED. The verified native shell, graph/trust/provenance/readiness surfaces, approval-gated create/edit/link/request flows, proof-temp workspace upgrade approval/execution, Phase 11 Chat readiness surfaces, native packaged visual QA, product hardening, installer plan, release-readiness governance, installer-build approval artifact write, approval-consumption dry run, and approved installer-build execution proof now establish a governed portable ZIP proof lane. Current Pass 10B packaged visual QA is verified on a vault-local executable using explicit external WebView2/temp runtime dirs. 2026-05-12 follow-up truth: installer-build packet `studio-installer-build-appr-ac14811da651baec` has been consumed exactly once by approved execution; marker `07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-ac14811da651baec.json`, ZIP `.pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip`, manifest, pre/post-output audits, dry-run evidence, execution evidence, and post-execution completion audit are present. Duplicate execution blocks. This was a `zip-portable` proof only: no branded logo/icon asset, install wizard, shortcut, signing, startup/autostart, registry, release promotion, host mutation, provider/connector call, Agent Bus write, Gate/Git/workflow mutation, or canonical writeback occurred. Remaining closure blockers are exact-once approval execution for important Chat/Studio target effects, real provider/runtime/browser execution or explicit deferral, real target workspace upgrade/migration or explicit deferral, branded installer/logo/icon packaging, and governed signing/startup/release/host mutation follow-through.*

*2026-05-11 update: ChaseOS VentureOps advanced to PARTIAL / LIVE CLIENT SCOPE CONTRACT VERIFIED / REAL CLIENT INPUT REQUIRED / NO LIVE CLIENT RUN / NO LIVE EXTERNAL DELIVERY. Codex added local live client scope contract output to `agent_runtime_governance_audit`, verified it with TDD, and ran the bounded AOR workflow against the synthetic client fixture. The latest internal AOR run wrote the seventeen-artifact chain under `07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-scope-contract*`, including proof, report, scorecard, offer packet, client scope, delivery approval contract, delivery packet preview, approval request JSON, approval consumption JSON, exact-once gate JSON, delivery gate marker JSON, external-send dry-run JSON, approved external-send JSON, CRM draft JSON, payment/invoice draft JSON, Workflow Exchange publication preview JSON, and live client scope contract JSON. No live client run, live client data ingestion, marketplace publication, payment mutation, CRM mutation, provider call, browser action, live external client delivery, client workflow, or live revenue workflow authority was added. Next required input: explicit real client-approved scope evidence.*

*2026-05-13 update: VentureOps pass 7 is now complete for one scoped local live-client workflow proof. The current MVP gate discovers the approved internal ChaseOS scope evidence and valid live-client workflow proof artifact. This does not authorize or prove live revenue, external delivery, CRM/payment mutation, provider/browser execution, marketplace publication, or canonical promotion.*

*PROJECT_FOUNDATION.md is an architectural truth document. Update it when significant architecture decisions are made, when implementation reality diverges from what is documented here, or when the project direction changes materially.*

*Version: 1.0 | Created: 2026-03-19 | Updated: 2026-03-20 (Phase 4 â€” Section 7 rewritten; Section 16 updated) | Updated: 2026-03-20 (Phase 6 preflight â€” Sections 3, 14, 16) | Updated: 2026-03-21 (Gate verification â€” Section 9: writeback doctrine) | Updated: 2026-03-21 (Gate micropass â€” Section 3: ACTIVE VERIFIED) | Updated: 2026-03-21 (Phase 6C â€” Sections 14, 16 stale language fixed; Section 17: Knowledge Taxonomy added) | Updated: 2026-03-21 (Phase 6C delta â€” Section 3: Current System State + subheadings; Section 18: ChaseOS Vocabulary added) | Updated: 2026-03-21 (Scope reset â€” Section 1: local-first SIOS identity + why-scope-changed note; Section 4: SIC + future phases; Section 14: Phase 7 architecture boundaries; Section 16: Phase 6D complete + scope reset; Section 19: Source Intelligence Core architecture declared) | Updated: 2026-03-23 (Architecture doctrine pass â€” Section 4: AOR + SBP detailed; Section 9: memory architecture reference added; Sections 9a + 9b: provenance + workspace-local vs durable added; Section 16: Phase 7 engineering active) | Updated: 2026-03-23 (Truth-sync pass â€” Section 3: current system state fully updated to Phase 7 active + SIC passes listed; Section 4: SIC header corrected to active engineering; Section 14: rewritten for current reality â€” stale Phase 7 architecture-pass language removed; local retrieval pass = next step; embedding provider as optional upgrade clarified; Execution Repair Memory + Agent Identity Ledger listed as Phase 9 planned)*

**Last updated:** 2026-05-13

**2026-06-02 update:** Terminal Workbench + ChaserAgent + Studio expansion is now scoped as a Phase 9/10 bridge from `06_AGENTS/ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2.md`. Architecture docs and feature matrix were added for ChaserAgent, Terminal Workbench, and Session Export/Artifacts. Implementation evidence is limited to a PARTIAL TerminalAdapter foothold for bounded read-only subprocess execution under `runtime/operator_surface/adapters/terminal_adapter.py`, with policy at `runtime/operator_surface/policies/terminal.yaml` and focused verification passing (`python -m pytest runtime/operator_surface/tests/test_terminal_adapter.py`, 6 passed). ChaserAgent runtime code, `runtime/chaser/`, `board.py`, Terminal Workbench UI, CLI terminal operation, and general session export/artifact hub remain planned.
**Status:** Phase 9 ACTIVE — Pass 4 (bounded first-wave workflow completion) COMPLETE 2026-04-09: `operator_today`, `operator_close_day`, `graph_hygiene`, and `graduate_ideas` now run end-to-end through the real AOR path; `graph_hygiene` and `graduate_ideas` are proposal-only. Graph Substrate Passes 1+2 COMPLETE 2026-04-10. Architecture Pass COMPLETE 2026-04-14 (Operator-Briefing-Architecture.md, Scheduling-Intent-Architecture.md, ChaseOS-MCP-Server.md). **OpenClaw LIVE 2026-04-15** — OpenClaw installed and operational; Discord delivery operational; scheduled execution proven through OpenClaw cron/control plane. **Discord Control Plane SPEC 2026-04-20** — `06_AGENTS/ChaseOS-Discord-Control-Plane.md` defines Discord as shared transport, not authority. **Native Schedule Layer BUILT 2026-04-15** — `runtime/schedules/` is live: `loader.py`, 2 canonical schedule intent files (`sch-operator-today-0700`, `sch-operator-close-day-1900`), `chaseos schedule list/show/enable/disable/validate` CLI, state change log; ChaseOS now owns schedule intent as canonical state; execution still happens through OpenClaw (reads ChaseOS intent, invokes `chaseos run`). **Acquisition + Normalization Architecture + Pass 1A COMPLETE 2026-04-23** — named Phase 9 bridge layer defined for governed acquisition, source-pack normalization, provenance/trust/freshness/outcome contracts, runtime responsibility, and StrikeZone pilot scope; generic substrate now validates acquisition plans, builds first-wave `source_packet`, `normalized_source_pack`, and `briefing_ready_input_set` artifacts, and writes only bounded non-canonical runtime pack outputs. Phase 8 COMPLETE (2026-03-31) — all 10 passes; 485 tests. Phase 7 (SIC) COMPLETE — all 7 passes done 2026-03-26.
