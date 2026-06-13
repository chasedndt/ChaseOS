# runtime/pulse/

Schema-first scaffold for ChaseOS Pulse.

Pulse is the native proactive intelligence layer for ChaseOS. It is not a
generic daily digest or an OpenClaw cron feature. This runtime package defines
the first card/deck contracts, non-mutating pipeline steps, backend deck
artifacts, and a local-only first surface over those artifacts:

1. `signal_collector.py` - declared local signal contracts.
2. `topic_selector.py` - groups signals into Pulse topics.
3. `ranker.py` - ranks Pulse cards without mutating source state.
4. `deck_generator.py` - builds card decks from declared signals.
5. `minimal_deck.py` - emits deterministic backend user, agent, and shared decks.
6. `multi_audience_decks.py` - dry-run/write orchestration and inventory for local multi-audience decks.
7. `signal_driven_decks.py` - local signal snapshot and user/agent/shared deck generation from repo evidence.
8. `renderer_markdown.py` and `renderer_json.py` - render decks.
9. `writeback.py` - writes rendered deck artifacts only under `07_LOGS/Pulse-Decks/`.
10. `local_surface.py` - renders the latest user deck as a static local surface, including read-only operator review and Agent Bus handoff previews.
11. `visual_card_deck_shell.py` - renders the first Phase 10 visual Pulse card/deck shell over existing local Pulse contracts.
12. `personal_map_visualization.py` - renders the first read-only Personal Map visualization contract and static artifact.
13. `feedback.py` - captures governed feedback records and append-only candidates.
14. `feedback_review_queue.py` - read-only pending candidate queue and non-executing apply contracts.
15. `review_decision_log.py` - append-only persisted review decisions without apply effects.
16. `candidate_inspector.py` - read-only unified candidate/review-decision snapshot.
17. `bus_review_contract.py` - non-mutating Agent Bus REVIEW request previews for Pulse candidates.
18. `bus_review_queue.py` - read-only in-memory queue preview over bus review contracts.
19. `bus_enqueue_design.py` - design-only enqueue preflights; no live bus writes.
20. `bus_enqueue_approval_request.py` - append-only approval-request records; no approval grant.
21. `bus_enqueue_approval_validation.py` - in-memory approval validation; no execution.
22. `bus_enqueue_evidence.py` - append-only operator/Gate evidence records; no approval grant or handoff.
23. `bus_handoff_preflight.py` - non-live final readiness inspector over request, evidence, duplicate posture, and Agent Bus target posture.
24. `operator_gate_approval_contract.py` - contract-only operator/Gate approval packet for future UI surfaces.
25. `supervised_live_enqueue_rehearsal.py` - dry-run supervised live-enqueue procedure packet; no task creation.
26. `bus_enqueue.py` - final guarded Agent Bus REVIEW task enqueue after ready validation.
27. `pipeline_runner.py` - dry-run-by-default pipeline orchestration over plan, approval request, validation, and guarded enqueue.
28. `bus_review_response_ingest.py` - dry-run-by-default ingest of completed review responses into Pulse review decisions.
29. `post_completion_hardening.py` - read-only post-completion proof/boundary verifier.
30. `approval_center.py` - read-only approval-center readiness packet for future Studio surfaces.
31. `memory_runtime_readiness.py` - read-only Context Memory Core / AgentHub readiness packet.
32. `runtime/studio/runtime_brain_dashboard.py` - Studio-facing read-only Runtime Brain dashboard contract over the memory/runtime readiness substrate.
33. `runtime_brain_visualization.py` - renders the first local-only static Runtime Brain visualization over the read-only Studio contract.
34. `approval_queue_ui.py` - renders the first local-only static Approval Queue UI over Pulse readiness and candidate lanes.
35. `personal_map_review_apply.py` - renders a Personal Map candidate review/apply surface over the existing governed apply lane without running apply.
36. `product_shell.py` - renders the first integrated local Pulse product shell over the existing Phase 10 surfaces.
37. `product_shell_browser_qa.py` - detects durable browser-QA evidence for the integrated static Pulse product shell.
38. `final_product_readiness_audit.py` - read-only final product-readiness audit separating current v1 local completion from full product-grade gaps.
39. `card_schema.py` - card, scope, source link, evidence, action, feedback, and deck schema.
40. `deck_schema.py` - markdown/JSON artifact metadata.

