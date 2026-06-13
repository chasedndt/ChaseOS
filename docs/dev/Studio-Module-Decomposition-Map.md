# Studio Module Decomposition Map

> First stabilization pass for the ChaseOS Studio/Agent Control Plane monoliths. This map is intentionally practical: each future pass should extract one seam into a source-owned, tested module instead of adding more behavior directly to giant files.

## Scope and authority

- Runtime lane: Hermes / Optimus implementation support for ChaseOS Studio surfaces.
- Authority boundary: local Studio/source-owned UI model extraction only.
- Canonical policy anchor: `06_AGENTS/ChaseOS-Studio-Architecture.md` → "Studio monolith freeze and facade policy".
- Developer execution plan: `docs/dev/Studio-Monolith-Reduction-Roadmap.md`.
- No provider calls, no credential handling, no canonical knowledge promotion, no Gate bypass.
- New behavior should be test-backed before wiring into product surfaces.

## P0 freeze policy for agent harnesses

Implementation agents must not add major new feature logic directly into:

```text
runtime/studio/shell/frontend/app.js
runtime/studio/shell/api.py
runtime/studio/launcher_update_check.py
```

Allowed changes in those files are limited to thin adapter calls, imports/module loading, compatibility wrappers, unavoidable narrowly scoped bug fixes, comments/markers identifying extraction seams, and deletion/replacement after tests prove the extracted seam.

New feature behavior belongs in source-owned modules/facades with focused tests before product wiring.

## Current large files to freeze

| File | Current risk | Rule for future passes |
|---|---|---|
| `runtime/studio/shell/frontend/app.js` | Very large frontend monolith; chat/sidebar/runtime panels are tightly coupled. | Do not add substantial new feature logic directly. Add thin adapters only after tested helper modules exist. |
| `runtime/studio/shell/api.py` | Legacy Studio API bridge still loads recovered bytecode in the core. | Treat as compatibility/facade layer. New Python logic belongs in source-owned modules with tests. |
| `runtime/studio/launcher_update_check.py` | Large launcher/update/runtime-control accumulation point. | Extract launcher/runtime status helpers before adding new restart/log-tail behavior. |

## Initial monolith inventory — generated 2026-06-11

This is a first-pass map from live source inspection. It is deliberately grouped by ranges so agent harnesses can route work without loading entire monoliths into context. Future passes should replace each range row with exact function-level rows as seams are extracted.

### `runtime/studio/shell/frontend/app.js`

| Line range | Owner / panel | Function count | Authority classification | Extraction target | Notes |
|---|---:|---:|---|---|---|
| 1-2200 | Global shell / product copy | 45 | read-only / local UI | `frontend shell utility modules` | Runtime identity, copy polish, graph seed helpers, feature help. |
| 2201-3700 | Shell nav + Graph workspace controls | 77 | local-state write / read-only | `shell_nav.js`, `graph_workspace_state.js` | Sidebar collapse, inspector collapse, graph source/scene tab state. |
| 3701-5050 | Graph command/context workflow | 25 | approval-gated write previews / runtime-adjacent | `graph_command_surface.js` | Graph command preview/execute and inspection workflow UI. |
| 5051-5725 | Inspector + route state | 35 | local-state write / read-only | `object_inspector.js`, `studio_route_state.js` | Object inspector actions, route mapping, panel activation. |
| 5726-7600 | Knowledge Graph render/model/lens | 92 | read-only / local-state write | `graph_render_model.js`, `graph_lens.js` | Graph styling, selection, rendering, filters, hover state. |
| 7601-12000 | Studio panel loaders/product panels | 203 | mostly read-only; some approval packets | `panel_loaders/*.js` | Dashboard and product-panel rendering should split by panel family. |
| 12001-17000 | Runtime/Agent/approval-adjacent surfaces | 179 | runtime lifecycle + approval-gated | `runtime_status_view.js`, `approval_center_view.js` | Needs deeper classification before movement. |
| 17001-23500 | Phase 11 Chat and sidebar-adjacent UI | 244 | local-state write + approval packet previews | `chat_sidebar_view.js`, `chat_route_state.js`, `chat_workspace_view.js` | Immediate extraction lane. See focused chat/sidebar inventory below. |
| 23501-31000 | Docs/Markdown/Knowledge UI | 229 | local-state write + approval-gated writes | `docs_workspace_view.js`, `markdown_actions.js` | Includes vault-local document actions; must preserve approval gates. |
| 31001-38500 | Terminal/Workbench/SiteOps/Runtime tools | 188 | runtime lifecycle / approval-gated / host-sensitive | `terminal_workbench_view.js`, `runtime_tools_view.js` | Do not move without explicit lifecycle/host authority tests. |
| 38501-44713 | Voice/companions/settings/bootstrap | 222 | provider-sensitive + local-state + read-only | `voice_view.js`, `companions_view.js`, `settings_view.js` | Provider-sensitive surfaces require no-secret/no-provider-call test checks. |

