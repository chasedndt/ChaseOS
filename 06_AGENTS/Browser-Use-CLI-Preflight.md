---
title: Browser Use CLI Preflight
type: browser-runtime-readiness
status: implemented / installed externally / preflight ready / no execution
created: 2026-05-05
updated: 2026-05-05
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio
runtime: Codex
---

# Browser Use CLI Preflight

This note records the `chaseos` CLI surface for checking Browser Use CLI setup without invoking the executable.

## Command

```powershell
chaseos operate browser browser-use-cli-preflight --json
```

To read an operator-provided executable name/path:

```powershell
$env:CHASEOS_BROWSER_USE_CLI = "browser-use"
chaseos operate browser browser-use-cli-preflight --from-env --json
```

Current external install path:

```powershell
$env:CHASEOS_BROWSER_USE_CLI = "C:\tmp\chaseos-browser-use-cli-venv\Scripts\browser-use.exe"
```

The current Windows user environment value is also set to that path. ChaseOS now reads
`CHASEOS_BROWSER_USE_CLI` from process env first, then from the Windows User environment,
so a fresh shell or Codex process does not have to reassign `$env:CHASEOS_BROWSER_USE_CLI`
before using `--from-env`.

An explicit argument takes precedence:

```powershell
chaseos operate browser browser-use-cli-preflight --executable browser-use --json
```

## Current Result

As of 2026-05-05, after operator-authorized external install into `C:\tmp\chaseos-browser-use-cli-venv`, the live preflight reports:

```text
status: ready_for_operator_authorized_live_validation_no_execution
executable: C:\tmp\chaseos-browser-use-cli-venv\Scripts\browser-use.exe
executable_found: true
ready_for_future_live_validation: true
blocker: browser_use_cli_live_validation_not_run
executable_source: CHASEOS_BROWSER_USE_CLI
executable_source_detail: windows_user
```

Studio external runtime readiness now also honors `CHASEOS_BROWSER_USE_CLI`, so the Browser Use branch gate can become ready without relying on PATH discovery.

## Boundary

This command reads the Browser Runtime wrapper/config posture and checks executable discoverability. It does not install dependencies, run subprocess probes, invoke Browser Use CLI, launch a browser, read real profiles, read credentials/cookies, export cookies, sync profiles, open public tunnels, write or activate trusted skills, enqueue Agent Bus tasks, call providers, mutate Gate, or write canonical ChaseOS state.

## Next Use

After an external runtime/operator installs or exposes Browser Use CLI outside ChaseOS, rerun:

```powershell
chaseos operate browser browser-use-cli-preflight --from-env --json
chaseos studio external-runtime-readiness --json
chaseos studio external-runtime-branch-gate --branch browser-use-cli-external-runtime-validation --json
```

Do not run live Browser Use CLI validation until this preflight reports `ready_for_future_live_validation=true`, the branch gate reports `can_start_branch=true`, and the operator explicitly approves a no-account validation pass.

## Follow-On Validation

The next bounded validation command is documented in `06_AGENTS/Browser-Use-CLI-External-Validation.md`.

Current result:

```text
browser_use_cli_external_validation_complete_help_probe_no_browser
```

That result proves the installed CLI responds to `--help`; it does not prove Browser Use can safely open or operate a browser target yet.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
