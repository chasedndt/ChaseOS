---
title: ChaseOS CLI Surfaces
status: active
created: 2026-04-24
updated: 2026-04-27
---

# ChaseOS CLI Surfaces

> High-level map of the intended ChaseOS shell command tree.

---

## Current Purpose

This file gives a top-level operator-facing map of how ChaseOS shell surfaces should organize as a coherent command tree.

For the canonical command inventory, see:
- `runtime/COMMANDS.md`

For runtime-specific command usage, see:
- `runtime/COMMANDS-README.md`
- `runtime/state/CLI-README.md`

---

## Intended Top-Level Tree

```text
chaseos capture ...
chaseos intake ...
chaseos watch ...
chaseos run ...
chaseos runtime ...
chaseos gate ...
chaseos schedule ...
chaseos doctor ...
chaseos test ...
```

---

## Key Idea

This tree is organized by OS-level operator intent, not by whichever implementation stub happened to appear first.

That is important because ChaseOS is becoming an operating system surface, not just a bundle of scripts.

---

## Current Strongest Footholds

Right now, the strongest directly inspectable local footholds in this repo are:
- `runtime.cli.main:main` → canonical operator CLI entrypoint
- `runtime/state/runtime_cli.py` → subsystem-local runtime foothold beneath the canonical CLI
- `runtime/chaseos_gate.py` → subsystem-local gate foothold beneath the canonical CLI
- `runtime/cli.py` → compatibility shim for direct invocation
- `chaseos.py` → compatibility shim for direct invocation

---

## Recommended Reading

- `runtime/COMMANDS.md`
- `06_AGENTS/ChaseOS-CLI-Surface-Architecture.md`
- `06_AGENTS/ChaseOS-Runtime-Command-Contract.md`
- `runtime/state/COMMAND-CONTRACT-README.md`

---

## Why This Matters

A good CLI tree is part of the product shape of the OS.
It helps ensure that future CLI, local interface, and gateway layers are built on a coherent shell model rather than ad hoc command growth.

Current command-spine rule:
- add new shell-facing command registration in `runtime/cli/main.py`
- keep `chaseos.py` and `runtime/cli.py` as passive compatibility shims only


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
