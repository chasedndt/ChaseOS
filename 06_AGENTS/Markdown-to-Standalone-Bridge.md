---
title: Markdown-to-Standalone Bridge
type: architecture-bridge
status: seeded — live markdown/Obsidian to future standalone mapping layer
version: 0.2
created: 2026-04-24
updated: 2026-04-25
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Markdown-to-Standalone Bridge

> This document defines how the current ChaseOS markdown vault maps forward into future standalone ChaseOS surfaces.
> It is the explicit bridge between today's Obsidian-first, markdown/index-note operating model and tomorrow's graph-first, standalone Studio/native representation.

**Approval Center routing:** standalone approval-center references should route to [[ChaseOS-Approval-Center]] for current cross-feature Approval Center truth and graph hygiene.

---

## 1. Why This Bridge Exists

Several docs already say that ChaseOS should remain:
- markdown-first today,
- standalone-ready tomorrow.

But those claims need one explicit translation layer that answers:
- which markdown structures are foundational,
- which file classes should become standalone nodes,
- which index notes should become navigation surfaces,
- which machine-readable runtime scaffolds should become first-class records,
- and what must remain stable so a standalone surface can rebuild the system without inventing a second truth store.

This document is that translation layer.

---

## 2. Governing Rule

**The markdown vault remains the current source of truth.**
Standalone surfaces, graph views, native clients, and future Studio layers must treat the markdown/repo state as authoritative unless and until ChaseOS explicitly defines a different canonical storage model.

The deferred persisted-graph contract in `06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md` defines how a future backend graph store and durable node-ID registry could become explicit operating artifacts. It does **not** change the current rule: markdown/repo state remains authoritative, graph indexes/views are derived, and canonical/source mutation still requires governed approval/Gate paths.

The bridge therefore maps forward from markdown — it does not demote markdown.

---

## 3. Foundational Markdown Structures That Must Survive

### A. Stable path roles
These folder roles are foundational and should survive as first-class structural concepts:
- `00_HOME/` — control/state layer
- `01_PROJECTS/` — project operating layer
- `02_KNOWLEDGE/` — durable knowledge layer
- `03_INPUTS/` — quarantine/raw inbound layer
- `04_SOPS/` — procedure layer
- `05_TEMPLATES/` — reusable structure layer
- `06_AGENTS/` — routing/governance/runtime-doc layer
- `07_LOGS/` — temporal output layer
- `runtime/` — machine-readable execution/runtime layer
- `99_ARCHIVE/` — non-operational history/reference layer

### B. Index-note surfaces
These should not be treated as ordinary notes only; they are navigation surfaces:
- `02_KNOWLEDGE/Knowledge-Index.md`
- `07_LOGS/Build-Logs/Build-Logs-Index.md`
- `07_LOGS/Agent-Activity/Agent-Activity-Index.md`
- `99_ARCHIVE/Documentation-History/Documentation-History-Index.md`
- equivalent folder index anchors across the system

### C. Routing anchors
These docs define movement through the system and should become explicit standalone navigation/control surfaces:
- `06_AGENTS/Vault-Map.md`
- `06_AGENTS/Runtime-Navigation-Map.md`
- runtime profile docs
- browser autonomy/governance docs
- core/split/sync doctrine docs

---

## 4. Mapping Rules — Markdown to Standalone Objects

### Markdown docs -> standalone nodes
Human-readable docs become standalone nodes/records when they serve one of these roles:
- governance node
- routing node
- project node
- knowledge node
- log node
- template node
- SOP node

### Index notes -> navigation/index panels
Index notes should usually map to standalone navigation or list views, not just plain note nodes.

Examples:
- `Build-Logs-Index.md` -> chronological log browser
- `Knowledge-Index.md` -> domain knowledge navigator
- `Documentation-History-Index.md` -> archive/history browser

### Machine-readable runtime files -> structured records
Files under `runtime/` should map to typed structured records rather than freeform documents.

