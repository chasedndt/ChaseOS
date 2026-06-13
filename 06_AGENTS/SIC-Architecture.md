---
type: framework-architecture
title: Source Intelligence Core — Architecture
version: 1.1
created: 2026-03-21
updated: 2026-03-28
scope: Phase 7 — Source Intelligence Core
status: complete — all 7 passes done 2026-03-26; source packages, workspaces, index/embedding state, local retrieval + evidence query, output generation + workspace-local persistence + output type contract, embedding backend abstraction + benchmark
---

# Source Intelligence Core — Architecture

> The Source Intelligence Core (SIC) is a ChaseOS subsystem.
> It is not a replacement for ChaseOS, not a separate product, and not a disconnected memory layer.
> It is the source reasoning, workspace grouping, retrieval, and structured output layer inside ChaseOS.
> All SIC outputs feed the existing governed vault structure through the standard taxonomy and Gate rules.

---

## 1. What the SIC Is (and Is Not)

### What it is

The Source Intelligence Core is the reasoning and workspace intelligence layer inside ChaseOS. It provides:

- A normalized internal representation for all source types (Source Package)
- Workspace/notebook grouping of source sets around topics, projects, and investigations
- Retrieval-backed reasoning over workspace sources — outputs are grounded in specific source passages
- Structured output generation: summaries, FAQs, briefings, synthesis drafts, Idea Generation notes
- A pluggable provider adapter layer for generation and embeddings (model-agnostic)
- Governed writeback into the existing ChaseOS vault structure

### What it is not

- **Not a replacement for ChaseOS** — ChaseOS is the full system. The SIC is one major subsystem inside it.
- **Not a separate product or memory layer** — SIC does not create a disconnected knowledge store. All durable SIC outputs become ChaseOS vault artifacts under standard taxonomy governance.
- **Not a chat interface** — SIC produces structured outputs with source evidence, not a free-form chat layer. Every meaningful output should be classifiable under the ChaseOS taxonomy.
- **Not a bypass of the Gate** — SIC outputs that become durable knowledge must pass through the standard promotion gate (ingestion promotion guard, taxonomy frontmatter, domain index update).
- **Not a replacement for NotebookLM** — it replaces the *dependency* on NotebookLM. External tools may remain as optional inbound connectors (Phase 8). The intelligence architecture belongs to ChaseOS.
- **Not a substitute for the governed markdown layer** — `03_INPUTS/`, `02_KNOWLEDGE/`, `01_PROJECTS/`, domain indexes, backlinks, and Obsidian-visible markdown artifacts are all preserved and extended by SIC, not replaced.

---

## 2. How SIC Fits Within ChaseOS

