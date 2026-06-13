---
title: ChaseOS Studio Architecture
type: architecture
status: active
version: 1.44
created: 2026-04-08
updated: 2026-05-21
phase: Phase 10 — ChaseOS Studio (Interface / Experience Layer)
---

# ChaseOS Studio Architecture

> Canonical architecture and product specification for ChaseOS Studio — the standalone desktop interface and experience layer for ChaseOS.
> Studio is now partially built as a native shell with mounted read-only and approval-gated panels. Read this architecture with `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`, `06_AGENTS/ChaseOS-Studio-Full-Desktop-Card-UI-Closure-Criteria.md`, and `06_AGENTS/Studio-Product-UI-Feature-Family-Normalization.md` for current implementation truth.

---

## 1. What ChaseOS Studio Is

ChaseOS Studio is the standalone desktop, graph-first, mouse-first visual operating surface for ChaseOS and compatible markdown vaults.

It is the human-facing product realization of Phase 10 — the layer where the full ChaseOS system becomes something a person can use without navigating raw markdown files, running CLI commands, or understanding the internal runtime architecture.

Studio is the **product shell** that wraps everything below it:
- Phase 7 SIC (source packages, workspaces, retrieval)
- Phase 8 Capture (quarantine, dedup, provenance)
- Phase 9 AOR (workflows, operator runtime, event bus)

Studio does not replace or duplicate those layers. It surfaces them, operates through them, and enforces their governance rules at the point of user interaction.

### Studio monolith freeze and facade policy

ChaseOS Studio implementation now has a P0 monolith-growth freeze because the major Studio shell files have become control-plane risk surfaces for testability, regression isolation, agent-harness context limits, GUI verification, onboarding, and authority-boundary reasoning.

Implementation agents must not add major new feature logic directly into:

```text
runtime/studio/shell/frontend/app.js
runtime/studio/shell/api.py
runtime/studio/launcher_update_check.py
```

Allowed changes in those files are limited to:

- thin adapter calls into tested/source-owned modules,
- imports or module-loading wiring,
- compatibility wrappers around existing behavior,
- narrowly scoped bug fixes that cannot yet be safely isolated,
- comments/markers identifying extraction seams,
- deletion/replacement of a legacy slice after tests prove the extracted seam.

New feature behavior must land in source-owned modules/facades with focused tests before product wiring. `runtime/studio/shell/api.py` should be treated as a legacy pywebview compatibility/delegation layer; new Python Studio API behavior belongs in source-owned modules such as `runtime/studio/api_facade/`. `runtime/studio/shell/frontend/app.js` should become a loader/adapter around frontend modules such as chat sidebar model/API/action/view modules. `runtime/studio/launcher_update_check.py` should be reduced through launcher/status/log-tail/lifecycle facade modules before new runtime-control behavior is added.

Developer execution details and the active decomposition inventory live in:

```text
docs/dev/Studio-Monolith-Reduction-Roadmap.md
docs/dev/Studio-Module-Decomposition-Map.md
```

### Voice I/O Surface Boundary

Voice I/O is now architected as a Phase 10 Studio/OSRIL ingress and egress lane in `06_AGENTS/Voice-IO-Architecture.md`. Studio may eventually render push-to-talk capture, transcript review, spoken status/briefing output, and an AudioContext visualizer, but those surfaces must emit Tier 4 intent candidates and visible text readouts only. They must not directly dispatch workflows, consume approvals, write Agent Bus tasks, call providers outside a governed adapter, persist transcripts by default, or mutate canonical notes.

### Current Phase 10 Product Lane — ChaseOS Pulse

The current implementation lane may start with **ChaseOS Pulse** as the first broadly useful proactive-intelligence surface. Pulse is not a replacement for the Studio shell; it is a native ChaseOS feature family that Studio should render through governed card/deck, feedback, provenance, memory-candidate, runtime-brain, and schedule-intent surfaces.

Studio must treat Pulse cards as proposals/briefs with evidence and recommended actions, not as canonical truth. Pulse UI controls must route feedback, task creation, memory promotion, schedule catch-up, connector invocation, and canonical writeback through their existing ChaseOS governance layers instead of becoming direct UI toggles.

See: `06_AGENTS/ChaseOS-Pulse-UI-and-Runtime-Handoff.md`.

2026-04-30 implementation note: Pulse now has a first static local surface in
`runtime/pulse/local_surface.py` that renders the latest user deck artifact and
shows feedback candidates only. This is a governed foothold over existing Pulse
deck logs, not the full Studio desktop shell and not a new write authority.

2026-04-30 feedback note: Pulse feedback candidates can now be appended as
pending-review JSONL records under `07_LOGS/Pulse-Decks/feedback-candidates/`.
Studio must treat that lane as an approval/review inbox input only. It is not an
applied feedback state, not approved memory, not task creation, and not
canonical writeback.

2026-04-30 review-queue note: Pulse now has a read-only pending candidate queue
and contract-only review/apply object model in
`runtime/pulse/feedback_review_queue.py`. Studio may later render this queue,
but persisted decisions and effects still require a governed service-layer pass.
The current contract does not apply feedback, approve memory, create tasks,
mutate source decks, or write canonical state.

2026-05-02 dashboard note: the Studio Dashboard now exposes a read-only
`pulse_panel` composed from `runtime/studio/pulse_inspector.py`. The panel
surfaces deck, candidate, review-decision, approval-request, and enqueue-result
counts for visibility only. It does not apply candidates, grant approvals,
enqueue Agent Bus tasks, call providers/connectors, activate schedules, or write
canonical state.

2026-05-02 app-launcher dashboard note: the Studio Dashboard now exposes a
read-only `app_launcher_panel` composed from `runtime/studio/app_launcher.py`.
The panel surfaces Studio app count, read-only/write-capable counts,
confirmation-required count, child-app health counts, launcher URL, and slim app
metadata for visibility only. It does not start child apps, execute workflows,
call providers/connectors/browsers/MCP, mutate runtime startup state, activate
schedules, or write canonical state.

2026-05-15 Discord control-plane dashboard note: the Studio Dashboard now
exposes a read-only `discord_control_plane_panel` composed from
`runtime/discord_bindings.py`. The panel validates the local Git-ignored
`.chaseos/discord_instance_bindings.yaml` file, reports active runtime labels,
bound channel counts, Git-ignore status, blockers, and planned runtime-control
capabilities for quick chat opening, thread creation, runtime board routing,
cron/schedule management, and chat-driven setup. It does not expose raw IDs or
secret values, call Discord APIs/webhooks, write Agent Bus tasks, mutate
schedules, consume approvals, or write canonical state.

2026-05-15 native Chat workspace note: the Studio Chat panel now renders a
read-only ChaseOS-native workspace/thread foundation from
`runtime/studio/phase11_chat_workspaces_foundation.py`. The surface models
projects, folders, tabs, threads, runtime lanes, Discord transport posture, and
proposal actions for Hermes/OpenClaw/Codex board handoff, thread creation,
cron/schedule management, and chat-driven setup. It is product-shape only in
this pass: it does not persist chat state, send messages, create Discord
threads, call Discord APIs/webhooks, write Agent Bus tasks, mutate runtime
boards or schedules, call providers, consume approvals, expose credential
values, or mutate canonical state.

2026-05-15 native Chat workspace proposal-writer note: the Studio Chat panel
now embeds a digest-bound proposal writer from
`runtime/studio/phase11_chat_workspace_proposal_writer.py` for workspace,
folder, and runtime-thread requests. The writer can queue a pending Studio
approval artifact only when the operator supplies the exact proposal digest.
Generic Studio approval execution blocks these artifacts; only
`runtime/studio/phase11_chat_workspace_proposal_consumption_executor.py` may
consume them. The consumption executor requires approval id plus exact proposal
digest, writes one proposal JSON record under
`runtime/studio/chat/workspace-proposals/`, and records marker/audit evidence.
The follow-on target-state executor now requires proposal path/id, exact digest,
and an operator target-state statement before writing local native Studio Chat
state under `runtime/studio/chat/native-state/`; the Chat foundation reads those
state records back into the project/folder/thread model. The route-state and
draft surface now persists selected Chat workspace/folder/thread/tab state plus
local message draft/intent JSON under `runtime/studio/chat/native-state/`; this
lets Studio remember the active runtime chat lane and unsent draft without
dispatching anything. The runtime-board handoff proposal surface now packages
that selected thread or draft into an exact-digest approval request for a future
Hermes/OpenClaw/Codex board item, while `StudioService.execute_approved()` blocks
ambient execution of those artifacts. The schedule proposal packet surface now
packages a selected thread or draft into an exact-digest approval request for a
future `runtime/schedules/*.yaml` schedule intent and blocks ambient execution
before any schedule YAML write, schedule-index regeneration, or external
scheduler mutation. The schedule proposal consumption executor now consumes one
approved digest-bound schedule proposal into a staged Studio record under
`runtime/studio/chat/schedule-proposals/` with exact-once marker/audit evidence.
The approved schedule-intent writer now consumes one staged approved proposal
with exact schedule digest plus operator write statement and writes the declared
disabled `runtime/schedules/*.yaml` intent plus regenerated
`runtime/schedules/index.yaml`. The activation-readiness surface now inspects an
existing disabled schedule intent, previews future `enabled: true` YAML and
adapter export posture, and can queue a digest-bound activation approval packet
while ambient Studio execution remains blocked. The approved schedule-activation
executor now consumes one activation approval exactly once, verifies the current
disabled schedule hash, enables the matching ChaseOS schedule, regenerates
`runtime/schedules/index.yaml`, refreshes the adapter export read model, and
writes marker/audit evidence. The adapter export-readiness surface now reads
enabled schedules for a registered runtime adapter, computes an exact export
digest, previews a local adapter export packet, and can queue a pending approval
packet while ambient Studio execution remains blocked. The approved adapter
export packet writer can consume one of those approvals exactly once and write
the local JSON export packet under
`runtime/studio/chat/schedule-adapter-exports/`. The schedule UI controls and
readback surface now renders that full local chain in the native Chat page as
manual-test fields, buttons, status text, and readback rooted in existing
governed Studio API methods. A loopback-only manual browser harness now exists
at `runtime/studio/phase11_chat_schedule_manual_test_app.py` for operator
click-through testing of the same chain through `/`, `/health.json`,
`/api/readback`, and `/api/action`; it renders no credential fields and blocks
secret-like input strings. External scheduler mutation, OpenClaw/Hermes cron
mutation, live runtime dispatch, and Discord/provider effects remain deferred.
These surfaces do not create Discord
threads, send messages, persist transcripts/conversation logs, call Discord
APIs/webhooks, write Agent Bus tasks, mutate runtime boards, change external cron
state, call providers, expose credential values, or mutate broader canonical
state beyond the approved schedule intent/index/enablement path and the
approval-queue record plus local adapter export packet writer.

