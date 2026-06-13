---
title: Live Operator Shell Browser Surface
type: phase10-surface-contract
status: SEEDED / SPEC-READY / NO LIVE ACTION AUTHORITY
created: 2026-05-12
updated: 2026-05-12
phase: Phase 10 Studio / Operator Shell over Phase 9 Browser Runtime + OSRIL
runtime: Hermes / Optimus
---

# Live Operator Shell Browser Surface

This contract seeds the full Phase 10 Live Operator Shell browser lane beyond the existing read-only Browser Runtime panel and the governed Chat/Studio browser-runtime dispatch proof.

The lane is an operator-facing shell for browser/runtime action visibility, readiness, approval context, and evidence. It is not a direct browser-control backend. Browser launch, CDP connection, navigation, screenshots, DOM capture, approval consumption, Agent Bus writes, provider/connector calls, credential/profile access, and canonical writeback remain Phase 9-and-below dependencies routed through explicit backend contracts.

## Current Repo Truth

Existing substrates this surface must consume rather than replace:

| Substrate | Current proof | Live-shell use |
| --- | --- | --- |
| Browser Runtime readiness panel | `runtime/studio/browser_runtime_operator_ui_readiness.py` and `06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md` | Supplies read-only Browser Runtime status, blockers, evidence paths, approval placeholders, and no-action posture. |
| Governed Chat/Studio dispatch lane | `runtime/studio/chat_browser_runtime_dispatch_lane.py` | Supplies browser-bound intent manifest, target profile, approval-artifact binding, denial proofs, visible-control metadata, and exact-once lower-phase executor handoff. |
| Studio desktop shell mock | `runtime/studio/desktop_shell_app.py` | Existing localhost-only shell that can mount read-only panels and degraded/no-action states. |
| Agent control UX contract | `06_AGENTS/Agent-Control-UX-Contract.md` | Defines control HUD, lane/state taxonomy, manual takeover, audit/provenance visibility, and visible-control requirements. |
| OSRIL runtime substrate | `runtime/osril/` and `06_AGENTS/Operator-Surface-Runtime-Interaction.md` | Supplies runtime/session/event/approval visibility; the shell consumes it without becoming a command authority. |

## Product Scope

The Browser Live Operator Shell should expose these panels as a single operator lane:

| Panel | Purpose | Minimum no-action state |
| --- | --- | --- |
| Browser Session Header | Shows runtime, lane, target profile, target URL/domain, approval id, session scope, risk level, and current state. | `no_browser_session_active`; no launch button unless a lower-phase approved contract is present. |
| Visible Control HUD | Shows who/what is observing or controlling, current action, cursor/focus/action-feedback expectations, manual takeover affordance, and audit link. | `control_inactive`; render proof/requirements, not a fake controller. |
| Readiness + Blockers | Composes Browser Runtime readiness, dispatch-lane denial proofs, external-runtime branch gates, approval state, and missing backend contracts. | `blocked_no_approved_backend_contract` or more specific denial reason. |
| Approval Context | Shows required approval schema, supplied approval id, approval status, exact-once/idempotency posture, and whether approval consumption is delegated to the executor only. | `approval_missing_or_not_consumable_by_shell`. |
| Action Preview Rail | Lists requested browser actions in structured form, target profile constraints, blocked effects, and lower-phase owner. | `preview_only`; cannot dispatch from the shell. |
| Live Evidence Rail | Shows Browser Run log, screenshot, DOM snapshot, Agent Activity, approval consumption, idempotency marker, and candidate/evidence refs when they exist. | `no_live_evidence_yet`; link readiness/evidence roots only. |
| Dependency Routing | Turns missing backend authority into explicit lower-phase work items: browser dispatch execution, runtime dispatch, Agent Bus writes, credentials/profile access, provider/connector calls, or approval consumption. | `dependency_routing_only`; no automatic enqueue until Agent Bus write contract exists. |
| Operator Stop / Takeover | Shows pause/takeover semantics for future live control sessions. | `manual_takeover_not_available_until_live_runner_contract`. |

## Readiness States

The shell must distinguish display readiness from action readiness:

| State | Meaning | Allowed surface behavior |
| --- | --- | --- |
| `display_ready` | Shell can render current Browser Runtime/dispatch/readiness/evidence data. | Read-only panels and no-action previews. |
| `blocked_missing_backend_contract` | Requested live action lacks an approved lower-phase contract. | Show blocker and dependency owner. |
| `blocked_missing_approval` | Live action requires a Gate/AOR approval artifact and none is valid. | Show approval requirements; do not execute or consume. |
| `blocked_scope_or_target` | Target URL/profile/session scope violates target-profile policy. | Show denial proof; no browser launch. |
| `armed_for_lower_phase_handoff` | All shell-visible preconditions are present, but execution still belongs to lower-phase executor. | Show exact lower-phase handoff packet; shell remains non-executing unless a future approved dispatcher contract exists. |
| `live_execution_observed` | A lower-phase executor has produced events/evidence. | Render evidence and OSRIL/browser events; do not mutate them. |
| `completed_with_evidence` | Run completed and evidence refs exist. | Show results, provenance, and follow-up proposals. |
| `manual_takeover` | Human operator has paused/taken control. | Show pause boundary and stop all automated action display as active. |

## Authority Boundary

The Live Operator Shell browser lane must not:

- launch browsers or attach to existing browser profiles;
- connect CDP/MCP or invoke Browser Use CLI;
- navigate targets, click, type, upload, download, draw, or mutate DOM;
- read credentials, cookies, browser storage, history, password managers, or real profiles;
- consume approvals or reserve idempotency markers;
- enqueue Agent Bus tasks or mutate runtime state unless a separate approved write contract exists;
- call providers/connectors;
- promote skills or write trusted artifacts;
- mutate Gate policy, workflow manifests, role cards, protected files, or canonical ChaseOS knowledge.

