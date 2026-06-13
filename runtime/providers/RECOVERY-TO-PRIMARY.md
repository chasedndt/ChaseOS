---
type: runtime-design
status: DOCS-ONLY / PHASE-9 DESIGN COMPLETE / PHASE-10 IMPLEMENTATION DEFERRED
date: 2026-04-29
owner: ChaseOS runtime control plane
---

# Governed Recovery-to-Primary Design

This document defines the ChaseOS governance contract for recovering from a fallback provider/model back to the primary provider/model.

It is a Phase 9 runtime/control-plane design pass. It does not add a live recovery command, does not switch providers, and does not mutate runtime model configuration. The Phase 10 implementation can build from this contract without moving recovery logic into Hermes, OpenClaw, or any single adapter.

## Scope

Governed recovery-to-primary covers:

- identifying when a runtime is on fallback after primary degradation
- reading provider-state evidence for rate-limit, cooldown, fallback, and recovery events
- deciding whether primary recovery is eligible, blocked, or already complete
- planning future operator-visible recovery actions
- preserving auditability when a future apply path changes runtime state

It does not cover:

- connector retry behavior
- SBP delivery retry behavior
- Hermes-only behavior
- OpenClaw-only behavior
- silent provider switching
- cooldown clearing by hand
- credential or secret handling

## Phase Boundary

Phase 9 responsibility:

- define the evidence model
- keep recovery-to-primary visible through read-only provider-status output
- define the state machine and blocked reasons
- define Gate operation names for future mutation
- preserve the boundary between provider governance and adjacent adapter health

Phase 10 responsibility:

- implement a live recovery planner/apply command if still needed
- expose the plan/apply result through Settings or Studio
- enforce any provider/model configuration mutation through Gate
- write explicit recovery audit events after operator approval

Current status: DOCS-ONLY. `chaseos runtime provider-status` remains read-only.

## Evidence Lane

The only provider fallback-governance evidence lane is:

```text
runtime/providers/state/provider_state_events.jsonl
```

Relevant event types:

- `provider.request`
- `provider.rate_limited`
- `provider.cooldown_started`
- `provider.cooldown_ended`
- `provider.fallback_activated`
- `provider.recovery_primary_eligible`
- `provider.recovery_primary_completed`

Adjacent ledgers remain separate:

- acquisition connector health: `runtime/acquisition/state/connector_health_events.jsonl`
- SBP delivery health: `runtime/sbp/state/delivery_health_events.jsonl`

Connector-health and delivery-health evidence may appear beside provider posture in `adapter_health_rollup`, but it must not trigger fallback activation, recovery eligibility, cooldown clearing, or recovery-to-primary apply behavior.

## Recovery State Machine

The read side may summarize recovery using these states:

| State | Meaning |
| --- | --- |
| `no_events` | No provider-state evidence exists for the runtime. |
| `fallback_active` | A fallback activation is the latest relevant recovery state and no primary recovery completion has superseded it. |
| `primary_recovery_eligible` | Provider-state evidence says primary recovery may be attempted, but no recovery completion event has superseded it. |
| `primary_recovered` | A primary recovery completion event supersedes active fallback evidence. |
| `blocked` | Recovery cannot be attempted because rate-limit/cooldown/config evidence blocks it. |

`blocked` is a planned control-plane planning state. The existing `provider-status` reader may expose blocked reasons through readiness/operator attention items before a dedicated plan command exists.

## Eligibility Rules

A future recovery plan may mark primary recovery eligible only when all required evidence is true:

- fallback is active for the runtime/provider route
- primary provider is configured and valid
- primary model binding is readable
- no active rate-limit event blocks primary use
- no active cooldown event blocks primary use, or a later `provider.cooldown_ended` event exists
- a primary probe/request succeeds, or an explicit operator approval accepts a manual recovery attempt

Eligibility must be derived from provider-state evidence and model/provider configuration. It must not be derived from connector-health or delivery-health success.

## Future Command Shape

No recovery command exists in this pass. If Phase 10 implements it, use a separate command family rather than expanding read-only `provider-status`:

```powershell
chaseos runtime provider-recovery plan --runtime RUNTIME --json
chaseos runtime provider-recovery apply --runtime RUNTIME --approval-id APPROVAL_ID --json
```

Planned command contract:

- `plan` is read-only and returns planned actions, blocked reasons, evidence, and required approval.
- `apply` is mutating and requires explicit approval.
- `provider-status` remains an inspection surface and never performs recovery.
- both JSON and human-readable output must report whether connector/delivery health was excluded from fallback governance.

## Gate Operations

Future mutation must be guarded by named deny-by-default Gate operations:

- `runtime.provider_recovery.plan` for optional policy-visible planning checks
- `runtime.provider_recovery.apply` before any provider/model route mutation

If a future implementation writes only an eligibility event without switching provider/model state, it should still use an explicit operation such as:

- `runtime.provider_recovery.mark_eligible`

The exact operation names must be added to runtime policy and command-contract docs in the same implementation pass that adds code.

## Apply Requirements

A future `apply` path must:

- require an approval id or equivalent explicit operator approval
- be idempotent when the runtime is already recovered
- append provider-state evidence before or alongside any state mutation
- write an audit record with runtime, provider, model route, source evidence, blocked reasons, and approval reference
- avoid reading or writing secrets
- avoid direct adapter-specific behavior unless routed through the runtime control plane
- fail closed when model configuration or provider registry state is unreadable

## Prohibited Behavior

Recovery-to-primary must not:

- automatically recover because a connector or delivery adapter became healthy
- clear rate-limit or cooldown state without evidence
- mutate provider/model route from `provider-status`
- bypass Gate for a control-plane mutation
- use Hermes/OpenClaw adapter health as provider fallback-governance evidence
- perform live network probes without an explicit command, bounded timeout, and reported result
- claim recovery is verified without provider-state evidence or focused tests

## Phase 10 Implementation Checklist

Before implementing live recovery:

- add a planner module under the runtime provider/control-plane layer
- add focused tests for each recovery state and blocked reason
- add Gate policy rows for the selected operation names
- add command-contract entries only when commands are implemented
- update generated CLI docs in the same pass
- add live smoke coverage that proves `provider-status` remains read-only
- add audit/writeback documentation for any state mutation
- keep connector-health and delivery-health tests proving they do not drive provider recovery

## Current Status

This pass completes the governed recovery-to-primary design boundary for Phase 9. Live recovery planning/apply behavior is deferred to Phase 10.
