# Studio Startup Host Mutation Executor Blocker Report

Status: BLOCKED / DEFERRED
Created: 2026-05-12
Runtime lane: Phase 10 Studio over Phase 9 runtime/lifecycle governance
Primary task: P10 open item — actual startup/autostart host mutation execution from Studio

## Purpose

This report separates completed Studio/runtime startup readiness surfaces from the still-unbuilt actual startup/autostart host mutation executor.

The Phase 10 Studio side can already render startup state, request/decision/preflight/consumption posture, host-boundary previews, audit-template previews, and success-marker policy posture. That is not the same as being authorized to write Windows Startup-folder launchers, Task Scheduler entries, registry keys, services, launch agents, cron entries, or other host autostart state.

Current conclusion: actual Studio-triggered host startup/autostart mutation remains deferred. The correct next implementation path is a lower-phase runtime/lifecycle executor activation path, not a broad Studio desktop shortcut or direct UI write.

## Live Truth Checked

Files/surfaces inspected for this pass:

- `runtime/studio/runtime_startup_controls.py`
- `runtime/studio/runtime_cockpit_action_readiness.py`
- `runtime/studio/settings_runtime_controls_panel.py`
- `runtime/lifecycle/startup_surfaces.py`
- `runtime/policy/gateway_allowlists.json`
- `runtime/chaseos_gate.py`
- `06_AGENTS/ChaseOS-Hardening-Passover.md`
- `06_AGENTS/Phase9-Hardening-Passover.md`
- `06_AGENTS/Runtime-Startup-Controls-Portable-Handoff.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/ChaseOS-Runtime-Lifecycle-Contract.md`
- latest startup/runtime-cockpit build-log index entries from 2026-05-01 and 2026-05-02

Commands/smokes used for current posture:

```powershell
.venv/Scripts/python.exe chaseos.py runtime startup-surface-settings --runtime hermes --json
.venv/Scripts/python.exe chaseos.py studio runtime-startup-controls --runtime hermes --action model --json
.venv/Scripts/python.exe chaseos.py runtime startup-surface-executor-readiness --runtime hermes --surface gateway --intent enable --gate-approval-id dummy --plan-digest dummy --json
.venv/Scripts/python.exe chaseos.py runtime startup-surface-host-boundary-policy --runtime hermes --surface gateway --intent enable --gate-approval-id dummy --plan-digest dummy --json
.venv/Scripts/python.exe chaseos.py runtime startup-surface-host-mutation-audit-template --runtime hermes --surface gateway --intent enable --gate-approval-id dummy --plan-digest dummy --json
.venv/Scripts/python.exe chaseos.py runtime startup-surface-success-marker-acceptance-policy --runtime hermes --surface gateway --intent enable --gate-approval-id dummy --plan-digest dummy --json
```

## Completed Readiness / Request Surfaces

These surfaces exist and are allowed to remain visible to Studio/runtime cockpit code:

| Layer | Current state | Boundary |
|---|---|---|
| startup surface discovery | built | read-only rendering of lifecycle-declared startup/autostart surfaces |
| startup settings model | built | reports UI-ready settings and mutation metadata; does not itself mutate host state |
| toggle plan | built | read-only preview of intent, target, verification, rollback, and plan digest |
| mutation contract | built | read-only contract for future approval/execution path |
| approval request artifact | built | repo-local request artifact path; not host mutation |
| approval decision artifact | built | repo-local decision artifact path; not approval consumption or host mutation |
| executor preflight | built | validates exact approval/material posture before consumption; no host mutation |
| approval consumption / idempotency marker | built as repo-local artifact path | must remain separate from host mutation; create-new-only semantics |
| transaction-order report | built | read-only future sequence model; no host mutation |
| executor readiness packet | built | fail-closed eligibility model; executor disabled |
| host-boundary policy packet | built | read-only WSL/Windows boundary policy preview; blocked |
| host-mutation audit template packet | built | read-only future audit evidence template; blocked |
| success-marker evidence / acceptance packets | built | read-only verifier/policy posture; success marker writes blocked |
| Studio CLI wrapper | built | wraps lifecycle/Gate surfaces; no direct host writer |
| localhost visual wrapper | built | localhost-only; must not bypass lifecycle/Gate surfaces |
| Runtime Cockpit / desktop shell mock | built read-only footholds | must not submit toggles, consume approvals, mutate schedulers, or write canonical memory |

