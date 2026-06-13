---
title: ChaseOS Runtime Lifecycle Contract
type: architecture
status: seeded
created: 2026-04-24
updated: 2026-05-01
phase: phase-9-active, phase-10-relevant
---

# ChaseOS Runtime Lifecycle Contract

> This document defines how ChaseOS should eventually manage runtime start/stop/restart behavior for bounded external runtime lanes such as OpenClaw and Hermes.
It now also covers the adjacent question of **runtime-owned coordination-watch loop launching** for the ChaseOS coordination bus.

---

## 1. Why This Exists

ChaseOS now has a growing runtime inspection surface:
- runtime state resolution
- runtime status CLI foothold
- Gate policy inspection
- a local CLI integration seam

But runtime inspection is not the same as runtime lifecycle control.

If ChaseOS is to become the real control plane for its runtime lanes, it must eventually define how it manages:
- starting runtimes
- stopping runtimes
- restarting runtimes
- determining whether a runtime is healthy or running
- launching and supervising the runtime's coordination-bus refresh loop

This document defines that contract.

---

## 2. Core Distinction

ChaseOS should distinguish between two command classes:

### A. Runtime inspection
Examples:
- `chaseos runtime resolve`
- `chaseos runtime status`

These commands inspect current runtime posture.

### B. Runtime lifecycle control
Examples:
- `chaseos runtime start <runtime>`
- `chaseos runtime stop <runtime>`
- `chaseos runtime restart <runtime>`
- `chaseos runtime coordination-watch <runtime>`

These commands affect live runtime processes, service posture, or long-running runtime-owned coordination loops.

They are not the same and should not be conflated.

---

## 3. Runtimes in Scope

First lifecycle-managed runtimes should be:
- `openclaw`
- `hermes`

Why these first:
- both are already treated as named runtime lanes in ChaseOS doctrine
- both have runtime-specific identity/profile/binding surfaces
- both are meaningful enough to justify explicit lifecycle ownership

---

## 4. Command Contract (Target Shape)

```text
chaseos runtime status [--runtime <id>] [--refresh] [--json]
chaseos runtime resolve [--runtime <id>] [--json]
chaseos runtime start <runtime>
chaseos runtime stop <runtime>
chaseos runtime restart <runtime>
chaseos runtime health <runtime>
chaseos runtime status <runtime>
chaseos runtime logs <runtime>
chaseos runtime coordination-watch <runtime> [--once|--interval N]
chaseos runtime coordination-watch-supervisor <runtime> [--action plan|status|start|stop] [--interval N]
chaseos runtime coordination-watch-bootstrap <runtime> [--action plan|status|install|remove]
chaseos runtime coordination-watch-bootstrap <runtime> [--action apply|verify|unregister|handoff|reboot-verify|capture-success|reconcile-reboot-result|activation-report|activation-checklist]
chaseos runtime startup-surfaces [--runtime <id|all>] [--json]
chaseos runtime startup-surface-settings [--runtime <id|all>] [--json]
chaseos runtime startup-surface-toggle-plan --runtime <id> --surface <surface_id> --intent enable|disable [--json]
chaseos runtime startup-surface-mutation-contract --runtime <id> --surface <surface_id> --intent enable|disable [--json]
chaseos runtime startup-surface-approval-request --runtime <id> --surface <surface_id> --intent enable|disable [--gate-approval-id <id>] [--write-approval-request] [--json]
chaseos runtime startup-surface-approval-decision --gate-approval-id <id> --decision approved|denied [--write-approval-decision] [--json]
chaseos runtime startup-surface-executor-preflight --runtime <id> --surface <surface_id> --intent enable|disable --gate-approval-id <id> --plan-digest <sha256> [--json]
chaseos runtime startup-surface-approval-consumption --runtime <id> --surface <surface_id> --intent enable|disable --gate-approval-id <id> --plan-digest <sha256> [--write-approval-consumption] [--json]
chaseos runtime startup-surface-toggle --runtime <id> --surface <surface_id> --intent enable|disable --confirm [--json]
chaseos studio runtime-startup-controls --runtime <id|all> [--json]
chaseos studio runtime-startup-controls --runtime <id> --surface <surface_id> --intent enable|disable --action dry-run|toggle [--confirm-action] [--json]
```

