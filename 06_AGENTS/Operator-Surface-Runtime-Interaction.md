---
title: Operator Surface + Runtime Interaction Layer
type: architecture
status: phase9-runtime-feature-scope-complete — Phase 9 runtime-side OSRIL feature scope is COMPLETE / VERIFIED; Phase 10+ operator surfaces and long-lived continuation UX remain PLANNED; Phase 9 global closeout is not claimed
version: 1.7
created: 2026-04-08
updated: 2026-05-12
phase: Phase 9 (runtime-side) / Phase 10 (surface-side) — cross-phase family
knowledge_class: canonical-state
---

# Operator Surface + Runtime Interaction Layer (OSRIL)
## ChaseOS — Cross-Phase Feature Family Architecture

> The Operator Surface + Runtime Interaction Layer is the feature family that bridges ChaseOS's internal runtime/control plane with a live operator experience — visible task execution, real-time feedback, approval surfaces, voice interaction, and session continuity — while preserving all ChaseOS governance constraints.

**Version:** 1.7
**Created:** 2026-04-08
**Status:** Phase 9 runtime-side feature scope COMPLETE / VERIFIED — contract/session/event inspection, immutable approval-response records, OSRIL session-state application markers, bounded AOR approval-gate resume, read-only wait/resume queue surface, and Gate-bound one-shot `resume-ready` runner are built. This closes OSRIL's Phase 9 feature scope only, not Phase 9 globally. The cross-phase OSRIL family remains PARTIAL overall because Phase 10+ operator surfaces, reconnect transport, voice/visual surfaces, companion surface, and long-lived continuation UX are still future; ChaseOS governance constraints apply from day one.

**Phase 9 closeout:** `06_AGENTS/OSRIL-Phase9-Closeout.md`

**Approval Center routing:** Phase 10+ OSRIL approval surfaces route through [[ChaseOS-Approval-Center]] for the current cross-feature Approval Center truth. OSRIL remains the runtime/session approval substrate; the Approval Center is the operator-facing aggregation surface.

**Voice I/O routing:** Phase 10 voice ingress/egress is architected in [[Voice-IO-Architecture]]. Voice remains an ingress/experience lane only: spoken requests become untrusted structured intent candidates until reviewed, confirmed, and routed through existing OSRIL / Agent Bus / Workflow Registry / Gate paths.

---

## What OSRIL Is

The Operator Surface + Runtime Interaction Layer (OSRIL) is a cross-phase ChaseOS feature family that does one thing: makes ChaseOS legible and interactive to its operator — in real time, with session continuity, without bypassing governance.

Without OSRIL, ChaseOS is a strong internal system — excellent at governed ingestion, structured memory, bounded autonomous execution, and audit trails — but with no live feedback surface for the operator. You run a workflow; you read logs after. You have no way to see what is happening mid-execution, confirm an approval gate in context, or interact from a phone.

OSRIL changes that. It adds:
- A runtime interaction contract so the operator can receive events from AOR in real time
- Action dispatch visibility so execution is not a black box
- A runtime session model so work can be resumed without re-briefing
- An operator shell (Phase 10) so the operator has a live surface — browser, voice, or companion
- Voice I/O (Phase 10) as a first-class optional interaction path

OSRIL sits **on top of** ChaseOS governance — it does not bypass it.

---

## Why OSRIL Exists

ChaseOS Phase 9 delivers bounded autonomous execution (AOR) and scheduled pipelines (SBP). These produce real execution events: workflow started, permission gate reached, output written, approval needed, failure halted.

Currently none of those events reach the operator in real time. The operator discovers them by reading logs. This is acceptable for fire-and-forget workflows, but insufficient for:
- Approval-gated workflows that must pause for human confirmation
- Long-running operations where the operator wants status visibility
- Voice-initiated tasks or briefings
- Mobile operator scenarios (viewing a brief from a phone)
- Session continuity across multiple operator devices

