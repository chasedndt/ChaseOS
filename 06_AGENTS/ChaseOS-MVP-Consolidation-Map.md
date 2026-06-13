---
title: ChaseOS MVP Consolidation Map
type: current-state-map
status: CURRENT / MVP CONSOLIDATION / READINESS GATE ADDED
created: 2026-05-13
updated: 2026-05-14
runtime: Codex
session_descriptor: mvp-consolidation-map
---

# ChaseOS MVP Consolidation Map

## Operator Quick Brief

For the clear current goal, sector, pass plan, and operator-owned next actions, see [[ChaseOS-MVP-Current-Goal-and-Pass-Plan]].

2026-05-14 continuation note: the canonical next-action card, no-secret operator-input template, P0 OpenAI secret-reference card, and tracked Chat approval/readiness cards were refreshed with current read-only evidence. The state is now P0-only: `safe_to_call_update_goal_complete=false`, `openai_secret_reference` remains the P0 blocker, and tracked approval `5849a53f-10e0-46af-a89a-7de06150f7f8` is executed/marker-present rather than a current P1 operator decision.

## Executive Summary

ChaseOS does not need a new feature family for the MVP. It needs one complete operational loop.

The current MVP sector is:

`MVP Integration / Operator Workflow Activation`

The best next outcome is:

> Chat/Studio create a governed request, approval is consumed once, an Agent Bus task is completed by a bounded runtime worker, evidence is written, and the daily/log/history layer explains the run.

The most important May 13 correction to the May 11 audit is that part of this loop has now moved:

- Studio internal portable MVP is closed with deferrals.
- Companion-selection approval consumption is complete for one approved selection.
- Chat runtime-dispatch approval consumption is complete for one approved dispatch.
- One bounded Agent Bus task for `Codex` was enqueued by that runtime-dispatch executor.
- The task lifecycle has now been exercised and machine-checked by `runtime/mvp_agent_bus_lifecycle.py`: task `task-e417a38df4d0` is `done`, owned by `Codex` / `Axiom-Codex`, has created/claimed/started/result-attached events, and has matching stdout/stderr/result artifacts.
- Chat-to-Approval is now proven for one supported proposal lane: Chat request -> tracked Studio approval artifact `5849a53f-10e0-46af-a89a-7de06150f7f8` -> Approval Center visibility -> governed lifecycle evidence.
- Approval-to-Action is now reconciled against the explicit MVP criterion: approval `60a3153a-00e4-4258-af43-9df89d515705` was consumed exactly once into approved Agent Bus task `chat-runtime-dispatch-ec40d576ce3940c3b3d2`; broader approval execution remains source-specific.
- The remaining operator inputs are consolidated in [[ChaseOS-MVP-Operator-Unblock-Packet]].
- The current blocker map is now machine-checkable with `python -m runtime.cli.main mvp readiness-gate --json`; the gate is read-only, does not read secret values, reports the exact current operator inputs still required, and points to the canonical no-secret MVP handoff card.
- The same readiness gate, operator unblock packet, and Studio `mvp_readiness_panel` now include `mvp_usecase_snapshot`, which consolidates usable-now, blocked-now, and parked-later feature families for the active MVP use case.
- The compact handoff `python -m runtime.cli.main mvp operator-unblock-packet --json` now includes `operator_input_schema_version=chaseos.mvp_operator_input_schema.v1`, with typed fields, current provided/missing state, validation commands, and secret/client-data policies for the OpenAI secret reference. Pending Chat approval decision fields appear only when a tracked approval is actually pending.
- The same compact handoff now includes `operator_input_template_version=chaseos.mvp_operator_input_template.v1`, a fillable placeholder set for operator-approved reference names and repo-relative paths only.
- Filled input packets can now be checked with `python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json`; the validator reports field validity without echoing candidate values and does not write setup metadata, author VentureOps artifacts, consume approvals, write Agent Bus tasks, call providers, ingest client data, or mutate canonical state.
- A valid filled input packet now produces `safe_followup_plan.status=ready_for_operator_confirmed_followup`, with ordered template-only next steps for provider metadata setup and any currently pending approval review. Historical/no-proof vaults can still expose a VentureOps packet-authoring step. The plan does not fill command values or grant execution authority.
- Provider live readiness is still blocked by credential reference problems; [[ChaseOS-MVP-Credential-Readiness-Checklist]] now isolates the P0 operator input as a resolvable OpenAI secret reference outside the repo, and `python -m runtime.cli.main mvp credential-handoff --json` now exposes the credential-only P0/P1/P2 handoff without secret values.
- VentureOps pass 7 is now proof-discovered by the MVP gate: `ventureops evidence-discovery-preflight` finds the approved internal ChaseOS scope packet and valid live-client workflow proof artifact. Revenue proof and external delivery remain outside this MVP criterion.