2026-05-16 native Chat authority-tier controls note: the Studio Chat page now
renders `runtime/studio/phase11_chat_authority_tier_controls.py` as the unified
control/readiness block for provider calls, credentials, runtime dispatch,
Agent Bus tasks, Discord actions, and external cron apply. Its buttons navigate
to existing governed Chat/readiness surfaces only; direct execution buttons are
disabled, and the surface does not read secret values, call providers or
Discord, write Agent Bus tasks, dispatch runtimes/workflows, mutate external
schedulers or OpenClaw/Hermes cron, consume approvals, or mutate canonical
state.

2026-05-16 native Chat authority execution controls note: the Studio Chat page
now also renders `runtime/studio/phase11_chat_authority_execution_controls.py`
as the governed manual all-lanes test block. It prepares exact approval digests
and can run one operator-statement-gated stack for
`runtime/studio/phase11_chat_live_provider_execution_executor.py`, Hermes
runtime dispatch, OpenClaw Discord-control handoff, OpenClaw cron/schedule
handoff, and Agent Bus readback. Provider execution uses only the provider env
reference and never renders credential values. Discord control and cron control
are runtime handoffs, not direct Studio Discord API calls or external scheduler
mutation. Live Hermes/OpenClaw completion remains a manual runtime test.

2026-05-02 Pulse Deck app note: `runtime/studio/pulse_deck_app.py` now registers
as the localhost-only `pulse-deck-app` at port `8767`. It renders the latest
Pulse user deck and can write feedback candidates only after explicit operator
form submission. It does not write review decisions, apply candidates, grant
approvals, enqueue Agent Bus tasks, dispatch workflows, call providers or
connectors, activate schedules, create a second datastore, or mutate canonical
state. This is a Pulse v1 local UI proof, not broad Studio desktop completion.

2026-05-03 governed controls note: the Pulse Deck app now exposes every
supported Pulse feedback/action type as a pending-review candidate control:
thumbs up/down, show more/less, never show, save, delegate, turn into task,
promote/link actions, memory candidate, correction, and review-state actions.
The controls append only feedback-candidate JSONL records under
`07_LOGS/Pulse-Decks/feedback-candidates/`. They do not apply candidates,
approve memory, create tasks directly, dispatch runtimes, write Agent Bus
tasks, activate schedules, call providers/connectors, or write canonical truth.

2026-05-02 test-infrastructure note: repo-root pytest now keeps Studio temp
fixtures under per-process `.pytest_tmp_env/pytest-of-chaseos-<pid>` roots,
cache writes under `.pytest_tmp_env/cache`, and includes a Windows-only pytest
bootstrap shim for unreadable `0o700` temp directories. This supports broader
Studio verification bundles only; it does not change Studio product
architecture, Pulse behavior, app-launcher behavior, or runtime authority.

2026-05-02 shell foundation note: `runtime/studio/desktop_shell_foundation.py`
and `chaseos studio desktop-shell-foundation --json` provide a read-only Phase
10A foundation contract for the real Studio shell. The contract reports current
local footholds, planned gaps, workspace detection posture, authority
boundaries, and the next implementation sequence. It does not start servers,
launch child apps, execute workflows, call providers/connectors, mutate startup
state, consume approvals, write settings, or write canonical memory.

2026-05-02 Open Folder readiness note:
`runtime/studio/open_folder_readiness.py` and
`chaseos studio open-folder-readiness --json` provide the first read-only
contract for the future Start New / Open Folder entry flow. It classifies
operator-selected folders as ChaseOS-native, partial ChaseOS, general
markdown/Obsidian, empty/unknown, or invalid; reports bounded markdown path
inventory and required ChaseOS shape; and preserves no file-content parsing,
graph inference, node-id writes, settings writes, server start, provider calls,
or canonical writeback.

2026-05-02 markdown scan note:
`runtime/studio/markdown_scan_contract.py` and
`chaseos studio markdown-scan-contract --json` provide the first read-only
bounded markdown scanner contract for future graph-index work. The contract
reads markdown file contents only within explicit file/byte limits and detects
frontmatter keys, headings, wikilinks, markdown links, tags, task items, and
block-id markers. It does not write node IDs, build graph state, mutate opened
folders, write settings, call providers/connectors, execute workflows, or write
canonical state.

2026-05-03 graph-index contract note:
`runtime/studio/graph_index_contract.py` and
`chaseos studio graph-index-contract --json` provide the first read-only
derived graph-index contract for future Studio graph and node-inspector work.
The contract consumes bounded markdown scan output and creates deterministic
in-memory node and edge identities for files, headings, tags, tasks, block
markers, wikilinks, markdown links, unresolved references, and external
resources. It does not persist graph state, write node IDs, mutate opened
folders, write settings, call providers/connectors, execute workflows, or write
canonical state.

2026-05-03 node-inspector contract note:
`runtime/studio/node_inspector_contract.py` and
`chaseos studio node-inspector-contract --path <file> --json` provide the first
read-only node-inspector contract over the derived graph model. The contract
selects a graph node by path or deterministic node ID, returns incoming and
outgoing edge context, related nodes, relation counts, and a bounded source
excerpt for file-backed nodes. It does not render a UI panel, edit nodes, write
node IDs, persist graph state, mutate opened folders, write settings, call
providers/connectors, execute workflows, or write canonical state.

2026-05-03 graph-view static renderer note:
`runtime/studio/graph_view_static_renderer.py` and
`chaseos studio graph-view-static-render` provide the first local static HTML
renderer over the read-only graph-view contract. It renders in memory by
default and writes only explicit artifacts under `07_LOGS/Studio-Graph-Views`
when `--write` is passed. It does not mount a Studio UI, start servers, persist
graph state, edit nodes, write node IDs, mutate opened folders, write settings,
call providers/connectors, execute workflows, or write canonical state.

2026-05-03 graph-view static browser QA note:
`07_LOGS/Studio-Graph-Views/2026-05-03-graph-view-static-render-browser-qa.md`
records targeted in-app browser QA over a generated static graph artifact.
The QA evidence verifies one visible SVG graph, 20 rendered nodes, 15 rendered
edges, visible focus/legend/readiness panels, no script tags, and zero browser
console errors. Runtime readiness contracts now treat the static browser QA
evidence as built and advance to
the shell-panel contract lane. This still does not mount a graph panel inside
Studio, add interactive graph controls, persist graph state, edit nodes, write
node IDs, mutate opened folders, write settings, call providers/connectors,
execute workflows, or write canonical state.

2026-05-03 graph-view shell-panel contract note:
`runtime/studio/graph_view_shell_panel.py` and
`chaseos studio graph-view-shell-panel --json` define the first read-only
Studio shell-panel contract over the verified static graph artifact and
browser-QA evidence. The contract reports panel route, panel id, mount target,
source artifact URI/path, browser-QA evidence, static renderer summary,
readiness, and blocked authority. It advances Studio graph readiness to
`phase10-studio-graph-view-shell-panel-mount`. The follow-on read-only shell
mount is now built separately; interactive graph controls, persisted graph
state, node editing, node ID writes, service-layer writes, and canonical
writeback remain unbuilt.

2026-05-03 graph-view shell-panel mount note:
`runtime/studio/desktop_shell_app.py` and
`chaseos studio desktop-shell-app --dry-run --json` now mount the Graph View
shell-panel contract as a read-only `#graph-view` panel and expose
`/graph-view-shell-panel.json`. The mount embeds the browser-QA verified static
graph artifact and reports graph no-write authority flags. It does not add
interactive graph controls, graph-index persistence, node editing, node ID
writes, settings writes, provider/connector calls, workflow execution, or
canonical writeback. Studio graph readiness now advances to
`phase10-studio-graph-view-shell-panel-browser-qa`.

2026-05-03 Pulse product-shell browser-QA, panel-contract, and Studio mount note:
`07_LOGS/Pulse-Decks/product-shell/2026-05-03-pulse-product-shell-browser-qa.md`
records targeted in-app browser QA over the integrated static Pulse product
shell artifact. `runtime/studio/pulse_product_shell_panel.py` and
`chaseos studio pulse-product-shell-panel --json` define a read-only Studio
panel contract over that verified artifact. The contract reports the `#pulse`
route, panel id, mount target, source artifact URI/path, browser-QA evidence,
Pulse shell summary, readiness, and blocked authority. `runtime/studio/desktop_shell_app.py`
now mounts that contract as a read-only `#pulse` panel and exposes
`/pulse-product-shell.json`. It does not submit feedback, execute approvals,
apply candidates, dispatch runtimes, activate schedules, call
providers/connectors, create a second datastore, mutate canonical state, or
update the R&D workbook.

2026-05-03 Pulse Approval Queue panel mount note:
`runtime/studio/approval_queue_panel.py` and
`chaseos studio approval-queue-panel --json` define a read-only Studio panel
contract over the static Pulse Approval Queue artifact. `runtime/studio/desktop_shell_app.py`
now mounts that contract under `#approval-queue` and exposes
`/approval-queue.json`. The mount surfaces review lanes, candidate counts,
display action counts, and missing approval-key posture without granting
approvals, executing approvals, writing review decisions, applying candidates,
writing Agent Bus tasks, dispatching runtimes, activating schedules, calling
providers/connectors, creating a second datastore, mutating canonical state, or
updating the R&D workbook.

