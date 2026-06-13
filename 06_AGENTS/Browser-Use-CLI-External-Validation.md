---
title: Browser Use CLI External Validation
type: browser-runtime-readiness
status: implemented / help probe complete / no browser automation
created: 2026-05-05
updated: 2026-05-05
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio
runtime: Codex
---

# Browser Use CLI External Validation

This note records the bounded Browser Use CLI external validation command.

## Command

```powershell
$env:CHASEOS_BROWSER_USE_CLI = "C:\tmp\chaseos-browser-use-cli-venv\Scripts\browser-use.exe"
chaseos operate browser browser-use-cli-external-validation --from-env --execute-help-probe --write-evidence --run-slug browser-use-cli-external-validation-20260505-help-probe --json
```

## Current Result

As of 2026-05-05, the validation reports:

```text
status: browser_use_cli_external_validation_complete_help_probe_no_browser
help_probe_attempted: true
help_probe_exit_code: 0
expected_help_surface_present: true
observed_command_tokens: install, doctor, open, click, extract, cookies, tunnel, profile
```

Evidence:

```text
07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.json
07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.md
```

## Boundary

This command runs only `browser-use --help` when `--execute-help-probe` is set. It does not run Browser Use browser commands such as `open`, `click`, `extract`, `cookies`, `tunnel`, `profile`, or `cloud`; does not launch a browser; does not use a real profile; does not read credentials or cookies; does not call providers; does not write or activate skills; does not enqueue Agent Bus work; does not mutate Gate; and does not write canonical ChaseOS state.

## Next Use

The next pass is not unrestricted Browser Use automation. The next pass is:

```text
browser-use-cli-no-account-safe-url-validation-design
```

That pass must define the exact safe URL, profile isolation, timeout, allowed subcommand, evidence shape, and rollback/cleanup posture before any Browser Use browser command runs.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
