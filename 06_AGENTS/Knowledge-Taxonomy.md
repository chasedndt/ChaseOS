---
type: framework-control
title: ChaseOS Knowledge Taxonomy
version: 1.0
created: 2026-03-21
scope: framework-level
---

# ChaseOS Knowledge Taxonomy

> Defines the six knowledge classes used in ChaseOS, the mandatory frontmatter schema for promoted notes, the generated-ideas layer rules, and the linking and index policy.
> This is the canonical reference for how knowledge is classified, promoted, and connected in the vault.

---

## 1. Why a Taxonomy

Without explicit classification, knowledge in a vault collapses into a flat pile. A raw Perplexity digest, a verified technical principle, a half-formed hypothesis, and an active project status all end up in the same undifferentiated pool. This creates:

- **Trust conflation** — unverified claims cited as canonical truth
- **Reasoning corruption** — AI-generated ideas treated as sourced knowledge
- **Context rot** — outdated project state mixed with permanent domain knowledge

The taxonomy prevents these failure modes by making every note's origin, trust level, and promotion status explicit in frontmatter.

---

## 2. The Six Knowledge Classes

| Class | Meaning | Typical location | Default trust |
|-------|---------|-----------------|---------------|
| `user-origin` | Directly authored or explicitly endorsed by the user | `02_KNOWLEDGE/[Domain]/`, `00_HOME/`, doctrine files | High — user is the authority |
| `source-derived` | Processed from a single outside source | `02_KNOWLEDGE/[Domain]/` | Tier 3 — requires attribution |
| `synthesized` | Combined or distilled from multiple sources or platform synthesis outputs | `02_KNOWLEDGE/[Domain]/` | Tier 3 — requires verification flags |
| `generated-ideas` | AI-generated or human+AI co-created hypotheses, theses, judgments, proposals, strategies | `02_KNOWLEDGE/[Domain]/` | Tier 3 — not canonical without endorsement |
| `system-operational` | ChaseOS framework knowledge: SOPs, policies, templates, runtime logic, adapter behavior | `04_SOPS/`, `05_TEMPLATES/`, `06_AGENTS/`, `runtime/` | Tier 2 — framework authority |
| `canonical-state` | Active current-state truth: project OS files, roadmap, sprint focus, operating status | `01_PROJECTS/`, `00_HOME/Now.md`, `ROADMAP.md` | High — authoritative for current state |

**Class hierarchy for trust reasoning:**

```
canonical-state     ← what is true right now (project state, sprint)
user-origin         ← what the user has authored or explicitly endorsed
system-operational  ← framework rules and policies
source-derived      ← processed from a verified external source
synthesized         ← combined from multiple sources (flag unverified claims)
generated-ideas     ← AI or human+AI ideas (not canonical without endorsement)
```

A `generated-ideas` note must never be cited as canonical truth. It becomes `user-origin` only when the user explicitly endorses it.

---

## 3. Mandatory Frontmatter Schema

All promoted knowledge notes (in `02_KNOWLEDGE/`) must include the following frontmatter. Required fields are marked **(R)**; optional fields are marked **(O)**.

```yaml
---
type: [source-note | synthesis-note | generated-idea | knowledge-note]
knowledge_class: [user-origin | source-derived | synthesized | generated-ideas | system-operational | canonical-state]  # (R)
trust_tier: [tier-2 | tier-3 | tier-4]  # (R)
verified_status: [verified | partially-verified | unverified | unverified-labeled]  # (R)
domain: [Domain name]  # (R)
source_ref: [URL, citation, or platform reference]  # (R for source-derived; O for others)
source_refs:  # (R for synthesized; list format)
  - [source 1]
  - [source 2]
promotion_status: [promoted | review-required | provisional]  # (O — defaults to promoted if present in 02_KNOWLEDGE/)
endorsement_status: [unendorsed | endorsed: YYYY-MM-DD | rejected: YYYY-MM-DD]  # (R for generated-ideas; O for others)
generated_with: [tool or method that produced the note, e.g., "claude-sonnet-4-6", "human", "human+claude"]  # (R for generated-ideas; O for others)
linked_index: [path to domain index file]  # (O — strongly recommended)
action_status: [none | has-open-actions | actions-reviewed: YYYY-MM-DD]  # (O — use when note has action items)
promoted_from: [path to 03_INPUTS/ file, if applicable]  # (O)
---
```