## Current Artifact Output

Phase B backend output exists as local log artifacts only:

```text
07_LOGS/Pulse-Decks/users/YYYY-MM-DD-user-pulse.md
07_LOGS/Pulse-Decks/users/YYYY-MM-DD-user-pulse.json
07_LOGS/Pulse-Decks/agents/YYYY-MM-DD-agent-pulse-expanded.md
07_LOGS/Pulse-Decks/agents/YYYY-MM-DD-agent-pulse-expanded.json
07_LOGS/Pulse-Decks/shared/YYYY-MM-DD-shared-pulse-expanded.md
07_LOGS/Pulse-Decks/shared/YYYY-MM-DD-shared-pulse-expanded.json
07_LOGS/Pulse-Decks/users/YYYY-MM-DD-*-user-pulse-signal.md
07_LOGS/Pulse-Decks/users/YYYY-MM-DD-*-user-pulse-signal.json
07_LOGS/Pulse-Decks/agents/YYYY-MM-DD-*-agent-pulse-signal.md
07_LOGS/Pulse-Decks/agents/YYYY-MM-DD-*-agent-pulse-signal.json
07_LOGS/Pulse-Decks/shared/YYYY-MM-DD-*-shared-pulse-signal.md
07_LOGS/Pulse-Decks/shared/YYYY-MM-DD-*-shared-pulse-signal.json
07_LOGS/Pulse-Decks/users/YYYY-MM-DD-*-user-pulse-signal.visual-shell.html
07_LOGS/Pulse-Decks/personal-map/YYYY-MM-DD-personal-map-visualization.html
07_LOGS/Pulse-Decks/runtime-brains/YYYY-MM-DD-runtime-brain-visualization.html
07_LOGS/Pulse-Decks/runtime-brains/YYYY-MM-DD-runtime-brain-<runtime_id>.html
07_LOGS/Pulse-Decks/approval-queue/YYYY-MM-DD-approval-queue.html
07_LOGS/Pulse-Decks/personal-map-review/YYYY-MM-DD-personal-map-review-apply.html
07_LOGS/Pulse-Decks/product-shell/YYYY-MM-DD-pulse-product-shell.html
07_LOGS/Pulse-Decks/product-shell/YYYY-MM-DD-pulse-product-shell-browser-qa.md
07_LOGS/Pulse-Decks/product-shell/YYYY-MM-DD-pulse-product-shell-browser-qa.png
```

The artifact writer validates that output remains under `07_LOGS/Pulse-Decks/`.
It does not write to canonical knowledge, Now.md, Project-OS files, schedule
state, or governance docs.

Current CLI surfaces:

```text
chaseos pulse generate-decks [--audience user|agent|shared_coordination] [--write]
chaseos pulse generate-signal-decks [--write]
chaseos pulse deck-inventory
chaseos pulse memory-runtime-readiness
chaseos pulse final-product-readiness-audit
chaseos pulse product-shell [--deck-path PATH] [--write]
chaseos pulse visual-card-deck-shell [--write]
chaseos pulse personal-map-visualization [--write]
chaseos pulse personal-map-review-apply [--write]
chaseos pulse runtime-brain-visualization [--runtime RUNTIME_ID] [--write]
chaseos pulse approval-queue-ui [--request-id REQUEST_ID] [--evidence-id EVIDENCE_ID] [--write]
chaseos studio runtime-brain-dashboard
chaseos studio pulse-product-shell-panel
```

`generate-decks` is dry-run by default. With `--write`, it writes only
markdown/JSON deck artifacts under `07_LOGS/Pulse-Decks/`; it does not dispatch
runtimes, enqueue Agent Bus tasks, activate schedules, call providers or
connectors, approve memory, create a second datastore, or mutate canonical
state.

