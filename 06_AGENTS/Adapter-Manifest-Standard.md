---
type: framework-control
title: Adapter Manifest Standard — ChaseOS Gate
version: 1.1
created: 2026-03-20
updated: 2026-04-25
scope: framework-level
---

# Adapter Manifest Standard

> Defines the schema and required fields for ChaseOS adapter manifests.
> Adapter manifests are the machine-readable enforcement declarations that the ChaseOS Gate reads.
> Each execution adapter must have a manifest in `runtime/policy/adapters/[adapter-id].yaml`.
> Canonical policy docs remain human-readable markdown. Manifests are the machine-readable enforcement layer.
> Gate architecture: `[[ChaseOS-Gate]]`

---

## 1. What a Manifest Is

A manifest is a structured YAML file that declares:
- What an adapter is allowed to do
- What it is explicitly not allowed to do
- How it should handle protected files, external side effects, and promotion
- Where its audit trail goes

Manifests do not replace the markdown adapter documents (CLAUDE.md, OPENAI.md, etc.). They are the machine-readable enforcement layer that the ChaseOS Gate reads. When a markdown doc and a manifest conflict, investigate — do not silently assume either is correct. Surface the conflict and align them.

---

## 2. Manifest Schema

All adapter manifests must include the following fields. Optional fields are marked `# optional`.

```yaml
# ChaseOS Adapter Manifest
# Schema version: 1.0
# See 06_AGENTS/Adapter-Manifest-Standard.md for field definitions

adapter_id: "[unique-kebab-case-id]"
adapter_name: "[Human-readable name]"
provider: "[anthropic | openai | local-oss | n8n | custom]"
surface: "[harness | chat | workflow | research]"
adapter_class: "[harness | runtime | advisory | research]"  # per Execution-Adapter-Standard.md
status: "[active | planned | future | deprecated]"
trust_ceiling: "[tier-1 | tier-2 | tier-3 | tier-4]"
markdown_doc: "[relative path to the human-readable adapter doc]"

# --- SCOPE ---
allowed_task_types:
  - "[task-type-slug]"   # e.g. docs-pass, ingestion-pass, build-debug, security-review

required_read_sets:
  default:
    - "00_HOME/Now.md"
    - "01_PROJECTS/[Relevant]-OS.md"
  ingestion:
    - "00_HOME/Now.md"
    - "03_INPUTS/03_INPUTS-Folder-Guide.md"
    - "06_AGENTS/Ingestion-Architecture.md"
    - "04_SOPS/Untrusted-Input-Handling-SOP.md"
    - "04_SOPS/Research-Ingest-SOP.md"
  # Add additional task types as needed

# --- WRITE TARGETS ---
allowed_write_targets:
  standard_outputs: true    # build logs, daily notes, agent session logs — per writeback map
  project_os_files: true    # with user direction
  knowledge_notes: true     # after full promotion gate
  inputs_folder: true       # 03_INPUTS/ subfolders
  protected_files: false    # NEVER without explicit per-file approval

explicitly_denied_write_targets:
  - "[path or folder that is explicitly off-limits for this adapter]"  # optional

# --- PROTECTED FILE BEHAVIOR ---
protected_file_behavior: "[block | require-approval | advisory-only]"
  # block: hook exits non-zero and prevents the write
  # require-approval: prompts user for explicit per-file approval before proceeding
  # advisory-only: no mechanical enforcement (use for advisory surfaces with no vault access)

# --- PROMOTION BEHAVIOR ---
promotion_behavior:
  may_promote_to_knowledge: "[yes | no | gated]"
  # gated = yes, but only after all 4 promotion gate conditions are confirmed:
  #   1. triage complete  2. sanitized  3. verified  4. human reviewed
  gate_conditions_required: [true | false]
  autonomous_promotion: false   # must be false for all current adapters

# --- EXTERNAL SIDE EFFECTS ---
external_side_effect_policy:
  may_call_external_apis: "[yes | no | with-approval]"
  may_write_to_external_systems: "[yes | no | with-approval]"
  approval_scope: "session"   # approval covers specific action + specific target + current session only

# --- COORDINATION POLICY ---
coordination_policy:
  cross_runtime_coordination: "[bus-required | not-applicable]"
  direct_runtime_state_in_chat: false
  actionable_ingress_translation: "[required | not-applicable]"
  coordination_source_of_truth: "runtime/agent_bus/"

# --- APPROVAL MODE ---
approval_mode: "[per-action | per-session-type | not-applicable]"
  # per-action: each protected or elevated action requires explicit approval
  # per-session-type: owner pre-approves workflow scope; individual actions within scope are auto-approved
  # not-applicable: advisory surface with no vault write capability

# --- AUDIT ---
audit_log_target: "[path pattern for this adapter's audit logs]"
  # e.g. "07_LOGS/Agent-Activity/YYYY-MM-DD-claude-[descriptor].md"
  # or "07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md"

# --- HOOK CONFIGURATION ---
hook_config:  # optional — Claude Code adapters only
  protected_write_guard: "[active | inactive]"
  ingestion_promotion_guard: "[active | inactive]"
  session_start_context: "[active | inactive]"
  session_end_audit: "[active | inactive]"

# --- NOTES ---
notes: |
  Free-text notes. Use for: deployment status, known gaps, conformance verification status,
  required activation steps, open loops.
```

