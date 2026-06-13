---
title: Native Runtime Chat Control Plane — Execution Prompts
path: 06_AGENTS/Native-Runtime-Chat-Control-Plane-Execution-Prompts.md
status: implementation-kickoff-pack
created: 2026-06-01
owner: ChaseOS
companion_doc: 06_AGENTS/Native-Runtime-Chat-Control-Plane.md
primary_execution_agents:
  - Codex / Antigravity
  - Hermes
prototype_target: JOS_SQL repository first, then ChaseOS core
scope: prompt pack only; no runtime authority granted by this note
---

# Native Runtime Chat Control Plane — Execution Prompts

> Use this file together with `06_AGENTS/Native-Runtime-Chat-Control-Plane.md`.
>
> The purpose of this file is to give repo-aware agents the first implementation prompts for turning ChaseOS Chat into a native runtime control plane.

---

## 0. How to use this prompt pack

Run these in order:

1. **Codex / Antigravity pass** — repository audit + first implementation foothold in the JOS_SQL prototype repository.
2. **Hermes pass** — runtime adapter/config/event bridge work for Hermes, OpenClaw, Codex, and future runtimes.
3. **Integration closure pass** — only after both outputs exist; reconcile schema, bridge path, tests, docs, and live proof.

Do not run the Hermes pass as broad runtime authority expansion.
Do not run the Codex pass as a full app rewrite.
Do not start cross-user enterprise sharing yet.
Do not expose hidden chain-of-thought.
Do not let Chat become a bypass around AOR, Gate, OSRIL, Agent Bus, or existing permission boundaries.

---

## 1. Prompt for Codex / Antigravity

