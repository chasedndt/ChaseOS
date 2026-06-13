---
title: Excalidraw Local Target Response Intake
type: browser-runtime-target-response
status: COMPLETE TARGETED / PENDING EXTERNAL RUNTIME / NO EXECUTION
created: 2026-05-03
updated: 2026-05-03
phase: Phase 9 Browser Runtime Adapter / Site Skill Memory
runtime: Codex
---

# Excalidraw Local Target Response Intake

This document defines the ChaseOS intake surface for the external runtime/operator response to the Excalidraw local target contract.

The response intake exists so ChaseOS can receive a loopback target URL as an untrusted pending input before rerunning live-readiness. It does not install dependencies, start servers, probe URLs, launch a browser, connect to CDP, invoke MCP, navigate, write trusted skills, activate skills, mutate Gate, enqueue Agent Bus work, call providers, or write canonical state.

## Command

Write the pending response packet:

```powershell
python -m runtime.browser_runtime.excalidraw_target_response --vault-root . --write-response --json
```

Validate a direct loopback URL without probing it:

```powershell
python -m runtime.browser_runtime.excalidraw_target_response --vault-root . --target-url http://127.0.0.1:<port>/ --json
```

Validate a JSON response file without probing it:

```powershell
python -m runtime.browser_runtime.excalidraw_target_response --vault-root . --response-file <path-to-response.json> --json
```

Accepted response shape:

```json
{
  "target_url": "http://127.0.0.1:<port>/"
}
```

## Current Evidence

```text
03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json
```

Current status:

```text
excalidraw_local_target_response_pending_external_runtime
```

## Accepted Target Rules

- Target URL must be `http` or `https`.
- Host must be `127.0.0.1`, `localhost`, or `::1`.
- Target must require no login, cookies, saved browser profile, collaboration link, or real account.
- Target must support the future harmless rectangle plus `ChaseOS` label proof.
- No public tunnel, cloud browser, profile sync, or remote account surface is accepted.

## Next Step

When the external runtime/operator supplies a valid loopback URL, rerun the live-readiness gate:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_live_readiness --vault-root . --local-target-url <loopback-url> --write-readiness --json
```

This response-intake pass does not authorize the live proof. A later execution-approval pass must still approve any browser/CDP/MCP action.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