So the next practical implementation pass should not be "build more surfaces." After the lifecycle proof, the active blocker is credential readiness:

`credential-readiness-repair`

The completed lifecycle pass used the already-created task `chat-runtime-dispatch-ec40d576ce3940c3b3d2`, claimed it as `Codex` / `Axiom-Codex`, and result-logged it as policy-blocked because the task packet prohibited live subprocess execution. The follow-up task `task-e417a38df4d0` then proved the real Codex daemon can return useful text output for a no-write read-only task when the task packet is embedded in the stdin prompt.

## Repo-Truth Delta Since 2026-05-11 Audit

| Area | May 11 Audit Truth | May 13 Current Truth |
|---|---|---|
| Studio MVP | PARTIAL; native/package proof blocked in some paths | Internal portable MVP is CLOSED WITH DEFERRALS; release-grade Studio still open |
| Studio release-grade | broad blockers | action center plus safe-preview runner exist; execution remains blocked |
| Pass 10B / Graph Design | visual/packaging truth still noisy | expanded Pass 10B Graph Design System audit is COMPLETE / VERIFIED |
| Companion selection | readiness/blocked | one governed companion-selection approval was consumed and target JSON written |
| Chat runtime dispatch | readiness/blocked | one approved runtime-dispatch executor consumed approval and wrote a bounded Agent Bus task |
| Agent Bus | local readable, populated | local readable and pass-6 machine-checked through task `task-e417a38df4d0`; queue hygiene still has open/expired backlog |
| Provider readiness | blocked | still blocked by OpenAI placeholder/missing secret reference and missing local fallback |
| VentureOps | real client input required | complete for one scoped local live-client workflow proof; revenue/external delivery still separate |
| Pulse | local v1 complete, effects blocked | same: feature lane complete, broader effects remain approval-gated |
| Full system control | not MVP | still not MVP; pass 10 is now machine-checked by `runtime/mvp_system_control_boundary.py` and the readiness gate |

## Current One-Page State

| Sector | Current Status | What It Means |
|---|---|---|
| Provider credentials | BLOCKED / OPERATOR INPUT REQUIRED / VALIDATION FAILS CLOSED / COCKPIT-BRIDGED | OpenAI is configured structurally but `SET_OPENAI_SECRET_REF` does not resolve; `setup provider validate openai --json`, `mvp readiness-gate --json`, `mvp credential-handoff --json`, and Studio `mvp_readiness_panel` now agree on `secret_reference_resolvable=false`; see [[ChaseOS-MVP-Credential-Readiness-Checklist]], [[ChaseOS-MVP-Operator-Unblock-Packet]], and [[2026-05-13-mvp-openai-secret-reference-handoff-card]] |
| Chat intake | COMPLETE FOR ONE APPROVAL ARTIFACT / PARTIAL BROADER | one supported Chat `project-create` request wrote pending approval artifact `5849a53f-10e0-46af-a89a-7de06150f7f8`; unsupported intents remain blocked |
| Approval consumption | COMPLETE FOR ONE APPROVED AGENT BUS TASK / PARTIAL BROADER | [[ChaseOS-MVP-Completion-Audit]] reconciles pass 5; approval `60a3153a-00e4-4258-af43-9df89d515705` executed and wrote task `chat-runtime-dispatch-ec40d576ce3940c3b3d2` |
| Agent Bus | ACTIVE / MVP LIFECYCLE MACHINE-CHECKED / BACKLOG HYGIENE OPEN | readiness gate now verifies one Codex task lifecycle through SQLite events and adapter artifacts; open/expired hygiene remains separate |
| Codex as worker | LIVE READ-ONLY OUTPUT VERIFIED | Codex daemon readiness, mock lifecycle, policy-block lifecycle, timeout diagnosis, and post-fix live output are proven for simple no-write tasks |
| Studio cockpit | VERIFIED INTERNAL MVP COCKPIT / RELEASE-GRADE OPEN | `studio dashboard --json` now includes `mvp_readiness_panel` with 10-pass status, P0/P1 blockers, safe next commands, operator input schema/template/validator handoff, approvals, runtime health, Agent Bus counts, graph/source status, and no execution authority |
| VentureOps | COMPLETE FOR ONE SCOPED LOCAL LIVE-CLIENT WORKFLOW PROOF / REVENUE STILL SEPARATE | `mvp readiness-gate` now discovers the approved internal ChaseOS scope evidence and valid live-client workflow proof artifact; no external delivery, CRM/payment mutation, revenue proof, provider call, browser action, or canonical promotion is implied |
| Graph/source intelligence | VERIFIED FOR READ-ONLY WORKFLOW CONTEXT | the MVP readiness gate now builds a `context_bridge` proving workflow `ventureops_ai_runtime_security_audit` can reference Phase 7 source workspace refs and graph-context refs without source promotion, graph writes, workflow execution, provider calls, browser control, host mutation, or canonical mutation |
| Pulse | LOCAL V1 COMPLETE | useful as read-only/local product lane; schedule/provider/canonical effects remain gated |
| Full system control | PARKED / MACHINE-CHECKED BOUNDARY | `mvp readiness-gate` now exposes `chaseos_mvp_system_control_boundary`; do not include broad control in MVP beyond read-only boundary reports and separate-approval local CDP proof previews |