`generate-signal-decks` is also dry-run by default. It reads only the current
local Pulse proof surface: recent build logs, recent agent activity logs,
schedule manifests, completion status, hardening status, and existing deck
inventory. With `--write`, it writes only user, agent, and shared markdown/JSON
deck artifacts under `07_LOGS/Pulse-Decks/`. It does not browse, call
providers/connectors, dispatch runtimes, write Agent Bus tasks, activate
schedules, approve memory, update the R&D workbook, create a second datastore,
or mutate canonical state.

`memory-runtime-readiness` reads Context Memory Core and AgentHub runtime-memory
lanes and returns a readiness packet only. `studio runtime-brain-dashboard`
composes that packet with runtime profiles, identity ledgers, runtime
navigation maps, execution repair memory, and scorecards for future Studio
rendering. Both commands are read-only; they do not apply feedback, mutate
Personal Map state, update Runtime Brains, expand permissions, dispatch
runtimes, activate schedules, call providers/connectors, write canonical state,
create a second datastore, or update the R&D workbook.

`final-product-readiness-audit` composes the current Pulse completion,
post-completion hardening, approval-center, memory/runtime readiness, Runtime
Brain dashboard, and prior catch-up build-log evidence. It reports that the
current bounded v1 local Pulse lane is complete while full product-grade Pulse
remains partial until visual UI, Personal Map visualization, approval queue UI,
native schedule activation proof, and optional connector/source scanner lanes
are explicitly completed.

`visual-card-deck-shell` composes the latest user Pulse deck with final product
readiness, approval-center readiness, memory/runtime readiness, and the Runtime
Brain dashboard contract into a static local HTML shell. It is dry-run by
default. With `--write`, it writes one HTML artifact under
`07_LOGS/Pulse-Decks/users/` beside the source deck. It does not submit
feedback, apply candidates, mutate memory or Personal Map state, update Runtime
Brains, write Agent Bus tasks, dispatch runtimes, activate schedules, call
providers/connectors, create a second datastore, mutate canonical state, or
update the R&D workbook.

`product-shell` composes the current user deck, visual card shell, Personal Map
visualization, Personal Map review/apply surface, Runtime Brain visualization,
Approval Queue UI, and final product-readiness audit into one integrated static
local shell. It is dry-run by default. With `--write`, it writes one HTML
artifact under `07_LOGS/Pulse-Decks/product-shell/`. It does not start a
server, open a browser, submit feedback, execute approvals, apply candidates,
dispatch runtimes, activate schedules, call providers/connectors, create a
second datastore, mutate canonical state, or update the R&D workbook.

`studio pulse-product-shell-panel` is a read-only Studio panel contract over
the latest static Pulse product shell artifact and durable browser-QA evidence.
It reports the intended Studio route, mount target, source artifact URI,
browser-QA note/screenshot, panel/card counts, and blocked authority. It does
not mount Studio, start a server, open a browser, submit feedback, execute
approvals, apply candidates, write Agent Bus tasks, dispatch runtimes, activate
schedules, call providers/connectors, mutate canonical state, or update the
R&D workbook.

`personal-map-visualization` composes the Personal Map architecture, pending
Personal Map candidate queue, and memory/runtime readiness posture into a
read-only visualization contract. It is dry-run by default. With `--write`, it
writes one static HTML artifact under `07_LOGS/Pulse-Decks/personal-map/`. It
does not apply candidates, approve memory, mutate the Personal Map, create
tasks, edit Now or Project-OS files, update Runtime Brains, write Agent Bus
tasks, dispatch runtimes, activate schedules, call providers/connectors, create
a second datastore, mutate canonical state, or update the R&D workbook.

