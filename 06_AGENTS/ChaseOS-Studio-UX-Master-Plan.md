---
date: 2026-05-21
runtime: Codex
session_descriptor: studio-ui-master-plan
type: studio-ux-master-plan
status: ACTIVE / MASTER PLAN DRAFT / OPERATOR REVIEW REQUIRED
scope: ChaseOS Studio global shell, navbar IA, Command Center/Home, Memory/Graph direction, page cleanup, visual system
authority: docs/planning only; grants no runtime, approval, provider, browser, host, release, graph, memory, Agent Bus, or canonical write authority
---

# ChaseOS Studio UX Master Plan

## Purpose

This is the master UI plan for turning ChaseOS Studio into the actual user-facing MVP product shell.

It sits above the implementation handover and the feature-family normalization docs:

- `[[Finalize-ChaseOS-Studio-Product-UI-Handover]]` is the work-order checklist.
- `[[Studio-Product-UI-Feature-Family-Normalization]]` maps current panels to canonical feature families.
- `[[ChaseOS-Feature-Family-and-Subfeature-Inventory]]` is the capability inventory truth.
- This file defines the product shell, information architecture, page model, and design direction.

This file does not authorize UI implementation by itself. It is the planning node to review before the navbar and Dashboard/Home work starts.

## Current Repo-Truth Baseline

As of 2026-05-21:

- Studio has a working native shell and packaged `.exe` lane.
- Current Studio registry truth is 39 declared panels, 38 mounted panels, and 1 readiness-only panel.
- Feature-family deep reconciliation is complete at documentation/register level.
- The Dashboard is still an implementation/status console, not a product Command Center.
- The current sidebar is still shaped by mounted implementation panels rather than final product concepts.
- The confirmed top-level sidebar headings are:
  - Main
  - Knowledge Graph
  - Content
  - Runtime
  - Personal Memory
  - Governance
- Navbar and shell framing are implemented; Home/Command Center is implemented as Pass 2. Runtime group productization is implemented as Pass 4. Content and Personal Memory productization is implemented as Pass 5. Governance and Advanced productization is implemented as Pass 6. Visual design refinement is implemented as Pass 7. Chat, Workspaces, and Graph Hygiene were productized in `studio-ui-final-productization-closure`. `pass10b-pywebview-runtime-diagnostic` resolved the pythonnet fallback, and `studio-native-current-exe-all-page-proof-and-dev-copy-sweep` superseded the older native pixel-capture blocker with green current-EXE all-page proof: 38 mounted pages attempted, 0 failed. Remaining work is manual page review, duplicate screenshot hash review, route-specific product-depth polish, runtime/chat proof, and governed signing/installer/store/mobile/release lanes.
- Graph + Docs / Inspector have completed inspection/product-frame and clickthrough productization passes. The graph substrate is real and bounded, selected-node shell context is productized, but deeper graph workflows remain governed by existing evidence.
- Provider/model calls, browser dispatch, runtime dispatch, approval consumption, host/release mutation, graph/canonical promotion, and broad memory mutation remain governed by existing lower-layer evidence and must not be implied by UI labels.

## 2026-06-09 Source Remaster Coverage Audit Note

The source-level Studio UI remaster coverage is now verified across the current mounted shell:

- Current mounted shell count: `43` panels.
- Final source visual QA harness: `runtime/studio/final_productization_visual_qa.py`.
- Latest evidence folder: `07_LOGS/Visual-QA/2026-06-09-studio-source-remaster-coverage-audit/`.
- Result: `ok=true`, `86` screenshots, desktop and mobile proof for all `43` mounted panels.
- The broad visual QA report found no missing required tokens, no forbidden visible product-copy terms, no page errors, and no console errors.
- The harness authority report keeps provider calls, external actions, runtime dispatch, workflow execution, browser-control authority expansion, approval consumption, graph mutation, installer/startup mutation, schedule mutation, cron mutation, and Agent Bus task writes unavailable.

This note supersedes the older panel-count baseline in this document for source UI completion accounting only. It does not claim packaged/native wrapper proof, installer/signing/startup/autostart, public release packaging, live Hermes/OpenClaw chat response proof, or Strikezone schedule repair.

## 2026-05-22 Pass 1 Implementation Note

Pass 1, `studio-ui-navbar-ia-shell-framing`, is implemented and ready for operator review.

Source of truth for this pass: `%USERPROFILE%\Downloads\ChaseOS_Studio_Final_UI_Refactor_Master_Plan.md`.

Implemented:

- Locked the left sidebar to the six product navigation groups: Main, Knowledge Graph, Content, Runtime, Personal Memory, and Governance.
- Reframed implementation-facing panel labels into product-facing Studio labels while preserving existing routes where possible.
- Moved advanced/debug-oriented surfaces under Advanced Runtime or Governance / Advanced unless they are required in the main product IA.
- Added global shell framing for workspace selection, mode posture, command/search, active runs, approvals, review queue, quick create, and voice/mic readiness.
- Added a right object-inspector rail with read-only/direct-safe/proposal-only/approval-gated action posture language.

Not changed:

- Home/Command Center content and page internals were not redesigned in this pass.
- No provider/model call, browser dispatch, runtime dispatch, approval consumption, host/release mutation, graph/canonical promotion, memory mutation, or external action authority was added.
- Existing lower-layer safety and approval boundaries remain authoritative.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\panel_registry.py`
- Focused shell regression: `343 passed`.
- Desktop/mobile static visual QA captured to `C:\tmp\chaseos-studio-pass1-desktop.png` and `C:\tmp\chaseos-studio-pass1-mobile.png`.

## 2026-05-22 Pass 2 Implementation Note

Pass 2, `studio-ui-home-command-center-productization`, is implemented and ready for operator review.

Source of truth for this pass: `%USERPROFILE%\Downloads\ChaseOS_Studio_Final_UI_Refactor_Master_Plan.md`.

Implemented:

- Replaced the default Home/Dashboard renderer with a product-facing Command Center surface.
- Kept the visible sidebar label as `Home` while making the page model `Command Center`.
- Added the Home command prompt: `What do you want ChaseOS to do?`
- Added Command Center tabs for Overview, Inbox, Active Runs, Approvals, Recent Artifacts, and System Health.
- Added user-facing sections for attention queue, saved views, safe quick launch routes, approval queue summary, active run posture, recent artifacts, and system health.
- Moved Studio build/proof posture into a collapsed `Advanced Studio build status` detail instead of making implementation cards the default view.
- Hid the panel registry count banner from default Home.
- Kept runtime daemon controls visible only as a system-health/status block and preserved existing safe/approval-gated posture.

Not changed:

- Backend `get_dashboard()` data shape was not expanded or granted new authority.
- Graph, Docs / Inspector, Runtime, Content, Personal Memory, Governance, README, foundation docs, and guides were not productized in this pass.
- No provider/model call, browser dispatch, runtime dispatch, approval consumption, host/release mutation, graph/canonical promotion, memory mutation, or external action authority was added.
- Existing implementation proof data remains accessible through Logs / Audit, QA / Proof, advanced surfaces, or the collapsed build-status detail.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\panel_registry.py`
- Focused shell regression: `92 passed`.
- Localhost browser visual QA captured desktop/mobile screenshots under `07_LOGS/Visual-QA/2026-05-22-studio-ui-home-command-center-productization/`.
- Visual QA readback confirmed the Command Center prompt, tab model, command input, hidden registry banner, Overview/Runs tab behavior, zero console/page errors, and no mobile horizontal overflow.

## 2026-05-22 Pass 3 Implementation Note

Pass 3, `studio-ui-graph-docs-inspector-inspection`, is implemented and ready for operator review.

Implemented:

- Created `[[docs/audits/2026-05-22_studio_graph_docs_inspector_current_feature_inspection]]` as the current evidence-based Graph + Docs / Inspector capability audit.
- Added a product-facing Graph page header with purpose, action posture, search, Quick Switch, Filters, Docs / Inspector, Graph Hygiene, and Provenance controls.
- Kept graph filters hidden on initial Graph load and wired the visible Filters control to the existing `Ctrl+F` toggle path.
- Renamed the page-owned Node Inspector surface to `Docs / Inspector` in the visible page title and empty state.
- Added Docs / Inspector posture chips for formatted Markdown, backlinks, provenance, and metadata approval requests.
- Reworded node actions so unavailable attach/task/archive actions are disabled and approval-gated delete remains blocked unless an endpoint is mounted.

Not changed:

