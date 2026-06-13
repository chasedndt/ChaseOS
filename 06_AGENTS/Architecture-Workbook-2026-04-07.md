---
title: ChaseOS Architecture Workbook — R&D Truth Extraction
type: architecture-reference
status: active
version: 1.0
created: 2026-04-07
updated: 2026-04-07
phase: Phase 9 — Operator Runtime (active)
knowledge_class: canonical-state
---

# ChaseOS Architecture Workbook — R&D Truth Extraction

> Evidence-based extraction of current ChaseOS architecture layers, feature implementation status, contradictions, and spreadsheet-ready reference tables.
> Basis: live repo files read 2026-04-07. Feature status is judged from file presence in the repo, not from doc claims alone.
> This is a point-in-time snapshot. Verify against current code before acting on specific claims.

---

## 1. REAL ARCHITECTURE LAYERS

Derived from folder structure, implemented code, `.claude/` hooks, and `runtime/policy/`. Layers are ordered by data flow (external content → internal state → execution → interface). No invented categories.

| # | Layer Name | What It Is | Primary Proof Location |
|---|-----------|-----------|----------------------|
| 1 | **Foundation / Vault Structure** | Folder hierarchy, naming conventions, Obsidian-native markdown substrate. The physical skeleton everything else builds on. | `00_HOME/`–`99_ARCHIVE/` directories; `CLAUDE.md`, `Vault-Map.md` |
| 2 | **Governance & Identity** | SOPs, templates, personal doctrine, agent contracts, session discipline, build log protocol. Rules the system runs on. | `04_SOPS/`, `05_TEMPLATES/`, `SOUL.md`, `00_HOME/Assistant-Contract.md`, `00_HOME/Principles.md` |
| 3 | **Agent Control Plane** | Permission matrix, trust tiers, agent registry, execution adapter standard, backends matrix, security model. Who can do what, at what trust level, on which surface. | `06_AGENTS/Agent-Control-Plane.md`, `Permission-Matrix.md`, `Trust-Tiers.md`, `Agent-Registry.md`, `Execution-Adapter-Standard.md`, `Backends-Supported.md` |
| 4 | **Gate / Mechanical Enforcement** | Hook scripts enforcing protected-file writes and ingestion promotion guard at tool-call level. Policy YAML files. Adapter manifests. Anthropic lane only — other lanes are doc-only. | `.claude/hooks/` (4 scripts), `runtime/policy/` (YAML files), `.claude/settings.json` |
| 5 | **Memory & Knowledge** | Six-class knowledge taxonomy, 18-domain knowledge base, project OS files, domain index files, context routing rules. The vault's epistemology. | `02_KNOWLEDGE/`, `01_PROJECTS/`, `06_AGENTS/Knowledge-Taxonomy.md`, `06_AGENTS/Vault-Map.md` |
| 6 | **Ingestion Pipeline** | Five-stage quarantine-to-promotion pipeline (Capture → Triage → Sanitize → Route/Promote → Memory Curation). Physical quarantine boundary. Sidecar provenance. Dedup registry. | `03_INPUTS/00_QUARANTINE/`, `runtime/capture/content_packet.py`, `intake_writer.py`, `router.py`, `dedup_registry.py`, `06_AGENTS/Ingestion-Architecture.md` |
| 7 | **Source Intelligence Core (SIC)** | Local-first intelligence layer: source packages, workspaces, embedding backends, retrieval, structured output generation, output persistence. Post-promotion reasoning layer. | `runtime/source_intelligence/pipelines/`, `workspaces/`, `indexes/`, `retrieval/`, `output/` |
| 8 | **Connector / Capture Automation** | Operator CLI (`chaseos`/`chase`) plus five connectors (CLI, RSS, browser/HTML, Perplexity API, Grok API) and watched-folder automation. Drives content into the ingestion pipeline. | `runtime/capture/connectors/`, `runtime/cli/main.py`, `pyproject.toml` |
| 9 | **AOR Foundation (partial)** | 8-stage bounded execution pipeline, workflow registry, role cards, task-type router, task-type table. Handlers are scaffolded but not implemented. Workflow manifests exist as `status=draft`. | `runtime/aor/engine.py`, `registry.py`, `role_cards.py`, `task_router.py`, `task_type_table.yaml`; `runtime/workflows/registry/` (4 manifests); `06_AGENTS/role-cards/` (2 cards) |
| 10 | **Institutional Memory / Audit** | Decision Ledger (immutable records), Pivot Log, build logs, agent activity audit JSONs (written by AOR engine). Durable trace of decisions and executions. | `07_LOGS/Decision-Ledger/` (3 entries), `07_LOGS/Pivot-Log/`, `07_LOGS/Build-Logs/` (55+ entries), `07_LOGS/Agent-Activity/` |
| 11 | **Interface / Experience** | Full GUI/TUI, workspace browser, approval surfaces, provenance inspector. Not built. Phase 10 only. | No runtime files — docs only in `06_AGENTS/Feature-Fit-Register.md` |

---

## 2. FEATURE TRUTH TABLE

**Classification:**
- **Implemented** = code exists and runs; tests pass
- **Partial** = scaffolded or spec complete; some components missing
- **Adopted / Docs Only** = architecture doc exists; no runtime code written
- **Idea Only** = mentioned in docs but no architecture doc and no code
- **Stale / Contradicted** = claim in docs contradicts repo state

---

### 2A — Foundation

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| 18-domain folder hierarchy | Implemented | Foundation | Stable skeleton | Content navigability | All layers | `00_HOME/`–`99_ARCHIVE/` | `Vault-Map.md` | |
| Naming conventions | Implemented | Foundation | Deterministic file discovery | Agent navigation | Gate, Ingestion | `07_LOGS/Build-Logs/` (applied) | `CLAUDE.md` | |
| `CLAUDE.md` routing anchor | Implemented | Foundation | Claude Code session contract | Prevents context overload | Gate, Agent Control | `CLAUDE.md` v2.0 | `Agent-Control-Plane.md` | |
| Execution adapter docs (non-Anthropic) | Partial | Foundation | Multi-backend conformance | Framework portability | Agent Control, Gate | `OPENAI.md`, `LOCAL-OSS.md`, `N8N.md` | `Execution-Adapter-Standard.md` | Docs only; no enforcement wired — see Contradiction C9 |
| Core/Personal directory split | Idea Only | Foundation | Forkability | Framework portability | Foundation | None | `FORKING.md` | Conceptual only; mixed-layer content throughout |

---

