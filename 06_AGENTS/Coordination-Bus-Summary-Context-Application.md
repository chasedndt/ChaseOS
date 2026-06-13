---
title: Coordination Bus Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for dual-runtime coordination
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Coordination Bus Summary Context Application

> This document is the first concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how dual-runtime coordination summaries should behave inside ChaseOS so they can later surface as typed operating artifacts instead of generic log text.

---

## 1. Purpose

The Summary Context Layer defines the feature-level claim that summaries should carry operating meaning.
What this document does is apply that claim to one concrete subsystem:
- `runtime/agent_bus/`
- runtime coordination bridge docs
- task/result/blocker/review/heartbeat state
- Discord-visible milestone summaries

This is the right next slice because the coordination bus already depends on a distinction between:
- machine state,
- operator visibility,
- runtime authority,
- and durable audit state.

Summaries are the human-facing seam across those layers.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
- `runtime/agent_bus/task-packet.schema.json`
- `runtime/agent_bus/event.schema.json`
- `runtime/agent_bus/heartbeat.schema.json`
- `runtime/agent_bus/examples/*.json`
- `runtime/openclaw/coordination_bridge.md`
- `runtime/hermes/coordination_bridge.md`
- agent-bus CLI summaries from `chaseos agent-bus ...`
- Discord-facing milestone/blocker/review summaries derived from bus state

Not included yet:
- canonical summary-context schema enforcement in code
- final Phase 10 UI component contracts
- automatic Discord delivery formatting rules
- generalized event-bus rendering beyond coordination summaries

---

## 3. Why Coordination Summaries Need Typed Context

A coordination summary is easy to misread if rendered as plain text.

Examples of ambiguity without typed context:
- Is this a new task or only a status update?
- Is this a blocker, a result, or a review request?
- Which runtime owns the task now?
- Is the message authoritative machine state or only a human-readable mirror?
- Should the operator see this in a timeline, a runtime cockpit, or an approval/review surface?

The coordination bus architecture already answers these questions structurally.
The Summary Context Layer makes those distinctions visible when a summary is shown to a person.

---

## 4. Core Summary Classes for the Coordination Bus Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Coordination task summary | task packet with `intent=TASK` | new handoff / bounded unit of work | coordination bus inbox / runtime cockpit |
| Coordination result summary | task packet or event with `intent=RESULT` | work returned for review or closure | coordination result panel / timeline |
| Coordination blocker summary | task packet or event with `intent=BLOCKER` | runtime is halted pending operator or peer help | blocker center / runtime cockpit |
| Coordination review summary | task packet or event with `intent=REVIEW` or `status=review` | review/verification requested | review queue / approval-adjacent surface |
| Coordination heartbeat summary | heartbeat record | liveness and runtime posture snapshot | runtime status strip / cockpit |
| Coordination notice summary | event/notice packet | low-stakes operational visibility | timeline / activity feed |

---

## 5. Current Markdown-Era Artifacts and Their Summary Meaning

### A. Governance / authority layer
These define what a coordination summary is allowed to mean:
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `runtime/hermes/coordination_bridge.md`
- `runtime/openclaw/coordination_bridge.md`

### B. Machine-state layer
These define the actual coordination state:
- SQLite bus store
- packet/event/heartbeat schemas
- task/result/blocker/review packets
- heartbeat rows and watch outputs

### C. Human-visible mirror layer
These are the human-facing summaries that can be produced from the bus:
- Discord milestone summaries
- CLI watch summaries
- build logs referencing coordination outcomes
- future runtime cockpit summaries

Current lifecycle/retention truth for this mirror layer:
- heartbeats are only as fresh as the latest explicit bus heartbeat write
- stale active owned tasks may become `expired`
- completed/cancelled tasks remain visible as retained bus history unless a future archive/compaction layer is added

The standalone must preserve the distinction:
**machine state remains the source; summaries remain the mirror.**

