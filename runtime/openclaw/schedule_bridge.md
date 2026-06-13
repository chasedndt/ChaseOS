---
title: OpenClaw Schedule Bridge
type: openclaw-runtime-control
scope: runtime-local — defines how OpenClaw consumes ChaseOS-native schedule intent; does not override ChaseOS governance
created: 2026-04-21
---

# OpenClaw Schedule Bridge

> This file defines the binding contract between ChaseOS-native schedule intent
> (`runtime/schedules/`) and OpenClaw's cron/execution layer.
>
> ChaseOS owns schedule intent. OpenClaw executes it. This document tells OpenClaw
> exactly where to read and what to do.

---

## Authority Boundary

| Layer | Owner | Role |
|-------|-------|------|
| Schedule intent (what/when/governance) | ChaseOS — `runtime/schedules/` | Canonical source of truth |
| Cron daemon / execution timer | OpenClaw | Executes on behalf of ChaseOS intent |
| Audit record | ChaseOS AOR — `07_LOGS/Agent-Activity/` | Written by AOR Stage 8 |
| Output (operator brief) | ChaseOS AOR — `07_LOGS/Operator-Briefs/` | Written by AOR Stage 7 |

**OpenClaw cron config is not authoritative.** It is a derived view of ChaseOS intent.
When ChaseOS schedule intent changes, OpenClaw cron must be updated to match.

---

## How to Consume ChaseOS Schedule Intent

### Step 1 — Discover enabled schedules

Run this command to get the schedules OpenClaw is responsible for:

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main schedule export --adapter openclaw --json
```

This produces a JSON object with all enabled schedules targeting `runtime_adapter_target: openclaw`.

### Step 2 — Read intent files directly (alternative)

Read `runtime/schedules/index.yaml` to discover all registered schedules.
For each entry with `runtime_adapter_target: openclaw` and `enabled: true`,
read the full intent file at `runtime/schedules/<schedule_id>.yaml`.

### Step 3 — Wire OpenClaw cron from intent

For each schedule in the export:

| Intent field | OpenClaw cron config |
|---|---|
| `schedule_kind` | Target type: `workflow` or `command` |
| `workflow_id` / `command_id` | ChaseOS target identity |
| `cron_expression` | Cron schedule pattern |
| `timezone` | Cron timezone |
| `command` | Exact command to invoke (e.g. `chaseos run operator_today` or `chaseos events watch --once --execute`) |
| `shadow_mode: true` | Suppress external delivery after run |
| `enabled: false` | Do not register cron job for this schedule |

**Rule:** OpenClaw must not add schedules that are not present in `runtime/schedules/`.
**Rule:** OpenClaw must not invoke workflows with a different cron schedule than what is declared here.
**Rule:** When `shadow_mode: true`, OpenClaw must not deliver output externally.

### Step 4 — Current host execution form

On this Windows host, the exact invocation forms are:

#### operator_today (07:00 ET weekdays)

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run operator_today
```

#### operator_close_day (19:00 ET weekdays)

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run operator_close_day
```

#### events.watch (every minute)

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main events watch --once --execute
```

---

## Current Active Schedules (as of 2026-04-27)

These are the schedules OpenClaw must execute. Run `chaseos schedule export --adapter openclaw`
to get the authoritative current view.

| Schedule ID | Kind | Target | Cron | Timezone | Enabled |
|---|---|---|---|---|---|
| sch-events-watch-every-minute | command | events.watch | `* * * * *` | America/New_York | true |
| sch-operator-today-0700 | workflow | operator_today | `0 7 * * 1-5` | America/New_York | true |
| sch-operator-close-day-1900 | workflow | operator_close_day | `0 19 * * 1-5` | America/New_York | true |
| sch-strikezone-acquisition-0550 | workflow | strikezone_acquisition | `50 5 * * 1-5` | America/New_York | true |
| sch-os-hygiene-graph-0300 | workflow | os_hygiene_graph | `0 3 * * *` | America/New_York | true |

**Event dependency:** `sch-strikezone-acquisition-0550` emits `acquisition.new_item` on success. `sch-events-watch-every-minute` dispatches that event to `sbp_strikezone_digest`. The fixed 06:00 digest schedule is disabled to prevent double execution after acquisition succeeds.

### StrikeZone acquisition (05:50 ET weekdays)

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run strikezone_acquisition
```

### StrikeZone digest fallback (06:00 ET weekdays, disabled)

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run sbp_strikezone_digest
```

---

## Disabled Schedules

These schedule intents are present and valid, but disabled. They are not included in the OpenClaw export while disabled.

| Schedule ID | Kind | Target | Cron | Timezone | Enabled |
|---|---|---|---|---|---|
| sch-sbp-strikezone-digest-0600 | workflow | sbp_strikezone_digest | `0 6 * * 1-5` | America/New_York | false |
| sch-openclaw-watch-every-minute | workflow | openclaw_watch | `* * * * *` | America/New_York | false |
| sch-hermes-watch-every-minute | workflow | hermes_watch | `* * * * *` | America/New_York | false |

2026-04-27 event dispatch note: `sch-sbp-strikezone-digest-0600` remains as a valid fallback intent, but the live primary trigger is now `acquisition.new_item -> events.watch -> sbp_strikezone_digest`.

2026-04-27 reset note: do not run the watch loops as one-minute OpenClaw agent-turn cron jobs until the watcher path moves to lifecycle/bootstrap or a direct runner. The observed OpenClaw agent-turn runs exceeded the one-minute cadence and created overlap pressure.

---

## Reconciliation Protocol

When OpenClaw restarts or resumes, it must re-read ChaseOS schedule intent and reconcile
its cron config:

1. Run `chaseos schedule export --adapter openclaw --json`
2. Compare against current cron config
3. Add any missing schedules, remove any schedules not in the export, update any that differ
4. Do NOT preserve cron entries that are not backed by ChaseOS intent

---

## Change Protocol

To change schedule timing or state:

```powershell
# Disable a schedule
chaseos schedule disable sch-operator-today-0700

# Enable a schedule
chaseos schedule enable sch-operator-today-0700

# Validate all schedule intents
chaseos schedule validate
```

After any change, OpenClaw must reconcile its cron config against the new export.

**Do not modify schedule timing in OpenClaw directly.** Edit the intent file in
`runtime/schedules/` and let OpenClaw derive its config from the updated intent.

---

## No Duplicate Schedule Truth Rule

OpenClaw must not maintain an independent schedule config that duplicates ChaseOS intent.
The source of truth is `runtime/schedules/`. OpenClaw's cron entries are derived state.

If a schedule exists in OpenClaw cron but NOT in `runtime/schedules/`, it is unauthorized.
Remove it.

---

*runtime/openclaw/schedule_bridge.md — v1.1 | Created: 2026-04-21 | Updated: 2026-04-27*
*ChaseOS Phase 9 — OpenClaw schedule-source sync pass*


*Graph links: [[OpenClaw-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