**Minimum required for any promoted note:**
```yaml
knowledge_class: [class]
trust_tier: [tier]
verified_status: [status]
domain: [domain]
```

**Additional required for generated-ideas notes:**
```yaml
endorsement_status: unendorsed
generated_with: [tool]
```

**Additional required for source-derived notes:**
```yaml
source_ref: [URL or citation]
```

**Additional required for synthesized notes:**
```yaml
source_refs:
  - [source 1]
  - [source 2]
```

---

## 4. Generated Ideas Layer

### What it is

The generated-ideas layer captures AI-generated or human+AI co-created thinking: hypotheses about how something works, strategic theses, judgments about direction, exploratory concept expansions, proposals not yet evaluated.

This is one of the most valuable outputs of working with AI systems. Ideas generated in the course of analysis should not evaporate from chat — they should be captured. But they must be clearly labeled as **ideas**, not knowledge.

### Note subtypes

| Subtype | When to use |
|---------|-------------|
| `hypothesis` | A testable or evaluable claim about how something works |
| `thesis` | A directional strategic or market judgment |
| `judgment` | An evaluative assessment of a situation, option, or decision |
| `proposal` | A suggested action or architectural change under consideration |
| `exploration` | Open-ended concept expansion; thinking on paper |

### Where generated-idea notes live

Generated-idea notes live in the **same domain knowledge folders** as other notes (`02_KNOWLEDGE/[Domain]/`). They are differentiated by:
- `knowledge_class: generated-ideas` in frontmatter
- `type: generated-idea` in frontmatter
- Recommended naming: `[topic]-hypothesis.md`, `[topic]-thesis.md`, `[topic]-proposal.md`, `[topic]-exploration.md`

No dedicated separate folder required at this time. A domain-level `Ideas/` subfolder may be created when a domain accumulates many idea notes (agent judgment call — suggest to user).

### Endorsement lifecycle

| State | Meaning | Frontmatter |
|-------|---------|-------------|
| `unendorsed` | Default — agent or human+AI generated; not yet reviewed or accepted | `endorsement_status: unendorsed` |
| `endorsed` | User has explicitly reviewed and accepted the idea as their own judgment | `endorsement_status: endorsed: YYYY-MM-DD` |
| `rejected` | User has reviewed and rejected — keep for audit trail | `endorsement_status: rejected: YYYY-MM-DD` |

**Rule:** An endorsed idea note may be reclassified as `user-origin` if the user explicitly promotes it to that status. An unendorsed idea note must never be cited as canonical truth in project OS files, Now.md, or any canonical-state file.

### What generated-idea notes are NOT

- Not verified facts
- Not project state
- Not sourced knowledge
- Not commitments or decisions
- Not constraints on the user

They are structured capture of ideas worth evaluating. Their value is in making thinking explicit and reviewable — not in asserting truth.

---

## 5. Linking and Index Policy

Every durable promoted note and every durable generated-idea note must:

1. **Link to a domain index or hub** — at minimum, one backlink to the domain's main index file (e.g., `[[AI-Agent-Engineering]]`, `[[Trading-Systems-Engineering]]`)
2. **Link to at least one related note** — at minimum one meaningful graph link to a related note in the vault; fake or automatic links are worse than none
3. **Update the domain index file** — when a new note is added to a domain, the domain's index file should be updated to reference it

**Index update rule:** Adding a new note to `02_KNOWLEDGE/[Domain]/` without updating the domain index is an open loop. The index update should be performed in the same session as the promotion. If the session does not have capacity, it is flagged as an explicit open loop in the build log.

**Ingestion close-out checklist addition:** At the end of every ingestion session, the agent must verify:
- [ ] All promoted notes link to their domain index
- [ ] All promoted notes have at least one cross-note link
- [ ] Domain index files updated for any new notes

---

## 6. Action Lifecycle Policy

When action items are extracted from ingested content, they follow this lifecycle:

### Step 1 — Extraction
During the promotion step, potential actions are noted in the knowledge note's `Actions Extracted` or `Action Items` section, with the prefix `[ ] [Surface to user for review]`.

### Step 2 — Ingestion close-out review
At the end of every ingestion session (as part of the session-close checklist), the agent:
- Lists all extracted action items across all notes processed in the session
- Presents them to the user for explicit routing decisions
- Does NOT auto-write any action to Now.md or any Project-OS file