## Current Hermes Gateway Evidence

For Hermes `gateway` enable intent with dummy Gate material, the current no-mutation reports are intentionally blocked/fail-closed:

| Report | Current result |
|---|---|
| executor readiness | `read_only: true`, `readiness_status: blocked`, `executor_enabled_now: false`, `eligible_for_future_enablement: false`, `execution_enabled: false`, `host_mutation_attempted: false`, `approval_consumed: false`, `idempotency_marker_written: false` |
| host-boundary policy | `read_only: true`, `policy_status: blocked`, `executor_enabled_now: false`, `execution_enabled: false`, `host_mutation_attempted: false`, `approval_consumed: false`, `idempotency_marker_written: false` |
| host-mutation audit template | `read_only: true`, `executor_enabled_now: false`, `execution_enabled: false`, `host_mutation_attempted: false`, `approval_consumed: false`, `idempotency_marker_written: false` |
| success-marker acceptance policy | `read_only: true`, `acceptance_policy_status: blocked`, `executor_enabled_now: false`, `execution_enabled: false`, `host_mutation_attempted: false`, `approval_consumed: false`, `idempotency_marker_written: false`, `success_marker_written: false` |

Representative blockers include:

- `approval-driven-host-mutation-executor-not-built`
- `host-mutation-backend-not-enabled`
- `operator-confirmation-policy-not-finalized`
- `rollback-recovery-policy-not-finalized`
- `post-mutation-verification-policy-not-finalized`
- `wsl-windows-host-boundary-policy-not-finalized`
- `production-approval-to-mutation-envelope-not-enabled`
- `agent-activity-audit-template-not-finalized`
- `success-marker-acceptance-policy-not-approved`
- `success-marker-write-gate-not-approved`
- `host-executor-still-disabled`
- `approval-consumption-not-enabled-for-success-marker`

## Host Policy Gate

`runtime/policy/gateway_allowlists.json` currently declares `host.startup_folder` as an operator-gated external host API:

```json
"host.startup_folder": {
  "description": "Bounded local Windows Startup-folder launcher create/remove actions for declared runtime gateways.",
  "approval_gate": "operator",
  "audit_requirement": "startup_write_tag"
}
```

This is the right posture for Phase 10: host startup mutation is possible only through a named, operator-approved lane. The existence of this allowlist row does not activate Studio or runtime-host mutation by itself.

## Approved Executor Path

The future executor path must be service-layer/lifecycle-owned and must not be implemented as direct Studio UI filesystem/scheduler writes.

Approved path shape:

1. Operator selects exact runtime, surface, and intent in Studio/runtime controls.
2. Studio renders `startup-surface-toggle-plan` and `startup-surface-mutation-contract` with:
   - runtime id
   - surface id
   - intent
   - target host API
   - target file/task/service identity
   - plan digest
   - verification commands
   - rollback plan
   - Agent Activity/audit requirements
3. Operator creates or references a Gate approval request with the exact plan digest.
4. Operator/Gate decision record explicitly approves that exact runtime/surface/intent/operation/digest tuple.
5. `startup-surface-executor-preflight` reruns immediately before any write and validates:
   - approval artifact exists
   - approval status is approved
   - runtime/surface/intent match
   - Gate operation matches expected host API
   - plan digest is current
   - idempotency marker is absent or matches an already-completed exact-once execution
   - rollback and post-mutation verification material are present
6. Approval consumption writes a create-new-only repo-local consumption record and exact-once marker candidate, but does not yet claim host success.
7. The lower-phase host executor performs exactly one declared mutation through the approved lifecycle lane:
   - Windows Startup folder launcher create/remove, or
   - Windows Task Scheduler task create/remove/update, or
   - future platform-specific launch-agent/cron/service operation
