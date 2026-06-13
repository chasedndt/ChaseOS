# Context Memory Core

**Status:** PARTIAL - schema-first scaffold  
**Created:** 2026-04-29  
**Runtime scaffold:** `runtime/memory/context_events.py`, `memory_atoms.py`, `memory_clusters.py`, `temporal_facts.py`, `feedback_rules.py`, `candidate_store.py`

## Purpose

Context Memory Core is the structured memory substrate Pulse uses to turn
operator history, feedback, active project state, and runtime evidence into
inspectable memory candidates.

It extends the existing Layer B/C/D/E memory doctrine without replacing it:

- Layer B - user/operator context memory
- Layer C - runtime-specific behavior memory
- Layer D - task-local context
- Layer E - execution/audit history

## Content / Context / Memory / Pulse Boundary

| Term | Meaning | Storage posture |
|---|---|---|
| Content | Raw or processed material: articles, PDFs, videos, transcripts, source packages, captures, chat logs, build logs, and agent logs | Capture/ingestion surface; not automatically memory |
| Context | The subset of content/state relevant to a project, day, workflow, runtime, or decision | Context event or selected signal |
| Memory | Durable extracted understanding: preferences, goals, constraints, patterns, doctrine, temporal facts, runtime lessons | Candidate-first memory atom/cluster/fact |
| Pulse | Proactive synthesis over context and memory that decides what matters next | Card/deck output; not canonical truth |

Context Memory Core records events and candidates so Pulse can learn without
dumping unreviewed material into `02_KNOWLEDGE/`.

## Core Objects

### Context Event

A context event records something observed, corrected, decided, or fed back.

Required fields:

- `event_id`
- `event_type`
- `summary`
- `source_path`
- `source_type`
- `observed_at`
- `trust_label`
- `evidence`
- `related_nodes`

Allowed first-pass event types:

- `observation`
- `correction`
- `decision`
- `preference`
- `feedback`
- `project_state`
- `schedule`
- `runtime_reflection`

### Memory Atom

A memory atom is a candidate durable memory unit. It may represent a user
preference, recurring operating pattern, runtime tendency, or task-local lesson.

Required fields:

- `atom_id`
- `layer`
- `scope`
- `content`
- `status`
- `promotion_state`
- `evidence`
- `related_event_ids`
- `related_node_ids`

Memory atoms are candidates by default. They do not become canonical truth until
a separate governed promotion/review path validates them.

### Memory Cluster

A memory cluster groups related memory atoms into an operating domain or pattern
used by Pulse topic selection.

Required fields:

- `cluster_id`
- `label`
- `status`
- `memory_ids`
- `related_projects`
- `related_agents`
- `related_card_types`
- `evidence`
- `canonical_writeback_enabled`

Clusters remain candidate/advisory until reviewed. They do not promote their
member atoms.

### Temporal Fact

A temporal fact records something whose truth has a validity window.

Required fields:

- `fact_id`
- `summary`
- `valid_from`
- `valid_until`
- `source_event_ids`
- `related_node_ids`
- `evidence`
- `confidence`
- `status`
- `canonical_writeback_enabled`

Temporal facts help Pulse reason about what is current, stale, expired, or
superseded without overwriting canonical project truth.

### Feedback Rule Result

Feedback rules determine whether operator feedback should:

- dismiss a card
- correct a card
- create a memory candidate
- create a personal map candidate
- require operator review

Feedback rules never grant canonical writeback directly.

### Durable Feedback Rule

A durable feedback rule records a candidate preference or ranking rule inferred
from governed feedback. Examples:

- suppress generic AI news unless tied to an active ChaseOS build lane
- boost agent runtime blockers
- link a recurring card class to a project, Personal Map node, or agent brain
- create a memory candidate from `promote_to_memory`

Required fields:

- `rule_id`
- `rule_type`
- `target_type`
- `target`
- `scope`
- `weight_delta`
- `condition`
- `source_card_id`
- `status`
- `canonical_writeback_allowed`

Feedback rules remain candidates or governed rules. They do not approve memory,
create tasks, mutate projects, or promote knowledge by themselves.

### Personal Map Candidate Store

The first persistent Context Memory Core candidate store is append-only and
pending-review only:

- `07_LOGS/Pulse-Decks/memory-candidates/personal-map/YYYY-MM-DD-personal-map-candidates.jsonl`

It stores proposed Personal Map nodes and edges as Pulse log artifacts. It does
not apply Personal Map updates, approve memory, create tasks, mutate project
files, promote `02_KNOWLEDGE/`, or write a second datastore.

## Writeback Boundary

Context Memory Core may produce:

- memory candidates
- personal map candidates
- card ranking hints
- evidence bundles
- review queues

Context Memory Core must not:

- auto-promote to `02_KNOWLEDGE/`
- mutate `00_HOME/Now.md`
- mutate Project-OS files
- overwrite existing runtime profiles
- treat feedback as verified truth without review

## Implementation Status

| Runtime file | Status |
|---|---|
| `runtime/memory/context_events.py` | PARTIAL - dataclass schema |
| `runtime/memory/memory_atoms.py` | PARTIAL - dataclass schema |
| `runtime/memory/memory_clusters.py` | PARTIAL - dataclass schema |
| `runtime/memory/temporal_facts.py` | PARTIAL - dataclass schema |
| `runtime/memory/feedback_rules.py` | PARTIAL - feedback decision helper and durable rule candidate schema |
| `runtime/memory/candidate_store.py` | PARTIAL - append-only pending-review Personal Map candidate logs and read-only queue |
| `runtime/memory/test_memory_schema.py` | PARTIAL - focused tests |
| `runtime/memory/test_memory_cluster_temporal_schema.py` | PARTIAL - focused tests |
| `runtime/memory/test_candidate_store.py` | PARTIAL - focused candidate-store tests |

## Next Pass

Define the operator review/apply lane for Context Memory Core candidates before
any write-side workflow is enabled. Review decisions must stay separate from
automatic memory approval, Personal Map mutation, task creation, and canonical
writeback.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
