---
title: Runtime Startup Controls Post-Reboot Checklist
type: operator-checklist
status: active
created: 2026-05-02
updated: 2026-05-02
scope: runtime-startup-controls
---

# Runtime Startup Controls Post-Reboot Checklist

Keep this file open before rebooting.

Purpose: collect proof after a real Windows reboot/logon for the Hermes/OpenClaw runtime startup surfaces. This is not new implementation work. It is live evidence collection for the startup/autostart feature that is already implemented.

---

## What Is Already Done

Implementation status: COMPLETE / VERIFIED TARGETED / CHAT CLOSEABLE.

Built and verified:
- Hermes Gateway startup launcher, including WSL Ubuntu entry, retry-on-logon behavior, and diagnostic logging.
- OpenClaw Gateway startup surface.
- `chaseos runtime startup-surfaces`
- `chaseos runtime startup-surface-settings`
- `chaseos runtime startup-surface-toggle`
- `chaseos studio runtime-startup-controls`
- `chaseos studio runtime-startup-controls-app`
- Dashboard runtime startup panel.
- Studio app launcher visibility.
- Approval request/decision/consumption/idempotency artifact chain.
- Portable onboarding rules for future ChaseOS user instances.

Remaining after reboot: proof collection, not core feature implementation.

---

## After Reboot

Wait 2-3 minutes after Windows login so Startup folder launchers, WSL, and coordination-watch supervisors have time to settle.

Open PowerShell in the ChaseOS workspace:

```powershell
cd <VAULT_ROOT>
```

Create a timestamp for evidence files:

```powershell
$stamp = Get-Date -Format yyyyMMdd-HHmmss
```

---

## 1. Capture Overall Startup Surface State

Run:

```powershell
python -m runtime.cli.main runtime startup-surfaces --runtime all --json | Tee-Object "runtime\lifecycle\run\runtime-startup-post-reboot-$stamp.json"
```

Good signs:
- `ok: true`
- `runtime_count: 4`
- `surface_count: 6`
- Hermes `gateway` state is `registered`
- OpenClaw `gateway` state is `registered`
- Hermes `coordination_watch_supervisor` state is `running`
- OpenClaw `coordination_watch_supervisor` state is `running`
- `degraded` count is `0`

Important boundary:
- `proven_after_reboot` may still be `0` unless a reboot verification artifact was generated and imported.
- If `coordination_watch_bootstrap` is `partial`, that means the startup registration proof is incomplete. It does not automatically mean the gateway startup implementation failed.

---

## 2. Capture Hermes Bootstrap Activation Report

Run:

```powershell
python -m runtime.cli.main runtime coordination-watch-bootstrap --runtime hermes --action activation-report --json | Tee-Object "runtime\lifecycle\run\hermes-bootstrap-post-reboot-$stamp.json"
```

Good signs:
- `proof_ready` is `true` or useful evidence is present.
- `supervisor_running` is `true`.
- `heartbeat_fresh` is `true`.
- `success_observed` is `true`.

If this still says `scheduler_registered: false`, record it. That means the Task Scheduler registration still needs a future proof/config pass.

---

## 3. Capture OpenClaw Bootstrap Activation Report

Run:

```powershell
python -m runtime.cli.main runtime coordination-watch-bootstrap --runtime openclaw --action activation-report --json | Tee-Object "runtime\lifecycle\run\openclaw-bootstrap-post-reboot-$stamp.json"
```

Good signs:
- `supervisor_running` is `true`.
- `heartbeat_fresh` is `true`.
- `success_observed` is `true`.

If this still says `scheduler_registered: false`, record it. That means the Task Scheduler registration still needs a future proof/config pass.

---

## 4. Check Studio Dashboard Model

Run:

```powershell
python -m runtime.cli.main studio dashboard --json | Tee-Object "runtime\studio\state\studio-dashboard-post-reboot-$stamp.json"
```

Good signs:
- `runtime_startup_panel` exists.
- `surface_count` is `6`.
- `manageable_surface_count` is `6`.
- Hermes and OpenClaw startup cards are present.
- `app_launcher_panel` exists and lists `runtime-startup-controls-app`.

---

## 5. Check Hermes Gateway Diagnostic Log

Run:

```powershell
Get-Content "$env:USERPROFILE\.hermes\gateway-startup.log" -Tail 120
```

Good signs:
- A timestamp near the reboot/logon time.
- `Hermes gateway startup begin`
- `wsl.exe -d Ubuntu -u chaseos`
- No repeated final failure after all retry attempts.

If Hermes starts but exits with errors, keep the tail output for the next pass.

---

## 6. Optional Host Registration Checks

Check Startup folder entries:

```powershell
Get-ChildItem "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup" | Where-Object { $_.Name -like '*Hermes*' -or $_.Name -like '*OpenClaw*' } | Select-Object Name,FullName,LastWriteTime
```

Check Task Scheduler entries:

```powershell
schtasks /Query /TN ChaseOS-Hermes-Coordination-Watch
schtasks /Query /TN ChaseOS-OpenClaw-Coordination-Watch
```

If Task Scheduler reports that the task cannot be found, do not treat the whole feature as failed. Record it as:

```text
coordination_watch_bootstrap remains partial: Task Scheduler registration missing after reboot.
```

---

## What To Bring Back To Codex

Start the next chat/pass with:

```text
Run runtime-startup-controls-post-reboot-proof. I rebooted and collected the evidence files.
```

Then provide or point Codex to:
- `runtime/lifecycle/run/runtime-startup-post-reboot-<stamp>.json`
- `runtime/lifecycle/run/hermes-bootstrap-post-reboot-<stamp>.json`
- `runtime/lifecycle/run/openclaw-bootstrap-post-reboot-<stamp>.json`
- `runtime/studio/state/studio-dashboard-post-reboot-<stamp>.json`
- the tail of `<HERMES_HOME>/<path>` if Hermes had errors

---

## Interpretation

### Pass

Treat the reboot proof as good if:
- Hermes Gateway is registered and launches through the WSL profile.
- OpenClaw Gateway remains registered.
- Hermes/OpenClaw coordination-watch supervisors are running after login.
- Heartbeats are fresh.
- Studio dashboard still sees the startup controls.

### Partial

Treat as partial if:
- Gateway registration is good.
- Supervisors are running.
- But `coordination_watch_bootstrap` still lacks Task Scheduler registration or reboot-verification evidence.

This is a follow-up proof/config issue, not a reason to reopen the completed implementation chat.

### Fail

Treat as failed if:
- Hermes Gateway is missing from Startup folder.
- Hermes managed target launcher is missing or hash-mismatched.
- WSL launch repeatedly fails in `gateway-startup.log`.
- Both Hermes and OpenClaw supervisors are not running after a reasonable wait.
- `startup-surfaces` reports degraded state.

---

## Related Docs

- `06_AGENTS/Runtime-Startup-Controls-Portable-Handoff.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `07_LOGS/Build-Logs/2026-05-02-ChaseOS-runtime-startup-controls-chat-closeout-readiness.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
