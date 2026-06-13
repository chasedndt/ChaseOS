---
title: Native Runtime Chat Control Plane
path: 06_AGENTS/Native-Runtime-Chat-Control-Plane.md
status: canonical-candidate / implementation-brief
phase: Phase 11 / Studio Chat + Phase 9 Runtime Continuation
created: 2026-06-01
owner: ChaseOS
primary_runtime_targets:
  - Hermes
  - OpenClaw
  - Codex
  - future Claude/design lane
prototype_target: JOS_SQL repository first, then ChaseOS core
authority: documentation and architecture only; no runtime authority granted by this note
---

# Native Runtime Chat Control Plane

> This file is the full contextual note for turning ChaseOS Chat into the native runtime control plane. It should live at `06_AGENTS/Native-Runtime-Chat-Control-Plane.md` and be handed to Claude/Codex/Hermes before any implementation pass.

---

## 0. One-line thesis

ChaseOS Chat must stop being a simple message pane and become the native runtime control surface where the operator can see, approve, audit, and coordinate all agent/runtime activity in real time.

The goal is not merely to show logs in chat.

The goal is to make ChaseOS itself the place where the operator sees:

- agent acknowledgement
- live runtime activity
- tool calls
- terminal commands
- file reads/writes
- patches
- approval requests
- audit writeback
- continuation threads
- multiple agents/runtimes in the same room
- governed cross-user / cross-agent interaction later

Discord currently demonstrates the desired interaction pattern. ChaseOS must absorb the useful primitives of that pattern without inheriting Discord as authority.

---

## 1. Why this feature exists

The current Discord control plane works because it gives the operator a fast, visible, interactive stream of what the agents are doing. The user can send a message, see that the runtime noticed it, watch the tool calls, see approvals, and track run progress without opening separate terminals or logs.

The current ChaseOS Chat page is visually close to the right destination, but it is missing the main thing that makes Discord operationally useful: live runtime transparency.

The missing functionality is:

1. **Immediate acknowledgement** — the runtime should visibly acknowledge that it saw the message.
2. **Live activity stream** — every major action should appear as a structured event card.
3. **Approval cards** — high-risk actions should ask for scoped operator approval inside the conversation.
4. **Thread/channel behavior** — runtime work should be separable into task threads, run threads, debug threads, approval threads, and continuation rooms.
5. **Multi-agent room participation** — Hermes, OpenClaw, Codex, companion agents, future providers, and human operators should be able to share one session without equal authority.
6. **Audit trail** — all execution must map back to evidence, logs, approval decisions, and artifacts.
7. **Native ownership** — Discord should become optional transport, not the main control plane.

The product target is:

> When a user works in ChaseOS Chat, there should be no operational need to open Discord just to understand what the runtimes are doing.

---

## 2. Product definition

### 2.1 Feature name

Recommended canonical name:

**Native Runtime Chat Control Plane**

Other acceptable UI/product labels:

- Runtime Chat
- Agent Activity Stream
- Runtime Control Chat
- Native Agent Control Room
- Chat Control Plane

Use the canonical doc title for architecture. Use shorter product labels in UI.

### 2.2 What this feature is

This feature is the runtime-visible chat layer for ChaseOS. It turns Chat into a governed activity surface over existing runtime infrastructure.

It should combine:

- normal chat messages
- live runtime event cards
- approval cards
- status indicators
- run/thread navigation
- participant management
- audit references
- artifact links
- companion status
- Agent Bus / AOR / OSRIL visibility

### 2.3 What this feature is not

This feature is not:

- a generic chatbot UI
- a Discord clone
- a raw log dump
- a terminal emulator replacement
- a second datastore of truth
- a bypass around AOR/Gate
- a direct provider-call surface without approval
- a new authority layer for runtimes
- a place to reveal hidden model chain-of-thought
- a way for agents to mutate canonical files without the existing governance chain

---

## 3. Current system context

This feature sits at the intersection of multiple existing ChaseOS layers.

### 3.1 ChaseOS core

ChaseOS remains the constitutional system:

- governance
- Gate
- permission matrix
- trust tiers
- AOR workflows
- runtime registry
- Agent Bus
- source intelligence
- capture/provenance
- audit trails
- protected/canonical surfaces

Chat is a control surface over these layers. It must not override them.

### 3.2 ChaseOS Studio

Studio is the human-facing desktop/product shell. The Chat page belongs here as a runtime-visible operator cockpit.

Studio should surface:

- runtime events
- approvals
- provider readiness
- companion state
- AOR run state
- Agent Bus activity
- audit artifacts
- provenance references

Studio should not create new authority. It should route through the same service layer, Gate, OSRIL, AOR, and approval mechanisms as the rest of ChaseOS.

### 3.3 OSRIL / runtime interaction substrate

OSRIL is the natural substrate for operator-visible runtime events.

This feature should not invent an unrelated event model if OSRIL already has a session/event/approval/wait-resume substrate. Instead, the Chat implementation should either:

1. reuse the existing OSRIL event contract directly, or
2. extend it with a compatible `RuntimeEvent` model that can be consumed by Studio Chat.

### 3.4 AOR

The Autonomous Operator Runtime remains the governed execution engine.

Chat can request or display AOR activity, but AOR remains responsible for:

- manifest validation
- task-type routing
- role card loading
- stage dispatch
- policy binding
- Gate handoff
- audit generation
- bounded writeback

Chat should never directly run high-risk workflow actions without the AOR/Gate chain.

### 3.5 Agent Bus

The Agent Bus should become the routing lane for:

- task claims
- agent activity
- runtime event publish/subscribe
- handoff records
- queue updates
- approval wait/resume messages

The Chat page can render Agent Bus events, but it should not silently create or mutate bus tasks outside the governed service layer.

### 3.6 Hermes

Hermes is now a bounded runtime lane. In current architecture it must remain subordinate to ChaseOS governance.

Hermes should eventually emit structured events such as:

- message received
- acknowledged
- context loaded
- tool call proposed
- tool call started
- file read
- file write proposal
- shell command proposed
- approval requested
- draft written
- audit written
- run completed

Hermes must not be granted ambient vault access just because it appears in Chat.

### 3.7 OpenClaw

OpenClaw is also a bounded runtime lane. It is powerful and high-risk because it can operate across local files, shell, browser, and integrations.

OpenClaw activity is one of the clearest reasons this feature must be structured and governed. If raw chat output becomes authority, ChaseOS recreates the same trust-boundary collapse it is trying to avoid.

### 3.8 Codex / Antigravity

Codex/Antigravity currently act as repo-aware implementation lanes. For this feature they should first audit repo truth and implement the backend/frontend bridge.

Codex should focus on:

- existing Chat files
- existing Studio service layer
- OSRIL / Agent Bus / AOR event surfaces
- event schema
- persistence
- UI cards
- tests

### 3.9 Claude/design lane

Claude should be used carefully for:

- product surface design
- card hierarchy
- copy
- UX state machine
- information architecture
- implementation handoff to Codex

Claude should not be asked to grant authority, bypass Gate, or directly mutate protected runtime policy.

### 3.10 MCP

MCP may later expose controlled read/tool/prompt surfaces into the runtime chat system. MCP should follow the existing discipline:

- resources are read surfaces
- tools are action surfaces
- prompts are reusable instruction scaffolds
- schemas must validate early
- draft/proposal modes should precede mutation
- scope must be minimized

MCP is not the first implementation target for this feature. It is future-compatible architecture.

---

## 4. Reference behavior from Discord

Discord currently provides useful primitives:

### 4.1 Fast acknowledgement

Agents often respond with an emoji or typing state. This matters because it tells the operator:

- the message was seen
- the runtime is alive
- work has been queued
- the system is not silently failing

ChaseOS should implement this as a structured state, not merely an emoji.

Possible states:

- `seen`
- `queued`
- `acknowledged`
- `typing`
- `planning`
- `executing`
- `awaiting_approval`
- `blocked`
- `failed`
- `completed`

### 4.2 Live tool/action stream

Discord currently shows compact action traces such as:

- skill view
- terminal command
- file read
- file write
- patch
- command approval required
- working timer
- compacting context

ChaseOS should render these as typed cards, not as raw pasted logs.

### 4.3 Embedded approvals

Discord approval cards with actions like Allow Once / Allow Session / Always Allow / Deny are useful. ChaseOS should keep the ease but harden the authority.

An approval button in ChaseOS must map to a scoped approval object with:

- request id
- actor
- runtime/adapter
- workflow/action
- exact command/action
- read targets
- write targets
- external systems
- risk class
- approval scope
- expiry
- audit destination
- decision record

Emoji reactions are not approvals.

### 4.4 Threads and channels

Discord makes it easy to create channels/threads for sub-work. ChaseOS needs its own version:

- task thread
- run thread
- approval thread
- debug thread
- continuation thread
- audit thread
- shared room

The goal is not to copy Discord exactly. The goal is to give runtime work a clean separation model.

### 4.5 Participants and permissions

Discord lets users and bots appear in the same place. ChaseOS needs a safer version where presence does not imply authority.

A participant can be visible in a chat without having permission to execute actions.

---

## 5. Core architectural decision

Do not scrape raw logs into the chat timeline.

Build a structured runtime event stream.

The canonical flow should be:

```text
User message
→ ChaseOS Chat service
→ policy / command envelope / intent classification
→ Agent Bus or AOR request path
→ runtime adapter: Hermes / OpenClaw / Codex / future
→ structured RuntimeEvent stream
→ persistence / audit
→ Studio Chat timeline cards
→ approval / wait-resume / audit writeback
```

This lets ChaseOS render Discord-like visibility while preserving machine-checkable governance.

Raw logs may exist as artifacts. The timeline should show structured summaries and links to full artifacts.

---

## 6. Required conceptual separation

Do not collapse these into one table or one message type:

1. **Chat message** — human or agent natural-language message.
2. **Runtime event** — machine-readable event from execution state.
3. **Agent run** — bounded run/session/workflow execution.
4. **Tool call** — a tool/action request or result.
5. **Approval request** — permission object awaiting decision.
6. **Approval decision** — operator response to a scoped request.
7. **Audit artifact** — immutable or append-only evidence/log output.
8. **Participant** — human, runtime, service, companion, or system actor.
9. **Thread** — scoped continuation/sub-room around work.
10. **Artifact reference** — file/log/screenshot/diff/output pointer.

The UI may render all of these in one timeline, but storage and authority must remain separate.

---

## 7. User experience target

### 7.1 Normal operator flow

The user sends:

```text
Hermes, inspect the current website launch scaffold and tell me what is left before we start coding.
```

ChaseOS should immediately show:

