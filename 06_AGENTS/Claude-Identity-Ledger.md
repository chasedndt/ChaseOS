---
title: Claude Identity Ledger
type: runtime-identity-ledger
status: seeded-operational
version: 0.1
created: 2026-04-27
updated: 2026-04-27
runtime: claude
memory_layer: C
---

# Claude Identity Ledger

> First human-readable Agent Identity Ledger for the Claude / Anthropic Agent Harness lane.
> This is a behavioral record and inspection surface, not a permission source.

Machine-readable ledger:
- `runtime/memory/adapters/claude/identity-ledger.json`

Schema:
- `runtime/memory/adapters/_identity_ledger_schema.json`

---

## Current Actor Posture

Claude is the primary vault-writing engineering and documentation harness for the Anthropic lane.

Current posture:
- Execution surface: Claude Code CLI / Anthropic Agent Harness.
- Access mode: direct vault read/write through the local filesystem when operating in the configured harness.
- Trust ceiling: Tier 2 per `06_AGENTS/Agent-Registry.md`, bounded by Gate, Permission Matrix, protected-file rules, and operator approval.
- Primary value: repo-grounded implementation, truth-sync, documentation continuity, and writeback discipline.

This ledger does not expand Claude's authority. It records behavioral expectations and evidence-backed tendencies for future inspection.

---

## Evidence Sources

Current seed sources:
- `CLAUDE.md`
- `06_AGENTS/Agent-Registry.md`
- `06_AGENTS/Claude-Memory-System.md`
- `06_AGENTS/Agent-Memory-Architecture.md`
- `07_LOGS/Build-Logs/`
- `07_LOGS/Agent-Activity/`

No dedicated `runtime/memory/scorecards/claude.json` exists in this pass. Workflow history is therefore log-backed and human-readable, not scorecard-derived.

---

## Behavioral Baseline

Expected tendencies:
- Read current vault truth before acting.
- Treat the vault as authoritative over chat memory or adapter memory.
- Keep implementation truth, documentation truth, logs, daily notes, and indexes aligned.
- Make narrow, evidence-backed edits to protected governance surfaces.
- Preserve the distinction between complete, partial, planned, docs-only, and unverified work.

---

## Doctrine Adherence Posture

Seeded expected disciplines:
- Repo-truth preflight before meaningful edits.
- Build log and documentation-history writeback for meaningful passes.
- Daily note and index linkage.
- Agent Activity logging for runtime, adapter, operator, Gate, automation, and control-plane work.
- No secrets or credentials in memory, logs, docs, sidecars, or ledger records.
- No permission escalation from memory records.

Current evidence state:
- Governance and memory doctrine are documented.
- Build logs and agent activity logs provide execution history.
- A dedicated Claude scorecard and automated identity-drift scoring are not yet built.

---

## Correction History

| Correction | Status | Evidence |
|-----------|--------|----------|
| Build logs must be written directly and indexed after meaningful vault changes. | Standing rule | `06_AGENTS/Claude-Memory-System.md`, `07_LOGS/Build-Logs/Build-Logs-Index.md` |
| Adapter memory accelerates orientation but current vault files win on conflict. | Standing rule | `06_AGENTS/Claude-Memory-System.md`, `06_AGENTS/Agent-Memory-Architecture.md` |
| Protected truth files require narrow, repo-grounded edits. | Standing rule | `06_AGENTS/Permission-Matrix.md`, `CLAUDE.md` |

---

## Drift Signals

No dedicated drift signals are recorded in this first ledger.

Future drift signals should be added only when supported by repeated logs, explicit operator correction, or validated scorecard evidence.

---

## Boundaries

The Claude Identity Ledger is Layer C memory. It is advisory.

It cannot:
- raise trust tier
- approve protected-file edits
- bypass Gate policy
- override role cards, workflow manifests, Permission Matrix, or operator approval
- replace current vault truth
- convert a single incident into durable behavioral memory without confirmation

---

## Current Verdict

This pass makes the Agent Identity Ledger operational in first form for the primary Claude / Anthropic lane.

The result is COMPLETE for the Phase 9 formal-file foothold:
- human-readable ledger exists
- machine-readable ledger exists
- memory inspector can surface identity ledger presence and detail
- docs now distinguish identity from authority

Remaining future work:
- add automated scorecard inputs for Claude if/when the lane has structured execution records
- add drift/adherence scoring only after evidence accumulation
- build Phase 10 identity-ledger UI surfaces

---

*Graph links: [[Hermes-Runtime-Profile]] · [[Agent-Memory-Architecture]] * [[Claude-Memory-System]] * [[Agent-Registry]] * [[Permission-Matrix]] * [[Trust-Tiers]] * [[CLAUDE]]*

*Claude-Identity-Ledger.md - v0.1 | Created: 2026-04-27 | Agent Identity Ledger first formal-file foothold*
