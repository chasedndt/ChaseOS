---
title: Browser Workflow Replay Trial Candidate
type: architecture
status: implemented targeted / reviewed local candidate selected / no execution
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Replay Trial Candidate

This note records the first reviewed local workflow trial candidate for the
ChaseOS Browser Runtime Adapter + Site Skill Memory feature family.

It is a cache/readiness artifact only. It is not an active Site Skill, not a
trusted SiteOps skill card, and not a live replay authorization.

## Machine Surface

Preview without writing:

```powershell
python -m runtime.browser_runtime.workflow_replay_trial_candidate --vault-root . --json
```

Write or reselect the reviewed local trial candidate:

```powershell
python -m runtime.browser_runtime.workflow_replay_trial_candidate --vault-root . --write-trial-candidate --json
```

Implementation:

```text
runtime/browser_runtime/workflow_replay_trial_candidate.py
runtime/browser_runtime/test_workflow_replay_trial_candidate.py
```

## Selected Candidate

Workflow id:

```text
wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502
```

Workflow entry:

```text
runtime/browser_workflows/workflows/wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502.workflow.json
```

Source evidence:

```text
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png
07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-product-ui-browser-proof.md
06_AGENTS/Browser-Skills/_drafts/draft-vincisos-product-ui-browser-proof-20260502.md
03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260502__candidate-vincisos-product-ui-browser-proof-20260502.md
```

The source run was the local Studio Product UI Test Target at
`http://127.0.0.1:8770/`, using the Codex in-app browser backend. It verified
safe-mode product UI selectors, opened local tabs/panels, clicked the harmless
safe-mode inspection button, and captured screenshot evidence.

## Boundaries

This pass kept these false:

- execution allowed,
- workflow replay attempted,
- browser launch attempted,
- CDP connection attempted,
- Browser Harness used,
- Browser Use CLI live used,
- real profile access attempted,
- credential or cookie read attempted,
- Agent Bus enqueue attempted,
- provider call attempted,
- Gate mutation attempted,
- trusted skill write attempted,
- skill activation attempted,
- canonical writeback attempted,
- external code copied.

The global workflow cache metadata still keeps:

```text
activation_allowed: false
replay_allowed: false
trusted_write_allowed: false
external_code_copied: false
```

Only the selected workflow entry has `replay_allowed=true`, and only for
readiness validation. It remains `reviewed_for_trial` and inactive.

## Readiness Result

After selection, the read-only readiness command:

```powershell
python -m runtime.browser_runtime.workflow_replay_execution_readiness --vault-root . --workflow-id wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502 --target-url http://127.0.0.1:8770/ --allowed-domain 127.0.0.1 --json
```

returns:

```text
workflow_replay_execution_readiness_ready_no_execution
```

That means ChaseOS now has a selected reviewed local workflow candidate for the
next approval/idempotency design pass. It still does not mean replay execution
is authorized or implemented.

## Independence Rule

This is ChaseOS-native code and ChaseOS-native metadata. Browser Use,
Browser Harness, Browser Harness JS, Workflow Use, web-ui, and Excalidraw MCP
remain reference sources only. Workflow Use is AGPL-3.0 reference-only, and no
workflow-use code was copied into ChaseOS.

## Status

Status: COMPLETE TARGETED / NO EXECUTION.

Next recommended pass:

```text
workflow-replay-execution-approval-and-idempotency
```

## Graph Links

[[Browser-Workflow-Replay-Execution-Readiness]] - [[Browser-Workflow-Replay-Executor]] - [[Browser-Workflow-Cache]] - [[Browser-Runtime-Completion-Status]] - [[Browser-Runtime-Feature-Readiness-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
