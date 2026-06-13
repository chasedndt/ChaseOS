# ChaseOS Graph Architecture + Runtime Overlay Handover

**Version:** v0.1  
**Date:** 2026-06-01  
**Scope:** ChaseOS Studio Graph page, graph backend, graph renderer, graph tabs/scenes, Agent Bus / runtime daemon overlay, 2D/3D architecture, performance strategy, future agent-native graph features.  
**Status:** Product/architecture handover for upcoming implementation.  
**Primary rule:** This document defines the target architecture and development sequence. It does **not** grant new runtime, writeback, approval, provider, browser, graph mutation, or canonical memory authority.

---

## 0. Executive verdict

The ChaseOS Graph page should not be “Obsidian graph with nicer colors.”

It should become the **live operating map of ChaseOS**:

> **A local-first, agent-aware, provenance-aware graph control surface where the user can see the system, inspect the system, and understand what the agents/runtimes are doing in real time.**

The graph has two jobs:

1. **Stable knowledge map:** docs, memory, source packages, projects, domains, approvals, logs, artifacts, workflows, runtime profiles, provenance, trust states.
2. **Live operating overlay:** Agent Bus tasks, runtime daemon heartbeats, runtime file touches, active edits, approval waits, generated outputs, blocked actions, recent changes.

The current graph renders, but it is not good enough yet. It loads as a dense hairball, the 2D mode can collapse into a line, 3D is too hard to use as a default, labels are not readable enough, performance is not acceptable enough, and the graph is not yet wired to the live Agent Bus / runtime daemon layer.

The next step should be **Graph Architecture + Runtime Overlay development**, not another cosmetic graph prompt.

---

## 1. Current repo truth and internal constraints

ChaseOS already has partial graph substrate and Studio graph surfaces. The feature inventory says Graph View, Node Inspector, Graph Hygiene, and Provenance Explorer are partial product UI surfaces; it also records graph substrate features such as `GraphSnapshot`, `GraphIndex`, deterministic extractors, topology reports, typed overlays, trust/provenance overlays, graph provenance inspector, approval-gated node/link paths, and deferred persisted graph storage. fileciteturn19file0

Studio is explicitly designed as a standalone desktop, graph-first, mouse-first visual surface. The Studio architecture says the graph model is one of ChaseOS’s most valuable interfaces because it exposes nodes, edges, trust states, and provenance chains in a purpose-built visual surface. fileciteturn19file1

Studio should treat agents and harnesses as first-class actors. The architecture already calls out `touched-by-agent` runtime edges, workflow-output graph nodes, pending approvals surfaced on the graph, and a future Timeline/Ledger view for agent/operator action history. fileciteturn19file5

Studio already has a read-only native shell foundation with bundled Cytoscape, graph load, node click, Inspector display, filters, trust-state rings, edge styles, and an edge legend. That means the current graph is not empty; it has an early substrate and UI-local display controls. fileciteturn19file6

The graph index is derived/rebuildable and the service layer owns writes. UI graph controls must not directly mutate vault state, trust state, canonical files, runtime state, providers, approvals, or Agent Bus tasks. fileciteturn19file2

The Studio architecture already defines explicit links, structural links, suggested semantic links, and runtime/action links, including `touched-by-agent`, `used-by-workflow`, `blocked-by-policy`, `pending-approval`, `produced-by-scheduled-run`, and `linked-to-audit-log`. fileciteturn19file3

The trust states ChaseOS must surface include `raw`, `quarantined`, `suggested`, `promoted`, `canonical`, `archived`, `disputed`, and `generated`. Generated vs canonical must stay visually distinct and promotions require explicit operator approval through Gate/service-layer paths. fileciteturn19file3

The current Feature-Fit register confirms the graph substrate already has a `GraphSnapshot`, an in-memory `GraphIndex`, deterministic extraction, and pure-Python topology algorithms, but it also says the index layer is derived from snapshots and does not yet provide persistent graph state. fileciteturn19file4

---

## 2. Competitor baseline and what ChaseOS should learn

### 2.1 Obsidian

Obsidian’s graph is valuable because it is fast enough, local, understandable, and centered around notes. Its official docs distinguish global graph from local graph: the global graph shows all notes, while local graph shows notes connected to the active note and supports a depth slider. citeturn986918search0

What ChaseOS should learn:

- Global graph is not enough.
- Local graph is mandatory.
- Depth control is mandatory.
- Filters are mandatory.
- The default view must be readable immediately.
- Graph should not force users to understand the whole vault at once.

What ChaseOS should beat:

- Obsidian mostly shows linked notes.
- ChaseOS should show notes + memory + source packages + approvals + runtimes + Agent Bus activity + provenance + generated/canonical separation + trust state + runtime touch edges.

### 2.2 Neo4j Bloom

Neo4j Bloom’s workspace is a “graph scene” containing the parts of the graph discovered through search or exploration, not necessarily the whole database at once. citeturn986918search23 Bloom scene interactions include expected exploration behaviours like zooming and dynamic node text sizing. citeturn986918search15

What ChaseOS should learn:

