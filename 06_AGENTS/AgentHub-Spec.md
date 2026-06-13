# AgentHub Spec

**Status:** PARTIAL - first schema pass  
**Created:** 2026-04-29  
**Runtime scaffold:** `runtime/agents/agent_hub.py`, `runtime/agents/runtime_profile.py`, `runtime/agents/repair_candidate_store.py`

## Definition

AgentHub is the ChaseOS-owned profile and brain registry for runtimes. It is a
metadata and inspection layer. It does not create authority.

AgentHub connects:

- runtime registry records
- runtime profiles
- runtime brain indexes
- runtime navigation maps
- agent identity ledgers
- execution repair memory
- runtime reflection logs
- skill gap registers
- runtime Pulse decks and history
- runtime memory surfaces
- policy references
- feedback and repair candidates

## Required Runtime Profile Fields

- `runtime_id`
- `provider`
- `execution_surface`
- `access_mode`
- `trust_tier`
- `status`
- `authority`
- `allowed_task_families`
- `allowed_actions`
- `forbidden_actions`
- `memory_surfaces`
- `policy_refs`
- `canonical_promotion_authority`

## Required Runtime Brain Fields

- `runtime_id`
- `profile`
- `reflections`
- `pulse_deck_refs`
- `runtime_pulse_history_refs`
- `known_strengths`
- `known_weaknesses`
- `repeated_blockers`
- `successful_repair_patterns`
- `skill_gap_notes`
- `workflow_preferences`
- `permission_requests`
- `permission_issues`
- `drift_signals`
- `next_improvement_candidates`
- `runtime_navigation_map_refs`
- `agent_identity_ledger_refs`
- `execution_repair_memory_refs`
- `self_upgrade_active`

## Required AgentHub Surfaces

| Surface | Purpose | Status |
|---|---|---|
| Runtime Registry | Declares runtime IDs, adapter families, and registration metadata | PARTIAL facade in `runtime/agents/agent_hub.py` |
| Runtime Profile | Defines bounded runtime identity, trust ceiling, scopes, and forbidden actions | PARTIAL schema |
| Runtime Brain Index | Advisory learned runtime operating state | PARTIAL schema fields |
| Runtime Navigation Map | Runtime-specific route overlay for safe navigation and repair routes | Referenced only; existing Layer C lane |
| Agent Identity Ledger | Behavioral history, doctrine adherence, drift, strengths/weaknesses | Referenced only; existing Layer C lane |
| Execution Repair Memory | Reusable failure/workaround patterns | PARTIAL schema in `runtime/agents/execution_repair_memory.py` |
| Execution Repair Candidate Store | Pending-review repair memory candidates | PARTIAL append-only log in `runtime/agents/repair_candidate_store.py` |
| Runtime Reflection Log | Bounded reflections from executions | PARTIAL reflection dataclass |
| Skill Gap Register | Missing skills/tools/connectors detected from runtime work | PARTIAL list fields |
| Runtime Pulse History | Agent Pulse deck references over time | PARTIAL reference fields |

## Governance Rules

- Registration does not grant write access.
- A runtime profile cannot grant canonical promotion authority.
- A runtime brain cannot activate self-upgrade.
- Runtime memory remains advisory and subordinate to role cards, Gate policy,
  workflow manifests, and current repo truth.
- AgentHub must read existing profiles before creating duplicates.

## Relationship To Existing Runtime Systems

AgentHub complements:

- `runtime/aor/runtime_registry/` - lifecycle and policy binding records
- `runtime/memory/adapters/` - Layer C runtime profile and identity ledger files
- `runtime/memory/nav/` - Runtime Navigation Map overlays
- `runtime/memory/repair/` - execution repair memory
- `runtime/memory/scorecards/` - runtime scorecards
- `07_LOGS/Agent-Activity/` - execution/audit history
- `07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/` - pending-review repair memory candidates

## Implementation Status

| Surface | Status |
|---|---|
| RuntimeProfile schema | PARTIAL |
| AgentRuntimeBrain schema | PARTIAL |
| ExecutionRepairMemoryEntry schema | PARTIAL |
| ExecutionRepairMemoryCandidate store | PARTIAL - pending-review JSONL artifacts and read-only queue |
| AgentHub facade | PARTIAL |
| Persistent AgentHub store | NOT BUILT |
| Runtime onboarding integration | NOT BUILT in this pass |
| Authority expansion | NOT BUILT |

## Next Pass

Map AgentHub schema to the existing runtime registry and memory adapters without
duplicating runtime profile paths.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