### Focused `app.js` Phase 11 Chat/sidebar inventory

Immediate extraction target: replace only the sidebar/thread navigator internals after model/API/view/action tests are green.

| Line | Function | Owner | Authority | Extraction target |
|---:|---|---|---|---|
| 19862 | `initChatAdapterSelector` | Chat runtime selector | local-state/read-only | `chat_runtime_status.js` |
| 19886-20183 | `_defaultChatThreadForRuntime` through `_updateChatThreadRuntimeBadge` | Chat runtime targeting/status | local-state write + read-only runtime status | `chat_runtime_status.js`, `chat_route_state.js` |
| 20233-20528 | `_chatRuntimeActionState` through `_syncChatSendReadiness` | Chat runtime controls/readiness | runtime lifecycle-adjacent + local UI | `chat_runtime_status.js` |
| 20570-20591 | `_formatChatFileSize`, `_stageChatAttachments`, `_renderChatAttachmentTray` | Chat attachments | local-state write | `chat_attachments.js` |
| 20611 | `_selectChatThread` | Chat selection | local-state write | `chat_route_state.js` |
| 20636 | `_selectChatFolder` | Chat selection | local-state write | `chat_route_state.js` |
| 20660-20798 | `_chatThreadMatchesAdapter` through `_chatProductThreadPreview` | Sidebar render model helpers | read-only / pure-ish | `chat_sidebar_model.js` |
| 20798 | `_threadNavigatorRow` | Sidebar view row rendering | read-only DOM render | `chat_sidebar_view.js` |
| 20810 | `_chatFolderRowsFromWorkspaces` | Sidebar model grouping | read-only / pure-ish | `chat_sidebar_model.js` |
| 20828 | `ensureFolder` | Sidebar model grouping | read-only / pure-ish | `chat_sidebar_model.js` |
| 20841 | `_renderChatFolderDropdown` | Sidebar view/dropdown | local UI | `chat_sidebar_view.js` |
| 20880 | `_renderChatThreadNavigator` | Sidebar view adapter | DOM render + local-state selection | thin `app.js` adapter after `chat_sidebar_view.js` |
| 21000-21062 | `_showChatCreatePanel` through `_createChatThreadFromUi` | Create folder/thread | local-state write via API | `chat_sidebar_actions.js`, `chat_sidebar_api.js` |
| 21098-21271 | `_renameChatFolderFromUi` through `_renameChatThreadFromUi` | Rename/move/delete | local-state write via API; destructive confirm required | `chat_sidebar_actions.js`, `chat_sidebar_api.js` |
| 21288-21341 | `_chatContextFolderRows` through `_showChatContextMenu` | Sidebar context menu | local UI + action dispatch | `chat_sidebar_actions.js`, `chat_sidebar_view.js` |
| 21370-21560 | `_refreshChatAdapterNames`, `_startChatDaemon`, `_stopChatDaemon` | Runtime daemon controls | runtime lifecycle | `chat_runtime_status.js` / API facade; not part of sidebar view extraction |
| 21608-22026 | `_chatCompanion*` functions | Chat companions | local-state + provider-sensitive adjacency | `chat_companions_view.js` |
| 22111-22424 | `_sendChatMessage` through `_initPhase11ChatPanel` | Chat send/result/polling/slash menu | provider/runtime-adjacent + local UI | `chat_send.js`, `chat_results_view.js`, `chat_slash_menu.js` |
| 22801-22886 | `loadPhase11ChatPanel`, `renderPhase11ChatPanel` | Chat panel mount | read-only/load + local UI | thin `app.js` adapter after submodules |
| 23229-23461 | chat activity/card/product shell functions | Runtime event cards | read-only runtime activity | `chat_activity_cards.js` |
| 23604-23873 | Phase 11 authority controls | Chat authority/execution previews | approval-gated | `chat_authority_controls.js` |

### `runtime/studio/shell/api.py`

