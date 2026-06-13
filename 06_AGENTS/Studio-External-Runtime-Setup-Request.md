---
title: Studio External Runtime Setup Request
type: runtime-handoff
status: implemented / handoff ready / no execution
created: 2026-05-05
updated: 2026-05-05
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio
runtime: Codex
---

# Studio External Runtime Setup Request

This note records the no-execution setup handoff for the external Browser Use CLI and Excalidraw branches.

## Command

```powershell
chaseos studio external-runtime-setup-request --json
```

To write handoff evidence:

```powershell
chaseos studio external-runtime-setup-request --write-evidence --evidence-slug 2026-05-05-studio-external-runtime-setup-request --json
```

Implementation:

```text
runtime/studio/external_runtime_setup_request.py
runtime/studio/test_external_runtime_setup_request.py
```

## Current Result

As of 2026-05-05, the request packet reports:

```text
status: external_runtime_setup_request_ready_for_operator
requested_branches: browser-use, excalidraw
```

Evidence:

```text
07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-setup-request.md
07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-setup-request.json
```

## Meaning

The internal Studio lane is not blocked by another UI implementation pass. The blocker is external setup:

- Browser Use CLI must be installed or exposed outside ChaseOS, without real profiles, credentials, cookies, synced profiles, or public tunnels.
- Excalidraw needs an accepted loopback target response under `03_INPUTS/Browser-Target-Responses/_pending/`.

Browser Use CLI setup can now be checked through:

```powershell
chaseos operate browser browser-use-cli-preflight --from-env --json
```

The command reads `CHASEOS_BROWSER_USE_CLI` only when `--from-env` is passed and does not invoke Browser Use CLI.

After either setup branch is completed, rerun:

```powershell
chaseos studio external-runtime-readiness --json
```

Do not start Browser Use CLI validation or Excalidraw live proof until that readiness gate reports the relevant branch ready.

## Excalidraw Response Shape

Accepted target response shape:

```json
{
  "target_url": "http://127.0.0.1:<port>/"
}
```

Existing intake command:

```powershell
python -m runtime.browser_runtime.excalidraw_target_response --vault-root . --target-url http://127.0.0.1:<port>/ --write-response --json
```

ChaseOS CLI intake command:

```powershell
chaseos operate browser excalidraw-target-response --from-env --write-response --json
```

The CLI command reads `CHASEOS_EXCALIDRAW_TARGET_URL` only when `--from-env` is passed. It does not probe the target.

## Boundary

The setup request is a handoff only. It does not install dependencies, run subprocess probes, start servers, probe networks, launch browsers, run Browser Use CLI, run Excalidraw proof, connect CDP, invoke MCP, navigate targets, capture screenshots, grant or execute approvals, consume decisions, reserve markers, access real profiles, read credentials/cookies, export cookies, sync profiles, open public tunnels, write or activate skills, enqueue Agent Bus tasks, call providers/connectors, mutate Gate, or write canonical ChaseOS state.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
