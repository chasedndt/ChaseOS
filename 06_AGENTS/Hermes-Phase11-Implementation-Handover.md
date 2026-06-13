---
title: Hermes Phase 11 Implementation Handover
type: handover
status: active bounded continuation lane
phase: 11
runtime-lane: Hermes/Optimus
created: 2026-05-11
updated: 2026-05-11
---

# Hermes Phase 11 Implementation Handover

> Phase 11 Chat is a ChaseOS operator surface over governed lower-phase contracts. It is not a control plane, not a canonical truth engine, and not a bypass around Phase 9 AOR/Gate/Agent Bus authority.
>
> Hermes/Optimus may continue bounded Chat surface, proposal-card, preview, readiness, local UI-shell, and audit/handoff work. Backend execution, canonical mutation, approval consumption, runtime dispatch, browser/shell/connector use, credential/config mutation, source-pack promotion, and protected-file writes route back to Phase 9-and-below unless a separate lower-phase workflow grants that exact authority.

---

## 1. Current Phase 11 Status

Phase 11 Chat is currently a read-only / approval-gated Studio surface lane with verified contract layers already present under `runtime/studio/`. Dependency reports from these surfaces must expose the exact section-6 field names (`affected_phase10_or_phase11_surface` and `lower_phase_owner_or_surface`) and must not emit the legacy aliases `affected_phase_surface`, `affected_phase10_11_surface`, or `lower_phase_owner_surface`.

Implemented and testable Phase 11 surfaces now include:

- `phase11_chat_router_contract.py` — classifies Chat intents, produces no-execution action previews, flags denied side effects, and maps lower-phase dependencies using the exact section-6 dependency report fields.
- `phase11_chat_safety_policy.py` — centralizes deny-default action-class policy and lower-phase ownership routing without granting Chat execution authority.
- `phase11_chat_panel_contract.py` — exposes Chat panel status and dependency posture for Studio UI rendering.
- `phase11_chat_approval_handoff_queue_contract.py` — previews future approval queue handoffs while keeping queue writes blocked.
- `phase11_chat_approval_queue_write.py` — models the approval-gated queue write proof path; live execution remains blocked except where separately approved and proven.
- `phase11_chat_approval_consumption_readiness.py` — previews approval-consumption readiness without mutating approval status, writing exact-once markers, executing approvals, or touching targets.
- `phase11_chat_approval_consumption_executor.py` — contains the bounded executor contract surface for separately approved approval consumption; Phase 11 Chat handover work must still treat actual approval consumption as a lower-phase-gated transition.
- `phase11_chat_runtime_dispatch_readiness.py` — reads runtime capability / Agent Bus / AOR posture and previews future runtime dispatch packets without creating or claiming tasks.
- `phase11_chat_agent_bus_dispatch_bridge.py` — previews Agent Bus dispatch bridge material without writing Agent Bus tasks or dispatching runtimes.
- `phase11_chat_browser_dispatch_readiness.py` — previews browser-dispatch readiness without launching Browser Use, CDP/MCP, navigation, screenshots, Agent Bus tasks, or canonical mutation.
- `phase11_chat_live_provider_approval_preview.py` — previews future provider execution approval material without provider/model calls, approval writes, approval execution, conversation writes, runtime/browser dispatch, Agent Bus task writes, or canonical mutation.
- `phase11_chat_live_provider_execution_contract.py` — defines the provider execution contract posture while keeping provider calls credential-safe and approval-gated outside the Chat surface.
- `phase11_chat_conversation_persistence_contract.py` — previews conversation/audit target paths and future persistence approval material without writing conversation logs.
- `phase11_chat_companion_status.py`, `phase11_chat_companion_selection_preview.py`, and `phase11_chat_companion_selection_queue_write_readiness.py` — expose companion status/selection readiness and queue-write metadata while keeping runtime control, identity mutation, profile writes, approval artifacts, and selection target writes blocked.
- `phase11_goal_checkpoint_contract.py` and `phase11_post_closeout_planning.py` — preserve long-running `/goal` checkpoint and post-closeout planning state without expanding authority.