OSRIL is the infrastructure layer that routes those events to wherever the operator is — without those events becoming execution bypasses or authority sources.

---

## Core Principles

### 1. Surface Does Not Govern
The operator shell is a window into AOR and the vault — not a command authority above them. Approvals triggered from the shell are recorded by AOR and enforced through the same permission and audit chain as all other operator actions. The UI does not become the control plane.

### 2. Transport Does Not Trust
The runtime interaction contract (event bus) routes events from AOR to the operator surface. Events are read-only outputs of AOR execution — they are not instructions arriving from an untrusted surface. Inputs from the shell surface (operator approval responses, task triggers) are validated by AOR before execution. They are not ambient commands.

### 3. Session State Is Not Canonical Memory
The Runtime Session Model maintains active task/session state for operator convenience. This is runtime-local state — it is ephemeral by default. Anything that needs to persist to canonical memory goes through standard vault writeback and Gate. The session store is not a replacement for `07_LOGS/` or `02_KNOWLEDGE/`.

### 4. Voice I/O Is a Provider-Neutral Adapter
Voice input (STT) and output (TTS) are pluggable adapters in Phase 10. The architecture does not assume a specific voice provider. Provider-specific integrations live in adapter modules — they do not reach into the control plane.

### 5. Harness Agnosticism Is Maintained
The same event bus schema and session model should function regardless of whether the active execution harness is Anthropic, OpenAI, or a local runtime. Provider-specific quirks live in the adapter layer. The OSRIL contract is harness-neutral.

### 6. Gate Rules Apply at Every Surface
The operator shell cannot trigger promotions, protected-file writes, or cross-repo actions that would be blocked by the Gate if attempted through the CLI. Every action initiated from the shell goes through the same AOR → Gate chain as any other execution path.

---

## Phase Split

OSRIL is a cross-phase family. The two halves are architecturally distinct:

| Half | Phase | What It Is |
|------|-------|------------|
| Runtime-side | Phase 9 | Infrastructure inside AOR — event bus, dispatch visibility, session model, harness-agnostic routing |
| Surface-side | Phase 10 | Operator-facing surfaces — browser shell, voice UI, visual shell, companion surface |

**Phase 9 builds the runtime foundation.** Phase 10 consumes it. Phase 10 surfaces cannot be built without the Phase 9 contracts being stable.

---

## Phase 9 — Runtime-Side Half

These four subfeatures live inside Phase 9 AOR infrastructure. They create the runtime foundation that Phase 10 surfaces will consume.

### Subfeature 1: Runtime Interaction Contract

**What it is:** A defined event bus schema that standardizes how AOR execution events are communicated from the runtime to any consuming surface. The contract defines the event types, their fields, the message format (JSON), session continuity behavior, and reconnect protocol.

**Event types (minimum viable schema):**
- `status` — runtime state change (idle / working / waiting_approval / halted)
- `task_started` — AOR workflow execution begun; includes workflow_id and permission ceiling
- `task_progress` — mid-execution progress update; structured text
- `approval_required` — execution gate reached; operator response expected
- `approval_response` — immutable operator response applied to OSRIL session state; AOR consumes approved responses through bounded `approval_gate` resume records
- `task_complete` — workflow finished; outcome and writeback summary
- `task_failed` — workflow halted; failure reason and vault state

**Session continuity:** The event bus maintains session identity across reconnects. If the operator shell disconnects and reconnects, it can retrieve recent event history for the current session.

**Where it lives:** `runtime/aor/event_bus.py` (future); event schema documented in `runtime/aor/schemas/event_bus_schema.yaml` (future).

