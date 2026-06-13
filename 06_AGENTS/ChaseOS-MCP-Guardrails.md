---
title: ChaseOS MCP Guardrails - V1 plus Active V2 Invocation Guardrails
type: architecture-doc
status: frozen - v1.2 2026-04-21; V1 guardrails preserved; workflow.invoke_bounded active V2 guardrails implemented
created: 2026-04-19
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Guardrails

> Red-team analysis and explicit guardrails for the ChaseOS Runtime MCP V1.
>
> This document names the four most dangerous failure modes the MCP design must defend against, documents the specific guardrails for each, and provides smell tests for detecting authority creep during implementation.
>
> Read this alongside `[[ChaseOS-MCP-Safety-Modes]]` and `[[ChaseOS-MCP-Surface-Map]]`.

---

## Why Guardrails Are Written Before Implementation

MCP surfaces are easy to extend. A runtime requests a new capability, an implementer adds a handler, and suddenly the server does something the design never authorized. This is authority creep — not from malicious intent, but from the natural pressure to be helpful.

Writing explicit guardrails before implementation creates a documented standard against which every handler can be checked. If a proposed handler violates a guardrail, the violation is visible and named — not a silent drift.

---

## Red-Team Risk 1 — Workflow Invocation Risk

**Danger:** The MCP server becomes an execution escalator. A runtime submits what looks like a read request, or a handler added "just to be helpful" triggers execution outside the explicit AOR-governed invocation surface.

**Why this is the highest-risk path:**
- Workflow execution through MCP is only safe if it routes through AOR and preserves manifest check, role card enforcement, task router, permission ceiling check, Stage 6 handler dispatch, Stage 7 writeback, and Stage 8 AOR audit.
- A runtime that can invoke workflows through MCP has more effective authority than the permission matrix grants it.
- Execution side effects in the vault are not reversible without operator action.

**Current V1 status:** No V1 execution surface exists. The V1 boundary is enforced by absence.

**Active V2 status:** Pass 6B implements `workflow.invoke_bounded` under `draft_execution` only. The first-release allowlist is exactly `operator_today` and `operator_close_day`, routed through AOR only.

**V1 Guardrail:**
- No V1 handler may call `chaseos run`, `engine.run_workflow()`, or any AOR execution function.
- No V1 handler may write to canonical vault paths (anything outside the proposal staging area).
- If a future implementer proposes a "lightweight workflow trigger" as a resource query, reject it. Read resources do not trigger execution. If a handler needs to invoke a workflow, it is a tool.

**Active V2 Guardrail:**
- The only MCP workflow invocation tool is `workflow.invoke_bounded`.
- It is available only in `draft_execution`.
- It must call AOR, not workflow handlers directly.
- It must deny all workflow IDs except `operator_today` and `operator_close_day`.
- It must deny arbitrary handler names, Python modules, paths, schedule IDs, shell commands, git operations, browser actions, network actions, apply/commit instructions, approval flags, and canonical write intents.
- It must return bounded status/output-path summaries only, not full generated brief text or raw vault content.
- It must produce an MCP envelope audit record with AOR audit references before returning success.

**Detection during implementation:**
- In V1, any handler that imports from `runtime.aor.engine` is a hard stop.
- In V2, only the dedicated `workflow.invoke_bounded` implementation may import/call the bounded AOR invocation API, and that import must be reviewed against `[[ChaseOS-MCP-Workflow-Invocation]]`.
- Any resource or prompt that imports from `runtime.aor.engine` is a hard stop.
- Any tool that writes directly to `07_LOGS/Operator-Briefs/`, `07_LOGS/Agent-Activity/`, or `01_PROJECTS/` instead of returning through AOR/audit ownership is suspect.
- Any handler that calls `subprocess`, `os.system`, or `shutil` is a hard stop.

**Invocation-specific smell tests:**
- Does the request accept anything other than `workflow_id` plus manifest-declared inputs? If yes, stop.
- Does the allowlist include a workflow family wildcard instead of exact IDs? If yes, stop.
- Does the tool infer authorization from schedule intent or current time? If yes, stop.
- Does the response include full generated output content instead of artifact paths and status? If yes, stop.
- Can the client retry after unknown status and cause duplicate execution without operator visibility? If yes, stop and design idempotency/audit handling first.
- Can MCP return success if its own invocation audit write failed? If yes, stop.

---

## Red-Team Risk 2 — State Snapshot Overreach

**Danger:** `chaseos.current_truth` becomes an ambient vault mirror. The client requests increasingly broad state, the handler reads increasingly many files, and eventually the resource is returning the equivalent of a full vault dump.

