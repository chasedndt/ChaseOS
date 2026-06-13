---
type: framework-control
title: Claude Memory System — ChaseOS
version: 1.0
created: 2026-03-20
scope: Anthropic Agent Harness (execution adapter)
---

# Claude Memory System

> Defines how the Claude Code persistent memory system (`~/.claude/`) relates to ChaseOS.
> Covers what belongs in memory, what must never go there, how it is kept current, and the risks of stale memory.
> This is a component of the Anthropic execution adapter lane — it does not apply to advisory surfaces or other adapters.
> Execution adapter: `[[CLAUDE]]` · Standard: `[[Execution-Adapter-Standard]]` · Security: `[[Agent-Security-Model]]`

---

## 1. What the Claude Memory System Is

Claude Code supports a persistent, file-based memory system stored outside the vault at:

```
~/.claude/projects/[encoded-project-path]/memory/
```

For this vault instance, the memory lives at:
```
%USERPROFILE%\.claude\projects\C--Users-chaseos-Documents-chaseos-obsidian\memory\
```

Memory files are loaded into Claude Code's context automatically at session start. They supplement the vault — they do not replace it.

**The vault is the authoritative state store. Memory is a session-start accelerant.** If they conflict, the vault wins. Stale memory must be corrected from vault content, not acted on.

---

## 2. Memory File Structure

Memory is organized as individual files with frontmatter + content, indexed by a `MEMORY.md` file.

### MEMORY.md
The index file. Loaded automatically into every session. Lines after 200 are truncated — keep it concise. Contains links to individual memory files with brief descriptions. Never contains memory content directly — it is an index only.

### Individual memory files
Each covers a single topic, named semantically (e.g., `feedback_build_logs.md`, `user_role.md`). Contains frontmatter with:
- `name` — the memory name
- `description` — one-line description (used to judge relevance; be specific)
- `type` — `user` | `feedback` | `project` | `reference`

---

## 3. Memory Types

### user
Information about Chase's role, goals, responsibilities, and working style. Used to calibrate response tone and depth.

**Save when:** You learn details about the user's role, expertise level, or preferences.

**ChaseOS examples:**
- Chase is a builder/trader/founder operating across 18 domains in ChaseOS
- Primary engineering work is in full-stack web2/web3 and trading systems
- Active trading with daily morning thesis workflow

### feedback
Guidance on how to approach work — corrections and confirmed approaches. The most operationally critical memory type.

**Save when:** The user corrects an approach OR confirms a non-obvious approach worked.

**Structure:** Lead with the rule → **Why:** line → **How to apply:** line.

**ChaseOS examples:**
- Always create a build log in `07_LOGS/Build-Logs/` after every prompt that produces vault changes
- Write build logs directly — do not prompt the user to do it manually

### project
Facts about ongoing work, goals, initiatives, and in-progress decisions not derivable from current code or git history.

**Save when:** You learn who is doing what, why, or by when. Convert relative dates to absolute.

**ChaseOS examples:** Current phase, active blockers, deferred decisions.

### reference
Pointers to where information lives in external systems.

**Save when:** You learn about external resources and their purpose.

**ChaseOS examples:** Which n8n instance URL, which exchange API endpoint, which Discord server is used for a specific workflow.

---

## 4. What Must Be Mirrored From ChaseOS Into Memory

Memory should not duplicate vault content — it should capture what is *not derivable by reading the current vault*. The right question: "Will a future session reasonably need this, and would it require loading multiple vault files to reconstruct it?"

### High-value memory for ChaseOS

| Memory type | What to capture | Why |
|-------------|----------------|-----|
| feedback | Build log and writeback rules — the ones users have had to correct | Prevents repeated corrections |
| feedback | Protected-file behavior — any time the user had to remind about per-file approval | Prevents unauthorized edits |
| feedback | Response style preferences — length, tone, preamble behavior | Session quality |
| feedback | Confirmed non-obvious approaches (architectural decisions validated by user) | Preserves validated judgment |
| project | Current phase and what Phase 5B covers | Prevents re-reading full ROADMAP |
| project | Any active deadline or blocker that doesn't belong in a public vault file | Time-sensitive context |
| user | Chase's domain expertise profile | Calibrates depth and framing |
| reference | Location of external credentials (by name, never by value) | Avoids repeated lookup |

### What memory should NOT duplicate
- Code patterns, file paths, vault conventions — derivable by reading current vault state
- Git history or recent changes — `git log` is authoritative
- Build log content — the file is the record; memory is not a summary layer
- Anything already in CLAUDE.md or documented framework files
- Ephemeral session context that only matters within this conversation

---

## 5. What Memory May Never Contain

These are hard rules, not guidelines:

- **Credentials or secrets of any kind** — API keys, passwords, tokens, private keys. Reference by name/location only. See `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]`.
- **Protected file drafts or pre-edit content** — memory is not a staging area for edits to SOUL.md, CLAUDE.md, Permission-Matrix.md, or any other protected file
- **Unverified claims from Tier 3 or Tier 4 sources** — memory is not a shortcut around the ingest SOP
- **PII or sensitive personal data** that should not appear outside the vault
- **Fabricated or inferred vault state** — do not save what you think is true about the vault; save only what you have confirmed by reading it

