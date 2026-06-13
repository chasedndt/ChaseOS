---
title: Operator Briefing Architecture
type: architecture-doc
status: active — v1.0 defined 2026-04-14; Phase 9 pass; operator_today v2 design target
created: 2026-04-14
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# Operator Briefing Architecture

> Defines the layered architecture for daily operator briefings — how `operator_today` and `operator_close_day` should work as a two-node execution brain bridge, not as a generic vault-state summary.
>
> This document is the design authority for briefing behavior. The workflow manifests and handlers implement it.
> Live implementation target: operator_today v2 / operator_close_day v2.

---

## 1. Why This Architecture Exists

The current `operator_today` handler reads vault state and produces a structured summary. That is useful, but it is not yet what the briefing system should be.

The operator briefing must do three things that a simple vault summary cannot:

1. **Bridge the human brain and the runtime/AI brain.** The human brain holds judgment, intent, domain knowledge, and informal context that is not in any file. The AI/runtime brain holds what is in the vault: structured state, history, patterns, decisions. The briefing is the interface between them — it synthesizes runtime-accessible state into a human-actionable form without claiming to replace the human's judgment.

2. **Persist operating context across days.** A single session summary loses everything by the next morning. The briefing system must carry forward open loops, deferred items, priority shifts, and unresolved questions so that the operator does not have to rebuild context manually each morning.

3. **Make synthesis visible and labeled.** Any output that mixes canonical state with AI-generated suggestions without labeling is a trust trap. The operator cannot tell what to trust. The v2 briefing architecture enforces explicit labeling of every layer of its output.

---

## 2. The Four-Layer Model

Every operator briefing output is structured as four labeled layers. The layers are distinct, clearly separated in the output, and have different trust implications.

### Layer 1 — Canonical State

**What it is:** Current authoritative truth from vault files.

**Sources read:**
- `00_HOME/Now.md` — current phase, sprint focus, active domains
- All active Project-OS files for domains in the "Active Now" section of Now.md
- `ROADMAP.md` phase line — current phase and pass status
- `07_LOGS/Decision-Ledger/` — decisions from the last 7 days

**Trust level:** These are canonical state files. What they say is the authoritative current truth of the system.

**Output rule:** Present canonical state exactly as found. Do not interpret, summarize away contradictions, or smooth over inconsistencies. Contradictions must be flagged explicitly.

**Label in output:** `[CANONICAL]`

---

### Layer 2 — Carry-Forward

**What it is:** Context persisted from the previous `operator_close_day` run.

**Sources read:**
- Most recent close note in `07_LOGS/Operator-Briefs/` with file pattern `*-close-*` or `*-operator_close_day-*`
- Open loops section from that close note
- Deferred items noted in that close note
- Unresolved escalation flags from recent `07_LOGS/Agent-Activity/` records (last 48 hours)

**Trust level:** These are from a previous AOR run — they are runtime-sourced context, not canonical vault state. They represent what was true at close-of-day and may have changed since.

**Output rule:** Present carry-forward items as a distinct section. Explicitly note the date of the last close note. If no close note exists, state that no carry-forward is available.

**What this layer enables:**
- Open loops that were not resolved yesterday persist into today's view
- The operator does not need to manually re-read yesterday's session
- The runtime can detect what changed between yesterday's close and today (via Layer 3)

**Label in output:** `[CARRY-FORWARD: <date>]`

---

### Layer 3 — Sourced Context

**What it is:** Operationally relevant context that is not canonical state but is real and current.

**Sources read (selective — only what is relevant to current sprint):**
- `07_LOGS/Build-Logs/` — last 3 days of build log file names and their descriptors (not full content)
- `07_LOGS/Agent-Activity/` — AOR run records from last 48 hours (status counts only: success/escalated/failed)
- Quarantine queue depth — from `.chaseos/dedup_registry.json` entry count or `chaseos intake ls` output
- Project-OS files for domains marked "Active Now" — open loops section only (not full file)

**Trust level:** Sourced context is real operational data, not canonical truth. Build logs are accurate records; AOR activity is accurate audit data. Open loops from Project-OS files are project-level canonical state.

**Output rule:** Present sourced context with its source clearly labeled. Count-based data (quarantine depth, AOR run stats) is more reliable than qualitative interpretations.

**Label in output:** `[SOURCED: <source>]`

---

### Layer 4 — Synthesized Planner Output