This means the `runtime` family should eventually have two subdomains:
- inspection
- lifecycle

Current promotion note (2026-04-27):
- `status` and `health` are live inspection surfaces
- `coordination-watch`, `coordination-watch-supervisor`, and `coordination-watch-bootstrap` are bounded lifecycle footholds for bus refresh and host-startup evidence
- `startup-surfaces` is a read-only Studio-facing report over lifecycle-declared gateway/autostart/control surfaces
- `startup-surface-settings` is a read-only CLI/Studio settings model over those surfaces, including user-manageable toggle metadata and managed launcher profiles
- `startup-surface-toggle-plan` is a read-only Studio-facing preview of enable/disable intent, target state, required future mutation steps, and verification commands for one startup surface
- `startup-surface-mutation-contract` is a read-only approval/execution contract for the same future mutation path; it declares required Gate operation names, operator evidence, write-target categories, external side-effect boundary, verification commands, audit records, and rollback behavior while keeping host mutation disabled
- `startup-surface-approval-request` and `startup-surface-approval-decision` write/preview repo-local approval artifacts for exact runtime/surface/intent requests
- `startup-surface-executor-preflight` validates the approval artifact id and plan digest against current state, required Gate operation, and idempotency marker posture before consumption
- `startup-surface-approval-consumption` writes only repo-local approval-consumption and exact-once idempotency marker artifacts; it does not mutate host startup
- `startup-surface-toggle` is the guarded CLI executor for one concrete runtime/surface/intent; it requires `--confirm` for live mutation, supports `--dry-run`, writes runtime lifecycle mutation markers/events, and only calls the declared host Startup-folder/process/scheduler lane for that surface
- `studio runtime-startup-controls` is the Studio CLI wrapper over the same settings model and lifecycle executor; it renders Studio-ready control cards, supports `--action dry-run`, and requires `--confirm-action` for live `--action toggle`
- coordination-watch run, supervisor start/stop, and bootstrap install/apply/verify/unregister/handoff/reboot-verify/capture-success/reconcile-reboot-result/activation-report/remove now have named Gate runtime operations and explicit lifecycle/process/scheduler allowlists
- general runtime `start`, `stop`, `restart`, and `logs` remain target-shape commands until their runtime-operation policy approval rules are explicit
- before promotion, each new lifecycle side effect needs a named Gate operation, actor/target manifest requirements where applicable, process authority boundaries, log read/write scope, approval posture, and blocker/precondition documentation such as `06_AGENTS/Studio-Startup-Host-Mutation-Executor-Blocker-Report.md` for the still-deferred approval-driven startup/autostart host mutation executor

---

## 5. What Lifecycle Control Must Know

A lifecycle-managed runtime record must now define or be capable of defining:
- runtime id
- startup method
- shutdown method
- restart behavior
- expected health signal
- coordination-watch launch defaults
- coordination-watch supervision defaults
- startup/autostart UI support declarations
- gateway launcher registration kind and enable/disable command surface, when supported
- coordination-watch bootstrap registration kind and enable/disable command surface, when supported
- proof surfaces that distinguish `configured`, `registered`, `running`, and `proven-after-reboot`
- log location
- service owner or process model
- platform assumptions

This now belongs in the live machine-readable layer:
- `runtime/lifecycle/`

---

## 6. Proposed Future Runtime Lifecycle Record

Example shape:

```yaml
runtime_id: openclaw
platform: windows
lifecycle_mode: external-service
start_command: openclaw gateway start
stop_command: openclaw gateway stop
restart_command: openclaw gateway restart
health_check:
  kind: command
  command: openclaw gateway status
log_hint: runtime/openclaw/
ownership: chaseos-managed
notes: OpenClaw is a bounded external runtime lane with ChaseOS governance overlays.
```