```text
Hermes saw this message.
Hermes queued runtime run.
Hermes loaded declared context.
Hermes read repo files.
Hermes found implementation blockers.
Hermes proposes next action.
```

If an action needs execution:

```text
Approval required:
Run static inspection command in repo root?
[Allow Once] [Allow Session] [Always Allow Scoped] [Deny]
```

If approved:

```text
Terminal command started.
Terminal command completed.
Audit artifact written.
Run summary ready.
```

### 7.2 What should appear in the timeline

The timeline should show a blend of:

- human messages
- agent messages
- agent acknowledgement chips
- event cards
- approval cards
- run summary cards
- artifact links
- error cards
- continuation proposals

### 7.3 What should not appear

Do not show:

- raw provider secrets
- OAuth tokens
- API keys
- hidden chain-of-thought
- full unredacted environment dumps
- unbounded terminal output by default
- raw private memory unless explicitly permitted
- direct credential values
- full file contents when a short diff/preview is enough

---

## 8. Runtime participants

### 8.1 Participant types

Suggested participant types:

| Type | Examples | Default authority |
|---|---|---|
| `human_operator` | Chase | Full only where logged-in and approved |
| `runtime_agent` | Hermes, OpenClaw, Codex | Adapter-specific, deny-by-default |
| `assistant_agent` | Claude/design, companion | Advisory unless explicitly bound |
| `system_service` | AOR, Gate, OSRIL, Agent Bus | Internal state only |
| `approval_gate` | Approval Center | Decision surface |
| `audit_writer` | Audit service | Append-only logs |
| `external_user` | enterprise shared user | Read-only/request-only by default |
| `webhook` | Discord/webhook bridge | Untrusted until classified |

### 8.2 Participant roles

Suggested roles:

| Role | Meaning |
|---|---|
| `viewer` | Can see permitted timeline content |
| `commenter` | Can send normal chat messages |
| `responder` | Can answer but not act |
| `planner` | Can propose actions/threads/tasks |
| `executor` | Can execute bounded actions through AOR/Gate |
| `approver` | Can approve scoped requests |
| `auditor` | Can read/write audit summaries |
| `owner` | Operator-level authority |

Presence in a chat does not automatically grant executor authority.

### 8.3 Participant status

UI should display:

- online/offline
- last seen
- current run state
- active workflow
- awaiting approval count
- blocked reason
- trust tier / authority ceiling
- current adapter lane

For companions, personality and avatar state must not imply authority.

---

## 9. Companion acknowledgement model

The Discord “eyes emoji” behavior is useful because it creates immediate feedback.

In ChaseOS, this should become a companion/agent acknowledgement layer:

```text
Hermes saw this.
OpenClaw queued this.
Codex is drafting.
AOR is waiting for approval.
Gate blocked this action.
Audit Writer saved evidence.
```

This can be visually gamified through companion avatars, but the backend meaning should be real.

### 9.1 Companion rule

Companion profile is display state only.

It must not grant:

- runtime dispatch authority
- protected-file access
- Agent Bus write authority
- provider-call authority
- canonical writeback authority
- memory mutation authority

### 9.2 Companion memory boundary

Companion memory can inform context only after:

- explicit approval
- raw/non-canonical classification
- bounded context packet generation
- future governed provider lane

No ambient memory injection.

---

## 10. Runtime event schema

### 10.1 Minimum RuntimeEvent fields

```yaml
RuntimeEvent:
  id: string
  schema_version: string
  event_type: string
  session_id: string
  thread_id: string | null
  run_id: string | null
  parent_event_id: string | null
  sequence: integer
  timestamp: string
  source:
    actor_id: string
    actor_type: string
    runtime_id: string | null
    adapter: string | null
  visibility:
    audience: string
    redaction_level: string
  severity: info | warning | error | critical
  status: pending | running | succeeded | failed | blocked | cancelled
  payload: object
  artifact_refs: array
  approval_ref: string | null
  audit_ref: string | null
  idempotency_key: string
```

### 10.2 Event type categories

#### Chat/session events

- `message.received`
- `message.classified`
- `agent.acknowledged`
- `agent.typing.started`
- `agent.typing.stopped`
- `session.created`
- `thread.created`
- `thread.proposed`
- `thread.closed`
- `participant.joined`
- `participant.left`
- `participant.role_changed`

#### Run lifecycle events

- `run.queued`
- `run.started`
- `run.stage_reached`
- `run.paused`
- `run.resume_ready`
- `run.resumed`
- `run.completed`
- `run.failed`
- `run.cancelled`

#### Context events

- `context.load.started`
- `context.loaded`
- `context.file_read`
- `context.provenance_attached`
- `context.redacted`
- `context.blocked`

#### Tool/action events

- `tool.proposed`
- `tool.called`
- `tool.completed`
- `tool.failed`
- `terminal.started`
- `terminal.output_chunk`
- `terminal.completed`
- `file.read`
- `file.write.proposed`
- `file.write.completed`
- `patch.proposed`
- `patch.applied`
- `browser.action.proposed`
- `browser.action.completed`
- `screenshot.captured`

#### Approval events

- `approval.requested`
- `approval.granted`
- `approval.denied`
- `approval.expired`
- `approval.consumed`
- `approval.cancelled`

#### Audit/artifact events

- `audit.artifact.created`
- `audit.writeback.completed`
- `artifact.linked`
- `handover.created`
- `summary.created`

#### Error/security events

- `policy.blocked`
- `permission.denied`
- `credential.redacted`
- `prompt_injection.flagged`
- `unknown_actor.blocked`
- `schema.invalid`
- `runtime.unhealthy`

### 10.3 Example event: acknowledgement

```json
{
  "id": "evt_01",
  "schema_version": "1.0",
  "event_type": "agent.acknowledged",
  "session_id": "chat_website_launch",
  "thread_id": null,
  "run_id": "run_123",
  "sequence": 3,
  "timestamp": "2026-06-01T18:00:00Z",
  "source": {
    "actor_id": "hermes",
    "actor_type": "runtime_agent",
    "runtime_id": "hermes_wsl",
    "adapter": "hermes"
  },
  "visibility": {
    "audience": "session_participants",
    "redaction_level": "safe_summary"
  },
  "severity": "info",
  "status": "succeeded",
  "payload": {
    "message": "Hermes saw this and queued a bounded repo-inspection run.",
    "ack_state": "queued"
  },
  "artifact_refs": [],
  "approval_ref": null,
  "audit_ref": null,
  "idempotency_key": "hermes:run_123:ack"
}
```

### 10.4 Example event: terminal command

```json
{
  "id": "evt_02",
  "schema_version": "1.0",
  "event_type": "terminal.completed",
  "session_id": "chat_website_launch",
  "thread_id": "thread_run_123",
  "run_id": "run_123",
  "sequence": 17,
  "timestamp": "2026-06-01T18:03:11Z",
  "source": {
    "actor_id": "codex",
    "actor_type": "runtime_agent",
    "runtime_id": "codex_repo_lane",
    "adapter": "codex"
  },
  "visibility": {
    "audience": "operator_only",
    "redaction_level": "stdout_preview"
  },
  "severity": "info",
  "status": "succeeded",
  "payload": {
    "cwd": "/repo/JOS_SQL",
    "command_preview": "python -m pytest tests/test_chat_events.py",
    "exit_code": 0,
    "duration_ms": 4210,
    "stdout_preview": "12 passed",
    "stderr_preview": ""
  },
  "artifact_refs": [
    {
      "type": "log",
      "path": "07_LOGS/Agent-Activity/2026-06-01-chat-event-test.md"
    }
  ],
  "approval_ref": "apr_789",
  "audit_ref": "audit_456",
  "idempotency_key": "codex:run_123:pytest:complete"
}
```

### 10.5 Example event: approval requested

```json
{
  "id": "evt_03",
  "schema_version": "1.0",
  "event_type": "approval.requested",
  "session_id": "chat_website_launch",
  "thread_id": "thread_run_123",
  "run_id": "run_123",
  "sequence": 9,
  "timestamp": "2026-06-01T18:02:00Z",
  "source": {
    "actor_id": "gate",
    "actor_type": "system_service",
    "runtime_id": null,
    "adapter": null
  },
  "visibility": {
    "audience": "operator_only",
    "redaction_level": "safe_summary"
  },
  "severity": "warning",
  "status": "pending",
  "payload": {
    "request_id": "apr_789",
    "target_adapter": "codex",
    "workflow_action": "terminal.execute",
    "risk_class": "medium",
    "exact_action_preview": "Run pytest for chat event tests in JOS_SQL repository.",
    "read_targets": ["tests/", "runtime/chat/"],
    "write_targets": [".pytest_cache/", "07_LOGS/Agent-Activity/"],
    "external_systems": [],
    "allowed_decisions": ["allow_once", "allow_session", "deny"],
    "expires_at": "2026-06-01T18:17:00Z"
  },
  "artifact_refs": [],
  "approval_ref": "apr_789",
  "audit_ref": null,
  "idempotency_key": "gate:apr_789:requested"
}
```

---

## 11. Persistence model

### 11.1 Suggested tables / models

This can be SQL, JSONL, or hybrid depending on repo state. For a prototype in JOS_SQL, SQL tables are appropriate.

#### `chat_sessions`

- `id`
- `workspace_id`
- `title`
- `mode`
- `created_by_actor_id`
- `created_at`
- `status`
- `default_visibility`

#### `chat_threads`

- `id`
- `session_id`
- `parent_thread_id`
- `parent_run_id`
- `thread_type`
- `title`
- `created_by_actor_id`
- `created_at`
- `status`

#### `chat_messages`

- `id`
- `session_id`
- `thread_id`
- `sender_actor_id`
- `sender_type`
- `content_markdown`
- `content_kind`
- `created_at`
- `visibility`
- `classification_state`

#### `runtime_runs`

- `id`
- `session_id`
- `thread_id`
- `runtime_id`
- `adapter`
- `workflow_id`
- `task_type`
- `status`
- `stage_reached`
- `approval_state`
- `started_at`
- `completed_at`
- `audit_ref`

#### `runtime_events`

- `id`
- `session_id`
- `thread_id`
- `run_id`
- `event_type`
- `sequence`
- `source_actor_id`
- `adapter`
- `severity`
- `status`
- `payload_json`
- `artifact_refs_json`
- `approval_ref`
- `audit_ref`
- `idempotency_key`
- `created_at`

#### `tool_calls`

- `id`
- `run_id`
- `event_id`
- `tool_name`
- `tool_family`
- `command_preview`
- `cwd`
- `status`
- `risk_class`
- `duration_ms`
- `stdout_preview`
- `stderr_preview`
- `artifact_ref`

