---
title: ChaseOS MCP Surface Map - V1 plus Active V2 Invocation
type: architecture-doc
status: frozen - v1.2 2026-04-21; V1 surfaces unchanged; workflow.invoke_bounded live as active V2
created: 2026-04-19
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Surface Map

> The complete V1 surface inventory for the ChaseOS Runtime MCP.
>
> A surface map defines every capability the MCP server exposes, defers, or excludes — with class, authority level, and rationale for each.
>
> This document is frozen for V1. Changes to V1 surfaces require a deliberate design decision, not a code change.
>
> Pass 6B implements `workflow.invoke_bounded` as the first active V2 surface. V1 remains unchanged, and no other deferred surface moves.

---

## What a Surface Map Is

A surface map answers three questions for every possible MCP capability:

1. **What class is it?** Resource (read-only state), Tool (action with side effects), or Prompt (structured template).
2. **What authority does it require?** How much vault access and trust is needed to serve it safely?
3. **Is it active?** Included in V1, active as V2, deferred to a later pass, or excluded permanently.

The surface map is the authoritative source for what the MCP server can do. No surface may be implemented that does not appear here as active or explicitly approved for the implementation pass.

---

## V1 Included Surfaces

### Resources — V1

| Resource URI | Class | Authority | Description | Guardrail |
|---|---|---|---|---|
| `runtime.identity` | Resource | low | Server name, version, ChaseOS phase, transport type | Metadata only — no vault content |
| `runtime.capabilities` | Resource | low | Available resources, tools, prompts in current safety mode | Reflects active mode; no filesystem disclosure |
| `chaseos.current_truth` | Resource | medium | Curated vault snapshot: sprint focus, phase, active domains, recent decisions | Schema-fixed fields only; no arbitrary path reads |
| `workflows.registry` | Resource | medium | Registered workflow IDs, names, task types, statuses | Status view only; no manifest content or handler code |
| `workflows.role_boundaries` | Resource | medium | Role card names, write scope, forbidden zones (summary) | Boundary view only; no full role card dump |
| `runtime.permission_envelope` | Resource | medium | Trust tier, permitted surfaces, forbidden surfaces for the requesting runtime | Per-runtime ceiling enforcement |
| `runtime.handoff.current` | Resource | medium | Current handoff packet: open loops, carry-forward status, sprint alignment | Structured output — not raw Now.md |
| `runtime.audit.recent` | Resource | medium | Last N AOR activity events: workflow_id, status, timestamp, files_written | Summary counts and recent entries only; no full log content |
| `operator.briefing.latest` | Resource | low/medium | Most recent operator brief structured sections: phase, decisions, carry-forward | Structured summary only; not full brief document dump |

**Resource authority model:** Resources are read-only. They never modify vault state. They serve live vault content through a curated schema, not raw file reads. Returning a field means knowing exactly which vault file it comes from — no ambient reads.

---

### Tools — V1

| Tool Name | Class | Authority | Description | Guardrail |
|---|---|---|---|---|
| `proposal.submit` | Tool | medium | Stage a vault write proposal artifact — does NOT apply the proposal | Artifact-based; no canonical write path in V1 |
| `proposal.validate` | Tool | medium | Validate a staged proposal against governance rules (protected file flags, permission ceiling, schema) | Validation only; no apply; no mutation |
| `proposal.diff_preview` | Tool | medium | Generate a unified diff preview of a staged proposal for human review | Preview only; no apply |
| `approval_request.create` | Tool | medium | Create a human approval request artifact delivered to `07_LOGS/Operator-Briefs/` | Delivers artifact; does not approve or apply |

**Tool authority model:** V1 tools are proposal-scope only. They create and validate staged artifacts. They do not modify canonical vault state. There is no apply/commit tool in V1. A human reviewer is the approval gate.

---

### Prompts — V1

| Prompt Name | Class | Authority | Description | Notes |
|---|---|---|---|---|
| `handoff.runtime_draft_frame` | Prompt | low | Structured prompt frame guiding a runtime to request the correct resources for session start | Template only; does not execute; does not query vault |

**Prompt authority model:** Prompts are structured templates. They are not disguised tools. A prompt does not make resource requests or trigger tool calls — it guides the runtime to do so explicitly. The distinction is enforced: a prompt that implicitly performs reads or writes is a tool, not a prompt.

---

## Active V2 and Deferred Surfaces

These surfaces are designed-and-named but excluded from V1. Pass 6B moves only `workflow.invoke_bounded` from the Pass 6A design target to active V2 implementation status. It remains unavailable in `read_only` and `read_plus_proposal`; it is exposed only in `draft_execution`.

