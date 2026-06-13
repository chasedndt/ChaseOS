---
title: ChaseOS Setup Init Scaffold Specification
type: architecture
status: active
created: 2026-04-26
updated: 2026-04-27
phase: phase-9-hardening
---

# ChaseOS Setup Init Scaffold Specification

> This document defines what `chaseos setup init` should scaffold on a fresh system when ChaseOS is treated as a deployable product, not just a manually curated personal vault.

**Canonical CLI truth (2026-04-27):** the operator CLI entrypoint is `runtime.cli.main:main`. Installed `chaseos` and `chase` scripts point there directly. `chaseos.py` and `runtime/cli.py` are compatibility shims only and must not become parallel parser/registration surfaces.

---

## 1. Why This Exists

The existing `setup` family began as provider/integration onboarding.
That is necessary, but insufficient for ChaseOS as a deployable operator system.

A new user or machine needs more than API/provider setup.
It needs:
- a root node structure
- mandatory OS files
- machine-readable governance and runtime scaffolds
- operator-facing indexes
- runtime profile stubs
- personalization placeholders

`chaseos setup init` is the product bootstrap layer for that.

---

## 2. Design Principle

`setup init` should scaffold a **clean ChaseOS root** with:
- mandatory framework files
- generated machine-readable state
- human-readable orientation files
- optional profile-dependent extras
- placeholder personalization surfaces

It should **not** aggressively rewrite or absorb a user’s whole system.
It should create the ChaseOS substrate first, then support later attachment/import.

---

## 3. What `setup` Means in ChaseOS

`setup` is an operator-facing command family owned by the canonical parser in `runtime.cli.main`.
Design docs may propose subcommands and behavior, but shell-facing registration should land in one place only:
- `runtime/cli/main.py`

`chaseos.py` and `runtime/cli.py` may continue to exist for compatibility invocation paths, but they are shim entrypoints, not command-definition surfaces.

Recommended internal split:

### A. `setup init`
First-run bootstrap and scaffold creation.

### B. `setup validate` / `setup doctor`
Integrity and readiness checking.

### C. `setup wizard`
Guided mutation of providers, integrations, runtime profiles, and operator metadata.

### D. `setup attach` (future)
Attach existing folders, dashboards, source stores, or runtime endpoints into the ChaseOS substrate.

---

## 4. Scaffold Categories

### 4.1 Identity and operator layer
Purpose:
- define who operates this ChaseOS instance
- define machine/system role
- distinguish framework/core from user-personalized instance

Suggested files:
- `README.md`
- `PROJECT_FOUNDATION.md`
- `SOUL.md`
- operator profile stub
- system identity stub
- deployment profile stub

### 4.2 Home / control layer
Purpose:
- orient the operator on first open
- provide a current-state dashboard
- define system doctrine and contract surfaces

Suggested files:
- `00_HOME/Now.md`
- `00_HOME/Dashboard.md`
- `00_HOME/Operating-System.md`
- `00_HOME/Principles.md`
- `00_HOME/Assistant-Contract.md`

### 4.3 Knowledge and memory layer
Purpose:
- create durable operator indexes and review anchors
- avoid a flat undifferentiated note pile

Suggested files or indexes:
- `02_KNOWLEDGE/` domain roots
- `02_KNOWLEDGE/...` knowledge index files
- `07_LOGS/Daily/`
- `07_LOGS/Build-Logs/`
- `07_LOGS/Documentation-History/`
- `07_LOGS/Decisions/` or equivalent decision-log surfaces
- `KNOWLEDGE-INDEX.md`
- `BUILD-LOGS-INDEX.md`
- `DAILY-INDEX.md`
- `DOCUMENTATION-HISTORY-INDEX.md`
- `DECISIONS-INDEX.md`
- `OPERATOR-BRIEF-INDEX.md`

### 4.4 Governance layer
Purpose:
- make permission, trust, routing, and handoff behavior explicit
- define what agents may and may not do