- Use graph scenes/tabs.
- Search should create exploration views.
- Expand neighbors instead of dumping all nodes.
- Right-click/inspector exploration is valuable.

What ChaseOS should beat:

- ChaseOS scenes should be local-first, runtime-aware, trust-aware, approval-aware, and integrated with Docs / Inspector and Agent Bus.

### 2.3 LangGraph / LangSmith Studio

LangGraph docs emphasize deep visibility into agent behavior through execution paths, state transitions, and runtime metrics. citeturn295857search0 LangSmith Studio is described as a specialized agent IDE for visualization, interaction, and debugging of agentic systems. citeturn295857search10 Another LangSmith Studio page says local agent visualization can show each step an agent takes, including prompts, tool calls, tool results, and final output. citeturn295857search14

What ChaseOS should learn:

- Users want to see what agents are doing.
- Traces and runtime state matter.
- Agent work should be visible, not hidden in logs.

What ChaseOS should beat:

- LangGraph/LangSmith show agent execution flow.
- ChaseOS should merge agent execution flow with a persistent knowledge/runtime/provenance graph.

### 2.4 Cytoscape.js

Cytoscape.js is an open-source JavaScript graph theory/network library for graph analysis and visualization. citeturn986918search1 It can also be used headlessly for graph operations on a server, according to a Cytoscape.js update paper. citeturn986918search13

Current implication:

- Since ChaseOS already bundles Cytoscape in the shell, the first move should be to audit and repair the current Cytoscape-based graph before replacing everything.
- Cytoscape can remain a good default renderer if layout, graph slicing, label thresholds, and caching are fixed.

### 2.5 Sigma.js / Graphology

Sigma.js is an open-source JavaScript library for visualizing graphs with thousands of nodes and edges using WebGL, built on Graphology. citeturn986918search2 Sigma’s site positions it as a WebGL-powered library for rendering large graphs in the browser. citeturn986918search14

Current implication:

- Sigma/Graphology may be a strong future candidate for a large-graph performance renderer.
- But WebGL should not become the only default path because current agent visual-QA/screenshot issues matter.
- If added, use Sigma as a renderer adapter behind the shared GraphStore, not as the graph truth layer.

### 2.6 ForceAtlas2 / layout warning

Graphology ForceAtlas2 docs state that each node must have starting `x` and `y` positions before running layout, and that layout cannot be computed if all nodes start at `x=0, y=0`. citeturn295857search2

Current implication:

- The ChaseOS 2D layout collapsing into a line may be caused by invalid or poor initial positions, bad layout seeding, bad force/layout settings, or rendering too much at once.
- Fixing layout seeding and layout caching is a backend/architecture task, not just UI polish.

---

## 3. Product thesis

### 3.1 What the graph should be

ChaseOS Graph is:

> **The visual control map for a local-first AI operating system.**

It shows:

- what exists,
- what is connected,
- what was generated,
- what is canonical,
- what is raw/quarantined,
- what needs review,
- what agents are doing,
- what runtimes touched,
- what approvals block,
- what provenance chain produced a node,
- what should be inspected next.

### 3.2 What the graph should not be

ChaseOS Graph is not:

- a decorative network animation,
- a full graph hairball,
- a generic note graph clone,
- a 3D demo view pretending to be daily UX,
- a second datastore,
- a bypass around Gate/service-layer writes,
- an automatic canonical promotion system.

### 3.3 Primary user questions

The graph should answer these quickly:

- What is my AI doing?
- What changed recently?
- What did Hermes touch?
- What did OpenClaw touch?
- What did Codex edit?
- What is blocked by approval?
- Why does this node exist?
- What created this node?
- What depends on this node?
- What is generated vs canonical?
- What is raw/quarantined/disputed?
- Which nodes need graph hygiene?
- What sources/provenance produced this output?
- Which runtime is working on this file now?
- What should I inspect next?

---

## 4. Current graph problems

### 4.1 Visual hairball

The current graph loads too much at once. A full graph of thousands of nodes/edges is technically impressive but functionally useless if the user cannot interpret it.

### 4.2 2D collapse

The 2D graph can collapse into a long thin line. This likely indicates a layout issue rather than a pure styling issue.

Potential causes:

- invalid initial positions,
- all nodes start at the same position,
- poor force layout tuning,
- bad edge weights,
- too many edges rendered at once,
- no clustering,
- no layout cache,
- no local/focus mode,
- camera/fit logic wrong,
- 2D/3D shared state conflict.

### 4.3 3D as default is wrong

3D is visually interesting but bad for default operator work:

- harder label reading,
- harder navigation,
- mouse controls are more complex,
- screenshot/visual QA issues,
- higher GPU pressure,
- not ideal for daily file inspection.

### 4.4 No live agent-native layer yet

The graph does not yet show “what is cooking.”

It should show:

- runtime live pulses,
- file/node touches,
- active tasks,
- daemon heartbeats,
- approval waits,
- generated outputs,
- task completion flashes,
- runtime trails.

### 4.5 Backend persistence/caching incomplete

