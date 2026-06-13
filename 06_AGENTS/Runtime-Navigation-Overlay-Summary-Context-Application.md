---
title: Runtime Navigation Overlay Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for route/trust/risk and escalation summaries
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Runtime Navigation Overlay Summary Context Application

> This document is the next concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how runtime navigation overlays should surface as typed route/trust/risk/escalation summaries inside ChaseOS.

---

## 1. Purpose

The Summary Context Layer says summaries should carry operating meaning.
This pass applies that to the Runtime Navigation Map subsystem that answers:
- where a runtime tends to go,
- which routes it trusts,
- which zones are risky,
- where escalation should happen,
- and how route intelligence differs from runtime state, workflow authority, or canonical vault structure.

This slice matters because runtime navigation outputs are easy to misread as:
- generic profile notes,
- direct authority grants,
- immutable routing doctrine,
- or simple status summaries.

But in ChaseOS, runtime navigation overlays are:
- evidence-derived,
- route-oriented,
- runtime-specific,
- subordinate to Vault Map/Gate/permission ceilings,
- and useful precisely because they are inspectable operating intelligence rather than raw doctrine.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`
- `runtime/memory/nav/hermes/nav-map.json`
- `runtime/memory/nav/openclaw/nav-map.json`
- runtime-nav related index alignment and stable-path mapping
- route/trust/risk/escalation content currently expressed across profile docs and nav-map JSON

Not included yet:
- live evidence accumulation automation beyond seeded artifacts
- graph visualization implementation
- route heatmaps or hot/cold node UI
- canonical machine-readable summary-context schema
- promotion of runtime navigation intelligence into any authority-bearing layer

---

## 3. Why Runtime Navigation Summaries Need Typed Context

Runtime navigation artifacts describe how a runtime moves through the system.
Without typed context, those artifacts can be misunderstood in dangerous ways.

Examples of ambiguity without typed context:
- Is this a preferred route or a required route?
- Is this a trusted zone or an allowed write zone?
- Is this a risk zone or a forbidden zone by constitutional rule?
- Is this escalation point advisory or mandatory?
- Is this routing map runtime-specific or system-wide truth?

The RNM architecture already distinguishes these things.
The Summary Context Layer makes those distinctions visible when route intelligence is surfaced to a human.

---

## 4. Core Summary Classes for the Runtime-Navigation Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Preferred route summary | preferred read routes / route arrays | best-known runtime path for a task class | runtime navigation workspace |
| Trusted zone summary | trusted_zones | runtime-local zone confidence summary | runtime navigation workspace |
| Safe writeback path summary | safe_write_paths / safe writeback sections | governance-compatible preferred write destinations | runtime navigation workspace / writeback panel |
| Risk zone summary | risk_zones | areas where route caution is needed | risk panel |
| Escalation point summary | escalation_points | where the runtime should stop and escalate | escalation panel |
| Navigation posture summary | runtime profile + nav-map combination | concise explanation of how this runtime tends to navigate | runtime profile inspector |
| Navigation authority summary | RNM doctrine + profile/nav artifact relationship | concise explanation that route intelligence is subordinate to deeper governance | navigation governance inspector |

---

## 5. Current Artifact Layers and Their Summary Meaning

### A. Navigation doctrine layer
These docs define what runtime navigation is allowed to mean:
- `Runtime-Navigation-Map.md`
- runtime profile docs where route posture is explained in human-readable terms

### B. Machine-readable overlay layer
These records hold the structured runtime navigation overlays:
- `runtime/memory/nav/*/nav-map.json`

### C. Runtime profile layer
These docs interpret machine-readable route data into a readable runtime-specific posture:
- preferred read routes
- trusted zones
- safe writeback paths
- risk zones
- escalation boundaries

The standalone must preserve the distinction:
**Vault Map is shared structure; RNM/profile artifacts are runtime-specific route intelligence overlays on top of that structure.**

---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `06_AGENTS/Runtime-Navigation-Map.md` | RNM doctrine and constitutional explanation | navigation authority summary reference | navigation governance inspector |
| `06_AGENTS/Hermes-Runtime-Profile.md` | Hermes-readable route posture | navigation posture summary source object | Hermes runtime navigation panel |
| `06_AGENTS/OpenClaw-Runtime-Profile.md` | OpenClaw-readable route posture | navigation posture summary source object | OpenClaw runtime navigation panel |
| `runtime/memory/nav/hermes/nav-map.json` | machine-readable Hermes route overlay | preferred/trusted/risk/escalation summary source object | Hermes route overlay panel |
| `runtime/memory/nav/openclaw/nav-map.json` | machine-readable OpenClaw route overlay | preferred/trusted/risk/escalation summary source object | OpenClaw route overlay panel |
| preferred_read_routes arrays | task-class route sequences | preferred route summary source object | route inspector |
| trusted_zones arrays | runtime-local zone confidence | trusted zone summary source object | trusted zones panel |
| safe_write_paths arrays | governance-compatible route outputs | safe writeback path summary source object | writeback panel |
| risk_zones arrays | route hazard/caution areas | risk zone summary source object | risk panel |
| escalation_points arrays | stop/escalate conditions | escalation point summary source object | escalation panel |

---

## 7. Recommended Summary Context Fields for Navigation Outputs

A preferred route summary should eventually preserve fields like:

```json
{
  "summary_class": "preferred_route_summary",
  "source_family": "runtime_navigation",
  "runtime_id": "hermes",
  "task_class": "runtime-coordination-and-discord-lane-work",
  "authority_posture": "route-intelligence-subordinate",
  "source_posture": "evidence-derived-navigation",
  "routing_surface": "runtime_navigation_workspace",
  "promotion_posture": "runtime-local-route-guidance",
  "operator_action_needed": false,
  "source_refs": [
    "runtime/memory/nav/hermes/nav-map.json",
    "06_AGENTS/Hermes-Runtime-Profile.md"
  ]
}
```

A risk/escalation summary should preserve more caution-oriented meaning:

```json
{
  "summary_class": "escalation_point_summary",
  "source_family": "runtime_navigation",
  "runtime_id": "openclaw",
  "authority_posture": "route-caution-subordinate",
  "source_posture": "evidence-derived-navigation",
  "routing_surface": "navigation_escalation_panel",
  "promotion_posture": "runtime-local-route-guidance",
  "operator_action_needed": true,
  "source_refs": [
    "runtime/memory/nav/openclaw/nav-map.json",
    "06_AGENTS/OpenClaw-Runtime-Profile.md"
  ]
}
```

Key point:
A navigation summary must make clear that it is route intelligence, not permission doctrine.

---

## 8. Routing Rules for Runtime-Navigation Summaries

### Preferred route summary
Use when the main value is helping the runtime or operator understand the best-known route for a task class.
Show in:
- runtime navigation workspace
- route inspector

### Trusted zone summary
Use when the main value is showing where a runtime navigates safely and confidently.
Show in:
- trusted zones panel
- runtime navigation workspace

### Safe writeback path summary
Use when the operator needs to know which paths have historically been safe and governance-compatible for this runtime.
Show in:
- writeback panel
- route/workspace detail panel

### Risk zone summary
Use when the main value is route caution.
Show in:
- risk panel
- runtime navigation workspace
- linked chronology/repair surfaces when available

### Escalation point summary
Use when a runtime should stop and surface uncertainty or boundary pressure.
Show in:
- escalation panel
- runtime cockpit caution strip

### Navigation posture summary
Use when the operator wants the whole route/trust/risk picture for a runtime.
Show in:
- runtime profile inspector
- runtime navigation overview panel

### Navigation authority summary
Use when the operator needs the distinction between RNM and constitutional truth explained clearly.
Show in:
- navigation governance inspector
- route-authority explainer surface

---

## 9. Governance Rules for This Slice

### Runtime navigation is not authority
A preferred route does not create permission.
A trusted zone does not override a protected-file rule.
A safe writeback path does not bypass Gate.

### Shared Vault Map still wins
If runtime navigation overlays conflict with Vault Map structural truth, the shared Vault Map wins.
The navigation overlay is runtime-local route intelligence, not structural doctrine.

### Risk and escalation summaries must remain cautionary
Risk zone and escalation summaries should be presented as route guidance and safety posture, not as decorative profile fluff.

### Route intelligence must remain evidence-derived
The summary should make clear that navigation claims come from operational evidence, not from arbitrary preference or invented policy.

### Runtime-specific meaning must remain runtime-specific
A Hermes route summary is not automatically an OpenClaw route summary, and vice versa.
The runtime identity must remain attached.

---

## 10. Recommended Standalone Views

### A. Runtime Navigation Workspace
Should show:
- preferred routes by task class
- trusted zones
- risk zones
- escalation points
- concise route posture explanation

### B. Route Inspector
Should show:
- route sequence
- task class
- why the route is preferred
- links to profile/nav-map sources

### C. Risk and Escalation Panel
Should show:
- risk zones
- escalation triggers
- operator-facing caution summaries
- links to relevant repair/history surfaces later

### D. Navigation Governance Inspector
Should show:
- RNM doctrine
- subordination to Vault Map/Gate/trust ceilings
- distinction between route intelligence and permission doctrine

---

## 11. What This Application Pass Proves

This pass proves the Summary Context Layer works for route intelligence and navigational posture, not just state, workflows, browser work, chronology, and acquisition.

Specifically, it proves ChaseOS can distinguish between:
- shared structural routing and runtime-specific overlays,
- preferred routes and required routes,
- trusted zones and authority zones,
- risk/escalation guidance and hard governance doctrine.

That makes the Summary Context Layer much more useful for future runtime navigation surfaces.

---

## 12. Recommended Next Summary-Context Applications

After this slice, the strongest next applications are:
1. approval/decision traces convergence
   - approval summaries vs chronology summaries
   - decision outcome summaries
2. runtime shell / command-surface summaries
   - runtime status/doctor summary families
   - command-contract summaries
3. agent activity / runtime activity convergence
   - runtime event summaries
   - audit vs activity summary distinctions

---

## 13. Current Verdict

Runtime navigation overlays already carry typed operating meaning.
This pass defines how ChaseOS should preserve that meaning when presenting route intelligence to a human.

So the rule for this slice is:

**A runtime-navigation summary is a runtime-specific, evidence-derived route/trust/risk/escalation artifact — not generic text, and not a permission or structural truth source.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Runtime-Navigation-Map]] · [[Runtime-Navigation-and-Browser-Governance-Standalone-Application]] · [[Hermes-Runtime-Profile]] · [[OpenClaw-Runtime-Profile]]*

*Runtime-Navigation-Overlay-Summary-Context-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
