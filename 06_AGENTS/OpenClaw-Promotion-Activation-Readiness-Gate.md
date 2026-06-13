---
title: OpenClaw Promotion Activation Readiness Gate
type: architecture
status: seeded — activation-readiness contract, not authority expansion
version: 0.1
created: 2026-04-25
updated: 2026-04-25
owner: Optimus
phase: Phase 9 second-wave
---

# OpenClaw Promotion Activation Readiness Gate

This document defines the **first activation-readiness gate** for the future OpenClaw bounded promotion path.

It does **not** activate canonical promotion authority.
It answers the next open question after draft-substrate validation and engine-awareness testing:

- **Should ChaseOS maintain an explicit activation-readiness gate for OpenClaw?**
- **Yes — but as one runtime-specific gate inside a parity model, not as a primary-runtime ruling.**
- **Hermes has a mirrored readiness artifact and equal constitutional authority under `06_AGENTS/Runtime-Instance-Authority-Parity.md`.**

---

## 1. Why This Pass Exists

The runtime-instance promotion thread now has:
- bounded OpenClaw/Hermes promotion-path contracts
- draft workflow + role-card substrate for both runtimes
- focused loader/router validation
- engine-awareness proof that draft workflows remain blocked at `workflow_lookup`

That means the next honest question is no longer "can the draft files load?"
It is:

**What exact conditions must ChaseOS satisfy before OpenClaw could ever move from draft substrate into activation review — without accidentally granting authority too early?**

This document defines that gate.

---

## 2. Current Truth Boundary

OpenClaw remains **non-promotion-capable** in current repo truth.

