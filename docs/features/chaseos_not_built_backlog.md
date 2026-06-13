# ChaseOS Not-Built / Partial Feature Backlog

> Working backlog refreshed from the operator screenshots plus live `README.md` and `PROJECT_FOUNDATION.md` on 2026-05-30. This is a planning surface, not canonical feature truth. Canonical adoption/readiness still belongs in `06_AGENTS/Feature-Register.md` and `06_AGENTS/Feature-Fit-Register.md`.

## Source sweep

- Screenshots supplied in Discord thread: README and PROJECT_FOUNDATION sections showing `Personal contains`, `What Is Planned / Not Yet Built`, `What is not yet built (honest boundaries)`, Core/Personal split, and Studio/Phase 9/Phase 10 status notes.
- Live docs inspected:
  - `README.md` Core/Personal and honest-boundaries sections.
  - `PROJECT_FOUNDATION.md` planned/not-built, future standalone direction, and Core/Personal split sections.
- Studio product surface inspected:
  - `runtime/studio/shell/frontend/index.html`
  - `runtime/studio/shell/frontend/app.js`
  - `runtime/studio/shell/panel_registry.py`

## Extracted backlog items

| ID | Feature / gap | Visible source wording / live-doc wording | Current status | Product-facing / Studio mapping |
|---|---|---|---|---|
| NB-001 | Event-triggered AOR workflows | `event-triggered workflows remain next` | Not built / next | `Schedules`, `Tasks & Runs`, `Agents / Runtimes` |
| NB-002 | Scheduled Briefing Pipelines expansion | `Scheduled Briefing Pipelines — architecture defined; implementation is Phase 9` | Architecture defined; implementation incomplete | `Proactive Briefings`, `Schedules`, `Review Queue` |
| NB-003 | Workflow Registry completion | `Workflow Registry (PARTIAL)` | Partial | `Workflows` |
| NB-004 | Agent Role Cards completion | `Agent Role Cards (PARTIAL)` | Partial | `Role Cards`, `Agents / Runtimes` |
| NB-005 | Phase 9 second-wave features | `Provenance Schema, Context Governance Layer, Agent Scorecards, Meeting Ingest Linker, trace_idea, drift_scan — spec complete; engineering deferred to after first-wave stable` | Spec complete; engineering deferred | `Provenance`, `Quality Review`, `History / Audit`, `Review Queue` |
| NB-006 | Agent Memory Architecture file structure | `Layers C and D formalized in architecture; file structure not yet created` | Architecture defined; implementation missing | `Memory Manager`, `Memory Ledger`, `Context Import` |
| NB-007 | Agent Identity Ledger implementation | `conceptual; no implementation yet` | Not implemented | `Agent Identity` |
| NB-008 | Runtime Navigation Map accumulation | `implementation foothold seeded ... broader accumulation remains Phase 9` | Seeded foothold; broader work remains | `Runtime Navigation` |
| NB-009 | Multi-Repo / Multi-Directory policy enforcement | `schema defined; enforcement is Phase 9` | Schema only | `Settings`, `Workspace Entry`, `Agents / Runtimes` |
| NB-010 | Layer C durable generated artifacts | `architecture defined; directories created lazily on first promotion` | Deferred until promotion path | `Memory Manager`, `Docs / Inspector` |
| NB-011 | Persisted Studio graph storage | `persisted graph storage ... remain future work` | In progress: read-only graph-store cache/status surface implemented; snapshot write/refresh remains approval-gated future work | `Graph View`, `Docs / Inspector`, `Home` release-grade action center |
| NB-012 | Real target-folder/file workspace upgrade execution | `real target-folder/file upgrade execution ... remain future work` | Future work / approval-gated | `Workspace Entry` |
| NB-013 | Runtime action execution | `runtime action execution ... remain future work` | Future work | `Agents / Runtimes`, `Approval Center` |
| NB-014 | Runtime/adapter activation | `runtime/adapter activation remain future work` | Future work | `Agents / Runtimes`, `Settings` |
| NB-015 | Core export target restoration/revalidation | `export target and manual review artifact missing, so current verification is blocked until restored through the guarded export lane` | Blocked | `Workspace Entry`, `History / Audit`, `Quality Review` |
| NB-016 | Public Core repo gates | `Git initialization, public repository setup, license choice, public .gitignore, remote creation, push/publication, and canonical promotion remain separate approval gates` | Approval-gated / not done | `Workspace Entry`, `Approval Center` |
| NB-017 | Broader Gate coverage beyond Anthropic lane | `broader gateway/Studio/lifecycle/browser-action side-effect coverage remains Phase 9 hardening` | Partial / hardening remains | `Approvals`, `Settings`, `Browser Runtime` |
| NB-018 | Live browser acquisition and connector/API acquisition expansion | `live browser acquisition, connector/API acquisition ... remain future` | Future | `Sources`, `Browser Runtime` |
| NB-019 | Memory candidates / action-ready packets / delivery-ready packets | `memory candidates, action-ready packets, delivery-ready packets ... remain future` | Future | `Context Import`, `Review Queue`, `Missions` |
| NB-020 | Outcome scoring and scheduler integration for acquisition/normalization | `outcome scoring, scheduler integration ... remain future` | Future | `Sources`, `Schedules`, `Quality Review` |
| NB-021 | SBP consumer wiring | `SBP consumer wiring remain future` | Future | `Proactive Briefings`, `Schedules` |
| NB-022 | Full standalone governed Studio product experience | `full standalone governed product experience is still incomplete` | Partial | `Home`, `App Launcher`, all Studio surfaces |
| NB-023 | Branded installer/logo/icon packaging | `no branded logo/icon asset, install wizard, shortcut, signing, startup/autostart, registry, release promotion, host mutation... occurred` | Not done after portable ZIP proof | `Settings`, `History / Audit` |
| NB-024 | Signing/startup/release/host mutation follow-through | `governed signing/startup/release/host mutation follow-through` remains a blocker | Blocked / future | `Settings`, `Approval Center` |
| NB-025 | Real provider/runtime/browser execution or explicit deferral | `real provider/runtime/browser execution or explicit deferral` remains a closure blocker | Blocked / needs decision | `Chat`, `Agents / Runtimes`, `Browser Runtime` |
| NB-026 | Real target workspace upgrade/migration or explicit deferral | `real target workspace upgrade/migration or explicit deferral` remains a closure blocker | Blocked / needs decision | `Workspace Entry` |
| NB-027 | Live client run / live external delivery / live revenue workflow authority | `NO LIVE CLIENT RUN / NO LIVE EXTERNAL DELIVERY`; no payment/CRM/provider/browser/marketplace authority | Not authorized / future | `Missions`, `Workflow Packs`, `VentureOps` surfaces |
| NB-028 | MCP surface expansion | `MCP server V1 is LIVE ... further MCP surface expansion is deferred per design-freeze` | Deferred | `Tools / MCP` coming-soon nav |
| NB-029 | Companion surface | `future companion surface — not yet available` | Planned | `Companion Surface`; likely also `Chat` |
| NB-030 | Voice Mode | Operator-identified missing page: `need to make an additional page for voice mode` | Missing page; first safe slice should mount read-only status/planning page | Studio `#/voice-mode` route -> `runtime/studio/shell/frontend/index.html#panel-voice-mode`; linked from `Chat` |
| NB-031 | Artifact Intelligence & Submission Operator (AISO) | Operator-submitted feature-family spec: local artifact discovery + media comprehension + evidence-backed rename/package + submission draft workflow | Planned / blueprint / not built; documentation registration only | `Missions`, `Workflow Packs`, `Sources / Capture`, `Approval Center`, `Browser Runtime`, future Studio mission card |

