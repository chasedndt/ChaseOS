---
title: Scheduling Intent Architecture
type: architecture-doc
status: active - v1.9 updated 2026-05-16; design complete; implementation BUILT; Studio proposal-to-local-adapter-export-packet plus manual UI controls PARTIAL
created: 2026-04-14
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# Scheduling Intent Architecture

> Defines how ChaseOS owns schedule intent as canonical state.
> Runtimes (OpenClaw, n8n, Hermes, future adapters) execute it — they do not invent it.
>
> This document is the design authority. The schema and storage location defined here are the implementation target.
> Current state: design complete. Native `runtime/schedules/` implementation LIVE as of 2026-04-15.

2026-05-16 Studio Chat update: Studio can now prepare digest-bound schedule proposal packets, consume approved proposal artifacts into staged records, explicitly write one approved disabled schedule intent into `runtime/schedules/*.yaml` with `runtime/schedules/index.yaml` regeneration through `runtime/studio/phase11_chat_approved_schedule_intent_writer.py`, prepare a digest-bound activation approval packet through `runtime/studio/phase11_chat_schedule_intent_activation_readiness.py`, consume one approved activation packet through `runtime/studio/phase11_chat_approved_schedule_activation_executor.py` to enable the matching ChaseOS schedule plus regenerate `runtime/schedules/index.yaml`, prepare a digest-bound adapter export approval packet through `runtime/studio/phase11_chat_schedule_adapter_export_readiness.py`, consume one approved export approval through `runtime/studio/phase11_chat_approved_schedule_adapter_export_packet_writer.py` to write the local adapter export JSON packet under `runtime/studio/chat/schedule-adapter-exports/`, render manual Studio Chat UI action controls/readback through `runtime/studio/phase11_chat_schedule_ui_action_controls_and_readback.py`, serve a loopback-only manual browser test harness through `runtime/studio/phase11_chat_schedule_manual_test_app.py`, and expose external cron apply as one blocked lane in the new `runtime/studio/phase11_chat_authority_tier_controls.py` Chat control block. This is still partial scheduling control: external scheduler mutation, OpenClaw/Hermes cron updates, runtime dispatch, Agent Bus task writes, Discord calls, provider calls, credential reads, and broader canonical writeback remain blocked until separate external apply/execution passes exist.

---

## 1. The Problem This Solves

As of Phase 9 Pass 4, all scheduling of ChaseOS workflows lives in the runtime layer — in OpenClaw's cron configuration, or in the operator's manual invocation pattern. ChaseOS has no native representation of when workflows should run or what governs their execution timing.

This creates three problems:

1. **Schedule intent is not inspectable.** There is no way to ask "what is scheduled, when, and why?" from within ChaseOS.
2. **Schedule governance is not enforced.** The runtime can schedule anything, including workflows that should not be scheduled, without ChaseOS governance applying.
3. **Scheduling is adapter-coupled.** If the operator switches from OpenClaw to n8n, the schedule configuration has to be rebuilt from scratch in the new adapter.

The Scheduling Intent Architecture solves this by making ChaseOS the owner of schedule intent. Runtimes are consumers of that intent — they read it and execute according to it. They do not define it.

---

## 2. Ownership Boundary

**ChaseOS owns:**
- The schedule intent object (what workflow, when, under what governance)
- The workflow class allowlist (which task_types are allowed to be scheduled at all)
- The delivery policy (what outputs are vault-local vs externally deliverable)
- The audit requirements (what must be logged for every scheduled run)
- Whether a schedule is enabled/disabled/shadow-mode
- The provenance of who created the schedule and why

**The runtime adapter owns:**
- The actual execution process (cron daemon, persistent timer, event listener)
- The transport surface (how the `chaseos run` command gets invoked)
- The approval UI and control plane (if any)
- Adapter-specific mechanics (OpenClaw cron vs n8n trigger vs local cron job)
- Recovery on adapter restart (re-reading the intent from ChaseOS)

This boundary means: if the runtime adapter is replaced, the schedule intent survives. The new adapter reads the same intent files and executes accordingly. No schedule configuration is lost.

---

## 3. Schedule Intent Schema