Current graph substrate has snapshot/index/extractor/topology pieces, but persisted graph storage is still deferred. Without persistent graph storage and layout caching, large graph UX will stay fragile.

---

## 5. Target architecture overview

Use **one graph truth layer** and multiple renderers.

```text
Markdown / runtime profiles / sources / approvals / logs / Agent Bus / daemon events
        ↓
Graph Builder + Incremental Extractors
        ↓
GraphStore / GraphIndex / GraphQuery API
        ↓
Graph Scenes + Layout Cache + Runtime Overlay Store
        ↓
2D Renderer Adapter
3D Renderer Adapter
Static Screenshot Renderer
Docs / Inspector Adapter
Provenance Adapter
Hygiene Adapter
Chat / Task Adapter
```

Core principle:

> 2D and 3D should not have separate truth systems. They should read from the same GraphStore and scene query API.

---

## 6. Backend architecture changes required for speed

This is the part that matters most for performance.

### 6.1 Persisted GraphStore

Create or extend a local persistent graph store.

Current state appears to have `GraphSnapshot` and `GraphIndex`, but persistent graph storage is deferred. fileciteturn19file0

Proposed store:

```text
runtime/graph/
  artifact.py              # existing GraphSnapshot
  index.py                 # existing GraphIndex
  extractor.py             # existing extractors
  topology.py              # existing topology
  store.py                 # new persistent store
  query.py                 # new graph query API
  scenes.py                # new graph scene/tab model
  layout_cache.py          # new layout position cache
  overlay.py               # new live runtime overlay store
  events.py                # new event schema + ingest helpers
  runtime_links.py         # new runtime/action edge materialization
  hygiene.py               # graph issue query layer
  provenance.py            # provenance chain query layer
```

### 6.2 SQLite-first local storage

Use SQLite as the default local persistent graph store unless repo constraints already define another better local store.

Why SQLite:

- local-first,
- portable,
- stable,
- fast enough for metadata/query cache,
- no daemon required,
- works with desktop app packaging,
- supports indexes,
- supports FTS5 for file/node search,
- easy to rebuild from markdown if corrupted.

Suggested tables:

```sql
nodes(
  node_id TEXT PRIMARY KEY,
  stable_id TEXT,
  workspace_id TEXT,
  type TEXT,
  title TEXT,
  path TEXT,
  trust_state TEXT,
  status TEXT,
  source_file TEXT,
  frontmatter_json TEXT,
  metadata_json TEXT,
  content_hash TEXT,
  mtime REAL,
  created_at TEXT,
  updated_at TEXT
)

edges(
  edge_id TEXT PRIMARY KEY,
  source_id TEXT,
  target_id TEXT,
  relation TEXT,
  edge_family TEXT,
  confidence TEXT,
  trust_state TEXT,
  provenance_ref TEXT,
  metadata_json TEXT,
  created_at TEXT,
  updated_at TEXT
)

adjacency(
  node_id TEXT,
  neighbor_id TEXT,
  direction TEXT,
  relation TEXT,
  edge_id TEXT
)

layout_positions(
  workspace_id TEXT,
  scene_key TEXT,
  node_id TEXT,
  x REAL,
  y REAL,
  z REAL,
  pinned INTEGER,
  updated_at TEXT,
  PRIMARY KEY(workspace_id, scene_key, node_id)
)

graph_scenes(
  scene_id TEXT PRIMARY KEY,
  workspace_id TEXT,
  title TEXT,
  mode TEXT,
  renderer TEXT,
  query_json TEXT,
  filters_json TEXT,
  root_node_ids_json TEXT,
  depth INTEGER,
  camera_json TEXT,
  pinned_nodes_json TEXT,
  created_at TEXT,
  last_used_at TEXT
)

runtime_events(
  event_id TEXT PRIMARY KEY,
  ts TEXT,
  runtime_id TEXT,
  agent_id TEXT,
  event_type TEXT,
  node_id TEXT,
  file_path TEXT,
  task_id TEXT,
  run_id TEXT,
  status TEXT,
  source TEXT,
  metadata_json TEXT
)

node_touch_summary(
  node_id TEXT,
  runtime_id TEXT,
  touch_count INTEGER,
  last_touched_at TEXT,
  last_event_type TEXT,
  heat_score REAL,
  PRIMARY KEY(node_id, runtime_id)
)

node_search_fts(
  title,
  path,
  body_excerpt,
  tags,
  content='nodes',
  content_rowid='rowid'
)
```

### 6.3 Stable node identity

The Studio architecture says nodes need stable identity beyond filename/path because paths change and file moves would break edges/provenance/runtime-action links. fileciteturn19file14

Implement:

- stable node IDs,
- path aliases/history,
- content hash,
- frontmatter node ID if present,
- generated deterministic IDs if not present,
- migration path from path-based nodes.

Node ID priority:

```text
frontmatter chaseos_id / node_id
→ existing graph stable_id
→ deterministic hash(workspace_id + normalized_path + first_heading + type)
→ fallback path hash
```

### 6.4 Incremental extraction

Avoid rebuilding the entire graph on every load.

Use:

