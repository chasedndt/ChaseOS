---
title: Browser Use CLI Safe-URL Validation Run
type: browser-runtime-readiness
status: complete targeted / no-account loopback open verified
created: 2026-05-05
updated: 2026-05-05
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio
runtime: Codex
---

# Browser Use CLI Safe-URL Validation Run

This note records the bounded Browser Use CLI no-account validation run against a ChaseOS-owned loopback target.

## Command

```powershell
chaseos operate browser browser-use-cli-safe-url-validation-run --run-browser-use --write-evidence --run-slug browser-use-cli-safe-url-validation-run-20260505 --run-timeout-seconds 90 --target-ready-timeout-seconds 15 --json
```

## Result

```text
status: browser_use_cli_safe_url_validation_run_complete
target_url: http://127.0.0.1:8770/
browser_use_cli_open_attempted: true
browser_use_cli_exit_code: 0
browser_use_open_succeeded: true
browser_use_cli_close_attempted: true
browser_use_cli_close_exit_code: 0
browser_use_close_succeeded: true
next_recommended_pass: browser-runtime-external-validation-closeout
```

Evidence:

```text
07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-run-20260505.json
07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-run-20260505.md
```

## Download / Dependency Truth

- Browser Use Python package/executable download/install: COMPLETE.
- Verified package: `browser-use` 0.12.6.
- Verified executable: `C:\tmp\chaseos-browser-use-cli-venv\Scripts\browser-use.exe`.
- Browser Use browser dependency availability: VERIFIED BY SUCCESSFUL `open`.
- `browser-use install`: NOT RUN by this pass.
- Browser dependency auto-download evidence: not observed in stdout/stderr.

## Runtime Boundary

The runner started the ChaseOS Studio Product UI test target only because `http://127.0.0.1:8770/health.json` was not already ready. It killed only the process it started after the Browser Use run.

Allowed Browser Use actions in this pass:

- `open http://127.0.0.1:8770/`
- `close` for the named throwaway session cleanup

This pass did not use `--profile`, `--cdp-url`, `--connect`, `--headed`, `install`, cookies, extract, eval, python, upload, tunnel, cloud, provider calls, real profiles, credentials, Gate mutation, Agent Bus writes, skill activation, trusted writes, or canonical writeback.

## Completion Truth

Browser Use CLI live validation is now complete targeted for the no-account safe-URL lane. Remaining Browser Runtime production blockers are Excalidraw target/readiness and Excalidraw live browser/MCP proof.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