## First safe implementation slice

- Completed earlier: mounted `Voice Mode` as a product-facing, read-only/planned Studio page with explicit `No microphone`, `No provider call`, and `No runtime dispatch` posture.
- Current slice: moved NB-011 from pure future work to an actionable read-only graph-store status/cache surface. Studio can now report whether `runtime/graph/store/manifests/current.json` points to a valid persisted snapshot, expose cache counts in the Graph View contract, and show the persisted-graph lane in the Home release-grade action center without writing snapshots, identities, Markdown, or canonical state.

## Follow-up implementation order

1. Keep README / PROJECT_FOUNDATION public-facing and neutral while linking this backlog as the detailed planning surface.
2. Keep `Voice Mode` wired into Studio navigation, feature catalog, panel registry, and static tests as a planned/read-only surface.
3. Next NB-011 pass: add an explicit operator-confirmed snapshot write/refresh command under `runtime/graph/store/`; no frontend writes and no source Markdown mutation.
4. Treat NB-031 / AISO as a high-value but medium-high-risk feature family: first implementation slice should be documentation/manifest/role-card + read-only Recent Artifact Locator over declared safe roots, not email/browser/send/upload execution.
5. Promote selected backlog entries into `06_AGENTS/Feature-Register.md` only when adoption/readiness criteria are met; AISO is now registered as a planned family but remains not built.
6. Implement NB-001/NB-002 through existing AOR/Schedule/Pulse lanes before adding any new authority surface.

## Graph links

[[README]] · [[PROJECT_FOUNDATION]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[06_AGENTS/ChaseOS-Studio-Architecture]]
