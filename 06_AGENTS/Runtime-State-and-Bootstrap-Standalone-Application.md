---
title: Runtime State and Bootstrap Standalone Application
type: implementation-bridge-plan
status: seeded — second concrete application of the markdown-to-standalone bridge
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Runtime State and Bootstrap Standalone Application

> This document is the second concrete application pass for `06_AGENTS/Markdown-to-Standalone-Bridge.md`.
> It translates the bridge rules into a second real standalone-ready slice: runtime state resolution + bootstrap/user attachment.

---

## 1. Purpose

The first application pass proved that ChaseOS can map runtime navigation and browser governance into future standalone surfaces without collapsing docs, typed records, and policy boundaries.

The next strongest slice is the one that answers:
- what runtime is active,
- what attachment mode is active,
- what bootstrap evidence produced that answer,
- and how future Studio/native surfaces should inspect that posture without inventing a second truth store.

This document applies the bridge to:
- runtime state resolution,
- runtime bootstrap contracts,
- detachable user attachment contracts,
- and the future inspection surfaces that sit above them.

This is still a planning/application artifact.
It does **not** replace markdown as source of truth.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Portable-Runtime-Identity-and-User-Binding.md`
- `06_AGENTS/ChaseOS-Runtime-State-and-Gateway-Design.md`
- `runtime/bindings/Runtime-Bindings-Folder-Guide.md`
- `runtime/bindings/runtime-bootstrap.schema.json`
- `runtime/bindings/user-attachment.schema.json`
- `runtime/bindings/openclaw.bootstrap.example.json`
- `runtime/bindings/hermes.bootstrap.example.json`
- `runtime/bindings/user-attachment.example.json`
- `runtime/state/README.md`
- `runtime/state/runtime-state.schema.json`
- `runtime/state/current_state.example.json`
- `runtime/state/resolver.py`

Not included yet:
- live daemon/service implementation
- localhost status endpoint
- real machine-local private attachment storage outside the repo
- final CLI/API contract for `chaseos runtime status` or `chaseos runtime resolve`
- approval-capable mutation surfaces

---

## 3. Current Markdown-Era Roles

### A. Human-governance layer
These docs explain the meaning of runtime identity, attachment, and state resolution:
- `Portable-Runtime-Identity-and-User-Binding.md`
- `ChaseOS-Runtime-State-and-Gateway-Design.md`
- folder guides under `runtime/bindings/` and `runtime/state/`

### B. Machine-readable contract layer
These files define typed contracts for startup/bootstrap posture:
- bootstrap schema
- user attachment schema
- example bootstrap records
- example user-attachment record
- runtime-state schema

### C. Machine-readable resolution layer
These artifacts express current or derived posture:
- `runtime/state/current_state.example.json`
- future `runtime/state/current_state.json`
- future `runtime/state/last_error.json`
- `runtime/state/resolver.py`

### D. Current operating pattern
Today ChaseOS keeps these layers useful by preserving the distinction between:
- doctrine that explains what a runtime is allowed to infer,
- typed records that describe bootstrap and attachment state,
- and derived runtime-state artifacts that summarize resolved posture.

The standalone should preserve that three-layer separation rather than flattening them into generic notes or opaque config blobs.

---

## 4. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| Portable runtime identity doctrine | Governance Node | runtime identity / attachment explainer panel |
| Runtime-state design doc | Architecture / Routing Node | runtime-state design and enforcement panel |
| `runtime/bindings/*.schema.json` | Bootstrap Contract Record | bootstrap contract inspector |
| `runtime/bindings/*.example.json` | Bootstrap / Attachment Record | startup-input inspector |
| `runtime/state/runtime-state.schema.json` | Runtime State Schema Record | runtime-state schema inspector |
| `runtime/state/current_state*.json` | Runtime State Record | active runtime-state inspector |
| `runtime/state/last_error.json` | Runtime Failure Record | fail-closed startup/error panel |
| `runtime/state/resolver.py` | Resolver Implementation Artifact | implementation-backed resolver inspector / provenance panel |

---

## 5. Concrete Mapping Table

| Current path | Current role | Future standalone role | Key fields / behaviors that must survive |
|---|---|---|---|
| `06_AGENTS/Portable-Runtime-Identity-and-User-Binding.md` | architecture anchor for separating governance, runtime identity, machine bindings, and detachable user state | runtime identity explainer node | constitutional vs runtime vs machine-local vs personal attachment split |
| `06_AGENTS/ChaseOS-Runtime-State-and-Gateway-Design.md` | runtime-state design and next-step architecture | runtime-state design panel | canonical-state-object idea, fail-closed startup, file-first before daemon, local-first interface progression |
| `runtime/bindings/Runtime-Bindings-Folder-Guide.md` | folder guide for startup/attachment contracts | bootstrap layer explainer panel | startup order, GitHub-safe default, non-authority rule |
| `runtime/bindings/runtime-bootstrap.schema.json` | typed startup contract schema | bootstrap contract inspector | runtime_id, platform_family, repo_root_resolution, binding discovery, attachment modes, fail-closed rules |
| `runtime/bindings/user-attachment.schema.json` | typed detachable user contract schema | attachment contract inspector | attachment_mode, user_binding_present, private_state_locations, export safety, detachment rules |
| `runtime/bindings/openclaw.bootstrap.example.json` | seeded bootstrap example | startup-input record | runtime bootstrap evidence, candidate repo roots, machine-local binding locations |
| `runtime/bindings/hermes.bootstrap.example.json` | seeded bootstrap example | startup-input record | Hermes-specific runtime bootstrap evidence and attachment expectations |
| `runtime/bindings/user-attachment.example.json` | seeded detachable user example | attachment-input record | personal attachment posture, machine-local binding references, export-safe split |
| `runtime/state/runtime-state.schema.json` | canonical resolved-state schema | runtime-state schema inspector | runtime_id, adapter_id, attachment_mode, trust_ceiling, write targets, bootstrap_status, sources |
| `runtime/state/current_state.example.json` | seeded resolved-state example | runtime-state preview panel | what the future active runtime-state object should look like |
| `runtime/state/current_state.json` | generated current posture artifact | active runtime-state inspector | one canonical answer to current runtime posture |
| `runtime/state/last_error.json` | generated unresolved/error posture artifact | bootstrap failure panel | visible fail-closed error state instead of silent ambiguity |
| `runtime/state/resolver.py` | resolution logic foothold | resolver provenance panel | derived-from-existing-inputs rule, honest missing-manifest handling, fail-closed bias |

---

## 6. Recommended Standalone Views

### A. Runtime Attachment Workspace
This should answer, at a glance:
1. **Which runtime is active?**
2. **What attachment mode is active?**
3. **What evidence produced that answer?**
4. **What limitations follow from that posture?**

Recommended panels:
1. **Resolved posture summary**
   - runtime ID
   - adapter ID
   - platform family
   - attachment mode
   - trust ceiling
   - bootstrap status
2. **Bootstrap input inspector**
   - resolved bootstrap contract
   - discovered binding locations
   - repo-root resolution strategy
3. **User attachment inspector**
   - attached vs detached status
   - user-binding presence
   - portable export safety
   - detachment rules
4. **Derived permissions panel**
   - active task types
   - allowed write targets
   - approval mode
   - external side-effect policy

### B. Runtime Failure / Ambiguity Workspace
This should make fail-closed startup visible rather than hidden.

Recommended panels:
1. **Current resolution failure**
   - error message
   - unresolved layer
   - timestamp
2. **Conflicting/missing inputs**
   - missing manifest
   - ambiguous repo root
   - contradictory attachment signals
3. **Recommended corrective action**
   - which file or contract is missing
   - whether operator review is required

### C. Resolver Provenance Workspace
This should let the user inspect how ChaseOS derived runtime posture.

Recommended panels:
1. **Source artifact map**
   - which schema/record/doc was consulted
2. **Derivation trace**
   - which fields were sourced directly
   - which fields were inferred conservatively
3. **Integrity warnings**
   - missing adapter manifest
   - fallback-derived values
   - unresolved bindings

---

## 7. Service-Layer Boundary Rules

The standalone service layer for this slice should preserve the exact distinctions the markdown system currently preserves.

### Read-first before mutate-first
Initial standalone surfaces should inspect runtime posture and bootstrap evidence before they edit anything.

### Contracts do not become authority by themselves
Bootstrap records and attachment records are runtime inputs.
They are not autonomous permission grants.
Constitutional rules, adapter manifests, and Gate ceilings still govern actual authority.

### Runtime state is derived, not sovereign
`current_state.json` and future runtime-state views should be treated as resolved posture artifacts derived from deeper sources.
They should not become a shadow truth layer that silently overrides doctrine or manifests.

### Attachment visibility must not leak private state by default
The standalone should distinguish:
- portable/core-safe posture metadata,
- machine-local binding references,
- and private user identity or secret-bearing state.

A useful inspector must not become an accidental credential or personal-data surface.

### Error state must remain first-class
A failure to resolve posture is itself a meaningful operational state.
The standalone must surface unresolved/error posture explicitly instead of degrading into guessed defaults.

---

## 8. Suggested Data Model Direction

This slice suggests ChaseOS likely needs at least these additional standalone object families:
- `bootstrap_contract_record`
- `attachment_contract_record`
- `runtime_state_record`
- `runtime_failure_record`
- `resolver_source_record`

And likely these specialized presentation layers:
- `runtime_attachment_view`
- `runtime_state_view`
- `bootstrap_failure_view`
- `resolver_provenance_view`

That matters because it shows the future standalone cannot just render markdown text and call the job done.
This slice is structural, typed, and stateful.

---

## 9. What This Application Pass Proves

This pass proves the bridge can be applied beyond routing/policy surfaces and into startup/state surfaces.
It clarifies:
- which runtime-state files become inspectors instead of generic notes,
- which bootstrap contracts stay as typed input records,
- which state outputs are derived posture artifacts,
- and which boundaries the standalone must preserve around private attachment state.

This means the markdown-to-standalone bridge now has a second worked example that is closer to actual runtime operation.

### Summary-context application
For how runtime posture, attachment, bootstrap, and fail-closed resolution states should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Runtime-State-and-Bindings-Summary-Context-Application.md`

---

## 10. Recommended Next Application Passes

After this slice, the strongest next bridge applications would be:
1. **workflow registry + role cards**
   - `runtime/workflows/registry/`
   - `06_AGENTS/role-cards/`
2. **agent bus + coordination substrate**
   - `runtime/agent_bus/`
   - `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
3. **core/personal split + export surfaces**
   - `CORE_MANIFEST.md`
   - `core_templates/`
   - `06_AGENTS/Core-Export-Sync-Procedure.md`

That sequence would move from state/bootstrap posture into executable contracts, coordination, and cross-repo portability surfaces.

---

## 11. Current Verdict

A future ChaseOS standalone should not begin by pretending runtime posture is obvious.
It should begin with a **typed runtime-state and bootstrap inspector** that can show:
- what runtime is active,
- how startup posture was resolved,
- whether a personal user is attached,
- and where the system is unresolved or fail-closed.

That is the real bridge between markdown-first ChaseOS today and a future standalone/runtime-native operator surface.

---

*Graph links: [[Markdown-to-Standalone-Bridge]] · [[Portable-Runtime-Identity-and-User-Binding]] · [[ChaseOS-Runtime-State-and-Gateway-Design]] · [[Runtime-Navigation-and-Browser-Governance-Standalone-Application]] · [[ChaseOS-Studio-Architecture]]*

*Runtime-State-and-Bootstrap-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