8. Post-mutation verification runs the declared proof commands and compares before/after host state.
9. Rollback is attempted or made available if verification fails.
10. Agent Activity and lifecycle mutation events record:
    - approval id
    - plan digest
    - consumed marker path
    - before/after host state
    - verification result
    - rollback result if any
    - target reached flag
    - runtime/surface/intent binding
11. Success-marker acceptance remains denied until audit evidence is complete and policy allows a marker write.

## Preconditions Before Host Mutation Executor Enablement

Minimum preconditions before any executor may mutate host startup/autostart state:

1. Exact operator approval artifact exists and is approved for the current plan digest.
2. Gate operation policy allows the named host API for the actor/surface.
3. `runtime/policy/gateway_allowlists.json` preserves operator approval and audit requirement for the host target.
4. `startup-surface-executor-preflight` passes immediately before mutation.
5. Approval consumption and exact-once marker semantics are create-new-only and replay-safe.
6. WSL/Windows boundary policy is finalized:
   - WSL must not silently write Windows Startup-folder/Task Scheduler state as an ambient side effect.
   - Windows-side execution requirements and path translation must be explicit.
7. Operator confirmation phrase binds runtime, surface, intent, Gate approval id, plan digest, and target host API.
8. Rollback policy is implemented and tested for each supported host target.
9. Post-mutation verification evidence is implemented and tested for each supported host target.
10. Agent Activity audit template is finalized and linked to `[[Hermes-Runtime-Profile]]`, `[[HERMES]]`, and `[[Agent-Activity-Index]]` for Hermes/Optimus runs.
11. Success-marker evidence verifier and acceptance policy remain fail-closed until verified evidence is complete.
12. Focused tests and live no-mutation smokes prove the UI/readiness path cannot accidentally mutate host state.
13. A separate operator-approved execution pass authorizes the first real host mutation smoke, including cleanup/rollback expectations.

## Explicit Non-Goals / Forbidden Shortcuts

The following are not approved implementation paths:

- Studio visual component writes Startup-folder files directly.
- Studio visual component creates/removes Task Scheduler entries directly.
- Runtime Cockpit or desktop shell mock consumes approval implicitly.
- Approval decision writing doubles as approval consumption.
- Idempotency marker is written before host verification and then treated as proof of success.
- WSL process mutates Windows host startup state without explicit host-boundary policy and operator confirmation.
- Startup/autostart state changes are treated as normal settings writes.
- Success-marker acceptance is self-certified by the runtime that performed the mutation.
- Gateway/Discord input becomes command authority for startup/autostart host mutation.

## Blocker Decision

Actual Studio-triggered startup/autostart host mutation should stay deferred until a lower-phase runtime/lifecycle implementation pass explicitly builds and validates the host executor under the path above.

The current Phase 10 Studio-safe output is this blocker report plus discoverability sync. It is testable now as a fail-closed readiness surface, but not as a real host-mutation executor.

## Next Implementation Handoff

The next executable child should be a lower-phase runtime/lifecycle task, not a Studio UI task:

- Add a failing test for an approval-gated host executor command that remains disabled by default.
- Implement only the smallest Windows Startup-folder executor adapter behind Gate/preflight/approval-consumption/idempotency/audit checks.
- Keep Task Scheduler mutation as a separate later adapter unless the approved task specifically includes it.
- Run no-mutation tests first, then a separate operator-approved live host mutation smoke only if explicit approval is granted.

Until that task exists and passes review, Studio should continue rendering readiness/request/preflight/audit/success-marker posture and should not offer a live host mutation execution claim.

## OS Alignment

This preserves the ChaseOS operating-system model: Studio is an operator surface over lifecycle/Gate contracts, not a separate authority layer. Runtime startup/autostart mutation belongs to Phase 9 runtime/lifecycle governance and must leave durable approval, preflight, consumption, host-boundary, verification, rollback, and audit evidence before ChaseOS treats it as real operating authority.

Graph links: [[ChaseOS-Studio-Architecture]] · [[ChaseOS-Runtime-Lifecycle-Contract]] · [[Runtime-Startup-Controls-Portable-Handoff]] · [[ChaseOS-Hardening-Passover]] · [[Phase9-Hardening-Passover]] · [[Hermes-Runtime-Profile]] · [[HERMES]] · [[Agent-Activity-Index]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
