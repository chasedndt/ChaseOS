---
title: Workflow Registry and Role Cards Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for workflow authority envelopes
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Workflow Registry and Role Cards Summary Context Application

**Approval Center routing:** workflow approval-center summary references should route to [[ChaseOS-Approval-Center]] for current cross-feature Approval Center semantics.

> This document is the next concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how workflow-linked summaries should carry executable identity and permission-envelope meaning inside ChaseOS.

---

## 1. Purpose

The Summary Context Layer says summaries should carry operating meaning.
This pass applies that to the subsystem that answers:
- what workflow produced an output,
- what role card bounded that workflow,
- what authority posture the output inherited,
- and whether the output should be treated as advisory, operational, evidentiary, or review-facing.

This slice matters because workflow outputs are easy to flatten into generic text such as:
- a brief,
- a report,
- a proposal,
- a draft,
- or a status summary.

But in ChaseOS, those outputs only make sense when tied back to:
- manifest identity,
- role-card boundaries,
- writeback scope,
- approval posture,
- and audit expectations.

---

## 2. Scope of This Application Pass

Included in this pass:
- workflow manifests under `runtime/workflows/registry/`
- role cards under `06_AGENTS/role-cards/`
- `runtime/workflows/registry/_schema.yaml`
- `06_AGENTS/role-cards/_schema.yaml`
- workflow-linked summary outputs such as:
  - operator briefings
  - browser research outputs
  - hygiene/proposal outputs
  - acquisition/build outputs
  - shadow-mode draft/audit outputs

