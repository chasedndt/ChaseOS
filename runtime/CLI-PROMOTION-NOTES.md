---
title: Runtime CLI Promotion Notes
status: seeded
created: 2026-04-25
updated: 2026-04-25
---

# Runtime CLI Promotion Notes

## Why `health` and `health-debug` belong in the CLI tree

During runtime lifecycle hardening, a temporary standalone test harness was useful for isolating root-cause behavior.
But the durable product shape for ChaseOS is CLI-first.

That means:
- routine runtime health should live under `runtime health`
- diagnostic visibility should live under `runtime health-debug`
- both should remain part of the runtime family rather than drifting into ad hoc scripts

## Current local command shapes

```powershell
python runtime\cli.py runtime resolve
python runtime\cli.py runtime status --refresh --json
python runtime\cli.py runtime health --runtime openclaw --json
python runtime\cli.py runtime health-debug --runtime openclaw --json
python chaseos.py runtime health --runtime openclaw --json
```

## Product-shape meaning

This is part of ChaseOS becoming an operator-facing system surface rather than a loose set of implementation scripts.

The CLI tree is starting to separate:
- runtime inspection
- runtime lifecycle health
- runtime health diagnostics
- policy/gate checks

into one coherent operator model.

Top-level richness target:
- `chaseos.py runtime status` should surface the same important posture fields an operator would need from the runtime-state layer
- `chaseos.py runtime health` should match the richer lifecycle-health rendering already used in the runtime CLI seam
- gate may remain delegated a little longer because its dependency/profile story still needs hardening

## Consistency expectation

The promoted top-level `chaseos.py` health output should match the unified `runtime/cli.py` health output closely enough that the operator does not feel like they are switching tools when they move between those two surfaces.
