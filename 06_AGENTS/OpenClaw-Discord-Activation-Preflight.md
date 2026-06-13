---
title: OpenClaw Discord Activation Preflight
type: operational-preflight
status: active-preflight
created: 2026-04-20
phase: 9
owner: ChaseOS
---

# OpenClaw Discord Activation Preflight

This document is the machine-local preflight for activating Discord through the OpenClaw-first lane without turning Discord into broad multi-harness control.

This is a documentation and operations pass only. It does not implement a Discord bot, alter runtime code, alter adapter policy, add MCP, add Home Assistant, enable Hermes Discord, or broaden Hermes authority.

## Current Machine Truth

- OpenClaw is the active bounded runtime adapter lane on this machine.
- OpenClaw Discord transport/control surface is operational.
- Existing OpenClaw execution is bounded through the OpenClaw -> `chaseos run` -> AOR path.
- `operator_today` and `operator_close_day` are live bounded AOR workflows.
- `graph_hygiene` is available as a proposal-only AOR workflow.
- ChaseOS remains the constitutional control plane and source of canonical truth.
- `06_AGENTS/ChaseOS-Discord-Control-Plane.md` is the canonical Discord control-plane spec.
- Hermes is bounded shadow active only. Hermes is not Discord-enabled.
- MCP is a separate lane and is not part of this preflight.

## Extracted Blockers Before Multi-Harness Discord Execution

The canonical Discord control-plane spec blocks true multi-harness Discord execution until all of the following exist:

1. A Discord identity map for operator and runtime bot accounts.
2. A channel registry mapping real Discord channels to canonical channel classes.
3. A signed or authenticated command envelope.
4. A request classifier that treats all Discord-origin input as untrusted until explicitly scoped.
5. An approval ledger that writes approval records to `07_LOGS/Agent-Activity/` or a future formal audit path.
6. Adapter allowlists defining which workflows may be triggered from Discord.
7. Deny-by-default handling for unknown commands, unknown users, unknown channels, and ambiguous actions.
8. Red-team tests for prompt injection, impersonation, replay, malformed approvals, and channel confusion.
9. Dry-run mode for every Discord-triggered execution route.
10. Rollback and failure behavior documentation for every route.

Until these blockers are closed, Discord may be treated as an OpenClaw-facing operator transport, not as a general multi-harness runtime authority.

## What Is Already Live

The live lane that this preflight may rely on is:

| Surface | Status | Notes |
|---|---:|---|
| OpenClaw local runtime lane | Live | Active bounded adapter lane on this machine. |
| OpenClaw Discord transport | Live | Operational control/transport surface. |
| `operator_today` via AOR | Live | Bounded workflow through `chaseos run operator_today`. |
| `operator_close_day` via AOR | Live | Bounded workflow through `chaseos run operator_close_day`. |
| `graph_hygiene` via AOR | Live, proposal-only | May produce hygiene reports; no canonical mutation. |
| Native schedule intent | Built | ChaseOS owns intent; OpenClaw may execute bounded schedule routes. |
| AOR audit writeback | Live | Writes to existing audit/log surfaces. |
| Discord control-plane spec | Live spec | Architecture only; implementation hardening still blocked. |

## Preflight Channel Classes

Discord channels must be mapped to the canonical channel classes before multi-harness execution. For this OpenClaw-first preflight, treat all real Discord channels as untrusted until mapped.

| Channel class | Preflight use |
|---|---|
| `control-plane-routing` | Triage operator intent and decide whether it remains advisory, needs approval, or is forbidden. |
| `runtime-chat` | OpenClaw bounded status and low-risk runtime conversation only. |
| `approvals` | Explicit approval records only after identity and command envelope hardening exist. |
| `audit-writeback` | Pointers to vault artifacts, run IDs, and summaries; Discord is never the canonical audit store. |
| `alerts` | Run success/failure signals and bounded schedule alerts. |
| `debug` | Sanitized diagnostics and dry-run output; no production execution from debug channels. |
| `docs-archive` | Links to build logs, archive notes, and governance docs. |

## OpenClaw Routing Model

OpenClaw may be the first Discord-facing lane only for existing bounded ChaseOS routes.

Allowed or eligible OpenClaw routes:

| Discord-origin request | Route | Approval |
|---|---|---|
| "Show today's operator status" | OpenClaw -> AOR/read-only status summary | Advisory only if no state change occurs. |
| "Run `operator_today`" | OpenClaw -> `chaseos run operator_today` | Approval required for ad hoc execution unless already covered by a configured schedule. |
| "Run `operator_close_day`" | OpenClaw -> `chaseos run operator_close_day` | Approval required for ad hoc execution unless already covered by a configured schedule. |
| "Show schedule state" | OpenClaw -> ChaseOS schedule status | Advisory only if read-only. |
| "Run graph hygiene" | OpenClaw -> `graph_hygiene` proposal route | Approval required; output remains proposal-only. |
| "List intake / dedup status" | OpenClaw -> existing read-only intake commands | Advisory only if read-only. |

