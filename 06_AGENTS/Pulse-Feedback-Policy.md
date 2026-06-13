# Pulse Feedback Policy

**Approval Center routing:** Pulse approval-queue references in this policy should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** PARTIAL - policy, runtime helper, candidate persistence, review-queue contract, non-applying decision log, read-only unified inspector, non-mutating Agent Bus review request contract, read-only Agent Bus review queue preview, design-only enqueue preflight, persisted approval-request records, non-executing approval validation, append-only enqueue evidence artifacts, non-live handoff preflight, contract-only operator/Gate approval UI packet, dry-run supervised enqueue rehearsal, real approval artifact-chain rehearsal, guarded Agent Bus enqueue, dry-run-first pipeline runner, and explicit review-response ingest  
**Created:** 2026-04-29  
**Runtime scaffold:** `runtime/pulse/feedback.py`, `runtime/pulse/feedback_review_queue.py`, `runtime/pulse/review_decision_log.py`, `runtime/pulse/candidate_inspector.py`, `runtime/pulse/bus_review_contract.py`, `runtime/pulse/bus_review_queue.py`, `runtime/pulse/bus_enqueue_design.py`, `runtime/pulse/bus_enqueue_approval_request.py`, `runtime/pulse/bus_enqueue_approval_validation.py`, `runtime/pulse/bus_enqueue_evidence.py`, `runtime/pulse/bus_handoff_preflight.py`, `runtime/pulse/operator_gate_approval_contract.py`, `runtime/pulse/supervised_live_enqueue_rehearsal.py`, `runtime/pulse/real_approval_artifact_rehearsal.py`, `runtime/pulse/bus_enqueue.py`, `runtime/pulse/pipeline_runner.py`, `runtime/pulse/bus_review_response_ingest.py`, `runtime/memory/feedback_rules.py`

## Purpose

Pulse feedback is how the operator shapes future Pulse decks, memory
candidates, personal map candidates, and runtime reflection quality.

Feedback is governed input. It is not automatic truth.

## Feedback Types

Pulse card feedback:

- `accepted`
- `dismissed`
- `snoozed`
- `corrected`
- `needs_more_evidence`
- `memory_candidate`
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

Context memory feedback:

- `confirm`
- `correct`
- `dismiss`
- `snooze`
- `mark_memory_candidate`
- `mark_personal_map_candidate`

## Feedback Effects

| Feedback | Effect |
|---|---|
| `accepted` / `confirm` | positive ranking signal |
| `dismissed` / `dismiss` | negative ranking signal |
| `snoozed` / `snooze` | suppress until reviewed later |
| `corrected` / `correct` | creates review-required correction event |
| `needs_more_evidence` | card remains untrusted until evidence improves |
| `memory_candidate` | creates a memory candidate only |
| `mark_personal_map_candidate` | creates a personal map candidate only |
| `show_more_like_this` / `show_less_like_this` | creates durable ranking-rule candidates |
| `never_show_this` | creates a suppress-rule candidate |
| `turn_into_task` | creates a task candidate only; no task is created in this scaffold |
| `promote_to_memory` | creates a memory candidate only; memory remains unapproved |
| `link_to_project` | creates a project-link candidate only |
| `link_to_personal_map` | creates a Personal Map candidate only |
| `link_to_agent_brain` | creates an AgentHub/runtime-brain link candidate only |

## Writeback Rules

- Feedback may update a Pulse card record or create a candidate object.
- Feedback must not write directly to `02_KNOWLEDGE/`.
- Feedback must not mutate `00_HOME/Now.md`.
- Feedback must not mutate Project-OS files.
- Feedback must not change runtime permissions.
- Feedback must not activate agent self-upgrade.
- Corrections require operator review before becoming durable memory.

## Durable Feedback Rules

Feedback may create durable rule candidates for future ranking and selection.
Examples:

- suppress a topic
- boost a card class
- link future cards to a project
- link a recurring pattern to Personal Map
- link runtime failures to an agent brain
- create a memory candidate