---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md` | coordination doctrine | governance reference for coordination summaries | coordination policy panel |
| `runtime/agent_bus/task-packet.schema.json` | task contract | defines task summary shape and required fields | task schema inspector |
| `runtime/agent_bus/event.schema.json` | immutable event contract | defines event-derived summary semantics | event schema inspector |
| `runtime/agent_bus/heartbeat.schema.json` | liveness contract | defines heartbeat summary semantics | heartbeat inspector |
| task packet rows / example task JSON | active machine handoff state | task summary source object | coordination inbox / task detail panel |
| result packet rows / example result JSON | returned work state | result summary source object | result/review panel |
| blocker/review events | escalation/review state | blocker or review summary source object | blocker/review queue |
| heartbeat rows | liveness state | runtime status summary source object | runtime status strip / cockpit |
| `runtime/hermes/coordination_bridge.md` | Hermes summary/visibility behavior | runtime-specific interpretation rules | Hermes runtime coordination inspector |
| `runtime/openclaw/coordination_bridge.md` | OpenClaw summary/visibility behavior | runtime-specific interpretation rules | OpenClaw runtime coordination inspector |

---

## 7. Recommended Summary Context Fields for Coordination Outputs

A coordination summary should eventually preserve fields like:

```json
{
  "summary_class": "coordination_result",
  "source_family": "agent_bus",
  "runtime_from": "OpenClaw",
  "runtime_to": "Hermes",
  "task_id": "bootstrap-001",
  "intent": "RESULT",
  "task_status": "review",
  "authority_posture": "coordination-visible",
  "source_posture": "machine-state-mirror",
  "routing_surface": "coordination_review_panel",
  "operator_action_needed": true,
  "governance_refs": [
    "06_AGENTS/Runtime-InterAgent-Coordination-Bus.md"
  ],
  "source_refs": [
    "runtime/agent_bus/agent_bus.sqlite",
    "runtime/agent_bus/examples/openclaw-result.example.json"
  ]
}
```

Key point:
The summary should make clear that the displayed text is a mirror of bus state, not the canonical machine state itself.

---

## 8. Routing Rules for Coordination Summaries

### Task summary
Use when a new bounded task is created or assigned.
Show in:
- coordination inbox
- runtime cockpit active-work panel

### Result summary
Use when a runtime returns completed work or review-ready artifacts.
Show in:
- result/review panel
- timeline if low-friction visibility is useful

### Blocker summary
Use when progress has halted.
Show in:
- blocker center
- runtime cockpit banner
- Discord milestone alert when operator awareness is needed

### Review summary
Use when Hermes or an operator needs to inspect returned work.
Show in:
- review queue
- approval-adjacent surface when human judgment is needed

### Heartbeat summary
Use for compact liveness visibility.
Show in:
- runtime status strip
- cockpit summary band

---

## 9. Governance Rules for This Slice

### Discord is summary visibility, not machine truth
A Discord coordination summary should always be understood as a human-facing mirror.
The machine source of truth remains the coordination bus state.

### Summary does not equal permission
A result or blocker summary does not change runtime authority.
It reports state within already-bounded authority.

### Review posture must stay visible
If a result is in `review`, the summary must not look like final completion.
The review-needed posture is part of the meaning.

### Coordination summaries are not canonical truth promotion
They may link to artifacts and outcomes, but they do not promote anything into canonical knowledge by themselves.

---

## 10. Recommended Standalone Views

### A. Coordination Bus Inspector
Should show:
- open tasks
- owner/runtime split
- task intent and state
- event history
- concise summary mirror for operator readability

### B. Runtime Coordination Panel
Per runtime, show:
- claimed tasks
- blocked tasks
- last result returned
- last heartbeat
- concise summary of current coordination posture

### C. Review / Blocker Surface
Show only items needing operator or peer attention:
- review-needed results
- blockers
- stale or expired tasks

This is where typed summary context matters most.
A blocker should not look like a done result.
A review-needed return should not look like a closed task.

---

## 11. What This Application Pass Proves

This pass proves the Summary Context Layer is not only a general product idea.
It can already be applied to a live Phase 9 substrate.

Specifically, it proves that ChaseOS can distinguish between:
- machine state and human summary,
- task vs result vs blocker vs review vs heartbeat,
- runtime ownership and operator visibility,
- coordination surfaces and canonical truth surfaces.

That makes the Summary Context Layer more concrete and OS-native.

---

## 12. Recommended Next Summary-Context Applications

After the coordination bus slice, the strongest next applications are:
1. `runtime/state/` + `runtime/bindings/`
   - runtime posture summaries
   - attachment-mode summaries
2. workflow registry + role cards
   - workflow-class summaries
   - authority/permission summaries
3. browser watchlists + evidence flows
   - monitored-source summaries
   - quarantine/evidence posture summaries

---

## 13. Current Verdict

The coordination bus already has typed machine meaning.
This pass defines how ChaseOS should preserve that meaning when it produces human-facing summaries.

So the rule for this slice is:

**A coordination summary is a typed mirror of task/event/heartbeat state — not generic text, and not the machine source of truth itself.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Markdown-to-Standalone-Bridge]] · [[ChaseOS-Studio-Architecture]]*

*Coordination-Bus-Summary-Context-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
