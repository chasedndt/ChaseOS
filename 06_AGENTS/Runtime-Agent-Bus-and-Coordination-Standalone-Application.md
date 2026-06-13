---
title: Runtime Agent Bus and Coordination Standalone Application
type: implementation-bridge-plan
status: seeded — fourth concrete application of the markdown-to-standalone bridge
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Runtime Agent Bus and Coordination Standalone Application

> This document is the fourth concrete application pass for `06_AGENTS/Markdown-to-Standalone-Bridge.md`.
> It translates the bridge rules into a standalone-ready coordination slice: `runtime/agent_bus/` plus the dual-runtime coordination contract.

**Approval Center routing:** runtime shell / approval-center / operator-browser references in this coordination plan should route to [[ChaseOS-Approval-Center]] for the current Approval Center node.

---

## 1. Purpose

The earlier worked bridge passes covered:
- runtime navigation + browser governance,
- runtime state + bootstrap/user attachment,
- workflow registry + role-card execution contracts,
- and summary-context framing for typed operating artifacts.

The next strong slice is the coordination substrate that lets Hermes and OpenClaw work together without turning Discord into the machine-state source of truth.

This document applies the bridge to:
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `runtime/agent_bus/`
- runtime-local bridge docs under `runtime/openclaw/` and `runtime/hermes/`
- the future standalone/operator surfaces that should expose task routing, ownership, result return, blockers, reviews, and heartbeats.

This remains a planning/application artifact.
It does **not** replace the current markdown docs, schemas, SQLite state, or CLI surfaces as current truth.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Coordination-Bus-Summary-Context-Application.md`
- `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
- `runtime/agent_bus/task-packet.schema.json`
- `runtime/agent_bus/event.schema.json`
- `runtime/agent_bus/heartbeat.schema.json`
- `runtime/agent_bus/sqlite_schema.sql`
- `runtime/agent_bus/bus.py`
- `runtime/agent_bus/examples/hermes-task.example.json`
- `runtime/agent_bus/examples/openclaw-result.example.json`
- `runtime/agent_bus/examples/heartbeat.example.json`
- `runtime/openclaw/coordination_bridge.md`
- `runtime/hermes/coordination_bridge.md`

Not included yet:
- final Phase 10 UI components
- real-time push transport beyond local CLI/watcher substrate
- multi-machine coordination generalization beyond current dual-runtime host model
- mutation-capable operator UI for task authoring or reassignment
- generalized distributed systems features beyond the bounded ChaseOS coordination bus

---

## 3. Current Markdown-Era Roles

