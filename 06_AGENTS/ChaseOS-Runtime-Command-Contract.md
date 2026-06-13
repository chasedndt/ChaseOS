---
title: ChaseOS Runtime Command Contract
type: architecture
status: seeded
created: 2026-04-24
updated: 2026-04-24
phase: phase-9-active
---

# ChaseOS Runtime Command Contract

> This document defines the intended command contract for ChaseOS runtime inspection and resolution surfaces.

---

## 1. Purpose

ChaseOS now has:
- runtime adapter manifests
- bootstrap and user-attachment contracts
- runtime navigation overlays
- a canonical runtime-state artifact
- a local CLI foothold under `runtime/state/runtime_cli.py`

The next requirement is a stable command contract.

Without that, runtime inspection remains an implementation detail.
With that, it becomes part of the operating system surface.

---

## 2. First Command Family

Recommended first runtime command family:

```text
chaseos runtime resolve
chaseos runtime status
```

These commands should be the formal OS-facing wrapper around the existing `runtime/state/` substrate.

---

## 3. Command Intent

### `chaseos runtime resolve`
Purpose:
- resolve runtime posture from current machine-readable sources
- write or refresh the canonical `current_state.json`
- optionally target a specific runtime lane

### `chaseos runtime status`
Purpose:
- show the current resolved runtime state
- optionally refresh first
- support summary view and JSON view

---

## 4. Proposed Command Contract

### Resolve
```text
chaseos runtime resolve [--runtime <runtime-id>] [--json]
```

Behavior:
- resolves runtime state
- writes `runtime/state/current_state.json`
- prints either a human summary or JSON output

### Status
```text
chaseos runtime status [--runtime <runtime-id>] [--refresh] [--json]
```

Behavior:
- reads `runtime/state/current_state.json` if present
- with `--refresh`, re-resolves first
- prints summary by default
- prints full JSON with `--json`

---

## 5. Expected Output Behavior

### Summary mode
Human-readable, concise, operator-first.
Should include at least:
- runtime id
- adapter id
- platform family
- attachment mode
- trust ceiling
- approval mode
- bootstrap status
- path to current state artifact

**Summary-context note:** This output should now be interpreted as a `runtime_status_summary` family artifact under `Runtime-Shell-and-Command-Surface-Summary-Context-Application.md`, not as sovereign runtime doctrine or a permission-bearing record.

### JSON mode
Full machine-readable resolved state object.
Useful for:
- tooling
- scripts
- future UI surfaces
- later local interface or gateway layers

---

## 6. Error Behavior

If resolution fails:
- write `runtime/state/last_error.json`
- print a concise operator-facing error
- return non-zero exit code

This is important because runtime inspection is only useful if unresolved state is also surfaced cleanly.

---

## 7. Relationship to the Overall ChaseOS OS

This command family matters because it is the first OS-facing runtime inspection contract.

It connects:
- governance doctrine
- machine-readable runtime policy
- canonical runtime-state resolution
- operator-visible command surfaces

This is the bridge between internal runtime substrate and future interface layers.

In other words:
this is one of the first places ChaseOS starts to look like an operating system with inspectable runtime state rather than only a governed repository.

---

## 8. Boundary

This command contract is for runtime inspection and resolution only.

It is not yet:
- runtime control
- process management
- daemon orchestration
- gateway administration
- network endpoint control

Those can come later, after inspection surfaces are stable.

---

## 9. Current Foothold Mapping

Current local foothold implementation:
- `python runtime\\state\\runtime_cli.py resolve`
- `python runtime\\state\\runtime_cli.py status`

Future intended stable OS-facing commands:
- `chaseos runtime resolve`
- `chaseos runtime status`

That means the current local script is not wasted work.
It is the proving ground for the future command contract.

---

## 10. Recommended Next Step

After this contract is accepted, the next implementation pass should either:
1. harden the local runtime CLI for packaging/promotion, or
2. define the broader ChaseOS CLI surface that this command family will live inside.

---

*Graph links: [[ChaseOS-Runtime-CLI-Foothold]] · [[ChaseOS-Runtime-State-and-Gateway-Design]] · [[Autonomous-Operator-Runtime]] · [[Runtime-Shell-and-Command-Surface-Summary-Context-Application]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
