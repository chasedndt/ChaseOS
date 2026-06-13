---
title: Runtime-Instance Promotion Workflow and Role-Card Pair Specifications
type: architecture
status: seeded — contract pair specification pass
version: 0.2
created: 2026-04-24
updated: 2026-04-25
owner: Optimus
phase: Phase 9 second-wave
---

# Runtime-Instance Promotion Workflow and Role-Card Pair Specifications

This document defines the first bounded **workflow manifest + role-card pairs** that would be needed if ChaseOS later chooses to activate provenance-aware canonical promotion for runtime instances.

It does not activate those workflows.
It specifies the first acceptable contract shapes for:
- OpenClaw
- Hermes

---

## 1. Why This Pass Exists

The prior passes defined the future promotion-path contracts for OpenClaw and Hermes.

The next concrete architectural step is to define the first bounded workflow/role-card pairs those runtime instances would actually need.

Without that pair-level definition, the promotion-path contracts remain too abstract to evaluate cleanly.

---

## 2. OpenClaw Pair — First Candidate

### Proposed workflow manifest
- `runtime/workflows/registry/openclaw_promote_note.yaml`

### Proposed role card
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml`

### OpenClaw manifest intent
This workflow should represent:
- one bounded promotion candidate at a time
- one bounded canonical target at a time
- one explicit approval context at a time

### Proposed manifest shape

```yaml
id: openclaw_promote_note
name: "OpenClaw Promote Note"
version: "1.0"
description: "Bounded AOR/Gate-mediated promotion workflow for one OpenClaw note candidate."
task_type: promotion-review
role_card: openclaw-promotion-review
trigger_type: manual
owner: operator
status: draft
permission_ceiling: gated_canonical_write
writeback_targets:
  - "02_KNOWLEDGE/"
  - "07_LOGS/Agent-Activity/"
  - "07_LOGS/Build-Logs/"
failure_behavior: escalate
inputs:
  - candidate_path
  - target_path
  - source_refs
  - source_package_id
  - verification_status
  - knowledge_class
  - index_update_targets
  - promotion_reason
  - operator_approval_ref
outputs:
  - promoted_note_path
  - index_update_paths
  - provenance_check_result
  - audit_record_path
approval_rule: operator-explicit
rollback_path: "remove bounded writeback outputs from this run if promotion is rejected before finalization"
audit_expectations:
  - "approval reference recorded"
  - "provenance minimum result recorded"
  - "canonical write target recorded"
  - "index update evidence recorded"
```

### OpenClaw role-card intent
This role card should:
- permit declared-source review and bounded canonical write
- forbid ambient repo mutation
- forbid shell/connector expansion beyond declared workflow scope
- preserve OpenClaw’s subordination to AOR/Gate

### Proposed role-card shape

```yaml
id: openclaw-promotion-review
name: "OpenClaw Promotion Review Role Card"
version: "1.0"
description: "Permission envelope for one bounded OpenClaw promotion-review workflow."
owner: operator
allowed_actions:
  - read_declared_candidate
  - read_declared_sources
  - read_declared_indexes
  - write_bounded_canonical_note
  - write_bounded_index_update
  - write_promotion_log
  - write_agent_activity_log
forbidden_actions:
  - ambient_vault_write
  - write_protected_files
  - execute_undeclared_shell_actions
  - connector_expansion
  - multi_repo_access
  - autonomous_promotion
write_scope:
  - "02_KNOWLEDGE/"
  - "07_LOGS/Agent-Activity/"
  - "07_LOGS/Build-Logs/"
forbidden_write_zones:
  - "SOUL.md"
  - "CLAUDE.md"
  - "00_HOME/"
  - "01_PROJECTS/"
  - "06_AGENTS/"
  - "runtime/"
escalation_rules:
  - "approval missing or invalid"
  - "provenance minimums fail"
  - "target outside declared canonical scope"
  - "index update target not declared"
  - "attempted write outside write_scope"
runtime_expectations:
  - "AOR stages execute before writeback"
  - "Gate provenance minimums are checked centrally"
  - "OpenClaw remains non-autonomous for promotion"
required_reads:
  - "candidate_path (declared at runtime)"
  - "source_refs (declared at runtime)"
optional_reads:
  - "index_update_targets (declared at runtime)"
```

---

## 3. Hermes Pair — First Candidate

### Proposed workflow manifest
- `runtime/workflows/registry/hermes_promote_note.yaml`

### Proposed role card
- `06_AGENTS/role-cards/hermes-promotion-review.yaml`

### Hermes manifest intent
This workflow should represent:
- one bounded promotion candidate at a time
- one explicit control-plane/approval envelope at a time
- one AOR/Gate-mediated canonical write path

### Proposed manifest shape

```yaml
id: hermes_promote_note
name: "Hermes Promote Note"
version: "1.0"
description: "Bounded AOR/Gate-mediated promotion workflow for one Hermes note candidate with explicit control-plane approval linkage."
task_type: promotion-review
role_card: hermes-promotion-review
trigger_type: manual
owner: operator
status: draft
permission_ceiling: gated_canonical_write
writeback_targets:
  - "02_KNOWLEDGE/"
  - "07_LOGS/Agent-Activity/"
  - "07_LOGS/Build-Logs/"
