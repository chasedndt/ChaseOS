---
title: Runtime Onboarding, Registration, and Memory Bootstrap Layer
type: architecture
status: active
version: 1.0
created: 2026-04-09
updated: 2026-04-09
phase: 9
layer: AOR — Runtime Operator Intelligence
---

# Runtime Onboarding, Registration, and Memory Bootstrap Layer

> Canonical architecture doc for the ChaseOS Phase 9 feature family that detects or declares a newly used runtime/provider/surface combination, registers it through ChaseOS governance, bootstraps its runtime-specific memory and profile surfaces, binds it to policy and lifecycle state, and enables governed, inspectable runtime-specific memory growth over time.

---

## 1. What This Document Is

This document defines the architecture, pipeline, lifecycle states, guardrails, and implementation shape for the Runtime Onboarding & Brain Bootstrap feature family.

It is not a sprint spec or implementation ticket. It is the canonical design reference for this feature family in ChaseOS.

**Related documents:**
- `06_AGENTS/Agent-Memory-Architecture.md` — the five-layer memory model this feature extends
- `06_AGENTS/Agent-Identity-Ledger.md` (future) — the per-runtime identity ledger this feature seeds
- `06_AGENTS/Execution-Repair-Memory.md` (future) — the repair-memory layer this feature seeds
- `06_AGENTS/Runtime-Navigation-Map.md` — the per-runtime route overlay this feature seeds
- `06_AGENTS/Autonomous-Operator-Runtime.md` — the AOR this feature is a subsystem of
- `06_AGENTS/Feature-Fit-Register.md` — canonical phase/layer triage register

---

## 2. What This Feature Family Is

Runtime Onboarding & Brain Bootstrap is a ChaseOS Phase 9 runtime subsystem that:

1. Detects or declares a newly used runtime/provider/surface combination
2. Registers it through ChaseOS Gate governance
3. Bootstraps its runtime-specific memory and profile surfaces
4. Binds it to policy and lifecycle state
5. Enables governed, inspectable runtime-specific memory growth over time

Without this feature, adding a new model, provider, or runtime surface to ChaseOS remains an ad hoc, manually-documented action. With this feature, ChaseOS treats every new runtime as a formal entry into its governance model — with identity, policy binding, lifecycle state, and inspectable memory surfaces from the start.

---

## 3. What Problem It Solves

ChaseOS is explicitly model-agnostic and vendor-agnostic at the architecture level. Each provider and surface is supposed to bind into the same Gate model. The system already has:

- Shared Vault Map — common routing/governance layer
- Agent/Runtime-Specific Memory — per-runtime accumulated memory concept
- Agent Identity Ledger — future runtime behavior ledger concept
- Execution Repair Memory — future failure/fix learning layer concept
- Runtime Navigation Map — future per-runtime route overlay concept
- ChaseOS Gate — the execution control layer above all adapters

What is missing is the formal feature that:
- recognizes a new runtime,
- creates its managed identity inside ChaseOS,
- seeds its runtime-specific brain surfaces,
- binds it to the right policy tier,
- and lets it build governed memory over time.

Without this feature, the architecture describes per-runtime brains but the system has no onboarding/bootstrap mechanism to create them.

---

## 4. Core Pipeline

The onboarding pipeline runs when a new runtime/provider/surface combination first appears.

### Stage 1 — Declaration

The operator explicitly declares a new runtime via the `chaseos agent register` command:

```
chaseos agent register <provider> <surface>
```

**Auto-detection is not in Phase 9 scope.** A runtime does not appear in the registry without direct operator intent. This is a hard decision (see Decision Ledger: `auto-detection-deferred-explicit-declaration-only`): auto-detection violates the fail-closed posture and could create spurious registry entries. If auto-detection is ever revisited, it must require operator review before any registry write and must not fire on untrusted input.

Declaration does not grant trust. It opens the onboarding sequence.

### Stage 2 — Registration Handshake

The runtime is registered in the Runtime Registry with:
- runtime ID (stable, unique)
- provider
- surface type
- adapter/binding status
- trust ceiling (starts at Tier 4 / sandboxed)
- allowed task families (empty or minimal at registration)
- current lifecycle state (starts at `declared`)
- initial scope posture (read-only by default)

Registration aligns with Gate doctrine: adapters must be registered before they are allowed to act.

### Stage 3 — Brain Bootstrap