## Machine-Readable MVP Gate

The one-clean current-state map command is:

```powershell
python -m runtime.cli.main mvp current-state --json
```

The current MVP readiness command is:

```powershell
python -m runtime.cli.main mvp readiness-gate --json
```

The compact operator handoff command is:

```powershell
python -m runtime.cli.main mvp operator-unblock-packet --json
```

The prompt-to-artifact completion audit command is:

```powershell
python -m runtime.cli.main mvp completion-audit --json
```

The explicit operator-action-required gate is:

```powershell
python -m runtime.cli.main mvp operator-action-required --json
```

The standalone no-secret operator input template command is:

```powershell
python -m runtime.cli.main mvp operator-input-template --json
```

The filled input validation command is:

```powershell
python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json
```

Current verified result for this pass:

- `mvp current-state`: `surface=chaseos_mvp_current_state_map`, `pass_status_count=10`, `safe_to_call_update_goal_complete=false`, next operator action `openai_secret_reference`, and `canonical_operator_handoff.path=07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md`.
- 2026-05-14 rollover recheck: `mvp current-state`, `mvp completion-audit`, `mvp operator-action-required`, `mvp credential-handoff`, `setup provider validate openai`, and the tracked Chat consumption readiness contract agree on the P0-only operator-blocked state; no `update_goal` call is allowed.
- `mvp readiness-gate`: `surface=chaseos_mvp_readiness_gate`, `readiness_status=blocked_operator_input_required`, `completion_matrix_count=10`, `blocked_requirement_ids=[]`, and `canonical_operator_handoff.path=07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md`.
- Studio `mvp_readiness_panel.current_state_map`: same surface, pass count, safe completion flag, and current-state command bridged into the cockpit.
- `readiness_status=blocked_operator_input_required`
- `overall_goal_complete=false`
- `p0_blocker_count=1`
- `operator_input_schema_version=chaseos.mvp_operator_input_schema.v1`
- `operator_input_template_version=chaseos.mvp_operator_input_template.v1`
- `completion_matrix_count=10`
- `blocked_requirement_ids`: none
- P0 blockers: `openai_secret_reference`
- P1 operator decision ids: none
- `next_action_queue`: `openai_secret_reference`
- `operator_input_schema`: `secret_reference_target`.
- `operator_input_template`: fillable placeholder for the same field, with secret values and private client material explicitly forbidden.
- `mvp validate-operator-input`: accepted packets include `safe_followup_plan.status=ready_for_operator_confirmed_followup`; invalid packets include `safe_followup_plan.status=blocked_until_input_validation_passes`.
- `safe_followup_plan.next_steps`: `setup_provider_secret_reference_metadata`; every step keeps `execution_allowed_now=false`.
- `next_operator_action.operator_handoff_steps`: `set_outside_repo_secret_reference` -> `update_setup_metadata_reference` -> `validate_reference_without_secret_read` -> `request_guarded_live_probe_approval`.
- `pending_chat_approval_decision.operator_handoff_steps`: conditional handoff exists only for future pending approvals; tracked approval `5849a53f-10e0-46af-a89a-7de06150f7f8` is executed/marker-present and replay-blocked.
- tracked approval readiness command: `python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract --approval-id 5849a53f-10e0-46af-a89a-7de06150f7f8 --json`.
- `mvp_usecase_snapshot.current_sector`: `MVP Integration / Operator Workflow Activation`.
- `mvp_usecase_snapshot.usable_now`: read-only status consolidation, Chat/Studio approval artifacts, one approval-to-Agent-Bus proof, one Codex Agent Bus lifecycle proof, scoped VentureOps workflow proof, Studio cockpit visibility, and read-only graph/source context.
- `mvp_usecase_snapshot.blocked_now`: `provider_backed_chat_studio`.
- `mvp_usecase_snapshot.parked_or_later`: `full_system_control`, `revenue_external_delivery`, `n8n_connector_automation`, `wallet_exchange_credentials`, `canonical_memory_mutation`.
- `mvp readiness-gate` and `mvp operator-unblock-packet`: both expose top-level completion aliases (`objective_achieved=false`, `safe_to_call_update_goal_complete=false`, `operator_input_ids`, P0/P1 ids, blocked/incomplete ids, and `completion_decision`) so shallow callers can read the same stop/continue decision as current-state, operator-action-required, and completion-audit.
- Studio `mvp_readiness_panel`: mirrors the same top-level completion aliases so the cockpit can read the current stop/continue decision directly while still retaining the nested current-state map.
- `mvp completion-audit`: `surface=chaseos_mvp_completion_audit`, `deliverable_count=10`, top-level `safe_to_call_update_goal_complete=false`, top-level completion aliases mirroring `completion_decision`, incomplete/operator-blocked numbered requirement ids empty, and `canonical_operator_handoff.path=07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md`; credential readiness is covered as no-secret identification/handoff, pass 5 `approval_to_action` is covered by one executed Agent Bus proof, and the OpenAI reference is the current operator input.
- `mvp credential-handoff`: `surface=chaseos_mvp_credential_handoff`, P0 required now `openai_secret_reference`, top-level completion aliases, `required_operator_inputs`, P1 optional/later provider/output references, P2/out-of-scope connector/payment/wallet/system credentials, and no secret/provider/setup/approval/task/browser/host/canonical authority.
- `mvp operator-action-required`: `surface=chaseos_mvp_operator_action_required`, `operator_action_required=true`, `no_safe_autonomous_completion_pass_available=true`, required action `openai_secret_reference`, and `canonical_operator_handoff.path=07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md`.
- `mvp operator-action-required` also exposes `required_actions` as a shallow alias of `required_operator_actions`, plus top-level operator input/P0/P1/blocker aliases mirroring `completion_decision`; `mvp operator-unblock-packet` exposes `required_operator_inputs` as a shallow alias of `operator_inputs_required`.
- `mvp operator-input-template`: `surface=chaseos_mvp_operator_input_template_packet`, current group `openai_secret_reference`, top-level completion aliases, `required_operator_inputs`, no secret value field, and no execution authority; `--write-template` can write the no-secret JSON artifact [[07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json|2026-05-13-mvp-operator-input-template.json]].
- `mvp validate-operator-input`: `surface=chaseos_mvp_operator_input_validation`, `valid=false` for the current template, blocked group `openai_secret_reference`, top-level completion aliases, `required_operator_inputs`, hidden source/candidate values, and no execution authority.
- `ventureops.selected_live_client_workflow_proof_path`: `07_LOGS/Workflow-Proofs/2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof_live-client-workflow-proof.json`.
- Studio `mvp_readiness_panel.operator_input_handoff`: schema/template versions, group field names, forbidden values, and the `mvp validate-operator-input` command without candidate value echo.
- Authority boundary: read-only; no secret-value read, provider call, approval execution, Agent Bus write, browser/host control, or canonical mutation.

