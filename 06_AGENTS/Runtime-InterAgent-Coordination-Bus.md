---
title: Runtime Inter-Agent Coordination Bus
type: architecture
status: active
version: 0.3
created: 2026-04-24
updated: 2026-04-29
phase: 9
layer: AOR / runtime coordination substrate
---

# Runtime Inter-Agent Coordination Bus

> Canonical architecture and operating contract for Hermes ↔ OpenClaw machine coordination inside ChaseOS.
> This is a ChaseOS-owned coordination layer. It is not owned by Hermes, OpenClaw, or Discord.

---

## 1. Purpose

ChaseOS now supports two live runtime lanes with different strengths:
- **Hermes** — bounded coordination, planning, review, documentation, and Discord-facing advisory work
- **OpenClaw** — bounded execution, scheduled workflow operation, and Windows-side implementation work

A direct chat loop between the two is not acceptable as the primary machine protocol.

The Coordination Bus exists to provide:
- durable task ownership
- structured handoff state
- resumability across runtime restarts
- inspectable audit state
- bounded autonomy without Discord spam loops

---

## 2. Constitutional Rule

**Discord is visibility. The bus is coordination.**

Discord may carry:
- operator requests
- summaries
- blockers
- approvals
- milestone visibility

Discord does **not** become the machine-state source of truth for runtime-to-runtime work.

The authoritative machine coordination surface is:
- `runtime/agent_bus/`

Generalized rule:
- operator/control panels are ingress surfaces
- the bus is the coordination substrate
- execution still routes through AOR/manifests/role cards/Gate
- harness/runtime adapters that participate in coordination-sensitive multi-runtime work must route through this substrate rather than ambient chat/thread state

This matters because Discord is only the current transport, not the permanent control-plane identity of ChaseOS.
Future standalone panels, shell surfaces, or other bounded operator ingress paths should follow the same rule.

---

## 3. Authority Boundary

| Layer | Owner | Authority |
|---|---|---|
| Coordination protocol | ChaseOS | Canonical coordination contract |
| Task ownership/state | Coordination bus | Operational state for cross-runtime work |
| Workflow execution | AOR + adapter manifests + role cards | Governs what each runtime may actually do |
| Canonical truth | ChaseOS vault + Gate | Final authority |

The coordination bus does **not** grant new permissions.
It routes work only within already-declared adapter and workflow boundaries.

### Phase 11 Chat dependency handoff rule

Phase 11 Chat and Phase 10 Studio may surface backend dependencies, but they must not convert those dependencies into Chat-originated execution. When a Hermes/Optimus `/goal` agent finds a Chat blocker that belongs to Agent Bus, AOR, Gate, provider, lifecycle, browser, graph, source-pack, credential/config, protected-file, or canonical-promotion authority, it records a dependency report rather than writing a bus task or executing the backend path directly.

Required report fields:
- `missing_contract`
- `affected_phase10_or_phase11_surface`
- `lower_phase_owner_or_surface`
- `minimum_proof_needed`
- `blocked_action_reason`

The bus may carry follow-up work only when a governed lower-phase workflow creates or approves an appropriate task. Chat/Studio previews remain operator visibility and handoff context, not coordination state mutation by themselves.

---

## 4. Current Implementation Shape

### Pass 1 (bootstrap — 2026-04-24)

