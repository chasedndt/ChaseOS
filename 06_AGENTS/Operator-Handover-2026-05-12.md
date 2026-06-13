---
title: Operator Handover — 2026-05-12
type: handover
created: 2026-05-12
scope: Hermes cron + WSL gateway + hardening checklist + Phase 11 state
status: open
---

# Operator Handover — 2026-05-12

> Open this at the start of your next session. Work top to bottom.
> Items marked ✅ are done. Items marked ⬜ need action.

---

## What Was Completed This Session

| ✅ Done | Detail |
|---------|--------|
| Option C — Hermes self-contained cron | `hermes_watch.py` now polls all schedules itself each cycle. One Task Scheduler entry replaces per-workflow cron entries. 51 tests pass. |
| WSL Gateway fix | `%USERPROFILE%\.hermes\gateway.cmd` rewritten with two-phase approach: Phase 1 explicitly starts Ubuntu (`wsl -d Ubuntu -- exit`, retries every 5s up to 20x), Phase 2 launches the gateway (retries every 60s up to 6x). Replaces broken `timeout` with reliable `ping -n` delays. |
| Google Gemini clarification | `Operator-Setup-Checklist.md` updated: Gemini subscription ≠ Google Docs/Drive API access. `google_enabled: false` is the right setting. |
| `tzdata` + `pip` + `pyyaml` installed | `tzdata` required for cron timezone evaluation. `pip` was missing from venv — bootstrapped and reinstalled. `pyyaml` reinstalled (required by ChaseOS Gate hook). |

---

## Remaining — Operator Actions (do these yourself)

### ⬜ 1. Run the credential check (takes 30 seconds)

Paste this in the terminal:

```powershell
! echo "PERPLEXITY: $env:PERPLEXITY_API_KEY"; echo "IMAP_USER: $env:IMAP_USER"; echo "GMAIL: $env:GMAIL_IMAP_USER"; echo "GOOGLE_OAUTH: $env:GOOGLE_OAUTH_TOKEN"; echo "GOOGLE_SA: $env:GOOGLE_SERVICE_ACCOUNT_FILE"
```

Note which are set (non-empty) vs blank. You need this for items 2 and 3 below.

---

### ⬜ 2. C-1: Strikezone acquisition schedule hardening

**If `PERPLEXITY_API_KEY` was non-empty above**, disable the schedule first:
```
! chaseos schedule disable sch-strikezone-acquisition-0550
```

Then apply shadow mode (recommended):

**File:** `runtime/schedules/sch-strikezone-acquisition-0550.yaml`
- Change `enabled: true` → `enabled: false`
- Change `shadow_mode: false` → `shadow_mode: true`

**File:** `runtime/workflows/registry/strikezone_acquisition.yaml`
- Change `approval_rule: none` → `approval_rule: operator-first-run`

**If `PERPLEXITY_API_KEY` was empty**, the spending risk is zero but shadow mode is still recommended.

---

### ✅ 3. M-2/P-D2 adapter flags — DONE

Implemented with safe defaults. All credential-requiring adapters are off by default.

**Files changed:**
- `runtime/acquisition/plans/strikezone-daily.json` — `adapter_flags` block added
- `runtime/acquisition/live_sources.py` — reads flags, skips disabled categories before any network call
- `runtime/acquisition/adapters/email_adapter.py` — `enabled` guard added
- `runtime/acquisition/adapters/google_adapter.py` — `enabled` guard added on both entry points

**To enable Perplexity when you get an API key:** open `runtime/acquisition/plans/strikezone-daily.json` and change `"perplexity_enabled": false` → `true`. That's the only change needed.

---

### ⬜ 4. Create the Windows Task Scheduler entry for `hermes_watch`

This is the one external trigger that activates Option C. Hermes then handles all other schedules itself.

1. Open **Task Scheduler** (search Start menu)
2. Click **Create Task** (not Basic Task)
3. **General tab:**
   - Name: `ChaseOS-Hermes-Watch`
   - Run with highest privileges: checked
4. **Triggers tab → New:**
   - Begin the task: At log on
   - Repeat task every: **1 minute**
   - For a duration of: Indefinitely
5. **Actions tab → New:**
   - Action: Start a program
   - Program: `%CHASEOS_VAULT_ROOT%\.venv\Scripts\python.exe`
   - Arguments: `%CHASEOS_VAULT_ROOT%\chaseos.py run hermes_watch`
   - Start in: `%CHASEOS_VAULT_ROOT%`
6. **Conditions tab:** Uncheck "Start only if on AC power" if on a laptop
7. Click OK

Once active, Hermes evaluates all 9 schedules every minute and fires due workflows automatically.

---

## Hardening Scorecard

| Section | Status |
|---------|--------|
| Section 1 — Credential check | ⬜ Not run yet |
| Section 2 — C-1 strikezone hardening | ⬜ Pending credential check |
| Section 3 — M-2/P-D2 adapter flags | ✅ Implemented with safe defaults (all credential adapters off; flip `perplexity_enabled: true` in `strikezone-daily.json` when ready) |
| Section 4 — Hermes cron executor (Option C) | ✅ Implemented — Task Scheduler entry still needed |
| Section 5 — Credentials setup | ⬜ Optional (only if you want adapters live) |
| WSL gateway | ✅ Fixed — two-phase wake + launch, 60s retry |

**Completing Sections 1–3 brings hardening from 19/25 to full operational state.**
The remaining 6 are deferred architecture items with no immediate action required.

---

## Phase 11 State (for context — no action required now)

**Current marker:** `operator-action-required-no-autonomous-phase11-pass`

All read-only/audit passes are complete. Portable installer ZIP is built and verified.

Six executor lanes remain and each requires an explicit operator authority decision before Archon can proceed:

| Lane | Blocked on |
|------|-----------|
| Companion selection executor | Operator selects companion + approves write |
| Live provider/model execution | Operator selects model + approves |
| Runtime dispatch executor | Operator approves |
| Browser dispatch executor | Operator approves |
| Approval target mutation executor | Operator approves |
| Agent Bus / canonical writeback | Operator approves |

**To activate a lane:** open a new session and name which one you want. Archon runs only that governed pass.
**To close Phase 11 as-is:** say "close Phase 11 at the current read-only boundary".

---

## Files to Open in IDE

| File | Why |
|------|-----|
| `runtime/schedules/sch-strikezone-acquisition-0550.yaml` | C-1 shadow_mode toggle |
| `runtime/workflows/registry/strikezone_acquisition.yaml` | C-1 approval_rule change |
| `%USERPROFILE%\.hermes\gateway.cmd` | WSL gateway (fixed — review if needed) |
| `06_AGENTS/Operator-Setup-Checklist.md` | Full checklist with all steps |

---

*Handover created: 2026-05-12 | Session: Hermes Option C cron + WSL gateway fix + venv repair*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*

*Graph links: [[OpenClaw-Runtime-Profile]]*