The practical payoff is that Hermes/OpenClaw summaries and Studio Chat can now show a user what would be needed to act, why it is blocked, and which lower-phase lane owns the missing proof. The ChaseOS OS alignment is that Chat remains an operator interface on top of AOR, Gate, Agent Bus, provider, lifecycle, and graph contracts rather than becoming a separate authority layer.

---

## 2. Bounded Hermes/Optimus Continuation Lane

Hermes/Optimus owns the Phase 11 continuation lane for:

1. Chat panel and Studio UI surfaces that render existing contract state.
2. Proposal-card and action-preview copy that is visibly disabled unless a lower-phase gate is satisfied.
3. Read-only readiness packets that inspect existing artifacts, manifests, indexes, or bus state without mutating them.
4. Handoff/audit documentation that keeps future `/goal` agents oriented.
5. Test updates that assert no-write, no-dispatch, no-provider, no-browser, no-credential, no-canonical, and no-protected-file behavior.

Hermes/Optimus does not own backend execution enablement for Phase 11. If a requested next step requires a lower-phase contract, create a dependency report and route it through the appropriate Phase 9-and-below lane instead of implementing it inside Chat.

---

## 3. Next Implementation Goals

Recommended next goals, in safe order:

1. Keep the Chat router and panel dependency maps synchronized with this handover, including the exact dependency report fields in section 6.
2. Harden proposal-card and action-preview UX so every disabled control explains the missing lower-phase contract and displays no-write proof.
3. Extend read-only readiness packets only when they can inspect existing state without creating approvals, consuming approvals, writing Agent Bus tasks, invoking providers, launching browsers, or mutating canonical graph/vault state.
4. Add test fixtures for long-running `/goal` handoffs: checkpoint cadence, artifact paths, no-write proof fields, and dependency routing examples.
5. Use Agent-Activity records to preserve continuation state for future Hermes/Optimus `/goal` agents.
6. Defer live execution until a separate lower-phase owner provides proof that the backend contract exists, is gated, is tested, and exposes a non-Chat execution consumer.

---

## 4. Checkpoint Rules for 12h+ `/goal` Agents

Long-running Hermes/Optimus `/goal` agents working Phase 11 must checkpoint regularly so continuation remains inspectable after restarts.

Minimum checkpoint expectations:

- Post a short checkpoint at major seams and at least every few hours during a 12h+ run.
- Include current surface, current artifact(s), tests or smokes run, authority posture, next safe action, and any blocker report ids/paths.
- Preserve no-write proof: explicitly state whether any file, queue, provider, browser, Agent Bus, approval, Gate, or canonical target was mutated.
- If a dependency is discovered, record it using the exact dependency fields in section 6 before proceeding.
- Keep future handoff context in `07_LOGS/Agent-Activity/` using a `hermes` or `hermes-optimus` slug and links to `[[Hermes-Runtime-Profile]]`, `[[HERMES]]`, and `[[Agent-Activity-Index]]`.
- Do not rely on Discord/chat memory as the machine source of truth. Durable coordination-sensitive state belongs in `runtime/agent_bus/` or an approved audit/handoff artifact.

Suggested checkpoint shape:

```markdown
## Checkpoint — <UTC timestamp>
- Surface: Phase 11 Chat / <specific module or doc>
- Artifact(s): <paths>
- Status: read-only / approval-gated / blocked / verified
- Tests or smokes: <commands and result>
- No-write proof: provider_call=false; browser_launch=false; agent_bus_task_written=false; approval_consumed=false; canonical_writeback=false; protected_file_write=false
- Dependency reports: <ids or inline reports>
- Next safe action: <bounded action or lower-phase route>
```

---

## 5. Test Expectations

A Phase 11 continuation pass is testable now when it touches runtime/Studio code. At minimum:

- Add or update focused `runtime/studio/test_phase11_*.py` coverage for any changed contract fields.
- Assert that Chat surfaces return `read_only: true` or equivalent no-mutation posture when applicable.
- Assert negative side-effect flags: provider calls, credential reads, approval consumption, queue writes, Agent Bus task writes, browser launch/navigation/screenshots, runtime dispatch, target vault writes, protected-file writes, and canonical writeback remain false unless the exact lower-phase workflow explicitly grants and tests them.
- Run focused tests for the touched surface before broad regressions.
- Use WSL-safe ChaseOS command style when running Python tests: `PYTHONPATH=. uvx --with pyyaml pytest ...`.

