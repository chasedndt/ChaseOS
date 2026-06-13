---
title: Browser Watchlists and Evidence Flow Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for monitored-source and browser evidence summaries
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Browser Watchlists and Evidence Flow Summary Context Application

> This document is the next concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how monitored-source summaries, browser evidence summaries, and watchlist change summaries should behave inside ChaseOS.

---

## 1. Purpose

The Summary Context Layer says summaries should carry operating meaning.
This pass applies that to the browser-monitoring and evidence-flow subsystem that answers:
- what monitored source was checked,
- under what task class and origin boundary,
- whether the output is evidence, watchlist status, or change alert,
- and whether it belongs in a browser workspace, chronology browser, or operator-facing alert surface.

This slice matters because browser outputs are especially easy to misread as:
- generic research notes,
- canonical truth,
- ordinary status messages,
- or ungoverned monitoring chatter.

But in ChaseOS, browser evidence is bounded by:
- allowed origins,
- task classes,
- quarantine-first routing,
- evidence-not-instruction handling,
- and explicit non-canonical posture.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Browser-Autonomy-Policy.md`
- `06_AGENTS/Browser-Task-Patterns.md`
- `runtime/browser_registry/allowed_origins.yaml`
- `runtime/browser_registry/task_classes.yaml`
- `runtime/browser_registry/watchlists/Browser-Watchlists-Folder-Guide.md`
- future watchlist entry files under `runtime/browser_registry/watchlists/`
- browser-derived summaries and evidence references written to:
  - `07_LOGS/Operator-Briefs/`
  - `07_LOGS/Agent-Activity/`
  - quarantine/evidence-adjacent paths where declared

Not included yet:
- live watchlist entry instances beyond the folder guide
- final runtime-specific browser monitor UI
- canonical summary-context schema enforcement in code
- notification formatting rules for future browser alerts
- direct promotion flow from evidence summary to canonical knowledge

---

## 3. Why Browser Evidence Summaries Need Typed Context

Browser outputs are dangerous to flatten into ordinary text because they carry several distinctions that matter operationally.

Examples of ambiguity without typed context:
- Is this a routine page health check or a meaningful detected change?
- Is this a bounded evidence capture or a proposed conclusion?
- Did this come from a watchlist monitor, a selector extraction, or a one-off research sweep?
- Is the result quarantine-adjacent evidence, an operator brief, or a browser policy warning?
- Should the operator read this as truth, as evidence, or as a prompt to review source material?

The browser-governance stack already answers these questions structurally.
The Summary Context Layer makes those distinctions visible when a summary is presented to a human.

---

## 4. Core Summary Classes for the Browser / Evidence Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Watchlist change summary | watchlist task + detected change | monitored source changed in a meaningful bounded way | watchlist panel / alert surface |
| Watchlist no-change summary | watchlist task + no meaningful diff | monitored source checked successfully with no notable change | watchlist status view |
| Browser evidence summary | screenshot capture, extraction, visible text capture | bounded evidence from an approved browser task | browser evidence workspace |
| Browser health-check summary | page health/status check | known page reachable/recognizable or degraded | browser status panel |
| Browser extraction summary | known-selector or declared URL sweep output | bounded structured extraction for review or downstream use | extraction/result panel |
| Browser policy/authority summary | origin group + task class + policy docs | concise explanation of what browser boundary shaped the output | browser governance inspector |

---

## 5. Current Artifact Layers and Their Summary Meaning

### A. Governance / policy layer
These define what browser outputs are allowed to mean:
- `Browser-Autonomy-Policy.md`
- `Browser-Task-Patterns.md`

### B. Registry / contract layer
These define the machine-bounded browser surface:
- `allowed_origins.yaml`
- `task_classes.yaml`
- watchlist entry definitions

### C. Evidence / output layer
These represent what the browser work actually produced:
- change/no-change summaries
- evidence screenshots
- extracted text blocks
- operator-facing browser summaries
- audit traces

The standalone must preserve the distinction:
**policy defines browser posture, registry defines bounded execution shape, and evidence summaries reflect both without becoming canonical truth.**

---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `06_AGENTS/Browser-Autonomy-Policy.md` | governance rule set for browser work | browser policy/authority summary reference | browser governance panel |
| `06_AGENTS/Browser-Task-Patterns.md` | bounded task-pattern catalog | browser task-class summary reference | task-pattern browser |
| `runtime/browser_registry/allowed_origins.yaml` | approved origin-group registry | origin-boundary summary source contract | origin registry inspector |
| `runtime/browser_registry/task_classes.yaml` | bounded browser task-class registry | task-class summary source contract | task-class inspector |
| watchlist entry files under `runtime/browser_registry/watchlists/` | monitored source declarations | watchlist summary source contracts | watchlist manager |
| `Browser-Watchlists-Folder-Guide.md` | watchlist structure/rules guide | watchlist summary rules reference | watchlist explainer panel |
| screenshot/evidence artifact references | bounded visual evidence outputs | browser evidence summary source objects | evidence viewer |
| extracted text or structured browser outputs | bounded extraction outputs | browser extraction summary source objects | extraction/result panel |
| operator brief entries for monitored pages | human-facing browser mirror output | watchlist change/no-change summary objects | operator alert / chronology browser |
| agent activity entries for browser monitor runs | runtime audit traces | browser audit summary objects | chronology/audit panel |

---

## 7. Recommended Summary Context Fields for Browser Outputs

A browser evidence or watchlist summary should eventually preserve fields like:

```json
{
  "summary_class": "watchlist_change_summary",
  "source_family": "browser_monitoring",
  "origin_group": "public-status-and-monitoring",
  "task_class": "watchlisted_page_change_monitor",
  "watchlist_id": "example-watchlist",
  "authority_posture": "bounded-browser-evidence",
  "source_posture": "browser-derived",
  "routing_surface": "watchlist_alert_panel",
  "promotion_posture": "evidence",
  "operator_action_needed": true,
  "governance_refs": [
    "06_AGENTS/Browser-Autonomy-Policy.md",
    "runtime/browser_registry/task_classes.yaml"
  ],
  "source_refs": [
    "runtime/browser_registry/watchlists/example-watchlist.yaml",
    "07_LOGS/Operator-Briefs/..."
  ]
}
```

For routine no-change visibility, the same shape should shift meaning:

```json
{
  "summary_class": "watchlist_no_change_summary",
  "operator_action_needed": false,
  "routing_surface": "watchlist_status_view",
  "promotion_posture": "status-only"
}
```

Key point:
A browser summary must preserve its evidence posture and bounded task/origin context.

---

## 8. Routing Rules for Browser-Linked Summaries

### Watchlist change summary
Use when a declared monitored source changes meaningfully.
Show in:
- watchlist alert panel
- browser governance workspace
- chronology browser if historical trace matters

### Watchlist no-change summary
Use when the source was checked successfully but nothing important changed.
Show in:
- watchlist status view
- compact runtime/browser status surfaces

### Browser evidence summary
Use when the main value is the evidence capture itself.
Show in:
- browser evidence workspace
- screenshot/evidence viewer
- review surface if downstream interpretation is needed

### Browser health-check summary
Use when the task is bounded page availability/recognizability.
Show in:
- browser status panel
- watchlist panel for monitored status pages

### Browser extraction summary
Use when the task class is bounded extraction rather than change monitoring.
Show in:
- extraction/result panel
- downstream workflow prep view if it feeds another system surface

### Browser policy/authority summary
Use when the operator needs to know why a browser output is bounded the way it is.
Show in:
- browser governance inspector
- task-class inspector
- watchlist manager details

---

## 9. Governance Rules for This Slice

### Browser-derived summary is not canonical truth
A browser summary may be useful and well-grounded, but it remains browser-derived evidence or status output unless separately promoted through normal ChaseOS review/Gate paths.

### Origin boundary must stay attached
A useful summary should preserve which allowed-origin group and task class governed the browser work.
Without that, the output loses part of its safety meaning.

### Watchlist output must distinguish change from routine status
A no-change check should not look like an alert.
A meaningful change alert should not look like background noise.

### Quarantine/evidence posture must remain visible
If the output is evidence-like or quarantine-adjacent, the summary should not look like settled knowledge.

### Browser summaries remain subordinate to policy and registry sources
If a rendered browser summary conflicts with browser policy docs or registry entries, the policy/registry sources win.

---

## 10. Recommended Standalone Views

### A. Watchlist Monitor Panel
Should show:
- monitored source identity
- origin group
- task class
- last check time
- change vs no-change posture
- concise explanation of what happened

### B. Browser Evidence Workspace
Should show:
- screenshot or extracted evidence references
- source URL/origin grouping
- bounded task class
- review notes or operator-facing summary mirror

### C. Browser Governance Inspector
Should show:
- origin group rules
- task class bounds
- approval-required actions
- forbidden actions
- which summary postures follow from that governance

### D. Change Alert / Review Surface
Should make it impossible to confuse:
- routine status checks
- evidence captures
- meaningful detected changes
- policy-boundary warnings

---

## 11. What This Application Pass Proves

This pass proves the Summary Context Layer works for browser monitoring and evidence posture, not just workflows, runtime state, and coordination.

Specifically, it proves ChaseOS can distinguish between:
- monitored-source status and meaningful change,
- evidence capture and settled knowledge,
- browser task class and browser output class,
- human-facing browser summaries and the deeper policy/registry stack beneath them.

That makes the Summary Context Layer more useful for future browser governance and watchlist surfaces.

---

## 12. Recommended Next Summary-Context Applications

After this slice, the strongest next applications are:
1. build logs + operator briefs convergence
   - chronology summaries vs cockpit summaries
   - audit vs advisory split
2. acquisition/source-pack outputs
   - source-pack summary classes
   - briefing-input-set summaries
3. runtime navigation overlays
   - route/trust/risk summary views
   - escalation-point summaries

---

## 13. Current Verdict

Browser watchlists and evidence flows already carry typed operating meaning.
This pass defines how ChaseOS should preserve that meaning when browser work produces human-facing summaries.

So the rule for this slice is:

**A browser-linked summary is a typed, bounded evidence or monitoring artifact shaped by policy, origin group, and task class — not generic text, and not canonical truth by default.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Browser-Autonomy-Policy]] · [[Browser-Task-Patterns]] · [[ChaseOS-Studio-Architecture]]*

*Browser-Watchlists-and-Evidence-Flow-Summary-Context-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
