---
title: Runtime Launch & Internal Terminal — Operator Handover
status: live
updated: 2026-06-11
runtime_node: "[[Chaser-Agent-Runtime-Profile]]"
---

# Runtime Launch & Internal Terminal — Operator Handover

How to launch and test the **Hermes** and **OpenClaw** gateways and runtime
daemons **from inside ChaseOS Studio**, plus the executing internal terminal. No
external PowerShell window required.

> **Key correction to a prior note:** Studio **can** launch the runtimes, and the
> internal **Terminal** panel **does execute** commands. The read-only thing is the
> separate **Terminal Workbench (records)** panel — that one is deliberately
> review-only. Use the **Terminal** panel for live execution and the **Runtime
> Launchers** / Runtime Cockpit for gateway+daemon launch.

---

## 1. The two launch surfaces (both already wired)

### A. Runtime launch buttons — `launch_runtime_component`
`StudioAPI.launch_runtime_component(runtime_id, component_id)` →
`runtime/studio/runtime_gateway_controls.py`. Launches one component, tracks PID,
writes an event log, supports `dry_run`, and detects "already running".

| runtime | component | what it runs |
|---|---|---|
| hermes | `daemon` | `python -m runtime.cli.main runtime daemon --runtime hermes --vault-root <vault>` (bus consumer, bounded) |
| hermes | `gateway` | `cmd /c ~/.hermes/gateway.cmd` → launches the **credentialed WSL Hermes gateway** |
| openclaw | `daemon` | `python -m runtime.cli.main runtime daemon --runtime openclaw --vault-root <vault>` |
| openclaw | `gateway` | `cmd /c ~/.openclaw/gateway.cmd` (Windows) |

All four resolve and spawn on this machine (verified 2026-06-11). Both gateway
launchers exist: `~/.hermes/gateway.cmd`, `~/.openclaw/gateway.cmd`.

**Two ways to get genuine Hermes model replies:**
1. Launch the **`gateway`** — the WSL Hermes that holds the model key (simplest).
2. Launch the **`daemon` with the approval-gated `synthesize` opt-in** (added
   2026-06-11). `--synthesize` is NEVER hardcoded (audit item C-2): pass
   `synthesize=True` **and** a non-empty `synthesize_approval_id`, or the launch is
   refused with `status: approval_required`. Dry-run shows the flag + the
   `runtime_daemon_synthesis_launch` approval scope without spawning. Every synth
   launch is audited to `studio-runtime-gateway-control-events.jsonl`.

   ```python
   # dry-run preview (shows --synthesize, requires approval):
   launch_runtime_component(vault, "hermes", "daemon", synthesize=True, dry_run=True)
   # real launch (needs an approval id):
   launch_runtime_component(vault, "hermes", "daemon",
                            synthesize=True, synthesize_approval_id="<appr-id>")
   ```
   StudioAPI: `launch_runtime_component(runtime_id, component_id, synthesize, synthesize_approval_id, dry_run)`.

The plain Studio-launched `daemon` (no opt-in) stays bounded — it claims/coordinates
bus tasks but does not call a provider. Provider-agnostic by design — Studio never
holds a key; synthesis runs inside the Hermes daemon with the runtime's own creds.

### B. Internal executing terminal — `runtime/studio/terminal_sessions.py`
Real subprocess execution with multi-tab sessions, per-command classification,
Tier-4 audited output. A true interactive PTY/ConPTY turns on automatically when
`pywinpty` is installed (`PTY_AVAILABLE`); otherwise it runs line-oriented
subprocess mode (still executes — verified `echo` round-trips).
**As of 2026-06-11, `pywinpty` is installed in `.venv` → `PTY_AVAILABLE: True`,
backend `conpty_pywinpty` (true interactive terminal).**

API: `create_terminal_session`, `write_terminal_input`, `read_terminal_output`,
`list_terminal_sessions`, `attach_terminal_session`, `terminate_terminal_session`,
`resize_terminal_session`, `interrupt_terminal_session`. Frontend: the **Terminal**
panel (`#panel-terminal`) — tab bar, session list, **Runtime Launchers**, input row.

---

## 2. Test it — step by step

### 2.1 From the CLI (fastest sanity check)
```powershell
# dry-run the launch commands (no spawn):
.venv\Scripts\python -c "from pathlib import Path; from runtime.studio.runtime_gateway_controls import launch_runtime_component as L; [print(r,c, L(Path('.').resolve(), r, c, dry_run=True)['command']) for r in ('hermes','openclaw') for c in ('daemon','gateway')]"
```
Expect four resolved commands. If a gateway line raises "launcher is missing",
the `~/.<runtime>/gateway.cmd` file isn't there — (re)generate it (Section 4).

### 2.2 Launch a runtime daemon from Studio
```powershell
.venv\Scripts\python -c "from pathlib import Path; from runtime.studio.runtime_gateway_controls import launch_runtime_component as L; print(L(Path('.').resolve(),'openclaw','daemon'))"
```
Expect `status: started` + a `pid`. Confirms Studio spawns the bus consumer
attached to THIS vault.

