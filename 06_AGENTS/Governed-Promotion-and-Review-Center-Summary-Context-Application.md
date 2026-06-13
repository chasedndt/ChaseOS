---
title: Governed Promotion and Review Center Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for governed promotion, review, and promotion-candidate summaries
version: 0.2
created: 2026-04-24
updated: 2026-04-25
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Governed Promotion and Review Center Summary Context Application

> This document is the next concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how governed review, approval, graduation, and promotion-facing artifacts should behave as typed human-facing summaries inside ChaseOS.

**Approval Center routing:** approval-center and approval-queue references in this review-summary slice should route to [[ChaseOS-Approval-Center]] for the current canonical operator-facing approval surface.

---

## 1. Purpose

The Summary Context Layer says summaries should carry operating meaning.
This pass applies that rule to the governed promotion / review center slice that answers:
- whether a summary is a pending review item, a promotion candidate, an approval-linked provenance warning, a review outcome, or a standing governance context reference,
- whether a summary is proposal-only, review-required, promotion-ready, approved, denied, deferred, or historically resolved,
- and how governed review surfaces should stay distinct from generic notifications, chronology-only views, and canonical truth itself.

This matters because review and promotion language is easy to flatten into catch-all terms such as:
- “approval,”
- “review item,”
- “proposal,”
- “promotion,”
- or “governance notification.”

But in ChaseOS these are not all the same thing.
A graduation proposal is not yet a promotion.
A pending approval is not a standing decision.
A provenance warning is not the same as a denial outcome.
A review queue item is not canonical truth just because it is visible in an operator surface.

Those should be linked, but not collapsed into one summary family.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md`
- `06_AGENTS/Approval-and-Decision-Trace-Summary-Context-Application.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `07_LOGS/Decision-Ledger/Decision-Ledger-Index.md`
- `07_LOGS/Graduation-Proposals/Graduation-Proposals-Index.md` where present
- `07_LOGS/Promotion-Records/`
- proposal/graduation artifacts under `07_LOGS/Graduation-Proposals/`
- `runtime/aor/promotion_readiness.py`
- approval and review references already present in runtime/operator docs
- `06_AGENTS/Standalone-Summary-Context-Layer.md`

Especially relevant examples:
- pending approval or review-needed items described in approval/decision docs
- graduation proposal artifacts in `07_LOGS/Graduation-Proposals/`
- standing governance references in `07_LOGS/Decision-Ledger/Decision-Ledger-Index.md`
- provenance-linked review context described in chronology/provenance bridge docs

Not included yet:
- a final machine-readable summary schema,
- the final approval-center UI implementation,
- automatic governed apply/commit backends,
- final cross-artifact promotion schema,
- a complete persistent review-state store across every surface.

---

## 3. Why Governed Promotion and Review Summaries Need Typed Context

Governed review surfaces combine several meanings that should remain separate:
- pending review work,
- proposal-only candidate state,
- evidence and provenance sufficiency,
- review outcomes,
- standing governance context,
- and promotion consequence visibility.

Without typed context, a UI or operator can blur:
- a promotion candidate vs already-promoted truth,
- a pending approval vs an immutable decision,
- a provenance deficiency vs a content-quality judgment,
- a denied item vs a deferred item,
- and a review-center queue row vs the artifact being reviewed.

That ambiguity is dangerous in ChaseOS because the review center is supposed to be a governed decision lane, not a convenience inbox.
A summary rendered there must preserve:
- what kind of governed work it is,
- what posture it is in,
- what evidence and consequences attach to it,
- and what downstream state would change if it were approved.

A future standalone should present governed review as typed governance state, not generic queue text.

---

