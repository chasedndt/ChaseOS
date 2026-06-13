---
title: ChaseOS Operator Setup Checklist
type: operator-guide
created: 2026-05-11
scope: Hardening completion + Hermes executor activation
status: active
---

# ChaseOS Operator Setup Checklist

> Open this file in the IDE. Work top to bottom. Each section has a terminal command or
> file change to make. Check the box when done.

---

## Section 1 — Credential Check (do this first, right now)

Run this in the terminal. It tells you exactly which credentials are set in your env:

```powershell
! echo "PERPLEXITY: $env:PERPLEXITY_API_KEY"; echo "IMAP_USER: $env:IMAP_USER"; echo "GMAIL: $env:GMAIL_IMAP_USER"; echo "GOOGLE_OAUTH: $env:GOOGLE_OAUTH_TOKEN"; echo "GOOGLE_SA: $env:GOOGLE_SERVICE_ACCOUNT_FILE"
```

Note the output — you need it for Sections 2 and 3 below.

**XAI/Grok:** Not needed. No `XAI_API_KEY` is being used. Grok adapter calls in
`live_sources.py` fail gracefully and skip — no action required.

---

## Section 2 — C-1: Strikezone Acquisition Schedule (URGENT)

**Risk:** `sch-strikezone-acquisition-0550.yaml` has `enabled: true`. Fires weekdays at 05:50 ET.
If `PERPLEXITY_API_KEY` is set, it spends money with no approval gate.

### Step 2a — Check and disable if needed

If `PERPLEXITY_API_KEY` was non-empty in Section 1, run this immediately:

```
! chaseos schedule disable sch-strikezone-acquisition-0550
```

### Step 2b — Choose your remediation approach

**Option A — Shadow mode (recommended: safest, instant)**

Open: `runtime/schedules/sch-strikezone-acquisition-0550.yaml`

Change line `enabled: true` → `enabled: false`
Change line `shadow_mode: false` → `shadow_mode: true`

Then open: `runtime/workflows/registry/strikezone_acquisition.yaml`

Change line `approval_rule: none` → `approval_rule: operator-first-run`

**Option B — Approval gate only (keeps schedule live, blocks at approval stage)**

Open: `runtime/workflows/registry/strikezone_acquisition.yaml`

Change line `approval_rule: none` → `approval_rule: operator-first-run`

### When to re-enable

Re-enable the schedule only after:
1. P-D2 enabled flags are in place (Section 3)
2. You confirm which API keys you want active
3. You test with `chaseos run strikezone_acquisition` manually first

---

## Section 3 — M-2 / P-D2: Adapter Enabled Guards

**This section requires the credential state you checked in Section 1.**

### Background

`email_adapter.py` and `google_adapter.py` have no kill switch. If IMAP or Google
credentials are set, they run silently on every acquisition cycle. P-D2 fixes this by
adding per-adapter `enabled` flags to the acquisition plan.

### Step 3a — Tell me your credential state

After the Section 1 check, one of these is true:

**Case A: No IMAP or Google credentials set**
→ We add the enabled flags with all credential adapters defaulting to `false`.
→ No functional change — they were already failing silently. Now fails explicitly.

**Case B: IMAP credentials set (GMAIL_IMAP_USER / IMAP_USER)**
→ Decide: keep IMAP enabled or disable it. Email setup guide is in Section 5.

**Case C: Google credentials set (GOOGLE_OAUTH_TOKEN or GOOGLE_SERVICE_ACCOUNT_FILE)**
→ Decide: keep Google enabled or disable it. Google setup guide is in Section 5.

> **Note:** `google_adapter.py` reads Google **Docs** and **Drive** files (Google Workspace).
> It has nothing to do with Google Gemini (the AI model). A Gemini subscription does not
> give access to the Docs/Drive API. If your only Google access is Gemini → set `google_enabled: false`.
> No Google setup is needed.

### Step 3b — Code changes (Chaser Agent implements these once you confirm)

Once you report your credential state, Chaser Agent will implement:

**File 1:** `runtime/acquisition/plans/strikezone-daily.json`
Add an `adapter_flags` block:
```json
"adapter_flags": {
  "rss_enabled": true,
  "web_scrape_enabled": true,
  "perplexity_enabled": false,
  "grok_enabled": false,
  "email_enabled": false,
  "google_enabled": false
}
```
(Set `perplexity_enabled: true` if you want Perplexity live after credential confirmation.)

**File 2:** `runtime/acquisition/live_sources.py`
`run_all_live_acquisitions()` reads the `adapter_flags` from the plan and skips
disabled categories before making any network call.

**File 3:** `runtime/acquisition/adapters/email_adapter.py`
`run_email_acquisitions()` entry point: check `enabled` flag before executing.

**File 4:** `runtime/acquisition/adapters/google_adapter.py`
Same pattern as email.

---

## Section 4 — Hermes as Cron Executor

You declared Hermes as the primary schedule executor (schema change — all 9 schedule
files now say `runtime_adapter_target: hermes`). But Hermes still needs a mechanism
to actually fire the schedules at the right times.

Three options — pick one:

### Option A — Continue using OpenClaw as the actual cron runner (easiest, zero work)

All 9 schedules have `runtime_adapter_fallback: openclaw`. OpenClaw reads schedules
via `export_schedules_for_adapter("openclaw")` and receives `is_fallback: True` entries.
It fires `chaseos run <workflow_id>` as usual.

**Hermes is the declared owner of the intent. OpenClaw is the executor in practice.**
This is a valid operational posture. The schema ownership is still correct.

No action needed. Just keep OpenClaw running as it was.

### Option B — Windows Task Scheduler (replaces OpenClaw cron, no extra code)

For each timed schedule, create a Task Scheduler entry that runs:
```
chaseos run <workflow_id>
```
at the declared cron time.

Key schedules to wire:
| Task | Time | Command |
|------|------|---------|
| os_hygiene_graph | 03:00 ET daily | `chaseos run os_hygiene_graph` |
| strikezone_acquisition | 05:50 ET Mon-Fri | `chaseos run strikezone_acquisition` |
| sbp_strikezone_digest | 06:00 ET Mon-Fri | `chaseos run sbp_strikezone_digest` |
| operator_today | 07:00 ET Mon-Fri | `chaseos run operator_today` |
| operator_close_day | 19:00 ET Mon-Fri | `chaseos run operator_close_day` |

For every-minute watch loops, use a Task Scheduler entry that repeats every 1 minute:
| Task | Repeat | Command |
|------|--------|---------|
| chaser_agent_watch | every 1 min | `chaseos run chaser_agent_watch` |
| hermes_watch | every 1 min | `chaseos run hermes_watch --adapter hermes` |
| openclaw_watch | every 1 min | `chaseos run openclaw_watch --adapter openclaw` |
| events watch | every 1 min | `chaseos events watch --once --execute` |

### Option C — Build Hermes schedule polling in `hermes_watch.py` ✅ IMPLEMENTED

Schedule-polling logic is now built into `hermes_watch.py`:
- `_check_due_schedules()` calls `export_schedules_for_adapter("hermes")` each cycle
- Evaluates cron expressions against ET timezone (`zoneinfo` + `tzdata`)
- Fires due workflows via `subprocess.run` (fail-open)
- Deduplicates per-minute via `.chaseos/hermes_schedule_state.json`
- Respects `shadow_mode`: records intent but does not execute
- Never fires `hermes_watch` itself (recursion guard)

**To activate:** Create one Windows Task Scheduler entry:
```
Action: chaseos run hermes_watch
Schedule: Repeat every 1 minute
```
That single entry is the only external trigger needed. Hermes handles all other schedules.

---

## Section 5 — Credential Setup Guides (if you want to enable adapters)

### Perplexity (PERPLEXITY_API_KEY)