**What it is:** AI-synthesized operational recommendations built from Layers 1–3.

**This layer is explicitly NOT canonical.** It is the runtime's reasoned synthesis, not vault truth.

**Contents:**
- **Priority synthesis** — given the sprint focus in Layer 1 and open loops in Layer 2, what deserves attention today in ranked order
- **Active build lane** — what engineering work is most aligned with Now.md's phase line and recent build logs
- **Trading session prep** — what market context is most relevant to the trading domains in scope today
- **Delegable tasks** — what tasks, if any, could be dispatched to AOR without human judgment
- **Human-only tasks** — what explicitly requires operator decision and cannot be delegated
- **Open loop check** — from Layer 2, which open loops are still live? Which may have resolved?
- **Operator recommendations** — 3–5 concrete suggested actions for today, ranked by alignment with canonical sprint focus

**Trust level:** This is AI-synthesized analysis. It is a starting point for the operator's judgment, not a replacement for it. Any recommendation here is a proposal — the operator decides what to act on.

**Output rule:**
- Each item must reference which Layer 1/2/3 inputs it was derived from
- Never embed Layer 4 output in canonical state files (Now.md, Project-OS files, ROADMAP.md)
- Output goes to `07_LOGS/Operator-Briefs/` only
- The operator may choose to act on a recommendation, but that action is operator-executed, not auto-written

**Label in output:** `[SYNTHESIS] — derived from: <source references>`

---

## 3. The Human–Runtime Brain Bridge Principle

The briefing system bridges two distinct cognition layers:

```
Human Brain                    Runtime/AI Brain
──────────────────────         ──────────────────────
Domain judgment                Structured vault state
Informal intent                Decision Ledger
Recent unlogged context        Build log history
Emotional state / energy       AOR execution records
Domain expertise               Knowledge taxonomy
Priorities not yet written     Project-OS open loops
                               ↕
                    ┌──────────────────────┐
                    │  Operator Briefing   │
                    │  (the bridge layer)  │
                    │                      │
                    │  Layer 1: Canonical  │
                    │  Layer 2: Carry-Fwd  │
                    │  Layer 3: Sourced    │
                    │  Layer 4: Synthesis  │
                    └──────────────────────┘
```

The briefing must never collapse the distinction between the two sides. The human brain holds things the vault does not. The runtime brain surfaces what the human may have forgotten or deprioritized. The bridge makes both visible — it does not claim to replace either.

**Anti-pattern to avoid:** A briefing that confidently states "your top priority today is X" without labeling that as Layer 4 synthesis has collapsed the bridge — it is silently presenting AI judgment as truth. This is the most dangerous failure mode of briefing systems.

---

## 4. Operator Close Day V2 Architecture

`operator_close_day` is the pair to `operator_today`. It runs at end-of-session and produces carry-forward state for the next morning's brief.

### Close Day Layers

**Capture Layer — What happened today?**
- Read all build logs from today (`07_LOGS/Build-Logs/YYYY-MM-DD-*.md`)
- Read AOR activity records from today (`07_LOGS/Agent-Activity/YYYYMMDD-*.json`)
- Accept operator-provided `notes` and `open_loops` inputs via CLI flags

**Delta Layer — What changed from morning to now?**
- Compare today's open loops (from operator inputs) against carry-forward from this morning's brief
- Which loops were resolved? Which opened? Which remain?
- Any priority changes explicitly logged in Decision Ledger today?

**Carry-Forward Layer — What must persist to tomorrow?**
- Open loops not resolved today — with explicit status (blocked / in-progress / deferred)
- Any deferred decisions that need the operator's attention tomorrow
- Active build state: which file/module is mid-work; what the next concrete step is
- Any escalations from AOR that need operator review

**Runtime Record Layer — What should AOR know for next execution?**
- Which workflows ran today and their outcomes
- Any patterns in AOR audit records that deserve operator attention
- Which scheduled intents (if any) need attention before next run

**Vault Writeback Rule:**
- Close note → `07_LOGS/Operator-Briefs/` (bounded writeback, same as open-day brief)
- Nothing in close-day goes to Now.md, Project-OS files, or canonical state
- If the operator decides to update canonical state based on the close note, that is a separate explicit operator action — it is never auto-written by AOR

---

## 5. What Never Goes Into Canonical State from Briefings

The following must NEVER be auto-written by the briefing system:

| Output | Reason |
|--------|--------|
| Now.md sprint focus updates | Sprint focus is operator-determined, not runtime-synthesized |
| Project-OS file open loop changes | Open loops are canonical project state — operator-maintained |
| ROADMAP.md phase line changes | Roadmap truth is explicit architectural decision |
| Decision Ledger entries | Decisions are immutable operator records, not AI suggestions |
| Knowledge promotions | Gate governs all promotion — no briefing can trigger it |
| Any file in `01_PROJECTS/` or `02_KNOWLEDGE/` | Project and knowledge state is operator-maintained |

The briefing synthesizes these inputs. It never rewrites them.

---

## 6. Explicit File Read List (v2 Target)

The operator_today v2 handler should declare and log every file read:

```
Required reads (always):
  00_HOME/Now.md
  01_PROJECTS/ChaseOS/ChaseOS-OS.md
  01_PROJECTS/TradingSystems/TradingSystems-OS.md
  01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md
  01_PROJECTS/University/Degree-OS.md
  ROADMAP.md (first 30 lines — phase status only)

Carry-forward read (if exists):
  07_LOGS/Operator-Briefs/ — most recent close note

Sourced reads (with explicit scope):
  07_LOGS/Build-Logs/ — file listing only for last 3 days
  07_LOGS/Agent-Activity/ — JSON status fields only, last 48h
  07_LOGS/Decision-Ledger/Index.md — last 7 days

Optional reads (only when relevant to active sprint):
  01_PROJECTS/[Domain]-OS.md for any domain with recent activity
  runtime/workflows/registry/ — manifest statuses (if AOR work is in sprint)
```

The briefing output must list every file it read in a "Sources read" footer section. This makes the synthesis auditable.

---

## 7. Output Structure

Every operator brief (open or close) must follow this structure:

```markdown
# Operator Brief — [OPEN|CLOSE] — YYYY-MM-DD

**Generated by:** AOR / operator_today v2
**Files read:** [explicit list]
**Carry-forward from:** [date of last close note, or "none"]

---

## [CANONICAL] Current State

[Phase, sprint focus, active domains — exactly as in vault]

---

## [CARRY-FORWARD: YYYY-MM-DD] Open Loops from Yesterday

[Persistent open loops, deferred items, unresolved escalations]

---

## [SOURCED] Operational Context

[Build log summary, AOR run stats, quarantine depth — with source labels]

---

## [SYNTHESIS] Today's Recommendations

> This section is AI-synthesized analysis. It is a starting point for your judgment, not a replacement for it. Sources used are listed inline.

### Priority Synthesis
...

### Active Build Lane
...

### Trading Session Prep
...

### Delegable Tasks
...

### Human-Only Tasks
...

### Open Loop Check
...

---

*Operator Brief — written to 07_LOGS/Operator-Briefs/ only — not canonical state*
*This document is synthesis output. Act on it at your discretion.*
```

---

## 8. Implementation Path

**Current state:** `operator_today` and `operator_close_day` implement a v1 briefing structure — they read vault state and produce a structured output, but do not implement the four-layer model, carry-forward mechanism, or explicit file read logging.

**v2 target:**
1. Add carry-forward read to `operator_today` handler — read most recent close note from `07_LOGS/Operator-Briefs/`
2. Add four-layer output structure to briefing template
3. Add explicit "Files read" logging to both handlers
4. Add delta detection in `operator_close_day` — compare open loops from morning brief against close-of-day inputs
5. Add "Runtime Record Layer" section to close-day output
6. Update both workflow manifests to reference this architecture doc

This is an engineering task for a future Phase 9 pass.

---

## 9. Relationship to Scheduling Intent

When the native Scheduling-Intent-Architecture is implemented, the briefing system gains a new capability: the scheduled execution of `operator_today` at a configured time (e.g., 0700 ET) means the operator wakes up to a brief already written.

The scheduling intent does not change the briefing architecture. It changes the trigger. The four-layer model, carry-forward mechanism, and canonical-state-isolation rules apply regardless of whether the brief was triggered manually or by a schedule.

See `06_AGENTS/Scheduling-Intent-Architecture.md`.

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Scheduling-Intent-Architecture]] · [[Permission-Matrix]] · [[Phase9-Adopted-Feature-Specification]]*

*Operator-Briefing-Architecture.md — v1.0 | Created: 2026-04-14 | Phase 9 Architecture Pass*