- No graph backend contract, parser, provenance implementation, graph hygiene executor, or approval-consumption behavior changed.
- No persisted graph engine, durable node ID writer, trust promotion, canonical graph mutation, provenance writeback, provider call, browser dispatch, workflow execution, approval consumption, host/release mutation, or memory mutation was added.
- Graph Hygiene, create-node, visual-link, metadata edits, archive/delete, and future attach/create-task actions remain direct-safe, proposal-only, approval-gated, blocked-with-reason, or coming-soon based on existing lower-layer evidence.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\api.py runtime\studio\shell\panel_registry.py`
- Focused Graph/Docs regression: `51 passed`.
- Focused frontend shell regression: `36 passed`.
- Desktop/mobile Playwright visual QA captured Graph, Graph Filters, and Docs / Inspector screenshots under `07_LOGS/Visual-QA/2026-05-22-studio-ui-graph-docs-inspector-inspection/`.
- Visual QA confirmed `Graph` title, filters hidden initially, Filters opening on click, live graph canvas data (`6` nodes / `5` links), `Docs / Inspector` title, no page errors, and only Chromium WebGL `ReadPixels` performance warnings.

## 2026-05-22 Pass 3B Implementation Note

Pass 3B, `studio-ui-graph-docs-inspector-clickthrough-productization`, is implemented and ready for operator review.

Implemented:

- Added visible Graph `Local Graph` controls for All / 1 hop / 2 hop.
- Wired a session-scoped local-focus depth override into the existing graph filter path.
- Rendered selected graph/doc node context in the global object inspector.
- Added direct-safe selected-node actions for Open, Focus Graph, Pin Focus, Provenance, and Copy ID / Path.
- Kept Attach, Create Task, Archive, and Delete visibly disabled/gated.
- Preserved existing graph-click navigation into Docs / Inspector.

Not changed:

- No backend API, graph write, canonical promotion, graph hygiene execution, archive/delete execution, task creation, memory attachment, provider call, browser dispatch, runtime dispatch, approval consumption, host/release mutation, or external delivery authority was added.
- Object-inspector contexts for tasks, runs, approvals, artifacts, sources, and memory items remain later page-pass work.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\api.py runtime\studio\shell\panel_registry.py`
- Focused Graph/Docs regression: `54 passed`.
- Focused frontend shell regression: `36 passed`.
- Combined focused shell slice: `90 passed`.
- In-app Browser desktop/mobile visual QA captured selected-node and local-focus screenshots under `07_LOGS/Visual-QA/2026-05-22-studio-ui-graph-docs-inspector-clickthrough-productization/` with zero console error/warn logs.

## 2026-05-22 Pass 4 Implementation Note

Pass 4, `studio-ui-runtime-tasks-runs-productization`, is implemented and ready for operator review.

Implemented:

- Renamed the visible `Runtime Cockpit` page header to `Agents / Runtimes`.
- Renamed the visible `AOR Executions` page header to `Tasks & Runs`.
- Added product subtitles and action-posture chips to Agents / Runtimes, Tasks & Runs, Schedules, and Agent Bus.
- Added a Tasks & Runs board view grouped into Done, Needs Review, Failed, and Other lanes.
- Added selected-object inspector contexts for runs, runtime cards, schedules, and Agent Bus tasks.
- Kept unsafe runtime actions visibly disabled or approval-gated in the right inspector.
- Added a Runtime operating overview above runtime cards.

Not changed:

- No runtime start/stop/restart, Agent Bus task write/claim/dispatch, schedule mutation, retry/resume, approval consumption, provider/model call, browser dispatch, host/release mutation, external delivery, graph/canonical writeback, or memory mutation authority was added.
- Backend Runtime, AOR, Schedules, and Agent Bus APIs were not changed.
- Content, Personal Memory, Governance, README, project foundation, and guides were not productized in this pass.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\api.py runtime\studio\shell\panel_registry.py`
- Focused Runtime shell regression: `240 passed, 1 skipped`.
- In-app Browser desktop/mobile visual QA captured Runtime, Tasks & Runs, Agent Bus, and mobile board screenshots under `07_LOGS/Visual-QA/2026-05-22-studio-ui-runtime-tasks-runs-productization/` with zero console error/warn logs.

## 2026-05-23 Pass 5 Implementation Note

Pass 5, `studio-ui-content-personal-memory-productization`, is implemented and ready for operator review.

Implemented:

- Reframed Content page headers into product-facing labels: `Intake`, `Capture`, `Sources`, and `Research Collections`.
- Reframed Personal Memory page headers into product-facing labels: `Memory Manager`, `Context Import`, `Memory Ledger`, `Proactive Briefings`, and `Review Queue`.
- Added product subtitles and action-posture chips across Content and Personal Memory surfaces.
- Added selected-object inspector contexts for captures, intake items, sources, research collections, memory ledger entries, runtime memory cards, proactive briefing lanes, and review queue items.
- Added disabled/gated inspector actions for attach, create task, promote, archive, and delete where lower-layer authority is not mounted.
- Added product overview framing for Context Import and Memory Ledger so these pages read as memory operations, not implementation proof cards.

Not changed:

- No backend API, source ingestion, external acquisition, Visual Capture Markdown write executor, downstream AOR dispatch, Personal Map mutation, memory promotion, Agent Bus enqueue, schedule trigger, provider/model call, browser dispatch, approval consumption, host/release mutation, graph/canonical writeback, or external delivery authority was added.
- Existing CLI commands, proof logs, guarded write lanes, and approval-gated capture/source workflows remain governed by existing lower-layer evidence.
- Governance/Advanced, README, project foundation, and guides were not productized in this pass.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\api.py runtime\studio\shell\panel_registry.py`
- Focused Content + Personal Memory shell regression: `217 passed`.
- In-app Browser DOM/interaction QA checked Capture, Intake, Sources, Research Collections, Memory Ledger, Proactive Briefings, Review Queue, and Runtime Memory Inspector routes with zero console error/warn logs.
- Browser screenshot capture timed out; Playwright fallback captured desktop/mobile screenshots under `07_LOGS/Visual-QA/2026-05-23-studio-ui-content-personal-memory-productization/` with zero console error/warn logs and zero bad resource responses.

## 2026-05-23 Pass 6 Implementation Note

Pass 6, `studio-ui-governance-advanced-productization`, is implemented and ready for operator review.

Implemented:

- Reframed Governance page headers into product-facing labels: `Approvals`, `Logs / Audit`, `Decisions`, `Settings`, `Feature Audit`, `Workflow Registry`, and `Role Cards`.
- Reframed Advanced / Advanced Runtime surfaces that were still implementation-facing: `Site Skills`, Browser Runtime, Runtime Navigation, Workspace Entry, App Launcher, and QA / Proof.
- Added product subtitles and compact action-posture chips across Governance and Advanced surfaces.
- Added selected-object inspector contexts for approvals, audit logs, decisions, feature rules, workflows, role cards, provider config posture, runtime navigation maps, Site Skill runs/approvals, App Launcher surfaces, Browser Runtime records, and Workspace Entry signals.
- Kept proof/debug evidence accessible through Logs / Audit, QA / Proof, Workflow Registry, Role Cards, Feature Audit, App Launcher, and advanced drawers without making implementation proof cards the default product face.

Not changed:

- No backend API, approval decision write, approval consumption, workflow execution, runtime dispatch, Agent Bus write, provider/model call, browser control, Site Skill deployment, host/release mutation, graph/canonical writeback, memory mutation, settings write, permission mutation, trust-tier mutation, or external delivery authority was added.
- README, project foundation, and user guides were not rewritten in this pass.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\api.py runtime\studio\shell\panel_registry.py`
- Focused Governance + Advanced shell regression: `492 passed`.
- Browser DOM/interaction QA loaded the static harness and selected the Approval inspector.
- Browser screenshot capture timed out; Playwright fallback captured desktop/mobile screenshots under `07_LOGS/Visual-QA/2026-05-23-studio-ui-governance-advanced-productization/` with zero console error/warn logs and zero bad resource responses.

## 2026-05-23 Pass 7 Implementation Note

Pass 7, `studio-ui-visual-design-refinement`, is implemented and ready for operator review.

Implemented:

- Added product shell state tokens for live, read-only, approval-gated, coming-soon, blocked, and focus-ring states.
- Added a compact ChaseOS Studio wordmark mark in the top shell without introducing a new image asset or brand-locking final logo work.
- Converted visible sidebar acronym tiles into CSS-rendered product glyphs while preserving existing nav labels, routes, ARIA labels, and `data-state` posture.
- Added state dots to sidebar icons so live/read-only/approval-gated/coming-soon/blocked posture is visible without changing authority.
- Tightened topbar quick-create, voice readiness, help, and settings controls into icon-framed buttons.
- Refined topbar status, panel status pills, authority chips, shared title rows, empty states, loading states, and generic error states for better density, contrast, and text fit.
- Added visual-design regression coverage for tokens, nav icon mappings, topbar icon framing, status chips, shared page template behavior, and empty/loading/error state styling.

Not changed:

- No backend API, provider/model call, browser dispatch/control, runtime dispatch, Agent Bus write, approval decision write, approval consumption, workflow execution, source ingestion, memory mutation, graph/canonical writeback, host/release mutation, settings write, permission mutation, trust-tier mutation, or external delivery authority was added.
- Page content models were not redesigned in this pass; this was a global shell and shared visual-system refinement pass.
- README, project foundation, and user guides were not rewritten.
- No final logo, illustration system, or marketing hero surface was introduced.

Verification:

- `node --check runtime\studio\shell\frontend\app.js`
- `python -m py_compile runtime\studio\shell\api.py runtime\studio\shell\panel_registry.py`
- Focused visual + Governance regression: `10 passed`.
- `git diff --check`
- In-app Browser DOM/screenshot QA loaded the static harness, selected `Approvals`, confirmed nav icon acronym text is visually hidden, product glyphs render, shell status/empty-state rules load, and no horizontal overflow or page errors were observed.
- Browser desktop screenshot captured under `07_LOGS/Visual-QA/2026-05-23-studio-ui-visual-design-refinement/`.
- Browser mobile screenshot capture timed out; Playwright fallback captured refreshed desktop/mobile screenshots and readbacks under the same visual QA directory with zero console error/warn logs.

## 2026-05-23 Pass 8 Implementation Note

Pass 8, `studio-ui-packaged-proof-closure-update`, is partial and blocked on packaged runtime remediation.

Implemented:

- Verified `dist/studio/ChaseOS-Studio.exe` exists and recorded current SHA-256: `9fd0ed3e6f890c154fe1acdf6b27c98929b926a1e0dab63aa5966f67980e979d`.
- Preserved the bounded packaged launch smoke evidence under `07_LOGS/Visual-QA/2026-05-23-studio-ui-packaged-proof-closure-update/`.
- Tightened packaged proof tooling so markdown/approval sentinel deltas are reported and block green status instead of being side details.
- Tightened packaged visual QA runtime-error classification so packaged pywebview `pythonnet` failures are explicit.
- Tightened installer-plan evidence selection so newer `07_LOGS/Visual-QA` packaged visual QA reports override stale green legacy reports from `Studio-Graph-Views`.
- Regenerated installer-plan evidence as blocked against the latest packaged visual QA.

Blocked evidence:

- Current packaged visual QA starts and terminates the owned `.exe` process, but no native screenshot is captured.
- Startup log reports: `You must have pythonnet installed in order to use pywebview.`
- Screenshot proof is missing: `07_LOGS/Visual-QA/2026-05-23-studio-ui-packaged-proof-closure-update/2026-05-23-studio-ui-packaged-proof-visual-qa.png`.
- The packaged visual QA sentinel observed markdown modifications during the final run in:
  - `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
  - `06_AGENTS/ChaseOS-CLI-Operator-Handbook.md`

