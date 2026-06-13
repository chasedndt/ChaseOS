---
title: ChaseOS Pulse UI and Runtime Handoff
type: handover
status: ACTIVE / CURRENT IMPLEMENTATION CONTEXT
created: 2026-04-29
updated: 2026-05-07
phase: Phase 10 — ChaseOS Studio / Pulse UI
runtime: Codex + Hermes + registered ChaseOS runtimes
source_capture: 03_INPUTS/00_QUARANTINE/2026-04-29-ChaseOS-Pulse-user-dossier.md
related_architecture: ChaseOS-Pulse-Architecture.md
---

# ChaseOS Pulse UI and Runtime Handoff

## Purpose

This handoff records the active implementation pivot: **ChaseOS Pulse** is the user-facing feature family now being implemented around the existing Pulse scaffold and the upcoming Phase 10 product shell.

The source dossier is captured at:

- `03_INPUTS/00_QUARANTINE/2026-04-29-ChaseOS-Pulse-user-dossier.md`

That source is user-provided context, not automatic canonical truth. This handoff translates it into an implementation-safe ChaseOS plan.

## Naming Decision

The feature name is **ChaseOS Pulse**. Do not rename the user-facing feature to Operator Pulse, Context Pulse, Daily Digest, or a generic digest label. Internal implementation names may still include:

- Context Memory Core
- Personal Map
- AgentHub
- Runtime Brain
- Agent Pulse
- Pulse Card Deck
- Native Schedule Engine
- Pulse Feedback Loop
- Pulse Writeback Layer

## Current Live Repo Truth

As of this handoff, Pulse is already partially scaffolded:

- `06_AGENTS/ChaseOS-Pulse-Architecture.md`
- `06_AGENTS/Context-Memory-Core.md`
- `06_AGENTS/Personal-Map-Architecture.md`
- `06_AGENTS/AgentHub-Spec.md`
- `06_AGENTS/Agent-Runtime-Brain-Architecture.md`
- `06_AGENTS/Pulse-Card-Schema.md`
- `06_AGENTS/Pulse-Feedback-Policy.md`
- `06_AGENTS/Pulse-Truth-State-Audit-Checklist.md`
- `runtime/pulse/`
- `runtime/memory/`
- `runtime/agents/`
- `runtime/schedules/manifests/chaseos_pulse_daily.yaml`
- `runtime/schedules/manifests/hermes_runtime_pulse.yaml`
- `07_LOGS/Pulse-Decks/users/`

The existing scaffold is **PARTIAL** as a broad product family. Local UI
footholds now exist, but Pulse is still not a full Studio desktop, not a live
schedule runner, not external browsing, not canonical writeback, and not
autonomous memory promotion.

2026-04-30 update: the first local-only Pulse user deck surface is now scaffolded
as `runtime/pulse/local_surface.py`. It renders existing user deck JSON artifacts
from `07_LOGS/Pulse-Decks/users/` into a derived static HTML artifact and exposes
feedback as candidate records only. It is still not the full Studio desktop UI,
not a browser surface, not a live runtime, not a schedule runner, not MCP, not
delivery, not provider execution, and not canonical writeback.

2026-04-30 feedback update: `runtime/pulse/feedback.py` now includes an
append-only feedback candidate persistence lane under
`07_LOGS/Pulse-Decks/feedback-candidates/`, with
`runtime/pulse/local_surface.py` able to submit a candidate row for a card. This
is still pending-review only. It does not apply feedback to decks, approve
memory, create tasks, mutate project files, or enable canonical writeback.

2026-04-30 review-queue update: `runtime/pulse/feedback_review_queue.py` now
loads pending feedback candidates into a read-only queue and builds
contract-only review/apply objects. This is not a visual review UI, not
persisted review decisions, not feedback application, not memory approval, not
task creation, and not canonical writeback.

2026-04-30 OpenClaw operator-surface update: `runtime/pulse/local_surface.py`
now embeds a bounded read-only Operator Review Queue Snapshot from
`runtime/pulse/candidate_inspector.py`. The local surface can show candidate and
review-decision counts plus a small existing-lane preview. This remains a
derived static surface only: no persisted derived queue, no decision apply, no
memory approval, no task creation, no provider/connector calls, no schedule
activation, no canonical writeback, and no second datastore.

2026-04-30/05-01 Agent Bus handoff preview update: `runtime/pulse/local_surface.py`
now also embeds a read-only Agent Bus Review Handoff Preview from
`runtime/pulse/bus_review_queue.py`. It exposes the bounded REVIEW task previews
that current Pulse candidates would produce for peer-runtime review while
keeping bus task writes, approval-request writes, live dispatch, candidate
apply, review-response ingest, and canonical writeback blocked. This connects
the operator surface to the Agent Bus coordination lane without bypassing the
separate approval/evidence/final-enqueue gates.