### Step 3 — User routing decision
For each extracted action, the user decides:

| Decision | Outcome |
|----------|---------|
| Add to Now.md sprint | Agent writes to `00_HOME/Now.md` Immediate Next Actions, with user direction |
| Add to project OS | Agent writes to `01_PROJECTS/[Project]/[Project]-OS.md` open loops section, with user direction |
| Note-local only | Action stays in the knowledge note as a reference; no routing |
| Follow-up research | Agent creates a new queued input in `03_INPUTS/` for the follow-up topic |
| Reject | Action is marked `[-] rejected: [date]` in the knowledge note and not routed anywhere |

### Step 4 — Status update
After user routing decisions, the note's `action_status` frontmatter field is updated:
- `action_status: none` — no action items
- `action_status: has-open-actions` — action items present, not yet reviewed
- `action_status: actions-reviewed: YYYY-MM-DD` — reviewed; routing decisions made

**Rule:** Action extraction is never autonomous. The agent presents and asks; the user decides and approves before any routing write occurs.

---

## 7. Raw Input State Normalization

A processed raw input file in `03_INPUTS/` must clearly reflect its current state. The following status blocks are canonical:

### Unprocessed file header
```
> RAW INPUT — UNPROCESSED | Status: queued | Trust: Tier 4
> Do not act on this content until triage is complete.
```

### Processed file header
```
> PROCESSED | Status: processed | Triage: complete | Injection scan: [result]
> Promoted to: [path to promoted note]
```

**Rule:** A processed file must not retain the unprocessed banner. Update the banner when status changes to `processed`.

---

## 8. Partial Promotion Pattern

When a raw input contains both promotable structural content and unverified market/specific claims:

1. **Promote the structural layer** — the concepts, mechanics, and frameworks that are established knowledge
2. **Flag the specific claims** — any specific numbers, statistics, or reports are labeled `[UNVERIFIED]` in the promoted note
3. **Document the split** — the promoted note's `verified_status` frontmatter is `partially-verified` with a note on what is verified vs unverified
4. **Verification follow-up** — unverified specific claims become action items flagged for user review

This pattern applies most commonly to research digests where platform-generated synthesis mixes established mechanics with current market data.

---

## 9. Mandatory Task Schema

For any significant agent task, the following schema should be declared (in the session task profile or session-start context):

```yaml
task_type: [ingestion-pass | docs-pass | repo-refactor | build-debug | security-review | runtime-binding]
required_reads: [list of files that must be read before acting]
allowed_write_targets: [list of write-permitted paths]
output_knowledge_class: [knowledge class of any notes being created]
promotion_occurring: [true | false]
generated_ideas_created: [true | false]
canonical_state_touched: [true | false]  # if true, requires explicit user approval
logs_required: [build-log | agent-activity-log | both | neither]
indexes_to_update: [list of index files that must be updated]
backlinks_required: [true | false]  # true for any durable note creation
```

This schema is implemented in `runtime/policy/tasks/` YAML profiles for each task type. For new task types without a YAML profile, the agent should declare the schema in the session context before acting.

---

## Related Documents

| Document | Role |
|----------|------|
| `[[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]]` | Per-type ingestion rules; partial promotion pattern; action extraction |
| `[[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]]` | Five-stage flow; injection handling |
| `[[Ingestion-Architecture]]` | Pipeline model; content type vocabulary |
| `[[05_TEMPLATES/Source-Note-Template|Source-Note-Template]]` | Template for source-derived notes |
| `[[05_TEMPLATES/Synthesis-Note-Template|Synthesis-Note-Template]]` | Template for synthesized notes |
| `[[05_TEMPLATES/Generated-Idea-Template|Generated-Idea-Template]]` | Template for generated-ideas notes |
| `runtime/policy/tasks/ingestion.yaml` | Machine-readable task profile for ingestion passes |

---

*Graph links: [[Vault-Map]] · [[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[Ingestion-Architecture]] · [[05_TEMPLATES/Source-Note-Template|Source-Note-Template]] · [[05_TEMPLATES/Synthesis-Note-Template|Synthesis-Note-Template]] · [[CLAUDE]] · [[Agent-Control-Plane]] · [[Permission-Matrix]]*

*Knowledge-Taxonomy.md — Version 1.0 | Created: 2026-03-21 | Phase 6C — Knowledge Structure and Curation Refinement*