Docs-only handover passes should still be verified by direct file reads, link/index checks, and, when possible, focused tests for any synchronized runtime contract change.

---

## 6. Required Backend Dependency Report Fields

Every Phase 11 backend or canonical dependency must be routed with these exact fields:

| Field | Required content |
|---|---|
| `missing_contract` | The absent lower-phase contract, executor, gate, policy, manifest, or approval seam. |
| `affected_phase10_or_phase11_surface` | The Studio/Chat surface blocked by the missing contract. |
| `lower_phase_owner_or_surface` | The responsible lower-phase owner/surface such as AOR, Gate, Agent Bus, RPGL/provider governance, browser policy, graph mutation policy, lifecycle policy, or protected-file workflow. |
| `minimum_proof_needed` | The smallest evidence bundle needed before Phase 11 may expose or enable the next surface. |
| `blocked_action_reason` | The concrete action Phase 10/11 must not perform until the proof exists. |

Example:

```yaml
missing_contract: agent_bus runtime dispatch packet creation and claim/execute contract
affected_phase10_or_phase11_surface: Phase 11 Chat runtime task preview / handoff surface
lower_phase_owner_or_surface: runtime/agent_bus router plus Phase 9 AOR workflow foundation
minimum_proof_needed: schema-valid packet preview, eligible runtime route, approval envelope where required, non-Chat execution consumer, and audit proof
blocked_action_reason: Chat may preview the handoff but must not create Agent Bus tasks, claim work, or dispatch executable runtimes
```

---

## 7. Dependencies That Route Back to Phase 9-and-Below

Route these dependencies out of the Hermes/Optimus Phase 11 surface lane:

- Backend contract gaps for AOR, Gate, Agent Bus, RPGL/provider routing, lifecycle, source-pack, graph, memory, or audit writers.
- Lifecycle execution: starting, stopping, restarting, scheduling, activating, or supervising runtimes.
- Source-pack creation or promotion, including quarantine-to-canonical paths.
- Graph canonical mutation, graph diff application, durable edge creation, or protected graph updates.
- Approval consumption/execution, idempotency marker writes, or approval decision mutation.
- Runtime dispatch, Agent Bus task creation/claim/execute, or live runtime handoff.
- Browser, shell, connector, CDP/MCP, provider, or external API authority.
- Credential reads, secret exposure, provider config mutation, model/provider setting writes, or environment changes.
- Protected-file writes, governance policy changes, Permission Matrix / Trust Tiers / Gate changes, or control-plane mutation.
- Canonical knowledge promotion or direct writes to `02_KNOWLEDGE/`.

---

## 8. Audit and Logging Conventions

For Phase 11 continuation work:

- Use `07_LOGS/Agent-Activity/YYYY-MM-DD-hermes-optimus-<topic>.md` for Hermes/Optimus handoff/audit records.
- Link `[[Hermes-Runtime-Profile]]`, `[[HERMES]]`, and `[[Agent-Activity-Index]]` in the activity record.
- Include changed files, tests/smokes, no-write proof, dependency routes, and next safe pass.
- Update `07_LOGS/Agent-Activity/Agent-Activity-Index.md` with a short row for discoverability.
- If a blocker belongs to another runtime lane, describe it as a runtime-instance lane dependency, not generic non-Claude work. OpenClaw may provide Windows-side/backend evidence; Hermes/Optimus remains the bounded Studio/Chat surface implementation lane.

---

## 9. Explicit Non-Goals

Phase 11 Chat and Phase 10 Studio must not be redefined as sources of canonical truth. They are operator surfaces over ChaseOS.

This handover does not authorize:

- backend execution
- canonical graph mutation
- approval consumption
- runtime dispatch
- source-pack promotion
- credential/config mutation
- browser control
- shell authority
- connector authority
- protected-file writes
- Gate or permission policy mutation
- direct canonical knowledge promotion

---

*Graph links: [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Hermes-Adapter-Spec]] · [[Hermes-Workflow-Boundaries]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Agent-Activity-Index]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Security-Model]]*
