---
title: Hermes First Bounded Promotion Path
ctype: architecture
status: seeded — promotion-path contract, not active authority
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 second-wave
---

# Hermes First Bounded Promotion Path

This document defines the **first plausible bounded promotion-capable path** for Hermes after the current Claude hook lane.

It is a contract proposal, not an activation grant.
Hermes remains **non-promotion-capable** in current repo truth until its manifest, workflow contract, and AOR/Gate path are explicitly expanded.

---

## 1. Why Hermes Needs Its Own Contract

Hermes needs an explicit contract shape because ChaseOS now treats Hermes and OpenClaw as peer runtime instances under `06_AGENTS/Runtime-Instance-Authority-Parity.md`.

Given current ChaseOS state:
- Hermes is an active bounded Discord runtime lane
- Hermes already executes a declared bounded workflow (`hermes_operator_today_shadow`)
- Hermes already produces audit/draft outputs through governed paths
- Hermes is explicitly blocked from canonical promotion today

So the right move is not to activate Hermes promotion now.
The right move is to define the first acceptable future shape without treating Hermes as a lower-authority runtime.

---

## 2. Current Truth Boundary

Hermes is **not allowed** to promote canonically right now.

Current manifest truth (`runtime/policy/adapters/hermes.yaml`):
- `may_promote_to_knowledge: "no"`
- `gate_conditions_required: false`
- `autonomous_promotion: false`
- `02_KNOWLEDGE/**` explicitly denied

Current adapter-spec truth (`06_AGENTS/Hermes-Adapter-Spec.md`):
- canonical promotion requires Gate with human review
- current local implementation is narrower than the maximum spec
- active bounded lane is still advisory/shadow oriented

This document does **not** change those facts.
It defines the first future bounded Hermes promotion shape under the same constitutional authority model that now applies to both Hermes and OpenClaw.

---

## 3. Target Shape

The first valid Hermes promotion-capable path should look like:

```text
Hermes runtime instance
  -> declared bounded workflow request
    -> AOR manifest + role card + task classification
      -> approval envelope / control-plane validation
        -> Gate promotion checks
          -> check_provenance_minimums()
            -> bounded canonical write to 02_KNOWLEDGE/
              -> audit + promotion record + index update
```

Not:

```text
Discord message -> direct Hermes write -> 02_KNOWLEDGE/
```

And not:

```text
Hermes ambient direct write -> 02_KNOWLEDGE/
```

---

## 4. Required Contract Pieces Before Activation

### A. Adapter manifest change
`runtime/policy/adapters/hermes.yaml` would need to move from:
- `may_promote_to_knowledge: "no"`

to a bounded gated posture such as:
- `may_promote_to_knowledge: "gated"`
- `gate_conditions_required: true`
- `autonomous_promotion: false`

But only after the rest of this contract exists.

### B. Promotion-oriented workflow manifest
A new bounded AOR workflow would need to exist, for example:
- `runtime/workflows/registry/hermes_promote_note.yaml`

This workflow should:
- target one candidate note or one bounded promotion packet at a time
- declare exact reads
- declare exact writeback targets
- declare required approval posture
- route through AOR/Gate rather than direct adapter write
- remain consistent with Discord/control-plane governance rules

### C. Role card
A dedicated role card would need to exist, for example:
- `06_AGENTS/role-cards/hermes-promotion-review.yaml`

It should:
- allow read of declared source artifacts, provenance refs, and target note candidate
- allow bounded write to the canonical target plus required index/update lanes only if gate checks pass
- forbid shell expansion, undeclared connector use, unrelated writes, and ambient vault mutation

### D. Promotion record lane
The first Hermes promotion path should not write a note silently.
It should also create durable operator/audit artifacts such as:
- promotion session log
- Gate decision trace
- approval-envelope linkage
- index update evidence
- maybe a dedicated promotion record lane if ChaseOS formalizes one

### E. Test coverage
Before activation, ChaseOS should have tests covering:
- manifest + role-card validity
- Hermes path blocked when provenance minimums fail
- Hermes path blocked when approval envelope is absent or invalid
- Hermes path blocked outside declared canonical scope
- Hermes path blocked when control-plane authority is insufficient
- Hermes path allowed only when all bounded conditions are met

---

## 5. First Recommended Caller Shape

The strongest first Hermes implementation is **not** a Discord-level shortcut and **not** a generic gateway-triggered write.

The stronger Hermes shape is:
- Hermes receives a bounded request through the declared control-plane path
- a promotion-oriented AOR workflow is invoked
- that workflow reaches a Gate check point
- the Gate check point calls `check_provenance_minimums()`

Why this shape is better:
- keeps Discord/gateway interaction as control-plane visibility and bounded approval, not direct authority
- keeps policy centralized
- preserves AOR auditability
- prevents the Hermes lane from becoming a shadow governance system