### A. Governance / authority layer
These docs define what the coordination layer is allowed to mean:
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Coordination-Bus-Summary-Context-Application.md`
- runtime-local coordination bridge docs for Hermes and OpenClaw

### B. Machine-state layer
These files define actual coordination state and contracts:
- packet/event/heartbeat schemas
- SQLite schema and local bus store
- `bus.py` helpers and CLI-facing runtime interaction
- example packets

### C. Human-visible mirror layer
These are the summary and visibility surfaces that reflect bus state to a person:
- Discord milestone summaries
- CLI watch/status output
- build logs referencing coordination runs
- future runtime cockpit / coordination inspector surfaces

### D. Current operating pattern
Today ChaseOS coordination works by keeping the following distinctions intact:
- Discord is visibility, not machine truth
- `runtime/agent_bus/` is operational coordination state
- AOR, manifests, and role cards still govern what any runtime may actually do
- summaries mirror coordination state but do not become the state itself

The standalone must preserve those distinctions instead of flattening coordination into a generic chat thread or a generic notifications feed.

---

## 4. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| Coordination doctrine docs | Coordination Governance Node | coordination policy panel |
| `runtime/agent_bus/*.schema.json` | Coordination Contract Record | task/event/heartbeat schema inspector |
| SQLite-backed task/event/heartbeat state | Coordination State Record | coordination bus inspector |
| runtime-local bridge docs | Runtime Coordination Profile View | Hermes/OpenClaw coordination behavior panel |
| bus watch/status outputs | Coordination Summary View | operator coordination feed |
| task/result/blocker/review/heartbeat mirrors | Summary Context View | coordination inbox / blocker center / review queue / runtime status strip |

---

## 5. Concrete Mapping Table

| Current path | Current role | Future standalone role | Key fields / behaviors that must survive |
|---|---|---|---|
| `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md` | canonical coordination doctrine | coordination governance node | Discord-vs-bus distinction, authority boundary, allowed intents, state machine, loop prevention, audit expectations |
| `06_AGENTS/Coordination-Bus-Summary-Context-Application.md` | summary-context application for coordination outputs | coordination summary-context panel | machine-state-vs-summary distinction, task/result/blocker/review/heartbeat classes, routing posture |
| `runtime/agent_bus/Agent-Bus-Folder-Guide.md` | runtime-local bus layer explainer | coordination substrate explainer | SQLite-primary rule, JSON contract rule, Discord mirror rule, canonical runtime names |
| `runtime/agent_bus/task-packet.schema.json` | bounded task-handoff contract | task schema inspector | task identity, from/to runtimes, intent, status, expected output, ownership semantics |
| `runtime/agent_bus/event.schema.json` | immutable task-event contract | event schema inspector | state transition semantics, note/event provenance, timeline meaning |
| `runtime/agent_bus/heartbeat.schema.json` | runtime liveness contract | heartbeat schema inspector | runtime identity, health state, current task, last seen semantics |
| `runtime/agent_bus/sqlite_schema.sql` | durable local machine-state structure | coordination state-model inspector | durable task/event/heartbeat storage shape |
| `runtime/agent_bus/bus.py` | executable substrate helper | coordination implementation/provenance panel | status, claim, update, heartbeat, stale expiry, watch-loop semantics |
| `runtime/agent_bus/examples/hermes-task.example.json` | example task packet | coordination task record preview | Hermes-origin task handoff meaning |
| `runtime/agent_bus/examples/openclaw-result.example.json` | example result packet | coordination result record preview | OpenClaw result return meaning, review/result posture |
| `runtime/agent_bus/examples/heartbeat.example.json` | example heartbeat packet | heartbeat record preview | liveness/state mirror meaning |
| `runtime/openclaw/coordination_bridge.md` | OpenClaw runtime-local coordination behavior | OpenClaw coordination panel | claim/update/result/blocker behavior within OpenClaw bounds |
| `runtime/hermes/coordination_bridge.md` | Hermes runtime-local coordination behavior | Hermes coordination panel | intent classification, task routing, result review, Discord summary behavior |

---

## 6. Recommended Standalone Views

### A. Coordination Bus Inspector
This should answer:
1. what tasks exist,
2. who owns them,
3. what state they are in,
4. what event history produced the current posture,
5. and what human-readable summary mirror should be shown.

Recommended panels:
1. **Task inbox / active bus list**
   - task ID
   - from / to
   - intent
   - owner
   - current state
2. **Task detail panel**
   - request
   - expected output
   - creation/update timestamps
   - related result/blocker/review records
3. **Event chronology**
   - immutable state changes
   - ownership transitions
   - stale/expiry transitions
4. **Summary mirror panel**
   - concise typed human-facing rendering of the current state

### B. Runtime Coordination Workspace
Per runtime, show:
- claimed tasks
- in-progress tasks
- blocked tasks
- review-needed items
- last heartbeat
- concise coordination posture summary

This should not be a chat window.
It should be a bounded operational state view.

### C. Blocker / Review Surface
This should elevate only the items that need human or peer attention:
- tasks in `blocked`
- tasks in `review`
- stale or expired tasks
- review-needed results

This is the surface where typed summary context matters most, because a blocker must not look like a completion and a review request must not look like closure.

### D. Runtime Liveness Strip
Compact runtime health/status surface showing:
- Hermes state
- OpenClaw state
- current task
- last seen time
- health summary

This should derive from heartbeat state, not ad hoc narrative text.

---

## 7. Relationship to the Summary Context Layer

This slice depends heavily on the Summary Context Layer.

Without typed summary context, coordination visibility becomes ambiguous:
- task vs result vs blocker vs review blur together
- Discord mirrors can be mistaken for machine truth
- review-needed work can be mistaken for finished work
- liveness pings can be mistaken for substantive state transitions

The Summary Context Layer already established that summaries should carry:
- runtime identity
- output class
- authority posture
- routing destination
- promotion/review posture

The coordination bus applies that directly.
In this slice, future standalone surfaces should treat coordination outputs as:
- **typed mirrors of bus state**, not generic prose,
- routed by task/result/blocker/review/heartbeat class,
- visibly subordinate to machine state rather than replacing it.

That keeps coordination summaries aligned with ChaseOS as an operating system rather than drifting into informal chat-like visibility.

---

## 8. Service-Layer Boundary Rules

The standalone service layer for this slice should preserve the exact distinctions ChaseOS already relies on.

### Discord does not become machine-state truth
A surface may show Discord-visible summaries, but the authoritative coordination state remains the bus.

### Bus state does not grant runtime authority
Task ownership and routing state do not override workflow manifests, role cards, adapter bounds, or Gate rules.

### Summary mirrors stay visibly derivative
Human-facing coordination summaries should always be traceable back to task/event/heartbeat source records.

### Review and blocker posture must remain explicit
A result in `review` is not `done`.
A blocker is not a low-priority notice.
The standalone must preserve these semantic boundaries.

### Coordination views are not uncontrolled chat surfaces
The bus inspector should expose structured intent/state, not encourage free-form runtime-to-runtime discussion as a primary protocol.

---

## 9. Suggested Data Model Direction

This slice suggests ChaseOS likely needs at least these additional standalone object families:
- `coordination_task_record`
- `coordination_event_record`
- `coordination_heartbeat_record`
- `coordination_runtime_profile`
- `coordination_summary_record`

And likely these specialized presentation layers:
- `coordination_bus_view`
- `runtime_coordination_view`
- `blocker_review_view`
- `runtime_liveness_strip`

That matters because coordination is neither just workflow execution nor just messaging.
It is a distinct bounded OS substrate that sits between planning, execution, and operator visibility.

---

## 10. What This Application Pass Proves

This pass proves the bridge can be extended into the dual-runtime coordination substrate.
It clarifies:
- which coordination docs become governance nodes,
- which schemas and SQLite-backed artifacts become typed coordination records,
- which runtime-local bridge docs become per-runtime coordination behavior panels,
- and how coordination summaries should remain typed mirrors of state rather than generic text.

This gives the bridge a fourth worked example and extends it from posture and execution identity into runtime-to-runtime operational coordination.

---

## 11. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

### A. It preserves constitutional layering
ChaseOS coordination remains layered:
- doctrine defines the protocol,
- bus state tracks operational coordination,
- AOR/manifests/role cards govern what each runtime may actually do,
- Discord provides visibility,
- logs preserve durable history.

This pass keeps those layers explicit.

### B. It protects the machine-state source of truth
ChaseOS is trying to avoid ad hoc runtime chat loops as the real coordination substrate.
This pass reinforces the OS rule that structured state belongs in a ChaseOS-owned layer, not in ambient messaging.

### C. It improves operator legibility without broadening autonomy
A future standalone operator should be able to see:
- who owns a task,
- what is blocked,
- what needs review,
- what each runtime is doing,
without that visibility silently becoming new authority.

That is core ChaseOS operating-system behavior: legible, bounded, inspectable autonomy.

### D. It keeps coordination summaries OS-native
When Hermes/OpenClaw expose coordination status, those summaries should remain visibly tied to:
- coordination intent,
- runtime ownership,
- machine-state origin,
- review/blocker posture,
- routing surface.

That is how summaries align with the wider ChaseOS model: not as loose text updates, but as governed operating artifacts.

---

## 12. Recommended Next Application Passes

After this slice, the strongest next bridge applications would be:
1. **core/personal split + export surfaces**
   - `CORE_MANIFEST.md`
   - `core_templates/`
   - `06_AGENTS/Core-Export-Sync-Procedure.md`
2. **runtime shell / approval center / operator-browser surfaces**
   - runtime shell docs
   - approval-center planning docs
   - runtime browser / cockpit planning docs
3. **summary taxonomy + object-model consolidation**
   - refine summary classes across workflow, coordination, and runtime-state slices
   - move toward a shared machine-readable summary-context schema

---

## 13. Current Verdict

A future ChaseOS standalone should not represent Hermes↔OpenClaw coordination as a chat transcript.
It should represent it as a **typed coordination substrate** with:
- explicit task state,
- explicit ownership,
- explicit blocker/review/result posture,
- explicit machine-state provenance,
- and explicit human-facing summary mirrors.

That is how coordination aligns with the overall ChaseOS operating system.

---

*Graph links: [[Markdown-to-Standalone-Bridge]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Coordination-Bus-Summary-Context-Application]] · [[Standalone-Summary-Context-Layer]] · [[ChaseOS-Studio-Architecture]]*

*Runtime-Agent-Bus-and-Coordination-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