### 2B — Governance & Identity

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| Build Log SOP + discipline | Implemented | Governance | Writeback accountability | Output persistence | Foundation, Audit | `07_LOGS/Build-Logs/` (55+ entries), `04_SOPS/Build-Log-SOP.md` | `CLAUDE.md` | 55+ build logs written |
| Research Ingest SOP | Implemented | Governance | Quarantine discipline for external content | Injection prevention | Ingestion | `04_SOPS/Research-Ingest-SOP.md` v2.1 | `Ingestion-Architecture.md` | Includes injection section |
| SOPs (full set, 8 files) | Implemented | Governance | Structured handling for every session type | Reduces variability | All layers | `04_SOPS/` | `Vault-Map.md` | |
| Templates (full set, 15+) | Implemented | Governance | Consistent note creation | Format consistency | All layers | `05_TEMPLATES/` | `Vault-Map.md` | Includes Phase 9 templates |
| Feature Filter SOP | Implemented | Governance | Prevent roadmap scope creep | Formal 6-question gate before feature adoption | AOR, Feature-Fit-Register | `04_SOPS/Feature-Filter-SOP.md`, `05_TEMPLATES/Feature-Filter-Template.md` | `Feature-Fit-Register.md` | Phase 9 Pass 1 — see Contradiction C1 |
| Promotion-Session SOP | Implemented | Governance | Structured knowledge promotion | Prevents ad hoc promotion | Ingestion, Gate | `04_SOPS/Promotion-Session-SOP.md` | `Ingestion-Architecture.md` | |
| Ingestion Cadence SOP | Implemented | Governance | Daily/weekly ingestion rhythm | Prevents backlog | Ingestion | `04_SOPS/Ingestion-Cadence.md` | | |
| SOUL.md identity layer | Implemented | Governance | Agent behavioral alignment | Cross-session consistency | Agent Control | `SOUL.md` | `Assistant-Contract.md` | Protected file |
| Principles.md doctrine | Implemented | Governance | Decision doctrine for ambiguous choices | Reduces agent guesswork | Governance | `00_HOME/Principles.md` | `SOUL.md` | Protected file |
| Assistant-Contract.md | Implemented | Governance | Binding agent behavior rules | Consistent across all agent types | Agent Control | `00_HOME/Assistant-Contract.md` v2.0 | `Agent-Control-Plane.md` | |

---

### 2C — Agent Control Plane

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| Agent Control Plane | Implemented | Agent Control | Central governance anchor | Single source of truth | Permission Matrix, Trust Tiers | `06_AGENTS/Agent-Control-Plane.md` | `CLAUDE.md` | v1.1 |
| Permission Matrix | Implemented | Agent Control | Explicit per-surface, per-action permissions | Prevents ambient access | Trust Tiers, Gate | `06_AGENTS/Permission-Matrix.md` | `Agent-Control-Plane.md` | Canonical protected-file source |
| Trust Tiers (1–4) | Implemented | Agent Control | Authority ceiling model | Prevents trust escalation | Permission Matrix | `06_AGENTS/Trust-Tiers.md` v1.1 | `Agent-Control-Plane.md` | Tiers as ceilings, not capability bundles |
| Agent Registry | Implemented | Agent Control | Enumerate all agents | Auditable inventory | Trust Tiers | `06_AGENTS/Agent-Registry.md` v3.1 | `Execution-Adapter-Standard.md` | |
| Handoff Protocol | Implemented | Agent Control | Session start/close discipline | Cross-session continuity | Memory | `06_AGENTS/Handoff-Protocol.md` | `CLAUDE.md` | |
| Agent Security Model | Implemented | Agent Control | 8-attack-class threat model | Fail-closed security baseline | Gate, Trust Tiers | `06_AGENTS/Agent-Security-Model.md` | `Agent-Control-Plane.md` | |
| Execution Adapter Standard | Implemented | Agent Control | 4 adapter classes, 11 required sections | Framework portability | Backends, Adapters | `06_AGENTS/Execution-Adapter-Standard.md` v1.0 | `Backends-Supported.md` | |
| Subagent Patterns | Implemented | Agent Control | Permission inheritance rules | Prevents escalation via delegation | Trust Tiers | `06_AGENTS/Subagent-Patterns.md` | | Phase 5B |
| Hook Patterns | Implemented | Agent Control | Session-open/close hook design | Structural discipline | Gate | `06_AGENTS/Hook-Patterns.md` | `CLAUDE.md` | Phase 5B |
| Claude Memory System | Implemented | Agent Control | Rules for `~/.claude/` memory | Prevents stale memory contamination | Context Routing | `06_AGENTS/Claude-Memory-System.md` | `Hook-Patterns.md` | Memory seeded with 3 entries |
| Backends Supported Matrix | Implemented | Agent Control | Provider/surface/access-mode matrix | Prevents runtime confusion | Execution Adapter Standard | `06_AGENTS/Backends-Supported.md` v1.1 | | |

---

### 2D — Gate / Enforcement

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| Protected-write guard hook | Implemented | Gate | Block writes to protected files | Mechanical Permission Matrix enforcement | Permission Matrix | `.claude/hooks/protected_write_guard.py` | `ChaseOS-Gate.md` | VERIFIED; Anthropic lane only |
| Ingestion promotion guard hook | Implemented | Gate | Block promotion without `CHASEOS_PROMOTION_APPROVED=1` | Governs knowledge gate | Ingestion Pipeline | `.claude/hooks/ingestion_promotion_guard.py` | `ChaseOS-Gate.md` | VERIFIED |
| Session-start context hook | Implemented | Gate | Required context loading | Prevents cold-start errors | Handoff Protocol | `.claude/hooks/session_start_context.py` | `Hook-Patterns.md` | VERIFIED |
| Session-end audit hook | Implemented | Gate | Audit checklist at session close | Prevents silent output loss | Governance | `.claude/hooks/session_end_audit.py` | `Handoff-Protocol.md` | VERIFIED |
| Runtime policy YAML files | Implemented | Gate | Machine-readable policy | Policy-as-code, not just docs | Gate, Agent Control | `runtime/policy/protected_files.yaml`, `runtime/policy/adapters/`, `runtime/policy/tasks/` | `Adapter-Manifest-Standard.md` | 7 YAML files present |
| Gate — OpenAI/Local/n8n lanes | Adopted / Docs Only | Gate | Multi-backend policy enforcement | Provider-agnostic governance | Execution Adapter Standard | Policy YAMLs only — no hooks wired | `ChaseOS-Gate.md` | See Contradiction C9 |
| Adapter Manifest Standard | Implemented | Gate | Schema and lifecycle for adapter manifests | Uniform adapter governance | Gate, Execution Adapter Standard | `06_AGENTS/Adapter-Manifest-Standard.md`, `05_TEMPLATES/Adapter-Compliance-Checklist.md` | `ChaseOS-Gate.md` | |