Hermes may use a different mode, for example:
- direct process
- WSL command
- script wrapper
- service unit

That is why lifecycle records should be runtime-specific.

---

## 7. Safety Rules

Lifecycle control is more powerful than runtime inspection.
So ChaseOS should apply explicit safety rules:

- lifecycle commands must only target declared runtimes
- runtime start/stop/restart should be idempotent where possible
- failure should return a clear error and log target
- health checks should be separate from state resolution
- lifecycle control should not silently alter policy, bindings, or runtime identity files

---

## 8. Relationship to OpenClaw and Hermes

### OpenClaw
OpenClaw is the active bounded runtime lane.
ChaseOS should eventually be able to:
- inspect its runtime posture
- check whether its gateway/runtime is healthy
- restart it through a defined lifecycle method

### Hermes
Hermes is a named runtime in ChaseOS and a peer authority runtime instance alongside OpenClaw under `06_AGENTS/Runtime-Instance-Authority-Parity.md`.
If Hermes remains a maintained runtime lane, ChaseOS should apply the same lifecycle model to it as a matter of runtime parity, even when current machine-local implementation breadth differs.

---

## 9. Alignment with the Overall ChaseOS OS

This contract matters because a real operating system does not only inspect runtimes.
It eventually manages them.

That is a later and more powerful layer than runtime-state reporting.
But it should grow from the same family tree, not as a separate unrelated control plane.

This is part of ChaseOS moving from:
- runtime doctrine
- runtime state
- runtime CLI inspection

toward:
- runtime lifecycle ownership
- runtime health management
- eventual local control-plane capability

---

## 10. Current Live Coordination-Watch Supervision Truth

ChaseOS now has a bounded supervision foothold for runtime coordination-watch loops:
- lifecycle records declare `coordination_watch.supervision`
- `runtime/lifecycle/coordination_watch_supervisor.py` builds a runtime-specific launch plan
- `runtime coordination-watch-supervisor` and `chaseos runtime coordination-watch-supervisor` can:
  - inspect the planned background command
  - inspect current background state
  - start the loop in a bounded local background process
  - stop that process and clear runtime-owned state

This is **not yet full OS service management**.
It is a ChaseOS-owned bootstrap/supervision foothold that brings long-running coordination loops under explicit runtime lifecycle ownership.

Gate posture:
- `start` and `stop` are now blocked by `lifecycle.coordination_watch_supervisor.start` / `stop` policy before local host process side effects
- lifecycle supervisor state/log writes are scoped to the `runtime_lifecycle_state` allowlist

## 11. Current Live Coordination-Watch Bootstrap Registration Truth

