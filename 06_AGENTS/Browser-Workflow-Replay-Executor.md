---
title: Browser Workflow Replay Executor
type: architecture
status: implemented disabled-by-default / no execution
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Replay Executor

This document records the first ChaseOS-native Browser Workflow replay executor
implementation patch.

The executor is implemented as a disabled-by-default validation surface. It can
load a cached workflow entry, validate review/replay/domain/step posture, and
return a planned step list. It does not execute browser actions.

## Machine Surface

```powershell
python -m runtime.browser_runtime.workflow_replay_executor --vault-root . --json
```

Current repo result with no selected workflow:

```text
workflow_replay_executor_disabled_no_workflow_selected
```

## Boundary

The executor keeps these false:

- execution allowed,
- workflow replay attempted,
- replay artifacts written,
- browser launch attempted,
- CDP connection attempted,
- Browser Harness used,
- Browser Use live used,
- real profile access attempted,
- credential or cookie read attempted,
- Agent Bus enqueue attempted,
- provider call attempted,
- Gate mutation attempted,
- trusted skill write attempted,
- skill activation attempted,
- canonical writeback attempted.

## Validation Rules

The current executor blocks unless:

- a workflow id is selected,
- the cache foundation is present,
- the workflow entry exists,
- the entry is a valid `browser.workflow_cache.v1` record,
- the entry is reviewed for trial,
- the entry explicitly sets `replay_allowed=true`,
- the target domain is allowlisted,
- no forbidden step action appears,
- the executor is explicitly enabled for validation posture.

Even when those checks pass, a live run request returns
`blocked_live_workflow_replay_execution_deferred`. Live browser replay requires a
separate future approval and implementation pass.

## Follow-On Readiness Preflight

The next bounded surface is:

```powershell
python -m runtime.browser_runtime.workflow_replay_execution_readiness --vault-root . --json
```

It checks whether a reviewed replay workflow is available and selected for a
future approved execution pass. It does not execute replay, launch a browser,
connect CDP, write Browser Run logs, write Agent Activity logs, activate skills,
or mutate trusted/canonical state.

## Independence Rule

The executor is ChaseOS-native. It does not copy code from Browser Use, Browser
Harness, Browser Harness JS, Workflow Use, web-ui, or Excalidraw MCP. External
projects remain research/reference material only.

## Status

Status: IMPLEMENTED DISABLED-BY-DEFAULT / NO EXECUTION.

Workflow replay execution remains deferred.

## Graph Links

[[Browser-Workflow-Replay-Execution-Readiness]] - [[Browser-Workflow-Replay-Executor-Implementation-Approval]] - [[Browser-Workflow-Replay-Executor-Implementation-Request]] - [[Browser-Workflow-Replay-Executor-Design]] - [[Browser-Workflow-Cache]] - [[Browser-Runtime-Completion-Status]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
