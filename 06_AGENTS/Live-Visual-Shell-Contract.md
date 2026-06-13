---
title: Live Visual Shell Contract
type: phase10-operator-surface-contract
status: seeded — contract only; no execution authority
version: 0.1
created: 2026-05-12
updated: 2026-05-12
owner: Optimus
phase: Phase 10 — Studio / OSRIL surface-side
related_docs:
  - 06_AGENTS/Operator-Surface-Runtime-Interaction.md
  - 06_AGENTS/Phase10-Operator-Runtime-Adapter-Gap-Plan.md
  - 06_AGENTS/Phase10-Desktop-Shell-Engineering-Plan.md
  - 06_AGENTS/OSRIL-Phase9-Closeout.md
related_runtime_surfaces:
  - runtime/studio/runtime_cockpit.py
  - runtime/studio/aor_pipeline_monitor.py
  - runtime/studio/desktop_shell_app.py
---

# Live Visual Shell Contract

> This document defines the first Phase 10 contract for a state-tied visual animation shell over ChaseOS runtime events. It is a visualization contract only. It does not execute workflows, consume approvals, mutate runtime state, write canonical notes, start child apps, call providers/connectors, dispatch browsers, or grant a new authority lane.

---

## 1. Purpose

The Live Visual Shell is the ambient visual/status layer for ChaseOS Studio. It turns already-authorized runtime state into operator-readable animation states: idle, thinking/planning, working, waiting for approval, blocked, failed/degraded, speaking/voice-output, and complete.

This pass seeds the contract for that surface so future Studio implementation can render a visual shell without inventing a second event bus or treating animation state as operational truth.

The key rule is simple:

```text
AOR / OSRIL / lifecycle / approval truth -> read-only state adapter -> visual shell animation
```

The reverse direction is forbidden:

```text
visual shell animation -/-> workflow execution
visual shell animation -/-> approval consumption
visual shell animation -/-> runtime/lifecycle mutation
visual shell animation -/-> canonical writeback
```

---

## 2. Authority Boundary

The Live Visual Shell may:

- read bounded event/status summaries that are already exposed to Studio/OSRIL surfaces;
- normalize those summaries into visual states;
- render animations, badges, counts, timestamps, labels, and degraded-state explanations;
- expose QA evidence that the renderer stayed read-only;
- link the operator to the authoritative surface that owns the next action.

The Live Visual Shell must not:

- execute AOR workflows;
- resume or consume approvals;
- write approval artifacts;
- write Agent Bus tasks;
- mutate lifecycle state;
- start, stop, or restart runtimes;
- call providers, connectors, browsers, shell commands, or host startup actions;
- write canonical knowledge or protected governance docs;
- treat visual/animation state as the source of truth.

Any action suggested by the visual shell must route to an existing governed surface such as Runtime Cockpit action readiness, Approval Center, Agent Bus, OSRIL wait/resume queue, or a future explicitly approved operator action wrapper.

---

## 3. Current Live Repo Footholds

This contract is grounded in current repo truth rather than a blank-slate UI idea.

| Existing surface | Current role | Live Visual Shell use | Boundary |
|---|---|---|---|
| `runtime/studio/runtime_cockpit.py` | Aggregates dashboard, runtime startup controls, lifecycle/post-reboot indicators, logs/audit, Agent Bus/readiness posture | Primary Studio-side status source for runtime cards, readiness counts, blocked/degraded panel state, and runtime health badges | Already read-only; reports no host mutation or success-marker acceptance authority |
| `runtime/studio/aor_pipeline_monitor.py` | Lists/inspects/summarizes recent AOR audit records from `07_LOGS/Agent-Activity/*.json` | Source for recent execution status: success, escalated, failed, stage reached, escalation reason, workflow id | Reads audit files only; no pipeline replay or audit mutation |
| `runtime/studio/desktop_shell_app.py` | Localhost-only shell-shaped Studio mock mounting Runtime Cockpit, graph, approval, Pulse, ARSL, and related panels | Likely first render target for visual-shell panel/card mounting and static browser QA | Localhost/read-only mock; no child app start, workflow execution, approval execution, provider call, browser automation, schedule mutation, or canonical writeback |
| `runtime/osril/` | Phase 9 OSRIL event/session/approval substrate | Canonical lower-layer event contract for operator-visible state transitions | Lower-phase owner; Phase 10 visual shell consumes, not defines, OSRIL runtime truth |
| `runtime/lifecycle/` | Lifecycle profiles, coordination-watch/bootstrap evidence, startup proof surfaces | Source for runtime availability/degraded/offline/post-reboot indicators | Lower-phase owner; visual shell cannot register, unregister, or reconcile lifecycle state |
| Approval Center / Runtime Cockpit action readiness | Operator-facing approval/readiness surfaces | Source for waiting-approval counts and action-route labels | Visual shell links to these surfaces; it does not consume decisions |

