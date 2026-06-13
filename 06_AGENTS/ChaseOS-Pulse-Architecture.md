# ChaseOS Pulse Architecture

**Approval Center routing:** Pulse approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

**Status:** PARTIAL - first architecture and runtime scaffold pass  
**Created:** 2026-04-29  
**Runtime label:** Codex  
**Canonical scope:** Native ChaseOS proactive intelligence layer

## Definition

ChaseOS Pulse is the native proactive intelligence layer for ChaseOS. It turns
current operating truth, memory, source intelligence, project state, runtime
activity, and feedback into future-facing Pulse cards and decks.

Pulse is not a generic daily digest. It is not owned by OpenClaw cron, Windows
Task Scheduler, Hermes, n8n, or any external runtime. Those surfaces may execute
or render declared work later, but ChaseOS owns the schema, schedule intent,
source policy, feedback policy, writeback boundaries, and audit trail.

## Master-Context Distinctions

Pulse must preserve four different layers:

| Layer | Meaning | Pulse posture |
|---|---|---|
| Content | Raw or processed material such as notes, source packages, logs, captures, transcripts, PDFs, or build artifacts | Input only; not automatically durable truth |
| Context | Situation-relevant state selected for a run, project, agent, or decision | Selected and evidence-linked |
| Memory | Durable extracted understanding such as preferences, constraints, goals, patterns, and runtime lessons | Candidate-first unless explicitly reviewed |
| Pulse | Proactive synthesis that decides what matters next and proposes governed actions | Generated cards/decks, not canonical truth |

This is the central product distinction: a digest summarizes what happened, a
dashboard shows current state, and ChaseOS Pulse interprets operating state to
surface future-facing next-action intelligence.

## Map Separation

Pulse uses three different map surfaces:

| Map | Owner / purpose | Status |
|---|---|---|
| Vault Map | Shared ChaseOS/system map for operators and runtimes to understand where repo/vault truth lives | Existing ChaseOS architecture surface |
| Personal Map | User profile graph: domains, goals, projects, doctrine, habits/cadences, Business OS, learning, content/brand, and trading context | PARTIAL schema in `runtime/memory/personal_map.py` |
| Runtime Navigation Map | Per-runtime learned route overlay for safe navigation, common routes, repair paths, escalation points, and weak spots | Existing Layer C memory lane; Pulse references only in this pass |

Personal Map is not the Vault Map. Runtime Navigation Maps are not authority
grants. They are inspectable context surfaces subordinate to ChaseOS governance.

## Architecture Adopted

Pulse is a ChaseOS-owned pipeline:

1. Signal collection - gather declared local signals from governed sources.
2. Topic selection - group signals into future-facing operating topics.
3. Ranking - prioritize by urgency, evidence, source class, and feedback.
4. Deck generation - emit user, agent, or shared coordination decks.
5. Rendering - produce markdown or JSON for approved consumers.
6. Local surface rendering - render existing deck artifacts for operator review.
7. Feedback capture - expose operator feedback as governed candidates.
8. Feedback candidate persistence - append pending-review candidates to Pulse logs.
9. Feedback review queue - inspect pending candidates and build non-executing review/apply contracts.
10. Review-decision logging - persist operator review intent without applying effects.
11. Unified candidate inspection - read feedback, Personal Map, execution
    repair, and review-decision lanes together without applying effects.
12. Agent Bus review request contracts - shape non-mutating REVIEW task
    previews for registered runtimes without enqueueing tasks.
13. Agent Bus review queue previews - aggregate candidate review contracts in
    memory without persisting a queue or enqueueing tasks.
14. Agent Bus enqueue preflights - describe future operator-approved task
    handoff requirements without writing bus or approval state.
15. Agent Bus enqueue approval requests - persist operator-reviewable enqueue
    intent without granting approval or creating bus tasks.
16. Agent Bus enqueue approval validation - check request evidence in memory
    without granting approval or creating bus tasks.
17. Agent Bus enqueue evidence artifacts - persist operator/Gate evidence
    records without granting approval or creating bus tasks.
18. Agent Bus handoff preflight - compose request, evidence, validation,
    duplicate-work posture, and Agent Bus target posture without writing tasks.
19. Operator/Gate approval UI contract - expose a contract-only review packet
    for future operator/Gate UI surfaces without rendering UI or granting approval.
20. Supervised live-enqueue rehearsal - expose a dry-run operator procedure and
    manual command preview without executing live enqueue.
21. Real approval artifact-chain rehearsal - create a real feedback candidate,
    approval request, evidence record, and blocked supervised rehearsal from an
    existing user deck without claiming approval or writing bus tasks.