**Status:** COMPLETE / VERIFIED for Phase 9 runtime-side feature scope — `runtime/osril/contract.py`, `runtime/osril/session.py`, `runtime/osril/inspector.py`, `runtime/osril/wait_resume.py`, `runtime/osril/resume_ready.py`, normalized AOR outcome emission into `runtime/osril/run/`, read-only CLI inspection through `chaseos osril sessions|show|events`, approval queue/response inspection through `chaseos osril approvals`, read-only wait/resume readiness through `chaseos osril wait-resume`, one-shot approved-ready resume through `chaseos osril resume-ready`, and `approval_response` event/application recording through `chaseos osril respond` are live. Broader transport/reconnect routing and all Phase 10 surfaces remain future.

---

### Subfeature 2: Action Dispatch Visibility

**What it is:** Operator-visible real-time log of what AOR is executing. Every tool call, file write, external API call, and delivery action emits an event through the Runtime Interaction Contract. The operator can see what the system is doing mid-execution — not just the final output.

**What it is not:** A command surface. Dispatch visibility is read-only from the operator's perspective. Seeing an action does not authorize it. Authorization is declared in the workflow manifest.

**Where audit records go:** Dispatch visibility events are a live view into the same records that go to `runtime/audit/` (future). They do not create a parallel audit trail — they surface it.

**Status:** COMPLETE / VERIFIED for Phase 9 baseline — bounded run-level dispatch visibility exists because AOR emits normalized `status`, `task_started`, `approval_required`, `task_complete`, and `task_failed` events to `runtime/osril/run/*.events.jsonl`, and operators can inspect them through `chaseos osril events`. Richer per-tool/per-write streaming remains Phase 10+ enrichment, not a remaining Phase 9 OSRIL blocker.

---

### Subfeature 3: Runtime Session Model

**What it is:** Work mode and resumable session infrastructure. AOR tracks the active workflow session — which workflow is running, which project context is loaded, what the current execution state is — and makes this resumable across operator sessions.

**Resumable session behavior:**
- Operator disconnects during a long-running workflow
- On reconnect, the operator shell presents current session state (workflow, progress, pending approvals)
- The operator can resume interaction without re-briefing the runtime

**Important distinction:** The runtime session store is ephemeral runtime-local state. It is NOT canonical memory. It does NOT write to `07_LOGS/` without explicit operator confirmation. When a session ends, the session store is cleared. Anything worth keeping has already been written through the standard AOR → writeback → Gate chain.

**SQLite vs. markdown:** Runtime-local session state can use a lightweight store (SQLite or equivalent). This is explicitly separate from ChaseOS durable knowledge (vault markdown). The session store never becomes a knowledge source without a Gate-governed promotion.

**Status:** COMPLETE / VERIFIED for Phase 9 baseline — runtime-local session snapshots exist via `runtime/osril/session.py` and `runtime/osril/run/*.session.json`, with read-only inspection through `chaseos osril sessions` and `chaseos osril show`. Approval wait/resume readiness is inspectable through `chaseos osril wait-resume`, and approved-ready one-shot resume is available through `chaseos osril resume-ready`. Full reconnect UX and long-lived surface continuation remain Phase 10+ work.

---

### Subfeature 4: Harness-Agnostic Operator Execution

**What it is:** AOR workflow dispatch routes correctly regardless of whether the active execution harness is Anthropic (Claude Code), OpenAI, or a local runtime. Provider-specific quirks — different API surfaces, different tool call formats, different streaming behavior — live in the adapter layer and do not propagate upward into the dispatch logic or the OSRIL event bus.

**Why this matters:** If the runtime interaction contract is Anthropic-specific, migrating to a different harness breaks the operator shell. OSRIL requires the event bus schema and session model to be harness-neutral.

**Where the boundary is:** The Execution Adapter Standard (`06_AGENTS/Execution-Adapter-Standard.md`) already defines the adapter pattern. Harness-agnostic operator execution is the OSRIL-specific constraint that the event bus and session model must be implemented above the adapter boundary, not inside it.

**Status:** COMPLETE / VERIFIED for Phase 9 baseline — current AOR-to-OSRIL schema/emission lives above the adapter boundary and is provider-neutral. Broader executor/adapter producers still need to conform as more Phase 10+ surfaces come online.