failure_behavior: escalate
inputs:
  - candidate_path
  - target_path
  - source_refs
  - source_package_id
  - verification_status
  - knowledge_class
  - index_update_targets
  - promotion_reason
  - operator_approval_ref
  - control_plane_request_ref
outputs:
  - promoted_note_path
  - index_update_paths
  - provenance_check_result
  - approval_linkage_record
  - audit_record_path
approval_rule: operator-explicit
rollback_path: "remove bounded writeback outputs from this run if promotion is rejected before finalization"
audit_expectations:
  - "approval envelope reference recorded"
  - "provenance minimum result recorded"
  - "canonical write target recorded"
  - "index update evidence recorded"
```

### Hermes role-card intent
This role card should:
- permit declared-source review and bounded canonical write only through approved control-plane posture
- forbid Discord/gateway text from being treated as direct write authority
- preserve Hermes’s stronger control-plane and bounded-workflow posture

### Proposed role-card shape

```yaml
id: hermes-promotion-review
name: "Hermes Promotion Review Role Card"
version: "1.0"
description: "Permission envelope for one bounded Hermes promotion-review workflow."
owner: operator
allowed_actions:
  - read_declared_candidate
  - read_declared_sources
  - read_declared_indexes
  - read_control_plane_approval_record
  - write_bounded_canonical_note
  - write_bounded_index_update
  - write_promotion_log
  - write_agent_activity_log
forbidden_actions:
  - ambient_vault_write
  - direct_discord_driven_write
  - write_protected_files
  - shell_expansion
  - connector_expansion
  - multi_repo_access
  - autonomous_promotion
write_scope:
  - "02_KNOWLEDGE/"
  - "07_LOGS/Agent-Activity/"
  - "07_LOGS/Build-Logs/"
forbidden_write_zones:
  - "SOUL.md"
  - "CLAUDE.md"
  - "00_HOME/"
  - "01_PROJECTS/"
  - "06_AGENTS/"
  - "runtime/"
escalation_rules:
  - "approval envelope missing or invalid"
  - "provenance minimums fail"
  - "target outside declared canonical scope"
  - "index update target not declared"
  - "attempted write outside write_scope"
  - "Discord/control-plane input treated as direct authority"
runtime_expectations:
  - "AOR stages execute before writeback"
  - "Gate provenance minimums are checked centrally"
  - "control-plane approval linkage is recorded"
  - "Hermes remains non-autonomous for promotion"
required_reads:
  - "candidate_path (declared at runtime)"
  - "source_refs (declared at runtime)"
  - "control_plane_request_ref (declared at runtime)"
optional_reads:
  - "index_update_targets (declared at runtime)"
```

---

## 4. Shared Task-Type Direction

Both pairs imply a future task type such as:
- `promotion-review`

This task type would need to encode:
- read-heavy + bounded canonical write posture
- mandatory approval linkage
- mandatory provenance minimum checks
- mandatory audit logging
- fail-closed escalation on any undeclared target

This task type is **not** activated by this pass.

---

## 5. Equal Authority, Runtime-Specific Readiness

Even though the two runtime instances may still differ in local implementation readiness, ChaseOS now treats them as equal-authority peers under `06_AGENTS/Runtime-Instance-Authority-Parity.md`.

That means:
- symmetric contract definition reflects the constitutional model correctly
- readiness validation may still be runtime-specific
- sequencing differences must not be described as lower authority for Hermes

---

## 6. Canonical Pre-Activation Helper Comparison

The pair-level substrate is no longer just symmetric at the manifest/role-card layer.
ChaseOS now also has **runtime-specific canonical helper surfaces** for reading pre-activation failure posture directly from live draft-contract truth.

### OpenClaw canonical helper
- `runtime/aor/promotion_readiness.py::collect_openclaw_preactivation_failure_signals(...)`

This helper is the canonical read-only inspection surface for whether the still-draft OpenClaw contract already declares:
- approval-linkage failure posture
- exact target-scope failure posture
- audit-survival expectations for blocked runs

### Hermes canonical helper
- `runtime/aor/promotion_readiness.py::collect_hermes_preactivation_failure_signals(...)`

This helper is the canonical read-only inspection surface for whether the still-draft Hermes contract already declares:
- approval-linkage failure posture
- control-plane linkage posture
- direct-authority denial for Discord/control-plane input
- exact target-scope failure posture
- audit-survival expectations for blocked runs

### Shared interpretation rule
These helper surfaces are intentionally parallel but not flattened.

They are both:
- read-only contract inspection helpers
- non-executing and non-authorizing
- subordinate to AOR/Gate governance
- compatible with equal runtime-instance authority and runtime-specific readiness detail

They do **not**:
- activate the workflow manifests
- bypass the centralized Gate seam
- change adapter fail-closed posture
- grant canonical promotion authority to either runtime instance

That means ChaseOS now has a clean pair-level answer to two different OS questions:
- **Do OpenClaw and Hermes have equal constitutional authority?** Yes.
- **Can their pre-activation failure posture still differ in runtime-specific detail?** Also yes.

## 7. Current Verdict

ChaseOS now has the next concrete layer of the runtime-instance provenance promotion story:
- first bounded promotion-path contracts for OpenClaw and Hermes
- and now the first proposed workflow/role-card pairs each path would require

The next substrate layer now exists as draft-only implementation artifacts:
- `runtime/workflows/registry/openclaw_promote_note.yaml`
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml`
- `runtime/workflows/registry/hermes_promote_note.yaml`
- `06_AGENTS/role-cards/hermes-promotion-review.yaml`
- `runtime/aor/task_type_table.yaml` (`promotion-review` row)