Not changed:

- No Home/Command Center, graph, runtime, content, memory, governance, or page-internal UI redesign was performed in this pass.
- No installer was created.
- No signing, startup/autostart, registry, shortcut, approval consumption, workflow execution, provider/model call, connector call, Agent Bus task write, graph/canonical write, memory mutation, host/release mutation, or external-delivery authority was added.

Verification:

- `python -m pytest runtime\studio\test_packaged_app_launch_smoke.py runtime\studio\test_packaged_app_visual_qa.py runtime\studio\test_installer_plan.py -q` -> `43 passed`.
- `python -m py_compile runtime\studio\packaged_app_launch_smoke.py runtime\studio\packaged_app_visual_qa.py runtime\studio\installer_plan.py`.
- `node --check runtime\studio\shell\frontend\app.js`.
- `python -m pytest runtime\studio\shell\test_studio_visual_design_refinement.py -q` -> `6 passed`.
- `git diff --check`.
- `python -m runtime.cli.main studio packaged-app-visual-qa ... --write-evidence --json` -> blocked with explicit pywebview/pythonnet runtime dependency, missing native screenshot, and markdown sentinel delta.
- `python -m runtime.cli.main studio installer-plan ... --write-evidence --json` -> blocked because latest packaged visual QA is not green and screenshot evidence is missing.

## 2026-05-23 Pass 10B PyWebView Runtime Diagnostic Note

`pass10b-pywebview-runtime-diagnostic` is implemented and verified.

Implemented:

- Forced the Studio packaged shell onto the pywebview Qt backend with `PYWEBVIEW_GUI=qt`, `QT_API=pyqt6`, and `webview.start(gui="qt", ...)`.
- Added Qt backend preflight logging to `CHASEOS_STUDIO_STARTUP_LOG` so future packaged startup failures report the real Qt import error instead of falling through to WinForms/pythonnet.
- Added PyQt6, PyQt6-WebEngine, and qtpy to Studio packaging extras.
- Removed stale packaging guidance that suggested installing `pythonnet`.
- Rebuilt `dist/studio/ChaseOS-Studio.exe`.

Verified:

- New executable SHA-256: `4f5c2dbd8d1e6aa4cb114524736fdc319b4f1a46ddeb72319bdc39afcc0e7820`.
- Packaged launch smoke passed with no markdown or approval artifact sentinel changes.
- Packaged native visual QA passed: screenshot captured, nonblank verification passed, Studio content sentinel passed, startup log absent, runtime error status `not_applicable`, no markdown or approval artifact sentinel changes.
- Installer-plan evidence is green again and reports `ready_for_governed_installer_design`.

Not changed:

- No installer was created.
- No signing, startup/autostart, registry, shortcut, approval consumption, workflow execution, provider/model call, connector call, Agent Bus task write, graph/canonical write, memory mutation, host/release mutation, or external delivery was added.

## Product Principle

ChaseOS Studio should have one global shell and object-specific surfaces inside it.

The user should not feel like they are browsing implementation passes, CLI proof cards, or internal readiness contracts. They should feel like they are operating a local-first AI control plane with clear objects, queues, approvals, memory, sources, runtimes, and evidence.

Implementation evidence still matters, but it belongs in details drawers, Logs / Audit, QA / Proof, and advanced governance surfaces.

## Global Shell Model

| Shell area | Product purpose | Implementation rule |
|---|---|---|
| Top header | Workspace switcher, global command/search, active runs indicator, quick create, notifications, profile/settings. | Add only after navbar/Home shape is accepted. Global command must create intent/proposal objects unless a governed executor already exists. |
| Left sidebar | Main navigation using the six confirmed headings. | Use product labels, not acronyms or pass names. Keep advanced/debug surfaces collapsed or under Governance. |
| Main canvas | Current object surface: Command Center, workspace, task board, graph, source pack, memory node, run, approval, artifact, settings page. | Each page must show user objects first and implementation evidence second. |
| Right inspector | Details for selected task, run, approval, memory node, artifact, source, tool, runtime, or graph node. | Do not reintroduce an always-visible global inspector that conflicts with the current Node Inspector overhaul. Use page-local or object-triggered inspector behavior. |
| Bottom / overlay layer | Command palette, quick create, logs drawer, shortcut help, and temporary run/output drawers. | Keep overlays nonblocking, dismissible, and safe. No hidden execution authority. |

## Core Product Objects

The UI should organize around objects the operator understands.

| Object | Meaning in Studio | Typical inspector details |
|---|---|---|
| Workspace | Current vault/project/context/mode. | Mode, project, graph/source/memory counts, linked tasks, current approvals. |
| Task | Human or agent work item. | Status, owner/runtime, source context, approvals, output artifacts, logs. |
| Run | Runtime/AOR/Agent Bus execution or proof run. | Runtime, inputs, outputs, trace, errors, cost/latency when available, authority posture. |
| Approval | Governed decision packet. | Requested action, exact digest/scope, target path, status, markers, allowed executor. |
| Agent / Runtime | Hermes, OpenClaw, Codex, Archon, future runtimes. | Health, daemon state, policies, capabilities, queue, recent runs. |
| Source | Captured/imported/reviewed material. | Provenance, trust, transformations, source pack status, downstream readiness. |
| Memory node | Durable memory/doc/fact/ledger entry. | Trust state, backlinks, extracted facts, attached work, provenance. |
| Artifact | Output file, proof card, deck, report, generated stub, UI proof. | Source run, owner, status, path, preview, follow-up actions. |
| Tool / MCP | Capability endpoint or server. | Permission class, test calls, secrets boundary, blocked authority. |
| Automation / Schedule | Repeatable work trigger. | Next run, disabled/enabled state, approval/export posture, history. |
| Mission / Workflow Pack | Repeatable product workflow over a goal. | Pack type, local runs, approval gates, artifacts, resume state, external deferrals. |

## Navbar IA Draft

Use the six confirmed headings. Product labels can change after operator confirmation, but implementation acronyms should not be the default UI.

### Main

- [ ] Command Center
- [ ] Chat
- [ ] Workspaces
- [x] Missions
- [ ] Builder / Canvas
- [x] Extensions

Notes:

- `Command Center` replaces the current Dashboard concept. If the operator prefers, the visible label can remain `Home`, but the page model should be Command Center.
- `Builder / Canvas` is the creation/editing surface for generated outputs, artifacts, previews, and future deploy/history flows. It should not bypass Chaser Forge, Workflow Packs, or governed generation lanes.
- `Extensions` maps to Chaser Forge local governed MVP. Public marketplace remains deferred.

### Knowledge Graph

- [ ] Graph View
- [ ] Node Inspector
- [ ] Knowledge Boxes
- [ ] Graph Hygiene
- [ ] Provenance

Notes:

- `Knowledge Boxes` is a planned product abstraction, not yet a verified feature family.
- Graph mutation must remain approval-gated.
- Persisted graph storage remains deferred until separately evidenced.

### Content

- [x] Intake
- [x] Capture
- [x] Sources
- [x] Research Collections
- [ ] Artifacts

Notes:

- `Capture` should include Visual Capture Markdown, but the default UI should not expose pass numbers.
- `Sources` should be the acquisition/source pipeline surface.
- `Research Collections` maps to SIC workspaces/source intelligence.
- `Artifacts` can be a cross-feature output browser if it becomes durable enough; otherwise keep it inside Command Center/Logs until built.
- 2026-05-24 source-render QA verified Intake, Capture, Sources, and Research Collections across desktop/mobile and proved desktop right-inspector selection where selectable objects exist.

### Runtime

