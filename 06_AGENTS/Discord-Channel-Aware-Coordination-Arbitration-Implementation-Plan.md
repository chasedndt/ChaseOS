---
title: Discord Channel-Aware Coordination Arbitration Implementation Plan
type: implementation-plan
status: active — ingress metadata, duplicate-fingerprint guard, lane-aware claim suppression, Discord create-time normalization, and channel-bound Discord ingress translation surface implemented; direct gateway/bot wiring closure still open
version: 0.2
created: 2026-04-26
updated: 2026-04-26
owner: Optimus
phase: Phase 9
---

# Discord Channel-Aware Coordination Arbitration Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Upgrade the ChaseOS coordination bus and Discord ingress path so Hermes/OpenClaw arbitration operates on the real unit of work: runtime + channel/lane + thread/topic + origin work item, not just runtime name alone.

**Architecture:** Keep `runtime/agent_bus/` as the canonical coordination substrate, but extend it with ingress-context metadata and dedupe/claim scope. Discord remains ingress/visibility; structured bus state remains the machine source of truth. The key shift is translating Discord-origin requests into channel-aware bus-owned work records before runtime execution continues.

**Tech Stack:** Python stdlib, existing `runtime/agent_bus/` SQLite substrate, `runtime/lifecycle/coordination_watch*`, Hermes Discord gateway config/docs, pytest focused + CLI + regression slices.

---

## Why this is now the highest-impact next move

New live repo truth + operator clarification established:
- the bus currently models ownership primarily at `runtime` scope (`Hermes`, `OpenClaw`)
- Hermes Discord ingress already distinguishes channel IDs and thread IDs
- ChaseOS actively uses multiple Discord ingress lanes for one runtime:
  - `hermes-chat`
  - `hermes-chat` threads/topics
  - `chaseos-ops`
- the current bus/watch architecture is therefore too coarse even when active
- the Hermes coordination-watch layer is configured but not actually live/persistent on this machine

So the strongest next work is **not scaffold generation yet**.
It is to finish the real runtime-coordination substrate so duplicate Hermes handling stops happening across Discord lanes.

---

## Deliverables

1. **Ingress-aware bus schema extension**
   - source platform/channel/thread/message/conversation metadata
   - work fingerprint / dedupe key
   - claim scope aligned to ingress context

2. **Discord-to-bus translation path**
   - Discord-origin operator/control requests become structured bus-owned work records before machine coordination-sensitive work proceeds

3. **Lane-aware claim/dedupe behavior**
   - prevent duplicate processing of the same underlying task across `hermes-chat`, threads, and `chaseos-ops`

4. **Live coordination-watch activation surface**
   - Hermes coordination-watch should be operator-visible from the user’s own terminals, not just ad hoc agent-invoked terminals
   - supervision/bootstrap truth must become real live runtime state, not only test artifacts

5. **Truth-sync docs/tests**
   - update bus architecture, Discord control-plane docs, and active Phase 9 priority docs

---

## Ordered Task Program

### Task 1: Define the real unit of coordinated work

**Objective:** Document and encode the identity model the bus must arbitrate.

**Files:**
- Modify: `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- Modify: `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
- Create/modify tests later after schema agreement

**Required model additions:**
- `source_platform`
- `source_channel_id`
- `source_thread_id`
- `source_channel_class`
- `conversation_key`
- `origin_message_id` or envelope ID
- `work_fingerprint`
- optional `control_plane_route`

**Verification:**
- doc explicitly states runtime-only arbitration is insufficient for multi-lane Discord ingress
- doc explicitly names `hermes-chat`, `hermes-chat` threads, and `chaseos-ops` as distinct ingress contexts

---

### Task 2: Add failing schema/storage tests for ingress-aware tasks

**Objective:** Prove the current bus cannot represent the required work identity.

**Files:**
- Modify: `runtime/agent_bus/test_agent_bus.py`
- Modify/create: `runtime/agent_bus/test_agent_bus_cli.py`
- Possible new file: `runtime/agent_bus/test_agent_bus_ingress_context.py`

**Test expectations to add first:**
- task creation can persist ingress metadata
- list/claim surfaces preserve ingress context
- duplicate Discord-origin work items with the same fingerprint are rejected or merged fail-closed
- two different threads under `hermes-chat` remain distinguishable
- same operator work mirrored into another lane does not create parallel claims when fingerprint matches

**Verification:**
- focused pytest started RED for the missing duplicate-fingerprint guard and missing promoted ingress flags, then passed once those seams were wired
- current repo truth now already proves:
  - task creation persists ingress metadata
  - duplicate Discord-origin work items with the same fingerprint are rejected fail-closed
  - two different threads under `hermes-chat` remain distinguishable when fingerprints differ
  - Discord ingress now fails closed when `source_channel_id` is missing
  - `conversation_key` / `control_plane_route` can be normalized from source channel/thread identity
  - `origin_message_id` can seed the default `work_fingerprint` when callers do not provide one

---

### Task 3: Extend bus schema and storage layer *(partially complete 2026-04-26)*

**Objective:** Make the SQLite bus store ingress-aware task identity.

**Files:**
- Modify: `runtime/agent_bus/bus.py`
- Modify backend/schema files under `runtime/agent_bus/` as needed
- Modify CLI serializers if new fields must display

**Implementation requirements:**
- add columns / JSON field(s) for ingress metadata
- add `work_fingerprint` uniqueness or guarded duplicate detection
- preserve backward compatibility for older tasks where possible
- avoid granting new authority; this is routing/audit structure only