Durable feedback rules must remain reviewable and must keep
`canonical_writeback_allowed: false` unless a later governed writeback layer is
explicitly approved.

## Staged Writeback Ladder

Pulse outputs move through explicit stages only:

1. card generated
2. card saved
3. card archived
4. card becomes task candidate
5. card becomes memory candidate
6. memory approved
7. project update approved
8. knowledge promotion approved

The default scaffold stops at candidate/review contracts and does not apply
feedback to source truth.

The first local Pulse surface exposes feedback as candidate records only. It
does not apply feedback to the source deck, approve memory, create tasks, mutate
project files, or perform canonical writeback.

## Candidate Persistence Lane

`runtime/pulse/feedback.py` now defines an append-only candidate lane:

```text
07_LOGS/Pulse-Decks/feedback-candidates/YYYY-MM-DD-feedback-candidates.jsonl
```

Candidate records are `pending_review` only. They preserve the source deck path,
card ID, feedback type, operator note, timestamp, review requirement, and the
explicit flags that canonical writeback, source-deck mutation, memory approval,
and task creation are blocked.

This lane is not a second datastore. It is a Pulse log artifact path under
`07_LOGS/Pulse-Decks/`. It exists so later approval/review surfaces can inspect
feedback candidates without treating them as already applied feedback.

## Review Queue Contract

`runtime/pulse/feedback_review_queue.py` now defines the first review queue
contract over pending feedback candidates.

The queue can:

- load pending candidates from the governed Pulse candidate log tree
- expose candidate metadata as read-only review items
- build an in-memory review decision
- build a non-executing apply contract
- preserve blocked effects for source deck mutation, memory approval, task
  creation, project-file mutation, knowledge promotion, schedule activation,
  provider calls, connector calls, and canonical writeback

Supported review decision types:

- `accept_for_future_ranking`
- `reject_candidate`
- `defer_candidate`
- `request_more_context`

This is not a full review UI and not feedback application. The apply contract
declares what a later governed surface may do, but does not mutate decks,
memory, tasks, project files, or canonical knowledge.

## Review Decision Log

`runtime/pulse/review_decision_log.py` defines the first persisted review
decision lane for feedback, Personal Map, and execution repair candidates:

```text
07_LOGS/Pulse-Decks/review-decisions/YYYY-MM-DD-review-decisions.jsonl
```

Supported decision records include:

- feedback: `accept_for_future_ranking`, `reject_candidate`, `defer_candidate`,
  `request_more_context`, `mark_duplicate`, `request_revision`
- Personal Map: `approve_for_future_apply`, `reject_candidate`,
  `defer_candidate`, `request_more_context`, `mark_duplicate`,
  `request_revision`
- execution repair: `approve_for_future_apply`, `reject_candidate`,
  `defer_candidate`, `request_more_context`, `mark_duplicate`,
  `request_revision`

The decision log persists review intent only. It blocks source-deck mutation,
feedback application, Personal Map mutation, runtime memory mutation, memory
approval, task/SOP creation, Runtime Navigation Map updates, Agent Identity
Ledger updates, permission expansion, project-file mutation, knowledge
promotion, schedule activation, provider/connector calls, canonical writeback,
and second datastore writes.

## Unified Candidate Inspector

`runtime/pulse/candidate_inspector.py` provides a read-only aggregate snapshot
over feedback candidates, Personal Map candidates, execution repair candidates,
and persisted review-decision records.

The inspector can show related candidate IDs, source log paths, source deck/card
refs, runtime refs, target refs, follow-up signals, counts by item kind, and
decision counts by candidate ID. It does not persist a derived queue, apply
feedback, approve memory, mutate Personal Map/runtime memory, create tasks/SOPs,
update Runtime Navigation Maps or Agent Identity Ledgers, expand permissions,
call providers/connectors, activate schedules, or write canonical state.

## Audit Rules

Every durable feedback record should preserve:

- feedback ID
- card ID or target object ID
- feedback type
- operator note
- timestamp
- source deck or card path
- whether it creates a candidate
- whether review is required

Durable candidate logs must also preserve:

- candidate ID
- source deck path
- source surface path, when available
- candidate-only state
- pending-review status
- canonical-writeback blocked flag
- applied-to-source-deck blocked flag
- memory-approval blocked flag
- task-creation blocked flag

Review queue snapshots must also preserve:

- queue status as `read_only`
- pending candidate count
- source candidate log paths
- allowed review decisions
- blocked effects
- contract-only state for review decisions and apply contracts

Persisted review decision logs must also preserve:

- decision ID
- candidate ID and candidate kind
- decision type
- reviewer and operator note
- source candidate/card/deck references where available
- record-only state
- follow-up signal only, not target-system mutation
- blocked effects
- canonical-writeback and second-datastore blocked flags

Unified candidate inspector snapshots must also preserve:

- inspector status as `read_only`
- source log paths for all discovered candidate/review lanes
- item counts by item kind
- review-decision counts by candidate ID
- no write paths
- blocked effects for every apply, mutation, permission, provider, connector,
  schedule, second-datastore, or canonical-writeback effect

Agent Bus review request contracts must also preserve:

- source candidate ID and inspector item refs
- source log, deck, card, runtime, and target refs
- `intent: REVIEW`
- `sender: Operator`
- target review runtime, defaulting to Hermes unless explicitly overridden
- a deterministic work fingerprint
- `bus_task_creation_allowed: false`
- `bus_task_written: false`
- `writes_performed: false`
- no approval persistence
- no live runtime dispatch
- all candidate-apply, provider, connector, schedule, second-datastore, and
  canonical-writeback blocks

Agent Bus review queue previews must also preserve:

- source log paths discovered by the inspector
- count by candidate kind
- count by review recipient
- generated Agent Bus task previews
- `queue_status: read_only`
- `bus_task_creation_allowed: false`
- `bus_tasks_written: false`
- no derived queue persistence
- no approval queue persistence
- no live runtime dispatch
- no candidate apply or canonical writeback

Agent Bus enqueue preflights must also preserve:

- source review contract ID
- source candidate ID and candidate kind
- `preflight_status: ready_for_operator_approval`
- `sender: Operator`
- target review recipient limited to declared Pulse review recipients
- required approval list
- work fingerprint for duplicate review
- generated task payload preview
- `enqueue_allowed: false`
- `agent_bus_task_written: false`
- `approval_request_written: false`
- `duplicate_check_performed: false`
- no live runtime dispatch
- no review-response ingestion
- no candidate apply or canonical writeback

Agent Bus enqueue approval-request records must also preserve:

- approval request ID
- source preflight and review contract IDs
- source candidate ID and candidate kind
- operation: `pulse.agent_bus.enqueue_review`
- required approvals
- work fingerprint and task payload preview
- source log/deck/card/runtime refs where known
- `status: approval_requested`
- `approval_granted: false`
- `gate_policy_defined: false`
- `duplicate_check_performed: false`
- `live_agent_bus_handoff_allowed: false`
- `agent_bus_task_written: false`
- `approval_executed: false`
- no review-response ingestion
- no candidate apply or canonical writeback

Agent Bus enqueue approval validation results must also preserve:

- source approval request ID
- satisfied approvals
- missing approvals
- validation status
- `validation_record_only: true`
- `persisted_validation: false`
- `approval_granted: false`
- `approval_executed: false`
- `gate_policy_mutated: false`
- `duplicate_query_performed: false`
- `live_agent_bus_handoff_allowed: false`
- `agent_bus_task_written: false`
- no review-response ingestion
- no candidate apply or canonical writeback

Agent Bus enqueue evidence records must also preserve:

- source approval request ID
- reviewer and evidence note
- separate evidence booleans for operator approval, Gate policy,
  external-sender allowance, and duplicate-work-fingerprint review