Focused validation for that draft substrate now also exists:
- `runtime/aor/test_runtime_instance_promotion_drafts.py` (now also asserts OpenClaw and Hermes promotion-record scope at the pair-validation layer, promotion-review task-type cross-link alignment, output/audit/build-log lane distinction, canonical helper-signal dimensions for both runtimes, explicit approval-input requirements (`operator_approval_ref` for both plus `control_plane_request_ref` for Hermes), runtime-specific plus shared escalation-rule structure, shared execution controls plus audit expectations, required/optional read structure, shared forbidden-boundary structure, manifest/role-card identity plus draft-doctrine alignment, shared plus runtime-specific `runtime_expectations` structure, shared plus runtime-specific allowed-action structure, the shared blocked-activation dimensions that keep both readiness helpers at `ready: false`, and the shared readiness-substrate invariants such as fail-closed adapter posture, centralized provenance-gate seam presence, and on-disk promotion-record routing substrate)
- `runtime/aor/test_runtime_instance_promotion_engine_drafts.py`
- `runtime/aor/test_openclaw_promotion_activation_readiness.py`
- `runtime/aor/test_hermes_promotion_activation_readiness.py`
- `runtime/aor/test_openclaw_promotion_preactivation_failures.py`
- `runtime/aor/test_hermes_promotion_preactivation_failures.py`
- `runtime/aor/promotion_readiness.py` (`assess_openclaw_promotion_activation_readiness(...)` + `collect_openclaw_preactivation_failure_signals(...)` for OpenClaw, and `assess_hermes_promotion_activation_readiness(...)` + `collect_hermes_preactivation_failure_signals(...)` for Hermes)

OpenClaw's draft contract now also explicitly declares the promotion-record lane while remaining non-runnable and non-authoritative:
- `runtime/workflows/registry/openclaw_promote_note.yaml` now includes `07_LOGS/Promotion-Records/`
- `06_AGENTS/role-cards/openclaw-promotion-review.yaml` now includes `07_LOGS/Promotion-Records/` plus `write_promotion_record`
- the readiness helper still reports activation blocked because the workflow remains `draft` and the adapter manifest remains fail-closed

Hermes's draft contract now also explicitly declares the promotion-record lane while remaining non-runnable and non-authoritative:
- `runtime/workflows/registry/hermes_promote_note.yaml` now includes `07_LOGS/Promotion-Records/`
- `06_AGENTS/role-cards/hermes-promotion-review.yaml` now includes `07_LOGS/Promotion-Records/` plus `write_promotion_record`
- the readiness helper still reports activation blocked because the workflow remains `draft` and the adapter manifest remains fail-closed

The next parity-safe runtime-specific pre-activation gates now also exist:
- `06_AGENTS/OpenClaw-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Hermes-Promotion-Activation-Readiness-Gate.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`
- `07_LOGS/Promotion-Records/`

This keeps the architecture moving forward without pretending either runtime already has canonical promotion authority.

---

*Graph links: [[OpenClaw-First-Bounded-Promotion-Path]] · [[Hermes-First-Bounded-Promotion-Path]] · [[OpenClaw-Promotion-Activation-Readiness-Gate]] · [[Hermes-Promotion-Activation-Readiness-Gate]] · [[Runtime-Instance-Authority-Parity]] · [[Runtime-Instance-Provenance-Promotion-Caller-Alignment]] · [[OpenClaw-Adapter-Spec]] · [[Hermes-Adapter-Spec]] · [[Vault-Map]]*