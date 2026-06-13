---
title: Operator Overlay UX Spec
type: specification
status: docs-only — Phase 9 sub-track; defines future visible shell semantics; implementation is Phase 10 Studio + OSRIL surface work
version: 1.0
created: 2026-04-15
updated: 2026-04-15
phase: Phase 9 (runtime state model) / Phase 10 (visual implementation)
knowledge_class: canonical-state
---

# Operator Overlay UX Spec
## ChaseOS — FSOS Visible Shell Semantics for All Surfaces

> The Operator Overlay UX Spec defines the visible shell semantics — status indicators, mode states, step feed, approval banners, and outcome states — for all Full-System Operator Surface executions. This is the canonical definition of what the operator sees when FSOS is running. Visual implementation is a Phase 10 Studio / OSRIL concern. This spec defines the underlying state model that Phase 10 consumes.

**Version:** 1.0
**Created:** 2026-04-15
**Status:** Docs-only — Phase 9 defines the state model. Phase 10 Studio provides the visual implementation. The mode states in this spec are reflected in `OperatorSession.status` and `OperatorEvent.event_type` from the runtime layer.

---

## 1. What This Spec Is

The Operator Overlay UX Spec defines the operator-facing UX semantics of FSOS execution. It is the contract between:
- The runtime layer (which produces events and session state)
- The presentation layer (which consumes those events and renders them)

This spec must be written before Phase 10 surface work begins so that the runtime produces the right state signals and the UI contract is stable before implementation.

---

## 2. Mode States

All FSOS execution runs cycle through these mode states. States are mutually exclusive — the operator is always in exactly one mode per active run.

| Mode | State enum | Description |
|------|-----------|-------------|
| **OBSERVE** | `OBSERVE` | Passive monitoring — FSOS is reading/inspecting but not acting. Output visible; no writes in progress. |
| **PLAN** | `PLAN` | Planner is active — generating the step sequence for the current goal. No actions taken yet. |
| **ASK** | `ASK` | FSOS needs operator clarification before proceeding. Execution paused. Input required. |
| **ACT** | `ACT` | FSOS is executing planned steps. Actions are being taken on the target surface. |
| **AWAIT_APPROVAL** | `AWAIT_APPROVAL` | Execution paused at an approval gate. Operator response required to continue. |
| **RECOVER** | `RECOVER` | A step failed. Recovery protocol is active. Operator is watching recovery unfold. |
| **DONE** | `DONE` | Run completed successfully. All planned steps executed. Outputs available. |
| **FAILED** | `FAILED` | Run halted on unrecoverable failure. Audit written. No further actions possible for this run. |

---

## 3. UI Components

### 3.1 Runtime Status Pill

A compact, always-visible indicator showing the current mode state:

```
[●  OBSERVE]      — gray/neutral
[●  PLAN   ]      — blue, pulsing (planning animation)
[●  ASK    ]      — yellow, static (needs input)
[●  ACT    ]      — green, pulsing (active execution)
[●  AWAIT  ]      — amber, static (waiting for approval)
[●  RECOVER]      — orange, pulsing (recovery in progress)
[●  DONE   ]      — green checkmark, static
[●  FAILED ]      — red, static
```

The status pill is the minimum viable display surface. Even a terminal-based operator experience should show a text equivalent of the status pill.

### 3.2 Current Surface Indicator

Shows which FSOS surface is active:

```
[BROWSER]  |  [TERMINAL]  |  [DESKTOP]  |  [FILESYSTEM]
```

When multiple surfaces are active in a multi-step workflow: shows the currently active surface with others dimmed.

### 3.3 Current Task Display

Shows the current goal/task description:

```
Task: "Extract market summary from finviz.com screener for FSOS research workspace"
```

Sourced from the workflow manifest `purpose` field + the current step `reason` field. Does not display sensitive parameters (no credentials, no internal paths shown unless operator-level permission).

### 3.4 Step Feed

A live scrolling list of the most recent N events:

```
✓  [12:03:04]  NAVIGATE  →  finviz.com/screener
✓  [12:03:06]  EXTRACT   →  table#screener-table  (87 rows)
●  [12:03:07]  EXTRACT   →  parsing content...
```

Step feed symbols:
- `✓` — step complete
- `●` — step in progress
- `✗` — step failed
- `⏸` — step paused (approval required)
- `↺` — recovery in progress

Step feed shows the last 10 events by default. Full event history available via `chaseos operate replay RUN_ID`.

### 3.5 Target Highlight

When FSOS is acting on a browser surface, optionally shows the current target:

```
Target: finviz.com/screener (Tier A — DOM)
```

Grounding tier is shown to the operator so they can see if the run is operating in Tier C (visual fallback) — which is lower-confidence.

### 3.6 Approval-Required Banner

When mode = `AWAIT_APPROVAL`, the overlay prominently shows an approval banner:

```
┌─────────────────────────────────────────────────────┐
│  ⚠  APPROVAL REQUIRED                               │
│                                                     │
│  Action: Submit search form at finviz.com/screener  │
│  Action class: form_submit                          │
│  Run ID: op_abc123                                  │
│  Step: 4 of 7                                       │
│                                                     │
│  [  APPROVE  ]         [  DENY  ]                   │
└─────────────────────────────────────────────────────┘
```