```text
We are starting the Native Runtime Chat Control Plane implementation foothold.

Repository target:
- Prototype first in the JOS_SQL repository if this is the active repo.
- If this is ChaseOS core instead, apply the same pass to the existing ChaseOS Chat / Studio code path.

This is not a broad UI rewrite.
This is not a Discord bot pass.
This is not an AOR rebuild.
This is not enterprise sharing.
This is not a general runtime authority expansion.
This is not a hidden chain-of-thought viewer.

Goal:
Turn the existing Chat page into the first native runtime control surface capable of showing structured live agent/runtime activity the same way Discord currently makes runtime work visible.

Required source document:
- Read `06_AGENTS/Native-Runtime-Chat-Control-Plane.md` first.
- If this execution-prompt file exists, also read `06_AGENTS/Native-Runtime-Chat-Control-Plane-Execution-Prompts.md`.

Core product truth:
Discord is currently useful because it shows:
- immediate agent acknowledgement
- live typing/progress
- tool and terminal activity
- embedded approval cards
- separate threads/channels
- audit/writeback lanes

ChaseOS Chat must implement the same primitives natively, but with structured records and ChaseOS governance.

Critical design decision:
Do not scrape raw logs into chat.
Build a structured runtime event stream.

The system must distinguish:
1. chat message
2. runtime event
3. runtime run
4. tool call
5. approval request
6. approval decision
7. audit artifact
8. participant
9. thread

Even if the UI renders them in one conversation timeline, they must not be collapsed into one untyped message table.

Read first, if present:
- README.md
- PROJECT_FOUNDATION.md
- ROADMAP.md
- 00_HOME/Now.md
- CLAUDE.md
- HERMES.md
- OPENCLAW.md
- 06_AGENTS/Native-Runtime-Chat-Control-Plane.md
- 06_AGENTS/Agent-Control-Plane.md
- 06_AGENTS/Permission-Matrix.md
- 06_AGENTS/Trust-Tiers.md
- 06_AGENTS/Handoff-Protocol.md
- 06_AGENTS/ChaseOS-Gate.md
- 06_AGENTS/Autonomous-Operator-Runtime.md
- 06_AGENTS/Execution-Adapter-Standard.md if present
- 06_AGENTS/Hermes-Adapter-Spec.md
- 06_AGENTS/Hermes-Workflow-Boundaries.md
- 06_AGENTS/Hermes-Memory-Boundary.md
- 06_AGENTS/ChaseOS-Discord-Control-Plane.md
- 06_AGENTS/Discord-Identity-Map.md
- 06_AGENTS/Discord-Channel-Registry.md
- 06_AGENTS/Discord-Command-Envelope-Schema.md
- runtime/aor/engine.py if present
- runtime/aor/registry.py if present
- runtime/aor/task_router.py if present
- runtime/aor/role_cards.py if present
- runtime/workflows/registry/_schema.yaml if present
- current frontend Chat page/component files
- current backend Chat API files
- current Agent Bus / OSRIL / runtime event files
- current approval-related files
- current audit / agent activity log files
- database schema / migrations / ORM models if present

What this pass must do:

1. Audit current Chat architecture
Find and report:
- frontend Chat page files
- backend Chat API / route files
- current message model
- current runtime integration points
- whether WebSocket, SSE, polling, or static fetch is used
- whether Agent Bus / OSRIL / AOR events already exist
- current approval card implementation, if any
- current audit/log persistence paths
- current database layer and migration pattern

2. Create or propose the canonical RuntimeEvent schema
Implement if safe. Otherwise create exact files/specs needed.

Minimum event types:
- message.received
- agent.acknowledged
- agent.typing
- run.queued
- run.started
- context.loaded
- tool.called
- terminal.started
- terminal.completed
- file.read
- file.written
- patch.proposed
- approval.requested
- approval.granted
- approval.denied
- audit.written
- artifact.created
- run.completed
- run.failed
- handover.created

RuntimeEvent minimum fields:
- id
- session_id
- thread_id
- run_id
- parent_event_id
- actor_id
- actor_type
- adapter
- event_type
- severity
- status
- summary
- payload_json
- artifact_refs
- approval_request_id
- created_at
- redaction_state

3. Create or propose persistence model
Use the repository’s real persistence layer.

If the repo has SQL/ORM/migrations, add proper models/migrations.
If it is still file-backed, create a small JSONL-backed event store with a future migration note.

Target logical records:
- chat_sessions
- chat_threads
- chat_messages
- runtime_runs
- runtime_events
- tool_calls
- approval_requests
- approval_decisions
- audit_artifacts
- chat_participants
- adapter_permissions

Do not fake database usage if the repo does not have DB infrastructure yet.
Use the smallest truthful implementation.

4. Build the first minimal event-stream path
The smallest acceptable vertical slice is:
- user sends message in Chat
- backend persists chat message
- backend creates or links a runtime run
- backend emits `agent.acknowledged`
- backend emits at least one additional structured runtime event
- frontend receives event via WebSocket, SSE, or current repo-appropriate stream mechanism
- frontend renders the event as a card in the Chat timeline
- event is persisted or logged

Preferred transport:
- Use WebSocket if the app already has WebSocket infrastructure.
- Use SSE if WebSocket is absent and SSE is simpler.
- Use polling only if that is the existing pattern and streaming is too large for this pass.

5. UI card foundation
Create or wire minimal cards for:
- AgentAcknowledgementCard
- RuntimeEventCard
- ToolCallCard
- TerminalCard
- FileActivityCard
- ApprovalRequestCard
- AuditWritebackCard
- RunSummaryCard
- ErrorEventCard

Keep the current ChaseOS visual style.
Do not redesign the entire app.
Do not add unnecessary animation or brand changes.

6. Approval card foundation
Approval cards must be scoped records, not loose chat replies.

ApprovalRequest must include:
- request_id
- session_id
- run_id
- actor
- adapter
- action
- exact command/action if applicable
- read targets
- write targets
- risk class
- requested scope
- expiration
- expected audit destination
- status

Buttons can be:
- Allow Once
- Allow Session
- Always Allow
- Deny

But for this pass, do not grant real high-risk authority unless an existing Gate approval path is already present.
If the approval backend is not ready, buttons may record decision objects only and mark execution as blocked/pending.

Never treat emoji reactions, plain text replies, or raw chat messages as approvals.

7. Thread foundation
Define or implement minimal thread records for:
- run thread
- approval thread
- debug thread
- continuation thread

Do not implement cross-user shared rooms yet.
Agents may propose a thread, but user approval should be required for actual shared/new room creation unless an existing room policy allows it.

8. Runtime participants
Add or define participant records for:
- human operator
- Hermes
- OpenClaw
- Codex
- AOR
- Agent Bus
- Approval Gate
- Audit Writer

Each participant should have a role/capability boundary such as:
- viewer
- responder
- executor
- approver
- auditor
- system

Do not treat all participants as equally authorized.

9. Security and redaction rules
The event stream must not expose:
- API keys
- OAuth tokens
- provider tokens
- passwords
- private credentials
- seed phrases
- raw secrets
- hidden model chain-of-thought

It may expose:
- action summaries
- tool names
- command previews where safe
- file paths where safe
- stdout/stderr previews where redacted
- approval metadata
- audit references
- run status

10. Tests
Add or update tests for:
- event schema validation
- malformed event rejected/fails closed
- message to event vertical slice
- approval request creation
- approval decision recording
- event redaction
- UI rendering if frontend test harness exists

11. Documentation and writeback
Create/update:
- implementation note or build log
- archive/documentation-history note if the repo uses that pattern
- index updates if the repo uses Build-Logs-Index.md and Documentation-History-Index.md
- a cross-link from the architecture note to this implementation if appropriate

Do not broadly rewrite README/ROADMAP unless this pass genuinely changes live truth.

Out of scope:
- cross-user enterprise sharing
- external-user agent messaging
- unrestricted shell execution
- direct provider credential handling
- broad Hermes/OpenClaw authority expansion
- Discord runtime changes
- raw hidden reasoning display
- full standalone dashboard rewrite
- database replatforming unless absolutely required
- MCP expansion
- Home Assistant or unrelated connectors

Acceptance criteria:
This pass succeeds if:
1. current Chat architecture is audited
2. a RuntimeEvent schema exists
3. events are persisted or logged
4. the Chat page can render at least acknowledgement + one runtime event card
5. approval request records exist or are clearly scaffolded
6. security/redaction rules are implemented or explicitly enforced in schema/API
7. tests prove the first slice or clearly document why repo state blocks execution
8. build/archive writeback exists if that is the repo pattern

Final handover must list:
1. exact files inspected
2. exact files modified
3. exact files created
4. current Chat architecture found
5. event stream transport chosen
6. event schema created
7. persistence model created or proposed
8. UI cards implemented or proposed
9. approval card behavior
10. runtime participants model
11. security/redaction behavior
12. tests run and results
13. what works live after this pass
14. what remains blocked
15. exact build log path
16. exact archive note path
17. index update confirmations

Do not stop at proposal unless implementation is impossible from repo state.
Execute the smallest safe foundation.
```

