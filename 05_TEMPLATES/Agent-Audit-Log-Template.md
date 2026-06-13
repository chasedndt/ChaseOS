---
type: template
title: Agent Audit Log Template
created: 2026-03-20
scope: framework-level
---

# Agent Audit Log Template

> Use this template to record individual agent actions where audit-grade traceability is required.
> Not every session requires an audit log — build logs cover standard sessions.
> Use this when: an agent took action on a sensitive file, an escalation occurred, or a non-standard permission was granted.
> File in: `07_LOGS/Agent-Activity/YYYY-MM-DD-[agent]-audit.md`

---

## How to Use This Template

Copy the fields below. Remove any that are not applicable. Do not leave fields blank — use "N/A" or "None" explicitly.

---

```markdown
---
type: agent-audit-log
agent: [agent name and backend — e.g. Claude Code (Anthropic)]
date: YYYY-MM-DD
session-id: [optional — reference to build log or session identifier]
trust-tier: [Tier 1 / Tier 2 / Tier 3 / Tier 4]
---

# Agent Audit Log — [Date] — [Brief descriptor]

## Agent
**Name:** [Claude Code / Claude Chat / NotebookLM / etc.]
**Trust Tier:** [Tier 2 — High Trust]
**Session type:** [Engineering / Research / Documentation / Ingest / Handoff / Other]

---

## Actions Taken

| Action | Target File / System | Authorized By | Notes |
|--------|---------------------|---------------|-------|
| [e.g. Edit] | [file path] | [User instruction / SOP / Session default] | [any relevant notes] |

---

## Files Created
- [file path] — [brief description]

## Files Modified
- [file path] — [what changed and why]

## Files Deleted
- [file path] — [explicit instruction reference]
- *(or: None)*

---

## Permissions Invoked

| Permission | Granted By | Scope |
|------------|------------|-------|
| [e.g. Edit protected file] | [User explicit instruction, 2026-MM-DD] | [This session only / This file only] |
| *(or: Standard session permissions — no escalation)* | | |

---

## Escalations

*List any situation where the agent stopped and asked for user direction.*

- [Situation] → [User response] → [Action taken]
- *(or: None — no escalations required)*

---

## Assumptions Made

*List any assumptions required because context was ambiguous or missing.*

- [Assumption] — [What was assumed and why]
- *(or: None)*

---

## Contradictions Found

| Contradiction | Status |
|---------------|--------|
| [Files in conflict + description] | [Resolved / Unresolved — details] |
| *(or: None)* | |

---

## Prompt Injection / Hostile Input Detected

- [Description of suspicious content, source, and how it was handled]
- *(or: None detected)*

---

## Open Loops

*Items not resolved in this session that require follow-up.*

- [Open loop] — [What is needed to resolve it]
- *(or: None)*

---

## Handoff State

*Complete this section if the session ended before completion or if another agent will continue.*

**Last completed action:** [Exact action]
**Next action in queue:** [Exact next step]
**Context required by next agent:** [What files to read, what state to understand]

---

*Audit log — [YYYY-MM-DD] | [Agent name] | [[Agent-Activity-Index]]*
```

---

*Graph links: [[06_AGENTS/Vault-Map|Vault-Map]] · [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[06_AGENTS/Trust-Tiers|Trust-Tiers]] · [[Handoff-Protocol]] · [[04_SOPS/Agent-Failure-Ambiguity-SOP|Agent-Failure-Ambiguity-SOP]] · [[Agent-Activity-Index]]*

*Agent-Audit-Log-Template.md — Created: 2026-03-20 | Phase 4 — Agent Control Plane*
