---
title: OpenClaw Cron Setup Guide
type: openclaw-implementation-guide
scope: OpenClaw cron configuration — all ChaseOS scheduled workflows
created: 2026-04-24
status: CURRENT — reflects enabled schedules as of 2026-04-27 runtime reset
---

# OpenClaw Cron Setup Guide

> **How to use this document:**
> This file is the single source of truth for configuring OpenClaw's cron layer
> to execute ChaseOS scheduled workflows. Read it top to bottom, implement each
> job in the cron table exactly as specified, then verify with the commands at
> the bottom. Do not add, remove, or modify any cron entry that is not in this file.

---

## System Context

ChaseOS owns schedule intent. OpenClaw executes it.

- **ChaseOS** declares what runs, when, and under what governance (`runtime/schedules/`)
- **OpenClaw** reads that intent and fires the cron jobs
- **The AOR pipeline** (`runtime/aor/engine.py`) handles the actual workflow execution when invoked
- **ChaseOS Gate hooks** enforce write boundaries on every run

All jobs invoke `chaseos run <workflow_id>` through the ChaseOS operator CLI. OpenClaw does not call workflow logic directly.

**Working directory for all jobs:**
```
<VAULT_ROOT>
```

**Python interpreter for all jobs:**
```
<VAULT_ROOT>\.venv\Scripts\python.exe
```

---

## Complete Cron Table

These are **all enabled** ChaseOS-managed cron jobs that OpenClaw must execute. Add all five. Remove any existing OpenClaw cron entries for these workflows that are not in this table.

| #   | Cron Expression | Timezone         | Workflow               | Command                              | Delivery        |
| --- | --------------- | ---------------- | ---------------------- | ------------------------------------ | --------------- |
| 1   | `50 5 * * 1-5`  | America/New_York | strikezone_acquisition | `chaseos run strikezone_acquisition` | vault only      |
| 2   | `0 6 * * 1-5`   | America/New_York | sbp_strikezone_digest  | `chaseos run sbp_strikezone_digest`  | vault + Discord |
| 3   | `0 7 * * 1-5`   | America/New_York | operator_today         | `chaseos run operator_today`         | vault only      |
| 4   | `0 19 * * 1-5`  | America/New_York | operator_close_day     | `chaseos run operator_close_day`     | vault only      |
| 5   | `0 3 * * *`     | America/New_York | os_hygiene_graph       | `chaseos run os_hygiene_graph`       | vault only      |

**Days:** Monday–Friday only (`1-5` in cron day-of-week field).
**Timezone:** All times are US Eastern (America/New_York). OpenClaw must apply ET timezone to all five jobs.

---

## Job-by-Job Reference

---

### Job 1 — StrikeZone Acquisition (05:50 ET, Mon–Fri)

**Schedule ID:** `sch-strikezone-acquisition-0550`
**Cron:** `50 5 * * 1-5` (America/New_York)

**What it does:**
Reads two vault files — `Now.md` (current sprint focus) and `StrikeZone-Crypto-OS.md` (project state) — and builds a normalized source pack artifact under `runtime/acquisition/packs/`. After the pack is written, it also writes a stable pointer file at `runtime/acquisition/packs/strikezone-latest.json` that points to the freshly built pack.

This is a **pre-brief data preparation job**. It produces no human-facing output. It feeds Job 2.

**Why it must run before Job 2:**
Job 2 (the digest) reads the pointer file this job writes. If this job hasn't run, Job 2 still executes but the acquisition layer degrades gracefully (it was declared `optional: true`).

**Output:**
- `runtime/acquisition/packs/<date>-strikezone-daily/` — source packets + BRIS artifacts
- `runtime/acquisition/packs/strikezone-latest.json` — latest pointer file

**Failure behavior:** Escalate and log. Job 2 will still run and produce a partial digest (vault notes only, no acquisition pack). This is acceptable — do not block Job 2 on Job 1 failure.

**Exact invocation (PowerShell):**
```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run strikezone_acquisition
```

---

### Job 2 — StrikeZone Digest (06:00 ET, Mon–Fri)

**Schedule ID:** `sch-sbp-strikezone-digest-0600`
**Cron:** `0 6 * * 1-5` (America/New_York)

**What it does:**
Reads vault context (Now.md, StrikeZone-Crypto-OS.md) and the acquisition pack produced by Job 1. Generates a structured morning market briefing for the StrikeZone community. Writes the briefing to the vault and delivers it to Discord via webhook.