22. Guarded Agent Bus enqueue - create REVIEW tasks only after ready validation
    and duplicate-fingerprint checks, without applying candidates.
23. Pipeline runner - compose plan, approval request, validation, and guarded
    enqueue with dry-run as the default mode.
24. Review-response ingest - read completed review responses into review-decision
    records only when explicitly run live.
25. Audit and review - preserve evidence and truth-state checks before promotion.
26. Connector/source-scanner readiness - inventory declared local source lanes
    and connector adapter posture without reading source content, calling
    providers/connectors, scanning browser history, or enabling live external
    source access.
27. Connector/source-scanner local preview - turn already persisted local
    source artifacts into metadata-only source candidates without reading
    source content, executing connectors, or promoting sources.
28. Connector/source-scanner candidate cards - turn local preview metadata
    into user, agent, and shared-coordination Pulse cards without reading
    source content, executing connectors, promoting sources, or writing
    canonical state.
29. Connector/source-scanner live-approved proof - report the fail-closed
    live connector proof posture, required approval evidence slots, and
    pending-request artifact path without granting approval or executing
    connectors.

The first scaffold lives in `runtime/pulse/`. It validates basic card/deck shape,
writes backend markdown/JSON artifacts, renders a static local user-deck surface
from existing artifacts, and can append feedback candidates to a governed Pulse
log. It can also build read-only pending candidate queues and persist
non-applying review decisions. A unified inspector can now aggregate the
candidate and review-decision lanes as a read-only in-memory snapshot. It can
also build Agent Bus enqueue preflights, append approval-request records,
persist operator/Gate evidence records, validate explicit handoff evidence, and
inspect final non-live handoff readiness against duplicate and target posture.
It can also build a contract-only operator/Gate approval packet that future UI
surfaces can render without inventing approval semantics. It can now dry-run
the supervised enqueue procedure and expose the manual command preview without
creating Agent Bus tasks. A guarded enqueue module can create REVIEW tasks only
from a ready validation result and still does not apply candidates. The
pipeline runner remains dry-run by default, and its `operator_approved` flag
proves only operator approval; Gate
policy, external-sender allowance, and duplicate-work-fingerprint review are
separate evidence flags. Pulse now has a read-only connector/source-scanner
readiness contract over local source surfaces and connector adapter presence,
a metadata-only local preview of already persisted source artifacts,
multi-audience candidate-card generation from that metadata, and a fail-closed
live-approved proof request layer. It still does not perform live source
scanning, full Studio UI operation, feedback application, candidate
application, approval execution, canonical writeback, or autonomous promotion.

## Source Inputs

Pulse may generate cards from:

- user context memory
- personal map / user profile graph
- active projects and project operating files
- `00_HOME/Now.md` and `00_HOME/Dashboard.md`
- Source Intelligence Core outputs
- build logs
- agent activity logs
- AOR workflows and workflow outputs
- runtime profiles
- runtime reflection logs
- feedback history
- optional external sources/connectors only when explicitly enabled

External connector input is disabled by default and remains Tier 3/4 until
classified by the relevant ChaseOS workflow.

The current connector/source-scanner readiness command is:

```text
chaseos pulse connector-source-scanner-readiness --json
```

It reports source-surface and connector readiness only. It does not read source
content, call connectors, fetch RSS feeds, scrape web pages, access private
email/cloud documents, inspect browser history, read secrets, or promote any
source.

The current local preview command is:

```text
chaseos pulse connector-source-scanner-local-preview --json
```

It reports metadata-only source candidates from already persisted local
artifacts. It does not read file content or execute live connectors.

The current candidate-card command is:

```text
chaseos pulse connector-source-scanner-candidate-cards --json
```

It generates governed Pulse cards from local preview metadata only. Optional
`--write` mode creates user, agent, and shared-coordination deck artifacts under
`07_LOGS/Pulse-Decks/`. It does not read source content, call connectors, call
providers, activate schedules, execute approvals, approve memory, promote
sources, or write canonical state.

The current live-approved proof command is:

```text
chaseos pulse connector-source-scanner-live-approved-proof --json
```

It reports the approval-gated future live connector posture only. Optional
`--write-request` creates a pending operator-review JSON artifact under
`07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/`. It does not grant
approval, execute approvals, call connectors/providers, read source content,
promote sources, write Agent Bus tasks, activate schedules, or write canonical
state.

## Card Audiences

Pulse supports three card audiences:

| Audience | Purpose |
|---|---|
| `user` | Operator-facing personal and project intelligence |
| `agent` | Runtime-facing reflection, repair, and improvement prompts |
| `shared_coordination` | Coordination cards between operator and runtimes |

Runtime code also keeps `shared` as a legacy alias for existing deck artifacts.

## Card Classes

User card classes:

- Today's Operating Brief
- Future Prep
- Project Momentum
- Business OS Opportunity
- Learning / University Focus
- Content / Brand Edge
- Trading / Market Watch
- Research Watch
- Memory Update
- Personal Map Update
- Manual Input Needed
- Decision Needed
- Risk / Blocker
- Runtime Blocker
- Carry-Forward
- Schedule Catch-Up
- Suggested Delegation

Agent card classes:

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

Shared card classes:

- Agent Handoff
- AOR Pending Decision
- Multi-Agent Coordination
- Governance Risk
- Source Conflict
- Review Queue
- Cross-Runtime Blocker
- Schedule / Delivery Failure
- Promotion Candidate
- Truth-State Warning

## Governance Rules

- Pulse cards are proposals or briefs, not canonical truth.
- Pulse feedback may create memory candidates, not automatic memory writes.
- Pulse never writes to `02_KNOWLEDGE/` by default.
- Pulse never mutates `00_HOME/Now.md`, Dashboard, or Project-OS files.
- Pulse does not enable agent self-upgrade.
- Runtime profile or runtime brain data cannot grant permission.
- External browsing and connectors require explicit enablement.
- Full Studio/desktop visual UI work remains out of scope; the first local
  static deck surface is a derived artifact only.

## Native Schedule Approach

Pulse schedule manifests are ChaseOS-owned intent declarations under
`runtime/schedules/manifests/`.

This pass creates inactive manifest shapes for:

- `chaseos_pulse_daily.yaml`
- `hermes_runtime_pulse.yaml`

These are not OpenClaw cron jobs. `runtime/pulse/native_schedule_runner_proof.py`
now provides a non-executing proof that a future native schedule runner can
read these manifests and model missed-run catch-up/review decisions while
keeping manifests disabled. `runtime/pulse/native_schedule_activation_gate.py`
adds the supervised activation gate/request layer for future operator review:
it requires operator approval, a permission envelope, run-queue scope, audit
identity, runtime-adapter scope, rollback, external-scheduler denial, and
canonical-writeback denial references before it can report readiness.
`runtime/pulse/native_schedule_run_queue_audit_proof.py` then models the
proof-only run-queue entry and audit-event shapes that would be needed for a
future supervised run. Existing adapter runners may also read these manifests
later, but adapters remain executors, not owners.

OpenFlow is not present in repo truth, so no OpenFlow Pulse schedule manifest
was created.

Native schedule intent must include `schedule_id`, cadence, timezone,
`workflow_id`, delivery target, approval policy, enabled/disabled state,
catch-up policy, and audit identity. Missed runs should map to:

- machine off: `catch_up_once`
- server down: `queue_pending`
- runtime unavailable: `defer_to_review`
- approval timeout: `create_review_card`

Runtimes such as Hermes, OpenClaw/OpenFlow-style adapters, Codex, Claude Code,
or local/OSS models may execute declared work later, but they do not own Pulse
schedule intent.

## Business OS Example

If an OpenFlow/OpenClaw-style browser runtime repeatedly blocks on Shopify or
WordPress product work because product images, product video, or metadata are
missing, Pulse should generate governed cards rather than attempting hidden
completion:

- Manual Input Needed - request missing product assets or metadata.
- SOP Needed - propose a product-asset/preflight SOP draft.
- Connector Needed - surface missing image/video/analytics connector needs.
- Workflow Improvement - add preflight checks before upload attempts.
- Agent Skill Gap - record the runtime capability gap.
- Execution Repair Pattern - preserve the failure/workaround pattern as
  reusable runtime memory.

None of these cards may publish products, call external services, promote
knowledge, or mutate project truth without an explicit approval envelope.

## Phase Boundary

Phase 9 Pulse work should remain backend/control-plane first: memory schemas,
agent brains, native schedule manifests, deck generation, feedback candidates,
review queues, execution repair memory, and governed writeback contracts.

Phase 10 is the appropriate home for visual card polish, dashboard rendering,
Personal Map visualization, runtime brain dashboards, and approval queue UI.

## Implementation Status

