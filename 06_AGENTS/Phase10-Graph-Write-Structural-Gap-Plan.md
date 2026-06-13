---
title: Phase 10 Graph and Controlled Write Structural Gap Plan
type: implementation-backlog
status: DECISION-COMPLETE-BACKLOG
phase: 10
runtime: Codex
updated: 2026-05-07
---

# Phase 10 Graph and Controlled Write Structural Gap Plan

This note splits the remaining 10A-10D graph and write-surface gaps into implementation passes that should not be split into smaller dependent chats. It is a planning artifact only. It does not approve canonical writes, Gate mutation, graph index mutation, provider calls, Agent Bus writes, or host mutation.

**Approval Center routing:** graph/write approval-queue dependencies should route through [[ChaseOS-Approval-Center]] for current cross-feature Approval Center boundaries.

## Repo-Truth Baseline

- Native Studio shell panels are mounted through Pass 10W.
- Backend foothold exists in `runtime/studio/service.py`, `runtime/studio/graph_view.py`, `runtime/studio/provenance.py`, and shell API wrappers.
- Existing graph and write surfaces are partial and bounded.
- Remaining work is product-surface depth: governed write actions and action-ready runtime surfaces. Parser-backed graph input is complete as of `phase10x-graph-scanner-parser`; typed graph/trust overlays are complete as of `phase10y-typed-graph-trust-overlays`; read-only graph provenance inspection is complete as of `phase10z-graph-provenance-inspector`; controlled node create/edit hardening is complete as of `phase10aa-controlled-node-create-edit`; visual link approval flow is complete as of `phase10ab-visual-link-approval-flow`; Runtime Cockpit action readiness is complete as of `phase10ac-runtime-cockpit-action-readiness`.

## Pass Map

| Pass | Status | Dependencies | Output |
|---|---|---|---|
| `10X-graph-scanner-parser` | COMPLETE / READ-ONLY / VERIFIED | Existing bounded scan contract, markdown scan contract | Parser-backed graph input for Markdown/Obsidian/ChaseOS folders |
| `10Y-typed-graph-trust-overlays` | COMPLETE / READ-ONLY / VERIFIED | `10X` graph input schema | Visual node family, edge layer, and trust overlay renderer |
| `10Z-graph-provenance-inspector` | COMPLETE / READ-ONLY / VERIFIED | `10X`, `10Y`, existing provenance backend | Graph-to-provenance detail entrypoint |
| `10AA-controlled-node-create-edit` | COMPLETE / APPROVAL-GATED / VERIFIED | service.py Gate contracts, Node Inspector shell | Create/edit node metadata through approval-first service calls |
| `10AB-visual-link-approval-flow` | COMPLETE / APPROVAL-GATED / VERIFIED | `10AA`, graph selection model, approval queue | Drag/context/Shift-drag visual link proposals with bounded non-canonical pending overlays |
| `10AC-runtime-cockpit-action-readiness` | COMPLETE / APPROVAL-GATED / VERIFIED | approval center, runtime cockpit, startup approval lanes | Runtime cards that show actionable readiness and queue approval-request artifacts without direct mutation |

## 10X - Graph Scanner Parser

Status: COMPLETE / READ-ONLY / VERIFIED.

Completion evidence:
- Build log: `07_LOGS/Build-Logs/2026-05-07-ChaseOS-phase10x-graph-scanner-parser.md`
- Static QA evidence: `07_LOGS/Studio-Graph-Views/2026-05-07-phase10x-graph-scanner-parser-static-qa.md`
- CLI: `chaseos studio graph-scanner-parser --json`
- QA runner: `chaseos studio qa-runner --surface graph-scanner-parser --mode static --json`
- Full Studio shell suite: `1261 passed`

Current boundary:
- Built: read-only parser-backed graph input, source parser model in graph-index/graph-view/node-inspector contracts, shell parser summary, CLI/QA surface.
- Later passes built: 10Y typed visual overlays and 10Z graph provenance inspection.
- Still not built: persisted graph engine, node-ID persistence, writeable graph store, create/edit/link write flows.

Likely touched files:
- `runtime/studio/markdown_scan_contract.py`
- `runtime/studio/graph_view_contract.py`
- `runtime/studio/graph_view.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/styles.css`
- focused tests under `runtime/studio/` and `runtime/studio/shell/`

Backend contract:
- Parse Markdown frontmatter, headings, tags, wikilinks, markdown links, embeds, tasks, and Obsidian-style aliases.
- Return structured graph input with stable file nodes, heading nodes, link targets, unresolved references, and parse warnings.
- Preserve source file paths and line references.
- Keep full source writes disabled.

