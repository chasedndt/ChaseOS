---
title: Memory Editing and Curation Surfaces Standalone Application
type: implementation-bridge-plan
status: seeded — standalone application of memory editing and curation surfaces
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Memory Editing and Curation Surfaces Standalone Application

> This document applies the markdown-to-standalone bridge to the memory-maintenance side of ChaseOS.
> It defines how future standalone ChaseOS should let an operator review, curate, confirm, revise, or retire memory artifacts without collapsing memory-layer boundaries, bypassing governance, or treating all memory as equally editable.

---

## 1. Purpose

Earlier bridge/application slices now cover:
- runtime posture and lifecycle visibility
- workflows and role-card execution contracts
- coordination and ingress
- project/workspace surfaces
- provenance and chronology
- consolidated cockpit composition
- knowledge/domain navigation
- settings / provider-config / scaffold surfaces
- governed promotion / review center surfaces
- cross-panel object-model consolidation
- agent scorecards / runtime quality surfaces
- execution repair / failure recovery surfaces
- memory inspector / runtime-memory surfaces
- agent identity ledger surfaces
- graph-native node and edge consolidation surfaces

What was still missing was the explicit memory-maintenance lane:

**How should future standalone ChaseOS let the operator safely curate memory — confirming, pruning, reclassifying, or retiring memory entries — without violating the memory architecture, confusing memory with source truth, or turning the memory inspector into an ungoverned edit surface?**