| Surface | Status |
|---|---|
| Architecture docs | PARTIAL - first pass created |
| Card schema | PARTIAL - dataclass scaffold, expanded taxonomy, explicit source URL field, and tests |
| Backend minimal user deck | PARTIAL - markdown/JSON log artifacts generated under `07_LOGS/Pulse-Decks/users/` |
| Local user deck surface | PARTIAL - static local HTML surface generated from latest user deck JSON; feedback shown as candidate-only controls; not a live app |
| Feedback candidate persistence | PARTIAL - pending-review JSONL candidate logs under `07_LOGS/Pulse-Decks/feedback-candidates/` |
| Feedback review queue | PARTIAL - read-only pending inspector plus non-executing review/apply contract |
| Pulse review-decision log | PARTIAL - persisted review intent under `07_LOGS/Pulse-Decks/review-decisions/`; no apply effects |
| Unified candidate inspector | PARTIAL - read-only aggregate snapshot across feedback, Personal Map, execution repair, and review-decision lanes; no writes or apply effects |
| Agent Bus review request contract | PARTIAL - in-memory REVIEW task previews from candidate inspector items; no bus task creation, approval persistence, runtime dispatch, or apply effects |
| Agent Bus review queue preview | PARTIAL - read-only in-memory aggregate over Pulse candidate review contracts; no persisted queue, live enqueue, approval persistence, runtime dispatch, or apply effects |
| Agent Bus review queue audit | PASS - source/import and behavior guard tests verify the queue preview remains read-only, in-memory, non-enqueueing, non-applying, and non-canonical |
| Agent Bus enqueue design | PARTIAL - design-only preflight objects define required approvals, duplicate work-fingerprint review, recipient bounds, and task payload previews; no live enqueue, approval persistence, runtime dispatch, review-response intake, or apply effects |
| Agent Bus enqueue approval request | PARTIAL - append-only approval-request records under `07_LOGS/Pulse-Decks/agent-bus-approval-requests/`; no approval grant, live enqueue, runtime dispatch, review-response intake, candidate apply, or canonical writeback |
| Agent Bus enqueue approval validation | PARTIAL - in-memory validation of approval-request evidence; no validation persistence, approval grant, Gate mutation, duplicate query, live enqueue, runtime dispatch, or apply effects |
| Agent Bus enqueue evidence artifacts | PARTIAL - append-only evidence records under `07_LOGS/Pulse-Decks/agent-bus-enqueue-evidence/`; evidence can feed validation but does not grant approval, mutate Gate policy, query duplicates, create bus tasks, or apply candidates |
| Agent Bus handoff preflight | PARTIAL - non-live readiness inspector over persisted approval request, evidence artifact, validation, duplicate-work posture, and Agent Bus target posture; no persisted preflight, approval grant, Gate mutation, bus task creation, runtime dispatch, candidate apply, or canonical writeback |
| Operator/Gate approval UI contract | PARTIAL - contract-only packet over handoff preflight with visible evidence fields, decision controls, and supervised command preview; no visual UI, persisted contract, approval grant, Gate mutation, bus task creation, runtime dispatch, candidate apply, provider/connector call, schedule activation, or canonical writeback |
| Supervised live-enqueue rehearsal | PARTIAL - dry-run procedure packet over operator/Gate contract; exposes manual command preview only when ready; no rehearsal persistence, live enqueue execution, approval grant, Gate mutation, bus task creation, runtime dispatch, candidate apply, provider/connector call, schedule activation, or canonical writeback |
| Real approval artifact-chain rehearsal | PARTIAL / VERIFIED BLOCKED - created a live feedback candidate, approval request, and evidence record from the existing user deck; rehearsal correctly blocks because operator/Gate evidence is missing; no Agent Bus task, approval grant, runtime dispatch, candidate apply, or canonical writeback |
| Completion status surface | PARTIAL / READ-ONLY - `chaseos pulse completion-status --json` reports backend/control-plane catch-up as `phase10_ui_pending`, with Phase 10 UI as the remaining blocker and no authority flags expanded |
| Approval readiness summary | PARTIAL / READ-ONLY - `chaseos pulse approval-readiness --json` summarizes the current request/evidence/preflight/contract/rehearsal chain and missing approval evidence without writing evidence, granting approval, exposing a live command while blocked, or creating Agent Bus tasks |
| Guarded Agent Bus enqueue | PARTIAL - `runtime/pulse/bus_enqueue.py` can write REVIEW tasks only from a ready validation result and records outcomes; no candidate apply, canonical writeback, memory mutation, provider/connector call, or schedule activation |
| Pulse enqueue pipeline runner | PARTIAL - dry-run by default; live mode persists approval requests and requires separate evidence for operator approval, Gate policy, external-sender allowance, and duplicate-work-fingerprint review before guarded enqueue |
| Pulse review-response ingest | PARTIAL - can append review-decision records from completed review task events only when explicitly run live; no review decision apply, memory approval, Personal Map mutation, or canonical writeback |
| Context Memory Core schema | PARTIAL - event, atom, cluster, temporal fact, map, feedback primitives |
| Personal Map schema | PARTIAL - node/edge graph scaffold |
| Personal Map candidate store | PARTIAL - append-only pending-review JSONL artifacts and read-only queue |
| AgentHub/runtime brain schema | PARTIAL - profile/brain scaffold |
| Execution Repair Memory | PARTIAL - schema-only runtime memory entry and agent-card projection |
| Execution Repair candidate store | PARTIAL - append-only pending-review JSONL artifacts and read-only queue |
| Schedule manifests | PROOF-ONLY / INACTIVE - inactive native manifest shapes plus `ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof`, `ChaseOS-Pulse-Native-Schedule-Runner-Proof`, `ChaseOS-Pulse-Native-Schedule-Activation-Gate`, and `ChaseOS-Pulse-Native-Schedule-Run-Queue-Audit-Proof`; no daemon start, manifest enablement, real run queue write, real audit event write, runtime dispatch, workflow execution, approval execution, external scheduler ownership, or schedule activation |
| Connector/source scanner readiness | COMPLETE TARGETED / LIVE EXECUTION BLOCKED - `runtime/pulse/connector_source_scanner_readiness.py`; no connector calls |
| Connector/source scanner local preview | COMPLETE TARGETED / METADATA-ONLY - `runtime/pulse/connector_source_scanner_local_preview.py`; no source content reads |
| Connector/source scanner candidate cards | COMPLETE TARGETED / LOG-ONLY - `runtime/pulse/connector_source_scanner_candidate_cards.py`; multi-audience cards from local metadata only |
| Connector/source scanner live-approved proof | COMPLETE TARGETED / APPROVAL REQUEST PROOF / LIVE BLOCKED - `runtime/pulse/connector_source_scanner_live_proof.py`; pending request artifacts only, no connector calls |
| Feedback policy | PARTIAL - proposal/candidate only; append-only candidate persistence exists |
| Full Studio visual UI | NOT BUILT |
| Unrestricted browsing | NOT BUILT |
| Canonical writeback | NOT BUILT |
| Agent self-upgrade | NOT BUILT |

