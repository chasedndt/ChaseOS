# ChaseOS Command README

> Historical promotion note for the first repo-local ChaseOS-branded top-level command entrypoint. Retained for architecture history, not as the current command-truth source.

---

## What This Is

This file documents the first repo-local promoted ChaseOS command surface:

```powershell
python chaseos.py ...
```

That historical promotion step mattered, but it is no longer the canonical CLI truth.
Current canonical operator entrypoint:
- `runtime.cli.main:main`

Installed `chaseos` and `chase` scripts point there directly.
`chaseos.py` now survives as a compatibility shim only.

---

## Why This Matters

Before this promotion step, the operator had to know subsystem-specific paths such as:
- `python runtime\cli.py ...`
- `python runtime\state\runtime_cli.py ...`
- `python runtime\lifecycle\health_cli.py ...`

After this promotion step, the operator can begin using:
- `python chaseos.py runtime status`
- `python chaseos.py runtime resolve`
- `python chaseos.py runtime health --runtime openclaw`
- `python chaseos.py gate validate`

That is much closer to the intended long-term shell identity.

---

## Current Commands

### Runtime inspection
```powershell
python chaseos.py runtime resolve
python chaseos.py runtime status
python chaseos.py runtime status --refresh --json
python chaseos.py runtime health --runtime openclaw
```

### Gate inspection
```powershell
python chaseos.py gate validate
python chaseos.py gate list
python chaseos.py gate show openclaw
```

### Lifecycle health foothold
Preferred shape:
```powershell
python chaseos.py runtime health --runtime openclaw
python chaseos.py runtime health --runtime openclaw --json
```

Legacy transitional alias still available:
```powershell
python chaseos.py health openclaw
python chaseos.py health openclaw --json
```

---

## Important Current Truth

This file should now be read as command-surface history, not the live command contract.

Current command-spine truth:
- installed `chaseos` / `chase` -> `runtime.cli.main:main`
- `python chaseos.py ...` -> compatibility shim into the same parser
- `python runtime/cli.py ...` -> compatibility shim into the same parser

So the operator-facing progression was:
- internal subsystem scripts
- local CLI seam under `runtime/cli.py`
- promoted repo-local top-level entrypoint under `chaseos.py`
- canonical package-native CLI under `runtime.cli.main:main`

---

## Relationship to the Overall ChaseOS OS

This step matters because it gives the operating system a more recognizable command identity.

It is one of the first places where ChaseOS starts to look like:
- a real command surface
- a control plane in formation
- an OS with a branded shell entrypoint

---

## Recommended Reading

For current command truth, prefer:
- `runtime/CLI-README.md`
- `06_AGENTS/ChaseOS-CLI-Surface-Architecture.md`
- `06_AGENTS/ChaseOS-CLI-Consolidation-Refactor.md`

For historical context:
- `runtime/COMMANDS.md`
- `CLI-SURFACES.md`
- `runtime/LIFECYCLE-README.md`
- `06_AGENTS/ChaseOS-Top-Level-Command-Promotion.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