- [x] Agents / Runtimes
- [x] Tasks
- [x] Agent Bus
- [x] Automations / Schedules
- [x] Runs
- [x] Browser Runtime
- [x] Site Skills
- [ ] Tools / MCP

Notes:

- `Agents / Runtimes` should surface Hermes/OpenClaw/Codex/Archon posture, daemon state, and capability boundaries.
- `Tasks` and `Runs` are currently productized together as `Tasks & Runs`; they can be split later only if the operator needs separate work-management and proof-run workflows.
- `Browser Runtime`, `Site Skills`, and `Tools / MCP` should remain advanced or visibly gated if operator-facing readiness is not clean enough.

### Personal Memory

- [x] Memory Manager
- [ ] Memory Graph
- [x] Memory Ledger
- [x] Context Import
- [x] Runtime Memory
- [x] Proactive Briefings
- [x] Review Queue
- [ ] Companion Surface

Notes:

- Personal Memory is a product grouping, not one canonical feature family.
- It spans Agent Memory Architecture, Personal Context Import, Pulse, companion memory, and runtime memory.
- Memory mutation must remain governed and evidence-backed.
- `Companion Surface` remains advanced/readiness-only until promoted.

### Governance

- [x] Approvals
- [ ] Policies / Permissions
- [x] Logs / Audit
- [x] Decisions
- [x] Workflow Registry
- [x] Role Cards
- [x] Feature Audit
- [x] QA / Proof
- [x] Settings
- [x] Advanced

Notes:

- Governance is where implementation evidence belongs.
- Settings must not hide operational queues, approvals, or runtime state.
- QA / Proof remains useful for development and operator verification, but it should not dominate the first-run product experience.

## Command Center / Home Model

Command Center is the operating desk. It is not a basic dashboard and not a build-status page.

### Top command input

User-facing concept:

```text
What do you want ChaseOS to do?
```

Required behavior:

- [ ] Include workspace/context selector.
- [ ] Generate an inspectable intent/proposal/action spec first.
- [ ] Show required approval or blocked authority before execution.
- [ ] Never imply direct provider/runtime/browser/host execution unless that lane is verified.

### Command Center tabs

- [ ] Overview
- [ ] Inbox
- [ ] Active Runs
- [ ] Approvals
- [ ] Recent Artifacts
- [ ] System Health
- [ ] Quick Launch

### Command Center layout

| Section | UI treatment |
|---|---|
| Active runs strip | Horizontal cards for running/recent runtimes, daemons, tasks, and proof runs. |
| Main tabs | Overview, Inbox, Active Runs, Approvals, Recent Artifacts, System Health. |
| Left mini panel inside page | Saved views, filters, workspace mode, object type, status. |
| Center canvas | Queue, timeline, board, artifact list, or health grid depending on tab. |
| Right inspector | Selected run/task/artifact/approval details. |

### What Command Center must show

- [ ] Current workspace identity and mode.
- [ ] Next actions requiring the operator.
- [ ] Pending approvals and blocked lanes.
- [ ] Active/recent runs and daemon health.
- [ ] Source/intake items needing review.
- [ ] Graph hygiene issues needing decision.
- [ ] Recent artifacts with provenance.
- [ ] Compact system health across agents, schedules, graph, approvals, and vault.

### What Command Center must remove from default view

- [ ] Internal portable MVP closure banner.
- [ ] Release-grade action-center grids.
- [ ] Raw CLI command snippets.
- [ ] Localhost/native launch command cards.
- [ ] Closure gate / manual acceptance / decision packet paths.
- [ ] Panel registry count banners.
- [ ] Implementation pass names and raw JSON evidence paths.

Move that material to:

- Governance -> Logs / Audit
- Governance -> QA / Proof
- Settings -> Advanced
- Collapsed Studio Build Status drawer only if still operationally useful

## Memory And Graph Direction

The Memory and Knowledge Graph areas should combine Obsidian-style navigation with AI-native memory controls.

| Surface | Inspired by | ChaseOS version |
|---|---|---|
| Global graph | Obsidian graph | Shows all memory/docs/nodes in a workspace with trust and authority overlays. |
| Local graph | Obsidian local graph | Shows connections around the selected doc/node/task/source/run. |
| Formatted Markdown viewer | Obsidian/Notion | Renders markdown beautifully, not raw text. Current Node Inspector markdown rendering is the baseline. |
| Backlinks panel | Obsidian backlinks | Shows which tasks, runs, docs, approvals, and artifacts reference this node. |
| Context attach control | AI workspace pattern | Attaches selected memory/source/node to a task, run, agent, workspace, or proposal. |
| Extraction panel | AI-native addition | Shows facts, entities, summaries, chunks, embeddings/source fragments, and confidence/provenance. |

### Memory page model

- [ ] Memory Manager: user-facing review and apply surface for personal/context memory candidates.
- [ ] Memory Graph: graph-local memory view with filters for trust, source, runtime, domain, and workspace mode.
- [ ] Memory Node Detail: markdown, provenance, backlinks, extracted facts, attached tasks/runs, and governed actions.
- [ ] Memory Ledger: durable memory records with trust state and authority boundary visible.
- [ ] Runtime Memory: runtime profile, scorecard, nav map, repair memory, and recent task-local context.
- [ ] Context Import: review-first import workflow for personal context exports and route candidates.
- [ ] Proactive Briefings: Pulse cards/decks and schedule proof without proof-language in default labels.
- [ ] Review Queue: pending Pulse/memory/context candidates and feedback items.

### Memory non-claims

- [ ] Do not imply automatic Personal Map writes.
- [ ] Do not imply canonical memory promotion without approval evidence.
- [ ] Do not imply runtime brain mutation unless the exact lane is verified.
- [ ] Do not treat generated facts as verified facts without source/trust state.

## Page Cleanup Standard

Every product page should answer five questions without requiring the user to understand implementation history.

| Question | Page requirement |
|---|---|
| What am I looking at? | Product title and one-sentence purpose in user language. |
| What exists here? | Current objects, queues, cards, runs, nodes, artifacts, or source items. |
| What needs attention? | Next action, blockers, approvals, warnings, failed checks. |
| What can I safely do? | Primary safe action row with clear authority badge. |
| What is the evidence? | Details drawer or inspector with logs, paths, commands, digests, tests, and source contracts. |

### Page productization checklist

- [ ] Remove pass names from default visible copy.
- [ ] Remove raw implementation command snippets from default cards.
- [ ] Replace acronyms with product labels unless the acronym is paired with plain English.
- [ ] Move paths, command contracts, digests, markers, JSON evidence, and test names into details.
- [ ] Keep authority badges compact and consistent.
- [ ] Add empty states that explain what is missing in product terms.
- [ ] Keep blocked/gated status visible, but do not make blocked implementation lanes the whole page.
- [ ] Verify text fit and no overlap in desktop and mobile.

## Visual System Direction

This is a product tool, not a marketing page.

- [ ] Wordmark: use `ChaseOS Studio` as the product shell name unless the operator intentionally chooses a public alias.
- [ ] Logo: create or select a durable ChaseOS Studio mark before release-grade packaging.
- [ ] Icons: use consistent familiar icons for nav/actions; no acronym-only nav prefixes such as `FG`, `WP`, or `CM`.
- [ ] Color: dark product shell, neutral surfaces, restrained accents, status colors with clear meaning.
- [ ] Background: stable, quiet, high-contrast work surface. Avoid decorative gradients that reduce scanability.
- [ ] Cards: 8px radius or less unless existing system requires otherwise. No cards inside cards.
- [ ] Typography: compact operational scale; no hero-sized type inside panels.
- [ ] Status language: `read-only`, `approval-gated`, `blocked`, `executing`, `complete`, `proof-only`, `deferred`.
- [ ] Responsive rule: fixed-format controls need stable dimensions; labels must not overflow or overlap.

## Implementation Sequence

### Pass 0 - Feature truth and panel mapping

- [x] Complete feature-family deep reconciliation.
- [x] Normalize Studio panel-to-feature-family mapping.
- [x] Create finalization handover/checklist.
- [x] Create this UX master plan.

### Pass 1 - Navbar IA and global shell framing

- [x] Implement six-heading sidebar.
- [x] Rename default labels to product language.
- [x] Hide or collapse dev/debug surfaces under Governance / Advanced.
- [x] Add top shell framing and right object inspector rail.
- [x] Preserve route IDs and authority boundaries.
- [x] Run static/frontend checks and visual QA.

### Pass 2 - Command Center / Home implementation

- [x] Replace current Dashboard content with Command Center model while keeping visible `Home` label.
- [x] Add workspace identity, next actions, active runs, approvals, recent artifacts, health, and quick launch.
- [x] Move build/release/proof content into details rather than default cards.
- [x] Verify desktop/mobile visual layout.

### Pass 3 - Graph + Docs / Inspector framing

- [x] Inspect current Graph and Docs / Inspector capability evidence.
- [x] Productize Graph and Docs / Inspector headers, controls, and authority language.
- [x] Keep Graph write, archive/delete, provenance writeback, and canonical mutation governed.
- [x] Verify desktop/mobile visual layout.

### Pass 3B - Graph + Docs / Inspector clickthrough

- [x] Add Local Graph controls.
- [x] Add selected-node object-inspector context.
- [x] Add direct-safe and disabled/gated selected-node actions.
- [x] Verify desktop/mobile clickthrough behavior.