---

### Phase 9 — Approval-Linked Execution Flow

A fifth Phase 9 concern that spans the AOR execution engine and OSRIL:

**What it is:** When a workflow manifest declares an approval gate, AOR pauses execution, emits an `approval_required` event via the Runtime Interaction Contract, and waits for an operator response. The approval response is recorded in the audit trail before execution continues.

**Governance:** Approval gates are declared in the workflow manifest. AOR cannot add or remove approval gates at runtime. An approval response from the shell does not modify the workflow manifest. The approval record is immutable once written.

**Status:** COMPLETE / VERIFIED for Phase 9 runtime-side feature scope — OSRIL can list pending `approval_required` events, record one immutable operator response through `chaseos osril respond`, write a separate immutable application marker, append an `approval_response` event that releases the session from `waiting_approval` or halts it on denial, expose a read-only wait/resume queue through `chaseos osril wait-resume`, and run bounded one-shot approved-ready resume through `chaseos osril resume-ready`. AOR stops `operator-explicit` workflows at `approval_gate`, resumes on a referenced approved response through `operator_approval_ref`, writes a one-time immutable `.resume.json` marker, and rejects denial/replay before handler execution. Long-lived continuation UX remains Phase 10+ work; it is not required for OSRIL Phase 9 feature closeout.

---

## Phase 10 — Surface-Side Half

These subfeatures are the operator-facing surfaces built on top of the Phase 9 runtime infrastructure. None of these can be meaningfully built without the Phase 9 Runtime Interaction Contract being stable.

### Subfeature 5: Operator Shell

**What it is:** A browser-accessible operator shell that surfaces ChaseOS runtime state, task activity, approvals, and system health. The operator can see what workflows are running, what events have occurred, what approvals are pending, and the current system status — without navigating raw markdown files.

**Core capabilities:**
- Runtime state display (idle / working / waiting_approval / halted)
- Task activity feed — recent events from AOR
- Approval queue — pending approval_required events awaiting operator response
- System health panel — Gate status, quarantine queue depth, audit trail health
- Settings/configuration surface — vault root, active adapters, credential health

**Architecture constraint:** The Operator Shell is a read + approve surface. All execution remains in AOR. The shell cannot initiate executions that are not declared in the Workflow Registry.

**Status:** NOT BUILT — conceptual.

---

### Subfeature 6: Voice I/O Architecture

**What it is:** Provider-neutral voice interaction abstraction — speech-to-text (STT) for operator input and text-to-speech (TTS) for operator briefings. The architecture defines the voice session, intent-candidate, transcript/audit, STT/TTS adapter, and browser playback contract without coupling to a specific voice provider.

**Canonical contract:** `06_AGENTS/Voice-IO-Architecture.md`.

**Key architecture decisions:**
- STT and TTS are pluggable adapters; future implementations should live behind a common `runtime/studio/voice/` contract rather than reaching into AOR, Gate, Agent Bus, or canonical write helpers.
- Browser-side voice must start as explicit operator-triggered listening, not ambient always-on recording.
- Voice ingress produces a Tier 4 `voice_intent_candidate` with `requires_operator_confirmation: true`; it is not a command and cannot dispatch workflows, grant/consume approvals, write Agent Bus tasks, or mutate canonical notes.
- TTS speaks already-visible governed text/status/brief payloads only; approval prompts must match the visible approval object.
- Transcript retention defaults to ephemeral raw audio and audit-scoped text only when a separate governed action needs evidence.
- Playback state machine remains idle / listening / transcribing / review-pending / speaking / error / closed and stays tied to OSRIL/AOR runtime state events.
- Analyser seams are visual feedback only and do not become evidence, biometric identity, or authority signals.

**Governance:** Voice I/O is an ingress/experience adapter. Spoken requests are untrusted intent until structured and confirmed, then routed through existing OSRIL / Agent Bus / Workflow Registry / Gate paths. It does not bypass AOR or the Gate.

