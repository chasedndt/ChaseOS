---
title: Browser Workflow Replay Execution Approval
type: architecture
status: implemented no-write / no execution
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Replay Execution Approval

This note records the no-write approval and idempotency contract for a future
local Browser Workflow replay proof.

The contract is not an approval artifact and not an executor. It binds a
reviewed local workflow, target URL, allowed domain, approval-request preview,
and exact-once idempotency marker path. It does not write the approval request,
consume an approval, reserve the idempotency marker, launch a browser, connect
CDP, or replay workflow steps.

## Machine Surface

```powershell
python -m runtime.browser_runtime.workflow_replay_execution_approval --vault-root . --workflow-id wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502 --target-url http://127.0.0.1:8770/ --allowed-domain 127.0.0.1 --json
```

Current repo result:

```text
status: workflow_replay_execution_approval_ready_no_execution
workflow_id: wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502
target_url: http://127.0.0.1:8770/
approval_request_written: false
approval_decision_consumed: false
idempotency_marker_written: false
workflow_replay_attempted: false
browser_launch_attempted: false
next_step: safe-local-workflow-replay-execution-proof
```

## Approval Preview

The module computes a deterministic approval request id for the selected
workflow/target/domain/requester binding.

Current approval request id:

```text
browser-workflow-replay-appr-wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502-5034e6c4e271e47c
```

Future approval-request path, not written in this pass:

```text
07_LOGS/Agent-Activity/_browser_workflow_replay_approvals/browser-workflow-replay-appr-wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502-5034e6c4e271e47c.json
```

Future idempotency marker path, not written in this pass:

```text
07_LOGS/Agent-Activity/_browser_workflow_replay_approvals/_execution_markers/browser-workflow-replay-appr-wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502-5034e6c4e271e47c.json
```

If the marker already exists, the contract reports
`workflow_replay_execution_approval_blocked_idempotency_marker_exists` and the
future executor must abort before browser launch.

## Checks

The contract requires:

- replay execution readiness is `ready_no_execution`;
- disabled executor status is `workflow_replay_executor_ready_no_execution`;
- workflow entry is bound to the reviewed cache file;
- target URL matches the reviewed workflow `source_url`;
- target domain is local-only: `127.0.0.1`, `localhost`, or `::1`;
- target domain is in `allowed_domains`;
- idempotency marker is absent;
- approval request remains preview-only;
- no browser/runtime/write side effects occur.

## Boundary

The contract keeps these false:

- approval request written,
- approval decision written or consumed,
- idempotency marker written,
- execution allowed,
- workflow replay attempted,
- browser launch attempted,
- CDP connection attempted,
- real profile access attempted,
- credential or cookie read attempted,
- trusted skill write attempted,
- skill activation attempted,
- canonical writeback attempted,
- Agent Bus enqueue attempted,
- provider call attempted,
- Gate mutation attempted.

## Status

Status: IMPLEMENTED NO-WRITE / NO EXECUTION / LOCAL-ONLY CONTRACT READY.

Workflow replay execution remains deferred. The next pass is a separate
safe-local replay proof. That future pass must reserve the idempotency marker
before browser launch, use only a throwaway/local browser profile, write only
bounded Browser Run / Agent Activity / screenshot / draft-candidate artifacts,
and keep trusted skills, active skill promotion, Gate mutation, Agent Bus
enqueue, provider calls, real accounts, credentials, cookies, public tunnels,
and canonical writeback blocked.

## Independence Rule

This surface is ChaseOS-native. It does not copy Browser Use, Browser Harness,
Browser Harness JS, Workflow Use, web-ui, or Excalidraw MCP code. Workflow Use
remains AGPL-3.0 reference-only.

## Graph Links

[[Browser-Workflow-Replay-Execution-Readiness]] - [[Browser-Workflow-Replay-Trial-Candidate]] - [[Browser-Workflow-Replay-Executor]] - [[Browser-Workflow-Cache]] - [[Browser-Runtime-Completion-Status]] - [[Browser-Runtime-Test-Plan]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