---

## 4. Event Source Classes

The first visual shell adapter should accept a bounded packet with five source classes. Missing classes must degrade gracefully instead of blocking the whole shell.

| Source class | Minimum fields | Example producer | Visual contribution | Missing-contract behavior |
|---|---|---|---|---|
| Runtime lifecycle | `runtime_id`, `runtime_label`, `lifecycle_status`, `last_seen_at`, `degraded_reason?` | `runtime/studio/runtime_cockpit.py`, `runtime/lifecycle/*.yaml`, lifecycle run artifacts | online/offline/degraded ring, runtime badge, stale indicator | show `unknown_runtime_state`; route dependency lower to lifecycle/OSRIL owners |
| AOR execution events | `workflow_id`, `status`, `stage_reached`, `timestamp_utc`, `escalation_reason?`, `error?` | `runtime/studio/aor_pipeline_monitor.py`, AOR audit records | thinking/working/complete/failed/escalated pulse, recent-event trail | show `no_recent_execution_events`; visual shell remains idle/unknown |
| Approval posture | `approval_required_count`, `approval_found_count`, `pending_approval_ids?`, `approval_surface_route` | Runtime Cockpit readiness, Approval Center | waiting-approval amber state, pending count, route-to-approval label | show `approval_posture_unavailable`; no approval action rendered |
| Coordination / Agent Bus | `open_count`, `blocked_count`, `expired_count`, `runtime_target?`, `queue_stale?` | Agent Bus status/read-only summary | coordination activity sparkline, backlog/degraded badge | show `coordination_unknown`; no bus task write path |
| Voice/audio playback | `playback_state`, `speaking`, `analyser_available`, `provider_route?` | future voice I/O adapter | speaking animation / waveform/orb intensity | show `voice_signal_absent`; no microphone/speaker/provider access |

The first implementation should support static fixtures for these classes before any long-lived stream or WebSocket is introduced.

---

## 5. Visual State Model

The visual shell should normalize all source classes into a single display state. This state is presentation-only and must include a pointer back to authoritative evidence.

| Visual state | Meaning | Input conditions | Animation guidance | Operator route |
|---|---|---|---|---|
| `idle` | No current work and no urgent blockers known | no active AOR event; lifecycle healthy; no pending approval count | calm low-motion orb/ring | Runtime Cockpit overview |
| `thinking` | Planning/lookup/contract preparation visible but not executing a privileged action | AOR stage before handler execution, planning/status event, or queued declared work | slow blue pulse / orbit | AOR pipeline monitor / workflow detail |
| `working` | Declared workflow/run is in progress | recent AOR event with running/handler stage or equivalent status | stronger motion / progress ring | AOR pipeline monitor |
| `waiting_approval` | A governed action is blocked pending operator approval | approval-required count > 0 or AOR escalation reason indicates approval missing/invalid | amber hold/pulse with count badge | Approval Center / action readiness surface |
| `blocked` | Known dependency prevents progress but is not a crash | lifecycle degraded, missing backend contract, queue stale, host evidence absent | orange/red paused orbit with blocker label | responsible lower-phase surface named in blocker |
| `failed` | AOR/audit/runtime event reports failed execution | status failed/error, non-empty error field | red flash then settled degraded state | AOR audit detail / build log / remediation route |
| `complete` | Most recent visible run completed successfully | recent success status and no newer active blocker | brief green completion pulse then idle | audit/build-log detail |
| `speaking` | Voice output/audio playback is active | playback_state speaking or analyser signal active | waveform/orb amplitude animation | Voice I/O surface when built |
| `unknown` | Required status source unavailable | source missing, malformed, stale, or unsupported | neutral grey ring with missing-source label | docs/dependency route, not execution |

