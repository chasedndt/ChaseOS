---
title: Excalidraw Target Response CLI
type: browser-runtime-readiness
status: implemented / no-probe intake
created: 2026-05-05
updated: 2026-05-05
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio
runtime: Codex
---

# Excalidraw Target Response CLI

This note records the `chaseos` CLI surface for accepting an operator-provided local Excalidraw/MCP/canvas target URL into the existing no-probe target response intake.

## Command

```powershell
chaseos operate browser excalidraw-target-response --from-env --json
```

The command reads `CHASEOS_EXCALIDRAW_TARGET_URL` only when `--from-env` is passed. An explicit argument takes precedence:

```powershell
chaseos operate browser excalidraw-target-response --target-url http://127.0.0.1:<port>/ --json
```

To persist an accepted or pending response artifact:

```powershell
chaseos operate browser excalidraw-target-response --from-env --write-response --json
```

## Current Result

As of 2026-05-05, a no-env run reports pending external runtime setup and writes nothing:

```text
status: excalidraw_local_target_response_pending_external_runtime
target_url_source: CHASEOS_EXCALIDRAW_TARGET_URL
response_artifact_written: false
```

A temporary loopback-env smoke accepted the URL shape without writing:

```text
CHASEOS_EXCALIDRAW_TARGET_URL=http://127.0.0.1:3030/
status: excalidraw_local_target_response_accepted_no_probe
target_host: 127.0.0.1
response_artifact_written: false
```

## Boundary

This command does not install dependencies, start servers, probe networks, launch browsers, connect CDP, invoke MCP, navigate targets, read real profiles, read credentials/cookies, open public tunnels, write or activate trusted skills, enqueue Agent Bus tasks, call providers, mutate Gate, or write canonical ChaseOS state.

The only optional write is the untrusted setup response artifact under:

```text
03_INPUTS/Browser-Target-Responses/_pending/
```

## Next Use

After an operator or external runtime starts a safe local target, set:

```powershell
$env:CHASEOS_EXCALIDRAW_TARGET_URL = "http://127.0.0.1:<port>/"
```

Then run:

```powershell
chaseos operate browser excalidraw-target-response --from-env --write-response --json
chaseos studio external-runtime-readiness --json
```

Only proceed to Excalidraw readiness/proof branches when the Studio readiness gate reports `excalidraw_branch_ready=true`.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
