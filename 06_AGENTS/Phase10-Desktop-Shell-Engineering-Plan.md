---
title: Phase 10 Desktop Shell Engineering Plan
type: engineering-plan
status: active — framework selected; implementation ready to begin
version: 1.1
created: 2026-05-04
updated: 2026-05-04
phase: Phase 10 — ChaseOS Studio
knowledge_class: system-operational
owner: Chaser Agent (primary engineering runtime)
related_docs:
  - 06_AGENTS/ChaseOS-Studio-Architecture.md
  - 06_AGENTS/Phase10A0-UI-Runtime-Handover.md
  - 06_AGENTS/Markdown-to-Standalone-Bridge.md
  - 06_AGENTS/Operator-Overlay-UX-Spec.md
  - runtime/studio/ (all modules — backend complete)
---

# Phase 10 Desktop Shell Engineering Plan

> This document is the canonical engineering plan for the ChaseOS Studio desktop application.
> It defines the framework decision, architecture, subphase breakdown, and runtime handover
> instructions for all runtimes participating in Phase 10 engineering.
>
> Backend is complete. This document is the starting gun for the shell.

---

## 1. Context — What Already Exists

Before any desktop shell work, the following is fully operational:

**Native shell progress** (`runtime/studio/shell/`):
- Pass 10A is built: PyWebView shell entry point, `StudioAPI` bridge, local
  frontend, bundled Cytoscape, graph load, node click, and Inspector display.
- First Pass 10B slice is built: UI-local node-type/trust/relation filters,
  richer node type shape mapping, trust-state ring emphasis, edge family
  styles, and edge legend.
- Current 10B controls are read-only frontend state only. They do not persist
  graph filters, write node IDs, edit graph nodes, call providers/connectors,
  execute workflows, or mutate canonical state.

**Backend services** (`runtime/studio/` — 37 Python modules, 51 CLI commands):
- `service.py` — validated write governance (Gate enforcement, approval queue, audit)
- `graph_view.py` / `graph_view_contract.py` / `graph_index_contract.py` — complete graph model
- `graph_view_static_renderer.py` — static SVG/HTML graph render (proof the data model works)
- `node_inspector_contract.py` / `node_inspector_shell_panel.py` — node detail model
- `markdown_scan_contract.py` / `open_folder_readiness.py` — folder scan + workspace detection
- `dashboard.py` — 7-panel system status aggregation
- `runtime_cockpit.py` — Runtime Cockpit desktop contract (aggregates bus, startup, agent state)
- `desktop_shell_foundation.py` — machine-readable map of what's built and what's next
- `desktop_shell_app.py` — full shell-shaped localhost HTML mock (running proof of layout)
- `Live-Visual-Shell-Contract.md` — Phase 10 visual-state contract for mapping AOR/OSRIL/runtime/lifecycle/approval posture into read-only shell animation/status; future implementation should add `runtime/studio/live_visual_shell.py` plus a desktop shell panel without gaining execution or approval authority
- All inspector modules (provenance, memory, SIC, AOR, schedule, pulse, siteops)
- All localhost apps (dashboard, runtime cockpit, approval center, pulse deck, acquisition cockpit)
- `app_launcher.py` — panel registry
- `approval_queue_panel.py` / `approval_center_app.py` — approval queue model
- `pulse_product_shell_panel.py` — Pulse product shell panel contract
- `runtime_brain_dashboard.py` — memory/runtime readiness packet

**What this means for the desktop shell:**
- Every backend call is already written and tested
- The data models for every panel are stable contracts
- The layout is proven (browse `chaseos studio desktop-shell-app` to see it)
- All governance rules are encoded in `service.py` — the shell calls the service, never the vault directly
- The shell's job is to wrap what exists in a native window, not to invent new backend logic

---

## 2. Framework Decision

Three serious candidates exist. This section defines each, evaluates them against ChaseOS
requirements, and records the decision.

---

### 2A — Tauri

**What it is:** A Rust-based application shell that embeds the OS-native webview (WebView2 on
Windows 11, WebKit on macOS, GTK WebKit on Linux). The backend logic is written in Rust; the
frontend is HTML/CSS/JS that runs inside the webview. Rust ↔ JS communication happens via a
typed IPC command system (Tauri commands).

**Architecture for ChaseOS:**
```
[HTML/CSS/JS frontend] → tauri.invoke("cmd") → [Rust handler] → Python subprocess → [runtime/studio/*.py]
```

**Pros:**
- Very small binary (~5–15 MB installer, no bundled browser engine)
- Native performance and memory footprint — Rust is fast and memory-safe
- WebView2 on Windows 11 is pre-installed (part of the OS since Win11) — reliable rendering
- Strong security model — granular allowlist for what JS can invoke
- Active development, well-maintained, growing ecosystem
- Modern: VS Code team is watching it; several serious apps shipping with it

**Cons:**
- **Three-language stack**: Rust + TypeScript/JS + Python. Rust is the hardest of the three.
- Python is never called directly — it must go through subprocess IPC (Rust spawns Python process,
  passes args, reads stdout). This adds latency and serialization for every backend call.
- Build pipeline complexity: Rust toolchain + Node.js + Python venv all need to be configured
- Rust learning curve is real — backend logic for IPC, file dialogs, menus, etc. must be written
  in Rust, not Python
- Debugging cross-language: JS error → Rust IPC → Python subprocess traceback is hard to follow

**Verdict for ChaseOS:** Correct framework for a broadly distributed, multi-user product.
Incorrect framework for a system where the entire backend is already Python. The Rust layer adds
a language and IPC overhead that provides no benefit here — there is nothing Rust needs to do
that Python cannot do directly.

---