Examples:
- `runtime/memory/nav/_schema.json` -> navigation schema record
- `runtime/memory/nav/*/nav-map.json` -> runtime navigation records
- `runtime/browser_registry/*.yaml` -> bounded browser policy/registry records
- `runtime/schedules/*.yaml` -> schedule intent records
- workflow manifests -> workflow records

---

## 5. Explicit Mapping Tables

### A. Human-readable markdown node-family mapping

| Current markdown object | Current source pattern | Standalone family | Default standalone representation | Notes |
|---|---|---|---|---|
| Control/state doc | `00_HOME/*.md` | Control Node | state/control panel node | `Now.md` and `Operating-System.md` should remain high-priority orientation nodes |
| Project OS file | `01_PROJECTS/**/[Project]-OS.md` | Project Node | project cockpit / project record | Preserve mission, status, goals, open loops |
| Knowledge note | `02_KNOWLEDGE/**/*.md` | Knowledge Node | knowledge record / graph node | Must preserve `knowledge_class` and provenance fields |
| SOP | `04_SOPS/*.md` | SOP Node | procedure node | Service layer and approval logic may later reference these directly |
| Template | `05_TEMPLATES/*.md` | Template Node | template record | Templates remain reusable structures, not canonical truth |
| Governance/routing doc | `06_AGENTS/*.md` | Governance Node / Routing Node | policy panel or routing panel | `Vault-Map.md` and related docs should become navigation/control surfaces, not just notes |
| Log artifact | `07_LOGS/**/*.md` | Log Node | timeline/log entry | Time ordering matters more than folder display alone |
| Archive/reference note | `99_ARCHIVE/**/*.md` | Archive Node | historical/reference record | Must remain non-operational by default |

### B. Index-surface mapping

| Current index note | Standalone role | Why it is special |
|---|---|---|
| `02_KNOWLEDGE/Knowledge-Index.md` | domain knowledge navigator | It is the master knowledge anchor, not just a note |
| `07_LOGS/Build-Logs/Build-Logs-Index.md` | chronological build log browser | It is a navigation/index surface over many log entries |
| `07_LOGS/Agent-Activity/Agent-Activity-Index.md` | runtime activity browser | It is the operator/runtime audit entry point |
| `99_ARCHIVE/Documentation-History/Documentation-History-Index.md` | documentation-history browser | It organizes historical passes rather than ordinary note content |
| Any folder-local `Index.md` / `*-Index.md` | list/index panel | The standalone should preserve index semantics instead of flattening them into generic note nodes |

### C. Machine-readable record-family mapping

| Current runtime file | Standalone family | Default representation | Notes |
|---|---|---|---|
| `runtime/memory/nav/_schema.json` | Schema Record | runtime-nav schema inspector | Defines record shape, not runtime state |
| `runtime/memory/nav/*/nav-map.json` | Runtime Navigation Record | runtime route/trust/risk overlay | Should align with runtime profile docs |
| `runtime/browser_registry/allowed_origins.yaml` | Browser Policy Record | allowed-origin registry panel | Registry, not freeform note |
| `runtime/browser_registry/task_classes.yaml` | Browser Task-Class Record | task-class inspector | Maps bounded browser actions and forbiddens |
| `runtime/browser_registry/watchlists/*` | Browser Watchlist Record | watchlist manager / monitor config | Should remain bounded and source-declared |
| `runtime/schedules/*.yaml` | Schedule Intent Record | schedule panel | Time-based operational object, not ordinary document |
| `runtime/workflows/registry/*.yaml` | Workflow Record | workflow registry browser | Manifest-backed executable identity |
| `06_AGENTS/role-cards/*.yaml` | Role Card Record | bounded permission-envelope inspector | Human-readable source may exist, but YAML is the typed contract |
| `06_AGENTS/Live-Visual-Shell-Contract.md` | Visual Shell Contract | read-only runtime-state animation/status panel contract | Maps existing runtime/event/approval/lifecycle truth into presentation state only; standalone shells must not treat animation as authority |

### D. Bridge targets for current seeded artifacts