```
┌──────────────────────────────────────────────────────────────────┐
│  ChaseOS — Governed Human-AI Source Intelligence Operating System │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Memory + Governance Layer (Phases 1–6)                      │  │
│  │  03_INPUTS/ → 02_KNOWLEDGE/ → 01_PROJECTS/ → Now.md         │  │
│  │  Knowledge Taxonomy · Gate · Domain Indexes · Build Logs    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                         ↑  SIC feeds this layer                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Source Intelligence Core (Phase 7)                          │  │
│  │  Source Packages · Workspaces · Retrieval · Output Gen      │  │
│  │  Provider Adapter (pluggable model backend)                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                         ↑  Ingest from here                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Capture Layer (current: 03_INPUTS/ manual; Phase 8: auto)  │  │
│  │  PDFs, transcripts, web clips, digests, documents           │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. Sources enter `03_INPUTS/` (manual capture now; automated in Phase 8)
2. SIC ingests sources from `03_INPUTS/` and creates normalized Source Packages
3. Source Packages are grouped into Workspaces
4. SIC generates structured outputs over workspaces using the retrieval layer and provider adapter
5. SIC outputs are routed back into the ChaseOS vault as source notes, synthesis notes, or Idea Generation notes — through the standard taxonomy and promotion gate
6. Domain indexes and backlinks are updated per the standard linking policy

**The vault is the durable memory.** SIC is the reasoning layer that produces content for the vault. It does not replace the vault.

---

## 3. The Five Layers

### Layer 1 — Source Package

Every source becomes a normalized internal object. See `runtime/source_intelligence/schemas/source_package_schema.md` for the full schema.

**Source types in scope:**
- PDF documents
- Plain text files
- Markdown notes and exports
- Webpages / URLs (extracted text)
- Transcripts (verbatim: YouTube, lecture, meeting, podcast)
- Audio-derived transcripts / captions
- Pasted/clipboard text
- Research digests (Perplexity, Grok, newsletters)
- Local document exports

**YouTube scoping rule:** For this phase, YouTube sources are supported as transcript/captions-derived text with metadata and source reference preserved. Full video media-awareness (multimodal, visual content understanding) is out of scope until justified in a future pass.

**Key guarantee:** A Source Package always references its origin file in `03_INPUTS/` or a local storage path. Source files are never embedded inside the vault structure — they are referenced. The normalized text representation is what the SIC operates over.

### Layer 2 — Workspace / Notebook

A Workspace groups Source Packages around a coherent topic, project, course, research question, or investigation. See `runtime/source_intelligence/schemas/workspace_schema.md` for the full schema.

A workspace is the self-built equivalent of a NotebookLM notebook — owned and stored locally, not platform-dependent.

**Workspace capabilities:**
- Summarize all sources in the workspace
- Extract key concepts across sources
- Generate FAQ with source citations
- Compare and contrast sources
- Build a study guide from the workspace
- Create a briefing or executive summary
- Generate an Idea Generation note (hypothesis, thesis, exploration)
- Answer a specific question with retrieval-grounded evidence

**Workspace storage:** Workspace objects are stored in `runtime/source_intelligence/workspaces/` as local files. They are not stored in the Obsidian-visible vault hierarchy unless explicitly promoted as a knowledge artifact.

### Layer 3 — Retrieval / Evidence

The evidence engine. This layer prevents outputs from becoming generic summaries disconnected from source material.

**Retrieval process:**
1. Chunk source packages at section or paragraph level
2. Embed chunks (using the configured provider adapter's embedding capability)
3. Store embedding index locally in `runtime/source_intelligence/` (never sent to a third-party storage service)
4. For any workspace query: retrieve the most relevant chunks → surface them as evidence → generate output with citations

**Evidence requirement:** Every SIC output that references source content must carry citations (source package ID + passage reference). Outputs without evidence attribution are workspace-local intermediate artifacts only — they may not be promoted to durable knowledge without the user adding attribution.

**Source-grounded vs. generated-ideas distinction:**
- If the output is directly supported by retrieved source passages → it is source-derived or synthesized
- If the output is a hypothesis, thesis, or proposal that goes beyond what sources say → it is `generated-ideas`
- This distinction maps directly to the ChaseOS knowledge taxonomy classes

### Layer 4 — Output Generation

Structured outputs generated over a workspace with evidence grounding. See Section 5 for the full output class → ChaseOS routing table.

**Output types:**
- Source summary (per source or per workspace)
- FAQ (question + sourced answer with citation)
- Briefing document (structured executive summary)
- Study guide (organized learning material from workspace sources)
- Timeline (chronological synthesis from sources)
- Comparison note (structured differences across two or more sources)
- Idea Generation note (hypothesis, thesis, proposal, exploration — `knowledge_class: generated-ideas`)
- Synthesis draft (multi-source synthesis ready for taxonomy-governed promotion)

**Intermediate vs. durable outputs:**
- **Workspace-local intermediate:** Output exists in the workspace record but has not been promoted to `02_KNOWLEDGE/`. It is searchable within SIC but does not appear in the vault's markdown structure. Suitable for in-progress work.
- **Durable knowledge artifact:** Output has been promoted through the standard gate into `02_KNOWLEDGE/` as a markdown note with taxonomy frontmatter, domain index link, and backlinks.

The default for all SIC outputs is **workspace-local intermediate** until the user explicitly promotes them.

### Layer 5 — Provider Adapter

Pluggable model backend for generation and embeddings. See `runtime/source_intelligence/SIC-Provider-Adapter-Standard.md` for the full standard.

The provider adapter supplies: text generation, embeddings for retrieval indexing, optional audio transcription, optional tool access (if configured).

The provider adapter does NOT own: workspace logic, source package schema, retrieval decisions, output classification, writeback routing, or Gate enforcement. Those belong to ChaseOS.

---

## 4. SIC Session Workflow

A typical SIC session flows as follows:

```
1. USER: Define or select a workspace
2. SIC: Load workspace → retrieve source packages → build/update retrieval index
3. USER: Issue a query or request an output type
4. SIC: Retrieve relevant chunks → generate output with evidence citations
5. SIC: Present output as workspace-local intermediate artifact
6. USER: Review output
7. USER (optional): Promote output to 02_KNOWLEDGE/ via standard promotion session
8. If promoted: SIC writes markdown artifact, taxonomy frontmatter, domain index link
9. If Idea Generation output: endorsement_status: unendorsed until user explicitly endorses
```

**Gate enforcement at step 8:** Writing to `02_KNOWLEDGE/` requires `CHASEOS_PROMOTION_APPROVED=1` in the executing shell. Standard `ingestion_promotion_guard` applies. The SIC does not bypass this.

**Action extraction at step 6:** If the SIC output contains implied action items, they follow the standard action extraction lifecycle from `Knowledge-Taxonomy.md` Section 6 — surfaced to user for routing, never autonomously written to Now.md or project OS files.

---

## 5. SIC Outputs and the AI-Generated Output Bridge

SIC workspace outputs are **Layer B** in the AI-Generated Output Bridge architecture. This is a critical distinction:

```
Layer A: Raw Quarantine         03_INPUTS/00_QUARANTINE/[class]/
              ↓ Gate promotion
