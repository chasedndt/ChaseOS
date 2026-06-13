---
title: Portable Runtime Identity and User Binding
type: architecture
status: seeded
created: 2026-04-24
updated: 2026-04-24
phase: phase-9-seeded phase-10-relevant
---

# Portable Runtime Identity and User Binding

> This document defines how ChaseOS should separate portable runtime governance from machine-local and personal user binding.
> The goal is to let any runtime or harness launched on this system, or later on another system, inherit ChaseOS governance cleanly across Windows, WSL, Linux, and future execution surfaces.

---

## 1. Why This Exists

ChaseOS is evolving toward a human-AI operating system, not a single-runtime chat setup.

That means three things must be true:

1. Runtime rules must travel cleanly across execution surfaces.
2. Personal user state must be attachable and detachable.
3. GitHub-safe framework truth must remain separable from private machine-local truth.

Right now, those layers are still partly fused.

This document names the separation explicitly so the runtime layer can become portable without leaking personal-instance state.

---

## 2. Core Principle

ChaseOS should distinguish between:

### A. System Constitutional Layer
Portable, framework-safe, repo-safe.

Contains:
- control-plane rules
- Permission Matrix
- Trust Tiers
- Gate / AOR governance
- adapter standards
- routing doctrine
- runtime identity contracts

### B. Runtime Identity Layer
Mostly portable, runtime-specific, GitHub-safe.

Contains:
- runtime posture
- navigation overlays
- self-orientation contracts
- capability classes
- blocked/deferred/allowed state models
- runtime-specific read/write/escalation routes

### C. Personal User Binding Layer
Machine-local, detachable, private.

Contains:
- real user IDs
- local account bindings
- Discord/Telegram/etc. instance bindings
- personal memory
- user profile attachment
- machine-local secrets and private overrides

This separation allows the same ChaseOS runtime substrate to operate across different machines and users without hard-baking one personal instance into the framework.

---

## 3. Architectural Goal

A runtime launched under ChaseOS should be able to answer three different questions cleanly:

- **What rules govern me?** → constitutional layer
- **What kind of runtime am I?** → runtime identity layer
- **Which user am I attached to on this machine?** → personal binding layer

Those answers should come from different files and should be removable independently.

---

## 4. Layer Model

```text
ChaseOS Constitutional Layer
  -> shared governance, permissions, doctrine, adapter rules

Runtime Identity Layer
  -> runtime type, self-state, navigation, capabilities, next actions

Machine Binding Layer
  -> platform bindings, local paths, runtime bootstrap bindings

Personal User Binding Layer
  -> user attachment, private memory, local account identity, secrets
```

The lower layers may specialize the upper ones.
They must not override them arbitrarily.

---

## 5. Cross-Platform Runtime Requirement

This model must work for runtimes launched from:
- native Windows
- WSL
- Linux
- future containerized or remote runtime surfaces

Therefore ChaseOS should eventually provide a runtime bootstrap contract that expresses:
- platform family
- path normalization rules
- repo root resolution
- machine-local binding discovery
- runtime identity discovery
- user attachment discovery
- fail-closed behavior when bindings are missing or ambiguous

A runtime should not need to infer personal identity from the repo itself.

---

## 6. Runtime Bootstrap Expectations

Any runtime or harness launched under ChaseOS should eventually bootstrap in this order:

1. Load ChaseOS constitutional rules.
2. Load runtime identity profile.
3. Load machine-local binding layer.
4. Attach a personal user profile only if locally present and permitted.
5. Surface current posture: portable core only vs attached personal instance.

This means a runtime can still function in a GitHub-safe or public-core mode even when no personal user is attached.

---

## 7. Detachable User Binding

The user layer must be detachable.

Detaching a personal user should remove or isolate:
- private memory
- personal account bindings
- machine-local IDs
- personal operating history
- private connectors and credentials

Detaching a user should **not** break:
- ChaseOS constitutional rules
- runtime identity contracts
- adapter manifests
- routing doctrine
- markdown index structure
- build-log and archive discipline

This is essential for open-source publication and future multi-user portability.

---

## 8. Relationship to Existing ChaseOS Files

This document does not replace:
- `CLAUDE.md`
- `README.md`
- `06_AGENTS/Agent-Control-Plane.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Runtime-Navigation-Map.md`
- runtime profiles under `06_AGENTS/`

Instead it sits across them and clarifies which parts belong to portable runtime identity vs private user attachment.

---

## 9. Immediate Implementation Direction

Near-term implementation should focus on:
- making runtime self-orientation portable
- making self-report files explicitly governance-subordinate
- introducing a machine-readable user-binding contract later
- separating repo-safe runtime profile files from local private bindings
- ensuring markdown indexes remain stable during the split

This is a Phase 9 architectural preparation task with clear Phase 10 relevance.

---

## 10. Recommended Machine-Readable Counterparts

Over time this doc should map to machine-readable layers such as:
- `runtime/memory/nav/<runtime>/state.json`
- `runtime/memory/nav/<runtime>/capabilities.json`
- `runtime/memory/nav/<runtime>/next-actions.json`
- `runtime/memory/nav/<runtime>/self-report.json`
- future `runtime/bindings/` for platform-local runtime bootstrap data
- future machine-local user attachment file outside the public repo or under a private local layer

---

## 11. Current Verdict

ChaseOS should not treat a personal user instance as the same thing as runtime identity.

Portable runtime governance, runtime self-description, and detachable user attachment are separate layers.

That separation is what will let ChaseOS become:
- multi-runtime
- cross-platform
- GitHub-safe at the framework layer
- personal where intended
- detachable where necessary

---

*Graph links: [[Vault-Map]] · [[README]] · [[CLAUDE]] · [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Runtime-Navigation-Map]] · [[OpenClaw-Runtime-Profile]] · [[Hermes-Runtime-Profile]] · [[Core-Personal-Split-Implementation-Plan]]*
