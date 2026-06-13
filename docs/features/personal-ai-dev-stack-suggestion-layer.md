---
type: feature-spec
status: proposed-personal-instance
created: 2026-05-26
scope: personal_chaseos_instance_only
core_promotion: false
---

# Personal AI Dev Stack Suggestion Layer

This spec defines the desired personal-instance suggestion layer for ChaseOS Discord Control Plane and ChaseOS standalone surfaces. It is not ChaseOS Core.

Related: [[02_KNOWLEDGE/AI-Agents/Personal-AI-Era-Developer-Stack|Personal AI Era Developer Stack]] · [[04_SOPS/Personal-AI-Dev-Stack-Development-Workflow-SOP|Personal AI Dev Stack Development Workflow SOP]]

## Goal

When Chase develops through Hermes Discord Control Plane or ChaseOS standalone, the agent should automatically recognize when to suggest or apply the personal AI dev stack:

- Matt Pocock engineering methods by default.
- GStack review/planning/security/design methods behind safety gates.
- CLI-Anything safe wrapper for future approved local tool harnesses.
- Tmux for durable interactive agent sessions.
- No ARS implementation.
- No Codex default routing for this stack.

## MVP behavior

A read-only suggestion card can be generated from task classification:

```json
{
  "task_type": "feature_planning|implementation|debugging|ui_design|security_sensitive|browser_qa|tool_automation|release",
  "suggested_stack": ["zoom-out", "to-prd", "to-issues", "tdd"],
  "gstack_gate": "methodology_only|approval_required|blocked",
  "cli_anything_gate": "discovery_only|allowlist_required|blocked",
  "tmux_candidate": true,
  "codex_default": false,
  "authority_notes": ["no external side effects", "no browser cookies", "no deploy"]
}
```

## Suggested routing table

| Task signal | Suggestion |
|---|---|
| "idea", "wedge", "should I build" | gstack office-hours / CEO review |
| "plan", "feature", "roadmap" | Matt zoom-out → PRD → issues; optional gstack eng review |
| "implement", "build", "fix" | Matt TDD |
| "bug", "broken", "why failing" | Matt diagnose |
| "dashboard", "frontend", "UX" | gstack design review/shotgun/html + prototype |
| "auth", "payments", "trading", "secrets", "browser automation" | gstack CSO threat model before implementation |
| "generate artifact", "diagram", "export", "tool CLI" | CLI-Anything safe wrapper discovery first |
| "long-running", "multiple agents", "interactive" | tmux-managed Hermes session or Hermes Kanban/subagent |

## Authority boundaries

The suggestion layer may propose methods; it does not grant authority to:

- install project repo files,
- mutate ChaseOS Core,
- bypass Gate,
- read credentials,
- import cookies,
- activate workflows,
- send outbound messages,
- trade or touch exchange/wallet keys,
- deploy/merge/release without approval.

## Implementation surface options

1. **Now:** Hermes skill + SOP + personal knowledge graph note.
2. **Next:** ChaseOS standalone read-only suggestion card in Agent Operating Console / Chat.
3. **Later:** Agent Bus task metadata field `suggested_dev_stack` for dispatchers.
4. **Later:** Personal Agent Tool Registry UI for CLI-Anything allowlists.

## Acceptance criteria

- A Hermes/standalone agent can name which dev-stack lane applies before development.
- CLI-Anything operational commands are denied unless allowlisted.
- GStack browser/cookie/deploy/tunnel/gbrain features are not suggested by default.
- Matt Pocock TDD/diagnose/planning methods are suggested by default for development.
- Tmux is named as the durable interactive agent surface.
- ARS remains excluded from implementation.