#### `approval_requests`

- `id`
- `session_id`
- `thread_id`
- `run_id`
- `requesting_actor_id`
- `target_adapter`
- `workflow_action`
- `exact_action_json`
- `read_targets_json`
- `write_targets_json`
- `external_systems_json`
- `risk_class`
- `scope`
- `status`
- `expires_at`
- `created_at`

#### `approval_decisions`

- `id`
- `approval_request_id`
- `decided_by_actor_id`
- `decision`
- `scope`
- `operator_statement`
- `decision_digest`
- `created_at`

#### `audit_artifacts`

- `id`
- `run_id`
- `artifact_type`
- `path`
- `sha256`
- `created_by_actor_id`
- `created_at`
- `summary`

#### `chat_participants`

- `id`
- `session_id`
- `actor_id`
- `actor_type`
- `display_name`
- `role`
- `trust_tier`
- `authority_ceiling`
- `joined_at`
- `status`

#### `adapter_permissions`

- `id`
- `runtime_id`
- `adapter`
- `task_family`
- `read_scope_json`
- `write_scope_json`
- `tool_scope_json`
- `requires_approval`
- `trust_ceiling`
- `status`

### 11.2 JSONL fallback option

If repo state makes SQL premature, start with append-only JSONL:

```text
runtime/chat/events/{session_id}.jsonl
runtime/chat/runs/{run_id}.json
runtime/chat/approvals/{approval_id}.json
runtime/chat/threads/{thread_id}.json
```

This is acceptable for the first proof, but the schema should still be written as if SQL persistence will come later.

---

## 12. UI card layer

### 12.1 Required card types

#### Agent acknowledgement card

Shows:

- agent/runtime
- ack state
- timestamp
- run id if known

Example:

```text
Hermes saw this and queued a bounded runtime run.
```

#### Tool call card

Shows:

- tool name
- adapter
- status
- risk class
- short summary
- artifact link

#### Terminal card

Shows:

- command preview
- working directory
- approval status
- exit code
- duration
- stdout/stderr preview
- full log link

#### File read/write card

Shows:

- file path
- action: read / proposed write / applied write
- diff preview if write
- risk class
- approval ref

#### Patch card

Shows:

- files touched
- summary
- diff preview
- tests linked
- approval status

#### Browser/screenshot card

Shows:

- target URL or page title
- action type
- screenshot thumbnail if allowed
- DOM/visual evidence ref

#### Approval card

Shows:

- request id
- adapter
- workflow/action
- risk class
- exact action
- read/write targets
- scope
- expiry
- buttons

Buttons:

- Allow Once
- Allow Session
- Always Allow Scoped
- Deny

`Always Allow Scoped` must never become broad unlimited authority.

#### Audit writeback card

Shows:

- artifact type
- path
- created by
- run id
- link/open action

#### Run summary card

Shows:

- status
- runtime
- workflow
- duration
- stages reached
- outputs
- open loops
- next action

#### Error/security card

Shows:

- error class
- severity
- failed event id
- safe summary
- retry option if safe
- escalation note

### 12.2 Card style rule

Cards must make the control-plane meaning obvious:

- information cards are neutral
- approval cards are visibly distinct
- blocked/security cards are high-signal
- audit cards are traceable
- raw logs are collapsed by default

### 12.3 Timeline grouping

Group related events into collapsible run sections:

```text
Run: Hermes repo-inspection #run_123
  ✓ acknowledged
  ✓ context loaded
  ✓ file reads
  ⚠ approval requested
  ✓ terminal completed
  ✓ audit written
  ✓ summary created
```

---

## 13. Live streaming behavior

### 13.1 Transport options

Preferred first implementation:

- Server-Sent Events for simple one-way stream from backend to UI

Alternative:

- WebSocket for bidirectional runtime stream

For MVP, SSE is usually enough if the user sends messages through normal HTTP and events stream back.

### 13.2 Requirements

- Events must be ordered by `sequence` inside a run.
- Events must be idempotent by `idempotency_key`.
- UI must tolerate reconnects.
- UI must replay recent events after reconnect.
- Backend must persist before broadcasting when possible.
- Event payloads must be redacted before UI emission.
- Long stdout/stderr should be chunked or collapsed.
- Event stream must not leak secret-bearing payloads.

### 13.3 Reconnect behavior

On reconnect:

1. UI requests events since last `sequence` / timestamp.
2. Backend returns missed events.
3. Live stream resumes.
4. Duplicate events are ignored by idempotency key.

---

## 14. Approval model

### 14.1 Approval principles

Approvals must be:

- scoped
- auditable
- digest-bound
- expiring
- tied to actor/runtime/action
- tied to exact targets
- consumed exactly once when appropriate
- impossible to grant by emoji or ambiguous chat reply

Current implementation note, 2026-06-02: `record_approval_consumption(...)`
supports exact-once consumption only for an existing Chat approval request with a
recorded allow decision and explicit OSRIL approval id. It validates OSRIL
response/application state, workflow/runtime/session linkage, denial/reuse
guards, records the OSRIL resume marker, writes a Chat approval-consumption
sidecar, and emits `approval.consumed`. It does not run AOR, shell, browser,
provider, connector, or canonical writeback work.

### 14.2 Approval scopes

| Scope | Meaning |
|---|---|
| `allow_once` | One exact action / one run / one target set |
| `allow_session` | Same action family within current session and declared targets |
| `allow_thread` | Same bounded action family inside one thread |
| `always_allow_scoped` | Long-lived only for exact low-risk action class and target pattern |
| `deny` | Reject request |

### 14.3 Always Allow rule

`Always Allow` must never mean broad authority.

It must include:

- allowed adapter
- allowed workflow/action
- allowed target pattern
- allowed risk ceiling
- expiry/review interval
- audit requirement
- revocation path

### 14.4 Approval object requirements

Every approval request must include:

- request id
- source session/thread
- requesting actor
- target adapter/runtime
- workflow/action
- exact command/action
- input summary
- read targets
- write targets
- external systems
- risk class
- proposed scope
- expiry
- expected audit destination
- digest of decision packet

### 14.5 Approval UI should support

- expand/collapse full details
- copy request id
- open audit destination
- open related run thread
- deny with reason
- allow with typed operator statement for high-risk actions

---

## 15. Thread model

### 15.1 Required thread types

| Thread type | Purpose |
|---|---|
| `task_thread` | Work around a user task |
| `run_thread` | Timeline for one runtime run |
| `approval_thread` | Approval discussion + decision record |
| `debug_thread` | Error/retry/debug detail |
| `audit_thread` | Audit writeback and evidence review |
| `continuation_thread` | New room after compaction/context split |
| `shared_room` | Multi-agent / multi-user collaboration room |

### 15.2 Thread creation rules

Agents may propose threads.

Agents may not silently create new shared rooms unless the room policy allows it.

Default:

- run threads can auto-create for each runtime run
- approval threads can auto-create when approval requested
- continuation threads require operator confirmation if they change participants or scope
- shared rooms require operator action

### 15.3 Continuation behavior

When context compaction or handoff is needed, Chat should offer:

```text
Create continuation thread from this run?
Includes: summary, open loops, artifacts, current approvals, next action.
```

The continuation packet must include:

- source session
- source run/thread
- summary
- assumptions
- unresolved ambiguity
- artifacts
- approvals consumed/pending
- next recommended action
- authority ceiling

---

## 16. Multi-agent room model

### 16.1 Example room

```text
Room: Website Launch Final Features
Participants:
- Chase / operator
- Hermes / runtime planner
- Codex / repo implementation
- OpenClaw / governed execution lane
- Gate / approval service
- Audit Writer / evidence
- Companion / status layer
```

### 16.2 Default authority split

| Actor | Can read? | Can speak? | Can execute? | Needs approval? |
|---|---:|---:|---:|---:|
| Human operator | yes | yes | via UI | depends on action |
| Hermes | declared scope only | yes | bounded workflows only | yes for expansion |
| OpenClaw | declared scope only | yes | bounded runtime actions | yes for high risk |
| Codex | repo scope only | yes | code/test path | yes for writes/commands |
| Companion | status/context only | yes | no | n/a |
| External user | room policy only | yes/request | no by default | yes |

### 16.3 Agent-to-agent coordination

Agents can coordinate through the room only if:

- each agent is registered
- each agent has a role
- each agent has a trust ceiling
- each agent’s adapter permissions are known
- tool/action requests are routed through the same approval path

Do not let agents create hidden off-channel delegation that bypasses audit.

### 16.4 Mentioning agents

Mentioning an agent should not automatically execute actions.

A mention can produce:

- notification
- proposed task
- request for agent response
- request for operator approval if external/other-user agent

---

## 17. Cross-user / enterprise sharing model

This should not be implemented in the first pass, but the architecture must not block it.

### 17.1 Core rule

Joining a shared chat does not grant permission to command another user’s agent.

### 17.2 Permission levels

| Level | Meaning |
|---|---|
| Level 0 — no access | User/agent cannot see room |
| Level 1 — visible only | Can see permitted content |
| Level 2 — comment | Can speak in room |
| Level 3 — request agent contact | Can request that another user’s agent read/respond |
| Level 4 — shared workflow proposal | Can propose bounded workflow for approval |
| Level 5 — shared execution | Can trigger predefined workflows under explicit policy |

Default for external users:

- no direct access to another user’s agent
- no tool access
- no credential access
- no canonical writeback
- no memory import
- no cross-room context

### 17.3 Request-to-message model

If User B wants to message User A’s agent:

1. User B writes a request.
2. ChaseOS creates `external_agent_message_request`.
3. User A sees approval card.
4. User A approves/denies.
5. Only approved message is delivered to User A’s agent.
6. Agent response visibility follows the approved scope.

### 17.4 External-user prompt-injection rule

All external user text is Tier 4 untrusted input unless explicitly promoted or approved.

It can be shown in chat, but it cannot become system instruction.

---

## 18. Security and governance

### 18.1 Main risks

This feature introduces risk because it brings high-privilege runtime activity into a natural-language interface.

Risks:

- prompt injection from chat
- privilege aggregation
- trust boundary collapse
- hidden credential leakage
- overbroad approvals
- untrusted users commanding agents
- Discord/webhook transport treated as authority
- raw logs leaking secrets
- agents creating untracked threads/tasks
- hidden cross-runtime delegation
- chain-of-thought leakage
- uncontrolled file writes
- external connector calls without approval

### 18.2 Non-negotiable security rules