Treat this file as a compatibility/delegation layer. New Python source should land in `runtime/studio/api_facade/` and be directly tested.

| Line range | Owner / panel | Function count | Authority classification | Extraction target | Notes |
|---|---:|---:|---|---|---|
| 1-260 | Runtime daemon/model/watchdog/audit/log bridge | 12 | runtime lifecycle / provider-sensitive / read-only | `api_facade/runtime_controls.py`, `model_info.py`, `watchdog.py`, `audit_feed.py` | Good first facade target because public bridge methods already cluster here. |
| 261-492 | Intake + Hermes installation panels | 4 | read-only / local-state | `api_facade/intake.py`, `hermes_installation.py` | Low-risk source-owned read facade. |
| 493-1800 | Launcher update/source restoration proof wrappers | 40 | approval-gated / runtime lifecycle | `launcher_facade/update_readiness.py` | Keep as wrappers; real proof code belongs outside pywebview bridge. |
| 1801-3000 | StudioService bridge/mixed wrappers | 47 | mixed / unknown pending deeper map | `api_facade/service_bridge.py` | Requires deeper function-level classification before movement. |
| 3001-4165 | Chat runtime + Phase 11 workspace APIs | 39 | local-state write + approval-gated consumption | `api_facade/chat_threads.py`, `chat_send.py`, `approvals.py`, `companions.py` | Sidebar API bridge should call normalized source-owned endpoints over time. |
| 4166-4415 | Status/runtime profiles | 4 | read-only | `api_facade/model_info.py`, `runtime_profiles.py` | Safe read-only facade candidate. |
| 4416-6139 | Docs/Markdown APIs | 52 | local-state write + approval-gated write + vault-local reveal | `api_facade/docs_workspace.py` | Must preserve vault-local path guards and approval gates. |
| 6140-8337 | Graph/node APIs | 76 | read-only / approval-gated graph proposals | `api_facade/graph_nodes.py` | Do not add direct canonical graph mutation. |

### `runtime/studio/launcher_update_check.py`

Treat this file as accumulated launcher/update proof infrastructure. New launcher behavior should land in `runtime/studio/launcher_facade/` with tests.

| Line range | Owner / panel | Function count | Authority classification | Extraction target | Notes |
|---|---:|---:|---|---|---|
| 1-1800 | Extension manifest/readiness helpers | 6 | read-only | `launcher_facade/update_readiness.py` | Safe read/status model seam. |
| 1801-4807 | Production relaunch/source recovery proofs | 28 | approval-gated / runtime lifecycle | `launcher_facade/lifecycle_actions.py` | Keep operator-statement requirements intact. |
| 4808-9630 | Source candidate inventory/import/materialization | 50 | approval-gated protected-file/source restoration | `launcher_facade/source_recovery.py` | Protected-file sensitive; no speculative restore. |
| 9631-13014 | Governed live evidence/installer runner packets | 38 | approval-gated / host-sensitive | `launcher_facade/evidence_packets.py` | Host mutation and live evidence require explicit operator proof. |
| 13015-14451 | Artifact signing/disposable dry-run/local manifest | 17 | host-sensitive / read-only proofs | `launcher_facade/artifact_status.py` | Keep signing/status separated from lifecycle mutation. |
| 14452-16146 | Final update closeouts + source regeneration | 21 | approval-gated source restoration | `launcher_facade/source_regeneration.py` | Bytecode/source-regeneration risk stays quarantined; no fabricated source. |

## First extracted seam: Chat sidebar model

### New module

`runtime/studio/shell/frontend/chat_sidebar_model.js`

### Purpose

DOM-free and pywebview-free model helpers for the Phase 11 chat sidebar:

- normalize folder and thread records,
- build stable folder keys,
- group threads into folders,
- keep default `runtime-ops::runtime-control` folder available,
- preserve selected thread/folder state,
- sort selected/current runtime threads first,
- filter folders/threads by search text,
- expose display titles/previews without touching the DOM.

### Test contract

`runtime/studio/shell/test_chat_sidebar_model.py` runs `runtime/studio/shell/chat_sidebar_model_harness.js` through Node and verifies:

- explicit selected thread is preserved,
- selected folder key is stable,
- declared empty folders remain visible when not searching,
- implicit thread folders are synthesized,
- selected thread sorts first within its folder,
- search narrows to matching folders/threads,
- auto-selection chooses an eligible thread in the requested folder,
- `chatFolderKey` defaults empty values to `runtime-ops::runtime-control`.