This document answers that.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Agent-Memory-Architecture.md`
- `06_AGENTS/Claude-Memory-System.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`
- `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md`
- `06_AGENTS/Agent-Identity-Ledger-Surfaces-Standalone-Application.md`
- `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md`
- `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md`
- `06_AGENTS/Feature-Register.md` memory-inspector references
- future runtime-memory stores already named in doctrine:
  - `runtime/memory/repair/`
  - `runtime/memory/scorecards/`
  - `runtime/memory/adapters/[adapter-name]/identity-ledger.json`

Not included yet:
- live memory-editing UI implementation
- final mutation rules per memory store
- automatic pruning policies
- memory conflict-resolution engine
- final approval hooks for high-consequence memory edits

---

## 3. Why This Slice Is Needed

Without a dedicated memory-editing / curation pass, the future standalone would risk having:
- strong memory visibility,
- strong runtime-memory visibility,
- strong identity/repair/scorecard surfaces,

…but no explicit answer to:
- which memory layers are operator-curatable,
- what kinds of edits are safe,
- how stale or disproven memory should be revised,
- how memory maintenance differs from editing source truth,
- and what review/governance boundaries apply before a memory change should take effect.

A real memory-bearing operating system needs not only memory inspection.
It also needs a disciplined **memory-maintenance surface**.

---

## 4. Governing Rule

**Memory curation surfaces must preserve the distinction between inspectable memory, editable memory, and canonical source truth.**

That means:
- some memory may be operator-curatable,
- some memory may be runtime-maintained but operator-reviewable,
- some memory may be effectively derived and not directly editable,
- and canonical files or governance doctrine remain outside casual memory editing.

Short form:
- inspectability does not imply editability
- memory editing is not source-truth editing
- memory changes remain bounded by layer rules
- governance still outranks memory maintenance

---

## 5. Current Markdown- and Runtime-Era Roles Feeding Memory-Curation Surfaces

### A. Memory architecture layer
Provides:
- the five memory layers
- what belongs in each layer
- update rules and durability boundaries
- where memory may or may not be changed

### B. Runtime-memory boundary layer
Provides:
- what Hermes/runtime-local memory may hold
- what remains subordinate to ChaseOS canonical truth
- what should not be promoted casually

### C. Claude/user-memory maintenance layer
Provides:
- stale-memory update discipline
- correction/removal expectations
- the distinction between profile memory and current state

### D. Runtime learned-memory layers
Provide the memory families most likely to need curation surfaces:
- navigation memory
- scorecards
- repair memory
- identity-ledger material

### E. Memory-inspector layer
Provides:
- inspectable memory family boundaries
- the distinction between memory evidence and memory assertion
- the operator-facing inspection shell that curation would extend

---

## 6. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| memory architecture docs | Memory Curation Policy Surface | curation rules / editability matrix |
| user-memory maintenance rules | User Memory Curation Surface | user-memory maintenance panel |
| runtime-memory families | Runtime Memory Curation Surface | runtime-memory maintenance panel |
| learned-memory evidence | Memory Review Surface | memory review and confirmation queue |
| stale/corrected/retired memory concepts | Memory Lifecycle Surface | memory lifecycle / status panel |
| memory-evidence links | Memory Justification Surface | evidence-backed memory edit detail |

---

## 7. Recommended Standalone Surfaces

### A. Memory curation home
Show:
- which memory families are visible
- which are editable, review-only, or derived-only
- curation policies by layer
- outstanding stale or disputed memory items

This should answer: **what memory can be maintained here, and under what rules?**

### B. User-memory maintenance panel
Show:
- user-specific memory items
- stale/corrected/disputed markers
- operator correction workflow
- why an item exists and when it was last confirmed

This should answer: **how should user memory be reviewed or corrected?**

### C. Runtime-memory maintenance panel
Show:
- runtime-specific memory items
- navigation/repair/identity/scorecard-linked curation posture
- whether the item is directly editable, derived, or review-based
- links to supporting evidence

This should answer: **how should runtime memory be maintained without confusing it with source truth?**

### D. Memory review queue
Show:
- stale memory items
- disproven memory candidates
- provisional memory needing confirmation
- evidence conflicts
- pending curation decisions

This should answer: **what memory needs maintenance attention now?**

### E. Memory lifecycle panel
Show:
- proposed → confirmed → stale → corrected → retired posture
- who or what last changed the memory
- relationship between old and new entries

This should answer: **what lifecycle stage is this memory item in?**

### F. Memory evidence / justification drill-down
Show:
- linked incidents/history/provenance
- why a memory item was created
- why a correction is being suggested
- whether evidence is strong enough for confirmation or retirement

This should answer: **what evidence supports keeping, changing, or retiring this memory?**

---

## 8. Object and Typing Requirements

These surfaces should distinguish at least:
- `memory_curation_item`
- `memory_editability_item`
- `memory_review_item`
- `memory_lifecycle_item`
- `memory_correction_item`
- `memory_retirement_item`
- `memory_justification_item`
- `memory_dispute_item`
- `memory_confirmation_item`

The point is to avoid flattening:
- a stale user-memory item,
- a derived runtime scorecard,
- a repair-memory correction,
- and a canonical source contradiction

…into one generic “edit memory” action.

ChaseOS should treat memory curation as a typed maintenance workflow.

---

## 9. Service-Layer Boundary Rules

### A. Memory editability must be explicit by layer
Layer B user memory, Layer C runtime memory, and Layer E execution history should not all expose the same mutation affordances.

### B. Derived memory should remain distinct from directly maintained memory
A scorecard or derived trend may be operator-reviewable without being directly hand-edited.

### C. Memory changes must remain distinguishable from source-truth changes
Changing memory must not silently mutate project files, knowledge notes, doctrine, or runtime-state artifacts.

### D. Memory lifecycle state should remain legible
A stale memory item, a disputed memory item, and a retired memory item should not look like the same thing.

### E. Evidence-backed curation is required
High-value memory changes should remain drillable back to the history or evidence that justifies them.

### F. Memory maintenance must remain subordinate to governance and auditability
Memory curation may improve the system, but must not become an untracked side door around existing controls.

---

## 10. Relationship to Earlier Bridge Slices

This slice complements earlier passes by extending the memory-inspection and runtime-memory family into an explicit maintenance lane beside:
- the **memory inspector**, which shows what memory exists
- the **runtime quality surfaces**, which show derived performance memory
- the **repair/recovery surfaces**, which show learned repair patterns and failure state
- the **identity-ledger surfaces**, which show runtime behavioral evolution

Together these now imply a future standalone where the operator can inspect not only:
- what ChaseOS remembers,
- what it has learned about runtimes,
- and how those memories are structured,

but also:
- how memory should be curated responsibly over time.

---

## 11. Suggested Data Model Direction

This slice suggests ChaseOS likely needs higher-level standalone object families such as:
- `memory_curation_view`
- `memory_review_queue_view`
- `memory_lifecycle_view`
- `memory_editability_view`
- `memory_justification_view`
- `memory_correction_view`

Likely supporting derived records include:
- `memory_status_summary`
- `memory_staleness_summary`
- `memory_editability_summary`
- `memory_correction_summary`
- `memory_dispute_summary`
- `memory_retirement_summary`

These should be derived from memory-layer doctrine, machine-readable memory stores, and evidence/history surfaces — not invented as opaque standalone-only mutation state.

---

## 12. What This Application Pass Proves

This pass proves the markdown-to-standalone bridge can carry the memory-maintenance lane forward as a first-class operator surface.

It clarifies:
- how memory visibility can gain maintenance workflows without collapsing layer boundaries,
- how user memory and runtime memory can have different curation rules,
- how stale/disputed/retired memory can become explicit operating state,
- how memory curation can stay evidence-backed and audit-friendly,
- and how ChaseOS can feel more like a living memory-bearing operating system instead of a static memory snapshot.

---

## 13. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

### A. It gives ChaseOS a true memory-maintenance surface
A real memory-bearing operating system should not only expose memory — it should expose how memory is maintained.

### B. It preserves constitutional layering between memory, source truth, and governance
This pass explicitly keeps memory curation separate from canonical source editing and broader governance authority.
That is strongly ChaseOS-native.

### C. It strengthens Phase 9 -> Phase 10 continuity for memory operations
The existing memory architecture and memory-inspector direction now have a clearer continuation into operator-facing curation surfaces.

### D. It improves operator trust through controlled memory maintenance
The operator should be able to understand what can be changed, what should only be reviewed, what evidence supports the change, and how memory lifecycle status is evolving.
That is operating-system alignment, not just settings UX.

---

## 14. Recommended Next Application Passes

After this slice, the strongest next continuations would be:
1. **runtime-memory schema and storage consolidation surfaces** to unify nav maps, scorecards, repair memory, and identity ledgers under a clearer machine-readable family
2. **graph-backed operator canvas / whiteboard surfaces** to connect freeform investigation modes to governed graph-native structure
3. **governed memory-promotion and doctrine-candidate surfaces** to specify how confirmed lessons escalate toward broader doctrine without bypassing Gate discipline

---

## 15. Current Verdict

A future ChaseOS standalone should not stop at memory inspection.
It should also provide clear **memory editing / curation surfaces** where the operator can:
- review stale or disputed memory,
- correct or retire bounded memory items,
- understand memory lifecycle state,
- and maintain memory quality without confusing that work with editing canonical source truth.

That is how the memory-maintenance side aligns with the overall ChaseOS operating system.

---

*Graph links: [[Agent-Memory-Architecture]] · [[Claude-Memory-System]] · [[Hermes-Memory-Boundary]] · [[Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application]] · [[Agent-Identity-Ledger-Surfaces-Standalone-Application]] · [[Markdown-to-Standalone-Bridge]] · [[ChaseOS-Studio-Architecture]]*

*Memory-Editing-and-Curation-Surfaces-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
