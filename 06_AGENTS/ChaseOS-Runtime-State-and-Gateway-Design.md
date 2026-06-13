---
title: ChaseOS Runtime State and Gateway Design
type: architecture
status: seeded
created: 2026-04-24
updated: 2026-04-24
phase: phase-9-active, phase-10-relevant
---

# ChaseOS Runtime State and Gateway Design

> This document defines the next practical development step after portable runtime bootstrap seeding: a live runtime-state surface and bootstrap-enforcement path that can later evolve into a ChaseOS-native gateway/interface layer.

---

## 1. Why This Is the Next Priority

ChaseOS now has enough runtime doctrine to stop adding architecture in the abstract and start making runtime posture visible and enforceable.

What exists already:
- adapter manifests under `runtime/policy/adapters/`
- AOR workflow substrate under `runtime/aor/`
- runtime navigation overlays under `runtime/memory/nav/`
- bootstrap and user-attachment contracts under `runtime/bindings/`
- bounded live runtime proof via OpenClaw

What is still missing:
- one canonical machine-readable answer to **what runtime is active right now**
- one canonical machine-readable answer to **what attachment mode is active right now**
- bootstrap resolution logic that can fail closed when bindings are ambiguous
- a future-facing interface/gateway surface for inspecting and operating that state

That missing middle is the next highest-value Phase 9 development priority.

---

## 2. Core Goal

Introduce a ChaseOS-owned runtime-state layer that:
- resolves runtime posture at startup
- exposes that posture in machine-readable form
- lets AOR and future operator surfaces consult one canonical state object
- can later be surfaced through a local interface, status endpoint, or gateway process

This is not yet a full ChaseOS interface product.
It is the beginning of one.

---

## 3. Recommended Deliverable for This Phase

### Phase 9 target
Build a **Runtime State Resolver** plus a **local runtime-state artifact**.

Minimum deliverables:
- runtime bootstrap resolution flow
- attachment-mode resolution flow
- canonical runtime-state JSON artifact
- failure-state artifact for unresolved or ambiguous startup
- status command or loader that AOR and adapters can consult

This would give ChaseOS a live substrate for runtime identity rather than only static doctrine.

---

## 4. Proposed New Runtime Surface

Recommended new folder:

```text
runtime/state/
  README.md
  runtime-state.schema.json
  resolver.py
  current_state.json          # generated, machine-readable runtime posture
  last_error.json             # generated when bootstrap resolution fails
```

### Role of each file

| File | Role |
|------|------|
| `runtime/state/README.md` | human-readable explanation of the runtime-state layer |
| `runtime/state/runtime-state.schema.json` | schema for the canonical runtime-state object |
| `runtime/state/resolver.py` | resolves runtime identity, attachment mode, adapter, platform posture |
| `runtime/state/current_state.json` | current resolved runtime state |
| `runtime/state/last_error.json` | fail-closed error snapshot when resolution fails |

---

## 5. Canonical Runtime State Object

Recommended state fields:

```json
{
  "state_version": "0.1",
  "timestamp": "ISO-8601",
  "runtime_id": "openclaw",
  "adapter_id": "openclaw",
  "platform_family": "windows",
  "repo_root": "%CHASEOS_VAULT_ROOT%",
  "attachment_mode": "attached-personal",
  "user_binding_present": true,
  "trust_ceiling": "tier-2",
  "active_task_types": ["operator-briefing", "graph-hygiene"],
  "allowed_write_targets": [
    "07_LOGS/Operator-Briefs/",
    "07_LOGS/Agent-Activity/"
  ],
  "protected_file_behavior": "fail-closed",
  "approval_mode": "explicit",
  "external_side_effect_policy": "manifest-only",
  "bootstrap_status": "resolved"
}
```

This object should be derived from, not independent of:
- adapter manifest
- runtime bootstrap contract
- user attachment contract
- runtime profile / nav surface
- constitutional rule ceiling

---

## 6. Bootstrap Resolution Flow

Recommended resolution order:

1. Detect platform family.
2. Resolve repo root.
3. Determine target runtime (`openclaw`, `hermes`, future runtime).
4. Load adapter manifest.
5. Load runtime bootstrap file or example-derived config.
6. Discover machine-local binding locations.
7. Detect user attachment presence.
8. Resolve attachment mode:
   - `core-only`
   - `runtime-only`
   - `attached-personal`