Schedule intents are stored as YAML files in `runtime/schedules/`.

One file per schedule intent. File name: `<schedule_id>.yaml`.

```yaml
# runtime/schedules/<schedule_id>.yaml
# ChaseOS Scheduling Intent — canonical schedule declaration
#
# This file is ChaseOS-owned. Do not create schedule intents
# directly in the runtime adapter (OpenClaw, n8n, etc.).
# The adapter reads this file and executes according to it.

schedule_id: string          # unique identifier, e.g. "sch-operator-today-0700-et"
workflow_id: string          # must exist in runtime/workflows/registry/

owner: "operator"            # "operator" always in Phase 9

cadence:
  type: "cron" | "event" | "manual" | "webhook"
  cron_expression: string    # ISO cron, e.g. "0 7 * * 1-5" (required if type=cron)
  timezone: string           # IANA timezone, e.g. "America/New_York"
  event_type: string         # if type=event, e.g. "market-open" | "intake-file-added"
  event_source: string       # source system emitting the event (optional)

trigger_source: string       # "openclaw" | "n8n" | "manual" | "webhook" | "chaseos-cli"

runtime_adapter_target: string  # "openclaw" | "claude" | "n8n" | "local"
                                 # must be a registered adapter in Execution-Adapter-Standard

delivery:
  primary_target: string     # "vault-local" | "discord" | "email" | "whop" | "slack"
  vault_writeback_targets:   # must match manifest writeback_targets
    - string
  external_delivery_declared: boolean  # true if any delivery goes outside the vault
  vault_local_only: boolean            # if true, external delivery is explicitly forbidden

approval_policy: string      # "none" | "pre-execution" | "pre-delivery"
                              # "none" = runs without operator confirmation
                              # "pre-execution" = operator must approve before handler runs
                              # "pre-delivery" = runs, but holds output before delivery

enabled: boolean             # false = schedule is registered but not active
shadow_mode: boolean         # if true: runs, audits, but does NOT deliver externally
                              # shadow_mode overrides delivery regardless of delivery config

failure_behavior: string     # "escalate" | "retry-once-then-escalate" | "silent-fail-log"

audit_requirements:
  - string                   # e.g. "run_start_timestamp", "run_duration", "files_written"
  # Minimum required: workflow_id, schedule_id, trigger_time, status, files_written

allowed_workflow_task_types: # task_types from task_type_table.yaml this schedule allows
  - string                   # e.g. ["operator-briefing"]
                              # schedule may not invoke workflows outside this list

provenance:
  created_by: string         # "operator" or runtime that created it on operator's behalf
  created_at: string         # ISO 8601 datetime
  rationale: string          # why this schedule exists

notes: string                # free-form notes for operator reference
```

---

## 4. Workflow Class Allowlist

Not every AOR workflow should be schedulable. The `allowed_workflow_task_types` field enforces which task_types from `runtime/aor/task_type_table.yaml` may be scheduled.

**Schedulable by default:**
- `operator-briefing` — safe to run on schedule; writes to operator brief log only
- `graph-hygiene` — safe to run on schedule; writes to hygiene report only
- `graduate-ideas` — safe to run on schedule; writes proposal only
- `scheduled-briefing-pipeline` (future) — designed specifically for scheduled execution

**Not schedulable without explicit per-schedule justification:**
- `vault-mutation` — autonomous vault edits must not run on a timer without explicit operator intent per run
- Any task_type that involves writes beyond log folders — requires approval_policy: pre-delivery minimum

**Never schedulable:**
- Any task_type with `permission_ceiling: protected_file_writes` or `permission_ceiling: canonical_promotion`
- Any ad-hoc or experimental workflow not in the registry

---

## 5. Storage Location and Index

```
runtime/schedules/
  index.yaml                   — list of all registered schedule intents; status summary
  sch-operator-today-0700.yaml — example: scheduled operator_today at 0700 ET weekdays
  sch-graph-hygiene-weekly.yaml — example: graph hygiene every Sunday morning
  sch-operator-close-day.yaml  — example: close-day brief at 1900 ET weekdays
```

The `index.yaml` provides a machine-readable summary of all registered schedules:

```yaml
# runtime/schedules/index.yaml
schedules:
  - schedule_id: "sch-operator-today-0700"
    workflow_id: "operator_today"
    cadence_type: "cron"
    enabled: true
    shadow_mode: false
    runtime_adapter_target: "openclaw"
    created_at: "YYYY-MM-DDTHH:MM:SSZ"
```

---

## 6. Adapter Execution Model

When a runtime adapter starts, it reads `runtime/schedules/index.yaml` to discover what schedules are registered. For each enabled schedule, it reads the full intent file and wires execution according to its own internal mechanics.

**OpenClaw example:**
- OpenClaw reads `sch-operator-today-0700.yaml`
- Registers a cron trigger for `0 7 * * 1-5 America/New_York`
- At trigger time: invokes `chaseos run operator_today` through the AOR path
- AOR executes the workflow, writes brief and audit record
- OpenClaw has no awareness of what the brief contains — it only invoked the command

**n8n example:**
- n8n reads `sch-operator-today-0700.yaml` 
- Creates an n8n cron node for the same expression
- At trigger: calls `chaseos run operator_today` via subprocess or webhook
- Same AOR path, same output

**Key principle:** The adapter is the executor. ChaseOS owns what gets executed, when, and under what governance. The adapter's schedule configuration is derived from ChaseOS intent, not the other way around.

---

## 7. Multi-Runtime Safety

Multiple runtime adapters may read the same schedule intents. This must not cause double-execution.

**Resolution model:**
- `runtime_adapter_target` specifies which adapter is the designated executor for a given schedule
- A runtime adapter must only execute schedules where `runtime_adapter_target` matches its own adapter ID
- If multiple adapters are active and both could theoretically execute a schedule, only the designated one does

**Locking:** For Phase 9, adapter-level configuration enforces this. Full distributed locking is a later concern.

---

## 8. Event-Triggered Schedules

Not all schedules are time-based. The `cadence.type: event` model supports event-triggered execution.

**Planned event types:**
- `intake-file-added` — triggers when a new file lands in quarantine; could trigger `graduate-ideas` scan
- `market-open` — triggers at market session open; could trigger trading-related briefing
- `aor-run-failed` — triggers when an AOR workflow fails; could alert operator
- `now-updated` — triggers when Now.md is edited; could re-validate sprint alignment

Event-triggered schedules use the same schema with `cadence.type: event` and `cadence.event_type` set to the event name. The runtime adapter is responsible for emitting and consuming these events.

This is a Phase 9+ capability. Phase 9 initial implementation is cron-only.

---

## 9. Shadow Mode and Testing

Before enabling a new schedule in production, operators should test with `shadow_mode: true`:

- The workflow executes on schedule
- All audit records are written
- The brief/output is written to `07_LOGS/Operator-Briefs/` as normal
- External delivery does NOT happen — Discord, email, Whop are not contacted

Shadow mode allows operators to verify that a scheduled workflow runs correctly, produces the right output, and stays within its declared scope — before enabling external delivery.

**Protocol:**
1. Create schedule with `shadow_mode: true`, `enabled: true`
2. Run through 2–3 scheduled cycles
3. Review outputs and audit records
4. If clean: set `shadow_mode: false`

---

## 10. Relationship to Other Components

| Component | Relationship |
|-----------|-------------|
| **AOR (engine.py)** | Schedules do not bypass AOR. A scheduled workflow still runs through all 8 stages: manifest lookup, task classification, role card, permission ceiling, required reads, handler, writeback, audit. |
| **Workflow Registry** | `workflow_id` in a schedule must exist in `runtime/workflows/registry/`. Invalid reference = schedule fails validation before execution. |
| **ChaseOS Gate** | Gate rules apply to all AOR writeback regardless of how the run was triggered. Scheduled runs are not exempt. |
| **OpenClaw** | OpenClaw is the current designated runtime adapter. It reads schedule intents and executes via `chaseos run`. |
| **n8n** | n8n is a planned alternate adapter. Same read-and-execute model. |
| **Operator-Briefing-Architecture** | The scheduling layer provides the trigger for operator briefings. The briefing architecture governs the content. Both are needed; neither replaces the other. |
| **ChaseOS-MCP-Server** | A future MCP server could expose schedule status as a read surface. It must not expose schedule mutation. |
| **Permission Matrix** | Schedules are bounded by the same permission ceilings as the workflows they invoke. |