`runtime-brain-visualization` composes the read-only Studio Runtime Brain
dashboard contract into a static Pulse visualization surface. It is dry-run by
default and can be filtered with `--runtime`. With `--write`, it writes one
HTML artifact under `07_LOGS/Pulse-Decks/runtime-brains/`. It does not update
Runtime Brains, Runtime Navigation Maps, Agent Identity Ledgers, or Execution
Repair Memory; it does not grant permissions, activate self-upgrade, write
Agent Bus tasks, dispatch runtimes, activate schedules, call
providers/connectors, create a second datastore, mutate canonical state, or
update the R&D workbook.

`approval-queue-ui` composes the approval-center readiness contract and
candidate inspector snapshot into a static Pulse approval queue surface. It is
dry-run by default and can be scoped with `--request-id` / `--evidence-id`.
With `--write`, it writes one HTML artifact under
`07_LOGS/Pulse-Decks/approval-queue/`. It does not grant or execute approvals,
write review decisions or feedback candidates, apply candidates, write Agent
Bus tasks, dispatch runtimes, activate schedules, call providers/connectors,
approve memory, create a second datastore, mutate canonical state, or update
the R&D workbook.

`personal-map-review-apply` composes pending Personal Map candidates, persisted
Personal Map review decisions, current runtime-memory graph state, and the
existing `apply-decisions --kind personal_map` dry-run preview into a static
review/apply surface. It is dry-run by default. With `--write`, it writes one
HTML artifact under `07_LOGS/Pulse-Decks/personal-map-review/`. The surface
does not run the live apply command, approve memory, mutate `00_HOME/Now.md`,
edit Project-OS files, write `02_KNOWLEDGE/`, update Runtime Brains, write
Agent Bus tasks, dispatch runtimes, activate schedules, call
providers/connectors, create a second datastore, mutate canonical state, or
update the R&D workbook.

## Current Local Surface Output

The first Pulse surface is a derived static HTML artifact generated from the
latest user deck JSON:

```text
07_LOGS/Pulse-Decks/users/YYYY-MM-DD-user-pulse.surface.html
```

`local_surface.py` reads only existing user deck artifacts under
`07_LOGS/Pulse-Decks/users/`. Feedback controls are exposed as governed
candidate records only; they are not applied to cards, memory, project files,
or canonical knowledge.

The surface also embeds a bounded read-only Operator Review Queue Snapshot from
`candidate_inspector.py`. This shows candidate/review-decision counts and a
small preview of existing candidate lanes, but it does not persist a derived
queue, apply review decisions, approve memory, create tasks, call providers or
connectors, activate schedules, write canonical state, or create a second
datastore.

The surface now also includes a read-only Agent Bus Review Handoff Preview from
`bus_review_queue.py`. It renders the REVIEW task previews that candidates would
produce for bounded peer review, while keeping `bus_tasks_written=false`,
`approval_requests_written=false`, and live runtime dispatch blocked. This is a
visibility/coordination pass only; actual enqueue remains behind the separate
approval/evidence/final-enqueue lane.

The surface also shows a read-only Supervised Live Handoff Readiness snapshot
for persisted Agent Bus enqueue approval requests. It composes
`bus_handoff_preflight.py` so the operator can see whether requests are blocked
by missing evidence, active duplicate fingerprints, or bus snapshot posture
before any final enqueue command. This grants no approval, performs no live
handoff, writes no Agent Bus tasks, applies no candidates, and does not enable
canonical writeback.

## Current Feedback Candidate Output

When explicitly submitted by a caller, feedback candidates append to JSONL
artifacts under the existing Pulse log tree:

```text
07_LOGS/Pulse-Decks/feedback-candidates/YYYY-MM-DD-feedback-candidates.jsonl
```

These records are pending-review candidates only. They do not mutate the source
deck, approve memory, create tasks, update project files, or write canonical
knowledge. The candidate writer rejects source decks outside
`07_LOGS/Pulse-Decks/users/` and candidate logs outside
`07_LOGS/Pulse-Decks/feedback-candidates/`.

## Current Feedback Review Queue

`feedback_review_queue.py` can load pending candidate JSONL rows into a
read-only queue snapshot and build in-memory review/apply contracts. The
contracts can express operator intent such as `accept_for_future_ranking`,
`reject_candidate`, `defer_candidate`, or `request_more_context`.