## 4. Core Summary Classes for the Governed Promotion / Review Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Review queue summary | approval/review docs, approval-center bridge docs | pending governed work needing operator attention | governed review queue |
| Promotion candidate summary | graduation proposals, promotion-facing artifacts | proposal-only candidate for durable/governed destination | promotion candidate panel |
| Review impact summary | review-center doctrine, provenance/promotion consequences | what changes if this item is approved/denied | impact panel / approval detail |
| Approval-linked provenance summary | provenance docs, promotion evidence context | evidence sufficiency or provenance risk attached to a review item | provenance and impact panel |
| Review outcome summary | approval outcomes, review result records | approved, denied, deferred, or otherwise resolved governance result | review history timeline |
| Proposal-vs-promotion authority summary | review-center doctrine + promotion docs | explains why proposal visibility is not durable promotion | governance explainer |
| Review-vs-standing-governance summary | decision ledger + approval docs | explains why a pending review item differs from a standing immutable decision | governance context sidebar |
| Promotion-readiness summary | graduation/provenance/review minimums together | whether an item is mature enough to proceed through governed promotion | promotion readiness surface |
| Runtime-instance readiness summary | readiness-gate docs + pair-spec/runtime helper layer + shared pair-level validation | whether a runtime lane is still constitutionally blocked from activation review and why | runtime readiness comparison surface |
| Helper-inspection summary | `runtime/aor/promotion_readiness.py` + helper-linked docs + shared validation references | read-only contract-inspection summary of which failure-path/readiness signals are actually declared on disk and already reinforced by shared validation | helper-backed inspection surface |

---

## 5. Current Artifact Layers and Their Summary Meaning

### A. Governed review doctrine layer
These artifacts define the review center as an explicit governed lane:
- approval queue concept,
- promotion candidate concept,
- provenance/impact expectations,
- distinction between review and standing governance.

### B. Approval and decision layer
These artifacts define:
- pending review items,
- approval outcomes,
- standing decision references,
- and action-context governance traces.

### C. Provenance and evidence layer
These artifacts define:
- what evidence supports promotion,
- what lineage or trust caveats remain,
- what provenance minimums are missing,
- and why an item is review-sensitive.

### D. Graduation and promotion-candidate layer
These artifacts define:
- proposal-only candidate artifacts,
- draft graduation pathways,
- and bridges from generated/synthesized outputs into governed destinations.

### E. Runtime-instance readiness and helper-inspection layer
These artifacts define:
- whether OpenClaw and Hermes remain blocked by draft workflow state,
- whether fail-closed adapter posture still holds,
- whether promotion-record routing exists,
- which helper-inspected contract signals are present before any activation review,
- and which shared pair-level validation checks already reinforce those bounded contract claims on disk.

The standalone must preserve the distinction:
**review queue items, promotion candidates, provenance sufficiency, runtime-instance readiness, helper inspection, shared validation evidence, review outcomes, and standing governance context are related but different summary families.**