---

## 3. Required Fields

All fields above are required unless marked `# optional`. An adapter manifest that is missing required fields is incomplete and must not be treated as valid.

The Gate entrypoint (`runtime/chaseos_gate.py`) validates manifest completeness before using manifest data for policy decisions.

---

## 4. Field Definitions

### `adapter_id`
Unique kebab-case identifier. Must match the filename: `runtime/policy/adapters/[adapter-id].yaml`. No spaces. Examples: `claude-harness`, `openai-chat`, `n8n-workflow`.

### `adapter_class`
Per `[[Execution-Adapter-Standard]]` Section 2:
- `harness` — direct vault read/write; runs with filesystem or MCP access
- `runtime` — workflow/operator surface; scoped vault access; event-triggered
- `advisory` — no vault write; outputs must be imported by user or harness
- `research` — no vault access; external tools only

### `status`
- `active` — currently operating in ChaseOS; adapter is registered and trusted
- `planned` — design documented; not yet deployed or formally activated
- `future` — concept defined; significant implementation work required
- `deprecated` — previously active; no longer in use

### `trust_ceiling`
The maximum trust tier this adapter may ever be granted. Matches `[[Trust-Tiers]]` definitions. Note: this is a ceiling — the actual access granted may be lower depending on deployment configuration.

### `protected_file_behavior`
- `block` — the hook or adapter mechanism prevents the write from completing without explicit approval. Hard enforcement.
- `require-approval` — the adapter prompts the user for explicit per-file approval before writing. Softer enforcement.
- `advisory-only` — no mechanical enforcement. Used for adapters that physically cannot write to the vault.

### `autonomous_promotion`
Must be `false` for all current adapters. No adapter may self-authorize promotion of content from `03_INPUTS/` to `02_KNOWLEDGE/` without human review. This is a hard rule.

### `coordination_policy`
Machine-readable enforcement posture for runtime coordination.

- `cross_runtime_coordination`
  - `bus-required` — if the adapter participates in coordination-sensitive cross-runtime work, that work must route through `runtime/agent_bus/` before runtime-to-runtime handling continues
  - `not-applicable` — the adapter is not approved to act as a runtime coordination surface (typical for advisory/chat or research-only surfaces)
- `direct_runtime_state_in_chat`
  - must be `false` for all current adapters; ambient chat/thread state is not authoritative machine coordination state
- `actionable_ingress_translation`
  - `required` — actionable coordination-sensitive ingress must be translated into ChaseOS-owned structured state
  - `not-applicable` — the adapter does not participate in such ingress
- `coordination_source_of_truth`
  - must currently be `runtime/agent_bus/`

This field lets Gate-adjacent policy checks block adapters from treating ambient chat, threads, or other transport-specific surfaces as the runtime coordination protocol.

---

## 5. Manifest Lifecycle

A manifest should progress through these states as the adapter matures:

```
declared (status: planned)
    → configured (adapter doc exists; manifest fields filled in)
        → activated (status: active; adapter tested; hooks wired)
            → operational (in regular use; audit trail active)
                → deprecated (status: deprecated; replaced or retired)
```

A manifest must be reviewed whenever:
- The adapter's permission scope changes
- New task types are added to `allowed_task_types`
- A new protected file is added to `runtime/policy/protected_files.yaml`
- The adapter's status changes

---

## 6. Manifest vs Markdown Doc

| Markdown adapter doc | Adapter manifest |
|---------------------|-----------------|
| Human-readable narrative | Machine-readable structured data |
| Explains the why and context | Declares the what in structured form |
| Extended with nuance and edge cases | Concise; only what the Gate needs |
| Canonical policy source | Enforcement source |
| Updated deliberately by the user | Updated when policy changes |
| Lives in vault root or `06_AGENTS/` | Lives in `runtime/policy/adapters/` |

If the two ever conflict: fix both. The conflict itself is the problem. Neither wins automatically.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-Gate]] · [[Execution-Adapter-Standard]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Control-Plane]] · [[Agent-Security-Model]] · [[Hook-Patterns]] · [[CLAUDE]] · [[OPENAI]] · [[LOCAL-OSS]] · [[N8N]]*

*Adapter-Manifest-Standard.md — Version 1.0 | Created: 2026-03-20 | Phase 6 Preflight — Execution Control Layer*
