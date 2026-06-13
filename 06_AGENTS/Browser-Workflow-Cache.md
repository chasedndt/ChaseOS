---
title: Browser Workflow Cache
type: architecture
status: partial / inactive cache foundation with reviewed local trial candidate
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Cache

Browser Workflow Cache is the ChaseOS-native store for reusable browser workflow
candidates derived from Browser Run evidence.

This is not a workflow executor. It is an inactive review cache that prepares
successful browser-run patterns for later operator review, SiteOps promotion,
and AOR-controlled execution.

## Current Status

Status: PARTIAL / INACTIVE CACHE FOUNDATION.

Implemented:

- `runtime/browser_runtime/workflows.py`
- `runtime/browser_runtime/test_browser_workflow_cache.py`
- `runtime/browser_workflows/metadata.json`
- `runtime/browser_workflows/workflows/`

The cache can model, validate, summarize, and write inactive workflow entries in
a bounded helper path. It now also contains one reviewed local trial candidate
for no-execution readiness validation. It does not replay workflows.

## External Reference

`browser-use/workflow-use` remains reference-only because it is AGPL-3.0. ChaseOS
adopts the concept of caching successful workflows, but no workflow-use code is
copied into ChaseOS.

Primary reference: `https://github.com/browser-use/workflow-use`

## Boundaries

- Entries are review-only.
- `activation_allowed=false`.
- global metadata keeps `replay_allowed=false`.
- individual entries may set `replay_allowed=true` only when they are
  `reviewed_for_trial`, local-only, inactive, and selected for read-only
  readiness validation.
- No real Chrome profile use.
- No saved credentials, cookies, sessions, or browser history.
- No Browser Harness live authority.
- No Browser Use live CLI authority.
- No Agent Bus enqueue.
- No provider calls.
- No Gate mutation.
- No canonical writeback.

## Replay Executor Design

The no-execution replay-executor design preflight now lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_design --vault-root . --json
```

It defines the future AOR/SiteOps executor contract, allowed preconditions, stop
conditions, and required artifacts. It does not run workflows.

The no-write implementation-request packet now lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_request --vault-root . --json
```

It returns `workflow_replay_executor_implementation_request_ready_no_write` in
the current repo and names a future patch scope without writing a request
artifact or enabling replay execution.

The no-write implementation-approval packet now lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_approval --vault-root . --decision approve --json
```

It returns `workflow_replay_executor_implementation_approval_ready_no_write` in
the current repo and can approve only a later bounded implementation patch. It
does not write an approval artifact, implement a replay executor, or authorize
workflow replay execution.

The disabled implementation now lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor --vault-root . --json
```

It returns `workflow_replay_executor_disabled_no_workflow_selected` in the
current repo when no workflow is selected. It validates and plans only; it does
not execute cached workflows, launch browsers, connect CDP, or write replay
artifacts.

## Reviewed Local Trial Candidate

The first selected workflow trial candidate is:

```text
runtime/browser_workflows/workflows/wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502.workflow.json
```

It is derived from:

```text
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json
```

The cache metadata still keeps top-level `activation_allowed=false`,
`replay_allowed=false`, `trusted_write_allowed=false`, and
`external_code_copied=false`. The entry's `replay_allowed=true` is only for
readiness validation by the disabled executor and does not authorize live
workflow replay.

## Future Work

The next step after trial-candidate selection is not live replay. It is a
separate execution approval and idempotency pass with Gate/AOR approval,
Browser Run and Agent Activity targets, and isolated browser-profile
requirements.

## Graph Links

[[Browser-Workflow-Replay-Trial-Candidate]] - [[Browser-Workflow-Replay-Execution-Readiness]] - [[Browser-Workflow-Replay-Executor]] - [[Browser-Runtime-Skill-Memory]] - [[Browser-Runtime-Feature-Readiness-Tracker]] - [[Browser-Runtime-Completion-Status]] - [[ChaseOS-SiteOps]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