CLI equivalent:
```
chaseos operate approve op_abc123 step_4
chaseos operate deny op_abc123 step_4
```

The approval banner is blocking — the step feed freezes. No new events until an approval response is recorded.

### 3.7 Blocked / Failed / Recovery / Done States

**BLOCKED** (subset of AWAIT_APPROVAL — waiting for input):
```
[⏸ BLOCKED — waiting for operator input]
```

**FAILED** state overlay:
```
┌─────────────────────────────────────────────────────┐
│  ✗  RUN FAILED                                      │
│                                                     │
│  Step 5 of 7 failed: Navigation timeout             │
│  Recovery: attempted, unsuccessful                  │
│  Vault state: unchanged                             │
│  Audit written to: 07_LOGS/Agent-Activity/...       │
│                                                     │
│  [  VIEW AUDIT  ]    [  REPLAY  ]    [  CLOSE  ]   │
└─────────────────────────────────────────────────────┘
```

**RECOVERY** state (overlaid on step feed):
```
↺  [12:04:02]  RECOVERY  →  Closing browser context
↺  [12:04:03]  RECOVERY  →  Navigating back to entry point
```

**DONE** state:
```
┌─────────────────────────────────────────────────────┐
│  ✓  RUN COMPLETE                                    │
│                                                     │
│  Steps: 7/7  |  Approvals: 1  |  Surface: BROWSER  │
│  Extracted: 87 rows → quarantine (capture_id: ...)  │
│  Duration: 00:01:23                                 │
│                                                     │
│  [  VIEW OUTPUT  ]   [  VIEW AUDIT  ]   [  CLOSE  ] │
└─────────────────────────────────────────────────────┘
```

---

## 4. Mode State Transitions

Valid mode transitions:

```
(idle) → PLAN
PLAN → ACT
PLAN → ASK
PLAN → FAILED
ACT → OBSERVE (when reading/inspecting only)
ACT → AWAIT_APPROVAL
ACT → RECOVER
ACT → DONE
ACT → FAILED
OBSERVE → ACT
OBSERVE → DONE
ASK → PLAN (operator answered)
ASK → FAILED (operator denied or no answer)
AWAIT_APPROVAL → ACT (approved)
AWAIT_APPROVAL → FAILED (denied)
RECOVER → ACT (recovered — resume)
RECOVER → FAILED (unrecoverable)
```

Invalid transitions are blocked by the session state machine. The session cannot jump from PLAN directly to DONE (at least one ACT step must occur).

---

## 5. State Mapping to Runtime Events

Mode states are derived from `OperatorEvent.event_type`:

| Event type | → Mode state |
|-----------|-------------|
| `PLAN_READY` | `PLAN` → `ACT` (ready to execute) |
| `STEP_STARTED` | `ACT` |
| `STEP_COMPLETE` (all steps done) | `DONE` |
| `STEP_COMPLETE` (more steps remain) | `ACT` |
| `STEP_FAILED` | `RECOVER` |
| `AWAIT_APPROVAL` | `AWAIT_APPROVAL` |
| `APPROVAL_RECEIVED` (APPROVE) | `ACT` |
| `APPROVAL_RECEIVED` (DENY) | `FAILED` |
| `RECOVERY_STARTED` | `RECOVER` |
| `RECOVERY_COMPLETE` | `ACT` |
| `SESSION_COMPLETE` | `DONE` |
| `SESSION_FAILED` | `FAILED` |

The UI is a pure consumer of event stream state. It does not maintain its own mode transitions — it derives them from the event sequence.

---

## 6. Multi-Surface Runs

When a workflow involves multiple surfaces (future capability):

- Each surface gets its own status pill in the multi-surface view
- The step feed shows surface labels for each event
- Approval banners include the surface name
- The "current surface" indicator shows which surface is active

Multi-surface run example (future):
```
[BROWSER: ACT]  →  Extract from finviz.com
[TERMINAL: OBSERVE]  →  waiting for browser to complete
```

---

## 7. Implementation Notes for Phase 10

When Phase 10 Studio implements this UX:
- Derive all state from OSRIL event bus — do NOT maintain parallel state in the UI
- Status pill must update within 500ms of event receipt
- Approval banner must be dismissible but re-summoned from step feed
- Step feed must support scroll-back (full event history for the current run)
- Audit link in DONE/FAILED states opens the vault build log directly in Studio's markdown viewer
- Overlay must work in both the full Studio desktop app and the compact companion surface (mobile)

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Full-System-Operator-Surface]] · [[Operator-Surface-Adapter-Spec]] · [[Browser-Operator-Surface]] · [[Operator-Surface-Runtime-Interaction]] · [[ChaseOS-Studio-Architecture]] · [[Autonomous-Operator-Runtime]]*

*Operator-Overlay-UX-Spec.md — v1.0 | Created: 2026-04-15 | Phase 9 sub-track (state model) / Phase 10 (visual implementation) | Mode states: OBSERVE/PLAN/ASK/ACT/AWAIT_APPROVAL/RECOVER/DONE/FAILED | Defines operator-visible semantics for all FSOS surfaces*
