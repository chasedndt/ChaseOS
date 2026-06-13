---
title: ChaseOS Pulse Native Schedule Activation Gate
type: implementation-proof
status: complete-targeted
created: 2026-05-03
runtime: Codex
---

# ChaseOS Pulse Native Schedule Activation Gate

## Result

`runtime/pulse/native_schedule_activation_gate.py` now defines the supervised
activation gate for future ChaseOS Pulse native schedule activation.

The command is:

```powershell
chaseos pulse native-schedule-activation-gate --json
```

Optional request artifact write:

```powershell
chaseos pulse native-schedule-activation-gate --write-request --json
```

The write mode is restricted to:

```text
07_LOGS/Pulse-Decks/native-schedule-activation-requests/
```

## What It Is

This is an activation gate packet and pending-request writer. It verifies the
evidence that must exist before any future supervised schedule activation work
can be considered.

It is not a schedule activator.

## Required Evidence Slots

The gate requires real non-placeholder references for:

- `operator_approval_ref`
- `permission_envelope_ref`
- `run_queue_scope_ref`
- `audit_identity_ref`
- `runtime_adapter_scope_ref`
- `rollback_plan_ref`
- `external_scheduler_denial_ref`
- `canonical_writeback_denial_ref`

With no evidence, the gate reports `blocked_missing_activation_evidence`.

With all evidence references supplied, the gate reports
`ready_for_operator_supervised_activation`.

That ready state is still advisory. It does not grant approval or execute any
runtime work.

## What It Reads

- `runtime/schedules/manifests/chaseos_pulse_daily.yaml`
- `runtime/schedules/manifests/hermes_runtime_pulse.yaml`
- `runtime/pulse/native_schedule_runner_proof.py`

The gate composes the prior runner proof so ChaseOS can keep schedule intent
native while still blocking live execution until the next run-queue/audit proof
exists.

## What It Writes

Only when `--write-request` is passed, the command writes a pending
operator-review JSON request under:

```text
07_LOGS/Pulse-Decks/native-schedule-activation-requests/
```

The request records missing evidence and previews the future supervised lane.
It does not approve, consume, dispatch, enqueue, activate, or execute anything.

## Boundaries

This pass does not:

- start a schedule daemon
- enable or write schedule manifests
- write a run queue
- write Agent Bus tasks
- dispatch Hermes, OpenClaw, Codex, Claude Code, or any other runtime
- execute workflows
- grant approval
- execute approval requests
- call providers or connectors
- install OpenClaw cron, Windows Task Scheduler, or any external schedule owner
- mutate `Now.md`, Project-OS files, governance docs, or `02_KNOWLEDGE/`
- update the R&D workbook
- perform canonical writeback

## Current Smoke Evidence

The dry-run command reports two ChaseOS-owned inactive targets:

- `chaseos_pulse_daily`
- `hermes_runtime_pulse`

The request-write smoke created:

```text
07_LOGS/Pulse-Decks/native-schedule-activation-requests/2026-05-03-activation-request-chaseos_pulse_daily-hermes_runtime_pulse.json
```

The all-evidence smoke reports `ready_for_operator_supervised_activation` while
all execution authority fields remain false.

## Next Pass

The next pass is:

```text
chaseos-pulse-native-schedule-run-queue-audit-proof
```

That pass is now represented by
`runtime/pulse/native_schedule_run_queue_audit_proof.py` and
`chaseos pulse native-schedule-run-queue-audit-proof --json`. It proves
run-queue/audit packet shape only; it still does not write the real run queue,
write real audit events, activate schedules, dispatch runtimes, or execute
workflows.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
