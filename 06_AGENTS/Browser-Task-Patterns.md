---
title: Browser Task Patterns
type: workflow-patterns
status: seeded — bounded task-pattern layer for autonomous browser work
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
---

# Browser Task Patterns

> Reusable bounded browser task classes for ChaseOS runtimes.
> These are patterns, not blanket permissions. A runtime still needs the right role card, allowed origins, and writeback boundaries.

---

## 1. Why These Patterns Exist

The browser surface is useful when it is:
- repeatable,
- scope-bounded,
- auditable,
- compatible with the Obsidian markdown/index structure,
- and later portable into standalone ChaseOS representations.

These patterns turn browser work from vague intent into declared task classes.

---

## 2. Pattern A — Declared URL Research Sweep

**Use when:** a runtime needs to read a small declared set of public URLs and produce a bounded summary.

**Inputs:**
- explicit URL list
- declared `allowed_origins`
- summary goal

**Actions:**
- navigate
- read page state
- extract visible text / structured content
- quarantine capture
- write operator brief

**Outputs:**
- quarantine captures under `03_INPUTS/00_QUARANTINE/`
- summary in `07_LOGS/Operator-Briefs/`
- audit trace in `07_LOGS/Agent-Activity/`

**Not allowed:** recursive crawling, login, submission, download.

---

## 3. Pattern B — Public Page Health Check

**Use when:** a runtime needs to confirm a known page remains available and structurally recognizable.

**Inputs:**
- declared URL
- expected page title/text/selector or state marker

**Actions:**
- navigate
- read title/url/visible text
- optional screenshot

**Outputs:**
- status note in runtime logs or operator brief
- optional screenshot reference

**Best for:** docs pages, reference pages, public dashboards, status pages.

---

## 4. Pattern C — Watchlisted Page Change Monitor

**Use when:** a runtime should watch an approved set of public pages for meaningful changes.

**Inputs:**
- watchlist entry from `runtime/browser_registry/watchlists/`
- allowed origin registration
- change criteria

**Actions:**
- navigate to known page
- capture title/text/selector snapshot
- compare to prior bounded state
- log change/no-change result

**Outputs:**
- change summary in `07_LOGS/Operator-Briefs/` or runtime-specific report paths
- audit activity
- optional quarantine capture for substantial content changes

**Not allowed:** adding new origins ad hoc during execution.

---

## 5. Pattern D — Known-Selector Structured Extraction

**Use when:** a public site has a stable layout and only a narrow slice of content matters.

**Inputs:**
- declared URL
- known selector targets
- extraction format

**Actions:**
- navigate
- extract bounded content by selector
- normalize result into markdown/json summary

**Outputs:**
- bounded extraction artifact
- quarantine/raw capture if needed
- brief or downstream runtime artifact

**Best for:** public docs, static release notes, known data blocks.

---

## 6. Pattern E — Evidence Screenshot Capture

**Use when:** a runtime needs visual evidence of a page state without acting on the page.

**Inputs:**
- declared URL
- reason for capture

**Actions:**
- navigate
- screenshot
- optional read of title/url

**Outputs:**
- screenshot artifact
- audit/event trail
- optional brief reference

**Note:** screenshots are evidence, not canonical truth by themselves.

---

## 7. Patterns Explicitly Excluded

These are not part of the approved bounded pattern set:
- recursive discovery crawl
- authenticated workflow automation
- payment/purchase workflows
- account management flows
- file download workflows
- credential-assisted browsing
- browser work that mutates canonical vault state directly

---

## 8. Index and Standalone Alignment

Each pattern should be representable in both:
- current markdown-first routing (`06_AGENTS/`, `runtime/`, `07_LOGS/`, `03_INPUTS/`), and
- future standalone/native runtime orchestration views.

That means every pattern should keep stable references to:
- governing policy docs
- machine-readable registry entries
- output index destinations
- runtime audit surfaces

### Summary-context application
For how watchlist change/no-change outputs, browser evidence captures, and monitored-source summaries should preserve bounded evidence posture in future standalone surfaces, see:
- `06_AGENTS/Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application.md`

---

*Graph links: [[Browser-Autonomy-Policy]] · [[Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application]] · [[Browser-Operator-Surface]] · [[Vault-Map]] · [[ChaseOS-Studio-Architecture]]*

*Browser-Task-Patterns.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*