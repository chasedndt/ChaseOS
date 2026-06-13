---
title: Core-Personal Split Implementation Plan
type: implementation-plan
status: active structural/export lane — candidate evidence exists, current target revalidation required, Git/publication gates separate
version: 0.2
created: 2026-04-24
updated: 2026-05-11
owner: Optimus
---

# Core-Personal Split Implementation Plan

> Concrete plan and status anchor for moving ChaseOS from a conceptual Core/Personal split to an active structural/export lane.
> This plan is written to preserve the current Obsidian markdown/index-note structure while also preparing a cleaner export path into a separate framework repository and later standalone ChaseOS surfaces.

---

## 1. Goal

Separate ChaseOS into two clearly managed layers:

### Core
The reusable, forkable, framework-level layer.

### Personal
The private, populated, operator-specific instance.

The split must preserve:
- current markdown path stability where needed
- Obsidian graph/index usability
- runtime routing via `06_AGENTS/Vault-Map.md`
- future standalone node/record portability

---

## 2. Current Reality

Current truth is no longer "conceptual only." The split is now an active structural/export development lane:
- the current repo remains the populated personal implementation and primary development surface,
- `CORE_MANIFEST.md` defines Core-included and Core-excluded categories,
- `core_export/export_manifest.yaml` and `core_export/core_candidate_inventory.yaml` provide allowlist and inventory machinery,
- `core_export/reports/latest/core-export-dry-run-report.json` records a 57-candidate scanner-clean dry-run preview packet,
- `core_export/reports/latest/core-export-feature-completion-tracker-2026-05-01.md` records local export verification history and `Git initialized: no`,
- `core_export/templates/**` and report previews provide sanitized/template-rendered Core output,
- the guarded local inspection target is `<CHASEOS_CORE_REPO>`, but its current path presence must be revalidated before any Git/publication step.

This plan therefore remains the structural doctrine anchor, but implementation has progressed beyond the seed stage. Remaining gates are license decision, public ignore policy, Git-init approval, public repo setup, push/publication, and canonical promotion.

---

## 3. Design Principles

1. **Do not break the current personal instance first.**
2. **Separate framework material by explicit inventory, not guesswork.**
3. **Preserve index-note and routing conventions.**
4. **Keep Core markdown-first and standalone-ready.**
5. **Treat sanitization as a first-class task, not an afterthought.**

---

## 4. What Belongs in Core

Core should contain reusable structure such as:
- folder conventions
- file naming conventions
- routing rules
- generic architecture docs
- generic governance docs
- templates and SOPs safe for publication
- runtime substrate code that is not user-specific
- example notes and example indexes
- fork guidance and setup guidance

Core should also preserve stable representations of:
- markdown index-note conventions
- routing anchors like `Vault-Map.md`
- machine-readable runtime scaffolds that are generic
- standalone bridge docs that describe how markdown structures map forward

---

## 5. What Belongs in Personal

Personal should contain:
- real identity files
- real `Now.md`
- real project OS files
- real knowledge notes
- real logs/history
- account-specific tool maps and registry data
- runtime records containing personal/private operational truth

---

## 6. Proposed Migration Strategy

### Phase A — Inventory and labeling
1. Create `CORE_MANIFEST.md` as the explicit framework inventory.
2. Stage safe framework-ready material under `core_templates/` inside the current repo.
3. Do not move live personal files yet.

### Phase B — Template shadow structure
1. Mirror top-level folders under `core_templates/`.
2. Add sanitized/example placeholders for files that must exist in every fork.
3. Add README files that explain what is template-safe vs personal-only.

### Phase C — Separate repository bootstrap
1. Create a sibling repository such as `chaseos-core`.
2. Copy only material listed in `CORE_MANIFEST.md`.
3. Verify no personal context is present.

### Phase D — Sync discipline
1. Define which docs are edited in Core first.
2. Define which docs remain personal-instance only.
3. Treat pull-through from Core to Personal as deliberate, reviewed sync — not uncontrolled overwrite.

---

## 7. Obsidian / Index-Structure Requirements

The split must preserve the idea that ChaseOS is currently navigated through:
- markdown paths
- wikilinks
- index notes
- `Vault-Map.md`
- stable folder roles

That means Core should not merely export files; it should export a **navigable markdown framework**.

At minimum, Core should preserve template/index concepts for:
- logs
- knowledge
- archive
- project structure
- runtime/governance docs

---

## 8. Standalone Preparation Requirements

The split should also prepare for the future standalone representation by ensuring that Core includes:
- stable document identities
- stable folder roles
- explicit routing docs
- example machine-readable registry/state scaffolds
- docs that explain how markdown/index structures map to future standalone nodes/records

This is why Core should include both markdown docs and selected runtime scaffolds.

---

## 9. Initial Deliverables for This Split

### Docs
- `06_AGENTS/Core-Personal-Split-Implementation-Plan.md`
- `CORE_MANIFEST.md`

### Template staging
- `core_templates/Core-Templates-Folder-Guide.md`
- `core_templates/00_HOME/HOME-Templates-Guide.md`
- `core_templates/01_PROJECTS/PROJECTS-Templates-Guide.md`
- `core_templates/02_KNOWLEDGE/KNOWLEDGE-Templates-Guide.md`
- `core_templates/06_AGENTS/AGENTS-Templates-Guide.md`
- `core_templates/07_LOGS/LOGS-Templates-Guide.md`
- `core_templates/runtime/Runtime-Templates-Guide.md`

### Future follow-up
- separate `chaseos-core` repo scaffold
- sanitized example files
- sync procedure doc

---

## 10. Risks

- accidental leakage of personal context into Core
- creation of dual truth if Core and Personal diverge without sync rules
- losing markdown/index navigability in the name of abstraction
- over-exporting runtime state that should remain personal-instance specific

---

## 11. Current Verdict

The correct move is:
1. **inventory first**,
2. **template-stage second**,
3. **separate repo third**.

Do not begin by moving files blindly. Begin by making the Core boundary explicit and navigable.

---

*Graph links: [[FORKING]] · [[Vault-Map]] · [[ChaseOS-Studio-Architecture]] · [[Runtime-Navigation-Map]] · [[Browser-Autonomy-Policy]]*

*Core-Personal-Split-Implementation-Plan.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*