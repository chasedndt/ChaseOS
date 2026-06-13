---
title: Browser Workflow Replay Execution Readiness
type: architecture
status: implemented read-only / no execution
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Replay Execution Readiness

This note records the read-only readiness preflight for future Browser Workflow
replay execution.

The preflight is not a replay executor. It inspects the native ChaseOS workflow
cache and the disabled replay executor, then reports whether ChaseOS has a
selected reviewed workflow, target/domain posture, and approval boundary for a
future live replay pass.

## Machine Surface

```powershell
python -m runtime.browser_runtime.workflow_replay_execution_readiness --vault-root . --json
```

Current repo result with the reviewed local VincisOS trial candidate selected:

```text
workflow_replay_execution_readiness_ready_no_execution
workflow_id: wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502
execution_allowed: false
workflow_replay_attempted: false
browser_launch_attempted: false
```

## Boundary

The readiness preflight keeps these false:

- execution allowed,
- workflow replay attempted,
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
- canonical writeback attempted,
- workflow cache entry write,
- Browser Run log write,
- Agent Activity log write.

## Readiness Checks

The preflight checks:

- workflow cache foundation status,
- whether reviewed replay-allowed workflow entries exist,
- whether a workflow id is selected,
- whether the disabled executor reaches `ready_no_execution`,
- whether a live replay request was kept out of this pass,
- whether a separate execution approval remains required,
- whether the pass produced no browser/runtime/writeback side effects.

## Current Follow-On

The current ChaseOS repo has the cache foundation, disabled executor, and one
reviewed local workflow selected for trial. That is readiness only, not live
replay approval.

The follow-on approval/idempotency contract is now implemented as no-write /
no-execution:

```text
workflow_replay_execution_approval_ready_no_execution
```

It defines the approval preview and exact-once marker path for a later local
replay proof. It still does not run the workflow, launch a browser, activate
skills, write trusted memory, consume an approval, or reserve the marker.

## Independence Rule

This preflight is ChaseOS-native. It does not copy code from Browser Use,
Browser Harness, Browser Harness JS, Workflow Use, web-ui, or Excalidraw MCP.
Workflow Use remains AGPL-3.0 reference-only.

## Status

Status: IMPLEMENTED READ-ONLY / NO EXECUTION / REVIEWED LOCAL WORKFLOW SELECTED.

Workflow replay execution remains deferred.

## Graph Links

[[Browser-Workflow-Replay-Trial-Candidate]] - [[Browser-Workflow-Replay-Executor]] - [[Browser-Workflow-Cache]] - [[Browser-Runtime-Completion-Status]] - [[Browser-Runtime-Test-Plan]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