ChaseOS now also has a bounded bootstrap-registration foothold above that supervisor layer:
- lifecycle records declare `coordination_watch.bootstrap`
- `runtime/lifecycle/coordination_watch_bootstrap.py` builds host-registration artifacts and command previews
- it now also writes structured bootstrap event records so registration attempts, handoffs, verification, and cleanup remain visible after the immediate shell output is gone
- it now also builds bounded post-registration reboot-verification bundles so ChaseOS can define what should be checked after a successful elevated registration and subsequent host restart/logon and write a durable host-side observed-result JSON artifact; the generated verifier treats scheduler registration as true only when the scheduler query returns zero and the expected task name appears in output
- it now also captures durable success-state records from observed scheduler + supervisor evidence so post-boot truth is not only spoken in chat
- `capture-success` now prefers a host-written reboot verification result when one exists and matches the expected runtime/task identity, so restart/logon evidence can reconcile directly into the success-state layer instead of being re-entered manually; mismatched reboot-result artifacts are rejected and do not count as proof
- `reconcile-reboot-result` now exists as an explicit operator-facing wrapper for that same preference path when the operator wants to request reconciliation directly rather than rely on the generic success-capture wording
- `activation-report` now exists as a read-only evidence aggregator over bootstrap status, scheduler query, supervisor state, agent-bus heartbeat freshness, success-state records, and reboot verification results; it validates evidence identity and scheduler-query proof before exposing both live-liveness readiness and full proof completion, so startup proof cannot be inferred from a currently running loop alone
- `activation-checklist` now exists as a read-only operator checklist built from the activation report; it turns missing evidence into ordered steps, ready CLI commands, host/elevation-required actions, and evidence paths without mutating host scheduler, supervisor, or lifecycle artifacts
- `startup-surfaces` now exists as a read-only aggregator over lifecycle-declared startup/autostart surfaces for Studio. It reports per-surface state and proof boundaries without enabling, disabling, registering, unregistering, starting, stopping, or editing host startup state.
- `startup-surface-settings` now exists as a read-only settings model for CLI/Studio startup controls. It reports user-manageable toggle surfaces, live CLI enable/disable commands, dry-run commands, plan/contract/preflight commands, and managed launcher profile/drift evidence without itself editing launchers or mutating host startup state.
- `startup-surface-toggle-plan` now exists as a read-only pre-mutation planner for Studio. It requires one concrete runtime, one surface, and `--intent enable|disable`, then returns the target state, service-layer mutation steps, read-only verification commands, and an explicit no-mutation boundary.
- `startup-surface-mutation-contract` now exists as a read-only contract for UI/approval wrapping. It composes the toggle plan with approval evidence requirements, per-surface Gate operation names, write-target categories, external side-effect classification, verification commands, audit records, and rollback steps while reporting the CLI-confirm executor as implemented and approval-driven host mutation as pending.
- `startup-surface-approval-request`, `startup-surface-approval-decision`, and `startup-surface-approval-consumption` now exist for guarded artifact flows. Request/decision artifacts live under `07_LOGS/Agent-Activity/_runtime_startup_surface_approvals/`; consumption writes only an approval-consumption record plus exact-once idempotency marker and leaves host mutation disabled.
- `startup-surface-executor-preflight` now exists as a validator for an approval-artifact flow. It requires a concrete runtime, surface, intent, `--gate-approval-id`, and `--plan-digest`, then reports approval artifact status, current plan digest, Gate-operation match, idempotency marker path/presence, and explicit safety flags before any consumption or host mutation.
- `startup-surface-toggle` now exists as the guarded CLI executor. It requires `--runtime`, `--surface`, `--intent enable|disable`, and `--confirm` for live mutation. `--dry-run --json` previews the exact target files and Gate operation without mutation. Gateway enable writes/repairs the declared managed target launcher plus Startup-folder delegate; gateway disable removes only the declared Startup-folder delegate. Supervisor and bootstrap surfaces route through their declared lifecycle process/scheduler operations and record lifecycle mutation markers/events.
- `studio runtime-startup-controls` now exists as a Studio-facing CLI wrapper. It renders Runtime Cockpit startup-control cards from the settings report and calls the same lifecycle startup-surface executor for `--action dry-run|toggle`; live toggle still requires `--confirm-action` and Gate checks.
- it now also emits an Agent Activity / runtime-audit markdown record when that captured evidence confirms a real startup success cycle
- `runtime coordination-watch-bootstrap` and `chaseos runtime coordination-watch-bootstrap` can:
  - inspect the intended host-registration plan
  - write launcher scripts and machine-readable registration artifacts
  - report whether those artifacts are present
  - remove those artifacts cleanly
  - attempt Task Scheduler registration through the declared command
  - verify whether the named task is visible to the host scheduler
  - emit a ready-to-run elevated handoff bundle when the current shell is privilege-bounded
  - append structured bootstrap event records for install/apply/verify/handoff/unregister/remove visibility
  - emit a bounded reboot-verification bundle for post-registration restart/logon checks, including a durable result-output path for host-side observed evidence
  - capture a durable success-state record from later observed scheduler + supervisor evidence, including reconciliation from a host-written reboot verification result artifact when present
  - explicitly trigger that same reconciliation path through `reconcile-reboot-result` when the operator wants a named reboot-result import action
  - emit a bounded Agent Activity record when the captured evidence confirms scheduler registration plus expected supervisor artifacts together
  - inspect an ordered activation checklist that names the current step and separates repo-local commands from host/elevation-required actions
  - reverse the scheduler entry through the declared unregister command

