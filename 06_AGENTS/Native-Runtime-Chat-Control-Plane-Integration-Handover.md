# Native Runtime Chat Control Plane — Integration Closure + Handover Prompt

> **Target repo placement:** `06_AGENTS/Native-Runtime-Chat-Control-Plane-Integration-Handover.md`  
> **Use after:** Codex/Antigravity pass and Hermes runtime/config pass have both returned handovers.  
> **Purpose:** Reconcile the Chat-side implementation with the runtime-side event bridge and prove the smallest live vertical slice without widening runtime authority.

---

## 1. Where this fits

This is the **third prompt** in the Native Runtime Chat Control Plane sequence.

The first prompt is for **Codex / Antigravity**. It owns the ChaseOS Chat side:

- Chat event schema
- backend event ingestion
- persistence/logging
- frontend activity cards
- approval-card foundation
- thread/session model foundation

The second prompt is for **Hermes**. It owns the runtime/config side:

- Hermes/OpenClaw/Codex adapter event contracts
- runtime event emitter or spool bridge
- fail-closed event validation
- redaction policy
- no-secret / no-hidden-reasoning enforcement
- adapter configs and manifests

This third prompt is the **integration closure pass**.

It is not a new feature-expansion pass. It exists to make sure both sides actually join together.

---

## 2. What this pass does exactly

This pass answers these questions:

1. Did Codex and Hermes use the same event schema?
2. Did they choose compatible event transport?
3. Can a runtime-originated event reach ChaseOS Chat?
4. Can ChaseOS Chat render that event as a visible card?
5. Are events persisted or logged?
6. Are approvals represented as scoped objects, not informal replies?
7. Are secrets redacted?
8. Is hidden model reasoning excluded?
9. Does the system fail closed on malformed or unauthorized runtime events?
10. What exact blocker remains before this becomes the default control plane?

The success condition is intentionally small:

```text
one runtime emits one safe event
→ ChaseOS backend accepts it
→ event is persisted/logged
→ Chat page displays it
→ audit/log evidence exists
```

---

## 3. Privacy and redaction rules before running this

Before pasting Codex or Hermes handovers into another model or this prompt, remove:

- API keys
- OAuth tokens
- provider tokens
- bearer tokens
- session cookies
- passwords
- private keys
- seed phrases
- credential file contents
- raw `.env` contents
- full stdout/stderr containing secrets
- personal account identifiers that are not needed for implementation

Safe to include:

- filenames
- relative repo paths
- event schema names
- adapter IDs
- redacted config shapes
- test names/results
- audit IDs
- build-log paths
- archive-note paths
- redacted error messages
- summaries of commands run

Never ask the system to expose hidden model chain-of-thought. The runtime event stream should expose action summaries, tool calls, file paths, commands, outcomes, approvals, and audit trails — not private reasoning.

---

## 4. Prompt 3 — Integration Closure Pass

Paste this into Codex/Antigravity, Claude Code, or the repo-aware agent that can see the current ChaseOS codebase after the Codex and Hermes passes have both run.