---

## 11. Implementation Target

**Phase 9 — native scheduling implementation:**

1. Create `runtime/schedules/` directory
2. Define `ScheduleIntent` dataclass (mirrors the YAML schema)
3. Create `runtime/schedules/loader.py` — read + validate schedule intent files
4. Update `runtime/cli/main.py` — `chaseos schedule list`, `chaseos schedule status`, `chaseos schedule enable/disable`
5. Create `runtime/schedules/index.yaml` — index of registered intents
6. Create first schedule intent files:
   - `sch-operator-today-0700.yaml` — weekday morning brief
   - `sch-operator-close-day-1900.yaml` — weekday close brief
   - `sch-graph-hygiene-sunday.yaml` — weekly vault hygiene
7. Update OpenClaw adapter config to read from `runtime/schedules/` rather than declaring its own cron config
8. Update workflow manifests: add `schedule_intent_ref` field pointing to the schedule intent file (null until wired)
9. Add `chaseos schedule validate` command — validates all schedule intents against registry

**Built 2026-04-15. See `runtime/schedules/` for the implementation.**
**OpenClaw schedule-source sync bridge COMPLETE 2026-04-21. See `runtime/openclaw/schedule_bridge.md`.**

Implementation summary:
- `runtime/schedules/loader.py` — ScheduleIntent dataclass + load/list/validate/enable/disable/export_schedules_for_adapter public API
- `runtime/schedules/sch-operator-today-0700.yaml` — canonical seed intent for operator_today daily (0700 ET weekdays)
- `runtime/schedules/sch-operator-close-day-1900.yaml` — canonical seed intent for operator_close_day (1900 ET weekdays)
- `runtime/schedules/index.yaml` — auto-generated summary; regenerated on every enable/disable
- `runtime/schedules/test_phase9_schedules.py` — 25 tests; all pass
- `runtime/schedules/test_schedule_bridge.py` — 17 bridge tests; all pass (2026-04-21)
- `chaseos schedule list/show/enable/disable/validate/export` — full CLI surface in `runtime/cli/main.py`
- `07_LOGS/Schedule-State/schedule_state_log.jsonl` — state change audit trail
- `runtime/openclaw/schedule_bridge.md` — bridge contract telling OpenClaw how to consume intent (2026-04-21)

Execution reality: OpenClaw is the designated runtime adapter. OpenClaw must derive its cron config from `runtime/schedules/` via `chaseos schedule export --adapter openclaw`. No independent OpenClaw schedule source is permitted. ChaseOS native cron execution is not yet built.

2026-05-15 Studio Chat schedule proposal packet update: `runtime/studio/phase11_chat_schedule_proposal_packet.py` now provides the native Studio Chat request layer for future schedule intent changes. It previews the exact `runtime/schedules/*.yaml` content, computes a stable `schedule_digest`, and can queue a pending Studio approval artifact only when the operator supplies the exact digest. Generic `StudioService.execute_approved()` blocks these artifacts.

2026-05-16 Studio Chat schedule proposal consumption update: `runtime/studio/phase11_chat_schedule_proposal_consumption_executor.py` can consume one approved digest-bound schedule proposal exactly once into `runtime/studio/chat/schedule-proposals/` after approval id plus exact schedule digest validation. It validates the approved YAML through the schedule loader, writes a marker and audit evidence, and mutates only the matching approval record. This is still staging, not canonical schedule activation: no `runtime/schedules/*.yaml` file is written, no `runtime/schedules/index.yaml` regeneration occurs, no schedule is enabled, no OpenClaw/Hermes cron state changes, and no Agent Bus task, runtime/workflow dispatch, Discord call, provider call, credential read, or canonical mutation occurs. A separate approved schedule-intent writer is required before staged proposals become canonical schedule intent state.