### Pass 4 - Runtime and Tasks/Runs cleanup

- [x] Productize Agents / Runtimes.
- [x] Productize Tasks & Runs board and run inspector context.
- [x] Productize Agent Bus task view and inspector context.
- [x] Productize Schedules view and inspector context.
- [x] Preserve no runtime execution, no Agent Bus writes, no schedule mutation, and no approval consumption.
- [x] Verify desktop/mobile visual layout.

### Pass 5 - Content and Personal Memory cleanup

- [x] Productize Intake, Capture, Sources, Research Collections, and related artifact/source views.
- [x] Make Visual Capture Markdown visible as a real Capture capability without exposing pass-number evidence as the default face.
- [x] Productize Memory Manager, Context Import, Memory Ledger, Runtime Memory, Proactive Briefings, and Review Queue.
- [x] Keep memory mutation and canonical writeback governed.

### Pass 6 - Governance and Advanced cleanup

- [x] Productize Approvals, Logs / Audit, Decisions, Settings, QA / Proof, Feature Audit, Workflow Registry, Role Cards, App Launcher, and remaining Advanced surfaces.
- [x] Keep implementation proof accessible without making it the default product face.

### Pass 7 - Visual design pass

- [x] Apply icon system.
- [x] Apply status color and badge system.
- [x] Apply page template.
- [x] Add missing empty/loading/error states.
- [x] Check contrast, spacing, text fit, and no-overlap rules.

### Pass 8 - Packaged proof and closure update

- [x] Run focused frontend/static checks.
- [x] No page-internal rendered QA required in this pass because no Studio page UI files changed; Pass 7 desktop/mobile visual evidence remains the current page-render proof.
- [x] Run packaged `.exe` smoke/visual proof only with bounded authorization; launch smoke passed, native visual proof blocked before clickthrough by pywebview/pythonnet and missing screenshot evidence.
- [x] Update closure criteria only with evidence; installer-plan evidence is now blocked by the latest packaged visual QA.
- [x] Keep full desktop/card UI open because packaged visual blockers are verified, not deferred.

### Pass 9 - Final backlog page productization and package truth refresh

- [x] Productize Chat as a command surface with workspace context, runtime lane posture, safe actions, and advanced proof details collapsed.
- [x] Productize Workspaces as a workspace hub with sprint focus, pinned workspaces, domain grouping, and read-only/no-migration posture.
- [x] Productize Graph Hygiene as a review workspace with decision-draft flow and advanced evidence details.
- [x] Add desktop/mobile source-render QA for Chat, Workspaces, and Graph Hygiene.
- [x] Rebuild `dist/studio/ChaseOS-Studio.exe` after source changes; current SHA-256 is `e270921e2e4cff990c12e0710ee9d12c58b6bf98f51a98fa175093612984e412`.
- [x] Correct native shell local frontend loading to `file:///` URI.
- [x] Strengthen package QA so title-bar-only screenshots and timestamp-only markdown touches cannot overclaim readiness.
- [x] Preserve no provider/model/browser/runtime/approval/graph/memory/installer/signing/startup/release authority expansion.
- [ ] Native packaged pixel capture remains blocked: UI Automation sees loaded shell text, but bitmap capture is black/near-uniform in this environment.
- [ ] Final installer/release readiness remains blocked until packaged native visual QA is green.

### Pass 10 - Runtime health sync, Chat continuity, and Home fail-open

- [x] Add shared read-only Hermes/OpenClaw runtime liveness that combines Agent Bus heartbeat, lifecycle/registry/env gateway ports, fast TCP probes, and Studio PID-file evidence.
- [x] Detect WSL-hosted Hermes on the registry gateway port `9119` instead of relying only on Studio PID files or default lifecycle ports.
- [x] Detect OpenClaw gateway TCP liveness on the lifecycle port `18789`.
- [x] Keep dispatch readiness stricter than gateway liveness; stale/missing heartbeats display as `gateway live / heartbeat required`.
- [x] Update Chat runtime controls so they no longer tell the operator a runtime is simply "not running" when a gateway is live.
- [x] Add visible Chat folders and previous chats/thread rows to the product surface.
- [x] Make Home/Command Center render a safe fail-open shell immediately.
- [x] Use a lightweight Studio API dashboard model for Home so heavy evidence panels do not block first paint.
- [x] Capture desktop/mobile source-render screenshots for Home and Chat.
- [ ] Restore fresh Hermes/OpenClaw Agent Bus heartbeats; runtime chat dispatch remains blocked until heartbeat freshness is proven.

### Pass 11 - Runtime heartbeat coordination repair

- [x] Bind Studio-launched runtime daemon commands to the selected vault root with explicit `--vault-root`.
- [x] Launch daemon subprocesses from the selected vault root so packaged/source launches do not depend on the app working directory.
- [x] Surface stale coordination-watch state in the shared runtime live-status model.
- [x] Show `heartbeat repair required` when a gateway is live but the coordination-watch state is stale.
- [x] Preserve the dispatch gate: gateway liveness does not equal chat dispatch readiness.
- [x] Verify current live state: Hermes gateway is live in WSL on `9119`; OpenClaw gateway probes open on `18789`; both Agent Bus heartbeats remain stale until a real watch loop is relaunched.
- [ ] Fresh persistent Agent Bus heartbeats are not restored by this documentation/code pass because starting long-running watch loops remains an operator/approval-controlled runtime action.

### Pass 12 - Operator runtime watch relaunch controls

- [x] Keep Studio runtime relaunch on the selected-vault direct daemon path rather than switching to the lifecycle supervisor while supervisor watch execution still resolves repo root internally.
- [x] Treat a fresh selected-vault Agent Bus heartbeat as already running and do not spawn a duplicate daemon.
- [x] Block duplicate daemon launch when a Studio PID file points to a live process but no fresh selected-vault heartbeat is visible.
- [x] Clean only stale selected-vault `runtime/lifecycle/run/{runtime}-coordination-watch.json` state before a governed relaunch.
- [x] Fix Chat daemon start/stop controls so start and stop both use the approval modal before phase-two execution.
- [x] Fix runtime daemon card stop controls so stop no longer calls the approval-gated API as if it were direct-safe.
- [x] Verify focused runtime/Chat tests and read-only dispatch status.
- [ ] Persistent Hermes/OpenClaw watch relaunch was not performed: automated live start was rejected because auto-approval plus OpenClaw task claiming is a governed runtime side effect.

### Pass 13 - Operator-approved live heartbeat verification

- [x] Receive explicit operator approval for short live heartbeat restoration.
- [x] Check open Agent Bus tasks before relaunch: Hermes `0`, OpenClaw `0`.
- [x] Start selected-vault Hermes daemon watch loop with `synthesize=false`.
- [x] Start selected-vault OpenClaw daemon watch loop with `synthesize=false`.
- [x] Clean stale Hermes coordination-watch state before relaunch.
- [x] Verify Hermes heartbeat fresh, gateway online, coordination-watch running, and dispatch ready.
- [x] Verify OpenClaw heartbeat fresh, gateway online, coordination-watch running, and dispatch ready.
- [x] Verify Phase 11 Chat dispatch status moved to `VERIFIED / DISPATCH CHAIN WIRED / RUNTIME ONLINE`.
- [ ] Long-duration heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.
- [ ] Agent Bus fault-source/rework analysis remains a separate session.

### Pass 14 - Chat live runtime sync productization

- [x] Add a Chat `Live Runtime Sync` product section for Hermes and OpenClaw.
- [x] Render gateway port, heartbeat state, and dispatch readiness as separate user-facing facts.
- [x] Refresh read-only runtime availability before Chat preview rendering so live status is visible in the product desk.
- [x] Gate Chat send readiness for bus runtimes that lack fresh heartbeat/runtime receive posture.
- [x] Keep gateway-only runtimes visible but blocked for dispatch.
- [x] Update desktop/mobile source-render QA mocks and evidence output for this pass.
- [x] Verify Hermes live on `127.0.0.1:9119`, OpenClaw live on `127.0.0.1:18789`, and both dispatch ready via read-only runtime verification.
- [x] Preserve no provider/model calls, runtime dispatch, Agent Bus task writes, approval consumption, memory/graph/canonical mutation, installer/startup/release mutation, or external delivery.
- [ ] Long-duration heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.
- [ ] Packaged native visual QA for this exact UI state remains unverified.

### Pass 15 - Workspaces product polish

- [x] Add `Workspace Operating Context` so the page states local workspace root, sprint source, safe action, and read-only/no-write authority in product language.
- [x] Add `Workspace Readiness` so project index, Now.md, sprint focus, vault writes, and provider calls are visible without exposing implementation pass evidence as the default face.
- [x] Wire pinned workspace rows and domain/project rows to the right inspector as selected product objects.
- [x] Preserve Workspaces as read-only: no project writes, migrations, status mutation, source promotion, task creation, provider/model calls, Agent Bus writes, approval consumption, graph/memory/canonical mutation, installer/startup/release mutation, or external delivery.
- [x] Refresh desktop/mobile source-render visual QA evidence for Chat, Workspaces, and Graph Hygiene under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting a Workspaces project card updates the right inspector on desktop.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Mobile right-inspector interaction remains unverified because the mobile rendered pass is screenshot/token validation only.

