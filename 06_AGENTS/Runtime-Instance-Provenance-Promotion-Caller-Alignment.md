---
title: Runtime-Instance Provenance Promotion Caller Alignment
type: architecture
status: seeded — runtime-instance alignment pass
version: 0.2
created: 2026-04-24
updated: 2026-04-25
owner: Optimus
phase: Phase 9 second-wave
---

# Runtime-Instance Provenance Promotion Caller Alignment

This document defines how provenance-minimum enforcement should expand beyond the first Claude hook lane and into the ChaseOS runtime-instance model.

The focus is not generic “non-Claude” surfaces.
The focus is the **runtime instance** as the governance unit, especially:
- OpenClaw instance lanes
- Hermes instance lanes

---

## 1. Why This Pass Exists

The first live caller path for provenance minimums now exists in:
- `.claude/hooks/ingestion_promotion_guard.py`

That is useful, but it is not enough for the long-term ChaseOS operating system.

If provenance minimums stay only in the Claude hook lane, the rule behaves like an adapter-specific feature instead of a constitutional OS rule.

ChaseOS needs a clearer answer to:
- which runtime instances may ever participate in canonical promotion,
- through what bounded caller path,
- and how all such paths should converge on the same Gate provenance seam.

---

## 2. Core Rule

`runtime/chaseos_gate.py` owns the provenance-minimum rule.

Runtime-instance caller paths should:
1. **call the same centralized rule**
2. **not fork or redefine provenance policy locally**
3. **only become live callers when the runtime instance is actually promotion-eligible**

This preserves one constitutional policy with multiple bounded execution lanes.

---

## 3. Current State

### Live caller path now
- `.claude/hooks/ingestion_promotion_guard.py`
- applies to approved writes targeting `02_KNOWLEDGE/`
- calls `check_provenance_minimums()` after the broader promotion gate is met

### OpenClaw current state
OpenClaw is active and proven as a bounded execution lane, but its current adapter manifest says:
- `may_promote_to_knowledge: "no"`
- `gate_conditions_required: false`
- `autonomous_promotion: false`
- `02_KNOWLEDGE/**` is explicitly denied

So OpenClaw is **not yet a live caller candidate** in its current bounded activation.

### Hermes current state
Hermes is active as a bounded Discord/shadow runtime lane, but its current adapter manifest says:
- `may_promote_to_knowledge: "no"`
- `gate_conditions_required: false`
- `autonomous_promotion: false`
- `02_KNOWLEDGE/**` is explicitly denied

So Hermes is also **not yet a live caller candidate** in its current bounded activation.

---

## 4. What “No Hook-Lane Only” Means in ChaseOS Terms

It does **not** mean every runtime should immediately get promotion rights.

It means:
- provenance minimums should not remain conceptually trapped inside one adapter-specific enforcement lane forever
- when a runtime instance later gains a promotion-capable path, it should call the same Gate seam rather than inventing a new rule

Plainly:
- **today:** Claude hook lane is the first live caller
- **later:** OpenClaw and/or Hermes may become additional caller lanes only after their bounded runtime contracts actually permit promotion paths

So “no hook-lane only” is about **future caller alignment**, not premature authority expansion.

---

## 5. Runtime-Instance Alignment Matrix

| Runtime instance | Current promotion authority | Should call `check_provenance_minimums()` now? | Why |
|---|---|---|---|
| Claude Code lane | gated knowledge-write lane exists | Yes — already live | Actual `02_KNOWLEDGE/` hook lane exists |
| OpenClaw instance | no canonical promotion in current manifest | No — not yet | No promotion-capable path is declared yet |
| Hermes instance | no canonical promotion in current manifest | No — not yet | Current Hermes lane is bounded to shadow/advisory outputs |

---

## 6. Conditions Before OpenClaw Becomes a Caller

OpenClaw should only become a live caller path after all of the following are true:

1. adapter manifest changes from:
   - `may_promote_to_knowledge: "no"`
   to a bounded gated posture
2. explicit workflow/role-card path exists for promotion-oriented writes
3. the writeback path is tested and audited
4. Gate provenance minimums are called centrally rather than reimplemented in OpenClaw-local logic
5. the promotion lane remains non-autonomous unless the constitutional model explicitly changes

