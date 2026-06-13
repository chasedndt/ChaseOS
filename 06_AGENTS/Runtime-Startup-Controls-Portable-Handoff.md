---
title: Runtime Startup Controls Portable Handoff
type: architecture
status: active
created: 2026-05-02
updated: 2026-05-02
scope: framework-level
---

# Runtime Startup Controls Portable Handoff

> Permanent framework note for the runtime startup/autostart feature.
> This preserves the important implementation and product decisions from the runtime startup control work so the originating chat can be deleted.

---

## Purpose

ChaseOS runtimes must not become invisible background processes that users cannot inspect or control.

Any runtime lane that can start at login, run a gateway, maintain a coordination-watch loop, or register host startup artifacts must expose that behavior through ChaseOS-owned lifecycle state and user-facing controls.

This feature gives ChaseOS a reusable pattern for:
- declaring runtime startup surfaces
- reporting whether they are configured, registered, running, degraded, or proven after reboot
- previewing enable/disable actions before mutation
- toggling startup behavior through governed CLI/service-layer commands
- rendering the same controls in a local Studio-facing visual wrapper
- onboarding future runtimes without inventing a new startup-control path each time

---

## Current Implemented Surfaces

The current implementation provides these command families:

```powershell
chaseos runtime startup-surfaces --runtime <id|all> --json
chaseos runtime startup-surface-settings --runtime <id|all> --json
chaseos runtime startup-surface-toggle-plan --runtime <id> --surface <surface_id> --intent enable|disable --json
chaseos runtime startup-surface-mutation-contract --runtime <id> --surface <surface_id> --intent enable|disable --json
chaseos runtime startup-surface-approval-request --runtime <id> --surface <surface_id> --intent enable|disable [--gate-approval-id <id>] [--write-approval-request] --json
chaseos runtime startup-surface-approval-decision --gate-approval-id <id> --decision approved|denied [--write-approval-decision] --json
chaseos runtime startup-surface-executor-preflight --runtime <id> --surface <surface_id> --intent enable|disable --gate-approval-id <id> --plan-digest <sha256> --json
chaseos runtime startup-surface-approval-consumption --runtime <id> --surface <surface_id> --intent enable|disable --gate-approval-id <id> --plan-digest <sha256> [--write-approval-consumption] --json
chaseos runtime startup-surface-toggle --runtime <id> --surface <surface_id> --intent enable|disable --dry-run --json
chaseos runtime startup-surface-toggle --runtime <id> --surface <surface_id> --intent enable|disable --confirm
chaseos studio runtime-startup-controls --runtime <id|all> --json
chaseos studio runtime-startup-controls --runtime <id> --surface <surface_id> --intent enable|disable --action dry-run --json
chaseos studio runtime-startup-controls --runtime <id> --surface <surface_id> --intent enable|disable --action toggle --confirm-action
chaseos studio runtime-startup-controls-app --runtime <id|all> --dry-run --json
chaseos studio runtime-startup-controls-app --runtime <id|all> --host 127.0.0.1 --port 8766
chaseos studio runtime-cockpit --runtime <id|all> --json
chaseos studio runtime-cockpit-app --runtime <id|all> --dry-run --json
chaseos studio runtime-cockpit-app --runtime <id|all> --host 127.0.0.1 --port 8771
chaseos studio desktop-shell-app --runtime <id|all> --dry-run --json
chaseos studio desktop-shell-app --runtime <id|all> --host 127.0.0.1 --port 8772
```

Current status:
- CLI report/settings/plan/contract/preflight surfaces: COMPLETE / VERIFIED TARGETED.
- Guarded CLI toggle executor: COMPLETE / VERIFIED TARGETED.
- Approval request, decision, and exact-once consumption/idempotency marker artifacts: COMPLETE / VERIFIED TARGETED.
- Studio CLI wrapper: COMPLETE / VERIFIED TARGETED.
- Localhost visual wrapper: COMPLETE / VERIFIED TARGETED.
- First read-only Studio Runtime Cockpit desktop contract: COMPLETE / VERIFIED TARGETED (`chaseos studio runtime-cockpit`).
- First localhost-only read-only Studio Runtime Cockpit mount/app: COMPLETE / VERIFIED TARGETED (`chaseos studio runtime-cockpit-app`).
- First localhost-only read-only Studio Desktop shell mock over Runtime Cockpit: COMPLETE / VERIFIED TARGETED (`chaseos studio desktop-shell-app`).
- Targeted browser visual QA for the Studio Desktop shell mock: COMPLETE / VERIFIED TARGETED.
- Full standalone ChaseOS Studio desktop shell integration: PLANNED / NOT BUILT.
- Approval-driven host mutation executor for UI-triggered toggles: PLANNED / NOT BUILT; current blocker report and approved executor path are captured in `06_AGENTS/Studio-Startup-Host-Mutation-Executor-Blocker-Report.md`.
- Live confirmed host mutation from the visual app: CONFIGURED BUT UNVERIFIED unless a user instance has run and logged it; Phase 10 Studio must not claim real host startup mutation until the lower-phase lifecycle executor path in `Studio-Startup-Host-Mutation-Executor-Blocker-Report.md` is implemented, approved, and verified.