---

### 2E — Memory & Knowledge

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| Six-class knowledge taxonomy | Implemented | Memory | Prevents knowledge conflation | Trust labeling | Ingestion, SIC, Gate | `06_AGENTS/Knowledge-Taxonomy.md` | `Ingestion-Architecture.md` | Mandatory `knowledge_class` frontmatter |
| Domain knowledge base (18 domains) | Implemented | Memory | Structured knowledge per domain | Domain-scoped retrieval | SIC, Context Routing | `02_KNOWLEDGE/` (11 folders) | `Vault-Map.md` | |
| Project OS files (all active domains) | Implemented | Memory | Canonical per-project state | Agent re-orientation speed | Context Routing | `01_PROJECTS/` (20+ OS files) | `Vault-Map.md` | All major active domains populated |
| Generated-Ideas layer | Partial | Memory | Separate AI hypotheses from verified knowledge | Trust separation | Knowledge Taxonomy | `02_KNOWLEDGE/[Domain]/Generated-Ideas/` (lazy creation) | `AI-Generated-Output-Bridge.md` | Dirs created on first promotion only |
| AI-Generated-Output-Bridge | Adopted / Docs Only | Memory | 4-layer (A→B→C→D) graduation path | Explicit AI output promotion flow | Knowledge Taxonomy, SIC | `06_AGENTS/AI-Generated-Output-Bridge.md` | `SIC-Architecture.md` | Layers A/B are live; C/D are manual |
| Agent Memory Architecture (5-layer) | Adopted / Docs Only | Memory | Formal model for ChaseOS memory growth | Compound operational context | All layers | `06_AGENTS/Agent-Memory-Architecture.md` | `Claude-Memory-System.md` | Layers A/B implemented; C/D/E partial or not built |

---

### 2F — Ingestion Pipeline

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| ContentPacket | Implemented | Ingestion | Connector-agnostic data container | Universal connector interface | All connectors | `runtime/capture/content_packet.py` | `Connector-Capture-Architecture.md` | |
| Router + type-first naming | Implemented | Ingestion | Deterministic quarantine filenames | Collision-free navigation | ContentPacket | `runtime/capture/router.py` | | Naming: `YYYYMMDD-HHMMSS__class__source__slug.md` |
| Intake writer + sidecar v8.3 | Implemented | Ingestion | Durable provenance per capture | Audit trail from write | Router, Dedup | `runtime/capture/intake_writer.py` | `Connector-Capture-Architecture.md` | v8.3 is current canonical schema |
| Physical quarantine boundary | Implemented | Ingestion | `03_INPUTS/00_QUARANTINE/[class]/` | Distinct from legacy content | Intake Writer | `03_INPUTS/00_QUARANTINE/` | | Legacy coexists; migration is manual |
| SHA-256 dedup registry | Implemented | Ingestion | First-capture-wins dedup | Idempotent capture runs | Capture API | `runtime/capture/dedup_registry.py` | | `.chaseos/dedup_registry.json`; fail-open |
| Semantic breadcrumb hints | Implemented | Ingestion | 6 advisory hint fields in sidecar | Assists triage; future AOR routing | Intake Writer | `runtime/capture/content_packet.py` | `Connector-Capture-Architecture.md` | Advisory only — no routing automation triggered |
| Five-stage pipeline (manual) | Implemented | Ingestion | Quarantine-to-promotion flow | Prevents contamination and evaporation | Gate, Knowledge | `03_INPUTS/`, `04_SOPS/Research-Ingest-SOP.md` | `Ingestion-Architecture.md` | Human-gated promotion; no autonomous promotion |

---

### 2G — Source Intelligence Core

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| Source Package Builder | Implemented | SIC | Normalize promoted sources | Enables workspace grouping | Workspace Manager | `runtime/source_intelligence/pipelines/source_package_builder.py` | `SIC-Architecture.md` | 4 source types; PDF deferred |
| Workspace Manager | Implemented | SIC | Group source packages | Topic-scoped retrieval | Source Packages | `runtime/source_intelligence/workspaces/workspace_manager.py` | | |
| Embedding backends | Implemented | SIC | Pluggable embeddings | Local-first; OpenAI opt-in | Index Manager | `runtime/source_intelligence/indexes/embedder.py`, `backend_registry.py`, `providers/openai_embedder.py` | `SIC-Provider-Adapter-Standard.md` | `LocalWordEmbedder` (no deps) + `OpenAIEmbedder` (opt-in) |
| Index Manager | Implemented | SIC | Build/save workspace indexes | Idempotent embedding cache | Embedding Backends | `runtime/source_intelligence/indexes/index_manager.py` | | Workspace-local |
| Retrieval + cosine similarity | Implemented | SIC | Evidence-grounded reasoning | Source-cited outputs | Index, Output | `runtime/source_intelligence/retrieval/retriever.py`, `similarity.py` | | 8 status codes; local-only for local backends |
| Output Generation Layer | Implemented | SIC | 9 output types over workspaces | AI-assisted synthesis from owned sources | Retrieval | `runtime/source_intelligence/output/generator.py`, `prompt_builder.py` | `SIC-Architecture.md` | `AnthropicGenerationAdapter` opt-in; `vault_writeback_candidate` flag |
| Output Store | Implemented | SIC | Workspace-local output persistence | Durable output without canonical write | Output Generation | `runtime/source_intelligence/output/output_store.py` | | Layer B only; explicit promotion for Layer C |
| Embedding benchmark | Implemented | SIC | Backend quality comparison | Provider selection support | Embedding Backends | `runtime/source_intelligence/retrieval/benchmark.py` | | Dev/eval only |
| SIC → Capture provenance link | Idea Only | SIC | Trace SIC output to quarantine `capture_id` | Full lineage | Ingestion, SIC | None | `Feature-Fit-Register.md` | Future Phase 8.x |
| Cross-workspace retrieval | Idea Only | SIC | Query across multiple workspaces | Broader evidence base | SIC Retrieval | None | `Feature-Fit-Register.md` | Future SIC v2 |

---