On first registration, ChaseOS seeds runtime-specific surfaces:
- runtime profile (identity, provider, surface, capabilities summary)
- runtime navigation seed (empty route overlay — populated over time)
- runtime identity ledger seed (blank behavioral baseline)
- runtime repair-memory seed (empty failure/fix register)
- runtime-specific routing hints (empty — populated over time)

These are seeds only. They contain no pre-granted permissions and no pre-populated memory. The purpose is to create inspectable, named surfaces for this runtime before it operates — so memory growth has governed targets, not opaque blobs.

Bootstrap writes to `runtime/aor/runtime_registry/<runtime_id>/`. This path is consistent with the `runtime/aor/` namespace that owns all AOR engine code and data. See Decision Ledger: `runtime-registry-path-under-aor`.

### Stage 4 — Policy Binding

The runtime is bound to:
- Gate policy tier
- allowed task types (from `task_type_table.yaml`)
- required-read rules
- writeback targets
- promotion rules
- audit/logging targets
- escalation boundaries

Policy binding produces a policy binding record stored in the Runtime Registry entry. The binding record is immutable once signed.

A runtime cannot execute AOR workflows until policy binding is complete.

### Stage 5 — Governed Memory Growth

As the runtime continues operating, it safely accumulates:
- preferred read orders
- common route patterns
- trusted project zones
- common weak spots
- repair patterns
- escalation points
- behavior history
- runtime-specific strengths and limitations

All memory growth writes go through ChaseOS Gate and the AOR audit trail. No runtime writes directly to canonical knowledge without promotion. No runtime memory is allowed outside inspectable, registered surfaces.

---

## 5. Runtime Registry Schema

Each entry in the Runtime Registry represents one registered runtime. Stored at `runtime/aor/runtime_registry/<runtime_id>/registry_entry.yaml`.

Required fields:

```yaml
runtime_id: <unique_stable_id>          # e.g., anthropic-claude-code-v1
provider: <provider_name>               # e.g., anthropic, openai, ollama
surface: <surface_type>                 # e.g., harness, chat-ui, local-runner
adapter_doc: <path_to_adapter_doc>      # e.g., CLAUDE.md
trust_ceiling: <tier_number>            # e.g., 2 (never auto-elevated)
lifecycle_state: <state>               # see Section 6
allowed_task_families: []              # grows via operator-approved updates
scope_posture: read-only               # default; upgrades require operator action
policy_binding_record: <path>          # immutable once written
registered: <ISO-8601-date>
last_evaluated: <ISO-8601-date>
```

---

## 6. Runtime Lifecycle States

A runtime progresses through formal lifecycle states. Transitions require explicit operator action and are recorded in the Decision Ledger.

| State | Meaning |
|-------|---------|
| `discovered` | System has observed the runtime being used but no formal action taken |
| `declared` | Operator has declared the runtime; onboarding sequence opened |
| `registered` | Runtime Registry entry created; brain bootstrap complete |
| `sandboxed` | Runtime operates with read-only, minimal-scope permissions; audit-only |
| `advisory-only` | Runtime can produce outputs but all writeback requires explicit operator approval |
| `review-required` | Pending operator evaluation before any state change |
| `execution-capable` | Runtime can execute governed AOR workflows within its role card scope |
| `suspended` | Runtime is temporarily not permitted to act; entry preserved |
| `retired` | Runtime is no longer in use; entry preserved for audit history |

No runtime auto-promotes to `execution-capable`. Every lifecycle transition requires:
- Operator-initiated action
- Decision Ledger entry
- Audit trail record

---

## 7. Brain Bootstrap Outputs

The bootstrap sequence creates the following directory structure on first registration:

```
runtime/aor/runtime_registry/<runtime_id>/
├── registry_entry.yaml          # runtime identity, lifecycle, trust ceiling
├── policy_binding.yaml          # bound task types, writeback targets, escalation rules
├── runtime_profile.md           # human-readable runtime profile summary
├── navigation_seed.yaml         # empty Runtime Navigation Map seed
├── identity_ledger_seed.yaml    # empty Agent Identity Ledger seed
├── repair_memory_seed.yaml      # empty Execution Repair Memory seed
└── audit/
    └── onboarding_trace.yaml    # onboarding pipeline execution record
```

These are seeds. They do not contain pre-populated data. They provide inspectable, governed targets for future memory growth.

---

## 8. Guardrails — Non-Negotiables

This feature must never:

- Auto-trust a new runtime
- Silently grant vault write access
- Auto-promote runtime output into canonical knowledge
- Bypass ChaseOS Gate
- Create uncontrolled node sprawl
- Create hidden private memory blobs outside inspection
- Let runtime-specific memory override shared doctrine or shared Vault Map
- Allow lifecycle state transitions without operator action and Decision Ledger record