**Why this matters:**
- Ambient vault access via MCP defeats the purpose of the curated interface — runtimes get everything they want without any scoping.
- A runtime that can read arbitrary vault content through `current_truth` effectively has the same access as one with direct filesystem access — but without the explicit governance that filesystem access creates.
- Protected file content could leak through an overreaching `current_truth` handler if the handler's file-read list is not strictly scoped.

**Guardrail:**
- `chaseos.current_truth` returns only schema-defined fields. The schema is fixed at implementation time.
- The handler reads exactly the vault files needed to serve each field. It does not read any file not in the field-to-source mapping.
- No dynamic field expansion. A client cannot request `current_truth?fields=*` and get all vault files.
- The field-to-source mapping is a hard-coded configuration, not a runtime parameter.
- If the client asks for a field that does not exist, the server returns `input_error`, not a partial result.

**Current V1 field budget for `chaseos.current_truth`:**
- `sprint_focus` → reads the current phase line from `00_HOME/Now.md` only
- `current_phase` → reads the phase header from `00_HOME/Now.md` only
- `active_domains` → reads the "Active Now" table from `00_HOME/Now.md` only
- `recent_decisions` → reads `07_LOGS/Decision-Ledger/Index.md` only (last N entries, no full entries)
- `open_loops` → reads the open loops sections from the relevant Project-OS files only

Each field maps to exactly one source. No field reads a protected file. No field reads raw quarantine content.

**Detection during implementation:**
- A handler that calls `glob()`, `os.walk()`, or any directory enumeration is a hard stop.
- A handler that reads more files than are listed in the field-to-source mapping is a hard stop.
- A handler that conditionally reads a file based on a client parameter is suspect — file access should not be client-controlled.

---

## Red-Team Risk 3 — Proposal Drift into Mutation

**Danger:** The proposal flow — submit, validate, diff, approval_request — quietly becomes a mutation path. Either the `proposal.submit` handler writes to a canonical vault path instead of a staging area, or a future "approval" tool is added that skips human review.

**Why this matters:**
- If proposals land in canonical vault paths, the "approval required" guarantee is false — runtimes are writing to the vault without human review.
- The approval model is the entire basis for why `read_plus_proposal` mode is safe. If the model is compromised, the mode is not safe.
- Proposal drift is subtle: a handler that writes to `01_PROJECTS/ChaseOS/ChaseOS-OS.md` instead of a staging path looks like a bug, not an attack. But the effect is the same.

**Guardrail:**
- Staged proposals are written to a dedicated proposal staging area only. The staging area is NOT a canonical vault path.
- The proposal staging area path is fixed in configuration and cannot be overridden by a client request.
- `approval_request.create` delivers an artifact (a human-readable approval request) to `07_LOGS/Operator-Briefs/` only. It does not apply the proposal.
- Audit records are written separately to `07_LOGS/Agent-Activity/` by the server/envelope through `MCPAuditLogger`, not by proposal or approval handlers.
- No V1 tool may read a proposal and apply it to a canonical vault path. The apply path does not exist in V1.
- If a handler is proposed that "applies an approved proposal," it is a V4 `approved_write` surface — it requires an explicit architecture decision, not an implementation shortcut.

**Detection during implementation:**
- Any handler that writes to a path outside the proposal staging area is a hard stop.
- Any handler that reads an "approved" flag from a proposal artifact and then modifies a vault file is a hard stop.
- Any handler named `proposal.apply`, `proposal.commit`, or `proposal.write` is not a V1 surface — reject it.

---

## Red-Team Risk 4 — Schedule-as-Execution-Authority

**Danger:** Schedule intent data, when exposed via MCP, is interpreted by a runtime as execution authorization. The reasoning: "The schedule says `operator_today` should run at 07:00 ET, it's 07:01 ET, therefore I am authorized to invoke it." This bypasses the AOR governance path and the OpenClaw cron control plane.

**Why this matters:**
- ChaseOS owns schedule intent; runtime adapters own execution. The split is intentional. It allows ChaseOS to change what is scheduled without changing execution mechanics.
- If a runtime can read schedule state and treat it as execution authorization, the split collapses. Every runtime becomes a scheduler, not just the designated adapter (currently OpenClaw).
- Double-execution becomes a real risk: OpenClaw fires at 07:00, a second runtime reads the schedule at 07:01 and fires again.

