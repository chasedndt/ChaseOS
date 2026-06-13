---
title: ChaseOS CLI Integration Seam
type: architecture
status: historical
created: 2026-04-24
updated: 2026-04-27
phase: phase-9-hardening
---

# ChaseOS CLI Integration Seam

> Historical note for the first integration seam that turned subsystem-local command footholds into a more unified ChaseOS CLI surface. Retained as architecture history, not as the current command-spine source of truth.

---

## 1. Why This Exists

ChaseOS now has multiple local command footholds:
- `runtime/chaseos_gate.py`
- `runtime/state/runtime_cli.py`

It also has a documented future shell tree:
- `capture`
- `intake`
- `watch`
- `run`
- `runtime`
- `gate`
- `schedule`
- `doctor`
- `test`

The next requirement is an integration seam.

That means:
- not yet a full packaged CLI rewrite
- not yet a final production entrypoint
- but no longer leaving each subsystem as a disconnected manual script

---

## 2. Goal

Create a small unifying CLI foothold that:
- dispatches to the strongest current local command families
- preserves the already-built subsystem code
- mirrors the intended future top-level shell tree
- gives operators one emerging command entrypoint to grow around

---

## 3. Recommended First Seam

Historical local entrypoint:

```powershell
python runtime\cli.py ...
```

That seam mattered, but it is no longer the canonical CLI truth.
Current command-spine truth:
- installed `chaseos` / `chase` -> `runtime.cli.main:main`
- `python chaseos.py ...` -> compatibility shim
- `python runtime\cli.py ...` -> compatibility shim

---

## 4. First Families to Wire

The first unified seam should wire only the command families that already have meaningful local implementation:

### `runtime`
Backed by:
- `runtime/state/runtime_cli.py`

### `gate`
Backed by:
- `runtime/chaseos_gate.py`

That means the first seam can support commands such as:

```text
python runtime\cli.py runtime resolve
python runtime\cli.py runtime status
python runtime\cli.py gate validate
python runtime\cli.py gate list-adapters
```

---

## 5. Why This Is the Right Order

Because ChaseOS should promote real subsystem footholds upward gradually.

The wrong approach would be:
- invent a beautiful top-level CLI that mostly dispatches to nothing

The right approach is:
- start with the strongest real command families
- unify them behind one seam
- expand outward as other families become real

---

## 6. Expected Future Promotion Path

### Current foothold
```text
python runtime\cli.py runtime ...
python runtime\cli.py gate ...
```

### Later promotion
```text
chaseos runtime ...
chaseos gate ...
```

This keeps the shell tree architecture stable while allowing the concrete entrypoint to evolve later.

---

## 7. Alignment with the Overall ChaseOS OS

This seam matters because it is one of the first steps from:
- subsystem scripts

toward:
- a unified operating-system command surface

It helps ChaseOS develop a CLI identity without prematurely forcing full packaging or a gateway daemon.

---

## 8. Recommended Next Step

This next step has already been surpassed by the CLI consolidation pass.
For current truth, prefer:
- `06_AGENTS/ChaseOS-CLI-Surface-Architecture.md`
- `06_AGENTS/ChaseOS-CLI-Consolidation-Refactor.md`
- `runtime/CLI-README.md`

---

*Graph links: [[ChaseOS-CLI-Surface-Architecture]] · [[ChaseOS-Runtime-Command-Contract]] · [[ChaseOS-Runtime-CLI-Foothold]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