| Current artifact | Immediate markdown role | Future standalone role |
|---|---|---|
| `06_AGENTS/Hermes-Runtime-Profile.md` | human-readable runtime profile | runtime profile view |
| `06_AGENTS/OpenClaw-Runtime-Profile.md` | human-readable runtime profile | runtime profile view |
| `06_AGENTS/Browser-Autonomy-Policy.md` | browser governance anchor | browser policy surface |
| `06_AGENTS/Browser-Task-Patterns.md` | browser task-pattern catalog | bounded task-pattern browser |
| `06_AGENTS/Core-Personal-Split-Implementation-Plan.md` | split plan / governance doc | workspace-structure planner |
| `06_AGENTS/Core-Export-Sync-Procedure.md` | priority/sync doctrine | repo-role / sync-doctrine panel |

---

## 6. Specific Current Bridge Targets

### A. Runtime navigation layer
Current markdown + machine-readable bridge:
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`
- `runtime/memory/nav/_schema.json`
- `runtime/memory/nav/hermes/nav-map.json`
- `runtime/memory/nav/openclaw/nav-map.json`

Standalone target:
- runtime profile views
- runtime route/risk/trust overlays
- route audit and escalation surfaces

### B. Browser autonomy layer
Current bridge artifacts:
- `06_AGENTS/Browser-Autonomy-Policy.md`
- `06_AGENTS/Browser-Task-Patterns.md`
- `runtime/browser_registry/allowed_origins.yaml`
- `runtime/browser_registry/task_classes.yaml`
- `runtime/browser_registry/watchlists/`

Standalone target:
- browser policy viewer
- allowed-origin registry browser
- watchlist management surface
- bounded browser task-class inspector

First concrete application pass:
- `06_AGENTS/Runtime-Navigation-and-Browser-Governance-Standalone-Application.md`

### C. Runtime state + bootstrap layer
Current bridge artifacts:
- `06_AGENTS/Portable-Runtime-Identity-and-User-Binding.md`
- `06_AGENTS/ChaseOS-Runtime-State-and-Gateway-Design.md`
- `runtime/bindings/`
- `runtime/state/`

Standalone target:
- runtime attachment inspector
- bootstrap contract inspector
- runtime-state inspector
- fail-closed startup/error panel
- resolver provenance surface

Second concrete application pass:
- `06_AGENTS/Runtime-State-and-Bootstrap-Standalone-Application.md`

### D. Workflow registry + role-card layer
Current bridge artifacts:
- `runtime/workflows/registry/`
- `06_AGENTS/role-cards/`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`

Standalone target:
- workflow registry browser
- role-card / permission-envelope inspector
- workflow contract panel
- workflow-linked summary/output posture view

Third concrete application pass:
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`

### E. Agent-bus + coordination layer
Current bridge artifacts:
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Coordination-Bus-Summary-Context-Application.md`
- `runtime/agent_bus/`
- `runtime/openclaw/coordination_bridge.md`
- `runtime/hermes/coordination_bridge.md`

Standalone target:
- coordination bus inspector
- runtime coordination panel
- blocker / review surface
- runtime liveness strip
- coordination summary mirror view

Fourth concrete application pass:
- `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md`

### F. Core/Personal split layer
Current bridge artifacts:
- `06_AGENTS/Core-Personal-Split-Implementation-Plan.md`
- `06_AGENTS/Core-Export-Sync-Procedure.md`
- `CORE_MANIFEST.md`
- `core_templates/`

Standalone target:
- workspace mode / repo-role inspector
- Core vs Personal structure browser
- export readiness / sanitization checklist surface
- template staging browser
- sync posture / support-lane panel

Sixth concrete application pass:
- `06_AGENTS/Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application.md`