### 2H — Connector / Capture Automation

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| Operator CLI (`chaseos`/`chase`) | Implemented | Capture | Scriptable operator interface | Removes manual file-drop | All connectors | `runtime/cli/main.py`, `pyproject.toml` | | Console scripts installed via `.venv`; NOT a GUI |
| CLI connector (file/stdin) | Implemented | Capture | Local file and pipe capture | Text intake | ContentPacket | `runtime/capture/connectors/cli_connector.py` | | |
| RSS/Atom connector | Implemented | Capture | Feed capture; stdlib-only | Automated research intake | ContentPacket, Dedup | `runtime/capture/connectors/rss_connector.py` | | `chaseos capture rss URL` |
| Browser/HTML connector (local) | Implemented | Capture | HTML→markdown; title extraction | Browser-saved article capture | ContentPacket | `runtime/capture/connectors/browser_connector.py` | | Local files only in Pass 7 |
| `chaseos capture browser live URL` | Idea Only | Capture | Live URL fetch | Real-time web capture | Browser connector | None | `Feature-Fit-Register.md` | Phase 8.x future |
| Perplexity API connector | Implemented | Capture | Perplexity API; citations extraction | AI research digest capture | ContentPacket, Dedup | `runtime/capture/connectors/perplexity_connector.py` | | `PERPLEXITY_API_KEY` env var only |
| Grok/xAI API connector | Implemented | Capture | xAI Grok API; OpenAI-compat | AI digest capture (alternate) | ContentPacket, Dedup | `runtime/capture/connectors/grok_connector.py` | | `XAI_API_KEY` env var only; default model grok-3 |
| Watched-folder automation | Implemented | Capture | Polling-based folder monitor | Automatic file intake without daemon | ContentPacket, Dedup | `runtime/capture/watch_folders.py` | | No recursive scan; no OS daemon |
| Connector plugin system | Adopted / Docs Only | Capture | Drop-in connector registration | Extensibility | AOR, CLI | None | `Feature-Fit-Register.md` | Phase 9 AOR scope |
| Additional API connectors | Idea Only | Capture | More API coverage | Extended intake sources | ContentPacket | None | `Feature-Fit-Register.md` | Phase 8.x future |

---

### 2I — AOR Foundation

| Feature | Status | Layer | Why It Exists | What It Improves | Coordinates With | Proof Files | Linked Docs | Notes |
|---------|--------|-------|--------------|-----------------|-----------------|-------------|-------------|-------|
| AOR 8-stage pipeline engine | Partial | AOR | Bounded execution pipeline | Governs every workflow run | Registry, Role Cards, Task Router | `runtime/aor/engine.py` | `Autonomous-Operator-Runtime.md` | Stages 1–5 and 8 functional; Stage 6 handler dispatch is empty (`_handlers={}`); Stage 7 writeback is scaffold-only — see Contradiction C6 |
| Workflow Registry loader | Partial | AOR | Load/validate workflow manifests | Governed workflow enumeration | AOR Engine | `runtime/aor/registry.py`, `runtime/workflows/registry/` (4 YAMLs) | `Phase9-Adopted-Feature-Specification.md` | 4 manifests present (all `status=draft`); registry loader operational; no scheduler — see Contradiction C1 |
| Role Card loader | Implemented | AOR | Load/validate role cards | Per-role permission envelope | AOR Engine | `runtime/aor/role_cards.py`, `06_AGENTS/role-cards/operator-briefing.yaml`, `vault-maintenance.yaml` | | Loader fully functional; 2 cards live |
| Task-Type Router | Implemented | AOR | Classify task types; escalate unclassified | Prevents unknown tasks from running | AOR Engine | `runtime/aor/task_router.py`, `task_type_table.yaml` (9 types + sentinel) | | Unclassified sentinel enforced |
| AOR audit record writer | Implemented | AOR | Immutable JSON audit per execution | Accountability trail | AOR Engine | `runtime/aor/engine.py` (`_write_audit_record`) | | Writes to `07_LOGS/Agent-Activity/`; NOT `runtime/audit/` — see Contradiction C7 |
| Workflow manifests (4) | Partial | AOR | Declares 4 authorized workflows | Governed enumeration | Workflow Registry | `runtime/workflows/registry/*.yaml` | | All `status=draft`; manifests valid; handlers not implemented |
| operator_today handler | Adopted / Docs Only | AOR | Daily briefing execution | Structured daily brief | Workflow Registry, Role Card | None (handler dispatch empty) | `Phase9-Adopted-Feature-Specification.md` | Phase 9 Pass 2 — see Contradiction C6 |
| operator_close_day handler | Adopted / Docs Only | AOR | Session close-out | Close checklist automation | operator_today | None | | Phase 9 Pass 2 |
| graph_hygiene handler | Adopted / Docs Only | AOR | Vault entropy scan; proposals only | Vault link health | Vault-Map, Knowledge | None | | Phase 9 Pass 2+ |
| graduate_ideas handler | Adopted / Docs Only | AOR | Ideas promotion workflow | Operationalizes A→D graduation | AI-Generated-Output-Bridge | None | | Phase 9 Pass 2+ |
| Decision Ledger | Implemented | Audit | Immutable decision records | Institutional memory | AOR, Governance | `07_LOGS/Decision-Ledger/` (Index + 3 entries) | `Phase9-Adopted-Feature-Specification.md` | Misleadingly marked NOT BUILT in Feature-Fit-Register — see Contradiction C1 |
| Pivot Log | Implemented | Audit | Immutable pivot records | Scope change history | Decision Ledger | `07_LOGS/Pivot-Log/` | | |
| Scheduled Briefing Pipelines | Adopted / Docs Only | AOR | Scheduled, guardrailed briefing pattern | Replace manual briefing assembly | AOR Engine, SIC | None | `06_AGENTS/Scheduled-Briefing-Pipelines.md` | No code; first implementation (StrikeZone Market Digest) not started |
| Runtime Navigation Map | Adopted / Docs Only | AOR | Per-runtime evolving route overlay | Compounding runtime efficiency | AOR, Agent Memory | None | `06_AGENTS/Runtime-Navigation-Map.md` | No code |
| Execution Repair Memory | Adopted / Docs Only | AOR | Pattern-learning from AOR failures | Reduce repeated failure | AOR Audit | None | `06_AGENTS/Agent-Memory-Architecture.md` | No code |
| Agent Identity Ledger | Adopted / Docs Only | AOR | Per-agent identity + drift detection | Behavioral inspection | Agent Scorecards | None | `06_AGENTS/Agent-Memory-Architecture.md` | No code |
| Agent Scorecards | Adopted / Docs Only | AOR | Reliability tracking per runtime | Feeds Identity Ledger | AOR Audit, Role Cards | None | `Phase9-Adopted-Feature-Specification.md` | Second-wave |
| Context Governance Layer (CGL) | Adopted / Docs Only | AOR | Trust metadata on notes for AOR eligibility | AOR input governance | Role Cards, Knowledge Taxonomy | None | `Phase9-Adopted-Feature-Specification.md` | Second-wave |
| Provenance Schema | Adopted / Docs Only | AOR | Full lineage chain from capture to canonical | Inspectable provenance | SIC, Sidecar v8.3 | None | `Phase9-Adopted-Feature-Specification.md` | Second-wave |
| trace_idea workflow | Adopted / Docs Only | AOR | Lineage traversal of idea provenance | Full idea history | Provenance Schema | None | `Phase9-Adopted-Feature-Specification.md` | Second-wave |
| drift_scan workflow | Adopted / Docs Only | AOR | Doctrine-vs-behavior comparison | Catch AOR behavioral drift | operator_close_day, Decision Ledger | None | `Phase9-Adopted-Feature-Specification.md` | Second-wave |
| Meeting Ingest Linker | Adopted / Docs Only | AOR | Map meeting entities to vault | Enriched meeting capture | Phase 8 capture, graph_hygiene | None | `Phase9-Adopted-Feature-Specification.md` | Second-wave |
| AOR task scheduler / cron | Idea Only | AOR | Autonomous scheduled execution | Removes manual trigger | Watched Folders, AOR | None | `Feature-Fit-Register.md` | |
| MCP integration | Idea Only | AOR | External tool orchestration | ChaseOS as MCP host | AOR Engine | None | `Feature-Fit-Register.md` | |
| Multi-repo policy enforcement | Idea Only | AOR | Multi-vault AOR | Cross-vault governance | Permission Matrix | None | `Feature-Fit-Register.md` | |