**Status:** ARCHITECTED / NOT BUILT — provider-neutral contract seeded; no live microphone capture, provider calls, credential reads, browser AudioContext mount, workflow dispatch, approval execution, Agent Bus write, transcript persistence, or canonical writeback is enabled.

---

### Subfeature 7: Live Visual Shell

**What it is:** A state-tied visual animation/feedback layer in the operator shell. The visual state machine reflects the AOR/runtime state (idle / thinking / working / waiting_approval / blocked / failed / speaking / complete). Useful for ambient operator awareness.

**Architecture note:** This is pure UX chrome. It consumes the same AOR/OSRIL/runtime lifecycle/approval posture events that drive the rest of the operator shell — it does not create its own data path. The visual layer is purely cosmetic and entirely subordinate to the operator shell. Implementation is a Phase 10 concern.

**Seeded contract:** `06_AGENTS/Live-Visual-Shell-Contract.md` now maps source classes, visual states, precedence, future contract packet shape, QA proof expectations, and lower-phase dependency routing. It explicitly forbids workflow execution, approval consumption, runtime/lifecycle mutation, Agent Bus writes, provider/connector/browser calls, and canonical writeback from the visual shell.

**Status:** CONTRACT SEEDED — implementation not built; future work should start with fixture-backed state mapping and read-only Studio contract tests.

---

### Subfeature 8: Companion Surface

**What it is:** A mobile/tablet/browser companion surface for the operator. The companion allows the operator to: view active briefs and workflow outputs, respond to approval requests, trigger declared workflow executions, and view system health — from a phone or tablet.

**Architecture seed:** `06_AGENTS/Companion-Surface-Mobile-Tablet-Architecture.md` now defines the Phase 10 companion-surface lane over live Phase 11 companion-status/selection truth. It covers brief viewing, approval inboxes, capture-trigger previews, runtime status cards, push/delivery posture, privacy/security, backend blockers, and a strict authority ceiling.

**Backend requirement:** The Phase 9 Runtime Interaction Contract and the existing StudioService/AOR/Gate response chain must remain the source of action truth. Mobile/tablet delivery, approval responses, capture triggers, credentials, runtime dispatch, and canonical writes route through their lower-layer contracts; the companion is only a consumer/request surface.

**Permission constraint:** The companion surface inherits the same permission ceilings as any other operator surface. It cannot initiate executions not declared in the Workflow Registry. Approval responses from the companion follow the same audit chain as desktop responses. Companion personality/status never grants authority.

**Status:** SEEDED / NOT LIVE — architecture and read-only companion-status/selection footholds exist, but live mobile/tablet auth, gateway delivery, capture trigger, approval-response execution, runtime dispatch, and canonical write paths remain blocked behind their proper Gate/AOR/StudioService dependencies.

---

### Subfeature 9: Runtime Support Loops

**What it is:** A governed set of post-execution support subsystems that improve operator experience and runtime quality over time.

**Subsystems:**
- **QA Verification** — post-execution check that validates workflow outputs against declared success criteria; reports discrepancies to operator
- **Proactive Suggestions** — after task completion, the runtime generates next-step suggestions (governed output; requires operator approval before any action is taken)
- **Usage Tracking** — tracks workflow invocations, approval patterns, and runtime utilization (feeds Agent Scorecards — Phase 9 second-wave)
- **Learning / Execution Repair** — accumulates failure patterns and operator corrections into Execution Repair Memory (already architectured in `06_AGENTS/Agent-Memory-Architecture.md`)

**Governance constraint:** All support loop outputs are governed. Suggestions are not auto-executed. QA reports go to the operator for review. Tracking feeds AOR audit trail and Agent Scorecards — not a separate database. Execution Repair Memory follows the four-tier repair lifecycle already defined.