Suggested files:
- `06_AGENTS/Agent-Registry.md`
- `06_AGENTS/Vault-Map.md`
- `06_AGENTS/Tool-Map.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Trust-Tiers.md`
- `06_AGENTS/Handoff-Protocol.md`
- `06_AGENTS/Agent-Control-Plane.md`
- `VAULTMAP.md` or operator shortcut alias if the product wants a top-level orientation surface
- machine-readable policy companions under `runtime/policy/`

### 4.5 Runtime layer
Purpose:
- scaffold runtime-aware operator surfaces for OpenClaw, Hermes, and future runtimes

Suggested files:
- runtime registry / runtime inventory seed
- lifecycle records
- bootstrap binding examples
- runtime profile stubs
- attachment/user-binding stubs
- navigation/runtime map seed surfaces

Suggested directories:
- `runtime/bindings/`
- `runtime/lifecycle/`
- `runtime/state/`
- `runtime/policy/`
- `runtime/schedules/`

Suggested runtime targets seeded by default:
- `openclaw`
- `hermes`
- future extensibility slot for more runtimes

### 4.6 Setup layer
Purpose:
- bootstrap the setup subsystem itself
- keep provider/integration/runtime onboarding explicit and machine-readable

Suggested files:
- `runtime/setup_registry.json`
- `runtime/setup_provider_profiles.json`
- `runtime/setup_state.example.json`
- `runtime/setup_state.schema.json`
- `runtime/setup_state.json`
- `runtime/SETUP-README.md`

### 4.7 Operational / dashboard layer
Purpose:
- let the user immediately see what exists, what is missing, and what to do next

Suggested files:
- `DASHBOARD.md` or `00_HOME/Dashboard.md`
- `SYSTEM-STATUS.md`
- `RUNTIME-REGISTRY.md`
- `NEXT-STEPS.md`

---

## 5. Scaffold-Appropriate vs Not Scaffold-Appropriate

This distinction is critical.
`setup init` should only scaffold files that are legitimate framework/bootstrap surfaces.
It should not pre-author personal truth, project truth, or fabricated history.

### Scaffold-appropriate
These are appropriate for `setup init` to create as:
- framework seeds
- placeholders
- starter templates
- machine-readable substrate files

Examples:
- root framework/product docs that are part of the deployable ChaseOS shape
- `00_HOME` orientation/control placeholders
- governance/routing surfaces
- runtime/setup machine-readable files
- dashboard/next-step/status surfaces
- index notes
- runtime profile seeds
- registry/manifest/state scaffolds

### Not scaffold-appropriate
These should not be auto-authored beyond maybe creating an empty containing folder or explicit placeholder stub where appropriate.

Examples:
- real personal doctrine content
- real project operating truth
- actual knowledge notes
- generated fake history
- fake daily notes
- fake build logs
- fake operator briefs
- fabricated decisions, experiments, or runtime outcomes
- private credentials or secrets
- user-specific domain populations pretending to be real

### Rule
If a file represents lived user state, real project truth, real history, or real verified knowledge, `setup init` should not invent it.
If a file represents framework orientation, runtime/setup substrate, or a placeholder the operator is expected to fill in, it is a better scaffold candidate.

## 6. Mandatory vs Optional

### Mandatory framework-generated
These should normally be created by `setup init`:
- core folder hierarchy
- governance files
- machine-readable runtime/setup policy surfaces
- runtime profile seeds
- core operator indexes
- dashboard / next-step surfaces
- permission matrix
- vault map / system map

### Optional profile-based
These may vary by init profile:
- academic surfaces
- business dashboards
- lab/server deployment notes
- creator/content engine scaffolds
- extra runtime slots
- extra integration/provider targets

### User-owned personalization
These should be created as placeholders only:
- operator doctrine details
- personal knowledge index population
- dashboard customization
- project-specific OS files
- private history/log content

