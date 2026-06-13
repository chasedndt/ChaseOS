---
title: ChaseOS Top-Level Command Promotion
type: architecture
status: seeded
created: 2026-04-24
updated: 2026-04-24
phase: phase-9-active
---

# ChaseOS Top-Level Command Promotion

> This document defines the next step after local CLI footholds and integration seams: promoting the operator-facing command identity toward real `chaseos ...` commands.

---

## 1. Why This Exists

ChaseOS now has:
- runtime inspection command footholds
- Gate command footholds
- a local CLI integration seam under `runtime/cli.py`
- a broader CLI tree architecture
- a runtime lifecycle contract and seeded lifecycle layer

But the operator-facing entry surface still looks like:
- `python runtime\\cli.py ...`
- `python runtime\\state\\runtime_cli.py ...`
- `python runtime\\lifecycle\\health_cli.py ...`

That is acceptable for a foothold.
It is not the right long-term product shape.

The intended operator-facing identity should become:
- `chaseos runtime ...`
- `chaseos gate ...`
- later broader `chaseos ...` command families

---

## 2. Core Principle

ChaseOS should distinguish between:

### internal footholds
Scripts and subsystem entrypoints used during incremental implementation.

### promoted operator surface
The stable branded shell identity that operators are expected to use.

The current `python ...` paths are internal footholds.
The future `chaseos ...` family is the promoted operator surface.

---

## 3. Promotion Goal

The next goal is not necessarily full packaging yet.
It is to create a first real top-level command entrypoint that exposes the growing CLI tree under the ChaseOS name.

That means the operator should begin seeing and using:

```text
chaseos runtime status
chaseos runtime resolve
chaseos gate validate
```

while the current subsystem scripts remain as internal implementation seams underneath.

---

## 4. Recommended First Promotion Shape

A first promotion foothold could look like:

```text
chaseos.py runtime status
chaseos.py runtime resolve
chaseos.py gate validate
```

or another repo-local top-level entrypoint that clearly represents the future branded command family.

This still would not be the final installed CLI package, but it would move the operator experience from:
- subsystem script paths

to:
- ChaseOS-branded command identity

---

## 5. Promotion Strategy

### Phase 1
Unify command dispatch behind a single repo-local top-level entrypoint.

### Phase 2
Treat subsystem-local scripts as internal modules or delegated handlers.

### Phase 3
Promote that entrypoint into a packaged or installed `chaseos` command.

This has now begun in practice:
- the package script entrypoint has been redirected to the richer top-level `chaseos.py` surface
- install notes now describe the editable-install path for the promoted command tree
- the remaining work is validation and final adoption, not deciding whether promotion should happen

This keeps implementation practical without abandoning the product-facing CLI identity.

---

## 6. Why This Aligns with the Overall ChaseOS OS

This matters because an operating system needs a recognizable command identity.

Policy, state, lifecycle, runtime control, and shell surfaces all become easier to reason about once they are presented under one coherent top-level command family.

This is part of ChaseOS becoming:
- more operable
- more inspectable
- more product-shaped
- less dependent on implementation-path knowledge

---

## 7. Recommended Next Step

Create a first repo-local promoted entrypoint that dispatches to the current CLI seam and lifecycle footholds, then document it clearly as:
- the current promoted command surface
- still one step below a fully packaged installed `chaseos` binary

---

*Graph links: [[ChaseOS-CLI-Integration-Seam]] · [[ChaseOS-CLI-Surface-Architecture]] · [[ChaseOS-Runtime-Lifecycle-Contract]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
