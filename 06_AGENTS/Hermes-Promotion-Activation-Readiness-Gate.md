---
title: Hermes Promotion Activation Readiness Gate
type: architecture
status: seeded — activation-readiness contract, not authority expansion
version: 0.1
created: 2026-04-25
updated: 2026-04-25
owner: Optimus
phase: Phase 9 second-wave
---

# Hermes Promotion Activation Readiness Gate

This document defines the **first activation-readiness gate** for the future Hermes bounded promotion path.

It does **not** activate canonical promotion authority.
It should now be read together with `06_AGENTS/Runtime-Instance-Authority-Parity.md`, which establishes that Hermes and OpenClaw are equal-authority runtime instances in ChaseOS doctrine.

---

## 1. Why This Pass Exists

The runtime-instance promotion thread already has:
- bounded OpenClaw/Hermes promotion-path contracts
- draft workflow + role-card substrate for both runtimes
- focused loader/router validation
- engine-awareness proof that draft workflows remain blocked at `workflow_lookup`

The parity ruling means Hermes must have an explicit readiness gate at the same doctrinal level as OpenClaw.

The correct question is therefore:

**What exact conditions must ChaseOS satisfy before Hermes could move from draft substrate into activation review — without granting authority too early and without treating Hermes as secondary?**

---

## 2. Current Truth Boundary

Hermes remains **non-promotion-capable** in current repo truth.

Current live constraints still hold:
- `runtime/policy/adapters/hermes.yaml` keeps `may_promote_to_knowledge: "no"`
- `runtime/policy/adapters/hermes.yaml` keeps `gate_conditions_required: false`
- `runtime/workflows/registry/hermes_promote_note.yaml` remains `status: draft`
- `06_AGENTS/role-cards/hermes-promotion-review.yaml` remains a draft bounded envelope only
- `02_KNOWLEDGE/**` remains explicitly denied to Hermes in the adapter manifest
- Gate remains the policy authority; Hermes remains only a possible future caller through AOR

This pass changes none of those facts.

---

## 3. Activation-Readiness Verdict

### Decision for the next continuation slice
ChaseOS should keep a **Hermes activation-readiness gate** in parallel with the OpenClaw one.

ChaseOS should **not** in this pass:
- flip any manifest status from `draft` to `active`
- relax adapter manifest write denial for `02_KNOWLEDGE/**`
- add live runnable promotion behavior
- treat Hermes parity as automatic implementation activation

### Parity interpretation
Hermes no longer inherits a "later" or "secondary" authority framing.
If Hermes activation readiness is implemented in a different order than OpenClaw, that is a sequencing fact only.

---

## 4. Required Gate Categories Before Any Hermes Activation Pass

Hermes promotion activation must remain blocked until **all** of the following categories are satisfied.

### A. Adapter-manifest gate
`runtime/policy/adapters/hermes.yaml` must not move toward a gated promotion posture until ChaseOS has test-backed proof for the rest of this stack.

Required future conditions before any manifest change:
- promotion workflow remains explicitly named and bounded
- Gate-path enforcement exists for promoted-note provenance minimums
- target scope enforcement proves `02_KNOWLEDGE/` writes stay exact and declared
- promotion record routing exists as a first-class output lane
- approval/control-plane linkage is proven and auditable

Until then, adapter truth stays:
- `may_promote_to_knowledge: "no"`
- `gate_conditions_required: false`

### B. Workflow-status gate
`runtime/workflows/registry/hermes_promote_note.yaml` must remain `status: draft` until the activation-readiness suite proves the workflow is blocked correctly when any required condition is missing.

Required future conditions before any status change:
- approval missing -> escalate
- control-plane linkage missing -> escalate
- provenance minimums fail -> escalate
- target outside declared scope -> escalate
- promotion-record target missing -> escalate
- protected-file path touched -> escalate

### C. Role-card boundary gate
`06_AGENTS/role-cards/hermes-promotion-review.yaml` must preserve:
- bounded canonical target scope only
- no ambient repo mutation
- no Discord text treated as direct write authority
- no connector expansion beyond declared governance
- no autonomous promotion

### D. Gate-path enforcement gate
Promotion readiness must be backed by explicit Gate-path checks, not by manifest wording alone.

The first readiness-proof seam should stay narrow and testable:
- centralized provenance minimum check via `runtime/chaseos_gate.py::check_provenance_minimums()`
- path-sensitive evaluation for `02_KNOWLEDGE/*.md`
- fail-closed behavior when frontmatter or provenance anchors are missing

### E. Promotion-record lane gate
Hermes must not gain even bounded canonical write capability without a distinct place to record what promotion happened and why.

That lane already exists as shared runtime-instance routing substrate:
- `07_LOGS/Promotion-Records/`
- `07_LOGS/Promotion-Records/PROMOTION-RECORDS-Folder-Guide.md`
- `07_LOGS/Promotion-Records/Promotion-Records-Index.md`

---

## 5. Immediate Follow-On

The next implementation-facing pass after this doctrinal parity update now exists as a focused Hermes-side readiness validation layer:
- `runtime/aor/test_hermes_promotion_activation_readiness.py`
- `runtime/aor/test_hermes_promotion_preactivation_failures.py`
- `runtime/aor/test_runtime_instance_promotion_drafts.py`
- `runtime/aor/promotion_readiness.py::assess_hermes_promotion_activation_readiness()`
- `runtime/aor/promotion_readiness.py::collect_hermes_preactivation_failure_signals(...)`

Hermes-specific checks now cover at least:
- fail-closed adapter posture
- control-plane approval linkage declaration
- direct-authority denial for Discord/control-plane input
- declared promotion-record routing inside the still-draft Hermes contract
- pair-level draft validation now also asserts Hermes promotion-record scope
- activation still blocked while the workflow stays draft and the adapter stays fail-closed

### Next best follow-on
The Hermes pre-activation helper is now already surfaced directly in the active readiness docs as the canonical read-only helper for control-plane-linkage / direct-authority / target-scope / audit-survival posture:
- `runtime/aor/promotion_readiness.py::collect_hermes_preactivation_failure_signals(...)`

That pair-level comparison/cleanup follow-on is now also complete:
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md` now contains a dedicated canonical helper comparison subsection for both runtime-instance helper surfaces

The next implementation-facing pass is now:
- continue with the next Hermes-side substrate or validation gap rather than re-deciding whether this helper should be surfaced

---

## 6. Current Verdict

Hermes now has an explicit readiness-gate artifact at the same doctrinal level as OpenClaw.

That means ChaseOS can describe:
- equal authority model
- separate runtime-specific readiness gates
- no automatic live activation for either runtime

without treating Hermes as secondary.

---

*Graph links: [[Hermes-Runtime-Profile]] · [[Runtime-Instance-Authority-Parity]] · [[Hermes-First-Bounded-Promotion-Path]] · [[Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications]] · [[HERMES]] · [[ChaseOS-Gate]] · [[Vault-Map]]*