### Product wiring status

`runtime/studio/shell/frontend/index.html` now loads `chat_sidebar_model.js` before `app.js`, exposing `window.ChaseOSChatSidebarModel` for the next extraction pass. The current `app.js` renderer is not yet replaced; this pass creates the safe seam first.

## Second extracted seam: Docs Inspector model

### New module

`runtime/studio/shell/frontend/docsInspectorModel.js`

### Purpose

DOM-free and pywebview-free model helpers for the Docs / Inspector workspace:

- define file-tree icon constants as ASCII HTML entities to avoid fragile raw emoji injection,
- flatten nested Docs file-tree data into render rows with active/expanded state,
- parse frontmatter fields and infer field types,
- rewrite frontmatter without touching DOM/editor state,
- build proposal-preview Markdown without calling approval executors.

### Test contract

`runtime/studio/shell/test_node_inspector_model_seam.py` runs `runtime/studio/shell/frontend/docsInspectorModel.test.js` through Node and verifies:

- closed/open folder and file icons stay `&#128193;`, `&#128194;`, and `&#128196;`,
- collapsed and expanded file-tree rows preserve ordering, depth, active state, and labels,
- frontmatter parsing classifies text/boolean/number/structured values,
- frontmatter writing sanitizes keys and preserves the existing body contract,
- proposal Markdown remains proposal-only preview text.

### Product wiring status

`runtime/studio/shell/frontend/index.html` now loads `docsInspectorModel.js` before `app.js`. `app.js` uses the model for Docs file-tree rows and delegates frontmatter/proposal helpers through compatibility wrappers. Renderer replacement remains intentionally thin; future Docs extraction should move view rendering to a separate Docs workspace view module only after browser smoke coverage stays green.

## Recommended next extraction order

1. **Docs workspace view renderer**
   - New file: `runtime/studio/shell/frontend/docs_workspace_view.js`
   - New harness: `runtime/studio/shell/frontend/docsWorkspaceView.test.js`
   - New test: `runtime/studio/shell/test_node_inspector_docs_view.py`
   - Consumes `DocsInspectorModel.buildDocsTreeRows(...)` output and renders tree/document side-panel snippets.
   - Authority: read-only DOM render plus local editor state only; no pywebview/provider/runtime calls.

2. **Docs API facade slice**
   - New Python module target: `runtime/studio/api_facade/docs_workspace.py`
   - Keep `runtime/studio/shell/api.py` as pywebview compatibility delegation.
   - Preserve vault-local path guards, WSL/Windows reveal behavior, approval gates, and backup-before-write behavior.

3. **Chat sidebar view renderer**
   - New file: `runtime/studio/shell/frontend/chat_sidebar_view.js`
   - New harness: `runtime/studio/shell/chat_sidebar_view_harness.js`
   - New test: `runtime/studio/shell/test_chat_sidebar_view.py`
   - Consumes `ChaseOSChatSidebarModel.buildChatSidebarModel(...)` output and renders folder sections/thread rows.
   - Contract: stable data attributes for `chat_sidebar_actions.js` remain unchanged.
   - Authority: read-only DOM render; no pywebview/provider/runtime calls.

2. **App.js adapter slice**
   - Replace the internal `_renderChatThreadNavigator(...)` body with: state resolve → `buildChatSidebarModel` → `ChaseOSChatSidebarView.render(...)` → existing bind hooks.
   - Keep route-state persistence in `app.js` until separately extracted.
   - Adapter change must be thin and covered by model/API/view/action harnesses.

3. **Visual density pass**
   - Only after model/API/view/action/adapter tests are green.
   - Scope: collapsible folders, compact density, active folder highlight, folder counts, drag affordances, keyboard navigation, search/filter polish, and “New chat in selected folder.”

4. **Runtime launcher/log-tail seam**
   - Extract status/log-tail view model before adding Stop/Restart UI.
   - Preserve C-2: Studio never stores provider keys; synthesize stays approval-gated and runtime-owned.

5. **Studio API facade plan**
   - Add source-owned `runtime/studio/api_facade/` modules for new APIs.
   - Keep `runtime/studio/shell/api.py` as compatibility delegation until legacy bytecode can be retired safely.

## Verification command

```bash
uvx --from pytest pytest runtime/studio/shell/test_chat_sidebar_model.py runtime/studio/test_chat_thread_rename.py -q
```

Latest observed result: `5 passed`.