Likely first OpenClaw caller shape:
- OpenClaw -> `chaseos run [promotion-oriented workflow]` -> AOR/Gate -> centralized provenance check -> bounded canonical write

Not:
- ambient OpenClaw direct write to `02_KNOWLEDGE/`

---

## 7. Conditions Before Hermes Becomes a Caller

Hermes should only become a live caller path after all of the following are true:

1. Hermes is granted a real promotion-capable workflow beyond the current shadow/advisory lane
2. Discord/gateway interaction is still treated as data/visibility, not authority by itself
3. a declared AOR/Gate promotion path exists for Hermes
4. provenance minimums are checked through the same centralized Gate seam
5. canonical promotion remains explicitly approved and audited

Likely first Hermes caller shape:
- Hermes bounded workflow -> AOR/Gate promotion step -> centralized provenance check -> bounded writeback

Not:
- direct Discord-driven canonical mutation
- ambient Hermes write to `02_KNOWLEDGE/`

---

## 8. Recommended Promotion Caller Shapes

### A. Strongest shape
A future explicit promotion workflow should call `check_provenance_minimums()` inside the Gate/AOR promotion path.

This is stronger than adapter-specific hooks because it is runtime-neutral once a workflow is authorized.

### B. Transitional shape
Adapter-local caller path (like the current Claude hook) may exist when that is the only real write lane currently available.

This is acceptable as a first foothold, but it should point back to centralized policy.

### C. Forbidden shape
Do not create separate provenance-minimum rule variants per runtime instance.

Bad examples:
- one rule in Claude hook
- a different looser rule in OpenClaw
- a third Discord-specific rule in Hermes

That would fracture ChaseOS constitutional policy.

---

## 9. What This Means for the Next Real Runtime Work

The next runtime-instance question is not:
- “what other non-Claude lane should call the rule?”

The better question is:
- “which runtime instance is the first one ChaseOS actually wants to make promotion-capable after Claude, and through what bounded workflow path?”

For this repo’s current truth:
- OpenClaw and Hermes are peer runtime instances under the authority-parity ruling
- both remain explicitly bounded away from canonical promotion in their current active lanes
- local implementation breadth and enablement may still differ between the two runtimes

So if ChaseOS later expands beyond the Claude hook lane, the correct framing is:
- **OpenClaw and Hermes are both valid runtime-instance caller candidates in principle**
- **each runtime still requires its own bounded workflow/approval/provenance/readiness proof**
- **sequencing does not imply lower authority for either runtime**

---

## 10. Current Verdict

ChaseOS should treat provenance minimum enforcement as:
- **already live** in the Claude hook lane,
- **owned centrally** in `runtime/chaseos_gate.py`,
- **not yet active** for OpenClaw or Hermes,
- and **ready for future runtime-instance alignment** only when those instances gain explicit promotion-capable paths.

That preserves the constitutional model:
- one provenance rule,
- multiple possible caller lanes,
- no premature authority expansion,
- no hook-lane-only future.

That first contract layer now has additional runtime-instance substrate and validation truth behind it:
- `06_AGENTS/OpenClaw-First-Bounded-Promotion-Path.md`
- `06_AGENTS/Hermes-First-Bounded-Promotion-Path.md`
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `runtime/aor/promotion_readiness.py`

So the current ChaseOS truth is stronger than simple caller-alignment intent:
- both runtime instances now have draft promotion workflow/role-card substrate
- both runtime instances now have canonical pre-activation helper surfaces for contract inspection
- both runtime instances now have shared bounded `write_scope` and manifest `writeback_targets` parity machine-checked at the pair-level validation surface
- both runtime instances remain blocked from activation while the workflows stay `draft` and the adapter manifests keep `may_promote_to_knowledge: "no"`

---

*Graph links: [[Provenance-Schema-and-Trace-Idea-Implementation-Plan]] · [[ChaseOS-Gate]] · [[OpenClaw-Adapter-Spec]] · [[Hermes-Adapter-Spec]] · [[OPENCLAW]] · [[HERMES]] · [[Feature-Fit-Register]] · [[Vault-Map]]*