2026-05-12 Pulse governed feedback review/apply UI spec note:
`06_AGENTS/ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI.md` defines the
bounded Phase 10 Studio contract for a future governed Pulse review/apply panel
over existing candidate inspector, review-decision, Approval Center, and
`candidate_apply.py` dry-run/non-canonical runtime-memory apply substrates. The
surface may display candidate state, review decisions, apply previews,
apply-registry status, and exact blocked effects, but it must not create a new
apply backend, consume approvals, auto-run live apply, mutate canonical Personal
Map truth or `02_KNOWLEDGE/`, write Agent Bus tasks, activate schedules, call
providers/connectors, create a second datastore, or hide Studio mutation behind
UI state.

2026-05-04 ARSL Route Review panel mount note:
`runtime/studio/arsl_route_review_panel.py` and
`chaseos studio arsl-route-review-panel --json` define a read-only Studio panel
contract over the Adaptive Runtime Surface Layer route-review contract.
`runtime/studio/desktop_shell_app.py` now mounts that contract under
`#arsl-route-review` and exposes `/arsl-route-review.json`. The mount surfaces
runtime surface review rows, preview decision, selected authority layer,
approval posture, Gate posture, audit posture, and policy/risk counts without
executing routes, committing route proposals, writing the routing ledger,
granting approvals, mutating Gate policy, dispatching runtimes, writing Agent
Bus tasks, calling providers, controlling browsers, exposing raw manifests,
exposing MCP tools, reading credentials/browser profiles, mutating canonical
state, or updating the R&D workbook.

2026-05-04 ARSL Route Review browser QA note:
`07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa.md`
records targeted desktop and mobile browser QA for the mounted ARSL panel. The
QA verified the `#arsl-route-review` panel, compact read-only status badge,
route-review content, boundary text, no shell script tags, and zero
ARSL-relevant console errors. Existing shared-shell Playwright warnings for
Pulse/Approval Queue `file://` iframes were recorded as unrelated. The QA did
not execute routes, write the routing ledger, grant approvals, mutate Gate
policy, dispatch runtimes, call providers, control browsers through ARSL, read
credentials/browser profiles, or mutate canonical state.

2026-05-03 graph-view contract note:
`runtime/studio/graph_view_contract.py` and
`chaseos studio graph-view-contract --json` provide the first read-only
graph-view contract over the derived graph and node-inspector models. The
contract returns bounded visible graph slices, deterministic grid layout
coordinates, filters, legends, truncation warnings, and optional focus context
without rendering a UI, writing static artifacts, persisting graph state,
editing nodes, writing node IDs, mutating opened folders, writing settings,
calling providers/connectors, executing workflows, or writing canonical state.

2026-05-02 Pulse Approval Center note: `runtime/studio/approval_center_app.py`
and `chaseos studio approval-center-app --host 127.0.0.1 --port 8773` now mount
the Pulse approval-center readiness contract as a localhost-only read-only
Studio app. It renders Pulse deck, candidate, review-decision, approval-request,
final-gate, and hardening-availability lanes. It does not grant or execute
approvals, write Agent Bus tasks, apply candidates, call providers/connectors,
activate schedules, approve memory, create a second datastore, mutate canonical
state, or update the R&D workbook.

2026-05-02 Runtime Brain dashboard contract note:
`runtime/studio/runtime_brain_dashboard.py` and
`chaseos studio runtime-brain-dashboard --json` now expose a read-only Studio
contract for future Runtime Brain dashboard rendering. The contract composes
Pulse memory/runtime readiness with runtime profiles, Agent Identity Ledgers,
Runtime Navigation Maps, Execution Repair Memory, and scorecards. It does not
update runtime brains, apply repair candidates, update navigation maps, expand
permissions, dispatch runtimes, activate schedules, call providers/connectors,
create a second datastore, mutate canonical state, or update the R&D workbook.

2026-05-04 Node Inspector shell-panel QA runner note:
`runtime/studio/desktop_shell_app.py` and
`chaseos studio desktop-shell-app --qa-runner --write-qa-evidence` now provide
a bounded localhost-only QA runner for the mounted Node Inspector shell panel.
The runner starts the desktop shell mock on an ephemeral loopback port, probes
the shell and panel routes, verifies selected-node/read-only authority flags,
writes optional JSON/Markdown evidence under `07_LOGS/Studio-Graph-Views`, and
shuts the server down before returning. It is an anti-hang QA infrastructure
pass, not visual browser screenshot QA; `phase10-studio-node-inspector-shell-panel-browser-qa`
remains the next verification pass. It does not write node IDs, persist graph
state, edit nodes, call providers/connectors, execute workflows, or mutate
canonical state.

2026-05-04 native desktop shell Pass 10A/10B note:
`runtime/studio/shell/` now contains the first native PyWebView ChaseOS Studio
desktop shell. Pass 10A added the read-only Python `StudioAPI` bridge, local
HTML/CSS/JS frontend, bundled Cytoscape asset, graph load, node click, and
Inspector display. The first Pass 10B slice adds UI-local graph controls:
node-type filters, trust-state filters, relation filters, richer node type
shape mapping, trust-state ring emphasis, edge-family styles, and an edge
legend. These controls only alter in-memory Cytoscape display state in the
desktop frontend. They do not write filters, persist graph state, write node
IDs, edit nodes, call providers/connectors, execute workflows, or mutate
canonical state.


### Audience and Platform

**Audience priority:** User-first. Agents and harnesses surface more deeply as runtime capability grows — Studio's agentic depth is not hidden, but it is not required to get value on day one.

**First platform:** Standalone desktop application. **Web support is not planned for the first release.** Desktop-first is the correct sequencing — a polished local desktop product before any browser surface.

**Primary use case:** Project operations, source intelligence, runtime/operator visibility, and vault map navigation — together in one surface.

---

## 2. Why Studio Exists

ChaseOS has built a rigorous internal architecture:
- Governed ingestion pipeline (Phase 8)
- Source intelligence workspaces (Phase 7)
- Bounded operator runtime (Phase 9)
- Trust tiers, permission ceilings, Gate enforcement (Phase 4–5)

But operating ChaseOS currently requires direct vault navigation via Obsidian, CLI commands, and knowledge of the internal folder/schema conventions. That is appropriate during the build phase. It is not appropriate for the product layer.

Studio exists because:
1. The architecture has matured enough to need a coherent product surface
2. The graph model of ChaseOS is its most valuable and distinctive interface — nodes, edges, trust states, provenance chains — and that model deserves a purpose-built visual surface
3. The operator should be able to see, approve, inspect, and act on what ChaseOS produces without opening raw files
4. ChaseOS needs to be accessible to compatible markdown vaults and Obsidian users as an onboarding path into ChaseOS-native operation

### Studio's Purpose: Graph as the Map, Cockpit as the Point

The graph is the primary navigation surface. The cockpit is the purpose.

Studio is not built to make a pretty graph. It is built so the operator can run ChaseOS — approving actions, inspecting state, tracking what agents and workflows are doing, and making governed decisions — using a visual surface instead of raw file navigation.

The graph is how you see the system. The cockpit is how you operate it. Both are necessary. Neither alone is enough.

### Agentic Affordances Layer

Studio is built knowing that agents and harnesses are actors in the system alongside the human operator. As runtime capability grows, Studio surfaces agentic activity as first-class graph content:
- AOR workflow outputs become graph nodes with typed edges back to the workflow that produced them
- Agent touchpoints appear as `touched-by-agent` runtime edges
- Pending approvals from workflow runs surface in the Approval Center and on the graph
- The Timeline / Ledger View makes the full agent and operator action history navigable
- Role cards and permission ceilings are visible in the Agent / Operator Browser
- Provenance and chronology bridge/application mapping is documented in `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`

This is not an advanced feature toggled on later. The graph model must account for agents as actors from the beginning — both human and automated actions produce nodes, edges, and audit events that Studio surfaces the same way.

---

## 3. ChaseOS vs ChaseOS Studio — Distinction

| Layer | What It Is |
|-------|------------|
| **ChaseOS** | The full operating system, framework, and control plane — ingestion, intelligence, governance, runtime, agent contracts, memory architecture, and enforcement hooks |
| **ChaseOS Studio** | The human-facing standalone desktop product layer — the graph-first visual operating surface for using, visualizing, navigating, inspecting, and safely interacting with ChaseOS |

Studio is NOT ChaseOS. ChaseOS is the constitutional system. Studio is its interface.

Studio does not:
- Replace vault governance or the Gate
- Create a second unmanaged truth store
- Bypass service-layer write rules
- Override trust tier ceilings
- Autonomously promote canonical state

Studio does:
- Surface ChaseOS structure visually
- Make governed operations accessible to a mouse-first operator
- Enforce the same write rules through a service layer
- Route all state-changing actions through the appropriate ChaseOS infrastructure

---

## 4. Operating Modes

Studio supports two primary modes:

### Mode A — ChaseOS Native

When opened against a ChaseOS-compliant workspace, Studio understands:
- ChaseOS node types and folder conventions
- Trust states (raw, quarantined, suggested, promoted, canonical, archived, disputed, generated)
- Provenance rules and sidecar metadata
- Promotion states and lifecycle rules
- Workflow, runtime, and agent objects
- Governed writeback rules and approval requirements
- Protected and canonical surfaces
- AOR event bus and runtime interaction contract (Phase 9 OSRIL)

### Mode B — General Markdown / Obsidian-Compatible

When opened against a normal markdown folder or Obsidian vault, Studio works as:
- A high-quality visual graph and file productivity surface
- A markdown-compatible graph explorer with best-effort node type inference
- A migration and onboarding path into ChaseOS-native mode later

Compatibility behavior:
- Scan folder structure and detect markdown files
- Detect links, wikilinks, frontmatter, and block structure
- Infer graph structure from links
- Classify files into best-effort node types (Project, Source, Log, Knowledge, etc.)
- Preserve backward compatibility — no mutations to existing files without explicit operator action
- Offer optional upgrade into ChaseOS-native mode at any time

This means Studio is usable without a full ChaseOS installation. General markdown vault users are a first-class entry path.

---

## 5. Entry Points