---

### 2J — Interface / Experience (Phase 10)

| Feature | Status | Layer | Notes |
|---------|--------|-------|-------|
| Operator dashboard | Idea Only | Interface | Read-only system status view |
| Quarantine review UI | Idea Only | Interface | Must wire to Gate |
| Provenance inspector | Idea Only | Interface | Reads sidecar chain; no write required |
| SIC workspace browser | Idea Only | Interface | Read-only SIC view |
| AOR pipeline monitor | Idea Only | Interface | Depends on AOR audit trail |
| TUI variant | Idea Only | Interface | Requires stable CLI API (Phase 8 provides) |
| Paperclip (orchestration surface) | Idea Only | Interface | Reserved; post-Phase 10; MUST NOT bypass Gate |

---

## 3. CONTRADICTION REPORT

### C1 — Feature-Fit-Register marks Phase 9 first-wave as "NOT BUILT" but they are partially built

**Severity: Medium**

`06_AGENTS/Feature-Fit-Register.md` (v1.1, 2026-03-31) lists all Phase 9 first-wave features as `NOT BUILT`.

**Repo truth:** Phase 9 Pass 1 (2026-03-31) built concrete artifacts for all 6 governance infrastructure features:
- Workflow Registry: `runtime/workflows/registry/` + 4 manifests + `runtime/aor/registry.py`
- Agent Role Cards: `06_AGENTS/role-cards/` (2 YAML cards) + `runtime/aor/role_cards.py`
- Task-Type Router: `runtime/aor/task_router.py` + `task_type_table.yaml`
- Decision Ledger: `07_LOGS/Decision-Ledger/` (Index + 3 entries)
- Feature Filter: `04_SOPS/Feature-Filter-SOP.md` + `05_TEMPLATES/Feature-Filter-Template.md`
- Project Pivot Log: `07_LOGS/Pivot-Log/`

The 4 workflow handlers (operator_today, operator_close_day, graph_hygiene, graduate_ideas) are legitimately NOT BUILT.

**Fix needed:** Feature-Fit-Register Phase 9 table should be split into "infrastructure scaffold — PARTIAL" vs. "workflow handlers — NOT BUILT".

---

### C2 — README "What is not yet built" lists items that ARE built

**Severity: Medium**

`README.md` states: "Phase 9 first-wave features... spec complete; engineering not yet started"

**Repo truth:** Engineering has started. Phase 9 Pass 1 is complete. This section was not updated after Pass 1.

---

### C3 — Now.md footer is stale

**Severity: Low**

`Now.md` footer says "updated: 2026-03-29 | Phase 8 Pass 8 COMPLETE". Body shows Phase 9 Pass 1 COMPLETE (2026-03-31).

---

### C4 — Vault-Map.md last-updated footer vs. content

**Severity: Low**

Footer says "Updated: 2026-03-21" but content includes Phase 9 Pass 1 additions (role-cards, Decision-Ledger, Pivot-Log rows) that were added 2026-03-31. Footer was not bumped.

---

### C5 — Connector file paths: docs reference `runtime/capture/` but actual paths are `runtime/capture/connectors/`

**Severity: Low**

`CLAUDE.md` audit notes and several docs reference `rss_connector.py`, `browser_connector.py`, `perplexity_connector.py`, `grok_connector.py`, `cli_connector.py` as if in `runtime/capture/` directly.

**Repo truth:** All five connectors are in `runtime/capture/connectors/`. `watch_folders.py` and `dedup_registry.py` are correctly in `runtime/capture/`.

---

### C6 — AOR "live" claim vs. empty handlers

**Severity: Medium**

High-level claims (CLAUDE.md, Now.md) state "Phase 9 Pass 1 COMPLETE" and describe the AOR engine as live. Technically accurate but:

- `engine.py` line 243: `_handlers: dict = {}` — Stage 6 always returns `handler_status="not_yet_implemented"` for ALL workflows
- Stage 7 writeback returns `writeback_status = "scaffold_only"` for all runs
- No workflow can execute real work. Every run returns `status="success"` with empty handler result.

This is internally disclosed in engine docstrings ("handler dispatch is scaffolded — Pass 1") but high-level summaries can create false impression of executable workflows.

---

### C7 — `runtime/audit/` referenced but does not exist

**Severity: Low**

`Feature-Fit-Register.md` "Audit trail persistence" row references `runtime/audit/` as the target. The AOR engine writes audit records to `07_LOGS/Agent-Activity/`. No `runtime/audit/` directory found in repo.

---

### C8 — Semantic hint enforcement correctly documented as advisory (no contradiction)

Advisory-only semantics for sidecar hints are consistently stated across `Connector-Capture-Architecture.md`, `AI-Generated-Output-Bridge.md`, and `Feature-Fit-Register.md`. Not a contradiction — correctly noted here for completeness.

---

### C9 — Non-Anthropic adapter policy YAMLs exist but no hooks enforce them

**Severity: Medium**

`runtime/policy/adapters/openai.yaml`, `local_oss.yaml`, `n8n.yaml` exist. But no hook scripts enforce these lanes. Only Anthropic lane is verified active.

The docs correctly disclose this ("other adapter lanes documented but not yet active") but YAML file presence can imply enforcement. Already partially disclosed — no new fix needed to docs, only awareness.

---

### C10 — Phase 9 and Phase 8 test suites are separate (informational)

The 485 test count (Phase 8) and 34 test count (Phase 9 Pass 1) are from separate test files. They are not unified. Any future test count reporting should distinguish the suites.