## P0 / P1 / P2 Scope Lock

### P0 - Required For Useful MVP

1. **Agent Bus Codex task lifecycle proof**
   - Status: COMPLETE / MACHINE-CHECKED FOR ONE CODEX TASK LIFECYCLE.
   - Evidence: `mvp readiness-gate` pass 6 returns `complete_for_one_codex_task_lifecycle`; proof task `task-e417a38df4d0` is `done`, claimed by `Codex`, has created/claimed/started/result-attached events, and has matching stdout/stderr/result artifacts.

2. **Credential readiness repair**
   - Status: CHECKLIST COMPLETE / OPERATOR SECRET REFERENCE REQUIRED.
   - Evidence: [[ChaseOS-MVP-Credential-Readiness-Checklist]].
   - Replace placeholder OpenAI secret reference outside the repo.
   - Validate setup without exposing the key; provider validation, MVP readiness, and Studio cockpit must fail until `secret_reference_resolvable=true`.
   - Run provider live-smoke readiness until primary is unblocked.

3. **Operator daily loop**
   - Daily note must show current task, blocker, command, result, and next action.
   - Build log/history/activity indexes must stay current.

4. **VentureOps real-client evidence intake**
   - Status: COMPLETE FOR ONE SCOPED LOCAL LIVE-CLIENT WORKFLOW PROOF.
   - Evidence: `mvp readiness-gate` pass 7 returns `complete_for_one_live_client_workflow_proof`.
   - Selected scope packet and live-client workflow proof are under `07_LOGS/Workflow-Proofs/`.
   - Revenue proof, external delivery, CRM/payment mutation, provider/browser action, and canonical promotion remain separate and gated.

