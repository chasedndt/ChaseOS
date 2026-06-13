---
title: ChaseOS CLI JSON Output Contract
type: architecture-contract
status: active-foothold
created: 2026-04-27
model: Codex GPT-5
phase: phase-9-hardening
---

# ChaseOS CLI JSON Output Contract

> This note documents the canonical JSON envelope for `chaseos ... --json` output.

---

## Contract

Canonical CLI JSON output must use these top-level keys:

```json
{
  "ok": true,
  "action": "command.family.action",
  "result": {},
  "errors": [],
  "warnings": [],
  "audit_id": null
}
```

Key meanings:

- `ok` - boolean success state, derived from command exit code.
- `action` - dotted CLI action path, such as `gate.check-operation` or `agent-bus.task.create`.
- `result` - native command payload. Existing detailed payloads live here.
- `errors` - list of machine-readable or human-readable error details.
- `warnings` - list of non-fatal warnings.
- `audit_id` - audit record identifier where a command creates or returns one; otherwise `null`.

---

## Implementation

The canonical wrapper lives at:

```text
runtime/cli/json_contract.py
```

`runtime/cli/main.py` applies the envelope at the `main()` boundary when `args.output_json` is true. This preserves existing command handler internals while making the shell-facing contract consistent.

Handlers may still print their native JSON payloads. Canonical CLI callers see those payloads under `result`.

---

## Current Scope

Active through canonical CLI entrypoints:

```text
python -m runtime.cli.main ... --json
chaseos ... --json
chase ... --json
python chaseos.py ... --json
python runtime/cli.py ... --json
```

Direct subsystem CLIs, such as `python runtime/setup_cli.py ... --json`, are not yet guaranteed to use the envelope unless they call through `runtime.cli.main`.

---

## Runtime Guidance

When adding a new command:

1. Keep native command data as a dict/list suitable for `result`.
2. Return non-zero exit codes for failed commands.
3. Prefer native payload keys `errors`, `warnings`, and `audit_id` when available; the wrapper will lift them into the envelope.
4. Avoid printing non-JSON noise to stdout when `--json` is set. Use stderr for human diagnostics.
5. Do not bypass `runtime.cli.main` for operator-facing command registration.

---

## Verification

Focused verification on 2026-04-27:

```powershell
python -m py_compile runtime\cli\json_contract.py runtime\cli\main.py runtime\cli\agent_bus_commands.py runtime\cli\gate_commands.py
python -m pytest -q runtime\tests\test_cli_json_contract.py runtime\tests\test_gate_deny_default_runtime_policy.py runtime\tests\test_agent_bus_runtime_cli_surface.py runtime\tests\test_cli_gate_and_coordination_surface.py -p no:cacheprovider
```

Result:

```text
16 passed
```

Smokes:

```powershell
python -m runtime.cli.main gate check-operation gateway.magic.write --json
python -m runtime.cli.main gate check-operation agent_bus.task.create --actor-adapter Hermes --target-runtime OpenClaw --json
python -m runtime.cli.main agent-bus runtimes --json
```

All emitted the top-level contract keys.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
