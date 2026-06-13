# Browser Operator Surface Folder Guide

This folder is the Phase 10 browser lane for the ChaseOS Live Operator Shell.

Current status: SPEC-SEEDED / NO EXECUTION CODE.

Canonical scope document:

```text
06_AGENTS/Live-Operator-Shell-Browser-Surface.md
```

## Purpose

`runtime/operator_surface/browser/` is reserved for shell-facing browser panel models and no-action/dependency-routing contracts. It exists so future Studio/Operator Shell code has a clear home that is separate from lower-phase browser executors.

The folder may contain:

- pure read-only panel/data builders;
- no-action/degraded state models;
- dependency-routing packet builders;
- tests that prove display, blocker, and evidence states;
- adapters that compose existing Browser Runtime, OSRIL, and Studio readiness payloads without side effects.

The folder must not contain:

- browser launchers;
- CDP or MCP clients;
- Browser Use CLI invocations;
- approval-consumption logic;
- idempotency marker reservation;
- Agent Bus writers;
- provider/connector calls;
- credential/profile/cookie readers;
- canonical writeback logic.

## Boundary

This is a Phase 10 operator-surface lane. Lower-phase execution remains in Browser Runtime, SiteOps, AOR, OSRIL, Agent Bus, Gate, and provider/credential adapters as applicable.

If a future shell action needs authority, this folder should return a structured dependency record naming the missing lower-phase contract instead of performing the action.

## First implementation target

Add a read-only browser shell panel model that composes:

- `runtime.studio.browser_runtime_operator_ui_readiness.build_studio_browser_runtime_operator_ui_readiness(...)`
- `runtime.studio.chat_browser_runtime_dispatch_lane.build_chat_studio_browser_runtime_dispatch_lane_manifest(...)`
- visible-control UX metadata from `06_AGENTS/Agent-Control-UX-Contract.md`
- dependency-routing records defined in `06_AGENTS/Live-Operator-Shell-Browser-Surface.md`

The first implementation should expose display-ready and blocked/no-action states only.

*Graph links: [[OpenClaw-Runtime-Profile]]*