- optional evidence refs for Gate policy, external-sender allowance, and
  duplicate review
- `status: evidence_recorded`
- `evidence_record_only: true`
- no approval grant, approval execution, Gate mutation, duplicate query, Agent
  Bus task write, runtime dispatch, review-response ingest, candidate apply, or
  canonical writeback

Agent Bus handoff preflights must also preserve:

- source approval request ID
- optional evidence artifact ID
- in-memory validation result
- duplicate work-fingerprint posture
- Agent Bus target posture
- `preflight_record_only: true`
- `persisted_preflight: false`
- `approval_granted: false`
- `gate_policy_mutated: false`
- `live_agent_bus_handoff_allowed: false`
- `agent_bus_task_written: false`
- no runtime dispatch, review-response ingest, candidate apply, provider or
  connector call, schedule activation, or canonical writeback

Operator/Gate approval UI contracts must also preserve:

- source approval request ID, handoff preflight ID, and optional evidence ID
- visible evidence fields for operator/Gate review
- enabled/disabled decision controls
- supervised live command preview only when the handoff preflight is ready
- `ui_contract_only: true`
- `visual_ui_built: false`
- `persisted_contract: false`
- `approval_granted: false`
- `approval_executed: false`
- `gate_policy_mutated: false`
- `live_agent_bus_handoff_allowed: false`
- `agent_bus_task_written: false`
- no runtime dispatch, review-response ingest, candidate apply,
  provider/connector call, schedule activation, second-datastore write, or
  canonical writeback

Supervised live-enqueue rehearsals must also preserve:

- source approval request ID and optional evidence ID
- nested operator/Gate approval contract
- manual command preview only when ready
- required operator steps
- blocked reasons when not ready
- `rehearsal_record_only: true`
- `persisted_rehearsal: false`
- `live_enqueue_executed: false`
- `approval_granted: false`
- `approval_executed: false`
- `gate_policy_mutated: false`
- `agent_bus_task_written: false`
- no runtime dispatch, review-response ingest, candidate apply,
  provider/connector call, schedule activation, second-datastore write, or
  canonical writeback

Real approval artifact-chain rehearsals must also preserve:

- source user deck path and card ID
- append-only feedback candidate artifact path
- append-only approval request artifact path
- append-only evidence artifact path
- nested supervised live-enqueue rehearsal result
- explicit evidence flags for operator approval, Gate policy,
  external-sender allowance, and duplicate-work-fingerprint review
- `approval_granted: false`
- `approval_executed: false`
- `live_enqueue_executed: false`
- `agent_bus_task_written: false`
- no runtime dispatch, review-response ingest, candidate apply, memory
  approval, provider/connector call, schedule activation, second-datastore
  write, or canonical writeback

Guarded Agent Bus enqueue results must also preserve:

- source approval validation ID
- source approval request, preflight, contract, candidate, recipient, and work
  fingerprint refs
- result status: `enqueued`, `blocked`, `duplicate_skipped`, or `bus_error`
- task ID only when a REVIEW task is actually created
- duplicate task ID only when an active duplicate is found
- no feedback application, candidate apply, memory approval, Personal Map
  mutation, runtime memory mutation, task/SOP creation, provider/connector
  call, schedule activation, or canonical writeback

Pulse pipeline runner evidence must remain split:

- `operator_approved` means only operator enqueue approval is present
- `gate_policy_defined` must be separate evidence
- `external_sender_allowance_present` must be separate evidence
- `duplicate_work_fingerprint_reviewed` must be separate evidence
- a single operator-approved flag must not imply the other three evidence
  requirements

## Next Pass

Run an operator-approved live REVIEW enqueue only after the current artifact
chain has explicit evidence for operator approval, Gate policy,
external-sender allowance, and duplicate-work-fingerprint review. Memory
approval, source-deck mutation, candidate application, review-decision apply,
task/SOP creation, runtime permission expansion, and canonical writeback remain
out of scope until a separate approval-gated implementation pass.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