### Pass 16 - Tasks & Runs inspector polish

- [x] Add `Run Operating Context` so Tasks & Runs states audit source, visible run count, safe action, and read-only authority in product language.
- [x] Add `Run Readiness` so audit reads, audit writes, pipeline trigger, canonical mutation, inspector selection, and scanned records are visible without making implementation proof the whole page.
- [x] Keep board, list, and timeline run objects selectable and keyboard-accessible.
- [x] Wire run selection to the right inspector with direct-safe run-proof posture.
- [x] Refresh desktop/mobile source-render visual QA evidence for Chat, Workspaces, Graph Hygiene, and Tasks & Runs under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting a Tasks & Runs card updates the right inspector on desktop.
- [x] Preserve Tasks & Runs as read-only: no retry/resume, runtime dispatch, approval consumption, Agent Bus writes, audit writes, provider/model calls, graph/memory/canonical mutation, installer/startup/release mutation, or external delivery.
- [ ] Agents / Runtimes cockpit page was not changed in this pass.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Mobile right-inspector interaction remains unverified because the mobile rendered pass is screenshot/token validation only.

### Pass 17 - Agents / Runtimes product polish

- [x] Add `Runtime Operating Context` so Agents / Runtimes states worker profiles, live workers, heartbeat freshness, capability gates, source model, and safe action in product language.
- [x] Add `Runtime Feature Coverage` so capability-level feature-family coverage is visible for Runtime, Agent Bus, Chat dispatch readiness, Personal Memory, Governance, and Advanced Runtime surfaces.
- [x] Add `Runtime Capability Gates` so lifecycle, startup-surface, Agent Bus readiness, and provider/config readiness categories are visible without exposing every blocked command as the default page face.
- [x] Enrich runtime cards with heartbeat freshness, platform/mode, last heartbeat, health source, keyboard-selectability, and right-inspector selection.
- [x] Keep system details collapsed so raw drift, logs, post-reboot indicators, startup cards, and authority flags remain accessible without dominating the product UI.
- [x] Refresh desktop/mobile rendered visual QA evidence for Chat, Workspaces, Graph Hygiene, Tasks & Runs, and Agents / Runtimes under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting an Agents / Runtimes runtime card updates the right inspector on desktop.
- [x] Preserve no runtime start/stop/restart, runtime dispatch, Agent Bus task write/claim/enqueue, provider/model call, approval decision, approval consumption, memory/graph/canonical mutation, installer/startup/release mutation, browser control, MCP execution, host mutation, or external delivery.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Long-duration Hermes/OpenClaw heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.

### Pass 18 - Agent Bus product polish

- [x] Add `Bus Operating Context` so Agent Bus states visible queue count, open lanes, active lanes, worker heartbeat readback, source model, and safe action in product language.
- [x] Add `Bus Readiness` so queue readback, worker heartbeat readback, task write/claim/dispatch blocks, approval-consumption block, and provider/browser block are visible as direct-safe product facts.
- [x] Add `Agent Bus Feature Coverage` so Runtime, Chat dispatch substrate, Workflow Packs, and Governance/audit coverage are represented at capability level.
- [x] Productize the default queue as `Coordination Queue` with task cards, route/owner/priority/created metadata, request preview, and explicit no-claim/no-dispatch/no-approval-consumption boundary language.
- [x] Productize heartbeats as `Worker Heartbeats` with runtime/instance freshness evidence and stale-or-missing state without implying Studio can start or repair workers from this page.
- [x] Productize events as `Audit Stream` so task events are evidence/readback, not an implementation console.
- [x] Wire queue cards to the right inspector with direct-safe selected-bus-task posture.
- [x] Refresh desktop/mobile rendered visual QA evidence for Chat, Workspaces, Graph Hygiene, Tasks & Runs, Agents / Runtimes, and Agent Bus under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting an Agent Bus task card updates the right inspector on desktop.
- [x] Preserve no task write, claim, dispatch, retry, cancellation, workflow execution, approval consumption, provider/model call, browser control, graph/memory/canonical mutation, installer/startup/release mutation, host mutation, or external delivery.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Long-duration Hermes/OpenClaw heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.
- [ ] Agent Bus fault-source/rework analysis remains a separate runtime session.

### Pass 19 - Schedules product polish

- [x] Add `Schedule Operating Context` so Schedules states local schedule intents, enabled/disabled count, runtime targets, schedule-state log source, and safe inspection posture in product language.
- [x] Add `Schedule Readiness` so intent readback, state-change audit readback, approval-gated enable/disable, cron/runtime dispatch block, and Agent Bus/provider/delivery write blocks are visible without turning the page into a raw manifest console.
- [x] Add `Schedule Feature Coverage` so Scheduled Briefing Pipelines, Scheduling Intent Architecture, Operator Runtime/AOR, Phase 11 Chat control lanes, and Governance/audit coverage are represented at capability level.
- [x] Productize schedule intent cards with workflow/command, cadence, runtime target, owner, approval posture, explicit no-run/no-cron/no-Agent-Bus/no-approval-consumption boundary language, keyboard selection, and right-inspector selection.
- [x] Productize schedule detail with read-only cadence/runtime/provenance/state-change evidence and action-boundary chips.
- [x] Refresh desktop/mobile rendered visual QA evidence for Chat, Workspaces, Graph Hygiene, Tasks & Runs, Agents / Runtimes, Agent Bus, and Schedules under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting a Schedules card updates the right inspector on desktop.
- [x] Preserve no schedule enable/disable mutation, cron mutation, external scheduler mutation, runtime dispatch, workflow execution, Agent Bus task write, approval consumption, provider/model call, browser control, graph/memory/canonical mutation, installer/startup/release mutation, host mutation, or external delivery.
- [ ] Two existing schedule YAML data-quality warnings remain outside this UI pass: `runtime/schedules/sch-events-watch-every-minute.yaml` has invalid `allowed_workflow_task_types`, and `runtime/schedules/sch-strikezone-acquisition-0550.yaml` starts with a BOM that the current loader rejects.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Long-duration Hermes/OpenClaw heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.

### Pass 20 - Missions / Workflow Packs product polish

- [x] Reframe the `Workflow Packs` page as the product-facing `Missions` surface while preserving the existing route and Workflow Packs API contract.
- [x] Add `Mission Operating Context` so Missions states local pack count, local run count, review queue count, proof card count, approval/resume posture, and safe mission inspection language.
- [x] Add `Mission Readiness` so local pack registry, local artifact writes, review queue, proof cards, exact-once marker reservation, approved local resume, and external/runtime/provider blocks are visible without turning the page into a raw implementation console.
- [x] Add `Mission Pack Coverage` so VentureOps/Missions, Product Workflow Packs, Governance approval lanes, AOR proof evidence, and Workspace Mode framing are represented at capability level.
- [x] Productize mission pack cards for Visual Product & Creative Studio, Founder / Personal Automation Audit, Research-to-Product Intelligence Engine, and Safe Agent Runtime Governance Kit with explicit no-provider/no-browser/no-external-delivery/no-Agent-Bus/no-runtime-dispatch boundaries.
- [x] Wire mission pack, local run, review queue, and proof card selections to the right inspector with direct-safe selected Mission object posture.
- [x] Refresh desktop/mobile rendered visual QA evidence for Chat, Workspaces, Missions, Graph Hygiene, Tasks & Runs, Agents / Runtimes, Agent Bus, and Schedules under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting a Mission pack card updates the right inspector on desktop.
- [x] Preserve no workflow execution, runtime dispatch, Agent Bus task write, approval consumption, provider/model call, browser action, graph/canonical/memory mutation, host mutation, release/startup mutation, external action, or external delivery authority.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Long-duration Hermes/OpenClaw heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.

### Pass 21 - Chaser Forge / Extensions product polish

- [x] Reframe the `Chaser Forge` page as the product-facing `Extensions` surface while preserving the existing route and Forge API contract.
- [x] Add `Extension Operating Context` so Extensions states local catalog, local library, governed install, manual static artifacts, proof chain, and blocked authority posture in product language.
- [x] Add `Extension Readiness` so approved extension points, manifest validation, protected-core guards, local catalog/library/install, manual static distribution, proof-chain coverage, and blocked remote/provider/runtime authority are visible without turning the page into an implementation console.
- [x] Add `Extension Capability Coverage` so Chaser Forge, local marketplace, remote distribution foundation, static-host publication proof, Governance approval lanes, and Interface / Experience Layer coverage are represented at capability level.
- [x] Productize extension object cards for Forge foundation, local library, governed install, static distribution, proof chain, and blocked authority with explicit no-network/no-provider/no-Agent-Bus/no-protected-core/no-payment/no-canonical authority boundaries.
- [x] Wire extension object cards to the right inspector with direct-safe selected Extension object posture.
- [x] Preserve local digest-bound proof/write lanes while fixing Chaser Forge published static index registration digest/write compatibility: digest calculation now excludes write-state fields and Windows test paths no longer exceed local path limits.
- [x] Align Studio static-host upload receipt and published-index registration wrapper chains so receipt statements use the same declared static base URL.
- [x] Refresh desktop/mobile rendered visual QA evidence for Chat, Workspaces, Missions, Extensions, Graph Hygiene, Tasks & Runs, Agents / Runtimes, Agent Bus, and Schedules under the pass-specific evidence folder.
- [x] Add rendered interaction proof that selecting an Extension object card updates the right inspector on desktop.
- [x] Preserve no ambient remote exchange, network fetch/upload, external registry mutation, untrusted third-party package exchange, payment/license mutation, provider/model call, Agent Bus dispatch, runtime policy write, protected-core mutation, installer write, approval consumption expansion, Pulse/Personal Map/R&D mutation, graph/canonical mutation, or external delivery authority.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Browser direct-file validation remains blocked by Browser URL policy; localhost static shell check loaded the route but cannot render pywebview-backed data without the Studio API bridge.
- [ ] Long-duration Hermes/OpenClaw heartbeat stability remains unverified.
- [ ] Actual end-to-end Chat message response remains unverified.