---

## 4. SPREADSHEET-READY TABLES

### Table A — Layer_Catalog

| layer_id | layer_name | status | primary_runtime_path | primary_doc_path | phase_built | mechanical_enforcement |
|----------|-----------|--------|---------------------|-----------------|-------------|----------------------|
| L1 | Foundation / Vault Structure | Live | `00_HOME/`–`99_ARCHIVE/` | `CLAUDE.md`, `Vault-Map.md` | Phase 1 | No — convention only |
| L2 | Governance & Identity | Live | `04_SOPS/`, `05_TEMPLATES/`, `SOUL.md` | `Assistant-Contract.md`, `Build-Log-SOP.md` | Phase 2 | No — SOP + discipline |
| L3 | Agent Control Plane | Live | `06_AGENTS/*.md` | `Agent-Control-Plane.md`, `Permission-Matrix.md` | Phase 4 | No — Gate enforces |
| L4 | Gate / Enforcement (Anthropic lane) | Live | `.claude/hooks/`, `runtime/policy/` | `ChaseOS-Gate.md`, `Hook-Patterns.md` | Phase 6 | Yes — 4 hooks VERIFIED |
| L4b | Gate / Enforcement (other lanes) | Docs Only | `runtime/policy/adapters/` | `Adapter-Manifest-Standard.md` | Phase 5–6 | No — not wired |
| L5 | Memory & Knowledge | Live | `02_KNOWLEDGE/`, `01_PROJECTS/` | `Knowledge-Taxonomy.md`, `Vault-Map.md` | Phase 3/6 | Partial — frontmatter required |
| L6 | Ingestion Pipeline | Live | `runtime/capture/`, `03_INPUTS/00_QUARANTINE/` | `Ingestion-Architecture.md`, `Connector-Capture-Architecture.md` | Phase 6/8 | Partial — quarantine enforced; promotion hook enforced |
| L7 | Source Intelligence Core | Live | `runtime/source_intelligence/` | `SIC-Architecture.md` | Phase 7 | No — local-first; no hook enforcement |
| L8 | Connector / Capture Automation | Live | `runtime/capture/connectors/`, `runtime/cli/` | `Connector-Capture-Architecture.md` | Phase 8 | No — credential boundary only |
| L9 | AOR Foundation | Partial | `runtime/aor/`, `runtime/workflows/registry/`, `06_AGENTS/role-cards/` | `Autonomous-Operator-Runtime.md`, `Phase9-Adopted-Feature-Specification.md` | Phase 9 Pass 1 | Partial — pipeline enforced; handlers not built |
| L10 | Institutional Memory / Audit | Live | `07_LOGS/Decision-Ledger/`, `07_LOGS/Build-Logs/`, `07_LOGS/Agent-Activity/` | `Handoff-Protocol.md` | Phase 3+ | No — append-only discipline |
| L11 | Interface / Experience | Not Built | None | `Feature-Fit-Register.md` | Phase 10 | N/A |

---

### Table B — Feature_Register (full set)

