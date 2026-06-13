---
title: Hermes Operations Runbook
type: operational-runbook
status: active-runbook
version: 1.1
created: 2026-04-20
phase: 9
owner: ChaseOS
---

# Hermes Operations Runbook

This runbook documents how to operate Hermes safely on this machine while preserving the current ChaseOS boundary:

- Hermes is an active bounded Discord runtime lane.
- The approved Hermes workflow set is exact and narrow: `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`.
- Hermes may post to designated Discord channels (hermes-chat, alerts-hermes, debug-hermes, audit-writeback).
- Hermes may write advisory and shadow draft/audit artifacts only; no canonical vault state changes.
- Hermes has no shell authority through ChaseOS.
- Hermes has no connector, external network, or canonical promotion authority through ChaseOS.

This runbook does not grant new permissions. It is an operator procedure for starting, checking, restarting, and stopping the local Hermes process and dashboard safely.

## Paths

Real ChaseOS repo path from Windows:

```powershell
%CHASEOS_VAULT_ROOT%
```

Real ChaseOS repo path from Ubuntu/WSL:

```bash
<WSL_CHASEOS_VAULT_ROOT>
```

Do not operate Hermes from an empty Linux-side mirror such as:

```bash
<CHASEOS_VAULT_ROOT>
```

unless that directory has been intentionally created and verified as the real active repo. For this machine, use the `/mnt/c/...` path.

## Start WSL

From PowerShell:

```powershell
wsl --status
wsl -l -v
```

Enter Ubuntu:

```powershell
wsl -d Ubuntu
```

If Ubuntu is the default distribution, this is also acceptable:

```powershell
wsl
```

If WSL is confused or stale, cleanly shut it down from PowerShell and reopen Ubuntu:

```powershell
wsl --shutdown
wsl -d Ubuntu
```

## Enter The Real ChaseOS Repo

Inside Ubuntu:

```bash
export CHASEOS_REPO="<WSL_CHASEOS_VAULT_ROOT>"
cd "$CHASEOS_REPO"
pwd
```

The expected `pwd` output is:

```bash
<WSL_CHASEOS_VAULT_ROOT>
```

Verify repo binding before starting Hermes:

```bash
test -f HERMES.md
test -f PROJECT_FOUNDATION.md
test -f .chaseos/hermes_config.yaml
test -f runtime/policy/adapters/hermes.yaml
test -f runtime/workflows/registry/hermes_operator_today_shadow.yaml
test -f runtime/workflows/registry/hermes_review_execute.yaml
test -f runtime/workflows/registry/hermes_watch.yaml
test -f runtime/aor/hermes_shadow.py
```

If any command fails, stop. You are in the wrong directory or the repo is incomplete.

## Start Hermes Safely

Hermes must be started from the real ChaseOS repo path.

First verify the local Hermes launcher:

```bash
command -v hermes
hermes --help
```

Then start Hermes using the command form exposed by `hermes --help`, from the verified repo root.

Current Hermes v0.11 safe pattern for the messaging gateway in WSL:

```bash
cd "$CHASEOS_REPO"
hermes gateway run
```

This is foreground mode and is the safest WSL default. Keep the terminal open while the gateway is running.

If the installed background service is configured and WSL user-service linger is enabled:

```bash
cd "$CHASEOS_REPO"
hermes gateway restart
```

If `hermes gateway restart` reports that linger is not enabled, stop and get explicit operator approval before running `sudo loginctl enable-linger chaseos`. Linger is a persistent service-behavior change.

Do not add Discord, gateway, connector, shell, tunnel, webhook, or external network flags.

## Windows Startup Gateway Launcher

As of 2026-04-30, Hermes has a Windows Startup-folder launcher matching the local OpenClaw gateway pattern:

```text
%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Hermes Gateway.cmd
```

The Startup-folder file delegates to:

```text
%USERPROFILE%\.hermes\gateway.cmd
```

The delegated gateway command is intentionally secret-free. It sets only local runtime marker variables and launches the Hermes gateway through WSL Ubuntu from the verified ChaseOS repo path as user `chaseos`. As of 2026-05-01, it also retries after logon while WSL is coming online and writes a diagnostic log to `%USERPROFILE%\.hermes\gateway-startup.log`.

```powershell
wsl.exe -d Ubuntu -u chaseos -- bash -lc "cd <WSL_CHASEOS_VAULT_ROOT> && exec <WSL_HOME>/.local/bin/hermes gateway run"
```