UI behavior:
- Show parsed graph source count, warnings, unresolved link count, and folder/vault mode.
- Allow scan refresh only as read-only inspect action.
- No migration or writeback controls in this pass.

Authority boundary:
- Allowed: read vault Markdown, produce in-memory graph model, optionally write QA evidence if command flag requests it.
- Forbidden: graph index writes, node id writes, frontmatter rewrites, canonical state writes.

Tests:
- Markdown parser unit tests for frontmatter, headings, tags, wikilinks, markdown links, embeds, tasks.
- Obsidian folder fixture with unresolved references.
- Shell API envelope tests.
- Product-hardening static QA.

## 10Y - Typed Graph Trust Overlays

Status: COMPLETE / READ-ONLY / VERIFIED.

Completion evidence:
- Build log: `07_LOGS/Build-Logs/2026-05-07-ChaseOS-phase10y-typed-graph-trust-overlays.md`
- CLI: `chaseos studio graph-visual-overlays --max-files 250 --max-nodes 1500 --max-edges 3000`
- QA runner: `chaseos studio qa-runner --surface graph-visual-overlays --mode static --json`
- Focused graph/QA suite: `56 passed`
- Full Studio shell suite: `1267 passed`

Current boundary:
- Built: read-only typed visual model, overlay contract, graph-view/static-renderer/native-shell overlay wiring, edge-layer filters, node-family/trust/edge legends, generated/canonical visual distinction, CLI/API/QA surface.
- Later passes built: 10Z graph provenance inspection.
- Still not built: persisted graph engine, node-ID persistence, create/edit/link write flows, trust promotion, canonical graph mutation.

Likely touched files:
- `runtime/studio/graph_visual_model.py`
- `runtime/studio/graph_visual_overlays.py`
- `runtime/studio/graph_view_contract.py`
- `runtime/studio/graph_view_static_renderer.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/graphStyles.js`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- shell graph tests

Backend contract:
- Expose 14 node families and 4 edge layers:
  - Explicit
  - Structural
  - Suggested
  - Runtime-Action
- Expose trust states:
  - raw
  - quarantined
  - suggested
  - promoted
  - canonical
  - generated
  - archived
  - disputed

UI behavior:
- Render typed nodes with distinct family shape/color/icon.
- Render edge layers with distinct line styles and filters.
- Overlay trust state badges/rings without claiming trust promotion.
- Distinguish generated and canonical content visually.

Authority boundary:
- Allowed: read graph contracts and style registry.
- Forbidden: accepting suggestions, promoting trust, rewriting node metadata.

Tests:
- Visual model coverage for all 14 node families, 4 edge layers, and 8 trust states.
- Overlay contract coverage for graph-view integration, generated/canonical distinction, readiness flags, and no-write authority.
- Static renderer coverage for overlay summary, typed node/edge visuals, trust rings, and legends.
- Shell API/registry/frontend coverage for panel mount, filters, legends, summary, and CSS classes.
- QA runner and CLI contract/generated docs coverage.

## 10Z - Graph Provenance Inspector

Status: COMPLETE / READ-ONLY / VERIFIED.

Completion evidence:
- Build log: `07_LOGS/Build-Logs/2026-05-07-ChaseOS-phase10z-graph-provenance-inspector.md`
- CLI: `chaseos studio graph-provenance-inspector --path README.md --max-nodes 1500 --json`
- QA runner: `chaseos studio qa-runner --surface graph-provenance-inspector --mode static --json`
- Focused 10Z tests: `9 passed`
- Graph/parser/node/provenance contract tests: `29 passed`
- Full Studio shell suite: `1272 passed`

Touched files:
- `runtime/studio/graph_provenance_inspector.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/shell/frontend/inspectorTabs.js`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- focused tests under `runtime/studio/` and `runtime/studio/shell/`

Backend contract:
- Given a graph node id or file path, return graph identity plus sidecar, capture, quarantine, promotion, generated/canonical, dedup, and audit-chain data where present.
- Missing provenance returns explicit missing state, not failure.
- Malformed optional sidecars return explicit malformed state, not panel crash.

UI behavior:
- Node Inspector provenance tab now prefers graph-aware provenance via `get_graph_node_provenance`.
- Chain steps, source hashes/status, promotion state, generated/canonical distinction, and missing links are visible in read-only form.
- Semantic suggestion acceptance remains non-built and must stay non-canonical until separately approved.

Authority boundary:
- Read-only. No promotion, no trust-state mutation, no sidecar editing.