5. **Studio as cockpit**
   - Use internal portable Studio and action-center previews to see status/blockers.
   - `python -m runtime.cli.main studio dashboard --json` now exposes `mvp_readiness_panel` with the same operator-input blocker map as the readiness gate.
   - Do not wait for release-grade Studio before proving the MVP loop.

### P1 - Next After MVP Loop Works

1. Chat live provider response lane.
2. Conversation persistence with redaction/retention proof.
3. Studio release-grade approval-consumption lane selection.
4. Graph hygiene decision review and safe cleanup execution.
5. Source/capture live connector pass for one selected connector.
6. VentureOps revenue/external-delivery proof after separate approval, if needed.

### P2 - Later / Explicitly Gated

1. Broad computer or full system control.
2. Payment, CRM, invoices, and revenue claims.
3. Workflow Exchange / marketplace publication.
4. n8n deployment or connector automation.
5. Release-grade installer branding/signing/startup/release promotion.
6. Browser automation beyond already bounded safe targets.

## Ten-Pass Consolidation Checklist

| Requested Pass | Current State | Evidence | MVP Decision |
|---|---|---|---|
| 1. Repo-Truth Consolidation | COMPLETE FOR THIS PASS | this map plus build log | keep current |
| 2. MVP Scope Lock | COMPLETE FOR THIS PASS | P0/P1/P2 table | MVP is one operator loop, not all features |
| 3. Credential Readiness | CHECKLIST COMPLETE / PROVIDER BLOCKED / VALIDATION FAILS CLOSED / STUDIO-BRIDGED | `mvp readiness-gate` reports `openai_secret_reference_target_placeholder_or_missing`, `secret_reference_resolvable=false`, and `secret_reference_probe_error=reference_not_found`; `setup provider validate openai --json` exits nonzero with missing `secret_reference_resolvable`; Studio `mvp_readiness_panel` mirrors the same fields | operator must provide outside-repo OpenAI reference first |
| 4. Chat-to-Approval | COMPLETE FOR ONE SUPPORTED PROPOSAL LANE | [[ChaseOS-MVP-Chat-To-Approval-Proof]]; approval `5849a53f-10e0-46af-a89a-7de06150f7f8` is the tracked Chat approval artifact and is now executed/marker-present | sufficient for MVP Chat intake artifact proof |
| 5. Approval-to-Action | COMPLETE FOR ONE APPROVED AGENT BUS TASK / PARTIAL BROADER | [[ChaseOS-MVP-Completion-Audit]]; approval `60a3153a-00e4-4258-af43-9df89d515705` executed, exact-once marker written, task `chat-runtime-dispatch-ec40d576ce3940c3b3d2` created | sufficient for the explicit MVP pass-5 criterion; broader approval classes remain source-specific |
| 6. Agent Bus Lifecycle | COMPLETE / MACHINE-CHECKED FOR ONE CODEX TASK LIFECYCLE | `mvp readiness-gate` includes `chaseos_mvp_agent_bus_lifecycle`; task `task-e417a38df4d0` is `done`, owned by `Codex` / `Axiom-Codex`, has created/claimed/started/result-attached events, and has matching stdout/stderr/result artifacts | sufficient for MVP bus-output proof; broader task classes remain task-specific |
| 7. VentureOps Real-Use | COMPLETE FOR ONE SCOPED LOCAL LIVE-CLIENT WORKFLOW PROOF | `mvp readiness-gate` and Studio discover the approved internal ChaseOS scope evidence plus valid live-client workflow proof artifact; no provider call, browser action, external delivery, CRM/payment mutation, revenue proof, or canonical promotion is implied | sufficient for MVP pass 7; keep revenue/external delivery gated |
| 8. Studio Cockpit | VERIFIED INTERNAL MVP COCKPIT | `studio dashboard --json` includes `mvp_readiness_panel`, Approval/Agent Bus/runtime/graph/product panels, and no direct execution authority | use as cockpit now |
| 9. Graph / Source Intelligence | VERIFIED FOR READ-ONLY WORKFLOW CONTEXT | `mvp readiness-gate` pass 9 returns `ready_for_read_only_workflow_context_reference` with source workspace refs, graph refs, and all mutation/execution authority false | use as context/navigation, keep mutation gated |
| 10. Full System Control Boundary | PARKED / MACHINE-CHECKED | `mvp readiness-gate` includes `chaseos_mvp_system_control_boundary`: broad system control, browser automation, host mutation, workflow replay, approval consumption, credential/cookie/session/profile access, trusted skill writes, Agent Bus writes, and canonical mutation are all false; CDP read-only proof remains disabled without separate approval | exclude broad control from MVP |

