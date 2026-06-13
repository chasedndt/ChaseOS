---
title: Normalization + Provenance Contract
type: architecture
status: canonical - Phase 9 artifact contract; local/import declared metadata extension repo-observed
version: 1.2
created: 2026-04-23
updated: 2026-04-28
phase: Phase 9 - Acquisition + Normalization
knowledge_class: canonical-state
---

# Normalization + Provenance Contract
## ChaseOS - Source Pack, Evidence, Trust, Freshness, And Outcome Model

> Normalization turns acquired material into stable, inspectable ChaseOS artifacts. Provenance records where the material came from and how it changed. Trust evaluates the source and transformation quality. Outcome scoring records later usefulness without rewriting origin truth.

---

## 1. Base Envelope

Every normalized artifact produced by this layer should carry an envelope with this shape:

```yaml
artifact_id: "acq_<date>_<slug>_<shortid>"
artifact_type: "normalized_source_pack"
schema_version: "anl.v1"
created_at: "2026-04-23T00:00:00Z"
owner_layer: "acquisition_normalization"
owning_workflow: "workflow_id_or_manual"
objective:
  title: "why this was gathered"
  requested_by: "operator|schedule|workflow|runtime"
  downstream_target: "sbp|aor|sic|memory_review|delivery|operator_review"
acquirer:
  runtime_id: "claude_code|openclaw|hermes|browser_operator|capture_cli|user"
  adapter_id: "optional"
  role_card: "optional"
scope:
  read_scope: []
  browser_scope: []
  network_scope: []
  cadence_or_trigger: "manual|schedule|event"
items: []
provenance: []
trust_evaluation: {}
freshness: {}
transformation_chain: []
promotion:
  status: "workspace-local"
  allowed_next_steps: []
  canonical_mutation_allowed: false
audit:
  activity_log_ref: null
  source_hashes: []
```

This is an architecture contract, not a built schema module yet.

---

## 2. Artifact Model

| Artifact type | Purpose | Owner layer | Expected shape | Write location | Promotion status | Durability | Generic/use-case |
|---|---|---|---|---|---|---|---|
| source packet | One acquired item normalized into text/metadata with origin proof | Acquisition + Normalization | envelope + item metadata + raw pointer + normalized text/excerpt + provenance refs | future `runtime/acquisition/items/` or task bundle; captured externals remain in `03_INPUTS/00_QUARANTINE/` | quarantine or workspace-local | temporary to durable-adjacent | generic |
| evidence packet | Specific claim/passage/fact with citation and confidence | SIC or Acquisition + Normalization | claim, evidence_refs, source_ids, citation spans, confidence, caveats | SIC workspace outputs or future `runtime/acquisition/evidence/` | workspace-local | task/workspace durable | generic |
| normalized source pack | Bundle of source packets for one objective/workflow/date | Acquisition + Normalization | envelope + source packet refs + freshness/trust summary + gaps | future `runtime/acquisition/packs/<workflow>/<date>/pack.json`; optional markdown summary in `07_LOGS/Acquisition-Packs/` | workspace-local | durable working artifact | generic |
| workspace evidence bundle | Retrieval-ready or SIC-ready source/evidence collection | SIC + Acquisition + Normalization | workspace_id, source_package_refs, evidence packets, query context | `runtime/source_intelligence/workspaces/<id>/` or future acquisition pack path | workspace-local | workspace durable | generic |
| task-local acquisition bundle | Inputs prepared for one AOR run | AOR + Acquisition + Normalization | run_id, objective, items, trust, freshness, allowed use, audit refs | future `runtime/tasks/<run_id>/acquisition/`; current fallback `07_LOGS/Agent-Activity/` refs | temporary | run-local | generic |
| daily operator source pack | Day-specific packet for operator_today/close-day style workflows | AOR + Acquisition + Normalization | date, canonical reads, carry-forward refs, recent logs, approvals, gaps | future `07_LOGS/Acquisition-Packs/YYYY-MM-DD-operator-source-pack.md` | log-local | durable log | generic |
| briefing-ready input set | Pack shaped for SBP or operator briefing generation | Acquisition + Normalization -> SBP | sections, sources, freshness, trust summary, exclusions, known gaps | future `runtime/acquisition/briefing_inputs/<pipeline>/<date>.json` | workspace/log-local | durable working artifact | generic |
| action-ready runtime packet | Evidence and constraints sufficient for an action proposal | AOR + Acquisition + Normalization | objective, evidence refs, allowed actions, forbidden actions, required approvals | future `runtime/tasks/<run_id>/action_packet.json` | proposal-only | temporary until action resolved | generic |
| memory candidate artifact | Proposed memory update with evidence and review state | Agent Memory + Acquisition + Normalization | memory_layer, proposed_fact, evidence refs, reason, approval state | future `runtime/memory/candidates/`; current fallback `07_LOGS/Agent-Activity/` | candidate only | durable if approved | generic |
| provenance record | Standalone origin and transformation record | Acquisition + Normalization | source_origin, method, acquirer, timestamps, hashes, chain | adjacent to source pack or future `runtime/provenance/` | support record | durable-adjacent | generic |
| trust-evaluation record | Trust/freshness/actionability assessment for an item or pack | Acquisition + Normalization | trust_tier, confidence, quality markers, caveats, evaluator | adjacent to pack/item | support record | durable-adjacent | generic |
| delivery-ready summary packet | Summary prepared for delivery adapter after briefing generation | SBP/Delivery + Acquisition + Normalization | audience, summary, source refs, omitted risks, delivery target | SBP output path, e.g. `07_LOGS/SBP-Runs/` | log-local | durable log | use-case-specific wrapper |