Gate posture:
- bootstrap artifact/evidence writes are scoped to `runtime_lifecycle_state`
- host scheduler query/register/unregister paths are bound to the `host.scheduler` external API allowlist
- actions that mutate scheduler state (`apply`, `unregister`) are marked as external side effects and blocked before host calls when policy denies them

Important boundary:
- this is **registration-artifact ownership plus bounded elevated handoff generation plus bounded reboot-verification planning**, not proof that the host scheduler has already been mutated
- on this machine, the current live shape is a Windows Task Scheduler-oriented artifact/command bundle, including WSL launch indirection for Hermes
- live smoke on this machine currently returns `Access is denied.` for scheduler mutation from the present shell, so the apply/verify surface is truthful but still privilege-bounded
- the new `handoff` action exists specifically to bridge that boundary safely by generating a PowerShell/UAC-ready elevated registration bundle rather than silently pretending the current shell can cross it
- the new `reboot-verify` action defines the post-registration evidence bundle and now predeclares a durable result artifact path, but it still does **not** itself prove persistence until a successful elevated registration and later restart/logon actually occur and write that observed result; the generated script now records scheduler registration only when the scheduler query returns zero and the expected task name appears in output
- the new `capture-success` action records the currently observed post-boot truth, now preferring a host-written reboot verification result when available and identity-matched, and it emits Agent Activity writeback only when that truth reaches `success_observed: true`; on this machine today it still honestly evaluates to `success_observed: false` until a real elevated registration has happened
- the new `reconcile-reboot-result` action is an explicit wrapper around that same evidence path; it does not manufacture stronger truth than the available reboot-result artifact or live verify surface
- the new `activation-report` action reports `activation_state`, `proof_ready`, `proof_complete`, named checks, missing evidence, evidence-validation issues, and next actions; `activation_state: proven` now requires scheduler registration, running supervisor, fresh heartbeat, validated success-state evidence, and validated reboot-verification evidence together. It does not install, register, start, stop, or otherwise mutate the host
- the new `activation-checklist` action is a read-only activation runbook over that report. It gives an ordered command/action plan but does not create artifacts, register a scheduler task, start a supervisor, run reboot verification, or reconcile evidence

## 12. Recommended Next Step

After this contract, the next implementation/design pass should define:
- how the broad Studio desktop Runtime Cockpit should adopt the existing localhost `studio runtime-startup-controls-app` service contract and when higher-risk flows should require approval request/decision/preflight/consumption artifacts instead of direct `--confirm-action`
- how approval-consumed startup-surface flows should hand off to a future host mutation executor without bypassing exact-once markers
- how successful elevated registration should be executed and later re-verified on the actual host, not just through bounded artifact generation
- whether the explicit `reconcile-reboot-result` wrapper should later gain distinct audit/event semantics beyond the current bounded wrapper behavior
- which commands can be safely delegated to existing runtime-native control surfaces versus ChaseOS-managed local supervisors and bootstrap artifacts

For OpenClaw, this likely means reusing its native runtime control commands instead of inventing a duplicate process manager.

## 13. Studio Runtime Startup Toggle Contract

Phase 10 Studio must render runtime startup/autostart control as a user-facing Runtime Cockpit feature.