This is not feedback application. Decisions are not persisted, cards are not
updated, memory is not approved, tasks are not created, and canonical writeback
remains blocked.

## Current Review Decision Log

`review_decision_log.py` can persist operator review decisions for feedback,
Personal Map, and execution repair candidates under:

```text
07_LOGS/Pulse-Decks/review-decisions/YYYY-MM-DD-review-decisions.jsonl
```

These records capture review intent only. They do not apply feedback, mutate the
Personal Map, apply runtime repair memory, approve memory, create tasks/SOPs,
update Runtime Navigation Maps, write Agent Identity Ledgers, expand
permissions, call providers/connectors, create a second datastore, or write
canonical knowledge.

## Current Unified Candidate Inspector

`candidate_inspector.py` reads existing feedback candidate, Personal Map
candidate, execution repair candidate, and review-decision JSONL lanes into one
read-only in-memory snapshot.

The snapshot can report source log paths, counts by item kind, review-decision
counts by candidate ID, candidate/runtime/source references, and follow-up
signals. It does not write a derived queue, create folders on empty reads, apply
feedback, approve memory, mutate candidate targets, create tasks/SOPs, activate
schedules, call providers/connectors, or write canonical knowledge.

## Current Agent Bus Review Request Contract

`bus_review_contract.py` builds an in-memory Agent Bus `REVIEW` task preview
from one Pulse candidate inspector item or candidate ID.

The contract preserves source log, source deck, card, runtime, and target refs
and defaults the review recipient to Hermes. It does not import or call the
Agent Bus task writer, initialize bus storage, enqueue tasks, persist approval
requests, apply candidates, dispatch runtimes, activate schedules, call
providers/connectors, create tasks/SOPs, approve memory, or write canonical
state.

## Current Agent Bus Review Queue Preview

`bus_review_queue.py` builds an in-memory queue preview over current Pulse
candidates by composing the unified candidate inspector with the Agent Bus
review request contract.

The preview can filter by candidate kind or candidate ID, limit returned
contracts, route candidate kinds to a selected review runtime, and report counts
by candidate kind and recipient. It does not persist a derived queue, write
approval requests, create Agent Bus tasks, dispatch runtimes, apply candidates,
call providers/connectors, activate schedules, or write canonical state.

## Current Agent Bus Review Queue Audit

`test_bus_review_queue_audit.py` and
`06_AGENTS/ChaseOS-Pulse-Agent-Bus-Review-Queue-Audit.md` verify the current
queue-preview boundary. The audit checks source-level import boundaries,
read-only behavior, no file-tree delta, no Agent Bus task creation, no approval
persistence, no candidate apply, and no R&D workbook update.

## Current Agent Bus Enqueue Design

`bus_enqueue_design.py` defines denied-by-default enqueue preflight objects for
a future operator-approved Agent Bus REVIEW handoff.

The preflight can describe the source review contract, candidate refs, review
recipient, required approvals, duplicate work fingerprint, and task payload
preview. It remains design-only: no Agent Bus backend import, no bus task write,
no persisted approval request, no runtime dispatch, no review-response intake,
no candidate apply, and no canonical writeback.

Codex is registered on the Agent Bus for bounded code/repo task classes, but it
is not silently promoted to a default Pulse REVIEW recipient by this scaffold.

## Current Agent Bus Enqueue Approval Request Lane

`bus_enqueue_approval_request.py` persists operator-reviewable enqueue intent
under:

```text
07_LOGS/Pulse-Decks/agent-bus-approval-requests/YYYY-MM-DD-agent-bus-approval-requests.jsonl
```

These records are approval requests only. They preserve the preflight, work
fingerprint, required approvals, source refs, and task payload preview, but they
do not grant approval, validate Gate policy, perform duplicate suppression,
write Agent Bus tasks, dispatch runtimes, ingest review responses, apply
candidates, or write canonical state.

## Current Agent Bus Enqueue Approval Validation

`bus_enqueue_approval_validation.py` validates approval-request records in
memory against explicit evidence flags:

- operator enqueue approval present
- Gate policy defined
- external-sender allowance present
- duplicate work fingerprint reviewed

Validation can return `blocked_missing_required_evidence` or
`ready_for_final_handoff_review`. The ready state is still not an approval grant
and not live handoff permission. The validation layer does not persist
validation records, query live Agent Bus duplicate history, mutate Gate policy,
write Agent Bus tasks, dispatch runtimes, ingest review responses, apply
candidates, or write canonical state.

## Current Agent Bus Enqueue Evidence Artifacts

`bus_enqueue_evidence.py` persists operator/Gate evidence records under:

```text
07_LOGS/Pulse-Decks/agent-bus-enqueue-evidence/YYYY-MM-DD-agent-bus-enqueue-evidence.jsonl
```

Evidence records can carry operator approval, Gate policy evidence,
external-sender allowance evidence, duplicate-work-fingerprint review evidence,
and optional refs. They convert to validation evidence, but they do not grant
approval, mutate Gate policy, query duplicates, create Agent Bus tasks, dispatch
runtimes, ingest review responses, apply candidates, or write canonical state.

CLI:

```text
chaseos pulse enqueue-evidence REQUEST_ID [evidence flags]
chaseos pulse enqueue-evidence-list [--request-id ID] [--evidence-id ID]
chaseos pulse enqueue-candidate REQUEST_ID --evidence-id EVIDENCE_ID
```

## Current Agent Bus Handoff Preflight

`bus_handoff_preflight.py` composes a persisted approval request, the latest or
specified evidence artifact, in-memory approval validation, active duplicate
work-fingerprint posture, and Agent Bus target posture.

The preflight is intentionally non-live and non-persisted. It can report
`ready_for_supervised_live_enqueue_review`, but that is only a readiness signal
for a later explicit operator command. It does not grant approval, mutate Gate
policy, write Agent Bus tasks, dispatch runtimes, ingest review responses,
apply candidates, call providers/connectors, activate schedules, or write
canonical state.

CLI:

```text
chaseos pulse handoff-preflight REQUEST_ID [--evidence-id EVIDENCE_ID]
```

## Current Operator/Gate Approval UI Contract

`operator_gate_approval_contract.py` turns a non-live handoff preflight into a
contract-only operator/Gate approval packet for a future UI or operator surface.
It exposes visible evidence fields, enabled/disabled decision controls, safety
warnings, and a supervised live enqueue command preview only when the underlying
handoff preflight is ready.

This is not the visual UI. It does not persist a contract artifact, grant
approval, mutate Gate policy, write Agent Bus tasks, dispatch runtimes, ingest
review responses, apply candidates, call providers/connectors, activate
schedules, or write canonical state.

CLI:

```text
chaseos pulse operator-gate-contract REQUEST_ID [--evidence-id EVIDENCE_ID]
```

## Current Supervised Live-Enqueue Rehearsal

`supervised_live_enqueue_rehearsal.py` consumes the operator/Gate approval
contract and returns a dry-run operator procedure packet. When the contract is
ready, it exposes the exact manual enqueue command preview and required
operator steps. When blocked, it exposes blocked reasons and hides the command.

This is not live enqueue execution. It does not persist rehearsal artifacts,
grant approval, mutate Gate policy, write Agent Bus tasks, dispatch runtimes,
ingest review responses, apply candidates, call providers/connectors, activate
schedules, or write canonical state.

CLI:

```text
chaseos pulse supervised-enqueue-rehearsal REQUEST_ID [--evidence-id EVIDENCE_ID]
```

## Current Real Approval Artifact-Chain Rehearsal

`real_approval_artifact_rehearsal.py` creates a real governed artifact chain
from an existing user Pulse deck:

1. append-only feedback candidate
2. append-only Agent Bus approval request
3. append-only enqueue evidence record
4. non-persisted supervised live-enqueue rehearsal

By default, the evidence record does not claim operator approval, Gate policy,
external-sender allowance, or duplicate-work review. The resulting rehearsal is
therefore blocked until those approval facts are explicitly supplied.