---

## 3. Required Provenance Fields

| Field | Meaning |
|---|---|
| `source_origin.kind` | `vault`, `quarantine`, `url`, `api`, `browser`, `runtime_log`, `user_prompt`, `schedule_intent`, `manual_import`, `connector`, `memory` |
| `source_origin.ref` | Path, URL, API endpoint label, runtime log id, message id, or schedule id |
| `source_origin.display_name` | Human-readable source name |
| `source_origin.declared_url` | Optional operator-declared source URL, validated as a concrete `http` or `https` URL and treated as provenance metadata rather than network authority |
| `acquisition_method` | Method from `Acquisition-Surface-Map.md` |
| `acquirer.identity` | Runtime/user/tool that gathered it |
| `acquirer.trust_tier_ceiling` | Authority ceiling of the acquirer, not source content |
| `captured_at` | When acquired |
| `source_event_at` | When the source event/content claims to be from, if known |
| `freshness_window` | `real_time`, `same_day`, `recent`, `historical`, `unknown` |
| `content_sha256` | Hash of normalized body or raw content where available |
| `sidecar_ref` | Phase 8 sidecar path when acquired through capture |
| `audit_ref` | AOR/MCP/FSOS activity record where applicable |
| `raw_pointer` | Path/URL/ref to raw material, not necessarily embedded content |
| `representation_level` | `raw`, `extracted`, `normalized`, `summarized`, `synthesized` |
| `transformation_chain` | Ordered list of operations from raw to current artifact |
| `license_or_terms_note` | Optional note for web/API sources where use limits are relevant |

---

## 4. Trust Model

Base trust tier and outcome quality are separate.

### Base Trust

| Input kind | Default trust treatment |
|---|---|
| canonical vault state | Tier 1 or Tier 2 depending file class |
| internal logs/audit records | Tier 2 as execution history, not necessarily content truth |
| SIC workspace outputs | Tier 3 until promoted |
| advisory/research outputs | Tier 3 as research, not canonical |
| raw web/API/social/browser content | Tier 4 until triaged |
| user prompt/objective | Operator intent, not evidence; do not trust as source fact unless separately sourced |
| runtime memory | Runtime-local context; subordinate to vault truth |

### Trust Evaluation Fields

```yaml
trust_evaluation:
  base_trust_tier: 4
  assigned_by: "normalizer_id"
  confidence: "high|medium|low|unknown"
  quality_marker: "verified|plausible|unverified|conflicting|stale|incomplete"
  source_quality_notes: []
  contradiction_refs: []
  operator_approval_state: "not_required|pending|approved|rejected"
  actionability: "none|briefing_only|review_required|action_candidate|blocked"
```

`base_trust_tier` records origin authority. `confidence` and `quality_marker` evaluate current handling quality. `actionability` records what downstream use is allowed.

---

## 5. Freshness Model

Freshness is separate from truth. A source can be trustworthy but stale, or untrusted but current.

Local/import research metadata may supply `source_event_at` and `captured_at` when the operator saved an external digest/export before pack build. These timestamps enrich freshness and provenance only; they do not mark content reviewed, elevate trust, create browser/network authority, or permit canonical mutation.

| Freshness field | Values |
|---|---|
| `source_event_at` | ISO timestamp/date or null |
| `captured_at` | ISO timestamp |
| `freshness_window` | `real_time`, `same_day`, `recent`, `historical`, `unknown` |
| `expires_at` | Optional for time-sensitive sources |
| `staleness_policy` | `allow`, `warn`, `block_for_action`, `requires_refresh` |
| `time_sensitive_domain` | `trading`, `security`, `news`, `schedule`, `legal`, `medical`, `none` |