1. Chat input is data, not instruction authority.
2. Unknown actors are denied by default.
3. External users cannot command local runtimes by default.
4. Runtime event payloads must be redacted before display.
5. Approval must be scoped and audited.
6. Secrets must never be rendered.
7. Hidden model reasoning must never be displayed.
8. Canonical writes still go through Gate/service layer.
9. Runtime dispatch still goes through AOR/Agent Bus.
10. Discord/webhooks remain transport, not authority.
11. Companion personality never grants authority.
12. Always Allow must be scoped and revocable.

### 18.3 Prompt-injection handling

Any message from:

- Discord
- webhooks
- external users
- documents
- browser pages
- emails
- raw logs
- generated artifacts
- companion memory

must be treated as untrusted input by default.

The UI can display it. The runtime cannot treat it as policy.

### 18.4 Redaction requirements

The event bridge must redact:

- API keys
- OAuth tokens
- bearer tokens
- cookies
- session IDs
- passwords
- seed phrases
- private keys
- database URLs
- `.env` values
- authorization headers
- raw provider request payloads where secrets may appear

### 18.5 No hidden chain-of-thought

The timeline should show:

- action summaries
- decisions at summary level
- tool calls
- commands
- diffs
- outputs
- audit references
- explicit assumptions
- open loops

The timeline should not show private hidden reasoning.

Use `reason_summary`, not raw reasoning.

---

## 19. Hermes event bridge

### 19.1 Purpose

Hermes should emit structured runtime events that ChaseOS Chat can render.

### 19.2 Safe emission points

Potential emission points:

- message received
- adapter run started
- context read started/completed
- tool proposed
- tool started/completed
- approval requested
- draft artifact written
- audit artifact written
- run completed/failed

### 19.3 Hermes bridge options

Preferred implementation order:

1. **JSONL file bridge** — Hermes writes structured events to a watched file/path.
2. **Agent Bus bridge** — Hermes publishes events to Agent Bus.
3. **Direct event API** — Hermes POSTs events to ChaseOS service.
4. **WebSocket/SSE bridge** — later only if needed.

For first implementation, JSONL is often safest because it avoids network authority expansion.

**Current repo truth as of 2026-06-02:** the JSONL spool bridge, rotated
per-adapter spool support, cursor poller, local-only SSE card stream, and Studio
Runtime Control Daemon lifecycle wrapper are implemented. SSE is loopback-only
delivery of validated ActivityCards, not public network authority and not an
execution channel. Remaining Hermes work is parity and breadth of live event
coverage, not existence of the local SSE/spool/lifecycle substrate.

Example path:

```text
runtime/events/hermes/{run_id}.jsonl
```

or:

```text
07_LOGS/Agent-Activity/hermes-events/{date}-{run_id}.jsonl
```

### 19.4 Hermes redaction contract

Hermes must not emit:

- raw provider payloads containing secrets
- hidden chain-of-thought
- credential values
- unbounded terminal output
- private memory outside declared scope

### 19.5 Hermes first supported events

Minimum first bridge:

- `run.started`
- `agent.acknowledged`
- `context.file_read`
- `tool.called` or `file.read`
- `audit.artifact.created`
- `run.completed`
- `run.failed`

### 19.6 Hermes non-goals in first pass

Do not add:

- broader workflow authority
- shell execution
- connector authority
- multi-repo authority
- persistent memory authority
- canonical write authority
- direct Discord execution

The bridge is observability first.

---

## 20. OpenClaw event bridge

### 20.1 Purpose

OpenClaw should emit structured events for actions currently visible in Discord.

### 20.2 High-risk surfaces

OpenClaw can touch:

- local files
- shell execution
- browser actions
- SaaS integrations
- chat platforms
- credentials/config

Therefore OpenClaw event rendering must be especially careful.

### 20.3 Minimum events

- `run.started`
- `agent.acknowledged`
- `tool.proposed`
- `terminal.started`
- `terminal.completed`
- `file.read`
- `file.write.proposed`
- `approval.requested`
- `approval.consumed`
- `audit.artifact.created`
- `run.completed`

### 20.4 OpenClaw non-goals in first pass

Do not broaden OpenClaw authority just to display events.

The event bridge must be read/emit only.

---

## 21. Codex / repo-aware implementation lane

Codex should own the initial repo implementation because this feature needs real file inspection.

### 21.1 Codex should inspect

- existing Chat frontend files
- Studio service layer
- OSRIL event/session files
- Agent Bus files
- AOR engine/run events
- approval queue files
- audit/log writer files
- runtime adapter surfaces
- existing tests
- database/storage layer if present

### 21.2 Codex should implement first

- schema/types for `RuntimeEvent`
- persistence or JSONL store
- simple backend event stream endpoint
- minimal UI cards
- dummy/test runtime event emitter
- tests
- no broad runtime authority changes

### 21.3 Codex should not implement first

- enterprise sharing
- direct Discord API actions
- cross-user agent control
- provider execution expansion
- new shell permissions
- new connector powers
- unapproved memory writes

---

## 22. Prototype scope: JOS_SQL repository first

The user specifically wants this to be prototyped first with the JOS_SQL repository.

### 22.1 Why prototype in JOS_SQL

JOS_SQL is an appropriate first prototype if it provides:

- a bounded repo surface
- lower blast radius than core ChaseOS
- SQL/database patterns for persistence
- a clean test bed for chat event tables
- a place to prove event schema and UI behavior before integrating into ChaseOS core

### 22.2 Prototype target

Build the smallest working proof:

```text
User sends message in local chat
→ test runtime emits events
→ backend stores events
→ UI streams and renders cards
→ approval card can be created/resolved
→ audit record written
```

### 22.3 Prototype constraints

Do not include:

- cross-user sharing
- real Hermes authority expansion
- OpenClaw shell actions
- production Discord integration
- external connectors
- canonical ChaseOS writeback
- provider/model secrets

### 22.4 JOS_SQL suggested tables

If using SQL:

- `chat_sessions`
- `chat_messages`
- `runtime_runs`
- `runtime_events`
- `approval_requests`
- `approval_decisions`
- `audit_artifacts`
- `participants`

### 22.5 JOS_SQL success criteria

Prototype passes when:

1. At least one session can be created.
2. User message persists.
3. Dummy runtime run starts.
4. Runtime emits at least five typed events.
5. UI receives events live.
6. Approval card appears from event stream.
7. Approval decision persists.
8. Run summary card appears.
9. Audit artifact record is created.
10. Event replay works after refresh.

---

## 23. Implementation phases

### Phase A — Documentation / repo-truth audit

Goal:

- locate existing Chat architecture
- locate runtime event surfaces
- confirm whether OSRIL/Agent Bus already solves part of this
- avoid duplicate architecture

Outputs:

- repo audit summary
- exact files to modify
- implementation plan
- updated version of this doc if repo truth differs

### Phase B — Event schema and persistence

Goal:

- define RuntimeEvent model
- define run/thread/message/approval models
- implement storage or JSONL equivalent

Outputs:

- schema/types
- validation
- tests

### Phase C — Event stream backend

Goal:

- expose SSE/WebSocket stream
- support replay after reconnect
- support safe redaction

Outputs:

- event publish endpoint or service
- event subscribe endpoint
- test emitter

### Phase D — UI card renderer

Goal:

- render event timeline cards in Chat page
- support grouped runs
- support collapsed stdout/logs

Outputs:

- card components
- timeline grouping
- loading/error states

### Phase E — Approval card foundation

Goal:

- create approval requests from event stream
- decision writes are scoped/auditable

Outputs:

- approval UI
- approval backend
- decision audit

### Phase F — Hermes bridge

Goal:

- Hermes emits safe structured events
- ChaseOS Chat renders them

Outputs:

- JSONL or bus bridge
- redaction
- tests

### Phase G — OpenClaw bridge

Goal:

- OpenClaw emits structured events
- ChaseOS Chat renders actions similar to Discord

Outputs:

- adapter bridge
- approval integration
- tests

### Phase H — Thread model

Goal:

- run threads
- approval threads
- continuation threads

Outputs:

- thread schema
- thread UI
- thread creation policy

### Phase I — Multi-agent rooms

Goal:

- multiple runtime participants in one session
- permissions enforced per participant

Outputs:

- participant manager
- role/permission UI
- agent mention policy

### Phase J — Enterprise sharing / cross-user model

Goal:

- shared chats
- external agent message requests
- approval gates for cross-user agent access

This is future scope. Do not start here.

---

## 24. Acceptance criteria

### 24.1 MVP acceptance criteria

The first real pass is successful only if:

1. Chat message and runtime event are separate record types.
2. Runtime events are typed, persisted, and replayable.
3. UI renders at least acknowledgement, tool, terminal/file, approval, audit, summary, and error cards.
4. Approval card creates a scoped approval object.
5. Approval decision is recorded separately.
6. No secret values are displayed.
7. No hidden chain-of-thought is displayed.
8. Event stream survives refresh/reconnect.
9. At least one dummy or safe runtime emits events live.
10. Tests exist for schema validation and UI rendering.

### 24.2 Hermes acceptance criteria

Hermes bridge is successful only if:

1. Hermes emits safe structured events.
2. Events render in ChaseOS Chat.
3. Read/write/tool actions are redacted and summarized.
4. Audit artifacts are linked.
5. No new Hermes authority is granted.
6. Malformed events fail closed.
7. Hidden reasoning is excluded.
8. Secrets are excluded.

### 24.3 OpenClaw acceptance criteria

OpenClaw bridge is successful only if:

1. OpenClaw emits structured events for existing actions.
2. Terminal/file/browser/tool events render as cards.
3. Approvals map to scoped approval objects.
4. High-risk activity is not silently allowed.
5. Secrets and credentials are redacted.
6. Event bridge does not widen OpenClaw permissions.

### 24.4 Multi-agent acceptance criteria

Multi-agent room is successful only if:

1. Participants have explicit roles.
2. Authority is not inferred from presence.
3. Agent mentions do not auto-execute actions.
4. Each runtime keeps its own adapter boundary.
5. Cross-agent delegation is visible and audited.

---

## 25. Failure modes to test

### 25.1 Event failure modes

- duplicate event id
- duplicate idempotency key
- out-of-order event
- malformed payload
- unknown event type
- missing run id where required
- oversized stdout
- event with secret-looking content
- redaction failure
- reconnect replay gap

### 25.2 Approval failure modes

- expired approval
- reused approval
- approval for wrong run
- approval for wrong target
- approval with broadened target set
- ambiguous chat reply treated as approval
- external user attempting approval
- missing audit destination

### 25.3 Security failure modes

- prompt injection in chat
- prompt injection in file output
- malicious terminal output
- untrusted Discord/webhook message
- external user asks another user’s agent to reveal data
- agent attempts to write protected file
- companion memory tries to become instruction
- raw log includes token