- `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
- JSON schemas for packets, events, and heartbeats
- SQLite schema for a durable local task bus
- bridge docs for Hermes and OpenClaw
- runtime-local bridge instructions under `runtime/openclaw/` and `runtime/hermes/`
- ChaseOS CLI: `chaseos agent-bus status / task list|claim|update / heartbeat / expire-stale / watch`

### Pass 2 (capability-aware routing — 2026-04-24)

Adds the full routing layer above the raw bus:

- `capabilities.py` — filesystem-based capability registry (`runtime/*/capabilities.yaml`)
- `router.py` — liveness-aware + capacity-aware routing
- CLI: `chaseos agent-bus route / runtimes / task create / task reclaim`

### Pass 3 (router completion — 2026-04-25)

Enforces declared limits at dispatch time:

- **Concurrent load** — `route_task_type()` checks active task count per runtime against `max_concurrent_tasks`; routes around at-capacity runtimes
- **Priority ceiling** — `create_task()` rejects tasks whose priority exceeds `recipient.priority_ceiling`
- 73 routing tests / 1245 total vault tests pass

### Pass 4 (promoted enforcement surfaces — 2026-04-25)

Makes the bus-first rule visible at daily operator/harness surfaces instead of only inside the raw Gate helper:

- `chaseos gate check-coordination ...` is now a promoted operator-facing policy surface
- coordination-sensitive workflows can declare `runtime_adapter` + `coordination_requirements` in the workflow registry
- `chaseos run ...` now blocks coordination-sensitive workflows unless the caller declares the invoking adapter and the bus path (`--coordination-via runtime/agent_bus/`)
- this keeps the shell surface subordinate to the same bus-first governance that the manifest + Gate layer already enforces

### Pass 5 (canonical command hardening â€” 2026-04-27)

Validates that bus smoke flows use the public ChaseOS operator surface:

- canonical smoke tests invoke `python chaseos.py agent-bus ...`, not `runtime/agent_bus/cli.py`
- side-effecting smoke tests use a disposable `--vault-root` temp vault
- created smoke tasks are cancelled with a unique cleanup marker
- the live bus database is checked to ensure that marker did not land in real task or heartbeat state
- covered flows: task creation, Discord ingress translation, heartbeat publication, watch/claim, reclaim, and cancellation

The implementation is:
- **SQLite for machine state**
- **capabilities.yaml per runtime for routing declarations**
- **JSON packet examples for interoperability**
- **Discord summaries for human visibility**
- **a ChaseOS-owned raw watch loop surface** via `chaseos agent-bus watch --once|--interval N` for explicit heartbeat refresh, stale-expiry checks, and optional next-task claim behavior
- **runtime-specific live daemon surfaces** via `chaseos runtime daemon --runtime hermes --daemon-interval N` and `chaseos runtime daemon --runtime openclaw --daemon-interval N`; these run the selected runtime's coordination-watch loop in an operator-owned shell so Hermes/OpenClaw can publish fresh bus heartbeat state, claim eligible tasks, dispatch only their declared workflow handlers, and return result/audit writebacks without using Discord chat as the machine protocol
- **a lane-aware claim arbitration surface** via `evaluate_task_claimability(...)`, `claim_task(...)`, and `watch_once(...)` so direct claims and watch-loop claims both reject active Discord/control-surface lane conflicts before a runtime can pick up duplicate channel/thread work
- **runtime-instance task ownership** via nullable `owner_instance` on task rows so Hermes and OpenClaw can claim Discord/control-surface thread lanes as `runtime + instance`, not only as a runtime-wide owner
- **a runtime-lifecycle supervision foothold** via `chaseos runtime coordination-watch-supervisor --action plan|status|start|stop` so Hermes/OpenClaw can have bounded local background-loop ownership inside ChaseOS rather than only ad hoc terminal invocation
- **a runtime-lifecycle bootstrap-registration foothold** via `chaseos runtime coordination-watch-bootstrap --action plan|status|install|remove` so Hermes/OpenClaw can own host-startup artifacts inside ChaseOS rather than keeping autostart shape as undocumented external glue
- **a host apply/verify seam** via `chaseos runtime coordination-watch-bootstrap --action apply|verify|unregister` so ChaseOS can attempt the declared scheduler mutation and report the real host response instead of pretending startup registration is already active
- **a privilege-aware elevated handoff seam** via `chaseos runtime coordination-watch-bootstrap --action handoff` so ChaseOS can generate a PowerShell/UAC-ready registration bundle when the current shell cannot create the Task Scheduler entry directly
- **a structured bootstrap event seam** so registration attempts, verification checks, handoffs, unregisters, and cleanup actions remain visible as runtime event records even after the immediate shell output is gone
- **a bounded reboot-verification seam** via `chaseos runtime coordination-watch-bootstrap --action reboot-verify` so ChaseOS can define the post-registration evidence bundle and host-side observed-result JSON path that should be checked after a successful elevated registration and later restart/logon; the generated verifier now requires a zero scheduler-query exit code and expected task-name evidence before marking scheduler registration observed
- **a durable success-state capture seam** via `chaseos runtime coordination-watch-bootstrap --action capture-success` so ChaseOS can persist the currently observed scheduler + supervisor evidence as a machine-readable success/failure record rather than leaving it only in transient shell output, now reconciling host-written reboot verification results when they exist and match the expected runtime/task identity
- **an explicit reboot-result reconcile seam** via `chaseos runtime coordination-watch-bootstrap --action reconcile-reboot-result` so operators can request that same evidence-import path directly when they want a named post-boot reconciliation action
- **a read-only activation proof report** via `chaseos runtime coordination-watch-bootstrap --action activation-report` so ChaseOS can aggregate scheduler, supervisor, heartbeat, success-record, and reboot-verification evidence into one operator-facing truth surface, with `proof_complete`, missing-evidence, and evidence-validation fields preventing `proven` status before validated reboot-verification evidence exists
- **a read-only activation checklist** via `chaseos runtime coordination-watch-bootstrap --action activation-checklist` so ChaseOS can translate that evidence into ordered operator steps, ready commands, host/elevation-required actions, and evidence paths without mutating host or lifecycle state
- **a bounded Agent Activity writeback seam** so confirmed startup-success captures can be promoted into the audit-facing runtime history lane without claiming success when the evidence is still partial or negative
- **a promoted Gate coordination check plus run-surface preflight** so harness-facing CLI execution cannot silently bypass the bus on declared coordination-sensitive workflows

What remains future:
- actual elevated registration plus later restart/logon verification on the host machine
- dedicated archive/compaction policy for completed coordination history

---

## 5. Core Objects

### Task Packet
A bounded unit of work assigned from one runtime to another.

Required fields:
- `task_id`
- `run_id`
- `from`
- `to`
- `intent`
- `status`
- `request`
- `expected_output`
- `created_at`
- `updated_at`

Ingress-aware fields (now part of the substrate direction and initial implementation footing):
- `source_platform`
- `source_channel_id`
- `source_thread_id`
- `source_channel_class`
- `conversation_key`
- `origin_message_id`
- `control_plane_route`
- `work_fingerprint`

Execution-constraint fields (optional metadata, not permission grants):
- `execution_constraints.allow_shell_commands`
- `execution_constraints.allow_live_subprocess`
- `execution_constraints.write_policy`
- `execution_constraints.allowed_write_paths`

Mission Mode dry-review task enqueue is now live as a bounded local coordination surface. `chaseos ventureops mission-agent-bus-enqueue-gate --write-approval --consume --enqueue-task` may write exactly one open Agent Bus task for `mission.run_dry_review` after exact-once Mission Mode gates clear. The follow-on `chaseos ventureops mission-runtime-claim-result-gate --write-approval --consume --claim-task --dispatch-aor --ingest-result --close-task` surface may then claim that exact local task, dispatch only the existing local AOR dry-review handler, ingest the local result back into the mission workspace, and close the task to `done`. The live `mission-chase-ai-runtime-governance-kit` workspace consumed this path once on 2026-05-14. Duplicate or stale claims block before dispatch/result ingestion. This does not call providers, use browsers, send externally, read credentials, mutate CRM/payment systems, or promote canonical state.

Current create-time normalization now also exists in the live bus layer:
- Discord-origin task creation fails closed if `source_channel_id` is missing
- `conversation_key` is auto-derived from Discord channel/thread identity when callers provide source IDs but omit the key
- `control_plane_route` can default to the same normalized lane identity so the ingress route remains machine-visible
- `origin_message_id` can seed the default `work_fingerprint` when callers have not computed one explicitly
- execution constraints are normalized into a task-level object so adapter packets can carry no-shell, no-live-subprocess, and write-policy requests from ingress; recipients may use this only to narrow execution inside their existing authority

Current claim-time arbitration now also exists in the live bus layer:
- `evaluate_task_claimability(...)` reports whether a runtime may claim a task and returns `lane` plus `conflicts` metadata for operator/runtime inspection
- `claim_task(...)` rejects open tasks that conflict with active work already owned by that runtime on the same `work_fingerprint`, `origin_message_id`, or `conversation_key`
- `watch_once(..., claim_next=True)` uses the same evaluator and reports `skipped_conflict_count` plus `skipped_conflicts` when it skips blocked lane work and claims the next safe task
- backend implementations must enforce the same lane rule inside the serialized claim mutation; SQLite now does this under a `BEGIN IMMEDIATE` write transaction so the lane check and ownership update share one atomic path
- successful claims persist `owner_instance` when supplied by `--runtime-instance-id` or when derivable from Discord lane metadata; OpenClaw and Hermes both use the same derivation:
  - thread-scoped work: `discord-thread-{source_thread_id}`
  - shared channel-scoped work such as `chaseos-ops`: `discord-channel-{source_channel_id}`
  - metadata-only fallback: `discord-lane-{conversation_key with ":" replaced by "-"}`

Instance-aware fields (partially live now; broader ownership/routing use still expanding):
- `runtime_instance_id`
- `heartbeat_scope`
- `control_surface`
- `control_surface_key`
- `owner_instance`

The bus must not assume one runtime equals one ingress lane. A single runtime may participate through multiple operator-facing channels, topics, CLI sessions, or future ingress surfaces; coordination state therefore needs the real work-item context and runtime-instance identity, not only the runtime name. Task ownership is now represented as `owner` plus optional `owner_instance`; heartbeats continue to use `runtime` plus optional `runtime_instance_id`.

### Event Record
Immutable state transition or note attached to a task.
Examples:
- task created
- claimed
- blocked
- review requested
- done
- stale timeout

### Heartbeat
Per-runtime or per-runtime-instance liveness record indicating:
- runtime identity
- runtime instance identity
- current state
- current task
- control-surface / ingress scope
- last seen time
- health summary

Current implementation direction:
- heartbeat freshness comes from explicit writes (`upsert_heartbeat(...)`) rather than autonomous background refresh inside the bus itself
- ChaseOS should no longer assume one heartbeat row per runtime name, because a single runtime may be actively controlled through multiple Discord channels, Discord threads, CLI sessions, or future ingress surfaces at the same time
- promoted shell surfaces now also expose explicit instance-aware heartbeat publication fields so operators/runtime wrappers can publish lane-scoped liveness without dropping back to runtime-only identity
- the bus therefore needs instance-aware heartbeat identity for control-surface-affined work, while still preserving a runtime-level summary view for operator inspection
- CLI/watch helpers can publish fresh heartbeats, lifecycle-backed supervision can keep a bounded local loop running, and bootstrap registration can now generate startup artifacts, host-apply/handoff seams, structured bootstrap event records, and validated reboot-result evidence, but ChaseOS still does not yet prove reboot-persistent execution after a successful elevated registration
- Activation checklist inspection can now show the exact remaining proof step per runtime, but it remains an inspection/runbook surface. It does not perform elevated registration, reboot the host, or manufacture post-reboot proof.

---

## 5b. Current Lifecycle / Retention Posture

The current coordination bus is durable, but it is not yet a fully self-managing queue with archival rotation.

### What it does now
- persists tasks, events, and heartbeats in SQLite
- allows explicit heartbeat refresh
- expires stale **owned active** tasks through `mark_stale_tasks(...)`
- records immutable `expired` events when stale expiry occurs
- retains completed/cancelled history in the same primary store

### What it does not do yet
- autonomously refresh heartbeats without an explicit caller
- archive completed tasks into a separate history lane
- compact or prune done/cancelled tasks out of the primary task store
- define a separate retention window for long-lived coordination history

### Practical interpretation
Current bus lifecycle behavior should be understood as:
- **explicit heartbeat publication**
- **guardrailed stale expiry for active owned work**
- **retention-in-place for completed history**

not as:
- automatic liveness refresh
- automatic archival rollover
- self-pruning queue maintenance

This distinction matters for future operator surfaces: completed tasks are still inspectable bus history right now, not moved to a separate coordination archive.

---

## 5a. Routing Layer

The routing layer is the dispatch-time intelligence sitting above the raw bus. It answers "which runtime should handle this task type right now?" before a task is created.

### Architecture

```
runtime/{runtime}/capabilities.yaml
        │
        ▼
capabilities.py
  discover_runtime_names()
  load_runtime_capabilities()
  get_eligible_runtimes(task_type)
        │
        ▼
router.py
  get_runtime_liveness()      ← reads heartbeats from SQLite
  _read_owned_task_counts()   ← reads active tasks from SQLite
  route_task_type(task_type)  ← eligible × live × capacity → recommended
        │
        ▼
bus.py / create_task()
  known runtime check
  priority ceiling check      ← rejects if task priority > recipient.priority_ceiling
  SQL INSERT
```

### Three-filter routing

`route_task_type()` applies filters in order:

| Filter | Source | Rule |
|---|---|---|
| Eligibility | capabilities.yaml `handles` | runtime declares it can handle this task_type |
| Liveness | SQLite heartbeats | heartbeat age < `heartbeat_stale_seconds` |
| Capacity | SQLite active task count | owned active tasks < `max_concurrent_tasks` |

Recommended = first runtime passing all three, sorted by declared priority (primary before secondary before tertiary).

If all live runtimes are at capacity → still recommend the first live one (task may queue).  
If all eligible runtimes are stale → `recommended = None`.

### Priority ceiling enforcement

`create_task()` checks task priority against `recipient.priority_ceiling` before writing to the bus.

Priority ranks: `low=0`, `normal=1`, `high=2`, `critical=3`

| Runtime | ceiling | Max task priority accepted |
|---|---|---|
| OpenClaw | normal | normal (high/critical rejected) |
| Hermes | high | high (critical rejected) |

Ceiling check is fail-open: if the recipient has no capabilities.yaml, the check is skipped.

### N-runtime extensibility

Adding a third runtime requires:
1. `runtime/{new_runtime}/capabilities.yaml` — declares bus_name, handles, max_concurrent_tasks, heartbeat_stale_seconds, priority_ceiling
2. runtime registry / policy-binding records appropriate to the runtime's authority lane
3. `runtime/{new_runtime}/coordination_bridge.md` — runtime-local bridge doc

The bus storage and JSON packet contracts are runtime-generic by current live implementation; capability and policy validation, not SQL CHECK-constraint rewrites, are the authority layer for live runtime identity.

---

## 6. Runtime Names

Use stable `bus_name` values from capabilities.yaml in all machine messages:
- `Hermes`
- `OpenClaw`
- `Codex`

Nicknames, casual aliases, and conversational phrasing are not machine-safe identifiers.
The filesystem runtime folder name (e.g. `openclaw`) and the bus_name (e.g. `OpenClaw`) are distinct. Always use `bus_name` in packets.

---

## 7. Allowed Intents

Machine packets should use a narrow intent set:
- `TASK`
- `RESULT`
- `BLOCKER`
- `REVIEW`
- `QUESTION`
- `HEARTBEAT`
- `NOTICE`

If a message cannot be expressed in one of these classes, it should not become a bus packet yet.

---

## 8. Task State Machine

Allowed task states:
- `open`
- `claimed`
- `in_progress`
- `blocked`
- `review`
- `done`
- `cancelled`
- `expired`

Rules:
1. One task has one owner at a time.
2. Only the owner may move a task into `in_progress`.
3. Reviewers do not silently take ownership.
4. Reassignment requires a new event record.
5. Stale tasks are escalated, not ignored.

---

## 9. Runtime Role Split

### Hermes default role
- planning
- decomposition
- review
- policy-aware routing
- summaries and audit visibility
- Discord-facing coordination
- primary Phase 10 Studio / Phase 11 Chat surface implementation when the work is bounded to read-only/readiness/local wrapper UI, approved audit updates, and handoff documentation

### OpenClaw default role
- concrete execution
- Windows-side actions
- implementation / build / test work in its allowed scope
- artifact production
- structured result return
- backend dependency tracking and lower-phase handoff evidence for Studio/Chat blockers that Hermes/Optimus cannot resolve inside Phase 10 authority

This is a default operating split, not a hardcoded exclusivity rule. The split does mean that OpenClaw should not silently become the Phase 10 Studio implementer just because it tracks a backend blocker, and Hermes/Optimus should not cross into Phase 9-and-below backend authority just because it owns the Studio surface.

### Backend dependency report schema

When a Phase 10 Studio or Phase 11 Chat surface is blocked by lower-layer work, the bus packet, handoff note, or Agent-Activity checkpoint must carry these fields:

| Field | Meaning |
|---|---|
| `missing_contract` | The absent or unproven backend/AOR/Gate/Agent Bus/runtime contract. |
| `affected_phase10_or_phase11_surface` | The Studio or Chat surface that cannot proceed. |
| `lower_phase_owner_or_surface` | The Phase 9-and-below lane that must supply the contract or proof, such as AOR, Gate, Agent Bus, provider governance, browser/runtime dispatch, OpenClaw Windows-side proof, or another named runtime lane. |
| `minimum_proof_needed` | The smallest test, audit artifact, CLI/static output, or operator approval evidence that would unblock the surface. |
| `blocked_action_reason` | The exact action Hermes/Optimus or OpenClaw refused to take across the authority boundary. |

Studio and Chat dependency reports are coordination evidence only. They do not grant shell, connector, credential, canonical writeback, approval-consumption, browser, runtime dispatch, or protected-file authority.

---

## 10. Loop Prevention Rules

The bus must prevent runaway agent self-conversation.

Minimum controls:
- max handoff count per task
- max retry count
- stale timeout
- dedupe on repeated identical blocker/result packets
- no free-form runtime-to-runtime chat outside structured intents

---

## 11. Discord Relationship

Discord remains a shared control-plane and visibility surface.

Recommended pattern:
1. Operator request arrives in Discord
2. Request is classified and, when actionable, translated into structured ChaseOS state
3. Cross-runtime or coordination-sensitive work proceeds through `runtime/agent_bus/`
4. Direct declared workflow execution proceeds through the bounded AOR path
5. Discord receives milestone summaries and blocker notices

No runtime should treat ambient Discord chatter as a machine instruction.

The same pattern should apply to future shell, standalone, mobile, or other bounded control surfaces:
- ingress surface receives the request
- ChaseOS translates it into structured state
- execution/coordination continue through governed substrates rather than transport-local logic

---

## 12. Audit Expectations

When the bus is used for meaningful work, ChaseOS should preserve:
- task IDs
- ownership transitions
- runtime heartbeats
- result artifacts
- links to AOR logs or build logs where applicable

The bus itself is operational state, not canonical truth.
Durable outcomes still belong in normal ChaseOS writeback and audit surfaces.

### Summary-context application
For how task/result/blocker/review/heartbeat states should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Coordination-Bus-Summary-Context-Application.md`

For the current Obsidian-openable inspection hub and live CLI verification
commands, see:
- [[Agent-Bus-Visual-Inspection]]

---

## 13. Non-Goals

This pass does **not**:
- grant Hermes shell authority
- grant Hermes unrestricted workflow authority
- grant OpenClaw protected-file authority
- replace AOR workflows
- let Discord act as the machine-state source of truth
- create uncontrolled autonomous debate loops between runtimes

---

## 14. Current Verdict

The correct autonomous pattern for dual-runtime ChaseOS work is:

**structured task bus + bounded execution + Discord visibility**

not

**constant runtime-to-runtime prompting in chat**

---

*Graph links: [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[ChaseOS-Discord-Control-Plane]] · [[Agent-Bus-Visual-Inspection]] · [[Codex-Runtime-Profile]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[Runtime-Navigation-Map]] · [[Runtime-Instance-Authority-Parity]] · [[Runtime-Onboarding-Standard]]*