9. Derive effective posture:
   - trust ceiling
   - write scope
   - approval mode
   - side-effect policy
10. Write `current_state.json` or fail closed into `last_error.json`.

If any required layer is missing or contradictory, resolution should stop and emit an explicit unresolved state.

---

## 7. Fail-Closed Rules

The runtime-state resolver should fail closed when:
- adapter manifest cannot be found
- runtime bootstrap contract is missing for an enforced runtime
- repo root resolution is ambiguous
- machine-local binding discovery returns contradictory results
- attachment mode cannot be derived cleanly
- effective permissions would exceed constitutional ceilings

The important point: unresolved state should be visible, not silent.

---

## 8. Relationship to AOR

The AOR should eventually consult `runtime/state/current_state.json` before workflow execution.

This enables AOR to ask:
- which runtime is active
- what posture it currently has
- whether attachment is personal or detached
- whether a requested task type is valid for this resolved runtime
- whether writeback targets match current resolved state

This makes runtime state a shared substrate for all workflows, rather than burying runtime assumptions inside each adapter lane.

---

## 9. Interface and Gateway Direction

This work **can** become the beginning of a ChaseOS-native interface or gateway.

### My recommendation
Do **not** begin with a public networked gateway first.
Begin with a **local runtime-state service surface**.

That means:
- local file-based state first
- local CLI/status inspection second
- optional localhost HTTP interface third
- broader operator gateway later if it proves necessary

### Why
Because ChaseOS still needs the internal substrate before it needs a broad always-on control plane.
If you build the port/interface first, you risk creating transport before truth.
If you build runtime-state truth first, any later interface will have something clean to expose.

---

## 10. If You Want a Port or Interface

The best Phase 9 seed would be:

### Option A — file + CLI first (recommended)
- `runtime/state/current_state.json`
- `chaseos runtime status`
- `chaseos runtime resolve`

This is the safest and most Phase 9-appropriate move.

### Option B — localhost inspection interface (next step after A)
A small local-only surface such as:
- `127.0.0.1:42610`
- read-only status endpoints at first
- no external exposure
- no side-effecting mutations in first pass

Example endpoints:
- `GET /runtime/state`
- `GET /runtime/bootstrap`
- `GET /runtime/health`
- `GET /runtime/attachments`

### Option C — ChaseOS gateway (later)
A broader operator gateway like OpenClaw's control plane should be considered only after:
- runtime state exists
- bootstrap resolution exists
- task dispatch contracts exist
- approval and audit boundaries are explicit

Otherwise the gateway becomes premature infrastructure.

---

## 11. Recommended Phase 9 Boundary

For Phase 9, I recommend building only to **Option A**, while designing cleanly for Option B.

That means:
- build the runtime-state resolver
- generate the canonical state artifact
- expose a CLI/status surface
- define the future localhost interface contract in docs
- do not yet commit to a full always-on ChaseOS gateway daemon

This gives ChaseOS:
- real runtime self-knowledge
- enforceable bootstrap posture
- a reviewable launch surface
- a natural seam for future interface work

---

## 12. Proposed Follow-On Docs / Files

If this direction is approved, next concrete implementation pass should create:
- `runtime/state/README.md`
- `runtime/state/runtime-state.schema.json`
- `runtime/state/resolver.py`
- `06_AGENTS/ChaseOS-Runtime-State-and-Gateway-Design.md` *(this file)*
- a build log for the implementation pass

Optional companion design doc:
- `06_AGENTS/ChaseOS-Local-Runtime-Interface.md`

---

## 13. Recommended Verdict

Yes, this should be treated as the beginning of a ChaseOS-native interface layer.

But the right beginning is:
- **runtime state first**
- **enforcement-aware bootstrap second**
- **local inspection interface third**
- **true gateway daemon later**

So the immediate next development priority is not "build a gateway" in the abstract.
It is:

## **Build the Runtime State Resolver and canonical runtime-state artifact as the first internal interface surface of ChaseOS.**

That is the right Phase 9 move and a clean bridge into Phase 10.

---

*Graph links: [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[OpenClaw-Adapter-Spec]] · [[Portable-Runtime-Identity-and-User-Binding]] · [[ChaseOS-MCP-Server]] · [[OpenClaw-Runtime-Profile]] · [[Hermes-Runtime-Profile]]*