### 5A — Start New

Create a new ChaseOS-native workspace from scratch:

1. Prompt for workspace name, location, and domain selection
2. Scaffold baseline ChaseOS folder structure (`00_HOME` through `99_ARCHIVE`)
3. Generate required starter files — `CLAUDE.md`, `README.md`, `ROADMAP.md`, `PROJECT_FOUNDATION.md`
4. Initialize system map and core `Now.md` sprint focus file
5. Bootstrap initial graph with core root nodes
6. Generate default ontology/schema pack
7. Create default role cards and starter workflow manifests (status=draft)
8. Start file watching and indexing
9. Open Studio in ChaseOS-native mode against the new workspace

### 5B — Open Folder

Open an existing workspace — Obsidian vault, ChaseOS workspace, or general markdown folder:

1. Scan folder structure
2. Detect markdown files, links, wikilinks, frontmatter, and blocks
3. Infer graph structure from link analysis
4. Classify files into best-effort node types
5. Detect ChaseOS-compliance (presence of `CLAUDE.md`, ChaseOS schema in frontmatter)
6. If ChaseOS-native: enable full governance and trust-state surfaces
7. If general markdown: open in compatibility mode, offer upgrade path
8. Preserve full backward compatibility — no mutations without explicit action

---

## 6. Graph Prerequisites

Before Studio can render a meaningful graph, certain architectural requirements must be met. These are not implementation details — they are design constraints that apply at every subphase.

### 6A — Stable Node Identity

**Nodes must have a stable identity beyond their filename or path.**

A node's identity cannot be its filepath. Filenames change. Files move. Vaults get reorganized. If the graph is anchored to filepaths as node identity, every rename or move breaks edges, provenance links, audit trail references, and runtime-action links.

Studio requires a `node_id` system:
- Each node has a persistent identifier independent of filename and path
- The `node_id` is stored in frontmatter or a graph manifest
- Edge definitions reference `node_id` values, not file paths
- Rename or move of a file does not invalidate existing edges
- In ChaseOS-native mode: `node_id` is part of the ChaseOS frontmatter schema
- In compatibility mode: Studio generates and maintains a local identity manifest (not written into the source files without operator consent)

### 6B — Typed Schemas and Canonical Metadata

Studio requires a stable schema for each node type:
- Each node family has a defined set of expected frontmatter fields
- Schema is used to classify nodes, generate typed edges, and validate mutations
- The schema pack can be extended but not silently mutated
- In ChaseOS-native mode: the ChaseOS frontmatter conventions are the schema
- In compatibility mode: Studio infers schema from detected patterns; operator can refine

### 6C — Graph Builder, Indexer, Watcher

Studio must not require hand-rebuilding the graph each session. The graph infrastructure must:

1. **Build deterministically** — given the same vault state, the graph builder must produce the same graph. No randomness, no session-local state in the graph model.
2. **Index on open** — when a workspace is opened, Studio scans, parses, and indexes the graph. The index is cached locally.
3. **Watch for changes** — Studio maintains a filesystem watcher. When files are created, modified, or deleted, the graph index is updated incrementally without a full rebuild.
4. **Rebuild safely** — if the index is missing or corrupt, Studio can rebuild from scratch from the vault state. The vault is always the source of truth. The graph index is a derived view.
5. **Rebuild on new machine** — if the operator opens the same vault on a different machine (or reinstalls Studio), the full graph must be reconstructable from the vault files alone. No graph state should live exclusively in the Studio installation.

This is the **install-once / rebuild-anywhere** requirement. The vault is portable. The graph must be too.

### 6D — Deterministic Edge Creation

Structural edges (7B) must be created deterministically from vault structure and frontmatter:
- `belongs-to-project` is determined by folder location and frontmatter
- `source-of` / `derived-from` is determined by `source_ref` frontmatter fields
- `generated-by` is determined by `generated_by` frontmatter field
- All structural edges must be reproducible from the vault state alone

This ensures that a graph rebuilt from scratch produces the same structural topology as the cached graph.

---

## 7. Node Ontology

Studio recognizes the following minimum node families. In ChaseOS-native mode these map directly to vault objects. In compatibility mode they are inferred from file content, naming, and structure.

| Node Family | Description | ChaseOS Source |
|-------------|-------------|----------------|
| **Project** | Active project with operating file, goals, and status | `01_PROJECTS/[Domain]/[Project]-OS.md` |
| **Source** | Promoted source knowledge in a SIC workspace | `runtime/source_intelligence/workspaces/` |
| **Synthesis** | Multi-source synthesis or derived knowledge note | `02_KNOWLEDGE/[Domain]/` |
| **Knowledge** | Classified knowledge note with trust tier | `02_KNOWLEDGE/[Domain]/` |
| **SOP** | Standard operating procedure | `04_SOPS/` |
| **Workflow** | AOR workflow manifest | `runtime/workflows/registry/` |
| **Agent** | Agent definition with role card and trust tier | `06_AGENTS/` |
| **Runtime** | Active runtime configuration and state | AOR engine state |
| **Decision** | Immutable decision ledger entry | `07_LOGS/Decision-Ledger/` |
| **Log** | Build log, daily note, or operator brief | `07_LOGS/` |
| **Generated Artifact** | AI-generated output pending endorsement | `02_KNOWLEDGE/[Domain]/Generated-Ideas/` |
| **Intake** | Quarantined item pending promotion | `03_INPUTS/00_QUARANTINE/` |
| **Template** | Reusable content template | `05_TEMPLATES/` |
| **Domain** | Top-level domain node (18 domains) | `00_HOME/Operating-System.md` |

---

## 8. Edge Ontology

Studio models four distinct link layers:

### 7A — Explicit Links
Direct, declared relationships:
- Wikilinks and backlinks (`[[TargetNode]]`)
- Manual visual links created via drag or context menu
- Inline relationships declared in frontmatter (`source_ref`, `linked_index`, etc.)

### 7B — Structural Links
Inferred from ChaseOS schema and folder conventions:
- `belongs-to-project`
- `belongs-to-domain`
- `source-of` / `derived-from`
- `generated-by`
- `uses-workflow`
- `output-of-runtime`
- `child-of` / `parent-of`
- `block-containment`

### 7C — Suggested Semantic Links
Probable relationships surfaced by Studio for operator review:
- Probable topic overlap
- Likely support / belongs-to / merge / contradiction signals
- Visible as a distinct edge type — not canonical until operator accepts
- Acceptance makes the link structural; rejection discards without mutation

### 7D — Runtime / Action Links
Links produced by ChaseOS runtime activity:
- `touched-by-agent`
- `used-by-workflow`
- `blocked-by-policy`
- `pending-approval`
- `produced-by-scheduled-run`
- `linked-to-audit-log`

---

## 9. Trust and Provenance Model

Studio surfaces and enforces the ChaseOS trust state model. Every node in Studio has a visible trust state. Nodes cannot change state without an appropriate action through the service layer.

### Trust / Lifecycle States

| State | What It Means |
|-------|---------------|
| **raw** | Captured, not yet reviewed |
| **quarantined** | In quarantine boundary, awaiting triage |
| **suggested** | AI-suggested link or synthesis, not yet operator-accepted |
| **promoted** | Passed through Gate, in SIC workspace or knowledge index |
| **canonical** | Immutable system truth (protected files, role cards, decision ledger entries) |
| **archived** | Retired, no longer active |
| **disputed** | Flagged for review — trust state contested |
| **generated** | AI-generated artifact in the Generated Ideas layer |

### Provenance Visibility
Studio can trace any node back through its capture and promotion history:
- Original capture source (sidecar `.meta.json`)
- Capture method and connector
- Quarantine status at capture
- Promotion path and Gate decision record
- Any AOR workflow that produced or modified the node
- Audit trail entries referencing the node

This trace is read-only. The provenance chain cannot be edited through the Studio UI.

### Generated vs Canonical Separation
Studio enforces the AI-Generated-Output-Bridge architecture:
- Generated artifacts are visually distinct from promoted/canonical nodes
- Promoted/canonical state requires explicit operator approval action
- No silent promotion through Studio UI
- Generated artifacts that are promoted must go through the Gate → service layer chain

### Trust Visibility Principle: Visible but Light

Trust state is always surfaced — every node carries its state. But for promoted and canonical nodes (the healthy majority), trust state should be a quiet indicator, not a barrier. Visual weight scales with urgency: a canonical node carries a small indicator; a quarantined or generated node carries a clear visual call-to-action. The friction is reserved for raw, quarantined, and generated nodes where the operator needs to take action — not for the trusted content the operator is simply using.

---

## 10. Service Layer

Studio requires a service layer between the UI and the vault filesystem.

**The service layer is the traffic controller.** Every state-changing action — create, edit, link, promote, delete — goes through the service layer before touching the filesystem. The UI never writes directly to the vault. The service layer is where ChaseOS governance lives in the product.

The service layer:
1. **Validates** every requested action before execution (schema, trust conditions, permissions)
2. **Enforces** governance rules — protected-file boundaries, Gate policies, promotion rules
3. **Updates** files safely through the appropriate write path
4. **Indexes** graph state after each write (triggers incremental graph index update)
5. **Logs** actions in the audit trail where required
6. **Coordinates** approval surfaces for gated actions (pause, present, wait, record)
7. **Emits** events to the OSRIL event bus for runtime visibility

The UI should feel easy. The write path is still governed.

**This is not optional.** Studio without a service layer is an uncontrolled vault writer. Every write that touches ChaseOS state must go through the service layer. This applies in both ChaseOS-native mode and compatibility mode.

---

## 11. Action Model

### Safe Low-Friction Actions (direct execution)

- Create a new node/file from graph
- Create a visual link between two nodes
- Edit local metadata on a node (non-schema-affecting)
- Add a block or note from graph view
- Move/reorganize visual layout (graph position data only — not file location)
- View/inspect any node, edge, or provenance chain

### Approval-Gated Actions (require inline confirmation)