Runtime-specific memory must remain:
- Inspectable
- Governed
- Subordinate to ChaseOS rules
- Unable to expand permissions by itself

These constraints match the existing treatment of Runtime Navigation Map as subordinate to ChaseOS governance and unable to override Gate or shared system routing.

---

## 9. Relationship to Adjacent Concepts

This feature creates and seeds the following — it does not replace them.

| Concept | Relationship |
|---------|-------------|
| **Shared Vault Map** | System-wide routing layer; unchanged by runtime onboarding; runtime memory is subordinate to it |
| **Runtime-Specific Memory** | This feature creates the seed surfaces; memory growth happens over time through governed operation |
| **Agent Identity Ledger** | This feature seeds the identity ledger for each runtime; the ledger grows through operation |
| **Execution Repair Memory** | This feature seeds the repair-memory surface; populated through AOR failure/fix cycles |
| **Runtime Navigation Map** | This feature seeds the navigation overlay; populated through real route patterns |
| **AOR Core Runtime** | This feature is a subsystem of Phase 9 AOR; registration handshake and policy binding require AOR to be operational |
| **Hermes Adapter** | Hermes is one runtime that will be onboarded through this mechanism; it does not bypass it |

---

## 10. Correct Abstraction Level

This feature is NOT:
- "Gemma support" or "Ollama support" — too low-level
- "New model added" — too low-level
- "Adapter detection helper" — scope too narrow

This IS:
- A framework/runtime feature family for ChaseOS itself
- The entry/bootstrapping layer for all per-runtime intelligence
- The missing bridge between "ChaseOS supports multiple runtimes" and "ChaseOS builds a distinct, governed brain for each runtime it uses"

---

## 11. Phase Placement

**Phase:** Phase 9 — Autonomous Operator Runtime
**Layer:** Runtime / operator intelligence layer
**Why not Phase 8:** This is not a capture/connector feature. It is AOR infrastructure.
**Why not Phase 10:** Phase 10 may expose outputs of this feature visually, but the feature itself is an AOR runtime concern.

**Dependency order:**
1. AOR core runtime scaffold (PARTIAL — Pass 1 complete)
2. Workflow Registry and Role Cards (PARTIAL — Pass 1 complete)
3. Task-Type Router (IMPLEMENTED — Pass 1 complete)
4. Shell Command Router and `chaseos agent` family (NOT BUILT — Phase 9 Runtime Shell)
5. **Runtime Onboarding Standard** (DOCS COMPLETE — this document; architecture decisions resolved 2026-04-09)
6. Runtime Registry engineering at `runtime/aor/runtime_registry/` (NOT BUILT — future pass)
7. `chaseos agent register` command implementation (NOT BUILT — Phase 9 Runtime Shell pass)
8. Brain Bootstrap Sequence engineering (NOT BUILT — future pass)
9. Agent Identity Ledger engineering (NOT BUILT — Phase 9 later)
10. Runtime Navigation Map engineering (NOT BUILT — Phase 9 later)
11. Execution Repair Memory engineering (NOT BUILT — Phase 9 later)

---

## 12. First Implementation Shape

The first implementation is explicit-declaration-only (see Decision Ledger: `auto-detection-deferred-explicit-declaration-only`):

- The operator runs `chaseos agent register <provider> <surface>` to declare a new runtime
- Bootstrap generates the registry entry at `runtime/aor/runtime_registry/<runtime_id>/` and seeds all runtime surfaces
- Trust starts at Tier 4 / sandboxed — the runtime cannot execute AOR workflows until the operator completes lifecycle progression
- Lifecycle transitions require explicit operator action and a Decision Ledger entry throughout

This keeps the first version deterministic, governed, and auditable.

Auto-detection is explicitly deferred and not on the Phase 9 roadmap. If revisited, it must pass the Feature Filter and cannot write to the registry without operator review.

---

*Runtime Onboarding, Registration, and Memory Bootstrap Layer — ChaseOS*
*Version: 1.1 | Created: 2026-04-09 | Updated: 2026-04-09 (architecture decisions resolved: runtime registry path → runtime/aor/runtime_registry/; auto-detection deferred from Phase 9; chaseos runtime register → chaseos agent register; three Decision Ledger entries created) | Phase 9 — Autonomous Operator Runtime*


*Graph links: [[Vault-Map]]*