Live 2026-05-01 artifact IDs:

- candidate: `feedback-candidate-pulse-user-2026-04-29-01-show_more_like_this-6623cb04ce4a`
- request: `pulse-bus-enqueue-approval-f59f16c29a9a`
- evidence: `pulse-bus-enqueue-evidence-20318b971e53`

This surface does not grant approval, write Agent Bus tasks, dispatch runtimes,
ingest review responses, apply candidates, approve memory, call providers or
connectors, activate schedules, or write canonical state.

## Current Completion Status Surface

`completion_status.py` reports whether Pulse is done from repo-local evidence.
It reads the tracker, candidate/evidence/result/decision lanes, and reports the
current blockers without writing status artifacts.

CLI:

```text
chaseos pulse completion-status [--json]
```

As of 2026-05-01, the live status is `backend_proof_pending` with
`feature_done=false`.

## Current Approval Readiness Surface

`approval_readiness_summary.py` compresses the current Pulse request, evidence,
handoff preflight, operator/Gate contract, supervised rehearsal, and completion
status into a compact read-only summary.

CLI:

```text
chaseos pulse approval-readiness [REQUEST_ID] [--evidence-id EVIDENCE_ID] [--json]
```

As of 2026-05-01, the live readiness status is
`blocked_missing_required_evidence`. The summary can show missing evidence and
operator evidence-capture hints, but it does not write evidence, grant approval,
enqueue tasks, dispatch runtimes, ingest reviews, apply candidates, or write
canonical state.

## Current Approval Center Readiness Surface

`approval_center.py` aggregates deck inventory, feedback/Personal Map/execution
repair candidate lanes, review decisions, Agent Bus approval requests, final
evidence gate state, and a non-writing post-completion hardening availability
signal into one local readiness packet for future Studio approval-center work.

CLI:

```text
chaseos pulse approval-center-readiness [--request-id REQUEST_ID] [--evidence-id EVIDENCE_ID] [--json]
```

This is not the visual approval center and not an approval executor. It exposes
display-only action previews and does not write review decisions, apply
candidates, grant approvals, execute approval commands, create Agent Bus tasks,
dispatch runtimes, activate schedules, approve memory, call providers or
connectors, mutate canonical state, create a second datastore, or update the
R&D workbook.

## Current Memory/Runtime Readiness Surface

`memory_runtime_readiness.py` composes the existing Context Memory Core and
AgentHub evidence into one read-only readiness packet. It reads Layer C/D memory
summary evidence, runtime profiles, identity ledgers, runtime navigation maps,
repair memory, scorecards, accepted feedback signal records, Personal Map
candidates, and execution repair candidates.

CLI:

```text
chaseos pulse memory-runtime-readiness [--json]
```

The packet exposes readiness lanes for Context Memory Core, Personal Map
candidates, feedback rules, runtime profiles, runtime identity ledgers, runtime
navigation maps, execution repair memory, and runtime brain readiness. It does
not apply memory, apply feedback rules, mutate the Personal Map, apply execution
repair candidates, update runtime brains, grant permissions, write Agent Bus
tasks, dispatch runtimes, activate schedules, call providers/connectors, write
canonical state, create a second datastore, or update the R&D workbook.

## Current Guarded Agent Bus Enqueue

`bus_enqueue.py` is the only Pulse module that writes Agent Bus REVIEW tasks.
It requires a validation result with all required approvals satisfied, checks
active-task duplicate fingerprints, writes an enqueue result record under
`07_LOGS/Pulse-Decks/agent-bus-enqueue-results/`, and keeps all canonical
writeback, candidate-apply, memory-mutation, provider/connector, and schedule
activation flags false.

`pipeline_runner.py` composes the planning, approval-request, validation, and
enqueue layers. It remains `dry_run=True` by default. In live mode,
`operator_approved=True` proves only operator enqueue approval; Gate policy,
external-sender allowance, and duplicate-work-fingerprint review must be
provided as separate evidence flags before any task can reach ready validation.