This is a host startup convenience only. It does not grant Hermes new ChaseOS authority, shell authority through ChaseOS, connector authority, protected-file authority, canonical writeback, or direct promotion rights. The separate ChaseOS Hermes coordination-watch supervisor remains governed by `runtime/lifecycle/hermes.lifecycle.yaml`.

ChaseOS now exposes the settings/readiness model for this startup surface through:

```powershell
chaseos runtime startup-surface-settings --runtime hermes --json
```

That command shows the current state and the exact enable/disable commands. The direct CLI controls for the Hermes gateway startup entry are:

```powershell
chaseos runtime startup-surface-toggle --runtime hermes --surface gateway --intent enable --dry-run --json
chaseos runtime startup-surface-toggle --runtime hermes --surface gateway --intent enable --confirm

chaseos runtime startup-surface-toggle --runtime hermes --surface gateway --intent disable --dry-run --json
chaseos runtime startup-surface-toggle --runtime hermes --surface gateway --intent disable --confirm
```

`enable` writes or repairs the managed WSL retry target launcher and the Windows Startup-folder delegate. `disable` removes the Windows Startup-folder delegate and leaves `%USERPROFILE%\.hermes\gateway.cmd` in place so it can be re-enabled later. Both live commands write mutation evidence under `runtime/lifecycle/run/startup-surface-mutations/`. This does not grant Hermes any new ChaseOS authority.

The Studio-facing CLI wrapper is the easier operator control surface:

```powershell
chaseos studio runtime-startup-controls --runtime hermes --json
chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent enable --action dry-run --json
chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent enable --action toggle --confirm-action
chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent disable --action dry-run --json
chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent disable --action toggle --confirm-action
```

The Studio wrapper still uses the lifecycle/Gate startup-surface executor. It is not a direct host writer.

The localhost visual wrapper is:

```powershell
chaseos studio runtime-startup-controls-app --runtime hermes --dry-run --json
chaseos studio runtime-startup-controls-app --runtime hermes --host 127.0.0.1 --port 8766
```

This renders the Hermes startup controls locally and posts dry-run/live toggle attempts through the same lifecycle executor. Broad ChaseOS Studio desktop integration and approval-artifact consumption remain future work.

## ChaseOS Coordination-Watch Launcher

As of 2026-04-30, the Hermes gateway launcher runs through WSL, but the ChaseOS Hermes coordination-watch bootstrap launcher runs on Windows Python:

```powershell
cd /d "%CHASEOS_VAULT_ROOT%"
"%CHASEOS_VAULT_ROOT%\.venv\Scripts\python.exe" "%CHASEOS_VAULT_ROOT%\chaseos.py" runtime coordination-watch-supervisor --runtime hermes --action start
```

Do not run the ChaseOS coordination-watch loop against the Windows-hosted Agent Bus SQLite database from inside WSL for long-lived operation. Short WSL probes can work, but the long-running loop can fail on `/mnt/c/.../agent_bus.sqlite`. Keep the bus watcher Windows-hosted and keep the Hermes gateway WSL-hosted.

## Start The Hermes Dashboard On Localhost

The dashboard must bind to loopback only. Use `127.0.0.1`, not `0.0.0.0`.

First inspect the dashboard command:

```bash
hermes dashboard --help
```

Preferred safe pattern when the dashboard supports host and port flags:

```bash
cd "$CHASEOS_REPO"
hermes dashboard --host 127.0.0.1 --port 8787
```

If port `8787` is already in use, use the next local-only port:

```bash
hermes dashboard --host 127.0.0.1 --port 8788
```

Then:

```bash
hermes dashboard --host 127.0.0.1 --port 8789
```

Only use a port after confirming it is free. Do not bind to `0.0.0.0`. Do not expose the dashboard through ngrok, Cloudflare Tunnel, port forwarding, a webhook, or a public gateway.

## Verify CWD, Port, And Repo Binding

Inside Ubuntu, from the Hermes terminal or a second WSL terminal:

```bash
pwd
printf '%s\n' "$CHASEOS_REPO"
test -f "$CHASEOS_REPO/HERMES.md"
test -f "$CHASEOS_REPO/.chaseos/hermes_config.yaml"
test -f "$CHASEOS_REPO/runtime/workflows/registry/hermes_operator_today_shadow.yaml"
test -f "$CHASEOS_REPO/runtime/workflows/registry/hermes_review_execute.yaml"
test -f "$CHASEOS_REPO/runtime/workflows/registry/hermes_watch.yaml"
```

Check local dashboard ports in Ubuntu:

```bash
ss -ltnp | grep -E ':8787|:8788|:8789'
```

If `ss` is unavailable:

```bash
netstat -tulpn | grep -E ':8787|:8788|:8789'
```

From PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8787,8788,8789 -ErrorAction SilentlyContinue
```

Optional local dashboard probe:

```bash
curl -I http://127.0.0.1:8787/
```

If you used `8788` or `8789`, replace the port in the URL.

The dashboard should identify or operate against:

```bash
<WSL_CHASEOS_VAULT_ROOT>
```

If it shows a Linux home directory, a temporary folder, or an empty repo, stop Hermes and restart from the real repo path.

## Restart Hermes Cleanly

Use this sequence for foreground Hermes/gateway/dashboard terminals:

1. In the Hermes process terminal, press `Ctrl+C`.
2. In the dashboard process terminal, press `Ctrl+C`.
3. Confirm no Hermes dashboard port remains open:

```bash
ss -ltnp | grep -E ':8787|:8788|:8789'
```

4. If needed, list background jobs:

```bash
jobs -l
```

5. Only after identifying the exact stuck Hermes process, stop that process:

```bash
kill <pid>
```

6. Re-enter the real repo path:

```bash
cd <WSL_CHASEOS_VAULT_ROOT>
pwd
```

7. Restart Hermes and the dashboard using the safe start commands above.

Avoid broad process-kill commands unless the exact Hermes process has been identified.

If Hermes is running as the installed background gateway service, use:

```bash
cd <WSL_CHASEOS_VAULT_ROOT>
hermes gateway status
hermes gateway restart
hermes gateway status
```

If the restart reports that linger is not enabled, do not work around it with a hidden background process. Either use foreground `hermes gateway run` or explicitly approve the persistent linger change first.

## Stop Hermes Cleanly

Use this sequence:

1. Stop the dashboard with `Ctrl+C`.
2. Stop the Hermes process with `Ctrl+C`.
3. Verify ports are closed:

```bash
ss -ltnp | grep -E ':8787|:8788|:8789'
```

4. From PowerShell, optionally verify:

```powershell
Get-NetTCPConnection -LocalPort 8787,8788,8789 -ErrorAction SilentlyContinue
```

No result means those ports are not listening.

## Verify Hermes Is Still Shadow-Bounded

From the repo root:

```bash
grep -n "hermes_operator_today_shadow" .chaseos/hermes_config.yaml runtime/policy/adapters/hermes.yaml runtime/workflows/registry/hermes_operator_today_shadow.yaml
grep -n "hermes_review_execute" .chaseos/hermes_config.yaml runtime/policy/adapters/hermes.yaml runtime/workflows/registry/hermes_review_execute.yaml
grep -n "hermes_watch" .chaseos/hermes_config.yaml runtime/policy/adapters/hermes.yaml runtime/workflows/registry/hermes_watch.yaml
grep -n "gateway_inputs: \"disabled\"" .chaseos/hermes_config.yaml
grep -n "delivery_connectors: \"disabled\"" .chaseos/hermes_config.yaml
grep -n "network_connectors: \"disabled\"" .chaseos/hermes_config.yaml
grep -n "shell.execute" .chaseos/hermes_config.yaml
grep -n "canonical_promotion: \"forbidden\"" .chaseos/hermes_config.yaml
```

Expected truth:

- `approved_workflows` contains exactly `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`.
- `gateway_inputs` is disabled.
- `delivery_connectors` is disabled.
- `network_connectors` is disabled.
- `shell.execute` is forbidden.
- canonical promotion is forbidden.
- writable paths remain limited to draft/audit surfaces.

From PowerShell, the bounded Hermes test can be rerun without giving Hermes new authority:

```powershell
.venv\Scripts\python.exe runtime\aor\test_phase9_pass2_hermes_shadow.py
```

This is a ChaseOS AOR test, not a Discord or gateway activation.

## Verify Hermes Discord Gateway State

Hermes is an active bounded Discord runtime lane. The Discord gateway is the Hermes bot account registered in `.chaseos/discord_instance_bindings.yaml` — not the local Hermes process or dashboard.

**Dashboard ≠ Gateway.** The localhost dashboard (port 8787) is a local inspection surface. The Discord gateway is the registered bot account that connects to Discord's API. These are separate surfaces. The dashboard running does not imply Discord gateway activity. Discord gateway activity is governed by the bot token and connection state, not by whether the dashboard is running.

Verify Hermes Discord identity binding:

```bash
grep -A 12 "hermes:" .chaseos/discord_instance_bindings.yaml
```

Expected truth:

- `bot_user_id` and `application_id` match the registered Hermes bot account.
- `trust_tier: 2`, `execution_eligible: true`, `allowed_adapters: [hermes]`.
- `execution_lane_status: live`.
- `hermes_execution_via_discord_enabled: true`.

Verify Hermes gateway is bounded to the approved workflow:

```bash
grep -n "hermes_operator_today_shadow" .chaseos/hermes_config.yaml runtime/policy/adapters/hermes.yaml runtime/workflows/registry/hermes_operator_today_shadow.yaml
grep -n "hermes_review_execute" .chaseos/hermes_config.yaml runtime/policy/adapters/hermes.yaml runtime/workflows/registry/hermes_review_execute.yaml
grep -n "hermes_watch" .chaseos/hermes_config.yaml runtime/policy/adapters/hermes.yaml runtime/workflows/registry/hermes_watch.yaml
grep -n "shell.execute" .chaseos/hermes_config.yaml
grep -n "canonical_promotion: \"forbidden\"" .chaseos/hermes_config.yaml
```

Expected truth: approved_workflows contains exactly `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`; shell execute is forbidden; canonical promotion is forbidden.

Verify Hermes still may not do:

- Invoke shell commands.
- Use connectors beyond what the manifest declares.
- Write `02_KNOWLEDGE/`, `01_PROJECTS/`, `06_AGENTS/`, or any protected file.
- Approve its own Discord requests.
- Use `0.0.0.0` for the dashboard.

## Port Rules

- **Canonical dashboard port: `8787`.**
- Fallback local-only ports: `8788`, then `8789`.
- Port `9119` was used in an ad-hoc operator session and is not the canonical port. Do not use it for Hermes dashboard unless all of `8787`, `8788`, and `8789` are confirmed occupied.
- Bind host: `127.0.0.1` only.
- Forbidden bind host: `0.0.0.0`.
- Forbidden exposure: public tunnel, webhook, gateway, forwarded port, public DNS, or Discord gateway.
- If a port is in use, inspect first; do not reuse it blindly.
- Closing Hermes must close the selected dashboard port.

## Troubleshooting

### Wrong CWD

Symptom: Hermes starts but cannot see ChaseOS docs, workflow registry, or Hermes config.

Fix:

```bash
cd <WSL_CHASEOS_VAULT_ROOT>
pwd
test -f HERMES.md
test -f .chaseos/hermes_config.yaml
```

Then restart Hermes.

### Wrong Repo

Symptom: dashboard points to another repo or shows stale docs.

Fix: stop Hermes, stop dashboard, return to the `/mnt/c/...` ChaseOS repo path, verify `PROJECT_FOUNDATION.md`, `.chaseos/hermes_config.yaml`, and `runtime/aor/hermes_shadow.py`, then restart.

### Empty Linux Directory

Symptom: `<CHASEOS_VAULT_ROOT>` exists but has few or no ChaseOS files.

Fix:

```bash
cd <WSL_CHASEOS_VAULT_ROOT>
pwd
ls HERMES.md PROJECT_FOUNDATION.md .chaseos/hermes_config.yaml
```

Do not start Hermes from the empty Linux-side directory.

### Dashboard Port Conflict

Symptom: dashboard fails to start because `8787` is in use.

Fix:

```bash
ss -ltnp | grep -E ':8787|:8788|:8789'
```

Pick the next free local-only port and bind to `127.0.0.1`.

### Dashboard Accidentally Bound Publicly

Symptom: dashboard command used `0.0.0.0` or a public tunnel.

Fix: stop the dashboard immediately, verify the port is closed, and restart with `--host 127.0.0.1`.

### Hermes Discord Gateway Exceeds Bounded Scope

Symptom: a Hermes process, dashboard, or config claims shell authority, connector access, canonical promotion, or workflow authority beyond `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`.

Fix: stop Hermes, do not use the route, and return to governance review. Any expansion of Hermes Discord authority beyond the declared bounded scope requires a separate governance pass.

## Related Docs

- `HERMES.md`
- `.chaseos/hermes_config.yaml`
- `runtime/policy/adapters/hermes.yaml`
- `runtime/workflows/registry/hermes_operator_today_shadow.yaml`
- `runtime/workflows/registry/hermes_review_execute.yaml`
- `runtime/workflows/registry/hermes_watch.yaml`
- `06_AGENTS/Hermes-Adapter-Spec.md`
- `06_AGENTS/Hermes-Workflow-Boundaries.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`
- `06_AGENTS/ChaseOS-Discord-Control-Plane.md`


*Graph links: [[Hermes-Runtime-Profile]] · [[Vault-Map]]*
