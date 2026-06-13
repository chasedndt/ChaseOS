---
title: Governed Promotion and Review Center Standalone Application
type: implementation-bridge-plan
status: seeded — standalone application of ChaseOS review, approval, and promotion surfaces
version: 0.2
created: 2026-04-24
updated: 2026-04-25
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Governed Promotion and Review Center Standalone Application

**Approval Center routing:** approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

> This document applies the markdown-to-standalone bridge to the governed review-and-promotion side of ChaseOS.
> It defines how future standalone ChaseOS should surface approvals, review-needed artifacts, graduation proposals, provenance-linked promotion checks, and decision-context governance without collapsing pending review into standing policy or browseable content into canonical truth.

---

## 1. Purpose

Earlier bridge/application slices now cover:
- runtime posture and lifecycle visibility
- workflow and role-card execution contracts
- coordination and ingress
- project/workspace surfaces
- provenance and chronology
- consolidated cockpit composition
- knowledge/domain navigation
- settings / provider-config / scaffold surfaces

What was still missing was the explicit governed review lane:

**How should future standalone ChaseOS let the operator review, approve, deny, graduate, or promote artifacts through visible governed pathways without turning approvals into generic notifications or promotion into a casual content action?**

This document answers that.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Approval-and-Decision-Trace-Summary-Context-Application.md`
- `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- `06_AGENTS/Normalization-Provenance-Contract.md`
- `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `07_LOGS/Graduation-Proposals/Graduation-Proposals-Index.md`
- `07_LOGS/Promotion-Records/`
- proposal/graduation artifacts under `07_LOGS/Graduation-Proposals/`
- decision-ledger references where standing governance context matters
- `runtime/aor/promotion_readiness.py`
- `runtime/operator_surface/approvals.py`
- `runtime/mcp/tools/approval.py`
- approval and review references already present in product/runtime docs
- `06_AGENTS/ChaseOS-Studio-Architecture.md`

Not included yet:
- final approval-center UI implementation
- final promotion object schema across all artifact families
- canonical apply/commit path for MCP approval artifacts
- automatic promotion execution backend
- final Graduation Proposal workflow automation expansion

---

## 3. Why This Slice Is Needed

Without a dedicated governed promotion/review pass, the future standalone would risk scattering governance work across:
- approval queue fragments,
- provenance drill-down panes,
- graduation proposal folders,
- chronology/history views,
- decision traces,
- and project/knowledge detail screens.

That would make ChaseOS look like it has many review-adjacent surfaces but no explicit governed review lane.

A real ChaseOS operating surface needs to answer:
- what needs human review now,
- what kind of review it is,
- what is merely a proposal versus what is promotion-facing,
- what provenance and consequences are attached,
- what standing decisions constrain the choice,
- and what downstream state would change if the operator approves.

---

## 4. Governing Rule

**The review center is a governed decision-and-promotion surface, not a generic inbox and not a shortcut around Gate.**

That means:
- approvals are typed governance actions,
- review-needed items are contextual work items,
- graduation proposals remain proposal-only until promoted through governed paths,
- provenance checks remain visible and binding,
- decision-ledger context may inform review,
- but browseability or operator convenience must not silently convert an item into canonical truth.

Short form:
- pending review is not standing policy
- proposal is not promotion
- approval visibility is not authority bypass
- canonical change still follows governed routes

---

## 5. Current Markdown- and Runtime-Era Roles Feeding the Review Center

### A. Approval/review summary layer
Provides:
- approval request summaries
- approval outcomes
- review-needed summaries
- typed distinction between pending governance and standing decisions

### B. Approval-center doctrine layer
Provides:
- approval queue concept
- approval detail expectations
- decision context and audit trace expectations
- runtime/workflow linkage for review items

### C. Provenance and chronology layer
Provides:
- source lineage and promotion chain context
- review history
- chronology of governance outcomes
- drill-through into why an item is review-sensitive

### D. Graduation proposal layer
Provides:
- proposal-only graduation outputs
- explicit idea-to-knowledge review posture
- bridge between generated/suggested content and durable knowledge candidates

### E. Decision-ledger context layer
Provides:
- standing governance decisions
- rationale and consequence context
- constraints that help explain why a review item can or cannot proceed

### F. Runtime-side approval artifact layer
Provides:
- approval request records
- pending/approved/denied state semantics
- future persistent approval-routing footholds
- concrete evidence that approval is an operating object, not just a chat message

### G. Runtime-instance readiness and helper-inspection layer
Provides:
- runtime-specific blocked-activation posture for OpenClaw and Hermes
- canonical helper-backed contract inspection before any activation review
- pair-level comparison between equal runtime-instance authority and runtime-specific readiness detail
- explicit route from review-center surfaces down to the helper/readiness substrate that explains why promotion remains blocked
- a shared machine-checked validation surface that now covers task-type cross-link alignment, approval-input requirements, escalation structure, execution controls, read structure, forbidden boundaries, allowed-action structure, and draft-doctrine posture

---

## 6. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| approval/review summary docs | Review Queue Surface | governed review queue |
| approval-center bridge/doctrine | Approval Detail Surface | review center / approval detail panel |
| graduation proposal logs | Promotion Candidate Surface | graduation / promotion review lane |
| provenance-linked trace docs | Promotion Evidence Surface | provenance and impact panel |
| decision-ledger context | Governance Context Surface | decision context sidebar |
| runtime approval artifacts | Approval State Surface | pending/approved/denied state strip |
| chronology-linked review outcomes | Review History Surface | outcome timeline / audit history panel |
| runtime-instance readiness docs + helper module | Runtime Readiness Surface | readiness comparison / helper-backed inspection panel |

---

## 7. Recommended Standalone Surfaces

### A. Governed review queue
Show:
- all pending review items
- approval class / review class
- source runtime/workflow/artifact
- urgency / age
- proposal vs promotion-facing status
- review owner / action needed posture

This should answer: **what governed review work needs operator attention now?**

### B. Approval detail panel
Show:
- requested action
- why approval is required
- affected files/surfaces/artifact families
- relevant runtime/workflow/role-card context
- clear approve / deny / defer posture

This should answer: **what exactly is being requested and why is it gated?**

### C. Promotion candidate panel
Show:
- graduation proposals
- generated/synthesized/source-derived posture
- target destination if promoted
- review rationale
- required provenance minimums / missing evidence

This should answer: **is this item mature enough for durable knowledge or another governed destination?**

### D. Provenance and impact panel
Show:
- source lineage
- transformation chain
- linked outputs or project/knowledge touchpoints
- decision consequences if approved
- traceability to prior reviews/decisions where relevant

This should answer: **what evidence and downstream effect sit behind this review choice?**

### E. Governance context sidebar
Show:
- relevant standing decisions
- role-card boundaries
- trust/protection implications
- why this is pending review rather than directly executable or directly promotable

This should answer: **what governance rules constrain this choice?**

### F. Review history timeline
Show:
- prior decisions/outcomes
- approval result chronology
- denied vs approved vs deferred items
- drill-through to immutable logs and related artifacts

This should answer: **what has already happened in this governance lane?**

### G. Runtime-instance readiness comparison panel
Show:
- OpenClaw and Hermes side-by-side blocked-activation posture
- workflow still-draft state
- adapter fail-closed posture
- promotion-record lane declared/seeded posture
- centralized provenance-gate seam presence
- links into runtime-specific readiness-gate docs and pair-spec comparison surfaces

This should answer: **what still blocks a runtime-instance promotion path from moving from draft substrate into activation review?**

### H. Helper-backed contract inspection panel
Show:
- canonical helper module route: `runtime/aor/promotion_readiness.py`
- OpenClaw helper route: `collect_openclaw_preactivation_failure_signals(...)`
- Hermes helper route: `collect_hermes_preactivation_failure_signals(...)`
- declared approval-linkage / control-plane-linkage / direct-authority / target-scope / audit-survival posture
- direct links to the draft workflow + role-card substrate being inspected
- explicit drill-through to the shared pair-level validation surface (`runtime/aor/test_runtime_instance_promotion_drafts.py`) that confirms those bounded contract structures remain aligned on disk

This should answer: **what contract signals are actually present on disk behind the review-center posture, and which parts are already reinforced by shared validation rather than prose alone?**

---

## 8. Object and Typing Requirements

These surfaces should distinguish at least:
- `approval_request_item`
- `approval_outcome_item`
- `review_needed_item`
- `promotion_candidate_item`
- `graduation_proposal_item`
- `promotion_evidence_item`
- `governance_context_item`
- `review_history_item`
- `decision_context_item`
- `runtime_readiness_item`
- `helper_inspection_item`

The point is to avoid flattening:
- a runtime approval request,
- a knowledge graduation proposal,
- a standing decision reference,
- and a provenance warning

…into one generic “notification.”

ChaseOS should treat review and promotion as typed governance state.

---

## 9. Service-Layer Boundary Rules

### A. Pending review must remain distinct from standing governance
A review item may reference a standing decision, but it is not itself standing policy.

### B. Proposal-only artifacts must remain proposal-only until governed promotion completes
Graduation proposals and similar candidate artifacts should stay visibly provisional.

### C. Provenance checks must remain close to the decision surface
The operator should not have to leave the review center entirely just to understand whether evidence is sufficient.

### D. Runtime-instance readiness must remain visible as readiness, not authority
OpenClaw and Hermes are equal-authority runtime instances under ChaseOS doctrine, but their readiness state may still differ by declared workflow, helper-surfaced failure posture, and local substrate maturity.

The review center must therefore expose readiness comparison without implying lower constitutional authority for either runtime.

### E. Approval and promotion routes must remain auditable
Every approve/deny/defer outcome should stay linked to durable chronology/audit surfaces.

### F. Review convenience must not bypass constitutional controls
A polished review center should still route governed actions through the proper ChaseOS authority chain.

### G. Governance context should explain constraints, not obscure them
The review center should make boundaries legible rather than burying them in doctrine-only files.

### H. Helper inspection must remain read-only and subordinate to Gate
Helper-backed contract inspection surfaces are for understanding current draft-contract truth.

They must not:
- execute workflows
- bypass Gate
- imply activation authorization
- silently mutate review or promotion state

---

## 10. Relationship to Earlier Bridge Slices

This slice complements earlier passes by pulling together the governed decision lane that was previously distributed across:
- the approval-center bridge slice
- approval-vs-decision summary-context work
- provenance and chronology surfaces
- knowledge/domain navigation
- consolidated cockpit attention queues

Together these now imply a future standalone where:
- the **cockpit** says what matters now,
- the **knowledge navigator** says what ChaseOS knows,
- the **settings/product-shell surfaces** say how the system is shaped,
- and the **governed review center** says what requires explicit human judgment before durable action or promotion proceeds.

---

## 11. Suggested Data Model Direction

This slice suggests ChaseOS likely needs higher-level standalone object families such as:
- `review_center_view`
- `approval_detail_view`
- `promotion_candidate_view`
- `governance_context_sidebar`
- `review_history_view`
- `promotion_readiness_summary`
- `runtime_readiness_comparison_view`
- `helper_contract_inspection_view`

Likely supporting derived records include:
- `review_queue_summary`
- `promotion_gap_summary`
- `approval_dependency_summary`
- `decision_context_summary`
- `review_outcome_summary`

These should be derived from existing logs/contracts/provenance surfaces, not invented as an opaque standalone-only truth layer.

---

## 12. What This Application Pass Proves

This pass proves the markdown-to-standalone bridge can carry the human-governed review-and-promotion lane forward as a first-class operator surface.

It clarifies:
- how approvals and review-needed items become a real review queue,
- how promotion candidates stay provisional until governed pathways complete,
- how provenance and decision context should sit near the review decision,
- how chronology and audit remain linked without replacing current action posture,
- and how ChaseOS can feel like a governed operating system rather than a pile of separate approval-adjacent panels.

---

## 13. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

It now also has a dedicated summary-context follow-on in:
- `06_AGENTS/Governed-Promotion-and-Review-Center-Summary-Context-Application.md`

That follow-on keeps review queue summaries, promotion candidate summaries, provenance-linked review warnings, review impacts, and review outcomes as separate typed operating artifacts instead of flattening them into generic review notifications.

### A. It creates a true governed review lane
A real operating system needs an explicit place where high-consequence review, approval, and promotion work is performed.
This pass defines that surface.

### B. It preserves constitutional layering between proposal, review, and canonical change
This pass keeps proposal-only artifacts, pending approval, standing decisions, and canonical promotion from collapsing into one ambiguous lane.
That is core ChaseOS discipline.

### C. It strengthens Phase 9 -> Phase 10 continuity for governance surfaces
The approval/provenance/summary-context work now has a clearer continuation into a future standalone review center rather than remaining spread across separate doctrine and trace docs.

It now also aligns more directly with the live runtime-instance promotion thread by exposing:
- caller-alignment doctrine
- authority parity doctrine
- readiness-gate comparison
- helper-backed contract inspection

### D. It improves operator legibility where judgment matters most
The operator should be able to see:
- what needs review,
- why it needs review,
- what evidence supports it,
- what rules constrain it,
- and what downstream state would change.

That is operating-system alignment, not just queue management.

---

## 14. Recommended Next Application Passes

After this slice, the strongest next continuations would be:
1. **cross-panel object model consolidation** to refine composition across cockpit, knowledge, project/workspace, settings, and review surfaces
2. **agent scorecards / runtime quality surfaces** to complement runtime browser and review lanes with reliability/performance visibility
3. **execution repair / failure recovery surfaces** so errors, blocked states, and repair memory become an explicit operator lane

---

## 15. Current Verdict

A future ChaseOS standalone should not treat review, approval, and promotion as scattered secondary details.
It should provide a clear **governed promotion / review center** where the operator can:
- inspect pending review items,
- evaluate promotion candidates,
- understand provenance and governance context,
- and approve or deny through explicit auditable pathways.

That is how the governed review side aligns with the overall ChaseOS operating system.

---

*Graph links: [[Approval-and-Decision-Trace-Summary-Context-Application]] · [[Governed-Promotion-and-Review-Center-Summary-Context-Application]] · [[Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Knowledge-Navigator-and-Domain-Browser-Standalone-Application]] · [[Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application]] · [[Markdown-to-Standalone-Bridge]] · [[ChaseOS-Studio-Architecture]]*

*Governed-Promotion-and-Review-Center-Standalone-Application.md — v0.2 | Created: 2026-04-24 | Updated: 2026-04-25 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