- Canonical promotion (quarantine → promoted → canonical)
- Editing protected files (`SOUL.md`, `Principles.md`, `CLAUDE.md`, `Permission-Matrix.md`, etc.)
- Schema-affecting mutations (frontmatter changes that alter node classification)
- AI-generated suggestions becoming durable truth
- AOR workflow actions with real filesystem side effects
- Merges that alter active project state
- Any action touching a node in `canonical` trust state

Approval records for gated actions are immutable once written to the audit trail.

### Blocked Actions (out-of-contract — surface as explanation, not failure)

- Editing files above the operator's trust tier ceiling
- Directly overwriting canonical trust-state records (Decision Ledger, Permission Matrix, Trust Tiers)
- Promotion actions that would skip the Gate
- Any write that would bypass the service layer
- Operations that the active role card explicitly forbids

Blocked actions must be surfaced clearly with an explanation, not silently swallowed or presented as a generic error. The operator must know what was blocked and why — not just that something failed.

---

## 12. Main Interface Views

Studio ships with these primary views:

| View | Description | Phase Target |
|------|-------------|-------------|
| **Graph View** | Graph-first home — all nodes, edges, trust states, provenance overlays | 10A/10B |
| **Node Inspector** | Detailed node view — content, metadata, trust state, provenance chain, linked edges | 10A/10B |
| **File / Repository View** | Raw file browser for power users and debugging | 10A |
| **Project / Workspace View** | Project-centric view — active projects, domain grouping, sprint focus | 10B/10C |
| **Runtime / Operator View** | AOR pipeline status, workflow activity, audit trail, agent visibility | 10D |
| **Intake / Promotion View** | Quarantine queue, promotion approvals, hint editing before Gate | 10C/10D |
| **Canvas / Whiteboard View** | Freeform investigation boards, architecture maps, spatial clustering | 10E |
| **Settings / Config View** | Provider config, watch folders, scaffold settings, automation comfort level | 10F |
| **Import / Onboarding View** | Open Folder flow, migration helpers, Obsidian import, ChaseOS bootstrap | 10F |
| **Timeline / Ledger View** | Chronological log of actions, approvals, promotions, and audit events — the system's own history made navigable | 10D |

**Graph View is the primary home view.** The graph is the map you always return to. All other views are tabs or panels that open around the graph — they do not replace it. The tab model: Graph View is the persistent base; Node Inspector, Runtime View, Intake View, and Canvas open as tabs or side panels. The graph is never buried.

Studio's layout model: **graph-first home with multiple tabs/views accessible around it** — not a flat multi-pane workspace where graph is one option among many.

**Graph Filters:** The graph view must support filtering by node type, trust state, edge type, domain, and project. Filters are not a late-stage UI polish feature — they are a core navigation requirement. A full vault graph is visually complex. Filters are how the operator reduces signal-to-noise to find what they need. Filter presets (e.g., "show only quarantined nodes," "show only this project's edges") should be saveable and recallable.

---


## 13. Phase 10A Runtime-Interface Priority Lanes

This section records the 2026-04-29 final Phase 9 → Phase 10 planning pass. The runtime substrate already exposes enough command/read surfaces to begin interface work, but the features below will not feel testable or operable until Studio provides a real desktop/product shell over them. Build them as governed views over ChaseOS-owned state, not as new authority systems.

| Lane | Studio responsibility | Current substrate to wrap | Non-negotiable boundary |
|---|---|---|---|
| **Settings / Provider / Config UI** | Show config validity, default runtime/provider posture, model/provider readiness, degradation reasons, and next actions | `chaseos config validate`, `chaseos config summary`, `chaseos runtime provider-status` | No credential display; no provider switching/recovery without explicit Gate-governed action |
| **Approval Center** | Present pending approvals, wait/resume state, immutable decisions, and explicit resume-ready actions. Canonical doc: [[ChaseOS-Approval-Center]] | OSRIL approval records, `osril wait-resume`, `osril resume-ready --dry-run` | Approval and resume are separate visible steps; no hidden auto-resume |
| **Runtime Cockpit** | Show Agent Bus queue health, bounded task lists, heartbeats, lifecycle/coordination-watch proof, runtime startup/autostart state, runtime/provider status, and degraded/stuck posture | `chaseos studio runtime-cockpit`, `agent-bus status`, task list/heartbeats, coordination-watch activation reports/checklists, provider-status, runtime registry/lifecycle | Read-only by default; mutations such as cleanup/cancel/retry and startup/autostart changes require scoped filters, explicit confirmation, and service-layer execution |
| **Provenance Explorer** | Navigate capture → normalization → promotion → workflow/audit lineage from any output/node | Provenance Schema, trace reports, sidecars, AOR/Agent-Activity records | Provenance is immutable/read-only from the UI |
| **Memory / Agent Identity Ledger UI** | Inspect runtime profiles, identity ledgers, repair memory, scorecards, nav overlays, and task-local memory | `chaseos memory summary/show/ledger`, runtime memory files | Layer C/D memory is advisory; never a permission grant or canonical truth override |
| **Runtime Support Loops** | Inspect QA verification, proactive-suggestion, usage-metrics, and repair-candidate packets as operator support evidence | `runtime/studio/runtime_support_loops.py`, `StudioAPI.get_runtime_support_loops_panel`, native `runtime-support-loops` panel | Read-only/advisory-only; no approval consumption, Agent Bus task creation, runtime dispatch, memory mutation, repair application, provider/connector call, self-upgrade, or canonical writeback |
| **Graph / Node UI** | Render node/edge ontology, trust states, runtime/action edges, block identities, and graph filters | `runtime/graph/`, vault markdown/frontmatter, provenance schema | Graph index is derived/rebuildable; service layer owns writes |
| **Voice / Visual / Companion Surfaces** | Provide multimodal interaction and companion UX over the same operator-shell state | Future OSRIL/Agent Bus ingress adapters | Tier-4 input by default; translate into structured state; no direct authority expansion |
| **Reconnect / History / Continuation UX** | Replay history, restore active tasks/sessions, show approval waits, and continue operator-shell sessions after reconnect | OSRIL events/sessions, Agent Bus tasks, audit logs | This is transport/presentation over existing truth, not a second memory store |

Design implication: Studio's early architecture should include a runtime-state service boundary immediately, even if the first visible feature is the narrower Phase 10A0 acquisition cockpit. Otherwise each feature will grow its own ad hoc status reader and the product shell will fracture.

Phase 10A0 UI implementation handover: `06_AGENTS/Phase10A0-UI-Runtime-Handover.md`.

### 13A. Runtime Startup Controls

Studio's Runtime Cockpit must include explicit user-controlled startup toggles for each runtime that declares startup support in its lifecycle record.

The UI requirement is:
- show whether each runtime supports a gateway launcher, coordination-watch supervisor, and coordination-watch bootstrap/autostart registration
- show state separately as `configured`, `registered`, `running`, `degraded`, and `proven-after-reboot` rather than collapsing all of those into a single "on" label
- let the operator turn supported startup behavior on or off per runtime, including Hermes, OpenClaw, and future runtime lanes
- render the `startup-surface-settings` model as the settings/source-of-truth layer for these controls, including runtime-specific launcher profiles and drift status
- route every startup/autostart mutation through the governed service layer and lifecycle/Gate operations; the current Studio CLI wrapper is `chaseos studio runtime-startup-controls`, and the localhost visual wrapper is `chaseos studio runtime-startup-controls-app`; broad Studio desktop integration must keep wrapping that service-layer path, `startup-surface-toggle --confirm`, or the startup-surface approval request/decision/preflight/consumption chain rather than writing host startup state directly
- use `runtime/studio/runtime_cockpit.py` and `chaseos studio runtime-cockpit --runtime <id|all> --json` as the first read-only desktop contract for the Runtime Cockpit mount; this contract aggregates the Studio Dashboard, Studio App Launcher, and Runtime Startup Controls without creating a desktop shell or new mutation authority
- use `runtime/studio/runtime_cockpit_app.py` and `chaseos studio runtime-cockpit-app --runtime <id|all> --host 127.0.0.1 --port 8771` as the first localhost-only read-only Runtime Cockpit app/mount over that contract; it may serve `/`, `/health.json`, `/contract.json`, and `/app-plan.json`, but it must not toggle startup state, write approval material, start child apps, execute workflows, call providers, automate browsers, deliver messages, mutate schedulers, or write canonical memory
- use `runtime/studio/desktop_shell_app.py` and `chaseos studio desktop-shell-app --runtime <id|all> --host 127.0.0.1 --port 8772` as the first read-only shell-shaped Studio mock over the Runtime Cockpit contract, App Launcher registry, Approval Center, and read-only Pulse product-shell panel; this is a local foothold only, not the full standalone desktop shell, and it must not submit feedback, submit toggles, consume approvals, apply candidates, start child apps, execute workflows, call providers, mutate schedules, or write canonical memory
- display plan digest, approval artifact status, required Gate operation, approval-consumption status, idempotency marker path, host-boundary policy preview, host-mutation audit-template preview, success-marker policy posture, and blockers before any future approval-driven host mutation executor invocation; the current exact blocker/precondition report is `06_AGENTS/Studio-Startup-Host-Mutation-Executor-Blocker-Report.md`
- require operator confirmation against the exact runtime, surface, intent, plan digest, Gate operation, affected target, verification commands, and rollback plan
- never silently add Startup-folder files, Task Scheduler entries, services, launch agents, or cron jobs
- record operator intent and resulting proof in lifecycle artifacts, Agent Activity, and the relevant audit/log surfaces
- preserve runtime-specific host truth, including Windows Startup folder launchers, Task Scheduler tasks, WSL indirection, service managers, or future platform-specific registration methods

New runtimes are not Studio-complete until their adapter/lifecycle onboarding declares the startup surfaces needed for this cockpit: runtime id, UI label, gateway support, coordination-watch support, startup registration kind, enable/disable commands, proof/check commands, expected evidence paths, host platform, privilege/elevation needs, and the difference between current-session running proof and post-reboot proof.