## Credential Checklist

Do not commit secret values. Record only reference names and validation status.

Detailed checklist: [[ChaseOS-MVP-Credential-Readiness-Checklist]]

| Credential / Config | Priority | Current State | MVP Need |
|---|---:|---|---|
| OpenAI secret reference | P0 | configured but unresolved placeholder `SET_OPENAI_SECRET_REF`; `OPENAI_API_KEY` absent in Studio provider preview | required if OpenAI remains default |
| OpenAI model target | P0 | `gpt-5.5` matches runtime configs | keep |
| Anthropic/Claude key | P1 | not configured | only needed if Claude/Hermes provider path is selected |
| Local OSS/Ollama endpoint/model | P1 | not configured | useful fallback, not required for first bus lifecycle proof |
| Discord | P1 | configured/bound | useful for output routing, not required for first MVP loop |
| Perplexity | P1/P2 | template only | only for live research connector |
| n8n | P2 | not configured | not MVP |
| payment/CRM/Whop | P2 | not configured/proof-only | not MVP |
| wallet/exchange/system credentials | out of scope | high risk | do not add |

## Next Work Order

### Pass Name

`operator-provide-openai-secret-reference`

### Why This Is Next

The bus can now claim, execute, result-log, and return useful text output for a simple live read-only Codex task. The credential readiness pass has narrowed provider setup to one P0 operator action. VentureOps pass 7 is now proof-discovered for one scoped local workflow proof, so the exact remaining handoff is consolidated in [[ChaseOS-MVP-Operator-Unblock-Packet]].

### Suggested Commands

```powershell
python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json
python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --json
python -m runtime.cli.main setup provider validate openai --json
python -m runtime.cli.main mvp credential-handoff --json
python -m runtime.cli.main runtime providers --json
python -m runtime.cli.main runtime provider live-smoke-readiness --json
python -m runtime.cli.main studio phase11-chat-live-provider-execution-approval-preview --json
```

### Success Criteria

- `SET_OPENAI_SECRET_REF` no longer appears as the active unresolved OpenAI setup target,
- `OPENAI_API_KEY` or an approved equivalent local secret reference resolves outside the repo,
- setup validation no longer blocks on `reference_not_found`,
- provider live probe remains approval-gated and does not expose secret values.

## Overall Outcome Target

The true MVP is achieved only when this can be demonstrated:

`operator request -> approval -> Agent Bus task -> runtime result -> evidence -> daily closeout`

The components of this loop are now proven across separate governed proofs, but not yet as one single contiguous provider-backed live user workflow. Provider credentials remain the P0 blocker for provider-backed usefulness. The tracked Chat approval artifact is executed/marker-present and replay-blocked, so it is no longer a current P1 operator input. VentureOps pass 7 is complete for one scoped local proof; payment/CRM/n8n/wallet-style credentials, revenue proof, and external delivery remain outside P0.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