### G. Runtime shell + approval/operator surfaces layer
Current bridge artifacts:
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/Operator-Surface-Runtime-Interaction.md`
- `06_AGENTS/Full-System-Operator-Surface.md`
- `06_AGENTS/Browser-Operator-Surface-Operational-State.md`
- `06_AGENTS/Live-Operator-Shell-Browser-Surface.md`
- `06_AGENTS/ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI.md`
- `runtime/operator_surface/browser/Browser-Operator-Surface-Folder-Guide.md`
- `06_AGENTS/Feature-Fit-Register.md`

Standalone target:
- runtime shell / command palette surface
- Approval Center
- Agent / Runtime Browser
- live operator shell / runtime session panel
- browser visible-control shell with no-action/dependency-routing states
- execution-route inspector
- governed Pulse feedback review/apply panel with dry-run previews, apply-registry status, and explicit non-canonical effect boundaries

Seventh concrete application pass:
- `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`

Phase 10 browser-shell scope pass:
- `06_AGENTS/Live-Operator-Shell-Browser-Surface.md`

Phase 10 Pulse feedback review/apply contract:
- `06_AGENTS/ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI.md`

This Pulse review/apply contract bridges persisted review-decision records, the read-only candidate inspector, Approval Center readiness, and the existing `candidate_apply.py` dry-run/non-canonical runtime-memory apply backend into a future Studio panel. It is a routing and preview surface only until a separately approved backend lane supplies explicit operator approval evidence; it does not create a new apply mechanism, consume approvals, mutate canonical Personal Map truth, write Agent Bus tasks, activate schedules, call providers/connectors, or promote `02_KNOWLEDGE/`.

### H. Project cockpit + workspace browser layer
Current bridge artifacts:
- `01_PROJECTS/**/[Project]-OS.md`
- `06_AGENTS/SIC-Architecture.md`
- `runtime/source_intelligence/`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`

Standalone target:
- project cockpit
- workspace browser
- evidence workspace detail panel
- project/workspace cross-link panel

Eighth concrete application pass:
- `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md`

### I. Provenance explorer + chronology browser layer
Current bridge artifacts:
- `06_AGENTS/Normalization-Provenance-Contract.md`
- `07_LOGS/Build-Logs/Build-Logs-Index.md`
- `07_LOGS/Agent-Activity/Agent-Activity-Folder-Guide.md`
- `07_LOGS/Agent-Activity/Agent-Activity-Index.md`
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`

Standalone target:
- Provenance Explorer
- chronology browser / timeline index surface
- approval trace detail surface
- build/runtime trace compare surface
- source-lineage inspector

Ninth concrete application pass:
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`

Follow-on implementation/migration artifacts:
- `06_AGENTS/Provenance-Schema-and-Trace-Idea-Implementation-Plan.md`
- `runtime/schemas/provenance_migration_notes.md`
- `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `06_AGENTS/OpenClaw-First-Bounded-Promotion-Path.md`
- `06_AGENTS/Hermes-First-Bounded-Promotion-Path.md`
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `runtime/workflows/registry/openclaw_promote_note.yaml`
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml`
- `runtime/workflows/registry/hermes_promote_note.yaml`
- `06_AGENTS/role-cards/hermes-promotion-review.yaml`
- `runtime/aor/task_type_table.yaml` (`promotion-review` row)
- `runtime/aor/test_runtime_instance_promotion_drafts.py`
- `07_LOGS/Promotion-Records/`
- `runtime/aor/promotion_readiness.py`

This bridge slice now rests on a richer shared runtime-instance validation substrate too, not just contract docs:
- helper-signal dimensions are machine-checked at the pair level
- bounded `write_scope` symmetry is machine-checked at the pair level
- bounded manifest `writeback_targets` symmetry is machine-checked at the pair level

### J. Browser watchlists + evidence-flow summary-context layer
Current bridge artifacts:
- `06_AGENTS/Browser-Autonomy-Policy.md`
- `06_AGENTS/Browser-Task-Patterns.md`
- `06_AGENTS/Runtime-Navigation-and-Browser-Governance-Standalone-Application.md`
- `runtime/browser_registry/allowed_origins.yaml`
- `runtime/browser_registry/task_classes.yaml`
- `runtime/browser_registry/watchlists/`
- `runtime/workflows/registry/browser_research.yaml`
- `06_AGENTS/role-cards/browser-research.yaml`
- `06_AGENTS/Acquisition-Surface-Map.md`