Forbidden OpenClaw routes from Discord:

- direct writes to `00_HOME/Now.md`, `01_PROJECTS/`, `02_KNOWLEDGE/`, `06_AGENTS/`, protected files, credentials, secrets, or adapter policy files
- direct shell execution outside declared OpenClaw runtime controls
- new workflow creation
- canonical promotion
- deletion, rename, or move operations
- external connector use not already declared by an approved AOR workflow
- multi-repo or extra-directory access
- Discord-triggered Hermes execution
- MCP implementation or MCP-triggered runtime changes
- Home Assistant execution

## What Must Be Implemented Before True Multi-Harness Control

OpenClaw can remain the live Discord-backed lane, but Discord becomes true multi-harness control only after the blocked control-plane components are implemented and tested:

1. Identity map for human operator accounts and runtime bot accounts.
2. Real channel registry with channel IDs mapped to canonical channel classes.
3. Authenticated command envelope with request ID, actor, source channel, target adapter, workflow, scope, and timestamp.
4. Request classifier that treats Discord text, attachments, embeds, reactions, and forwarded content as Tier 4 until narrowed.
5. Approval ledger with durable vault writeback and per-action approval scope.
6. Adapter allowlists separating OpenClaw, Hermes, MCP, and future harnesses.
7. Deny-by-default enforcement for unknown or ambiguous requests.
8. Dry-run mode for every executable route.
9. Red-team suite for transport confusion and prompt-injection cases.
10. Rollback and failure procedure for each Discord-triggered route.

## Exact Implementation Order

Use this order when moving from preflight to implementation:

1. Freeze this OpenClaw-first preflight as the local operational baseline.
2. Create the Discord identity map for operator accounts and bot/runtime accounts.
3. Create the channel registry and map real Discord channel IDs to canonical classes.
4. Define the command envelope schema and required request fields.
5. Add the Discord-origin request classifier.
6. Add the approval ledger and write approval records to the vault audit path.
7. Add adapter allowlists, initially allowing only existing OpenClaw bounded AOR routes.
8. Add dry-run support for `operator_today`, `operator_close_day`, schedule status, and `graph_hygiene`.
9. Add deny-by-default enforcement for unknown actors, channels, commands, workflows, and adapters.
10. Add red-team tests for prompt injection, impersonation, replay, malformed approvals, and channel confusion.
11. Document rollback/failure behavior for every route.
12. Enable limited OpenClaw execution from Discord after evidence, dry-run, audit, and rollback paths are proven.
13. Re-evaluate other harnesses only after the OpenClaw route is hardened. Hermes remains blocked unless a separate Hermes gateway pass is approved.

## Approval Model

Discord-sourced actions use four classes:

| Class | Meaning | OpenClaw preflight handling |
|---|---|---|
| Advisory only | Read-only, no state change, no execution | Allowed only for status, docs links, and bounded summaries. |
| Approval required | One run or write path needs explicit approval | Required for ad hoc AOR runs and proposal-producing workflows. |
| Allowed execution | Preapproved route under schedule or manifest | Allowed only after identity, channel, envelope, and audit controls exist. |
| Forbidden | Must not execute from Discord | Deny; log if meaningful; route to architecture review only if future spec work is requested. |

Approvals must be explicit records. Emoji reactions, casual acknowledgements, or messages from unmapped channels are not approvals.

## What Is Still Forbidden

The following remain forbidden during and after this OpenClaw-first preflight unless a later explicit spec and implementation pass changes them:

- Hermes Discord execution
- Hermes Discord read/post/gateway access
- Hermes shell execution
- Hermes connector expansion
- Hermes canonical promotion
- Hermes persistent memory expansion
- MCP implementation in this pass
- Home Assistant implementation
- new Discord bot implementation in this pass
- new AOR workflow creation in this pass
- protected-file edits from Discord
- direct `02_KNOWLEDGE/` promotion
- credential or secret disclosure
- external webhook, tunnel, or gateway expansion
- multi-repo execution

## Preflight Success Criteria

This preflight is complete when:

- The exact multi-harness blockers are documented.
- The OpenClaw-eligible routes are limited to current bounded AOR routes.
- Hermes remains explicitly non-Discord-enabled.
- No runtime code, adapter policy, workflow manifest, MCP code, Home Assistant code, or Hermes gateway code is changed.
- A build log, archive note, and index updates record the documentation pass.

## Related Docs

- `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
- `OPENCLAW.md`
- `HERMES.md`
- `06_AGENTS/Autonomous-Operator-Runtime.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Hermes-Adapter-Spec.md`
- `06_AGENTS/Hermes-Workflow-Boundaries.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`


*Graph links: [[Vault-Map]] · [[OpenClaw-Runtime-Profile]]*
