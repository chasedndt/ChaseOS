# Personal Map Architecture

**Status:** PARTIAL - first schema pass  
**Created:** 2026-04-29  
**Runtime scaffold:** `runtime/memory/personal_map.py`, `runtime/memory/candidate_store.py`

## Purpose

The Personal Map is the user profile graph that lets ChaseOS Pulse reason over
the operator's current identity, goals, projects, constraints, skills, habits,
preferences, commitments, and relevant events.

Operator-facing personal context is grouped in
[[00_HOME/Personal-Operator-Index|Personal Operator Index]]. Use that index to
review current identity, domains, project operating files, doctrine, and update
templates before proposing Personal Map candidates.

It is not a hidden model memory. It is inspectable, evidence-linked, and
subordinate to ChaseOS governance.

## Distinction From Other Maps

| Surface | Purpose |
|---|---|
| Vault Map | Shared ChaseOS map for where files, logs, runtime docs, governance surfaces, and project truth live |
| Personal Map | User profile graph for what the operator does, values, studies, builds, trades, publishes, and wants to prioritize |
| Runtime Navigation Map | Per-runtime route overlay for how a specific runtime has learned to navigate ChaseOS safely |

The Personal Map is about the user, not file location. It can reference Vault
Map paths as evidence, but it must not replace the Vault Map or grant runtime
navigation authority.

## Graph Objects

### Node

First-pass node types:

- `person`
- `goal`
- `project`
- `domain`
- `value`
- `doctrine`
- `habit`
- `cadence`
- `skill`
- `constraint`
- `preference`
- `commitment`
- `event`
- `business_os`
- `learning_map`
- `content_map`
- `trading_map`

Representative Personal Map domains include ChaseOS, Business OS, University,
Learning, Trading, Content / Brand, AI Engineering, Software Engineering,
Cybersecurity, Personal Doctrine, and Runtime Agents.

Required node fields:

- `node_id`
- `node_type`
- `label`
- `summary`
- `evidence`
- `tags`
- `updated_at`
- `status`

### Edge

Edges express relationships such as:

- `builds`
- `depends_on`
- `supports`
- `conflicts_with`
- `prefers`
- `requires_review`
- `learns`
- `belongs_to`

Required edge fields:

- `edge_id`
- `source_node_id`
- `target_node_id`
- `relation`
- `evidence`
- `confidence`

## Pulse Usage

Pulse can use the Personal Map to produce:

- Personal Map Update cards
- Future Prep cards
- Project Momentum cards
- Learning / University Focus cards
- Business OS Opportunity cards
- Memory Drift Warning cards when profile evidence conflicts

Example Business OS nodes can include Drip and Drown Town UK, E-commerce
Centre, Shopify upload workflows, WordPress workflows, product metadata,
product-image/video requirements, and Content / Brand Edge. These are profile
and workflow context nodes, not canonical business records unless reviewed.

## Governance Rules

- Personal Map updates are candidates by default.
- A Pulse card can recommend a Personal Map update, but cannot apply it.
- Personal Map evidence must reference local ChaseOS sources or explicitly
  enabled connector evidence.
- Personal Map cannot override `00_HOME/Now.md`, project truth, or system
  doctrine.
- Sensitive or personal claims require review before becoming accepted nodes.

## Candidate Store

Personal Map candidate persistence is now scaffolded as append-only Pulse log
artifacts:

- `07_LOGS/Pulse-Decks/memory-candidates/personal-map/YYYY-MM-DD-personal-map-candidates.jsonl`

The store supports pending-review node and edge candidates plus a read-only
queue snapshot. It does not mutate the Personal Map graph, approve memory, create
tasks, write Project-OS files, promote knowledge, or write a second datastore.

## Personal Context Import Boundary

Personal context imports can propose Personal Map candidates, but they do not
apply Personal Map memory.

Current Studio context-import implementation is preview-only:
`runtime/studio/personal_context_import.py` and
`06_AGENTS/Personal-Context-Import-Feature.md` describe raw intake, parent/child
node extraction, routing, secure storage, and future candidate staging. Any
candidate created from an import must land in the candidate store first, remain
pending review, and wait for the governed review/apply lane before becoming
accepted profile graph state.

## Implementation Status

| Surface | Status |
|---|---|
| Node schema | PARTIAL |
| Edge schema | PARTIAL |
| Graph container | PARTIAL |
| Candidate persistence | PARTIAL - pending-review JSONL artifacts only |
| Applied persistence | NOT BUILT |
| Inspector UI | NOT BUILT |
| Automatic profile mutation | NOT BUILT |

## Next Pass

Define the operator review workflow for Personal Map candidates before any
persistent map mutation is enabled.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]] . [[00_HOME/Personal-Operator-Index|Personal Operator Index]]*
