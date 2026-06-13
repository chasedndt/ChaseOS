---
type: architecture
project: ChaseOS
phase: Phase 8 — Connector / Capture Automation
version: 1.0
date: 2026-03-28
status: active-engineering
---

# AI-Generated Output Bridge — ChaseOS Architecture

## Purpose

ChaseOS already separates four content categories in doctrine: raw inputs, processed knowledge, generated ideas, and canonical state. This document makes that separation operationally explicit for AI-generated content — defining where each layer lives, how they relate, and what the governance rules are at each boundary.

The "bridge" is the set of governed promotion paths between:
- raw captured content in quarantine
- AI-generated drafts in SIC workspace-local storage
- durable AI-generated artifacts in the vault
- canonical promoted knowledge and system state

Without this clarity, AI-generated material accumulates in ambiguous places and either contaminates canonical knowledge or disappears when workspaces are cleared.

---

## The Four Layers

### Layer A — Raw Quarantine Capture

**Location:** `03_INPUTS/00_QUARANTINE/[class]/`

**What it is:**
Content captured from external sources, operator stdin, or automated connectors. Raw, unverified, unclassified. Lands in quarantine by default on every capture.

**What it is NOT:**
- Not SIC-ingested
- Not promoted to knowledge
- Not trusted until reviewed
- Not canonical in any sense

**Sidecar state at this layer:**
```
quarantine_status: "pending-review"
promotion_status: "quarantine"
source_package_status: "not-ingested"
```

**How it moves forward:**
Human review → Gate promotion (`CHASEOS_PROMOTION_APPROVED=1`) → Layer D (direct source promotion) or → SIC ingestion → Layer B

**Important:** AI-generated content captured from external tools (NotebookLM exports, Perplexity syntheses, Grok outputs) also lands here first. The `origin_kind` sidecar field records that it is AI-generated. This does NOT change the routing or promotion rules — AI-generated captures are still quarantine-first, review-required, Gate-gated, exactly like human-authored captures.

---

### Layer B — SIC Workspace-Local Outputs

**Location:** `runtime/source_intelligence/workspaces/{workspace_id}/outputs/`

**What it is:**
AI-generated drafts, evidence-grounded summaries, FAQs, hypotheses, synthesis candidates, and briefing components produced by SIC's output generation layer (`runtime/source_intelligence/output/`). Managed by `output_store.py`.

**What it is NOT:**
- Not durable vault content
- Not accessible via Obsidian by default
- Not canonical
- Not promoted knowledge
- Not visible in the knowledge graph

**When SIC workspace outputs are created:**
Only after Gate promotion of Layer A content. SIC receives promoted source packages. It does NOT process raw quarantine files directly. The pipeline is:

```
Layer A (quarantine) -> Gate promotion -> SIC ingestion -> Layer B (workspace outputs)
```

SIC is NOT triggered at capture time. The `source_package_status` field transitions from `"not-ingested"` to `"ingested"` only after Gate promotion and explicit SIC ingestion.

**Lifecycle of Layer B outputs:**
- Created by SIC output generation layer
- Stored in workspace-local `outputs/` directory
- Listable via `runtime/source_intelligence/output/generator.py` CLI
- Candidate for extraction to Layer C (operator decision)
- May be cleared when workspace is rebuilt/reset (non-durable)

---

### Layer C — Durable AI-Generated Artifacts

**Location:** `02_KNOWLEDGE/[Domain]/Generated-Ideas/` (or equivalent domain subfolder)

**What it is:**
AI-generated or human+AI collaborative artifacts that have been explicitly reviewed, endorsed, and promoted through the Gate. These are distinct from source-derived notes — they are ideas, hypotheses, synthesis candidates, or generated briefings that the operator has decided are worth keeping as durable vault records.

**Knowledge class:** `generated-ideas` (per Knowledge-Taxonomy.md)

**Required sidecar/frontmatter fields for Layer C artifacts:**
```yaml
knowledge_class: generated-ideas
endorsement_status: candidate | endorsed | rejected
source_workspace: <workspace_id>     # links back to SIC workspace
source_package_ids: [<uuid>, ...]    # links to source packages used
generated_by: sic | aor | operator  # who/what generated this
captured_at: <ISO 8601>
promoted_at: <ISO 8601>
```