Precedence should be explicit and deterministic:

1. `failed` when the latest authoritative event is an unhandled failure.
2. `waiting_approval` when an approval gate is currently blocking action.
3. `blocked` when a dependency or lifecycle degradation is active.
4. `working` when a declared run is currently active.
5. `thinking` when planning/queued work is visible but not executing.
6. `speaking` when voice output is active and no higher-severity state is active.
7. `complete` for a short dwell after successful completion.
8. `idle` when healthy and inactive.
9. `unknown` when the adapter cannot prove the state.

---

## 6. Contract Packet Shape

A future module such as `runtime/studio/live_visual_shell.py` should expose a pure builder function first:

```python
def build_live_visual_shell_contract(vault_root: str | Path, *, runtime_id: str = "all") -> dict[str, Any]:
    ...
```

Minimum output shape:

```json
{
  "ok": true,
  "surface": "studio_live_visual_shell_contract",
  "status": "contract_ready_static_fixture_or_live_readonly",
  "generated_at_utc": "2026-05-12T00:00:00Z",
  "runtime_id": "all",
  "visual_state": {
    "state": "waiting_approval",
    "severity": "attention",
    "label": "Waiting for approval",
    "reason": "1 pending approval-required runtime action",
    "evidence_route": "approval-center",
    "source_event_ids": []
  },
  "source_classes": {
    "runtime_lifecycle": {"available": true, "source": "runtime_cockpit"},
    "aor_execution_events": {"available": true, "source": "aor_pipeline_monitor"},
    "approval_posture": {"available": true, "source": "approval_center_or_runtime_cockpit"},
    "coordination_bus": {"available": false, "source": null, "missing_contract": "read-only summary adapter"},
    "voice_audio": {"available": false, "source": null, "missing_contract": "voice I/O adapter"}
  },
  "animation_profile": {
    "motion": "hold_pulse",
    "palette": "amber",
    "intensity": 0.65,
    "reduced_motion_safe": true,
    "screen_reader_label": "Runtime waiting for approval"
  },
  "authority": {
    "read_only": true,
    "executes_workflows": false,
    "consumes_approvals": false,
    "writes_runtime_state": false,
    "writes_agent_bus": false,
    "canonical_mutation_allowed": false
  },
  "qa_expectations": {
    "fixture_backed_state_mapping": true,
    "browser_visual_qa_required": true,
    "no_write_static_qa_required": true
  },
  "blockers": []
}
```

The adapter may read existing Studio helper outputs but should not make their lower-level sources less authoritative. If a lower-level helper returns `ok: false`, the visual shell must show a degraded/unknown state and preserve the error as evidence rather than hiding it.

---

## 7. First Implementation Plan

### Task 1 — Fixture-backed state mapper

**Objective:** Prove deterministic event-to-visual-state mapping without touching live runtime state.

**Files:**
- Create: `runtime/studio/live_visual_shell.py`
- Create: `runtime/studio/test_live_visual_shell.py`

**Steps:**
1. Write tests for the precedence order: failed > waiting_approval > blocked > working > thinking > speaking > complete > idle > unknown.
2. Add a pure `map_visual_state(packet: dict) -> dict` helper.
3. Assert the returned state always includes `state`, `severity`, `label`, `reason`, and `evidence_route`.
4. Assert the returned authority block denies workflow execution, approval consumption, Agent Bus writes, runtime mutation, and canonical mutation.

### Task 2 — Read-only source adapter

**Objective:** Aggregate current Studio read-only sources into the packet shape.

**Files:**
- Modify: `runtime/studio/live_visual_shell.py`
- Test: `runtime/studio/test_live_visual_shell.py`

