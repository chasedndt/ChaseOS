# Agent Runtime Brain Architecture

**Status:** PARTIAL - schema-first scaffold  
**Created:** 2026-04-29  
**Runtime scaffold:** `runtime/agents/runtime_brain.py`, `runtime/agents/repair_candidate_store.py`

## Purpose

The Agent Runtime Brain layer gives each runtime an inspectable advisory brain:
runtime profile, reflection history, Pulse deck references, skill gaps,
permission requests, workflow improvement candidates, and repair cues.

This is Layer C runtime memory. It is not personality, not hidden authority, and
not an autonomous self-upgrade system.

## Runtime Brain Index Fields

Agent runtime brains must be able to record:

- known strengths
- known weaknesses
- repeated blockers
- successful repair patterns
- skill gaps
- workflow preferences
- permission issues
- drift signals
- next improvement candidates
- runtime navigation map references
- agent identity ledger references
- execution repair memory references
- runtime Pulse history references

These fields are advisory operating memory. They do not override role cards,
Gate policy, permission matrices, schedule manifests, or current repo truth.

## Brain Objects

### Runtime Profile

Owned by AgentHub. Defines:

- runtime ID
- provider
- execution surface
- access mode
- trust tier / authority ceiling
- status
- allowed task families
- memory surfaces
- policy references
- forbidden actions

### Runtime Reflection

Captures one bounded observation about runtime behavior.

Examples:

- a workflow stayed inside declared scope
- a recurring error cluster appeared
- a skill gap was observed
- a permission request needs operator review
- a workflow should get an SOP

### Agent Pulse Deck

Agent-facing Pulse cards can include:

- Runtime Reflection
- Error Cluster
- Skill Gap
- Permission Request
- Workflow Improvement
- SOP Needed
- Tool Needed
- Connector Needed
- Self-Upgrade Proposal
- Memory Drift Warning
- Execution Repair Pattern
- Runtime Navigation Update
- Capability Gap
- Autonomy Envelope Suggestion

### Execution Repair Memory

Execution Repair Memory is mandatory for runtime learning. When a runtime fails
during browser work, repo work, connector work, or autonomous workflow execution
and finds a workaround, that failure/fix pattern must be logged as reusable
runtime memory.

Minimum fields:

- `repair_id`
- `runtime_id`
- `workflow_id`
- `failure_surface`
- `failure_type`
- `failure_summary`
- `resolution_summary`
- `repair_pattern`
- `source_logs`
- `promotion_status`
- `requires_user_review`
- `canonical_writeback_enabled`

Execution Repair Memory can produce Agent Pulse cards, SOP candidates, runtime
navigation map candidates, or manual input cards. It cannot silently update
SOPs, grant tools, invoke connectors, expand permissions, or promote knowledge.

The first repair candidate store writes pending-review JSONL artifacts under:

- `07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/<runtime_id>/YYYY-MM-DD-repair-candidates.jsonl`

This queue is read-only at inspection time and blocks runtime memory mutation,
Runtime Navigation Map updates, Agent Identity Ledger updates, SOP creation,
tool/connector grants, permission expansion, canonical writeback, and second
datastore writes.

### Business OS Repair Example

If an OpenFlow/OpenClaw-style browser runtime repeatedly blocks on Shopify
uploads because product images, product video, or product metadata are missing,
the runtime brain should record:

- repeated blocker: missing required product assets
- successful repair pattern: stop upload, create Manual Input Needed card,
  defer publishing, and add preflight recommendation
- skill gap: image/video generation or metadata normalization connector needed
- next improvement candidate: Shopify Product Upload Preflight SOP

## Self-Upgrade Boundary

Self-upgrade proposals may be represented as cards, but self-upgrade is not
active. A proposal must be operator-reviewed and routed through normal ChaseOS
governance before any runtime behavior changes.

## Implementation Status

| Surface | Status |
|---|---|
| Runtime brain dataclass | PARTIAL |
| Runtime reflection dataclass | PARTIAL |
| Execution repair memory dataclass | PARTIAL |
| Execution repair candidate store | PARTIAL - append-only pending-review logs |
| Agent Pulse card conversion | PARTIAL |
| Autonomous self-upgrade | NOT BUILT |
| Automatic skill creation | NOT BUILT |
| Permission expansion | NOT BUILT |

## Next Pass

Connect runtime reflections to existing Agent Activity logs and Layer C memory
inspectors in read-only mode.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