### 2.3 Launch the Hermes gateway (genuine model lane)
In Studio: **Terminal panel → Runtime Launchers → Hermes → Gateway** (or call
`launch_runtime_component(vault,'hermes','gateway')`). This runs `~/.hermes/gateway.cmd`
which brings up the WSL Hermes. Verify it heartbeats into this vault's bus:
```powershell
.venv\Scripts\python -c "from pathlib import Path; from runtime.agent_bus.bus import list_heartbeats; [print(h['runtime'], h.get('last_seen')) for h in list_heartbeats(Path('.').resolve())]"
```
Hermes `last_seen` should be seconds-fresh. Then the Chat runtime-status flips to
**Ready · live reply** and a Studio chat message gets a genuine Hermes reply.

### 2.4 Use the internal terminal
Studio: **Terminal** panel → **New Session** → type `echo hello` → Send. Output
streams in-panel. Open more tabs for parallel sessions. Catastrophic commands
(`rm -rf /`, `shutdown`, `mkfs`, fork bomb) are refused and audited; everything
else runs.

---

## 3. 24/7 always-on

Set the component's startup mode to `chaseos_start` (launch when Studio starts) or
`system_start` (OS startup) via the Runtime Gateway Controls preferences
(`runtime/studio/state/runtime-gateway-controls.json`, written through the API).
Detached daemons (`start_new_session`) survive Studio closing.

---

## 4. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "gateway launcher is missing" | `~/.<rt>/gateway.cmd` absent | regenerate via the lifecycle startup-surface tooling (`startup_surfaces`), or restore the file |
| Terminal feels non-interactive | `PTY_AVAILABLE: False` (no pywinpty) | `.venv\Scripts\pip install pywinpty` → restart Studio for true ConPTY |
| Daemon launched but no live chat reply | Studio daemon is bounded (no key) | launch the **gateway** instead (credentialed WSL Hermes) |
| "already_running" | component already up | stop first via `stop_runtime_component` or use the Stop button |
| Hermes heartbeat stale after gateway launch | gateway pointed at a different vault | ensure the WSL Hermes opens this vault's bus (`--vault-root /mnt/c/...`, see portable resolution in `coordination_watch_supervisor`) |

---

## 5. Governance posture (unchanged, honest)
- The internal Terminal **executes** under audit (Tier-4 output, catastrophic guard).
  Execution is logged to `07_LOGS/Terminal-Sessions/`.
- Gateway launch records an operator approval; daemon launch is operator-initiated.
- Studio never holds a model key and never calls a provider — synthesis happens
  only inside the runtime (gateway). Provider-agnostic.
- The **Terminal Workbench (records)** panel stays read-only — it is the review/
  audit surface, not an execution surface.

## 6. Status of prior enhancements (DONE 2026-06-11)
- ✅ True interactive PTY: `pywinpty` installed → `PTY_AVAILABLE: True`.
- ✅ Approval-gated `synthesize` opt-in on the Studio Hermes daemon launch (C-2
  respected — never hardcoded; requires a valid, approved, single-use approval id).

## 7. Control-plane hardening (added 2026-06-11)
- **Real synthesize approval ids** — `runtime/studio/runtime_synthesis_approval.py`
  (request → approve → consume-once). `launch_runtime_component` now *validates* the
  id (exists + approved + unconsumed + right runtime); "any non-empty string" no
  longer works. UI: a "Genuine replies (synthesize)" checkbox on the Hermes daemon
  launcher mints+approves+launches in one governed click. API:
  `request_synthesis_approval`, `approve_synthesis_approval`, `list_synthesis_approvals`.
- **Daemon watchdog (24/7)** — `runtime/studio/runtime_watchdog.py`:
  `check_runtime` (read-only verdict: heartbeat freshness + PID + restart_policy),
  `run_watchdog` (restarts down + `restart_policy in {auto,always,on-failure}` daemons
  via the governed launcher; never auto-enables synthesis). API:
  `runtime_watchdog_check` (dry-run), `runtime_watchdog_run`. Set a runtime's
  `restart_policy: auto` in its coordination-watch config to enable auto-restart.
- **Model-config visibility** — `runtime/studio/runtime_model_info.py`
  (`get_runtime_model_info`/`list_runtime_model_info`): which model each runtime is on
  (provider + primary + fallbacks), secrets redacted. API: `get_runtime_model_info`.
- **One control-plane audit feed** — `runtime/studio/control_plane_audit.py`:
  `get_control_plane_audit` (terminal sessions + runtime launches + synthesis
  approvals, newest-first) and `tail_log`. API: `get_control_plane_audit`,
  `tail_runtime_log(runtime_id, lines)` (vault-guarded).

## 8. Not done (honest)
- **De-marshal `runtime/studio/shell/api.py` back to source** — NOT done. Its core is
  recovered `cpython-314` bytecode; there is no reliable 3.14 decompiler and the
  original source is gone, so a faithful restore isn't safely possible. Consequence:
  Studio API unit tests only run under Python 3.14 (the real Studio runtime). New
  control-plane logic above lives in standalone, fully-tested modules to avoid this.
- **Streaming chat tokens, multi-harness compare view, retry/regenerate** — designed,
  not built (frontend/streaming-heavy; recommended next).