**What it is NOT:**
- Not canonical truth
- Not a verified factual claim
- Not equivalent to source-derived notes
- Not stable — may be superseded or retracted

**How it gets here:**
```
Layer B (workspace output) -> operator review -> Gate promotion -> Layer C
```

OR from a directly captured AI output:
```
Layer A (ai-generated capture) -> review -> Gate promotion -> Layer C
```

**Endorsement lifecycle (from Knowledge-Taxonomy.md):**
- `candidate` — written to vault as a generated idea; not yet acted on
- `endorsed` — operator has explicitly validated this idea as worth acting on
- `rejected` — operator has explicitly dismissed this idea

Only endorsed items are candidates for elevation to Layer D.

---

### Layer D — Canonical Promoted Knowledge and State

**Location:** `02_KNOWLEDGE/[Domain]/` (source notes, synthesis notes) and `01_PROJECTS/` (project state, operating files)

**Knowledge classes at this layer:** `source-derived`, `synthesized`, `canonical-state`

**What it is:**
Verified, reviewed, Gate-promoted knowledge that is authoritative within the domain. Source-derived notes from promoted captures. Multi-source synthesis notes from deliberate synthesis sessions. Canonical project/system state.

**What it is NOT:**
- Not raw output from AI generation
- Not automatically derived from Layer B or C
- Not implied by capturing content at Layer A

**How it gets here:**

From Layer A directly (source content):
```
Layer A (source/digest/transcript) -> human review -> Gate promotion -> Layer D (source-derived)
```

From Layer C (endorsed generated idea):
```
Layer C (endorsed generated-idea) -> synthesis session -> Gate promotion -> Layer D (synthesized)
```

Gate promotion to Layer D always requires explicit operator decision. No automated promotion to this layer occurs at any phase.

---

## Layer Relationship Summary

```
External Source
    |
    v
Layer A: Raw Quarantine Capture               03_INPUTS/00_QUARANTINE/
    |-- human review + Gate promotion -------> Layer D (source-derived content)
    |-- Gate promotion -> SIC ingestion -----> Layer B (SIC processes promoted packages)
    |
    v
Layer B: SIC Workspace-Local Outputs          runtime/source_intelligence/workspaces/{id}/outputs/
    |-- operator review + Gate promotion ----> Layer C (durable generated artifact)
    |
    v
Layer C: Durable AI-Generated Artifacts       02_KNOWLEDGE/[Domain]/Generated-Ideas/
    |-- endorsement + synthesis session -----> Layer D (if elevated to canonical)
    |
    v
Layer D: Canonical Promoted Knowledge         02_KNOWLEDGE/[Domain]/ | 01_PROJECTS/
```

**Immovable rule across all layers:**
Automated workflows may produce outputs at Layer B. They may NOT promote to Layer C, D, or canonical state. Every Layer C write and every Layer D write requires explicit human operator decision and Gate enforcement.

---

## How Semantic Breadcrumbs Connect to This Bridge

Pass 3 adds semantic hint fields to the sidecar at capture time (Layer A). These breadcrumbs are designed to inform future SIC workspace grouping and operator review — without triggering any automatic promotion.

| Breadcrumb field | How it helps later |
|-----------------|-------------------|
| `domain_hint` | SIC auto-suggests workspace grouping by domain |
| `project_hint` | Operator sees which project this likely feeds |
| `topic_hint` | SIC retrieval and workspace indexing can use this as context |
| `event_date_hint` | Temporal grouping for transcripts/lectures |
| `origin_kind` | Operator knows at a glance if this is AI-generated at source |
| `desired_output_kind` | Operator sees intended Layer C/D destination |
| `workspace_hint` | Operator-specified direct SIC workspace target |

The breadcrumbs surface in `chaseos intake inspect` so the operator sees full context during triage review. They do NOT cause automatic routing changes, SIC invocation, or promotion decisions.

---

## Strategy: Default-Local, Explicit-Promote