| feature_id | feature_name | status | layer_id | proof_path | doc_path | contradiction_flag |
|-----------|-------------|--------|----------|-----------|---------|-------------------|
| F01 | 18-domain folder hierarchy | Implemented | L1 | `00_HOME/`–`99_ARCHIVE/` | `Vault-Map.md` | None |
| F02 | Naming conventions | Implemented | L1 | `07_LOGS/Build-Logs/` | `CLAUDE.md` | None |
| F03 | `CLAUDE.md` routing anchor | Implemented | L1 | `CLAUDE.md` v2.0 | `Agent-Control-Plane.md` | None |
| F04 | Execution adapter docs (non-Anthropic) | Partial | L1 | `OPENAI.md`, `LOCAL-OSS.md`, `N8N.md` | `Execution-Adapter-Standard.md` | C9 |
| F05 | Core/Personal directory split | Idea Only | L1 | None | `FORKING.md` | None |
| F06 | Build Log SOP + discipline | Implemented | L2 | `07_LOGS/Build-Logs/` (55+ entries) | `Build-Log-SOP.md` | None |
| F07 | Research Ingest SOP | Implemented | L2 | `04_SOPS/Research-Ingest-SOP.md` v2.1 | `Ingestion-Architecture.md` | None |
| F08 | Feature Filter SOP | Implemented | L2 | `04_SOPS/Feature-Filter-SOP.md` | `Feature-Fit-Register.md` | C1 |
| F09 | SOPs (full set) | Implemented | L2 | `04_SOPS/` (8 files) | `Vault-Map.md` | None |
| F10 | Templates (full set) | Implemented | L2 | `05_TEMPLATES/` (15+ files) | `Vault-Map.md` | None |
| F11 | Agent Control Plane | Implemented | L3 | `06_AGENTS/Agent-Control-Plane.md` | `CLAUDE.md` | None |
| F12 | Permission Matrix | Implemented | L3 | `06_AGENTS/Permission-Matrix.md` | `Agent-Control-Plane.md` | None |
| F13 | Trust Tiers | Implemented | L3 | `06_AGENTS/Trust-Tiers.md` | `Agent-Control-Plane.md` | None |
| F14 | Agent Registry | Implemented | L3 | `06_AGENTS/Agent-Registry.md` v3.1 | `Execution-Adapter-Standard.md` | None |
| F15 | Handoff Protocol | Implemented | L3 | `06_AGENTS/Handoff-Protocol.md` | `CLAUDE.md` | None |
| F16 | Agent Security Model | Implemented | L3 | `06_AGENTS/Agent-Security-Model.md` | `Agent-Control-Plane.md` | None |
| F17 | Execution Adapter Standard | Implemented | L3 | `06_AGENTS/Execution-Adapter-Standard.md` | `Backends-Supported.md` | None |
| F18 | Protected-write guard hook | Implemented | L4 | `.claude/hooks/protected_write_guard.py` | `ChaseOS-Gate.md` | None |
| F19 | Ingestion promotion guard hook | Implemented | L4 | `.claude/hooks/ingestion_promotion_guard.py` | `ChaseOS-Gate.md` | None |
| F20 | Session-start context hook | Implemented | L4 | `.claude/hooks/session_start_context.py` | `Hook-Patterns.md` | None |
| F21 | Session-end audit hook | Implemented | L4 | `.claude/hooks/session_end_audit.py` | `Handoff-Protocol.md` | None |
| F22 | Gate — non-Anthropic lanes | Adopted / Docs Only | L4 | `runtime/policy/adapters/*.yaml` | `ChaseOS-Gate.md` | C9 |
| F23 | Six-class knowledge taxonomy | Implemented | L5 | `06_AGENTS/Knowledge-Taxonomy.md` | `Ingestion-Architecture.md` | None |
| F24 | Domain knowledge base | Implemented | L5 | `02_KNOWLEDGE/` | `Vault-Map.md` | None |
| F25 | Project OS files | Implemented | L5 | `01_PROJECTS/` (20+ files) | `Vault-Map.md` | None |
| F26 | Generated-Ideas layer | Partial | L5 | `02_KNOWLEDGE/[domain]/Generated-Ideas/` (lazy) | `AI-Generated-Output-Bridge.md` | None |
| F27 | AI-Generated-Output-Bridge | Adopted / Docs Only | L5 | `06_AGENTS/AI-Generated-Output-Bridge.md` | `SIC-Architecture.md` | None |
| F28 | Agent Memory Architecture (5-layer) | Adopted / Docs Only | L5 | `06_AGENTS/Agent-Memory-Architecture.md` | `Claude-Memory-System.md` | None |
| F29 | ContentPacket | Implemented | L6 | `runtime/capture/content_packet.py` | `Connector-Capture-Architecture.md` | None |
| F30 | Router + type-first naming | Implemented | L6 | `runtime/capture/router.py` | `Connector-Capture-Architecture.md` | None |
| F31 | Intake writer + sidecar v8.3 | Implemented | L6 | `runtime/capture/intake_writer.py` | `Connector-Capture-Architecture.md` | None |
| F32 | Physical quarantine boundary | Implemented | L6 | `03_INPUTS/00_QUARANTINE/` | `Connector-Capture-Architecture.md` | None |
| F33 | SHA-256 dedup registry | Implemented | L6 | `runtime/capture/dedup_registry.py` | `Connector-Capture-Architecture.md` | None |
| F34 | Semantic breadcrumb hints | Implemented | L6 | `runtime/capture/content_packet.py` | `Connector-Capture-Architecture.md` | None |
| F35 | Source Package Builder | Implemented | L7 | `runtime/source_intelligence/pipelines/source_package_builder.py` | `SIC-Architecture.md` | None |
| F36 | Workspace Manager | Implemented | L7 | `runtime/source_intelligence/workspaces/workspace_manager.py` | `SIC-Architecture.md` | None |
| F37 | Embedding backends | Implemented | L7 | `runtime/source_intelligence/indexes/embedder.py`, `backend_registry.py` | `SIC-Provider-Adapter-Standard.md` | None |
| F38 | Index Manager | Implemented | L7 | `runtime/source_intelligence/indexes/index_manager.py` | `SIC-Architecture.md` | None |
| F39 | Retrieval + cosine similarity | Implemented | L7 | `runtime/source_intelligence/retrieval/retriever.py`, `similarity.py` | `SIC-Architecture.md` | None |
| F40 | Output Generation Layer (9 types) | Implemented | L7 | `runtime/source_intelligence/output/generator.py`, `prompt_builder.py` | `SIC-Architecture.md` | None |
| F41 | Output Store | Implemented | L7 | `runtime/source_intelligence/output/output_store.py` | `SIC-Architecture.md` | None |
| F42 | Embedding benchmark | Implemented | L7 | `runtime/source_intelligence/retrieval/benchmark.py` | `SIC-Architecture.md` | Dev/eval only |
| F43 | SIC → Capture provenance link | Idea Only | L7 | None | `Feature-Fit-Register.md` | None |
| F44 | Cross-workspace retrieval | Idea Only | L7 | None | `Feature-Fit-Register.md` | None |
| F45 | Operator CLI (`chaseos`/`chase`) | Implemented | L8 | `runtime/cli/main.py`, `pyproject.toml` | `Connector-Capture-Architecture.md` | None |
| F46 | CLI connector (file/stdin) | Implemented | L8 | `runtime/capture/connectors/cli_connector.py` | `Connector-Capture-Architecture.md` | C5 (path) |
| F47 | RSS/Atom connector | Implemented | L8 | `runtime/capture/connectors/rss_connector.py` | `Connector-Capture-Architecture.md` | C5 (path) |
| F48 | Browser/HTML connector (local) | Implemented | L8 | `runtime/capture/connectors/browser_connector.py` | `Connector-Capture-Architecture.md` | C5 (path) |
| F49 | `chaseos capture browser live URL` | Idea Only | L8 | None | `Feature-Fit-Register.md` | None |
| F50 | Perplexity API connector | Implemented | L8 | `runtime/capture/connectors/perplexity_connector.py` | `Connector-Capture-Architecture.md` | C5 (path) |
| F51 | Grok/xAI API connector | Implemented | L8 | `runtime/capture/connectors/grok_connector.py` | `Connector-Capture-Architecture.md` | C5 (path) |
| F52 | Watched-folder automation | Implemented | L8 | `runtime/capture/watch_folders.py` | `Connector-Capture-Architecture.md` | None |
| F53 | Connector plugin system | Adopted / Docs Only | L8 | None | `Feature-Fit-Register.md` | None |
| F54 | Additional API connectors | Idea Only | L8 | None | `Feature-Fit-Register.md` | None |
| F55 | AOR 8-stage pipeline engine | Partial | L9 | `runtime/aor/engine.py` | `Autonomous-Operator-Runtime.md` | C6 |
| F56 | Workflow Registry loader | Partial | L9 | `runtime/aor/registry.py`, `runtime/workflows/registry/` | `Phase9-Adopted-Feature-Specification.md` | C1 |
| F57 | Role Card loader (2 live) | Implemented | L9 | `runtime/aor/role_cards.py`, `06_AGENTS/role-cards/` | `Phase9-Adopted-Feature-Specification.md` | C1 |
| F58 | Task-Type Router | Implemented | L9 | `runtime/aor/task_router.py`, `task_type_table.yaml` | `Phase9-Adopted-Feature-Specification.md` | C1 |
| F59 | AOR audit record writer | Implemented | L9 | `runtime/aor/engine.py` (`_write_audit_record`) | `Autonomous-Operator-Runtime.md` | C7 |
| F60 | Workflow manifests (4 draft) | Partial | L9 | `runtime/workflows/registry/*.yaml` | `Phase9-Adopted-Feature-Specification.md` | C1 |
| F61 | operator_today handler | Adopted / Docs Only | L9 | None (`_handlers={}`) | `Phase9-Adopted-Feature-Specification.md` | C6 |
| F62 | operator_close_day handler | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | C6 |
| F63 | graph_hygiene handler | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | C6 |
| F64 | graduate_ideas handler | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | C6 |
| F65 | Decision Ledger | Implemented | L10 | `07_LOGS/Decision-Ledger/` (3 entries) | `Phase9-Adopted-Feature-Specification.md` | C1 |
| F66 | Pivot Log | Implemented | L10 | `07_LOGS/Pivot-Log/` | `Phase9-Adopted-Feature-Specification.md` | C1 |
| F67 | Scheduled Briefing Pipelines | Adopted / Docs Only | L9 | None | `06_AGENTS/Scheduled-Briefing-Pipelines.md` | None |
| F68 | Runtime Navigation Map | Adopted / Docs Only | L9 | None | `06_AGENTS/Runtime-Navigation-Map.md` | None |
| F69 | Execution Repair Memory | Adopted / Docs Only | L9 | None | `06_AGENTS/Agent-Memory-Architecture.md` | None |
| F70 | Agent Identity Ledger | Adopted / Docs Only | L9 | None | `06_AGENTS/Agent-Memory-Architecture.md` | None |
| F71 | Agent Scorecards | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | None — second-wave |
| F72 | Context Governance Layer | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | None — second-wave |
| F73 | Provenance Schema | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | None — second-wave |
| F74 | trace_idea workflow | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | None — second-wave |
| F75 | drift_scan workflow | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | None — second-wave |
| F76 | Meeting Ingest Linker | Adopted / Docs Only | L9 | None | `Phase9-Adopted-Feature-Specification.md` | None — second-wave |
| F77 | AOR task scheduler / cron | Idea Only | L9 | None | `Feature-Fit-Register.md` | None |
| F78 | MCP integration | Idea Only | L9 | None | `Feature-Fit-Register.md` | None |
| F79 | Multi-repo policy enforcement | Idea Only | L9 | None | `Feature-Fit-Register.md` | None |
| F80 | Operator dashboard | Idea Only | L11 | None | `Feature-Fit-Register.md` | None |
| F81 | Quarantine review UI | Idea Only | L11 | None | `Feature-Fit-Register.md` | None |
| F82 | Provenance inspector UI | Idea Only | L11 | None | `Feature-Fit-Register.md` | None |
| F83 | SIC workspace browser UI | Idea Only | L11 | None | `Feature-Fit-Register.md` | None |
| F84 | AOR pipeline monitor UI | Idea Only | L11 | None | `Feature-Fit-Register.md` | None |
| F85 | TUI variant | Idea Only | L11 | None | `Feature-Fit-Register.md` | None |
| F86 | Paperclip | Idea Only | L11 | None | `Feature-Fit-Register.md` | Reserved; post-Phase 10 |

