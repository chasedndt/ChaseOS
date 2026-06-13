---
title: Browser Workflow Replay Execution Proof
type: architecture
status: complete targeted / live safe-local proof verified
created: 2026-05-03
updated: 2026-05-03
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Browser Workflow Replay Execution Proof

This note records the first ChaseOS-native bounded execution proof runner for
Browser Workflow replay.

The runner is not a general browser agent. It executes one reviewed local
workflow only after the workflow replay approval/idempotency contract is ready.
It writes a create-new approval record, reserves the exact-once idempotency
marker, and only then opens the browser controller.

## Machine Surface

```powershell
python -m runtime.browser_runtime.workflow_replay_execution_proof --vault-root . --workflow-id wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502 --target-url http://127.0.0.1:8770/ --allowed-domain 127.0.0.1 --execute-local-replay --run-slug safe-local-workflow-replay-execution-proof-20260503 --json
```

If the local browser controller is unavailable, the command blocks before
writing the approval record or marker. If a prior marker is safely failed, a
single retry can be run with `--retry-after-failed-marker`, which preserves the
failed marker and writes separate retry approval/marker artifacts.

## Proof Boundary

Allowed in the proof:

- selected workflow only;
- local-only domain only;
- throwaway-profile CDP controller only for live mode;
- injected controller in tests;
- bounded Browser Run, Agent Activity, screenshot, draft skill, and untrusted
  candidate artifacts;
- draft-only site skill memory.

Blocked in the proof:

- real Chrome profile or saved credentials;
- cookies, session tokens, browser history, public tunnels, or profile sync;
- free-form website automation;
- trusted skill write or skill activation;
- Agent Bus enqueue, provider calls, Gate mutation, or canonical writeback;
- Browser Harness or Workflow Use code adoption.

## Status

Status: COMPLETE TARGETED / LIVE SAFE-LOCAL PROOF VERIFIED.

Focused tests verify:

- no external Browser Use, Browser Harness, or Workflow Use code is imported;
- no-execution mode is read-only;
- the idempotency marker exists before the first browser `open`;
- duplicate markers block before browser action;
- unavailable controllers block before approval or marker writes;
- failures after marker reservation write failed evidence and keep the marker;
- non-local targets block without writes;
- failed-marker retry preserves the failed marker and writes a distinct retry
  marker when the failed run log is safe.

Live verification:

```text
07_LOGS/Browser-Runs/safe-local-workflow-replay-execution-proof-20260503_success.json
07_LOGS/Browser-Runs/safe-local-workflow-replay-execution-proof-20260503_screenshot.png
07_LOGS/Agent-Activity/2026-05-03-browser-workflow-replay-execution-proof.md
06_AGENTS/Browser-Skills/_drafts/draft-safe-local-workflow-replay-execution-proof-20260503.md
03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260503__candidate-safe-local-workflow-replay-execution-proof-20260503.md
```

The first sandbox-only attempt timed out waiting for the CDP endpoint and wrote
failed evidence:

```text
07_LOGS/Browser-Runs/safe-local-workflow-replay-execution-proof-20260503_failed.json
```

The successful retry used an isolated throwaway Chrome profile only and wrote:

```text
07_LOGS/Agent-Activity/_browser_workflow_replay_approvals/browser-workflow-replay-retry-60f399e21870.json
07_LOGS/Agent-Activity/_browser_workflow_replay_approvals/_execution_markers/browser-workflow-replay-retry-60f399e21870.json
```

No real browser profile, credentials, cookies, session data, Browser Harness
authority, Browser Use CLI execution, Workflow Use code, Agent Bus/provider
call, Gate mutation, skill activation, trusted write, or canonical writeback
was used.

## Next Gate

Move to `excalidraw-local-browser-mcp-proof-prep`. That pass should prepare a
local canvas/browser/MCP proof without real accounts, shared browser profiles,
credential/cookie access, trusted skill activation, Gate mutation, Agent Bus
enqueue, provider calls, or canonical writeback.

## Independence Rule

This surface is ChaseOS-native. It does not copy Browser Use, Browser Harness,
Browser Harness JS, Workflow Use, web-ui, or Excalidraw MCP code. Workflow Use
remains AGPL-3.0 reference-only.

## Graph Links

[[Browser-Workflow-Replay-Execution-Approval]] - [[Browser-Workflow-Replay-Execution-Readiness]] - [[Browser-Workflow-Replay-Trial-Candidate]] - [[Browser-Workflow-Cache]] - [[Browser-Runtime-Completion-Status]] - [[Browser-Runtime-Feature-Readiness-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
