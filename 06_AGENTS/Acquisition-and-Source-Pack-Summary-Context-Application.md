---
title: Acquisition and Source Pack Summary Context Application
type: implementation-bridge-plan
status: seeded — concrete Summary Context Layer application for acquisition-stage and source-pack summaries
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Acquisition and Source Pack Summary Context Application

> This document is the next concrete application pass for the `Standalone-Summary-Context-Layer` feature.
> It defines how acquisition-stage, source-pack, evidence-bundle, and briefing-input summaries should behave inside ChaseOS.

---

## 1. Purpose

The Summary Context Layer says summaries should carry operating meaning.
This pass applies that to the Acquisition + Normalization layer that answers:
- what was gathered,
- why it was gathered,
- how it was normalized,
- what downstream use is allowed,
- and whether the result is a source pack, evidence bundle, briefing input, or operator-facing summary.

This slice matters because acquisition outputs are easy to misread as:
- raw source truth,
- final briefing output,
- canonical knowledge,
- or just another generic JSON bundle.

But in ChaseOS, acquisition outputs sit in a distinct operating posture:
- provenance-rich,
- inspectable,
- normalized,
- action-bounded,
- and usually **upstream of** briefings, proposals, or delivery.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/Acquisition-Normalization-Layer.md`
- `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md`
- `runtime/acquisition/` implementation artifacts and pack outputs
- normalized source packs
- source packets
- briefing-ready input sets
- acquisition pack summary references and future operator-facing summaries

Especially relevant examples:
- `runtime/acquisition/packs/2026-04-23-strikezone-daily/normalized_source_pack.json`
- `runtime/acquisition/packs/2026-04-23-strikezone-daily/briefing_ready_input_set.json`
- `runtime/acquisition/packs/strikezone_pass1a_fixture/2026-04-23/*.json`
- `runtime/acquisition/packs/strikezone-latest.json`
- `runtime/workflows/registry/source_pack_builder.yaml`
- `06_AGENTS/role-cards/source-pack-builder.yaml`

Not included yet:
- final source-pack summary markdown surface under `07_LOGS/Acquisition-Packs/`
- machine-readable summary-context schema enforcement in code
- generalized evidence-bundle UI
- final bridge/application pass for acquisition-specific chronology surfaces

---

## 3. Why Acquisition Outputs Need Typed Context

Acquisition artifacts are upstream operating objects.
Without typed context, they can easily be mistaken for final outputs.

Examples of ambiguity without typed context:
- Is this a raw source packet or a normalized pack?
- Is this a briefing-ready input set or an operator brief?
- Is this allowed to drive action, or only briefing/review?
- Is this evidence, synthesis, or settled knowledge?
- Should it appear in an acquisition workspace, a cockpit, or a chronology browser?

The Acquisition + Normalization layer already answers these structurally.
The Summary Context Layer makes those distinctions visible when the artifact is surfaced to a human.

---

## 4. Core Summary Classes for the Acquisition Slice

| Summary class | Derived from | Typical meaning | Recommended surface |
|---|---|---|---|
| Source packet summary | one acquired source item | one bounded source with provenance and trust/freshness metadata | acquisition inspector |
| Normalized source-pack summary | normalized pack artifact | grouped multi-source packet prepared for downstream use | source-pack workspace |
| Briefing-input-set summary | briefing-ready input set | normalized packet specifically shaped for downstream briefing consumption | briefing-input inspector |
| Acquisition gap summary | pack gaps/freshness/trust conflicts | warnings about missing, stale, or excluded source material | acquisition warnings panel |
| Acquisition actionability summary | actionability + promotion fields | concise explanation of what downstream use is allowed | actionability inspector |
| Acquisition authority summary | acquisition workflow + role card posture | concise explanation of what authority shaped the pack | acquisition contract inspector |

---

## 5. Current Artifact Layers and Their Summary Meaning

### A. Acquisition doctrine layer
These docs define what acquisition and normalization are allowed to mean:
- `Acquisition-Normalization-Layer.md`
- `StrikeZone-Acquisition-Normalization-Pilot.md`

### B. Acquisition artifact layer
These machine-readable outputs define the actual stage outputs:
- source packets
- normalized source packs
- briefing-ready input sets
- latest-pointer records

### C. Downstream relationship layer
These fields define what may happen next:
- downstream targets
- actionability
- promotion status
- allowed next steps
- blocked actions

The standalone must preserve the distinction:
**source-pack artifacts are upstream operating inputs with provenance and action bounds — not final briefs and not canonical truth.**

---

## 6. Concrete Mapping Table

| Current artifact | Current role | Summary-context role | Future standalone surface |
|---|---|---|---|
| `runtime/acquisition/packs/.../source_packet_*.json` | one acquired source item | source packet summary source object | acquisition inspector |
| `runtime/acquisition/packs/.../normalized_source_pack.json` | normalized multi-source packet | normalized source-pack summary source object | source-pack workspace |
| `runtime/acquisition/packs/.../briefing_ready_input_set.json` | downstream briefing packet | briefing-input-set summary source object | briefing-input inspector |
| `runtime/acquisition/packs/strikezone-latest.json` | latest pack pointer | latest-pack routing summary source object | acquisition status panel |
| actionability blocks in acquisition artifacts | allowed/blocked downstream use | acquisition actionability summary source object | actionability inspector |
| freshness/trust/conflict summaries in acquisition artifacts | source quality and gaps | acquisition gap summary source object | acquisition warnings panel |
| `06_AGENTS/Acquisition-Normalization-Layer.md` | architecture/governance anchor | acquisition authority summary reference | acquisition doctrine panel |
| `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md` | pilot/source-pack contract | pilot-specific summary reference | pilot contract panel |
| `runtime/workflows/registry/source_pack_builder.yaml` | acquisition workflow manifest | acquisition authority summary contract | workflow/acquisition contract panel |
| `06_AGENTS/role-cards/source-pack-builder.yaml` | acquisition permission envelope | acquisition authority summary contract | role-card/authority inspector |

---

## 7. Recommended Summary Context Fields for Acquisition Outputs

A normalized source-pack summary should eventually preserve fields like:

```json
{
  "summary_class": "normalized_source_pack_summary",
  "source_family": "acquisition_pack",
  "artifact_id": "nsp_strikezone-daily",
  "artifact_type": "normalized_source_pack",
  "workflow_id": "source_pack_builder",
  "authority_posture": "acquisition-normalization-bounded",
  "source_posture": "provenance-rich-upstream-input",
  "routing_surface": "source_pack_workspace",
  "promotion_posture": "workspace-local",
  "operator_action_needed": false,
  "source_refs": [
    "runtime/acquisition/packs/2026-04-23-strikezone-daily/normalized_source_pack.json"
  ]
}
```

A briefing-input-set summary should preserve more downstream-specific meaning:

```json
{
  "summary_class": "briefing_input_set_summary",
  "source_family": "acquisition_pack",
  "artifact_id": "bris_strikezone-daily",
  "artifact_type": "briefing_ready_input_set",
  "workflow_id": "source_pack_builder",
  "authority_posture": "briefing-only-upstream",
  "source_posture": "normalized-briefing-input",
  "routing_surface": "briefing_input_inspector",
  "promotion_posture": "workspace-local",
  "operator_action_needed": false,
  "source_refs": [
    "runtime/acquisition/packs/2026-04-23-strikezone-daily/briefing_ready_input_set.json"
  ]
}
```

Key point:
A briefing-ready input set is still **upstream of** the operator brief itself.
It should not be mistaken for the final briefing output.

---

## 8. Routing Rules for Acquisition Summaries

### Source packet summary
Use when the operator needs to inspect one source item and its provenance/trust/freshness fields.
Show in:
- acquisition inspector
- source-item detail panel

### Normalized source-pack summary
Use when the main value is the grouped packet and its multi-source composition.
Show in:
- source-pack workspace
- acquisition overview panel

### Briefing-input-set summary
Use when the main value is a pack shaped for downstream briefing consumption.
Show in:
- briefing-input inspector
- downstream workflow prep view

### Acquisition gap summary
Use when missing/stale/excluded/conflict states matter.
Show in:
- acquisition warnings panel
- quality/freshness strip
- operator attention surface when the gap is blocking

### Acquisition actionability summary
Use when the operator needs to know what may happen next and what remains blocked.
Show in:
- actionability inspector
- acquisition contract panel

### Acquisition authority summary
Use when the operator needs to know what workflow and role-card posture shaped the artifact.
Show in:
- acquisition contract inspector
- workflow/role-card linkage view

---

## 9. Governance Rules for This Slice

### Acquisition artifacts remain upstream and non-canonical by default
A source pack is an operating input packet, not canonical truth.
A briefing-ready input set is a downstream prep artifact, not the final brief.

### Provenance and actionability must stay attached
A useful acquisition summary must preserve:
- where inputs came from,
- how they were gathered,
- what trust/freshness posture they carry,
- what downstream uses are allowed or blocked.

### Briefing-input summaries must not be confused with operator briefs
The packet that feeds a brief is not the brief itself.
Future surfaces should preserve that separation.

### Promotion posture must remain visible
If `canonical_mutation_allowed` is false and status is `workspace-local`, the summary must not appear as if it represents promoted or canonical state.

### Acquisition summaries remain subordinate to deeper contracts and artifacts
If a rendered summary conflicts with the underlying pack artifact, workflow manifest, role card, or doctrine source, the deeper source wins.

---

## 10. Recommended Standalone Views

### A. Source Pack Workspace
Should show:
- pack identity
- source count
- trust/freshness summary
- downstream target
- high-level explanation of what the pack is for

### B. Source Item / Packet Inspector
Should show:
- one acquired item
- origin ref
- acquisition method
- trust/freshness/actionability
- transformation-chain position

### C. Briefing Input Inspector
Should show:
- briefing-input-set identity
- downstream briefing target
- sections and source refs
- blocked actions and allowed next steps

### D. Acquisition Warnings Panel
Should show:
- stale items
- missing required sources
- conflicts
- excluded items
- whether operator attention is needed

### E. Acquisition Contract Inspector
Should show:
- acquisition workflow
- linked role card
- authority posture
- allowed next steps
- non-goals and blocked actions

---

## 11. What This Application Pass Proves

This pass proves the Summary Context Layer works for upstream operating packets, not just briefs, logs, workflows, and browser outputs.

Specifically, it proves ChaseOS can distinguish between:
- one source packet and a grouped normalized pack,
- a source pack and a briefing-ready input set,
- upstream input packets and final briefing outputs,
- provenance-rich operating inputs and canonical/promoted state.

That makes the Summary Context Layer much more useful for future acquisition and evidence-preparation surfaces.

---

## 12. Recommended Next Summary-Context Applications

After this slice, the strongest next applications are:
1. runtime navigation overlays
   - route/trust/risk summary views
   - escalation-point summaries
2. approval/decision traces convergence
   - approval summaries vs chronology summaries
   - decision outcome summaries
3. runtime shell / command-surface summaries
   - command-contract summaries
   - runtime status/doctor summary families

---

## 13. Current Verdict

Acquisition and source-pack artifacts already carry typed operating meaning.
This pass defines how ChaseOS should preserve that meaning when surfacing them to a human.

So the rule for this slice is:

**A source-pack or briefing-input summary is an upstream, provenance-rich operating packet with bounded actionability — not generic text, and not the final brief or canonical truth.**

---

*Graph links: [[Standalone-Summary-Context-Layer]] · [[Acquisition-Normalization-Layer]] · [[StrikeZone-Acquisition-Normalization-Pilot]] · [[ChaseOS-Studio-Architecture]]*

*Acquisition-and-Source-Pack-Summary-Context-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
