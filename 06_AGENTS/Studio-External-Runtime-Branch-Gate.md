---
title: Studio External Runtime Branch Gate
date: 2026-05-05
runtime: Codex
status: IMPLEMENTED / FAIL-CLOSED / BLOCKED CURRENT SETUP
phase: Phase 10 - ChaseOS Studio
---

# Studio External Runtime Branch Gate

## Summary

`chaseos studio external-runtime-branch-gate` is the required pre-start gate for
external Browser Runtime branches. It converts the broader Studio external
runtime readiness report into a branch-specific yes/no decision so future
runtime sessions cannot accidentally start Browser Use CLI validation or
Excalidraw live proof work from stale chat context.

## Command

```powershell
chaseos studio external-runtime-branch-gate --branch <branch> --json
```

Branches:

- `browser-use-cli-external-runtime-validation`
- `excalidraw-target-and-readiness`
- `excalidraw-live-browser-mcp-proof`

Optional evidence:

```powershell
chaseos studio external-runtime-branch-gate --branch excalidraw-target-and-readiness --write-evidence --json
```

Evidence is written only when `--write-evidence` is present, under
`07_LOGS/Studio-Graph-Views/` by default.

## Current Repo Result

As of this pass, all three branches are blocked:

- Browser Use CLI validation blocks because `browser-use` is not discoverable.
- Excalidraw target/readiness blocks because no accepted loopback target response exists.
- Excalidraw live browser/MCP proof blocks because target response, live readiness,
  approval readiness, and proof-shell readiness are not complete.

## Required Branch Flow

1. Run `chaseos studio external-runtime-readiness --json`.
2. Run this branch gate for the exact branch a runtime wants to start.
3. Start the external branch only if `can_start_branch=true`.
4. Treat exit code `1` as a hard stop, not a warning.

## Boundaries

The branch gate does not install dependencies, probe executables through
subprocess calls, start servers, probe URLs, launch browsers, run Browser Use
CLI, connect CDP, invoke MCP, call MCP tools, navigate targets, capture
screenshots, grant approvals, execute approvals, consume approval decisions,
reserve idempotency markers, read real profiles/credentials/cookies/history,
call providers/connectors, enqueue Agent Bus work, mutate Gate policy, or write
canonical ChaseOS state.

## Evidence

- Browser Use branch gate:
  `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-branch-gate-browser-use.md`
- Excalidraw target/readiness branch gate:
  `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-branch-gate-excalidraw-target.md`
- Excalidraw live proof branch gate:
  `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-branch-gate-excalidraw-proof.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