---

## Generic Runtime Startup Surface Model

Each runtime that supports startup/autostart control should declare startup surfaces in its lifecycle record under `runtime/lifecycle/<runtime_id>.lifecycle.yaml`.

Common surface IDs:

| Surface | Meaning |
|---|---|
| `gateway` | Runtime gateway/daemon launcher, often registered with host login/startup. |
| `coordination_watch_supervisor` | Current-session ChaseOS-owned coordination-watch loop supervisor. |
| `coordination_watch_bootstrap` | Host startup registration for the coordination-watch supervisor. |
| custom service surface | A runtime-specific service manager, launch agent, cron entry, systemd unit, or platform-native binding. |

Required portable fields for each supported surface:

| Field | Purpose |
|---|---|
| `surface_id` | Stable machine-readable ID. |
| `ui_label` | Human label for CLI/Studio surfaces. |
| `supported` | Whether this runtime supports the surface at all. |
| `toggle_supported` | Whether ChaseOS can expose enable/disable controls. |
| `current_state_source` | How ChaseOS reads state, for example `host_startup_file`, `host-process`, or `scheduler`. |
| `startup_registration_kind` | Host registration type, for example `windows-startup-folder`, `windows-task-scheduler`, `launch-agent`, `cron`, `service-manager`, or `none`. |
| `status_command` | Read-only proof/status command. |
| `enable_command` / `disable_command` | Runtime-native command if one exists, otherwise ChaseOS lifecycle commands own the mutation path. |
| proof/evidence paths | Files, scheduler task names, service names, heartbeats, logs, or success records used to distinguish states. |
| host/elevation notes | Whether the surface requires admin/elevated privileges, WSL, launch agents, cron, or platform-specific setup. |
| `mutation_status` | Truthful implementation status, not aspirational product text. |

If a runtime does not support startup controls, it should explicitly declare that status instead of making Studio infer it from missing fields.

---

## State Semantics

Do not collapse startup state into a single on/off label.

The UI and CLI must preserve these distinctions:

| State | Meaning |
|---|---|
| `off` | ChaseOS does not detect the configured startup registration. |
| `configured` | Required artifact/config exists, but host startup registration is not proven. |
| `registered` | Host startup registration exists, such as a Startup folder launcher or scheduler task. |
| `running` | A process/supervisor is currently live. |
| `degraded` | Expected evidence is missing, mismatched, stale, or partially failed. |
| `proven-after-reboot` | A post-login/reboot verification artifact proves startup behavior across a real restart/logon cycle. |

Current-session liveness is not reboot proof.

---

## User-Facing Operations

Recommended inspection flow:

```powershell
chaseos runtime startup-surfaces --runtime all --json
chaseos studio runtime-startup-controls --runtime all --json
```

Recommended safe preview flow:

```powershell
chaseos studio runtime-startup-controls --runtime <id> --surface <surface_id> --intent disable --action dry-run --json
```

Recommended confirmed CLI toggle flow:

```powershell
chaseos studio runtime-startup-controls --runtime <id> --surface <surface_id> --intent disable --action toggle --confirm-action
```

Recommended local visual wrapper:

```powershell
chaseos studio runtime-startup-controls-app --runtime <id|all> --host 127.0.0.1 --port 8766
```

The local app must remain loopback-only. It may render state and submit dry-run or confirmed toggle requests, but it must not write host startup files directly.

Recommended read-only Runtime Cockpit mount:

```powershell
chaseos studio runtime-cockpit-app --runtime <id|all> --host 127.0.0.1 --port 8771
```

This mount must remain loopback-only and read-only. It may serve the Runtime Cockpit contract through `/contract.json`, but it must not submit toggles, write approval material, start child apps, call providers, execute workflows, mutate schedulers, or write canonical memory.

