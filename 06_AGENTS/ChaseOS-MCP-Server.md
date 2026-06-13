---
title: ChaseOS MCP Server
type: architecture-doc
status: design-freeze-complete - v2.1 2026-04-21; V1 surface map unchanged; Pass 6B workflow.invoke_bounded active V2
created: 2026-04-14
version: 2.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Server

> Design-freeze document for the ChaseOS Runtime MCP V1.
>
> This file defines what the server is, what it is not, what V1 exposes, the approval model, and how it fits into the existing ChaseOS control plane.
>
> **Implementation status:** Pass 4 V1 stdio scaffold is implemented in `runtime/mcp/`; Pass 6B adds the active V2 `workflow.invoke_bounded` surface.
> This document remains the design authority for the server identity, V1 surfaces, approval model, and boundaries.

---

## 1. Product Identity

**This MCP server is:**
- The internal ChaseOS Runtime MCP
- Local-first
- stdio-first initial transport
- Policy-heavy by design
- A bounded runtime-to-brain / runtime-to-control-plane interface
- ChaseOS-native — governed by the same Gate, trust tier, and permission architecture that governs all agent surfaces
- Proposal-disciplined — write proposals are artifacts, not commits
- Audit-aware — all queries are logged

**This MCP server is NOT:**
- The public Markdown Brain MCP Toolkit (that is a separate, forthcoming public product)
- A shell-first automation server
- A generic repo or vault browser
- A replacement for ChaseOS Gate
- A replacement for trust tiers or the permission matrix
- A broad ambient authority layer
- A full-autonomy pass
- An execution engine — AOR is the execution engine

The identity distinction matters. This is an internal governance-compliant runtime-to-control-plane interface. Every design decision flows from that identity.

---

## 2. Mission

**One sentence:** Provide AI runtimes with a governed, scoped, audit-safe interface to ChaseOS vault state and proposal capability — without granting ambient vault access or execution authority.

**Three purposes:**

1. **Context minimization.** Runtimes request specific named slices of vault state — current sprint focus, workflow registry, latest operator brief. No raw file dumps. No directory walks. Curated endpoints only.

2. **Personalization at runtime boundary.** Every runtime connecting to ChaseOS gets operator-specific context through a structured interface. As the vault deepens with build history, decisions, and briefs, the MCP server becomes richer. The "ages with the user" principle expressed at the runtime layer.

3. **Governance enforcement at the query boundary.** Without a governed interface, runtimes with filesystem access have no structural barrier to reading protected files or raw credentials. The MCP server enforces the same access rules as the Gate and permission matrix — regardless of what filesystem permissions the runtime technically holds.

---

## 3. V1 Philosophy

**Read-first.** The dominant capability in V1 is read. All resources are read-only. The server serves curated vault state, not arbitrary file access.

**Proposal-capable.** V1 includes a proposal tool surface — runtimes can submit, validate, preview, and request approval for vault changes. Proposals are staged artifacts. There is no apply path in V1.

**Approval-aware.** The proposal surface ends at approval request creation. A human approves proposals. The MCP server does not approve its own proposals.

**Audit-safe.** Every MCP query produces an audit record. No silent access. Runtime data access is inspectable.

**Stateless by default.** The server does not maintain session state. Each request is resolved against live vault state. No caching, no stale snapshots. The vault is the truth.

**Curated, not ambient.** Named resources, not filesystem paths. A client cannot request `/some/arbitrary/path`. It requests `workflows.registry`. The server resolves the resource to the correct underlying files.

---

## 4. Approval Model (Frozen)

V1 uses an **artifact-based approval model**, not a UI-based model.

This means:
- `proposal.submit` creates a staged proposal artifact
- `proposal.validate` checks the proposal against governance rules
- `proposal.diff_preview` generates a diff preview for human review
- `approval_request.create` generates a human-readable approval request artifact delivered to `07_LOGS/Operator-Briefs/`
- A human reviews and approves the proposal outside the MCP surface
- Canonical application happens through a separate, future write gate — not through the MCP server in V1

**What this means in practice:**
- No MCP tool call can modify canonical vault state in V1
- No approval_request.create call magically applies the proposal
- The artifact-based model requires no standalone UI to work — it delivers to vault log targets
- The model is safe to ship in V1 without a dedicated approval UI

**Excluded from V1:**
- `writeback.commit_canonical` — the apply/commit tool is excluded entirely from V1
- Any tool that accepts an approved proposal and applies it

Full surface classification: `[[ChaseOS-MCP-Surface-Map]]`

---

