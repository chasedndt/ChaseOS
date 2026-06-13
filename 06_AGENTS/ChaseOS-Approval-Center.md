---
title: ChaseOS Approval Center
type: canonical-operator-surface
status: PARTIAL / NATIVE READ-ONLY PANEL MOUNTED / CROSS-FEATURE AGGREGATOR / FORGE SOURCE-SPECIFIC DECISION HANDOFF / FORGE OPERATOR DECISION FORM / FORGE DECISION-BOUND EXECUTOR CONSUMPTION / FORGE MARKETPLACE-IMPORT APPROVAL ROUTING / FORGE LIFECYCLE VISUAL QA / FORGE PROOF DECK PACKAGED / FORGE STUDIO CLICKTHROUGH VERIFIED
version: 0.1
created: 2026-05-09
updated: 2026-05-20
owner: ChaseOS
phase: Phase 10 / Phase 11 governance surface
---

# ChaseOS Approval Center

Canonical graph node: [[ChaseOS-Approval-Center]].

## Purpose

The ChaseOS Approval Center is the operator-facing review surface for governed
approval work across ChaseOS features. It is not owned by one subsystem.

It exists to answer:

- what approval-related items exist,
- which subsystem produced them,
- what action or write they are asking for,
- what evidence or source artifact supports the request,
- whether the item is pending, approved, rejected, blocked, or already consumed,
- and which authority remains denied until a later governed execution path.

The Approval Center is a visibility and review surface first. Phase 10 Studio is
an operator surface over ChaseOS, not a canonical truth engine. Approval
visibility is not the same as approval mutation, approval consumption, canonical
promotion, or target execution.

## Current Status

Status: PARTIAL / NATIVE READ-ONLY PANEL MOUNTED / CROSS-FEATURE AGGREGATOR.

Current native Studio implementation:

```text
runtime/studio/approval_center_panel.py
```

Current StudioAPI method:

```text
get_approval_center_panel
```

Current CLI surface:

```text
python -m runtime.cli.main studio approval-center-panel --json
```

Current panel registry id:

```text
approval-center
```

The current native panel is read-only. It aggregates approval posture and source
references, but it does not grant, reject, consume, execute, resume, dispatch,
or write approval decisions.

Current repo-truth evidence from the P10-5 audit/regression sweep:

- `runtime/studio/approval_center_panel.py` is a native read-only cross-source
  Studio model.
- `runtime/studio/approval_center_app.py` remains a localhost-only Pulse
  Approval Center app surface.
- `runtime/studio/approval_queue_panel.py` is a read-only panel contract over
  the Pulse Approval Queue static artifact.
- Focused Approval Center tests verify the panel/app/queue rendering boundary;
  adjacent approval preview/review/dry-run chunks are testable, but passing
  dry-run tests do not authorize approval consumption or execution.
- The live panel exposes `operator_decision_controls_present=false`,
  `approval_execution_available=false`,
  `allowed_actions=[inspect-approval-center-panel]`, and `possible_writes=[]`.
- 2026-05-20 Chaser Forge routing adds read-only discovery for sandbox,
  live-install, and rollback approval request artifacts under Agent-Activity.
  The panel shows lifecycle state, request digest, touch set, source refs, and
  safety posture only; it does not approve, consume, execute, install, or
  rollback Forge items.
- 2026-05-20 Chaser Forge lifecycle visual QA renders a temporary fixture
  through the production Approval Center frontend and captures desktop/mobile
  static UI evidence under
  `07_LOGS/Studio-Visual-QA/2026-05-20-chaser-forge-approval-center-lifecycle-proof/`.
  The rendered source group exposes pending, approved-pending-execution,
  consumed, rejected, and invalid Forge lifecycle counts. The fixture vault is
  removed after rendering and no real-vault Forge approval artifacts persist.
- 2026-05-20 Chaser Forge proof deck packages the implementation build logs,
  this Approval Center routing truth, and the lifecycle visual QA evidence into
  `07_LOGS/Workflow-Proofs/2026-05-20_chaser-forge-proof-deck.md` and `.json`.
  The deck is log-only evidence packaging; it does not add review-decision
  writing, approval consumption, Forge execution, registry mutation, extension
  file write/delete, provider/model, schedule, Agent Bus, protected-core, Pulse
  memory, Personal Map, R&D truth-state, or canonical authority.
