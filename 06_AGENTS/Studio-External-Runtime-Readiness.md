---
title: Studio External Runtime Readiness
type: runtime-readiness
status: implemented / blocked current setup / no execution
created: 2026-05-05
updated: 2026-05-05
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio
runtime: Codex
---

# Studio External Runtime Readiness

This note records the unified readiness gate for external Browser Runtime branches after the internal Studio Browser Runtime lane was closed.

## Command

```powershell
chaseos studio external-runtime-readiness --json
```

Implementation:

```text
runtime/studio/external_runtime_readiness.py
runtime/studio/test_external_runtime_readiness.py
```

## Current Result

As of 2026-05-05, the gate reports:

```text
status: blocked_external_runtime_setup_missing
browser_use_branch_ready: false
excalidraw_branch_ready: false
next_recommended_pass: external-runtime-provide-browser-use-cli-or-excalidraw-loopback-target
```

Current blockers:

- `browser_use:browser_use_cli_executable_not_found`
- `excalidraw_target_response:excalidraw_target_response_resolution_pending_external_runtime`
- `excalidraw_live_chain:target_response_not_accepted:excalidraw_target_response_resolution_pending_external_runtime`

Evidence:

```text
07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-readiness.md
07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-readiness.json
```

The corresponding setup handoff is:

```powershell
chaseos studio external-runtime-setup-request --json
```

Latest setup request evidence:

```text
07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-setup-request.md
07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-setup-request.json
```

## Meaning

Do not start `browser-use-cli-external-runtime-validation` until `browser_use_branch_ready=true`.

Do not start `excalidraw-target-and-readiness` or `excalidraw-live-browser-mcp-proof` until `excalidraw_branch_ready=true` and the relevant approval/readiness evidence exists.

## Boundary

The readiness gate is read-only. It does not install dependencies, invoke `browser-use`, probe targets, start servers, launch browsers, connect CDP, invoke MCP, navigate targets, capture screenshots, grant or execute approvals, consume decisions, reserve markers, read real profiles, read credentials/cookies, write skills, activate skills, enqueue Agent Bus tasks, call providers/connectors, mutate Gate, or write canonical ChaseOS state.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