### Pass 22 - Content + Personal Memory source-render QA sweep

- [x] Extend `runtime/studio/final_productization_visual_qa.py` beyond the prior Main/Runtime sweep so it covers Content and Personal Memory product surfaces.
- [x] Source-render verify desktop/mobile screenshots for Chat, Workspaces, Missions, Extensions, Graph Hygiene, Intake, Capture, Sources, Research Collections, Tasks & Runs, Agents / Runtimes, Agent Bus, Schedules, Memory Manager, Memory Ledger, Context Import, Proactive Briefings, and Review Queue.
- [x] Add desktop right-inspector interaction checks for Intake, Sources, Research Collections, Memory Manager, Memory Ledger, Proactive Briefings, and Review Queue, plus empty-state acceptance for Capture when no recent captures exist.
- [x] Confirm all required product labels and authority-posture tokens render without missing text, console errors, page errors, blank screenshots, selector failures, or interaction failures.
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical mutation, memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, or external delivery authority.
- [ ] Packaged native visual QA for this exact UI state remains unverified.
- [ ] Browser direct-file validation was not repeated because this pass changed the QA harness and register truth, not the frontend shell; source-render Playwright screenshots are the evidence for this pass.
- [ ] The two existing schedule YAML data-quality warnings remain separate from this UI QA pass.

### Pass 23 - Developer text, navbar collapse, and sizing polish

- [x] Add rendered QA blockers for visible developer-era copy such as `read-only`, `MVP`, `proof`, raw runtime commands, `Logs / Audit`, `Dashboard`, and `Node Inspector`.
- [x] Add a source UI product-copy polish layer that normalizes static and dynamic visible copy, tooltips, ARIA labels, and placeholders into product-facing language.
- [x] Rename visible governance surfaces to `History / Audit` and `Quality Review` while preserving existing routes.
- [x] Fix source markup so Home is the initial active panel and Graph/Docs panels cannot visually flash as the active page before shell boot.
- [x] Reset the right object inspector on page changes so selected Docs / Inspector or node context does not stick on Home.
- [x] Smooth sidebar collapse/open behavior with grid/sidebar transitions, ARIA/title synchronization, and non-abrupt label/header collapse.
- [x] Add desktop shell interaction proof for Docs / Inspector -> Home route reset and sidebar collapse/open state.
- [x] Improve product-page width constraints and fix History / Audit search field styling and empty/mock count.
- [x] Refresh desktop/mobile source-render visual QA across the expanded panel set, including Home, History / Audit, and Quality Review.
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical mutation, memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, or external delivery authority.
- [ ] Packaged native `.exe` visual QA for this exact source state remains unverified.
- [ ] Long-duration Hermes/OpenClaw heartbeat stability, end-to-end Chat response, Agent Bus fault-source analysis, and schedule YAML data repair remain separate runtime/data sessions.

### Pass 24 - Packaged/native current-EXE all-page proof and startup-copy remediation

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Run strict current-EXE packaged/native all-page visual QA with no markdown-sentinel or visual-readiness retries.
- [x] Identify the concrete remaining current-EXE blocker: 15 routes exposing startup/loading copy `Preparing Studio`.
- [x] Replace packaged startup/loading copy with product-facing shell copy: `Opening workspace` and `Local shell ready`.
- [x] Rebuild `dist/studio/ChaseOS-Studio.exe` with SHA-256 `550223DA0082D616EF6F9695631415F8B1FA61F2B23CF27071526FFA946248CF`.
- [x] Rerun targeted remediation proof for the 15 failed routes: 15 pages, 0 failed.
- [x] Rerun strict current-EXE all-page proof: 38 mounted pages attempted, 0 failed, all screenshots written, owned processes terminated.
- [x] Update current-truth docs so older native pixel-capture blocker language is superseded.
- [ ] Manual screenshot review remains open because final proof reports 29 unique screenshot hashes for 38 routes and a duplicate hash group among some advanced/personal-memory routes.
- [ ] Route-specific product-depth polish remains open for pages that intentionally share advanced shells or still need stronger feature-family specificity.
- [ ] Actual end-to-end Chat message response, long-duration Hermes/OpenClaw heartbeat stability, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

### Pass 25 - Native proof hardening and current product-facing route proof

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Treat the remaining issue as proof quality and UI-productization blockers rather than a goal tracker blocker.
- [x] Harden packaged/native screenshot proof so `PrintWindow` capture is preferred and duplicate route screenshot groups fail the proof.
- [x] Add visible-copy guards for `read only` / `readonly` and startup/loading guards for `Opening workspace` / `Loading...`.
- [x] Isolate all-page proof temp directories by route and retry while keeping final proof on the stable default WebView2 runtime path.
- [x] Productize Role Cards visible labels and details so raw `readonly` role slugs and raw YAML detail no longer appear as the product UI.
- [x] Add bounded Tasks & Runs history loading so local run-history failures resolve to a stable unavailable state instead of a visible loading state.
- [x] Remove startup overlay copy that remained visible to UI Automation during native capture.
- [x] Rebuild/prove the current packaged EXE with SHA-256 `424FD8B0ED38A0B73FE19A6C29C63C189CAB53BDFB68B046241E2006F6EBD145`.
- [x] Verify all 38 mounted product routes through chunked packaged/native visual QA: 38 pages, 38 unique panel IDs, 38 screenshots, 0 failed pages, 0 forbidden-copy failures, 0 startup/loading failures, and 0 duplicate screenshot groups.
- [x] Record aggregate evidence at [[2026-05-26-studio-native-final-product-facing-proof-v7-aggregate]].
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical mutation, memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, signing, release promotion, or external delivery authority.
- [ ] Manual operator page-by-page visual acceptance remains open.
- [ ] Actual end-to-end Chat response, long-duration Hermes/OpenClaw heartbeat stability, Agent Bus fault-source analysis, schedule YAML data repair, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

### Pass 26 - Product-facing copy polish and fresh packaged native proof

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Tighten visible product-copy normalization for developer-era terms including `not mounted`, `Shell action`, raw `chaseos studio` command text, and `--json`.
- [x] Remove Proactive Briefings raw command blocks from the user-facing panel.
- [x] Reword Proactive Briefings proof/write/read-only copy into verification, available controls, change-request, and inspect language.
- [x] Add packaged/native visual QA guards for `not mounted`, `shell action`, and `--json`.
- [x] Rebuild/prove the current packaged EXE with SHA-256 `0D5089A55292E5EF5D4C37E4B3F937D4D17BF983542E3C7BEF4E1F1F610B25B7`.
- [x] Verify focused product-copy tests: `49 passed`.
- [x] Verify targeted high-risk native proof: 10 pages, 0 failed.
- [x] Verify Proactive Briefings final native proof: 1 page, 0 failed, no forbidden visible copy, no markdown or approval artifact writes.
- [x] Verify combined native screenshot coverage across all 38 mounted routes through the partial final all-page sweep, missing-route chunk, and isolated Site Skills confirmation.
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical/memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, signing, release promotion, or external delivery authority.
- [x] Superseded in Pass 27: a single monolithic green all-page JSON report now exists for the current rebuilt EXE and all 38 mounted routes.
- [ ] Manual operator page-by-page visual acceptance remains open.
- [ ] Actual end-to-end Chat response, long-duration Hermes/OpenClaw heartbeat stability, Agent Bus fault-source analysis, schedule YAML data repair, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

### Pass 27 - Single-launch packaged/native proof harness completion

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Diagnose the single-launch all-page proof blocker as a QA harness completion issue, not a failed product page.
- [x] Replace bridge-only batch scheduling with direct Qt timer callbacks and route-level trace logging.
- [x] Replace blocking batch route navigation with async Qt WebEngine `runJavaScript`.
- [x] Bound PyInstaller `_MEI*` temp cleanup so large locked native runtime folders are recorded as deferred instead of blocking report completion.
- [x] Add fast Windows `System.Drawing` sampled screenshot analysis for all-page native proof reports, with the pure-Python PNG decoder retained as fallback.
- [x] Normalize fallback QA route text for legacy route IDs (`build-logs`, `qa-proof`, `pulse-schedule-proof`) to product-facing labels.
- [x] Rebuild/prove the current packaged EXE with SHA-256 `EC00E4F598DA3FDA996A8269771606912AB062CA6602A221268D21B08441B263`.
- [x] Verify focused harness and shell tests: `46 passed`.
- [x] Verify two-route single-launch smoke proof: 2 pages, 0 failed.
- [x] Verify full single-launch packaged/native proof: 38 mounted routes, 38 screenshots, 38 unique route screenshots, 0 failed pages, no markdown writes, no approval artifact writes.
- [x] Record final proof at [[2026-05-26-studio-single-launch-batch-all-pages-proof-v4]].
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical/memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, signing, release promotion, or external delivery authority.
- [ ] Manual operator page-by-page visual acceptance remains open.
- [ ] Actual end-to-end Chat response, long-duration Hermes/OpenClaw heartbeat stability, Agent Bus fault-source analysis, schedule YAML data repair, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