This feature is **PARTIAL / FIRST RUNTIME COCKPIT DESKTOP CONTRACT + LOCAL READ-ONLY RUNTIME COCKPIT MOUNT + READ-ONLY STUDIO DESKTOP SHELL MOCK + LOCAL STUDIO VISUAL WRAPPER + STUDIO CLI WRAPPER + BACKEND CLI TOGGLE EXECUTOR + REPORT + SETTINGS MODEL + TOGGLE PLAN + MUTATION CONTRACT + EXECUTOR PREFLIGHT + APPROVAL REQUEST/DECISION/CONSUMPTION ARTIFACTS IMPLEMENTED / FULL STANDALONE STUDIO DESKTOP SHELL UNBUILT / APPROVAL-DRIVEN HOST MUTATION EXECUTOR UNBUILT**. Current Hermes/OpenClaw startup work provides machine-local artifacts, lifecycle declarations, `chaseos runtime startup-surfaces --runtime all --json` for Studio state rendering, `chaseos runtime startup-surface-settings --runtime all --json` for CLI/Studio settings rendering, `chaseos runtime startup-surface-toggle-plan --runtime <id> --surface <surface_id> --intent enable|disable --json` for pre-mutation confirmation, `chaseos runtime startup-surface-mutation-contract --runtime <id> --surface <surface_id> --intent enable|disable --json` for approval/UI wiring, `startup-surface-approval-request`, `startup-surface-approval-decision`, `startup-surface-executor-preflight`, `startup-surface-approval-consumption`, host-boundary policy preview, and host-mutation audit-template preview for no-host-mutation approval artifact, exact-once marker, and audit-readiness handling, `chaseos runtime startup-surface-toggle --runtime <id> --surface <surface_id> --intent enable|disable --confirm` for direct guarded CLI mutation, `chaseos studio runtime-startup-controls --runtime <id|all> --json` plus `--action dry-run|toggle` for the Studio-facing CLI control wrapper, `chaseos studio runtime-startup-controls-app --runtime <id|all> --host 127.0.0.1 --port 8766` for a localhost-only visual wrapper, `chaseos studio runtime-cockpit --runtime <id|all> --json` for the first read-only desktop contract, `chaseos studio runtime-cockpit-app --runtime <id|all> --host 127.0.0.1 --port 8771` for the first read-only localhost Runtime Cockpit mount over that contract, and `chaseos studio desktop-shell-app --runtime <id|all> --host 127.0.0.1 --port 8772` for the first read-only shell-shaped Studio mock. The 2026-05-02 closeout pass confirmed the originating runtime-startup chat is closeable; remaining work is full standalone Studio desktop shell integration, preference records beyond mutation audit markers, post-login/reboot proof per user instance, approval center UI wiring, and approval-driven host mutation after consumption.

Portable handoff for this feature: `06_AGENTS/Runtime-Startup-Controls-Portable-Handoff.md`. Studio implementation should treat that file as the product/instance portability checklist for startup/autostart controls.

---
## 14. Implementation Subphases

### 10A — Studio Core Shell (Foundation)

Desktop application shell and minimum viable product foundation:
- Desktop shell (Tauri, Electron, or equivalent framework — TBD at engineering pass)
- Read-only desktop shell foundation contract (`chaseos studio desktop-shell-foundation`) for current footholds, planned gaps, workspace detection posture, authority boundaries, and implementation sequence
- Read-only Open Folder readiness contract (`chaseos studio open-folder-readiness`) for operator-selected folder mode detection and future scanner/UI wiring
- Read-only markdown scan contract (`chaseos studio markdown-scan-contract`) for bounded file/content scanning and future graph-index input
- Read-only derived graph-index contract (`chaseos studio graph-index-contract`) for deterministic in-memory node/edge identity over markdown scan output
- Read-only node-inspector contract (`chaseos studio node-inspector-contract`) for selected derived graph node detail, related edges/nodes, and bounded source excerpts
- Read-only graph-view contract (`chaseos studio graph-view-contract`) for bounded visible graph payloads, deterministic layout coordinates, filters, legends, and optional focus context over the derived graph model
- Local static graph-view renderer (`chaseos studio graph-view-static-render`) for explicit static HTML graph artifacts under `07_LOGS/Studio-Graph-Views`
- Read-only graph-view shell-panel contract and Studio shell mock mount (`chaseos studio graph-view-shell-panel`, `chaseos studio desktop-shell-app --dry-run --json`) over the verified static graph artifact
- Read-only desktop shell mock over Runtime Cockpit contract (`chaseos studio desktop-shell-app`) as a local foothold, not the full shell
- Targeted responsive/browser QA for that shell mock is complete; full product-shell visual QA remains future
- Start New / Open Folder entry flows
- File scan, markdown parser, and link detector
- Service layer foundation (validation, write path, index coordination)
- Graph engine foundation (node/edge data model, render pipeline)
- Node Inspector UI foundation (view node content and metadata over the read-only contract)
- Basic File / Repository View

Outputs: A working desktop app that can open a markdown folder, build a graph, and display nodes.

### 10B — Graph + Node Model

Full graph data model and visual surface:
- Typed nodes with ChaseOS ontology support
- Typed edges with all four link layer classes
- Block support path (blocks as first-class graph citizens)
- Trust state overlays (node color/badge by state)
- Provenance overlays (provenance chain accessible from graph)
- Generated / canonical visual separation
- Semantic link suggestions (visible, non-canonical until accepted)
- Graph-first home view as default landing surface

**Block support is a product direction, not just a phased feature.** The data model must treat blocks as addressable objects from the beginning — even if the block editing UI is deferred. A block must have a stable address, be linkable from the graph, and be promotable independently from its parent file. The block model affects node identity, edge creation, and the service layer contract. Design the data model with blocks as first-class from 10A. Ship the block interaction UI in 10B.

Outputs: A graph that knows what kind of thing each node is, what its trust state is, and where it came from.

### 10C — Controlled Write Surface

Create and edit from within the graph:
- Create new node/file from graph context menu
- Create visual link between nodes
- Edit node metadata from Node Inspector
- Add block or note inline
- Safe writeback through service layer for all mutations
- Approval queue for higher-risk actions (protected files, canonical promotion)
- Inline approval UI for gated actions

Outputs: Operator can make changes in Studio that persist correctly to the vault with appropriate governance.

### 10D — Project / Runtime Cockpit

Operational visibility and workspace management:
- Project / Workspace View — active projects, domain grouping, sprint focus surface
- Runtime / Operator View — AOR pipeline status, workflow cards, active task feed
- Runtime Cockpit Contract — read-only desktop contract over dashboard, app launcher, and runtime startup controls (`chaseos studio runtime-cockpit`)
- Runtime Cockpit Local Mount — localhost-only read-only app over the Runtime Cockpit contract (`chaseos studio runtime-cockpit-app`)
- Studio Desktop Shell Mock — localhost-only read-only shell-shaped mock over Runtime Cockpit, App Launcher, Approval Center, and the Pulse product-shell panel (`chaseos studio desktop-shell-app`)
- Product UI Test Target — localhost-only safe-mode synthetic Studio product target for Browser Runtime proofing (`chaseos studio product-ui-test-app`)
- Runtime Startup Controls — per-runtime gateway/autostart and coordination-watch/bootstrap toggles backed by lifecycle records, activation reports, and service-layer mutations
- Agent / Operator Browser — registered agents, role cards, permission ceilings, scorecard performance
- Intake / Promotion View — quarantine queue, semantic hint editor, Gate approval surface
- Approval Center — unified queue for all pending approvals across all sources

Outputs: Operator can see what ChaseOS is doing, approve or reject pending actions, and manage project state without raw markdown.

### 10E — Canvas / Whiteboard / Spatial Mode

Freeform investigation and architecture surfaces:
- Whiteboard canvas for investigation boards
- Architecture maps and system diagrams
- Freeform node clustering and grouping
- Notes and annotations on canvas that can link back to graph nodes
- Exported canvas maps (read-only link to canonical nodes)

Phase 10E is now specified in `06_AGENTS/ChaseOS-Studio-Freeform-Canvas-Graph-Linking.md`. The first Canvas lane should treat canvas documents as workspace-local draft JSON with graph-node pointers, draft note cards, groups, artifact references, and visual canvas links. Those links are not canonical graph edges unless a later approval-gated conversion path reuses the existing service-layer/visual-link approval flow. Canvas may display provenance summaries from existing graph/provenance contracts, but must not write provenance sidecars, trust state, source packages, graph snapshots, or canonical knowledge. Browser/Excalidraw integration remains a separate proof/interop lane and is not implied by Canvas UI availability.

**Canvas is a later Studio mode — not the V1 primary identity.** The stronger early wedge is the governed graph and operator cockpit (10A–10D).

### 10F — Import / Compatibility / Setup Experience

Onboarding and migration surfaces:
- Open Folder compatibility flow (general markdown, Obsidian vault detection)
- Migration helpers for adopting ChaseOS conventions incrementally
- Obsidian vault import with best-effort node type inference
- ChaseOS-native bootstrap and enhancement workflows
- Onboarding wizard for new workspace creation (wrapping `chaseos scaffold brain` CLI)
- ChaseOS-native mode upgrade flow for existing Obsidian/markdown vaults

---

## 15. Product Identity

ChaseOS Studio is NOT:
- An Obsidian plugin — it is a standalone desktop application
- A passive graph viewer — it is a governed write surface with runtime visibility
- A note-taking app — it is a control plane interface
- A Notion, AppFlowy, or Logseq clone — it is a provenance-aware, trust-state-aware, runtime-aware, agent-aware visual control surface
- A second unmanaged truth store — it is a window into the existing ChaseOS-governed store

### Reference Stack

Studio draws from existing tools as reference only — not as a base identity. **Do NOT copy their category baggage.** Take what they do well and leave behind what defines their category.

| Reference | What Studio Takes | What Studio Does NOT Take |
|-----------|-------------------|--------------------------|
| Joplin | Offline-first seriousness, import/export practicality, dependable local architecture discipline | Note-app category identity; hierarchical-folder-first navigation |
| AppFlowy | Product shell quality, structured workspace UX, polished multi-view app ambition | Database-block-native identity; Notion-clone positioning |
| Logseq / graph-native tools | Graph-native mental model, block-level awareness, graph ergonomics, spatial/visual linking | Daily-notes-first identity; local-graph-as-primary-purpose |
| Obsidian | Markdown-first conventions, link graph foundation, plugin-style extensibility inspiration | Plugin-ecosystem dependency; passive graph viewer identity |