1. Log in at `https://www.perplexity.ai/settings/api`
2. Generate an API key
3. Set in PowerShell: `$env:PERPLEXITY_API_KEY = "pplx-..."`
4. To make permanent, add to your Windows user environment variables or a `.env` loader
5. Test: `! chaseos capture perplexity --query "test query"`

### Gmail / IMAP (GMAIL_IMAP_USER + GMAIL_APP_PASSWORD)

1. Gmail Settings → See All Settings → Forwarding and POP/IMAP → Enable IMAP → Save
2. Go to `https://myaccount.google.com/apppasswords`
3. Generate App Password: select Mail + your device
4. Set env vars:
   ```powershell
   $env:GMAIL_IMAP_USER = "your@gmail.com"
   $env:GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
   ```
5. Test: add an `EmailFetchSpec` to the acquisition plan and run manually

### Google Docs / Drive (GOOGLE_OAUTH_TOKEN)

For public shared documents (anyone with link can view): **no credentials needed**.

For private docs:
1. Install gcloud CLI: `https://cloud.google.com/sdk/docs/install`
2. Run: `! gcloud auth login`
3. Run: `! gcloud auth print-access-token`
4. Set: `$env:GOOGLE_OAUTH_TOKEN = "<token from above>"`
5. Token expires hourly — automate refresh or use a service account instead

For service account (longer-lived):
1. `https://console.cloud.google.com` → IAM & Admin → Service Accounts → Create
2. Download JSON key → save to `.chaseos/credentials/service-account.json`
3. Set: `$env:GOOGLE_SERVICE_ACCOUNT_FILE = "C:\..\.chaseos\credentials\service-account.json"`

---

## Section 6 — Deferred Items (nothing to do now)

These require external setup or architecture work. Not blocking anything current.

| Item | What it is | Gate to reopen |
|------|-----------|----------------|
| D-1 | Automated context routing engine | Phase 12 |
| D-2 | Multi-repo policy enforcement | Second vault creation |
| D-3 | `runtime/audit/` migration | Cross-session audit tooling |
| D-4 | ChaseOS-native cron runner | Phase 10/11 |
| D-7 | Coordination-watch activation proof | Before enabling watch loop schedules |
| D-8 | Research-pack SBP verification | Before enabling sbp_strikezone_digest |
| M-6 | MCP V1 live integration hardening | Before any production MCP endpoint |
| M-7 | Pulse pipeline — single approval flag | Architecture decision |

---

## Completion Checklist

- [ ] Section 1: Credential check run, output noted
- [ ] Section 2: C-1 strikezone schedule disabled or shadow_mode applied
- [ ] Section 3: Credential state reported to Chaser Agent, M-2/P-D2 code changes implemented
- [x] Section 4: Cron execution method chosen — **Option C implemented** (Hermes self-contained schedule polling; one Task Scheduler entry needed)
- [ ] Section 5: Any desired credentials set in env and tested

When all boxes are checked: hardening is complete to 19/25. Remaining 6 are deferred
architecture items with no immediate action required.

---

## Files to Have Open in IDE

| File | Why |
|------|-----|
| `runtime/schedules/sch-strikezone-acquisition-0550.yaml` | C-1 — enable/shadow_mode toggle |
| `runtime/workflows/registry/strikezone_acquisition.yaml` | C-1 — approval_rule change |
| `runtime/acquisition/plans/strikezone-daily.json` | P-D2 — adapter_flags target |
| `runtime/acquisition/live_sources.py` | P-D2 — dispatcher enforcement |
| `runtime/acquisition/adapters/email_adapter.py` | M-2 — enabled guard |
| `runtime/acquisition/adapters/google_adapter.py` | M-2 — enabled guard |
| `06_AGENTS/ChaseOS-Hardening-Passover.md` | Canonical audit register |

---

*Operator-Setup-Checklist.md — ChaseOS hardening completion + Hermes executor activation guide*
*Created: 2026-05-11 | Scope: C-1, M-2, P-D2, Hermes cron*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*

*Graph links: [[OpenClaw-Runtime-Profile]]*