### Pass 28 - Operator-review targeted page polish

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Treat the remaining issue as product-depth polish on target pages rather than a goal tracker blocker.
- [x] Add reusable operator-surface overview/card/lane components for sparse product pages.
- [x] Productize Agent Identity with runtime identity posture, Hermes/OpenClaw/Codex lanes, and no-mutation runtime identity language.
- [x] Productize App Launcher with a product surface index covering Main, Knowledge Graph, Content, Runtime, Personal Memory, and Governance.
- [x] Productize Approvals with watched-lane queue state and remove visible command-style prompt copy from the default page.
- [x] Productize History / Audit with an activity-history landing view instead of a blank or hidden-right-panel state.
- [x] Productize Quality Review with a real product-facing quality hub instead of static placeholder text.
- [x] Productize Runtime Navigation with Chat handoff, Agent Bus, Memory readback, and approval-boundary lanes.
- [x] Productize Workflow Registry with a registry landing view and immediate fallback before application programming interface hydration.
- [x] Productize Workspace Entry with immediate fallback cards and overview before application programming interface hydration.
- [x] Rebuild/prove the packaged EXE with SHA-256 `1303A70257F183DBB764E1456C7484A48BCAFFBA34B05DB2E2077B35C16F9A63`.
- [x] Verify focused Studio tests: `46 passed`.
- [x] Verify targeted packaged/native proof for 8 changed pages: 8 pages, 0 failed, no forbidden visible copy, no startup/loading visible copy, no approval artifact writes, no non-ignored Markdown writes.
- [x] Record final evidence at [[2026-05-26-studio-operator-review-targeted-polish-v4]].
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical/memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, signing, release promotion, or external delivery authority.
- [x] Superseded in Pass 29: fresh all-38-route single-launch native proof is green for the rebuilt current EXE.
- [ ] Manual operator page-by-page visual acceptance remains open.
- [ ] Actual end-to-end Chat response, long-duration Hermes/OpenClaw heartbeat stability, Agent Bus fault-source analysis, schedule YAML data repair, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

### Pass 29 - Current EXE all-page proof and sparse surface gap sweep

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Run a fresh pre-edit all-38-route single-launch packaged/native proof against the Pass 28 EXE.
- [x] Review the all-page contact sheet for remaining sparse/default product surfaces.
- [x] Productize Docs / Inspector with a first-paint landing surface for formatted Markdown, connections, and safe actions.
- [x] Productize Browser Runtime with first-paint readiness, authority-boundary, readiness-signal, and future-work cards.
- [x] Productize Provenance with origin/trust/evidence-chain cards for empty/default record states.
- [x] Productize Memory Ledger with runtime coverage, task context, and memory-governance cards.
- [x] Productize Sources with first-paint source channel and recent-run cards covering Visual Capture, Web and Files, Research Collections, Collection Preview, and Source Activity.
- [x] Productize Review Queue with first-paint candidate preflight, approval handoff, and Agent Bus boundary cards.
- [x] Add native-shell QA mode detection for packaged visual proof.
- [x] Defer Review Queue live hydration until after first paint and skip live hydration during native visual QA so proof cannot stall on bridge readiness.
- [x] Rebuild/prove the packaged EXE with SHA-256 `EB913AA5D62499A3678B0FAE4D6033EF285B95B11A138B16F370A93E2622983B`.
- [x] Verify focused Studio tests: `46 passed`.
- [x] Verify targeted Review Queue and Sources packaged/native proof after the bridge guard: 2 pages, 0 failed.
- [x] Verify fresh full single-launch packaged/native proof: 38 mounted routes, 38 screenshots, 38 unique route screenshots, 0 failed pages, no markdown writes, no approval artifact writes.
- [x] Record final proof at [[2026-05-26-studio-final-exe-all-pages-product-depth-v1]].
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical/memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, signing, release promotion, or external delivery authority.
- [ ] Manual operator page-by-page visual acceptance remains open.
- [ ] Actual end-to-end Chat response, long-duration Hermes/OpenClaw heartbeat stability, Agent Bus fault-source analysis, schedule YAML data repair, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

### Pass 30 - Product sync fallback and all-page final proof

- [x] Confirm the active Studio UI remaster goal state: active, not blocked.
- [x] Treat the remaining blocker as proof/product-sync quality rather than a goal tracker block.
- [x] Add first-paint product-facing sync fallback surfaces for approval, runtime, Agent Identity, Source Intelligence, Tasks and Runs, Schedules, Proactive Briefings, Site Skills, and Agent Bus panels.
- [x] Add a bounded local application programming interface timeout helper so affected pages remain usable while local panel data is still syncing.
- [x] Harden shell-ready startup handling so the shell is visible even if an initializer degrades.
- [x] Normalize remaining visible developer-era copy through the render path and static labels.
- [x] Replace startup/loading language with product-facing syncing/local-shell language.
- [x] Inspect screenshots and fix the Approvals renderer error caused by stale undefined `records` / `recordsHtml` references.
- [x] Rebuild/prove the packaged EXE with SHA-256 `EBD14BC345A0B3BC8124FC775F036B524B87D2EDE6DA19C93B18BA33378BF62F`.
- [x] Verify focused Studio tests: `46 passed`.
- [x] Verify targeted Approvals packaged/native proof after the renderer fix: 1 page, 0 failed.
- [x] Verify fresh full single-launch packaged/native proof: 38 mounted routes, 38 screenshots, 38 unique route screenshots, 0 failed pages, no non-ignored markdown writes, no approval artifact writes.
- [x] Record final proof at [[2026-05-26-studio-product-sync-fallback-all-pages-v15-final]].
- [x] Scope the final Markdown sentinel ignore to live Codex runtime-profile drift only: `06_AGENTS/Codex-Runtime-Profile.md`.
- [x] Preserve no provider/model call, runtime dispatch, browser control, Agent Bus task write, workflow execution, approval consumption, graph/canonical/memory mutation, schedule/cron mutation, installer/startup mutation, host/release mutation, signing, release promotion, or external delivery authority.
- [ ] Manual operator page-by-page visual acceptance remains open.
- [ ] Actual end-to-end Chat response, long-duration Hermes/OpenClaw heartbeat stability, Agent Bus fault-source analysis, schedule YAML data repair, signing, installer, store/mobile, release promotion, and governed startup/autostart release behavior remain separate sessions.

## Page Backlog

Use `[[Finalize-ChaseOS-Studio-Product-UI-Handover]]` for the full 39-panel checklist. The highest-priority cleanup sequence is:

1. [x] Dashboard -> Command Center / Home.
2. [x] Sidebar/navbar labels and grouping.
3. [x] Chat.
4. [x] Project Workspace / Workspaces.
5. [x] Graph View and Node Inspector.
6. [x] Graph Hygiene.
7. [x] Capture / Intake / Sources / Research Collections.
8. [x] Agents / Runtimes, Agent Bus, Runs, Schedules.
9. [x] Personal Memory surfaces.
10. [x] Approvals, Logs / Audit, Decisions, Settings, Advanced governance.
11. [x] Chaser Forge / Extensions.

## Non-Claims

This master plan does not claim:

- Knowledge Boxes is built;
- Builder / Canvas is built as a distinct page;
- Artifacts is built as a distinct page;
- global command execution is authorized;
- packaged `.exe` UI was visually verified in Pass 3;
- provider/model/browser/runtime/host/release authority changed;
- any approval, graph, memory, Agent Bus, schedule, or canonical write occurred.

## Next Recommended Pass

Proceed to manual operator page-by-page review against the Pass 30 final all-route proof and contact sheet. Exact current-build all-page evidence is green for EXE hash `EBD14BC345A0B3BC8124FC775F036B524B87D2EDE6DA19C93B18BA33378BF62F`; remaining UI work should focus on operator-identified route-specific product depth rather than new authority. Hermes/OpenClaw Agent Bus heartbeats were restored in a prior runtime pass and the Phase 11 dispatch chain reported runtime online, but long-duration heartbeat stability, end-to-end Chat response proof, Agent Bus fault-source analysis, and schedule YAML data-quality repair should remain separate runtime/data sessions so UI productization does not mix runtime internals into page design work.

The installer path must remain governed and blocked unless current packaged native visual QA, signing, installer, and release evidence are green: no installer creation, signing, startup/autostart/registry writes, approval consumption, workflow execution, provider/model/connector calls, Agent Bus task writes, graph/memory/canonical mutation, host/release mutation, or external delivery without explicit approval and proof.

## Graph Links

[[Finalize-ChaseOS-Studio-Product-UI-Handover]] [[Studio-Product-UI-Feature-Family-Normalization]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]] [[ChaseOS-Studio-Product-Nav-Model]] [[ChaseOS-Studio-Architecture]]