**Guardrail:**
- `schedule.intent.read` is deferred from V1. Schedule surfaces do not appear in the V1 surface map.
- When `schedule.intent.read` eventually lands (deferred), it returns schedule metadata only: schedule ID, workflow ID, cadence, enabled status, last run timestamp. It does not return an "is it time to run?" boolean.
- No V1 resource or tool returns a "should execute now" signal for any workflow.
- The `runtime_adapter_target` field in schedule intent enforces which adapter is the designated executor. A runtime that is not the designated adapter must not execute even if it reads schedule state.

**Detection during implementation:**
- Any resource that returns a "next_run_at" field paired with a "current_time" field and an "execute_authorized" flag is a hard stop.
- Any tool that accepts a schedule ID and invokes the corresponding workflow is both an execution escalation risk AND a schedule-as-authority risk — double stop.

---

## What V1 Must Never Expose

This is a compact checklist. Each item here is either a protected file, a governance file, a credential surface, or a path that would compromise one of the four red-team guardrails above.

**Protected vault files — never exposed, never readable through any resource:**
- `SOUL.md`
- `00_HOME/Principles.md`
- `00_HOME/Assistant-Contract.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Trust-Tiers.md`
- `06_AGENTS/Handoff-Protocol.md`
- `CLAUDE.md` (routing anchor — not for runtime query)

**Credential and configuration surfaces — never exposed:**
- `.env` files of any kind
- `.secret` files of any kind
- `credentials.yaml` or equivalent
- `.claude/settings.json` (Gate configuration)
- `.claude/hooks/` (hook scripts)
- `runtime/policy/` (policy files governing runtimes must not be queryable by those runtimes)
- `runtime/openclaw/soul.md` (runtime-local identity isolation)

**Raw content surfaces — never exposed:**
- `03_INPUTS/00_QUARANTINE/` content (Tier 4 untrusted — no runtime ingests without human triage)
- Full file dumps of any vault document
- Directory listings of any vault path

**Execution surfaces — never in V1:**
- Any tool that invokes `chaseos run`
- Any tool that calls AOR directly
- Any bridge to shell, git, browser, or network

**Active V2 exception:** `workflow.invoke_bounded` may call AOR only under `draft_execution` and only for the exact Pass 6A/6B allowlist. This exception does not apply to V1 and does not permit shell, git, browser, network, schedule coupling, or canonical writeback.

**Mutation surfaces — never in V1:**
- Any tool that writes to canonical vault paths
- Any tool that applies a staged proposal without human review

---

## Authority Creep Smell Tests

Run these tests against every proposed surface, handler, and configuration change during implementation. If any answer is "yes," stop and review.

| Smell Test | Stop Signal |
|---|---|
| Can a client trigger a workflow execution through a V1 surface? | Yes → stop |
| Can a V2 invocation request bypass AOR or the exact `operator_today` / `operator_close_day` allowlist? | Yes → stop |
| Does this resource return content from a protected file? | Yes → stop |
| Does this resource or tool write to a canonical vault path? | Yes → stop |
| Can a proposal be applied without a human approval step? | Yes → stop |
| Does this surface return schedule state that implies execution authorization? | Yes → stop |
| Does this handler call `glob()`, `os.walk()`, or any directory enumeration? | Yes → stop |
| Can a client supply a path parameter to control which file is read? | Yes → stop |
| Does this handler import from `runtime.aor.engine`? | Yes -> review carefully; only the active V2 invocation tool may do this |
| Does this handler write outside the proposal staging area? | Yes → stop |
| Is this surface named in the deferred or excluded sections of the surface map? | Yes -> stop; `workflow.invoke_bounded` is the only active V2 exception |
| Does this "prompt" make API calls or vault reads? | Yes → it's a tool disguised as a prompt; reclassify |
| Does adding this surface require updating the surface map? | Yes → update the map first, then implement |

---

## Governing Principle

Every guardrail in this document derives from one principle:

**The V1 MCP server's authority is bounded by what it is permitted to know and what it is permitted to stage. It cannot act. It cannot execute. It cannot promote. It cannot approve.**

The active V2 exception is narrow: `workflow.invoke_bounded` may request exactly allowlisted draft-safe AOR workflows under `draft_execution`. Any design choice that creeps from that exception toward generic action, generic execution, promotion, or self-approval is a violation of this principle, regardless of how incremental or well-intentioned the change appears.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Workflow-Invocation]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Data-Contracts]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Control-Plane]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]*

*ChaseOS-MCP-Guardrails.md - v1.2 | Created: 2026-04-19 | Updated: 2026-04-21 Pass 6B (`workflow.invoke_bounded` active V2 guardrails implemented; V1 guardrails preserved)*