- file watcher,
- mtime/content hash,
- changed-file queue,
- incremental extractor,
- local store update,
- edge update for affected file only,
- stale edge cleanup for changed source file,
- graph version increment.

Flow:

```text
file changed
→ compute hash
→ if hash unchanged, skip
→ parse only changed file
→ update nodes/edges from that file
→ update adjacency
→ update search index
→ mark affected scenes/layout caches dirty
→ emit graph_updated event
```

### 6.5 Query API

The renderer should never receive the whole graph by default.

Add query endpoints/helpers:

```python
get_workspace_overview(max_nodes=300)
get_local_graph(root_node_id, depth=1, max_nodes=500, filters={})
get_focus_graph(query_or_node_id, depth=2, max_nodes=750)
get_runtime_trail(runtime_id, window="24h", max_nodes=500)
get_agent_touch_heatmap(window="7d", runtime_id=None)
get_provenance_chain(node_id, max_depth=10)
get_hygiene_graph(issue_type=None, max_nodes=500)
search_nodes(query, filters={}, limit=50)
get_node_inspector(node_id)
get_graph_scene(scene_id)
save_graph_scene(scene)
```

### 6.6 Layout cache

Layout should not recompute from zero every time.

Implement:

```text
scene_key = hash(mode + roots + filters + depth + renderer)
layout_positions[workspace_id, scene_key, node_id]
```

On scene load:

1. Load cached positions.
2. For existing nodes, reuse x/y.
3. For new nodes, seed around neighbors/community.
4. Run short layout stabilization only.
5. Stop simulation after settle.
6. Save updated positions.

### 6.7 Layout worker

Move expensive layout work away from the main UI thread.

Options:

- Python backend precomputes layout positions for scenes.
- Frontend Web Worker computes layout for visible scene.
- Use background layout cache generator.

Preferred:

```text
Backend precomputes stable layout for common scenes.
Frontend worker stabilizes only visible scene if needed.
```

### 6.8 Never render all details at once

For performance:

- send only visible scene slice,
- send minimal node payload for canvas,
- load inspector details on click,
- load provenance/backlinks on demand,
- load labels based on zoom,
- load runtime overlay separately.

Node payload to renderer:

```json
{
  "id": "node_id",
  "label": "short title",
  "type": "runtime",
  "trust": "canonical",
  "status": "active",
  "x": 123,
  "y": 456,
  "degree": 8,
  "runtimeOverlay": "working"
}
```

Full metadata only when inspector opens.

### 6.9 Edge thinning

Backend should support edge thinning before frontend render.

Default edge policy:

- explicit links visible,
- structural links visible but low opacity,
- suggested semantic links hidden unless enabled,
- runtime/action links shown as overlay/lens,
- high-degree edge bundles/clusters where useful,
- hide low-confidence edges by default.

### 6.10 Search index

Use SQLite FTS5 or an existing project search system.

Search should work over:

- node title,
- filename,
- path,
- headings,
- tags,
- frontmatter keys,
- runtime IDs,
- approval IDs,
- source package IDs.

### 6.11 Graph benchmarks

Create benchmark commands:

```bash
chaseos graph benchmark --workspace . --sizes 500,1000,3000,10000
chaseos graph scene benchmark --mode local --depth 2
chaseos graph renderer-benchmark --renderer cytoscape
chaseos graph renderer-benchmark --renderer sigma
```

Benchmark metrics:

- extraction time,
- store update time,
- query time,
- layout time,
- payload size,
- render time,
- FPS/interaction notes,
- memory use,
- screenshot success.

---

## 7. Renderer architecture

### 7.1 Renderer adapter model

Use renderer adapters:

```text
GraphRendererAdapter
  renderScene(scenePayload)
  updateOverlay(overlayEvents)
  focusNode(nodeId)
  fitView()
  exportScreenshot()
  destroy()
```

Adapters:

```text
Cytoscape2DAdapter
Sigma2DLargeGraphAdapter
StaticSVGAdapter
ThreeDSpatialAdapter
```

### 7.2 Default 2D renderer

2D is the daily operator mode.

Requirements:

- fast,
- labels readable,
- mouse navigation simple,
- screenshot friendly,
- local/focus default,
- context menu support,
- inspector integration,
- label thresholds.

### 7.3 3D renderer

3D is spatial/exploration/presentation mode.

Rules:

- not default,
- not full graph by default,
- cap nodes/edges,
- local/focus/runtimes only,
- labels mostly hover/selected,
- idle FPS reduction,
- pause when hidden,
- screenshot fallback if WebGL screenshot fails.

3D modes:

- Project constellation,
- Runtime swarm,
- Provenance chain flythrough,
- Agent activity spatial view.

### 7.4 Static screenshot renderer

Needed for QA and agent visual review.

Use cached layout positions and generate:

- SVG,
- Canvas snapshot,
- or static DOM overlay.

It does not need full interactivity.

---

## 8. Graph scenes / tabs

### 8.1 Why scenes/tabs are needed

A single graph canvas forces the user to lose context. Graph scenes let the user open multiple focused maps:

```text
Workspace Overview
Hermes Runtime Trail
README Local Graph
Pending Approvals
Graph Hygiene Issues
```

### 8.2 Scene data model

```json
{
  "sceneId": "scene_...",
  "title": "Hermes Runtime Trail",
  "mode": "runtime_trail",
  "renderer": "2d",
  "query": {
    "runtimeId": "hermes",
    "window": "24h"
  },
  "filters": {
    "trustStates": ["promoted", "canonical", "generated"],
    "edgeFamilies": ["runtime-action", "explicit"]
  },
  "rootNodeIds": ["runtime:hermes"],
  "depth": 2,
  "camera": {"x": 0, "y": 0, "zoom": 1.2},
  "pinnedNodes": [],
  "createdAt": "...",
  "lastUsedAt": "..."
}
```

### 8.3 Ways to create scenes

From search:

```text
Search Hermes → Open as graph tab
```

From node context:

```text
Right-click README → Open local graph in new tab
```

From command:

```text
Graph command: "show files touched by Codex this week"
→ new scene tab
```

From runtime:

```text
Click Hermes runtime node → Open Runtime Trail
```

From approval:

```text
Open pending approval graph
```

### 8.4 Built-in default scenes

Keep defaults minimal. Avoid fake one-size-fits-all graphs.

Suggested defaults:

1. Current Workspace
2. Recent Activity
3. Pending Attention

Everything else should be generated by search, context, runtime, or user command.

---

## 9. Live Agent / Runtime Overlay

### 9.1 Concept

The graph should show what agents are doing right now.

This is the “what is cooking?” layer.

Examples:

```text
Hermes is reading README.md
Codex is editing Graph-Substrate-Architecture.md
OpenClaw daemon is active
Approval is blocking a generated artifact
AOR workflow produced a new node
```

### 9.2 Event sources

Initial backend sources:

- Agent Bus,
- Agent Daemon / runtime daemon,
- OSRIL event bus,
- AOR workflow events,
- runtime heartbeat/status,
- file watcher,
- approval center,
- logs/audit records.

### 9.3 Runtime event schema

```json
{
  "event_id": "evt_20260601_001",
  "ts": "2026-06-01T12:00:00Z",
  "runtime_id": "hermes",
  "agent_id": "hermes",
  "event_type": "node_touch_started",
  "node_id": "doc:README.md",
  "file_path": "README.md",
  "task_id": "bus:task_123",
  "run_id": "run_456",
  "status": "working",
  "confidence": "observed",
  "source": "agent_bus",
  "metadata": {
    "operation": "review",
    "human_label": "Hermes is reviewing README.md"
  }
}
```

### 9.4 Event types

```text
runtime_heartbeat
runtime_degraded
task_claimed
task_started
task_completed
task_failed
node_read_started
node_read_finished
node_edit_started
node_edit_finished
node_touch_started
node_touch_finished
approval_requested
approval_blocked
approval_resolved
artifact_generated
log_written
run_started
run_completed
run_failed
daemon_started
daemon_stopped
daemon_degraded
```

### 9.5 Runtime colors

Use consistent runtime colors:

```text
Hermes = green/cyan/gold
OpenClaw = amber/cyan
Codex = blue/violet
Claude/Archon = amber/violet/cyan
User/manual = white/teal
System/Gate = gray/gold
```

### 9.6 Live overlay visual states

```text
reading       = faint scan pulse
editing       = stronger animated ring
working       = runtime-colored pulse
waiting       = dotted ring
approval      = amber ring
blocked       = red/amber lock
completed     = short green/cyan flash
failed        = dim/red warning marker
daemon alive  = small heartbeat dot
```

### 9.7 Overlay persistence

Separate:

```text
Ephemeral overlay:
- current status
- active pulses
- live task state
- TTL-based

Historical event log:
- runtime_events table/jsonl
- node_touch_summary
- timeline/replay
```

Do not make live pulses canonical truth.

---

## 10. Agent Touch Heatmap

### 10.1 Purpose

Show which parts of the system have been touched by agents.

Questions answered:

- What has Hermes worked on?
- What has Codex edited?
- What has OpenClaw touched?
- What has not been touched recently?
- Which nodes are being worked on by multiple agents?

### 10.2 Visual

```text
Hermes-touched nodes = green/cyan glow
Codex-touched nodes = blue/violet glow
OpenClaw-touched nodes = amber/cyan ring
Claude/Archon-touched nodes = amber/violet glow
Multiple runtimes = stacked/split ring
Untouched/stale = dim
```

### 10.3 Data

Use `node_touch_summary`:

```text
node_id
runtime_id
touch_count
last_touched_at
last_event_type
heat_score
```

### 10.4 UI

Heatmap controls:

- runtime filter,
- time window: 1h / 24h / 7d / 30d,
- event type filter,
- show untouched,
- show multi-runtime nodes.

---

## 11. Runtime Trails

### 11.1 Purpose

Runtime Trails answer:

> What has this runtime done, what is it doing, and what did it touch?

### 11.2 Hermes trail example

```text
Hermes
→ Hermes Chat
→ Agent Bus Task
→ README.md
→ Output Log
→ Approval Packet
→ Audit Event
```