Allowed Phase 10 work is read-only display, no-action preview, visible-control UX, dependency routing language, and handoff packet inspection over already-existing lower-phase contracts.

## Dependency Routing Contract

Every blocked live browser/runtime action must produce a dependency record with these fields:

```yaml
dependency_id: required
requested_surface: live_operator_shell_browser
blocked_action: required
blocked_action_reason: required
missing_contract: required
lower_phase_owner: Browser Runtime | AOR | OSRIL | Agent Bus | Gate | SiteOps | Provider Adapter | Credential/Profile Policy
affected_panel: required
minimum_proof_needed: required
allowed_now: read_only_preview | display_ready | dependency_routing_only
canonical_mutation_allowed: false
```

Recommended first blockers to route:

| Blocker | Lower-phase owner | Minimum proof needed |
| --- | --- | --- |
| Browser action execution from shell | Browser Runtime / SiteOps / AOR | Approved workflow/executor contract with target profile, approval artifact, idempotency, audit/evidence writes, and no direct shell authority. |
| Approval consumption from shell | AOR / Gate / OSRIL | Immutable approval-response/resume semantics and exact-once executor consumption path. |
| Agent Bus task creation from shell | Agent Bus / Gate | Runtime-operation policy for the exact task-write mutation and visible preview. |
| Authenticated browser/profile session | Credential/Profile Policy + Browser Runtime | User/session scope, credential non-disclosure, profile isolation, approval, and audit proof. |
| Provider/connector-backed browser actions | Provider/Connector Adapter + Gate | Explicit adapter manifest, credential boundary, approval, budget, and audit proof. |

## Acceptance Criteria

A future implementation may claim the browser live operator shell is ready only when:

1. The shell renders the Browser Runtime readiness panel, dispatch-lane manifest, visible-control HUD, approval context, action preview, evidence rail, and dependency routing without executing browser actions.
2. Every panel has an explicit no-action/degraded state and no fake success state.
3. The UI shows target URL/domain, target profile, runtime, session scope, approval id/status, denial reasons, and evidence refs before any lower-phase handoff.
4. The shell cannot consume approvals, reserve markers, or call the executor directly unless a separate backend contract explicitly authorizes that action path.
5. Missing backend authority produces a structured dependency record rather than a hidden button or generic error.
6. Browser credentials, cookies, real profiles, provider calls, Agent Bus writes, and canonical writeback are all denied by default and visible in the authority posture.
7. Tests prove no browser/CDP/MCP/Browser Use/provider/Agent Bus/canonical side effects occur while rendering display-ready or blocked states.
8. Operator-facing docs and build logs link the surface back to OSRIL, Browser Runtime readiness, Agent Control UX, and the dispatch proof.

## Rollout Stages

1. Read-only shell scope contract — this document and the folder guide under `runtime/operator_surface/browser/`.
2. Static data contract — a pure function that composes existing readiness/dispatch/readiness-evidence payloads into the panel model; no server, browser, or queue write.
3. Desktop shell mount — add the panel model to `runtime/studio/desktop_shell_app.py` as a read-only/degraded-safe view.
4. Static/local visual QA — prove the shell renders no-action, denied, and display-ready states without side effects.
5. Dependency-routing preview — add structured blocker packets for lower-phase work without Agent Bus mutation.
6. Approved Agent Bus write path — only after Gate/runtime-operation policy exists for the exact shell-to-bus mutation.
7. Approved lower-phase execution handoff — only after the backend executor contract explicitly consumes approval/idempotency and the shell remains visible-control/preview surface, not execution authority.

## Human Approval Gates

Before any stage beyond read-only rendering:

- Operator approval is required to write or consume any approval artifact.
- Human review is required before enabling Agent Bus task writes from the shell.
- Human review is required before any browser launch/CDP/Browser Use/MCP execution path can be reached from the shell.
- Human review is required before authenticated profile, credential, cookie, real account, or provider-backed action support.
- Gate/permission review is required before any workflow, role-card, adapter manifest, or runtime-operation policy change.

## Testability Now

This lane is testable now at the contract and no-action rendering level. The live ChaseOS runtime substrate already exists in repo truth: Browser Runtime readiness, governed Chat/Studio dispatch proof, OSRIL session/approval visibility, and the localhost Studio shell are all present. What is not built is uncontrolled live browser control from the shell; that remains intentionally blocked until lower-phase contracts and approvals exist.

Recommended focused validation for the next implementation slice:

```bash
PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_browser_runtime_operator_ui_readiness.py runtime/studio/test_chat_browser_runtime_dispatch_lane.py runtime/studio/test_desktop_shell_app.py -q
```

## Next Implementation Slice

Create a read-only `runtime/operator_surface/browser/` panel model that composes:

- `build_studio_browser_runtime_operator_ui_readiness(...)`
- `build_chat_studio_browser_runtime_dispatch_lane_manifest(...)`
- visible-control metadata from `Agent-Control-UX-Contract.md`
- explicit dependency-routing records for missing live action authority

The first implementation must return no-action states only and must not mount execution buttons, consume approvals, enqueue Agent Bus tasks, or launch browser/runtime actions.

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Operator-Surface-Runtime-Interaction]] · [[Studio-Browser-Runtime-Operator-UI-Readiness]] · [[Agent-Control-UX-Contract]] · [[ChaseOS-Approval-Center]] · [[Browser-Runtime-Feature-Readiness-Tracker]] · [[Hermes-Runtime-Profile]] · [[HERMES]] · [[Agent-Activity-Index]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