Layer B: SIC Workspace-Local    runtime/source_intelligence/workspaces/{id}/outputs/
              ↓ operator review + Gate promotion
Layer C: Durable Generated      02_KNOWLEDGE/[Domain]/Generated-Ideas/
              ↓ endorsement + synthesis session
Layer D: Canonical Knowledge    02_KNOWLEDGE/[Domain]/ | 01_PROJECTS/
```

**Key rules for SIC outputs (Layer B):**

1. **SIC outputs are NOT durable vault content by default.** All outputs from `generate_output()` / `generate_and_persist()` land in `runtime/source_intelligence/workspaces/{id}/outputs/`. They are NOT in the Obsidian-visible vault hierarchy. They are NOT canonical. They may be cleared when a workspace is rebuilt.

2. **SIC does NOT process raw quarantine files.** SIC operates on promoted source packages — content that has already passed Gate review. The flow is: `Layer A (capture) → Gate promotion → SIC ingestion → Layer B (workspace outputs)`. SIC is not triggered at capture time.

3. **Promotion from Layer B to Layer C requires explicit operator action.** When a workspace output is worth preserving as a durable artifact, the operator explicitly promotes it through the Gate into `02_KNOWLEDGE/[Domain]/Generated-Ideas/` with `knowledge_class: generated-ideas` and required provenance frontmatter.

4. **Automated workflows may produce Layer B.** Phase 9 AOR may run SIC sessions autonomously. AOR may produce workspace-local outputs (Layer B). AOR may NOT promote to Layer C, D, or canonical state — that gate is human-only.

5. **Semantic breadcrumbs inform SIC routing.** The `domain_hint`, `project_hint`, `topic_hint`, and `workspace_hint` fields written to the sidecar at capture time (Phase 8 Pass 3) are available to help operators route promoted content to the right workspace. They are hints only — no automatic SIC invocation occurs from capture.

For the full 4-layer architecture and promotion rules, see `[[AI-Generated-Output-Bridge]]`.

---

## 6. SIC Output Classes → ChaseOS Vault Routing

Every SIC output that becomes a durable vault artifact must be classified under the ChaseOS taxonomy. This table is the canonical routing reference.

| SIC Output Type | Knowledge Class | Vault Artifact | Domain Index Update | May Touch Canonical State |
|-----------------|----------------|----------------|--------------------|-----------------------------|
| Source summary (one source) | `source-derived` | Source note in `02_KNOWLEDGE/[Domain]/` | Yes — link from index | No |
| FAQ (workspace, source-grounded) | `synthesized` | Synthesis note in `02_KNOWLEDGE/[Domain]/` | Yes | No |
| Briefing document | `synthesized` | Synthesis note in `02_KNOWLEDGE/[Domain]/` | Yes | No |
| Study guide | `synthesized` | Synthesis note in `02_KNOWLEDGE/[Domain]/` | Yes | No |
| Timeline | `synthesized` | Synthesis note in `02_KNOWLEDGE/[Domain]/` | Yes | No |
| Comparison note | `synthesized` | Synthesis note in `02_KNOWLEDGE/[Domain]/` | Yes | No |
| Synthesis draft | `synthesized` | Synthesis note in `02_KNOWLEDGE/[Domain]/` | Yes | No |
| Idea Generation note (hypothesis, thesis, proposal, exploration) | `generated-ideas` | Generated-idea note in `02_KNOWLEDGE/[Domain]/` | Yes | No — requires endorsement before touching canonical state |
| Workspace-local summary (not promoted) | N/A — intermediate | Workspace record only; no vault artifact | No | No |
| Project-specific output (with explicit user direction) | Depends on content | Project note in `01_PROJECTS/[Project]/` or knowledge note | Only if durable | Only with explicit user approval |

**Rules that cannot be overridden:**
1. SIC outputs may never touch `00_HOME/Now.md`, `ROADMAP.md`, or any `01_PROJECTS/*.md` file autonomously. These are canonical-state files.
2. A `generated-ideas` note must carry `endorsement_status: unendorsed` when created. It does not become canonical without explicit user endorsement.
3. All promotion writes to `02_KNOWLEDGE/` require the standard `CHASEOS_PROMOTION_APPROVED=1` gate.
4. Domain index files must be updated in the same session as any promotion.
5. All promoted notes must carry the full taxonomy frontmatter schema (see `Knowledge-Taxonomy.md` Section 3).

---

## 7. What SIC Does Not Replace

The following ChaseOS layers are **authoritative and unchanged by SIC**:

| Layer | What it is | SIC relationship |
|-------|-----------|-----------------|
| `03_INPUTS/` raw intake | Quarantine zone for all external content | SIC reads from here; does not bypass |
| `02_KNOWLEDGE/` durable knowledge | Promoted markdown artifacts with taxonomy | SIC writes to here via standard gate |
| `01_PROJECTS/` project OS files | Active project canonical state | SIC never writes here autonomously |
| `00_HOME/Now.md` | Sprint focus canonical state | SIC never writes here autonomously |
| `06_AGENTS/Knowledge-Taxonomy.md` | Six knowledge classes and frontmatter schema | SIC output classes must comply |
| ChaseOS Gate (hook scripts) | Enforcement at tool-call level | SIC does not bypass; promotion guard applies |
| Domain indexes + backlinks | Graph connectivity in Obsidian | SIC promotion must update these |
| Build logs + agent activity logs | Session audit trail | SIC sessions must produce logs per standard |
| Promotion-Session-SOP | Governed promotion workflow | SIC promotion sessions follow this SOP |

---

## 8. Local-First and Provider-Pluggable Principle

**User data stays in the user's system.**

| Asset | Storage location |
|-------|-----------------|
| Source files (PDFs, transcripts, docs) | Local filesystem or `03_INPUTS/` |
| Source packages (normalized text + chunks) | `runtime/source_intelligence/schemas/` or local SIC store |
| Embedding indexes | Local only — `runtime/source_intelligence/` |
| Workspace objects | `runtime/source_intelligence/workspaces/` |
| Generated SIC outputs (workspace-local) | `runtime/source_intelligence/` or workspace record |
| Promoted durable artifacts | `02_KNOWLEDGE/[Domain]/` (Obsidian vault) |
| Canonical state | `01_PROJECTS/`, `00_HOME/`, `ROADMAP.md` (Obsidian vault) |

**Provider adapters handle generation and embeddings only.** They do not receive more source text than required for the current operation. They do not store workspace state. Credential handling follows `Credential-Boundaries-SOP.md`.

**Provider is swappable.** ChaseOS owns the source model and workspace logic. Switching from Claude to an OpenAI or local model adapter does not require migrating source packages, workspaces, or vault artifacts.

---

## 9. Phase 7 Scope Boundaries

**In scope for Phase 7:**
- Source Package schema and builder (PDF, transcript, plain text, markdown, webpage/URL)
- Workspace schema and definition
- Provider adapter interface (Claude/Anthropic first; OpenAI and local model as alternatives)
- Local embedding and retrieval path
- Output types: source summary, FAQ, synthesis draft, Idea Generation note
- Writeback through standard Gate and taxonomy
- Local-first storage model

**Out of scope for Phase 7 (deferred):**
- Automated capture / watched folder integration (Phase 8)
- n8n orchestration or event-triggered SIC sessions (Phase 8)
- Operator-style long-running SIC workflows (Phase 9)
- SIC workspace browser UI (Phase 10)
- Full video/audio media-aware processing beyond transcript/captions text
- MCP server exposing SIC workspaces to external agents
- Multi-workspace cross-workspace retrieval

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `runtime/source_intelligence/schemas/source_package_schema.md` | Canonical Source Package schema |
| `runtime/source_intelligence/schemas/workspace_schema.md` | Canonical Workspace schema |
| `runtime/source_intelligence/SIC-Provider-Adapter-Standard.md` | Provider adapter boundary |
| `[[AI-Generated-Output-Bridge]]` | **4-layer output bridge: Layer A (capture) → Layer B (SIC workspace-local) → Layer C (durable generated artifacts) → Layer D (canonical). SIC outputs are Layer B.** |
| `[[Knowledge-Taxonomy]]` | Six knowledge classes; frontmatter schema; generated-ideas rules |
| `[[Ingestion-Architecture]]` | Five-layer ingestion pipeline; SIC feeds from Layer 4 |
| `[[Connector-Capture-Architecture]]` | Phase 8 capture layer; semantic breadcrumbs (Layer A sidecar hints for SIC routing) |
| `[[04_SOPS/Promotion-Session-SOP|Promotion-Session-SOP]]` | How to run a promotion session for SIC outputs |
| `[[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]]` | Per-type processing rules that inform SIC source handling |
| `[[ChaseOS-Gate]]` | Enforcement control layer; SIC must not bypass |
| `ROADMAP.md` Phase 7 | Phase scope, outputs, and DoD |
| `PROJECT_FOUNDATION.md` Section 19 | SIC declared architecture (strategic framing) |

---

*Graph links: [[Vault-Map]] · [[Knowledge-Taxonomy]] · [[Ingestion-Architecture]] · [[AI-Generated-Output-Bridge]] · [[Connector-Capture-Architecture]] · [[04_SOPS/Promotion-Session-SOP|Promotion-Session-SOP]] · [[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]] · [[ChaseOS-Gate]] · [[ROADMAP]] · [[PROJECT_FOUNDATION]] · [[CLAUDE]]*

*SIC-Architecture.md — Version 1.1 | Created: 2026-03-21 | Updated: 2026-03-28 (Phase 7 COMPLETE; Section 5 AI-Generated-Output-Bridge wiring added; section numbering updated; Related Documents expanded)*