| Surface | Class | Authority | Future Status / Reason |
|---|---|---|---|
| `workflow.invoke_bounded` | Tool | high | **Active V2** as of Pass 6B; exact first-release allowlist is `operator_today` and `operator_close_day`; routes through AOR only under `draft_execution` |
| `schedule.intent.read` | Resource | medium | Schedule intent layer is live in `runtime/schedules/` but exposing it via MCP creates schedule-as-execution-authority risk if done prematurely |
| `schedule.proposal.submit` | Tool | high | Schedule mutation is execution-adjacent — cannot land before bounded workflow invocation governance is proven |
| `source.workspace.lookup` | Tool | high | SIC workspace queries require full retrieval pipeline integration; authority scope is non-trivial to bound safely |
| `operator.briefing.synthesis_frame` | Prompt | medium | Requires tested synthesis prompt engineering against the four-layer briefing model before freezing |
| `proposal.drafting_frame` | Prompt | medium | Drafting guidance for proposal creation — deferred until proposal surface is validated in Pass 3/4 |

**Active V2 is narrow.** `workflow.invoke_bounded` is the only active V2 surface. It does not make any other deferred surface active and does not weaken excluded boundaries.

**Deferred != approved.** A deferred surface is a named candidate. Before any deferred surface is implemented, it requires: (1) a design pass, (2) a surface map update, (3) a guardrails pass, and (4) a data contract. The classification into V1 cannot be skipped by citing the surface's presence in this list.

---

## Excluded Surfaces

These are permanently excluded from the ChaseOS Runtime MCP. They are not deferred — they will not be added to a future pass without an explicit architecture decision that overrides this document.

| Surface | Class | Authority | Why Excluded |
|---|---|---|---|
| `writeback.commit_canonical` | Tool | very high | Canonical vault writes go through AOR Stage 7 → Gate. The MCP server is not a write surface in any version. |
| `bridge.shell` | Tool | very high | Shell access via MCP creates an execution escalation path with no containment boundary |
| `bridge.git` | Tool | very high | Git operations are irreversible and require operator awareness; not appropriate for MCP surface |
| `bridge.browser` | Tool | very high | Browser control is the FSOS Browser Sub-Track — a separate, governed surface with its own AOR workflow. MCP is not the right host. |
| `bridge.network` | Tool | very high | External network calls via MCP bypass the input adapter declaration model and create unaudited data ingestion paths |

**Excluded is permanent unless overridden by a formal architecture decision recorded in the Decision Ledger.** Excluded surfaces cannot be quietly added during implementation.

---

## Authority Classification Reference

| Authority Level | Meaning | V1 Ceiling |
|---|---|---|
| low | Metadata, self-description, public server properties | Yes |
| medium | Curated vault state, workflow/schedule status, proposals | Yes |
| high | Bounded workflow invocation, schedule mutation, SIC queries | `workflow.invoke_bounded` active V2; remaining high-authority surfaces deferred |
| very high | Canonical writes, shell/git/browser/network | Excluded entirely |

---

## Surface Count Summary

| Category | Count |
|---|---|
| V1 Resources | 9 |
| V1 Tools | 4 |
| V1 Prompts | 1 |
| **V1 Total** | **14** |
| Active V2 | 1 |
| Deferred | 5 |
| Excluded | 5 |
| **Grand Total Named** | **25** |

---

## Relationship to Safety Modes

Not all 14 V1 surfaces are available in all safety modes. The safety mode determines which subset is active for a given runtime session. The `draft_execution` column below is active V2 and currently grants only `workflow.invoke_bounded` beyond the V1 proposal/prompt tools.

| Surface | read_only | read_plus_proposal | draft_execution (active V2) |
|---|---|---|---|
| All 9 resources | yes | yes | yes |
| `proposal.submit` | no | yes | yes |
| `proposal.validate` | no | yes | yes |
| `proposal.diff_preview` | no | yes | yes |
| `approval_request.create` | no | yes | yes |
| `handoff.runtime_draft_frame` | no | yes | yes |
| `workflow.invoke_bounded` | no | no | yes - exact allowlist only |

Full safety mode definitions: `[[ChaseOS-MCP-Safety-Modes]]`

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Workflow-Invocation]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Guardrails]] · [[ChaseOS-MCP-Data-Contracts]] · [[ChaseOS-MCP-Diagrams]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Autonomous-Operator-Runtime]]*

*ChaseOS-MCP-Surface-Map.md - v1.2 | Created: 2026-04-19 | Updated: 2026-04-21 Pass 6B (`workflow.invoke_bounded` active V2; V1 active surfaces unchanged)*