## 5. Role Relative to Gate, Trust Tiers, and Permission Matrix

The MCP server does not replace any existing governance layer. It operates under all of them.

**Relationship to ChaseOS Gate:**
- Gate rules apply to all vault writes, regardless of how they were initiated
- The MCP server does not write to canonical vault state in V1
- If a future write-capable version of the server lands, Gate enforcement must wrap every write
- The MCP server does not call Gate — Gate governs the vault; the MCP server governs what is queryable

**Relationship to Trust Tiers:**
- Runtimes connecting to the MCP server are assigned a trust tier per the existing tier model
- Tier assignment is enforced at the permission envelope (`runtime.permission_envelope` resource)
- A Tier 3 runtime gets fewer surfaces than a Tier 2 runtime
- The MCP server is a surface — it does not grant trust; it enforces the trust already assigned

**Relationship to Permission Matrix:**
- The Permission Matrix (`06_AGENTS/Permission-Matrix.md`) governs what agents can do per action and target
- The MCP server enforces the same rules at the query boundary
- A runtime cannot use the MCP server to read a protected file it could not otherwise read
- The Permission Matrix includes the MCP server as a named V1 surface as of Pass 4

**Relationship to AOR:**
- AOR is the execution engine; the MCP server is not an execution engine
- V1 surfaces remain read/proposal only and do not route into AOR
- Pass 6B adds one active V2 exception: `workflow.invoke_bounded` routes exactly `operator_today` and `operator_close_day` through AOR under `draft_execution`
- The MCP server does not call workflow handlers directly, spawn `chaseos run`, infer schedule authorization, or bypass AOR governance

---

## 6. Exposed Surfaces — V1 (Read and Proposal Only)

### Resources

| Resource | What It Returns | Authority | Notes |
|----------|----------------|-----------|-------|
| `runtime.identity` | Server name, version, phase, transport | low | Identity introspection only |
| `runtime.capabilities` | List of available resources, tools, prompts in current safety mode | low | Capability self-description |
| `chaseos.current_truth` | Curated vault snapshot: sprint focus, active domains, phase, recent decisions | medium | Curated schema — not full file dump |
| `workflows.registry` | Registered workflow IDs, names, statuses, task types | medium | Status only — not manifest content |
| `workflows.role_boundaries` | Role card names, write scope limits, forbidden zones | medium | Boundary view — not full card content |
| `runtime.permission_envelope` | Trust tier, allowed surfaces, forbidden surfaces for this runtime | medium | Per-runtime ceiling |
| `runtime.handoff.current` | Current handoff packet (open loops, carry-forward status) | medium | Structured handoff — not raw Now.md |
| `runtime.audit.recent` | Last N AOR activity events (summary only: workflow, status, timestamp) | medium | Audit stream — no full log content |
| `operator.briefing.latest` | Most recent operator brief (structured summary sections only) | low/medium | Summary — not full brief content |

### Tools

| Tool | What It Does | Authority | Notes |
|------|-------------|-----------|-------|
| `proposal.submit` | Stage a vault write proposal as an artifact | medium | Does not apply; stages only |
| `proposal.validate` | Validate a staged proposal against governance rules | medium | Checks protected file flags, permission ceiling |
| `proposal.diff_preview` | Generate a unified diff preview of a staged proposal | medium | Human-readable preview only |
| `approval_request.create` | Create a human approval request artifact for a staged proposal | medium | Delivers to `07_LOGS/Operator-Briefs/` only |

### Prompts

| Prompt | What It Does | Notes |
|--------|-------------|-------|
| `handoff.runtime_draft_frame` | Static prompt frame for drafting a runtime handoff request plan | Template-only; no vault reads or hidden context loading |

### Active V2 Tool

| Tool | What It Does | Authority | Notes |
|------|-------------|-----------|-------|
| `workflow.invoke_bounded` | Requests an allowlisted AOR workflow run | high | `draft_execution` only; exact allowlist `operator_today`, `operator_close_day`; no generic execution |

---

## 7. Never Exposed (Hard Limits)

These surfaces are excluded regardless of what the requesting runtime asks for, what trust tier it holds, or what safety mode is active.