**Verification:**
- focused tests pass
- existing bus tests still pass
- current repo truth already includes:
  - ingress metadata columns/JSON storage
  - migration from legacy runtime-only CHECK-constraint schemas
  - guarded duplicate detection on active same-recipient `work_fingerprint` values
  - promoted `agent-bus task create` flags for Discord-origin ingress metadata
  - canonical `runtime/cli/main.py` `agent-bus task create` now accepts and forwards the same ingress metadata / fingerprint arguments instead of lagging behind wrapper surfaces

---

### Task 4: Add lane-aware routing/claim semantics

**Objective:** Ensure bus claims reflect the real ingress context, not only runtime identity.

**Files:**
- Modify: `runtime/agent_bus/bus.py`
- Modify: `runtime/agent_bus/router.py`
- Modify tests under `runtime/agent_bus/`

**Implementation requirements:**
- preserve runtime-level ownership while adding ingress-aware dedupe scope
- allow distinct tasks from different lanes when genuinely different
- reject/merge duplicate mirrored work when the same operator intent is detected
- keep stale-runtime reclamation safe

**Verification:**
- same-fingerprint duplicate cannot create two active competing work items
- different thread IDs with different fingerprints can coexist
- current repo truth now also includes lane-aware claim suppression for already-active conversation/message scope, so `watch_once --claim-next` skips open tasks that conflict with an active claimed lane and prefers the next non-conflicting work item
- current repo truth now also includes instance-scoped heartbeats derived from claimed Discord-lane work, so coordination-watch can report lane-aware liveness keys instead of only coarse runtime-level heartbeat identity when a claimed task carries Discord ingress context

---

### Task 5: Wire Discord-origin coordination-sensitive requests into the bus earlier

**Objective:** Stop relying on ambient Discord lane state as if it were machine coordination state.

**Files:**
- Inspect/modify Hermes gateway integration points and/or ChaseOS ingress adapters that translate Discord-origin work
- Likely truth-sync docs:
  - `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
  - `HERMES.md`

**Implementation requirements:**
- requests from `hermes-chat`, `chaseos-ops`, or threads that require coordinated machine work should first become structured bus-owned state
- advisory-only chat should remain advisory
- no direct authority expansion from Discord ingress

**Verification:**
- tests or harness simulation show a Discord-origin coordinated task becomes one bus work item with ingress metadata
- current repo truth now also includes a promoted `agent-bus ingress discord ...` translation surface that resolves the bound Discord channel map, leaves runtime-chat advisory by default, and creates one bus-owned coordination item only when the request is explicitly classified coordination-sensitive
- actual Discord gateway/bot wiring into that translation seam remains an honest remaining closure item

---

### Task 6: Make Hermes coordination-watch genuinely live/persistent

**Objective:** Move Hermes coordination-watch from “configured/tested” to operator-visible live runtime behavior.

**Files:**
- Modify as needed under:
  - `runtime/lifecycle/coordination_watch.py`
  - `runtime/lifecycle/coordination_watch_supervisor.py`
  - `runtime/lifecycle/coordination_watch_bootstrap.py`
  - `runtime/lifecycle/hermes.lifecycle.yaml`
- Add/update tests around status/start/bootstrap state

**Implementation requirements:**
- Hermes watch should be startable and inspectable from user-owned terminals
- state/log/bootstrap artifacts should be real live artifacts, not only pytest-temp outputs
- `status` should reflect true running/install state

**Verification:**
- `python3 chaseos.py runtime coordination-watch-supervisor --runtime Hermes --action status --json`
- `python3 chaseos.py runtime coordination-watch-bootstrap --runtime Hermes --action status --json`
- user can inspect the resulting state/log files from their own shell

---

### Task 7: Truth-sync the Phase 9 program

**Objective:** Update active plans so scaffold generation is no longer incorrectly next.

**Files:**
- Modify: `06_AGENTS/Phase9-Implementation-Closure-Plan.md`
- Modify: `06_AGENTS/Immediate-Next-Steps-Execution-Plan.md`
- Modify: `06_AGENTS/Feature-Fit-Register.md`
- Modify: `07_LOGS/Build-Logs/Build-Logs-Index.md`
- Create build log for this reprioritization + later implementation passes

**Verification:**
- active docs show channel-aware coordination arbitration as the highest-impact immediate runtime-shell/AOR closure task

---

## Recommended execution order right now

1. Reprioritize docs/plan truth immediately
2. Write failing ingress-context bus tests
3. Implement schema/storage changes
4. Implement dedupe/claim behavior
5. Wire Discord ingress to bus-owned work creation
6. Bring Hermes coordination-watch live/persistent
7. Re-run focused + broader regressions

---

## Acceptance criteria

The upgrade is successful when all of the following are true:
- Hermes/OpenClaw bus state can distinguish:
  - `hermes-chat`
  - a thread under `hermes-chat`
  - `chaseos-ops`
- same underlying operator task mirrored across lanes does not create duplicate active work
- distinct lane/thread tasks remain distinct when they should
- Hermes coordination-watch is visibly live and inspectable from user-owned terminals
- Discord-origin coordination-sensitive work routes into `runtime/agent_bus/` before cross-runtime machine work continues
- active Phase 9 planning docs treat this as the current highest-impact priority, ahead of scaffold generation

---

## Immediate operator answer

Yes — this is now at the stage where it **should** be done, and it is the correct next highest-impact implementation lane.
Scaffold generation should wait until this coordination substrate is fixed, because duplicate runtime work across Discord lanes is a more fundamental OS problem.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
