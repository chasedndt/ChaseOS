---
title: OpenClaw First Bounded Promotion Path
ctype: architecture
status: seeded — promotion-path contract, not active authority
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 second-wave
---

# OpenClaw First Bounded Promotion Path

This document defines the **first plausible bounded promotion-capable path** for OpenClaw after the current Claude hook lane.

It is a contract proposal, not an activation grant.
OpenClaw remains **non-promotion-capable** in current repo truth until its manifest, workflow contract, and AOR/Gate path are explicitly expanded.

---

## 1. Why This OpenClaw Contract Exists

Given current ChaseOS state:
- OpenClaw is an active live bounded runtime adapter on this machine
- OpenClaw already executes real AOR workflows through `chaseos run`
- OpenClaw already has audit/writeback behavior proven in bounded lanes
- Hermes is a peer runtime instance under the authority-parity ruling, even though its current workflow breadth differs locally

So this document exists to define the OpenClaw-side bounded promotion shape without implying that Hermes is constitutionally secondary.

---

## 2. Current Truth Boundary

OpenClaw is **not allowed** to promote canonically right now.

Current manifest truth (`runtime/policy/adapters/openclaw.yaml`):
- `may_promote_to_knowledge: "no"`
- `gate_conditions_required: false`
- `autonomous_promotion: false`
- `02_KNOWLEDGE/**` explicitly denied

Current adapter-spec truth (`06_AGENTS/OpenClaw-Adapter-Spec.md`):
- canonical knowledge promotion is forbidden in first phase
- OpenClaw may write only through bounded AOR writeback to existing approved output lanes

This document does **not** change those facts.
It defines the first future bounded shape if ChaseOS decides to expand OpenClaw later.

---

## 3. Target Shape

The first valid OpenClaw promotion-capable path should look like:

```text
OpenClaw runtime instance
  -> chaseos run [promotion-oriented workflow]
    -> AOR manifest + role card + task classification
      -> Gate promotion checks
        -> check_provenance_minimums()
          -> bounded canonical write to 02_KNOWLEDGE/
            -> audit + promotion record + index update
```

Not:

```text
OpenClaw ambient direct write -> 02_KNOWLEDGE/
```

---

## 4. Required Contract Pieces Before Activation

### A. Adapter manifest change
`runtime/policy/adapters/openclaw.yaml` would need to move from:
- `may_promote_to_knowledge: "no"`

to a bounded gated posture such as:
- `may_promote_to_knowledge: "gated"`
- `gate_conditions_required: true`
- `autonomous_promotion: false`

But only after the rest of this contract exists.

### B. Promotion-oriented workflow manifest
A new bounded AOR workflow would need to exist, for example:
- `runtime/workflows/registry/openclaw_promote_note.yaml`

This workflow should:
- target one candidate note or one bounded promotion packet at a time
- declare exact reads
- declare exact writeback targets
- declare required approval posture
- route through AOR/Gate rather than direct adapter write

