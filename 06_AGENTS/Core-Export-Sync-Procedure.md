---
title: Core Export Sync Procedure
type: governance-procedure
status: active guidance — live repo remains primary; core export is long-term support lane
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
---

# Core Export Sync Procedure

> This procedure governs how the live ChaseOS personal repository and the long-term Core export lane should coexist.
> It exists to prevent framework-export work from displacing the primary mission: development of the live system.

---

## 1. Governing Rule

**The current ChaseOS repository remains the primary development surface and operational truth source.**

The Core export lane (`chaseos-core`, safe copies, template staging, and future public framework packaging) is a **long-term support feature**, not the main short-term execution lane.

---

## 2. Why This Procedure Exists

Once a safe copy or separate Core repo exists, a new risk appears:
- spending too much time exporting,
- duplicating effort across repos,
- letting framework packaging outrun live-system development,
- creating confusion about which repo holds the real current truth.

This procedure prevents that drift.

---

## 3. Repository Roles

### Live Personal Repo
This repository is for:
- active architecture work
- live runtime/governance changes
- current project/system truth
- logs, profiles, and operational documentation
- experimental implementation work

### Core Export Lane
This lane is for:
- sanitized framework extraction
- reusable templates/examples
- long-term forkability
- standalone-ready structural packaging
- docs/examples safe to publish or reuse

### Safe Copy / Backup Copies
These are for:
- redundancy
- protection
- restore points

They are not the main working surface unless explicitly promoted to that role.

---

## 4. Priority Order

When deciding what to work on next, use this order:

1. **Live current-repo development that affects actual ChaseOS capability**
2. **Truth-sync / architecture alignment in the live repo**
3. **Safety, routing, and governance work needed for the live repo**
4. **Template staging inside the live repo (`core_templates/`)**
5. **Core export / sibling repo packaging**

If export work is not supporting live development, it drops behind live-repo work.

---

## 5. When Core Export Work Is Appropriate

Core export work is appropriate when at least one of these is true:
- a live-repo feature has stabilized enough to be generalized
- a template/example is needed to clarify structure
- the export prevents future rework
- the user explicitly asks for framework extraction
- the export can be done without stealing focus from a more urgent live-repo need

If none are true, continue live-repo development instead.

---

## 6. Sync Discipline

### Live Repo -> Core
Allowed when:
- the material is reusable
- it has been sanitized
- it preserves navigation/routing clarity

### Core -> Live Repo
Allowed when:
- a framework clarification improves the live repo
- no personal-instance truth is overwritten incorrectly
- the change is intentionally reviewed, not blindly mirrored

### Backup / Safe Copies
Treat as recovery assets, not as implicit active branches.

---

## 7. Markdown and Standalone Continuity Rule

Whether work happens in the live repo or the Core lane, preserve:
- markdown routing
- index-note surfaces
- stable file roles
- standalone-ready machine-readable scaffolds

This keeps the system coherent across:
- current Obsidian use
- Core export/forkability
- future standalone ChaseOS surfaces

---

## 8. Recommended Working Pattern

For now:
- build and evolve features in the live repo first
- create or update example/template material in `core_templates/` when useful
- export only mature, sanitized pieces to `chaseos-core`
- treat any safe copy as backup, not as a competing development lane

---

## 9. Current Verdict

Core export is important, but it is **not the near-term priority lane**.

The live ChaseOS repo remains primary.
Core export continues as a controlled long-term feature.

---

*Graph links: [[Core-Personal-Split-Implementation-Plan]] · [[Vault-Map]] · [[CORE_MANIFEST]] · [[README]] · [[PROJECT_FOUNDATION]]*

*Core-Export-Sync-Procedure.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*