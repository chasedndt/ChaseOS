---
title: ChaseOS MCP Safety Modes - V1 plus Active V2 Invocation Mode
type: architecture-doc
status: frozen - v1.2 2026-04-21; V1 modes unchanged; draft_execution active for workflow.invoke_bounded only
created: 2026-04-19
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Safety Modes

> Defines the four safety modes of the ChaseOS Runtime MCP.
>
> A safety mode is the authority envelope a runtime session operates in. It determines which surfaces are active, what outputs can be produced, whether approval is needed, and what risks the mode is designed to contain.
>
> V1 shipped with two active modes. Pass 6B activates `draft_execution` for `workflow.invoke_bounded` only. `approved_write` remains excluded.

---

## Mode Hierarchy Overview

```
read_only              <- most constrained; resources only
read_plus_proposal     <- resources + proposal tools; no execution
draft_execution        <- ACTIVE V2 - exact workflow.invoke_bounded allowlist only
approved_write         <- EXCLUDED - not V1; reserved for future write gate
```

Each mode is additive in the sense that a higher mode includes the capabilities of the lower, plus additional surfaces. However, each mode is also a distinct authority level — a runtime does not automatically start in `read_plus_proposal` just because it has been granted it in the past. The mode must be declared per session.

---

## Mode 1 — read_only

### What it can do
- Query any of the 9 V1 resources
- Receive curated, live vault state
- Discover server identity and capabilities

### What it cannot do
- Submit proposals
- Validate or preview proposals
- Create approval requests
- Invoke any tool
- Access deferred or excluded surfaces
- Modify canonical vault state in any way

### Outputs it may produce
- Read responses only (structured JSON or text)
- No artifact creation
- No vault writes

### Approval needed
None. Read is unconditional within this mode.

### Risks this mode contains
- **All write risk.** No tool exists in this mode that modifies any file.
- **All proposal drift risk.** No proposal surface exists.
- **All execution escalation risk.** No execution surface exists.
- **Schedule-as-execution-authority risk.** Schedule surfaces are deferred; even if exposed in a future pass, `read_only` would not include invocation tools.

### When to use
- Runtime sessions focused on context loading only (e.g., operator briefing assembly, sprint status check)
- Any runtime that does not need to propose vault changes
- Default mode for new or untrusted runtime sessions

---

## Mode 2 — read_plus_proposal

### What it can do
- All of `read_only`
- `proposal.submit` — stage a vault write proposal
- `proposal.validate` — validate a staged proposal
- `proposal.diff_preview` — generate a diff preview
- `approval_request.create` — create a human approval request artifact
- `handoff.runtime_draft_frame` — use the handoff prompt template

### What it cannot do
- Apply or commit a proposal to canonical vault state
- Invoke AOR workflows
- Access deferred or excluded surfaces
- Access shell, git, browser, or network bridges
- Read protected files (SOUL.md, Principles.md, Permission-Matrix.md, etc.)
- Approve its own proposals

### Outputs it may produce
- Read responses (same as `read_only`)
- Staged proposal artifacts (in a proposal staging area, not canonical vault)
- Diff previews (text artifacts, not vault writes)
- Approval request artifacts delivered to `07_LOGS/Operator-Briefs/` only

### Approval needed
- **For reading:** None.
- **For proposal staging:** None — the proposal is staged, not applied.
- **For protected-file proposal staging:** None at submit time. The staged artifact is flagged and `proposal.validate` returns the governance violation.
- **For proposal application:** Yes — human approval required. The MCP server does not approve proposals. Approval is a human action, not a tool call.

### Risks this mode contains
- **Write risk** is contained because no apply/commit tool exists. A staged proposal is an artifact, not a commit.
- **Execution risk** is contained because no execution tool exists.
- **Proposal drift risk** is the primary risk to watch in this mode. See `[[ChaseOS-MCP-Guardrails]]` for the specific guardrail.

### When to use
- Runtime sessions where the runtime may propose vault changes (e.g., proposing a Now.md update, a project OS status change)
- Autonomous briefing workflows that need to propose carry-forward items
- Any runtime session where a human-reviewed proposal workflow is appropriate

---

## Mode 3 - draft_execution (ACTIVE V2 - workflow.invoke_bounded only)

### Status
**Active V2.** Pass 6B activates `draft_execution` only for `workflow.invoke_bounded`. The grant exists in `runtime/mcp/config.yaml` and `runtime/mcp/safety.py` for explicitly configured runtime(s) only.