- 2026-05-20 Chaser Forge Studio clickthrough verifies the native Chaser Forge
  panel can render the proof deck section and artifact paths through the
  production Studio shell route `#/chaser-forge`. Evidence lives under
  `07_LOGS/Studio-Visual-QA/2026-05-21-chaser-forge-marketplace-proof-deck-clickthrough/`.
  This is read-only Studio visibility and does not add Approval Center decision,
  approval consumption, Forge execution, registry mutation, extension file
  write/delete, proof-deck write, provider/model, schedule, Agent Bus,
  protected-core, Pulse memory, Personal Map, R&D truth-state, or canonical
  authority.
- 2026-05-20 Chaser Forge source-specific decision handoff adds
  `review_chaser_forge_approval_decision` and
  `runtime.forge.approval_decision.build_forge_approval_decision_handoff`.
  This is not a generic Approval Center control. It can record an approve/reject
  decision for one pending Forge approval artifact when the caller supplies the
  exact request digest and exact generated operator statement. It writes only a
  decision sidecar under the matching Forge approval source `_decisions/` folder
  and decision metadata back to the source artifact. It does not consume
  approvals, reserve exact-once markers, execute sandbox/live/rollback actions,
  mutate the Forge registry, write/delete extension files, patch Studio, mutate
  protected core/runtime policy/schedules, call providers/connectors, write
  Agent Bus tasks, or mutate Pulse memory, Personal Map, R&D truth-state, or
  canonical state.
- 2026-05-20 Chaser Forge Approval Center visual QA now verifies the
  source-specific handoff token and no-consumption/no-execution posture in the
  production Approval Center renderer. Evidence lives under
  `07_LOGS/Studio-Visual-QA/2026-05-20-chaser-forge-approval-center-decision-handoff/`.
- 2026-05-20 Chaser Forge decision-bound executor consumption now requires the
  sandbox, live-install, and rollback source-specific executors to validate a
  recorded `forge_approval_decision_handoff` sidecar before consuming an
  approved source artifact. Manual `status=approved` JSON mutation without the
  matching sidecar fails closed. This binds executor consumption to the
  source-specific decision digest without adding generic Approval Center
  approve/reject/execute controls.
- 2026-05-20 Chaser Forge operator decision form adds
  `get_chaser_forge_approval_decision_form` and
  `runtime.forge.approval_decision_form.build_forge_approval_decision_form`.
  This is a read-only, source-specific form contract for one pending Forge
  approval artifact. It prepares approved/rejected options, exact copyable
  operator statements, expected request digest, and the
  `review_chaser_forge_approval_decision` submit payload. It does not write a
  decision sidecar, mutate the source approval artifact, consume approvals,
  execute Forge lifecycle actions, mutate the registry, write/delete extension
  files, reserve exact-once markers, or add generic Approval Center controls.
- 2026-05-20 Chaser Forge marketplace-import routing adds read-only discovery
  for package import sandbox review artifacts under
  `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/`. Studio API
  `request_chaser_forge_marketplace_import_sandbox_approval` can create a
  digest-gated pending review artifact for a local package, and the
  source-specific decision handoff/form support the `marketplace-import` family.
  This remains review metadata only: no package install, sandbox request
  execution, approval consumption, exact-once marker reservation, registry
  mutation, extension file mutation, provider/connector call, Agent Bus task, or
  canonical mutation is added.
- 2026-05-20 Chaser Forge marketplace-import sandbox request bridge adds
  `get_chaser_forge_marketplace_import_sandbox_request` and
  `request_chaser_forge_marketplace_import_sandbox_request` as source-specific
  Forge APIs outside generic Approval Center authority. The bridge validates an
  approved, unconsumed marketplace-import review artifact plus its matching
  decision sidecar, then can write or reuse one normal pending sandbox approval
  request under `_forge_sandbox_approvals/` when the exact bridge digest is
  supplied. It does not make the Approval Center a decision writer or executor,
  and it does not install packages, consume approvals, reserve exact-once
  markers, mutate the registry, write extension files, call providers/connectors,
  dispatch Agent Bus tasks, or mutate canonical state.

## Approval Sources

The Approval Center may aggregate these approval families:

| Source family | Current role | Example artifacts / contracts |
|---|---|---|
| Studio Service approvals | Approval packets for Studio write requests | `runtime/studio/approvals/*.json` |
| Pulse approval readiness | Candidate lanes, review decisions, final evidence gate, Agent Bus request posture | `runtime/pulse/approval_center.py` |
| OSRIL approval gates | Runtime/session approval gates and response records | `runtime/osril/approvals.py` |
| Runtime resume evidence | Approval-linked resume response/evidence visibility | `runtime/osril/approvals/*.resume.json` |
| SiteOps approvals | SiteOps promotion/execution approval requests | `runtime/siteops/approvals.py`, `07_LOGS/SiteOps-Approvals` |
| Gate request artifacts | Gate/request decision evidence where present | Gate request artifact lanes |
| Runtime startup controls | Startup/autostart approval posture and requestability | `runtime/studio/runtime_startup_controls.py` |
| Phase 11 Chat proposals | Chat-originated pending Studio Service approval requests; source digest, duplicate protection, and handoff audit are recorded by the bounded queue writer | `runtime/studio/phase11_chat_approval_queue_write.py`, `runtime/studio/approvals/*.json`, `runtime/studio/approvals/chat-handoffs/*.json` |
| Chaser Forge approvals | Sandbox install, live-install, rollback, and marketplace-import request artifacts, source-specific operator decision form contracts, and source-specific decision sidecars for extension lifecycle review | `07_LOGS/Agent-Activity/_forge_sandbox_approvals/*.json`, `07_LOGS/Agent-Activity/_forge_live_install_approvals/*.json`, `07_LOGS/Agent-Activity/_forge_rollback_approvals/*.json`, `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/*.json`, `runtime.forge.approval_decision_form`, matching `_decisions/*.json` |

This table is intentionally feature-agnostic. Any future subsystem can become
an Approval Center source only if it produces bounded, auditable approval
artifacts with clear authority posture.

## Minimum Render Contract

Every Approval Center item should render enough context for an operator to
review the request without guessing or opening raw side-effect payloads. The
minimum visible fields are:

| Field family | What the operator must see | Current live truth |
|---|---|---|
| Request intent | The action being requested and the source subsystem that produced it | Studio Service approval `action_spec.action_type`, Pulse lane/action preview labels, Phase 11 Chat proposal/action-spec previews |
| Touch set | The files, refs, systems, or target paths the request would affect | Studio `target_path` / `target_ref`, affected files/systems metadata, preview/review/consumption future output and marker paths |
| Digest / provenance | Stable digest or source references that bind the displayed request to its originating artifact | Studio request digests where present, Phase 11 Chat action/source digests and handoff records, Pulse source refs and deck/candidate paths |
| State | Whether the item is pending, approved/ready, rejected/blocked, invalid, partial, duplicated, consumed, or waiting on execution proof | Source group status/counts, Studio Service status counts, SiteOps statuses, workspace-upgrade consumed/pending-execution-proof posture, preview/review/consumption lifecycle constants |
| Safety rationale | Why the item is safe or unsafe to review and which authority remains denied | `FORBIDDEN_AUTHORITY`, `authority`, `blocked_effects`, safety metadata where lower-phase packets provide it, and explicit no-execution queue handoff text |
| Audit trail | The artifact path, submitted/review timestamps, handoff record, source ref, or proof ref needed to trace the request | Studio JSON timestamps/review fields, source refs, Phase 11 Chat handoff audit records, SiteOps/OSRIL/workspace-upgrade refs; no universal request-to-effect chain yet |
| Operator review state | Whether the human is inspecting, needs to decide, has already decided, or is blocked by missing lower-phase proof | Pending/ready/blocked counts, duplicate/invalid/partial flags, queue-handoff blocker fields, and explicit absence of generic decision controls |

The panel may summarize or redact raw requested content. It should show what is
being requested, why, what it will touch, what evidence binds the request, and
which authority remains unavailable.

## What The Approval Center Is

The Approval Center is:

- a cross-feature approval visibility surface,
- a typed queue/review view,
- a place to inspect pending approval requests and related evidence,
- a way to keep approval items discoverable across Pulse, Studio, OSRIL,
  SiteOps, Runtime Cockpit, and future Chat surfaces,
- a bridge between proposal surfaces and later governed decision/execution
  surfaces.

## What The Approval Center Is Not

The Approval Center is not:

- a blanket write authority,
- a hidden executor,
- a provider/model caller,
- a runtime dispatcher,
- a browser controller,
- a memory promotion engine,
- a second canonical datastore,
- a way to bypass Gate, role-card, trust-tier, or protected-file rules.

## Authority Boundary

By default, the Approval Center blocks:

- vault/source writes,
- approval artifact writes unless a separate source-specific queue writer is
  explicitly implemented and approved,
- review decision writes,
- approval grants/rejections,
- approval consumption,
- approval execution,
- runtime resumes,
- workflow execution,
- Agent Bus task writes,
- provider or connector calls,
- browser control,
- schedule activation,
- memory approval,
- credential or secret display,
- canonical mutation.

Future passes may add narrow write paths, but each path must be source-specific,
operator-confirmed, auditable, test-covered, and bounded to its declared
artifact root. A queue write is still not execution.

Current narrow exception: Forge decision handoff is a source-specific review
decision writer, not generic Approval Center authority. It is bounded to Forge
approval roots, including marketplace-import review artifacts, digest-gated,
exact-statement-gated, sidecar-audited, and leaves approval consumption/execution
to separate Forge executors or future reviewed package-to-sandbox contracts.

The following backend authorities remain Phase 9-and-below contracts unless a
separate source-specific implementation is approved and verified:

- approval consumption or execution,
- source-pack promotion,
- graph or canonical knowledge mutation,
- runtime dispatch or resume execution,
- browser, shell, provider, connector, or external system authority,
- credential, secret, provider, or runtime configuration mutation,
- Agent Bus task writes,
- protected-file writes or canonical promotion.

Phase 10 may render status, request packets, and dependency evidence for those
authorities. It must not imply that a visible approval request is already safe
to execute, consume, promote, dispatch, or canonically write back.

## Approval Lifecycle Vocabulary

ChaseOS should keep these lifecycle states distinct:

1. **Proposal preview** - a feature shows what it would ask for; no artifact is
   written.
2. **Queue write** - an explicit operator action writes a pending approval
   request artifact.
3. **Review decision** - an operator records approve/reject/defer against the
   request.
4. **Consumption preflight** - an executor verifies the decision, digest,
   scope, and exact-once state before any target effect.
5. **Execution proof** - a separately governed executor performs only the
   approved action and writes evidence.
6. **Target write or action** - the actual vault/runtime/browser/provider/host
   effect, if and only if that specific executor is built and approved.

The current native Approval Center is primarily at stages 1-2 visibility. It
does not provide stages 3-6 as a generic capability.

Current implementation nuance: some source-specific lower-phase modules may
already implement bounded preview, review, queue-write, readiness, or dry-run
proof helpers. Those helpers are evidence for the Approval Center to display;
they do not make the Approval Center a generic approval executor.

## Relationship To Phase 11 Chat

The Phase 11 Chat panel can currently preview intents, proposal cards, provider
readiness, approval handoff posture, and conversation persistence target paths.

The current proposal/action preview UX is an operator-control surface, not an
executor. Proposal cards may render a bounded scope and summary, affected files
or systems, risk, required approvals, dry-run or blocked state, handback route,
and an evidence digest. The queue-handoff contract exposes this as
`proposal_card_preview`; the live-provider contract exposes the parallel
provider-facing shape as `action_preview_card`. Both cards exist so an operator
can understand what a Chat-originated request would ask ChaseOS to review before
any later governed queue write or execution lane is involved.

The copy boundary is explicit: preview cards do not execute, consume approvals,
dispatch runtimes, call providers, control browsers, read credentials, mutate
configuration, write protected or canonical files, write conversations, or
promote knowledge. Unsupported or missing authority returns lower-phase routing
notes naming the missing contract, affected Phase 10/11 surface, lower-phase
owner/surface, minimum proof needed, and blocked action reason. Handback labels
such as queue/review/open-in-Approval-Center describe routes to existing
governed contracts; they are not direct action buttons.

`phase11-chat-approval-queue-write-execution-proof` is the bounded handoff path
for supported Chat proposals. With an explicit operator queue-write request and
an exact `action_digest`, it may write one pending `StudioService` approval
request into `runtime/studio/approvals/` plus a matching handoff audit record in
`runtime/studio/approvals/chat-handoffs/`. The approval request metadata records
both `phase11_chat_action_digest` and `phase11_chat_source_digest`; duplicate
active requests for the same digest return the existing approval instead of
creating a second queue artifact.