---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md` | standalone bridge/application for review-center product surfaces | governed review summary-context reference node | review center / promotion lane architecture panel |
| `06_AGENTS/Approval-and-Decision-Trace-Summary-Context-Application.md` | distinction between approval traces and standing decisions | review outcome summary + review-vs-standing-governance summary reference | approval detail / governance context sidebar |
| `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md` | provenance/evidence and chronology drill-through | approval-linked provenance summary + review history summary reference | provenance and impact panel / history timeline |
| `07_LOGS/Decision-Ledger/Decision-Ledger-Index.md` | immutable standing governance record index | review-vs-standing-governance summary source | governance context sidebar |
| `07_LOGS/Graduation-Proposals/Graduation-Proposals-Index.md` | discovery/index for graduation candidates | promotion candidate summary index source | promotion candidate panel |
| graduation proposal artifacts | proposal-only promotion candidates | promotion candidate summary source objects | promotion candidate panel / readiness view |
| approval request / review-needed artifacts | governed work awaiting action | review queue summary source objects | governed review queue |
| review outcomes and linked traces | resolved governance outcomes | review outcome summary source objects | review history timeline |
| provenance warnings / evidence minimums | sufficiency and risk attached to promotion or approval | approval-linked provenance summary + promotion-readiness summary source | provenance and impact panel |
| `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md` + `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md` | runtime-specific blocked-activation truth | runtime-instance readiness summary source | runtime readiness comparison surface |
| `runtime/aor/promotion_readiness.py` | canonical read-only inspection module | helper-inspection summary source | helper-backed inspection surface |
| `runtime/aor/test_runtime_instance_promotion_drafts.py` | shared pair-level runtime-instance contract validation | validation-backed runtime readiness / helper evidence source | runtime readiness comparison surface / helper-backed inspection surface |
| `07_LOGS/Promotion-Records/` | governed promotion review-history lane | review outcome / promotion-history summary source | review history timeline / readiness detail |

---

## 7. Recommended Summary Context Fields for Governed Promotion and Review Outputs

A promotion-candidate summary should eventually preserve fields like:

```json
{
  "summary_class": "promotion_candidate_summary",
  "source_family": "approval_review",
  "artifact_family": "proposal_only_candidate",
  "authority_posture": "review-required",
  "source_posture": "graduation-proposal",
  "routing_surface": "promotion_candidate_panel",
  "promotion_posture": "proposal-only",
  "operator_action_needed": true,
  "source_refs": [
    "07_LOGS/Graduation-Proposals/..."
  ]
}
```

A review-impact summary should preserve different meaning:

```json
{
  "summary_class": "review_impact_summary",
  "source_family": "approval_review",
  "artifact_family": "governed_decision_effect",
  "authority_posture": "descriptive-governance-context",
  "source_posture": "review-center-derived",
  "routing_surface": "impact_panel",
  "promotion_posture": "review-context",
  "operator_action_needed": false,
  "source_refs": [
    "06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md"
  ]
}
```

An approval-linked provenance summary should preserve evidence meaning:

```json
{
  "summary_class": "approval_linked_provenance_summary",
  "source_family": "provenance_trace",
  "artifact_family": "promotion_evidence_warning",
  "authority_posture": "evidence-bearing-not-authorizing",
  "source_posture": "provenance-linked",
  "routing_surface": "provenance_impact_panel",
  "promotion_posture": "review-relevant",
  "operator_action_needed": true,
  "source_refs": [
    "06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md"
  ]
}
```

Key point:
A promotion candidate summary should feel provisional.
A review outcome summary should feel resolved.
A provenance-linked warning should feel evidentiary.
A standing decision reference should still feel like governance context, not the queue item itself.
A runtime-instance readiness summary should feel blocked-or-ready in a governed way, not like a generic status badge.
A helper-inspection summary should feel evidentiary and read-only, not like an action surface.

---

## 8. Routing Rules for Governed Promotion and Review Summaries

### Review queue summary
Use when the operator needs to see all pending governed work requiring attention.
Show in:
- governed review queue,
- approval center,
- attention surfaces in the operator cockpit.

### Promotion candidate summary
Use when the operator needs to evaluate whether a candidate should proceed toward durable/governed destinations.
Show in:
- promotion candidate panel,
- graduation proposal browser,
- promotion readiness view.

### Review impact summary
Use when the operator needs to understand the consequences of approval, denial, or deferral.
Show in:
- impact panel,
- approval detail panel,
- review center side panels.

### Approval-linked provenance summary
Use when the operator needs evidence sufficiency, lineage, or provenance risk attached to a review item.
Show in:
- provenance and impact panel,
- promotion readiness view,
- approval detail evidence tab.

### Review outcome summary
Use when the operator needs historical or recent governance results.
Show in:
- review history timeline,
- chronology drill-through,
- approval outcome panel.

### Proposal-vs-promotion authority summary
Use when the operator needs a clear explanation that a proposal is not yet durable promoted truth.
Show in:
- governance explainer,
- promotion candidate help panel,
- advanced review guidance.

### Review-vs-standing-governance summary
Use when the operator needs to understand why a pending review item differs from a standing immutable decision.
Show in:
- governance context sidebar,
- decision context panel,
- review detail explainer.

### Promotion-readiness summary
Use when the operator needs a concise judgment on whether minimum evidence and governance posture are sufficient to proceed.
Show in:
- promotion readiness surface,
- candidate panel,
- review detail summary card.

### Runtime-instance readiness summary
Use when the operator needs a concise answer about whether OpenClaw or Hermes remains blocked from moving from draft substrate into activation review.
Show in:
- runtime readiness comparison surface,
- review detail summary card,
- governance context sidebar.

### Helper-inspection summary
Use when the operator needs a concise, read-only explanation of what the canonical helper module says is currently declared on disk for a runtime-instance promotion contract, plus what the shared validation layer already confirms about that contract.
Show in:
- helper-backed inspection surface,
- review detail evidence tab,
- runtime readiness comparison drill-through.

---

## 9. Governance Rules for This Slice

### Review visibility is not authority bypass
A review-center surface must not make it look like visibility alone grants the right to promote or mutate governed state.

### Runtime-instance readiness remains distinct from authority parity
OpenClaw and Hermes are equal-authority runtime instances under ChaseOS doctrine.
Their readiness summaries may still differ because declared workflow state, helper-inspected failure posture, and local substrate maturity differ.

The summary layer must preserve that distinction rather than implying one runtime has lower constitutional status.

### Proposal-only artifacts remain proposal-only until governed promotion completes
Graduation proposals, candidate notes, and similar artifacts must stay visibly provisional.

### Pending review remains distinct from standing governance
A queued review item may reference a standing decision, but it is not itself a standing rule.

### Provenance sufficiency remains close to the decision surface
Operators should be able to evaluate evidence without losing the distinction between evidence posture and governance outcome.

### Review outcomes remain distinct from canonical truth
An approval or denial result is a governance artifact; it is not automatically the same thing as the final durable state unless the governed promotion path actually completes.

### Review-center summaries must survive future product surfaces
The future review center, chronology, cockpit, and provenance explorer must preserve why something is a candidate, warning, queue item, outcome, or standing context reference.

### Helper inspection remains read-only and subordinate to Gate
Summaries derived from `runtime/aor/promotion_readiness.py` should preserve that these helpers inspect contract truth.

They do not:
- authorize execution,
- bypass Gate,
- or convert a draft runtime lane into an active promotion lane.

---

## 10. Recommended Standalone Views

### A. Governed Review Queue
Should show:
- pending review items,
- review class,
- proposal vs promotion-facing posture,
- urgency/age,
- linked runtime/workflow/artifact source.

### B. Promotion Candidate Panel
Should show:
- graduation proposals,
- candidate rationale,
- target destination if promoted,
- maturity and missing evidence posture.

### C. Provenance and Impact Panel
Should show:
- source lineage,
- evidence sufficiency warnings,
- downstream consequences,
- linked prior reviews or decisions.

### D. Governance Context Sidebar
Should show:
- standing decision references,
- role-card/trust implications,
- why this remains review-required,
- proposal-vs-promotion explanation.

### E. Review History Timeline
Should show:
- approved/denied/deferred history,
- immutable outcome references,
- drill-through to related decision/provenance artifacts.

### F. Promotion Readiness Surface
Should show:
- candidate maturity,
- missing requirements,
- provenance minimums,
- whether the item should remain draft/proposal-only.

### G. Runtime Readiness Comparison Surface
Should show:
- OpenClaw vs Hermes blocked-activation posture,
- workflow draft state,
- fail-closed adapter posture,
- promotion-record declared/seeded posture,
- links to readiness-gate docs and pair-spec comparison truth.

### H. Helper-Backed Inspection Surface
Should show:
- shared helper module route,
- runtime-specific helper routes,
- declared approval-linkage / control-plane-linkage / direct-authority / target-scope / audit-survival posture,
- drill-through to the workflow/role-card substrate being inspected.

---

## 11. Feature Use Case When Hermes or OpenClaw Provides Summaries

When Hermes or OpenClaw provides a governed-review-related summary, ChaseOS should not treat it as generic assistant commentary.
It should know whether the runtime is providing:
- a review queue summary,
- a promotion candidate summary,
- a review impact summary,
- an approval-linked provenance warning,
- a review outcome summary,
- a runtime-instance readiness summary,
- a helper-inspection summary,
- or a proposal-vs-promotion explainer.

That matters because similar phrasing can mean very different things.
For example:
- “this item is ready for review” is a queue artifact,
- “this could be promoted to durable knowledge” is still a candidate artifact,
- “evidence is insufficient” is a provenance-linked warning,
- “this was denied” is an outcome artifact,
- “this runtime is still blocked by draft workflow + fail-closed adapter posture” is a readiness artifact,
- “the helper confirms target-scope and audit-survival posture are declared” is a helper-inspection artifact,
- “a standing decision constrains this choice” is governance context, not the review item itself.

By typing those summaries, ChaseOS can route them correctly:
- into governed review queues,
- promotion candidate panels,
- provenance/impact panels,
- review history timelines,
- runtime readiness comparison surfaces,
- helper-backed inspection surfaces,
- or governance context sidebars.

That keeps review and promotion reporting useful without confusing visibility with authority or proposals with promoted truth.

---

## 12. Alignment with the Overall ChaseOS Operating System

This slice aligns with ChaseOS as an operating system because it preserves governed review as a first-class but bounded decision lane.

### Phase 9 -> Phase 10 continuity stays intact
Phase 9 defines approval traces, provenance constraints, graduation proposals, decision records, and governed writeback pathways.
Phase 10 can later present them through review queues, promotion candidate panels, impact views, and history timelines.
The summary layer is what keeps those governance surfaces precise.

That continuity now also includes the runtime-instance promotion substrate already live on disk:
- caller-alignment doctrine
- authority parity doctrine
- readiness-gate artifacts
- helper-backed contract inspection
- promotion-record review history

### Operator legibility improves without collapsing governance boundaries
The operator can distinguish:
- what is pending review,
- what is only a proposal,
- what evidence is missing,
- what has been resolved,
- and what remains standing governance context.

That is exactly what an OS-quality governed review surface should provide.

### Canonical truth remains downstream of governed promotion
The future standalone can make review and promotion highly legible without implying that convenience surfaces create canonical truth directly.
This preserves ChaseOS’s constitutional promotion model.

### Review state stays distinct from activity history, runtime state, and settings state
That prevents future cockpit/review surfaces from turning into a confused mixture of queue work, historical notices, config posture, and current runtime condition.

---

## 13. Relationship to Earlier Summary-Context Passes

This slice depends directly on earlier passes:
- `Approval-and-Decision-Trace-Summary-Context-Application.md` because review queue items and standing governance references must remain distinct,
- `Build-Logs-and-Operator-Briefs-Summary-Context-Application.md` because review visibility must remain distinct from chronology/history and cockpit briefings,
- `Agent-Activity-and-Runtime-Activity-Summary-Context-Application.md` because review-center artifacts must remain distinct from runtime activity history,
- `Settings-Provider-Config-and-Scaffold-Summary-Context-Application.md` because governed review posture must remain distinct from setup/configuration posture,
- `Governed-Promotion-and-Review-Center-Standalone-Application.md` because the standalone bridge already defined the future product surfaces that this summary-context pass now types.

It now also depends on the runtime-instance promotion thread artifacts:
- `Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`
- `Runtime-Instance-Authority-Parity.md`
- `Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`
- `OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `Hermes-Promotion-Activation-Readiness-Gate.md`
- `runtime/aor/promotion_readiness.py`

This is the missing governance-specific summary-context layer that keeps the review/promotion side of ChaseOS aligned with the wider operating-system model.

---

## 14. Recommended Next Follow-On Slices

After this slice, the strongest next applications are:
1. cross-panel object model consolidation
   - shared object composition rules across cockpit, chronology, runtime, settings, and review surfaces
2. runtime quality / scorecard surfaces
   - scorecard posture summaries
   - quality-history summaries
   - evidence-backed runtime-quality explainers
3. execution repair / failure recovery surfaces
   - fail-closed summaries
   - recovery-path summaries
   - repair-memory summaries

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Governed-Promotion-and-Review-Center-Standalone-Application]] · [[Approval-and-Decision-Trace-Summary-Context-Application]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Runtime-Instance-Provenance-Promotion-Caller-Alignment]] · [[Runtime-Instance-Authority-Parity]] · [[Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
