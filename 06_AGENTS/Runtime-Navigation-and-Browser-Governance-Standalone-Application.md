---
title: Runtime Navigation and Browser Governance Standalone Application
type: implementation-bridge-plan
status: seeded — first concrete application of the markdown-to-standalone bridge
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Runtime Navigation and Browser Governance Standalone Application

> This document is the first concrete application pass for `06_AGENTS/Markdown-to-Standalone-Bridge.md`.
> It translates the bridge rules into one real standalone-ready slice: runtime navigation + browser governance.

---

## 1. Purpose

The bridge doc now defines **how** markdown-era ChaseOS artifacts should map forward.
What was still missing was one example that applies those rules to a real subsystem.

This document does that for the subsystem with the clearest Phase 9 -> Phase 10 crossover:
- runtime navigation,
- runtime profiles,
- browser governance,
- browser registries/watchlists.

This is still a planning/application artifact.
It does **not** replace the markdown vault as source of truth.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`
- `06_AGENTS/Browser-Autonomy-Policy.md`
- `06_AGENTS/Browser-Task-Patterns.md`
- `runtime/memory/nav/_schema.json`
- `runtime/memory/nav/hermes/nav-map.json`
- `runtime/memory/nav/openclaw/nav-map.json`
- `runtime/browser_registry/allowed_origins.yaml`
- `runtime/browser_registry/task_classes.yaml`
- `runtime/browser_registry/watchlists/`

Not included yet:
- visual UI mockups
- final API contracts
- write-capable service endpoints
- generalized graph-edge schemas beyond this slice

---

## 3. Current Markdown-Era Roles

### A. Human-governance layer
These docs explain meaning, rules, and interpretation:
- `Runtime-Navigation-Map.md`
- runtime profile docs
- `Browser-Autonomy-Policy.md`
- `Browser-Task-Patterns.md`

### B. Machine-readable runtime layer
These artifacts hold typed state or registry structure:
- runtime nav schema + nav-map JSON records
- browser allowed-origin registry
- browser task-class registry
- browser watchlist files

### C. Current operating pattern
Today the markdown vault works because these layers stay separate:
- docs explain policy and semantics,
- machine records hold runtime-readable structure,
- logs/history provide evidence,
- indexes keep the system navigable.

The standalone must preserve that separation rather than flattening everything into one generic "note" object.

---

## 4. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| Runtime navigation doctrine | Governance / Routing Node | runtime navigation explainer + route-policy panel |
| Runtime profile docs | Runtime Profile View | per-runtime profile inspector |
| `runtime/memory/nav/*` records | Runtime Navigation Record | route/trust/risk overlay panel |
| Browser autonomy policy docs | Browser Governance Node | browser policy panel |
| Browser task-pattern docs | Task Pattern Catalog | bounded browser task-pattern browser |
| `runtime/browser_registry/*.yaml` | Browser Registry Record | registry inspector |
| `runtime/browser_registry/watchlists/*` | Browser Watchlist Record | watchlist monitor/config panel |

---

## 5. Concrete Mapping Table

| Current path | Current role | Future standalone role | Key fields / behaviors that must survive |
|---|---|---|---|
| `06_AGENTS/Runtime-Navigation-Map.md` | doctrine + architecture anchor | runtime navigation explainer node | RNM purpose, evidence-only rule, subordinate-to-governance rule, Phase 9/10 split |
| `06_AGENTS/Hermes-Runtime-Profile.md` | human-readable runtime profile | Hermes runtime profile inspector | trust posture, strengths/weak spots, route preferences, caution zones |
| `06_AGENTS/OpenClaw-Runtime-Profile.md` | human-readable runtime profile | OpenClaw runtime profile inspector | same family as Hermes; must remain comparable side-by-side |
| `runtime/memory/nav/_schema.json` | schema contract | nav schema inspector | typed fields, validation rules, record expectations |
| `runtime/memory/nav/hermes/nav-map.json` | machine nav overlay | Hermes route/risk/trust record | preferred routes, hot zones, risk zones, escalation hints |
| `runtime/memory/nav/openclaw/nav-map.json` | machine nav overlay | OpenClaw route/risk/trust record | same family as Hermes; comparable across runtimes |
| `06_AGENTS/Browser-Autonomy-Policy.md` | policy anchor | browser governance panel | allowed vs approval-required vs forbidden, quarantine-first rule, origin discipline |
| `06_AGENTS/Browser-Task-Patterns.md` | bounded task taxonomy | task-pattern catalog | approved task shapes, task-class semantics, future execution routing hints |
| `runtime/browser_registry/allowed_origins.yaml` | origin allowlist registry | allowed-origin registry inspector | host/domain bounds, approval state, scope metadata |
| `runtime/browser_registry/task_classes.yaml` | task-class registry | task-class inspector | task class IDs, constraints, allowed actions, forbidden actions |
| `runtime/browser_registry/watchlists/*` | monitor config records | watchlist manager | source identity, polling/check cadence, change-detection fields, declared output route |

---

## 6. Recommended Standalone Views

### A. Runtime Navigation Workspace
This should present one runtime at a time with side-by-side comparison available.

Recommended panels:
1. **Runtime profile summary**
   - runtime name
   - status
   - trust posture
   - declared operating strengths
2. **Route overlay**
   - preferred read paths
   - trusted zones
   - risky zones
   - escalation points
3. **Evidence linkage**
   - pointers back to build logs / agent activity / repair history
4. **Governance boundary panel**
   - explicit reminder that RNM is subordinate to Vault Map, Gate, and trust ceilings

### B. Browser Governance Workspace
Recommended panels:
1. **Policy summary**
   - allowed browser classes
   - approval-required actions
   - forbidden classes
2. **Allowed-origin inspector**
   - approved origins and scope notes
3. **Task-class inspector**
   - task pattern definitions and action bounds
4. **Watchlist manager**
   - watchlisted sources
   - bounded monitoring intent
   - expected output routes

---

## 7. Service-Layer Boundary Rules

The standalone service layer for this slice should enforce the same distinctions the markdown vault currently preserves.

### Read-only first
Initial standalone surfaces should be read-first.
They should inspect doctrine and typed records before they mutate anything.

### Docs do not become executable authority by themselves
Human-readable docs remain explanatory/governance anchors.
Machine-readable registries and records remain typed execution inputs.
The standalone should show both together without collapsing them.

### No authority expansion
Displaying runtime navigation or browser governance in a standalone surface must not silently expand runtime powers.
A UI inspector is not permission grant.
A registry browser is not approval by itself.

### Evidence stays attached
Where possible, runtime navigation claims should remain traceable to logs, audits, or repeated observed patterns.
The standalone should preserve provenance links rather than turning RNM entries into unexplained assertions.

---

## 8. Suggested Data Model Direction

This slice suggests ChaseOS likely needs at least four standalone object families:
- `governance_node`
- `runtime_profile`
- `runtime_record`
- `browser_registry_record`

And likely these specialized presentation layers:
- `runtime_navigation_view`
- `browser_governance_view`
- `watchlist_view`
- `registry_inspector`

That is important because it shows why a generic markdown renderer would be insufficient for Phase 10.
The structure is not only textual; it is policy + typed runtime state + inspectable routing.

---

## 9. What This Application Pass Proves

This pass proves the bridge can already be used operationally.
It clarifies:
- which files become nodes versus typed records,
- which docs should become explainer/policy surfaces,
- which JSON/YAML artifacts should become inspectors,
- and which subsystem boundaries the standalone must preserve.

This means the bridge is no longer only conceptual.
It now has one real worked example.

### Summary-context application
For how preferred routes, trusted zones, risk zones, safe writeback paths, and escalation points should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Runtime-Navigation-Overlay-Summary-Context-Application.md`

---

## 10. Recommended Next Application Passes

After this slice, the strongest next bridge applications would be:
1. **runtime state + bootstrap bindings**
   - `runtime/state/`
   - `runtime/bindings/`
2. **workflow registry + role cards**
   - `runtime/workflows/registry/`
   - `06_AGENTS/role-cards/`
3. **agent bus + coordination substrate**
   - `runtime/agent_bus/`
   - `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`

That sequence would move from navigation/governance into execution and coordination surfaces.

---

## 11. Current Verdict

The first standalone application slice should not be a giant generic vault viewer.
It should be a **typed operational inspector** that can show:
- runtime posture,
- route intelligence,
- browser policy,
- and machine-readable registries together.

That is the real bridge between markdown-first ChaseOS today and a future standalone Studio/native surface.

---

*Graph links: [[Markdown-to-Standalone-Bridge]] · [[Runtime-Navigation-Map]] · [[Browser-Autonomy-Policy]] · [[Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application]] · [[Hermes-Runtime-Profile]] · [[OpenClaw-Runtime-Profile]] · [[ChaseOS-Studio-Architecture]]*

*Runtime-Navigation-and-Browser-Governance-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