---

## 6. How Memory Is Updated

Memory is maintained by the Claude Code harness during sessions. The protocol:

### When to save a new memory
- User explicitly asks you to remember something
- You receive a correction — save the corrected behavior immediately
- You confirm a non-obvious approach worked — save the validated judgment
- You learn a project fact that future sessions would benefit from knowing

### How to save
1. Write the memory to its own file in `~/.claude/projects/.../memory/[name].md` with correct frontmatter
2. Add a pointer + one-line description to `MEMORY.md`

### When to update an existing memory
- Vault state that memory describes has changed — update or remove the memory
- A memory's claim conflicts with current vault content — vault wins; update memory
- A saved rule has been superseded by new user feedback

### When to remove a memory
- User explicitly asks to forget something
- The memory is demonstrably stale and can no longer be trusted
- The underlying project, tool, or convention it describes no longer exists

---

## 7. Stale Memory Risks

Memory records what was true when it was written. It degrades over time as the vault evolves.

### Risk scenarios

| Scenario | Risk | Mitigation |
|----------|------|-----------|
| Memory names a file that was renamed or deleted | Claude recommends a path that doesn't exist | Verify file existence before recommending it from memory |
| Memory names a function or flag that was removed | Claude references non-existent code | Grep before recommending |
| Memory captures phase state that has changed | Claude operates under an outdated model of what's active | Re-read Now.md; update memory if stale |
| Memory captures a user preference that has shifted | Claude applies an outdated behavioral rule | Update on next user correction |

**Rule:** A memory that names a specific file, function, flag, or vault state is a claim about what was true when it was written — not what is true now. Before acting on such a memory, verify against current vault state.

---

## 8. Phase 4–6 Context in Memory

The following facts are worth maintaining in memory for ChaseOS session efficiency — they reduce the number of files that need to be re-read each session:

**Feedback memories to maintain:**
- Always create a build log at session end — write it directly, do not prompt the user
- Always update Build-Logs-Index.md when a new build log is created
- Always create an archive note for major passes; update Documentation-History-Index.md
- Read Now.md at the start of every session

**Project memories to maintain (update when they change):**
- Current ChaseOS phase: Phase 6D — Operational Readiness (active as of 2026-03-21)
- Phases 1–6C complete. Phase 6D adds: Promotion-Session-SOP.md, Ingestion-Cadence.md, memory seeded, truth docs updated
- Phase 6 preflight tasks: **COMPLETE** — hook backstops configured and verified ACTIVE; `~/.claude/` memory seeded 2026-03-21
- ChaseOS Gate: ACTIVE VERIFIED (Anthropic lane). All 4 hooks live-tested 2026-03-21. Interpreter: `.venv/Scripts/python.exe`
- Promotion gate: `CHASEOS_PROMOTION_APPROVED=1` env var required for writes to `02_KNOWLEDGE/`. See `Promotion-Session-SOP.md` for the full session protocol
- Knowledge taxonomy: six classes operational (`user-origin`, `source-derived`, `synthesized`, `generated-ideas`, `system-operational`, `canonical-state`). Every promoted note requires `knowledge_class` frontmatter

**Feedback memories NOT to maintain in memory (already in CLAUDE.md):**
- Read order, writeback targets, protected file list — these are in CLAUDE.md and loaded per-session
- Do not duplicate CLAUDE.md content in memory

---

## 9. Relationship to CLAUDE.md

`CLAUDE.md` is the execution adapter routing anchor — it governs how this session operates. It is loaded from the vault at session start.

The memory system is the cross-session persistence layer — it carries behavioral rules and project facts that survive session resets.

They are complementary, not redundant:
- CLAUDE.md: routing, read order, writeback discipline, protected files, failure behavior
- Memory: behavioral corrections, confirmed approaches, project state facts, user profile

If they appear to conflict, CLAUDE.md (vault truth) takes precedence. Update memory to resolve the conflict.

---

## 10. Memory for Future Execution Adapters

When other execution adapters become active (OpenAI Agent Harness, Local/OSS harnesses), their memory systems — if they have one — follow the same principles:

- Vault is authoritative; adapter memory is secondary
- Credentials may never be stored in adapter memory
- Memory captures what is not derivable from vault content
- Stale memory must not override current vault state
- Memory update rules mirror the process above

Each adapter's memory system is documented in its own adapter doc (`OPENAI.md`, `LOCAL-OSS.md`, `N8N.md`) under the Memory Rules section.

---

*Graph links: [[Hermes-Runtime-Profile]] · [[CLAUDE]] · [[Execution-Adapter-Standard]] · [[Agent-Security-Model]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Handoff-Protocol]] · [[Backends-Supported]] · [[Vault-Map]] · [[ROADMAP]]*

*Claude-Memory-System.md — Version 1.1 | Created: 2026-03-20 | Phase 5B — Repo / Runtime Binding | Updated: 2026-03-21 (Phase 6D — Section 8 updated: Phase 5-era language replaced with Phase 6D truth; preflight tasks now complete; Gate ACTIVE VERIFIED; promotion gate and taxonomy noted)*