**The correct product formula:**
> Joplin backend discipline + AppFlowy product shell + Logseq graph ergonomics + ChaseOS governance / provenance / runtime / agent-control semantics

Studio's strongest differentiation is not graph visualization (Obsidian already does this). It is:
- **Governed graph** — every node has a trust state and a provenance chain
- **Provenance-aware graph** — any node can be traced back to its origin
- **Runtime-aware graph** — AOR activity is visible in the graph
- **Agent-aware graph** — agent touchpoints and workflow outputs are surfaced as edges
- **Approval-aware control surface** — high-stakes mutations require operator confirmation
- **Operator cockpit behavior** — Studio knows what the system is doing, not just what is in the vault

### Forkable / Open-Source Product Surface

ChaseOS is designed as a forkable framework (see `FORKING.md`). Studio, as the product shell for ChaseOS, should follow the same principle:

- Studio should be buildable and distributable by anyone running a ChaseOS-compliant vault
- The Studio codebase should be structured so the ChaseOS-native governance layer is a module — not hardcoded into the shell
- Someone with a general markdown vault should be able to run Studio in compatibility mode without any ChaseOS runtime dependency
- The ChaseOS governance layer is opt-in from the Studio perspective (even though it is mandatory from the ChaseOS perspective)

This keeps Studio from being locked to a single distribution and creates the natural onboarding path: general markdown user discovers Studio, uses it in compatibility mode, eventually adopts ChaseOS conventions, upgrades to native mode.

---

## 16. Guardrails

These constraints apply at every implementation subphase:

1. **No second datastore.** Studio writes to the ChaseOS vault through the service layer. It does not maintain its own database of canonical truth.
2. **No silent promotion.** Canonical state changes require explicit operator action through the service layer.
3. **No bypass of Gate.** All promotion actions go through the Gate → service layer chain, not directly to the filesystem.
4. **No permission ceiling expansion.** Studio UI configuration does not change trust tiers, permission matrices, or Gate policies.
5. **Canvas outputs are not canonical.** Canvas notes and clustering are workspace-local artifacts — they do not become canonical knowledge without explicit promotion through the Gate.
6. **Compatibility mode is read-mostly.** General markdown mode can display and navigate but should not make aggressive mutations to non-ChaseOS vaults without clear operator intent.
7. **Service layer is not optional.** No UI feature may write to the vault outside the service layer path.
8. **Generated artifacts stay visually distinct.** Trust state must be visually surfaced at all times — generated vs promoted vs canonical must always be distinguishable.

---

## 17. Phase Dependencies

Studio is blocked on:

| Dependency | Why |
|------------|-----|
| Phase 8 complete (DONE) | Clean quarantine/provenance model; sidecar schema Studio will read |
| Phase 9 OSRIL — Runtime Interaction Contract | Studio consumes AOR events through the event bus; contract must be stable first |
| Phase 9 Runtime Shell — Config Store, Provider Registry | Studio settings surface wraps these |
| Phase 9 — first-wave AOR handlers | Studio runtime view needs real AOR events to display |
| Phase 9 — Provenance Schema | Studio's Provenance Explorer depends on this |

Studio engineering should NOT begin in earnest before Phase 9 first-wave AOR handlers (operator_today, operator_close_day) are operational and the OSRIL Runtime Interaction Contract is stable.

---

## 18. Related Documents

WML feature-family link: [[Workspace-Mode-Layer-Feature-Family]].

- `ROADMAP.md` — Phase 10 ChaseOS Studio roadmap
- `06_AGENTS/Feature-Fit-Register.md` — Phase 10 Studio feature registration
- `06_AGENTS/Operator-Surface-Runtime-Interaction.md` — OSRIL (event bus, approval flow)
- `06_AGENTS/ChaseOS-Runtime-Shell.md` — Runtime Shell (command surface, scaffold generator)
- `06_AGENTS/SIC-Architecture.md` — Source Intelligence Core (what Studio surfaces for knowledge)
- `06_AGENTS/AI-Generated-Output-Bridge.md` — generated/canonical separation rules
- `06_AGENTS/Permission-Matrix.md` — protected files Studio must not bypass
- `06_AGENTS/Trust-Tiers.md` — trust state model Studio must surface
- `04_SOPS/Untrusted-Input-Handling-SOP.md` — input handling rules in Studio intake views
- `PROJECT_FOUNDATION.md` — system-level context
- `README.md` — public product framing

---

*ChaseOS Studio Architecture — v1.19 | Created: 2026-04-08 | Updated: 2026-04-09 (spec reconciliation pass v1.1 — Section 6 "Graph Prerequisites" added; Section 2 cockpit framing; Section 10 traffic controller; Section 12 tab model; Section 13 block as product direction; Section 14 category baggage + forkable surface; sections renumbered) | Updated: 2026-04-09 (final verification pass v1.2 — Section 1 Audience and Platform subsection added: web excluded from V1, user-first priority; Section 2 Agentic Affordances Layer subsection added; Section 9 "Trust Visibility Principle: Visible but Light" subsection added; Section 11 Blocked Actions third tier added; Section 12 Timeline/Ledger View row added + Graph Filters note added) | Updated: 2026-04-29 (v1.3 — Phase 10A runtime-interface priority lanes added: Settings/provider/config UI, OSRIL Approval Center, Runtime Cockpit, Provenance Explorer, Memory/Agent Identity Ledger UI, graph/node UI, voice/visual/companion ingress surfaces, and reconnect/history continuation UX) | Updated: 2026-04-30 (v1.4 — Runtime Startup Controls added as a Phase 10 Runtime Cockpit requirement with per-runtime user toggles and future-runtime lifecycle declaration requirements) | Updated: 2026-04-30 (v1.5 — startup-surfaces read-only backend report added as the first Runtime Cockpit state contract; UI toggles remain unbuilt) | Updated: 2026-04-30 (v1.6 — startup-surface-toggle-plan added as the no-mutation pre-confirmation contract for future UI toggles) | Updated: 2026-05-01 (v1.7 — startup-surface-mutation-contract added as the no-mutation approval/executor contract; UI and executor remain unbuilt) | Updated: 2026-05-01 (v1.8 — startup-surface-executor-preflight added as the no-mutation guarded executor validation contract; UI, approval consumption, idempotency marker writes, and executor remain unbuilt) | Updated: 2026-05-01 (v1.9 — startup-surface-settings added as the CLI/Studio settings model and Hermes gateway WSL retry profile recorded; UI, preference writes, and executor remain unbuilt) | Updated: 2026-05-01 (v1.10 — startup-surface-toggle added as direct guarded CLI executor; Studio UI and approval-artifact flow remain unbuilt) | Updated: 2026-05-01 (v1.11 — `chaseos studio runtime-startup-controls` added as the Studio CLI control wrapper; visual UI and approval-artifact flow remain unbuilt) | Updated: 2026-05-01 (v1.12 — `chaseos studio runtime-startup-controls-app` added as the localhost visual wrapper; broad Studio desktop integration and approval-artifact flow remain unbuilt) | Updated: 2026-05-02 (v1.13 — portable runtime startup controls handoff linked for non-personal ChaseOS instances) | Updated: 2026-05-02 (v1.14 — startup-surface approval request/decision/consumption artifact chain added; approval-driven host mutation remains unbuilt) | Updated: 2026-05-02 (v1.15 — Studio Dashboard App Launcher panel added as read-only composition over the launcher registry; child app start remains outside dashboard authority) | Updated: 2026-05-02 (v1.16 — runtime-startup closeout readiness confirmed; Studio readiness packets include host-mutation audit-template preview and remaining work is future desktop/executor/reboot-proof product work) | Updated: 2026-05-02 (v1.17 — `chaseos studio runtime-cockpit` added as the first read-only Runtime Cockpit desktop contract; desktop shell mount and approval-driven host mutation remain unbuilt) | Updated: 2026-05-02 (v1.19 — `chaseos studio runtime-cockpit-app` added as the first localhost-only read-only Runtime Cockpit mount over the contract; full standalone desktop shell integration and approval-driven host mutation remain unbuilt).*


*Additional update: 2026-05-02 (v1.18 — Pulse Deck app registered as localhost-only candidate-feedback UI proof; broad Studio desktop remains future).*

*Additional update: 2026-05-02 (v1.20 — `chaseos studio desktop-shell-app` added as a localhost-only read-only Studio Desktop shell mock over the Runtime Cockpit contract and App Launcher registry; full standalone desktop shell, approval center UI, and approval-driven host mutation remain unbuilt).*

*Additional update: 2026-05-02 (v1.21 — `chaseos studio product-ui-test-app` added as a localhost-only safe-mode synthetic product UI target for Browser Runtime proofing; this is not the full Studio shell and grants no workflow, provider, Agent Bus, Gate, trusted-write, or canonical-writeback authority).*

*Additional update: 2026-05-02 (v1.22 — targeted in-app browser visual QA for `chaseos studio desktop-shell-app` fixed responsive overflow and long-command wrapping in the shell mock; this verifies the mock surface only, not the full standalone Studio desktop shell).*

*Additional update: 2026-05-02 (v1.23 - `chaseos studio desktop-shell-foundation --json` added as a read-only Phase 10A foundation contract over current Studio footholds, planned gaps, workspace detection posture, authority boundaries, and next implementation sequence; this does not build the full standalone desktop shell).*

*Additional update: 2026-05-02 (v1.24 - `chaseos studio approval-center-app` added as a localhost-only read-only Pulse Approval Center mount over the Pulse approval-center readiness contract; approval execution, candidate apply, Agent Bus task writes, schedule activation, provider/connector calls, memory approval, canonical writeback, and full standalone Studio remain unbuilt).*