2026-05-16 Studio Chat approved activation update: `runtime/studio/phase11_chat_approved_schedule_activation_executor.py` can consume one approved digest-bound activation packet exactly once after approval id, exact activation digest, and operator activation statement validation. It verifies the current disabled schedule file hash, validates the future enabled YAML against the schedule loader, reserves an exact-once marker, enables the matching schedule through `enable_schedule()`, regenerates `runtime/schedules/index.yaml`, refreshes the adapter export read model, and marks only the matching approval record executed. It still performs no external scheduler mutation, OpenClaw/Hermes cron update, Agent Bus task write, runtime/workflow dispatch, Discord call, provider call, credential read, or broader canonical writeback. A separate adapter export/readiness pass is still required before any external cron/runtime lane changes.

2026-05-16 Studio Chat adapter export-readiness update: `runtime/studio/phase11_chat_schedule_adapter_export_readiness.py` can inspect enabled schedules for one registered runtime adapter, compute an exact export digest over the adapter export entries plus schedule/index hashes, and queue a pending approval packet for a future local adapter export packet writer. `StudioService.execute_approved()` blocks ambient execution of these export approvals. This pass writes no local export packet, mutates no external scheduler or OpenClaw/Hermes cron, creates no Agent Bus task, dispatches no runtime/workflow, calls no Discord/provider API, reads no credentials, and performs no broader canonical writeback.

2026-05-16 Studio Chat approved adapter export packet writer update: `runtime/studio/phase11_chat_approved_schedule_adapter_export_packet_writer.py` can consume one approved digest-bound adapter export approval exactly once after approval id, exact export digest, and operator export-write statement validation. It verifies the current adapter export digest against schedule/index hashes, reserves an exact-once marker, writes the local JSON packet under `runtime/studio/chat/schedule-adapter-exports/`, and marks only the matching approval record executed. It still performs no external scheduler mutation, OpenClaw/Hermes cron update, Agent Bus task write, runtime/workflow dispatch, Discord call, provider call, credential read, or broader canonical writeback.

2026-05-16 Studio Chat schedule UI controls/readback update: `runtime/studio/phase11_chat_schedule_ui_action_controls_and_readback.py` now defines the manual-test UI contract for the local schedule chain. The native Chat panel renders fields, action buttons, status text, and readback for proposal preview/queue, proposal consumption, schedule intent write, activation preview/queue/execution, adapter export preview/queue, and local export packet write. The UI calls only the existing governed Studio API methods and keeps no secret fields; it still performs no external scheduler mutation, OpenClaw/Hermes cron update, Agent Bus task write, runtime/workflow dispatch, Discord call, provider call, credential read, or broader canonical writeback.

2026-05-16 Studio Chat authority-tier controls update: `runtime/studio/phase11_chat_authority_tier_controls.py` now includes `external_cron_apply` as one Chat authority lane beside provider, credential, runtime dispatch, Agent Bus, and Discord lanes. The lane navigates to the schedule controls/readback surface only; it does not mutate external scheduler files, OpenClaw/Hermes cron state, Agent Bus tasks, runtime/workflow dispatch, provider/Discord APIs, credentials, or broader canonical state.

---

*Graph links: [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Operator-Briefing-Architecture]] · [[ChaseOS-MCP-Server]] · [[Phase9-Adopted-Feature-Specification]] · [[OpenClaw-Adapter-Spec]] · [[Permission-Matrix]]*

*Scheduling-Intent-Architecture.md - v1.9 | Created: 2026-04-14 | Updated: 2026-04-15 (implementation live - runtime/schedules/ built) | Updated: 2026-04-21 (bridge complete - runtime/openclaw/schedule_bridge.md; export_schedules_for_adapter() added; chaseos schedule export --adapter; 17 bridge tests pass; no duplicate schedule truth) | Updated: 2026-05-15 (Studio Chat schedule proposal packet added as exact-digest approval-request layer; no schedule YAML/index/external scheduler mutation authority) | Updated: 2026-05-16 (Studio Chat schedule proposal consumption, approved schedule-intent writer, activation readiness, approved activation executor, adapter export-readiness, approved local adapter export packet writer, manual UI controls/readback, and authority-tier external cron apply navigation lane added; external scheduler/cron/runtime dispatch still blocked)*
