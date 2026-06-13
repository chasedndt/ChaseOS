---
title: Browser Workflow Replay Executor Design
type: architecture
status: design preflight / no execution
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Replay Executor Design

This document records the ChaseOS-native design preflight for a future Browser
Workflow replay executor.

This document began as a no-execution contract packet that defined what must be
true before a cached browser workflow can ever run. The follow-on implementation
now exists as a disabled validation/planning executor only.

## Design Rule

ChaseOS may study external workflow systems, but it must not copy their code.
The replay executor must be ChaseOS-native:

- AOR-owned,
- Gate-checked,
- SiteOps-aware,
- audit-first,
- approval-gated,
- local-first,
- profile-isolated,
- independent from `browser-use/workflow-use`.

`browser-use/workflow-use` remains AGPL-3.0 reference-only unless a separate
license review says otherwise.

## Current Machine Surface

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_design --vault-root . --json
```

Expected current status:

```text
status: ready_for_operator_review_no_execution
```

The command reads the inactive Browser Workflow Cache status and returns a
future executor contract. It does not write artifacts, replay workflows, launch
browsers, connect CDP, use Browser Harness, run Browser Use live, enqueue Agent
Bus tasks, call providers, mutate Gate, activate skills, write trusted artifacts,
or write canonical ChaseOS state.

## Implementation Request

The follow-on no-write implementation request lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_request --vault-root . --json
```

It composes this design preflight with the inactive cache foundation and returns
the future implementation patch scope for operator review. It does not implement
the executor, write a request artifact, run workflow replay, launch browsers,
connect CDP, use Browser Harness, run Browser Use live, copy external code, or
write trusted/canonical artifacts.

## Implementation Approval

The follow-on no-write implementation approval lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_approval --vault-root . --decision approve --json
```

It checks the request posture and returns an approve/reject packet for a later
bounded implementation patch. It does not write approval artifacts, implement an
executor, or authorize replay execution.

## Disabled Implementation

The follow-on disabled implementation lives at:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor --vault-root . --json
```

It loads a selected cache entry, validates replay posture, and returns a planned
step list. It does not run browser actions. With no selected workflow, current
repo status is `workflow_replay_executor_disabled_no_workflow_selected`.

## Future Preconditions

- Selected workflow entry validates as inactive review entry.
- Operator selects the entry for a trial.
- AOR manifest declares allowed domains, actions, artifacts, and stop policy.
- Gate allows only declared Browser Run and Agent Activity outputs.
- Any live trial uses a throwaway or isolated browser profile.
- Idempotency key and failure policy are declared before action.
- Browser Run Log and Agent Activity targets are declared.

## Stop Conditions

- Workflow entry is not reviewed or selected.
- Domain is not allowlisted.
- Step requires credentials, cookies, real profile state, payment, or account mutation.
- Selector or expected state mismatches.
- Target redirects to a forbidden domain.
- Artifact target falls outside declared log paths.
- Gate denies the operation or target.
- Idempotency marker collides.

## Status

Status: DESIGN PREFLIGHT COMPLETE / DISABLED IMPLEMENTATION EXISTS / NO
EXECUTION.

The follow-on implementation-request and implementation-approval surfaces are
now present, and the disabled implementation is present. Actual workflow replay
execution remains deferred.

## Graph Links

[[Browser-Workflow-Replay-Executor]] - [[Browser-Workflow-Replay-Executor-Implementation-Request]] - [[Browser-Workflow-Replay-Executor-Implementation-Approval]] - [[Browser-Workflow-Cache]] - [[Browser-Runtime-Completion-Status]] - [[Browser-Runtime-Feature-Readiness-Tracker]] - [[ChaseOS-SiteOps]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