### 11.3 OpenClaw trail example

```text
OpenClaw
→ Daemon Heartbeat
→ Scheduled Task
→ Local Operation
→ File/Node Touch
→ Blocked/Approved Action
→ Audit Log
```

### 11.4 Codex trail example

```text
Codex
→ branch/session
→ files edited
→ tests run
→ diff/output
→ handover markdown
```

### 11.5 Runtime Trail mode

Query:

```python
get_runtime_trail(runtime_id="hermes", window="24h", max_nodes=500)
```

Visual:

- runtime node centered/left,
- chronological or swimlane layout,
- task nodes,
- file nodes,
- output/log nodes,
- approval nodes,
- status edges.

---

## 12. Approval overlay

### 12.1 Purpose

Show what is blocked, pending, approved, or consumed.

Visual states:

```text
pending approval = amber ring
approved = green/cyan check
blocked = red/amber lock
consumed = gray completed badge
needs review = amber pulse
```

### 12.2 Node/edge metadata

```text
approval_id
requested_action
target_node
risk_level
status
decision_ref
resume_state
audit_log_path
```

### 12.3 Actions

- View approval packet,
- Open Approval Center,
- View affected nodes,
- View provenance,
- Resume-ready if governed path exists.

No hidden approval consumption.

---

## 13. Trust overlay

Trust state must be always visible but visually weighted by urgency.

States:

```text
raw
quarantined
suggested
promoted
canonical
archived
disputed
generated
```

Visual style:

```text
canonical = quiet small marker
promoted = calm marker
generated = violet/generative badge
quarantined = amber border
disputed = red/amber conflict marker
raw = dashed low-confidence ring
suggested = dotted edge
archived = dim/gray
```

Trust overlay should be filterable and can combine with runtime overlay.

---

## 14. Provenance chain view

### 14.1 Purpose

Show how something came to exist.

Example:

```text
capture
→ quarantine
→ source package
→ synthesis
→ generated artifact
→ approval
→ canonical node
```

### 14.2 Layout

Use left-to-right DAG, not force graph.

This is important: provenance is a chain, not a hairball.

### 14.3 Node click

Click a provenance node:

- view source,
- view sidecar,
- view gate decision,
- view artifact,
- view approval,
- open Docs / Inspector.

---

## 15. Hygiene graph

### 15.1 Purpose

Make graph maintenance actionable.

Hygiene issues:

- orphan nodes,
- duplicate candidates,
- unresolved links,
- stale nodes,
- disputed nodes,
- generated but unreviewed nodes,
- raw/quarantined nodes,
- broken provenance links,
- files missing stable IDs.

### 15.2 Layout

Group by issue type.

Avoid full graph.

### 15.3 Actions

- open node,
- open docs,
- view provenance,
- create review task,
- mark disputed,
- archive,
- propose merge,
- propose link.

All state changes through service layer.

---

## 16. Graph command bar

### 16.1 Purpose

Natural-language-like graph query → graph scene.

Examples:

```text
show Hermes activity this week
show nodes touched by Codex today
show pending approvals touching ChaseOS
show quarantined nodes in 03_INPUTS
show local graph around README depth 2
show docs that depend on Runtime Navigation Map
show generated nodes not promoted
show stale docs modified before May
show files touched by OpenClaw daemon
```

### 16.2 Output

Command creates:

- a new graph tab/scene,
- filters,
- root nodes,
- selected lens,
- explanation of query,
- counts.

### 16.3 Safety

The command bar should not execute mutations directly.

It can:

- create graph scene,
- attach context to Chat,
- create proposal/task if existing governed path exists.

---

## 17. Node context mini-chat

### 17.1 Concept

Right-click node → Ask about this node.

Small input:

```text
Ask ChaseOS about README.md...
```

Example questions:

```text
why does this exist?
what depends on this?
what touched this recently?
show related runtime activity
summarize this node
create a cleanup task
attach this to chat
show provenance
```

### 17.2 Behavior

- quick question → answer in inspector,
- bigger conversation → open Chat with node context,
- action → proposal/approval route if required.

### 17.3 Context packet

```json
{
  "node_id": "...",
  "title": "...",
  "path": "...",
  "type": "...",
  "trust_state": "...",
  "provenance_summary": "...",
  "neighbors": ["..."],
  "runtime_touches": ["..."]
}
```

---

## 18. Agent simulation overlay

### 18.1 Purpose

Before a run, show likely graph impact.

Example:

```text
Proposed run: Codex update README
Likely affected:
- README.md
- PROJECT_FOUNDATION.md
- build log
- approval packet
```

After run:

```text
Actual graph diff:
+ 1 generated artifact
+ 1 build log
+ 2 touched-by-agent edges
+ 1 approval edge
~ 1 doc updated
```

### 18.2 Phasing

This is not MVP. Design architecture now so it is possible later.

Needs:

- proposed action digest,
- predicted target nodes,
- actual runtime events,
- graph diff builder,
- approval link.

---

## 19. Timeline / Replay

### 19.1 Purpose

