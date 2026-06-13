---
title: ChaseOS CLI Consolidation Refactor
type: architecture-refactor
status: active
created: 2026-04-26
model: Codex GPT-5
phase: phase-9-hardening
---

# ChaseOS CLI Consolidation Refactor

> This note explains the 2026-04-26 CLI spine refactor so agentic runtimes can review it without rediscovering the old command split.

---

## Summary

The canonical operator CLI is now `runtime.cli.main:main`.

`pyproject.toml` maps both installed scripts to that package-native entrypoint:
- `chaseos = "runtime.cli.main:main"`
- `chase = "runtime.cli.main:main"`

Legacy front doors remain, but only as compatibility shims:
- `chaseos.py`
- `runtime/cli.py`

Those shims import `build_parser` and `main` from `runtime.cli.main`; they do not define a second parser tree, shell out to sibling scripts, or own command registration.

Follow-up hardening on 2026-04-26 also reduced the remaining setup-family grammar drift: `runtime/setup_cli.py` still exists for direct compatibility use, but its command grammar now comes from a shared `add_setup_subcommands(...)` builder instead of a separately maintained second setup parser tree.

---

## Why This Was Needed

Before this refactor, ChaseOS had multiple command fronts:
- root `chaseos.py`
- `runtime/cli.py`
- package CLI `runtime/cli/main.py`
- subsystem scripts such as `runtime/state/runtime_cli.py`, `runtime/setup_cli.py`, and `runtime/chaseos_gate.py`

That made Phase 10 gateway/studio integration risky because runtime, setup, and gate behavior could drift depending on which command front an agent or shell used.

The new rule is simple:

**All operator-facing command families are registered in `runtime/cli/main.py`.**

Subsystem scripts may remain for direct development or compatibility, but they are not the source of shell truth.

---

## What Changed

Implemented in this pass:
- `pyproject.toml` console scripts now point at `runtime.cli.main:main`
- `chaseos.py` is a shim for direct `python chaseos.py ...` usage
- `runtime/cli.py` is a shim for direct `python runtime/cli.py ...` usage
- `runtime/setup_cli.py` now exposes a shared setup-subcommand builder so direct setup compatibility uses the same grammar source as the canonical CLI
- `runtime.cli.main` now owns `runtime` commands:
  - `runtime resolve`
  - `runtime inventory`
  - `runtime status`
  - `runtime health`
  - `runtime health-debug`
  - `runtime coordination-watch`
  - `runtime coordination-watch-supervisor`
  - `runtime coordination-watch-bootstrap`
- `runtime.cli.main` now owns the top-level `health` compatibility alias
- `runtime.cli.main` now owns `setup` parser registration and calls `runtime.setup_cli` handlers directly
- `runtime/setup_cli.py` now supports package-native import via `runtime.setup_state`
- tests were rewritten to patch canonical `runtime.cli.main` behavior instead of shim internals

---

## Runtime Review Points

Agentic runtimes should inspect these files first:
- `runtime/cli/main.py`
- `chaseos.py`
- `runtime/cli.py`
- `pyproject.toml`
- `runtime/setup_cli.py`
- `runtime/tests/test_cli_entrypoint_consolidation.py`

The expected invariant:

```text
installed chaseos/chase
python chaseos.py ...
python runtime/cli.py ...
python -m runtime.cli.main ...
        |
        v
runtime.cli.main.build_parser()
```

---

## Security / Phase 10 Implications

This refactor reduces command-spine ambiguity, but it does not finish gateway security.

The first follow-up has now started:
- `06_AGENTS/ChaseOS-Deny-Default-Runtime-Policy.md`
- `07_LOGS/Build-Logs/2026-04-27-ChaseOS-Deny-Default-Runtime-Policy-Codex-GPT5.md`

The second follow-up started the canonical JSON response envelope:
- `06_AGENTS/ChaseOS-CLI-JSON-Output-Contract.md`
- `07_LOGS/Build-Logs/2026-04-27-ChaseOS-CLI-JSON-Output-Contract-Codex-GPT5.md`

The third follow-up started generated CLI docs and install verification:
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `runtime/cli/generate_docs.py`
- `chaseos doctor cli`
- `07_LOGS/Build-Logs/2026-04-27-ChaseOS-CLI-Docs-and-Doctor-CLI-Codex-GPT5.md`

Before Phase 10, continue adding:
- deny-by-default gateway operation policy and Studio-side caller coverage
- positive allowlists for external side effects, write targets, task types, and control-plane transports
- credential scan or credential-boundary validation for gateway/setup outputs
- Core/Personal export manifest verification before public or framework mirroring
- tests that prove gateway/studio surfaces call the same `chaseos gate` and `chaseos runtime` policy checks

---

## Logs

Build log:
- `07_LOGS/Build-Logs/2026-04-26-ChaseOS-CLI-Consolidation-Codex-GPT5.md`

Documentation history:
- `99_ARCHIVE/Documentation-History/2026-04-26-ChaseOS-CLI-Consolidation-Codex-GPT5.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