2026-05-01 supervised handoff readiness update: the same local surface now
also embeds a read-only Supervised Live Handoff Readiness panel over persisted
Agent Bus enqueue approval requests. It composes
`runtime/pulse/bus_handoff_preflight.py` so an operator can inspect missing
evidence, duplicate work fingerprints, validation readiness, and Agent Bus
target posture before any final live enqueue command. This panel grants no
approval, performs no live handoff, writes no Agent Bus task, applies no
candidate, enables no runtime dispatch, and performs no canonical writeback.

2026-05-02 Phase 10 local app update: `runtime/studio/pulse_deck_app.py` now
wraps the existing Pulse local surface as a localhost-only Pulse Deck app. It
renders the latest user deck and accepts explicit operator feedback only as
pending-review candidates under `07_LOGS/Pulse-Decks/feedback-candidates/`.
The app is registered in `runtime/studio/app_launcher.py`, exposed by the
Studio Dashboard Pulse panel, and documented in
`06_AGENTS/ChaseOS-Pulse-Phase10-UI-Proof.md`. It does not apply feedback,
write review decisions, enqueue Agent Bus tasks, call providers/connectors,
activate schedules, approve memory, create a second datastore, or mutate
canonical state.

2026-05-06 10A0 Studio cockpit update: `runtime/studio/acquisition_cockpit.py`
and `runtime/studio/acquisition_cockpit_app.py` now expose Pulse roadmap
controls inside the Studio Acquisition Intake Cockpit. The cockpit can show
non-executing schedule runner proof/status, show the supervised native schedule
activation gate, write only a pending schedule activation review request under
`07_LOGS/Pulse-Decks/native-schedule-activation-requests/` with explicit
confirmation, preview Pulse review-contract enqueue payloads without writes,
and run an operator-approved Agent Bus enqueue action only when
`--confirm-action`, operator approval, Gate policy evidence, external-sender
allowance evidence, and duplicate work-fingerprint review evidence are all
present. This is not live schedule activation/execution, not manifest
enablement, not schedule daemon start, not run queue write, not runtime
dispatch, not workflow execution, not candidate application, not review-response
ingest, not provider/connector execution, and not canonical writeback.

2026-05-07 10A0 Studio cockpit update: the same cockpit now exposes the existing
proof-only native schedule run-queue/audit packet through
`pulse-schedule-run-queue-audit-proof` and
`pulse-schedule-run-queue-audit-write-proof`. The write-proof action requires
explicit confirmation and writes only proof JSON under
`07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/`. This is not a real
run queue write, not a real audit event write, not live schedule
activation/execution, not runtime dispatch, not workflow execution, not Agent Bus
task creation, not provider/connector execution, not Pulse memory or Personal Map
mutation, and not canonical writeback.

2026-05-07 10A0 native shell update: the Studio native shell now mounts a
read-only Pulse Schedule Proofs panel at `pulse-schedule-proof` (sidebar [Y]).
It is backed by `runtime/studio/pulse_schedule_proof_panel.py` and
`get_pulse_schedule_proof_panel()`, reads the existing 10A0 cockpit proof model,
filters out enqueue controls, and treats proof-write controls as display
metadata only. It exposes no activation button, no proof-write button, no
`--execute-activation`, no daemon start, no manifest patching, no real run
queue/audit write, no Agent Bus enqueue, no workflow execution, no
provider/connector call, and no canonical writeback.

2026-05-07 10A0 native shell Agent Bus enqueue update: the Studio native shell
now mounts a read-only Pulse Agent Bus Enqueue panel at `pulse-enqueue`
(sidebar [G]). It is backed by `runtime/studio/pulse_agent_bus_enqueue_panel.py`
and `get_pulse_agent_bus_enqueue_panel()`, reads review-contract preflights,
persisted approval requests, evidence slots, duplicate/target handoff posture,
and supervised manual command previews. It exposes no approval grant, no
approval-request or evidence write, no live Agent Bus task write, no runtime
dispatch, no candidate apply, no review-response ingest, no schedule activation,
no provider/connector call, no Pulse memory/Personal Map/R&D mutation, and no
canonical writeback.

## Active Implementation Direction

Pulse should be developed as a native ChaseOS proactive intelligence layer that sits above existing ChaseOS substrates:

1. Context Memory Core
2. Personal Map / User Profile Graph
3. AgentHub / Runtime Brain Layer
4. Signal Collector
5. Topic Selector and Ranker
6. Pulse Card Generator
7. Feedback Loop
8. Native Schedule Engine
9. Governed Writeback Layer
10. Studio / card deck UI

The key product distinction is:

- a digest summarizes what happened
- a dashboard shows current state
- **Pulse decides what matters next**

## What Codex/UI Runtime Should Build First

If Codex is taking the UI lane, it should start from the existing backend scaffold instead of inventing a new Pulse model. The first UI/service increment should render existing Pulse deck/card artifacts and expose feedback safely.

Read first:

- `03_INPUTS/00_QUARANTINE/2026-04-29-ChaseOS-Pulse-user-dossier.md`
- `06_AGENTS/ChaseOS-Pulse-Architecture.md`
- `06_AGENTS/ChaseOS-Pulse-UI-and-Runtime-Handoff.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Pulse-Card-Schema.md`
- `06_AGENTS/Pulse-Feedback-Policy.md`
- `runtime/pulse/card_schema.py`
- `runtime/pulse/minimal_deck.py`
- `runtime/pulse/writeback.py`
- `runtime/pulse/test_pulse_schema.py`
- `runtime/pulse/test_backend_minimal_deck.py`

First UI target:

- show the latest user Pulse deck from `07_LOGS/Pulse-Decks/users/`
- render card classes, titles, summaries, evidence links, related nodes, recommended actions, confidence, and governance/writeback state
- include visible labels that cards are proposals/briefs, not canonical truth
- capture feedback as feedback events/candidates only
- do not enable memory promotion, task creation, connector calls, schedule activation, or canonical writes without separate governed surfaces

Initial implementation target:

- `runtime/pulse/local_surface.py`
- `runtime/pulse/feedback.py`
- `runtime/pulse/feedback_review_queue.py`
- `runtime/pulse/candidate_inspector.py`
- `runtime/pulse/bus_review_queue.py`
- `runtime/pulse/test_local_surface.py`
- `runtime/pulse/test_feedback_candidates.py`
- `runtime/pulse/test_feedback_review_queue.py`
- `runtime/pulse/test_candidate_inspector.py`
- `07_LOGS/Pulse-Decks/users/YYYY-MM-DD-user-pulse.surface.html`
- `07_LOGS/Pulse-Decks/feedback-candidates/YYYY-MM-DD-feedback-candidates.jsonl`

This first surface is static and local. It reads the backend user deck JSON and
does not maintain a second datastore or submit feedback automatically. Feedback
candidate logs are only written when a caller explicitly submits a governed
candidate.

The next safe operator surface may wrap the read-only review queue, but any
persisted review-decision lane, memory approval, task creation, or canonical
writeback must be added as a separate governed pass.

## Hermes Parallel Lane

Hermes should avoid duplicating Codex UI implementation. Useful Hermes-side work while Codex builds UI:

- keep Pulse docs truth-synced to live repo state
- run focused read-only validation
- inspect Agent Bus state and coordinate through structured bus packets
- produce review/audit build logs
- identify UI/backend contract drift
- preserve the source dossier and remind runtimes that it is an input artifact, not canonical truth

Hermes should not independently build a competing desktop UI unless explicitly assigned that lane.

## Non-Negotiable Boundaries

Pulse must not:

- become OpenClaw cron ownership
- become Hermes-owned memory
- become a loose daily digest
- silently scan browsing history
- read credentials
- call external connectors by default
- auto-promote memory atoms to approved memory
- auto-promote cards to `02_KNOWLEDGE/`
- mutate `00_HOME/Now.md`, Dashboard, Project-OS files, or protected docs from the card deck UI
- treat runtime brain or identity-ledger state as permission authority
- create a second unmanaged Studio datastore

Default writeback state:

1. card generated
2. card saved/logged
3. card archived
4. task/memory/project/knowledge promotion only through explicit governed flows

## Bus Coordination Note

Codex is not currently a registered Agent Bus recipient in this repo. A Hermes attempt to create a bus packet directly to `Codex` failed closed because Gate requires a valid target runtime manifest. A coordination notice was therefore routed to registered peer runtime `OpenClaw` under normal priority.

If Codex is expected to participate as a first-class bus runtime later, add a proper adapter/runtime manifest instead of bypassing Gate.

## Implementation Prompt For Codex

```text
Continue ChaseOS with repo-grounded task `chaseos-pulse-ui-first-surface`.

Read first:
- 03_INPUTS/00_QUARANTINE/2026-04-29-ChaseOS-Pulse-user-dossier.md
- 06_AGENTS/ChaseOS-Pulse-Architecture.md
- 06_AGENTS/ChaseOS-Pulse-UI-and-Runtime-Handoff.md
- 06_AGENTS/ChaseOS-Studio-Architecture.md
- 06_AGENTS/Pulse-Card-Schema.md
- 06_AGENTS/Pulse-Feedback-Policy.md
- runtime/pulse/card_schema.py
- runtime/pulse/minimal_deck.py
- runtime/pulse/writeback.py
- runtime/pulse/test_pulse_schema.py
- runtime/pulse/test_backend_minimal_deck.py

Build the first local-only ChaseOS Pulse card/deck surface against the existing Pulse backend scaffold. Render latest user Pulse deck artifacts from 07_LOGS/Pulse-Decks/users/ and expose feedback as governed feedback candidates only. Preserve ChaseOS governance: no browser, MCP, delivery, cron/schedule activation, live provider calls, secret display, automatic memory approval, canonical writeback, or second datastore. Add focused tests and required build/archive/daily/activity logs.
```

## Validation Before UI Work

Run:

```text
PYTHONPATH=. uvx pytest runtime/pulse runtime/memory runtime/agents -q
PYTHONPATH=. python3 -m runtime.cli.generate_docs --check
PYTHONPATH=. python3 -m runtime.cli.main agent-bus status --json
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