### What it can do in first release
- All of `read_plus_proposal`
- `workflow.invoke_bounded` for the exact first-release allowlist only:
  - `operator_today`
  - `operator_close_day`

Both workflows must remain `task_type: operator-briefing`, `role_card: operator-briefing`, `status: active`, `permission_ceiling: no_protected_file_writes`, and Stage 7 writeback limited to `07_LOGS/Operator-Briefs/`.

### What it does not do
- Invoke workflows outside the exact first-release allowlist
- Treat `task_type: operator-briefing` as a wildcard for future workflows
- Bypass AOR governance (manifest check, role card, task router, permission ceiling, audit)
- Call workflow handlers directly
- Accept handler names, module names, paths, schedule IDs, shell commands, git operations, browser actions, or network actions
- Apply, commit, approve, or promote canonical vault writes
- Access excluded surfaces

### Activation requirements
Bounded workflow invocation through MCP creates the highest single risk in the MCP surface: execution escalation. A runtime that can invoke workflows through MCP has more authority than a runtime that can only read and propose. Active `draft_execution` requires:

1. Full AOR routing at the MCP boundary
2. Exact workflow allowlist enforcement
3. Per-invocation role card and manifest preflight
4. Per-invocation MCP audit records with AOR audit references
5. Config-level `draft_execution` grants for specific runtimes
6. Tests proving denied workflow IDs, denied modes, and denied generic execution paths

Pass 6B satisfies these requirements for `openclaw` only. No other runtime is granted `draft_execution` unless config is deliberately updated.

### Risks this mode is designed to contain
- Execution authority is scoped to an exact workflow allowlist and AOR manifests — not ambient
- AOR governance cannot be bypassed; if AOR rejects the invocation, MCP does not override
- All invocations are audited; silent execution is not permitted
- Output is draft-safe/log-safe only; canonical writeback remains excluded

---

## Mode 4 — approved_write (EXCLUDED — Not V1)

### Status
**Excluded from V1.** This mode is defined here as a forward reference. It is not implemented and will not be implemented until an explicit architecture decision is made and recorded in the Decision Ledger.

### What it would do
- All of `draft_execution`
- Accept an approved proposal and apply it to canonical vault state, under Gate enforcement

### Why excluded from V1
The apply/commit path is the most dangerous surface in any vault-adjacent tool. Shipping it before the proposal workflow, the approval gate, and the bounded execution mode are all proven and stable is an unacceptable risk.

The correct sequencing is:
1. `read_only` → proven (V1)
2. `read_plus_proposal` → proven (V1)
3. `draft_execution` -> active but narrow (Pass 6B)
4. `approved_write` → enabled (well after 1-3 are stable)

Shortcutting this sequence by adding a write path in V1 would undermine the entire architecture.

### Risks this mode must eventually contain
- Every write must pass through Gate before landing in canonical vault state
- Protected files must be enforced at the write boundary, not just at the read boundary
- No write is silent — all writes produce an audit record
- No write is applied without explicit human approval on record

---

## Mode Assignment Rules

1. **Default for all new runtime sessions:** `read_only`
2. **Upgrade to `read_plus_proposal`:** Requires the runtime to be registered with a trust tier of Tier 2 or higher AND the session to explicitly declare `read_plus_proposal` mode
3. **Upgrade to `draft_execution`:** Requires an explicit config grant to that runtime, explicit session request for `draft_execution`, and the exact `workflow.invoke_bounded` implementation described in `[[ChaseOS-MCP-Workflow-Invocation]]`
4. **No runtime self-assigns a higher mode** — mode assignment is a permission grant from the operator, not a runtime capability
5. **Mode is per-session, not persistent** — a runtime that used `read_plus_proposal` or `draft_execution` in a prior session does not inherit that mode in the next session

---

## Failure Behavior Within Modes

If a request arrives for a surface not available in the current mode:

- The server returns a `domain_error` with code `surface_unavailable`
- The error includes the requested surface name, the current mode, and the minimum mode required
- No partial fulfillment — the request is rejected cleanly
- The rejection is logged to the audit stream

This prevents a runtime from discovering deferred surfaces through trial and error.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Workflow-Invocation]] · [[ChaseOS-MCP-Guardrails]] · [[ChaseOS-MCP-Data-Contracts]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Autonomous-Operator-Runtime]]*

*ChaseOS-MCP-Safety-Modes.md - v1.2 | Created: 2026-04-19 | Updated: 2026-04-21 Pass 6B (`draft_execution` active only for `workflow.invoke_bounded`; V1 modes unchanged)*