The adopted strategy for durable AI-generated artifacts:

1. **Default: SIC workspace-local** — AI outputs stay in `runtime/source_intelligence/workspaces/{id}/outputs/` until explicitly extracted. They are inspectable but not vault-visible.

2. **Explicit Layer C promotion** — When an operator decides a generated artifact is worth keeping as a durable record, it is promoted through the Gate as a `generated-ideas` knowledge note with required provenance frontmatter.

3. **Explicit Layer D elevation** — Only endorsed `generated-ideas` notes, after deliberate synthesis sessions, become `synthesized` or `source-derived` canonical knowledge.

This strategy ensures:
- AI outputs do not pollute the canonical knowledge layer by default
- Every AI-generated artifact in the vault has an explicit audit trail
- The distinction between "AI thought of this" and "I verified this" is always legible
- Workspace-local outputs can be freely generated, inspected, and discarded without vault contamination

---

## Relationship to Other ChaseOS Systems

- **Phase 8 Capture Layer** — writes Layer A. Semantic breadcrumbs are set here.
- **Phase 7 SIC** — reads from Layer A (after promotion) and produces Layer B.
- **ChaseOS Gate** — enforces the A→C, A→D, and C→D promotion gates.
- **Knowledge Taxonomy** — defines the knowledge_class system that distinguishes all four layers.
- **Phase 9 AOR** — will orchestrate A→B transitions and may produce Layer B outputs at scale. AOR does not bypass the Layer B→C or B→D gates.

---

## Layer C File-System Strategy

**Decision (Phase 8 Pass 4): Lazy creation on first promotion.**

`02_KNOWLEDGE/[Domain]/Generated-Ideas/` subdirectories are NOT created eagerly for all active domains. They are created on demand — when the operator first promotes a durable generated artifact into that domain.

**Why lazy:**
- No generated artifact has been promoted to Layer C yet; pre-creating empty directories adds noise with no benefit
- The folder structure is self-documenting when created with real content
- Each domain index file can be updated at promotion time to add the `Generated-Ideas/` link

**Naming convention inside `Generated-Ideas/`:**
```
02_KNOWLEDGE/[Domain]/Generated-Ideas/
    YYYY-MM-DD__[output-type]__[slug].md
```

Example: `02_KNOWLEDGE/Trading-Systems/Generated-Ideas/2026-03-28__synthesis-draft__crypto-perps-funding-mechanics.md`

**Required frontmatter** (from Layer C definition above): `knowledge_class: generated-ideas`, `endorsement_status`, `source_workspace`, `source_package_ids`, `generated_by`, `captured_at`, `promoted_at`.

---

## Semantic Hint Vocabulary — Advisory-Only (Phase 8 Pass 4 Decision)

The `origin_kind` and `desired_output_kind` hint fields introduced in Pass 3 remain **fully advisory-only** at this phase.

**Decided:**
- No validation at intake — any string is accepted; no CLI warning for unrecognized values
- No routing changes based on hint values
- No SIC invocation triggered by hints
- Vocabulary constants (`ORIGIN_KIND_*`, `DESIRED_OUTPUT_KIND_*`) in `content_packet.py` document the canonical values

**Why advisory-only for now:**
- The capture layer should remain simple and permissive; validation complexity is not justified until workflows that consume these fields are built
- Invalid values cause no harm — they are stored in the sidecar and visible via `chaseos intake inspect`
- Strict vocabulary validation is explicitly deferred to Phase 9 when AOR workflows consume these fields programmatically

**Future:** When AOR (Phase 9) begins routing on `desired_output_kind`, strict validation with configurable severity (warn/reject) may be added then.

---

## What Is NOT Automated (at Any Phase)

- Promotion of Layer A captures to Layer C or D — always human-gated
- Creation of Layer C artifacts without operator review — always human-gated
- Elevation of Layer C to Layer D without endorsement — always human-gated
- SIC invocation at capture time — SIC runs separately, after Gate promotion

---

*AI-Generated-Output-Bridge.md — Phase 8 Pass 3 — 2026-03-28*


*Graph links: [[Vault-Map]]*
