---
title: Excalidraw Local Target Contract
type: browser-runtime-target-contract
status: COMPLETE TARGETED / NO EXECUTION
created: 2026-05-03
updated: 2026-05-03
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Excalidraw Local Target Contract

This document defines the machine-readable local target contract for the future Excalidraw browser/MCP proof.

It exists because the current Browser Runtime next gate needs an externally supplied loopback URL. ChaseOS should not install, start, or probe that target until the operator/runtime supplies it and a later pass explicitly approves the next step.

## Command

Write the request packet:

```powershell
python -m runtime.browser_runtime.excalidraw_target_contract --vault-root . --write-contract --json
```

Validate a provided local URL without probing it:

```powershell
python -m runtime.browser_runtime.excalidraw_target_contract --vault-root . --target-url http://127.0.0.1:<port>/ --write-contract --json
```

## Current Evidence

```text
07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json
```

Current status:

```text
excalidraw_local_target_contract_request_ready_no_execution
```

## Target Requirements

- Bind only to `127.0.0.1`, `localhost`, or `::1`.
- Require no account login, collaboration link, saved cookies, or browser profile.
- Expose a visible canvas or Excalidraw-compatible drawing surface.
- Allow a harmless rectangle plus label proof.
- Do not expose a public tunnel or remote browser.
- Return only a local target URL to ChaseOS before live-readiness rerun.

## Forbidden In This Contract Pass

- dependency install,
- server start,
- network probe,
- browser launch,
- CDP connection,
- MCP invocation,
- target navigation,
- real profile access,
- credential/cookie/session read,
- Browser Harness or Browser Use live run,
- trusted skill write,
- skill activation,
- Agent Bus enqueue,
- provider call,
- Gate mutation,
- canonical writeback.

## Next Step

External runtime/operator provides the target URL. Then ChaseOS reruns:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_live_readiness --vault-root . --local-target-url <loopback-url> --write-readiness --json
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
