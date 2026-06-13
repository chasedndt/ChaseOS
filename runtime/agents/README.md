# runtime/agents/

Schema-first AgentHub and runtime brain scaffold for ChaseOS Pulse.

This package defines:

- `runtime_profile.py` - bounded runtime profile records.
- `runtime_brain.py` - advisory runtime brain and reflection records.
- `execution_repair_memory.py` - reusable runtime failure/workaround patterns.
- `repair_candidate_store.py` - append-only pending-review execution repair
  memory candidates under `07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/`.
- `agent_hub.py` - local registry facade for profiles and brains.

AgentHub does not register new runtime authority, grant permissions, promote
outputs, or activate agent self-upgrade. It is a shape for future governed
runtime profile inspection and Pulse agent decks.

Runtime brain fields are intentionally advisory: known strengths, known
weaknesses, repeated blockers, successful repair patterns, skill gaps, workflow
preferences, permission issues, drift signals, runtime navigation map refs,
identity ledger refs, execution repair memory refs, and next improvement
candidates do not change permissions or canonical truth.

Repair candidates are review artifacts only. The store does not apply runtime
memory, update Runtime Navigation Maps, write Agent Identity Ledgers, create
SOPs, grant tools/connectors, expand permissions, or promote knowledge.
