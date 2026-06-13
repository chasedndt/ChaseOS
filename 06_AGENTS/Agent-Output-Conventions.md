---
type: agent-knowledge
title: Agent Output Conventions
scope: framework-level
updated: 2026-03-19
---

# Agent Output Conventions

> Framework-level conventions for all agents operating in ChaseOS.
> This file applies to any agent backend — Claude, OpenAI-based agents, OpenRouter-backed systems, future operator workflows, or any other AI tool with vault write access.
> Claude-specific routing rules live in `CLAUDE.md`. This file governs the wider framework.

---

## 1. Framework Is Agent-Agnostic

ChaseOS is not Claude-specific. The framework is designed to work with any agent backend that can read markdown files and write structured outputs.

Supported and future-planned backends include:
- **Claude Code** — current primary engineering assistant
- **Claude Chat** — research and synthesis
- **OpenAI / GPT-based agents** — possible future backend
- **OpenRouter-backed agents** — multi-model workflows
- **n8n automation agents** — scheduled workflow execution
- **OpenClaw / custom operator systems** — future long-running operator layer
- **Any text-capable AI tool** — the vault structure is plain markdown

The underlying conventions — file structure, routing rules, writeback targets, SOP/template usage — must work for all of these, not only Claude.

---

## 2. What Agents Must Do

All agents operating in ChaseOS must:

1. **Read before writing.** Load the relevant Project-OS file and `Now.md` before taking action on any project.
2. **Use canonical files.** Project state lives in Project-OS files. Domain knowledge lives in `02_KNOWLEDGE/`. Don't fabricate state that isn't in the vault.
3. **Follow SOP/workflow files.** These are process definitions for agents to execute, not user admin guides. See `04_SOPS/`.
4. **Use templates.** When generating a log, journal entry, session record, or structured output, use the relevant template from `05_TEMPLATES/`.
5. **Write back to the correct target.** All outputs must land in their correct folder. See Section 4.
6. **Date outputs.** Any time-stamped output (logs, thesis entries, journal entries) must include date in filename and frontmatter.
7. **Respect trust boundaries.** See `00_HOME/Assistant-Contract.md` for what agents may and may not do.

---

## 3. Output Types and Definitions

Agents produce the following output types in ChaseOS:

| Output Type | Description | Primary Template |
|-------------|-------------|-----------------|
| Build log | Record of a build/engineering/documentation/architecture session | *(structured per Build-Log-SOP)* |
| Agent activity log | Record of non-build runtime activity, automation, audit-significant actions, or operational visibility binds | `05_TEMPLATES/Agent-Session-Log-Template.md` *(current base template)* |
| Morning thesis output | Pre-market session thesis | `05_TEMPLATES/Morning-Thesis-Output-Template.md` |
| Trade journal entry | Individual trade record with scoring | `05_TEMPLATES/Trade-Journal-Entry-Template.md` |
| Weekly trading review | End-of-week analysis and adjustments | *(per Weekly-Trading-Review-Workflow SOP)* |
| Documentation/archive note | Session summary for archive | *(per archive note conventions in `CLAUDE.md`)* |
| Knowledge note | Processed research or concept note | `05_TEMPLATES/Source-Note-Template.md` |
| Decision log | Significant decision record | `05_TEMPLATES/Decision-Log-Template.md` |
| Experiment log | Structured experiment record | `05_TEMPLATES/Experiment-Template.md` |

---

## 4. Writeback Targets

All agent outputs must be filed in the correct location. The canonical map:

| Output | Write to |
|--------|---------|
| Build logs | `07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md` |
| Agent activity logs | `07_LOGS/Agent-Activity/YYYY-MM-DD-[agent]-[descriptor].md` |
| Morning thesis outputs | `07_LOGS/Morning-Thesis/YYYY-MM-DD-thesis.md` |
| Trade journal entries | `07_LOGS/Trade-Journal/YYYY-MM-DD-[ASSET]-[DIRECTION].md` |
| Weekly trading reviews | `07_LOGS/Trading-Weekly/YYYY-WW-Trading-Review.md` |
| Daily notes | `07_LOGS/Daily/YYYY-MM-DD.md` |
| Archive / documentation notes | `99_ARCHIVE/Documentation-History/YYYY-MM-DD_[descriptor].md` |
| Knowledge notes | `02_KNOWLEDGE/[Domain]/[topic].md` |
| Project updates | Edit the relevant `01_PROJECTS/[Project]/[Project]-OS.md` |