---

## 6. Proposed Hermes Promotion Inputs

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
- `control_plane_request_ref`

These inputs should be declared and validated rather than inferred from ambient repo state or Discord message text alone.

---

## 7. Proposed Hermes Promotion Outputs

The first bounded promotion path should produce:
- promoted note in `02_KNOWLEDGE/...`
- corresponding domain index update in the same governed run
- audit record in `07_LOGS/Agent-Activity/`
- build/promotion log entry in `07_LOGS/Build-Logs/`
- explicit record of whether provenance minimums passed and by which anchors
- approval/control-plane linkage showing how the run was authorized

---

## 8. Gate and Control-Plane Requirements for This Path

The first Hermes promotion-capable path should require all of the following:

1. explicit approval/control-plane posture for the run
2. bounded workflow manifest is active
3. matching promotion role card is loaded
4. target path is exactly inside declared canonical scope
5. `check_provenance_minimums()` passes
6. protected-file behavior remains enforced
7. Discord/gateway input remains data/control-plane context, not direct write authority
8. audit record is always written regardless of outcome

---

## 9. Non-Goals

This first Hermes promotion path should **not** include:
- direct Discord-driven canonical mutation
- ambient Hermes writes to `02_KNOWLEDGE/`
- shell-enabled promotion behavior
- connector-expanded promotion behavior beyond declared governance
- autonomous batch promotion sweeps
- multi-repo canonical mutation
- simultaneous OpenClaw + Hermes promotion activation in the same pass

---

## 10. Relationship to OpenClaw

OpenClaw and Hermes are peer runtime instances under `06_AGENTS/Runtime-Instance-Authority-Parity.md`.

That means:
- Hermes does not inherit a lower constitutional authority class
- OpenClaw and Hermes may still have different local implementation/readiness states
- validation order does not determine authority rank

If ChaseOS later makes promotion-capable runtime lanes real, it may still stage validation work separately per runtime, but that staging must not be described as a primary/secondary authority split.

---

## 11. Current Verdict

If ChaseOS later chooses to expand provenance-aware canonical promotion to Hermes, the first serious acceptable path should be:
- **Hermes only through a bounded AOR/Gate promotion workflow**
- **with explicit control-plane approval linkage**
- **with centralized provenance checks**
- **without direct Discord or ambient runtime write authority**

That preserves the constitutional model while keeping Hermes subordinate to the ChaseOS control plane rather than turning the active Discord runtime lane into an uncontrolled canonical write surface.

### Follow-on pair-level contract
The next concrete specification layer is now:
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`

### Draft substrate artifacts now seeded
- `runtime/workflows/registry/hermes_promote_note.yaml`
- `06_AGENTS/role-cards/hermes-promotion-review.yaml`
- `runtime/aor/task_type_table.yaml` (`promotion-review` row)

These are draft substrate files only.
They do not activate Hermes promotion authority by themselves.

### Focused readiness validation now exists
The next Hermes-side pre-activation validation layer now also exists:
- `runtime/aor/test_hermes_promotion_activation_readiness.py`
- `runtime/aor/test_hermes_promotion_preactivation_failures.py`
- `runtime/aor/test_runtime_instance_promotion_drafts.py`
- `runtime/aor/promotion_readiness.py::assess_hermes_promotion_activation_readiness()`
- `runtime/aor/promotion_readiness.py::collect_hermes_preactivation_failure_signals(...)`

That validation now proves five things at once:
- the Hermes draft workflow/role-card contract explicitly routes `07_LOGS/Promotion-Records/`
- control-plane approval linkage remains declared in the draft contract
- direct-authority denial for Discord/control-plane input remains declared
- target-scope failure posture and audit-survival expectations are now both declared through the Hermes pre-activation failure-signals helper
- activation readiness still remains blocked because the workflow is still `status: draft` and the adapter manifest still keeps `may_promote_to_knowledge: "no"`

### Canonical Hermes pre-activation helper surface
For Hermes-side contract inspection before any activation review, the canonical read-only helper is now:
- `runtime/aor/promotion_readiness.py::collect_hermes_preactivation_failure_signals(...)`

Use it when ChaseOS needs a direct answer about whether the still-draft Hermes contract already declares:
- control-plane approval linkage posture
- direct-authority denial for Discord/control-plane input
- exact target-scope failure posture
- audit-survival expectations for blocked runs

This helper is a contract-inspection surface only.
It does not execute the workflow and does not imply activation readiness.

---

*Graph links: [[Hermes-Runtime-Profile]] · [[Runtime-Instance-Provenance-Promotion-Caller-Alignment]] · [[Hermes-Adapter-Spec]] · [[HERMES]] · [[ChaseOS-Gate]] · [[Provenance-Schema-and-Trace-Idea-Implementation-Plan]] · [[Feature-Fit-Register]] · [[Vault-Map]]*