That queue-write pass must still not:

- approve the request,
- execute the request,
- write the proposed project/source/conversation target,
- call providers,
- dispatch runtimes,
- control browsers,
- write Agent Bus tasks,
- mutate canonical state.

In other words: Chat may become a source of pending approval requests, but the
Approval Center remains the review surface and the executor remains a separate
governed path.

## Runtime-Lane Payoff

Clear approval packets make persistent runtime operators safer. Hermes,
OpenClaw, Optimus, and future runtime-instance lanes can inspect the same
operator-facing request context — intent, touch set, provenance, state, safety
rationale, audit trail, and review posture — without receiving extra authority.

That is the ChaseOS operating-system alignment: the Approval Center improves
operator intelligence and coordination while AOR, Gate, role-card, trust-tier,
and protected-file governance continue to decide what may actually execute or
be promoted. Runtime lanes can help review, summarize, route blockers, and
surface proof gaps, but they do not bypass approval consumption, canonical
mutation, runtime dispatch, shell/browser/provider authority, credential/config
mutation, or Gate-controlled writeback.

For ChaseOS Pulse specifically, the Approval Center is the operator review
surface for proactive-intelligence packets that may become approval requests.
Pulse can surface candidates and action previews; the Approval Center can make
their review posture visible; governed Phase 9-and-below contracts still own any
later enqueue, execution, or writeback.

## Current Operator Commands

Inspect the native Studio Approval Center panel contract:

```powershell
python -m runtime.cli.main studio approval-center-panel --json
```

Inspect Pulse approval-center readiness:

```powershell
python -m runtime.cli.main pulse approval-center-readiness --json
```

Start the older localhost-only Pulse Approval Center app plan or server:

```powershell
python -m runtime.cli.main studio approval-center-app --dry-run --json
python -m runtime.cli.main studio approval-center-app --host 127.0.0.1 --port 8773
```

## Current Implementation References

- Native Studio panel: `runtime/studio/approval_center_panel.py`
- Pulse readiness contract: `runtime/pulse/approval_center.py`
- Pulse local mount: `runtime/studio/approval_center_app.py`
- Studio service queue reader: `runtime/studio/approval_center_panel.py`
- Phase 11 Chat proposal-card preview contract: `runtime/studio/phase11_chat_approval_handoff_queue_contract.py`
- Phase 11 Chat provider action-preview contract: `runtime/studio/phase11_chat_live_provider_approval_preview.py`
- Phase 11 Chat approval queue writer: `runtime/studio/phase11_chat_approval_queue_write.py`
- Phase 11 Chat handoff audit records: `runtime/studio/approvals/chat-handoffs/*.json`
- Chaser Forge approval request roots:
  `07_LOGS/Agent-Activity/_forge_sandbox_approvals/*.json`,
  `07_LOGS/Agent-Activity/_forge_live_install_approvals/*.json`,
  `07_LOGS/Agent-Activity/_forge_rollback_approvals/*.json`,
  `07_LOGS/Agent-Activity/_forge_marketplace_import_approvals/*.json`
- Chaser Forge proof deck: `runtime/forge/proof_deck.py`,
  `07_LOGS/Workflow-Proofs/2026-05-20_chaser-forge-proof-deck.md`,
  `07_LOGS/Workflow-Proofs/2026-05-20_chaser-forge-proof-deck.json`
- OSRIL approval state: `runtime/osril/approvals.py`
- SiteOps approvals: `runtime/siteops/approvals.py`
- Runtime startup posture: `runtime/studio/runtime_startup_controls.py`

## Related Documentation

- [[ChaseOS-Pulse-Approval-Center-Readiness]]
- [[ChaseOS-Pulse-Studio-Approval-Center-Local-Mount]]
- [[ChaseOS-Pulse-Approval-Queue-UI]]
- [[ChaseOS-Pulse-Approval-Queue-Studio-Panel-Mount]]
- [[Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application]]
- [[Approval-and-Decision-Trace-Summary-Context-Application]]
- [[ChaseOS-Studio-Architecture]]
- [[ChaseOS-Studio-Phase10-Implementation-Tracker]]
- [[ChaseOS-Phase11-Architecture]]
- `07_LOGS/Build-Logs/2026-05-04-ChaseOS-studio-approval-center.md`

## Definition Of Done For A Future Complete Approval Center