Tests:
- Provenance-present fixture.
- Provenance-missing fixture.
- Malformed optional sidecar fixture.
- Graph context entrypoint test.
- API, registry, frontend, CSS, CLI, QA runner, command-contract, generated-docs, product-hardening, and full shell verification.

## 10AA - Controlled Node Create Edit

Status: COMPLETE / APPROVAL-GATED / VERIFIED.

Completion evidence:
- Build log: `07_LOGS/Build-Logs/2026-05-07-ChaseOS-phase10aa-controlled-node-create-edit.md`
- CLI: `chaseos studio controlled-node-create-edit --json`
- QA runner: `chaseos studio qa-runner --surface controlled-node-create-edit --mode static --json`
- Focused 10AA/write-surface suite: `98 passed`
- Graph/CLI dependency suite: `52 passed`
- Broad Studio/CLI/runtime suite: `2615 passed`

Touched files:
- `runtime/studio/controlled_node_write.py`
- `runtime/studio/service.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/writeActions.js`
- `runtime/studio/shell/frontend/inspectorTabs.js`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/qa_runner.py`
- `runtime/studio/product_hardening_status.py`
- `runtime/studio/shell/config.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- focused tests under `runtime/studio/`, `runtime/studio/shell/`, and `runtime/tests/`

Backend contract:
- `build_create_node_preview()` validates title, node type, domain, target path, collisions, pending target collisions, and source graph context without writing.
- `queue_create_node_approval()` always returns an approval-gated request; it writes no Markdown before approval.
- `build_node_metadata_edit_model()` resolves parser graph node IDs or file paths and returns editable metadata plus authority boundaries.
- `queue_metadata_update_approval()` whitelists `title`, `domain`, `project`, `tags`, `aliases`, `summary`, and `status`; preserves note body; prepends approved frontmatter when missing; blocks malformed frontmatter; blocks trust/canonical/provenance/runtime/path traversal fields.
- `StudioService.execute_approved()` now reserves execution state before action writes and records `executed` or `execution_failed`, so duplicate execution blocks before writes.

UI behavior:
- Graph create-node modal shows target preview and approval-required posture.
- Create submit queues approval and routes through the approval modal.
- Node Inspector overview exposes a metadata edit drawer/form, not a raw JSON editor.
- Save queues approval and refreshes graph, inspector metadata, provenance context, and approval badge after approval.
- Trust promotion, canonical/generated toggles, provenance edits, runtime authority edits, and direct write buttons remain absent.

Authority boundary:
- Allowed: prepare previews, validate candidate write packets, queue approval artifacts, execute writes only through approved `StudioService` requests.
- Forbidden: direct frontend writes, graph persistence, node-ID persistence, trust promotion, canonical state mutation, provenance writeback, visual link writeback, provider/connector calls, Gate mutation, Agent Bus writes, Git mutation, workflow execution, host/release mutation.

Tests:
- Create node queues approval and writes no Markdown before approval.
- Create collision blocks without approval artifact.
- Invalid title/type/domain blocks.
- All allowed node types map to valid target paths.
- Metadata edit queues approval and preserves body.
- Restricted metadata fields block.
- Malformed frontmatter blocks cleanly.
- Missing frontmatter is tolerated by approved prepend.
- Missing node fails cleanly.
- Protected files remain gate-blocked.
- Approval execution marks requests executed.
- Duplicate approval execution blocks before writes.
- Real-vault static QA leaves Markdown and approval snapshots unchanged.

## 10AB - Visual Link Approval Flow

Status: COMPLETE / APPROVAL-GATED / VERIFIED.

Completion evidence:
- Build log: `07_LOGS/Build-Logs/2026-05-07-ChaseOS-phase10ab-visual-link-approval-flow.md`
- CLI: `chaseos studio visual-link-approval-flow --json`
- QA runner: `chaseos studio qa-runner --surface visual-link-approval-flow --mode static --json`
- Focused 10AB/10AA suite: `23 passed`
- Graph/CLI dependency suite: `128 passed`
- Split broad verification: `runtime/studio/shell` `1284 passed`; top-level `runtime/studio --ignore=runtime/studio/shell` `529 passed`; `runtime/cli` `52 passed`; `runtime/tests` `769 passed`