**Status:** IMPLEMENTED / PROVEN READ-ONLY — `06_AGENTS/Runtime-Support-Loops-Contract.md` now reflects the shipped Phase 10 support-loop surface: `runtime/studio/runtime_support_loops.py` builds the contract and four packet families, `StudioAPI.get_runtime_support_loops_panel` exposes the panel, and the native registry mounts `runtime-support-loops`. Parent proof `t_c6791bf1` verified focused support-loop/API/registry tests and a live no-write snapshot with `changed_file_count: 0`. The surface remains advisory-only: QA reports, suggestions, usage metrics, and repair candidates may be inspected, but they do not approve actions, consume approvals, create Agent Bus tasks, dispatch runtimes, mutate memory, self-upgrade agents, call providers/connectors, or write canonical state.

---

## JARVIS Reference Analysis — Adopt / Adapt / Reject

ChaseOS OSRIL was informed by analyzing a reference JARVIS system. This section documents the design decisions made. JARVIS is reference material only — ChaseOS does not adopt its provider coupling, UI-first architecture, or ambient trust model.

### ADOPT / ADAPT

| JARVIS Component | ChaseOS Equivalent | Decision |
|-----------------|-------------------|----------|
| `main.ts` — browser state machine (idle/listening/thinking/speaking) | AOR runtime state events + Phase 10 Operator Shell state display | ADOPT — runtime state model is clean; adapt states to AOR event types |
| `ws.ts` — WebSocket with reconnect/backoff | Runtime Interaction Contract — event bus with reconnect | ADOPT pattern — ChaseOS event schema is ChaseOS-defined, not JARVIS-specific |
| `server.py` — event dispatch (status/task_spawned/task_complete/audio) | Runtime Interaction Contract server-side; AOR dispatch visibility | ADAPT — wire to AOR pipeline, not direct LLM call; event types defined by OSRIL schema |
| `work_mode.py` — project work session continuation | Runtime Session Model — resumable AOR sessions | ADAPT — ChaseOS sessions are AOR workflow continuations; not CLI `--continue` |
| `planner.py` — planning/confirmation flow | Approval-Linked Execution Flow | ADAPT — approvals declared in workflow manifest; not runtime-generated |
| `settings.ts` — health/config surface | Operator Shell settings/health panel | ADOPT concept — ChaseOS status = Gate status, audit health, pipeline status |
| `qa.py` — post-task QA verification | Runtime Support Loops — QA Verification subsystem | ADOPT pattern — governed output; feeds AOR audit trail |
| `suggestions.py` — proactive suggestions | Runtime Support Loops — Proactive Suggestions | ADOPT concept; suggestions require operator approval before action |
| `tracking.py` — usage analytics | Agent Scorecards + AOR audit trail analytics | ADOPT — feed through AOR audit trail, not separate database |
| `voice.ts` — STT/TTS/AudioContext | Voice I/O Architecture — Phase 10 | ADOPT pattern — STT/TTS as provider-neutral adapters; pause/resume lifecycle |
| `mail_access.py` — READ-ONLY constraint | Role card permission floor pattern | ADOPT as governance model — explicit permission ceiling per system integration |
| `calendar_access.py` — background cache | Adapter with role card scope | ADAPT — platform-neutral; declared in manifest; read-only by default |
| `notes_access.py` — READ+CREATE only | Operator adapter with explicit ceiling | ADOPT constraint pattern |

### REJECT / HEAVY ADAPT

