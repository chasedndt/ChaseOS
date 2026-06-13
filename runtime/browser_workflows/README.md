---
title: Browser Workflow Cache
type: runtime-registry
status: inactive review cache
created: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
---

# Browser Workflow Cache

This directory is the ChaseOS-native inactive cache for browser workflow
candidates derived from Browser Run evidence.

It is not `browser-use/workflow-use`, and no AGPL workflow-use code is copied
into ChaseOS. Workflow Use remains a reference-only external project pending
license review.

## Boundaries

- Entries are review-only.
- `activation_allowed` must remain `false`.
- Global cache metadata keeps `replay_allowed=false`.
- Individual entries may set `replay_allowed=true` only when they are
  `reviewed_for_trial`, local-only, inactive, and used by read-only readiness
  validation. This still does not authorize live replay execution.
- No real browser profile, credentials, cookies, session tokens, browser history,
  Browser Harness runtime authority, Browser Use live CLI authority, Agent Bus
  enqueue, provider call, Gate mutation, or canonical writeback is authorized by
  this cache.

## Layout

```text
runtime/browser_workflows/
  metadata.json
  workflows/
    *.workflow.json
```

The current store contains one reviewed local VincisOS trial candidate for
readiness validation only. Runtime helpers live in
`runtime/browser_runtime/workflows.py` and
`runtime/browser_runtime/workflow_replay_trial_candidate.py`.

## Replay Approval Boundary

Replay execution is still not globally enabled. The approval/idempotency
contract for the selected local trial candidate lives in
`runtime/browser_runtime/workflow_replay_execution_approval.py`.

That contract is no-write and no-execution. It computes the future approval
request and idempotency marker paths for one local replay proof, but it does not
write those artifacts or run the workflow. The next production blocker remains
the separate safe-local workflow replay execution proof.