Current live constraints still hold:
- `runtime/policy/adapters/openclaw.yaml` keeps `may_promote_to_knowledge: "no"`
- `runtime/policy/adapters/openclaw.yaml` keeps `gate_conditions_required: false`
- `runtime/workflows/registry/openclaw_promote_note.yaml` remains `status: draft`
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml` remains a draft bounded envelope only
- `02_KNOWLEDGE/**` remains explicitly denied to OpenClaw in the adapter manifest
- Gate remains the policy authority; OpenClaw remains only a possible future caller through AOR

This pass changes none of those facts.

---

## 3. Activation-Readiness Verdict

### Decision for the next continuation slice
ChaseOS should maintain a **runtime-specific OpenClaw activation-readiness gate** as documentation/specification and future-test surface.

ChaseOS should **not** in this pass:
- flip any manifest status from `draft` to `active`
- relax adapter manifest write denial for `02_KNOWLEDGE/**`
- add live runnable promotion behavior
- treat the existence of an OpenClaw gate as a claim that Hermes has lower authority

### Why this is runtime-specific rather than authority-ranked
OpenClaw currently has machine-local implementation facts that matter for its own readiness evaluation:
- it is an active bounded runtime lane on this machine
- it already executes real AOR workflows through `chaseos run`
- its activation shape can be evaluated through existing AOR/Gate seams

Those facts justify an OpenClaw-specific readiness artifact.
They do **not** justify a doctrine that Hermes is lower-authority.

### Hermes parity rule
Hermes has equal authority ceiling under `06_AGENTS/Runtime-Instance-Authority-Parity.md` and now has its own mirrored readiness artifact:
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`

---

## 4. Required Gate Categories Before Any OpenClaw Activation Pass

OpenClaw promotion activation must remain blocked until **all** of the following categories are satisfied.

### A. Adapter-manifest gate
`runtime/policy/adapters/openclaw.yaml` must not move toward a gated promotion posture until ChaseOS has test-backed proof for the rest of this stack.

Required future conditions before any manifest change:
- promotion workflow remains explicitly named and bounded
- Gate-path enforcement exists for promoted-note provenance minimums
- target scope enforcement proves `02_KNOWLEDGE/` writes stay exact and declared
- promotion record routing exists as a first-class output lane
- approval linkage is proven and auditable

Until then, adapter truth stays:
- `may_promote_to_knowledge: "no"`
- `gate_conditions_required: false`

### B. Workflow-status gate
`runtime/workflows/registry/openclaw_promote_note.yaml` must remain `status: draft` until the activation-readiness suite proves the workflow is blocked correctly when any required condition is missing.

Required future conditions before any status change:
- approval missing -> escalate
- provenance minimums fail -> escalate
- target outside declared scope -> escalate
- promotion-record target missing -> escalate
- protected-file path touched -> escalate

### C. Role-card boundary gate
`06_AGENTS/role-cards/openclaw-promotion-review.yaml` must preserve:
- bounded canonical target scope only
- no ambient repo mutation
- no shell expansion beyond declared workflow need
- no connector expansion
- no autonomous promotion

No activation pass should relax these clauses in the same change that first enables the workflow.

### D. Gate-path enforcement gate
Promotion readiness must be backed by explicit Gate-path checks, not by manifest wording alone.

The first readiness-proof seam should stay narrow and testable:
- centralized provenance minimum check via `runtime/chaseos_gate.py::check_provenance_minimums()`
- path-sensitive evaluation for `02_KNOWLEDGE/*.md`
- fail-closed behavior when frontmatter or provenance anchors are missing

If broader promotion behavior appears before this seam is tested through the OpenClaw path, the repo would be claiming a maturity level it has not yet earned.

### E. Promotion-record lane gate
OpenClaw must not gain even bounded canonical write capability without a distinct place to record what promotion happened and why.

That means a **dedicated promotion-record lane should exist before activation review begins**.

This pass therefore formalizes:
- `07_LOGS/Promotion-Records/`
- `07_LOGS/Promotion-Records/PROMOTION-RECORDS-Folder-Guide.md`
- `07_LOGS/Promotion-Records/Promotion-Records-Index.md`

The lane is seeded now as routing substrate only.
It does **not** imply active promotion workflows.

---

## 5. What Promotion Records Are For

A promotion record is the **human-readable governed writeback trace** for one bounded canonical promotion decision/path.

It should capture things like:
- candidate note path
- canonical target path
- approval reference
- Gate provenance verdict
- index update targets
- runtime instance used
- whether the promotion was applied, blocked, or escalated

### Relationship to nearby lanes
- **Agent Activity** = immutable machine/runtime audit evidence
- **Build Logs** = implementation-session explanation of what changed in the repo
- **Decision Ledger** = standing governance decisions
- **Promotion Records** = per-promotion bounded writeback trace for governed canonical mutation attempts

This distinction matters because a future standalone promotion center needs a review-history family that is neither just machine audit nor generic build commentary.

---

## 6. First Promotion-Record Contract

The first OpenClaw-ready promotion record should be treated as:
- one promotion candidate at a time
- one runtime instance at a time
- one approval context at a time
- one canonical target at a time

Recommended filename shape:

```text
07_LOGS/Promotion-Records/YYYY-MM-DD-openclaw-promotion-[slug].md
```

Recommended minimum fields:
- `runtime_adapter`
- `workflow_id`
- `candidate_path`
- `target_path`
- `approval_ref`
- `provenance_result`
- `index_update_targets`
- `outcome`
- `related_audit_record`

This lane should remain append-oriented and reviewable.
It should not become a second Decision Ledger or a second Build Logs family.

---

## 7. First Activation-Readiness Test Directions

The first focused readiness-validation foothold now exists in:
- `runtime/aor/test_openclaw_promotion_activation_readiness.py`
- `runtime/aor/promotion_readiness.py`

Current covered checks:
1. **Adapter posture still blocks knowledge writes by default**
   - OpenClaw manifest still denies ambient `02_KNOWLEDGE/**`
2. **Gate provenance seam blocks missing minimums**
   - promoted knowledge notes still fail without `verification_status`
3. **Promotion-record routing is now declared in the still-draft OpenClaw contract**
   - `openclaw_promote_note.yaml` and `openclaw-promotion-review.yaml` now both route `07_LOGS/Promotion-Records/`
4. **Activation readiness still remains blocked while activation switches stay closed**
   - the workflow remains `status: draft`
   - the adapter manifest still keeps `may_promote_to_knowledge: "no"` and `gate_conditions_required: false`

Additional readiness checks should still be added before any manifest or status flip:
5. **Promotion path fails without approval linkage**
   - no approval ref -> escalation/block
6. **Promotion path fails outside exact target scope**
   - any non-declared canonical target -> escalation/block
7. **Audit survives both success and escalation**
   - even blocked runs still emit machine audit evidence

This is intentionally still a pre-activation validation layer, not runnable promotion behavior.

---

## 8. Non-Goals of This Pass

This pass does **not**:
- activate OpenClaw promotion
- activate Hermes promotion
- change any adapter manifest authority
- change any workflow status
- add a live caller implementation
- grant `02_KNOWLEDGE/` write access

It only defines the first truthful gate ChaseOS must pass before such a change could even be reviewed.

---

## 9. Current Verdict

The strongest next continuation after draft-engine validation was **not** activation itself.
It was to define explicit runtime-specific readiness gates while separating implementation readiness from constitutional authority.

That gives ChaseOS a more honest operating-system shape:
- OpenClaw and Hermes are peer runtime instances under the same authority model
- each runtime can still have its own readiness artifact and validation path
- promotion governance now has a distinct review-history lane, not just generic logs
- future activation work now has concrete precondition lists instead of hand-wavy intent

### Immediate follow-on now completed
The prior immediate follow-on is now in place:
- focused readiness validation exists in `runtime/aor/test_openclaw_promotion_activation_readiness.py`
- focused pre-activation failure-path validation now also exists in `runtime/aor/test_openclaw_promotion_preactivation_failures.py`
- the read-only readiness helpers now exist in `runtime/aor/promotion_readiness.py`, including `collect_openclaw_preactivation_failure_signals(...)`
- `collect_openclaw_preactivation_failure_signals(...)` should now be treated as the canonical helper for approval-linkage / target-scope / audit-survival posture on the OpenClaw draft promotion contract
- the OpenClaw draft workflow/role-card contract now explicitly declares `07_LOGS/Promotion-Records/` while remaining non-runnable and non-authoritative

### Next best follow-on
That earlier Hermes-mirroring open loop is now complete.

The active comparison/cleanup follow-on is now also complete:
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md` now contains a dedicated canonical helper comparison subsection for `collect_openclaw_preactivation_failure_signals(...)` and `collect_hermes_preactivation_failure_signals(...)`

The next implementation-facing pass is now:
- continue with the next runtime-specific substrate or validation gap rather than re-deciding helper parity or helper discoverability

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[OpenClaw-First-Bounded-Promotion-Path]] · [[Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications]] · [[OpenClaw-Adapter-Spec]] · [[ChaseOS-Gate]] · [[Vault-Map]] · [[Approval-and-Decision-Trace-Summary-Context-Application]]*