Standalone target:
- browser watchlist monitor
- browser evidence workspace
- browser governance inspector
- browser change / comparison surface
- quarantine-aware browser evidence review panel

Summary-context application pass:
- `06_AGENTS/Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application.md`

### K. Consolidated operator cockpit layer
Current bridge artifacts:
- `06_AGENTS/Runtime-State-and-Bootstrap-Standalone-Application.md`
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`
- `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md`
- `06_AGENTS/Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application.md`
- `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md`
- `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`

Standalone target:
- consolidated operator cockpit
- global status band
- attention queue
- active work panel
- project/workspace context panel
- traceability sidebar

Eleventh concrete application pass:
- `06_AGENTS/Consolidated-Operator-Cockpit-Standalone-Application.md`

### L. Knowledge navigator + domain browser layer
Current bridge artifacts:
- `02_KNOWLEDGE/Knowledge-Index.md`
- `02_KNOWLEDGE/**/[Domain-Index].md`
- classified knowledge notes under `02_KNOWLEDGE/**`
- `06_AGENTS/SIC-Architecture.md`
- `04_SOPS/Research-Ingest-SOP.md`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`

Standalone target:
- knowledge navigator home
- domain browser
- knowledge detail panel
- domain relationship browser
- promotion-aware review surface

Twelfth concrete application pass:
- `06_AGENTS/Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md`

### M. Settings / provider-config / scaffold surfaces layer
Current bridge artifacts:
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/ChaseOS-CLI-Surface-Architecture.md`
- `06_AGENTS/ChaseOS-CLI-Integration-Seam.md`
- `06_AGENTS/ChaseOS-Runtime-Lifecycle-Contract.md`
- `runtime/COMMANDS.md`
- `runtime/CLI-README.md`
- `runtime/README.md`
- `runtime/openclaw/model_config.yaml`
- `runtime/hermes/model_config.yaml`
- `runtime/lifecycle/`
- future `.chaseos/config.yaml` and provider-registry surfaces referenced in doctrine/roadmap

Standalone target:
- settings home
- provider/model registry panel
- operator config panel
- runtime management and health panel
- scaffold generator / onboarding wizard
- readiness / diagnostics panel

Thirteenth concrete application pass:
- `06_AGENTS/Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application.md`

### N. Governed promotion / review center layer
Current bridge artifacts:
- `06_AGENTS/Approval-and-Decision-Trace-Summary-Context-Application.md`
- `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- `06_AGENTS/Normalization-Provenance-Contract.md`
- `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `runtime/aor/promotion_readiness.py`
- `07_LOGS/Graduation-Proposals/Graduation-Proposals-Index.md`
- proposal/graduation artifacts under `07_LOGS/Graduation-Proposals/`
- `07_LOGS/Promotion-Records/`
- `runtime/operator_surface/approvals.py`
- `runtime/mcp/tools/approval.py`

Standalone target:
- governed review queue
- approval detail panel
- promotion candidate panel
- provenance and impact panel
- runtime-instance readiness comparison panel
- helper-backed contract inspection panel
- governance context sidebar
- review history timeline

Fourteenth concrete application pass:
- `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md`

### O. Cross-panel object model consolidation layer
Current bridge artifacts:
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`
- `06_AGENTS/Consolidated-Operator-Cockpit-Standalone-Application.md`
- `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md`
- `06_AGENTS/Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md`
- `06_AGENTS/Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application.md`
- `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md`
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`
- `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md`
- `06_AGENTS/Runtime-State-and-Bootstrap-Standalone-Application.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`

Standalone target:
- shared cross-panel object families
- attention/work/context/trace/readiness/governance/relation objects
- reusable view-state contracts
- cross-surface composition rules

Fifteenth concrete application pass:
- `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md`

### P. Agent scorecards / runtime quality surfaces layer
Current bridge artifacts:
- scorecard references in `06_AGENTS/Phase9-Adopted-Feature-Specification.md`
- scorecard/runtime-quality references in `06_AGENTS/Feature-Fit-Register.md`
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`
- `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`
- future `runtime/memory/scorecards/[runtime_id].json`

Standalone target:
- runtime quality overview
- scorecard detail panel
- compliance comparison panel
- quality evidence drill-down
- reliability / improvement timeline

Sixteenth concrete application pass:
- `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md`

Runtime Support Loops implemented/proven read-only surface:
- `06_AGENTS/Runtime-Support-Loops-Contract.md`
- `runtime/studio/runtime_support_loops.py`
- `runtime/studio/shell/api.py::StudioAPI.get_runtime_support_loops_panel`
- `runtime/studio/shell/panel_registry.py` (`runtime-support-loops` mounted panel)

This support-loop surface sits between the runtime-quality layer and the repair/runtime-memory layers. It now proves how QA verification, proactive suggestions, usage tracking, and repair candidates become Phase 10 operator support packets while remaining advisory-only. It does not grant approval execution or consumption, Agent Bus task creation, runtime dispatch, memory mutation, provider/connector calls, self-upgrade, or canonical writeback; proof from parent task `t_c6791bf1` verified focused tests and a live no-write snapshot with `changed_file_count: 0`.

### Q. Execution repair / failure recovery surfaces layer
Current bridge artifacts:
- `06_AGENTS/Agent-Memory-Architecture.md`
- `04_SOPS/Agent-Failure-Ambiguity-SOP.md`
- `06_AGENTS/Full-System-Operator-Surface.md`
- `runtime/operator_surface/recovery.py`
- `06_AGENTS/ChaseOS-Runtime-State-and-Gateway-Design.md`
- fail-closed runtime-state references such as `current_state.json` / `last_error.json`
- `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`

Standalone target:
- failure state overview
- recovery process panel
- repair-memory browser
- failure evidence drill-down
- escalation / stop-condition panel

Seventeenth concrete application pass:
- `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md`

### R. Memory inspector / runtime-memory surfaces layer
Current bridge artifacts:
- `06_AGENTS/Agent-Memory-Architecture.md`
- `06_AGENTS/Claude-Memory-System.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`
- `06_AGENTS/Feature-Register.md`
- `06_AGENTS/Autonomous-Operator-Runtime.md`
- `runtime/memory/nav/`
- future `runtime/memory/scorecards/`
- future `runtime/memory/repair/`
- future `runtime/memory/adapters/[adapter-name]/identity-ledger.json`

Standalone target:
- memory inspector home
- user memory inspector
- runtime memory browser
- navigation memory inspector
- runtime learned-memory panel
- memory evidence / provenance drill-down

Eighteenth concrete application pass:
- `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md`

### S. Agent identity ledger surfaces layer
Current bridge artifacts:
- `06_AGENTS/Agent-Memory-Architecture.md`
- `06_AGENTS/Feature-Register.md`
- `06_AGENTS/Autonomous-Operator-Runtime.md`
- `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md`
- `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md`
- `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md`
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- future `06_AGENTS/[Adapter]-Identity-Ledger.md`
- future `runtime/memory/adapters/[adapter-name]/identity-ledger.json`

Standalone target:
- runtime identity overview
- identity ledger detail panel
- drift and adherence panel
- identity evidence drill-down
- identity evolution timeline

Nineteenth concrete application pass:
- `06_AGENTS/Agent-Identity-Ledger-Surfaces-Standalone-Application.md`

### T. Graph-native node and edge consolidation surfaces layer
Current bridge artifacts:
- `06_AGENTS/Graph-Substrate-Architecture.md`
- `06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md`
- `runtime/graph/artifact.py`
- `runtime/graph/extractor.py`
- `runtime/graph/topology.py`
- `runtime/graph/builder.py`
- `runtime/graph/index.py`
- `runtime/graph/query.py`
- `runtime/graph/reporter.py`

Standalone target:
- graph snapshot inspector
- node-type browser
- edge-type browser / relationship inspector
- cluster / topology explorer
- graph-backed surface relation inspector
- future durable node identity / migration-readiness inspector, after the backend graph-store contract is implemented and validated

Twentieth concrete application pass:
- `06_AGENTS/Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application.md`

### U. Memory editing / curation surfaces layer
Current bridge artifacts:
- `06_AGENTS/Agent-Memory-Architecture.md`
- `06_AGENTS/Claude-Memory-System.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`
- `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md`
- `06_AGENTS/Agent-Identity-Ledger-Surfaces-Standalone-Application.md`
- `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md`
- `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md`
- `06_AGENTS/Feature-Register.md`

Standalone target:
- memory curation home
- user-memory maintenance panel
- runtime-memory maintenance panel
- memory review queue
- memory lifecycle panel
- memory evidence / justification drill-down

Twenty-first concrete application pass:
- `06_AGENTS/Memory-Editing-and-Curation-Surfaces-Standalone-Application.md`

---

## 7. Stability Requirements

For this bridge to work, these things must remain stable or at least intentionally migrated:
- file role semantics
- folder-role semantics
- index-note concepts
- major routing anchors
- machine-readable schema/registry paths
- node identity strategy where introduced

This does not mean paths can never change.
It means changes must be explicit, migratable, and reflected in routing docs rather than occurring silently.

---

## 8. What Should Not Be Collapsed

The standalone surface should not flatten these distinctions away:
- raw input vs knowledge vs canonical state
- log/index note vs ordinary note
- runtime profile vs runtime state record
- markdown human-governance doc vs machine-readable runtime registry
- personal-instance truth vs Core/framework example material

These distinctions are part of ChaseOS, not temporary clutter.

---

## 9. Practical Rule for Ongoing Development

When adding a new important doc or runtime scaffold, ask:
1. what role does this play in the markdown system?
2. is it a node, an index surface, or a structured record in standalone form?
3. what must stay stable so that future standalone surfaces can reconstruct it correctly?

If a new artifact cannot answer those questions, the bridge is under-specified.

---

## 10. Current Verdict

ChaseOS does not need to choose between markdown and standalone.

The correct move is to keep building the live markdown-first system while making its structural concepts explicit enough that a standalone surface can later map them forward without inventing a second system from scratch.

---

*Graph links: [[ChaseOS-Studio-Architecture]] · [[Vault-Map]] · [[Runtime-Navigation-Map]] · [[Browser-Autonomy-Policy]] · [[Browser-Task-Patterns]] · [[Portable-Runtime-Identity-and-User-Binding]] · [[ChaseOS-Runtime-State-and-Gateway-Design]] · [[Standalone-Summary-Context-Layer]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Coordination-Bus-Summary-Context-Application]] · [[Normalization-Provenance-Contract]] · [[Core-Personal-Split-Implementation-Plan]] · [[Core-Export-Sync-Procedure]] · [[Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application]] · [[ChaseOS-Runtime-Shell]] · [[Operator-Surface-Runtime-Interaction]] · [[Runtime-Navigation-and-Browser-Governance-Standalone-Application]] · [[Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application]] · [[Runtime-State-and-Bootstrap-Standalone-Application]] · [[Workflow-Registry-and-Role-Cards-Standalone-Application]] · [[Runtime-Agent-Bus-and-Coordination-Standalone-Application]] · [[Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application]] · [[Project-Cockpit-and-Workspace-Browser-Standalone-Application]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Consolidated-Operator-Cockpit-Standalone-Application]] · [[Knowledge-Navigator-and-Domain-Browser-Standalone-Application]] · [[Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application]] · [[Governed-Promotion-and-Review-Center-Standalone-Application]] · [[Cross-Panel-Object-Model-Consolidation]] · [[Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application]] · [[Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application]] · [[Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application]] · [[Agent-Identity-Ledger-Surfaces-Standalone-Application]] · [[Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application]] · [[Memory-Editing-and-Curation-Surfaces-Standalone-Application]]*

*Markdown-to-Standalone-Bridge.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*