**Steps:**
1. Use `runtime_cockpit.build_runtime_cockpit_contract(...)` where available for runtime/lifecycle/readiness summaries.
2. Use `aor_pipeline_monitor.get_execution_summary(...)` or `list_recent_executions(...)` for recent execution posture.
3. Fail open/degraded per source class when a helper errors.
4. Do not write files, trigger pipelines, or consume approvals.

### Task 3 — Desktop shell panel mount

**Objective:** Mount the visual shell contract into the local desktop shell mock as read-only status chrome.

**Files:**
- Modify: `runtime/studio/desktop_shell_app.py`
- Test: existing desktop-shell app tests plus a new targeted panel assertion if needed.

**Steps:**
1. Add a panel/card with the current visual state, evidence route, authority flags, and missing-source blockers.
2. Expose a JSON endpoint such as `/live-visual-shell.json`.
3. Preserve current shell boundaries: localhost-only, no child app start, no approval execution, no workflow execution, no provider/browser/schedule/canonical writes.

### Task 4 — Static/browser QA proof

**Objective:** Prove the shell can render visual state while remaining read-only.

**Files:**
- Existing QA runner surface, or a narrow future `live-visual-shell` QA surface.

**Steps:**
1. Add fixture states for idle, working, waiting_approval, blocked, failed, speaking, unknown.
2. Run focused pytest for `runtime/studio/test_live_visual_shell.py`.
3. Run desktop shell static/no-write QA.
4. Capture browser visual proof once the panel is mounted.

---

## 8. Lower-Phase Dependencies to Route, Not Solve Here

The Phase 10 visual shell must route these gaps downward instead of filling them by inventing local state:

| Dependency | Owner layer | Minimum proof before richer visual shell work |
|---|---|---|
| Stable OSRIL event stream / event identifiers | Phase 9 OSRIL/AOR | documented event fields and fixture examples for status, approval, failure, completion, and session continuity |
| Lifecycle live state and stale/offline semantics | Runtime lifecycle / coordination-watch | read-only runtime availability packet with last-seen/staleness reason |
| Approval consumption and resume state | AOR/Gate/Approval Center | approval-required/pending/consumed distinctions exposed without giving the visual shell consume authority |
| Runtime dispatch / active-run detection | AOR runtime dispatch | authoritative running/queued/complete/failed event posture in audit or event stream |
| Voice analyser/playback state | Voice I/O adapter | provider-neutral playback-state packet with no microphone/provider authority implied |
| Browser/native visual QA path | Studio QA / packaging | repeatable static and browser proof that animation renders and writes nothing |

---

## 9. Acceptance Criteria

A first implementation of this contract is acceptable only when all of the following are true:

- state mapping is fixture-backed and deterministic;
- missing source classes produce visible degraded/unknown states rather than exceptions or fake green status;
- the contract exposes explicit authority flags denying execution, approval consumption, runtime mutation, Agent Bus writes, and canonical writeback;
- the desktop shell mount, if added, exposes a JSON contract endpoint and visible panel/card without changing existing shell authority;
- QA includes focused mapper tests, contract shape tests, desktop-shell no-write assertions, and browser/static visual evidence;
- documentation states that visual animation is subordinate to AOR/OSRIL/runtime/lifecycle truth.

---

## 10. Current Status After This Pass

This pass is a contract seed, not an implementation. It advances Live Visual Shell from a conceptual OSRIL row to a mapped Phase 10 surface contract with:

- source classes;
- visual states and precedence;
- a future contract packet shape;
- implementation tasks;
- QA expectations;
- explicit Phase 9-and-below dependency routing.

No runtime event stream, visual shell module, desktop shell panel, approval path, workflow execution path, provider/connector call, Agent Bus write, lifecycle mutation, or canonical writeback was created by this document.

---

*Graph links: [[Operator-Surface-Runtime-Interaction]] · [[Phase10-Operator-Runtime-Adapter-Gap-Plan]] · [[Phase10-Desktop-Shell-Engineering-Plan]] · [[OSRIL-Phase9-Closeout]] · [[ChaseOS-Studio-Architecture]] · [[ChaseOS-Runtime-Shell]] · [[Agent-Activity-Index]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
