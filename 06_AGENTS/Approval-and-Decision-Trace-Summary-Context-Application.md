---
title: Approval and Decision Trace Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for approval/review and decision-history summaries
version: 0.2
created: 2026-04-24
updated: 2026-05-13
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Approval and Decision Trace Summary Context Application

> This document is the next concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how approval/review and decision-history artifacts should behave as typed human-facing summaries inside ChaseOS.

---

## 1. Purpose

The Summary Context Layer says summaries should carry operating meaning.
This pass applies that to the approval and decision-trace subsystem that answers:
- whether something is pending review, approved, rejected, standing, or historically informative,
- whether a summary is a live approval-facing item or an immutable decision record,
- and how approval/review surfaces should stay distinct from chronology, workflow output, and canonical doctrine.

This slice matters because approval and decision artifacts are easy to flatten into one generic “history” lane.
But in ChaseOS they serve different roles:
- approval/review artifacts are about **pending or completed governance actions in context**
- decision-ledger artifacts are about **immutable standing decisions and rationale**

Those should be linked, but not collapsed into one summary family.

---

## 2. Scope of This Application Pass

Included in this pass:
- `07_LOGS/Decision-Ledger/Decision-Ledger-Index.md`
- decision-record markdown entries in `07_LOGS/Decision-Ledger/`
- `05_TEMPLATES/Decision-Ledger-Entry-Template.md`
- approval/review references already described in chronology/provenance bridge docs
- approval-center-related product references in Phase 10 docs where relevant
- decision/approval trace references in `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `runtime/aor/promotion_readiness.py`
- `07_LOGS/Promotion-Records/`

Especially relevant examples:
- `07_LOGS/Decision-Ledger/2026-04-19_fsos-browser-sub-track-parked-mcp-next.md`
- `07_LOGS/Decision-Ledger/2026-04-09_runtime-register-command-agent-family.md`
- `07_LOGS/Decision-Ledger/Decision-Ledger-Index.md`

Not included yet:
- a final decision/approval object schema shared across every source family
- dedicated pending-approval record storage beyond existing source-specific surfaces
- automatic merge logic between approval traces and chronology browser entries
- generic approval consumption, runtime dispatch, provider/browser/shell authority, protected-file writeback, or canonical mutation

The live Approval Center implementation is documented in `[[ChaseOS-Approval-Center]]`. This summary-context application defines how approval and decision summaries should preserve meaning when they are rendered; it does not turn Phase 10 Studio into a canonical truth engine or approval executor.

---

## 3. Why Approval and Decision Summaries Need Typed Context

Approval/review items and decision-ledger entries can look similar because both are governance-facing and historical.
But they answer different questions.

### Approval/review summaries answer:
- what needs review,
- what was approved or denied,
- what downstream action was allowed or blocked,
- what context or artifact the review applied to.

### Decision summaries answer:
- what standing decision was made,
- why it was made,
- what alternatives were rejected,
- what consequences follow from that standing decision.

Without typed context, a UI might blur:
- pending review vs standing policy,
- approval outcome vs decision rationale,
- live queue item vs immutable historical decision,
- chronology visibility vs governance authority.

---

## 4. Core Summary Classes for the Approval / Decision Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Approval request summary | approval-needed workflow/output context | review or approval is required before proceeding | approval center / review queue |
| Approval outcome summary | approved/denied/reviewed result | governance outcome for a specific action or artifact | approval trace panel |
| Review-needed summary | draft/proposal/shadow output needing inspection | human/operator attention required | review queue |
| Decision record summary | decision-ledger entry | immutable standing decision and rationale | decision browser / chronology detail |
| Decision consequence summary | decision record consequences section | what a standing decision enables or constrains | decision detail panel |
| Approval-vs-decision authority summary | comparison across approval trace and decision ledger | explains why a pending approval item differs from a standing decision | governance family inspector |
| Runtime-instance approval-readiness summary | readiness-gate docs + approval-linked runtime context | explains whether a runtime-specific promotion request is still blocked before activation review | approval detail / governance inspector |
| Helper-backed approval-trace summary | `runtime/aor/promotion_readiness.py` + readiness/helper docs | read-only contract-inspection summary used to explain why approval-linked promotion remains blocked | approval trace evidence panel |

---

## 5. Current Artifact Layers and Their Summary Meaning

### A. Decision-ledger layer
These artifacts are immutable standing governance records:
- decision-ledger index
- decision-record entries
- decision entry template

### B. Approval/review trace layer
These artifacts are governance-linked but action-contextual:
- approval-needed workflow outputs
- review queue references
- approval-linked chronology/provenance traces

### C. Cross-link layer
These connect approval and decision meaning without collapsing them:
- chronology/provenance trace docs
- workflow/role-card references
- rationale and consequence links from decisions into later work

### D. Runtime-instance promotion review layer
These artifacts now also matter when approval traces touch future runtime-instance promotion paths:
- caller-alignment doctrine
- runtime authority parity doctrine
- runtime-specific readiness gates
- helper-backed contract inspection surfaces
- promotion-record review history
- the shared pair-level validation surface proving bounded contract alignment across both runtime instances

The standalone must preserve the distinction:
**decision records are standing governance history; approval/review summaries are action-context governance state; helper-backed readiness evidence is read-only explanation, not authorization by itself; pair-level validation evidence is bounded contract verification, not activation authority.**

---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `07_LOGS/Decision-Ledger/Decision-Ledger-Index.md` | decision discovery/index surface | decision summary index | decision browser |
| decision-record markdown entries | immutable standing governance records | decision record summary source objects | decision detail panel |
| `05_TEMPLATES/Decision-Ledger-Entry-Template.md` | standing decision contract | decision authority summary reference | decision family inspector |
| approval-linked workflow outputs/proposal outputs | action-context review material | approval request or review-needed summary source objects | approval center / review queue |
| Phase 11 Chat approval queue handoff (`runtime/studio/approvals/*.json` plus `runtime/studio/approvals/chat-handoffs/*.json`) | Chat-originated supported proposal queued for human review after exact digest confirmation | approval request summary with `phase11_chat_action_digest`, `phase11_chat_source_digest`, duplicate/idempotency posture, and no-execution authority boundary | Approval Center / Chat proposal detail / approval trace evidence panel |
| approved/denied review outcomes | governance outcome artifacts | approval outcome summary source objects | approval trace panel |
| alternatives rejected / expected consequences sections in decision records | rationale/consequence detail | decision consequence summary objects | decision detail panel |
| provenance/chronology approval-trace references | cross-surface governance linkage | approval trace bridge references | chronology/provenance drill-through |
| `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md` + `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md` | runtime-specific blocked promotion-review posture | runtime-instance approval-readiness summary source | approval detail / governance inspector |
| `runtime/aor/promotion_readiness.py` | canonical read-only readiness/helper inspection module | helper-backed approval-trace summary source | approval trace evidence panel |
| `runtime/aor/test_runtime_instance_promotion_drafts.py` | shared pair-level runtime-instance contract validation | validation-backed approval-readiness evidence source | runtime readiness comparison drill-through / approval trace evidence panel |
| `07_LOGS/Promotion-Records/` | governed promotion review history | approval outcome / promotion-history trace source | approval trace panel / chronology drill-through |

---

## 7. Recommended Summary Context Fields for Approval and Decision Outputs

A decision record summary should eventually preserve fields like:

```json
{
  "summary_class": "decision_record_summary",
  "source_family": "decision_ledger",
  "decision_id": "runtime-register-command-agent-family",
  "artifact_family": "standing_governance",
  "authority_posture": "immutable-standing-decision",
  "source_posture": "decision-record",
  "routing_surface": "decision_browser",
  "promotion_posture": "standing",
  "operator_action_needed": false,
  "source_refs": [
    "07_LOGS/Decision-Ledger/2026-04-09_runtime-register-command-agent-family.md"
  ]
}
```

An approval/review summary should preserve different meaning:

```json
{
  "summary_class": "approval_request_summary",
  "source_family": "approval_trace",
  "artifact_family": "action_context_governance",
  "authority_posture": "review-required",
  "source_posture": "approval-linked-output",
  "routing_surface": "approval_center",
  "promotion_posture": "pending",
  "operator_action_needed": true,
  "source_refs": [
    "workflow/proposal/or/run-linked-artifact"
  ]
}
```

For Chat-originated approval queue handoffs, the approval request summary should
also carry exact handoff proof rather than just prose:

```json
{
  "summary_class": "approval_request_summary",
  "source_family": "phase11_chat",
  "artifact_family": "action_context_governance",
  "authority_posture": "pending-review-execution-blocked",
  "routing_surface": "approval_center",
  "source_digest": "phase11_chat_source_digest",
  "action_digest": "phase11_chat_action_digest",
  "dedupe_posture": "active-duplicate-returned-or-single-pending-request",
  "audit_refs": [
    "runtime/studio/approvals/<approval-id>.json",
    "runtime/studio/approvals/chat-handoffs/<action-digest>.json"
  ],
  "approval_execution_allowed": false,
  "target_write_allowed": false,
  "runtime_dispatch_allowed": false,
  "canonical_mutation_allowed": false
}
```

Key point:
A decision summary should feel standing and historical.
An approval summary should feel contextual and action-linked.
A runtime-instance approval-readiness summary should feel blocked-or-reviewable in a governed way, not like a generic runtime status badge.

---

## 8. Routing Rules for Approval vs Decision Summaries

### Approval request summary
Use when a workflow, proposal, or action needs operator review.
Show in:
- approval center
- review queue
- linked workflow detail panel

### Approval outcome summary
Use when a review/approval has completed.
Show in:
- approval trace panel
- chronology browser when governance outcome history matters

### Review-needed summary
Use when draft/proposal/shadow material needs inspection.
Show in:
- review queue
- draft/proposal detail panel

### Decision record summary
Use when the main value is a standing governance decision.
Show in:
- decision browser
- chronology detail panel
- governance inspector

### Decision consequence summary
Use when the operator needs the operational effect of a standing decision.
Show in:
- decision detail panel
- linked workflow or shell/approval surface explanation panel

### Approval-vs-decision authority summary
Use when the operator needs a clear explanation of why a pending approval item is not the same as a standing decision.
Show in:
- governance family inspector
- approval/decision explainer surface

### Runtime-instance approval-readiness summary
Use when the operator needs to understand why a promotion-oriented approval path for OpenClaw or Hermes is still blocked before activation review.
Show in:
- approval detail panel
- governance family inspector
- chronology/provenance drill-through.

### Helper-backed approval-trace summary
Use when the operator needs read-only evidence from the canonical helper module about what the draft runtime-instance promotion contract currently declares.
Show in:
- approval trace evidence panel
- approval detail explainer
- runtime-linked review detail surfaces.

---

## 9. Governance Rules for This Slice

### Decision records remain immutable and standing
They are not live queue items and should not render like pending reviews.

### Approval/review artifacts remain contextual and action-linked
They should preserve what action, artifact, or workflow they are attached to.
They are not broad standing doctrine by themselves.

### Outcome posture must stay visible
Pending, approved, denied, review-needed, and standing are different summary postures and should remain visibly distinct.

### Approval summaries do not replace decision rationale
An approval outcome can resolve a specific action.
A decision record explains enduring rationale and consequences.
Those are linked but not identical.

### Governance family distinctions must survive chronology views
If approval items and decision records appear in the same chronology browser, their family distinction must stay visible.

### Runtime-instance readiness evidence must remain distinct from decision authority
If an approval/review surface references OpenClaw or Hermes readiness state, it must preserve that equal authority parity and runtime-specific readiness are different concepts.

Readiness evidence explains whether a path is still blocked; it does not lower the constitutional status of a runtime instance.

### Helper-backed evidence remains read-only and Gate-subordinate
Approval-facing summaries derived from `runtime/aor/promotion_readiness.py` must remain explanatory.

They do not:
- approve actions,
- bypass Gate,
- or convert a draft runtime promotion lane into an active one.

---

## 10. Recommended Standalone Views

### A. Approval Center / Review Queue

Canonical cross-feature Approval Center reference:
[[ChaseOS-Approval-Center]]. This summary-context document explains approval
and decision trace semantics; the standalone Approval Center document owns the
current operator-surface source map, minimum render contract, and authority
boundary. Approval Center summaries should show request intent, touch set,
digest/provenance, state, safety rationale, audit trail, and operator review
state while keeping approval visibility separate from approval mutation,
consumption, execution, dispatch, and canonical writeback.
Should show:
- pending approval requests
- review-needed items
- affected workflow/artifact context
- concise explanation of what action is waiting

### B. Approval Trace Panel
Should show:
- request
- review context
- outcome
- downstream effect on related workflows/artifacts

### C. Decision Browser
Should show:
- decision IDs
- dates
- one-line decision statements
- standing status
- drill-down into rationale, alternatives rejected, and consequences

### D. Governance Family Inspector
Should show:
- difference between approval, review, and standing decision families
- when an item belongs in approval center vs decision browser vs chronology browser

### E. Runtime-Linked Approval Readiness Inspector
Should show:
- whether OpenClaw/Hermes promotion review remains blocked,
- workflow draft state,
- fail-closed adapter posture,
- links to readiness-gate docs and promotion-record history,
- and drill-through to shared pair-level validation evidence where the bounded contract is already machine-checked.

### F. Approval Trace Evidence Panel
Should show:
- helper-backed contract inspection results,
- runtime-specific approval linkage requirements,
- promotion-record history references,
- drill-through to the workflow/role-card substrate being explained,
- and the shared validation artifact that confirms the bounded contract remains aligned on disk.

---

## 11. What This Application Pass Proves

This pass proves the Summary Context Layer works for governance-facing artifacts without flattening them into one generic history stream.

Specifically, it proves ChaseOS can distinguish between:
- pending review and standing decision,
- approval outcome and decision rationale,
- contextual governance actions and immutable governance records,
- chronology visibility and authority meaning.

It now also proves ChaseOS can distinguish between:
- a promotion-oriented approval path that is still blocked by runtime readiness posture,
- and a standing decision or approval outcome that actually changes governed state.

That makes the Summary Context Layer much more useful for future approval-center and governance surfaces.

---

## 12. Alignment with the Runtime-Instance Promotion Thread

This slice now connects directly to the live runtime-instance promotion substrate:
- caller-alignment doctrine
- authority parity doctrine
- readiness-gate artifacts
- helper-backed contract inspection
- shared pair-level validation evidence
- promotion-record review history

That matters because approval/decision trace summaries are one of the places where operators could easily confuse:
- readiness evidence,
- validation evidence,
- approval posture,
- decision authority,
- and durable promotion outcomes.

This document now keeps those meanings separate.

## 13. Recommended Next Summary-Context Applications

After this slice, the strongest next applications are:
1. runtime shell / command-surface summaries
   - runtime status/doctor summary families
   - command-contract summaries
2. agent activity / runtime activity convergence
   - runtime event summaries
   - audit vs activity summary distinctions
3. summary taxonomy/object-model consolidation pass
   - cross-slice cleanup and canonical family consolidation

---

## 14. Current Verdict

Approval traces and decision records already carry different governance meanings.
This pass defines how ChaseOS should preserve that distinction when presenting them to a human.

So the rule for this slice is:

**An approval summary is an action-context governance artifact; a decision summary is a standing immutable governance artifact; link them, but do not collapse them into the same summary family.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Decision-Ledger-Index]] · [[Runtime-Instance-Provenance-Promotion-Caller-Alignment]] · [[Runtime-Instance-Authority-Parity]] · [[OpenClaw-Promotion-Activation-Readiness-Gate]] · [[Hermes-Promotion-Activation-Readiness-Gate]]*

*Approval-and-Decision-Trace-Summary-Context-Application.md — v0.2 | Created: 2026-04-24 | Updated: 2026-05-13 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