Recommended read-only Studio Desktop shell mock:

```powershell
chaseos studio desktop-shell-app --runtime <id|all> --host 127.0.0.1 --port 8772
```

This shell mock must remain loopback-only and read-only. It may mount the Runtime Cockpit contract and App Launcher registry through shell-shaped routes, but it is not the full standalone Studio desktop shell and must not submit toggles, consume approvals, start child apps, call providers, execute workflows, mutate schedulers, or write canonical memory.

---

## Governance Boundary

Startup/autostart control is lifecycle control, not a casual settings write.

Rules:
- The UI never writes Startup folders, Task Scheduler entries, services, launch agents, cron entries, or lifecycle files directly.
- Mutations must route through `startup-surface-toggle` or a future approval-driven host mutation executor.
- Live mutation requires explicit confirmation.
- Higher-risk UI-triggered mutation should use `startup-surface-approval-request`, `startup-surface-approval-decision`, `startup-surface-executor-preflight`, and `startup-surface-approval-consumption` before any future host mutation executor runs.
- Every live mutation must write lifecycle mutation markers/events.
- Runtime permission, role, trust tier, provider config, secrets, and canonical knowledge are out of scope for startup toggles.
- Gateway inputs remain Tier 4 data and must not become command authority.

---

## Portability Rules for Other ChaseOS Instances

Do not hard-code this instance's paths into framework docs or new runtime templates.

Portable examples should use placeholders:

```text
<workspace_root>
<user_home>
<runtime_id>
<surface_id>
<host_startup_path>
<runtime_gateway_command>
<runtime_log_path>
```

Instance-specific lifecycle records may contain real local paths, such as:
- Windows Startup folder entries
- WSL distro/user/workdir values
- local diagnostic logs
- Task Scheduler task names
- service manager unit names
- launch agent plist paths
- cron entries

Those values are implementation truth for one installation, not framework defaults for every user.

For a new user instance, the runtime onboarding flow should ask or detect:
- operating system
- user home path
- workspace root
- runtime install path
- gateway command
- whether WSL, service manager, launch agent, cron, or Startup folder is needed
- desired autostart surfaces
- diagnostic log path
- proof command and post-login verification path

---

## New Runtime Onboarding Checklist

When adding a new runtime, include startup/autostart support in the same pass if the runtime can run persistently.

Checklist:

- [ ] Add or update `runtime/lifecycle/<runtime_id>.lifecycle.yaml`.
- [ ] Declare all startup surfaces or explicitly mark unsupported surfaces.
- [ ] Add `gateway` surface if the runtime has a gateway/daemon.
- [ ] Add `coordination_watch_supervisor` if the runtime participates in the ChaseOS coordination bus.
- [ ] Add `coordination_watch_bootstrap` if the coordination-watch loop should survive login/reboot.
- [ ] Declare platform/host registration kind.
- [ ] Declare status/proof commands.
- [ ] Declare launcher/target/evidence paths using instance-local truth.
- [ ] Add managed launcher profile if ChaseOS owns a wrapper script.
- [ ] Ensure `startup-surfaces` reports useful state.
- [ ] Ensure `startup-surface-settings` exposes user-manageable controls.
- [ ] Ensure approval request/decision/consumption artifacts work for any startup surface that needs an approval-driven UI flow.
- [ ] Add toggle tests with temp paths, not real user startup paths.
- [ ] Update runtime-specific runbook docs.
- [ ] Update Studio/lifecycle docs if a new surface type is introduced.
- [ ] Record build log, documentation-history note, daily note, and agent activity log.

Definition of done for startup/autostart onboarding:
- Users can inspect current startup state.
- Users can dry-run an enable/disable action.
- Users can run a confirmed toggle through the service layer.
- Approval artifacts can be requested, decided, preflighted, and consumed into exact-once markers without host mutation.
- The runtime appears in the Studio CLI model.
- The localhost visual wrapper can render the runtime surface.
- The read-only Runtime Cockpit app can mount the runtime contract without adding mutation authority.
- The read-only Studio Desktop shell mock can mount the Runtime Cockpit contract without adding mutation authority.
- The shell mock has browser-verified responsive overflow handling for narrow in-app widths.
- Docs state what is supported, what is unverified, and what is not built.

---

## Instance-Specific Evidence From This Workspace

This workspace's first implementation focused on OpenClaw and Hermes:

- OpenClaw already had a Windows Startup gateway lane and ChaseOS coordination-watch startup lane.
- Hermes was brought to parity with a Windows Startup gateway lane.
- Hermes gateway execution is WSL-hosted in this instance.
- The Hermes managed launcher enters Ubuntu as user `chaseos`, runs from this workspace path, retries while WSL starts, and writes a diagnostic startup log.
- The local app was verified by dry-run and health endpoint, not by confirmed visual live toggle.

These facts are useful implementation evidence for this instance, but other ChaseOS users should generate their own lifecycle records from their own host paths, runtime commands, users, WSL distros, service managers, and log locations.

---

## 2026-05-02 Chat Closeout Readiness

Status: CLOSEABLE / VERIFIED TARGETED.

The originating runtime-startup chat can be deleted. The important implementation and product truth from that chat is now permanent in ChaseOS docs, logs, generated CLI reference, tests, and runtime/studio command surfaces.

Current verified scope:
- `chaseos runtime startup-surfaces --runtime all --json` reports 4 runtimes, 6 startup surfaces, 6 toggle-capable surfaces, and no degraded startup surfaces.
- Hermes and OpenClaw gateway startup surfaces are registered.
- Hermes and OpenClaw coordination-watch supervisors are running in the current Windows session.
- Hermes gateway is modeled as a WSL-hosted launcher for Ubuntu/user/workdir/log retry behavior in this instance.
- `chaseos runtime startup-surface-settings --runtime all --json` exposes user-manageable toggle commands for Hermes/OpenClaw surfaces.
- `chaseos studio runtime-startup-controls --runtime all --json` exposes the Studio-facing Runtime Cockpit model.
- `chaseos studio runtime-startup-controls-app --runtime all --dry-run --json` exposes the localhost visual wrapper model and allowed actions.
- `chaseos studio runtime-cockpit --runtime all --json` exposes the first read-only desktop contract over the dashboard, app launcher, and runtime startup controls.
- `chaseos studio runtime-cockpit-app --runtime all --dry-run --json` exposes the first localhost-only read-only Runtime Cockpit mount over the contract.
- `chaseos studio desktop-shell-app --runtime all --dry-run --json` exposes the first localhost-only read-only Studio Desktop shell mock over the Runtime Cockpit contract.
- `chaseos studio app-launcher --dry-run --json` lists the Runtime Startup Controls app, Runtime Cockpit app, and Studio Desktop shell mock for operator launch.
- `chaseos studio dashboard --json` exposes the runtime startup panel and app launcher panel.

Current proof boundary:
- `proven_after_reboot` is currently `0`; no post-login/reboot verification artifact was observed in this closeout pass.
- Coordination-watch bootstrap surfaces for Hermes/OpenClaw are currently partial because the Windows Task Scheduler query reports the tasks are not registered, even though current-session supervisors are running and historical success records exist.
- The localhost visual wrapper, Studio CLI model, first Runtime Cockpit desktop contract, read-only Runtime Cockpit local mount, and read-only Studio Desktop shell mock expose controls, approval readiness, host-boundary policy preview, and audit-template preview, but full standalone Studio desktop shell integration remains unbuilt.
- Approval request/decision/consumption/idempotency artifacts are built, but a production approval-driven host mutation executor remains future work.

Closeout conclusion:
- The original chat-scoped runtime startup feature is done enough to close the chat.
- Remaining items are future product/live-proof work, not missing chat context.
- New ChaseOS user instances should onboard startup surfaces through lifecycle records and the portable checklist above, not by copying this machine's local paths.

---

## Remaining Product Work

Still future:
- full standalone ChaseOS Studio desktop Runtime Cockpit shell integration
- approval-driven host mutation executor for UI-triggered startup toggles
- persisted user preference records beyond lifecycle mutation markers
- generalized `start`, `stop`, `restart`, and `logs` runtime lifecycle commands
- post-login/reboot verification proof per installed user instance
- platform adapters beyond the current Windows/WSL-oriented implementation evidence

---

## Canonical Related Files

- `runtime/lifecycle/README.md`
- `06_AGENTS/ChaseOS-Runtime-Lifecycle-Contract.md`
- `06_AGENTS/Runtime-Startup-Controls-Post-Reboot-Checklist.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Hermes-Operations-Runbook.md`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `runtime/studio/runtime_cockpit.py`
- `runtime/studio/runtime_cockpit_app.py`
- `runtime/studio/desktop_shell_app.py`
- `runtime/studio/runtime_startup_controls.py`
- `runtime/studio/runtime_startup_controls_app.py`
- `runtime/lifecycle/startup_surfaces.py`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