The target behavior:
- each lifecycle-managed runtime may declare one or more startup surfaces, such as a gateway launcher, coordination-watch supervisor, host bootstrap registration, or service manager binding
- Studio displays one explicit operator toggle per supported startup surface, not a hidden implicit autostart behavior
- toggle state must distinguish `off`, `configured`, `registered`, `running`, `degraded`, and `proven-after-reboot`
- enabling a toggle must call a declared lifecycle/Gate operation or service-layer wrapper; Studio must not write host Startup folders, Task Scheduler entries, services, launch agents, or cron jobs directly
- disabling a toggle must call a declared unregister/remove operation and record the result in lifecycle/audit evidence
- every toggle must expose proof links or paths for activation reports, success records, scheduler/service checks, supervisor state, heartbeat freshness, and relevant Agent Activity records
- current-session running proof is not the same as post-reboot proof; the UI must make that distinction visible

Future runtime onboarding requirement:
- a runtime is not considered fully Studio-ready until its lifecycle record declares the startup UI contract for that runtime
- if a runtime does not support user-controlled startup, it must declare that explicitly so Studio can show "startup control not supported" rather than guessing
- new runtime adapter/profile work should add the required lifecycle fields at the same time it adds gateway, service, coordination-watch, or autostart behavior

Initial known lanes:
- OpenClaw: existing Windows Startup gateway launcher plus ChaseOS coordination-watch lifecycle artifacts should be represented as separate startup surfaces
- Hermes: Windows Startup `Hermes Gateway.cmd` and Windows-hosted coordination-watch supervisor/bootstrap state should be represented as separate startup surfaces, with WSL gateway execution noted as runtime-specific host detail. The Hermes gateway managed launcher profile is WSL Ubuntu, user `chaseos`, repo workdir `<VAULT_ROOT>`, command `<WSL_HOME>/.local/bin/hermes gateway run`, retry-on-logon behavior, and diagnostic log `<HERMES_HOME>/<path>`.

Current backend status: **PARTIAL / LOCAL STUDIO VISUAL WRAPPER IMPLEMENTED + STUDIO CLI WRAPPER IMPLEMENTED + CLI TOGGLE EXECUTOR IMPLEMENTED + REPORT/SETTINGS/PLAN/CONTRACT/PREFLIGHT/APPROVAL-ARTIFACT REQUEST/DECISION/CONSUMPTION IMPLEMENTED / BROAD STUDIO DESKTOP INTEGRATION UNBUILT / APPROVAL-DRIVEN HOST MUTATION EXECUTOR UNBUILT**. Hermes/OpenClaw lifecycle records declare gateway, coordination-watch supervisor, and coordination-watch bootstrap startup surfaces. `chaseos runtime startup-surfaces --runtime all --json` exposes the read-only state model, `chaseos runtime startup-surface-settings --runtime all --json` exposes the CLI/Studio settings model, `chaseos runtime startup-surface-toggle-plan --runtime <id> --surface <surface_id> --intent enable|disable --json` exposes a no-mutation confirmation plan for Studio, `chaseos runtime startup-surface-mutation-contract --runtime <id> --surface <surface_id> --intent enable|disable --json` exposes the no-mutation approval/UI contract, `chaseos runtime startup-surface-approval-request`, `startup-surface-approval-decision`, `startup-surface-executor-preflight`, and `startup-surface-approval-consumption` provide the repo-local approval artifact and exact-once marker chain without host mutation, `chaseos runtime startup-surface-toggle --runtime <id> --surface <surface_id> --intent enable|disable --confirm` performs the direct guarded CLI toggle, `chaseos studio runtime-startup-controls --runtime <id|all> --json` plus `--action dry-run|toggle` provides the Studio CLI control wrapper, and `chaseos studio runtime-startup-controls-app --runtime <id|all> --host 127.0.0.1 --port 8766` provides the localhost visual wrapper.

Portable handoff for other ChaseOS user instances: `06_AGENTS/Runtime-Startup-Controls-Portable-Handoff.md`. That document is the compact durable feature summary and onboarding checklist for future runtimes and non-personal ChaseOS installs.

---

*Graph links: [[ChaseOS-CLI-Surface-Architecture]] · [[ChaseOS-Runtime-Command-Contract]] · [[ChaseOS-Runtime-State-and-Gateway-Design]] · [[OpenClaw-Adapter-Spec]] · [[Hermes-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