---

## 2. Prompt for Hermes

```text
We are starting the Hermes Runtime Adapter + Backend Config Wiring pass for the Native Runtime Chat Control Plane.

This is not a broad Hermes authority expansion.
This is not a Discord control-plane change.
This is not a shell expansion pass.
This is not an OpenClaw public-exposure pass.
This is not MCP expansion.
This is not Home Assistant.
This is not canonical memory/writeback expansion.

Goal:
Wire the runtime side so Hermes, OpenClaw, Codex, and future runtimes can emit structured runtime events that ChaseOS Chat can display as live activity cards.

Primary source document:
- Read `06_AGENTS/Native-Runtime-Chat-Control-Plane.md` first.
- If present, read `06_AGENTS/Native-Runtime-Chat-Control-Plane-Execution-Prompts.md`.

Your job:
Build or propose the backend/runtime configuration layer that lets runtimes publish safe structured events into ChaseOS without broadening their authority.

Important context:
ChaseOS Chat will consume typed runtime events. The runtime side must expose or emit those events with strict boundaries.

Core principle:
Runtimes may emit visibility events.
Event emission does not grant execution authority.

Read first, if present:
- HERMES.md
- OPENCLAW.md
- CLAUDE.md
- 06_AGENTS/Native-Runtime-Chat-Control-Plane.md
- 06_AGENTS/Hermes-Adapter-Spec.md
- 06_AGENTS/Hermes-Workflow-Boundaries.md
- 06_AGENTS/Hermes-Memory-Boundary.md
- 06_AGENTS/OpenClaw-Discord-Activation-Preflight.md
- 06_AGENTS/OpenClaw-Operations-Runbook.md if present
- 06_AGENTS/ChaseOS-Discord-Control-Plane.md
- 06_AGENTS/Discord-Command-Envelope-Schema.md
- 06_AGENTS/Execution-Adapter-Standard.md if present
- 06_AGENTS/Agent-Control-Plane.md
- 06_AGENTS/Permission-Matrix.md
- 06_AGENTS/Trust-Tiers.md
- 06_AGENTS/ChaseOS-Gate.md
- runtime/policy/adapters/hermes.yaml if present
- runtime/policy/adapters/openclaw.yaml if present
- runtime/policy/adapters/codex.yaml if present
- .chaseos/hermes_config.yaml if present
- .chaseos/openclaw_config.yaml if present
- runtime/aor/hermes_shadow.py if present
- runtime/aor/openclaw_shadow.py if present
- runtime/workflows/registry/hermes_operator_today_shadow.yaml if present
- 06_AGENTS/role-cards/hermes-operator-shadow.yaml if present
- current Agent Bus / OSRIL / runtime event schema created by Codex, if already present
- current Chat backend event API / SSE / WebSocket endpoint, if already created by Codex

What this pass must do:

1. Inspect current runtime surfaces
For Hermes, OpenClaw, Codex, and any registered runtime adapter, identify:
- where messages are received
- where runtime status is logged
- where tool calls are represented
- where file reads/writes are performed
- where terminal/shell commands are performed
- where approvals are requested
- where audit files are written
- where failures/retries are logged
- what config files define boundaries
- what is active vs docs-only

2. Define runtime adapter event contract
Create or update a machine-readable adapter event contract.

Minimum logical fields:
- adapter_id
- runtime_name
- runtime_type
- can_emit_events
- event_transport
- event_endpoint_or_spool_path
- allowed_event_types
- denied_event_types
- allowed_read_targets
- allowed_write_targets
- forbidden_targets
- allowed_tool_families
- forbidden_tool_families
- approval_required_for
- redaction_policy
- chain_of_thought_policy
- secret_handling_policy
- audit_required
- status

Preferred adapter config files, if consistent with repo conventions:
- runtime/policy/adapters/hermes.yaml
- runtime/policy/adapters/openclaw.yaml
- runtime/policy/adapters/codex.yaml
- runtime/policy/adapters/_runtime_event_schema.yaml

If the repo uses `.chaseos/` runtime configs, add or update:
- .chaseos/hermes_config.yaml
- .chaseos/openclaw_config.yaml
- .chaseos/codex_config.yaml

Do not invent paths if the repo already has a clear adapter-policy convention.
Use existing conventions first.

3. Select the safest event transport
If Codex already created a Chat event ingestion endpoint, use that.
If not, create a safe spool fallback.

Acceptable transports:
- direct local API call to ChaseOS backend if authenticated and already present
- Agent Bus publish if a local bus API exists
- JSONL spool file watched by ChaseOS
- SQLite/SQL event insert only if the repository already owns that DB path

Preferred fallback if no API exists:
- `07_LOGS/Runtime-Events/runtime-events.jsonl`
- or repo-approved equivalent event spool

Do not use Discord as the canonical event transport.
Do not send events to external services by default.
Do not introduce network listeners unless the repo already has local backend service boundaries.

4. Map runtime actions to ChaseOS event types
Return and/or implement a table:

Hermes/OpenClaw/Codex source event → ChaseOS event_type → payload fields → redaction policy → approval behavior → audit target.

Required mappings:
- runtime sees user message → agent.acknowledged
- runtime starts work → run.started
- runtime loads docs/context → context.loaded
- tool call proposed → tool.called
- shell command proposed/started/completed → terminal.started / terminal.completed
- file read → file.read
- file write or patch proposal → file.written or patch.proposed
- approval request → approval.requested
- approval decision observed → approval.granted / approval.denied
- audit file written → audit.written
- run completed → run.completed
- run failed → run.failed

5. Implement minimal event emitter if safe
If repo state supports implementation, create a small event emitter module.

Possible shapes:
- runtime/events/emitter.py
- runtime/chat/events.py
- runtime/aor/event_emitter.py
- runtime/adapters/event_emitter.py

The emitter must:
- validate required fields
- reject unknown event types unless explicitly allowed
- redact secrets
- exclude hidden chain-of-thought
- include adapter_id
- include run_id/session_id where available
- write to the selected transport
- fail closed on malformed events

Do not let event emission silently mutate canonical knowledge, Now.md, Project-OS files, 02_KNOWLEDGE, or runtime policy files.

6. Hermes-specific wiring
For Hermes:
- add or update Hermes adapter manifest
- add or update Hermes config boundary
- connect Hermes shadow workflow or runtime handler to emit structured events if safe
- make Hermes emit at least:
  - agent.acknowledged
  - context.loaded or file.read
  - audit.written or run.completed

Keep Hermes in bounded mode unless the repo already has verified wider permission closure.
No ambient repo traversal.
No connector expansion.
No shell execution expansion.
No memory promotion.
No canonical writeback expansion.

7. OpenClaw-specific wiring
For OpenClaw:
- add or update OpenClaw adapter manifest/config if present
- mark actual status honestly: active, configured, docs-only, unverified, or blocked
- define OpenClaw event types it may emit
- define forbidden surfaces
- define approval requirements for shell/browser/file actions

Do not enable public OpenClaw gateway exposure.
Do not widen localhost/network assumptions.
Do not add credentials or secrets into config.
Do not claim OpenClaw event bridge is live unless tested.

8. Codex/future runtime wiring
For Codex and future runtimes:
- create a generic adapter template if useful
- mark as template/unverified unless live code exists
- define minimal event capabilities
- avoid provider-specific authority assumptions

9. Secret and reasoning safety
Events must not include:
- provider tokens
- OAuth tokens
- API keys
- passwords
- seed phrases
- private credentials
- secret file contents
- raw hidden model reasoning

Events may include:
- short action summaries
- paths when safe
- command preview when safe
- stdout/stderr previews after redaction
- status
- audit artifact references
- approval metadata

10. Tests
Add or run tests proving:
- valid event accepted
- malformed event rejected
- unknown event type rejected or blocked
- secret-like payload redacted or rejected
- hidden reasoning field rejected
- Hermes can emit a minimal event
- spool/API write works
- OpenClaw config validates if implemented

If shell/connector denial cannot be exercised live, state that clearly.

11. Documentation and writeback
Create/update:
- build log
- documentation-history/archive note
- index updates if repo uses them
- adapter docs or runtime README as needed

Do not broadly update README/ROADMAP unless live truth changes.

Out of scope:
- public gateway exposure
- broad shell enablement
- connector expansion
- MCP expansion
- direct credentials handling
- cross-user agent sharing
- canonical knowledge promotion
- protected file writes
- Discord as canonical transport
- raw hidden reasoning display

Acceptance criteria:
This pass succeeds if:
1. runtime adapter event contract exists
2. Hermes adapter/config is wired or precisely specified
3. OpenClaw adapter/config is wired or honestly marked as unverified/template
4. event transport is selected and documented
5. minimal event emitter/spool/API bridge exists if repo state allows
6. tests or validation prove the event bridge fails closed
7. no secrets or hidden reasoning are emitted
8. writeback logs are created

Final handover must list:
1. exact files inspected
2. exact files modified
3. exact files created
4. runtime adapters found
5. adapter statuses: Hermes, OpenClaw, Codex, future/template
6. event transport chosen
7. event schema/contract path
8. Hermes wiring completed
9. OpenClaw wiring completed or deferred
10. Codex/future runtime template created or deferred
11. redaction/secret policy
12. hidden reasoning exclusion policy
13. tests run and results
14. what works live
15. what remains blocked
16. exact build log path
17. exact archive note path
18. index update confirmations

Do not stop at proposal unless implementation is impossible from repo state.
Execute the smallest safe runtime event bridge.
```