### 2B — Electron

**What it is:** A Node.js-based application shell that bundles a full Chromium browser engine.
The main process runs in Node.js; the renderer process is HTML/CSS/JS. IPC happens via
Electron's `ipcMain` / `ipcRenderer` system. Python is called via Node's `child_process`.

**Architecture for ChaseOS:**
```
[HTML/CSS/JS renderer] → ipcRenderer.invoke → [Node.js main process] → child_process.spawn → [Python]
```

**Pros:**
- Proven at scale — Obsidian, VS Code, Slack, Discord all use it. The pattern is validated.
- Consistent rendering: bundles Chromium, so every platform renders identically
- Huge ecosystem — npm packages for everything
- Node.js as the IPC bridge is less foreign than Rust for most developers
- Obsidian specifically is built on Electron — ChaseOS interoperating with or replacing Obsidian
  makes Electron a natural bridge choice

**Cons:**
- **Large bundle**: ~150–200 MB installer because Chromium is bundled
- **High memory**: Chromium process + Node.js process + Python process = 3 runtimes in memory
- Python is still never called directly — same subprocess IPC story as Tauri, just through Node.js
  instead of Rust
- Node.js as an intermediary adds a second backend language to manage
- Startup time is noticeably slower than Tauri due to Chromium startup

**Verdict for ChaseOS:** The Obsidian overlap makes this attractive for the compatibility mode
(opening Obsidian vaults), and the ecosystem is the most mature. But the same core problem as
Tauri applies: Python is still a subprocess. The bundle size and memory overhead are real costs
for a local-first personal OS tool.

---

### 2C — PyWebView (**Recommended**)

**What it is:** A Python library that wraps the OS-native webview (WebView2 on Windows, WebKit
on macOS) and exposes Python objects directly to JavaScript. There is no Rust, no Node.js, and
no subprocess. The Python runtime is the application — it creates a webview window, loads
HTML/JS, and exposes Python functions that JS calls directly.

**Architecture for ChaseOS:**
```
[HTML/CSS/JS frontend] → window.pywebview.api.get_dashboard() → [Python: runtime/studio/dashboard.py]
```

**Pros:**
- **Direct Python API calls — no subprocess, no Rust/Node orchestration.** `window.pywebview.api.method()`
  calls a Python method via the webview's JS bridge. `runtime/studio/*.py` is imported once at
  startup and every panel call is a direct Python function call. JS↔Python marshaling of basic
  types (strings, ints, dicts, lists, booleans, None) still occurs via promises — methods must
  return JSON-serializable values only. This is lightweight compared to subprocess + stdout
  parsing, but it is not zero-cost serialization. Design the API accordingly: return clean
  JSON-shaped envelopes, not arbitrary Python objects.
- **Zero backend refactoring** — all 37 studio modules work unchanged. The API class is a thin
  wrapper that calls existing functions.
- **Single language stack** — Python + HTML/CSS/JS. No Rust, no Node.js, no build toolchain
  beyond the existing Python venv.
- WebView2 on Windows 11 is pre-installed and Edge-based — reliable, fast, modern CSS/JS support
- Bundle via PyInstaller: `pyinstaller --onefile` produces a self-contained `.exe`. No separate
  Python install required for distribution.
- Same OS webview as Tauri on each platform — essentially the same rendering story, without Rust
- Startup time is fast: Python process starts, window opens, no Chromium cold start
- Debugging is straightforward: one language, one traceback, one process

**Cons:**
- Smaller community than Electron — less Stack Overflow coverage for edge cases
- No bundled Chromium — rendering is WebView2 (Windows), WebKit (macOS), GTK WebKit (Linux).
  Cross-platform consistency is slightly lower than Electron, though on the primary Windows 11
  target it is excellent.
- PyInstaller packaging requires care (hidden imports, data files, venv bundling) — more manual
  than `electron-builder`
- No built-in auto-update mechanism (unlike Electron Forge / Tauri Updater) — manual update
  distribution for now

**Verdict for ChaseOS:** The correct choice. The entire backend is Python. PyWebView means the
desktop shell is a Python program that opens a window — the same language, the same imports, the
same stack. Every panel call that currently goes through `http.server` → `requests` → JSON parse
becomes a direct Python method call with JS↔Python marshaling only for return values. The
existing localhost HTML mocks are the templates for the real UI. The effort to go from "localhost
HTML app" to "native desktop window" is one layer of wrapping, not a rewrite.

**Precise claim:** PyWebView avoids a separate Python backend subprocess and avoids Rust/Node-to-Python
orchestration. It does not eliminate JS↔Python type marshaling entirely — returned values are
promises and only basic Python types cross the boundary. This is why all `StudioAPI` methods must
return JSON-serializable dicts, not arbitrary Python objects.

---

### 2D — Framework Decision

**Selected: PyWebView**

**Rationale (recorded for Decision Ledger):**

1. The backend is entirely Python. PyWebView makes the shell a Python program. Tauri and Electron
   make Python a subprocess of a different runtime. There is no architectural reason to add a
   second runtime language when the backend already runs correctly in Python.

2. The HTML/CSS/JS frontend is already written. The localhost mock apps are the direct templates.
   The migration path is: replace `http.server` with `pywebview.create_window()`, replace
   `requests.get("/api/...")` with `window.pywebview.api.method()`. No framework rewrite.

3. Windows 11 primary platform. WebView2 is pre-installed. Rendering is Edge-based (Chromium
   core) — not an unknown webview.

4. ChaseOS is a local-first personal operating system. The user base for V1 is one person.
   Tauri's distributed-product advantages (small bundle, auto-updater, app store distribution)
   do not apply to the first version. They apply when ChaseOS Studio becomes a public product.
   At that point, a Tauri migration is a frontend-only concern — the Python backend and API
   surface do not change.