| JARVIS Component | Why Rejected or Heavily Adapted |
|-----------------|--------------------------------|
| `dispatch_registry.py` — SQLite as task truth | SQLite is acceptable for runtime-local ephemeral state; REJECTED as canonical truth; ChaseOS uses vault markdown + `runtime/audit/` |
| `memory.py` — SQLite FTS for memories/tasks | REJECTED as canonical memory; runtime-local queryable cache is OK; durable knowledge is vault markdown through Gate |
| `actions.py` — direct system actions (terminal, browser, Claude) | HEAVY ADAPT — every action must go through AOR + Gate + permission ceiling; no ambient system access; actions must be declared in workflow manifest |
| `browser.py` — Playwright automation | ADAPT — browser automation as a governed adapter declared in manifest; not ambient access |
| `screen.py` — screen awareness | DEFER — outside Phase 9/10 scope; future perception adapter |
| `learning.py` / `evolution.py` — autonomous template mutation | REJECT autonomous mutation; ChaseOS equivalent = Execution Repair Memory (requires operator sign-off at each tier) |
| `ab_testing.py` — A/B testing | DEFER — post-Phase-10 optimization concern |
| `orb.ts` — particle visualization | ADOPT concept as Live Visual Shell (Phase 10 UX chrome only) |
| Fish Audio / Anthropic coupling in core | REJECT — voice and model providers are pluggable adapters; coupling belongs in adapter layer only |
| UI dictating control plane | REJECT — control plane is AOR + Gate; UI is a read/approve surface only |
| Ambient trust / authority escalation | REJECT — all surfaces respect the same permission ceilings and Gate rules |

---

## Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **Autonomous Operator Runtime (AOR)** | OSRIL runtime-side subfeatures live inside AOR Phase 9 infrastructure. AOR is the execution engine; OSRIL is the transparency and interaction layer above it. |
| **ChaseOS Gate** | Gate rules apply at all OSRIL surfaces. No OSRIL subfeature can bypass Gate. Approval responses from the shell flow through the AOR → Gate chain. |
| **Execution Adapter Standard** | Harness-Agnostic Operator Execution requires the event bus and session model to be implemented above the adapter boundary defined in `06_AGENTS/Execution-Adapter-Standard.md`. |
| **Agent Memory Architecture** | Runtime Session Model is Layer D (workspace/task-local). Support Loop state (tracking, learning) feeds Layer C (Agent/Runtime-Specific Memory) and Layer E (Execution History). |
| **Agent Scorecards** | Usage Tracking (support loop) feeds Agent Scorecards in Phase 9 second-wave. |
| **Execution Repair Memory** | Runtime Support Loops — Learning subsystem is the Phase 10+ surface of Execution Repair Memory (already architectured in Phase 9). |
| **Scheduled Briefing Pipelines (SBP)** | SBP outputs (briefings, digests) may be surfaced through the Operator Shell and delivered via Voice I/O (Phase 10). SBP is an AOR workflow type; OSRIL is the interaction layer above it. |
| **Interface / Experience Layer (Phase 10)** | OSRIL is a named feature family within the broader Phase 10 interface planning. OSRIL provides the runtime interaction contracts and specific operator surfaces; Interface / Experience Layer also includes SIC workspace browser, provenance inspector, memory inspector, and Agent Identity Ledger UI — which are outside OSRIL scope. |
| **Runtime Navigation Map** | The RNM is an internal runtime navigation aid. OSRIL is the external operator-facing interaction layer. They are distinct; the RNM does not expose permissions — it informs routes. |

---

## What Is Not in Scope for OSRIL

These are explicitly not OSRIL concerns:

- **Autonomous knowledge promotion** — humans remain in the promotion loop regardless of what the shell surfaces
- **Bypassing workflow manifest declarations** — the shell cannot add, remove, or modify what a workflow is authorized to do
- **Replacing ChaseOS durable memory with runtime-local stores** — session state is ephemeral; SQLite for runtime state is acceptable; SQLite for canonical knowledge is rejected
- **UI-dictated control plane** — OSRIL surfaces make ChaseOS legible; they do not define ChaseOS governance
- **Non-governed system actions** — OSRIL does not grant the shell ambient OS access (terminal, filesystem beyond declared scope)
- **Screen awareness or real-world perception adapters** — these are future adapter concerns outside current phase
- **A/B testing or autonomous template evolution** — post-Phase-10 optimization concerns
- **Paperclip integration** — reserved for post-Phase-10; MUST NOT bypass Gate; constraint documented in `06_AGENTS/Phase9-Adopted-Feature-Specification.md`