```text
We are running the Native Runtime Chat Control Plane Integration Closure pass.

This is the third pass after:
1. Codex/Antigravity created or scaffolded the ChaseOS Chat runtime event stream and UI cards.
2. Hermes created or scaffolded the runtime adapter/config event bridge for Hermes, OpenClaw, Codex, and future runtimes.

This is not a broad feature expansion.
This is not a Discord bot pass.
This is not enterprise sharing.
This is not a UI redesign.
This is not a runtime authority expansion.
This is not a hidden chain-of-thought viewer.

Goal:
Reconcile the Chat-side event stream with the runtime-side adapter bridge and prove the smallest safe vertical slice:

runtime emits structured event
→ ChaseOS accepts event
→ event is persisted or logged
→ Chat timeline renders event card
→ audit/build evidence exists

Required source documents:
- 06_AGENTS/Native-Runtime-Chat-Control-Plane.md
- 06_AGENTS/Native-Runtime-Chat-Control-Plane-Execution-Prompts.md
- 06_AGENTS/Native-Runtime-Chat-Control-Plane-Integration-Handover.md if present

Also read the final handovers/build logs from:
- the Codex/Antigravity Chat event-stream pass
- the Hermes Runtime Adapter + Backend Config Wiring pass

If those handovers are not available as files, inspect the files modified by both passes directly.

Core rule:
Do not broaden runtime authority to make the demo work.
A visibility event is not an execution permission.

What this pass must do:

1. Compare Codex and Hermes outputs
Identify:
- event schema created by Codex
- event schema/contract created by Hermes
- event transport selected by Codex
- event transport selected by Hermes
- persistence model used by Codex
- runtime emitter/spool/API bridge used by Hermes
- approval object shape used by Codex
- runtime approval event shape used by Hermes

Return a short compatibility table:

Codex field/behavior → Hermes field/behavior → compatible? → required patch.

2. Normalize the RuntimeEvent contract
If the two passes drifted, create the smallest compatibility patch.

The canonical event shape should include, where applicable:
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

Do not rename existing working fields unnecessarily.
Add compatibility shims only if needed.

3. Verify allowed event types
Minimum event types to support or explicitly defer:
- agent.acknowledged
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

If only a subset is implemented, state exactly which are live and which are scaffolded.

4. Verify event transport
Determine the actual transport used:
- WebSocket
- SSE
- polling
- direct backend API
- Agent Bus publish
- JSONL spool file
- SQLite/SQL event insert
- repo-specific equivalent

The transport must be local-first unless the repo already has an authenticated local backend boundary.
Do not introduce external network services for this closure pass.
Do not use Discord as the canonical transport.

5. Implement the smallest compatibility patch
If needed, patch:
- event emitter
- event ingestion endpoint
- event schema validation
- event persistence/logging
- frontend card adapter
- runtime event spool reader
- test fixtures

Keep this small.
Do not rebuild the Chat page.
Do not expand Hermes/OpenClaw/Codex authority.

6. Prove one runtime-originated event end to end
Use Hermes as the preferred first runtime if its bridge exists.
If Hermes bridge is not live, use the safest available local test emitter.

Minimum live proof:
- emit agent.acknowledged or run.started
- persist/log event
- expose event to Chat timeline transport
- render card or produce frontend-verifiable event payload
- write audit/build evidence

If UI cannot be exercised in the current environment, produce a backend/API/test-level proof and clearly state that visual UI verification remains pending.

7. Verify redaction and reasoning exclusion
The event path must not emit:
- API keys
- OAuth tokens
- provider tokens
- passwords
- seed phrases
- private credentials
- secret file contents
- raw hidden model reasoning

The event path may emit:
- action summaries
- safe file paths
- safe command previews
- redacted stdout/stderr previews
- event status
- approval metadata
- audit artifact references

Add or run tests for redaction if test harness exists.

8. Verify approval safety
Approval cards/events must remain scoped objects.

They must not be treated as:
- emoji approvals
- plain-text chat replies
- implied consent from message content
- broad session authority unless explicitly represented as a scoped decision object

If approval execution is not ready, recording a pending/blocked approval object is acceptable.
Do not make unsafe approvals live just for this closure pass.

9. Fail-closed validation
Add or run tests for:
- malformed event rejected
- unknown event type rejected or safely ignored
- event with forbidden secret-like payload redacted or rejected
- event with hidden_reasoning / chain_of_thought field rejected
- unauthorized adapter rejected or marked blocked
- runtime event without required run/session fields handled safely

10. Mandatory writeback
Create or update:
- build log
- documentation-history/archive note
- Build-Logs-Index.md if repo uses it
- Documentation-History-Index.md if repo uses it

Do not broadly update README/ROADMAP unless the live truth changed.

Out of scope:
- enterprise shared rooms
- cross-user agent messaging
- broad multi-agent autonomy
- unrestricted shell execution
- protected file writes
- canonical knowledge promotion
- public gateway exposure
- Discord runtime changes
- MCP expansion
- Home Assistant
- raw hidden reasoning display
- full app redesign

Acceptance criteria:
This pass succeeds if:
1. Codex/Hermes schema compatibility is audited.
2. Any schema/transport drift is patched or explicitly documented.
3. One runtime-originated event can move through the local event path.
4. The event is persisted/logged.
5. The Chat timeline can render it or receive a frontend-ready card payload.
6. Redaction and hidden-reasoning exclusion are enforced or tested.
7. Approval objects remain scoped and safe.
8. Malformed or unauthorized events fail closed.
9. Build/archive writeback exists.

Final handover must list:
1. exact files inspected
2. exact files modified
3. exact files created
4. Codex Chat-side schema/path found
5. Hermes/runtime-side schema/path found
6. compatibility issues found
7. compatibility patches applied
8. event transport confirmed
9. runtime event used for proof
10. persistence/log evidence
11. UI/card verification status
12. redaction/secret-handling verification
13. hidden-reasoning exclusion verification
14. approval safety status
15. tests run and results
16. what works live now
17. what remains blocked
18. exact build log path
19. exact archive note path
20. index update confirmations

Do not stop after proposing unless repo state makes implementation impossible.
Execute the smallest safe integration closure.
```

---

## 5. Handover template to paste back into ChatGPT

After the integration closure pass completes, paste back this structure:

```text
Native Runtime Chat Control Plane — Integration Closure Handover

1. Agent used:
- Codex / Antigravity / Claude Code / Hermes / other:

2. Files inspected:
-

3. Files modified:
-

4. Files created:
-

5. Codex Chat-side implementation found:
- schema path:
- transport:
- persistence/logging:
- UI/card files:

6. Hermes/runtime-side implementation found:
- adapter config path:
- event emitter path:
- event transport/spool/API:
- runtime tested:

7. Compatibility result:
- compatible as-is / patched / blocked:
- fields patched:
- event types live:
- event types scaffolded:

8. Live proof:
- runtime:
- event emitted:
- run/session ID:
- event persisted where:
- Chat/UI verified how:

9. Approval behavior:
- scoped object exists:
- execution live or pending:
- unsafe approval paths blocked:

10. Redaction / privacy:
- secrets excluded:
- hidden reasoning excluded:
- malformed/secret-like events rejected or redacted:

11. Tests:
- command/test name:
- result:

12. Build/archive writeback:
- build log:
- archive note:
- index updates:

13. Remaining blockers:
-

14. Recommended next pass:
-
```

---

## 6. What to do with outputs from Codex and Hermes before closure

Before running the integration closure pass, collect:

### From Codex / Antigravity

- final handover
- changed file list
- event schema path
- frontend card component path
- backend event ingestion path
- persistence/migration/log path
- test results
- build log path
- archive note path

### From Hermes

- final handover
- changed file list
- adapter config path
- event emitter path
- event transport or spool path
- runtime manifests/configs changed
- redaction policy
- hidden reasoning policy
- test results
- build log path
- archive note path

Then run Prompt 3.

---

## 7. Do not run this too early

Do not run the integration closure prompt before both earlier passes return results.

If you only have Codex output, run Hermes next.
If you only have Hermes output, run Codex next.
If both are partial, ask the closure pass to audit and stop at compatibility findings only.

The proper sequence is:

```text
Codex/Antigravity Chat-side pass
→ Hermes runtime/config pass
→ Integration closure pass
→ paste closure handover back to ChatGPT
→ next implementation pass
```