---

### Table C — Agent_MCP_Control

| agent_id | surface | trust_tier | enforcement_mechanism | permission_ceiling | can_write_vault | can_promote_knowledge | can_write_protected | hook_enforced | status |
|---------|---------|-----------|----------------------|-------------------|----------------|----------------------|--------------------|--------------|-------|
| claude-code-anthropic | Claude Code (CLI) | Tier 2 | 4 hooks in `.claude/hooks/` | No protected writes; no promotion without `CHASEOS_PROMOTION_APPROVED=1` | Yes (non-protected) | No (gate enforced) | No (hook blocks) | Yes — VERIFIED | Active |
| claude-ai-advisory | claude.ai (Chat) | Tier 3 | Doc/contract only | Advisory — no vault writes | No | No | No | No | Active (advisory only) |
| openai-chat-ui | ChatGPT (Chat UI) | Tier 3 | Doc/contract only | Advisory | No | No | No | No | Active (advisory only) |
| local-oss-cline | Cline / OpenHands | Tier 2–3 | Doc/contract only | Sandboxed; approval required | Conditional | No | No | No | Documented; not verified active |
| n8n-workflow | n8n runtime | Tier 2 | Doc + policy YAML | Quarantine-only writes | Quarantine only | No | No | No | Documented; not verified active |
| aor-operator-briefing | AOR engine (operator-briefing role) | Tier 2 | AOR 8-stage pipeline + role card YAML | Write to `07_LOGS/Daily/` only | Yes (logs only) | No | No | Partial (engine enforces; handlers not built) | Partial — scaffold only |
| aor-vault-maintenance | AOR engine (vault-maintenance role) | Tier 2 | AOR 8-stage pipeline + role card YAML | No deletes ever; no protected writes | Yes (`02_KNOWLEDGE/`, logs) | Yes (with Gate check) | No | Partial (engine enforces; handlers not built) | Partial — scaffold only |

---

### Contradiction Summary

| ID | Description | Severity | Fix Required |
|----|-------------|----------|-------------|
| C1 | Feature-Fit-Register Phase 9 table wrong — marks built items as NOT BUILT | Medium | Split "infrastructure scaffold — PARTIAL" vs "handlers — NOT BUILT" |
| C2 | README "not yet built" section stale — lists Pass 1 items as not started | Medium | Update Phase 9 not-yet-built list after Pass 1 |
| C3 | Now.md footer stale — shows 2026-03-29 but body is 2026-03-31 | Low | Bump footer to 2026-03-31 |
| C4 | Vault-Map.md footer stale — shows 2026-03-21 but content is Phase 9 | Low | Bump footer date |
| C5 | Connector path inconsistency — docs say `runtime/capture/` but files are in `runtime/capture/connectors/` | Low | Update doc references to `connectors/` subdirectory |
| C6 | AOR "live" claim vs. empty handlers — Stage 6/7 are scaffold-only | Medium | Clarify in high-level claims that handlers are Pass 2 |
| C7 | `runtime/audit/` referenced but absent — audit records actually in `07_LOGS/Agent-Activity/` | Low | Update Feature-Fit-Register row |
| C9 | Non-Anthropic policy YAMLs exist but no hooks enforce them | Medium | Already partially disclosed; flag for awareness |

---

### Feature Count Summary

| Classification | Count |
|---------------|-------|
| Implemented | 36 |
| Partial | 7 |
| Adopted / Docs Only | 22 |
| Idea Only | 21 |
| **Total** | **86** |

---

*Architecture-Workbook-2026-04-07.md — ChaseOS*
*Version: 1.0 | Created: 2026-04-07 | Basis: live repo files read 2026-04-07, Phase 9 Pass 1 COMPLETE state*
*This is a point-in-time snapshot. Verify against current code before acting on specific feature claims.*
*Graph links: [[Vault-Map]] · [[Feature-Fit-Register]] · [[Phase9-Adopted-Feature-Specification]] · [[Autonomous-Operator-Runtime]] · [[Scheduled-Briefing-Pipelines]] · [[Runtime-Navigation-Map]] · [[Agent-Memory-Architecture]] · [[SIC-Architecture]] · [[Connector-Capture-Architecture]] · [[Ingestion-Architecture]] · [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Knowledge-Taxonomy]]*