## Next Pass

The current Pulse schedule lane next pass is
`chaseos-pulse-supervised-native-schedule-activation-execution-proof`, but it
must remain blocked unless real operator approval and permission envelope
evidence exist. Do not treat the proof-only schedule packets, activation gate
request, or run-queue/audit proof as schedule activation; actual runner
activation/missed-run execution remains separate and approval-gated.

Pulse is not feature-complete yet because the full operator-facing UI is not built. The completion tracker is
`06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md`, the machine-readable status
command is `chaseos pulse completion-status --json`, and the compact approval
readiness command is `chaseos pulse approval-readiness --json`.

Graph links: [[Context-Memory-Core]] - [[Personal-Map-Architecture]] - [[AgentHub-Spec]] - [[Agent-Runtime-Brain-Architecture]] - [[Pulse-Card-Schema]] - [[Pulse-Feedback-Policy]] - [[ChaseOS-Pulse-Candidate-Store-Policy]] - [[ChaseOS-Pulse-Review-Decision-Log-Policy]] - [[ChaseOS-Pulse-Unified-Candidate-Inspector-Policy]] - [[ChaseOS-Pulse-Agent-Bus-Review-Request-Contract]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Preview]] - [[ChaseOS-Pulse-Agent-Bus-Review-Queue-Audit]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Design]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Approval-Request]] - [[ChaseOS-Pulse-Agent-Bus-Enqueue-Approval-Validation]] - [[ChaseOS-Pulse-Operator-Gate-Approval-UI-Contract]] - [[ChaseOS-Pulse-Supervised-Live-Enqueue-Rehearsal]] - [[ChaseOS-Pulse-Real-Approval-Artifact-Rehearsal]] - [[ChaseOS-Pulse-Connector-Source-Scanner-Candidate-Cards]] - [[ChaseOS-Pulse-Connector-Source-Scanner-Live-Approved-Proof]] - [[ChaseOS-Pulse-Native-Schedule-Activation-Gate]] - [[ChaseOS-Pulse-Native-Schedule-Run-Queue-Audit-Proof]] - [[ChaseOS-Pulse-Completion-Tracker]] - [[ChaseOS-Pulse-Completion-Status]] - [[ChaseOS-Pulse-Approval-Readiness-Summary]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