---

## Current Status and Next Steps

**Phase 9 subset (runtime-side): COMPLETE / VERIFIED**

The Phase 9 runtime-side OSRIL feature scope is closed. This is not a global Phase 9 closeout. Current live truth:
- `runtime/osril/contract.py` defines the bounded machine-readable event schema
- `runtime/osril/session.py` persists runtime-local `*.session.json` snapshots plus `*.events.jsonl` event streams
- `runtime/osril/approvals.py` persists immutable approval responses, immutable application markers, linked `approval_response` session events, and immutable AOR approval-gate resume markers for consumed approvals
- `runtime/osril/wait_resume.py` exposes read-only wait/resume state for pending, approved-ready, denied, resumed, unapplied, and missing approval ids
- `runtime/osril/resume_ready.py` provides the bounded one-shot approved-ready resume runner behind `chaseos osril resume-ready`
- `runtime/aor/engine.py` emits normalized run-level `status`, `task_started`, `approval_required`, `task_complete`, and `task_failed` events and enforces bounded `approval_gate` resume for `operator-explicit` manifests
- `06_AGENTS/OSRIL-Phase9-Closeout.md` records the complete Phase 9 closeout boundary, evidence, non-claims, and Phase 10+ continuation backlog

Phase 10+ continuation sequence:

1. Build the Live Operator Shell as a read + approve surface that consumes OSRIL events, sessions, and wait/resume state. The browser lane is now scope-seeded in `06_AGENTS/Live-Operator-Shell-Browser-Surface.md` with a dedicated `runtime/operator_surface/browser/` folder guide; it can render readiness/proof/dependency states but still cannot execute browser actions.
2. Add reconnect/history transport without making transport a trusted command path
3. Convert the read-only wait/resume queue and bounded approval-gate resume into a long-lived continuation UX while preserving AOR/Gate/resume-marker enforcement
4. Expand OSRIL from run-level lifecycle events into richer per-tool/per-write dispatch visibility above the same contract
5. Add voice, visual, companion, and runtime support loop surfaces as Phase 10+ layers. Runtime Support Loops now have a proven read-only Studio module/API/panel surface; Voice has a provider-neutral contract in `06_AGENTS/Voice-IO-Architecture.md`, but it remains no-live-provider/no-dispatch/no-canonical-mutation until lower-phase dependencies and focused proof tests exist.

**Phase 10 subset (surface-side):**

Phase 10 subfeatures now have a Phase 9 OSRIL substrate to consume. The Live Operator Shell browser surface is spec-seeded as a read-only/visible-control/dependency-routing lane, but live browser/runtime actions still remain blocked until explicit lower-phase backend contracts and approvals exist.

---

*Graph links: [[OSRIL-Phase9-Closeout]] · [[Voice-IO-Architecture]] · [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Scheduled-Briefing-Pipelines]] · [[Agent-Memory-Architecture]] · [[Execution-Adapter-Standard]] · [[Feature-Fit-Register]] · [[Feature-Register]] · [[ROADMAP]] · [[Permission-Matrix]] · [[ChaseOS-Gate]]*

*Updated: 2026-05-12 (Voice I/O architecture contract linked; voice ingress/egress remains Phase 10 surface-only, provider-neutral, no-live-provider, and no-dispatch/no-canonical-mutation)*

*Operator-Surface-Runtime-Interaction.md — v1.7 | Created: 2026-04-08 | Updated: 2026-05-12 (Voice I/O provider-neutral contract seeded; no live provider/dispatch/canonical authority added) | Updated: 2026-04-28 (OSRIL Phase 9 runtime-side closeout; Phase 10+ surfaces remain planned) | Updated: 2026-04-28 (OSRIL feature closeout scope guard: `resume-ready` included and global Phase 9 closeout not claimed) | Canonical doc for the OSRIL cross-phase feature family; JARVIS reference analysis integrated and formally adopted/adapted/rejected*
