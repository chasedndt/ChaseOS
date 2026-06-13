---
type: framework-control
title: Handoff Protocol — ChaseOS Agent Layer
version: 1.0
created: 2026-03-20
scope: framework-level
---

# Handoff Protocol

> Defines how context, provenance, assumptions, open loops, and next actions are passed — between sessions, between agents, and across context boundaries.
> A handoff is any moment where one context window ends and another must begin with accurate understanding of what happened.
> Part of the Phase 4 Agent Control Plane — see `[[Agent-Control-Plane]]` for architecture context.

---

## Why Handoffs Matter

Agent sessions are ephemeral. The vault is not.

Every time a session ends — whether from context overflow, session close, or agent switching — the next session starts blind. Without a handoff protocol, context is rebuilt from scratch each time, leading to:
- Agents re-doing work that was already completed
- Agents unaware of open loops, contradictions, or blockers
- Loss of provenance (who decided what, why, and when)
- Stale Project-OS files being read as current when they are not

The handoff protocol ensures that the **vault is the handoff mechanism** — not chat history, not agent memory, not assumptions.

---

## Session Start Protocol

At the start of any session, an agent must:

### Step 1 — Read sprint state
```
Required: 00_HOME/Now.md
```
This file defines current phase, active domains, current structural truths, and immediate next actions. If it is more than two weeks old, treat it as unreliable and flag this to the user.

### Step 2 — Read project state
```
Required: 01_PROJECTS/[Relevant]-OS.md
```
Load only the project OS file for the project being worked. Do not load all project files simultaneously.

### Step 3 — Check for relevant open loops
If this session is continuing prior work, check the most recent build log for that project:
```
Optional: 07_LOGS/Build-Logs/[most-recent-for-project].md
```
Look for: unresolved contradictions, stated next actions, incomplete writeback items.

### Step 4 — Confirm understanding before acting
For non-trivial sessions, confirm understanding of the task and context before generating substantive output. If the task is ambiguous, ask before starting.

---

## Session Close Protocol

At the end of any substantive session, an agent must complete all applicable items:

### Writeback checklist
- [ ] Build log filed in `07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md`
- [ ] Project-OS updated if status, goals, or open loops changed
- [ ] New knowledge filed in `02_KNOWLEDGE/[Domain]/[topic].md` + linked in domain index
- [ ] Archive note created if this was a major pass (docs pass, architecture pass, refactor pass)
- [ ] Daily note updated or created if this was a substantive daily work session
- [ ] Any decisions filed using `Decision-Log-Template.md`

### Open loop documentation
Any item that was not resolved in this session must be explicitly documented:
- In the build log under "Open Loops / Unresolved Items"
- With a clear statement of what information or decision is needed
- Not left implicit — if it is not written, the next agent will not find it

### Handoff note (for context-overflow or agent-switch scenarios)
When a session ends due to context overflow, or when work is being handed to a different agent, include in the build log or as a separate handoff note:

```
## Handoff State
- Last completed action: [exact action taken]
- Next action in queue: [exact next step]
- Files created this session: [list]
- Files modified this session: [list]
- Open loops: [list with what is needed to resolve each]
- Assumptions made: [list]
- Contradictions found: [list with status — resolved/unresolved]
```

---

## Provenance Standards

Provenance = where did this content come from, and who decided it?

Agents must maintain provenance by:

1. **Attributing decisions to vault files, not to chat history** — "Per `TradingSystems-OS.md` Section 4..." not "As we discussed earlier..."
2. **Dating all outputs** — every file created or modified must include a date in frontmatter or footer
3. **Noting assumptions in build logs** — if a decision required an assumption (because context was ambiguous), it goes in the build log under "Assumptions Made"
4. **Flagging derived state** — if a project status was inferred from context rather than read from a Project-OS file, say so explicitly

---

## Context Priority Rules

When context sources conflict, resolve in this order:

1. **Current session instruction from user** — highest authority
2. **The relevant `Project-OS.md` file** — canonical project state
3. **`00_HOME/Now.md`** — canonical sprint state
4. **Build log entries** — recent history (check dates)
5. **Chat history or agent inference** — lowest priority; never treat as canonical

If a Project-OS file conflicts with `Now.md`, surface the conflict to the user rather than silently resolving it.

---

## Agent-Switch Handoffs

When a task moves from one agent type to another (e.g., from Claude Chat research to Claude Code implementation):

**The handing-off agent must produce:**
- A summary of what was done and what was decided
- The exact state of any files created or modified
- Open loops and unresolved questions
- The next specific action the receiving agent should take

**The receiving agent must:**
- Read the handoff note before acting
- Read `Now.md` and the relevant Project-OS file
- Confirm understanding of state before generating output
- Not assume prior session work is complete unless it is confirmed in the vault

---

## Context Overflow Handling

When a context window fills before a session is complete:

1. **Stop before overflow** — do not push to context limit and hope for the best
2. **Write a handoff state summary** into the current build log or a temporary handoff note
3. **Confirm what was completed** — list files created, files modified
4. **State exactly where the work stopped** — "Last action: X. Next action: Y"
5. **On resume** — the next session reads the handoff note and continues from the stated point

This is the same pattern used in the Phase 3 graph cleanup passes. It works.

---

## What Handoffs Are Not

- Not a substitute for writing work to the vault — if it is only in chat, it is not in the handoff
- Not a permission grant — a handoff note does not authorize the receiving agent to do more than its tier permits
- Not a way to bypass session-close protocol — the handoff must happen before the close checklist is complete

---

*Graph links: [[Vault-Map]] · [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[04_SOPS/Agent-Failure-Ambiguity-SOP|Agent-Failure-Ambiguity-SOP]] · [[Build-Logs-Index]] · [[Agent-Output-Conventions]]*

*Handoff-Protocol.md — Version 1.0 | Created: 2026-03-20 | Phase 4 — Agent Control Plane*