Replay how the workspace changed over time.

Useful for:

- audit,
- content,
- debugging,
- agent accountability,
- project history.

### 19.2 Data

Use:

- runtime_events,
- graph versions,
- approval decisions,
- file changes,
- generated artifacts,
- log writes.

### 19.3 UI

Timeline slider:

```text
last hour
today
this week
custom range
```

Visual:

- nodes appear/disappear,
- runtime touches flash,
- approvals resolve,
- generated artifacts promote or archive.

---

## 20. 2D graph design

### 20.1 Default 2D view

The default should not be all nodes.

Default priority:

1. last active graph scene,
2. active workspace focus,
3. recent/important graph,
4. local graph around current/selected doc,
5. only then full graph.

### 20.2 Layout modes

Use layout based on graph mode:

```text
Workspace overview = clustered radial/concentric
Local graph = force-directed
Runtime trail = swimlane/timeline
Provenance graph = left-to-right DAG
Approval graph = bipartite target ↔ approval
Hygiene graph = grouped issue clusters
```

### 20.3 Avoid line collapse

Actions:

- seed x/y positions,
- avoid all-zero initialization,
- cluster seed by node type/domain,
- reuse layout cache,
- run short force stabilization,
- cap edge density,
- use local/focus graph by default,
- detect bad bounding box ratio and auto-reset layout.

Detection:

```text
if graph_bbox_width / graph_bbox_height > 12
or graph_bbox_height / graph_bbox_width > 12
→ layout collapse suspected
→ reseed positions
→ rerun layout
```

### 20.4 Label system

Label priority:

1. selected node,
2. hovered node,
3. search result,
4. pinned node,
5. canonical/runtime/profile node,
6. local graph neighbors,
7. all others only at high zoom.

Rules:

- hover label always visible,
- selected label persistent,
- zoomed out = cluster labels only,
- medium zoom = important labels,
- zoomed in = node labels,
- full title in tooltip/inspector.

---

## 21. 3D graph design

### 21.1 Role

3D is spatial exploration/presentation, not default.

### 21.2 Use cases

- project constellation,
- runtime swarm,
- provenance chain flythrough,
- agent activity demo,
- high-level system exploration.

### 21.3 Limits

- cap nodes/edges,
- no full vault by default,
- no all-label mode,
- hover/selected labels only,
- pause when hidden,
- idle FPS reduction,
- screenshot fallback.

### 21.4 3D scene types

```text
3D local graph
3D runtime trail
3D project constellation
3D provenance chain
3D agent swarm
```

---

## 22. Licensing and open-source strategy

Important principle:

> Do not adopt a dependency that blocks ChaseOS from being open-source, redistributed, packaged, or commercially controlled.

Before adopting any graph library, audit:

- license type,
- commercial use,
- redistribution,
- desktop packaging compatibility,
- attribution requirements,
- dependency chain,
- native build requirements,
- security posture,
- maintenance activity,
- offline/local operation.

Initial candidates:

- Cytoscape.js: already present; audit current bundled version/license.
- Sigma.js + Graphology: evaluate for large graph rendering; audit license.
- D3 force/canvas: possible custom route for small/local graphs.
- Three/3D force graph: only if 3D remains bounded and optional; audit license.
- Neo4j: useful as concept/reference; not a default embedded dependency.
- Rust graph/layout module: future optional performance accelerator only if Python/JS path fails benchmarks.

Do not jump to graph databases unless the local SQLite/GraphStore path fails.

---

## 23. Hardware future / why the graph must scale

Local AI hardware is improving. NVIDIA positions DGX Spark as a desktop AI system with 128GB unified memory that can fine-tune models up to 70B parameters. citeturn295857search1 A PNY datasheet claims DGX Spark can support models up to 200B parameters with 128GB unified memory and FP4. citeturn295857search11

The implication for ChaseOS:

- more local models,
- more local runtimes,
- more parallel agents,
- more generated artifacts,
- more memory candidates,
- more approval packets,
- more provenance chains,
- more runtime events,
- more daily graph changes.

Therefore the graph must be incremental, cached, query-driven, and overlay-driven. It cannot rebuild and render the universe every time.

---

## 24. Development phases

### Phase 0 — Graph audit

Goal: find repo truth.

Audit:

- current renderer,
- Cytoscape integration,
- 2D layout code,
- 3D renderer code,
- graph data source,
- node schema,
- edge schema,
- filters,
- label code,
- layout/camera code,
- current performance,
- screenshot/QA issue,
- Agent Bus event availability,
- daemon heartbeat availability,
- file watcher state,
- current graph tests.

Output:

- Graph Audit Report,
- renderer truth,
- backend truth,
- bottlenecks,
- exact repair path.

### Phase 1 — GraphStore / persistent cache

Goal: make graph fast and stable.

Implement:

- SQLite/local graph store,
- indexes,
- layout cache,
- scene table,
- runtime event table,
- search index,
- migration/rebuild command.

### Phase 2 — Graph scenes/tabs

Goal: stop graph hairball.

Implement:

- graph scene model,
- tabs,
- local/focus graph queries,
- scene persistence,
- query-based scene creation.

### Phase 3 — 2D default repair

Goal: make daily graph usable.

Implement:

- 2D default,
- fit/reset,
- local/focus,
- label thresholds,
- edge thinning,
- node inspector,
- context menu,
- docs integration.

### Phase 4 — Runtime overlay

Goal: make graph agent-native.

Implement:

- runtime event ingest,
- live pulses,
- runtime colors,
- node touch heatmap,
- runtime trails,
- Agent Bus/daemon bridge.

### Phase 5 — Command/control

Goal: make graph a control plane.

Implement:

- graph command bar,
- right-click mini-chat,
- attach node to chat,
- create task proposal,
- why-does-this-exist,
- what-depends-on-this.

### Phase 6 — 3D spatial mode

Goal: keep 3D but make it bounded.

Implement:

- 3D local graph,
- 3D runtime trail,
- 3D project constellation,
- caps/performance controls,
- screenshot fallback.

### Phase 7 — Replay/simulation

Goal: future trust layer.

Implement:

- graph timeline,
- graph diff,
- agent simulation overlay,
- runtime action prediction vs actual.

---

## 25. Immediate implementation prompt: Graph Audit + Architecture Pass

Use this before changing graph code broadly.

```text
You are working on ChaseOS Studio Graph.

Do not start by making visual tweaks.
Do not rewrite the graph renderer yet.
Do not make 3D the default.
Do not expand graph write authority.

Task:
Run a Graph Architecture + Renderer + Runtime Overlay audit.

Goal:
Discover repo truth and produce the exact implementation plan for the upcoming graph refactor.

Audit these areas:
1. Current graph renderer/library.
2. Current 2D implementation.
3. Current 3D implementation.
4. Whether WebGL is used.
5. Whether Cytoscape is still the active 2D renderer.
6. Current graph data source.
7. Current node schema.
8. Current edge schema.
9. Current trust/provenance data available to graph.
10. Current layout algorithm and settings.
11. Why 2D collapses into a line.
12. Why default zoom/framing is wrong.
13. Whether layout positions are cached.
14. Whether graph scenes/tabs exist.
15. Whether local/focus graph API exists.
16. Current label rendering logic.
17. Current filter/preset logic.
18. Current node inspector integration.
19. Current Docs / Inspector integration.
20. Current Provenance/Hygiene integration.
21. Current Agent Bus event sources.
22. Current runtime daemon/heartbeat event sources.
23. Current file watcher/file touch event sources.
24. Current AOR/OSRIL events available.
25. Current graph performance bottlenecks.
26. Current visual QA/screenshot blockers.
27. Current tests/static checks for graph.

Then propose:
1. Whether to repair current Cytoscape path first.
2. Whether to add GraphStore persistence before frontend changes.
3. Exact backend modules to add/update.
4. Exact frontend components to add/update.
5. How to implement graph scenes/tabs.
6. How to implement local/focus graph.
7. How to implement Agent Bus/daemon runtime overlay.
8. How to implement node touch heatmap.
9. How to implement runtime trails.
10. How to implement 2D default and keep 3D optional.
11. How to benchmark graph speed.
12. What must remain read-only/gated.

Final output:
Create `ChaseOS_Studio_Graph_Architecture_Runtime_Overlay_Audit.md`.

Include:
- files inspected
- current renderer truth
- backend graph truth
- event source truth
- bottlenecks
- proposed architecture
- pass-by-pass implementation plan
- risks
- acceptance criteria
- exact next implementation prompt

Do not implement broad code changes in this pass unless a tiny diagnostic script is needed.
```

---

## 26. Acceptance criteria for the eventual graph refactor

The full graph refactor is successful when:

1. 2D is the default daily operator graph.
2. 3D is optional/spatial/bounded.
3. Graph first load is readable.
4. All-graph is not forced by default.
5. Local/focus graph works.
6. Graph tabs/scenes work.
7. Layout positions are cached.
8. 2D no longer collapses into a line.
9. Labels work by zoom/hover/selection.
10. Node context menu works.
11. Node opens Docs / Inspector.
12. Provenance chain works.
13. Hygiene view works.
14. Runtime nodes exist.
15. Agent Bus events can pulse graph nodes.
16. Agent daemon heartbeats can show live state.
17. Runtime trails work.
18. Agent touch heatmap works.
19. Approval overlay works.
20. Trust overlay works.
21. Graph command bar creates scenes.
22. Node mini-chat attaches context.
23. No graph action bypasses service layer/Gate.
24. Graph performs on normal laptops.
25. Screenshot/visual QA works for 2D.
26. Benchmarks exist.
27. Renderer/library licenses are audited.
28. Backend graph store is rebuildable from source truth.
29. Live overlay is separate from canonical graph truth.
30. The user can understand “what is cooking” in ChaseOS by looking at the graph.

---

## 27. Short north star

> Obsidian shows linked notes.  
> ChaseOS Graph should show linked notes, runtime activity, agent work, approvals, trust, provenance, generated/canonical distinction, and what to do next.

That is the product edge.
