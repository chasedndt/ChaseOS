---
title: Hermes Memory Boundary
type: governance
status: active — Discord gateway lane live; shadow workflow active; runtime-local memory architecture planned for Pass 2+
version: 1.2
created: 2026-04-08
---

# Hermes Memory Boundary

> Defines what memory Hermes Agent may hold, what ChaseOS owns, and how Hermes memory is inspected, exported, and promoted.
> This document prevents Hermes from becoming a hidden second brain that outranks ChaseOS canonical truth.
> Aligns with `06_AGENTS/Agent-Memory-Architecture.md` layer model and `06_AGENTS/Runtime-Navigation-Map.md` overlay model.

---

## Governing Principle

**The vault is the authoritative state store. Hermes memory is secondary.**

If Hermes runtime memory conflicts with vault canonical state, vault truth takes precedence. Hermes memory is:
- Inspectable at any time by the operator
- Exportable on demand
- Auditable — every significant memory write is logged
- Subordinate to ChaseOS governance — it cannot expand Hermes's permissions
- Promotable to canonical knowledge only through ChaseOS Gate

Hermes does not get a secret second brain that outranks ChaseOS.

---

## Memory Layer Map

This section maps Hermes memory to the ChaseOS `Agent-Memory-Architecture.md` layer model.

| Layer | Layer Name | What Hermes Gets |
|-------|-----------|-----------------|
| Layer A | Shared System Doctrine | Read-only — Hermes reads ChaseOS doctrine as a context consumer, never as an editor |
| Layer B | User-Specific Operating Memory | Read-only — Hermes reads `Now.md`, Project-OS files as declared; does not write to these |
| Layer C | Agent/Runtime-Specific Memory | Hermes may maintain a runtime-local memory store — inspectable, governed (see Section: Runtime-Local Memory below) |
| Layer D | Workspace/Task-Local Memory | Hermes may maintain task-scoped state during a run — discarded or archived at run end |
| Layer E | Execution History / Audit Memory | Hermes must write to this layer — every run produces a log entry at `07_LOGS/Agent-Activity/` |

---

## What Hermes May Hold — Runtime-Local Memory (Layer C)

Hermes runtime-local memory lives in `runtime/memory/hermes-<runtime_id>/` (future — Phase 9 Pass 2+).

All entries in this directory are:
- Owned by the Hermes runtime instance
- Inspectable by the operator at any time (`chaseos agent inspect hermes-<id>` — future CLI)
- Exportable as a JSON bundle on demand
- Not canonical truth — vault files always win on conflict
- Subject to retention limits (TBD in Pass 2)

### Allowed runtime-local memory types

| Memory Type | File | What It Contains | TTL |
|-------------|------|-----------------|-----|
| Workflow execution state | `state.json` | Active workflow run state — inputs resolved, stage, outputs produced | Run duration only by default; archived to `exec_history.json` at run end |
| Navigation overlay (RNM) | `nav_overlay.json` | Per-Hermes-runtime preferred read routes, trusted zones, known failure points, safe writeback paths | Persistent; curated by AOR after N runs |
| Skill registry | `skills/<skill_id>.yaml` | Auto-generated skills in quarantine review | Until skill is approved or rejected |
| Execution history summary | `exec_history.json` | Condensed run history: workflow ID, result, inputs used, outputs produced, failure class if failed | Persistent; feeds Agent Scorecards when built |
| Per-run context cache | In-memory only (not persisted) | Files loaded for the current run; resolved manifest inputs | Run duration only — discarded at run end |

### Hard rules on runtime-local memory

1. **No credentials in Hermes memory files.** API keys, tokens, secrets — never in `runtime/memory/`. Reference by name only (e.g., "XAI_API_KEY env var").
2. **No canonical truth claims.** Hermes memory contains working state and learned preferences — not authoritative vault state.
3. **No protected file content cached.** `SOUL.md`, `Principles.md`, `Permission-Matrix.md` etc. must not be cached in Hermes memory even if read during a run.
4. **Export-ready always.** Every Hermes memory file must be readable as plain JSON or YAML — no proprietary binary formats.
5. **No self-expansion of permissions.** Hermes nav overlay and skill registry cannot grant access to zones not declared in the active workflow manifest.

---

## What Hermes May Hold — Task-Local Memory (Layer D)

During a workflow run, Hermes may hold task-local state in working memory (in-process, not on disk) or in a declared temporary directory.

