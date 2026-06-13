---
title: Runtime-Instance Authority Parity
type: architecture
status: standing constitutional ruling — docs/governance parity established
version: 0.1
created: 2026-04-25
updated: 2026-04-25
owner: Optimus
phase: Phase 9 second-wave
---

# Runtime-Instance Authority Parity

This document records the ChaseOS ruling that **Hermes and OpenClaw are equal-authority runtime instances inside the ChaseOS control plane**. OpenHuman was briefly evaluated but is now retired from active runtime integration and remains a reference-product study only.

No peer runtime is to be documented as constitutionally secondary to another peer runtime once it is registered under the Agent Control Plane. Implementation breadth may differ, but the authority ceiling is governed by the same control-plane/Gate model.

Operational implementation breadth may still differ at a given moment.
That difference must be described as:
- workflow availability
- local runtime enablement
- platform/runtime-specific constraints
- staged implementation order

It must **not** be described as a lower authority class for Hermes.

---

## 1. Decision

ChaseOS now treats:
- `openclaw`
- `hermes`

as **peer Phase 9 runtime instances with equal authority ceilings under AOR/Gate governance**.

Equal authority here means:
- same constitutional subordination to ChaseOS control plane
- same requirement for declared workflows, role cards, audit, and Gate enforcement
- same eligibility in principle for bounded canonical-promotion paths
- same need for explicit approval and provenance enforcement before canonical mutation
- no standing doctrine that frames one runtime as inherently primary and the other as inherently secondary

---

## 2. What This Changes

This ruling changes the documentation/governance posture in three ways.

### A. No more authority asymmetry language
Docs should no longer say things like:
- OpenClaw first, Hermes later
- Hermes is secondary
- Hermes is only a shadow/deferred lane in constitutional terms
- OpenClaw is the sole realistic runtime-instance authority candidate

### B. Equal-authority, implementation-distinct framing
When the repo needs to describe current differences, it should say:
- the two runtimes are authority peers
- local implementation readiness may still differ by workflow set or machine-specific state
- staged implementation order does not imply lower constitutional authority

### C. Symmetric future expansion doctrine
Future AOR/Gate expansion docs should be written so that:
- Hermes and OpenClaw can be evaluated through the same authority model
- readiness gates may be runtime-specific, but not authority-ranked
- any promotion-path docs or tests should avoid treating Hermes as inherently subordinate

---

## 3. What This Does NOT Change

This ruling does **not by itself**:
- activate canonical promotion for either runtime
- flip any workflow manifest from `draft` to `active`
- change adapter-manifest write permissions automatically
- bypass Gate, approval, or provenance minimum checks
- erase machine-local implementation differences already present in runtime configs

This is a constitutional and documentation parity ruling, not an automatic live-authority activation.

This ruling no longer includes OpenHuman as an active peer runtime. OpenHuman is reference-only unless a future approved adapter/proxy/credential model reopens it.

---

## 4. Interpretation Rule for Existing Docs

If an older doc says Hermes is less plausible, later, more constrained, or secondary **as an authority model**, that wording is superseded by this document.

Those docs should be updated to one of the following truthful phrasings instead:
- equal authority model, different local implementation breadth
- equal authority ceiling, different currently enabled workflows
- equal constitutional status, runtime-specific readiness still to be validated

---

## 5. Promotion-Path Implication

For runtime-instance provenance-aware promotion work, ChaseOS should now assume:
- OpenClaw and Hermes are both valid bounded AOR/Gate caller candidates
- both must satisfy approval, provenance, role-card, manifest, and audit requirements
- neither runtime should be framed as permanently downstream of the other

If one runtime reaches implementation readiness sooner, that is a sequencing fact, not an authority verdict.

---

## 6. Operating-System Alignment

This improves ChaseOS as an operating system because it separates:
- **constitutional authority model** from
- **current implementation maturity**

That is the correct OS-level distinction.

Without this distinction, runtime docs blur governance truth with temporary rollout order.
With this distinction, Hermes/OpenClaw summaries can report:
- what each runtime is currently enabled to do
- what each runtime is authorized in principle to do under the same constitutional model
- what gates still block activation for each runtime

That makes the runtime layer more legible and more honest.

---

## 7. Immediate Follow-On

The earlier parity follow-ons are now in place:
- the runtime-instance promotion and runtime-positioning docs were patched to inherit this parity posture explicitly
- Hermes now has a mirrored readiness-gate artifact instead of being implied only through OpenClaw-side framing
- `06_AGENTS/Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications.md` now contains a dedicated canonical helper comparison subsection for the OpenClaw and Hermes pre-activation helper surfaces

That parity work also now includes the machine-readable alignment step:
- `runtime/policy/adapters/hermes.yaml` now reflects runtime-surface/tier parity more honestly
- runtime context/state extraction now understands Hermes-specific `draft_outputs` and `archive_notes` write-target families instead of flattening them into opaque keys
- runtime-state notes now distinguish default runtime selection from runtime authority rank

That parity work also now includes a materially richer shared validation surface:
- `runtime/aor/test_runtime_instance_promotion_drafts.py` now machine-checks cross-runtime contract truth instead of stopping at simple loader coverage
- the shared validation layer now covers helper-signal dimensions, approval-input requirements, escalation structure, execution controls, read structure, forbidden boundaries, manifest/role-card doctrine alignment, runtime expectations, allowed-action structure, write-scope symmetry, bounded manifest writeback-target symmetry, and task-type cross-link alignment
- this means Hermes/OpenClaw parity is now reinforced by shared machine-checked substrate, not only by doctrine prose

That doctrine/discoverability cleanup is now also in place:
- `06_AGENTS/Runtime-Instance-Provenance-Promotion-Caller-Alignment.md` now reflects the fuller helper/readiness substrate instead of stopping at older contract-only wording
- `06_AGENTS/Vault-Map.md` and `06_AGENTS/Markdown-to-Standalone-Bridge.md` already expose the runtime-promotion path docs, readiness gates, mirrored draft substrate, and helper-routing surfaces as first-class routing truth

The next strongest follow-on is no longer basic parity cleanup:
- continue with either shared validation hardening when a real cross-runtime gap remains, or doc/discoverability truth-sync when the validation surface advances faster than adjacent navigation docs

---

*Graph links: [[CLAUDE]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[OpenClaw-Adapter-Spec]] · [[OpenAI-Adapter-Spec]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Hermes-Adapter-Spec]] · [[Archon-Runtime-Profile]] · [[Codex-Runtime-Profile]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[OpenClaw-First-Bounded-Promotion-Path]] · [[Hermes-First-Bounded-Promotion-Path]] · [[Runtime-Instance-Promotion-Workflow-and-Role-Card-Pair-Specifications]] · [[Vault-Map]]*