`bus_review_response_ingest.py` can read completed review task events and, only
when explicitly run live, append review decision records. It does not apply
review decisions, mutate Pulse memory, approve Personal Map changes, or write
canonical project/knowledge state.

## Boundaries

- No unrestricted browsing.
- No full Studio visual UI implementation.
- No browser launch, dev server, or live interface runtime.
- No automatic writeback to `02_KNOWLEDGE/`.
- No mutation of `00_HOME/Now.md`, Dashboard, or Project-OS files.
- No autonomous promotion of memory or agent self-upgrade proposals.
- External connector signals require explicit enablement by the caller.
- No feedback application beyond pending-review candidate logs.
- No apply effects from review decisions.
- No apply effects from unified candidate inspection.
- No Agent Bus task creation from Pulse review contracts.
- No persisted Pulse approval requests from Agent Bus review contracts.
- No persisted queue or Agent Bus enqueue from Pulse review queue previews.
- No live Agent Bus enqueue from Pulse enqueue preflights.
- No persisted approval request or review-response ingestion from Pulse enqueue preflights.
- No approval grant or live Agent Bus handoff from Pulse approval-request records.
- No approval grant, Gate mutation, duplicate query, or live handoff from Pulse validation results.
- No approval grant, Gate mutation, duplicate query, or live handoff from Pulse evidence records.
- No approval grant, Gate mutation, Agent Bus write, runtime dispatch, candidate
  apply, or canonical writeback from Pulse handoff preflights.
- No visual UI render, persisted contract, approval grant, Gate mutation, Agent
  Bus write, runtime dispatch, candidate apply, provider/connector call,
  schedule activation, or canonical writeback from Pulse operator/Gate approval
  UI contracts.
- No feedback submission, approval execution, candidate apply, runtime
  dispatch, schedule activation, provider/connector call, canonical writeback,
  second datastore, or R&D workbook update from the read-only Studio Pulse
  product-shell mount.
- Governed Pulse controls may append pending-review feedback/action candidates
  only. They cannot write review decisions, apply candidates, approve memory,
  create tasks directly, write Agent Bus tasks, dispatch runtimes, activate
  schedules, call providers/connectors, or mutate canonical truth.
- No rehearsal persistence, live enqueue execution, approval grant, Gate
  mutation, Agent Bus write, runtime dispatch, review-response ingest,
  candidate apply, provider/connector call, schedule activation, or canonical
  writeback from Pulse supervised live-enqueue rehearsals.
- No approval claim, live enqueue execution, Agent Bus write, runtime dispatch,
  review-response ingest, candidate apply, memory approval, provider/connector
  call, schedule activation, or canonical writeback from Pulse real approval
  artifact-chain rehearsals.
- No status artifact write, approval grant, live enqueue execution, Agent Bus
  write, runtime dispatch, review-response ingest, candidate apply, memory
  approval, provider/connector call, schedule activation, canonical writeback,
  or R&D workbook update from Pulse completion status reports.
- No approval grant, approval execution, review-decision write, candidate apply,
  Agent Bus task write, runtime dispatch, schedule activation, provider or
  connector call, memory approval, canonical writeback, second datastore, or
  R&D workbook update from Pulse approval-center readiness reports.
- No memory mutation, feedback rule application, Personal Map candidate apply,
  execution repair candidate apply, runtime brain update, permission grant,
  Agent Bus task write, runtime dispatch, schedule activation, provider or
  connector call, memory approval, canonical writeback, second datastore, or
  R&D workbook update from Pulse memory/runtime readiness reports.
- No single operator-approved flag can imply Gate policy, external-sender
  allowance, or duplicate-work-fingerprint review evidence.

## Reconciliation Notes

The card schema now carries the master-context fields for `deck_id`,
`created_at`, `scope`, machine `type`, `why_it_matters`, `source_links`,
`promotion_status`, and `writeback_status`. `shared_coordination` is supported
as the explicit shared-audience label while existing `shared` artifacts remain
valid as a compatibility alias.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