### C. Role card
A dedicated role card would need to exist, for example:
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml`

It should:
- allow read of declared source artifacts, provenance refs, and target note candidate
- allow bounded write to the canonical target plus required index/update lanes only if gate checks pass
- forbid ambient repo mutation, shell expansion, connector use, and unrelated writes

### D. Promotion record lane
The first OpenClaw promotion path should not write a note silently.
It should also create durable operator/audit artifacts such as:
- promotion session log
- Gate decision trace
- index update evidence
- maybe a decision or promotion record lane if ChaseOS chooses to formalize one

### E. Test coverage
Before activation, ChaseOS should have tests covering:
- manifest + role-card validity
- OpenClaw path blocked when provenance minimums fail
- OpenClaw path blocked when promotion approval is absent
- OpenClaw path blocked outside declared target scope
- OpenClaw path allowed only when all bounded conditions are met

---

## 5. First Recommended Caller Shape

The strongest first implementation is **not** another adapter-local hook.

The stronger OpenClaw shape is:
- OpenClaw invokes a bounded AOR promotion workflow
- that workflow reaches a Gate check point
- the Gate check point calls `check_provenance_minimums()`

Why this shape is better than hook-only:
- runtime-neutral at the policy layer
- auditable through AOR stages
- easier to reuse later for Hermes or other runtimes
- keeps promotion inside declared workflow doctrine instead of adapter-local behavior only

---

## 6. Proposed OpenClaw Promotion Inputs

The first bounded promotion workflow should operate on explicit inputs like:
- `candidate_path`
- `target_path`
- `source_refs`
- `source_package_id` or `source_ids`
- `verification_status`
- `knowledge_class`
- `index_update_targets`
- `promotion_reason`
- `operator_approval_ref`

These inputs should be declared and validated rather than inferred from ambient repo state.

---

## 7. Proposed OpenClaw Promotion Outputs

The first bounded promotion path should produce:
- promoted note in `02_KNOWLEDGE/...`
- corresponding domain index update in the same governed run
- audit record in `07_LOGS/Agent-Activity/`
- build/promotion log entry in `07_LOGS/Build-Logs/`
- explicit record of whether provenance minimums passed and by which anchors

---

## 8. Gate Requirements for This Path

The first OpenClaw promotion-capable path should require all of the following:

1. existing promotion session approval / gate posture
2. bounded workflow manifest is active
3. matching promotion role card is loaded
4. target path is exactly inside declared canonical scope
5. `check_provenance_minimums()` passes
6. protected-file behavior remains enforced
7. audit record is always written regardless of outcome

---

## 9. Non-Goals

This first OpenClaw promotion path should **not** include:
- ambient direct OpenClaw writes to `02_KNOWLEDGE/`
- autonomous multi-note promotion sweeps
- silent index mutation with no promotion record
- connector-driven or Discord-driven canonical promotion
- generalized repo edit authority beyond the declared promotion lane
- Hermes alignment in the same activation step

---

## 10. Relationship to Hermes

Hermes should not be activated in parallel with this first OpenClaw promotion path.

Reason:
- Hermes is still bounded to shadow/advisory lanes
- Hermes has no current canonical promotion authority
- combining both expansions at once would blur which runtime contract was actually validated first

Recommended order:
1. Claude hook lane first — already done
2. OpenClaw bounded AOR/Gate promotion path second — this document defines the target shape
3. Hermes only after explicit control-plane review and bounded workflow expansion

---

## 11. Current Verdict

If ChaseOS chooses to expand provenance-aware canonical promotion beyond the current Claude hook lane, the OpenClaw-side acceptable path should be:
- **OpenClaw only through a bounded AOR/Gate promotion workflow**
- **with centralized provenance checks**
- **without ambient direct knowledge-write authority**
- **in parallel doctrine with the Hermes-side authority model defined elsewhere**

That preserves the constitutional model while allowing OpenClaw to become a governed promotion caller when and only when ChaseOS explicitly authorizes it, without framing Hermes as lower-authority.

### Follow-on pair-level contract
The next concrete specification layer is now:
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`

### Draft substrate artifacts now seeded
- `runtime/workflows/registry/openclaw_promote_note.yaml`
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml`
- `runtime/aor/task_type_table.yaml` (`promotion-review` row)

These are draft substrate files only.
They do not activate OpenClaw promotion authority by themselves.

### Runtime-specific readiness gates now defined
The next concrete pre-activation layer is now:
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`

Those passes formalize runtime-specific readiness gates, establish a dedicated promotion-record lane, and keep both runtimes in draft-only promotion posture until their respective readiness conditions are satisfied.

### Focused readiness validation now exists
The next pre-activation validation layer now also exists:
- `runtime/aor/test_openclaw_promotion_activation_readiness.py`
- `runtime/aor/test_openclaw_promotion_preactivation_failures.py`
- `runtime/aor/promotion_readiness.py`

That validation now proves four things at once:
- the Gate helper continues enforcing OpenClaw's explicit deny posture for `02_KNOWLEDGE/**`
- the OpenClaw draft workflow/role-card contract explicitly routes `07_LOGS/Promotion-Records/`
- approval-linkage failure posture, exact target-scope failure posture, and audit-survival expectations are all declared before any activation review
- `runtime/aor/promotion_readiness.py::collect_openclaw_preactivation_failure_signals(...)` is now the canonical helper for reading those three failure-path postures directly from live draft-contract truth
- activation readiness still remains blocked because the workflow is still `status: draft` and the adapter manifest still keeps `may_promote_to_knowledge: "no"`

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Runtime-Instance-Provenance-Promotion-Caller-Alignment]] · [[OpenClaw-Adapter-Spec]] · [[OPENCLAW]] · [[ChaseOS-Gate]] · [[Provenance-Schema-and-Trace-Idea-Implementation-Plan]] · [[Feature-Fit-Register]] · [[Vault-Map]]*