Especially relevant examples:
- `runtime/workflows/registry/operator_today.yaml`
- `runtime/workflows/registry/hermes_operator_today_shadow.yaml`
- `06_AGENTS/role-cards/operator-briefing.yaml`
- `06_AGENTS/role-cards/hermes-operator-shadow.yaml`
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`

Not included yet:
- live code enforcement of summary-context schema
- UI workflow editor behavior
- role-card mutation controls
- run-launch surface behavior beyond current bounded runtime surfaces

---

## 3. Why Workflow-Linked Summaries Need Typed Context

Without typed context, a workflow output may be misread in ways that break ChaseOS meaning.

Examples:
- A shadow draft can be mistaken for a final operational brief.
- A proposal-only hygiene output can be mistaken for an approved mutation.
- A browser-research summary can be mistaken for canonical truth instead of bounded evidence.
- A scheduled briefing can be mistaken for generic prose instead of a governed workflow result.

The workflow registry and role-card layer already encode the distinctions that prevent those mistakes.
The Summary Context Layer makes those distinctions visible when the output is rendered to a human.

---

## 4. Core Summary Classes for the Workflow / Role-Card Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Workflow briefing summary | operator-briefing workflow + role card | governed operational briefing output | runtime cockpit / briefing viewer |
| Workflow evidence summary | browser/acquisition/build workflow + role card | bounded evidence or build-stage output | evidence panel / acquisition workspace |
| Workflow proposal summary | hygiene / graduation / proposal-oriented workflow | review-required proposal output | approval/proposal queue |
| Workflow shadow summary | shadow workflow + shadow role card | advisory/draft output under restricted authority | draft/review panel |
| Workflow audit summary | manifest audit expectations + run artifact outputs | audit trail and run traceability summary | chronology browser / audit panel |
| Workflow authority summary | manifest + role card pairing | concise explanation of what authority shaped the output | workflow contract inspector |

---

## 5. Current Artifact Layers and Their Summary Meaning

### A. Executable identity layer
Workflow manifests define:
- workflow ID
- task type
- trigger type
- outputs
- writeback targets
- approval rule
- audit expectations

### B. Permission-envelope layer
Role cards define:
- allowed actions
- forbidden actions
- write scope
- forbidden write zones
- escalation rules
- required/optional reads
- runtime expectations

### C. Output/artifact layer
Actual summaries and artifacts inherit posture from the manifest + role-card pairing.
That means the same markdown-looking file can carry very different meaning depending on what produced it.

The standalone must preserve the distinction:
**workflow manifest says what the run is; role card says what boundaries govern it; summary output reflects both.**

---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `runtime/workflows/registry/operator_today.yaml` | active briefing workflow manifest | workflow briefing summary source contract | briefing workflow panel |
| `06_AGENTS/role-cards/operator-briefing.yaml` | read-heavy/write-logs permission envelope | briefing authority summary source contract | role-card/authority inspector |
| `runtime/workflows/registry/hermes_operator_today_shadow.yaml` | Hermes shadow workflow manifest | workflow shadow summary source contract | shadow workflow panel |
| `06_AGENTS/role-cards/hermes-operator-shadow.yaml` | shadow-only permission envelope | shadow authority summary source contract | shadow authority inspector |
| `runtime/workflows/registry/browser_research.yaml` | browser workflow manifest | workflow evidence summary source contract | browser evidence workflow panel |
| `06_AGENTS/role-cards/browser-research.yaml` | browser boundary envelope | browser evidence authority summary source contract | browser role-card inspector |
| `runtime/workflows/registry/graph_hygiene.yaml` | proposal-oriented maintenance workflow | workflow proposal summary source contract | proposal/hygiene panel |
| `06_AGENTS/role-cards/vault-maintenance.yaml` | maintenance boundary envelope | proposal authority summary source contract | maintenance role-card inspector |
| `runtime/workflows/registry/graduate_ideas.yaml` | review-required graduation workflow | workflow proposal summary source contract | graduation proposal queue |
| `06_AGENTS/role-cards/idea-graduation.yaml` | promotion-boundary envelope | proposal authority summary source contract | graduation authority inspector |
| `runtime/workflows/registry/source_pack_builder.yaml` | build/acquisition workflow | workflow evidence/build summary source contract | acquisition/build panel |
| `06_AGENTS/role-cards/source-pack-builder.yaml` | source-pack build boundary envelope | build authority summary source contract | source-pack authority inspector |
| `runtime/workflows/registry/sbp_strikezone_digest.yaml` | scheduled briefing workflow | scheduled workflow briefing summary source contract | scheduled briefing panel |
| `06_AGENTS/role-cards/scheduled-briefing.yaml` | delivery-safe briefing envelope | scheduled authority summary source contract | scheduled role-card inspector |

---

## 7. Recommended Summary Context Fields for Workflow Outputs

A workflow-linked summary should eventually preserve fields like:

```json
{
  "summary_class": "workflow_briefing_summary",
  "source_family": "workflow_output",
  "workflow_id": "operator_today",
  "task_type": "operator-briefing",
  "role_card_id": "operator-briefing",
  "authority_posture": "read-heavy-write-logs-only",
  "source_posture": "workflow-produced",
  "routing_surface": "briefing_viewer",
  "promotion_posture": "operational-briefing",
  "operator_action_needed": false,
  "governance_refs": [
    "runtime/workflows/registry/operator_today.yaml",
    "06_AGENTS/role-cards/operator-briefing.yaml"
  ],
  "source_refs": [
    "07_LOGS/Operator-Briefs/..."
  ]
}
```

For a shadow workflow, the same shape should shift meaning explicitly:

```json
{
  "summary_class": "workflow_shadow_summary",
  "workflow_id": "hermes_operator_today_shadow",
  "role_card_id": "hermes-operator-shadow",
  "authority_posture": "shadow-log-only",
  "promotion_posture": "draft",
  "routing_surface": "draft_review_panel",
  "operator_action_needed": true
}
```

Key point:
The summary must preserve the workflow class and authority envelope together.

---

## 8. Routing Rules for Workflow-Linked Summaries

### Workflow briefing summary
Use when a bounded briefing workflow writes an operator-facing brief.
Show in:
- briefing viewer
- runtime cockpit
- chronology browser when historical inspection matters

### Workflow evidence summary
Use when a workflow produces bounded evidence or build-stage outputs.
Show in:
- evidence workspace
- acquisition/build panel
- browser governance workspace where relevant

### Workflow proposal summary
Use when outputs are explicitly proposal/review oriented.
Show in:
- proposal queue
- approval center
- review panel

### Workflow shadow summary
Use when output is intentionally non-final, draft, or advisory-only.
Show in:
- draft/review surface
- shadow runtime panel
- never as if it were final canonical output

### Workflow audit summary
Use for concise run-trace visibility.
Show in:
- chronology browser
- audit panel
- workflow contract inspector

### Workflow authority summary
Use when the operator needs a concise explanation of what authority shaped the output.
Show in:
- workflow contract panel
- role-card linkage inspector

---

## 9. Governance Rules for This Slice

### Workflow output does not outrank its manifest and role card
A summary should never be treated as broader in authority than the workflow + role-card pairing that produced it.

### Shadow posture must remain visibly shadow
A shadow-mode output must not be rendered with the same posture as a normal active execution result.
Draftness is part of the meaning.

### Proposal posture must remain visibly proposal
If a workflow produces proposals or review items, the summary must not appear as approved state.

### Role-card meaning must stay attached
A workflow name alone is not enough context.
The operator should be able to see the role-card boundary shaping the output.

### Summary remains subordinate to governance chain
If there is a conflict between a rendered summary and its manifest/role-card/doctrine source, the source documents win.

---

## 10. Recommended Standalone Views

### A. Workflow Summary Viewer
Should show:
- workflow ID
- task type
- role card
- authority posture
- promotion posture
- concise explanation of what kind of summary this is

### B. Workflow Contract Inspector
Should show:
- manifest identity
- role-card boundary
- writeback targets
- approval rule
- audit expectations
- linked summary classes commonly emitted by this workflow

### C. Shadow / Proposal Distinction Surface
Should make it impossible to confuse:
- draft/shadow outputs
- proposal/review outputs
- normal governed operational outputs

### D. Role-Card Authority Panel
Should show:
- allowed actions
- forbidden actions
- write scope
- escalation rules
- which summary postures those boundaries imply

---

## 11. What This Application Pass Proves

This pass proves the Summary Context Layer works for execution identity and permission envelopes, not just runtime state and coordination.

Specifically, it proves ChaseOS can distinguish between:
- workflow type and workflow output class,
- manifest identity and role-card authority,
- draft/shadow outputs and normal outputs,
- proposal/review material and operational briefings,
- human-readable summaries and the deeper execution/governance chain beneath them.

That makes the Summary Context Layer much more useful for actual workflow inspection.

---

## 12. Recommended Next Summary-Context Applications

After this slice, the strongest next applications are:
1. browser watchlists + evidence flows
   - monitored-source summaries
   - evidence posture summaries
2. build logs + operator briefs convergence
   - chronology summaries vs cockpit summaries
   - audit vs advisory output split
3. acquisition/source-pack outputs
   - source-pack summary classes
   - briefing-input-set summaries

---

## 13. Current Verdict

Workflow registry and role cards already carry typed operating meaning.
This pass defines how ChaseOS should preserve that meaning when a workflow produces a human-facing summary.

So the rule for this slice is:

**A workflow-linked summary is a typed output shaped by manifest identity plus role-card authority envelope — not generic text, and not a free-floating artifact.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Workflow-Registry-and-Role-Cards-Standalone-Application]] · [[Autonomous-Operator-Runtime]]*

*Workflow-Registry-and-Role-Cards-Summary-Context-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
