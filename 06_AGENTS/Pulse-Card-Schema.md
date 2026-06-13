# Pulse Card Schema

**Status:** PARTIAL - runtime dataclass scaffold exists  
**Created:** 2026-04-29  
**Runtime scaffold:** `runtime/pulse/card_schema.py`

## Purpose

Pulse cards are the unit of proactive intelligence in ChaseOS Pulse. A card is
evidence-linked, audience-scoped, action-aware, and feedback-enabled.

Cards are proposal/briefing artifacts. They are not canonical knowledge.

## Required Card Fields

- `card_id`
- `deck_id`
- `created_at`
- `audience`
- `scope`
- `card_class`
- `type`
- `title`
- `summary`
- `why_it_matters`
- `generated_at`
- `evidence`
- `source_links`
- `related_nodes`
- `thumbnails`
- `recommended_actions`
- `feedback`
- `urgency`
- `confidence`
- `promotion_status`
- `writeback_status`
- `governance_state`
- `canonical_writeback_enabled`

Runtime JSON keeps `card_class` as the display/taxonomy label and adds `type`
as the stable machine-style card type, for example `Manual Input Needed` maps
to `manual_input_needed`.

## Scope Fields

- `user_id`
- `agent_id`
- `project_ids`
- `coordination_ids`

## Evidence Fields

- `source_path`
- `source_type`
- `summary`
- `trust_label`
- `observed_at`
- `quote`
- `source_url`

Evidence can point to vault files, runtime artifacts, build logs, source
intelligence outputs, personal map nodes, runtime profiles, or explicitly
enabled connector artifacts.

## Source Link Fields

- `label`
- `path`
- `url`
- `source_type`

Evidence records explain why a card exists. Source links provide direct local
or declared-connector references that a UI or review surface can show.

## Related Node Fields

- `node_id`
- `node_type`
- `relation`
- `label`

Related nodes connect cards to Personal Map, project graph, runtime graph, or
source-intelligence graph objects.

## Thumbnail Fields

- `path`
- `alt`
- `source_type`

Thumbnails are optional and must be local or explicitly declared connector
artifacts. The visual UI is not built in this pass.

## Recommended Action Fields

- `action_id`
- `label`
- `action_type`
- `target_ref`
- `requires_operator_approval`
- `mutates_canonical_state`

Canonical mutations require operator approval and are not enabled by the Pulse
scaffold.

## Deck Fields

- `deck_id`
- `audience`
- `generated_at`
- `cards`
- `source_summary`
- `schedule_ref`
- `feedback_policy_ref`
- `canonical_writeback_enabled`

## Audience/Class Matrix

| Audience | Allowed classes |
|---|---|
| `user` | Today's Operating Brief, Future Prep, Project Momentum, Business OS Opportunity, Learning / University Focus, Content / Brand Edge, Trading / Market Watch, Research Watch, Memory Update, Personal Map Update, Manual Input Needed, Decision Needed, Risk / Blocker, Runtime Blocker, Carry-Forward, Schedule Catch-Up, Suggested Delegation |
| `agent` | Runtime Reflection, Error Cluster, Skill Gap, Permission Request, Workflow Improvement, SOP Needed, Tool Needed, Connector Needed, Self-Upgrade Proposal, Memory Drift Warning, Execution Repair Pattern, Runtime Navigation Update, Capability Gap, Autonomy Envelope Suggestion |
| `shared_coordination` | Agent Handoff, AOR Pending Decision, Multi-Agent Coordination, Governance Risk, Source Conflict, Review Queue, Cross-Runtime Blocker, Schedule / Delivery Failure, Promotion Candidate, Truth-State Warning |

Runtime code still accepts `shared` as a legacy alias for existing artifacts.

## Feedback Options

The master feedback vocabulary is:

- `thumbs_up`
- `thumbs_down`
- `show_more_like_this`
- `show_less_like_this`
- `never_show_this`
- `save`
- `delegate`
- `turn_into_task`
- `promote_to_memory`
- `link_to_project`
- `link_to_personal_map`
- `link_to_agent_brain`
- `dismiss`

The scaffold also keeps older candidate/review terms such as `accepted`,
`dismissed`, `snoozed`, `corrected`, `needs_more_evidence`, and
`memory_candidate` for backward compatibility with existing local artifacts.

## Writeback Stages

Pulse writeback must remain staged:

1. `card_generated`
2. `card_saved`
3. `card_archived`
4. `task_candidate`
5. `memory_candidate`
6. `memory_approved`
7. `project_update_approved`
8. `knowledge_promotion_approved`

Default runtime state remains `promotion_status: not_promoted` and
`writeback_status: draft_only`.

## Governance Defaults

- `governance_state: proposal`
- `canonical_writeback_enabled: false`
- feedback does not mutate source truth
- recommended actions are review/approval surfaces, not hidden execution

## Runtime Validation

Focused tests live in `runtime/pulse/test_pulse_schema.py`,
`runtime/pulse/test_backend_minimal_deck.py`,
`runtime/pulse/test_local_surface.py`, and
`runtime/pulse/test_feedback_candidates.py`, and
`runtime/pulse/test_feedback_review_queue.py`.

## Local Surface Projection

The first local Pulse surface lives in `runtime/pulse/local_surface.py`. It reads
validated user deck JSON artifacts from `07_LOGS/Pulse-Decks/users/`, projects
the same card fields into a UI-ready model/static HTML artifact, and preserves
`canonical_writeback_enabled: false`. Feedback controls are candidate records
only and do not mutate the source card or deck.

## Feedback Candidate Persistence

`runtime/pulse/feedback.py` can persist candidate records as append-only JSONL
under:

```text
07_LOGS/Pulse-Decks/feedback-candidates/YYYY-MM-DD-feedback-candidates.jsonl
```

The persisted row is still not card feedback. It is a pending-review object with
`candidate_only: true`, `review_required: true`,
`applied_to_source_deck: false`, `approves_memory: false`,
`creates_task: false`, and `canonical_writeback_allowed: false`.

## Feedback Review Queue

`runtime/pulse/feedback_review_queue.py` projects persisted candidates into
read-only review items and contract-only review/apply objects. The queue
preserves card ID, feedback type, source deck path, source surface path,
operator note, pending-review status, blocked effects, and allowed review
decisions. It does not persist review decisions or apply feedback to source
cards/decks.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