5. Complexity budget. Chase is building this system solo across multiple domains. Adding Rust
   or Node.js to a Python-native codebase is an unnecessary cognitive cost.

**Tauri rule (recorded for all runtimes):**
> Do not use Tauri until ChaseOS Studio is ready to become a broadly distributed product, or
> until the frontend/backend API is mature enough that Python can become a stable sidecar.
> Do not re-litigate this decision during Phase 10. PyWebView is locked for V1.

**Migration path when ChaseOS Studio goes public:**
If Studio needs to be broadly distributed as a standalone app without Python dependency, the
correct migration is to Tauri at that time. The frontend (HTML/CSS/JS) migrates unchanged. The
Python backend becomes a sidecar process (Tauri's explicit sidecar model) or gets replaced by a
Rust reimplementation of the same API surface. The service layer contract (StudioService,
ActionSpec, etc.) is the stable interface — the shell only depends on that contract, not on
Python internals. Tauri's sidecar model treats external binaries as separate bundled executables
with shell permissions — this is fine for a polished public app, unnecessary friction for V1.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ChaseOS Studio Desktop Shell                      │
│                     (PyWebView — Python process + WebView2)              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    HTML/CSS/JS Frontend Layer                       │  │
│  │                                                                     │  │
│  │  ┌──────────┐  ┌─────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │  Graph   │  │   Node      │  │  Runtime   │  │   Approval   │  │  │
│  │  │  View    │  │  Inspector  │  │  Cockpit   │  │   Center     │  │  │
│  │  │ Panel    │  │   Panel     │  │   Panel    │  │   Panel      │  │  │
│  │  └────┬─────┘  └──────┬──────┘  └─────┬──────┘  └──────┬───────┘  │  │
│  │       │               │               │                │            │  │
│  │  window.pywebview.api.[method]()  ← JS → Python bridge              │  │
│  └───────┼───────────────┼───────────────┼────────────────┼────────────┘  │
│          │               │               │                │               │
│  ┌───────▼───────────────▼───────────────▼────────────────▼────────────┐  │
│  │                   Python API Bridge (StudioAPI class)                │  │
│  │   Thin wrapper — validates caller, routes to runtime/studio/*.py     │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
│                                   │                                         │
│  ┌────────────────────────────────▼─────────────────────────────────────┐  │
│  │                    runtime/studio/ Python Backend                     │  │
│  │                                                                       │  │
│  │  service.py  graph_view_contract.py  node_inspector_contract.py       │  │
│  │  dashboard.py  runtime_cockpit.py  provenance.py  siteops_inspector  │  │
│  │  pulse_inspector  schedule_inspector  memory_inspector  sic_browser   │  │
│  │  aor_pipeline_monitor  approval_queue_panel  app_launcher  ...        │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
│                                   │                                         │
│  ┌────────────────────────────────▼─────────────────────────────────────┐  │
│  │              ChaseOS Vault (markdown filesystem source of truth)      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key architectural rules

1. **The shell never reads the vault directly.** All vault reads go through `runtime/studio/*.py`.
2. **The shell never writes the vault directly.** All writes go through `runtime/studio/service.py`
   (`StudioService`). No exceptions.
3. **The JS frontend never calls Python arbitrarily.** All calls go through the `StudioAPI` bridge
   class, which validates the call and routes to the correct backend module.
4. **The Python backend is unchanged.** All existing `runtime/studio/*.py` modules are imported
   directly. No subprocess, no HTTP, no JSON serialization between shell and backend.
5. **The graph index is derived, not authoritative.** The vault is the truth. The graph is rebuilt
   from the vault on open and on file-change events.

---

## 4. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Shell runtime | Python 3.13 + PyWebView **6.2.1** (pinned) | Direct backend integration |
| Window/webview | PyWebView (`pywebview.create_window`) | Opens native window with WebView2 |
| Frontend framework | Vanilla HTML/CSS + small JS | No React/Vue needed — panels are data-driven renders; keep complexity low |
| Graph rendering | **Cytoscape.js** (bundled locally) | Purpose-built for node/edge graphs; Canvas-based by default (WebGL renderer is a 2025 preview — use only when graph size requires it); pan/zoom/click; rich styling API; no build system needed |
| State management | Vanilla JS module pattern | No Redux/Zustand — data flows from Python API calls; no complex client-side state |
| Packaging | PyInstaller | `--onefile` `.exe` for Windows; self-contained; no Python install needed on target machine |
| Hot reload (dev) | `pywebview` debug mode | Live reload HTML/CSS/JS during development without restarting Python |
| Filesystem watching | `watchdog` (Python) | File change events → incremental graph index update |

### Why Cytoscape.js for the graph

ChaseOS needs a graph that:
- Renders 500–5000 nodes (full vault) without performance collapse
- Supports typed node styling (color, shape, icon by node family)
- Supports typed edge rendering (solid/dashed/dotted by edge type)
- Supports trust-state visual overlays (color badges)
- Supports click-to-inspect (select node → populate Node Inspector panel)
- Supports filters (hide/show by node type, trust state, domain)
- Supports zoom/pan without redraws
- Is embeddable in an HTML page with no build system

Cytoscape.js satisfies all of these. D3.js requires more custom code for graph semantics. Sigma.js
is faster for massive graphs but lower-level. The static SVG renderer in
`graph_view_static_renderer.py` proved the data model. Cytoscape.js is the upgrade path.

**Rendering note:** Do not overclaim WebGL. Cytoscape's default rendering is Canvas-based.
The WebGL renderer was introduced as a preview in early 2025 for large-network performance.
Use Canvas/default rendering first. Test the WebGL renderer only when graph size causes
performance problems. Keep graph payloads bounded (default `max_nodes=500`).

---

## 5. Project Structure

### 10A target (start narrow — expand as passes complete)

```
runtime/
  studio/
    shell/                          ← NEW — desktop shell code lives here
      __init__.py
      main.py                       ← entry point: creates PyWebView window
      api.py                        ← StudioAPI bridge class (the only Python object exposed to JS)
      config.py                     ← app paths, dev/prod mode, vault root resolution
      file_watcher.py               ← watchdog-based vault watcher → graph index events
      frontend/                     ← NEW — HTML/CSS/JS frontend
        index.html                  ← shell chrome (sidebar, panel slots, status bar, status pill)
        app.js                      ← shell logic: tab switching, sidebar, pywebview.api calls
        styles.css                  ← layout + trust-state color system
        assets/
          cytoscape.min.js          ← bundled locally (no CDN — local-first, offline-first)
    [existing modules unchanged]

06_AGENTS/
  Phase10-Desktop-Shell-Engineering-Plan.md   ← THIS FILE
```

Later passes add files to `shell/` as needed. Do not pre-create empty files. The full multi-file
frontend structure (graph.js, inspector.js, cockpit.js, panels.css etc.) grows naturally as
panels are implemented. Start with one `index.html`, one `app.js`, one `styles.css`.

**Window state persistence** (resolved decision):
```text
~/.chaseos/studio/window-state.json      ← global user config (size, position, last vault)
~/.chaseos/studio/recent-workspaces.json ← recent vault paths
```
Vault-local state (`<vault>/.chaseos/studio/`) only after explicit write permission exists and
only for ChaseOS-native workspaces. General markdown vaults must not receive hidden state writes.

---

## 6. The StudioAPI Bridge

This is the most important architectural object in the shell. Every JS call from the frontend
goes through this class. It is the single point of governance enforcement between the UI and
the Python backend.

```python
# runtime/studio/shell/api.py

class StudioAPI:
    """
    Exposed to the WebView JS context as window.pywebview.api.
    Every method here is callable from JS. No other Python code is
    directly callable from the frontend.
    
    Rules:
    - All read methods return JSON-serializable dicts (ok, surface, result)
    - All write methods route through service.py (StudioService)
    - No method may raise an unhandled exception into JS (always return ok/error)
    - vault_root is set at window creation time, not passed per-call
    - Methods must be fast (<200ms) or return a job_id for async polling
    """
    
    def __init__(self, vault_root: str):
        self._vault_root = vault_root
        self._service = StudioService(vault_root)
    
    # ── Read surfaces ────────────────────────────────────────────────────
    
    def get_dashboard(self) -> dict: ...
    def get_graph_contract(self, *, max_nodes=500) -> dict: ...
    def get_graph_index(self) -> dict: ...
    def get_node(self, node_id: str) -> dict: ...
    def search_nodes(self, query: str) -> dict: ...
    def get_runtime_cockpit(self) -> dict: ...
    def get_approval_queue(self) -> dict: ...
    def get_provenance(self, file_path: str) -> dict: ...
    def get_quarantine_list(self) -> dict: ...
    def get_memory_summary(self, runtime_id: str) -> dict: ...
    def get_schedule_summary(self) -> dict: ...
    def get_pulse_summary(self) -> dict: ...
    def get_siteops_summary(self) -> dict: ...
    def get_aor_summary(self) -> dict: ...
    def get_sic_workspaces(self) -> dict: ...
    def get_app_launcher(self) -> dict: ...
    
    # ── Write surfaces (all routed through service.py) ───────────────────
    
    def create_node(self, node_type: str, title: str, domain: str) -> dict: ...
    def create_link(self, source_id: str, target_id: str) -> dict: ...
    def submit_approval(self, approval_id: str, decision: str, note: str) -> dict: ...
    def promote_from_quarantine(self, file_path: str) -> dict: ...
    def update_node_metadata(self, node_id: str, fields: dict) -> dict: ...
    
    # ── Settings ─────────────────────────────────────────────────────────
    
    def open_folder_dialog(self) -> dict: ...        # native file dialog
    def get_workspace_info(self) -> dict: ...
    def get_config_summary(self) -> dict: ...
    
    # ── Shell events (called from file watcher thread) ───────────────────
    
    def _on_file_changed(self, path: str, event_type: str) -> None: ...
```

**Critical rule:** The `StudioAPI` class has a fixed, documented surface. No UI feature may
call a Python function directly from JS outside of this class. New features add methods to this
class; they do not bypass it.

---

## 7. Subphase Implementation Plan

### Pass 10A — Core Shell (Target: working installable app)

**Goal:** A native application window opens, loads the vault, scans it, builds the graph model,
and displays a basic shell with navigation working. All subsequent passes build on this.

**Engineering tasks (in order):**

1. **Install PyWebView**
   ```
   .venv/Scripts/pip install pywebview==6.2.1 watchdog
   ```
   Add to `pyproject.toml` optional dependencies: `pywebview==6.2.1`, `watchdog>=4.0`.
   Pin the exact version — do not float `pywebview`. Verify the install works against
   WebView2 on Windows 11 before adding to pyproject.toml.

2. **`runtime/studio/shell/main.py`** — entry point
   - Reads vault root (CLI arg or last-used from window state)
   - Instantiates `StudioAPI(vault_root)`
   - Creates window: `pywebview.create_window("ChaseOS Studio", "frontend/index.html", js_api=api, ...)`
   - Starts file watcher thread
   - `pywebview.start(debug=DEV_MODE)`

3. **`runtime/studio/shell/api.py`** — `StudioAPI` class (read methods only for 10A)
   - `get_dashboard()` → calls `runtime.studio.dashboard.get_dashboard(vault_root)`
   - `get_graph_contract()` → calls `runtime.studio.graph_view_contract.build_graph_view_contract(vault_root)`
   - `get_workspace_info()` → calls `runtime.studio.open_folder_readiness.build_open_folder_readiness(vault_root)`
   - `open_folder_dialog()` → `window.create_file_dialog(FOLDER_DIALOG)` (PyWebView native dialog)

4. **`runtime/studio/shell/frontend/index.html`** — shell chrome
   - Left sidebar: icon buttons for Graph / Inspector / Cockpit / Approvals / Intake / Settings
   - Main content area: panel slots (one visible at a time, tab switching)
   - Top bar: vault name, workspace path, connection status indicator
   - Bottom status bar: Runtime Status Pill (OBSERVE/ACT/AWAIT_APPROVAL etc. from OSRIL spec)

5. **Graph panel inside `index.html`** (10A target: load and display — single-file for 10A)
   - Load `assets/cytoscape.min.js` — bundled locally, no CDN, no internet dependency
   - On panel activate: `window.pywebview.api.get_graph_contract()` → populate Cytoscape
   - Node click → `window.pywebview.api.get_node(id)` → dispatch to inspector panel
   - Basic trust-state color coding (8 states → 8 CSS classes)
   - Pan + zoom working
   - Node family icons/shapes working

6. **`runtime/studio/shell/frontend/css/trust-states.css`** — color system
   ```
   Trust state → CSS variable → node fill + border
   raw              #94a3b8  (gray)
   quarantined      #f97316  (orange)
   suggested        #facc15  (yellow)
   promoted         #22c55e  (green)
   canonical        #3b82f6  (blue)
   archived         #6b7280  (dark gray)
   disputed         #ef4444  (red)
   generated        #a855f7  (purple)
   ```

7. **`runtime/studio/shell/file_watcher.py`** — filesystem watcher
   - `watchdog` observer on vault root
   - On `.md` file create/modify/delete: rebuild graph index incrementally
   - Notify JS via `window.evaluate_js("onVaultChange({type, path})")` (PyWebView JS injection)

8. **`chaseos studio shell`** CLI command — launches the desktop shell
   - `python -m runtime.studio.shell.main [--vault-root PATH] [--dev]`

9. **PyInstaller spec file** — `chaseos-studio.spec`
   - Bundles `runtime/studio/`, `runtime/aor/`, `runtime/pulse/`, `runtime/agent_bus/`, etc.
   - Bundles `runtime/studio/shell/frontend/` as data files
   - Bundles Cytoscape.js
   - Output: `dist/ChaseOS-Studio.exe`

**10A acceptance criteria (narrow — window opens, graph loads, node click opens Inspector, no writes):**
- [ ] PyWebView window opens on Windows 11
- [ ] Frontend loads from local files (no server, no CDN)
- [ ] Cytoscape renders the graph payload from `get_graph_contract()`
- [ ] Graph payload warns (`truncated: true`) when node count exceeds `max_nodes`
- [ ] Clicking a node calls `StudioAPI.get_node(node_id)`
- [ ] Inspector panel displays node metadata, edges, related nodes, trust/provenance summary
- [ ] No vault writes occur during any 10A operation
- [ ] No provider calls occur
- [ ] No connector calls occur
- [ ] No runtime execution occurs

---

### Pass 10B — Graph + Node Model (Target: full typed graph)

**Engineering tasks:**

1. **Node type shapes in Cytoscape** — map all 14 node families to shapes
   ```
   Project       → rectangle (blue-green)
   Source        → hexagon (teal)
   Knowledge     → circle (indigo)
   Log           → diamond (amber)
   Workflow      → parallelogram (violet)
   Agent         → octagon (purple)
   Decision      → shield (blue)
   Generated     → dashed-border circle (purple)
   Intake        → triangle-down (orange)
   ...
   ```

2. **Four edge type styles** — Explicit (solid), Structural (medium), Suggested (dashed),
   Runtime/Action (dotted + animated)

3. **Trust state badges** — ring/border color on node perimeter by trust state

4. **Provenance chain UI in Node Inspector** — "Provenance" tab calls
   `window.pywebview.api.get_provenance(file_path)` and renders the chain

5. **Graph filters panel** — sidebar filter chips (by node type, trust state, domain, project);
   Cytoscape `filter()` + `style()` calls; filter presets saveable to `window_state.json`

6. **Generated vs canonical visual distinction** — generated nodes have dashed border + purple
   ring + "AI" badge; canonical nodes have solid blue ring

7. **Semantic link suggestions** — suggested edges rendered in dashed yellow; accept/reject
   controls in Node Inspector

**10B acceptance criteria:**
- [ ] All 14 node families visually distinct
- [ ] All 4 edge type layers rendered distinctly
- [ ] Trust state always visible on every node
- [ ] Filter by type/state/domain/project working with saveable presets
- [ ] Provenance chain traceable from any node in the graph
- [ ] Generated artifacts visually distinct from promoted/canonical at all times

---

### Pass 10C — Controlled Write Surface (Target: safe mutations from UI)

This pass wires `service.py` into the JS frontend.

**Engineering tasks:**

1. **Create node from graph context menu** → `StudioAPI.create_node(type, title, domain)`
   → `StudioService.execute_action(ActionSpec(action="create", ...))`

2. **Create link by drag** → `StudioAPI.create_link(source_id, target_id)` → service layer

3. **Edit node metadata in Node Inspector** → metadata form → `StudioAPI.update_node_metadata()`
   → service layer (protected-file guard applies)

4. **Inline approval UX** — when `service.py` returns `requires_approval=True`:
   - Modal appears with action summary, risk level, affected files
   - Operator confirms or rejects
   - On confirm: `StudioAPI.submit_approval(id, "approved", note)`

5. **Approval queue panel** — live feed of pending approvals from `approval_queue_panel.py`;
   resolve-in-panel flow

6. **Semantic link acceptance** — accept button on suggested edge → `create_link()` → service

**10C acceptance criteria:**
- [ ] Creating a node from graph persists to vault via service layer
- [ ] Editing metadata from Inspector persists correctly (frontmatter update)
- [ ] Approval gate triggers modal for protected/high-risk actions
- [ ] Approval records written to audit trail
- [ ] No write bypasses service layer (verifiable from audit log)

---

### Pass 10D — Project / Runtime Cockpit (Target: full operator surface)

**Engineering tasks:**

1. **Project/Workspace View** — reads `01_PROJECTS/` nodes from graph, groups by domain,
   surfaces sprint focus from `Now.md`

2. **Runtime Cockpit panel** — wire `runtime_cockpit.py` into shell panel; show agent bus queue,
   heartbeats, workflow activity, startup states

3. **Intake/Promotion View** — quarantine queue from `provenance.py`;
   `promote_from_quarantine()` action; semantic hint editor form before Gate

4. **Approval Center** — unified approval queue across all sources (OSRIL + studio write surface); canonical doc: [[ChaseOS-Approval-Center]];
   multi-step approval workflow UX

5. **Agent/Runtime Browser** — registered agents from `memory_inspector.py`; role cards; trust
   tier ceilings; scorecard sparklines

6. **Runtime Status Pill (bottom bar)** — consumes OSRIL `OperatorSession.status` state model
   from `Operator-Overlay-UX-Spec.md`; always-visible mode indicator

**10D acceptance criteria:**
- [ ] Workspace View shows all active projects grouped by domain
- [ ] Sprint focus from `Now.md` visible on workspace home
- [ ] Runtime Cockpit shows live agent bus state (refreshed on demand)
- [ ] Quarantine queue shows all `03_INPUTS/00_QUARANTINE/` items with hint editor
- [ ] Approval Center is a single panel for all pending approvals; current cross-feature boundary is tracked in [[ChaseOS-Approval-Center]]
- [ ] Runtime Status Pill reflects current OSRIL mode state

---

### Pass 10F — Import / Compatibility / Setup (Target: onboarding for non-ChaseOS vaults)

**Engineering tasks:**

1. **Open Folder flow** — native folder dialog → `open_folder_readiness.py` scan → detect
   ChaseOS vs general markdown → route to Native mode or Compatibility mode

2. **Compatibility mode rendering** — best-effort node type inference from folder structure,
   frontmatter, naming; compatibility-mode visual indicator (banner)

3. **ChaseOS bootstrap wizard** — step-by-step new workspace creation; wraps
   `chaseos scaffold brain` CLI; generates `CLAUDE.md`, `README.md`, folder structure

4. **Native mode upgrade flow** — from compatibility mode, offer guided migration into ChaseOS
   conventions; shows what would change; requires explicit operator confirmation at each step

5. **Import settings** — initial domain selection, watch folder config, provider config summary

**10F acceptance criteria:**
- [ ] Opening any markdown folder works (compatibility mode)
- [ ] ChaseOS-native vaults detected and opened in native mode
- [ ] Bootstrap wizard produces a valid ChaseOS workspace from scratch
- [ ] Native mode upgrade is non-destructive (no file mutations without operator confirmation)

---

### Pass 10E — Canvas / Whiteboard (Deferred)

Not V1 scope. The graph view serves as the primary investigation surface for V1. Canvas is a
later mode added after 10A–10D ship and the core shell is proven stable.

Seed spec: `06_AGENTS/ChaseOS-Studio-Freeform-Canvas-Graph-Linking.md`. Implementation must split into bounded passes: workspace-local canvas draft schema/read-only loader, graph-node reference resolver, Canvas shell-panel contract, explicit local draft-save authority boundary, visual-link proposal bridge, and optional Excalidraw/browser proof mapping. The first substrate must keep canvas objects as draft JSON pointers and annotations; graph-node references do not mutate graph truth, canvas links are not canonical edges, and any promotion/link conversion routes through the existing service layer, Gate, and approval surfaces.

---

## 8. IPC Contract

All `StudioAPI` methods must return JSON-serializable values only. PyWebView's JS bridge
marshals basic Python types (dict, list, str, int, float, bool, None) across the boundary
as promises. Complex Python objects will not cross. Design accordingly.

**Standard envelope — success:**
```json
{
  "ok": true,
  "status": "graph_loaded",
  "data": { ... },
  "warnings": [],
  "blocked_authority": []
}
```

**Standard envelope — failure:**
```json
{
  "ok": false,
  "status": "blocked_or_failed",
  "error": {
    "code": "missing_workspace",
    "message": "No workspace is open."
  },
  "warnings": [],
  "blocked_authority": []
}
```

**Standard envelope — approval required** (write surface gated actions):
```json
{
  "ok": false,
  "status": "requires_approval",
  "error": null,
  "approval": {
    "approval_id": "appr_abc123",
    "action": "promote_from_quarantine",
    "risk_level": "medium",
    "affected_files": ["03_INPUTS/00_QUARANTINE/Sources/article.md"]
  },
  "warnings": [],
  "blocked_authority": []
}
```

JS callers always check `ok` first. The `status` field is human-readable and frontend-routeable.
The `blocked_authority` array lists what was blocked and why — surfaces to user as explanation,
not generic error. This envelope shape is designed to be Tauri-portable (same JSON contract
works if frontend migrates to Tauri later).

**Async methods** (operations >200ms) return a job shape:
```json
{
  "ok": true,
  "status": "queued",
  "job_id": "job_abc123",
  "data": null,
  "warnings": [],
  "blocked_authority": []
}
```

JS polls `get_job_status(job_id)` until `status == "done"` or `status == "failed"`.

---

## 9. Graph Data Contract (Python → Cytoscape.js)

The `get_graph_contract()` API method returns a Cytoscape-compatible elements array:

```json
{
  "ok": true,
  "surface": "studio_api.get_graph_contract",
  "result": {
    "nodes": [
      {
        "data": {
          "id": "node_abc123",
          "label": "Now.md",
          "node_family": "home_doc",
          "trust_state": "canonical",
          "domain": "ChaseOS",
          "project": null,
          "file_path": "00_HOME/Now.md",
          "has_provenance": false
        }
      }
    ],
    "edges": [
      {
        "data": {
          "id": "edge_abc123_def456",
          "source": "node_abc123",
          "target": "node_def456",
          "edge_layer": "explicit",
          "link_text": "[[Operating-System]]"
        }
      }
    ],
    "node_count": 1,
    "edge_count": 1,
    "truncated": false,
    "max_nodes": 500
  }
}
```

`node_id` values are stable: they are the SHA-256 of the vault-relative file path (until a
proper `node_id` frontmatter scheme is implemented). The graph index contract (`graph_index_contract.py`)
already produces this stability model.

---

## 10. File Watcher → Live Graph Update Contract

When the file watcher detects a change:

1. Python: `file_watcher.py` receives event via `watchdog`
2. Python: rebuilds graph node for the changed file (incremental — not full rebuild)
3. Python: calls `window.evaluate_js(f"onVaultChange({json.dumps(event)})")` (PyWebView JS injection)
4. JS: `onVaultChange(event)` handler updates Cytoscape elements for that node/edge
5. JS: Node Inspector re-fetches if the changed node is currently inspected

```json
// vault change event shape
{
  "type": "modified" | "created" | "deleted",
  "path": "00_HOME/Now.md",
  "node_id": "node_abc123",
  "node_data": { ... }    // new node data, null if deleted
}
```

---

## 11. Packaging Plan (PyInstaller)

```python
# chaseos-studio.spec
block_cipher = None

a = Analysis(
    ['runtime/studio/shell/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('runtime/studio/shell/frontend', 'studio_frontend'),
        ('06_AGENTS/role-cards', 'role_cards'),
    ],
    hiddenimports=[
        'runtime.studio.service',
        'runtime.studio.graph_view_contract',
        'runtime.studio.dashboard',
        'runtime.studio.runtime_cockpit',
        'runtime.studio.provenance',
        'runtime.studio.memory_inspector',
        'runtime.studio.sic_workspace_browser',
        'runtime.studio.aor_pipeline_monitor',
        'runtime.studio.schedule_inspector',
        'runtime.studio.pulse_inspector',
        'runtime.studio.siteops_inspector',
        'runtime.agent_bus.bus',
        'runtime.aor.engine',
        # ... all runtime.* imports
    ],
    ...
)
```

**Target output:**
- `dist/ChaseOS-Studio.exe` — Windows standalone (no Python install required)
- `dist/ChaseOS-Studio/` — directory distribution (faster startup, larger folder)

**Dev mode:**
- `python -m runtime.studio.shell.main --dev` — PyWebView debug mode; browser devtools in window

---

## 12. Runtime Handover Instructions

This section is for all runtimes (Chaser Agent, Hermes, Codex, OpenClaw) participating in Phase 10
engineering.

### For the runtime implementing 10A (primary: Chaser Agent)

**Read before starting:**
1. This document (complete)
2. `06_AGENTS/ChaseOS-Studio-Architecture.md` — product spec and guardrails
3. `runtime/studio/desktop_shell_app.py` — the layout to replicate (run it to see current mock)
4. `runtime/studio/desktop_shell_foundation.py` — machine-readable map of what's built
5. `runtime/studio/graph_view_contract.py` — the data model the graph will consume
6. `runtime/studio/service.py` — the write governance layer (never bypass this)

**First task:** `runtime/studio/shell/main.py` + `api.py` + `frontend/index.html`. Get a window
opening with the vault loaded and a placeholder graph panel. Acceptance: window opens, graph
loads, clicking a node shows its path in the Inspector panel.

**Governance rules:**
- All vault writes through `StudioService` only
- `StudioAPI` is the only Python object exposed to JS (`js_api=` argument in `create_window`)
- No direct filesystem reads in JS
- Loopback binding only (no network exposure)
- Dev mode is the only mode that enables PyWebView devtools

### For the runtime implementing graph rendering (primary: Chaser Agent)

**Read before starting:**
1. `runtime/studio/graph_view_contract.py` and `runtime/studio/graph_index_contract.py`
2. `runtime/studio/graph_view_static_renderer.py` — the static render that already works; the
   Cytoscape.js implementation replaces this for the interactive shell
3. `06_AGENTS/ChaseOS-Studio-Architecture.md` Section 7 (Node Ontology) and Section 8 (Edge Ontology)

**Data shape:** `get_graph_contract()` returns a Cytoscape-compatible elements array (Section 9
of this document). No transformation needed between API return and `cytoscape({ elements: ... })`.

**First task:** Cytoscape.js canvas that loads graph data from `window.pywebview.api.get_graph_contract()`,
renders nodes with trust-state colors, and emits `nodeSelected(node_id)` event on click.

### For the runtime implementing write surfaces (primary: Chaser Agent / Codex review)

**Read before starting:**
1. `runtime/studio/service.py` — the `StudioService`, `ActionSpec`, `ApprovalRequest`, `ActionResult`
2. `06_AGENTS/ChaseOS-Studio-Architecture.md` Section 10 (Service Layer) and Section 11 (Action Model)

**Rules:**
- Every write method in `StudioAPI` calls `StudioService.execute_action(ActionSpec(...))`
- The `StudioService` returns `requires_approval=True` for gated actions — the API method must
  surface this to JS in the standard IPC response shape
- No write method in `StudioAPI` touches the filesystem directly
- Protected files (see `CLAUDE.md` protected files list) must be blocked at both service layer
  and surfaced to the user with an explanation, not a generic error

### For the runtime implementing 10D Runtime Cockpit (primary: Hermes/OpenClaw visibility)

**Read before starting:**
1. `runtime/studio/runtime_cockpit.py` — the existing desktop contract
2. `06_AGENTS/Operator-Overlay-UX-Spec.md` — the OSRIL mode state model for the status pill
3. `runtime/studio/runtime_startup_controls.py` — startup surface state contract

**Runtime Cockpit panel should surface:**
- Agent Bus queue health (open/claimed/in_progress task counts per runtime)
- Heartbeat recency per runtime
- Workflow activity (recent AOR executions from `aor_pipeline_monitor.py`)
- Startup state per runtime (from `runtime_startup_controls.py`)
- Runtime Status Pill consuming OSRIL `OperatorSession.status`

---

## 13. Resolved Decisions

All five previously-open decisions are now closed.

| Decision | Resolution |
|----------|-----------|
| **PyWebView version** | Pin `pywebview==6.2.1`. Current stable as of 2026-05-04. Verify against WebView2 on Windows 11 before committing to pyproject.toml. |
| **Cytoscape.js bundle vs CDN** | Bundle locally in `frontend/assets/cytoscape.min.js`. No CDN. ChaseOS is local-first; Studio must work offline. A CDN would violate the product identity. |
| **`node_id` stability scheme** | Hybrid model. For read-only graph scans: `node_id = chaseos:path:<sha256(normalized_relative_path)>`. For nodes created or explicitly upgraded by Studio: `chaseos_id: <uuid>` written to frontmatter. **Critical:** never inject frontmatter IDs into existing files during read-only scans. That would silently mutate vaults and break the compatibility promise. |
| **Window state persistence** | Global user config for app state: `~/.chaseos/studio/window-state.json` and `~/.chaseos/studio/recent-workspaces.json`. Vault-local state `<vault>/.chaseos/studio/` only after explicit write permission exists and only for ChaseOS-native workspaces. Compatibility-mode vaults receive no hidden state writes. |
| **Dev hot-reload** | PyWebView reload + `watchdog` for 10A. No Vite/React/build toolchain. Static HTML/CSS/JS is sufficient for the first shell. Frontend build tooling can be added if the UI becomes component-heavy in a later pass. |

---

## 14. What Is NOT in Phase 10 (Governance Guard)

These items are explicitly out of scope for every Phase 10 pass and must not be introduced:

- A second data store (Studio does not maintain its own database of canonical truth)
- A new trust-tier authority (UI configuration cannot change trust tiers or permission ceilings)
- Gate bypass (all promotion actions go through `service.py` → Gate → vault)
- Silent canonical promotion (every canonical state change requires explicit operator action)
- Canvas outputs that become canonical without Gate promotion
- Provider calls from the shell (all provider access through AOR workflows, not from Studio directly)
- Credential display (provider keys never displayed in Studio, even in settings)

---

## 15. Related Documents

| Document | Purpose |
|----------|---------|
| `06_AGENTS/ChaseOS-Studio-Architecture.md` | Product spec, subphase definitions, guardrails |
| `06_AGENTS/Markdown-to-Standalone-Bridge.md` | Markdown vault → standalone surface mapping |
| `06_AGENTS/Phase10A0-UI-Runtime-Handover.md` | Phase 10A0 specific handover (acquisition cockpit) |
| `06_AGENTS/Operator-Overlay-UX-Spec.md` | OSRIL mode states for Runtime Status Pill |
| `runtime/studio/desktop_shell_foundation.py` | Machine-readable current state map |
| `runtime/studio/desktop_shell_app.py` | Running proof of layout (visit localhost to see) |
| `runtime/studio/service.py` | Write governance — mandatory for all write operations |
| `runtime/studio/graph_view_contract.py` | Graph data model contract |
| `runtime/studio/graph_index_contract.py` | Rebuildable graph index from vault |

---

*Phase 10 Desktop Shell Engineering Plan — v1.1 | Created: 2026-05-04 | Updated: 2026-05-04
(v1.1 — PyWebView marshaling claim corrected: avoids subprocess/Rust/Node orchestration, does not
eliminate JS↔Python type marshaling; Cytoscape WebGL overclaim corrected: Canvas default, WebGL
preview for large graphs only; PyWebView version pinned to 6.2.1; Cytoscape bundled locally (no
CDN); 5 open decisions all resolved; IPC envelope format updated to ok/status/data/warnings/blocked_authority;
project structure simplified to 10A minimum; 10A acceptance criteria replaced with 10-point
read-only guard list; Tauri rule recorded explicitly: do not use until public distribution phase.)*

*Graph links: [[ChaseOS-Studio-Architecture]] · [[Phase10A0-UI-Runtime-Handover]] · [[Markdown-to-Standalone-Bridge]] · [[Operator-Overlay-UX-Spec]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