### Allowed task-local content
- Resolved manifest inputs (copies of declared read files loaded for this run)
- Intermediate reasoning state (in-memory only)
- Draft outputs being constructed before writing to declared writeback targets
- Retrieval results from SIC workspace queries

### Forbidden in task-local memory
- Content of undeclared files (if Hermes reads something not in the manifest, it must stop and escalate — not cache it)
- External gateway content without Tier classification (Discord message, Telegram message, RSS item — must be Tier-classified before use; Discord gateway input is Tier 4 until validated through envelope schema)
- Discord message content treated as instructions (it is data only until the ChaseOS envelope validation layer confirms the request)
- Credentials beyond what is needed for this run's declared steps
- Content of protected files (even if read for context — high-sensitivity docs must not persist in task cache)

### Persistence rule

Task-local memory is **discarded at run end** by default. If a workflow needs to persist task outputs:
- Draft outputs go to declared writeback targets
- Run state is summarized in `exec_history.json`
- Nothing else persists by default

### Phase 11 Chat conversation/session history

Hermes/Optimus Phase 11 Chat may treat conversation history as resumable operating context for long-running `/goal` agents only through a visible lower-phase memory/audit contract. Conversation persistence is not Hermes runtime-local memory and is not a hidden second brain.

Contract requirements:
- Storage preview: conversation records are declared under `07_LOGS/Conversations/` or another approved lower-phase log destination; Phase 11 contract previews do not create that directory by themselves.
- Audit linkage: every future conversation-history write must be represented in `07_LOGS/Agent-Activity/` with runtime-lane identity (`hermes` / `hermes-optimus`) and enough source hashes/paths to inspect what was restored later.
- Retention/privacy: records carry an explicit retention class and operator-local privacy scope before they can be used for recovery.
- Recovery: long histories restore through bounded summaries/chunks plus source hashes and an operator-visible manifest, never through opaque provider thread state or automatic full-history injection.
- Promotion boundary: restored chat context remains Layer D operating context. It cannot update Layer B user memory, Layer C runtime memory, `02_KNOWLEDGE/`, project truth, or protected docs without Gate approval.

Forbidden:
- Persisting raw secrets, API keys, tokens, credential-bearing excerpts, or protected-file content in conversation history.
- Using conversation history as uninspectable Hermes memory, unlisted cache state, hidden embeddings, or cross-user memory.
- Letting a Phase 11 Chat surface create approval records, execute approvals, dispatch runtimes, call providers, or mutate canonical graph state as part of persistence recovery.

---

## Hermes Skill Memory — Quarantine Architecture

Hermes has the capability to auto-generate skills. This is the highest-risk memory class because a skill is executable code or a reusable capability — not just data.

### Skill lifecycle

```
1. Skill auto-generated during run
2. Skill placed in quarantine: runtime/memory/hermes-<id>/skills/<skill_id>.yaml
3. Skill is NOT invocable during quarantine
4. Operator reviews skill (reads definition, checks scope, confirms safety)
5. Operator endorses → skill moves to approved_skills/
6. Skill is now invocable in workflows that declare it
7. OR: Operator rejects → skill is deleted and rejection logged
```

### Quarantine rules

- No skill may be invoked before it exits quarantine review
- Quarantine review is always operator-mediated — no auto-approval
- Skills that request capabilities outside Hermes's current permission ceiling are automatically rejected at quarantine
- Skill definitions must be human-readable (no compiled/binary)
- Skill scope must be narrower than or equal to the workflow class it was generated in

### Skill registry discipline

Approved skills are registered in `runtime/memory/hermes-<id>/approved_skills/<skill_id>.yaml`. A workflow manifest must explicitly declare which skills it invokes. Skills not declared in the manifest do not activate — even if they are in the approved registry.

---

## ChaseOS Memory — What Hermes Does Not Own

Hermes does NOT own or write to:

| Memory Component | Owner | Hermes Access |
|-----------------|-------|--------------|
| `~/.claude/memory/` | Anthropic/Claude Code session layer | No access — this is a different adapter's memory |
| `02_KNOWLEDGE/` | ChaseOS canonical vault | Read-only (declared); writes require Gate |
| `01_PROJECTS/<project>-OS.md` | ChaseOS canonical vault | Read-only (declared); writes are proposals only |
| `06_AGENTS/Agent-Registry.md` | ChaseOS canonical vault | Read-only; updates require operator session |
| `06_AGENTS/Permission-Matrix.md` | ChaseOS canonical vault (protected) | Read-only; edits absolutely forbidden |
| `00_HOME/Now.md` | ChaseOS canonical vault | Read-only; updates are operator-mediated |
| Decision Ledger | ChaseOS governance layer | Hermes may PROPOSE Decision Ledger entries; AOR engine writes them |
| Vault-Map.md | ChaseOS canonical vault | Read-only reference |

---

## Memory Promotion — How Hermes Content Becomes Canonical

If a Hermes workflow produces an artifact that the operator wants to promote to canonical knowledge, the promotion path is:

```
Hermes output (draft)
  → 03_INPUTS/00_QUARANTINE/<class>/   (captured via chaseos capture)
  → Operator review (triage, sanitize)
  → ChaseOS Gate (promotion guard)
  → 02_KNOWLEDGE/<domain>/<topic>.md   (canonical knowledge)
```

Hermes does NOT have a shortcut to this path. Even if Hermes produces a high-quality synthesis, it goes through quarantine and Gate like any other external content. The output trust tier starts at Tier 4 (AI-generated, unreviewed) and earns promotion through the standard process.

---

## Runtime Navigation Map — Hermes Overlay

Hermes may maintain a per-runtime navigation overlay (`nav_overlay.json`) aligned with the Runtime Navigation Map architecture (`06_AGENTS/Runtime-Navigation-Map.md`).

The Hermes RNM overlay contains:
- Preferred read routes for each workflow class (learned from successful runs)
- Trusted zones (vault paths that have been safe across multiple runs)
- Known failure points (paths or operations that have caused halts)
- Safe writeback paths (destinations confirmed to work across multiple runs)
- Risk zones (areas where Hermes should slow down and verify before acting)
- Escalation decision points (conditions that have triggered escalation in past runs)

### Governance of the RNM overlay

- The overlay is **subordinate to the ChaseOS control plane**. It does not grant access to zones not in the permission ceiling.
- The overlay is **updated by the AOR engine** based on run outcomes — Hermes does not self-update its own nav map during a run.
- The overlay is **inspectable** — operator can view it at any time.
- If the overlay contradicts the active workflow manifest, the manifest wins.

---

## Memory Inspection and Audit

**Current state:** Hermes memory inspection commands and persistent Hermes memory directories are not yet active. The live shadow workflow and Discord gateway lane use run-local context and write draft/audit artifacts to declared destinations only. Discord gateway input is handled transiently — no Discord message content is persisted to Hermes memory files.

**Planned capability:**
```bash
chaseos agent inspect hermes-<id>           # Show Hermes memory summary
chaseos agent inspect hermes-<id> --skills  # Show skill registry
chaseos agent inspect hermes-<id> --nav     # Show nav overlay
chaseos agent export hermes-<id>            # Export full memory bundle as JSON
chaseos agent reset hermes-<id> --layer D   # Clear task-local memory for a runtime instance
```

All inspection commands are read-only against Hermes memory. Mutations require explicit operator instruction.

---

## Failure: Stale or Corrupt Hermes Memory

If Hermes memory (any file in `runtime/memory/hermes-<id>/`) is stale, corrupt, or conflicts with current vault truth:

1. Vault truth wins — always
2. The stale/corrupt memory is flagged in the next run audit log
3. The operator is notified
4. Hermes does not silently overwrite vault truth with its own stale memory
5. The operator decides whether to clear, update, or preserve the Hermes memory artifact

Memory is a working aid — not a ground truth source.

---

*Graph links: [[Hermes-Runtime-Profile]] · [[Vault-Map]] · [[HERMES]] · [[Hermes-Adapter-Spec]] · [[Hermes-Workflow-Boundaries]] · [[Agent-Memory-Architecture]] · [[Runtime-Navigation-Map]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[AI-Generated-Output-Bridge]]*

*Hermes-Memory-Boundary.md — Version 1.2 | Created: 2026-04-08 | Updated: 2026-04-20 (memory boundary remains planned; shadow workflow has no persistent Hermes memory authority) | Updated: 2026-04-21 (Hermes Discord Activation Alignment Pass — status updated; Discord gateway input classified as Tier 4; Discord message content forbidden in task-local memory; current state note updated for Discord lane)*