---

## 5. Manual Writing Is Fallback

In ChaseOS, the agent/system is the primary author of structured outputs. Manual user writing is always available as a fallback, but is not the designed default.

This applies to:
- Build logs (agent writes after completing work)
- Trade journal entries (agent populates from user context)
- Morning thesis outputs (agent runs the workflow and writes the result)
- Agent activity logs (agent records runtime-side actions, automation traces, audit events, or operational binds)
- Archive and documentation notes (agent produces at session close)

For future typed standalone/operator surfaces, agent activity should now also be read through `Agent-Activity-and-Runtime-Activity-Summary-Context-Application.md`, which preserves the distinction between runtime activity summaries, audit-significant activity summaries, and ordinary build/session history.

The reason: manual obligation without agent support creates admin burden that erodes the system over time. The system must work at low energy, not only at high effort.

---

## 6. Agent Behavior During Outputs

When producing any output, agents must:

- Check whether an entry for today already exists before creating a duplicate
- Populate all template fields with available data; mark `{{placeholder}}` clearly for any fields that require user input
- Include relevant wikilinks back to Project-OS files, SOPs, templates, and knowledge notes
- Not fabricate data (market prices, trade results, project state) that is not provided
- Flag incomplete outputs explicitly rather than leaving them silently partial

---

## 7. Related Files

| File | Role |
|------|------|
| `06_AGENTS/Agent-Control-Plane.md` | **Framework-level control plane** — what agents can do, trust, permissions, failure policy |
| `06_AGENTS/Permission-Matrix.md` | Explicit permission table by agent type, action, and target |
| `06_AGENTS/Trust-Tiers.md` | Trust tier definitions with operational rules |
| `06_AGENTS/Handoff-Protocol.md` | Session start/close and context handoff protocol |
| `04_SOPS/Agent-Failure-Ambiguity-SOP.md` | Stop/escalate behavior for failure states |
| `CLAUDE.md` | Claude Code-specific routing and session rules |
| `00_HOME/Assistant-Contract.md` | Binding permission and behavior contract for all agents (v2.0) |
| `06_AGENTS/Vault-Map.md` | Full vault navigation guide |
| `06_AGENTS/Agent-Registry.md` | All active and planned agents with trust tiers and permission scopes |
| `04_SOPS/Build-Log-SOP.md` | Build session logging SOP |
| `04_SOPS/Morning-Thesis-Workflow.md` | Morning thesis execution SOP |
| `04_SOPS/Weekly-Trading-Review-Workflow.md` | Weekly review SOP |
| `07_LOGS/Agent-Activity/Agent-Activity-Index.md` | Agent activity index for runtime/audit/automation records |
| `07_LOGS/Morning-Thesis/Morning-Thesis-Index.md` | Morning thesis output folder |
| `07_LOGS/Trade-Journal/Trade-Journal-Index.md` | Trade journal folder |

*Graph links: [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Handoff-Protocol]] · [[CLAUDE]] · [[PROJECT_FOUNDATION]] · [[FORKING]] · [[Vault-Map]] · [[Tool-Map]] · [[Agent-Activity-Index]] · [[05_TEMPLATES/Agent-Session-Log-Template|Agent-Session-Log-Template]] · [[Build-Logs-Index]] · [[Morning-Thesis-Index]] · [[Trade-Journal-Index]] · [[Morning-Thesis-Output-Template]]*

*Agent-Output-Conventions.md — Updated: 2026-03-20 (Phase 4 — Phase 4 control plane links added)*