Approval Center should not be marked COMPLETE until it has:

- a canonical source registry for approval-producing features,
- stable item schema across source families,
- dedupe/idempotency rules for pending approval artifacts,
- explicit review-decision write path with operator confirmation,
- exact-once decision consumption contracts,
- target-specific execution proof lanes,
- audit links from request to decision to consumption to effect,
- tests for no hidden execution,
- tests for stale/digest-mismatched approval denial,
- tests for duplicate execution denial,
- documentation that separates queue writes, review decisions, consumption, and
  execution.

Until then, it remains PARTIAL and governed by source-specific passes.

## Lower-Phase Dependencies To Keep Visible

The Approval Center should continue to route missing backend authority using
this dependency shape rather than silently expanding Phase 10 authority:

1. missing contract: canonical cross-source approval item registry/schema with
   required intent, touch set, digest/provenance, state, safety rationale, and
   source refs; affected Phase 10/11 surface: Studio Approval Center, Pulse
   Approval Queue panel, Phase 11 Chat-originated approval items; lower-phase
   owner/surface: Phase 9-and-below approval artifact producers; minimum proof
   needed: schema fixtures and adapter tests proving every source emits required
   fields or fails closed; blocked action reason: Phase 10 cannot safely render
   or decide a unified queue item by inferring heterogeneous source semantics.
2. missing contract: source-specific operator review-decision write path for
   approve/reject/defer; affected Phase 10/11 surface: Approval Center review UX
   and Chat-originated pending requests; lower-phase owner/surface:
   source-specific Phase 9 approval writer/decision modules; minimum proof
   needed: operator-confirmed decision artifact writer tests with scoped roots,
   exact approval-id/digest binding, duplicate/mismatch denial, and no target
   execution; blocked action reason: visibility cannot become approval mutation
   without a governed decision writer.
3. missing contract: exact-once approval consumption and idempotency marker
   contract per action family; affected Phase 10/11 surface: consumed badges and
   any future execute affordance; lower-phase owner/surface: source-specific
   Phase 9 consumption/preflight modules; minimum proof needed: dry-run and
   write-mode tests for digest/scope match, marker absence/presence,
   create-new-only marker behavior, duplicate/replay refusal, and no
   host/canonical/provider mutation until executor stage; blocked action reason:
   UI must not imply approved equals executable or consumed.
4. missing contract: normalized audit trail chain from request to decision to
   consumption to execution proof/effect; affected Phase 10/11 surface: approval
   trace panel, chronology/provenance drill-through, item details; lower-phase
   owner/surface: Agent-Activity, Operator-Briefs, Decision-Ledger, OSRIL,
   SiteOps, Pulse producers, and governed executor proof writers; minimum proof
   needed: fixtures and tests linking source refs, digests, decision IDs,
   consumption marker IDs, and effect proof paths without protected/canonical
   writes; blocked action reason: Phase 10 can show refs but cannot claim full
   effect provenance yet.
5. missing contract: Gate/authority policy for when a display action preview may
   become executable; affected Phase 10/11 surface: Pulse action previews,
   Approval Center display actions, future Chat/Studio action controls;
   lower-phase owner/surface: ChaseOS Gate, command-contract registry,
   source-specific CLI handlers/executors; minimum proof needed: Gate policy and
   tests proving execution remains false by default and only source-specific
   allowlisted operations execute with approval evidence; blocked action reason:
   previewing commands is not the same as dispatch/provider/Agent Bus/canonical
   effect authority.

## Graph Links

[[Agent-Control-Plane]] - [[Permission-Matrix]] - [[Trust-Tiers]] -
[[Vault-Map]] - [[ChaseOS-Gate]] - [[ChaseOS-Studio-Architecture]] -
[[ChaseOS-Studio-Phase10-Implementation-Tracker]] -
[[ChaseOS-Phase11-Architecture]] - [[Operator-Surface-Runtime-Interaction]] -
[[Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application]] -
[[ChaseOS-Pulse-Approval-Center-Readiness]] -
[[ChaseOS-Pulse-Approval-Queue-UI]] - [[SiteOps-Approval-Policy]]

## Graph Hygiene Governance Links

Linked by Codex (2026-05-09): [[Agent-Control-Plane]] .
[[Permission-Matrix]] . [[Trust-Tiers]] . [[Vault-Map]]