| Surface | Why |
|---------|-----|
| `SOUL.md` | Protected identity file — never accessed by any external runtime |
| `00_HOME/Principles.md` | Protected doctrine |
| `00_HOME/Assistant-Contract.md` | Agent contract — runtimes governed by it must not query it |
| `06_AGENTS/Permission-Matrix.md` | Permission source — runtimes must not query their own limits |
| `06_AGENTS/Trust-Tiers.md` | Trust definitions — same reason as Permission Matrix |
| `06_AGENTS/Handoff-Protocol.md` | Session start/close protocol |
| Any `.env`, `.secret`, credentials file | Credential isolation is absolute |
| Raw quarantine content (`03_INPUTS/00_QUARANTINE/`) | Tier 4 untrusted — no runtime ingests without human triage |
| Arbitrary vault path navigation | The server exposes named resources, not a filesystem |
| `.claude/settings.json`, hook scripts | Gate configuration must not be queryable by governed runtimes |
| `runtime/policy/` files | Policy must not be queryable by the runtimes it governs |
| `runtime/openclaw/soul.md` | Runtime-local identity isolation must be preserved |
| Bulk vault export of any kind | Context minimization is a non-negotiable principle |

Full guardrail analysis: `[[ChaseOS-MCP-Guardrails]]`

---

## 8. Architectural Non-Goals

These are explicit non-goals. If a design choice moves toward any of these, it must be rejected.

- **Becoming an unrestricted vault API.** The server is scoped to named resources, not omniscient.
- **Becoming a write surface.** All canonical writes go through AOR Stage 7 → Gate. The MCP server does not bypass this.
- **Becoming a way to bypass trust tiers.** Trust is enforced at the query boundary, not trusted to the calling runtime.
- **Becoming a context dump service.** Narrow queries only. No bulk file exports.
- **Becoming a synchronization endpoint.** The vault is the truth; the MCP server serves it on request.
- **Becoming a generic execution surface.** V1 has no execution. Active V2 `workflow.invoke_bounded` is exact-allowlist AOR routing only.
- **Replacing ChaseOS Gate.** They serve different purposes. Gate governs writes. The MCP server governs what is queryable.
- **Becoming provider-specific.** No lock-in to any MCP SDK or transport variant that would make switching transports a breaking change.

---

## 9. Why This Exists in Phase 9

Phase 9 is the Operator Runtime phase. The central problem is: how do multiple runtimes (OpenClaw, Claude Code, n8n, future surfaces) get consistent, governed, up-to-date context about ChaseOS state without each runtime needing its own file-reading logic?

Without an MCP server:
- Each runtime must read raw vault files, requiring direct filesystem access (too broad) or manual context loading (expensive, error-prone)
- Runtimes build inconsistent mental models of vault state — stale, unverified, or contaminated by low-trust content
- There is no structural barrier to a runtime accidentally reading protected files

The MCP server solves these three problems in Phase 9:
1. Runtimes get a single governed interface to vault state
2. Context is always current (live vault reads, no caching)
3. Protected files are structurally excluded at the interface layer

This is the right phase to build it because:
- AOR is live and proven — the runtime architecture the MCP server supports is stable
- Operator Briefing V2 is complete — there is real vault state worth serving
- Native schedule layer is live — schedule intent is a real resource to expose
- OpenClaw is operational — there is a real MCP client that needs this

---

## 10. Implementation Target

**Passes 3 and 4 built:**

- Pass 3: File and module design — `runtime/mcp/` directory layout, module responsibility map, config schema, resource handler contracts
- Pass 4: stdio server scaffold — `runtime/mcp/server.py` entrypoint, resource/tool/prompt handlers, permission enforcer, audit logger, staging store, and V1 acceptance tests

**Implementation record:**
- This design-freeze document (complete — v2.0 2026-04-19)
- Surface map frozen (`ChaseOS-MCP-Surface-Map.md` — complete)
- Safety modes frozen (`ChaseOS-MCP-Safety-Modes.md` — complete)
- Guardrails documented (`ChaseOS-MCP-Guardrails.md` — complete)
- Data contracts frozen (`ChaseOS-MCP-Data-Contracts.md` — complete)
- Pass 4 build log: `07_LOGS/Build-Logs/2026-04-20-ChaseOS-phase9-mcp-stdio-scaffold-pass4.md`

**Built for V1 plus one active V2 surface.** `workflow.invoke_bounded` is live under `draft_execution`; no other deferred or excluded surfaces are implemented, and no MCP apply/commit path exists.

---

*Graph links: [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Scheduling-Intent-Architecture]] · [[Operator-Briefing-Architecture]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Control-Plane]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Guardrails]] · [[ChaseOS-MCP-Data-Contracts]] · [[ChaseOS-MCP-Diagrams]]*

*ChaseOS-MCP-Server.md - v2.1 | Created: 2026-04-14 (v1.0 placement doc) | Updated: 2026-04-21 (Pass 6B `workflow.invoke_bounded` active V2; V1 boundaries unchanged)*
