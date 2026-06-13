---
type: runtime-profile
title: ChaserAgent Runtime Profile
runtime_id: chaser
runtime_label: Chaser Agent
status: PARTIAL / CORE FOUNDATION PREVIEW / NOT LIVE
created: 2026-06-05
updated: 2026-06-06
runtime: Codex
---

# ChaserAgent Runtime Profile

## Current Status

Chaser Agent is a planned ChaseOS internal agent lane with a partial Phase A
core foundation. This profile prepares the runtime identity for Studio companion
and future runtime surfaces, but it does not activate Chaser as a live runtime.

Current implementation evidence indicates:

- `runtime/chaser/models.py` exists for core data shapes.
- `runtime/chaser/sessions.py` exists for read-only session discovery.
- `runtime/chaser/exports.py` exists for export/deck preparation.
- `runtime/chaser/gateway_diagnostic.py` exists for read-only diagnostic output.
- `runtime/chaser/agent.py`, `board.py`, `policies.py`, `profiles.py`,
  `memory.py`, `toolsets.py`, and `artifacts.py` exist as Phase A no-authority
  preview/contract modules only.

## Runtime Identity

- Runtime: Chaser Agent
- Runtime ID: `chaser`
- Execution surface: planned internal agent / gateway diagnostic lane
- Access mode: preview-only / not active
- Authority: profile and contract preview only
- Companion status: planned, visible, not hatchable/selectable

## Allowed Surfaces Now

- Read-only profile display.
- Companion roster card marked coming soon.
- Companion Apps configuration card in Studio Settings, reporting Chaser Agent
  as planned, visible, not hatchable/selectable, and not live.
- Studio chat adapter card marked coming soon.
- Read-only diagnostic/session/export references backed by existing
  `runtime/chaser/` footholds.
- In-memory task previews, board cards, policy snapshots, profile/toolset views,
  memory-boundary previews, and artifact manifests.

## Forbidden Until Built And Verified

- Runtime activation.
- Chat runtime selection.
- Agent Bus task claiming.
- Provider/model calls.
- Tool execution.
- Memory writes.
- Canonical state mutation.
- Protected-file writes.
- Autonomous workflow execution.

## Next Build Gate

The next implementation pass should build or verify ChaserAgent core runtime
integration around these contracts before changing this profile to `AVAILABLE`.
At minimum, that pass should add governed persistence/API surfaces or CLI
preview wiring while preserving no-provider, no-tool-execution, no-Agent-Bus,
and no-memory-write defaults.

## Companion Apps Configuration Evidence

The 2026-06-06 Companion Apps configuration pass added
`runtime/studio/companion_apps_configuration.py` and
`StudioAPI.get_companion_apps_configuration()`. The surface inventories Chaser
Agent runtime/profile state as read-only configuration only:

- Display name: Chaser Agent.
- Runtime ID: `chaser`.
- Package path: `runtime/chaser`.
- Status: planned.
- Selection: blocked.
- Hatch: blocked.
- Live runtime: false.
- Provider calls, runtime dispatch, Agent Bus claims/writes, tool/shell
  execution, memory writes, and canonical mutation: blocked.