### 25.4 Runtime failure modes

- Hermes offline
- OpenClaw offline
- Codex run fails
- Agent Bus unavailable
- AOR run blocked
- Gate denies action
- audit writeback fails
- provider rate limit

---

## 26. Repo file targets to inspect

Claude/Codex should inspect these if present. Exact paths may differ.

### 26.1 Core docs

- `README.md`
- `PROJECT_FOUNDATION.md`
- `ROADMAP.md`
- `00_HOME/Now.md`
- `CLAUDE.md`
- `HERMES.md`
- `OPENCLAW.md`

### 26.2 Agent/governance docs

- `06_AGENTS/Agent-Control-Plane.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Trust-Tiers.md`
- `06_AGENTS/Agent-Security-Model.md`
- `06_AGENTS/ChaseOS-Gate.md`
- `06_AGENTS/Autonomous-Operator-Runtime.md`
- `06_AGENTS/Execution-Adapter-Standard.md`
- `06_AGENTS/Handoff-Protocol.md`
- `04_SOPS/Agent-Failure-Ambiguity-SOP.md`

### 26.3 Discord/runtime docs

- `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
- `06_AGENTS/Discord-Identity-Map.md`
- `06_AGENTS/Discord-Channel-Registry.md`
- `06_AGENTS/Discord-Command-Envelope-Schema.md`
- `06_AGENTS/OpenClaw-Discord-Activation-Preflight.md`
- `06_AGENTS/Hermes-Adapter-Spec.md`
- `06_AGENTS/Hermes-Workflow-Boundaries.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`
- `06_AGENTS/Hermes-Operations-Runbook.md`

### 26.4 Studio / Chat docs

- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`
- `06_AGENTS/Studio-Product-UI-Feature-Family-Normalization.md`
- any `Studio Chat` architecture/docs
- any `Chat authority` docs
- any `Companion` docs

### 26.5 Runtime code

- `runtime/aor/engine.py`
- `runtime/aor/registry.py`
- `runtime/aor/task_router.py`
- `runtime/aor/role_cards.py`
- `runtime/aor/runtime_registry/`
- `runtime/osril/`
- `runtime/agent_bus/`
- `runtime/studio/`
- `runtime/studio/service.py`
- `runtime/studio/chat/`
- `runtime/memory/`
- `runtime/workflows/registry/`

### 26.6 Existing approval/audit code

- approval queue modules
- Gate modules
- audit writer modules
- build log writer modules
- Agent Activity logs
- OSRIL approvals/wait-resume modules

### 26.7 Existing frontend files

Find:

- Chat page component
- Runtime Chats component
- Hermes Chat page
- message renderer
- card components
- Studio shell routing
- panel registry
- API client
- state store

---

## 27. Feature-register / R&D row suggestion

If this feature is added to R&D tracking, recommended row:

```text
Feature Name: Native Runtime Chat Control Plane
Layer / Subsystem: Studio Chat + OSRIL + AOR Runtime Visibility
Status: Planned / Architecture canonical-candidate
Priority: P0 / P1 depending on active Chat roadmap
Summary: Turns ChaseOS Chat into the native runtime control surface for live agent acknowledgements, runtime event cards, approval cards, audit links, continuation threads, and multi-agent rooms. Replaces Discord as the required operator surface while preserving Discord as optional transport.
Dependencies: Studio Chat, OSRIL event substrate, Agent Bus, AOR, Gate, Permission Matrix, runtime registry, Hermes/OpenClaw adapter boundaries, audit writeback.
Guardrails: No raw log dumping, no hidden reasoning, no secret display, no runtime authority expansion, no bypass of Gate, all approvals scoped and auditable, external users request-only by default.
Prototype Target: JOS_SQL repository first; then ChaseOS core integration.
```

---

## 28. Design notes for Claude

Claude/design should focus on:

- card hierarchy
- visual density
- run grouping
- approval UX
- participant UX
- thread UX
- companion acknowledgement UX
- empty states
- loading states
- error states
- copy examples
- state diagrams

Claude should not decide authority.

Authority comes from:

- Gate
- Permission Matrix
- Trust Tiers
- Runtime Registry
- AOR manifests
- approval objects

---

## 29. Implementation notes for Codex

Codex should focus on:

1. repo audit
2. event schema
3. storage layer
4. backend stream
5. UI rendering
6. approval card foundation
7. test emitter
8. tests
9. writeback docs/logs

Codex should preserve existing architecture and avoid broad refactors.

---

## 30. Implementation notes for Hermes

Hermes should focus on:

1. finding where its runtime activity is currently logged
2. mapping those points to RuntimeEvent types
3. adding a safe event emission bridge
4. redacting secrets
5. excluding hidden reasoning
6. emitting only safe summaries
7. proving with tests

Hermes should not expand its own authority during the observability bridge pass.

---

## 31. Relationship to Discord

Discord becomes optional transport.

ChaseOS Chat becomes native control plane.

Discord messages should eventually be:

```text
Discord transport event
→ identity map
→ channel registry
→ command envelope
→ ChaseOS policy
→ Agent Bus/AOR
→ RuntimeEvent
→ ChaseOS Chat timeline
```

That means Discord-origin work can still appear in ChaseOS Chat as a first-class timeline item.

But Discord should not remain the only place where the operator can see runtime activity.

---

## 32. Relationship to approvals in Discord

Discord approval cards are a good reference for ease of use, but ChaseOS must make approvals stronger.

ChaseOS approval card must:

- bind to exact request
- bind to exact action
- bind to exact target set
- write approval decision
- create audit trail
- be consumed safely

Do not rely on Discord reactions.

---

## 33. Relationship to Studio graph

Runtime events should eventually be graph-visible:

- `touched-by-agent`
- `used-by-workflow`
- `output-of-runtime`
- `blocked-by-policy`
- `pending-approval`
- `linked-to-audit-log`

Chat does not replace graph. Chat and graph show different views of the same runtime truth.

---

## 34. Relationship to property repair / metadata repair

The user mentioned doing property repair alongside this work.

This feature should be compatible with a future property/metadata repair lane, but that lane should not be bundled into the first Runtime Chat pass unless repo truth shows it is already part of Chat architecture.

Possible future connection:

- runtime event cards can show metadata repair proposals
- approval cards can approve property repair operations
- audit artifacts can link repaired frontmatter/property changes
- property repair runs can create dedicated run threads

Do not combine first-pass event-stream implementation with broad metadata repair unless required.

---

## 35. Open questions for repo audit

Claude/Codex should answer these before implementation:

1. Where is the current Chat page implemented?
2. Is there already a `runtime/studio/chat/` backend?
3. Does OSRIL already have event/session tables or JSONL files?
4. Does Agent Bus already support live event streams?
5. Is there an existing approval queue UI?
6. Are Studio card components already reusable?
7. Is there a service layer route for runtime dispatch?
8. Are there existing runtime event types?
9. What persistence model is already used: SQL, JSONL, filesystem, mixed?
10. Can JOS_SQL prototype this independently?
11. Where should RuntimeEvent schema live?
12. Where should Chat-specific UI cards live?
13. How does Hermes currently log tool calls?
14. How does OpenClaw currently emit Discord logs?
15. What is the safest first dummy runtime event source?

---

## 36. Do-not-build list for first pass

Do not build these in the first pass:

- enterprise sharing
- cross-user agent messaging
- direct Discord actions
- real external webhook execution
- new provider secret handling
- broad runtime shell authority
- browser automation expansion
- Home Assistant
- MCP expansion
- canonical memory promotion
- companion autonomous actions
- multi-repo execution
- unrestricted terminal access
- broad UI redesign
- new standalone datastore
- hidden chain-of-thought display

---

## 37. First-pass deliverable checklist

A good first implementation pass should produce:

- `RuntimeEvent` schema
- minimal persistence or JSONL store
- event validation
- backend event stream
- test event emitter
- Chat UI card renderer
- approval request card foundation
- run summary card
- audit link card
- tests
- build log
- archive note
- index updates
- updated Feature/Fit register row if appropriate

---

## 38. Suggested markdown file placement

Place this file at:

```text
06_AGENTS/Native-Runtime-Chat-Control-Plane.md
```

Potential related future docs:

```text
06_AGENTS/Native-Runtime-Chat-Event-Schema.md
06_AGENTS/Native-Runtime-Chat-Approval-Model.md
06_AGENTS/Native-Runtime-Chat-Thread-Model.md
06_AGENTS/Hermes-Runtime-Event-Bridge.md
06_AGENTS/OpenClaw-Runtime-Event-Bridge.md
06_AGENTS/Studio-Chat-Runtime-Control-Implementation-Tracker.md
```

Only create separate docs if this file becomes too large or implementation needs formal decomposition.

---

## 39. Final framing

The end state is simple:

Discord currently works because it gives runtime visibility.

ChaseOS Chat must become better because it gives runtime visibility plus governance.

When this feature is complete, ChaseOS Chat should be the place where the operator can:

- talk to agents
- see what they are doing
- approve/deny actions
- inspect artifacts
- follow live runs
- split work into threads
- coordinate multiple runtimes
- keep auditability intact
- reduce reliance on Discord

The correct design is not “logs inside chat.”

The correct design is:

> **A structured, governed runtime event stream rendered as a native operator chat timeline.**

---

## 40. Immediate next action after saving this file

After this file is placed in `06_AGENTS/`, run a repo-aware audit pass.

That pass should not implement yet unless the implementation path is obvious.

It should first answer:

- what currently exists
- what files own Chat
- what files own OSRIL/Agent Bus events
- what persistence model exists
- what the smallest safe implementation path is
- whether JOS_SQL should prototype first or whether ChaseOS already has the substrate

Then run the implementation prompt.

---

## 41. Implementation trace

- 2026-06-01: First ChaseOS core foothold implemented in Studio Chat as PARTIAL / FOOTHOLD IMPLEMENTED / VERIFIED. The pass added `RuntimeEvent` schema validation, JSONL persistence, polling API exposure, Chat timeline event cards, scoped approval-decision records, participant/run/thread/audit sidecars, and tests. See build log `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-control-plane-foothold.md` and documentation history `99_ARCHIVE/Documentation-History/2026-06-01_native-runtime-chat-control-plane-foothold.md`. Not implemented in this pass: WebSocket/SSE, live Hermes/OpenClaw event bridges, approval consumption, packaged visual QA, or authority expansion.
- 2026-06-01: OpenClaw live wiring. `openclaw_watch._run_one_cycle` now emits
  visibility events (`agent.acknowledged` + `run.started` on claim, `run.completed`
  on success, `run.failed` on no-handler/exception) plus one hidden
  `runtime.heartbeat` per non-dry cycle for idle liveness — mirroring Hermes and
  reusing `emit_runtime_event` (no contract/emitter/spool duplication).
  `activity_cards` gained a noise filter (`runtime.heartbeat`/`agent.typing` hidden
  from the default timeline per §6.3; they still update presence/health).
  `runtime.heartbeat` added to `openclaw.yaml` + `hermes.yaml` allowed_event_types.
  Both live runtimes (Hermes + OpenClaw) now feed the activity bridge end-to-end,
  visibility-only. See build log
  `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-openclaw-live-wiring.md`.
