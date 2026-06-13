---
title: Knowledge Navigator and Domain Browser Standalone Application
type: implementation-bridge-plan
status: seeded — standalone application of ChaseOS knowledge/domain surfaces
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Knowledge Navigator and Domain Browser Standalone Application

> This document applies the markdown-to-standalone bridge to the knowledge/domain side of ChaseOS.
> It defines how `02_KNOWLEDGE/` should become future standalone knowledge navigators, domain browsers, knowledge detail views, and promotion-aware domain operating surfaces without flattening knowledge, source lineage, and canonical-state distinctions.

---

## 1. Purpose

Earlier bridge/application slices already mapped runtime, workflow, coordination, project, workspace, provenance, repo-mode, and consolidated cockpit surfaces.

What was still missing was the explicit knowledge-side answer to:

**How should a future standalone ChaseOS let the operator browse domains, inspect knowledge state, understand provenance/promotion posture, and move between knowledge, project, and evidence context without treating all notes as the same thing?**

This document answers that.

---

## 2. Scope of This Application Pass

Included in this pass:
- `02_KNOWLEDGE/Knowledge-Index.md`
- `02_KNOWLEDGE/**/[Domain-Index].md`
- classified notes under `02_KNOWLEDGE/**`
- `06_AGENTS/SIC-Architecture.md`
- `04_SOPS/Research-Ingest-SOP.md`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`

Not included yet:
- final graph rendering behavior
- note editing UX details
- automatic domain taxonomy generation
- full promotion workflow implementation
- knowledge quality scoring or dedup service logic

---

## 3. Why This Slice Is Needed

Without a dedicated knowledge/domain pass, the future standalone would risk having:
- strong runtime/operator surfaces,
- strong project/workspace surfaces,
- but only a generic markdown note browser for the knowledge layer.

That would underspecify one of ChaseOS's core OS responsibilities: turning research, synthesis, doctrine, and durable learning into structured operating knowledge.

A real ChaseOS standalone needs a way to answer:
- what domains exist,
- what each domain currently knows,
- what knowledge is canonical vs advisory vs generated,
- what project or workspace context a note belongs to,
- what source/provenance chain supports it,
- and what still needs review or promotion.

---

## 4. Governing Rule

**The knowledge navigator is a governed domain-view surface, not a generic notes app and not a second truth store.**

That means:
- markdown knowledge notes remain current source artifacts,
- knowledge indexes remain routing anchors,
- provenance and promotion posture must remain visible,
- domain browsing may unify visibility,
- but it must not erase knowledge class, trust posture, or source lineage.

Short form:
- domain indexes stay navigational anchors
- knowledge notes stay typed knowledge objects
- source lineage stays provenance-linked
- promotion posture stays explicit
- project/workspace links stay cross-surface references, not ownership replacement

---

## 5. Current Markdown-Era Roles Feeding the Knowledge Surface

### A. Master knowledge index layer
Provides:
- top-level domain list
- domain identity
- operator entry point into the knowledge system

### B. Domain knowledge index layer
Provides:
- domain-local scope
- subtopic grouping
- note routing context
- durable domain anchors

### C. Classified knowledge note layer
Provides:
- the actual durable note content
- `knowledge_class`
- derived/synthesized/generated posture
- local cross-links inside and across domains

### D. Research-to-knowledge pipeline layer
Provides:
- how raw inputs become knowledge
- promotion discipline
- source-derived vs synthesized distinction
- SIC workspace relationship

### E. Provenance and chronology layer
Provides:
- promoted-from lineage
- supporting source context
- build/runtime chronology when relevant
- auditability for promoted knowledge artifacts

### F. Project/domain linkage layer
Provides:
- where knowledge informs projects
- where projects create demand for more knowledge
- where domain truth should stay independent from project-specific operating state

---

## 6. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| `02_KNOWLEDGE/Knowledge-Index.md` | Knowledge Root Surface | domain navigator home |
| domain index files | Domain Browser Surface | domain browser / domain landing view |
| classified knowledge notes | Knowledge Detail Surface | note/detail panel with typing + provenance |
| domain-local note collections | Domain Map Surface | graph/list knowledge explorer |
| promotion and source lineage metadata | Knowledge Provenance Surface | provenance sidebar / lineage drill-down |
| project/workspace references into knowledge | Cross-Link Surface | project/domain/workspace relation panel |
| knowledge summaries and typed outputs | Knowledge Summary Surface | domain digest / operator summary strip |

---

## 7. Recommended Standalone Surfaces

### A. Knowledge navigator home
Show:
- all domains
- recent domain activity
- notable promoted knowledge
- domains with stale indexes or open review loops
- major cross-domain links

This should answer: **where should I go in the knowledge layer?**

### B. Domain browser
Show:
- domain identity and purpose
- domain index sections/topics
- recent and important notes
- canonical vs advisory vs generated note counts
- linked projects and active workspaces

This should answer: **what does this domain currently contain and how healthy is it?**

### C. Knowledge detail panel
Show:
- note content
- `knowledge_class`
- source/provenance posture
- domain placement
- linked projects, workspaces, and outputs
- chronology and promotion history where available

This should answer: **what is this knowledge object and why should I trust it?**

### D. Domain relationship browser
Show:
- cross-domain links
- repeated themes
- doctrine/project/technical intersections
- candidate cross-domain syntheses

This should answer: **how does this domain connect to the rest of ChaseOS knowledge?**

### E. Promotion-aware review surface
Show:
- notes lacking clear provenance
- synthesized notes needing strengthening
- generated ideas awaiting graduation
- domain indexes needing maintenance or re-linking

This should answer: **what knowledge work is incomplete, weak, or pending governance?**

---

## 8. Object and Typing Requirements

The knowledge navigator must not treat every markdown file under `02_KNOWLEDGE/` as the same object.

It should distinguish at least:
- `knowledge_domain`
- `knowledge_index`
- `knowledge_note`
- `knowledge_note_generated`
- `knowledge_note_synthesized`
- `knowledge_note_source_derived`
- `knowledge_lineage_trace`
- `knowledge_promotion_candidate`
- `knowledge_crosslink`

The point is not UI cosmetics.
The point is preventing epistemic flattening.

If the future standalone shows a generated idea, a promoted synthesis, and a domain anchor as if they were the same class of thing, the operator loses the very distinctions that make ChaseOS usable as an operating system.

---

## 9. Service-Layer Boundary Rules

### A. Domain indexes are navigation anchors, not disposable headings
The service layer should preserve domain indexes as special routing objects, not just the first note in a folder.

### B. Knowledge class must stay visible everywhere relevant
If a note is generated, synthesized, source-derived, or canonical-state-like, that posture must remain visible in list, detail, and relation views.

### C. Project relevance must not overwrite domain truth
A note may be highly relevant to one project while still belonging to a broader domain knowledge system.
Project linkage should be additive, not ownership-replacing.

### D. Workspace evidence must not silently masquerade as promoted knowledge
SIC workspaces may support or suggest knowledge, but workspace evidence and durable knowledge notes must remain visibly distinct.

### E. Provenance must stay close to the knowledge object
Operators should not have to leave the knowledge surface entirely just to answer “where did this come from?”
At least summary provenance should travel with the note.

### F. Promotion posture must remain governed
The knowledge navigator may expose promotion candidates or quality gaps, but it must not imply that browseability equals canonical promotion.

---

## 10. Relationship to Earlier Bridge Slices

This slice complements earlier passes by clarifying the knowledge-side half of the future standalone:

- the **project cockpit** shows what a project needs and is doing
- the **workspace browser** shows evidence/research environments
- the **provenance explorer** shows lineage and chronology in depth
- the **consolidated operator cockpit** shows what matters now operationally
- the **knowledge navigator** shows durable domain understanding and knowledge posture

Together these prevent the standalone from collapsing into either:
- a runtime dashboard with weak knowledge navigation, or
- a note browser that cannot respect operator/runtime/project boundaries.

---

## 11. Suggested Data Model Direction

This slice suggests ChaseOS likely needs higher-level standalone object families such as:
- `domain_browser_view`
- `knowledge_navigator_view`
- `knowledge_detail_view`
- `knowledge_health_item`
- `knowledge_promotion_item`
- `domain_crosslink_view`

Likely supporting derived records include:
- `domain_activity_summary`
- `knowledge_class_rollup`
- `project_domain_link_summary`
- `workspace_knowledge_link_summary`

These should be derived from vault truth and summary/provenance layers, not invented as detached standalone-only truth.

---

## 12. What This Application Pass Proves

This pass proves the markdown-to-standalone bridge can carry the knowledge layer forward as a first-class operator surface.

It clarifies:
- how domain indexes become domain browsers,
- how knowledge notes become typed knowledge objects,
- how provenance and promotion posture stay visible,
- how domain knowledge complements project/workspace/operator surfaces,
- and how the future standalone can support learning and durable reasoning without becoming a generic notes viewer.

---

## 13. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

### A. It preserves epistemic structure, not just file access
ChaseOS is not only a file system with dashboards.
It is a governed knowledge operating system.
This pass keeps the difference between domain anchors, durable knowledge, generated ideas, and supported/promoted knowledge legible.

### B. It complements project/workspace/operator surfaces with a true knowledge-side surface
Without this slice, the future standalone would be strong on execution and weak on understanding.
A real operating system needs both.

### C. It preserves constitutional layering between evidence, knowledge, and canonical state
This pass keeps SIC workspace evidence, durable knowledge notes, and higher-confidence promoted/canonical posture from collapsing into one generic content layer.
That is core ChaseOS discipline.

### D. It strengthens Phase 9 -> Phase 10 continuity
This is another concrete proof that current markdown knowledge architecture can map into a future standalone product shell without creating a second unmanaged truth system.

---

## 14. Recommended Next Application Passes

After this slice, the strongest next continuations would be:
1. **settings / provider-config / scaffold surfaces** to round out operator-facing product-shell functionality
2. **cross-panel object model consolidation** to refine how cockpit, knowledge, project, and runtime surfaces compose lower-level objects cleanly
3. **governed promotion / review center surfaces** so knowledge, approvals, provenance, and promotion pathways become one explicit review-oriented operator lane

---

## 15. Current Verdict

A future ChaseOS standalone should not force the operator to choose between:
- project/workspace operation,
- runtime/cockpit visibility,
- and domain knowledge navigation.

It should provide a **knowledge navigator / domain browser** that lets the operator:
- browse domains,
- inspect knowledge posture,
- understand provenance and promotion state,
- and move cleanly between durable knowledge, project context, and evidence context.

That is how the knowledge side aligns with the overall ChaseOS operating system.

---

*Graph links: [[Knowledge-Index]] · [[Markdown-to-Standalone-Bridge]] · [[Project-Cockpit-and-Workspace-Browser-Standalone-Application]] · [[Consolidated-Operator-Cockpit-Standalone-Application]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[ChaseOS-Studio-Architecture]]*

*Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