*Additional update: 2026-05-02 (v1.25 - `chaseos studio open-folder-readiness --json` added as a read-only Phase 10A/10F Open Folder readiness contract over operator-selected folder shape, bounded markdown path inventory, ChaseOS-native/general-markdown mode detection, and authority boundaries; full Start New/Open Folder UI, markdown scanner/parser, graph index, node inspector, workspace upgrade writer, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-02 (v1.26 - `chaseos studio markdown-scan-contract --json` added as a read-only Phase 10A bounded markdown scanner contract over file discovery, frontmatter-key detection, headings, wikilinks, markdown links, tags, tasks, and block-id markers; graph index, node IDs, node inspector, workspace upgrade writer, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.27 - `chaseos studio graph-index-contract --json` added as a read-only Phase 10A/10B derived graph-index contract over bounded markdown scan output with deterministic in-memory node and edge identities; persisted graph engine, node-ID writes, node inspector, workspace upgrade writer, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.28 - `chaseos studio node-inspector-contract --path <file> --json` added as a read-only Phase 10A/10B node-inspector contract over the derived graph model; node inspector UI, graph rendering, persisted graph engine, node-ID writes, node editing, workspace upgrade writer, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.29 - `chaseos studio graph-view-contract --json` added as a read-only Phase 10A/10B graph-view contract over the derived graph and node-inspector models; graph rendering UI, static graph artifact output, persisted graph engine, node editing, workspace upgrade writer, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.30 - `chaseos studio graph-view-static-render` added as a local static HTML renderer over the verified graph-view contract; dry-run renders in memory, `--write` writes only under `07_LOGS/Studio-Graph-Views`, and browser visual QA, shell mounting, persisted graph engine, node editing, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.31 - targeted in-app browser QA for `chaseos studio graph-view-static-render` verified the generated static HTML artifact and recorded evidence under `07_LOGS/Studio-Graph-Views`; readiness contracts now advance to the shell-panel contract lane while shell mounting, interactive graph controls, persisted graph engine, node editing, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.32 - `chaseos studio graph-view-shell-panel --json` added as a read-only shell-panel contract over the verified static graph artifact and browser-QA evidence; readiness contracts now advance to `phase10-studio-graph-view-shell-panel-mount` while actual shell mounting, interactive graph controls, persisted graph engine, node editing, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.33 - `chaseos studio pulse-product-shell-panel --json` added as a read-only panel contract over the browser-QA verified integrated Pulse product shell; interactive Pulse controls, approval execution, candidate apply, schedule activation, provider/connector calls, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.34 - `chaseos studio desktop-shell-app --dry-run --json` now mounts the browser-QA verified Pulse product shell as a read-only `#pulse` panel and exposes `/pulse-product-shell.json`; this is not full standalone Studio and grants no feedback execution, approval execution, candidate apply, runtime dispatch, schedule activation, provider/connector calls, or canonical writeback authority).*

*Additional update: 2026-05-03 (v1.35 - `chaseos studio pulse-deck-app --dry-run --json` now exposes the full Pulse feedback/action vocabulary as candidate-only governed controls; candidate apply, memory approval, task creation, Agent Bus writes, runtime dispatch, schedule activation, providers/connectors, and canonical writeback remain blocked).*

*Additional update: 2026-05-03 (v1.36 - `chaseos studio desktop-shell-app --dry-run --json` now mounts the Graph View shell-panel contract read-only under `#graph-view` and exposes `/graph-view-shell-panel.json`; graph-index persistence, node editing, node ID writes, interactive graph controls, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.37 - targeted browser QA for the mounted Graph View shell panel is verified under `07_LOGS/Studio-Graph-Views`; `chaseos studio desktop-shell-foundation --json` now advances graph/node productization beyond graph shell QA while graph-index persistence, node editing, node ID writes, service-layer writes, and canonical writeback remain unbuilt).*

*Additional update: 2026-05-03 (v1.38 - `chaseos studio node-inspector-shell-panel --json` added as a read-only shell-panel contract over selected-node detail and graph context, and `chaseos studio desktop-shell-app --dry-run --json` now mounts it under `#node-inspector` with `/node-inspector-shell-panel.json`; mounted browser QA, node editing, node ID writes, graph persistence, service-layer writes, provider/connector calls, workflow execution, and canonical writeback remain unbuilt or blocked).*

*Additional update: 2026-05-04 (v1.39 - `chaseos studio desktop-shell-app --qa-runner --write-qa-evidence` added as a bounded internal HTTP QA runner for the mounted Node Inspector shell panel; it writes optional evidence under `07_LOGS/Studio-Graph-Views` and shuts down before returning while visual browser screenshot QA, node editing, node ID writes, graph persistence, service-layer writes, provider/connector calls, workflow execution, and canonical writeback remain unbuilt or blocked).*

*Additional update: 2026-05-04 (v1.40 - `runtime/studio/shell/` is now the active native PyWebView Studio shell lane after Pass 10A, and the first Pass 10B slice adds read-only UI-local graph filters, node type shape mapping, trust-state ring emphasis, edge family styles, and an edge legend; graph persistence, node editing, node ID writes, service-layer writes, provider/connector calls, workflow execution, and canonical writeback remain unbuilt or blocked).*

*Additional update: 2026-05-14 (v1.42 - the Workspace Mode Layer now has a read-only Studio panel at `runtime/studio/workspace_mode_panel.py`, URL-persistent `wml_mode` selection in the desktop shell, project/domain/route cards, Chat-side WML deeplink cards, desktop/mobile screenshot proof, and canonical feature-family node `06_AGENTS/Workspace-Mode-Layer-Feature-Family.md`. These surfaces grant no WML workflow execution, profile writes, Agent Bus task writes, approval consumption, provider calls, or canonical mutation).*

*Graph links: [[Vault-Map]] · [[Workspace-Mode-Layer-Feature-Family]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]]*
 
*Additional update: 2026-05-16 (v1.43 - Personal Context Import now has a read-only Studio planner at `runtime/studio/personal_context_import.py`, a native `context-import` panel, Settings/Dashboard read models, and canonical feature contract `06_AGENTS/Personal-Context-Import-Feature.md`. The surface previews raw intake, parent/child node routing, Knowledge Index resolution, secure storage posture, Workspace Mode `personal_os` integration, and Personal Map candidate boundaries. It grants no raw intake write, node creation, index edit, Personal Map candidate write/apply, provider call, Agent Bus dispatch, runtime memory mutation, or canonical mutation).*

*Additional update: 2026-05-16 (v1.43b - Personal Context Import now includes the temp-only multi-instance fixture harness at `runtime/studio/personal_context_import_multi_instance_fixture_harness.py`. The harness runs anonymized positive and negative context fixtures through the digest-gated preview writer and approved-preview execution proof, verifies parent/child rule coverage, source-digest gating, secret blocking, review artifact boundaries, and no `00_HOME/`, `01_PROJECTS/`, `02_KNOWLEDGE/`, or `06_AGENTS/` canonical writes. Live-vault import writes, Personal Map apply, runtime memory mutation, Agent Bus dispatch, provider calls, and canonical mutation remain blocked).*

*Additional update: 2026-05-16 (v1.43c - Personal Context Import now includes runtime-consumption readiness at `runtime/studio/personal_context_import_runtime_consumption_readiness.py`. Studio can preview a `personal_context_runtime_reference_packet.v1` from Personal Operator Context plus WML `personal_os` using scoped references only. Raw full-memory injection, provider calls, Agent Bus task writes, runtime dispatch, runtime memory mutation, Personal Map apply, credential reads, and canonical writes remain blocked).*

*Additional update: 2026-05-16 (v1.43d - Personal Context Import now includes the canonical-promotion approval preview at `runtime/studio/personal_context_import_canonical_promotion_approval_preview.py`. Studio can compute an exact digest and queue an approval-preview packet for future Dashboard, Personal Operator, Operating System, Projects Hub, Knowledge Index, Personal Domains Index, and intake-index promotion targets. Ambient approval execution is blocked; canonical writes, Personal Map apply, runtime memory mutation, Agent Bus dispatch, provider calls, credential reads, and raw full-memory injection remain blocked until their governed executors exist).*

*Additional update: 2026-05-16 (v1.43e - Personal Context Import now includes the approved canonical-promotion executor at `runtime/studio/personal_context_import_canonical_promotion_approved_executor.py`. The executor consumes one exact-digest approval, requires an operator statement plus protected-target flag, writes managed route blocks to Dashboard, Personal Operator Index, Operating System, Projects Hub, Knowledge Index, Personal Domains Index, and Personal Context Intake Index, reserves an exact-once marker before writes, and writes rollback/evidence/audit records. Personal Map apply, runtime memory mutation, Agent Bus dispatch, provider calls, credential reads, raw full-memory injection, and arbitrary canonical rewrites remain blocked).*

*Graph link addendum: [[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]*

*Additional update: 2026-05-16 (v1.44 - Studio Chat schedule management now includes the approved adapter export packet writer at `runtime/studio/phase11_chat_approved_schedule_adapter_export_packet_writer.py`. It consumes one digest-bound approval and writes only the local adapter export JSON under `runtime/studio/chat/schedule-adapter-exports/`; external scheduler mutation, OpenClaw/Hermes cron mutation, Agent Bus writes, runtime dispatch, Discord/provider calls, credential reads, and broader canonical mutation remain deferred).*

*Additional update: 2026-05-16 (v1.45 - Studio Chat now includes authority-tier controls at `runtime/studio/phase11_chat_authority_tier_controls.py`. The native Chat page groups provider, credential, runtime dispatch, Agent Bus, Discord, and external cron apply lanes as navigation/readiness cards only; live execution, secret reads, provider calls, Discord calls, Agent Bus writes, runtime dispatch, cron mutation, and canonical mutation remain blocked).*

*Additional update: 2026-05-16 (v1.46 - Studio Chat now includes governed authority execution controls at `runtime/studio/phase11_chat_authority_execution_controls.py` plus the live provider executor at `runtime/studio/phase11_chat_live_provider_execution_executor.py`. Manual UI testing can prepare exact digests and run OpenAI provider execution, Hermes dispatch, Discord-control runtime handoff, cron-control runtime handoff, and Agent Bus readback under operator approval; raw secret display, direct Discord API, direct external cron mutation, runtime task claim, and canonical mutation remain blocked).*