Trading and market sources should default to `block_for_action` when stale but may remain `briefing_only` for context.

---

## 6. Transformation Chain

Every transformation should append a record:

```yaml
transformation_chain:
  - step_id: "raw_capture"
    performed_by: "capture_cli"
    method: "connector_capture"
    timestamp: "2026-04-23T00:00:00Z"
    input_ref: "external_url_or_file"
    output_ref: "03_INPUTS/00_QUARANTINE/..."
    representation_level: "raw"
  - step_id: "normalize_text"
    performed_by: "acquisition_normalizer"
    method: "html_to_markdown"
    timestamp: "2026-04-23T00:05:00Z"
    input_ref: "capture_id"
    output_ref: "source_packet_id"
    representation_level: "normalized"
```

Transformation types:

- `raw_capture`
- `file_read`
- `browser_extract`
- `html_to_markdown`
- `api_response_parse`
- `dedup_check`
- `injection_scan`
- `trust_evaluation`
- `freshness_evaluation`
- `source_pack_assembly`
- `evidence_extraction`
- `summary_generation`
- `synthesis_generation`
- `delivery_formatting`

---

## 7. Outcome Model

Outcome scoring is retrospective. It must not overwrite base provenance.

```yaml
outcome_feedback:
  evaluated_at: "2026-04-24T00:00:00Z"
  evaluator: "operator|workflow|scorecard"
  outcome_domain: "trading|project|research|ops"
  usefulness_score: 0.0
  accuracy_observation: "helpful|neutral|wrong|misleading|unknown"
  downstream_effect: "used_in_briefing|used_in_decision|ignored|blocked|contradicted"
  notes: []
```

For trading, later market behavior may help score whether a source, source class, or pattern was useful. It does not change the fact that the item came from a given source, by a given method, at a given time. Provenance is immutable; outcome feedback is append-only.

---

## 8. Promotion And Mutation Rules

### Historical migration posture

Older artifacts may preserve only part of the provenance story.
That is acceptable as long as ChaseOS stays honest about what is and is not known.

The migration posture is now documented in:
- `runtime/schemas/provenance_migration_notes.md`

Key rule:
- partial lineage is allowed
- fabricated complete lineage is not

Practical implication:
- older promoted notes may still be usable provenance anchors through fields like `verification_status`, `promoted_from`, `source_package_id`, or audit/build refs
- missing transformation steps should be recorded as unknown rather than silently synthesized
- chronology evidence and source-lineage evidence must remain distinguishable even when both help reconstruct history

| From | To | Rule |
|---|---|---|
| raw acquired item | source packet | Allowed inside normalization if provenance is preserved |
| source packet | normalized source pack | Allowed inside normalization |
| normalized source pack | briefing-ready input set | Allowed for SBP/AOR consumers |
| source/evidence pack | SIC workspace source package | Requires SIC ingestion rules and promotion boundary where applicable |
| any normalized artifact | `02_KNOWLEDGE/` | Requires Gate/human promotion |
| any normalized artifact | project OS / Now / roadmap | Requires explicit user instruction and protected-file rules if applicable |
| action-ready runtime packet | external action | Requires workflow approval and action-specific permission |
| memory candidate | durable memory | Requires memory review/update protocol |

No normalized artifact may claim `canonical_mutation_allowed: true` in this phase.

---

## 9. Minimal First-Wave Schema Status

Pass 1A implements and validates these three artifacts only:

1. `source_packet`
2. `normalized_source_pack`
3. `briefing_ready_input_set`

Add `memory_candidate_artifact`, `action_ready_runtime_packet`, and outcome scoring after provenance and context-governance second-wave work is stable.

---

## Related Documents

| Document | Purpose |
|---|---|
| `06_AGENTS/Acquisition-Normalization-Layer.md` | Canonical capability architecture |
| `06_AGENTS/Acquisition-Surface-Map.md` | Source and method classification |
| `06_AGENTS/Runtime-Acquisition-Responsibility-Matrix.md` | Runtime ownership |
| `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md` | First pilot contract |
| `runtime/schemas/provenance_migration_notes.md` | Historical partial-lineage migration posture |
| `06_AGENTS/Trust-Tiers.md` | Authority ceilings |
| `04_SOPS/Untrusted-Input-Handling-SOP.md` | Raw input policy |

*Normalization-Provenance-Contract.md - v1.2 | Created: 2026-04-23 | Updated: 2026-04-28 | Phase 9 Acquisition + Normalization Architecture Pass + Pass 1A artifact schema status + local/import declared metadata provenance extension*


*Graph links: [[Vault-Map]]*