This is the **community-facing output job**. It is the reason Jobs 1–4 exist.

**Delivery:**
- **Vault:** `07_LOGS/SBP-Runs/YYYY-MM-DD-sbp_strikezone_digest.md`
- **Discord:** `#strikezone-signals` channel via `DISCORD_WEBHOOK_URL` environment variable

**Credential required:**
`DISCORD_WEBHOOK_URL` must be set as an environment variable in the OpenClaw execution context. If it is not set, the digest is still written to the vault — Discord delivery is skipped gracefully. Do not hardcode the webhook URL anywhere. Do not put it in any config file.

**Failure behavior:** Halt and log. If generation fails, escalate — do not send a partial digest to Discord.

**Exact invocation (PowerShell):**
```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run sbp_strikezone_digest
```

---

### Job 3 — Operator Morning Brief (07:00 ET, Mon–Fri)

**Schedule ID:** `sch-operator-today-0700`
**Cron:** `0 7 * * 1-5` (America/New_York)

**What it does:**
Reads current vault state — Now.md, recent build logs, decision ledger, ROADMAP phase line, AOR activity from the last 48 hours — and produces a structured four-layer operator brief. Carries forward unresolved items from the previous close note.

This is a **private operator brief**. It goes to the vault only. No external delivery.

**Output:** `07_LOGS/Operator-Briefs/YYYY-MM-DD-operator-today.md`

**Failure behavior:** Escalate and log. Does not retry automatically.

**Exact invocation (PowerShell):**
```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run operator_today
```

---

### Job 4 — Operator Close (19:00 ET, Mon–Fri)

**Schedule ID:** `sch-operator-close-day-1900`
**Cron:** `0 19 * * 1-5` (America/New_York)

**What it does:**
Reads the morning brief carry-forward, today's AOR run record, open loops, build log summary, and quarantine status. Produces an end-of-day close note that the next morning's Job 3 will carry forward.

This is a **private close note**. Vault only. No external delivery.

**Output:** `07_LOGS/Operator-Briefs/YYYY-MM-DD-close-day.md`

**Failure behavior:** Escalate and log.

**Exact invocation (PowerShell):**
```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run operator_close_day
```

---

### Job 5 — OS Hygiene & Graph Integrity (03:00 ET, Daily)

**Schedule ID:** `sch-os-hygiene-graph-0300`
**Intent file:** `runtime/schedules/sch-os-hygiene-graph-0300.yaml`
**Cron:** `0 3 * * *` (America/New_York) — runs 7 days/week

**What it does:**
Executes the three-stage OS graph maintenance suite through the AOR governed pipeline:
1. **Vault Hygiene:** Repairs broken wikilinks, wires orphan nodes into their index maps, flags junk.
2. **Daily Hub Linker:** Ensures every YYYY-MM-DD-prefixed file is anchored in its daily hub note.
3. **Provenance Linker:** Injects runtime profile links (`[[OpenClaw-Runtime-Profile]]`, `[[Hermes-Runtime-Profile]]`) into AI-generated outputs.

Writes a structured run record to `07_LOGS/Maintain-Runs/YYYY-MM-DD-os-hygiene-graph-run.md`.
AOR audit trail written to `07_LOGS/Agent-Activity/`.

**Human CLI path (for manual runs or testing):**
```powershell
chaseos maintain [--dry-run] [--json]
```

**Exact governed invocation (OpenClaw cron):**
```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run os_hygiene_graph
```

---

## Order Dependencies

```
03:00 ET  Job 5 — os_hygiene_graph         (graph cleanup across the whole vault)
              ↓  (~3 hours)
05:50 ET  Job 1 — strikezone_acquisition   (writes strikezone-latest.json pointer)
              ↓  (10-minute window)
06:00 ET  Job 2 — sbp_strikezone_digest    (reads pointer, writes digest, delivers Discord)
              ↓  (1 hour)
07:00 ET  Job 3 — operator_today           (reads vault state, produces operator brief)
              ↓  (12 hours)
19:00 ET  Job 4 — operator_close_day       (reads today's activity, produces close note)
```

- Job 2 **should not be blocked** by Job 1 failure. It degrades gracefully.
- Job 3 does not depend on Jobs 1 or 2.
- Job 4 depends on Job 3's output for its carry-forward, but does not hard-fail if the morning brief is missing.

---

## Disabled Watch Schedules

The following schedule intents exist but are disabled as of the 2026-04-27 runtime reset:

| Schedule ID | Workflow | Cron | Reason |
|-------------|----------|------|--------|
| `sch-openclaw-watch-every-minute` | openclaw_watch | `* * * * *` | Hold until the watch loop runs through lifecycle/bootstrap or a direct runner instead of OpenClaw agent-turn cron. |
| `sch-hermes-watch-every-minute` | hermes_watch | `* * * * *` | Hold until the watch loop runs through lifecycle/bootstrap or a direct runner instead of OpenClaw agent-turn cron. |

During reset, both watch cron entries took longer than one minute to complete, which caused overlapping agent turns and gateway pressure. Keep them disabled in both ChaseOS intent and OpenClaw cron until the execution path is changed or the single-cycle runtime is proven below the one-minute cadence.

Disabled schedules still live in `runtime/schedules/` and must validate, but they are excluded from `schedule export --adapter openclaw --json`.

---

## Environment Variables Required

| Variable | Required For | Where to Set |
|----------|-------------|--------------|
| `DISCORD_WEBHOOK_URL` | Job 2 — Discord delivery | OpenClaw execution environment |

**Rule:** Credentials are never in schedule files, manifest files, or this document. They live in the execution environment only. See `04_SOPS/Credential-Boundaries-SOP.md`.

---

## Verification Steps

After configuring OpenClaw cron, verify with:

### 1. Export the ChaseOS schedule intent
```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main schedule list
```
Expected: 7 schedules registered: 5 enabled cron workflows and 2 disabled watch schedules.

```powershell
.\.venv\Scripts\python.exe -m runtime.cli.main schedule export --adapter openclaw --json
```
Expected: `schedule_count: 5`.

### 2. Validate all schedule intents
```powershell
.\.venv\Scripts\python.exe -m runtime.cli.main schedule validate
```
Expected: No errors.

### 3. Run Job 1 manually (first time only)
```powershell
.\.venv\Scripts\python.exe -m runtime.cli.main run strikezone_acquisition
```
Expected: Exits successfully. `runtime/acquisition/packs/strikezone-latest.json` now exists.

### 4. Run Job 2 manually to confirm digest produces output
```powershell
.\.venv\Scripts\python.exe -m runtime.cli.main run sbp_strikezone_digest
```
Expected: File created at `07_LOGS/SBP-Runs/`. Discord delivery attempted if `DISCORD_WEBHOOK_URL` is set.

### 5. Check audit trail
Audit records appear in `07_LOGS/Agent-Activity/` — one JSON file per run, named `YYYYMMDD-HHMMSS__<workflow_id>__<audit_id[:8]>.json`.

---

## Rules for OpenClaw

1. **Do not add cron entries that are not in this document.** If a workflow isn't listed here, it is not scheduled.
2. **Do not change cron timing without first updating the intent file in `runtime/schedules/`.** OpenClaw cron is derived state. The intent file is the truth.
3. **Do not hardcode credentials** (`DISCORD_WEBHOOK_URL` or any API key) in cron config, scripts, or manifest files.
4. **If a job fails, do not silently retry.** The AOR engine handles escalation and logging. Let it fail, log the audit record, and let the operator investigate.
5. **When reconciling after a restart**, run `chaseos schedule list` to get the authoritative current state before reconfiguring cron.

---

## Source Files (for reference)

All schedule intent files live in `runtime/schedules/`:

| Intent File | Workflow | Cron |
|-------------|----------|------|
| `sch-os-hygiene-graph-0300.yaml` | os_hygiene_graph | `0 3 * * *` |
| `sch-strikezone-acquisition-0550.yaml` | strikezone_acquisition | `50 5 * * 1-5` |
| `sch-sbp-strikezone-digest-0600.yaml` | sbp_strikezone_digest | `0 6 * * 1-5` |
| `sch-operator-today-0700.yaml` | operator_today | `0 7 * * 1-5` |
| `sch-operator-close-day-1900.yaml` | operator_close_day | `0 19 * * 1-5` |
| `sch-openclaw-watch-every-minute.yaml` | openclaw_watch | disabled |
| `sch-hermes-watch-every-minute.yaml` | hermes_watch | disabled |

Full bridge contract and reconciliation protocol: `runtime/openclaw/schedule_bridge.md`

---

*runtime/openclaw/CRON-SETUP-GUIDE.md*
*Created: 2026-04-24 | Phase 9 Pass 1C closure pass | Updated: 2026-04-27 runtime reset*
*Next update required when: a new schedule is added, removed, or timing changes*


*Graph links: [[OpenClaw-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