- 2026-06-01: Deferred backlog implemented in full. Event signing (`event_signing.py`,
  stdlib HMAC, opt-in emitter `sign=True`, importer records `signature_status`); Hermes
  self-check + smoke (`bridge_smoke.py`, `chaseos runtime-events check|smoke`); OpenClaw
  bridge-status honesty (`runtime_event_health` `bridge_status`:
  docs-only/active-unverified/active-observed/active-verified-event-bridge); golden
  fixtures (`runtime/tests/fixtures/runtime_events/`) + 300-case fuzz invariant; spool
  rotation/retention (`spool_layout.py`, emitter `rotate=True`, `poll_all_spools`); poll
  cadence loop (`poll_loop.py`, `chaseos studio chat-poll-loop`); local-only SSE
  (`sse_server.py`, 127.0.0.1 + token + GET-only, streams validated ActivityCards); live
  Hermes emit verified end-to-end (interop fix: importer hidden-reasoning check switched
  to exact-key match so the benign `chain_of_thought_policy` field no longer false-rejects
  Hermes events); frontend Runtime Activity surface (`runtime_activity.js` + chat-panel
  container + CSS: presence + grouped cards + Normal/Private/Debug + decisions-only + poll
  timer). Excluded: chaseos-core sanitization (operator-deferred). See build log
  `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-deferred-backlog-pass.md`.
- 2026-06-01: Core-readiness layer implemented (Hermes addendum). New
  `runtime/studio/chat/activity_cards.py` (RuntimeEvent → ActivityCard DTO:
  human-readable title/body, run grouping, claim-vs-verified, path classification,
  injection-risk marking, payload caps + truncation metadata, Normal/Private/Debug
  modes, why-blocked, display-only approval scope, action-required filter) and
  `runtime/studio/chat/runtime_event_health.py` (per-adapter health files + presence
  cards: live/degraded/stale/configured/template + bridge rollup). Studio API gained
  `get_chat_activity_cards` + `get_runtime_event_health`. Health updates wired into
  the importer (imported/rejected). Addendum items already shipped earlier: cursor
  importer, dead-letter queue, local-polling-over-validated-state. Formerly design-only
  backlog (§46) later shipped as local-only SSE delivery of validated cards plus
  spool rotation/retention. Crash-recovery
  + load tests added. See build log
  `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-core-readiness-pass.md`.