Touched files:
- `runtime/studio/visual_link_approval.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/shell/frontend/writeActions.js`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/shell/frontend/graphStyles.js`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- focused tests under `runtime/studio/`, `runtime/studio/shell/`, and `runtime/tests/`

Backend contract:
- `build_visual_link_preview()` resolves source/target by file path or parser graph node id, validates edge layer/relation/labels, blocks self-links, existing Markdown links, and active pending duplicates, and returns a non-canonical preview edge without writing.
- `queue_visual_link_approval()` always queues approval through `StudioService`; it writes no Markdown before approval.
- `build_visual_link_overlay()` reads only Studio approval artifacts, not Markdown, and returns a bounded pending-edge overlay capped at 250 approval edges by default.
- Approved execution inherits `StudioService.execute_approved()` exact-once behavior and appends the approved source Markdown link only after approval execution.

UI behavior:
- Graph context menu can start/finish/clear a visual link source.
- Shift-drag from one graph node to another opens the visual link modal.
- The modal previews source, target, edge layer, relation, label, evidence, and approval-required posture.
- Pending/approved/executing visual links render as non-canonical Cytoscape overlay edges and reuse existing node positions.
- Overlay refresh does not rebuild or duplicate the full graph payload, preserving large-vault memory posture.

Authority boundary:
- Allowed: prepare previews, validate proposed source/target/relation, queue approval artifacts, render pending overlay edges from approval artifacts, and execute the Markdown append only through approved `StudioService` execution.
- Forbidden: direct frontend writes, persisted graph storage, node-ID persistence, trust promotion, canonical graph writeback, provenance writeback, provider/connector calls, Gate mutation, Agent Bus writes, Git mutation, workflow execution, host/release mutation.

Tests:
- Preview resolves paths and builds non-canonical edge.
- Queue writes no Markdown before approval.
- Approved execution appends link and marks approval executed.
- Duplicate pending proposals block.
- Existing Markdown links block.
- Invalid edge layer/relation/text blocks.
- Missing/self-link targets fail cleanly.
- Protected source files remain Gate-blocked.
- Overlay reads approval artifacts only and caps results.
- API, registry, frontend tokens, static QA, CLI contract, generated docs, and split broad verification pass.

## 10AC - Runtime Cockpit Action Readiness

Status: COMPLETE / APPROVAL-GATED / VERIFIED.

Completion evidence:
- Build log: `07_LOGS/Build-Logs/2026-05-07-ChaseOS-phase10ac-runtime-cockpit-action-readiness.md`
- CLI: `chaseos studio runtime-cockpit-action-readiness --json`
- QA runner: `chaseos studio qa-runner --surface runtime-cockpit-action-readiness --mode static --json`
- Focused 10AC suite: `13 passed`
- CLI command/JSON contract: `10 passed`
- Expanded relevant pack: `64 passed`
- Split broad verification: `runtime/studio/shell` `1289 passed`; top-level `runtime/studio --ignore=runtime/studio/shell` `533 passed`; `runtime/cli` `52 passed`; `runtime/tests` `769 passed`

Implemented files:
- `runtime/studio/runtime_cockpit_action_readiness.py`
- `runtime/studio/runtime_cockpit_panel.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`

Backend contract:
- Build a bounded action-readiness matrix over current Runtime Cockpit/startup-control state.
- Classify startup-surface actions as requestable approval-packet-only actions when evidence is sufficient.
- Classify lifecycle/provider/Agent Bus/runtime execution actions as blocked or deferred with explicit blockers.
- Queue approval artifacts only through `request_runtime_cockpit_action`; future approved execution writes proof/request JSON only under governed evidence roots.

UI behavior:
- Runtime Cockpit renders action-readiness cards with category/status/evidence posture.
- Requestable actions show approval-required request buttons.
- Blocked/deferred actions show blockers and no execution controls.
- Successful requests refresh the approval badge and panel state.

Authority boundary:
- No runtime start/stop/restart execution.
- No host startup/autostart mutation.
- No provider/connector call.
- No Agent Bus task write.
- No workflow execution, Gate mutation, Git mutation, release mutation, or canonical writeback.

Tests:
- Runtime action matrix/boundary tests.
- API request approval-only tests.
- Registry approval-gated tests.
- Frontend token/static behavior tests.
- Static QA no-write tests.
- CLI contract, generated docs, and broad Studio/CLI/runtime verification.

## Dependency Rules

- `10Y` depends on completed `10X`; it is now complete/read-only/verified.
- `10Z` is complete/read-only/verified and should not be reopened for writeback authority.
- `10AA` is complete/approval-gated/verified.
- `10AB` is complete/approval-gated/verified and depends on 10AA exact-once approval semantics.
- `10AC` is complete/approval-gated/verified. Runtime Cockpit can queue approval-request artifacts only; any startup mutation executor remains a separate governed chain.
- Next mainline marker is `phase10f1-open-folder-compatibility-readiness`.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