---

## 7. Generated vs User-Owned Classification

`setup init` should classify scaffold outputs into:

### Generated and machine-maintained
Examples:
- machine-readable setup state
- runtime registry/state scaffolds
- generated indexes
- validation manifests

### Generated then user-maintained
Examples:
- dashboard
- next-step file
- operator brief index
- vault map companion notes

### Protected / high-authority
Examples:
- permission matrix
- assistant contract
- project foundation
- runtime governance docs

### User-authored personalization
Examples:
- doctrine details
- personal knowledge entries
- private project state
- operator notes/history

This classification should be reflected in `setup init` output and later in `setup doctor`.

---

## 8. Proposed Command Surface

All command examples below refer to the canonical operator surface reached through `runtime.cli.main:main`.
They should not be interpreted as justification for adding command registration directly to `chaseos.py`, `runtime/cli.py`, or other subsystem-local shell fronts.

```text
chaseos setup init
chaseos setup init --profile personal
chaseos setup init --profile workstation
chaseos setup init --with-runtime openclaw --with-runtime hermes
chaseos setup init --with-provider openai --with-provider claude
chaseos setup init --with-integration discord
chaseos setup init --dry-run
chaseos setup init --write
```

Likely companion commands:

```text
chaseos setup doctor
chaseos setup validate
chaseos setup attach ...
chaseos setup runtime wizard <runtime-id>
```

---

## 9. Recommended First Implementation Scope

The first real implementation of `setup init` should probably do only this:
- detect or accept a target root
- scaffold core folders
- scaffold mandatory setup/runtime machine-readable files
- scaffold key governance docs and indexes if missing
- seed `openclaw` and `hermes` runtime profile stubs
- produce a dry-run manifest of intended writes

Do not start with broad external-system scanning.
That belongs later, under explicit attach/import flows.

---

## 10. Recommendation on Vault Map and Permission Matrix

### `Vault-Map`
Yes, include it.
A deployable product needs a clear topological map.
If the product wants a friendlier top-level `VAULTMAP.md`, it can coexist with `06_AGENTS/Vault-Map.md` as long as one is canonical.

### `Permission-Matrix`
Absolutely include it.
This is a mandatory OS file, not an optional nice-to-have.
For a deployable agentic OS, permission boundaries must exist in both:
- human-readable form
- machine-readable enforcement form

---

## 11. Scaffold Boundary Guidance

### Appropriate to scaffold now
- folder hierarchy
- root product/foundation surfaces
- `00_HOME` orientation placeholders
- governance/routing docs that are part of the framework contract
- runtime/setup machine-readable records
- runtime profile seeds
- index-note surfaces
- operator-facing orientation/status/next-step files

### Not appropriate to scaffold as real content
- populated `01_PROJECTS/*-OS.md` files for actual user projects
- populated `02_KNOWLEDGE/*` notes pretending to be real knowledge
- dated daily notes
- dated build logs beyond the real log for the scaffold implementation itself
- real decision ledger entries unless a real decision occurred
- private tokens, auth values, secrets, or environment material
- fabricated runtime audit history

### Placeholder nuance
A placeholder is acceptable if it is visibly a placeholder and does not pretend to be real user truth.
A fake canonical note is not acceptable.

## 12. Next Development Step

After this spec:
1. keep `setup` command registration and parser ownership in `runtime/cli/main.py`
2. create a machine-readable scaffold manifest for `setup init`
3. implement dry-run output first
4. only then implement write mode
5. extend `setup doctor` / `validate` to check scaffold integrity

---

*Related: `README.md`, `PROJECT_FOUNDATION.md`, `FORKING.md`, `06_AGENTS/Vault-Map.md`, `06_AGENTS/Permission-Matrix.md`, `06_AGENTS/ChaseOS-Provider-and-Integration-Setup-CLI-Plan.md`*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