- 2026-06-01: Emitting side (Option A) implemented. New `runtime/studio/chat/runtime_event_emitter.py` (`RuntimeEventEmitter`): atomic JSONL append to the durable spool, per-adapter monotonic `adapter_sequence`, `event_hash`/`previous_event_hash` tamper-evidence chain, redaction-at-source, `runtime-adapter-event.v1` envelope, full convenience vocabulary incl. `runtime.heartbeat` (added to the allowlist). `RuntimeAdapterBridge` gained `sink="store"|"spool"` (`open_bridge(..., sink="spool")`) so the templated bridge can emit to the spool for the poller to ingest (store sink unchanged; one sink per run → no double-ingest). Importer now performs authority normalization (`runtime_claimed_authority` preserved vs `chaseos_effective_authority` always visibility-only) + `source_confidence: runtime_claim` + adapter sequence/hash traceability. Malformed lines are dead-lettered to `07_LOGS/Runtime-Events/dead-letter-events.jsonl` (secrets redacted, never silently dropped, never re-ingested). Broader Hermes north-star (per-adapter cursors, health/status panel, watcher/SSE transport, injection classifier/path policy/signing, product UI, run summaries/rotation, fuzz/load/crash suites, Core DTOs) recorded as sequenced backlog. See build log `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-emitting-side-pass.md`.
- 2026-06-01: Adapter ingestion pass implemented. Wired the pre-existing spool importer into a usable surface: `StudioAPI.import_chat_runtime_adapter_events(limit)` + `chaseos studio chat-import-adapter-events` CLI (safe stats + event refs); `get_chat_runtime_events` now imports-before-read (fail-open) and reports an `adapter_import` block; new Studio/Core-owned local cursor poller `runtime/studio/chat/adapter_event_poller.py` (only-new via byte-offset cursor, partial-line safe, truncation reset, no network/Discord/listener); importer dedup moved off the O(n) scan onto an indexed `source_event_id` (`ChatEventStore.has_source_event`, additive migration); denial tests prove `terminal.started`/connector events stay visibility-only with no reachable execution path. See build log `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-adapter-ingestion-pass.md`.
- 2026-06-01: Reliability pass implemented (transport debt + persistence + redaction-at-source + templated adapter bridge). Pluggable `ChatEventStore` added under `runtime/studio/chat/event_store/` (ABC + SQLite default + JSONL fallback + config loader), mirroring the Agent Bus Backend Abstraction Layer. `phase11_chat_runtime_events.append_runtime_event` / `list_runtime_events` now delegate to the store with stable signatures. Redaction-at-source added at `runtime/studio/chat/redaction.py`. Templated `RuntimeAdapterBridge` + registry added at `runtime/studio/chat/adapter_bridge.py`. See build log `07_LOGS/Build-Logs/2026-06-01-ChaseOS-native-runtime-chat-control-plane-reliability-pass.md` and documentation history `99_ARCHIVE/Documentation-History/2026-06-01_native-runtime-chat-control-plane-reliability-pass.md`.
- 2026-06-02: Packaged/native lifecycle slice implemented and proved at bounded scope. `runtime/studio/chat/runtime_control_daemon.py` now owns local poll-loop and loopback-only SSE lifecycle start/status/stop, bridge health, runtime heartbeat checks, graceful shutdown, fail-closed start behavior, restart/backoff entrypoints, and audit writeback. Studio shell gained opt-in supervision via `CHASEOS_STUDIO_RUNTIME_ACTIVITY_SERVICES=1` or `--runtime-activity-services`, with shutdown cleanup. The proof harness emitted 3 signed Hermes events, imported 3 ActivityCards, sampled current event IDs through lifecycle-managed SSE, launched a packaged/native Studio window, captured a nonblank Runtime Activity screenshot, and wrote audit evidence. A later same-day pass rebuilt and reran against fresh `dist/studio/ChaseOS-Studio.exe` hash `0d22a9f2c0acc1b93f7cd629b93202b720152b5f597ed91112247f3444610f7d`; the packaged startup log showed `Runtime Activity lifecycle services started` and `Runtime Activity lifecycle services stopped`. See build logs `07_LOGS/Build-Logs/2026-06-02-ChaseOS-native-runtime-chat-lifecycle-proof.md` and `07_LOGS/Build-Logs/2026-06-02-ChaseOS-native-runtime-chat-full-lifecycle-parity-proof.md`.
- 2026-06-02: Full lifecycle/parity proof repaired OpenClaw Agent Bus registration and made the Presence Board honest across event-bridge and bus-heartbeat proof channels. `runtime/agent_bus/capabilities.py` fallback YAML parsing now accepts nested list values under mapping keys, allowing the existing valid `runtime/openclaw/capabilities.yaml` to load instead of being silently skipped when PyYAML is unavailable. `runtime/studio/chat/runtime_event_health.py` now reports Agent Bus identity/reachability/heartbeat fields separately from RuntimeEvent bridge status. Live proof: Hermes is `live / active-verified-event-bridge`; OpenClaw is `live` via Agent Bus heartbeat and bus response while still `active-unverified-event-bridge` for RuntimeEvent parity; Codex and Chaser Agent remain stale/template as observed; AOR and Approval Gate remain configured/unverified. Hermes gateway probing remained offline, but Hermes bus response and RuntimeEvent bridge proof were verified. See build log `07_LOGS/Build-Logs/2026-06-02-ChaseOS-native-runtime-chat-full-lifecycle-parity-proof.md`.
- 2026-06-02: Codex full-criteria continuation pass tightened the MVP control-plane model without expanding authority. Implemented `task_thread`/`audit_thread` support, `thread.created|proposed|closed` events, automatic bounded `approval_thread` sidecars for Chat approval requests, conditional Chat approval decision mirroring into OSRIL approval responses when an explicit `osril_approval_id`/`operator_approval_ref` is present, Chaser Agent participant visibility, no-presence-authority flags, and missing card/event vocabulary (`terminal.output_chunk`, `audit.writeback.completed`, `summary.created`, approval lifecycle events). Updated Hermes/OpenClaw/Codex adapter event allowlists and `_runtime_event_schema.yaml` for the added visibility events. Focused tests passed (`59 passed`). Local lifecycle proof verified lifecycle-managed poll/SSE, 3 signed Hermes events, 3 ActivityCards, 3 SSE cards, 416.73 ms emit-to-card latency, a nonblank Runtime Activity screenshot, and all required presence labels visible. Packaged executable launch was attempted against `dist/studio/ChaseOS-Studio.exe`, but native screenshot capture remained blocked by `window_handle_not_found` and the packaged process changed a Markdown sentinel; packaged/native visual proof is therefore PARTIAL/BLOCKED, not complete.
- 2026-06-02: Structured Chat approval consumption bridge implemented at bounded scope. `runtime/studio/phase11_chat_runtime_events.py` now writes `approval_consumption` sidecars and emits `approval.consumed` only when a Chat approval request has a recorded allow decision, explicit OSRIL approval id, matching OSRIL response/application state, matching workflow/runtime/session linkage, and caller-supplied resumed session/run ids. Denied decisions, wrong workflow/runtime/session, missing OSRIL links, and duplicate reuse fail closed. The bridge records the OSRIL resume marker through `mark_approval_resume(...)` but does not invoke AOR `run_workflow`, shell/browser/provider actions, or canonical writeback. Focused tests passed (`63 passed` across RuntimeEvent, ActivityCard, OSRIL wait-resume, AOR approval gate, golden/fuzz coverage).
- 2026-06-02: AOR/Gate OSRIL event parity added for the approval lifecycle. `runtime/studio/chat/osril_event_bridge.py` imports existing OSRIL `approval_required`, `approval_response`, and AOR approval-gate approved `status` events into validated Studio `RuntimeEvent`s on `runtime-ops-aor-chat`, using deterministic `adapter_event_id=osril:<event_id>` dedup. Studio API pre-read import, lifecycle `run_poll_cycle()`, and loopback-only SSE now include this bridge, so Runtime Activity cards can render `approval.requested`, `approval.granted`/`approval.denied`, and `approval.consumed` from OSRIL/AOR truth. This remains visibility-only and does not respond to, consume, resume, or execute approvals. Focused tests passed (`81 passed` across RuntimeEvent, ActivityCard, OSRIL bridge, poll/SSE, lifecycle daemon, OSRIL wait-resume, AOR gate, golden/fuzz coverage).
- 2026-06-02: SSE/lifecycle hardening and live presence proof. Loopback-only SSE now imports adapter spool events and OSRIL approval events through a fail-open helper, so one failing bridge source cannot kill an otherwise valid ActivityCard stream. Focused Runtime Activity control-plane tests passed (`88 passed`), including Hermes and OpenClaw live bridge E2E tests. Promoted one-shot coordination-watch cycles verified fresh Agent Bus heartbeat presence for Hermes and OpenClaw without claiming new work; Hermes also expired stale bus tasks as part of watch-cycle housekeeping. Latest verified local lifecycle proof wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-02-native-runtime-chat-lifecycle-proof-live-presence/native-runtime-chat-lifecycle-proof.json`: 3 signed Hermes events, 3 ActivityCards, 3 lifecycle-managed SSE cards, 1,571.24 ms emit-to-card latency, nonblank screenshot, and visible Presence Board labels for Hermes, OpenClaw, Codex, AOR, Approval Gate, and Chaser Agent. Current Presence Board truth from that proof: Hermes `live / active-verified-event-bridge`; OpenClaw `live / active-observed-event-bridge`; Codex `stale / docs-only`; Chaser Agent `stale / active-unverified-event-bridge`; AOR and Approval Gate `configured / active-unverified-event-bridge`. Packaged/native proof was attempted against real `dist/studio/ChaseOS-Studio.exe` hash `25afb9587bc1b792a248a37b8e157a130726e24815240a40b3ae01cd48e729ad`, but Windows Application Control blocked launch with `[WinError 4551]`; therefore current packaged Runtime Activity screenshot proof is BLOCKED, not complete. Evidence is in `07_LOGS/Runtime-Chat-Proofs/2026-06-02-native-runtime-chat-lifecycle-proof/2026-06-02-native-runtime-chat-lifecycle-packaged-visual-qa.json`.
- 2026-06-03: Runtime Activity approval decision controls added at bounded product scope and verified with source-native click proof. `ActivityCard.approval_scope` now includes scoped `request_id`, `approval_thread_id`, and `approval_id` values so product-safe cards can address the existing approval decision ledger without reading raw event payloads. `runtime_activity.js` renders `Allow once` / `Deny` controls only on `approval.requested` cards and calls `record_chat_runtime_approval_decision`; it does not call `record_chat_runtime_approval_consumption`, does not resume OSRIL/AOR, does not execute workflows, and does not grant shell/browser/provider/canonical authority. Focused tests passed (`31 passed`), proof harness tests passed (`1 passed`), and the expanded Runtime Activity / approval / OSRIL / SSE / lifecycle / shell panel suite passed (`125 passed`). Source-native proof wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-approval-decision-proof/runtime-activity-approval-decision-proof.json` with status `VERIFIED`: clicked `Allow once`, wrote decision `apd-50fe289158aa427e`, emitted `approval.granted`, captured nonblank before/after screenshots, and verified `approval_consumed=false`, `workflow_execution_performed=false`, `provider_call_performed=false`, `shell_browser_authority_granted=false`, and `canonical_memory_written=false`. Packaged/native proof remains blocked by host policy.
- 2026-06-03: OSRIL/Gate approval consumption-resume path verified with source-native product proof. New `runtime/studio/native_runtime_chat_approval_consumption_proof.py` seeds explicit OSRIL `approval_required` state, creates a linked Chat approval request, records an allow decision, consumes it through the existing structured bridge, verifies the OSRIL resume marker, verifies a duplicate consumption attempt fails closed with `approval_request_already_consumed`, and renders Runtime Activity cards for `approval.requested`, `approval.granted`, and `approval.consumed`. Focused proof test passed (`1 passed`), Python compile passed, expanded Runtime Activity / approval / OSRIL / SSE / lifecycle / shell panel suite passed (`127 passed`), and the source-native proof wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-approval-consumption-proof/runtime-activity-approval-consumption-proof.json` with status `VERIFIED`. Audit flags show `approval_consumed=true`, `osril_resume_recorded=true`, `workflow_execution_performed=false`, `execution_unblocked=false`, `aor_workflow_run_invoked=false`, `provider_call_performed=false`, `shell_browser_authority_granted=false`, `canonical_memory_written=false`, and `public_endpoint_exposed=false`. No broad Runtime Activity approval-consumption UI was added; packaged/native proof remains blocked by host policy.
- 2026-06-03: Runtime Activity reconnect/replay proof added at source-native scope. New `runtime/studio/native_runtime_chat_reconnect_replay_proof.py` emits three signed Hermes visibility events, imports them through the existing poll cycle, verifies they persist in the SQLite ChatEventStore with indexed cursor support, renders Runtime Activity, reloads the frontend, verifies the same three event ids/cards rehydrate, verifies `after_event_id` cursor replay returns only the final two events, and verifies an unknown cursor returns empty. Focused proof test passed (`1 passed`), Python compile passed, expanded Runtime Activity / approval / OSRIL / SSE / lifecycle / shell panel suite passed (`128 passed`), and the source-native proof wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-reconnect-replay-proof/runtime-activity-reconnect-replay-proof.json` with status `VERIFIED`. Audit flags show `cursor_replay_verified=true`, `reload_replay_verified=true`, `provider_call_performed=false`, `approval_consumed=false`, `workflow_execution_performed=false`, `shell_browser_authority_granted=false`, `canonical_memory_written=false`, and `public_endpoint_exposed=false`. Packaged/native reconnect proof remains blocked by host policy.
- 2026-06-03: Multi-agent shared-room authority visibility verified at source-native scope. `shared_room` is now a supported runtime thread kind, normal-mode ActivityCards expose safe participant/authority fields, and Runtime Activity renders room authority notes when cards show participant presence. New `runtime/studio/native_runtime_chat_multi_agent_room_authority_proof.py` creates a `shared_room`, loads participant roles/boundaries for `human-operator`, `hermes`, `openclaw`, `codex`, `aor`, `approval-gate`, and `audit-writer`, emits supported room events (`thread.created`, `context.loaded`, `agent.acknowledged`, `run.started`, `patch.proposed`, `approval.requested`, `audit.written`), and renders a source-native Runtime Activity screenshot with Hermes/OpenClaw/Codex/AOR/Approval Gate presence visible. Focused tests passed (`53 passed`), Python compile and JavaScript syntax checks passed, expanded Runtime Activity / approval / OSRIL / SSE / lifecycle / shell panel suite passed (`132 passed`), and proof evidence wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-multi-agent-room-authority-proof/runtime-activity-multi-agent-room-authority-proof.json` with status `VERIFIED`. Audit flags show `presence_grants_authority=false`, `mentions_auto_execute=false`, `cross_agent_delegation_requires_audit=true`, `all_cards_visibility_only=true`, `provider_call_performed=false`, `approval_consumed=false`, `workflow_execution_performed=false`, `shell_browser_authority_granted=false`, `canonical_memory_written=false`, and `public_endpoint_exposed=false`. Packaged/native proof remains blocked by host policy.
- 2026-06-03: Thread/run/debug/audit/continuation/approval room model verified at source-native scope. Runtime Activity now renders generic `Thread room` notes for cards carrying safe `thread_kind`, `parent_thread_id`, and `source_thread_id` details. New `runtime/studio/native_runtime_chat_thread_room_model_proof.py` creates real thread sidecars for `task_thread`, `run_thread`, `debug_thread`, `audit_thread`, `continuation_thread`, and `approval_thread`, emits parent-thread navigation cards, and renders a source-native Runtime Activity screenshot showing run/debug/audit/continuation/approval room notes. Focused tests passed (`54 passed`) after fixing the proof to include a parent-thread navigation card for the approval-thread sidecar; Python compile and JavaScript syntax checks passed; expanded Runtime Activity / approval / OSRIL / SSE / lifecycle / shell panel suite passed (`134 passed`); proof evidence wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-thread-room-model-proof/runtime-activity-thread-room-model-proof.json` with status `VERIFIED`. Audit flags show `thread_notes_visible=true`, `approval_consumed=false`, `workflow_execution_performed=false`, `provider_call_performed=false`, `shell_browser_authority_granted=false`, `canonical_memory_written=false`, and `public_endpoint_exposed=false`. Packaged/native proof remains blocked by host policy.
- 2026-06-03: Runtime event card coverage verified at source-native scope. `runtime/studio/chat/activity_cards.py` now exposes `CARD_EVENT_TYPES`, `CLAIM_EVENT_TYPES`, `ACTION_EVENT_TYPES`, and `NOISE_EVENT_TYPES`, and normal-mode cards include safe artifact/handover path fields for product inspection. New `runtime/studio/native_runtime_chat_event_card_coverage_proof.py` emits one RuntimeEvent for every `ALLOWED_EVENT_TYPES` member, verifies the ActivityCard contract equals the allowed vocabulary, renders all 32 event cards through the real Runtime Activity frontend with `include_noise=true`, and fails if any event falls back to a generic title or loses visibility-only authority. Focused tests passed (`87 passed`), Python compile and JavaScript syntax checks passed, source-native proof wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-event-card-coverage-audit/runtime-activity-event-card-coverage-proof.json` with status `VERIFIED`, visual screenshot was inspected, and the expanded Runtime Activity / approval / OSRIL / SSE / lifecycle / shell panel suite passed (`168 passed`). Audit flags show `allowed_equals_card_contract=true`, `fallback_title_event_types=[]`, `claim_cards_verified=true`, `approval_consumed=false`, `workflow_execution_performed=false`, `provider_call_performed=false`, `shell_browser_authority_granted=false`, `canonical_memory_written=false`, and `public_endpoint_exposed=false`. Packaged/native event-card coverage proof remains blocked by host policy.
- 2026-06-03: Packaged/native Studio Runtime Activity card proof verified. New `runtime/studio/native_runtime_chat_packaged_studio_proof.py` seeds manifest-gated Hermes lifecycle events, imports them through the Studio poller, verifies source-native ActivityCards, launches real `dist/studio/ChaseOS-Studio.exe` with Runtime Activity services enabled, captures a native screenshot, and validates packaged DOM text for `Runtime Activity`, `Hermes acknowledged`, `Hermes started work`, and `Hermes completed`. The proof wrote `07_LOGS/Runtime-Chat-Proofs/2026-06-03-native-runtime-chat-packaged-studio-proof/native-runtime-chat-packaged-studio-proof.json` with status `VERIFIED`, no blockers, native screenshot captured, and executable hash `e705d823fa2ec3b6062cf8bc9a411d5e8e724d4c4e561d03aa3c45ed020cc2e6`. Supporting changes added a reusable single-route packaged batch QA helper, packaged DOM-result sentinel support, bridge-ready retry / newest-first Runtime Activity sorting, initial packaged Chat fallback card rendering, and scoped ignore for live Codex profile drift during the visual QA sentinel. This remains visibility proof only: no provider/connector call, workflow execution, approval consumption, shell/browser command authority, public endpoint, installer/signing/startup/autostart, or canonical ChaseOS memory write occurred.

---

## 45. Core-readiness layer (ActivityCards, health, classifiers)

`runtime/studio/chat/activity_cards.py` is the single product-safe boundary:
`RuntimeEvent → ActivityCard`. Core/Studio UI consumes cards, never raw events.
Each card carries human-readable title/body, run/session `group_key`, runtime
claim-vs-ChaseOS-verified split, per-path classification, rule-based injection
risk marking, payload caps + truncation metadata, a Normal/Private/Debug display
mode, a "why blocked?" explanation, and display-only approval scope (never
consumes an approval). `group_cards_by_run()` builds run timelines;
`action_required_only` filters to operator-decision cards.

`runtime/studio/chat/runtime_event_health.py` maintains per-adapter health files
(`runtime/studio/chat/native-state/runtime-event-health/{adapter}.json`) updated
on import; `get_runtime_event_health()` computes live/degraded/stale/configured/
template presence at read time + a bridge-level rejected rollup. Studio API:
`get_chat_activity_cards(...)` and `get_runtime_event_health(...)`.

## 46. Implemented local transport + rotation/retention

This section was originally design-only. Repo truth now shows these pieces are
implemented as local, visibility-only delivery and spool-management layers.
Fresh local Studio proof has verified in-process lifecycle supervision. A
2026-06-03 packaged/native Studio proof now verifies real `dist/studio/ChaseOS-Studio.exe`
Runtime Activity card rendering for manifest-gated Hermes lifecycle events,
including native screenshot capture and packaged DOM/text sentinels. Remaining
product-hardening gaps are release signing, installer/autostart/service policy,
and broader packaged route coverage, not SSE/spool/lifecycle existence.

**Local-only SSE delivery (implemented Core delivery layer).**
`runtime/studio/chat/sse_server.py` provides a `127.0.0.1`-only,
token-authenticated `GET /runtime-events/stream` that pushes already-validated
**ActivityCards** (never raw events) to the desktop UI. Hard boundaries remain:
bind to loopback only; never accept commands (one-way); stream cards produced by
the import/validation path only; no public exposure. SSE remains correct because
runtime activity is one-way visibility; there is no bidirectional authority
channel by design. This is a UI delivery optimization over the existing store +
card API and changes no security properties.

**Spool rotation / retention (implemented layout).**
`runtime/studio/chat/spool_layout.py` supports per-adapter daily files such as
`07_LOGS/Runtime-Events/{adapter}/YYYY-MM-DD.jsonl`; `RuntimeEventEmitter(...,
rotate=True)` writes that layout, and `poll_all_spools()` discovers both the
single shared spool and rotated adapter spools. The cursor model remains
rotation-safe: truncation/rotation resets the cursor and source-id dedup prevents
replays. Retention helpers exist; final retention policy and packaged lifecycle
wiring remain product hardening work.

**Studio Runtime Control Daemon (implemented lifecycle wrapper).**
`runtime/studio/chat/runtime_control_daemon.py` starts, supervises, reports, and
stops the local poll loop plus loopback-only SSE stream as one bounded Studio
Runtime Activity service. It performs bridge health and runtime heartbeat
checks, shuts down gracefully, fails closed if a component cannot start, supports
restart/backoff for safe local restart flows, and writes audit summaries without
exposing SSE tokens. `runtime/studio/shell/main.py` can opt into this lifecycle
on Studio startup with `--runtime-activity-services` or
`CHASEOS_STUDIO_RUNTIME_ACTIVITY_SERVICES=1` and stops it during shell shutdown.
The 2026-06-02 proof verified lifecycle-managed poll/SSE and local/source-native
Runtime Activity rendering with fresh Hermes/OpenClaw presence visibility. The
2026-06-03 packaged/native proof then launched real `dist/studio/ChaseOS-Studio.exe`
hash `e705d823fa2ec3b6062cf8bc9a411d5e8e724d4c4e561d03aa3c45ed020cc2e6`,
enabled Runtime Activity services, captured a nonblank native screenshot, and
verified packaged DOM/card text for Hermes acknowledgement, start, and completion
cards. Startup/autostart integration remains a separate governed product-hardening
surface.

## 42. Persistence model + JSONL → SQLite migration note

The event STREAM (high-volume, append + poll: `tool.called`, `terminal.*`, `file.*`,
…) is owned by a pluggable `ChatEventStore`:

- **SqliteEventStore (default).** `{vault}/runtime/studio/chat/native-state/chat_events.sqlite`,
  WAL mode, one row per event with a monotonic INTEGER PRIMARY KEY `seq` and a
  `(thread_id, seq)` index. Polls become `WHERE thread_id=? AND seq > ? ORDER BY seq LIMIT ?`
  (O(log n + k)). The client cursor `after_event_id` resolves to its `seq` via a
  single indexed lookup on the UNIQUE `id` column. This retires the foothold's
  O(n) full-file rescan-and-revalidate-per-poll.
- **JsonlEventStore (fallback).** Keeps the foothold's append-only per-thread
  JSONL files but adds a `<thread>.jsonl.idx` byte-offset index (seek past the
  cursor, parse only the tail) and a retention cap that rolls old events to
  `<thread>.archive.jsonl`. Selected via `chat_event_store.yaml` (`mode: jsonl`)
  for a human-readable / git-diffable / portable log.
- **Backend choice** is read from optional `{vault}/runtime/studio/chat/chat_event_store.yaml`
  (`mode: sqlite | jsonl`), fail-open to SQLite. One cached store per vault.

**Why a separate SQLite file from the Agent Bus.** The bus DB
(`runtime/agent_bus/agent_bus.sqlite`) is coordination state. Chat UI event
traffic is high-volume visibility state. Keeping them in separate WAL databases
prevents the chat stream from bloating or coupling its lifecycle to the bus while
preserving a clean future consolidation/server-mode path (both follow the same
backend-abstraction pattern). A future network/server backend slots in behind
`ChatEventStore` exactly as the bus server mode slots in behind `BusBackend` —
emitters, the bridge, and the API do not change.

**What deliberately stays as JSON sidecars.** The low-volume singleton records
(`runtime_runs`, `runtime_threads`, `approval_requests`, `approval_decisions`,
`audit_artifacts`, `runtime-participants`) remain individual JSON files written by
`phase11_chat_runtime_events.py`. They are read at most once per render and never
grow per-poll, so moving them into SQL buys nothing and would widen the schema
surface. They can migrate later if a query need emerges; the store abstraction
makes that additive, not a rewrite.

## 43. Redaction model (defense in depth)

1. **Redaction-at-source (preventive)** — `runtime/studio/chat/redaction.py`.
   The adapter bridge runs `redact_text_at_source` / `redact_payload_at_source`
   on every raw stdout/stderr/command/diff/file preview the moment it is captured,
   before it enters a payload. Shape-based: provider key prefixes (`sk-`, `sk-ant-`,
   `xai-`, `ghp_`, `AKIA…`, `AIza…`, …), JWTs, PEM private-key blocks, sensitive
   `KEY=VALUE` assignments, bearer tokens, seed-phrase hints, and unprefixed
   high-entropy tokens. Only matched spans are replaced, so paths/exit codes/tool
   names survive.
2. **Redaction-at-build (detective)** — `phase11_chat_runtime_events.build_runtime_event`.
   Key-name + secret-indicator scrub plus schema validation. Runs on EVERY event
   regardless of source. A secret must defeat both walls to leak. Hidden
   chain-of-thought markers are rejected outright (fail-closed).

## 44. Templated adapter bridge

`runtime/studio/chat/adapter_bridge.py` provides `RuntimeAdapterBridge` (base) +
a registry. Adding a future runtime is: subclass, declare `adapter` +
`authority_boundary` + `roles`, `register_bridge(id, cls)`. The base owns
redaction-at-source, RuntimeEvent construction/validation, and persistence — a
subclass cannot bypass redaction because all emission flows through `emit()`.
Built-in bridges: Hermes, OpenClaw, Codex (`claude-code`), Chaser Agent, AOR. `emit`
helpers cover the full event vocabulary (`run.*`, `tool.called`, `terminal.*`,
`file.*`, `patch.proposed`, `handover.created`). `request_approval()` creates a
scoped blocked/pending record - it grants no authority and consumes no approval.
The bridge is transport-agnostic: it writes to the store; the API polls the
store; a later SSE/WebSocket upgrade changes only the API read path.

## 45. Runtime parity proof (Hermes / OpenClaw / Codex / AOR / Gate)

The 2026-06-03 source-native parity proof verifies the repo-supported runtime
visibility lanes together in Runtime Activity:

- Hermes, OpenClaw, and Codex emitted manifest-validated visibility events into
  `07_LOGS/Runtime-Events/runtime-events.jsonl` and Studio imported them through
  the local adapter poller.
- AOR emitted native store-backed `run.queued` and `audit.written` cards through
  `runtime/studio/chat/adapter_bridge.py`.
- Approval Gate appeared through the OSRIL approval lifecycle bridge with
  `approval.requested`, `approval.granted`, and `approval.consumed` cards in the
  AOR room.

The proof rendered 14 Runtime Activity cards with visible labels for Hermes,
OpenClaw, Codex, AOR, and Approval Gate, zero frontend console errors, and a
nonblank screenshot. It is VERIFIED for source-native visibility parity only.
It did not launch runtime daemons, invoke the live Codex bus daemon, call
providers/connectors, execute AOR workflows, perform new Chat approval
consumption, grant shell/browser authority, expose a public endpoint, or mutate
canonical ChaseOS memory. A separate packaged/native Runtime Activity proof now
verifies packaged Studio rendering for manifest-gated Hermes lifecycle cards, but
full packaged parity across every runtime lane remains a future breadth pass.