---

## 3. Integration closure prompt after Codex + Hermes outputs exist

```text
We are now doing the Native Runtime Chat Control Plane integration closure pass.

Only run this after the Codex/Antigravity Chat implementation foothold and the Hermes runtime adapter/config pass both have handovers.

Goal:
Reconcile the frontend/backend Chat event stream with the runtime adapter event bridge so ChaseOS Chat can display at least one real runtime-originated event from Hermes or a local runtime spool.

Read first:
- 06_AGENTS/Native-Runtime-Chat-Control-Plane.md
- 06_AGENTS/Native-Runtime-Chat-Control-Plane-Execution-Prompts.md
- Codex pass build log / handover
- Hermes pass build log / handover
- runtime event schema files
- adapter config files
- Chat backend event ingestion files
- Chat frontend card files
- test files created by both passes

Tasks:
1. Compare Codex RuntimeEvent schema vs Hermes adapter event contract.
2. Normalize field names and event types.
3. Confirm transport path: API, Agent Bus, JSONL spool, DB, or other.
4. Wire one real local event from Hermes or a test adapter into the Chat event stream.
5. Render the event in Chat as a card.
6. Ensure redaction/secret policy still holds.
7. Ensure approval events do not bypass Gate.
8. Add one end-to-end test or documented smoke-test.
9. Update build/archive logs and indexes.

Acceptance:
- At least one real or controlled local runtime-originated event appears in the Chat timeline.
- Event is structured, persisted/logged, and redacted.
- No hidden reasoning is exposed.
- No authority is broadened.
- Handover lists exact remaining blockers before live Hermes/OpenClaw parity.
```

---

## 4. Repo placement

Place this file at:

```text
06_AGENTS/Native-Runtime-Chat-Control-Plane-Execution-Prompts.md
```

Place the companion architecture note at:

```text
06_AGENTS/Native-Runtime-Chat-Control-Plane.md
```

Internal Obsidian links to add later:

```text
[[Native-Runtime-Chat-Control-Plane]]
[[Native-Runtime-Chat-Control-Plane-Execution-Prompts]]
[[Agent-Control-Plane]]
[[Permission-Matrix]]
[[Trust-Tiers]]
[[Hermes-Adapter-Spec]]
[[ChaseOS-Discord-Control-Plane]]
```
